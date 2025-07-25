from celery import Celery
import httpx
import asyncio
from config import settings
from database import SessionLocal, Message, ChatSession, User
from datetime import datetime, timezone
import uuid

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
        
        # Call AI model API
        ai_response = call_ai_model(chat_session.scenario_prompt, history, max_tokens)
        
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
            return response_data.get("response", "I'm sorry, I couldn't generate a response.")
            
    except Exception as e:
        raise Exception(f"AI model call failed: {str(e)}")

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