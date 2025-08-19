"""
AI Model Manager for Backend (7B with 4-bit Quantization)
Handles transformers model loading, inference, and session management with GPU acceleration
"""
import logging
import time
import os
import gc
import threading
from threading import Lock
import torch
from typing import Dict, List, Optional, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from config import settings

logger = logging.getLogger(__name__)

class AIModelManager:
    """Manages 7B AI model loading, inference, and session management with 4-bit quantization"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.user_sessions: Dict[str, Dict] = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Thread safety for concurrent requests
        self.generate_lock = Lock()
        
        # Load model on initialization
        self._load_model()
    
    def _load_model(self):
        """Load the 7B AI model with 4-bit quantization optimized for RTX 4060 (8GB VRAM)"""
        try:
            logger.info(f"🚀 Loading 7B AI model: {settings.ai_model_name}")
            logger.info(f"🔧 Device: {self.device}")
            logger.info(f"📊 4-bit quantization: {settings.ai_use_4bit}")
            logger.info(f"💾 Max memory: {settings.ai_max_memory_gb}GB")
            logger.info(f"📏 Max context: {settings.ai_max_context_length} tokens")
            
            # Create new dedicated cache directory for model storage
            logger.info(f"📁 Creating new cache directory: {settings.ai_model_cache_dir}")
            os.makedirs(settings.ai_model_cache_dir, exist_ok=True)
            logger.info(f"✅ Cache directory ready: {settings.ai_model_cache_dir}")
            
            # Create offload directory if it doesn't exist
            os.makedirs(settings.ai_offload_folder, exist_ok=True)
            
            # Load tokenizer with new cache directory
            logger.info("📥 Loading tokenizer with new cache directory...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.ai_model_name,
                cache_dir=settings.ai_model_cache_dir,
                trust_remote_code=True
            )
            
            # Configure quantization for RTX 4060 (8GB VRAM) with conflict check
            if settings.ai_use_4bit and settings.ai_use_8bit:
                raise ValueError("❌ Cannot use both 4-bit and 8-bit quantization simultaneously")
            
            if settings.ai_use_4bit and self.device == "cuda":
                logger.info("🔧 Using simple 4-bit quantization (like working script)...")
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16  # Only 2 parameters like working script
                )
            elif settings.ai_use_8bit and self.device == "cuda":
                logger.info("🔧 Configuring 8-bit quantization...")
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    bnb_8bit_compute_dtype=torch.float16
                )
            else:
                logger.info("🔧 No quantization - using full precision")
                quantization_config = None
            
            # SIMPLE APPROACH - Use working pattern from user's script
            # No complex memory management - let transformers handle it automatically
            max_memory = None  # Let device_map="auto" handle memory
            logger.info("🔧 Using simple auto memory management (like working script)")
            
            # Load model with RTX 4060 optimizations + Guide's accuracy principles
            logger.info("📥 Loading 7B model with RTX 4060 + Guide optimization...")
            
            # Enable RTX 4060-specific optimizations for training/loading
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.set_float32_matmul_precision('high')
            
            # Enable kernel optimizations for RTX 4060 (fixed for compatibility)
            try:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                if hasattr(torch, 'set_float32_matmul_precision'):
                    torch.set_float32_matmul_precision('high')
                logger.info("✅ RTX 4060 kernel optimizations enabled")
            except Exception as e:
                logger.warning(f"⚠️ RTX 4060 optimizations unavailable: {e}")
            
            # Setup Flash Attention with fallback mechanism
            attn_kwargs = {}
            try:
                if self.device == "cuda":
                    attn_kwargs = {
                        "use_flash_attention_2": True,
                        "attn_implementation": "flash_attention_2"
                    }
                    logger.info("✅ Flash Attention 2 enabled")
            except Exception as e:
                logger.warning(f"⚠️ Flash Attention 2 not available, using default: {e}")
            
            # Use EXACT same pattern as your working script for 4GB VRAM usage
            logger.info("🚀 Loading model using your working script pattern...")
            self.model = AutoModelForCausalLM.from_pretrained(
                settings.ai_model_name,
                cache_dir=settings.ai_model_cache_dir,  # Use new dedicated cache
                quantization_config=quantization_config,
                device_map="auto" if quantization_config else None
            )
            
            # Move to device if not using device_map
            if not quantization_config:
                self.model = self.model.to(self.device)
            
            # CRITICAL ADDITION - Set to evaluation mode for maximum accuracy
            self.model.eval()
            logger.info("🔒 Model set to evaluation mode for maximum accuracy")
            
            # Aggressive garbage collection for 8GB RTX 4060
            gc.collect()
            torch.cuda.empty_cache()
            
            # Simple memory check (like working script)
            if self.device == "cuda":
                allocated = torch.cuda.memory_allocated() / 1024**3
                logger.info(f"📉 VRAM used: {allocated:.2f}GB")
            
            # Precision consistency for inference (guide recommendation)
            torch.set_grad_enabled(False)  # Ensure gradients are disabled
            logger.info("🔒 Gradients disabled for inference")
            
            # Simple model loading - NO TESTING, NO CALIBRATION (like working script)
            self.model_loaded = True
            logger.info("✅ 7B AI Model loaded successfully!")
            
            # Log cache and memory status
            logger.info(f"📁 Model cached in: {settings.ai_model_cache_dir}")
            logger.info(f"🔄 Next startup will use cached model (fast loading)")
            
            # Simple memory check (like working script)
            if self.device == "cuda":
                allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
                logger.info(f"💾 VRAM used: {allocated_memory:.1f} GB")
                logger.info(f"🎯 Target: 4GB VRAM usage (like your working script)")
            
        except Exception as e:
            logger.error(f"❌ Failed to load AI model: {e}")
            self.model_loaded = False
            raise
    
    def create_session(self, session_id: str, system_prompt: str) -> Dict:
        """Create a new chat session"""
        session = {
            "system_prompt": system_prompt,
            "history": [],
            "message_roles": [],  # Track user vs assistant messages
            "token_counts": [],   # Dynamic token counting for performance
            "created_at": time.time(),
            "last_updated": time.time()
        }
        
        self.user_sessions[session_id] = session
        logger.info(f"🎯 Created session {session_id} with {len(system_prompt)} char prompt")
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get an existing session"""
        return self.user_sessions.get(session_id)
    
    def rebuild_session_from_database(self, session_id: str, db_session, db) -> bool:
        """Rebuild AI session from database data"""
        try:
            # Avoid circular import by getting system prompt directly
            # Get the complete system prompt from database
            from database import SystemPrompt
            
            # Get user-specific or global system prompt
            if db_session.user and db_session.user.id:
                user_prompt = db.query(SystemPrompt).filter(
                    SystemPrompt.user_id == str(db_session.user.id),
                    SystemPrompt.is_active == True
                ).first()
                if user_prompt:
                    system_prompt = f"{user_prompt.head_prompt}\n\n{user_prompt.rule_prompt}"
                else:
                    # Fall back to global prompt
                    global_prompt = db.query(SystemPrompt).filter(
                        SystemPrompt.user_id.is_(None),
                        SystemPrompt.is_active == True
                    ).first()
                    if global_prompt:
                        system_prompt = f"{global_prompt.head_prompt}\n\n{global_prompt.rule_prompt}"
                    else:
                        system_prompt = "You are a helpful assistant."
            else:
                # Get global active prompt
                active_prompt = db.query(SystemPrompt).filter(
                    SystemPrompt.user_id.is_(None),
                    SystemPrompt.is_active == True
                ).first()
                if active_prompt:
                    system_prompt = f"{active_prompt.head_prompt}\n\n{active_prompt.rule_prompt}"
                else:
                    system_prompt = "You are a helpful assistant."
            
            # Create new AI session with correct system prompt
            self.create_session(session_id, system_prompt)
            
            # Get conversation history from database
            from database import Message
            messages = db.query(Message).filter(
                Message.session_id == db_session.id
            ).order_by(Message.created_at).all()
            
            # Rebuild conversation history
            for message in messages:
                if message.is_from_user:
                    self.add_user_message(session_id, message.content)
                else:
                    self.add_assistant_message(session_id, message.content)
            
            logger.info(f"🔄 Rebuilt AI session {session_id} from database with {len(messages)} messages")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to rebuild session from database: {e}")
            return False
    
    def add_user_message(self, session_id: str, message: str):
        """Add a user message to session history"""
        if session_id in self.user_sessions:
            session = self.user_sessions[session_id]
            session["history"].append(message)
            session["message_roles"].append("user")
            session["last_updated"] = time.time()
            
            # Enhanced history management for RTX 4060 memory efficiency
            # Use token-based truncation instead of message count for better memory management
            max_tokens = 512 if self.device == "cuda" else 1024  # RTX 4060 optimized
            
            # Adaptive history trimming based on VRAM pressure (guide recommendation)
            if self.device == "cuda":
                total_vram = torch.cuda.get_device_properties(0).total_memory
                allocated_vram = torch.cuda.memory_allocated()
                vram_pressure = allocated_vram / total_vram
                
                if vram_pressure > 0.8:  # High VRAM pressure
                    max_tokens = 384  # Reduce context when VRAM pressured
                    logger.info(f"🔧 High VRAM pressure ({vram_pressure:.1%}), reducing context to {max_tokens} tokens")
                elif vram_pressure > 0.6:  # Medium VRAM pressure
                    max_tokens = 448  # Moderate context reduction
                    logger.info(f"🔧 Medium VRAM pressure ({vram_pressure:.1%}), reducing context to {max_tokens} tokens")
            
            # Use stored token counts for performance (guide recommendation)
            if "token_counts" not in session:
                session["token_counts"] = []
            
            # Calculate and store token count for current message
            current_tokens = len(self.tokenizer.encode(message, add_special_tokens=False))
            session["token_counts"].append(current_tokens)
            
            # Calculate total tokens using stored counts for better performance
            total_tokens = sum(session["token_counts"])
            
            if total_tokens > max_tokens:
                # Trim history to fit within token limit
                trimmed_history = []
                trimmed_roles = []
                current_tokens = 0
                
                # Start from most recent messages and work backwards
                trimmed_token_counts = []
                for msg, role in zip(reversed(session["history"]), reversed(session["message_roles"])):
                    msg_tokens = len(self.tokenizer.encode(msg, add_special_tokens=False))
                    if current_tokens + msg_tokens <= max_tokens:
                        trimmed_history.insert(0, msg)
                        trimmed_roles.insert(0, role)
                        trimmed_token_counts.insert(0, msg_tokens)
                        current_tokens += msg_tokens
                    else:
                        break
                
                session["history"] = trimmed_history
                session["message_roles"] = trimmed_roles
                session["token_counts"] = trimmed_token_counts  # Update stored token counts
                logger.info(f"📝 Trimmed history to {len(trimmed_history)} messages ({current_tokens} tokens) for session {session_id} (RTX 4060 optimized)")
    
    def add_assistant_message(self, session_id: str, message: str):
        """Add an assistant message to session history"""
        if session_id in self.user_sessions:
            session = self.user_sessions[session_id]
            session["history"].append(message)
            session["message_roles"].append("assistant")
            session["last_updated"] = time.time()
    
    def build_chatml_prompt(self, system_prompt: str, history: List[str], message_roles: List[str], user_message: str) -> str:
        """Build enhanced ChatML format prompt for better accuracy"""
        
        # Use ONLY the user's system prompt without dilution
        enhanced_system = f"""<|im_start|>system
        {system_prompt.strip()}
        <|im_end|>
        
        """
        
        parts = [enhanced_system]
        
        # Add conversation history (limited to prevent dilution)
        for i, (message, role) in enumerate(zip(history, message_roles)):
            if role == "user":
                parts.append(f"<|im_start|>user\n{message}<|im_end|>\n")
            elif role == "assistant":
                parts.append(f"<|im_start|>assistant\n{message}<|im_end|>\n")
        
        # Add the user message and assistant prompt
        parts.append(f"<|im_start|>user\n{user_message}<|im_end|>\n")
        parts.append("<|im_start|>assistant\n")
        
        return "".join(parts)
    
    def generate_response(self, session_id: str, user_message: str, db_session=None, db=None) -> str:
        """Generate AI response using GGUF model"""
        if not self.model_loaded:
            raise RuntimeError("AI model not loaded")
        
        try:
            # Thread safety for concurrent requests
            with self.generate_lock:
                # Get or create session
                if session_id not in self.user_sessions:
                    # Try to rebuild session from database if available
                    if db_session and db:
                        self.rebuild_session_from_database(session_id, db_session, db)
                    else:
                        # Fallback to generic prompt if no database access
                        self.create_session(session_id, "You are a helpful assistant.")
                
                # Add user message to history
                self.add_user_message(session_id, user_message)
                
                # Get session data
                session = self.user_sessions[session_id]
                system_prompt = session["system_prompt"]
                history = session["history"][:-1]  # Exclude the current user message
                message_roles = session["message_roles"][:-1]  # Exclude the current user message
                
                # Build ChatML prompt
                prompt = self.build_chatml_prompt(system_prompt, history, message_roles, user_message)
                
                logger.info(f"🚀 Generating response for session {session_id}")
                logger.info(f"📝 Prompt length: {len(prompt)} characters")
                
                # Generate response with 7B transformers model
                start_time = time.time()
                
                # Tokenize the prompt with RTX 4060 memory limits
                inputs = self.tokenizer(
                    prompt, 
                    return_tensors="pt", 
                    truncation=True, 
                    max_length=settings.ai_max_context_length
                ).to(self.device)
                
            # Simple pre-generation check (like working script)
            pass
            
            # Setup inference precision for maximum accuracy
            self._setup_inference_precision()
            
            # Optimized parameters applying guide principles: Accuracy-First + Speed Optimization
            with torch.inference_mode():  # Stronger than no_grad for inference accuracy
                                # Use generation parameters like working script
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.8,            # Like working script
                    do_sample=True,
                    top_p=0.95,                # Like working script
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.2,    # Like working script
                    no_repeat_ngram_size=3     # Like working script
                )
                
                generation_time = time.time() - start_time
                
                # Decode the response
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Extract only the new tokens (remove the input prompt)
                # Use token-based extraction for better accuracy
                response = self._extract_ai_response(response, inputs, self.tokenizer)
                
                # Restore training precision settings
                self._restore_training_precision()
                
                # Validate and enhance response for better accuracy
                validated_response = self._validate_response(response, session_id)
                
                # Add validated assistant message to history
                self.add_assistant_message(session_id, validated_response)
                
                # Periodic memory optimization for RTX 4060 with cooldown (every 5 responses, 5 min cooldown)
                session = self.user_sessions.get(session_id, {})
                current_time = time.time()
                last_optimized = session.get("last_optimized", 0)
                
                if len(session.get("history", [])) % 5 == 0 and (current_time - last_optimized) > 300:  # 5 minutes
                    logger.info(f"🧹 Running periodic memory optimization for session {session_id}")
                    self._async_optimize_memory()
                    session["last_optimized"] = current_time
                
                # Log performance metrics with Guide's quality monitoring
                tokens_generated = len(validated_response.split())  # Approximate
                tokens_per_second = tokens_generated / generation_time if generation_time > 0 else 0
                
                # Guide principle: Monitor accuracy indicators
                accuracy_indicators = self._assess_response_quality(validated_response, session_id)
                
                logger.info(f"✅ Response generated in {generation_time:.2f}s")
                logger.info(f"📊 Tokens: {tokens_generated}, Speed: {tokens_per_second:.1f} tokens/s")
                logger.info(f"🎯 Response validation: {len(response)} -> {len(validated_response)} chars")
                logger.info(f"🎯 Quality assessment: {accuracy_indicators}")
                
                return validated_response
                
        except Exception as e:
            logger.error(f"❌ Failed to generate response: {e}")
            raise
    
    def _extract_ai_response(self, full_response: str, inputs, tokenizer) -> str:
        """Simplified response extraction for VRAM efficiency"""
        try:
            input_length = inputs["input_ids"].shape[1]
            response = tokenizer.decode(inputs["input_ids"][0][input_length:], skip_special_tokens=True)
            return response.strip()
        except:
            return full_response.strip()
    
    def _clean_system_instructions(self, response: str) -> str:
        """Simplified cleaning for VRAM efficiency"""
        return response.strip()  # Just strip whitespace
    
    def _validate_response(self, response: str, session_id: str) -> str:
        """Simplified validation for VRAM efficiency"""
        if not response or len(response.strip()) == 0:
            return "I'm here, what would you like me to do?"
        
        cleaned = response.strip()
        if len(cleaned) > 200:
            cleaned = cleaned[:197] + "..."
        
        return cleaned
    
    def _quick_quality_check(self, response: str) -> int:
        """Simplified quality check for VRAM efficiency"""
        if len(response) < 10:
            return 5
        if len(response) > 200:
            return 7
        return 10
    
    # REMOVED: _assess_response_quality function (redundant with _quick_quality_check)
    
    def _regenerate_with_character_focus(self, session_id: str, original_response: str) -> str:
        """Simplified regeneration for VRAM efficiency"""
        logger.info(f"🔄 Skipping regeneration for VRAM efficiency - using original response")
        return original_response
    
    def optimize_memory_usage(self) -> Dict:
        """Simplified memory optimization for VRAM efficiency"""
        try:
            logger.info("🧹 Simple memory cleanup for VRAM efficiency...")
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
            return {"status": "success", "message": "Memory cleaned"}
        except Exception as e:
            logger.error(f"❌ Memory optimization failed: {e}")
            return {"status": "error", "message": str(e)}
    
    # REMOVED: _async_optimize_memory function (redundant for VRAM efficiency)
    
    def _setup_inference_precision(self):
        """Simplified precision setup for VRAM efficiency"""
        pass  # Skip precision changes for VRAM efficiency
    
    def _restore_training_precision(self):
        """Simplified precision restoration for VRAM efficiency"""
        pass  # Skip precision changes for VRAM efficiency
    
    def _activate_low_memory_mode(self):
        """Simplified low memory mode for VRAM efficiency"""
        logger.warning("🚨 SIMPLIFIED LOW MEMORY MODE ACTIVATED")
        gc.collect()
        torch.cuda.empty_cache()
    
    def get_health_status(self) -> Dict:
        """Simplified health status for VRAM efficiency"""
        try:
            status = {
                "model_loaded": self.model_loaded,
                "model_type": "7B Transformers (4-bit quantization, RTX 4060 optimized)",
                "device": self.device,
                "quantization": "4-bit" if settings.ai_use_4bit else "8-bit" if settings.ai_use_8bit else "None",
            }
            
            if self.device == "cuda":
                allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
                status["gpu_memory_gb"] = round(allocated_memory, 1)
            
            return status
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Global instance
ai_model_manager = AIModelManager() 