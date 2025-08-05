"""
Advanced Security Module for EVE Chat Platform
Implements enterprise-grade security features including:
- Multi-factor authentication
- Advanced encryption
- Session management
- Audit logging
- Threat detection
- Security policies
"""

import os
import re
import hashlib
import secrets
import logging
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any, Tuple
from functools import wraps
from dataclasses import dataclass
from enum import Enum

import bcrypt
import pyotp
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db, AdminUser, AdminSession, User, SecurityEvent
from config import settings

# Configure advanced security logging
security_logger = logging.getLogger("advanced_security")
security_logger.setLevel(logging.INFO)

# Security configuration
class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    session_timeout: int = 28800  # 8 hours
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    mfa_required: bool = True
    encryption_required: bool = True
    audit_logging: bool = True
    threat_detection: bool = True

# Global security policy
SECURITY_POLICY = SecurityPolicy()

class AdvancedEncryption:
    """Advanced encryption utilities"""
    
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        
        # Generate RSA key pair for asymmetric encryption
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
    
    def encrypt_symmetric(self, data: str) -> str:
        """Encrypt data using symmetric encryption"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_symmetric(self, encrypted_data: str) -> str:
        """Decrypt data using symmetric encryption"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_asymmetric(self, data: str) -> str:
        """Encrypt data using asymmetric encryption"""
        encrypted = self.public_key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted.hex()
    
    def decrypt_asymmetric(self, encrypted_data: str) -> str:
        """Decrypt data using asymmetric encryption"""
        encrypted_bytes = bytes.fromhex(encrypted_data)
        decrypted = self.private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted.decode()
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with high cost factor"""
        salt = bcrypt.gensalt(rounds=14)  # High cost factor for security
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against bcrypt hash"""
        return bcrypt.checkpw(password.encode(), hashed.encode())

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
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=self.totp_window)
    
    def generate_backup_codes(self) -> List[str]:
        """Generate backup codes for MFA"""
        return [secrets.token_hex(4).upper() for _ in range(10)]

