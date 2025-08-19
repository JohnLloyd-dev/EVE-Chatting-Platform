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

logger = logging.getLogger(__name__)

class AIModelManager:
    """Simplified manager for 7B AI model loading and inference"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.user_sessions: Dict[str, Dict] = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.generate_lock = Lock()
        
        # Load model on initialization
        self._load_model()
    
    def _load_model(self):
        """Simple model loading optimized for RTX 4060"""
        try:
            logger.info(f"🚀 Loading AI model: {settings.ai_model_name}")
            logger.info(f"🔧 Device: {self.device}")
            
            # Simple quantization config (like your working main.py)
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
            )
            
            # Load tokenizer and model directly
            self.tokenizer = AutoTokenizer.from_pretrained(settings.ai_model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                settings.ai_model_name,
                device_map="auto",
                quantization_config=bnb_config
            )
            
            # Set to evaluation mode
            self.model.eval()
            self.model_loaded = True
            
            logger.info("✅ AI Model loaded successfully!")
            
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
        """Build ChatML format prompt"""
        prompt = f"<|system|>\n{system.strip()}\n"
        for entry in history:
            if entry.startswith("User:"):
                prompt += f"<|user|>\n{entry[5:].strip()}\n"
            elif entry.startswith("AI:"):
                prompt += f"<|assistant|>\n{entry[3:].strip()}\n"
        prompt += "<|assistant|>\n"
        return prompt
    
    def generate_response(self, session_id: str, user_message: str, max_tokens: int = 150) -> str:
        """Generate AI response using the model"""
        if not self.model_loaded:
            raise RuntimeError("AI model not loaded")
        
        # Thread safety for concurrent requests
        with self.generate_lock:
            # Get session
            if session_id not in self.user_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.user_sessions[session_id]
            
            # Add user message to history
            self.add_user_message(session_id, user_message)
            
            # Trim history to fit context window
            session["history"] = self.trim_history(
                system=session["system_prompt"],
                history=session["history"],
                max_tokens=3500
            )
            
            # Build prompt
            full_prompt = self.build_chatml_prompt(
                session["system_prompt"],
                session["history"]
            )
            
            # Tokenize with truncation
            inputs = self.tokenizer(
                full_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096
            ).to(self.model.device)
            
            # Adjust max tokens to available space
            max_output_tokens = min(
                max_tokens,
                4096 - inputs.input_ids.shape[1]
            )
            
            if max_output_tokens <= 0:
                raise ValueError("Input too long for response generation")
            
            # Generate response
            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    max_new_tokens=max_output_tokens,
                    temperature=0.8,
                    do_sample=True,
                    top_p=0.95,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=3
                )
            
            # Extract only new tokens
            response_tokens = output[0][inputs.input_ids.shape[1]:]
            response = self.tokenizer.decode(
                response_tokens,
                skip_special_tokens=True
            ).strip()
            
            # Save AI response to history
            self.add_assistant_message(session_id, response)
            
            return response

# Global instance
ai_model_manager = AIModelManager() 