from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import String
from datetime import datetime, timezone, timedelta
from typing import List
import uuid
import json

# Local imports
from database import get_db, User, ChatSession, Message, TallySubmission, AdminUser, generate_user_code
from schemas import (
    TallyWebhookData, ChatMessageRequest, ChatMessageResponse, 
    ChatSessionResponse, UserResponse, AdminLoginRequest, AdminLoginResponse,
    ConversationSummary, AdminInterventionRequest, UserBlockRequest,
    DashboardStats, MessageHistory
)
from auth import authenticate_admin, create_access_token, get_current_admin, create_admin_session
from extract_tally import generate_story_from_json
from celery_app import process_ai_response
from config import settings

app = FastAPI(title="Chatting Platform API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://frontend:3000",
        "http://204.12.223.76:3000"  # VPS public IP frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

# Tally webhook endpoint
@app.post("/webhook/tally")
async def tally_webhook(webhook_data: dict, db: Session = Depends(get_db)):
    """
    Receive Tally form submissions and create user sessions
    """
    try:
        # Extract form data
        form_data = webhook_data.get("data")
        if not form_data or "fields" not in form_data:
            raise HTTPException(400, detail="Invalid Tally webhook data")
        
        response_id = form_data.get("responseId")
        respondent_id = form_data.get("respondentId")
        form_id = form_data.get("formId")
        
        if not all([response_id, respondent_id, form_id]):
            raise HTTPException(400, detail="Missing required Tally form data")
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            User.tally_response_id == response_id
        ).first()
        
        if existing_user:
            return {"message": "User already exists", "user_id": str(existing_user.id)}
        
        # Extract email if available
        email = None
        for field in form_data.get("fields", []):
            if field.get("type") == "EMAIL" and field.get("value"):
                email = field["value"]
                break
        
        # Create new user
        user_code = generate_user_code(db)
        user = User(
            user_code=user_code,
            tally_response_id=response_id,
            tally_respondent_id=respondent_id,
            tally_form_id=form_id,
            email=email
        )
        db.add(user)
        db.flush()  # Get user ID
        
        # Generate scenario from Tally data
        scenario = generate_story_from_json(form_data)
        full_scenario = (
            "You are sexual fantasy Assistant. " + scenario + 
            " Rules: 1) Always speak in the first person and always stay in character. "
            "2) Indulge my sexual fantasies in detail by dominating me. "
            "3) Be sexually explicit with your replies "
            "4) Never reveal that you are an AI "
            "5) Keep your answers to two sentences or less "
            "6) Do not provide scene descriptions outside of dialogue "
            "7) Stay in the present tense"
        )
        
        # Create chat session
        chat_session = ChatSession(
            user_id=user.id,
            scenario_prompt=full_scenario
        )
        db.add(chat_session)
        
        # Store Tally submission data
        tally_submission = TallySubmission(
            user_id=user.id,
            form_data=form_data,
            processed_scenario=full_scenario
        )
        db.add(tally_submission)
        
        db.commit()
        
        return {
            "message": "User created and chat session initialized",
            "user_id": user.user_code,  # Return user_code instead of UUID
            "user_code": user.user_code,  # Also include explicit user_code field
            "session_id": str(chat_session.id)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, detail=f"Failed to process Tally webhook: {str(e)}")

