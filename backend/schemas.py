from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Tally webhook schemas
class TallyWebhookData(BaseModel):
    eventId: str
    eventType: str
    createdAt: datetime
    data: Dict[str, Any]

# Chat schemas
class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    max_tokens: int = Field(150, ge=10, le=500)

class ChatMessageResponse(BaseModel):
    id: str
    content: str
    is_from_user: bool
    created_at: datetime
    is_admin_intervention: bool = False

class ChatSessionResponse(BaseModel):
    id: str
    user_code: str  # Add user_code to response
    created_at: datetime
    updated_at: datetime
    is_active: bool
    messages: List[ChatMessageResponse] = []

# User schemas
class UserResponse(BaseModel):
    id: str
    tally_response_id: str
    created_at: datetime
    is_blocked: bool
    last_active: datetime
    email: Optional[str] = None

# Admin schemas
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_id: str
    username: str

class AdminUserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime
    is_active: bool

# Admin dashboard schemas
class ConversationSummary(BaseModel):
    session_id: str
    user_id: str
    user_email: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message: Optional[str]
    is_active: bool
    user_blocked: bool

class AdminInterventionRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=1000)

class UserBlockRequest(BaseModel):
    user_id: str
    block: bool = True

# Statistics schemas
class DashboardStats(BaseModel):
    total_users: int
    active_sessions: int
    total_messages: int
    blocked_users: int
    messages_today: int
    new_users_today: int

# Message history for admin
class MessageHistory(BaseModel):
    messages: List[ChatMessageResponse]
    session_info: ChatSessionResponse
    user_info: UserResponse

# System Prompt schemas
class SystemPromptCreate(BaseModel):
    name: str
    head_prompt: str
    rule_prompt: str

class SystemPromptUpdate(BaseModel):
    name: Optional[str] = None
    head_prompt: Optional[str] = None
    rule_prompt: Optional[str] = None
    is_active: Optional[bool] = None

class SystemPromptResponse(BaseModel):
    id: str
    name: str
    head_prompt: str
    rule_prompt: str
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None  # For future per-user prompts

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str
        }