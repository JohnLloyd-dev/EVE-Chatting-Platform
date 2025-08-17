from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database - Read from environment variable
    database_url: str = os.getenv("DATABASE_URL", "postgresql://adam2025man:adam2025@postgres:5432/chatting_platform")
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # AI Model (Integrated - no external server needed)
    # ai_model_url: str = "http://ai-server:8000"  # Removed - now integrated
    # ai_model_auth_username: str = "adam"         # Removed - no auth needed
    # ai_model_auth_password: str = "eve2025"      # Removed - no auth needed
    
    # JWT
    secret_key: str = "eve-super-secure-jwt-secret-key-2025-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Admin
    admin_username: str = "admin"
    admin_password: str = "adam@and@eve@3241"
    
    # Tally webhook security
    tally_webhook_secret: Optional[str] = None
    
    # AI Model Configuration (Optimized 7B model for 8GB VRAM)
    ai_model_name: str = "TheBloke/OpenHermes-2.5-Mistral-7B-GGUF"
    ai_model_cache_dir: str = "/app/.cache/huggingface"
    ai_generation_timeout: float = 30.0
    ai_request_timeout: float = 60.0
    
    class Config:
        env_file = ".env"

settings = Settings()