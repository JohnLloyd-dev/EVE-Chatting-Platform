# OPTIMIZED: Enhanced performance while maintaining accuracy
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from fastapi.middleware.cors import CORSMiddleware

import secrets
import torch
from uuid import uuid4
import logging
import re
import threading
import time
import asyncio  # For async operations
import gc # For garbage collection
from contextlib import asynccontextmanager

# Timeout configuration to prevent hanging
GENERATION_TIMEOUT = 30.0  # 30 seconds max for generation
REQUEST_TIMEOUT = 60.0      # 60 seconds max for entire request

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if accelerate is available
try:
    import accelerate
    ACCELERATE_AVAILABLE = True
    logger.info("✅ Accelerate library available")
except ImportError:
    ACCELERATE_AVAILABLE = False
    logger.warning("⚠️  Accelerate library not available - some strategies will be skipped")

app = FastAPI()
security = HTTPBasic()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Per-user session storage with thread safety
user_sessions = {}
session_lock = threading.Lock()
model_lock = threading.Lock()  # For model access synchronization

# Input schemas
class InitScenario(BaseModel):
    scenario: str = Field(..., min_length=1)

class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    max_tokens: int = Field(200, ge=50, le=1000)  # Increased default and max for complete responses
    temperature: float = Field(0.7, ge=0.1, le=1.0)
    top_p: float = Field(0.9, ge=0.1, le=1.0)
    speed_mode: bool = Field(False, description="Enable speed optimization mode")
    ultra_speed: bool = Field(False, description="Enable ultra-speed mode for maximum performance")

# Load model
model_name = "teknium/OpenHermes-2.5-Mistral-7B"

# Check if GPU is available
gpu_available = torch.cuda.is_available()
logger.info(f"GPU available: {gpu_available}")

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token  # Set pad token

# OPTIMIZATION: Advanced model inference optimizations
def optimize_model_for_speed():
    """Apply advanced optimizations for maximum speed while maintaining accuracy"""
    global model
    
    # Enable memory efficient attention for faster inference
    if hasattr(model, 'config') and hasattr(model.config, 'attention_mode'):
        model.config.attention_mode = 'flash_attention_2'
        logger.info("🚀 Enabled Flash Attention 2 for faster inference")
    
    # Enable gradient checkpointing for memory efficiency
    if hasattr(model, 'gradient_checkpointing_enable'):
        model.gradient_checkpointing_enable()
        logger.info("🚀 Enabled gradient checkpointing for memory efficiency")
    
    # Optimize model for inference
    model.eval()
    
    # Enable torch optimizations
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.deterministic = False
    
    # OPTIMIZATION: Enable Tensor Core math for maximum GPU performance
    if hasattr(torch.backends.cuda, 'matmul'):
        torch.backends.cuda.matmul.allow_tf32 = True  # Ampere+ GPUs
        logger.info("🚀 Tensor Core TF32 enabled for maximum GPU performance")
    
    if hasattr(torch.backends.cudnn, 'allow_tf32'):
        torch.backends.cudnn.allow_tf32 = True
        logger.info("🚀 cuDNN TF32 enabled for maximum GPU performance")
    
    # OPTIMIZATION: JIT optimizations for maximum speed
    torch._C._jit_set_profiling_executor(False)
    torch._C._jit_set_profiling_mode(False)
    torch._C._jit_override_can_fuse_on_cpu(True)
    torch._C._jit_override_can_fuse_on_gpu(True)
    logger.info("🚀 JIT optimizations enabled for maximum speed")
    
    # Enable JIT compilation if available
    try:
        if hasattr(torch, 'jit') and hasattr(model, 'forward'):
            model = torch.jit.optimize_for_inference(model)
            logger.info("🚀 JIT compilation enabled for faster inference")
    except Exception as e:
        logger.info(f"JIT compilation not available: {e}")
    
    # OPTIMIZATION: Static model compilation with TorchInductor
    try:
        if hasattr(torch, 'compile'):
            model = torch.compile(
                model,
                mode="reduce-overhead",
                fullgraph=True,
                dynamic=False
            )
            logger.info("🚀 TorchInductor compilation enabled for maximum performance")
    except Exception as e:
        logger.info(f"TorchInductor compilation not available: {e}")
    
    # Memory optimizations
    if hasattr(torch, 'cuda') and torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.info("🚀 CUDA cache cleared for optimal memory usage")
    
    # Enable memory efficient attention if available
    try:
        if hasattr(model, 'config') and hasattr(model.config, 'attn_implementation'):
            model.config.attn_implementation = "flash_attention_2"
            logger.info("🚀 Flash Attention 2 enabled for memory efficiency")
    except Exception as e:
        logger.info(f"Flash Attention 2 not available: {e}")
    
    # OPTIMIZATION: Force performance mode for maximum speed
    if hasattr(torch, 'cuda') and torch.cuda.is_available():
        # Set CUDA device to maximum performance
        torch.cuda.set_device(0)
        torch.cuda.empty_cache()
        
        # Force memory optimization
        if hasattr(torch.cuda, 'amp'):
            torch.cuda.amp.autocast(enabled=True)
        
        # Set memory fraction for maximum performance
        torch.cuda.set_per_process_memory_fraction(0.95)
        
        logger.info("🚀 CUDA performance mode enabled")
    
    logger.info("🚀 Model optimized for maximum speed")

# OPTIMIZATION: Preload model with optimized settings
def load_model_with_fallbacks():
    """Load model with performance optimizations"""
    # Prefer 4-bit quantization for best performance
    try:
        logger.info("🔄 Loading with 4-bit quantization...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            quantization_config=bnb_config,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
        logger.info("✅ 4-bit quantization successful")
        return model
    except Exception as e:
        logger.error(f"❌ 4-bit quantization failed: {e}")
    
    # Fallback to 8-bit
    try:
        logger.info("🔄 Loading with 8-bit quantization...")
        bnb_config_8bit = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_threshold=6.0
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            quantization_config=bnb_config_8bit,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
        logger.info("✅ 8-bit quantization successful")
        return model
    except Exception as e:
        logger.error(f"❌ 8-bit quantization failed: {e}")
    
    # Final fallback to float16 on GPU
    if gpu_available:
        logger.info("🔄 Loading with float16 on GPU...")
        return AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
    
    # CPU fallback
    logger.info("🔄 Falling back to CPU...")
    return AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="cpu",
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True
    )

