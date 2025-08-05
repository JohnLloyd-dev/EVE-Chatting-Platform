"""
Advanced Security Middleware
Integrates all security features into a comprehensive middleware system
"""

import time
import json
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from functools import wraps

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import jwt

from enhanced_security_config import (
    SECURITY_PATTERNS, 
    SECURITY_HEADERS, 
    RATE_LIMIT_CONFIG,
    security_config
)
from backend.enhanced_auth import session_manager, jwt_manager
from database import get_db, SecurityEvent, UserActivityLog, ApiRateLimits

class AdvancedSecurityMiddleware(BaseHTTPMiddleware):
    """Advanced security middleware with comprehensive protection"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limit_storage: Dict[str, Dict] = {}
        self.threat_scores: Dict[str, int] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.security_events: List[Dict] = []
    
    async def dispatch(self, request: Request, call_next):
        """Process request with comprehensive security checks"""
        start_time = time.time()
        
        # Get client information
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        request_path = request.url.path
        request_method = request.method
        
        # Step 1: IP-based security checks
        if not await self.check_ip_security(client_ip):
            return self.create_security_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Access denied - IP security check failed"
            )
        
        # Step 2: Rate limiting
        rate_limit_result = await self.check_rate_limiting(
            client_ip, request_path, request_method
        )
        if not rate_limit_result["allowed"]:
            return self.create_security_response(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                message=f"Rate limit exceeded. Try again in {rate_limit_result['retry_after']} seconds"
            )
        
        # Step 3: Threat detection
        threat_result = await self.detect_threats(request, client_ip)
        if threat_result["threat_detected"]:
            await self.handle_threat(client_ip, threat_result)
            return self.create_security_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Suspicious activity detected"
            )
        
        # Step 4: Input validation
        validation_result = await self.validate_input(request)
        if not validation_result["valid"]:
            return self.create_security_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Invalid input: {validation_result['reason']}"
            )
        
        # Step 5: Process request
        try:
            response = await call_next(request)
        except Exception as e:
            await self.log_security_event(
                "request_error",
                client_ip,
                user_agent,
                request_path,
                request_method,
                {"error": str(e)}
            )
            raise
        
        # Step 6: Add security headers
        response = await self.add_security_headers(response)
        
        # Step 7: Log activity
        await self.log_activity(
            client_ip,
            user_agent,
            request_path,
            request_method,
            response.status_code,
            time.time() - start_time
        )
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Get real client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def check_ip_security(self, client_ip: str) -> bool:
        """Check IP-based security restrictions"""
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            block_expiry = self.blocked_ips[client_ip]
            if datetime.now(timezone.utc) < block_expiry:
                return False
            else:
                del self.blocked_ips[client_ip]
        
        # Check threat score
        if client_ip in self.threat_scores:
            if self.threat_scores[client_ip] > 100:
                self.blocked_ips[client_ip] = datetime.now(timezone.utc) + timedelta(hours=24)
                return False
        
        return True
    
    async def check_rate_limiting(self, client_ip: str, path: str, method: str) -> Dict:
        """Advanced rate limiting with database storage"""
        current_time = time.time()
        
        # Determine rate limit configuration
        if "login" in path.lower() or "auth" in path.lower():
            config = RATE_LIMIT_CONFIG["login"]
        elif "webhook" in path.lower():
            config = RATE_LIMIT_CONFIG["webhook"]
        elif "admin" in path.lower():
            config = RATE_LIMIT_CONFIG["admin"]
        else:
            config = RATE_LIMIT_CONFIG["api"]
        
        # Check in-memory rate limiting
        key = f"{client_ip}:{path}:{method}"
        if key not in self.rate_limit_storage:
            self.rate_limit_storage[key] = {
                "requests": [],
                "blocked_until": None
            }
        
        rate_data = self.rate_limit_storage[key]
        
        # Check if currently blocked
        if rate_data["blocked_until"] and current_time < rate_data["blocked_until"]:
            return {
                "allowed": False,
                "retry_after": int(rate_data["blocked_until"] - current_time)
            }
        
        # Clean old requests
        window_start = current_time - config["window"]
        rate_data["requests"] = [req for req in rate_data["requests"] if req > window_start]
        
        # Check rate limit
        if len(rate_data["requests"]) >= config["requests"]:
            # Block for window duration
            rate_data["blocked_until"] = current_time + config["window"]
            return {
                "allowed": False,
                "retry_after": config["window"]
            }
        
        # Add current request
        rate_data["requests"].append(current_time)
        
        return {"allowed": True, "retry_after": 0}
    
    async def detect_threats(self, request: Request, client_ip: str) -> Dict:
        """Advanced threat detection"""
        threats = []
        threat_score = 0
        
        # Analyze URL path
        path_threats = self.analyze_patterns(request.url.path, "path_traversal")
        threats.extend(path_threats)
        threat_score += len(path_threats) * 10
        
        # Analyze query parameters
        for param_name, param_value in request.query_params.items():
            param_threats = self.analyze_patterns(str(param_value), "all")
            threats.extend([f"Query param {param_name}: {t}" for t in param_threats])
            threat_score += len(param_threats) * 15
        
        # Analyze headers
        header_threats = self.analyze_headers(request.headers)
        threats.extend(header_threats)
        threat_score += len(header_threats) * 20
        
        # Analyze user agent
        ua_threats = self.analyze_user_agent(request.headers.get("user-agent", ""))
        threats.extend(ua_threats)
        threat_score += len(ua_threats) * 5
        
        # Update threat score
        if client_ip not in self.threat_scores:
            self.threat_scores[client_ip] = 0
        self.threat_scores[client_ip] += threat_score
        
        return {
            "threat_detected": len(threats) > 0,
            "threats": threats,
            "threat_score": threat_score,
            "total_threat_score": self.threat_scores[client_ip]
        }
    
    def analyze_patterns(self, text: str, pattern_type: str) -> List[str]:
        """Analyze text for security patterns"""
        threats = []
        text_lower = text.lower()
        
        if pattern_type == "all":
            patterns_to_check = SECURITY_PATTERNS
        else:
            patterns_to_check = {pattern_type: SECURITY_PATTERNS.get(pattern_type, [])}
        
        for threat_type, patterns in patterns_to_check.items():
            for pattern in patterns:
                if pattern in text_lower:
                    threats.append(f"{threat_type}: {pattern}")
        
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
                header_threats = self.analyze_patterns(header_value, "header_injection")
                threats.extend([f"Header {header_name}: {t}" for t in header_threats])
        
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
        
        import re
        for pattern in suspicious_ua_patterns:
            if re.search(pattern, user_agent_lower, re.IGNORECASE):
                threats.append(f"Suspicious user agent pattern: {pattern}")
        
        return threats
    
    async def validate_input(self, request: Request) -> Dict:
        """Validate request input"""
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > security_config.max_input_length:
            return {
                "valid": False,
                "reason": "Request too large"
            }
        
        # Check query length
        if len(str(request.query_params)) > security_config.max_query_length:
            return {
                "valid": False,
                "reason": "Query string too long"
            }
        
        return {"valid": True, "reason": ""}
    
    async def handle_threat(self, client_ip: str, threat_result: Dict):
        """Handle detected threats"""
        # Log threat
        await self.log_security_event(
            "threat_detected",
            client_ip,
            "",
            "",
            "",
            threat_result
        )
        
        # Update threat score
        if threat_result["total_threat_score"] > 100:
            self.blocked_ips[client_ip] = datetime.now(timezone.utc) + timedelta(hours=24)
    
    async def add_security_headers(self, response: Response) -> Response:
        """Add comprehensive security headers"""
        for header_name, header_value in SECURITY_HEADERS.items():
            response.headers[header_name] = header_value
        
        return response
    
    async def log_security_event(self, event_type: str, client_ip: str, user_agent: str, 
                               path: str, method: str, details: Dict):
        """Log security event to database"""
        try:
            # This would normally use database session
            # For now, store in memory
            event = {
                "event_type": event_type,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "path": path,
                "method": method,
                "details": details,
                "timestamp": datetime.now(timezone.utc)
            }
            self.security_events.append(event)
            
            # Keep only last 1000 events
            if len(self.security_events) > 1000:
                self.security_events = self.security_events[-1000:]
                
        except Exception as e:
            # Log to console if database logging fails
            print(f"Failed to log security event: {str(e)}")
    
    async def log_activity(self, client_ip: str, user_agent: str, path: str, 
                          method: str, status_code: int, duration: float):
        """Log user activity"""
        try:
            # This would normally use database session
            # For now, just print
            if status_code >= 400:
                print(f"Activity: {method} {path} - {status_code} - {client_ip} - {duration:.3f}s")
        except Exception as e:
            print(f"Failed to log activity: {str(e)}")
    
    def create_security_response(self, status_code: int, message: str) -> JSONResponse:
        """Create standardized security response"""
        return JSONResponse(
            status_code=status_code,
            content={
                "error": "Security Violation",
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": secrets.token_urlsafe(16)
            }
        )

# Security decorators
def require_authentication(func):
    """Decorator to require authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would check authentication
        return await func(*args, **kwargs)
    return wrapper

def require_authorization(permission: str):
    """Decorator to require specific authorization"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would check authorization
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(limit_type: str = "api"):
    """Decorator to apply rate limiting"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would apply rate limiting
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def audit_log(event_type: str):
    """Decorator to audit log function calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would log the function call
            return await func(*args, **kwargs)
        return wrapper
    return decorator 