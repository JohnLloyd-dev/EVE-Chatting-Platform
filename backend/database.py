from sqlalchemy import create_engine, Column, String, Text, Boolean, DateTime, ForeignKey, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
import uuid
from config import settings

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_code = Column(String(20), unique=True, nullable=False)  # Simple memorable ID like EVE001, EVE002
    tally_response_id = Column(String(255), unique=True, nullable=True)  # Made nullable for device-based users
    tally_respondent_id = Column(String(255), nullable=True)  # Made nullable for device-based users
    tally_form_id = Column(String(255), nullable=True)  # Made nullable for device-based users
    device_id = Column(String(255), unique=True, nullable=True)  # For device-based identification
    user_type = Column(String(50), default="tally")  # "tally" or "device"
    email = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_blocked = Column(Boolean, default=False)
    ai_responses_enabled = Column(Boolean, default=True)  # Control AI responses separately from blocking
    last_active = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    tally_submissions = relationship("TallySubmission", back_populates="user", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scenario_prompt = Column(Text, nullable=False)
    ai_session_id = Column(String(255), nullable=True)  # Store AI model session ID for reuse
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_from_user = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_admin_intervention = Column(Boolean, default=False)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id"), nullable=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    admin = relationship("AdminUser", foreign_keys=[admin_id])

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    admin_sessions = relationship("AdminSession", back_populates="admin", cascade="all, delete-orphan")

class AdminSession(Base):
    __tablename__ = "admin_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    admin = relationship("AdminUser", back_populates="admin_sessions")

class TallySubmission(Base):
    __tablename__ = "tally_submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    form_data = Column(JSONB, nullable=False)
    processed_scenario = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="tally_submissions")

class SystemPrompt(Base):
    __tablename__ = "system_prompts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    head_prompt = Column(Text, nullable=False)  # System instructions
    rule_prompt = Column(Text, nullable=False)  # Behavioral rules
    is_active = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("admin_users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Future: For per-user system prompts
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # NULL = global prompt
    
    # Relationships
    admin = relationship("AdminUser")
    user = relationship("User", backref="custom_system_prompts")

class ActiveAITask(Base):
    __tablename__ = "active_ai_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(255), unique=True, nullable=False)  # Celery task ID
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_cancelled = Column(Boolean, default=False)
    
    # Relationships
    session = relationship("ChatSession")
    user = relationship("User")

def generate_user_code(db: SessionLocal) -> str:
    """
    Generate a simple, memorable user code like EVE001, EVE002, etc.
    """
    # Get the highest existing user code number
    latest_user = db.query(User).filter(
        User.user_code.like('EVE%')
    ).order_by(User.user_code.desc()).first()
    
    if latest_user and latest_user.user_code:
        try:
            # Extract number from code like EVE001 -> 1
            current_num = int(latest_user.user_code[3:])
            next_num = current_num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1
    
    # Format as EVE001, EVE002, etc.
    return f"EVE{next_num:03d}"

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()