from celery import Celery
import httpx
import asyncio
from config import settings
from database import SessionLocal, Message, ChatSession, User, SystemPrompt, ActiveAITask
from datetime import datetime, timezone
import uuid
import logging
import time

# Import AI model manager for direct integration
try:
    from ai_model_manager import ai_model_manager
    AI_MODEL_AVAILABLE = True
except ImportError:
    AI_MODEL_AVAILABLE = False
    logger.warning("⚠️ AI model manager not available, falling back to HTTP calls")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "chatting_platform",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["celery_app"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Fix deprecation warning
    broker_connection_retry_on_startup=True,
    # AI Server Integration Optimizations
    task_acks_late=True,  # Don't acknowledge until task is complete
    worker_prefetch_multiplier=1,  # Process one task at a time for AI server
    task_time_limit=300,  # 5 minutes max for AI generation tasks
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    # Retry and Error Handling
    task_always_eager=False,  # Ensure async processing
    task_eager_propagates=True,  # Propagate exceptions
    # Monitoring and Logging
    worker_send_task_events=True,
    task_send_sent_event=True,
)

@celery_app.task(bind=True, max_retries=3)
def process_ai_response(self, session_id: str, user_message: str, max_tokens: int = 300, is_ai_initiated: bool = False):
    """
    Process AI response asynchronously with improved AI server integration
    """
    try:
        # Get database session
        db = SessionLocal()
        
        # Check if this task has been cancelled
        active_task = db.query(ActiveAITask).filter(ActiveAITask.task_id == self.request.id).first()
        if active_task and active_task.is_cancelled:
            logger.info(f"Task {self.request.id} was cancelled, skipping AI response")
            db.close()
            return {"success": False, "error": "Task was cancelled"}
        
        # Get chat session
        chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            raise Exception(f"Chat session {session_id} not found")
        
        # Check if user is blocked
        if chat_session.user.is_blocked:
            logger.info(f"User {chat_session.user.user_code} is blocked, cancelling AI response")
            db.close()
            return {"success": False, "error": "User is blocked"}
        
        # Check if AI responses are enabled for this user
        if not chat_session.user.ai_responses_enabled:
            logger.info(f"AI responses disabled for user {chat_session.user.user_code}, cancelling AI response")
            db.close()
            return {"success": False, "error": "AI responses are disabled for this user"}
        
        # Get conversation history (excluding admin interventions)
        messages = db.query(Message).filter(
            Message.session_id == session_id,
            Message.is_admin_intervention == False  # Exclude admin messages from AI context
        ).order_by(Message.created_at).all()
        
        # Build conversation history for AI (only user messages for proper flow)
        history = []
        for msg in messages:
            if msg.is_from_user:
                history.append(msg.content)  # Only add user messages to history
            # Skip AI messages - they shouldn't be in the input history
        
        # Handle AI-initiated messages differently
        if is_ai_initiated:
            # For AI-initiated messages, don't add to history as user message
            # Just use the message as the AI's intended response
            ai_response = user_message  # "hi" in this case
        else:
            # Add current user message (without prefix)
            history.append(user_message)
            
            # Call AI model API with full conversation history
            combined_prompt = chat_session.scenario_prompt
            logger.info(f"Using session scenario prompt (already contains head + tally + rule)")
            logger.info(f"Session scenario prompt length: {len(combined_prompt)} characters")
            logger.info(f"Session scenario preview: {combined_prompt[:300]}...")
            
            # Call AI model API - will create new session with full context
            ai_response = call_ai_model(combined_prompt, history, max_tokens, str(session_id))
        
        # Save AI response to database
        ai_message = Message(
            id=uuid.uuid4(),
            session_id=session_id,
            content=ai_response,
            is_from_user=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(ai_message)
        
        # Update session timestamp
        chat_session.updated_at = datetime.now(timezone.utc)
        chat_session.user.last_active = datetime.now(timezone.utc)
        
        db.commit()
        
        # Get the message ID before closing the session
        message_id = str(ai_message.id)
        db.close()
        
        return {
            "success": True,
            "response": ai_response,
            "message_id": message_id
        }
        
    except Exception as exc:
        db.rollback()
        db.close()
        
        # Don't retry for specific errors that won't be resolved by retrying
        if any(error_msg in str(exc).lower() for error_msg in [
            "ai responses are disabled", 
            "user is blocked", 
            "task was cancelled",
            "chat session not found"
        ]):
            logger.info(f"Not retrying task due to permanent error: {exc}")
            return {"success": False, "error": str(exc)}
        
        # Improved retry logic for AI server communication issues
        if self.request.retries < self.max_retries:
            # Progressive retry delays: 5s, 15s, 30s (instead of 60s each)
            retry_delays = [5, 15, 30]
            current_retry = self.request.retries
            delay = retry_delays[current_retry] if current_retry < len(retry_delays) else 30
            
            logger.info(f"🔄 Retrying task {self.request.id}, attempt {current_retry + 1}/{self.max_retries}, delay: {delay}s")
            logger.info(f"📝 Error: {exc}")
            
            # Don't save error message to database on retries
            raise self.retry(countdown=delay, exc=exc)
        
        # If all retries failed, save error message (only on final failure)
        try:
            db = SessionLocal()
            error_message = Message(
                id=uuid.uuid4(),
                session_id=session_id,
                content="I'm sorry, I'm having trouble responding right now. Please try again later.",
                is_from_user=False,
                created_at=datetime.now(timezone.utc)
            )
            db.add(error_message)
            db.commit()
            db.close()
            logger.error(f"❌ Task {self.request.id} failed after {self.max_retries} retries: {exc}")
        except Exception as db_error:
            logger.error(f"❌ Failed to save error message: {db_error}")
        
        return {
            "success": False,
            "error": str(exc)
        }

def call_ai_model(system_prompt: str, history: list, max_tokens: int = 300, session_id: str = None) -> str:
    """
    Call the AI model API with improved timeout and health checking
    Always creates new AI session with full conversation history for context
    """
    try:
        # Log the system prompt being sent for debugging
        logger.info(f"Sending system prompt to AI model: {system_prompt[:200]}...")
        logger.info(f"Building context with {len(history)} messages from database")
        
        # Check AI server health first
        logger.info("🏥 Checking AI server health before request...")
        try:
            with httpx.Client(timeout=10.0) as health_client:
                health_response = health_client.get(
                    f"{settings.ai_model_url}/health",
                    auth=(settings.ai_model_auth_username, settings.ai_model_auth_password)
                )
                if health_response.status_code != 200:
                    logger.warning(f"⚠️ AI server health check failed: {health_response.status_code}")
                else:
                    logger.info("✅ AI server health check passed")
        except Exception as health_error:
            logger.warning(f"⚠️ AI server health check error: {health_error}")
        
        # Prepare the request with extended timeout for AI generation
        # AI generation can take 45-90 seconds for complex responses
        with httpx.Client(timeout=90.0) as client:  # ← FIXED: Extended timeout for AI generation
            # Initialize AI session with the correct session ID and system prompt from backend
            logger.info("Initializing AI session with backend data...")
            
            # Use the session ID from the database (not generate a new one)
            if session_id is None:
                raise Exception("Session ID is required for AI model initialization")
            session_id_str = str(session_id)  # Convert UUID to string
            
            init_response = client.post(
                f"{settings.ai_model_url}/init-session",
                json={
                    "session_id": session_id_str,
                    "system_prompt": system_prompt
                },
                auth=(settings.ai_model_auth_username, settings.ai_model_auth_password)
            )
            
            if init_response.status_code != 200:
                error_detail = f"Failed to initialize AI session: {init_response.status_code}"
                try:
                    error_data = init_response.json()
                    if 'detail' in error_data:
                        error_detail += f" - {error_data['detail']}"
                except:
                    error_detail += f" - {init_response.text}"
                raise Exception(error_detail)
            
            # Use the session ID we sent (not from cookies)
            session_cookie = session_id_str
            logger.info(f"Initialized AI session: {session_cookie}")
            
            # Verify the session was created by checking if we can access it
            verify_response = client.get(
                f"{settings.ai_model_url}/debug-session/{session_id_str}",
                auth=(settings.ai_model_auth_username, settings.ai_model_auth_password)
            )
            
            if verify_response.status_code == 200:
                session_info = verify_response.json()
                logger.info(f"✅ Session verified: {session_info.get('session_id')} with {len(session_info.get('system_prompt', ''))} chars")
            else:
                logger.warning(f"⚠️ Could not verify session creation: {verify_response.status_code}")
            
            # Build conversation context by sending all previous messages
            # This ensures the AI has full conversation history even after restarts
            if len(history) > 1:  # If we have more than just the current user message
                logger.info("Building conversation context...")
                context_messages = history[:-1]  # All messages except the current one
                
                # OPTIMIZATION: Limit context messages for speed
                max_context_messages = 4  # Reduced from 6 to 4 for maximum speed
                if len(context_messages) > max_context_messages:
                    logger.info(f"Limiting context to {max_context_messages} messages for speed (from {len(context_messages)})")
                    context_messages = context_messages[-max_context_messages:]  # Take most recent
                
                for i, msg in enumerate(context_messages):
                    try:
                        # Send each message to build context (with minimal tokens)
                        context_response = client.post(
                            f"{settings.ai_model_url}/chat",
                            json={
                                "message": msg,
                                "max_tokens": 100,  # ← OPTIMIZED: Increased for better sentence completion
                                "temperature": 0.1,  # Low temperature for context building
                                "top_p": 0.8,        # Focused sampling for context
                                "speed_mode": True   # ← OPTIMIZED: Enable speed mode for context
                            },
                            cookies={"session_id": session_cookie},
                            auth=(settings.ai_model_auth_username, settings.ai_model_auth_password)
                        )
                        
                        if context_response.status_code == 200:
                            logger.info(f"Context message {i+1}/{len(context_messages)} processed")
                        else:
                            logger.warning(f"Context message {i+1} failed: {context_response.status_code}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to process context message {i+1}: {e}")
                        # Continue with other context messages
                        continue
            
            # Get the current user message (last in history)
            current_user_message = None
            # Since we're alternating between user and AI messages, the last message should be the user's
            if history and len(history) > 0:
                current_user_message = history[-1]  # Last message is the user's
            
            if not current_user_message:
                raise Exception("No current user message found in history")
            
            logger.info(f"Sending current user message: {current_user_message[:100]}...")
            
            # Send chat request using existing session
            # Ensure max_tokens meets AI server requirements (min 100, max 1000)
            ai_max_tokens = max(100, min(max_tokens, 1000))
            
            # Send the current user message to get AI response
            chat_response = client.post(
                f"{settings.ai_model_url}/chat",
                json={
                    "message": current_user_message,
                    "max_tokens": ai_max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "speed_mode": True,   # ← OPTIMIZED: Enable speed mode for faster responses
                    "ultra_speed": True    # ← NEW: Enable ultra-speed mode for maximum performance
                },
                cookies={"session_id": session_cookie},
                auth=(settings.ai_model_auth_username, settings.ai_model_auth_password)
            )
            
            if chat_response.status_code != 200:
                # Enhanced error logging for integration debugging
                error_detail = f"AI model request failed: {chat_response.status_code}"
                try:
                    error_data = chat_response.json()
                    if 'detail' in error_data:
                        error_detail += f" - {error_data['detail']}"
                except:
                    error_detail += f" - {chat_response.text}"
                
                logger.error(f"❌ AI Server Integration Error: {error_detail}")
                logger.error(f"📤 Request sent: message='{current_user_message[:100]}...', max_tokens={ai_max_tokens}, temperature=0.7, top_p=0.9")
                
                # Check for common integration issues
                if chat_response.status_code == 422:
                    logger.error("❌ Validation Error: AI server rejected request parameters")
                elif chat_response.status_code == 500:
                    logger.error("❌ AI Server Error: Internal server error")
                elif chat_response.status_code == 404:
                    logger.error("❌ AI Server Error: Endpoint not found")
                
                raise Exception(error_detail)
            
            response_data = chat_response.json()
            raw_response = response_data.get("response", "I'm sorry, I couldn't generate a response.")
            
            # Clean the response to extract only the AI's response
            cleaned_response = clean_ai_response(raw_response)
            logger.info(f"Raw AI response: {raw_response[:200]}...")
            logger.info(f"Cleaned AI response: {cleaned_response[:200]}...")
            
            return cleaned_response
            
    except Exception as e:
        raise Exception(f"AI model call failed: {str(e)}")

def clean_ai_response(raw_response: str) -> str:
    """
    Clean the AI response to extract only the AI's actual response,
    removing any conversation formatting, ChatML tags, or echoed user messages.
    """
    try:
        import re
        
        # First, remove ALL ChatML tags from anywhere in the response
        cleaned_response = re.sub(r'<\|[\w]+\|>', '', raw_response)
        
        # Split by common conversation markers
        lines = cleaned_response.split('\n')
        ai_response_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Stop if we encounter user message markers or AI processing notes
            if any(marker in line.lower() for marker in ['< |user|', '<|user|', 'user:', '<!assistant!>', '<|assistant|>', '<!---', '-|assistent|>', '<!--', '-->']):
                break
                
            # Skip lines that look like conversation formatting (these shouldn't appear anymore)
            if line.startswith(('User:', 'AI:', 'Assistant:', 'Human:')):
                continue
                
            ai_response_lines.append(line)
        
        # Join the cleaned lines
        cleaned_response = '\n'.join(ai_response_lines).strip()
        
        # Clean up any extra whitespace that might be left
        cleaned_response = re.sub(r'\n\s*\n', '\n', cleaned_response)  # Remove empty lines
        cleaned_response = re.sub(r'^\s+', '', cleaned_response)  # Remove leading whitespace
        cleaned_response = re.sub(r'\s+$', '', cleaned_response)  # Remove trailing whitespace
        
        # If we got nothing, return the original (fallback)
        if not cleaned_response:
            # Try to extract everything before the first user marker or processing note
            user_markers = ['< |user|', '<|user|', '<!assistant!>', '<|assistant|>', '<!---', '-|assistent|>', '<!--', '-->']
            for marker in user_markers:
                if marker in raw_response:
                    cleaned_response = raw_response.split(marker)[0].strip()
                    break
            
            # If still nothing, return original
            if not cleaned_response:
                cleaned_response = raw_response
        
        return cleaned_response
        
    except Exception as e:
        logger.warning(f"Error cleaning AI response: {e}, returning original")
        return raw_response

@celery_app.task
def cleanup_expired_sessions():
    """
    Cleanup expired admin sessions
    """
    try:
        db = SessionLocal()
        from database import AdminSession
        
        # Delete expired sessions
        expired_sessions = db.query(AdminSession).filter(
            AdminSession.expires_at < datetime.now(timezone.utc)
        ).all()
        
        for session in expired_sessions:
            db.delete(session)
        
        db.commit()
        db.close()
        
        return f"Cleaned up {len(expired_sessions)} expired sessions"
        
    except Exception as e:
        return f"Cleanup failed: {str(e)}"

# Periodic task to cleanup expired sessions (run every hour)
celery_app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'celery_app.cleanup_expired_sessions',
        'schedule': 3600.0,  # Every hour
    },
}
celery_app.conf.timezone = 'UTC'