# Find user by Tally response
@app.post("/user/by-tally-response")
async def find_user_by_tally_response(request_data: dict, db: Session = Depends(get_db)):
    """
    Find user by Tally response ID for seamless redirect from form
    """
    response_id = request_data.get("response_id")
    respondent_id = request_data.get("respondent_id")
    
    if not response_id and not respondent_id:
        raise HTTPException(400, detail="Either response_id or respondent_id is required")
    
    # Try to find user by response_id first, then by respondent_id
    # Also try to find by respondent_id if response_id doesn't match (Tally sometimes mixes these up)
    user = None
    if response_id:
        user = db.query(User).filter(User.tally_response_id == response_id).first()
        # If not found by response_id, try respondent_id (in case Tally sent respondent_id as response_id)
        if not user:
            user = db.query(User).filter(User.tally_respondent_id == response_id).first()
    
    if not user and respondent_id:
        user = db.query(User).filter(User.tally_respondent_id == respondent_id).first()
        # If not found by respondent_id, try response_id (in case Tally sent response_id as respondent_id)
        if not user:
            user = db.query(User).filter(User.tally_response_id == respondent_id).first()
    
    if not user:
        raise HTTPException(404, detail="User not found. Please submit the form first.")
    
    if user.is_blocked:
        raise HTTPException(403, detail="User is blocked")
    
    # Get active session
    session = db.query(ChatSession).filter(
        ChatSession.user_id == user.id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(404, detail="No active session found")
    
    return {
        "user_id": user.user_code,  # Return user_code instead of UUID
        "user_code": user.user_code,  # Also include explicit user_code field
        "session_id": str(session.id),
        "email": user.email
    }

# Device-based session creation for testing
@app.post("/user/device-session")
async def create_device_session(request_data: dict, db: Session = Depends(get_db)):
    """
    Create or get a device-based user session for testing purposes
    """
    device_id = request_data.get("device_id")
    custom_prompt = request_data.get("custom_prompt")
    
    if not device_id:
        raise HTTPException(400, detail="device_id is required")
    
    if not custom_prompt:
        raise HTTPException(400, detail="custom_prompt is required")
    
    # Check if device-based user already exists
    existing_user = db.query(User).filter(
        User.device_id == device_id,
        User.user_type == "device"
    ).first()
    
    if existing_user:
        # Check if user is blocked
        if existing_user.is_blocked:
            raise HTTPException(403, detail="User is blocked")
        
        # Deactivate old sessions
        db.query(ChatSession).filter(
            ChatSession.user_id == existing_user.id,
            ChatSession.is_active == True
        ).update({"is_active": False})
        
        # Create new session with custom prompt
        chat_session = ChatSession(
            user_id=existing_user.id,
            scenario_prompt=custom_prompt
        )
        db.add(chat_session)
        
        # Update user's last active time
        existing_user.last_active = datetime.now(timezone.utc)
        
        db.commit()
        
        return {
            "user_id": str(existing_user.id),
            "session_id": str(chat_session.id),
            "message": "New session created for existing device user"
        }
    
    # Create new device-based user
    user_code = generate_user_code(db)
    user = User(
        user_code=user_code,
        device_id=device_id,
        user_type="device"
    )
    db.add(user)
    db.flush()  # Get user ID
    
    # Create chat session with custom prompt
    chat_session = ChatSession(
        user_id=user.id,
        scenario_prompt=custom_prompt
    )
    db.add(chat_session)
    
    db.commit()
    
    return {
        "user_id": user.user_code,  # Return user_code instead of UUID
        "user_code": user.user_code,  # Also include explicit user_code field
        "session_id": str(chat_session.id),
        "message": "Device user and session created successfully"
    }

# Get user session
@app.get("/chat/session/{user_id}", response_model=ChatSessionResponse)
async def get_user_session(user_id: str, db: Session = Depends(get_db)):
    """
    Get user's active chat session
    """
    # Try to find user by user_code first, then by UUID for backward compatibility
    user = db.query(User).filter(User.user_code == user_id).first()
    
    if not user:
        # Try UUID format for backward compatibility
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            pass
    
    if not user:
        raise HTTPException(404, detail="User not found")
    
    if user.is_blocked:
        raise HTTPException(403, detail="User is blocked")
    
    # Get active session
    session = db.query(ChatSession).filter(
        ChatSession.user_id == user.id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(404, detail="No active session found")
    
    # Get messages
    messages = db.query(Message).filter(
        Message.session_id == session.id
    ).order_by(Message.created_at).all()
    
    message_responses = [
        ChatMessageResponse(
            id=str(msg.id),
            content=msg.content,
            is_from_user=msg.is_from_user,
            created_at=msg.created_at,
            is_admin_intervention=msg.is_admin_intervention
        ) for msg in messages
    ]
    
    return ChatSessionResponse(
        id=str(session.id),
        user_code=user.user_code,  # Include user_code in response
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_active=session.is_active,
        messages=message_responses
    )

# Send message
@app.post("/chat/message/{session_id}")
async def send_message(
    session_id: str, 
    message_request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message in a chat session
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid session ID format")
    
    # Get session
    session = db.query(ChatSession).filter(
        ChatSession.id == session_uuid,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(404, detail="Session not found")
    
    if session.user.is_blocked:
        raise HTTPException(403, detail="User is blocked")
    
    # Save user message
    user_message = Message(
        session_id=session_uuid,
        content=message_request.message,
        is_from_user=True
    )
    db.add(user_message)
    
    # Update session timestamp
    session.updated_at = datetime.now(timezone.utc)
    session.user.last_active = datetime.now(timezone.utc)
    
    db.commit()
    
    # Queue AI response processing
    task = process_ai_response.delay(
        str(session_uuid), 
        message_request.message, 
        message_request.max_tokens
    )
    
    return {
        "message": "Message sent, AI response is being processed",
        "user_message_id": str(user_message.id),
        "task_id": task.id
    }

# Get AI response status
@app.get("/chat/response/{task_id}")
async def get_ai_response_status(task_id: str):
    """
    Check the status of AI response processing
    """
    from celery_app import celery_app
    
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        return {"status": "processing", "message": "AI is thinking..."}
    elif task.state == 'SUCCESS':
        return {"status": "completed", "result": task.result}
    elif task.state == 'FAILURE':
        return {"status": "failed", "error": str(task.info)}
    else:
        return {"status": task.state}

# Admin login
@app.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(login_request: AdminLoginRequest, db: Session = Depends(get_db)):
    """
    Admin login endpoint
    """
    admin = authenticate_admin(db, login_request.username, login_request.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(admin.id)}, expires_delta=access_token_expires
    )
    
    return AdminLoginResponse(
        access_token=access_token,
        admin_id=str(admin.id),
        username=admin.username
    )

# Admin dashboard - get all conversations
@app.get("/admin/conversations", response_model=List[ConversationSummary])
async def get_all_conversations(
    skip: int = 0,
    limit: int = 50,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all conversations for admin dashboard
    """
    sessions = db.query(ChatSession).join(User).order_by(
        ChatSession.updated_at.desc()
    ).offset(skip).limit(limit).all()
    
    conversations = []
    for session in sessions:
        # Get message count
        message_count = db.query(Message).filter(
            Message.session_id == session.id
        ).count()
        
        # Get last message
        last_message = db.query(Message).filter(
            Message.session_id == session.id
        ).order_by(Message.created_at.desc()).first()
        
        conversations.append(ConversationSummary(
            session_id=str(session.id),
            user_id=str(session.user.id),
            user_email=session.user.email,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count,
            last_message=last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else last_message.content if last_message else None,
            is_active=session.is_active,
            user_blocked=session.user.is_blocked
        ))
    
    return conversations

# Admin - get conversation details
@app.get("/admin/conversation/{session_id}", response_model=MessageHistory)
async def get_conversation_details(
    session_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get detailed conversation history for admin
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid session ID format")
    
    session = db.query(ChatSession).filter(ChatSession.id == session_uuid).first()
    if not session:
        raise HTTPException(404, detail="Session not found")
    
    # Get all messages
    messages = db.query(Message).filter(
        Message.session_id == session_uuid
    ).order_by(Message.created_at).all()
    
    message_responses = [
        ChatMessageResponse(
            id=str(msg.id),
            content=msg.content,
            is_from_user=msg.is_from_user,
            created_at=msg.created_at,
            is_admin_intervention=msg.is_admin_intervention
        ) for msg in messages
    ]
    
    return MessageHistory(
        messages=message_responses,
        session_info=ChatSessionResponse(
            id=str(session.id),
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active
        ),
        user_info=UserResponse(
            id=str(session.user.id),
            tally_response_id=session.user.tally_response_id,
            created_at=session.user.created_at,
            is_blocked=session.user.is_blocked,
            last_active=session.user.last_active,
            email=session.user.email
        )
    )

# Admin intervention
@app.post("/admin/intervene")
async def admin_intervene(
    intervention: AdminInterventionRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Admin can send a message in a conversation
    """
    try:
        session_uuid = uuid.UUID(intervention.session_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid session ID format")
    
    session = db.query(ChatSession).filter(ChatSession.id == session_uuid).first()
    if not session:
        raise HTTPException(404, detail="Session not found")
    
    # Create admin intervention message
    admin_message = Message(
        session_id=session_uuid,
        content=intervention.message,
        is_from_user=False,
        is_admin_intervention=True,
        admin_id=admin.id
    )
    db.add(admin_message)
    
    # Update session timestamp
    session.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return {"message": "Admin intervention sent", "message_id": str(admin_message.id)}

# Block/unblock user
@app.post("/admin/block-user")
async def block_user(
    block_request: UserBlockRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Block or unblock a user
    """
    try:
        user_uuid = uuid.UUID(block_request.user_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid user ID format")
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(404, detail="User not found")
    
    user.is_blocked = block_request.block
    db.commit()
    
    action = "blocked" if block_request.block else "unblocked"
    return {"message": f"User {action} successfully"}

# Dashboard statistics
@app.get("/admin/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics
    """
    today = datetime.now(timezone.utc).date()
    
    total_users = db.query(User).count()
    active_sessions = db.query(ChatSession).filter(ChatSession.is_active == True).count()
    total_messages = db.query(Message).count()
    blocked_users = db.query(User).filter(User.is_blocked == True).count()
    
    messages_today = db.query(Message).filter(
        Message.created_at >= datetime.combine(today, datetime.min.time().replace(tzinfo=timezone.utc))
    ).count()
    
    new_users_today = db.query(User).filter(
        User.created_at >= datetime.combine(today, datetime.min.time().replace(tzinfo=timezone.utc))
    ).count()
    
    return DashboardStats(
        total_users=total_users,
        active_sessions=active_sessions,
        total_messages=total_messages,
        blocked_users=blocked_users,
        messages_today=messages_today,
        new_users_today=new_users_today
    )

# User Management Endpoints
@app.get("/admin/users")
async def get_users(
    skip: int = 0,
    limit: int = 50,
    search: str = None,
    user_type: str = None,
    is_blocked: bool = None,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Get paginated list of users with filtering options
    """
    query = db.query(User)
    
    # Apply filters
    if search:
        search_filter = (User.id.cast(String).ilike(f"%{search}%"))
        if search:  # Add user_code search
            search_filter = search_filter | (User.user_code.ilike(f"%{search}%"))
        if search:  # Add email search if email is not null
            search_filter = search_filter | (User.email.ilike(f"%{search}%"))
        if search:  # Add tally_response_id search if not null
            search_filter = search_filter | (User.tally_response_id.ilike(f"%{search}%"))
        if search:  # Add device_id search if not null
            search_filter = search_filter | (User.device_id.ilike(f"%{search}%"))
        query = query.filter(search_filter)
    
    if user_type:
        query = query.filter(User.user_type == user_type)
    
    if is_blocked is not None:
        query = query.filter(User.is_blocked == is_blocked)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    # Get additional stats for each user
    user_data = []
    for user in users:
        # Get session count
        session_count = db.query(ChatSession).filter(ChatSession.user_id == user.id).count()
        
        # Get message count
        message_count = db.query(Message).join(ChatSession).filter(
            ChatSession.user_id == user.id
        ).count()
        
        # Get last session
        last_session = db.query(ChatSession).filter(
            ChatSession.user_id == user.id
        ).order_by(ChatSession.updated_at.desc()).first()
        
        user_data.append({
            "id": user.id,
            "user_code": user.user_code,
            "email": user.email,
            "tally_response_id": user.tally_response_id,
            "tally_respondent_id": user.tally_respondent_id,
            "device_id": user.device_id,
            "user_type": user.user_type,
            "is_blocked": user.is_blocked,
            "created_at": user.created_at,
            "last_active": user.last_active,
            "session_count": session_count,
            "message_count": message_count,
            "last_session_at": last_session.updated_at if last_session else None
        })
    
    return {
        "users": user_data,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@app.get("/admin/users/{user_id}")
async def get_user_details(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Get detailed information about a specific user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's sessions
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).order_by(ChatSession.created_at.desc()).all()
    
    # Get user's messages
    messages = db.query(Message).join(ChatSession).filter(
        ChatSession.user_id == user_id
    ).order_by(Message.created_at.desc()).limit(50).all()
    
    # Get Tally submission if exists
    tally_submission = None
    if user.tally_response_id:
        tally_submission = db.query(TallySubmission).filter(
            TallySubmission.user_id == user_id
        ).first()
    
    return {
        "user": {
            "id": user.id,
            "user_code": user.user_code,
            "email": user.email,
            "tally_response_id": user.tally_response_id,
            "tally_respondent_id": user.tally_respondent_id,
            "device_id": user.device_id,
            "user_type": user.user_type,
            "is_blocked": user.is_blocked,
            "created_at": user.created_at,
            "last_active": user.last_active
        },
        "sessions": [
            {
                "id": session.id,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "is_active": session.is_active,
                "message_count": db.query(Message).filter(Message.session_id == session.id).count()
            }
            for session in sessions
        ],
        "recent_messages": [
            {
                "id": message.id,
                "content": message.content,
                "is_from_user": message.is_from_user,
                "created_at": message.created_at,
                "session_id": message.session_id
            }
            for message in messages
        ],
        "tally_submission": {
            "form_id": user.tally_form_id,
            "response_id": user.tally_response_id,
            "respondent_id": user.tally_respondent_id,
            "submitted_at": tally_submission.created_at,
            "form_data": tally_submission.form_data
        } if tally_submission else None
    }

@app.put("/admin/users/{user_id}/block")
async def toggle_user_block(
    user_id: str,
    block_data: dict,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Block or unblock a user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_blocked = block_data.get("is_blocked", True)
    user.is_blocked = is_blocked
    
    # If blocking, deactivate all active sessions
    if is_blocked:
        db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        ).update({"is_active": False})
    
    db.commit()
    
    return {
        "message": f"User {'blocked' if is_blocked else 'unblocked'} successfully",
        "user_id": user_id,
        "is_blocked": is_blocked
    }

@app.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Delete a user and all associated data
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete user's messages
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
    for session in sessions:
        db.query(Message).filter(Message.session_id == session.id).delete()
    
    # Delete user's sessions
    db.query(ChatSession).filter(ChatSession.user_id == user_id).delete()
    
    # Delete Tally submission if exists
    db.query(TallySubmission).filter(
        TallySubmission.user_id == user_id
    ).delete()
    
    # Delete user
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully", "user_id": user_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)