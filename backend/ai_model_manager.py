"""
AI Model Manager for Backend (GGUF with GPU Acceleration)
Handles GGUF model loading, inference, and session management using llama-cpp-python
"""
import logging
import time
import os
import gc
from typing import Dict, List, Optional, Tuple
from llama_cpp import Llama
from config import settings

logger = logging.getLogger(__name__)

class AIModelManager:
    """Manages GGUF AI model loading, inference, and session management"""
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.user_sessions: Dict[str, Dict] = {}
        
        # Load model on initialization
        self._load_model()
    
    def _load_model(self):
        """Load the GGUF AI model with GPU acceleration"""
        try:
            logger.info(f"🚀 Loading GGUF AI model: {settings.ai_model_name}")
            logger.info(f"📁 Model file: {settings.ai_model_file}")
            
            # Check if model file exists
            model_path = os.path.join(settings.ai_model_cache_dir, settings.ai_model_file)
            if not os.path.exists(model_path):
                logger.warning(f"⚠️ Model file not found: {model_path}")
                logger.info("📥 You need to download the GGUF model file manually")
                logger.info("💡 Download from: https://huggingface.co/TheBloke/OpenHermes-2.5-Mistral-7B-GGUF")
                logger.info("💡 Recommended: openhermes-2.5-mistral-7b.Q5_K_M.gguf")
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Load GGUF model with GPU acceleration
            logger.info("📥 Loading GGUF model with GPU acceleration...")
            
            # Optimized settings for RTX 4060 (8GB VRAM)
            model_kwargs = {
                "model_path": model_path,
                "n_ctx": 4096,              # Context window size
                "n_gpu_layers": 33,         # Offload ALL layers to GPU (RTX 4060 can handle this)
                "n_threads": 8,             # CPU threads for non-offloaded operations
                "verbose": False,            # Reduce logging noise
                "n_batch": 512,             # Batch size for prompt processing
                "use_mmap": True,            # Memory mapping for efficiency
                "use_mlock": False,         # Don't lock memory (allows swapping if needed)
            }
            
            logger.info("🚀 Initializing GGUF model with GPU acceleration...")
            self.model = Llama(**model_kwargs)
            
            # Test model loading
            logger.info("🧪 Testing model with simple prompt...")
            test_output = self.model(
                prompt="Hello",
                max_tokens=10,
                temperature=0.0,
                stop=["\n"],
                stream=False
            )
            
            if test_output and "choices" in test_output:
                logger.info("✅ Model test successful!")
                self.model_loaded = True
                logger.info("✅ GGUF AI Model loaded successfully with GPU acceleration!")
                
                # Log model info
                logger.info(f"📊 Model context: {self.model.n_ctx} tokens")
                logger.info(f"🚀 GPU layers: {model_kwargs['n_gpu_layers']}")
                logger.info(f"⚙️ CPU threads: {model_kwargs['n_threads']}")
                
            else:
                raise RuntimeError("Model test failed - no output generated")
            
        except Exception as e:
            logger.error(f"❌ Failed to load GGUF AI model: {e}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            self.model_loaded = False
            
            # Provide specific error guidance
            if "CUDA" in str(e):
                logger.error("💡 CUDA Error: Check GPU drivers and CUDA installation")
            elif "out of memory" in str(e).lower():
                logger.error("💡 Memory Error: Reduce n_gpu_layers or use smaller quantization")
            elif "file not found" in str(e).lower():
                logger.error("💡 File Error: Download the GGUF model file first")
            
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
            
            # Enhanced history management to prevent system prompt dilution
            # Keep only last 6 messages to maintain system prompt impact
            if len(session["history"]) > 6:
                session["history"] = session["history"][-6:]
                session["message_roles"] = session["message_roles"][-6:]
                logger.info(f"📝 Trimmed history to last 6 messages for session {session_id}")
    
    def add_assistant_message(self, session_id: str, message: str):
        """Add an assistant message to session history"""
        if session_id in self.user_sessions:
            session = self.user_sessions[session_id]
            session["history"].append(message)
            session["message_roles"].append("assistant")
            session["last_updated"] = time.time()
    
    def build_chatml_prompt(self, system_prompt: str, history: List[str], message_roles: List[str]) -> str:
        """Build enhanced ChatML format prompt for better accuracy"""
        
        # Enhanced system prompt with reinforcement
        enhanced_system = f"""<|im_start|>system
{system_prompt.strip()}

**CRITICAL REMINDER:**
- Stay in character at all times
- Respond as the specified person
- Answer the user's question directly
- Use first person dialogue only
- Keep responses under 140 characters
<|im_end|>

"""
        
        parts = [enhanced_system]
        
        # Add conversation history (limited to prevent dilution)
        for i, (message, role) in enumerate(zip(history, message_roles)):
            if role == "user":
                parts.append(f"<|im_start|>user\n{message}<|im_end|>\n")
            elif role == "assistant":
                parts.append(f"<|im_start|>assistant\n{message}<|im_end|>\n")
        
        # Add final user prompt with character reminder
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
            prompt = self.build_chatml_prompt(system_prompt, history, message_roles)
            
            logger.info(f"🚀 Generating response for session {session_id}")
            logger.info(f"📝 Prompt length: {len(prompt)} characters")
            
            # Generate response with GGUF model
            start_time = time.time()
            
            # Optimized parameters for better instruction following and accuracy
            output = self.model(
                prompt=prompt,
                max_tokens=200,          # Shorter responses for better focus (140 char limit)
                temperature=0.3,         # Lower temperature for more consistent responses
                top_p=0.85,             # Tighter nucleus sampling for focused generation
                top_k=25,               # Lower top-k for more focused selection
                stop=["<|im_end|>", "\n\n", "User:", "Human:"],  # Better stop tokens
                stream=False,            # No streaming for now
                repeat_penalty=1.2,     # Higher repetition penalty to prevent generic responses
                frequency_penalty=0.1,   # Slight frequency penalty for variety
                presence_penalty=0.1,   # Slight presence penalty for engagement
            )
            
            generation_time = time.time() - start_time
            
            if output and "choices" in output and len(output["choices"]) > 0:
                response = output["choices"][0]["text"].strip()
                
                # Validate and enhance response for better accuracy
                validated_response = self._validate_response(response, session_id)
                
                # Add validated assistant message to history
                self.add_assistant_message(session_id, validated_response)
                
                # Log performance metrics
                tokens_generated = len(validated_response.split())  # Approximate
                tokens_per_second = tokens_generated / generation_time if generation_time > 0 else 0
                
                logger.info(f"✅ Response generated in {generation_time:.2f}s")
                logger.info(f"📊 Tokens: {tokens_generated}, Speed: {tokens_per_second:.1f} tokens/s")
                logger.info(f"🎯 Response validation: {len(response)} -> {len(validated_response)} chars")
                
                return validated_response
            else:
                raise RuntimeError("No response generated from model")
                
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
            
            # Ensure response is under 140 characters
            if len(cleaned) > 140:
                cleaned = cleaned[:137] + "..."
                logger.info(f"📝 Truncated response to 140 chars for session {session_id}")
            
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
    
    def _regenerate_with_character_focus(self, session_id: str, original_response: str) -> str:
        """Regenerate response with stronger character focus"""
        try:
            session = self.user_sessions.get(session_id, {})
            system_prompt = session.get("system_prompt", "")
            
            # Create a more focused prompt
            focused_prompt = f"{system_prompt}\n\n**URGENT: You MUST stay in character!**\n\nUser's question requires a response that stays true to your character."
            
            # Regenerate with stricter parameters
            output = self.model(
                prompt=focused_prompt,
                max_tokens=100,
                temperature=0.1,  # Very low temperature for consistency
                top_p=0.7,
                top_k=15,
                stop=["<|im_end|>", "\n\n"],
                repeat_penalty=1.3,
            )
            
            if output and "choices" in output and len(output["choices"]) > 0:
                new_response = output["choices"][0]["text"].strip()
                logger.info(f"🔄 Regenerated response with character focus for session {session_id}")
                return new_response[:140]  # Ensure length limit
            
            return original_response  # Fallback to original
            
        except Exception as e:
            logger.error(f"❌ Character focus regeneration failed: {e}")
            return original_response
    
    def optimize_memory_usage(self) -> Dict:
        """Optimize memory usage for GGUF model"""
        try:
            logger.info("🧹 Optimizing memory usage...")
            
            # Force garbage collection
            gc.collect()
            
            # Clear any cached data
            if hasattr(self.model, 'reset'):
                self.model.reset()
            
            logger.info("✅ Memory optimization completed")
            return {"status": "success", "message": "Memory optimized"}
            
        except Exception as e:
            logger.error(f"❌ Memory optimization failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_health_status(self) -> Dict:
        """Get health status of the AI model"""
        try:
            status = {
                "model_loaded": self.model_loaded,
                "model_type": "GGUF (llama-cpp-python)",
                "active_sessions": len(self.user_sessions),
                "total_sessions": len(self.user_sessions),
            }
            
            if self.model_loaded and self.model:
                status.update({
                    "context_window": getattr(self.model, 'n_ctx', 'Unknown'),
                    "gpu_layers": getattr(self.model, 'n_gpu_layers', 'Unknown'),
                    "cpu_threads": getattr(self.model, 'n_threads', 'Unknown'),
                })
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Failed to get health status: {e}")
            return {"status": "error", "message": str(e)}

# Global instance
ai_model_manager = AIModelManager() 