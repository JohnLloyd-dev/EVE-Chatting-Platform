from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import hashlib
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db, AdminUser, AdminSession
from config import settings
import uuid

# Simple password hashing (fallback for bcrypt issues)
def create_simple_hash(password: str) -> str:
    """Create a simple but secure hash for the password"""
    salt = "chatting_platform_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_simple_hash(password: str, hashed: str) -> bool:
    """Verify password against simple hash"""
    salt = "chatting_platform_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest() == hashed

# JWT token scheme
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using simple hash method"""
    return verify_simple_hash(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash using simple hash method"""
    return create_simple_hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def authenticate_admin(db: Session, username: str, password: str) -> Optional[AdminUser]:
    admin = db.query(AdminUser).filter(
        AdminUser.username == username,
        AdminUser.is_active == True
    ).first()
    
    if not admin or not verify_password(password, admin.password_hash):
        return None
    return admin

def create_admin_session(db: Session, admin_id: str) -> str:
    """Create a new admin session and return session token"""
    session_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=8)  # 8 hour sessions
    
    admin_session = AdminSession(
        admin_id=admin_id,
        session_token=session_token,
        expires_at=expires_at
    )
    
    db.add(admin_session)
    db.commit()
    
    return session_token

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """Get current admin user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        admin_id: str = payload.get("sub")
        if admin_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if admin is None or not admin.is_active:
        raise credentials_exception
    
    return admin

def get_admin_by_session_token(db: Session, session_token: str) -> Optional[AdminUser]:
    """Get admin user by session token"""
    session = db.query(AdminSession).filter(
        AdminSession.session_token == session_token,
        AdminSession.is_active == True,
        AdminSession.expires_at > datetime.now(timezone.utc)
    ).first()
    
    if not session:
        return None
    
    return session.admin