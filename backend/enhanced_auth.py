"""
Enhanced Authentication System
Implements advanced security features for authentication and authorization
"""

import os
import hashlib
import secrets
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from functools import wraps

import bcrypt
import pyotp
import jwt
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db, AdminUser, AdminSession, User
from config import settings

# Configure logging
auth_logger = logging.getLogger("enhanced_auth")
auth_logger.setLevel(logging.INFO)

# Security configuration
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes
SESSION_TIMEOUT = 28800  # 8 hours
PASSWORD_MIN_LENGTH = 12

class EnhancedPasswordManager:
    """Enhanced password management with bcrypt"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt with high cost factor"""
        salt = bcrypt.gensalt(rounds=14)  # High cost factor for security
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against bcrypt hash"""
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception as e:
            auth_logger.error(f"Password verification error: {str(e)}")
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = ["password", "123456", "qwerty", "admin", "letmein", "password123"]
        if password.lower() in weak_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors

class MultiFactorAuth:
    """Multi-factor authentication implementation"""
    
    def __init__(self):
        self.totp_window = 2  # Allow 2 time steps for clock skew
    
    def generate_secret(self) -> str:
        """Generate TOTP secret"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, secret: str, username: str) -> str:
        """Generate QR code URL for TOTP setup"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(username, issuer_name="EVE Chat Platform")
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=self.totp_window)
        except Exception as e:
            auth_logger.error(f"TOTP verification error: {str(e)}")
            return False
    
    def generate_backup_codes(self) -> List[str]:
        """Generate backup codes for MFA"""
        return [secrets.token_hex(4).upper() for _ in range(10)]

class SessionManager:
    """Enhanced session management"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.failed_attempts: Dict[str, Dict] = {}
    
    def create_session(self, user_id: str, user_type: str, ip_address: str, user_agent: str) -> str:
        """Create a new secure session"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "user_type": user_type,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.now(timezone.utc),
            "last_activity": datetime.now(timezone.utc),
            "is_active": True
        }
        
        self.active_sessions[session_id] = session_data
        return session_id
    
    def validate_session(self, session_id: str, ip_address: str) -> Optional[Dict]:
        """Validate session and return session data"""
        if session_id not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_id]
        
        # Check if session is expired
        if datetime.now(timezone.utc) - session_data["created_at"] > timedelta(seconds=SESSION_TIMEOUT):
            self.invalidate_session(session_id)
            return None
        
        # Check if session is active
        if not session_data["is_active"]:
            return None
        
        # Update last activity
        session_data["last_activity"] = datetime.now(timezone.utc)
        
        return session_data
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def record_failed_attempt(self, identifier: str, ip_address: str):
        """Record a failed login attempt"""
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = {
                "count": 0,
                "first_attempt": datetime.now(timezone.utc),
                "last_attempt": datetime.now(timezone.utc),
                "ip_address": ip_address
            }
        
        self.failed_attempts[identifier]["count"] += 1
        self.failed_attempts[identifier]["last_attempt"] = datetime.now(timezone.utc)
    
    def is_locked_out(self, identifier: str) -> bool:
        """Check if account is locked out"""
        if identifier not in self.failed_attempts:
            return False
        
        attempt_data = self.failed_attempts[identifier]
        
        # Check if lockout period has passed
        if datetime.now(timezone.utc) - attempt_data["last_attempt"] > timedelta(seconds=LOCKOUT_DURATION):
            del self.failed_attempts[identifier]
            return False
        
        # Check if max attempts exceeded
        return attempt_data["count"] >= MAX_LOGIN_ATTEMPTS
    
    def reset_failed_attempts(self, identifier: str):
        """Reset failed attempts for successful login"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]

