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
        
        # Use the integrated AI model manager instead of external AI server
        logger.info("🤖 Using integrated AI model manager...")
        
        try:
            # Get the AI session
            ai_session = ai_model_manager.get_session(str(session_id))
            if not ai_session:
                # Create new session if it doesn't exist
                ai_session = ai_model_manager.create_session(str(session_id), system_prompt)
                logger.info(f"✅ Created new AI session: {session_id}")
            else:
                logger.info(f"✅ Using existing AI session: {session_id}")
            
            # Add user message to AI session
            ai_model_manager.add_user_message(str(session_id), user_message)
            
            # Generate AI response using the integrated model
            logger.info("🚀 Generating AI response with integrated model...")
            ai_response = ai_model_manager.generate_response(
                str(session_id), 
                user_message, 
                max_tokens=200, 
                temperature=0.7
            )
            
            logger.info(f"✅ AI response generated: {len(ai_response)} characters")
            return ai_response
            
        except Exception as ai_error:
            logger.error(f"❌ Integrated AI model error: {ai_error}")
            raise Exception(f"AI model generation failed: {str(ai_error)}")
            
            # Get the current user message (last in history)
            current_user_message = None
            # Since we're alternating between user and AI messages, the last message should be the user's
            if history and len(history) > 0:
                current_user_message = history[-1]  # Last message is the user's
            
            # The integrated AI model manager already handled the response generation above
            # This section is no longer needed since we're using the integrated approach
            pass
            
    except Exception as e:
        raise Exception(f"AI model call failed: {str(e)}")

# clean_ai_response function removed - no longer needed with integrated AI model

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