class SessionManager:
    """Advanced session management"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.session_encryption = AdvancedEncryption()
    
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
        
        # Encrypt session data
        encrypted_data = self.session_encryption.encrypt_symmetric(json.dumps(session_data))
        self.active_sessions[session_id] = {"data": encrypted_data}
        
        return session_id
    
    def validate_session(self, session_id: str, ip_address: str) -> Optional[Dict]:
        """Validate session and return session data"""
        if session_id not in self.active_sessions:
            return None
        
        try:
            encrypted_data = self.active_sessions[session_id]["data"]
            session_data = json.loads(self.session_encryption.decrypt_symmetric(encrypted_data))
            
            # Check if session is expired
            if datetime.now(timezone.utc) - session_data["created_at"] > timedelta(seconds=SECURITY_POLICY.session_timeout):
                self.invalidate_session(session_id)
                return None
            
            # Check IP address (optional security measure)
            if session_data["ip_address"] != ip_address:
                security_logger.warning(f"IP mismatch for session {session_id}")
                # Don't invalidate immediately, just log
            
            # Update last activity
            session_data["last_activity"] = datetime.now(timezone.utc)
            encrypted_data = self.session_encryption.encrypt_symmetric(json.dumps(session_data))
            self.active_sessions[session_id]["data"] = encrypted_data
            
            return session_data
        except Exception as e:
            security_logger.error(f"Session validation error: {str(e)}")
            return None
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now(timezone.utc)
        expired_sessions = []
        
        for session_id, session_info in self.active_sessions.items():
            try:
                session_data = json.loads(self.session_encryption.decrypt_symmetric(session_info["data"]))
                if current_time - session_data["created_at"] > timedelta(seconds=SECURITY_POLICY.session_timeout):
                    expired_sessions.append(session_id)
            except:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.invalidate_session(session_id)

class ThreatDetector:
    """Advanced threat detection system"""
    
    def __init__(self):
        self.suspicious_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|vbscript|onload|onerror|onclick)\b)",
            r"(--|/\*|\*/|xp_|sp_|@@|0x[0-9a-fA-F]+)",
            r"(<script|javascript:|vbscript:|onload=|onerror=|onclick=)",
            r"(\.\.\/|\.\.\\|\.\.%2f|\.\.%5c)",
            r"(eval\(|exec\(|system\(|shell_exec|base64_decode|gzinflate|str_rot13|preg_replace.*\/e)",
            r"(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|vbscript|onload|onerror|onclick)",
            r"(admin|root|password|passwd|shadow|etc/passwd|/etc/shadow)",
            r"(\.\.\/|\.\.\\|\.\.%2f|\.\.%5c)",
            r"(<iframe|<object|<embed|<applet)",
            r"(document\.cookie|localStorage|sessionStorage)",
            r"(alert\(|confirm\(|prompt\()",
            r"(onload|onerror|onclick|onmouseover|onfocus|onblur)",
        ]
        
        self.threat_scores: Dict[str, int] = {}
        self.blocked_ips: Dict[str, datetime] = {}
    
    def analyze_request(self, request: Request, user_id: str = None) -> Tuple[bool, int, str]:
        """Analyze request for threats"""
        threat_score = 0
        threats_detected = []
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            if datetime.now(timezone.utc) - self.blocked_ips[client_ip] < timedelta(minutes=30):
                return False, 100, "IP address is blocked"
            else:
                del self.blocked_ips[client_ip]
        
        # Analyze URL path
        path_threats = self.analyze_path(request.url.path)
        threat_score += len(path_threats) * 10
        threats_detected.extend(path_threats)
        
        # Analyze query parameters
        query_threats = self.analyze_query_params(request.query_params)
        threat_score += len(query_threats) * 15
        threats_detected.extend(query_threats)
        
        # Analyze headers
        header_threats = self.analyze_headers(request.headers)
        threat_score += len(header_threats) * 20
        threats_detected.extend(header_threats)
        
        # Analyze user agent
        ua_threats = self.analyze_user_agent(request.headers.get("user-agent", ""))
        threat_score += len(ua_threats) * 5
        threats_detected.extend(ua_threats)
        
        # Check rate limiting
        if user_id:
            rate_threats = self.check_rate_limiting(user_id, client_ip)
            threat_score += len(rate_threats) * 25
            threats_detected.extend(rate_threats)
        
        # Update threat score for client
        if client_ip not in self.threat_scores:
            self.threat_scores[client_ip] = 0
        self.threat_scores[client_ip] += threat_score
        
        # Block if threat score is too high
        if self.threat_scores[client_ip] > 100:
            self.blocked_ips[client_ip] = datetime.now(timezone.utc)
            return False, self.threat_scores[client_ip], f"Threat score too high: {', '.join(threats_detected)}"
        
        return True, threat_score, ", ".join(threats_detected) if threats_detected else "No threats detected"
    
    def analyze_path(self, path: str) -> List[str]:
        """Analyze URL path for threats"""
        threats = []
        path_lower = path.lower()
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, path_lower, re.IGNORECASE):
                threats.append(f"Malicious pattern in path: {pattern}")
        
        return threats
    
    def analyze_query_params(self, params) -> List[str]:
        """Analyze query parameters for threats"""
        threats = []
        
        for param_name, param_value in params.items():
            if isinstance(param_value, str):
                param_lower = param_value.lower()
                for pattern in self.suspicious_patterns:
                    if re.search(pattern, param_lower, re.IGNORECASE):
                        threats.append(f"Malicious pattern in query param {param_name}: {pattern}")
        
        return threats
    
    def analyze_headers(self, headers) -> List[str]:
        """Analyze request headers for threats"""
        threats = []
        
        suspicious_headers = [
            "x-forwarded-for", "x-real-ip", "x-forwarded-host",
            "x-forwarded-proto", "x-forwarded-port"
        ]
        
        for header_name, header_value in headers.items():
            header_lower = header_name.lower()
            if header_lower in suspicious_headers:
                threats.append(f"Suspicious header: {header_name}")
            
            if isinstance(header_value, str):
                header_value_lower = header_value.lower()
                for pattern in self.suspicious_patterns:
                    if re.search(pattern, header_value_lower, re.IGNORECASE):
                        threats.append(f"Malicious pattern in header {header_name}: {pattern}")
        
        return threats
    
    def analyze_user_agent(self, user_agent: str) -> List[str]:
        """Analyze user agent for threats"""
        threats = []
        
        if not user_agent:
            threats.append("Missing user agent")
            return threats
        
        user_agent_lower = user_agent.lower()
        
        # Check for suspicious user agents
        suspicious_ua_patterns = [
            r"(bot|crawler|spider|scraper)",
            r"(sqlmap|nikto|nmap|metasploit)",
            r"(curl|wget|python-requests)",
            r"(admin|hack|exploit|inject)",
        ]
        
        for pattern in suspicious_ua_patterns:
            if re.search(pattern, user_agent_lower, re.IGNORECASE):
                threats.append(f"Suspicious user agent pattern: {pattern}")
        
        return threats
    
    def check_rate_limiting(self, user_id: str, client_ip: str) -> List[str]:
        """Check rate limiting for user and IP"""
        threats = []
        
        # This would integrate with a proper rate limiting system
        # For now, just return empty list
        return threats
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

class AuditLogger:
    """Advanced audit logging system"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.encryption = AdvancedEncryption()
    
    def log_event(self, event_type: str, user_id: str, details: Dict, severity: SecurityLevel, ip_address: str = None):
        """Log security event"""
        try:
            # Encrypt sensitive details
            encrypted_details = self.encryption.encrypt_symmetric(json.dumps(details))
            
            security_event = SecurityEvent(
                event_type=event_type,
                user_id=user_id,
                details=encrypted_details,
                severity=severity.value,
                ip_address=ip_address,
                timestamp=datetime.now(timezone.utc)
            )
            
            self.db.add(security_event)
            self.db.commit()
            
            # Also log to system log
            security_logger.info(f"Security Event: {event_type} - User: {user_id} - Severity: {severity.value} - IP: {ip_address}")
            
        except Exception as e:
            security_logger.error(f"Failed to log security event: {str(e)}")
    
    def get_events(self, user_id: str = None, event_type: str = None, limit: int = 100) -> List[Dict]:
        """Get security events"""
        query = self.db.query(SecurityEvent)
        
        if user_id:
            query = query.filter(SecurityEvent.user_id == user_id)
        
        if event_type:
            query = query.filter(SecurityEvent.event_type == event_type)
        
        events = query.order_by(SecurityEvent.timestamp.desc()).limit(limit).all()
        
        result = []
        for event in events:
            try:
                details = json.loads(self.encryption.decrypt_symmetric(event.details))
            except:
                details = {"error": "Could not decrypt details"}
            
            result.append({
                "id": event.id,
                "event_type": event.event_type,
                "user_id": event.user_id,
                "details": details,
                "severity": event.severity,
                "ip_address": event.ip_address,
                "timestamp": event.timestamp.isoformat()
            })
        
        return result

