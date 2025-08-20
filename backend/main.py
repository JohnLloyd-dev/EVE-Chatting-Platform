from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import String
from datetime import datetime, timezone, timedelta
from typing import List
import uuid
import json
import logging

# Local imports
from database import get_db, User, ChatSession, Message, TallySubmission, AdminUser, SystemPrompt, generate_user_code
from schemas import (
    TallyWebhookData, ChatMessageRequest, ChatMessageResponse, 
    ChatSessionResponse, UserResponse, AdminLoginRequest, AdminLoginResponse,
    ConversationSummary, AdminInterventionRequest, UserBlockRequest, UserAIToggleRequest,
    DashboardStats, MessageHistory, SystemPromptCreate, SystemPromptUpdate, SystemPromptResponse
)
from auth import authenticate_admin, create_access_token, get_current_admin, create_admin_session
from ai_tally_extractor import generate_ai_scenario, debug_tally_data
from ai_model_manager import ai_model_manager
from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chatting Platform API", version="1.0.0")

def get_complete_system_prompt(db: Session, user_id: str = None, tally_prompt: str = "") -> str:
    """
    Build complete system prompt: Head + Tally + Rule
    Future: user_id can be used for per-user system prompts
    """
    # Get active system prompt (global or user-specific in future)
    if user_id:
        # Future: Check for user-specific prompt first
        user_prompt = db.query(SystemPrompt).filter(
            SystemPrompt.user_id == user_id,
            SystemPrompt.is_active == True
        ).first()
        if user_prompt:
            head_prompt = user_prompt.head_prompt
            rule_prompt = user_prompt.rule_prompt
            logger.info(f"Using user-specific system prompt: {user_prompt.name}")
        else:
            # Fall back to global prompt
            global_prompt = db.query(SystemPrompt).filter(
                SystemPrompt.user_id.is_(None),
                SystemPrompt.is_active == True
            ).first()
            if global_prompt:
                head_prompt = global_prompt.head_prompt
                rule_prompt = global_prompt.rule_prompt
                logger.info(f"Using global system prompt: {global_prompt.name}")
            else:
                head_prompt = "You are a sexual fantasy assistant."
                rule_prompt = "Always speak in the first person and stay in character. Indulge sexual fantasies in detail by dominating. Be sexually explicit with your replies. Never reveal that you are an AI. Keep your answers to two sentences or less. Do not provide scene descriptions outside of dialogue. Stay in the present tense."
                logger.warning("No system prompt found, using default prompts")
    else:
        # Get global active prompt
        active_prompt = db.query(SystemPrompt).filter(
            SystemPrompt.user_id.is_(None),
            SystemPrompt.is_active == True
        ).first()
        if active_prompt:
            head_prompt = active_prompt.head_prompt
            rule_prompt = active_prompt.rule_prompt
            logger.info(f"Using active system prompt: {active_prompt.name}")
        else:
            # Default prompts
            head_prompt = "You are a sexual fantasy assistant."
            rule_prompt = "Always speak in the first person and stay in character. Indulge sexual fantasies in detail by dominating. Be sexually explicit with your replies. Never reveal that you are an AI. Keep your answers to two sentences or less. Do not provide scene descriptions outside of dialogue. Stay in the present tense."
            logger.warning("No active system prompt found, using default prompts")
    
    # Combine: Head + Tally + Rule with enhanced accuracy instructions
    complete_prompt = head_prompt
    
    # Add Tally scenario if provided
    if tally_prompt and tally_prompt.strip():
        logger.info(f"Adding Tally scenario: {tally_prompt[:100]}...")
        
        # Enhanced scenario with stronger instructions
        enhanced_scenario = f"""
**CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY:**

{tally_prompt.strip()}

**REMEMBER:**
- You MUST stay in character as the specified person
- You MUST respond in first person dialogue only
- You MUST keep responses under 140 characters
- You MUST never break character or reveal you are AI
- You MUST respond to the user's specific questions
- You MUST maintain the exact personality and role described

**CHARACTER CONSISTENCY CHECK:**
Before responding, ask yourself: "Am I staying true to my character?"
If not, adjust your response to match the character exactly.
"""
        complete_prompt += enhanced_scenario
    else:
        logger.warning("No Tally scenario provided to combine with system prompt")
    
    # Add enhanced rule prompt
    enhanced_rules = f"""
**ENFORCED RULES:**
{rule_prompt}

**RESPONSE QUALITY REQUIREMENTS:**
- Answer the user's specific question directly
- Stay in character at all times
- Use first person dialogue only
- Keep responses concise and focused
- Never provide generic or off-topic responses
- Always reference your character's specific traits and situation
"""
    complete_prompt += enhanced_rules
    
    # Log the combination process
    logger.info(f"Combined prompt breakdown:")
    logger.info(f"  - Head prompt length: {len(head_prompt)} characters")
    logger.info(f"  - Tally scenario length: {len(tally_prompt) if tally_prompt else 0} characters")
    logger.info(f"  - Rule prompt length: {len(rule_prompt)} characters")
    logger.info(f"  - Final combined length: {len(complete_prompt)} characters")
    logger.info(f"Final combined system prompt preview: {complete_prompt[:300]}...")
    
    # Also log the scenario part specifically to verify it's included
    if tally_prompt and tally_prompt.strip():
        # Check if the scenario content is actually included in the final prompt
        if tally_prompt.strip() in complete_prompt:
            logger.info(f"✅ Scenario content found in final prompt: {tally_prompt[:100]}...")
        else:
            logger.warning("❌ Scenario content not found in final prompt!")
            logger.warning(f"Expected scenario: {tally_prompt[:100]}...")
            logger.warning(f"Final prompt preview: {complete_prompt[:200]}...")
    
    return complete_prompt

