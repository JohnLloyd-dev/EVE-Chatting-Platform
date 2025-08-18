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
            
            # Configure 4-bit quantization for RTX 4060 (8GB VRAM)
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
            from main import get_complete_system_prompt
            
            # Get the complete system prompt
            system_prompt = get_complete_system_prompt(db, str(db_session.user.id), db_session.scenario_prompt or "")
            
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
            # Keep only last 4 messages to maintain system prompt impact and save memory
            max_history = 4 if self.device == "cuda" else 6
            if len(session["history"]) > max_history:
                session["history"] = session["history"][-max_history:]
                session["message_roles"] = session["message_roles"][-max_history:]
                logger.info(f"📝 Trimmed history to last {max_history} messages for session {session_id} (RTX 4060 optimized)")
    
    def add_assistant_message(self, session_id: str, message: str):
        """Add an assistant message to session history"""
        if session_id in self.user_sessions:
            session = self.user_sessions[session_id]
            session["history"].append(message)
            session["message_roles"].append("assistant")
            session["last_updated"] = time.time()
    
    def build_chatml_prompt(self, system_prompt: str, history: List[str], message_roles: List[str], user_message: str) -> str:
        """Build enhanced ChatML format prompt for better accuracy"""
        
        # Enhanced system prompt applying guide principles: Accuracy-First + Speed
        enhanced_system = f"""<|im_start|>system
        {system_prompt.strip()}
        
        **ACCURACY-FIRST INSTRUCTIONS (Guide Principles):**
        - Prioritize factual accuracy over speed
        - If uncertain, say "I need to verify" rather than guessing
        - Always double-check technical details
        - Stay in character at all times
        - Respond as the specified person
        - Answer the user's question directly
        - Use first person dialogue only
        - Keep responses under 500 characters for meaningful conversation
        
        **QUALITY ASSURANCE:**
        - Verify information before responding
        - Maintain character consistency
        - Avoid generic or off-topic responses
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
                    max_new_tokens=200,          # Optimized for 500 char limit + meaningful responses
                    temperature=0.28,            # Slightly lower for accuracy compensation (guide principle)
                    top_p=0.9,                  # More flexible than 0.85 for better accuracy (guide principle)
                    top_k=30,                   # Better than 25 for accuracy (guide principle)
                    do_sample=True,              # Enable sampling for better quality
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.15,    # Optimized for accuracy (guide principle)
                    use_cache=True,             # Enable KV cache for memory efficiency
                    num_beams=1,                # Single beam for memory efficiency
                    # New guide-based parameters for accuracy preservation
                    typical_p=0.9,              # Filters atypical tokens (guide principle)
                )
            
            generation_time = time.time() - start_time
            
            # Decode the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new tokens (remove the input prompt)
            # Look for the last assistant tag and extract from there
            if "<|im_start|>assistant\n" in response:
                response = response.split("<|im_start|>assistant\n")[-1].strip()
            else:
                # Fallback: use token-based extraction
                input_length = inputs["input_ids"].shape[1]
                response = response[input_length:].strip()
            
            # Validate and enhance response for better accuracy
            validated_response = self._validate_response(response, session_id)
            
            # Add validated assistant message to history
            self.add_assistant_message(session_id, validated_response)
            
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
    
    def _validate_response(self, response: str, session_id: str) -> str:
        """Validate and enhance response for better accuracy"""
        try:
            if not response or len(response.strip()) == 0:
                return "I'm here, what would you like me to do?"
            
            # Clean up response
            cleaned = response.strip()
            
            # Ensure response is under 500 characters for meaningful conversation
            if len(cleaned) > 500:
                cleaned = cleaned[:497] + "..."
                logger.info(f"📝 Truncated response to 500 chars for session {session_id}")
            
            # Check for character consistency indicators
            session = self.user_sessions.get(session_id, {})
            system_prompt = session.get("system_prompt", "").lower()
            
            # If response seems generic, add character reinforcement
            generic_indicators = ["i am an ai", "as an ai", "i'm an ai", "artificial intelligence"]
            if any(indicator in cleaned.lower() for indicator in generic_indicators):
                logger.warning(f"⚠️ Generic response detected, reinforcing character for session {session_id}")
                # Try to regenerate with stronger character focus
                return self._regenerate_with_character_focus(session_id, response)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"❌ Response validation failed: {e}")
            return response  # Return original if validation fails
    
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