from celery import Celery
import httpx
import asyncio
from config import settings
from database import SessionLocal, Message, ChatSession, User, SystemPrompt
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
)

@celery_app.task(bind=True, max_retries=3)
def process_ai_response(self, session_id: str, user_message: str, max_tokens: int = 150):
    """
    Process AI response asynchronously
    """
    try:
        # Get database session
        db = SessionLocal()
        
        # Get chat session
        chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            raise Exception(f"Chat session {session_id} not found")
        
        # Check if user is blocked
        if chat_session.user.is_blocked:
            raise Exception("User is blocked")
        
        # Get conversation history
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at).all()
        
        # Build conversation history for AI
        history = []
        for msg in messages:
            if msg.is_from_user:
                history.append(f"User: {msg.content}")
            else:
                history.append(f"AI: {msg.content}")
        
        # Add current user message
        history.append(f"User: {user_message}")
        
        # Use the session's scenario_prompt which already contains the complete combined prompt
        # This was built in main.py using: head_prompt + tally_prompt + rule_prompt
        combined_prompt = chat_session.scenario_prompt
        logger.info(f"Using session scenario prompt (already contains head + tally + rule)")
        logger.info(f"Session scenario prompt length: {len(combined_prompt)} characters")
        logger.info(f"Session scenario preview: {combined_prompt[:300]}...")
        
        # Call AI model API
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
        
        # Retry logic
        if self.request.retries < self.max_retries:
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
    """
    try:
        # Log the system prompt being sent for debugging
        logger.info(f"Sending system prompt to AI model: {system_prompt[:200]}...")
        
        # Prepare the request similar to your main.py structure
        with httpx.Client(timeout=30.0) as client:
            # First set the scenario
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
            
            # Get the last user message
            last_user_message = None
            for msg in reversed(history):
                if msg.startswith("User: "):
                    last_user_message = msg[6:]  # Remove "User: " prefix
                    break
            
            if not last_user_message:
                raise Exception("No user message found in history")
            
            # Send chat request
            chat_response = client.post(
                f"{settings.ai_model_url}/chat",
                json={
                    "message": last_user_message,
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