from celery import Celery
import httpx
import asyncio
from config import settings
from database import SessionLocal, Message, ChatSession, User, SystemPrompt, ActiveAITask
from datetime import datetime, timezone
import uuid
import logging

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
)

@celery_app.task(bind=True, max_retries=3)
def process_ai_response(self, session_id: str, user_message: str, max_tokens: int = 150, is_ai_initiated: bool = False):
    """
    Process AI response asynchronously
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
        
        # Build conversation history for AI
        history = []
        for msg in messages:
            if msg.is_from_user:
                history.append(f"User: {msg.content}")
            else:
                history.append(f"AI: {msg.content}")
        
        # Handle AI-initiated messages differently
        if is_ai_initiated:
            # For AI-initiated messages, don't add to history as user message
            # Just use the message as the AI's intended response
            ai_response = user_message  # "hi" in this case
        else:
            # Add current user message
            history.append(f"User: {user_message}")
            
            # Call AI model API with full conversation history
            combined_prompt = chat_session.scenario_prompt
            logger.info(f"Using session scenario prompt (already contains head + tally + rule)")
            logger.info(f"Session scenario prompt length: {len(combined_prompt)} characters")
            logger.info(f"Session scenario preview: {combined_prompt[:300]}...")
            
            # Call AI model API - will create new session with full context
            ai_response = call_ai_model(combined_prompt, history, max_tokens)
        
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
        
        # Retry logic only for recoverable errors
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task {self.request.id}, attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=60, exc=exc)
        
        # If all retries failed, save error message
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
        except:
            pass
        
        return {
            "success": False,
            "error": str(exc)
        }

def call_ai_model(system_prompt: str, history: list, max_tokens: int = 150) -> str:
    """
    Call the AI model API (your VPS deployment)
    Always creates new AI session with full conversation history for context
    """
    try:
        # Log the system prompt being sent for debugging
        logger.info(f"Sending system prompt to AI model: {system_prompt[:200]}...")
        logger.info(f"Building context with {len(history)} messages from database")
        
        # Prepare the request similar to your main.py structure
        with httpx.Client(timeout=30.0) as client:
            # Always create new AI session (simpler and more reliable)
            logger.info("Creating new AI session with full conversation context...")
            scenario_response = client.post(
                f"{settings.ai_model_url}/scenario",
                json={"scenario": system_prompt},
                auth=(settings.ai_model_auth_username, settings.ai_model_auth_password)
            )
            
            if scenario_response.status_code != 200:
                raise Exception(f"Failed to set scenario: {scenario_response.text}")
            
            # Get session cookie
            session_cookie = scenario_response.cookies.get("session_id")
            if not session_cookie:
                raise Exception("No session ID received from AI model")
            
            logger.info(f"Created AI session: {session_cookie}")
            
            # Build conversation context by sending all previous messages
            # This ensures the AI has full conversation history even after restarts
            if len(history) > 1:  # If we have more than just the current user message
                logger.info("Building conversation context...")
                context_messages = history[:-1]  # All messages except the current one
                
                for i, msg in enumerate(context_messages):
                    try:
                        # Send each message to build context (with minimal tokens)
                        context_response = client.post(
                            f"{settings.ai_model_url}/chat",
                            json={
                                "message": msg,
                                "max_tokens": 5  # Just enough to process, not generate response
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
            for msg in reversed(history):
                if msg.startswith("User: "):
                    current_user_message = msg[6:]  # Remove "User: " prefix
                    break
            
            if not current_user_message:
                raise Exception("No current user message found in history")
            
            logger.info(f"Sending current user message: {current_user_message[:100]}...")
            
            # Send the actual user message and get AI response
            chat_response = client.post(
                f"{settings.ai_model_url}/chat",
                json={
                    "message": current_user_message,
                    "max_tokens": max_tokens
                },
                cookies={"session_id": session_cookie},
                auth=(settings.ai_model_auth_username, settings.ai_model_auth_password)
            )
            
            if chat_response.status_code != 200:
                raise Exception(f"AI model request failed: {chat_response.text}")
            
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
    removing any conversation formatting or echoed user messages.
    """
    try:
        # Split by common conversation markers
        lines = raw_response.split('\n')
        ai_response_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Stop if we encounter user message markers or AI processing notes
            if any(marker in line.lower() for marker in ['< |user|', '<|user|', 'user:', '<!assistant!>', '<|assistant|>', '<!---', '-|assistent|>', '<!--', '-->']):
                break
                
            # Skip lines that look like conversation formatting
            if line.startswith(('User:', 'AI:', 'Assistant:', 'Human:')):
                continue
                
            ai_response_lines.append(line)
        
        # Join the cleaned lines
        cleaned_response = '\n'.join(ai_response_lines).strip()
        
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