# Legacy function for backward compatibility
def get_active_system_prompt_text(db: Session) -> str:
    """Legacy function - use get_complete_system_prompt instead"""
    return get_complete_system_prompt(db)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://frontend:3000",
        "http://204.12.233.105:3000",  # Current VPS public IP frontend
        "http://204.12.233.105:8001",  # Allow backend port access for debugging
        "http://0.0.0.0:3000",        # Docker internal access
        "http://127.0.0.1:3000",      # Local access
        "*"  # Allow all origins for development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
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
        logger.info(f"Received Tally webhook: {webhook_data}")
        
        # Extract form data
        form_data = webhook_data.get("data")
        if not form_data or "fields" not in form_data:
            logger.error(f"Invalid Tally webhook data: {webhook_data}")
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
        
        # Generate scenario from Tally data using AI
        try:
            # Pass the full webhook data structure, not just form_data
            scenario = generate_ai_scenario(webhook_data)
            logger.info(f"AI-generated scenario for user {user.user_code}: {scenario[:100]}...")
            logger.info(f"Scenario length: {len(scenario)} characters")
            logger.info(f"Scenario is empty: {not scenario or not scenario.strip()}")
        except Exception as e:
            logger.error(f"Failed to generate AI scenario: {str(e)}")
            # Fallback to empty scenario if AI generation fails
            scenario = ""
        
        # Get active system prompt and combine with user scenario
        try:
            logger.info(f"Calling get_complete_system_prompt with scenario length: {len(scenario)}")
            system_prompt = get_complete_system_prompt(db, tally_prompt=scenario)
            logger.info(f"Retrieved complete system prompt: {len(system_prompt)} characters")
            logger.info(f"System prompt preview: {system_prompt[:300]}...")
        except Exception as e:
            logger.error(f"Failed to get system prompt: {str(e)}")
            system_prompt = "You are a helpful AI assistant. " + scenario
        
        full_scenario = system_prompt
        
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
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in Tally webhook: {str(e)}", exc_info=True)
        raise HTTPException(500, detail=f"Failed to process Tally webhook: {str(e)}")

