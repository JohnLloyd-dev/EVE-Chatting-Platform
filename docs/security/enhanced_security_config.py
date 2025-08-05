"""
Enhanced Security Configuration
Comprehensive security settings for the EVE Chat Platform
"""

import os
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityConfig:
    """Comprehensive security configuration"""
    
    # Authentication settings
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    password_history_count: int = 5
    password_expiry_days: int = 90
    
    # Session settings
    session_timeout_minutes: int = 480  # 8 hours
    max_concurrent_sessions: int = 3
    session_inactivity_timeout: int = 30  # minutes
    
    # Login security
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    account_lockout_threshold: int = 10
    permanent_lockout_after: int = 20
    
    # MFA settings
    mfa_required: bool = True
    mfa_backup_codes_count: int = 10
    mfa_totp_window: int = 2
    
    # JWT settings
    jwt_access_token_expiry_minutes: int = 30
    jwt_refresh_token_expiry_days: int = 7
    jwt_algorithm: str = "HS256"
    jwt_token_rotation: bool = True
    
    # Rate limiting
    api_rate_limit_requests: int = 100
    api_rate_limit_window: int = 60  # seconds
    login_rate_limit_requests: int = 5
    login_rate_limit_window: int = 300  # 5 minutes
    webhook_rate_limit_requests: int = 2
    webhook_rate_limit_window: int = 60
    
    # Input validation
    max_input_length: int = 5000
    max_query_length: int = 1000
    max_file_size_mb: int = 10
    allowed_file_types: List[str] = None
    
    # Encryption settings
    encryption_required: bool = True
    encryption_algorithm: str = "AES-256-GCM"
    key_rotation_days: int = 90
    
    # Network security
    require_https: bool = True
    hsts_max_age: int = 31536000  # 1 year
    csp_enabled: bool = True
    cors_allowed_origins: List[str] = None
    
    # Logging and monitoring
    audit_logging: bool = True
    security_logging: bool = True
    log_retention_days: int = 90
    alert_on_security_events: bool = True
    
    # Threat detection
    threat_detection_enabled: bool = True
    suspicious_activity_threshold: int = 10
    auto_block_suspicious_ips: bool = True
    block_duration_hours: int = 24
    
    # Database security
    db_connection_pool_size: int = 10
    db_connection_timeout: int = 30
    db_query_timeout: int = 30
    db_ssl_required: bool = True
    
    # API security
    api_versioning: bool = True
    api_documentation_enabled: bool = False  # Disable in production
    api_rate_limiting_enabled: bool = True
    api_request_logging: bool = True
    
    # File upload security
    file_upload_enabled: bool = False  # Disable by default
    virus_scanning_enabled: bool = True
    file_quarantine_enabled: bool = True
    
    # Backup security
    backup_encryption_required: bool = True
    backup_retention_days: int = 30
    backup_verification_enabled: bool = True
    
    def __post_init__(self):
        if self.allowed_file_types is None:
            self.allowed_file_types = [".txt", ".pdf", ".doc", ".docx"]
        
        if self.cors_allowed_origins is None:
            self.cors_allowed_origins = [
                "http://localhost:3000",
                "https://yourdomain.com"
            ]

# Security patterns for threat detection
SECURITY_PATTERNS = {
    "sql_injection": [
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|vbscript|onload|onerror|onclick)\b)",
        r"(--|/\*|\*/|xp_|sp_|@@|0x[0-9a-fA-F]+)",
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|vbscript|onload|onerror|onclick)\b)",
    ],
    "xss": [
        r"(<script|javascript:|vbscript:|onload=|onerror=|onclick=)",
        r"(<iframe|<object|<embed|<applet)",
        r"(document\.cookie|localStorage|sessionStorage)",
        r"(alert\(|confirm\(|prompt\()",
        r"(onload|onerror|onclick|onmouseover|onfocus|onblur)",
    ],
    "path_traversal": [
        r"(\.\.\/|\.\.\\|\.\.%2f|\.\.%5c)",
        r"(\.\.\/|\.\.\\|\.\.%2f|\.\.%5c)",
    ],
    "code_injection": [
        r"(eval\(|exec\(|system\(|shell_exec|base64_decode|gzinflate|str_rot13|preg_replace.*\/e)",
        r"(eval\(|exec\(|system\(|shell_exec|base64_decode|gzinflate|str_rot13|preg_replace.*\/e)",
    ],
    "file_inclusion": [
        r"(\.\.\/|\.\.\\|\.\.%2f|\.\.%5c)",
        r"(include\(|require\(|include_once\(|require_once\()",
    ],
    "command_injection": [
        r"(\||&|;|`|\$\(|\)|>|<)",
        r"(cmd|powershell|bash|sh|python|perl|ruby)",
    ],
    "ldap_injection": [
        r"(\*|\(|\)|\||&|!)",
        r"(cn=|ou=|dc=|uid=)",
    ],
    "xml_injection": [
        r"(<!\[CDATA\[|<!DOCTYPE|<!ENTITY|<!ELEMENT)",
        r"(<script|javascript:|vbscript:)",
    ],
    "header_injection": [
        r"(\r|\n|%0d|%0a)",
        r"(location:|set-cookie:|content-type:)",
    ],
    "ssrf": [
        r"(http://|https://|ftp://|file://|gopher://|dict://|ldap://)",
        r"(localhost|127\.0\.0\.1|0\.0\.0\.0|::1)",
    ],
    "deserialization": [
        r"(O:|a:|s:|i:|d:|b:|N;|T:|R:)",  # PHP serialization
        r"(\{.*\"@type\".*\})",  # Java serialization
    ],
    "template_injection": [
        r"(\{\{.*\}\}|\{%.*%\}|\{.*\})",
        r"(request|config|self|class|builtins)",
    ]
}

# Security headers configuration
SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "upgrade-insecure-requests;"
    ),
    "Permissions-Policy": (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=(), "
        "ambient-light-sensor=(), "
        "autoplay=(), "
        "encrypted-media=(), "
        "picture-in-picture=()"
    ),
    "X-Permitted-Cross-Domain-Policies": "none",
    "X-Download-Options": "noopen",
    "X-DNS-Prefetch-Control": "off"
}

# CORS configuration
CORS_CONFIG = {
    "allow_origins": [
        "http://localhost:3000",
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": [
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With"
    ],
    "expose_headers": ["Content-Length", "Content-Range"],
    "max_age": 86400  # 24 hours
}

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "api": {
        "requests": 100,
        "window": 60,  # seconds
        "burst": 20
    },
    "login": {
        "requests": 5,
        "window": 300,  # 5 minutes
        "burst": 3
    },
    "webhook": {
        "requests": 2,
        "window": 60,  # 1 minute
        "burst": 5
    },
    "admin": {
        "requests": 50,
        "window": 60,  # 1 minute
        "burst": 10
    },
    "public": {
        "requests": 200,
        "window": 60,  # 1 minute
        "burst": 50
    }
}

# Database security configuration
DB_SECURITY_CONFIG = {
    "connection_pool_size": 10,
    "connection_timeout": 30,
    "query_timeout": 30,
    "ssl_required": True,
    "ssl_verify": True,
    "max_connections": 100,
    "idle_timeout": 300,
    "statement_timeout": 30000,  # milliseconds
    "lock_timeout": 5000,  # milliseconds
    "deadlock_timeout": 1000,  # milliseconds
    "log_statement": "all",
    "log_connections": True,
    "log_disconnections": True,
    "log_duration": True,
    "log_min_duration_statement": 1000,  # milliseconds
}

# File upload security configuration
FILE_UPLOAD_CONFIG = {
    "enabled": False,  # Disable by default
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_extensions": [".txt", ".pdf", ".doc", ".docx", ".jpg", ".png", ".gif"],
    "allowed_mime_types": [
        "text/plain",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png",
        "image/gif"
    ],
    "virus_scanning": True,
    "quarantine_suspicious": True,
    "scan_timeout": 30,  # seconds
    "upload_directory": "/tmp/uploads",
    "temp_directory": "/tmp/temp",
}

# Backup security configuration
BACKUP_CONFIG = {
    "enabled": True,
    "encryption_required": True,
    "encryption_algorithm": "AES-256-GCM",
    "retention_days": 30,
    "verification_enabled": True,
    "compression_enabled": True,
    "incremental_backups": True,
    "backup_schedule": "0 2 * * *",  # Daily at 2 AM
    "backup_directory": "/backups",
    "max_backup_size": 10 * 1024 * 1024 * 1024,  # 10GB
}

# Monitoring and alerting configuration
MONITORING_CONFIG = {
    "enabled": True,
    "log_level": "INFO",
    "log_retention_days": 90,
    "alert_on_security_events": True,
    "alert_on_performance_issues": True,
    "alert_on_disk_space": True,
    "alert_on_memory_usage": True,
    "alert_on_cpu_usage": True,
    "alert_thresholds": {
        "disk_usage_percent": 80,
        "memory_usage_percent": 85,
        "cpu_usage_percent": 90,
        "error_rate_percent": 5,
        "response_time_ms": 5000
    },
    "notification_channels": [
        "email",
        "slack",
        "webhook"
    ],
    "health_check_interval": 60,  # seconds
    "metrics_collection_interval": 300,  # 5 minutes
}

# Threat detection configuration
THREAT_DETECTION_CONFIG = {
    "enabled": True,
    "suspicious_activity_threshold": 10,
    "auto_block_suspicious_ips": True,
    "block_duration_hours": 24,
    "whitelist_ips": [],
    "blacklist_ips": [],
    "detection_rules": {
        "sql_injection": {
            "enabled": True,
            "threshold": 5,
            "action": "block"
        },
        "xss": {
            "enabled": True,
            "threshold": 5,
            "action": "block"
        },
        "brute_force": {
            "enabled": True,
            "threshold": 10,
            "action": "block"
        },
        "ddos": {
            "enabled": True,
            "threshold": 100,
            "action": "rate_limit"
        },
        "file_upload_abuse": {
            "enabled": True,
            "threshold": 5,
            "action": "block"
        }
    }
}

# Initialize security configuration
security_config = SecurityConfig()

def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    return security_config

def update_security_config(**kwargs) -> SecurityConfig:
    """Update security configuration"""
    global security_config
    for key, value in kwargs.items():
        if hasattr(security_config, key):
            setattr(security_config, key, value)
    return security_config

def validate_security_config(config: SecurityConfig) -> List[str]:
    """Validate security configuration"""
    errors = []
    
    if config.password_min_length < 8:
        errors.append("Password minimum length must be at least 8 characters")
    
    if config.session_timeout_minutes < 15:
        errors.append("Session timeout must be at least 15 minutes")
    
    if config.max_login_attempts < 1:
        errors.append("Maximum login attempts must be at least 1")
    
    if config.lockout_duration_minutes < 1:
        errors.append("Lockout duration must be at least 1 minute")
    
    if config.api_rate_limit_requests < 1:
        errors.append("API rate limit requests must be at least 1")
    
    if config.api_rate_limit_window < 1:
        errors.append("API rate limit window must be at least 1 second")
    
    return errors 