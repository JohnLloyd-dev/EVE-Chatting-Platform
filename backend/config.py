from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database - Read from environment variable
    database_url: str = "postgresql://adam2025man:adam2025@postgres:5432/chatting_platform"
    
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
    
    # AI Model Configuration (7B with 4-bit quantization for RTX 4060)
    ai_model_name: str = os.getenv("AI_MODEL_NAME", "teknium/OpenHermes-2.5-Mistral-7B")
    ai_model_file: str = os.getenv("AI_MODEL_FILE", "")  # Not needed for transformers
    ai_model_cache_dir: str = os.getenv("AI_MODEL_CACHE_DIR", "/app/.cache/huggingface")
    ai_generation_timeout: float = float(os.getenv("AI_GENERATION_TIMEOUT", "30.0"))
    ai_request_timeout: float = float(os.getenv("AI_REQUEST_TIMEOUT", "60.0"))
    ai_use_4bit: bool = os.getenv("AI_USE_4BIT", "true").lower() == "true"
    ai_use_8bit: bool = os.getenv("AI_USE_8BIT", "false").lower() == "true"
    
    # RTX 4060 Memory Optimization Settings (Emergency VRAM Mode)
    ai_max_context_length: int = int(os.getenv("AI_MAX_CONTEXT_LENGTH", "512"))  # CRITICAL: Reduced to 512 for 8GB VRAM
    ai_max_memory_gb: float = float(os.getenv("AI_MAX_MEMORY_GB", "4.5"))  # CRITICAL: Reduced to 4.5GB for 8GB VRAM
    ai_offload_folder: str = os.getenv("AI_OFFLOAD_FOLDER", "/app/offload")  # Disk offloading
    ai_batch_size: int = int(os.getenv("AI_BATCH_SIZE", "1"))  # Single batch for memory efficiency
    
    # Guide-Based Accuracy-First Parameters
    ai_temperature: float = float(os.getenv("AI_TEMPERATURE", "0.28"))  # Slightly lower for accuracy compensation
    ai_top_p: float = float(os.getenv("AI_TOP_P", "0.9"))  # More flexible for better accuracy
    ai_top_k: int = int(os.getenv("AI_TOP_K", "30"))  # Better than 25 for accuracy
    ai_typical_p: float = float(os.getenv("AI_TYPICAL_P", "0.9"))  # Filters atypical tokens
    ai_tfs_z: float = float(os.getenv("AI_TFS_Z", "0.95"))  # Tail-free sampling
    
    class Config:
        env_file = ".env"

settings = Settings()