# Find user by Tally response
@app.post("/user/by-tally-response")
async def find_user_by_tally_response(request_data: dict, db: Session = Depends(get_db)):
    """
    Find user by Tally response ID for seamless redirect from form
    """
    response_id = request_data.get("response_id")
    respondent_id = request_data.get("respondent_id")
    
    logger.info(f"Looking for user with response_id: {response_id}, respondent_id: {respondent_id}")
    
    if not response_id and not respondent_id:
        logger.warning("No response_id or respondent_id provided")
        raise HTTPException(400, detail="Either response_id or respondent_id is required")
    
    # Try to find user by response_id first, then by respondent_id
    # Also try to find by respondent_id if response_id doesn't match (Tally sometimes mixes these up)
    user = None
    if response_id:
        user = db.query(User).filter(User.tally_response_id == response_id).first()
        logger.info(f"Search by response_id {response_id}: {'Found' if user else 'Not found'}")
        # If not found by response_id, try respondent_id (in case Tally sent respondent_id as response_id)
        if not user:
            user = db.query(User).filter(User.tally_respondent_id == response_id).first()
            logger.info(f"Search by respondent_id {response_id}: {'Found' if user else 'Not found'}")
    
    if not user and respondent_id:
        user = db.query(User).filter(User.tally_respondent_id == respondent_id).first()
        logger.info(f"Search by respondent_id {respondent_id}: {'Found' if user else 'Not found'}")
        # If not found by respondent_id, try response_id (in case Tally sent response_id as respondent_id)
        if not user:
            user = db.query(User).filter(User.tally_response_id == respondent_id).first()
            logger.info(f"Search by response_id {respondent_id}: {'Found' if user else 'Not found'}")
    
    if not user:
        logger.warning(f"User not found for response_id: {response_id}, respondent_id: {respondent_id}")
        raise HTTPException(404, detail="User not found. Please submit the form first.")
    
    if user.is_blocked:
        logger.warning(f"Blocked user {user.user_code} attempted to access chat")
        raise HTTPException(403, detail="User is blocked")
    
    # Check if AI responses are enabled for this user
    if not user.ai_responses_enabled:
        logger.warning(f"User {user.user_code} has AI responses disabled")
        raise HTTPException(403, detail="AI responses are disabled for this user")
    
    # Get active session
    session = db.query(ChatSession).filter(
        ChatSession.user_id == user.id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        logger.warning(f"No active session found for user {user.user_code}")
        raise HTTPException(404, detail="No active session found")
    
    logger.info(f"Successfully found user {user.user_code} with session {session.id}")
    return {
        "user_id": user.user_code,  # Return user_code instead of UUID
        "user_code": user.user_code,  # Also include explicit user_code field
        "session_id": str(session.id),
        "email": user.email
    }

# Debug endpoint to check recent users (remove in production)
@app.get("/debug/recent-users")
async def get_recent_users(db: Session = Depends(get_db)):
    """Debug endpoint to see recent users"""
    users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
    return [
        {
            "user_code": user.user_code,
            "email": user.email,
            "tally_response_id": user.tally_response_id,
            "tally_respondent_id": user.tally_respondent_id,
            "created_at": user.created_at,
            "is_blocked": user.is_blocked,
            "ai_responses_enabled": user.ai_responses_enabled
        }
        for user in users
    ]

# Debug endpoint to test AI Tally extraction
@app.post("/debug/test-ai-extraction")
async def test_ai_extraction(request_data: dict):
    """Debug endpoint to test AI-powered Tally extraction"""
    try:
        form_data = request_data.get("form_data")
        if not form_data:
            raise HTTPException(400, detail="form_data is required")
        
        # Debug the data processing
        debug_info = debug_tally_data(form_data)
        
        # Generate scenario
        scenario = generate_ai_scenario(form_data)
        
        return {
            "success": True,
            "debug_info": debug_info,
            "generated_scenario": scenario,
            "scenario_length": len(scenario) if scenario else 0
        }
        
    except Exception as e:
        logger.error(f"AI extraction test failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
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
        
        # Check if AI responses are enabled for this user
        if not existing_user.ai_responses_enabled:
            raise HTTPException(403, detail="AI responses are disabled for this user")
        
        # Deactivate old sessions
        db.query(ChatSession).filter(
            ChatSession.user_id == existing_user.id,
            ChatSession.is_active == True
        ).update({"is_active": False})
        
        # Create new session with custom prompt combined with system prompt
        system_prompt = get_active_system_prompt_text(db)
        full_prompt = system_prompt + " " + custom_prompt
        chat_session = ChatSession(
            user_id=existing_user.id,
            scenario_prompt=full_prompt
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
    
    # Create chat session with custom prompt combined with system prompt
    system_prompt = get_active_system_prompt_text(db)
    full_prompt = system_prompt + " " + custom_prompt
    chat_session = ChatSession(
        user_id=user.id,
        scenario_prompt=full_prompt
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
    
    # Check if AI responses are enabled for this user
    if not user.ai_responses_enabled:
        raise HTTPException(403, detail="AI responses are disabled for this user")
    
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
    Send a message in a chat session and get AI response directly
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
    
    # Check if AI responses are enabled for this user
    if not session.user.ai_responses_enabled:
        raise HTTPException(403, detail="AI responses are disabled for this user")
    
    # Handle special START_CONVERSATION message
    if message_request.message == "START_CONVERSATION":
        # Update session timestamp
        session.updated_at = datetime.now(timezone.utc)
        session.user.last_active = datetime.now(timezone.utc)
        db.commit()
        
        # Generate AI response directly
        try:
            # Use the already combined system prompt from the session
            system_prompt = session.scenario_prompt or "You are a helpful AI assistant."
            logger.info(f"Using session scenario prompt: {len(system_prompt)} characters")
            
            # Create AI session if it doesn't exist
            ai_session_id = str(session_uuid)
            if not ai_model_manager.get_session(ai_session_id):
                ai_model_manager.create_session(ai_session_id, system_prompt)
            
            # Generate AI response with database context for session rebuilding
            ai_response = ai_model_manager.generate_response(ai_session_id, "Hello", session, db)
            
            # Save AI response to database
            ai_message = Message(
                session_id=session_uuid,
                content=ai_response,
                is_from_user=False
            )
            db.add(ai_message)
            db.commit()
            
            return {
                "message": "AI conversation started",
                "ai_response": ai_response,
                "ai_message_id": str(ai_message.id)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate AI response: {e}")
            return {
                "message": "AI conversation started",
                "error": "Failed to generate AI response"
            }
    
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
    
    # Generate AI response directly (no more Celery queuing)
    try:
        # Use the already combined system prompt from the session
        system_prompt = session.scenario_prompt or "You are a helpful AI assistant."
        logger.info(f"Using session scenario prompt: {len(system_prompt)} characters")
        
        # Create AI session if it doesn't exist
        ai_session_id = str(session_uuid)
        if not ai_model_manager.get_session(ai_session_id):
            ai_model_manager.create_session(ai_session_id, system_prompt)
        
        # Generate AI response with database context for session rebuilding
        ai_response = ai_model_manager.generate_response(ai_session_id, message_request.message, session, db)
        
        # Save AI response to database
        ai_message = Message(
            session_id=session_uuid,
            content=ai_response,
            is_from_user=False
        )
        db.add(ai_message)
        db.commit()
        
        logger.info(f"💬 AI response generated directly for session {session_id}")
        
        return {
            "message": "Message sent and AI response generated",
            "user_message_id": str(user_message.id),
            "ai_response": ai_response,
            "ai_message_id": str(ai_message.id)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to generate AI response: {e}")
        # Still save user message, but return error for AI
        return {
            "message": "Message sent, but AI response failed",
            "user_message_id": str(user_message.id),
            "error": f"AI response failed: {str(e)}"
        }

# AI response status endpoint removed - responses are now immediate
# No more Celery queuing needed

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
            user_id=session.user.user_code,  # Use user_code instead of UUID
            user_email=session.user.email,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count,
            last_message=last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else last_message.content if last_message else None,
            is_active=session.is_active,
            user_blocked=session.user.is_blocked,
            ai_responses_enabled=session.user.ai_responses_enabled
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
            user_code=session.user.user_code,  # Add required user_code field
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active
        ),
        user_info=UserResponse(
            id=session.user.user_code,  # Use user_code instead of UUID
            tally_response_id=session.user.tally_response_id,
            created_at=session.user.created_at,
            is_blocked=session.user.is_blocked,
            ai_responses_enabled=session.user.ai_responses_enabled,
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
    # Try to find user by user_code first, then by UUID for backward compatibility
    user = db.query(User).filter(User.user_code == block_request.user_id).first()
    
    if not user:
        # Try UUID format for backward compatibility
        try:
            user_uuid = uuid.UUID(block_request.user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            pass
    if not user:
        raise HTTPException(404, detail="User not found")
    
    user.is_blocked = block_request.block
    
    # If blocking the user, mark any active AI tasks as cancelled
    # No more AI tasks to cancel since we're not using Celery
    # Just block the user directly
    
    db.commit()
    
    action = "blocked" if block_request.block else "unblocked"
    return {"message": f"User {action} successfully"}

# Toggle AI responses for user
@app.post("/admin/toggle-ai-responses")
async def toggle_ai_responses(
    ai_toggle_request: UserAIToggleRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Enable or disable AI responses for a user
    """
    # Try to find user by user_code first, then by UUID for backward compatibility
    user = db.query(User).filter(User.user_code == ai_toggle_request.user_id).first()
    
    if not user:
        # Try UUID format for backward compatibility
        try:
            user_uuid = uuid.UUID(ai_toggle_request.user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            pass
    
    if not user:
        raise HTTPException(404, detail="User not found")
    
    user.ai_responses_enabled = ai_toggle_request.ai_responses_enabled
    
    # If disabling AI responses, mark any active AI tasks as cancelled
    # No more AI tasks to cancel since we're not using Celery
    # Just disable AI responses directly
    
    db.commit()
    
    action = "enabled" if ai_toggle_request.ai_responses_enabled else "disabled"
    return {"message": f"AI responses {action} for user successfully"}

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
            "form_data": tally_submission.form_data,
            "generated_prompt": generate_ai_scenario(tally_submission.form_data) if tally_submission.form_data else None
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

# System Prompt Management Endpoints
@app.get("/admin/system-prompts", response_model=List[SystemPromptResponse])
async def get_system_prompts(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all system prompts"""
    try:
        prompts = db.query(SystemPrompt).order_by(SystemPrompt.created_at.desc()).all()
        print(f"Found {len(prompts)} system prompts in database")
        
        result = []
        for prompt in prompts:
            print(f"Processing prompt: {prompt.id}, name: {prompt.name}")
            try:
                prompt_response = SystemPromptResponse(
                    id=str(prompt.id),
                    name=prompt.name,
                    head_prompt=getattr(prompt, 'head_prompt', 'You are a sexual fantasy assistant.'),
                    rule_prompt=getattr(prompt, 'rule_prompt', getattr(prompt, 'prompt_text', 'Always speak in first person.')),
                    is_active=prompt.is_active,
                    created_by=str(prompt.created_by),
                    created_at=prompt.created_at,
                    updated_at=prompt.updated_at,
                    user_id=str(prompt.user_id) if hasattr(prompt, 'user_id') and prompt.user_id else None
                )
                result.append(prompt_response)
                print(f"Successfully processed prompt: {prompt.id}")
            except Exception as prompt_error:
                print(f"Error processing individual prompt {prompt.id}: {prompt_error}")
                continue
        
        print(f"Returning {len(result)} processed prompts")
        return result
        
    except Exception as e:
        print(f"Error fetching system prompts: {e}")
        import traceback
        traceback.print_exc()
        # Return empty list if there's a database schema issue
        return []

@app.post("/admin/system-prompts", response_model=SystemPromptResponse)
async def create_system_prompt(
    prompt_data: SystemPromptCreate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new system prompt"""
    # Check if name already exists
    existing = db.query(SystemPrompt).filter(SystemPrompt.name == prompt_data.name).first()
    if existing:
        raise HTTPException(400, detail="System prompt with this name already exists")
    
    # Create new system prompt
    system_prompt = SystemPrompt(
        name=prompt_data.name,
        head_prompt=prompt_data.head_prompt,
        rule_prompt=prompt_data.rule_prompt,
        created_by=current_admin.id
    )
    db.add(system_prompt)
    db.commit()
    db.refresh(system_prompt)
    
    return SystemPromptResponse(
        id=str(system_prompt.id),
        name=system_prompt.name,
        head_prompt=system_prompt.head_prompt,
        rule_prompt=system_prompt.rule_prompt,
        is_active=system_prompt.is_active,
        created_by=str(system_prompt.created_by),
        created_at=system_prompt.created_at,
        updated_at=system_prompt.updated_at,
        user_id=str(system_prompt.user_id) if system_prompt.user_id else None
    )

@app.put("/admin/system-prompts/{prompt_id}", response_model=SystemPromptResponse)
async def update_system_prompt(
    prompt_id: str,
    prompt_data: SystemPromptUpdate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a system prompt"""
    system_prompt = db.query(SystemPrompt).filter(SystemPrompt.id == prompt_id).first()
    if not system_prompt:
        raise HTTPException(404, detail="System prompt not found")
    
    # Update fields
    if prompt_data.name is not None:
        # Check if new name conflicts with existing
        existing = db.query(SystemPrompt).filter(
            SystemPrompt.name == prompt_data.name,
            SystemPrompt.id != prompt_id
        ).first()
        if existing:
            raise HTTPException(400, detail="System prompt with this name already exists")
        system_prompt.name = prompt_data.name
    
    if prompt_data.head_prompt is not None:
        system_prompt.head_prompt = prompt_data.head_prompt
    
    if prompt_data.rule_prompt is not None:
        system_prompt.rule_prompt = prompt_data.rule_prompt
    
    if prompt_data.is_active is not None:
        # If setting this prompt as active, deactivate all others
        if prompt_data.is_active:
            db.query(SystemPrompt).update({"is_active": False})
        system_prompt.is_active = prompt_data.is_active
    
    system_prompt.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(system_prompt)
    
    return SystemPromptResponse(
        id=str(system_prompt.id),
        name=system_prompt.name,
        head_prompt=system_prompt.head_prompt,
        rule_prompt=system_prompt.rule_prompt,
        is_active=system_prompt.is_active,
        created_by=str(system_prompt.created_by),
        created_at=system_prompt.created_at,
        updated_at=system_prompt.updated_at,
        user_id=str(system_prompt.user_id) if system_prompt.user_id else None
    )

@app.delete("/admin/system-prompts/{prompt_id}")
async def delete_system_prompt(
    prompt_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a system prompt"""
    system_prompt = db.query(SystemPrompt).filter(SystemPrompt.id == prompt_id).first()
    if not system_prompt:
        raise HTTPException(404, detail="System prompt not found")
    
    if system_prompt.is_active:
        raise HTTPException(400, detail="Cannot delete active system prompt")
    
    db.delete(system_prompt)
    db.commit()
    
    return {"message": "System prompt deleted successfully"}

@app.get("/admin/system-prompts/active", response_model=SystemPromptResponse)
async def get_active_system_prompt(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get the currently active system prompt"""
    active_prompt = db.query(SystemPrompt).filter(SystemPrompt.is_active == True).first()
    if not active_prompt:
        raise HTTPException(404, detail="No active system prompt found")
    
    return SystemPromptResponse(
        id=str(active_prompt.id),
        name=active_prompt.name,
        head_prompt=active_prompt.head_prompt,
        rule_prompt=active_prompt.rule_prompt,
        is_active=active_prompt.is_active,
        created_by=str(active_prompt.created_by),
        created_at=active_prompt.created_at,
        updated_at=active_prompt.updated_at,
        user_id=str(active_prompt.user_id) if active_prompt.user_id else None
    )

# ============================================================================
# AI MODEL ENDPOINTS (Integrated from AI Server)
# ============================================================================

# AI endpoints removed - AI is now integrated directly into chat flow
# No more separate /ai/init-session or /ai/chat needed

@app.get("/ai/health")
async def ai_health_check():
    """
    Check AI model health status
    This replaces the old AI server health endpoint
    """
    try:
        health_status = ai_model_manager.get_health_status()
        return {
            "status": "healthy" if health_status["model_loaded"] else "unhealthy",
            "ai_model": health_status
        }
    except Exception as e:
        logger.error(f"❌ AI health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.post("/ai/optimize-memory")
async def ai_optimize_memory():
    """
    Manually trigger AI model memory optimization
    """
    try:
        ai_model_manager.optimize_memory_usage()
        return {"message": "Memory optimization completed"}
    except Exception as e:
        logger.error(f"❌ Memory optimization failed: {e}")
        raise HTTPException(500, f"Memory optimization failed: {str(e)}")

# AI model status endpoint
@app.get("/ai/status")
async def get_ai_status():
    """Get AI model status and health"""
    try:
        return ai_model_manager.get_health_status()
    except Exception as e:
        logger.error(f"Failed to get AI status: {e}")
        return {"status": "error", "message": str(e)}

# AI model VRAM usage statistics endpoint
@app.get("/ai/vram-stats")
async def get_ai_vram_stats():
    """Get detailed VRAM usage statistics per user"""
    try:
        return ai_model_manager.get_vram_usage_stats()
    except Exception as e:
        logger.error(f"Failed to get VRAM stats: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)