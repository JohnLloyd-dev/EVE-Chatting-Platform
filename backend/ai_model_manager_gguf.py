"""
GGUF AI Model Manager for Backend
Optimized for RTX 4060 with 8GB VRAM using llama-cpp-python
"""
import logging
import time
import os
import gc
import threading
from threading import Lock
from typing import Dict, List, Optional, Tuple
from llama_cpp import Llama
from config import settings

# Database imports moved to top level to prevent circular imports
try:
    from database import SystemPrompt, Message
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ Database imports not available - running in standalone mode")

logger = logging.getLogger(__name__)

class GGUFModelManager:
    """GGUF-based manager for AI model loading and inference using llama-cpp-python"""
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.user_sessions: Dict[str, Dict] = {}
        
        # GGUF OPTIMIZATION SETTINGS for RTX 4060 (8GB VRAM)
        self.MAX_ACTIVE_USERS = 3  # GGUF is more memory efficient
        self.MAX_CONTEXT_LENGTH = settings.ai_gguf_n_ctx
        self.MAX_HISTORY_TOKENS = 800   # Increased for GGUF efficiency
        self.MAX_HISTORY_MESSAGES = 5   # Increased for GGUF efficiency
        self.VRAM_CLEANUP_THRESHOLD = 1.5  # Lower threshold for GGUF
        
        self.generate_lock = Lock()
        
        # Load model on initialization
        self._load_model()
    
    def _load_model(self):
        """Load the GGUF AI model with optimized settings for RTX 4060"""
        try:
            logger.info(f"🚀 Loading GGUF AI model: {settings.ai_model_file}")
            logger.info(f"📁 Cache directory: {settings.ai_model_cache_dir}")
            logger.info(f"🔧 GGUF settings:")
            logger.info(f"   - GPU layers: {settings.ai_gguf_n_gpu_layers}")
            logger.info(f"   - Context window: {settings.ai_gguf_n_ctx}")
            logger.info(f"   - Batch size: {settings.ai_gguf_n_batch}")
            
            # Construct model path
            model_path = os.path.join(settings.ai_model_cache_dir, settings.ai_model_file)
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"❌ GGUF model file not found: {model_path}")
            
            logger.info(f"📁 Model path: {model_path}")
            logger.info(f"📊 File size: {os.path.getsize(model_path) / (1024**3):.2f}GB")
            
            # Initialize GGUF model with optimized settings
            self.model = Llama(
                model_path=model_path,
                n_gpu_layers=settings.ai_gguf_n_gpu_layers,  # Use GPU for most layers
                n_ctx=settings.ai_gguf_n_ctx,  # Context window
                n_batch=settings.ai_gguf_n_batch,  # Batch size for prompt processing
                verbose=False,  # Reduce logging noise
                seed=42,  # For reproducible results
            )
            
            self.model_loaded = True
            logger.info(f"✅ GGUF model loaded successfully!")
            
            # Test model with a simple prompt
            test_response = self.model.create_completion(
                "Hello", 
                max_tokens=5, 
                temperature=0.1,
                stop=["\n"]
            )
            logger.info(f"🧪 Model test successful: {test_response['choices'][0]['text']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load GGUF model: {str(e)}", exc_info=True)
            self.model_loaded = False
            raise
    
    def create_session(self, session_id: str, system_prompt: str):
        """Create a new user session with system prompt"""
        if session_id in self.user_sessions:
            logger.warning(f"Session {session_id} already exists, overwriting")
        
        self.user_sessions[session_id] = {
            "system_prompt": system_prompt,
            "messages": [],
            "created_at": time.time()
        }
        
        logger.info(f"✅ Created GGUF session {session_id}")
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get user session by ID"""
        return self.user_sessions.get(session_id)
    
    def add_user_message(self, session_id: str, message: str):
        """Add user message to session history"""
        if session_id not in self.user_sessions:
            logger.warning(f"Session {session_id} not found, creating new session")
            self.create_session(session_id, "You are a helpful AI assistant.")
        
        self.user_sessions[session_id]["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": time.time()
        })
        
        # Trim history if needed
        self._trim_session_history(session_id)
    
    def add_assistant_message(self, session_id: str, message: str):
        """Add assistant message to session history"""
        if session_id not in self.user_sessions:
            logger.warning(f"Session {session_id} not found, creating new session")
            self.create_session(session_id, "You are a helpful AI assistant.")
        
        self.user_sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": message,
            "timestamp": time.time()
        })
        
        # Trim history if needed
        self._trim_session_history(session_id)
    
    def _trim_session_history(self, session_id: str):
        """Trim session history to prevent memory issues"""
        session = self.user_sessions[session_id]
        messages = session["messages"]
        
        # Keep only the last N messages
        if len(messages) > self.MAX_HISTORY_MESSAGES:
            session["messages"] = messages[-self.MAX_HISTORY_MESSAGES:]
            logger.debug(f"Trimmed session {session_id} history to {self.MAX_HISTORY_MESSAGES} messages")
    
    def generate_response(self, session_id: str, user_message: str, chat_session=None, db=None) -> str:
        """Generate AI response using GGUF model"""
        if not self.model_loaded:
            raise RuntimeError("❌ GGUF model not loaded")
        
        with self.generate_lock:
            try:
                # Add user message to session
                self.add_user_message(session_id, user_message)
                
                # Get session
                session = self.get_session(session_id)
                if not session:
                    raise ValueError(f"Session {session_id} not found")
                
                # Build prompt with system message and conversation history
                prompt = self._build_prompt(session)
                
                logger.debug(f"Generating response for session {session_id}")
                logger.debug(f"Prompt length: {len(prompt)} characters")
                
                # Generate response using GGUF model
                response = self.model.create_completion(
                    prompt,
                    max_tokens=settings.ai_max_context_length,
                    temperature=settings.ai_temperature,
                    top_p=settings.ai_top_p,
                    top_k=settings.ai_top_k,
                    typical_p=settings.ai_typical_p,
                    tfs_z=settings.ai_tfs_z,
                    stop=["<|im_end|>", "<|endoftext|>", "\n\n\n"],  # Stop tokens
                    echo=False,  # Don't echo the prompt
                )
                
                # Extract response text
                ai_response = response['choices'][0]['text'].strip()
                
                # Add assistant message to session
                self.add_assistant_message(session_id, ai_response)
                
                logger.info(f"✅ GGUF response generated: {len(ai_response)} characters")
                return ai_response
                
            except Exception as e:
                logger.error(f"❌ Failed to generate GGUF response: {str(e)}", exc_info=True)
                raise
    
    def _build_prompt(self, session: Dict) -> str:
        """Build prompt from system prompt and conversation history"""
        system_prompt = session["system_prompt"]
        messages = session["messages"]
        
        # Start with system prompt
        prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        
        # Add conversation history
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
        
        # Add assistant prefix for response generation
        prompt += "<|im_start|>assistant\n"
        
        return prompt
    
    def get_health_status(self) -> Dict:
        """Get model health status"""
        return {
            "model_loaded": self.model_loaded,
            "model_type": "GGUF",
            "model_name": settings.ai_model_file,
            "active_sessions": len(self.user_sessions),
            "max_active_users": self.MAX_ACTIVE_USERS,
            "context_length": self.MAX_CONTEXT_LENGTH,
            "gpu_layers": settings.ai_gguf_n_gpu_layers,
            "status": "ready" if self.model_loaded else "not_loaded"
        }
    
    def get_vram_usage_stats(self) -> Dict:
        """Get VRAM usage statistics (GGUF doesn't expose this directly)"""
        return {
            "model_type": "GGUF",
            "note": "VRAM usage not directly accessible in GGUF",
            "estimated_usage": "3-4GB for 7B model with 35 GPU layers",
            "active_sessions": len(self.user_sessions)
        }
    
    def optimize_memory_usage(self):
        """Optimize memory usage by cleaning up old sessions"""
        current_time = time.time()
        sessions_to_remove = []
        
        for session_id, session in self.user_sessions.items():
            # Remove sessions older than 1 hour
            if current_time - session["created_at"] > 3600:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.user_sessions[session_id]
            logger.info(f"🧹 Removed old session: {session_id}")
        
        # Force garbage collection
        gc.collect()
        
        logger.info(f"🧹 Memory optimization completed. Removed {len(sessions_to_remove)} old sessions")
    
    def cleanup_session(self, session_id: str):
        """Clean up a specific session"""
        if session_id in self.user_sessions:
            del self.user_sessions[session_id]
            logger.info(f"🧹 Cleaned up session: {session_id}")

# Global instance
gguf_model_manager = GGUFModelManager() 