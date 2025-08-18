from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database - Read from environment variable
    database_url: str = os.getenv("DATABASE_URL", "postgresql://adam2025man:adam2025@postgres:5432/chatting_platform")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # AI Model (Integrated - no external server needed)
    # ai_model_url: str = "http://ai-server:8000"  # Removed - now integrated
    # ai_model_auth_username: str = "adam"         # Removed - no auth needed
    # ai_model_auth_password: str = "eve2025"      # Removed - no auth needed
    
    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "eve-super-secure-jwt-secret-key-2025-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Admin
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "adam@and@eve@3241")
    
    # Tally webhook security
    tally_webhook_secret: Optional[str] = os.getenv("TALLY_WEBHOOK_SECRET")
    
    # AI Model Configuration (GGUF optimized for RTX 4060)
    ai_model_name: str = os.getenv("AI_MODEL_NAME", "TheBloke/OpenHermes-2.5-Mistral-7B-GGUF")
    ai_model_file: str = os.getenv("AI_MODEL_FILE", "openhermes-2.5-mistral-7b.Q5_K_M.gguf")
    ai_model_cache_dir: str = os.getenv("AI_MODEL_CACHE_DIR", "/app/.cache/huggingface")
    ai_generation_timeout: float = float(os.getenv("AI_GENERATION_TIMEOUT", "30.0"))
    ai_request_timeout: float = float(os.getenv("AI_REQUEST_TIMEOUT", "60.0"))
    
    class Config:
        env_file = ".env"

settings = Settings()