# Load the model
logger.info("🚀 Starting model loading process...")
try:
    model = load_model_with_fallbacks()
    device = next(model.parameters()).device
    logger.info(f"✅ Model loaded on device: {device}")
    
    # Apply advanced optimizations for maximum speed
    optimize_model_for_speed()
    
except Exception as e:
    logger.critical(f"❌ Model loading failed: {e}")
    raise RuntimeError(f"Failed to load model: {e}")

logger.info("🎯 Model ready for inference")

# OPTIMIZATION: Memory management and caching
def optimize_memory_usage():
    """Optimize memory usage for better performance and prevent crashes"""
    if hasattr(torch, 'cuda') and torch.cuda.is_available():
        # Clear CUDA cache more aggressively
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        
        # Check memory usage and warn if getting too high
        memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
        memory_reserved = torch.cuda.memory_reserved() / 1024**3   # GB
        
        if memory_allocated > 8.0:  # If using more than 8GB
            logger.warning(f"⚠️ High GPU memory usage: {memory_allocated:.2f}GB allocated, {memory_reserved:.2f}GB reserved")
            # Force garbage collection
            gc.collect()
            torch.cuda.empty_cache()
        
        logger.info("🚀 CUDA cache cleared and synchronized")
    
    # Force garbage collection
    gc.collect()
    logger.info("🚀 Garbage collection completed")

# OPTIMIZATION: Pinned memory buffers for maximum GPU performance
def create_pinned_buffers():
    """Create pinned memory buffers for optimal GPU transfer"""
    try:
        if hasattr(torch, 'cuda') and torch.cuda.is_available():
            # Create pinned memory buffers for optimal GPU transfer
            global pin_memory_buffer
            pin_memory_buffer = torch.empty(
                (1, 4096), 
                dtype=torch.long,
                pin_memory=True
            )
            logger.info("🚀 Pinned memory buffers created for maximum GPU performance")
            return True
    except Exception as e:
        logger.warning(f"⚠️ Pinned memory creation failed: {e}")
        return False

# Create pinned buffers after model loading
pin_memory_buffer = None
if create_pinned_buffers():
    logger.info("✅ Pinned memory optimization enabled")
else:
    logger.info("ℹ️ Pinned memory optimization not available")

# OPTIMIZATION: Advanced caching for common operations
class PerformanceCache:
    """Advanced caching for performance optimization"""
    def __init__(self):
        self.prompt_cache = {}
        self.token_cache = {}
        self.max_cache_size = 1000
    
    def get_cached_prompt(self, system: str, history_hash: str) -> str:
        """Get cached prompt if available"""
        cache_key = f"{system[:50]}_{history_hash}"
        return self.prompt_cache.get(cache_key)
    
    def cache_prompt(self, system: str, history_hash: str, prompt: str):
        """Cache prompt for future use"""
        cache_key = f"{system[:50]}_{history_hash}"
        if len(self.prompt_cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.prompt_cache))
            del self.prompt_cache[oldest_key]
        self.prompt_cache[cache_key] = prompt
    
    def get_cached_tokens(self, text: str) -> int:
        """Get cached token count if available"""
        return self.token_cache.get(text)
    
    def cache_tokens(self, text: str, token_count: int):
        """Cache token count for future use"""
        if len(self.token_cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.token_cache))
            del self.token_cache[oldest_key]
        self.token_cache[text] = token_count

# Initialize performance cache
performance_cache = PerformanceCache()

# OPTIMIZATION: Cache tokenizer results for common phrases
# Comprehensive ChatML tag cleaning patterns
CLEAN_PATTERN = re.compile(r'<\|[\w]+\|>$')  # Tags at end
# Pre-compiled regex patterns for maximum performance
CHATML_TAG_PATTERN = re.compile(r'<\|[\w]+\|>|<\|im_start\|>[\w]+|<\|im_end\|>')  # All ChatML tags including OpenHermes format

# Common phrases for token counting optimization
COMMON_PHRASES = {
    "<|im_start|>system": tokenizer("<|im_start|>system")["input_ids"],
    "<|im_end|>": tokenizer("<|im_end|>")["input_ids"],
    "<|im_start|>user": tokenizer("<|im_start|>user")["input_ids"],
    "<|im_start|>assistant": tokenizer("<|im_start|>assistant")["input_ids"],
}

