from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database - Fixed username without special characters
    database_url: str = "postgresql://adam2025man:eve@postgres@3241@postgres:5432/chatting_platform"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # AI Model
    ai_model_url: str = "http://ai-server:8000"
    ai_model_auth_username: str = "adam"
    ai_model_auth_password: str = "eve2025"
    
    # JWT
    secret_key: str = "eve-super-secure-jwt-secret-key-2025-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Admin
    admin_username: str = "admin"
    admin_password: str = "adam@and@eve@3241"
    
    # Tally webhook security
    tally_webhook_secret: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()