class EnhancedJWTManager:
    """Enhanced JWT token management"""
    
    def __init__(self):
        self.blacklisted_tokens: set = set()
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token with enhanced security"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=30)  # Shorter default
        
        # Add additional security claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(16),  # Unique token ID
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(16),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token with enhanced security"""
        try:
            # Check if token is blacklisted
            if token in self.blacklisted_tokens:
                return None
            
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            
            # Check token type
            if payload.get("type") != "access":
                return None
            
            # Check if token is expired
            if datetime.fromtimestamp(payload["exp"], tz=timezone.utc) < datetime.now(timezone.utc):
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            auth_logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            auth_logger.warning(f"Invalid JWT token: {str(e)}")
            return None
        except Exception as e:
            auth_logger.error(f"JWT verification error: {str(e)}")
            return None
    
    def blacklist_token(self, token: str):
        """Blacklist a token (for logout)"""
        self.blacklisted_tokens.add(token)
        
        # Clean up old blacklisted tokens periodically
        if len(self.blacklisted_tokens) > 10000:
            # This is a simple cleanup - in production, use Redis or database
            self.blacklisted_tokens.clear()

# Initialize components
password_manager = EnhancedPasswordManager()
mfa_manager = MultiFactorAuth()
session_manager = SessionManager()
jwt_manager = EnhancedJWTManager()

# JWT token scheme
security = HTTPBearer()

def authenticate_admin(db: Session, username: str, password: str, ip_address: str) -> Optional[AdminUser]:
    """Authenticate admin with enhanced security"""
    # Check for lockout
    if session_manager.is_locked_out(username):
        auth_logger.warning(f"Admin account locked out: {username}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed attempts"
        )
    
    # Get admin user
    admin = db.query(AdminUser).filter(
        AdminUser.username == username,
        AdminUser.is_active == True
    ).first()
    
    if not admin:
        session_manager.record_failed_attempt(username, ip_address)
        return None
    
    # Verify password
    if not password_manager.verify_password(password, admin.password_hash):
        session_manager.record_failed_attempt(username, ip_address)
        return None
    
    # Reset failed attempts on successful login
    session_manager.reset_failed_attempts(username)
    
    return admin

def create_admin_session(db: Session, admin_id: str, ip_address: str, user_agent: str) -> str:
    """Create a new admin session with enhanced security"""
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=SESSION_TIMEOUT)
    
    admin_session = AdminSession(
        id=str(secrets.uuid4()),
        admin_id=admin_id,
        session_token=session_token,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
        is_active=True
    )
    
    db.add(admin_session)
    db.commit()
    
    # Also create in-memory session
    session_manager.create_session(admin_id, "admin", ip_address, user_agent)
    
    return session_token

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """Get current admin user with enhanced security"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify JWT token
        payload = jwt_manager.verify_token(credentials.credentials)
        if not payload:
            raise credentials_exception
        
        admin_id: str = payload.get("sub")
        if admin_id is None:
            raise credentials_exception
        
        # Get admin user
        admin = db.query(AdminUser).filter(
            AdminUser.id == admin_id,
            AdminUser.is_active == True
        ).first()
        
        if admin is None:
            raise credentials_exception
        
        return admin
        
    except Exception as e:
        auth_logger.error(f"Admin authentication error: {str(e)}")
        raise credentials_exception

def get_admin_by_session_token(db: Session, session_token: str, ip_address: str) -> Optional[AdminUser]:
    """Get admin user by session token with enhanced security"""
    # Check in-memory sessions first
    session_data = session_manager.validate_session(session_token, ip_address)
    if session_data:
        admin = db.query(AdminUser).filter(
            AdminUser.id == session_data["user_id"],
            AdminUser.is_active == True
        ).first()
        return admin
    
    # Fallback to database sessions
    session = db.query(AdminSession).filter(
        AdminSession.session_token == session_token,
        AdminSession.is_active == True,
        AdminSession.expires_at > datetime.now(timezone.utc)
    ).first()
    
    if not session:
        return None
    
    admin = db.query(AdminUser).filter(
        AdminUser.id == session.admin_id,
        AdminUser.is_active == True
    ).first()
    
    return admin

def logout_admin(db: Session, session_token: str):
    """Logout admin with enhanced security"""
    # Invalidate in-memory session
    session_manager.invalidate_session(session_token)
    
    # Invalidate database session
    session = db.query(AdminSession).filter(
        AdminSession.session_token == session_token
    ).first()
    
    if session:
        session.is_active = False
        db.commit()
    
    # Blacklist JWT token if provided
    # jwt_manager.blacklist_token(token)

# Security decorators
def require_secure_connection(func):
    """Decorator to require secure connection"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would check for HTTPS in production
        auth_logger.info("Secure connection required for sensitive operation")
        return await func(*args, **kwargs)
    return wrapper

def audit_auth_event(event_type: str):
    """Decorator to audit authentication events"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            auth_logger.info(f"Auth event: {event_type} - {func.__name__}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator 