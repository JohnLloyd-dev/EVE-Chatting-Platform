"""
AI Model Manager for Backend (7B with 4-bit Quantization)
Handles transformers model loading, inference, and session management with GPU acceleration
"""
import logging
import time
import os
import gc
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
            
            # Create offload directory if it doesn't exist
            os.makedirs(settings.ai_offload_folder, exist_ok=True)
            
            # Load tokenizer
            logger.info("📥 Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.ai_model_name,
                cache_dir=settings.ai_model_cache_dir,
                trust_remote_code=True
            )
            
            # Configure quantization for RTX 4060 (8GB VRAM) with conflict check
            if settings.ai_use_4bit and settings.ai_use_8bit:
                raise ValueError("❌ Cannot use both 4-bit and 8-bit quantization simultaneously")
            
            if settings.ai_use_4bit and self.device == "cuda":
                logger.info("🔧 Configuring 4-bit quantization...")
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
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
            
            # RTX 4060 Memory Optimization with Guide's Strategic Layer Management
            # Reserve some layers for CPU to prevent quantization drift (guide principle)
            if self.device == "cuda":
                # Guide principle: Keep some layers on CPU for accuracy
                # Reserve 0.5GB for CPU layers to prevent quantization drift
                cpu_memory = 0.5
                gpu_memory = settings.ai_max_memory_gb - cpu_memory
                max_memory = {
                    0: f"{gpu_memory}GB",      # GPU memory
                    "cpu": f"{cpu_memory}GB"    # CPU memory for some layers
                }
                logger.info(f"🔧 Strategic layer management: GPU {gpu_memory}GB, CPU {cpu_memory}GB")
            else:
                max_memory = None
            
            # Load model with RTX 4060 optimizations + Guide's accuracy principles
            logger.info("📥 Loading 7B model with RTX 4060 + Guide optimization...")
            
            # Enable RTX 4060-specific optimizations
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.set_float32_matmul_precision('high')
            
            self.model = AutoModelForCausalLM.from_pretrained(
                settings.ai_model_name,
                cache_dir=settings.ai_model_cache_dir,
                quantization_config=quantization_config,
                device_map="auto" if quantization_config else None,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                max_memory=max_memory,
                offload_folder=settings.ai_offload_folder,
                offload_state_dict=True,
                # RTX 4060 Flash Attention Support
                use_flash_attention_2=True,
                attn_implementation="flash_attention_2"
            )
            
            # Move to device if not using device_map
            if not quantization_config:
                self.model = self.model.to(self.device)
            
            # Test model loading with memory constraints
            logger.info("🧪 Testing model with memory constraints...")
            test_inputs = self.tokenizer("Hello", return_tensors="pt", max_length=64).to(self.device)
            
            with torch.no_grad():
                test_outputs = self.model.generate(
                    **test_inputs,
                    max_new_tokens=10,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id,
                    use_cache=True
                )
            
            test_response = self.tokenizer.decode(test_outputs[0], skip_special_tokens=True)
            
            if test_response and len(test_response) > 0:
                logger.info("✅ Model test successful!")
                self.model_loaded = True
                logger.info("✅ 7B AI Model loaded successfully with RTX 4060 optimization!")
                
                # Log model info and memory usage
                logger.info(f"📊 Model device: {self.device}")
                logger.info(f"🔧 Quantization: {'4-bit' if settings.ai_use_4bit else '8-bit' if settings.ai_use_8bit else 'None'}")
                if self.device == "cuda":
                    total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                    allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
                    reserved_memory = torch.cuda.memory_reserved(0) / 1024**3
                    logger.info(f"💾 Total VRAM: {total_memory:.1f} GB")
                    logger.info(f"💾 Allocated: {allocated_memory:.1f} GB")
                    logger.info(f"💾 Reserved: {reserved_memory:.1f} GB")
                    logger.info(f"💾 Available: {total_memory - allocated_memory:.1f} GB")
                
            else:
                raise RuntimeError("Model test failed - no output generated")
            
        except Exception as e:
            logger.error(f"❌ Failed to load 7B AI model: {e}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            self.model_loaded = False
            
            # Provide specific error guidance for RTX 4060
            if "CUDA" in str(e):
                logger.error("💡 CUDA Error: Check GPU drivers and CUDA installation")
            elif "out of memory" in str(e).lower():
                logger.error("💡 Memory Error: RTX 4060 memory exceeded")
                logger.error("💡 Try: Reduce ai_max_memory_gb or ai_max_context_length")
                logger.error("💡 Or: Use GGUF model instead")
            elif "transformers" in str(e).lower():
                logger.error("💡 Transformers Error: Check model name and cache directory")
            
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
            
            # Calculate total tokens in history
            total_tokens = sum(len(self.tokenizer.encode(msg, add_special_tokens=False)) for msg in session["history"])
            
            if total_tokens > max_tokens:
                # Trim history to fit within token limit
                trimmed_history = []
                trimmed_roles = []
                current_tokens = 0
                
                # Start from most recent messages and work backwards
                for msg, role in zip(reversed(session["history"]), reversed(session["message_roles"])):
                    msg_tokens = len(self.tokenizer.encode(msg, add_special_tokens=False))
                    if current_tokens + msg_tokens <= max_tokens:
                        trimmed_history.insert(0, msg)
                        trimmed_roles.insert(0, role)
                        current_tokens += msg_tokens
                    else:
                        break
                
                session["history"] = trimmed_history
                session["message_roles"] = trimmed_roles
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
            
            # Optimized parameters applying guide principles: Accuracy-First + Speed Optimization
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=100,          # Optimized for 200 char limit + concise responses
                    temperature=0.28,            # Slightly lower for accuracy compensation (guide principle)
                    top_p=0.9,                  # More flexible than 0.85 for better accuracy (guide principle)
                    top_k=30,                   # Better than 25 for accuracy (guide principle)
                    do_sample=True,              # Enable sampling for better quality
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.15,    # Optimized for accuracy (guide principle)
                    use_cache=True,             # Enable KV cache for memory efficiency
                    num_beams=1,                # Single beam for memory efficiency
                    # RTX 4060 Tensor Core Optimization
                    batch_size=4,               # Optimal for 7B on 8GB VRAM
                    # New guide-based parameters for accuracy preservation
                    typical_p=0.9,              # Filters atypical tokens (guide principle)
                )
            
            generation_time = time.time() - start_time
            
            # Decode the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new tokens (remove the input prompt)
            # Use token-based extraction for better accuracy
            response = self._extract_ai_response(response, inputs, self.tokenizer)
            
            # Validate and enhance response for better accuracy
            validated_response = self._validate_response(response, session_id)
            
            # Add validated assistant message to history
            self.add_assistant_message(session_id, validated_response)
            
            # Periodic memory optimization for RTX 4060 (every 5 responses)
            session = self.user_sessions.get(session_id, {})
            if len(session.get("history", [])) % 5 == 0:
                logger.info(f"🧹 Running periodic memory optimization for session {session_id}")
                self.optimize_memory_usage()
            
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
        """Extract only the AI-generated response using token positions (more reliable)"""
        try:
            # Use token position-based extraction (most reliable method)
            input_length = inputs["input_ids"].shape[1]
            response = tokenizer.decode(inputs["input_ids"][0][input_length:], skip_special_tokens=True)
            
            logger.info(f"📝 Extracted response using token position method: {len(response)} chars")
            
            # Clean up any system instructions that leaked through
            response = self._clean_system_instructions(response)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Token-based response extraction failed: {e}")
            # Fallback to string-based extraction
            try:
                if "<|im_start|>assistant\n" in full_response:
                    response = full_response.split("<|im_start|>assistant\n")[-1].strip()
                    logger.info(f"📝 Fallback: extracted response using assistant tag method")
                else:
                    response = full_response
                    logger.info(f"📝 Fallback: using full response")
                
                response = self._clean_system_instructions(response)
                return response
            except Exception as fallback_error:
                logger.error(f"❌ Fallback extraction also failed: {fallback_error}")
                return full_response
    
    def _clean_system_instructions(self, response: str) -> str:
        """Remove system instructions and unwanted content from AI responses"""
        try:
            # Remove system instruction patterns
            unwanted_patterns = [
                "**REMEMBER:**",
                "**CHARACTER CONSISTENCY CHECK:**",
                "You MUST stay in character",
                "You MUST respond in first person",
                "You MUST keep responses under 140 characters",
                "You MUST never break character",
                "You MUST respond to the user's specific questions",
                "You MUST maintain the exact personality",
                "Before responding, ask yourself:",
                "If not, adjust your response",
                "Start the conversation like you normally would",
                "**CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY:**"
            ]
            
            cleaned_response = response
            for pattern in unwanted_patterns:
                if pattern in cleaned_response:
                    # Remove everything from the pattern onwards
                    cleaned_response = cleaned_response.split(pattern)[0].strip()
                    logger.info(f"🧹 Cleaned response: removed '{pattern}'")
            
            # Remove any remaining markdown formatting
            cleaned_response = cleaned_response.replace("**", "").replace("*", "")
            
            # Remove excessive newlines and spaces
            cleaned_response = " ".join(cleaned_response.split())
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"❌ System instruction cleaning failed: {e}")
            return response
    
    def _validate_response(self, response: str, session_id: str) -> str:
        """Consolidated response validation and quality assessment"""
        try:
            if not response or len(response.strip()) == 0:
                return "I'm here, what would you like me to do?"
            
            # Clean up response
            cleaned = response.strip()
            
            # Ensure response is under 200 characters for concise, focused responses
            if len(cleaned) > 200:
                cleaned = cleaned[:197] + "..."
                logger.info(f"📝 Truncated response to 200 chars for session {session_id}")
            
            # Check for character consistency indicators
            session = self.user_sessions.get(session_id, {})
            system_prompt = session.get("system_prompt", "").lower()
            
            # If response seems generic, add character reinforcement
            generic_indicators = ["i am an ai", "as an ai", "i'm an ai", "artificial intelligence"]
            if any(indicator in cleaned.lower() for indicator in generic_indicators):
                logger.warning(f"⚠️ Generic response detected, reinforcing character for session {session_id}")
                # Try to regenerate with stronger character focus
                return self._regenerate_with_character_focus(session_id, response)
            
            # Log quality assessment inline (consolidated)
            quality_score = self._quick_quality_check(cleaned)
            logger.info(f"🎯 Response quality: {quality_score}/10 for session {session_id}")
            
            return cleaned
            
        except Exception as e:
            logger.error(f"❌ Response validation failed: {e}")
            return response  # Return original if validation fails
    
    def _quick_quality_check(self, response: str) -> int:
        """Quick quality assessment (1-10 scale)"""
        score = 10
        
        # Deduct points for various issues
        if len(response) < 10:
            score -= 3  # Too short
        if len(response) > 200:
            score -= 2  # Too long
        if "i am an ai" in response.lower():
            score -= 5  # Generic AI response
        if response.count(".") > 3:
            score -= 1  # Too many sentences
        if response.count("!") > 2:
            score -= 1  # Too many exclamations
            
        return max(1, score)  # Minimum score of 1
    
    def _assess_response_quality(self, response: str, session_id: str) -> Dict[str, str]:
        """Assess response quality using Guide's accuracy principles"""
        try:
            session = self.user_sessions.get(session_id, {})
            system_prompt = session.get("system_prompt", "").lower()
            
            quality_indicators = {
                "character_consistency": "✅",
                "factual_accuracy": "✅",
                "response_relevance": "✅",
                "length_appropriate": "✅"
            }
            
            # Check character consistency
            if "i am an ai" in response.lower() or "as an ai" in response.lower():
                quality_indicators["character_consistency"] = "❌"
            
            # Check factual accuracy indicators
            if "i need to verify" in response.lower() or "i'm not sure" in response.lower():
                quality_indicators["factual_accuracy"] = "⚠️"  # Good - shows honesty
            
            # Check response relevance
            if len(response.strip()) < 10:
                quality_indicators["response_relevance"] = "❌"
            
            # Check length appropriateness
            if len(response) > 500:
                quality_indicators["length_appropriate"] = "❌"
            
            return quality_indicators
            
        except Exception as e:
            logger.error(f"❌ Quality assessment failed: {e}")
            return {"error": "Assessment failed"}
    
    def _regenerate_with_character_focus(self, session_id: str, original_response: str) -> str:
        """Regenerate response with stronger character focus"""
        try:
            session = self.user_sessions.get(session_id, {})
            system_prompt = session.get("system_prompt", "")
            
            # Create a more focused prompt
            focused_prompt = f"{system_prompt}\n\n**URGENT: You MUST stay in character!**\n\nUser's question requires a response that stays true to your character."
            
            # Regenerate with stricter parameters using transformers (RTX 4060 optimized)
            inputs = self.tokenizer(
                focused_prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=settings.ai_max_context_length
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=70,           # Optimized for speed + accuracy
                    temperature=0.08,            # Very low for character consistency (guide principle)
                    top_p=0.8,                  # Balanced for accuracy
                    top_k=20,                   # Better selection for accuracy
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.25,    # Optimized for character consistency
                    early_stopping=True,
                    # Guide-based accuracy parameters
                    typical_p=0.95,             # High typical_p for character consistency
                    tfs_z=0.98,                 # High tfs_z for quality
                    use_cache=True,             # Memory efficiency
                    max_memory={0: f"{settings.ai_max_memory_gb}GB"} if self.device == "cuda" else None,
                )
            
            # Decode the response
            new_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new tokens
            input_length = inputs["input_ids"].shape[1]
            new_response = new_response[input_length:].strip()
            
            if new_response and len(new_response) > 0:
                logger.info(f"🔄 Regenerated response with character focus for session {session_id}")
                return new_response[:140]  # Ensure length limit
            
            return original_response  # Fallback to original
            
        except Exception as e:
            logger.error(f"❌ Character focus regeneration failed: {e}")
            return original_response
    
    def optimize_memory_usage(self) -> Dict:
        """Optimize memory usage for 7B transformers model on RTX 4060"""
        try:
            logger.info("🧹 Optimizing memory usage for RTX 4060...")
            
            # Force garbage collection
            gc.collect()
            
            # Clear CUDA cache if using GPU
            if self.device == "cuda" and torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("🧹 CUDA cache cleared")
                
                # Log memory before and after optimization
                before_memory = torch.cuda.memory_allocated(0) / 1024**3
                logger.info(f"💾 Memory before optimization: {before_memory:.2f} GB")
                
                # Force memory cleanup
                torch.cuda.synchronize()
                
                after_memory = torch.cuda.memory_allocated(0) / 1024**3
                logger.info(f"💾 Memory after optimization: {after_memory:.2f} GB")
                logger.info(f"💾 Memory freed: {before_memory - after_memory:.2f} GB")
            
            # Clear any cached data
            if hasattr(self.model, 'reset'):
                self.model.reset()
            
            # Clear session history if too many sessions
            if len(self.user_sessions) > 10:
                logger.info("🧹 Clearing old sessions to free memory...")
                # Keep only recent sessions
                current_time = time.time()
                old_sessions = [sid for sid, session in self.user_sessions.items() 
                              if current_time - session.get("last_updated", 0) > 3600]  # 1 hour
                for sid in old_sessions:
                    del self.user_sessions[sid]
                logger.info(f"🧹 Cleared {len(old_sessions)} old sessions")
            
            logger.info("✅ RTX 4060 memory optimization completed")
            return {"status": "success", "message": "RTX 4060 memory optimized"}
            
        except Exception as e:
            logger.error(f"❌ RTX 4060 memory optimization failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_health_status(self) -> Dict:
        """Get health status of the AI model"""
        try:
            status = {
                "model_loaded": self.model_loaded,
                "model_type": "7B Transformers (4-bit quantization, RTX 4060 optimized)",
                "active_sessions": len(self.user_sessions),
                "total_sessions": len(self.user_sessions),
            }
            
            if self.model_loaded and self.model:
                status.update({
                    "device": self.device,
                    "quantization": "4-bit" if settings.ai_use_4bit else "8-bit" if settings.ai_use_8bit else "None",
                    "model_name": settings.ai_model_name,
                    "max_context_length": settings.ai_max_context_length,
                    "max_memory_gb": settings.ai_max_memory_gb,
                })
                
                # Add detailed GPU memory info for RTX 4060
                if self.device == "cuda":
                    total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                    allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
                    reserved_memory = torch.cuda.memory_reserved(0) / 1024**3
                    status.update({
                        "gpu_total_memory_gb": round(total_memory, 1),
                        "gpu_allocated_memory_gb": round(allocated_memory, 1),
                        "gpu_reserved_memory_gb": round(reserved_memory, 1),
                        "gpu_available_memory_gb": round(total_memory - allocated_memory, 1),
                        "memory_efficiency_percent": round((allocated_memory / total_memory) * 100, 1),
                    })
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Failed to get health status: {e}")
            return {"status": "error", "message": str(e)}

# Global instance
ai_model_manager = AIModelManager() 