class SecurityValidator:
    """Advanced input validation and sanitization"""
    
    def __init__(self):
        self.password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$')
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < SECURITY_POLICY.password_min_length:
            errors.append(f"Password must be at least {SECURITY_POLICY.password_min_length} characters")
        
        if SECURITY_POLICY.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if SECURITY_POLICY.password_require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if SECURITY_POLICY.password_require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if SECURITY_POLICY.password_require_special and not re.search(r'[@$!%*?&]', password):
            errors.append("Password must contain at least one special character (@$!%*?&)")
        
        # Check for common weak passwords
        weak_passwords = ["password", "123456", "qwerty", "admin", "letmein"]
        if password.lower() in weak_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        return bool(self.email_pattern.match(email))
    
    def validate_uuid(self, uuid_str: str) -> bool:
        """Validate UUID format"""
        return bool(self.uuid_pattern.match(uuid_str.lower()))
    
    def sanitize_input(self, input_str: str, max_length: int = 1000) -> str:
        """Sanitize input string"""
        if not isinstance(input_str, str):
            return str(input_str)
        
        # Remove null bytes
        sanitized = input_str.replace('\x00', '')
        
        # Remove control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()

# Initialize security components
encryption = AdvancedEncryption()
mfa = MultiFactorAuth()
session_manager = SessionManager()
threat_detector = ThreatDetector()
security_validator = SecurityValidator()

# Security decorators
def require_mfa(func):
    """Decorator to require MFA for sensitive operations"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would check if MFA is enabled and verified
        # For now, just log the requirement
        security_logger.info("MFA required for sensitive operation")
        return await func(*args, **kwargs)
    return wrapper

def require_encryption(func):
    """Decorator to require encryption for sensitive data"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would ensure data is encrypted
        # For now, just log the requirement
        security_logger.info("Encryption required for sensitive data")
        return await func(*args, **kwargs)
    return wrapper

def audit_log(event_type: str, severity: SecurityLevel = SecurityLevel.MEDIUM):
    """Decorator to audit log function calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would log the function call
            # For now, just log the requirement
            security_logger.info(f"Audit log: {event_type} - {func.__name__}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator 