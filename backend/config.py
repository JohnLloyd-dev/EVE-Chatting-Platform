from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres123@localhost:5432/chatting_platform"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # AI Model
    ai_model_url: str = "http://204.12.223.76:8000"
    ai_model_auth_username: str = "adam"
    ai_model_auth_password: str = "eve2025"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Admin
    admin_username: str = "admin"
    admin_password: str = "admin123"
    
    # Tally webhook security
    tally_webhook_secret: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()