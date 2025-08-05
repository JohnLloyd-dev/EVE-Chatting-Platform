"""
Security module for the EVE Chat Platform
Implements comprehensive security measures including:
- Query allowlisting
- Input validation and sanitization
- SQL injection prevention
- Security logging
- Rate limiting
"""

import re
import logging
import hashlib
import secrets
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from functools import wraps
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure security logging
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.WARNING)

# Security configuration
SECURITY_CONFIG = {
    "max_query_length": 1000,
    "max_input_length": 5000,
    "rate_limit_requests": 100,
    "rate_limit_window": 60,  # seconds
    "blocked_patterns": [
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|vbscript|onload|onerror|onclick)\b)",
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|vbscript|onload|onerror|onclick)\b)",
        r"(--|/\*|\*/|xp_|sp_|@@|0x[0-9a-fA-F]+)",
        r"(<script|javascript:|vbscript:|onload=|onerror=|onclick=)",
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|vbscript|onload|onerror|onclick)\b)",
    ],
    "allowed_query_patterns": [
        r"^SELECT\s+.*\s+FROM\s+\w+\s*$",
        r"^INSERT\s+INTO\s+\w+\s+VALUES\s*\(.*\)\s*$",
        r"^UPDATE\s+\w+\s+SET\s+.*\s+WHERE\s+.*\s*$",
        r"^DELETE\s+FROM\s+\w+\s+WHERE\s+.*\s*$",
        r"^SELECT\s+COUNT\s*\(\s*\*\s*\)\s+FROM\s+\w+\s*$",
    ]
}

class SecurityViolation(Exception):
    """Custom exception for security violations"""
    pass

class QueryAllowlist:
    """Query allowlisting system to prevent unauthorized SQL operations"""
    
    def __init__(self):
        self.allowed_queries = {
            # User queries
            "get_user_by_id": "SELECT * FROM users WHERE id = %s",
            "get_user_by_email": "SELECT * FROM users WHERE email = %s",
            "get_user_by_tally_id": "SELECT * FROM users WHERE tally_response_id = %s",
            "create_user": "INSERT INTO users (id, tally_response_id, tally_respondent_id, tally_form_id, email, created_at, is_blocked, user_code, device_id, user_type, ai_responses_enabled) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            "update_user_last_active": "UPDATE users SET last_active = %s WHERE id = %s",
            "block_user": "UPDATE users SET is_blocked = %s WHERE id = %s",
            "toggle_ai_responses": "UPDATE users SET ai_responses_enabled = %s WHERE id = %s",
            
            # Chat session queries
            "get_chat_session": "SELECT * FROM chat_sessions WHERE id = %s",
            "get_user_chat_sessions": "SELECT * FROM chat_sessions WHERE user_id = %s ORDER BY created_at DESC",
            "create_chat_session": "INSERT INTO chat_sessions (id, user_id, scenario_prompt, created_at, updated_at, is_active) VALUES (%s, %s, %s, %s, %s, %s)",
            "update_chat_session": "UPDATE chat_sessions SET updated_at = %s, is_active = %s WHERE id = %s",
            
            # Message queries
            "get_session_messages": "SELECT * FROM messages WHERE session_id = %s ORDER BY created_at ASC",
            "create_message": "INSERT INTO messages (id, session_id, content, is_from_user, created_at, is_admin_intervention, admin_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            
            # Admin queries
            "get_admin_by_username": "SELECT * FROM admin_users WHERE username = %s",
            "get_admin_by_id": "SELECT * FROM admin_users WHERE id = %s",
            "create_admin_session": "INSERT INTO admin_sessions (id, admin_id, session_token, created_at, expires_at, is_active) VALUES (%s, %s, %s, %s, %s, %s)",
            "get_admin_session": "SELECT * FROM admin_sessions WHERE session_token = %s AND is_active = true AND expires_at > %s",
            
            # System prompt queries
            "get_active_system_prompt": "SELECT * FROM system_prompts WHERE is_active = true AND user_id IS NULL LIMIT 1",
            "get_user_system_prompt": "SELECT * FROM system_prompts WHERE user_id = %s AND is_active = true LIMIT 1",
            "get_all_system_prompts": "SELECT * FROM system_prompts ORDER BY created_at DESC",
            "create_system_prompt": "INSERT INTO system_prompts (id, name, head_prompt, rule_prompt, is_active, created_by, created_at, updated_at, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            "update_system_prompt": "UPDATE system_prompts SET name = %s, head_prompt = %s, rule_prompt = %s, is_active = %s, updated_at = %s WHERE id = %s",
            "delete_system_prompt": "DELETE FROM system_prompts WHERE id = %s",
            
            # Tally submission queries
            "create_tally_submission": "INSERT INTO tally_submissions (id, user_id, form_data, processed_scenario, created_at) VALUES (%s, %s, %s, %s, %s)",
            "get_user_tally_submissions": "SELECT * FROM tally_submissions WHERE user_id = %s ORDER BY created_at DESC",
            
            # AI task queries
            "create_ai_task": "INSERT INTO active_ai_tasks (id, task_id, session_id, user_id, created_at, is_cancelled) VALUES (%s, %s, %s, %s, %s, %s)",
            "get_ai_task": "SELECT * FROM active_ai_tasks WHERE task_id = %s",
            "cancel_ai_task": "UPDATE active_ai_tasks SET is_cancelled = true WHERE task_id = %s",
            
            # Statistics queries
            "get_user_count": "SELECT COUNT(*) FROM users",
            "get_message_count": "SELECT COUNT(*) FROM messages",
            "get_session_count": "SELECT COUNT(*) FROM chat_sessions",
            "get_recent_users": "SELECT * FROM users ORDER BY created_at DESC LIMIT %s",
            "get_conversation_stats": "SELECT COUNT(*) as message_count, MIN(created_at) as first_message, MAX(created_at) as last_message FROM messages WHERE session_id = %s"
        }
    
    def get_query(self, query_name: str) -> str:
        """Get an allowed query by name"""
        if query_name not in self.allowed_queries:
            raise SecurityViolation(f"Query '{query_name}' not in allowlist")
        return self.allowed_queries[query_name]
    
    def validate_query(self, query: str) -> bool:
        """Validate if a query matches allowed patterns"""
        query = query.strip().upper()
        for pattern in SECURITY_CONFIG["allowed_query_patterns"]:
            if re.match(pattern, query, re.IGNORECASE):
                return True
        return False

class InputValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID format"""
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, uuid_str.lower()))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def validate_length(value: str, max_length: int = None) -> bool:
        """Validate string length"""
        if max_length is None:
            max_length = SECURITY_CONFIG["max_input_length"]
        return len(value) <= max_length
    
    @staticmethod
    def sanitize_input(value: str) -> str:
        """Basic input sanitization (use parameterized queries instead)"""
        if not isinstance(value, str):
            return str(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Truncate if too long
        if len(value) > SECURITY_CONFIG["max_input_length"]:
            value = value[:SECURITY_CONFIG["max_input_length"]]
        
        return value
    
    @staticmethod
    def check_malicious_patterns(value: str) -> bool:
        """Check for malicious patterns in input"""
        value_lower = value.lower()
        for pattern in SECURITY_CONFIG["blocked_patterns"]:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False

class SecureDatabase:
    """Secure database operations with parameterized queries"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.allowlist = QueryAllowlist()
        self.validator = InputValidator()
    
    def execute_query(self, query_name: str, params: tuple = None) -> Any:
        """Execute a query from the allowlist with parameters"""
        try:
            # Get allowed query
            query = self.allowlist.get_query(query_name)
            
            # Validate parameters
            if params:
                for param in params:
                    if isinstance(param, str):
                        if self.validator.check_malicious_patterns(param):
                            raise SecurityViolation(f"Malicious pattern detected in parameter: {param}")
                        if not self.validator.validate_length(param):
                            raise SecurityViolation(f"Parameter too long: {len(param)} characters")
            
            # Execute with parameterized query
            result = self.db.execute(text(query), params or {})
            return result
            
        except Exception as e:
            security_logger.error(f"Database security error: {str(e)}")
            raise SecurityViolation(f"Database operation failed: {str(e)}")
    
    def get_user_by_id(self, user_id: str):
        """Get user by ID with validation"""
        if not self.validator.validate_uuid(user_id):
            raise SecurityViolation("Invalid UUID format")
        return self.execute_query("get_user_by_id", (user_id,))
    
    def get_user_by_email(self, email: str):
        """Get user by email with validation"""
        if not self.validator.validate_email(email):
            raise SecurityViolation("Invalid email format")
        return self.execute_query("get_user_by_email", (email,))

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        window_start = now - timedelta(seconds=SECURITY_CONFIG["rate_limit_window"])
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]
        else:
            self.requests[client_id] = []
        
        # Check rate limit
        if len(self.requests[client_id]) >= SECURITY_CONFIG["rate_limit_requests"]:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True

class SecurityMiddleware:
    """Security middleware for FastAPI"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.validator = InputValidator()
    
    async def __call__(self, request: Request, call_next):
        """Process request with security checks"""
        client_id = self.get_client_id(request)
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(client_id):
            security_logger.warning(f"Rate limit exceeded for client: {client_id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Input validation for query parameters
        for param_name, param_value in request.query_params.items():
            if isinstance(param_value, str):
                if self.validator.check_malicious_patterns(param_value):
                    security_logger.warning(f"Malicious pattern in query param {param_name}: {param_value}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input detected"
                    )
        
        # Process request
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        
        return response
    
    def get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Use X-Forwarded-For if behind proxy, otherwise use client host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

def security_log_violation(violation_type: str, details: str, client_ip: str = None):
    """Log security violations"""
    security_logger.error(f"SECURITY VIOLATION - Type: {violation_type}, Details: {details}, Client: {client_ip}")

def require_secure_connection(func):
    """Decorator to require HTTPS in production"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would check for HTTPS in production
        # For now, just log the requirement
        security_logger.info("Secure connection required for sensitive operation")
        return await func(*args, **kwargs)
    return wrapper

# Initialize security components
query_allowlist = QueryAllowlist()
input_validator = InputValidator()
security_middleware = SecurityMiddleware() 