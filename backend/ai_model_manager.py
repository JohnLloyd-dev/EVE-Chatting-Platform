"""
AI Model Manager for Backend
Handles model loading, inference, and session management
"""
import logging
import time
import torch
import gc
from typing import Dict, List, Optional, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
from config import settings

logger = logging.getLogger(__name__)

class AIModelManager:
    """Manages AI model loading, inference, and session management"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.user_sessions: Dict[str, Dict] = {}
        
        # Load model on initialization
        self._load_model()
    
    def _load_model(self):
        """Load the AI model and tokenizer"""
        try:
            logger.info(f"🚀 Loading AI model: {settings.ai_model_name}")
            
            # Check CUDA availability
            if torch.cuda.is_available():
                logger.info(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
                logger.info(f"✅ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
            else:
                logger.warning("⚠️ CUDA not available, using CPU")
            
            # Load tokenizer with timeout and retry
            logger.info("📥 Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.ai_model_name,
                cache_dir=settings.ai_model_cache_dir,
                local_files_only=False,
                trust_remote_code=True
            )
            self.tokenizer.pad_token = self.tokenizer.eos_token
            logger.info("✅ Tokenizer loaded successfully")
            
            # Load model with optimizations and timeout
            logger.info("📥 Loading model (this may take several minutes)...")
            
            # Check if this is a GGUF model
            if "GGUF" in settings.ai_model_name:
                logger.info("🚀 Detected GGUF model - using optimized loading...")
                # GGUF models are already optimized for memory
                model_kwargs = {
                    "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
                    "low_cpu_mem_usage": True,
                    "cache_dir": settings.ai_model_cache_dir,
                    "local_files_only": False,
                    "trust_remote_code": True,
                    "max_memory": {0: "7GB"} if torch.cuda.is_available() else None,
                }
            else:
                # Standard model loading with memory optimization
                model_kwargs = {
                    "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
                    "low_cpu_mem_usage": True,
                    "cache_dir": settings.ai_model_cache_dir,
                    "local_files_only": False,
                    "trust_remote_code": True,
                    "max_memory": {0: "7GB"} if torch.cuda.is_available() else None,
                    "offload_folder": "offload" if torch.cuda.is_available() else None,
                }
            
            # Use device_map="auto" for better memory management
            if torch.cuda.is_available():
                model_kwargs["device_map"] = "auto"
                logger.info("🚀 Using auto device mapping for GPU memory optimization")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                settings.ai_model_name,
                **model_kwargs
            )
            
            # Move to GPU if available
            if torch.cuda.is_available():
                logger.info("🚀 Moving model to GPU...")
                self.model = self.model.cuda()
                logger.info(f"✅ Model loaded on GPU: {self.model.device}")
                
                # Verify GPU memory usage
                memory_allocated = torch.cuda.memory_allocated() / 1024**3
                memory_reserved = torch.cuda.memory_reserved() / 1024**3
                logger.info(f"📊 GPU Memory: {memory_allocated:.1f}GB allocated, {memory_reserved:.1f}GB reserved")
            else:
                logger.info("✅ Model loaded on CPU")
            
            # Set model to evaluation mode
            self.model.eval()
            self.model_loaded = True
            
            logger.info("✅ AI Model loaded successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to load AI model: {e}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            self.model_loaded = False
            
            # Provide specific error guidance
            if "CUDA" in str(e):
                logger.error("💡 CUDA Error: Check GPU drivers and CUDA installation")
            elif "out of memory" in str(e).lower():
                logger.error("💡 Memory Error: Model too large for GPU memory")
            elif "timeout" in str(e).lower():
                logger.error("💡 Timeout Error: Model download taking too long")
            
            raise
    
    def create_session(self, session_id: str, system_prompt: str) -> Dict:
        """Create a new chat session"""
        session = {
            "system_prompt": system_prompt,
            "history": [],
            "message_roles": [],  # Track user vs assistant messages
            "created_at": time.time(),
            "last_updated": time.time()
        }
        
        self.user_sessions[session_id] = session
        logger.info(f"🎯 Created session {session_id} with {len(system_prompt)} char prompt")
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get an existing session"""
        return self.user_sessions.get(session_id)
    
    def add_user_message(self, session_id: str, message: str):
        """Add a user message to session history"""
        if session_id in self.user_sessions:
            session = self.user_sessions[session_id]
            session["history"].append(message)
            session["message_roles"].append("user")
            session["last_updated"] = time.time()
            
            # Trim history if too long (keep last 10 messages)
            if len(session["history"]) > 10:
                session["history"] = session["history"][-10:]
                session["message_roles"] = session["message_roles"][-10:]
    
    def add_assistant_message(self, session_id: str, message: str):
        """Add an assistant message to session history"""
        if session_id in self.user_sessions:
            session = self.user_sessions[session_id]
            session["history"].append(message)
            session["message_roles"].append("assistant")
            session["last_updated"] = time.time()
    
    def build_chatml_prompt(self, system_prompt: str, history: List[str], message_roles: List[str]) -> str:
        """Build ChatML format prompt for the model"""
        parts = [f"<|im_start|>system\n{system_prompt.strip()}<|im_end|>\n"]
        
        # Add conversation history
        for i, (message, role) in enumerate(zip(history, message_roles)):
            if role == "user":
                parts.append(f"<|im_start|>user\n{message.strip()}<|im_end|>\n")
            elif role == "assistant":
                parts.append(f"<|im_start|>assistant\n{message.strip()}<|im_end|>\n")
        
        # Add final assistant tag for the model to respond
        parts.append("<|im_start|>assistant\n")
        
        return "".join(parts)
    
    def generate_response(self, session_id: str, user_message: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        """Generate AI response for a chat session"""
        if not self.model_loaded:
            raise RuntimeError("AI model not loaded")
        
        try:
            # Add user message to history
            self.add_user_message(session_id, user_message)
            
            # Get session
            session = self.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Build prompt
            prompt = self.build_chatml_prompt(
                session["system_prompt"],
                session["history"],
                session["message_roles"]
            )
            
            logger.info(f"📝 Generated prompt: {len(prompt)} characters")
            logger.info(f"📝 History: {len(session['history'])} messages")
            
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096,
                padding=True
            )
            
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                generation_start = time.time()
                
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    top_k=50,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    max_time=settings.ai_generation_timeout
                )
                
                generation_time = time.time() - generation_start
                
                # Decode response
                response = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
                
                # Clean up response
                response = response.strip()
                if response.endswith("<|im_end|>"):
                    response = response[:-10].strip()
                
                logger.info(f"⚙️ Generated response in {generation_time:.2f}s: {len(response)} chars")
                
                # Add assistant response to history
                self.add_assistant_message(session_id, response)
                
                return response
                
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            raise
    
    def optimize_memory_usage(self):
        """Optimize GPU memory usage"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            
            memory_allocated = torch.cuda.memory_allocated() / 1024**3
            memory_reserved = torch.cuda.memory_reserved() / 1024**3
            
            logger.info(f"🚀 GPU Memory: {memory_allocated:.2f}GB allocated, {memory_reserved:.2f}GB reserved")
            
            if memory_allocated > 8.0:
                logger.warning(f"⚠️ High GPU memory usage: {memory_allocated:.2f}GB")
                gc.collect()
                torch.cuda.empty_cache()
    
    def get_health_status(self) -> Dict:
        """Get AI model health status"""
        return {
            "model_loaded": self.model_loaded,
            "model_name": settings.ai_model_name,
            "device": str(self.model.device) if self.model else "None",
            "active_sessions": len(self.user_sessions),
            "gpu_available": torch.cuda.is_available(),
            "gpu_memory_allocated": round(torch.cuda.memory_allocated() / 1024**3, 2) if torch.cuda.is_available() else 0,
            "gpu_memory_reserved": round(torch.cuda.memory_reserved() / 1024**3, 2) if torch.cuda.is_available() else 0
        }

# Global AI model manager instance
ai_model_manager = AIModelManager() 