# OPTIMIZATION: Ultra-fast token counting with advanced caching
def count_tokens_ultra_fast(text: str) -> int:
    """Ultra-fast token counting with advanced caching and pattern matching"""
    # Check advanced cache first
    cached_count = performance_cache.get_cached_tokens(text)
    if cached_count is not None:
        return cached_count
    
    # Extended common phrase cache for even faster counting
    if text in COMMON_PHRASES:
        performance_cache.cache_tokens(text, len(COMMON_PHRASES[text]))
        return len(COMMON_PHRASES[text])
    
    # Check for common patterns first
    for phrase, tokens in COMMON_PHRASES.items():
        if text.startswith(phrase):
            remaining = text[len(phrase):]
            total_count = len(tokens) + count_tokens_ultra_fast(remaining)
            performance_cache.cache_tokens(text, total_count)
            return total_count
    
    # For very short texts, estimate instead of full tokenization
    if len(text) < 20:
        estimated_count = max(1, len(text) // 4)  # Rough estimate for short texts
        performance_cache.cache_tokens(text, estimated_count)
        return estimated_count
    
    # For medium texts, use length-based estimation
    if len(text) < 100:
        estimated_count = max(1, len(text) // 3)  # Better estimate for medium texts
        performance_cache.cache_tokens(text, estimated_count)
        return estimated_count
    
    # Fallback to tokenizer only when necessary
    actual_count = len(tokenizer(text)["input_ids"])
    performance_cache.cache_tokens(text, actual_count)
    return actual_count

# OPTIMIZATION: Ultra-fast prompt building with minimal operations
def build_chatml_prompt_ultra_fast(system: str, history: list) -> str:
    """Ultra-fast prompt building with absolute minimal string operations"""
    # OpenHermes-2.5-Mistral-7B uses ChatML format as per official guide
    # Start with system instruction
    parts = [f"<|im_start|>system\n{system.strip()}<|im_end|>\n"]
    
    # Process conversation history
    for i, entry in enumerate(history):
        if entry.strip():  # Only add non-empty messages
            if i % 2 == 0:  # Even indices should be user messages
                parts.append(f"<|im_start|>user\n{entry.strip()}<|im_end|>\n")
            else:  # Odd indices should be assistant responses
                parts.append(f"<|im_start|>assistant\n{entry.strip()}<|im_end|>\n")
    
    # Add the final assistant tag for the AI to respond
    parts.append("<|im_start|>assistant\n")
    
    return "".join(parts)  # Single join operation

# OPTIMIZATION: Enhanced generation parameters for maximum speed
def get_ultra_fast_generation_params(req: MessageRequest, max_output_tokens: int) -> dict:
    """Get ultra-fast generation parameters for maximum speed"""
    base_params = {
        "max_new_tokens": max_output_tokens,
        "temperature": req.temperature,
        "top_p": req.top_p,
        "do_sample": True,
        "pad_token_id": tokenizer.eos_token_id,
        "eos_token_id": tokenizer.eos_token_id,
        "use_cache": True,
        "return_dict_in_generate": False,
    }
    
    if req.ultra_speed:
        # 🚀🚀 ULTRA SPEED MODE: Maximum possible speed
        base_params.update({
            "num_beams": 1,
            "repetition_penalty": 1.0,  # No penalty calculation
            "no_repeat_ngram_size": 0,  # No n-gram blocking
            "early_stopping": False,    # No early stopping logic
            "length_penalty": 1.0,      # No length penalty
            "typical_p": 1.0,           # No typical sampling
            "top_k": 50,                # Balanced for speed and quality
            "do_sample": True,          # Enable sampling for creativity
            "use_cache": True,          # Enable KV cache
            "return_dict_in_generate": False,  # Skip dict conversion
        })
    elif req.speed_mode:
        # 🚀 SPEED MODE: Fast generation with minimal overhead
        base_params.update({
            "num_beams": 1,
            "repetition_penalty": 1.0,  # No penalty calculation
            "no_repeat_ngram_size": 0,  # No n-gram blocking
            "early_stopping": False,    # No early stopping logic
            "length_penalty": 1.0,      # No length penalty
            "typical_p": 1.0,           # No typical sampling
            "top_k": 50,                # Balanced token selection for speed
            "do_sample": True,          # Enable sampling for creativity
            "use_cache": True,          # Enable KV cache
            "return_dict_in_generate": False,  # Skip dict conversion
        })
    else:
        # 🎯 ACCURACY MODE: Balanced quality and speed
        base_params.update({
            "num_beams": 1,
            "repetition_penalty": 1.02,  # Very minimal penalty for quality
            "no_repeat_ngram_size": 1,   # Minimal n-gram blocking
            "early_stopping": False,     # Disable for speed
            "length_penalty": 1.0,       # No length penalty
            "typical_p": 0.98,           # Very slight typical sampling
            "top_k": 60,                 # Balanced token selection
            "use_cache": True,           # Enable KV cache
        })
    
    return base_params

# OPTIMIZATION: Enhanced performance monitoring and batch processing
def build_chatml_prompt_batch(system: str, history: list) -> str:
    """Ultra-fast batch prompt building with minimal string operations"""
    # OpenHermes-2.5-Mistral-7B uses ChatML format as per official guide
    # Start with system instruction
    parts = [f"<|im_start|>system\n{system.strip()}<|im_end|>\n"]
    
    # Process conversation history
    for i, entry in enumerate(history):
        if entry.strip():  # Only add non-empty messages
            if i % 2 == 0:  # Even indices should be user messages
                parts.append(f"<|im_start|>user\n{entry.strip()}<|im_end|>\n")
            else:  # Odd indices should be assistant responses
                parts.append(f"<|im_start|>assistant\n{entry.strip()}<|im_end|>\n")
    
    # Add the final assistant tag for the AI to respond
    parts.append("<|im_start|>assistant\n")
    
    return "".join(parts)  # Single join operation

# Fallback function for compatibility
def build_chatml_prompt(system: str, history: list) -> str:
    """Legacy prompt building - use build_chatml_prompt_batch for better performance"""
    return build_chatml_prompt_batch(system, history)

# OPTIMIZATION: Faster cleaning with precompiled regex
def clean_response(response: str) -> str:
    """Optimized response cleaning - removes all ChatML tags and prevents mid-sentence cuts"""
    # Remove ALL ChatML tags from anywhere in the response
    response = CHATML_TAG_PATTERN.sub('', response)
    
    # Remove any conversation history that might have leaked through
    # Look for patterns like "User: message" or "AI: response" and remove them
    response = re.sub(r'(?:User|AI|Assistant|Human):\s*[^\n]*\n?', '', response, flags=re.IGNORECASE)
    
    # Remove any system prompt text that might have leaked
    response = re.sub(r'Remember: Only generate YOUR response.*?\.\n?', '', response, flags=re.IGNORECASE)
    
    # Clean up any extra whitespace that might be left
    response = re.sub(r'\n\s*\n', '\n', response)  # Remove empty lines
    response = re.sub(r'^\s+', '', response)  # Remove leading whitespace
    response = re.sub(r'\s+$', '', response)  # Remove trailing whitespace
    
    # Only trim if the response is clearly incomplete (very short or ends with obvious incomplete words)
    if response and len(response.strip()) > 10:  # Don't trim short responses
        # Check if it ends with incomplete words (common patterns)
        incomplete_patterns = [
            ' the', ' a ', ' an ', ' and', ' or', ' but', ' if', ' when', ' where', ' why', ' how',
            ' what', ' who', ' which', ' that', ' this', ' these', ' those', ' my', ' your', ' his',
            ' her', ' their', ' our', ' its', ' is', ' are', ' was', ' were', ' have', ' has', ' had',
            ' do', ' does', ' did', ' will', ' would', ' could', ' should', ' might', ' may', ' can'
        ]
        
        response_lower = response.lower()
        for pattern in incomplete_patterns:
            if response_lower.endswith(pattern):
                # Find the last complete sentence or phrase
                last_period = response.rfind('.')
                last_exclamation = response.rfind('!')
                last_question = response.rfind('?')
                last_complete = max(last_period, last_exclamation, last_question)
                
                if last_complete != -1 and last_complete > len(response) * 0.7:  # Only trim if we're not losing too much
                    return response[:last_complete+1].strip()
                break
    
    return response.strip()

# REMOVED: detect_incomplete_response function - was causing timeouts with retry logic
# The model should generate complete responses naturally without needing retries

def test_chatml_cleaning():
    """Test function to verify ChatML tag cleaning works correctly"""
    test_responses = [
        "<|assistant|>I am a helpful AI assistant.",
        "Hello! <|user|>How are you?",
        "This is a normal response without tags.",
        "<|system|>Here is some information.",
        "Mixed content <|assistant|>with tags in the middle.",
        "Ending with <|user|>",
        "<|assistant|>Starting with tag",
        "No tags here, just clean text."
    ]
    
    print("🧪 Testing ChatML tag cleaning...")
    for test_response in test_responses:
        cleaned = clean_response(test_response)
        has_tags = '<|' in cleaned or '|>' in cleaned
        print(f"  Input:  {test_response}")
        print(f"  Output: {cleaned}")
        print(f"  Clean:  {'✅' if not has_tags else '❌'}")
        print()
    
    return "ChatML cleaning test completed"

# OPTIMIZATION: Enhanced session storage with simplified KV caching
def create_session(session_id: str, system_prompt: str) -> dict:
    """Create optimized session with simplified KV caching support"""
    # Store the original system prompt without modification
    # Critical instructions will be added during prompt building instead
    
    return {
        "system_prompt": system_prompt,  # Keep original system prompt intact
        "history": [],
        "kv_cache": None,  # Simple boolean flag instead of complex past_key_values
        "tokenized_context": None,
        "token_count": 0,
        "last_trimmed": 0
    }

# OPTIMIZATION: Advanced context trimming with KV cache management
def trim_history_ultra_aggressive(system: str, history: list, max_tokens: int = 2000) -> list:
    """Ultra-aggressive history trimming for maximum speed with KV cache reset"""
    # Calculate system tokens once
    system_tokens = count_tokens_ultra_fast(f"<|system|>\n{system.strip()}\n")
    total_tokens = system_tokens
    keep_messages = []
    
    # Reserve tokens for new interaction (very aggressive)
    reserved_tokens = 200  # Reduced from 300 for maximum speed
    
    # Process in reverse order (newest first) for better context preservation
    # But limit to maximum 4 messages for ultra-speed
    max_messages = 4  # Reduced from 6 for maximum speed
    
    for i, msg in enumerate(reversed(history)):
        if len(keep_messages) >= max_messages:
            break
            
        # Determine message type based on position (even = user, odd = AI)
        msg_index = len(history) - 1 - i
        if msg_index % 2 == 0:  # User message
            formatted_msg = f"<|user|>\n{msg.strip()}\n"
        else:  # AI response
            formatted_msg = f"<|assistant|>\n{msg.strip()}\n"
        
        # Ultra-fast token counting
        msg_tokens = count_tokens_ultra_fast(formatted_msg)
        
        # Check token budget
        if total_tokens + msg_tokens + reserved_tokens > max_tokens:
            break
            
        total_tokens += msg_tokens
        keep_messages.insert(0, msg)  # Insert at beginning to maintain order
    
    return keep_messages

# OPTIMIZATION: Advanced context trimming with intelligent selection
def trim_history_advanced(system: str, history: list, max_tokens: int = 3000) -> list:
    """Advanced history trimming with intelligent message selection"""
    # Calculate system tokens once
    system_tokens = count_tokens_ultra_fast(f"<|system|>\n{system.strip()}\n")
    total_tokens = system_tokens
    keep_messages = []
    
    # Reserve tokens for new interaction (reduced for more context)
    reserved_tokens = 300  # Reduced for more aggressive trimming
    
    # Process in reverse order (newest first) for better context preservation
    # But limit to maximum 6 messages for speed
    max_messages = 6
    
    for i, msg in enumerate(reversed(history)):
        if len(keep_messages) >= max_messages:
            break
            
        # Determine message type based on position (even = user, odd = AI)
        msg_index = len(history) - 1 - i
        if msg_index % 2 == 0:  # User message
            formatted_msg = f"<|user|>\n{msg.strip()}\n"
        else:  # AI response
            formatted_msg = f"<|assistant|>\n{msg.strip()}\n"
        
        # Ultra-fast token counting
        msg_tokens = count_tokens_ultra_fast(formatted_msg)
        
        # Check token budget
        if total_tokens + msg_tokens + reserved_tokens > max_tokens:
            break
            
        total_tokens += msg_tokens
        keep_messages.insert(0, msg)  # Insert at beginning to maintain order
    
    return keep_messages

# OPTIMIZATION: Smart context trimming with batch processing
def trim_history_smart(system: str, history: list, max_tokens: int = 3500) -> list:
    """Smart history trimming with batch processing and intelligent selection"""
    # Calculate system tokens once
    system_tokens = count_tokens_ultra_fast(f"<|system|>\n{system.strip()}\n")
    total_tokens = system_tokens
    keep_messages = []
    
    # Reserve tokens for new interaction
    reserved_tokens = 400  # Reduced for more context
    
    # Process in reverse order (newest first) for better context preservation
    for i, msg in enumerate(reversed(history)):
        # Determine message type based on position (even = user, odd = AI)
        msg_index = len(history) - 1 - i
        if msg_index % 2 == 0:  # User message
            formatted_msg = f"<|user|>\n{msg.strip()}\n"
        else:  # AI response
            formatted_msg = f"<|assistant|>\n{msg.strip()}\n"
        
        # Ultra-fast token counting
        msg_tokens = count_tokens_ultra_fast(formatted_msg)
        
        # Check token budget
        if total_tokens + msg_tokens + reserved_tokens > max_tokens:
            break
            
        total_tokens += msg_tokens
        keep_messages.insert(0, msg)  # Insert at beginning to maintain order
        
        # Stop if we have enough context (don't process all messages unnecessarily)
        if len(keep_messages) >= 8:  # Limit to 8 messages for speed
            break
    
    return keep_messages

# OPTIMIZATION: Simplified KV cache management without past_key_values
def update_kv_cache(session: dict, inputs: dict, outputs: dict) -> None:
    """Update simplified KV cache for faster subsequent generations"""
    try:
        # Store the full context for next generation
        if hasattr(outputs, 'sequences'):
            session["tokenized_context"] = outputs.sequences[0]
        else:
            session["tokenized_context"] = outputs[0]
        
        session["token_count"] = session["tokenized_context"].shape[0]
        session["kv_cache"] = True  # Simple flag instead of complex past_key_values
        logger.info(f"🚀 Simplified KV cache updated: {session['token_count']} tokens cached")
    except Exception as e:
        logger.warning(f"⚠️ KV cache update failed: {e}")
        session["kv_cache"] = None
        session["tokenized_context"] = None
        session["token_count"] = 0

# OPTIMIZATION: Safe KV cache usage with fallback
def use_kv_cache_safely(session: dict, req: MessageRequest) -> tuple:
    """Safely use simplified KV cache with fallback to full context"""
    try:
        if (session.get("kv_cache") is True and 
            session.get("tokenized_context") is not None and
            session.get("token_count", 0) > 0):
            
            # Validate cache integrity
            cache_tokens = session["token_count"]
            if 0 < cache_tokens < 4096:
                logger.info(f"🚀 Using simplified KV cache: {cache_tokens} tokens cached")
                return True, session["tokenized_context"]
            else:
                logger.warning(f"⚠️ Invalid cache size: {cache_tokens}, falling back to full context")
                return False, None
        else:
            return False, None
    except Exception as e:
        logger.warning(f"⚠️ KV cache validation failed: {e}, falling back to full context")
        return False, None

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "adam")
    correct_password = secrets.compare_digest(credentials.password, "eve2025")
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Unauthorized")

# Session initializer - backend calls this to set up sessions with correct system prompts
@app.post("/init-session")
async def init_session(session_data: dict, request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    """
    Initialize a session with system prompt and other data from the backend
    This ensures the AI server has the correct session data including Tally scenarios
    """
    session_id = session_data.get("session_id")
    system_prompt = session_data.get("system_prompt", "")
    
    if not session_id:
        raise HTTPException(400, "Missing session_id")
    
    if not system_prompt:
        raise HTTPException(400, "Missing system_prompt")
    
    with session_lock:
        # Create session with the correct system prompt from backend
        user_sessions[session_id] = create_session(session_id, system_prompt)
        
        # Log the session initialization
        enhanced_prompt = user_sessions[session_id]["system_prompt"]
        logger.info(f"🎯 Session {session_id} initialized with backend data")
        logger.info(f"📝 System prompt length: {len(system_prompt)} characters")
        logger.info(f"📝 Enhanced prompt: {enhanced_prompt}")
    
    return {"message": "Session initialized successfully", "session_id": session_id}

# Scenario setter (legacy - kept for backward compatibility)
@app.post("/scenario")
async def set_scenario(scenario: InitScenario, request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    session_id = request.cookies.get("session_id", str(uuid4()))
    
    with session_lock:
        user_sessions[session_id] = create_session(session_id, scenario.scenario)
        
        # Log the scenario being set for debugging
        enhanced_prompt = user_sessions[session_id]["system_prompt"]
        logger.info(f"🎯 Scenario set for session {session_id}")
        logger.info(f"📝 Original prompt: {scenario.scenario}")
        logger.info(f"📝 Enhanced prompt: {enhanced_prompt}")
    
    response = JSONResponse({"message": "Scenario set!"})
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response

# OPTIMIZED chat endpoint with performance improvements
@app.post("/chat")
async def chat(req: MessageRequest, request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    # Performance monitoring start with timeout protection
    total_start_time = time.time()
    
    try:
        # Set request timeout
        if hasattr(asyncio, 'wait_for'):
            # Use asyncio timeout if available
            return await asyncio.wait_for(
                _chat_internal(req, request, credentials),
                timeout=REQUEST_TIMEOUT
            )
        else:
            # Fallback to synchronous timeout
            return await _chat_internal(req, request, credentials)
            
    except asyncio.TimeoutError:
        logger.error(f"❌ Request timeout after {REQUEST_TIMEOUT}s")
        raise HTTPException(408, f"Request timeout after {REQUEST_TIMEOUT} seconds")
    except Exception as e:
        logger.error(f"❌ Chat request failed: {e}")
        raise HTTPException(500, f"Chat request failed: {str(e)}")

async def _chat_internal(req: MessageRequest, request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    # Get session ID from request
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(400, "Missing session ID")
    
    # Check if we have this session in memory
    session_start = time.time()
    with session_lock:
        session = user_sessions.get(session_id)
        
        # If session not found in memory, reject the request
        if session is None:
            logger.error(f"❌ Session {session_id} not found in memory - backend must initialize sessions first")
            raise HTTPException(404, "Session not found. Backend must initialize session with /init-session first.")
    
    # Add user message to history (without prefix for cleaner AI responses)
    session["history"].append(req.message)
    
    # OPTIMIZATION: Always build full context to ensure system prompt is included
    # KV cache approach was broken - it bypassed system prompt and context
    logger.info("🔄 Building full context (ensuring system prompt is included)")
    
    # Trim history with optimizations
    trim_start = time.time()
    # Simple history trimming - keep last 10 messages for speed
    if len(session["history"]) > 10:
        session["history"] = session["history"][-10:]
    trim_time = time.time() - trim_start
    
    # Build prompt with system prompt and conversation history
    prompt_start = time.time()
    full_prompt = build_chatml_prompt_ultra_fast(
        session["system_prompt"],
        session["history"]
    )
    prompt_time = time.time() - prompt_start
    
    # Log the prompt being sent to the model for debugging
    logger.info(f"📝 System prompt: {session['system_prompt']}")
    logger.info(f"📝 Full prompt length: {len(full_prompt)} characters")
    logger.info(f"📝 History messages: {len(session['history'])}")
    
    # DEBUG: Log the actual prompt being sent to the model
    logger.info(f"🔍 FULL PROMPT SENT TO MODEL:")
    logger.info(f"🔍 {full_prompt}")
    logger.info(f"🔍 END OF PROMPT")
    
    # DEBUG: Log detailed history breakdown
    logger.info(f"🔍 HISTORY BREAKDOWN:")
    for i, entry in enumerate(session["history"]):
        role = "USER" if i % 2 == 0 else "ASSISTANT"
        logger.info(f"🔍 [{i}] {role}: {entry[:100]}{'...' if len(entry) > 100 else ''}")
    logger.info(f"🔍 END HISTORY BREAKDOWN")
    
    # Tokenize full prompt
    inputs = tokenizer(
        full_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=4096,
        padding=True
    ).to(model.device)
    
    session_time = time.time() - session_start
    
    # Tokenize with optimizations
    start_tokenize = time.time()
    # inputs already tokenized above
    tokenize_time = time.time() - start_tokenize
    
    # Calculate available context
    if isinstance(inputs, dict):
        # New context concatenation approach
        input_tokens = inputs["input_ids"].shape[1]
    else:
        # Original tensor approach
        input_tokens = inputs.input_ids.shape[1]
    
    max_output_tokens = min(req.max_tokens, 4096 - input_tokens)
    
    # Generation parameters
    generation_params = get_ultra_fast_generation_params(req, max_output_tokens)
    
    # Add better end-of-sequence detection to prevent mid-sentence cuts
    generation_params.update({
        "eos_token_id": tokenizer.eos_token_id,
        "pad_token_id": tokenizer.eos_token_id,
        "early_stopping": False,  # Disable early stopping to allow complete sentences
        "do_sample": True,        # Enable sampling for more natural responses
        "temperature": max(req.temperature, 0.7),  # Ensure some creativity
        "max_new_tokens": max(req.max_tokens, 100),  # Ensure enough tokens for complete responses
    })
    
    # OPTIMIZATION: Remove conflicting parameters that are already in inputs
    # This prevents "multiple values for keyword argument" errors
    if "attention_mask" in generation_params and "attention_mask" in inputs:
        del generation_params["attention_mask"]
    if "position_ids" in generation_params and "position_ids" in inputs:
        del generation_params["position_ids"]
    
    # OPTIMIZATION: No more past_key_values - using context concatenation instead
    # This avoids the cache position issues entirely
    
    # Generation with performance monitoring and timeout protection
    generation_start = time.time()
    try:
        with model_lock, torch.no_grad():
            # Set generation timeout to prevent hanging
            generation_timeout = GENERATION_TIMEOUT
            
            # Use torch.jit.optimized_execution for better performance
            if hasattr(torch.jit, 'optimized_execution'):
                with torch.jit.optimized_execution(True):
                    output = model.generate(
                        **inputs, 
                        **generation_params,
                        max_time=generation_timeout  # Prevent infinite generation
                    )
            else:
                output = model.generate(
                    **inputs, 
                    **generation_params
                )
                
    except RuntimeError as e:
        if "Half" in str(e) or "overflow" in str(e):
            logger.warning(f"⚠️ Precision error: {e}")
            inputs = {k: v.to(torch.float32) if torch.is_floating_point(v) else v for k, v in inputs.items()}
            with model_lock, torch.no_grad():
                output = model.generate(**inputs, **generation_params)
        else:
            logger.error(f"⚠️ Generation error: {e}")
            raise HTTPException(500, "Model generation failed")
    except Exception as e:
        logger.error(f"❌ Unexpected generation error: {e}")
        raise HTTPException(500, f"Model generation failed: {str(e)}")
    
    generation_time = time.time() - generation_start
    
    # Check if generation took too long
    if generation_time > GENERATION_TIMEOUT:
        logger.warning(f"⚠️ Generation took {generation_time:.2f}s (exceeded {GENERATION_TIMEOUT}s timeout)")
        # Force memory cleanup after long generation
        optimize_memory_usage()
    
    # OPTIMIZATION: KV cache removed - always use full context for better responses
    
    # Extract and clean response
    response_start = time.time()
    if hasattr(output, 'sequences'):
        if isinstance(inputs, dict):
            response_tokens = output.sequences[0][inputs["input_ids"].shape[1]:]
        else:
            response_tokens = output.sequences[0][inputs.input_ids.shape[1]:]
    else:
        if isinstance(inputs, dict):
            response_tokens = output[0][inputs["input_ids"].shape[1]:]
        else:
            response_tokens = output[0][inputs.input_ids.shape[1]:]
    
    response = tokenizer.decode(response_tokens, skip_special_tokens=True).strip()
    response = clean_response(response)
    
    # Final safety check: ensure no ChatML tags remain
    if '<|' in response or '|>' in response:
        logger.warning(f"⚠️ ChatML tags detected in response, applying final cleanup")
        response = re.sub(r'<\|[\w]+\|>', '', response)
        response = re.sub(r'\n\s*\n', '\n', response)  # Clean up extra whitespace
        response = response.strip()
    
    # Final safety check: ensure no conversation history leaked through
    if any(pattern in response.lower() for pattern in ['user:', 'ai:', 'assistant:', 'human:']):
        logger.warning(f"⚠️ Conversation history detected in response, applying aggressive cleanup")
        # Remove any lines that start with User:, AI:, Assistant:, or Human:
        lines = response.split('\n')
        cleaned_lines = []
        for line in lines:
            line_lower = line.lower().strip()
            if not any(line_lower.startswith(pattern) for pattern in ['user:', 'ai:', 'assistant:', 'human:']):
                cleaned_lines.append(line)
        response = '\n'.join(cleaned_lines).strip()
        
        # If we removed everything, provide a fallback
        if not response.strip():
            response = "I apologize, but I need to provide a fresh response. Could you please repeat your question?"
    
    # REMOVED: Incomplete sentence retry logic that was causing timeouts
    # The model should generate complete responses naturally
    
    response_time = time.time() - response_start
    
    # Enhanced performance logging
    total_time = time.time() - total_start_time
    tokens_per_sec = max_output_tokens / generation_time if generation_time > 0 else 0
    
    logger.info(f"🚀 PERFORMANCE BREAKDOWN:")
    logger.info(f"  📊 Session: {session_time:.3f}s (trim: {trim_time:.3f}s, prompt: {prompt_time:.3f}s)")
    logger.info(f"  🔤 Tokenize: {tokenize_time:.3f}s")
    logger.info(f"  ⚙️ Generate: {generation_time:.3f}s")
    logger.info(f"  🧹 Response: {response_time:.3f}s")
    logger.info(f"  ⏱️ Total: {total_time:.3f}s")
    logger.info(f"  🚀 Speed: {tokens_per_sec:.1f} tokens/s")
    logger.info(f"  📝 Context: {len(session['history'])} messages, {input_tokens} tokens")
    
    # OPTIMIZATION: Enhanced logging for model optimizations
    logger.info(f"  🔥 TF32: {'✅ Enabled' if torch.backends.cuda.matmul.allow_tf32 else '❌ Disabled'}")
    logger.info(f"  🔥 Compiled: {'✅ Yes' if hasattr(model, '_compiled_call_impl') else '❌ No'}")
    
    # Performance warnings with ultra-speed mode
    if req.ultra_speed and total_time > 2.0:
        logger.warning(f"⚠️ Ultra-speed mode is slow: {total_time:.2f}s (expected <2s)")
        logger.warning(f"🚀 Performance diagnostic: Check if model is in performance mode")
    elif req.speed_mode and total_time > 3.0:
        logger.warning(f"⚠️ Speed mode is slow: {total_time:.2f}s (expected <3s)")
        logger.warning(f"🚀 Performance diagnostic: Check generation parameters")
    elif not req.speed_mode and total_time > 6.0:
        logger.warning(f"⚠️ Accuracy mode is slow: {total_time:.2f}s (expected <6s)")
    
    # Memory optimization after response
    if total_time > 5.0:  # Only optimize if response was slow
        optimize_memory_usage()
    
    # Performance diagnostic for slow responses
    if generation_time > 5.0:
        logger.warning(f"🚀 Performance diagnostic: Generation took {generation_time:.2f}s")
        logger.warning(f"  - Model compilation: {'✅' if hasattr(model, '_compiled_call_impl') else '❌'}")
        logger.warning(f"  - Flash Attention: {'✅' if hasattr(model, 'config') and getattr(model.config, 'attn_implementation', None) == 'flash_attention_2' else '❌'}")
        logger.warning(f"  - TF32: {'✅' if torch.backends.cuda.matmul.allow_tf32 else '❌'}")
        logger.warning(f"  - KV Cache: {'✅' if session.get('kv_cache') else '❌'}")
    
    # Save to history (without prefix for cleaner AI responses)
    with session_lock:
        if session_id in user_sessions:
            session["history"].append(response)
    
    return {"response": response}

# Health check endpoint with comprehensive monitoring
@app.get("/health")
async def health_check():
    """Comprehensive health check to prevent crashes and timeouts"""
    try:
        # Check model status
        model_healthy = model is not None and hasattr(model, 'device')
        
        # Check memory usage
        memory_info = {}
        if hasattr(torch, 'cuda') and torch.cuda.is_available():
            memory_info = {
                "gpu_allocated_gb": round(torch.cuda.memory_allocated() / 1024**3, 2),
                "gpu_reserved_gb": round(torch.cuda.memory_reserved() / 1024**3, 2),
                "gpu_available_gb": round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2),
                "gpu_utilization": "high" if torch.cuda.memory_allocated() / 1024**3 > 8.0 else "normal"
            }
        
        # Check if memory usage is critical
        if memory_info.get("gpu_allocated_gb", 0) > 10.0:
            logger.warning(f"🚨 CRITICAL: GPU memory usage is {memory_info['gpu_allocated_gb']}GB - forcing cleanup")
            optimize_memory_usage()
        
        return {
            "status": "healthy" if model_healthy else "unhealthy",
            "model": model_name,
            "model_healthy": model_healthy,
            "memory_info": memory_info,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

# Test ChatML cleaning endpoint
@app.get("/test-cleaning")
async def test_cleaning_endpoint():
    """Test endpoint to verify ChatML tag cleaning works correctly"""
    try:
        result = test_chatml_cleaning()
        return {"message": "ChatML cleaning test completed", "result": result}
    except Exception as e:
        return {"error": f"Test failed: {str(e)}"}

# Test endpoint to verify ChatML format compatibility
@app.get("/test-chatml-format")
async def test_chatml_format_endpoint(credentials: HTTPBasicCredentials = Depends(authenticate)):
    """Test different ChatML formats to see which one OpenHermes supports"""
    try:
        test_system = "You are a helpful AI assistant. You must always say 'I am an AI assistant' when asked about your identity."
        test_history = ["Hello", "Hi there"]
        
        # Test different formats
        formats = {
            "OpenHermes format": f"<|im_start|>system\n{test_system}<|im_end|>\n<|im_start|>user\n{test_history[0]}<|im_end|>\n<|im_start|>assistant\n",
            "Standard ChatML": f"<|system|>\n{test_system}\n<|user|>\n{test_history[0]}\n<|assistant|>\n",
            "Simple format": f"System: {test_system}\n\nUser: {test_history[0]}\n\nAssistant: ",
            "No tags": f"{test_system}\n\nUser: {test_history[0]}\n\nAssistant: "
        }
        
        results = {}
        for format_name, prompt in formats.items():
            try:
                # Tokenize the prompt
                inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(model.device)
                
                # Generate a short response
                with torch.no_grad():
                    output = model.generate(
                        **inputs,
                        max_new_tokens=20,
                        temperature=0.1,
                        do_sample=False,
                        pad_token_id=tokenizer.eos_token_id,
                        eos_token_id=tokenizer.eos_token_id
                    )
                
                response = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
                results[format_name] = {
                    "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    "response": response,
                    "success": True
                }
            except Exception as e:
                results[format_name] = {
                    "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    "error": str(e),
                    "success": False
                }
        
        return {
            "message": "ChatML format compatibility test completed",
            "results": results,
            "recommendation": "Check which format generates the most appropriate response"
        }
    except Exception as e:
        return {"error": f"Test failed: {str(e)}"}

# Performance optimization endpoint
@app.post("/optimize-performance")
async def optimize_performance_endpoint(credentials: HTTPBasicCredentials = Depends(authenticate)):
    """Force performance optimizations and return current status"""
    try:
        # Force performance optimizations
        optimize_model_for_speed()
        optimize_memory_usage()
        
        # Get current performance status
        status = {
            "model_compiled": hasattr(model, '_compiled_call_impl'),
            "flash_attention": hasattr(model, 'config') and getattr(model.config, 'attn_implementation', None) == 'flash_attention_2',
            "tf32_enabled": torch.backends.cuda.matmul.allow_tf32 if hasattr(torch.backends.cuda, 'matmul') else False,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": str(torch.cuda.current_device()) if torch.cuda.is_available() else "N/A",
            "memory_allocated": f"{torch.cuda.memory_allocated() / 1024**3:.2f} GB" if torch.cuda.is_available() else "N/A",
            "memory_reserved": f"{torch.cuda.memory_reserved() / 1024**3:.2f} GB" if torch.cuda.is_available() else "N/A"
        }
        
        return {
            "message": "Performance optimizations applied",
            "status": status,
            "recommendations": [
                "Ensure ultra_speed=True for maximum performance",
                "Use speed_mode=True for balanced speed/quality",
                "Always use full context for better responses"
            ]
        }
    except Exception as e:
        return {"error": f"Performance optimization failed: {str(e)}"}

# Debug endpoint to verify system prompt application
@app.get("/debug-session/{session_id}")
async def debug_session_endpoint(session_id: str, credentials: HTTPBasicCredentials = Depends(authenticate)):
    """Debug endpoint to verify system prompt and context are properly applied"""
    try:
        with session_lock:
            if (session := user_sessions.get(session_id)) is None:
                raise HTTPException(404, "Session not found")
            
            # Build the prompt that would be sent to the model
            full_prompt = build_chatml_prompt_ultra_fast(
                session["system_prompt"],
                session["history"]
            )
            
            return {
                "session_id": session_id,
                "system_prompt": session["system_prompt"],
                "history_length": len(session["history"]),
                "history": session["history"],
                "full_prompt_preview": full_prompt[:500] + "..." if len(full_prompt) > 500 else full_prompt,
                "full_prompt_length": len(full_prompt),
                "kv_cache_status": "Disabled - using full context for better responses"
            }
    except Exception as e:
        return {"error": f"Debug failed: {str(e)}"}

# Debug endpoint to list all active sessions
@app.get("/debug-sessions")
async def debug_sessions_endpoint(credentials: HTTPBasicCredentials = Depends(authenticate)):
    """Debug endpoint to list all active sessions and their system prompts"""
    try:
        with session_lock:
            sessions_info = {}
            for session_id, session in user_sessions.items():
                sessions_info[session_id] = {
                    "system_prompt_length": len(session.get("system_prompt", "")),
                    "system_prompt_preview": session.get("system_prompt", "")[:200] + "..." if len(session.get("system_prompt", "")) > 200 else session.get("system_prompt", ""),
                    "history_length": len(session.get("history", [])),
                    "has_tally_scenario": "**Scenario**:" in session.get("system_prompt", "")
                }
            
            return {
                "total_sessions": len(user_sessions),
                "sessions": sessions_info
            }
    except Exception as e:
        return {"error": f"Debug failed: {str(e)}"}

# Speed test endpoint for performance benchmarking
@app.post("/speed-test")
async def speed_test(credentials: HTTPBasicCredentials = Depends(authenticate)):
    """Test AI generation speed with different parameters and KV caching"""
    try:
        # OPTIMIZATION: Pre-warm model for accurate speed testing
        logger.info("🔥 Pre-warming model for accurate speed testing...")
        warmup_input = tokenizer("Warmup", return_tensors="pt").to(model.device)
        with torch.no_grad():
            model.generate(**warmup_input, max_new_tokens=1)
        logger.info("✅ Model warmed up")
        
        test_prompts = [
            "Hello, how are you?",
            "What is the weather like today?",
            "Explain quantum computing in simple terms.",
            "Write a short poem about technology."
        ]
        
        results = []
        
        for i, prompt in enumerate(test_prompts):
            logger.info(f"🧪 Speed test {i+1}/4: {prompt}")
            
            # Test ultra-speed mode
            start_time = time.time()
            ultra_response = await chat(MessageRequest(
                message=prompt,
                max_tokens=50,
                temperature=0.7,
                top_p=0.9,
                ultra_speed=True
            ), MockRequest(), credentials)
            ultra_time = time.time() - start_time
            
            # Test speed mode
            start_time = time.time()
            speed_response = await chat(MessageRequest(
                message=prompt,
                max_tokens=50,
                temperature=0.7,
                top_p=0.9,
                speed_mode=True
            ), MockRequest(), credentials)
            speed_time = time.time() - start_time
            
            # Test accuracy mode
            start_time = time.time()
            accuracy_response = await chat(MessageRequest(
                message=prompt,
                max_tokens=50,
                temperature=0.7,
                top_p=0.9,
                speed_mode=False
            ), MockRequest(), credentials)
            accuracy_time = time.time() - start_time
            
            results.append({
                "prompt": prompt,
                "ultra_speed_mode": {
                    "time": round(ultra_time, 2),
                    "response": ultra_response.get("response", "")[:100]
                },
                "speed_mode": {
                    "time": round(speed_time, 2),
                    "response": speed_response.get("response", "")[:100]
                },
                "accuracy_mode": {
                    "time": round(accuracy_time, 2),
                    "response": accuracy_response.get("response", "")[:100]
                },
                "ultra_speedup": round(accuracy_time / ultra_time, 2) if ultra_time > 0 else 0,
                "speed_speedup": round(accuracy_time / speed_time, 2) if speed_time > 0 else 0
            })
        
        # Calculate averages
        avg_ultra_time = sum(r["ultra_speed_mode"]["time"] for r in results) / len(results)
        avg_speed_time = sum(r["speed_mode"]["time"] for r in results) / len(results)
        avg_accuracy_time = sum(r["accuracy_mode"]["time"] for r in results) / len(results)
        avg_ultra_speedup = avg_accuracy_time / avg_ultra_time if avg_ultra_time > 0 else 0
        avg_speed_speedup = avg_accuracy_time / avg_speed_time if avg_speed_time > 0 else 0
        
        return {
            "test_results": results,
            "summary": {
                "average_ultra_speed_time": round(avg_ultra_time, 2),
                "average_speed_mode_time": round(avg_speed_time, 2),
                "average_accuracy_mode_time": round(avg_accuracy_time, 2),
                "average_ultra_speedup": round(avg_ultra_speedup, 2),
                "average_speed_speedup": round(avg_speed_speedup, 2),
                "recommendation": f"Use ultra_speed=True for maximum performance ({avg_ultra_speedup:.1f}x faster than accuracy mode)"
            }
        }
        
    except Exception as e:
        logger.error(f"Speed test failed: {e}")
        raise HTTPException(500, f"Speed test failed: {str(e)}")

# Context optimization endpoint
@app.post("/optimize-context")
async def optimize_context(request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    """Optimize context building for faster responses"""
    try:
        session_id = request.cookies.get("session_id")
        if not session_id:
            raise HTTPException(400, "Missing session ID")
        
        with session_lock:
            if (session := user_sessions.get(session_id)) is None:
                raise HTTPException(404, "Session not found")
            
            # Analyze current context
            original_history = session["history"].copy()
            original_tokens = count_tokens_ultra_fast(
                build_chatml_prompt_ultra_fast(session["system_prompt"], original_history)
            )
            
            # Optimize context
            optimized_history = trim_history_advanced(
                system=session["system_prompt"],
                history=original_history,
                max_tokens=3000
            )
            
            optimized_tokens = count_tokens_ultra_fast(
                build_chatml_prompt_ultra_fast(session["system_prompt"], optimized_history)
            )
            
            # Apply optimization
            session["history"] = optimized_history
            
            return {
                "message": "Context optimized for speed",
                "original_messages": len(original_history),
                "optimized_messages": len(optimized_history),
                "original_tokens": original_tokens,
                "optimized_tokens": optimized_tokens,
                "token_reduction": original_tokens - optimized_tokens,
                "speedup_estimate": f"{(original_tokens / optimized_tokens):.1f}x faster"
            }
            
    except Exception as e:
        logger.error(f"Context optimization failed: {e}")
        raise HTTPException(500, f"Context optimization failed: {str(e)}")

# Mock request for speed testing
class MockRequest:
    def __init__(self):
        self.cookies = {"session_id": "speed_test_session"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1) 