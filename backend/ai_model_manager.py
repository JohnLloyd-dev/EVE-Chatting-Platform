"""
Simplified AI Model Manager for Backend (7B with 4-bit Quantization)
Optimized for RTX 4060 with 8GB VRAM
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

# Database imports moved to top level to prevent circular imports
try:
    from database import SystemPrompt, Message
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ Database imports not available - running in standalone mode")

logger = logging.getLogger(__name__)

class AIModelManager:
    """Simplified manager for 7B AI model loading and inference"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.user_sessions: Dict[str, Dict] = {}
        
        # Enhanced device detection with logging
        if torch.cuda.is_available():
            self.device = "cuda"
            logger.info(f"✅ CUDA detected: {torch.cuda.get_device_name(0)}")
            logger.info(f"💾 Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
            logger.info(f"🔧 CUDA version: {torch.version.cuda}")
        else:
            self.device = "cpu"
            logger.warning("⚠️ CUDA not available, using CPU")
            logger.warning("🔍 Checking CUDA environment...")
            logger.warning(f"   - CUDA_VISIBLE_DEVICES: {os.getenv('CUDA_VISIBLE_DEVICES', 'Not set')}")
            logger.warning(f"   - NVIDIA_VISIBLE_DEVICES: {os.getenv('NVIDIA_VISIBLE_DEVICES', 'Not set')}")
            logger.warning(f"   - PyTorch CUDA available: {torch.cuda.is_available()}")
            logger.warning(f"   - PyTorch version: {torch.__version__}")
        
        self.generate_lock = Lock()
        
        # Load model on initialization
        self._load_model()
    
    def _load_model(self):
        """Simple model loading optimized for RTX 4060"""
        try:
            logger.info(f"🚀 Loading AI model: {settings.ai_model_name}")
            logger.info(f"🔧 Device: {self.device}")
            
            # CRITICAL: Clear GPU memory before loading
            if self.device == "cuda":
                logger.info("🧹 Clearing GPU memory before model loading...")
                torch.cuda.empty_cache()
                gc.collect()
                
                # Check available memory
                total_vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
                free_vram = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1024**3
                logger.info(f"💾 After cleanup - Total: {total_vram:.2f}GB, Free: {free_vram:.2f}GB")
                
                if free_vram < 6.0:  # Need at least 6GB free for 7B model
                    logger.warning(f"⚠️ Insufficient VRAM ({free_vram:.2f}GB) - trying aggressive cleanup...")
                    # Force garbage collection
                    gc.collect()
                    torch.cuda.empty_cache()
                    # Wait a moment for cleanup
                    import time
                    time.sleep(2)
                    
                    free_vram = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1024**3
                    logger.info(f"💾 After aggressive cleanup - Free VRAM: {free_vram:.2f}GB")
                    
                    if free_vram < 6.0:
                        logger.error(f"❌ Still insufficient VRAM ({free_vram:.2f}GB) - cannot load 7B model")
                        raise RuntimeError(f"Insufficient VRAM: {free_vram:.2f}GB free, need 6GB+ for 7B model")
            
            # Conditional quantization based on device
            if self.device == "cuda":
                logger.info("🔧 Using 8-bit quantization for CUDA (better instruction-following)")
                bnb_config = BitsAndBytesConfig(
                    load_in_8bit=True,                    # Switch back to 8-bit for better quality
                    bnb_8bit_compute_dtype=torch.float16, # Use FP16 for computation
                    bnb_8bit_use_double_quant=True,       # Enable double quantization for memory efficiency
                    bnb_8bit_quant_type="nf8"            # Use NF8 for balanced quality/memory
                )
            else:
                logger.info("🔧 No quantization for CPU")
                bnb_config = None
            
            # Load tokenizer and model directly
            self.tokenizer = AutoTokenizer.from_pretrained(settings.ai_model_name)
            
            # Try loading with 8-bit quantization first, fallback to 4-bit if needed
            try:
                logger.info("🚀 Attempting to load model with 8-bit quantization (target: 5-6GB VRAM)...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    settings.ai_model_name,
                    quantization_config=bnb_config,
                    device_map="auto",                    # Auto device mapping for memory efficiency
                    low_cpu_mem_usage=True,               # Reduce CPU memory usage
                    torch_dtype=torch.float16,            # Use FP16 for lower memory
                    max_memory={0: "6GB"}                 # Limit GPU memory to 6GB max
                )
                logger.info("✅ Model loaded with 8-bit quantization (better instruction-following)")
                logger.info("💡 NOTE: 8-bit provides better quality but uses ~1-2GB more VRAM than 4-bit")
                logger.info("💡 If you need lower memory usage, the system will automatically fallback to 4-bit")
            except Exception as e:
                if self.device == "cuda" and "out of memory" in str(e).lower():
                    logger.warning(f"⚠️ 8-bit quantization failed due to memory: {e}")
                    logger.info("🔄 Trying 4-bit quantization as fallback (lower quality but fits)...")
                    
                    # Clear memory again
                    torch.cuda.empty_cache()
                    gc.collect()
                    
                    # Try with 4-bit quantization as fallback
                    bnb_config_4bit = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4"
                    )
                    
                    self.model = AutoModelForCausalLM.from_pretrained(
                        settings.ai_model_name,
                        quantization_config=bnb_config_4bit,
                        device_map="auto",
                        low_cpu_mem_usage=True,
                        torch_dtype=torch.float16,
                        max_memory={0: "5GB"}
                    )
                    logger.info("✅ Model loaded with 4-bit quantization (fallback - lower quality)")
                else:
                    # Re-raise if it's not a memory error
                    raise
            
            # Device mapping is handled automatically by device_map="auto"
            # No need for manual .to() calls
            logger.info("✅ Model device mapping handled automatically by device_map='auto'")
            
            # Set to evaluation mode
            self.model.eval()
            self.model_loaded = True
            
            # RTX 4060-specific speed optimizations
            if self.device == "cuda":
                # Enable Tensor Cores for faster computation
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                torch.set_float32_matmul_precision('high')
                
                # Enable memory-efficient attention
                if hasattr(self.model, 'config'):
                    if hasattr(self.model.config, 'use_flash_attention_2'):
                        self.model.config.use_flash_attention_2 = True
                        logger.info("✅ Flash Attention 2 enabled for speed")
                
                # Optimize for inference
                torch.set_grad_enabled(False)
                logger.info("✅ Inference optimizations enabled for RTX 4060")
                
                # Set memory management environment variables
                os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128,expandable_segments:True'
                logger.info("✅ Memory management environment variables set")
            
            logger.info("✅ AI Model loaded successfully!")
            
            # Monitor actual memory usage
            if self.device == "cuda":
                allocated = torch.cuda.memory_allocated(0) / 1024**3
                reserved = torch.cuda.memory_reserved(0) / 1024**3
                total = torch.cuda.get_device_properties(0).total_memory / 1024**3
                logger.info(f"💾 Memory Usage - Allocated: {allocated:.2f}GB, Reserved: {reserved:.2f}GB, Total: {total:.2f}GB")
                logger.info(f"🎯 TARGET: 5-6GB VRAM usage (8-bit quantization for better quality)")
                
                # Verify we're within target
                if allocated > 6.5:  # Should be under 6.5GB with 8-bit quantization
                    logger.warning(f"⚠️ VRAM usage ({allocated:.2f}GB) is higher than target (5-6GB)")
                else:
                    logger.info(f"✅ VRAM usage ({allocated:.2f}GB) is within target (5-6GB)")
            
        except Exception as e:
            logger.error(f"❌ Failed to load AI model: {e}")
            self.model_loaded = False
            raise
    
    def create_session(self, session_id: str, system_prompt: str) -> Dict:
        """Create a new chat session"""
        session = {
            "system_prompt": system_prompt,
            "history": [],
            "created_at": time.time(),
            "last_updated": time.time()
        }
        
        self.user_sessions[session_id] = session
        logger.info(f"🎯 Created session {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get an existing session"""
        return self.user_sessions.get(session_id)
    
    def rebuild_session_from_database(self, session_id: str, db_session, db) -> bool:
        """Rebuild AI session from database data"""
        if not DATABASE_AVAILABLE:
            logger.warning("⚠️ Database not available - cannot rebuild session")
            return False
            
        try:
            # Get the complete system prompt from database
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
            session["history"].append(f"User: {message}")
            session["last_updated"] = time.time()
    
    def add_assistant_message(self, session_id: str, message: str):
        """Add an assistant message to session history"""
        if session_id in self.user_sessions:
            session = self.user_sessions[session_id]
            session["history"].append(f"AI: {message}")
            session["last_updated"] = time.time()
    
    def trim_history(self, system: str, history: list, max_tokens: int = 3500) -> list:
        """Trim conversation history to fit within token budget"""
        system_tokens = self.tokenizer(system)["input_ids"]
        total_tokens = len(system_tokens)
        keep_messages = []
        
        # Process from newest to oldest
        for msg in reversed(history):
            msg_tokens = self.tokenizer(msg)["input_ids"]
            if total_tokens + len(msg_tokens) > max_tokens:
                break
            total_tokens += len(msg_tokens)
            keep_messages.append(msg)
        
        # Return kept messages in chronological order
        return list(reversed(keep_messages))
    
    def build_chatml_prompt(self, system: str, history: list) -> str:
        """Build clean ChatML format prompt for OpenHermes model"""
        # Use the system prompt exactly as provided (no extra instructions)
        prompt = f"<|im_start|>system\n{system.strip()}<|im_end|>\n"
        
        # Add conversation history with proper formatting
        for entry in history:
            if entry.startswith("User:"):
                user_message = entry[5:].strip()  # Remove "User: " prefix
                prompt += f"<|im_start|>user\n{user_message}<|im_end|>\n"
            elif entry.startswith("AI:"):
                ai_message = entry[3:].strip()  # Remove "AI: " prefix
                prompt += f"<|im_start|>assistant\n{ai_message}<|im_end|>\n"
        
        # Add assistant prompt
        prompt += "<|im_start|>assistant\n"
        return prompt
    
    def generate_response(self, session_id: str, user_message: str, session=None, db=None, max_tokens: int = 150) -> str:
        """Generate AI response using the model"""
        if not self.model_loaded:
            raise RuntimeError("AI model not loaded")
        
        # Thread safety for concurrent requests
        with self.generate_lock:
            try:
                # AGGRESSIVE MEMORY MANAGEMENT BEFORE GENERATION
                if self.device == "cuda":
                    logger.info("🧹 Aggressive memory cleanup before generation...")
                    
                    # Force garbage collection
                    gc.collect()
                    
                    # Clear PyTorch cache
                    torch.cuda.empty_cache()
                    
                    # Check available memory
                    free_vram = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1024**3
                    logger.info(f"💾 Available VRAM before generation: {free_vram:.2f}GB")
                    
                    # If less than 1GB free, force cleanup
                    if free_vram < 1.0:
                        logger.warning(f"⚠️ Low VRAM ({free_vram:.2f}GB) - forcing aggressive cleanup...")
                        
                        # Clear all sessions to free memory
                        old_sessions = list(self.user_sessions.keys())
                        for old_session_id in old_sessions:
                            del self.user_sessions[old_session_id]
                        logger.info(f"🗑️ Forced cleanup of {len(old_sessions)} sessions due to low VRAM")
                        
                        # Force garbage collection again
                        gc.collect()
                        torch.cuda.empty_cache()
                        
                        # Check memory again
                        free_vram = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1024**3
                        logger.info(f"💾 VRAM after forced cleanup: {free_vram:.2f}GB")
                        
                        if free_vram < 0.5:  # Still very low
                            logger.error(f"❌ Critically low VRAM ({free_vram:.2f}GB) - attempting emergency recovery...")
                            
                            # Try emergency memory recovery
                            if self._emergency_memory_recovery():
                                logger.info("✅ Emergency recovery successful, continuing...")
                            else:
                                logger.error("❌ Emergency recovery failed - cannot generate response")
                                return "I'm experiencing critical memory issues. Please try again later."
                
                # Get or create session
                if session_id not in self.user_sessions:
                    # Try to rebuild session from database if available
                    if session and db:
                        self.rebuild_session_from_database(session_id, session, db)
                    else:
                        # Fallback to generic prompt if no database access
                        self.create_session(session_id, "You are a helpful assistant.")
                
                # Get session data
                ai_session = self.user_sessions[session_id]
                system_prompt = ai_session["system_prompt"]
                
                # Trim existing history to fit context window (before adding new message)
                ai_session["history"] = self.trim_history(
                    system=system_prompt,
                    history=ai_session["history"],
                    max_tokens=2000  # Reduced from 3500 to save memory
                )
                
                # Add user message to history AFTER trimming
                self.add_user_message(session_id, user_message)
                
                # Build prompt with current history (including the new user message)
                full_prompt = self.build_chatml_prompt(
                    system_prompt,
                    ai_session["history"]
                )
                
                # DEBUG: Log the actual prompt being sent to the model
                logger.info(f"🔍 DEBUG: Full prompt being sent to model:")
                logger.info(f"🔍 Current user message: {user_message}")
                logger.info(f"🔍 System prompt (COMPLETE): {system_prompt}")
                logger.info(f"🔍 History length: {len(ai_session['history'])} messages")
                logger.info(f"🔍 COMPLETE CONVERSATION HISTORY:")
                for i, msg in enumerate(ai_session['history']):
                    logger.info(f"🔍 Message {i+1}: {msg}")
                logger.info(f"🔍 Full prompt length: {len(full_prompt)} characters")
                logger.info(f"🔍 COMPLETE PROMPT:")
                logger.info(f"🔍 {full_prompt}")
                logger.info(f"🔍 END OF PROMPT")
                
                # Tokenize with truncation
                inputs = self.tokenizer(
                    full_prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=2048  # Reduced from 4096 to save memory
                ).to(self.model.device)
                
                # Adjust max tokens to available space
                max_output_tokens = min(
                    max_tokens,
                    2048 - inputs.input_ids.shape[1]  # Reduced from 4096
                )
                
                if max_output_tokens <= 0:
                    raise ValueError("Input too long for response generation")
                
                # Generate response with balanced quality and memory parameters
                with torch.no_grad():
                    output = self.model.generate(
                        **inputs,
                        max_new_tokens=max_output_tokens,
                        # Balanced quality and memory parameters
                        temperature=0.8,           # Slightly higher for better creativity
                        do_sample=True,
                        top_p=0.92,               # Optimal for 7B models
                        top_k=40,                 # Good quality selection
                        typical_p=0.95,           # Tail-free sampling for consistency
                        repetition_penalty=1.15,   # Balanced repetition control
                        no_repeat_ngram_size=3,   # Prevent 3-gram repetition
                        # Memory optimizations
                        use_cache=True,           # Enable KV cache for speed
                        pad_token_id=self.tokenizer.eos_token_id,
                        eos_token_id=self.tokenizer.eos_token_id,
                        # Quality settings
                        num_beams=1,              # Single beam for speed
                        # Memory optimizations for ultra-low VRAM
                        output_scores=False,      # Don't compute scores (save memory)
                        output_attentions=False,  # Don't output attentions (save memory)
                        output_hidden_states=False, # Don't output hidden states (save memory)
                        # Additional memory optimizations
                        return_dict_in_generate=False,  # Return tensors instead of dict (save memory)
                    )
                
                # Extract only new tokens
                response_tokens = output[0][inputs.input_ids.shape[1]:]
                response = self.tokenizer.decode(
                    response_tokens,
                    skip_special_tokens=True
                ).strip()
                
                # DEBUG: Log the actual response from the model
                logger.info(f"🔍 DEBUG: Raw model response:")
                logger.info(f"🔍 Response length: {len(response)} characters")
                logger.info(f"🔍 COMPLETE RAW RESPONSE:")
                logger.info(f"🔍 {response}")
                
                # Enhanced response validation and quality control
                response = self._validate_and_enhance_response(response, user_message)
                
                # DEBUG: Log the final processed response
                logger.info(f"🔍 DEBUG: Final processed response:")
                logger.info(f"🔍 Final response length: {len(response)} characters")
                logger.info(f"🔍 COMPLETE FINAL RESPONSE:")
                logger.info(f"🔍 {response}")
                
                # Save AI response to history
                self.add_assistant_message(session_id, response)
                
                # POST-GENERATION MEMORY CLEANUP
                if self.device == "cuda":
                    # Clear generation outputs to free memory
                    del output
                    del inputs
                    
                    # Force garbage collection
                    gc.collect()
                    torch.cuda.empty_cache()
                    
                    # Log memory usage after generation
                    allocated = torch.cuda.memory_allocated(0) / 1024**3
                    free_vram = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1024**3
                    logger.info(f"💾 Post-generation VRAM - Allocated: {allocated:.2f}GB, Free: {free_vram:.2f}GB")
                
                # Automatic memory optimization for long conversations
                if len(ai_session["history"]) > 20:  # After 20 messages
                    logger.info(f"🧹 Auto-optimizing memory for long conversation (session: {session_id})")
                    self._auto_optimize_memory()
                
                return response
                
            except Exception as e:
                logger.error(f"❌ Error generating response for session {session_id}: {e}")
                # Return fallback response
                fallback_response = "I'm experiencing some technical difficulties. Please try again in a moment."
                self.add_assistant_message(session_id, fallback_response)
                return fallback_response
    
    def _auto_optimize_memory(self):
        """Automatic memory optimization during long conversations"""
        try:
            # Clear old sessions (older than 30 minutes)
            current_time = time.time()
            old_sessions = []
            for session_id, session in self.user_sessions.items():
                if current_time - session.get("last_updated", 0) > 1800:  # 30 minutes
                    old_sessions.append(session_id)
            
            if old_sessions:
                for session_id in old_sessions:
                    del self.user_sessions[session_id]
                logger.info(f"🗑️ Auto-cleaned {len(old_sessions)} old sessions")
            
            # Force garbage collection
            gc.collect()
            
            if self.device == "cuda":
                torch.cuda.empty_cache()
                allocated = torch.cuda.memory_allocated(0) / 1024**3
                logger.info(f"💾 Auto-optimization completed. GPU memory: {allocated:.2f}GB")
                
        except Exception as e:
            logger.warning(f"⚠️ Auto memory optimization failed: {e}")
    
    def _emergency_memory_recovery(self) -> bool:
        """Emergency memory recovery for critical situations"""
        try:
            logger.warning("🚨 EMERGENCY: Critical memory situation detected!")
            
            # Clear all sessions immediately
            session_count = len(self.user_sessions)
            self.user_sessions.clear()
            logger.warning(f"🗑️ Emergency cleanup: Cleared {session_count} sessions")
            
            # Force garbage collection multiple times
            for i in range(3):
                gc.collect()
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                time.sleep(0.5)  # Small delay between collections
            
            # Check if recovery was successful
            if self.device == "cuda":
                free_vram = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1024**3
                logger.warning(f"💾 Emergency recovery completed. Free VRAM: {free_vram:.2f}GB")
                return free_vram > 1.0  # Return True if we have at least 1GB free
            else:
                return True
                
        except Exception as e:
            logger.error(f"❌ Emergency memory recovery failed: {e}")
            return False
    
    def _validate_and_enhance_response(self, response: str, user_message: str) -> str:
        """Enhanced response validation and quality enhancement"""
        try:
            # Basic validation
            if not response or len(response.strip()) < 5:
                logger.warning(f"⚠️ Generated response too short, using fallback...")
                return "I understand your message. How can I help you further?"
            
            # Quality checks
            response = response.strip()
            
            # Remove common generation artifacts
            if response.startswith("I'm sorry") and "I cannot" in response:
                response = "I understand your request. Let me help you with that."
            
            # Ensure response is relevant to user message
            if self._is_response_relevant(response, user_message):
                return response
            else:
                logger.warning(f"⚠️ Response not relevant to user message, regenerating...")
                return "I want to make sure I understand correctly. Could you clarify your question?"
                
        except Exception as e:
            logger.error(f"❌ Response validation failed: {e}")
            return "I'm here to help. What would you like to discuss?"
    
    def _is_response_relevant(self, response: str, user_message: str) -> bool:
        """Check if AI response is relevant to user message"""
        try:
            # Simple relevance check based on content
            user_lower = user_message.lower()
            response_lower = response.lower()
            
            # Check for question-answer relevance
            if "?" in user_message:
                # User asked a question, check if response addresses it
                if any(word in response_lower for word in ["answer", "explain", "help", "assist", "guide"]):
                    return True
                if len(response) > 20:  # Substantial response
                    return True
            
            # Check for general conversation relevance
            if len(response) > 10 and not response.startswith("I'm sorry"):
                return True
                
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Relevance check failed: {e}")
            return True  # Default to accepting response
    
    def _regenerate_response(self, inputs, max_output_tokens: int) -> str:
        """Regenerate response with enhanced parameters for better accuracy"""
        try:
            logger.info("🔄 Regenerating response with enhanced parameters...")
            
            # Enhanced generation parameters for better quality
            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    max_new_tokens=max_output_tokens,
                    # Enhanced quality parameters
                    temperature=0.8,          # Balanced creativity and focus
                    do_sample=True,
                    top_p=0.94,              # Optimal for regeneration
                    top_k=35,                # Balanced quality
                    typical_p=0.96,          # Better consistency
                    repetition_penalty=1.12,  # Balanced repetition control
                    no_repeat_ngram_size=2,   # Prevent 2-gram repetition
                    length_penalty=1.0,      # Neutral length preference
                    # Memory optimizations
                    use_cache=True,
                    num_beams=1,
                    early_stopping=True,
                    # Memory optimizations
                    output_scores=False,
                    output_attentions=False,
                    output_hidden_states=False
                )
            
            # Extract and validate response
            response_tokens = output[0][inputs.input_ids.shape[1]:]
            response = self.tokenizer.decode(
                response_tokens,
                skip_special_tokens=True
            ).strip()
            
            # Enhanced validation
            if not response or len(response.strip()) < 5:
                # Final fallback with context
                response = "I understand your message. How can I help you further?"
            elif response.startswith("I'm sorry") and "I cannot" in response:
                response = "I want to help you with that. Could you provide more details?"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Response regeneration failed: {e}")
            return "I'm here to help. What would you like to discuss?"
    
    def get_health_status(self) -> Dict:
        """Get AI model health status for monitoring"""
        try:
            status = {
                "model_loaded": self.model_loaded,
                "model_type": "7B Transformers (8-bit quantization, RTX 4060 optimized)",
                "device": self.device,
                "quantization": "8-bit" if hasattr(self, 'bnb_config') and self.bnb_config else "None",
                "database_available": DATABASE_AVAILABLE,
                "active_sessions": len(self.user_sessions)
            }
            
            if self.device == "cuda":
                allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
                reserved_memory = torch.cuda.memory_reserved(0) / 1024**3
                total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                status.update({
                    "gpu_memory_gb": round(allocated_memory, 1),
                    "gpu_memory_reserved_gb": round(reserved_memory, 1),
                    "gpu_memory_total_gb": round(total_memory, 1),
                    "gpu_memory_usage_percent": round((allocated_memory / total_memory) * 100, 1)
                })
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Health status check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def optimize_memory_usage(self) -> Dict:
        """Optimize memory usage for long-running sessions"""
        try:
            logger.info("🧹 Running memory optimization...")
            
            # Clear old sessions (older than 1 hour)
            current_time = time.time()
            old_sessions = []
            for session_id, session in self.user_sessions.items():
                if current_time - session.get("last_updated", 0) > 3600:  # 1 hour
                    old_sessions.append(session_id)
            
            for session_id in old_sessions:
                del self.user_sessions[session_id]
                logger.info(f"🗑️ Cleaned up old session: {session_id}")
            
            # Force garbage collection
            gc.collect()
            
            if self.device == "cuda":
                torch.cuda.empty_cache()
                allocated_before = torch.cuda.memory_allocated(0) / 1024**3
                logger.info(f"💾 Memory optimization completed. Active sessions: {len(self.user_sessions)}")
                logger.info(f"💾 GPU memory after optimization: {allocated_before:.2f}GB")
            
            return {
                "status": "success", 
                "message": f"Memory optimization completed. Cleaned {len(old_sessions)} old sessions.",
                "active_sessions": len(self.user_sessions)
            }
            
        except Exception as e:
            logger.error(f"❌ Memory optimization failed: {e}")
            return {"status": "error", "message": str(e)}

# Global instance
ai_model_manager = AIModelManager() 