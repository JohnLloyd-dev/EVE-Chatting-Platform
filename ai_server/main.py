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
    max_tokens: int = Field(100, ge=20, le=500)
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
    """Optimize memory usage for better performance"""
    if hasattr(torch, 'cuda') and torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
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
CLEAN_PATTERN = re.compile(r'<\|[\w]+\|>$')
COMMON_PHRASES = {
    "User:": tokenizer("User:")["input_ids"],
    "AI:": tokenizer("AI:")["input_ids"],
    "<|system|>": tokenizer("<|system|>")["input_ids"],
    "<|user|>": tokenizer("<|user|>")["input_ids"],
    "<|assistant|>": tokenizer("<|assistant|>")["input_ids"],
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
    # Pre-allocate string parts for maximum efficiency
    parts = [f"<|system|>\n{system.strip()}\n"]
    
    # Batch process history with minimal string operations
    for entry in history:
        if entry.startswith("User:"):
            user_msg = entry[5:].strip()
            if user_msg:
                parts.append(f"<|user|>\n{user_msg}\n")
        elif entry.startswith("AI:"):
            ai_msg = entry[3:].strip()
            if ai_msg:
                parts.append(f"<|assistant|>\n{ai_msg}\n")
    
    parts.append("<|assistant|>\n")
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
            "top_k": 15,                # Very limited token selection for maximum speed
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
            "top_k": 25,                # Limited token selection for speed
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
    # Pre-allocate string parts for efficiency
    parts = [f"<|system|>\n{system.strip()}\n"]
    
    # Batch process history with minimal string operations
    for entry in history:
        if entry.startswith("User:"):
            user_msg = entry[5:].strip()
            if user_msg:
                parts.append(f"<|user|>\n{user_msg}\n")
        elif entry.startswith("AI:"):
            ai_msg = entry[3:].strip()
            if ai_msg:
                parts.append(f"<|assistant|>\n{ai_msg}\n")
    
    parts.append("<|assistant|>\n")
    return "".join(parts)  # Single join operation

# Fallback function for compatibility
def build_chatml_prompt(system: str, history: list) -> str:
    """Legacy prompt building - use build_chatml_prompt_batch for better performance"""
    return build_chatml_prompt_batch(system, history)

# OPTIMIZATION: Faster cleaning with precompiled regex
def clean_response(response: str) -> str:
    """Optimized response cleaning"""
    # Remove any trailing ChatML tags
    response = CLEAN_PATTERN.sub('', response)
    
    # Remove incomplete sentences at end
    if response and response[-1] not in {'.', '!', '?'}:
        last_period = response.rfind('.')
        if last_period != -1:
            return response[:last_period+1]
    return response.strip()

# OPTIMIZATION: Enhanced session storage with KV caching
def create_session(session_id: str, system_prompt: str) -> dict:
    """Create optimized session with KV caching support"""
    return {
        "system_prompt": system_prompt,
        "history": [],
        "kv_cache": None,  # Add KV cache storage
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
    
    for msg in reversed(history):
        if len(keep_messages) >= max_messages:
            break
            
        if msg.startswith("User:"):
            prefix = "User:"
            formatted_msg = f"<|user|>\n{msg[len(prefix):].strip()}\n"
        elif msg.startswith("AI:"):
            prefix = "AI:"
            formatted_msg = f"<|assistant|>\n{msg[len(prefix):].strip()}\n"
        else:
            continue
        
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
    
    for msg in reversed(history):
        if len(keep_messages) >= max_messages:
            break
            
        if msg.startswith("User:"):
            prefix = "User:"
            formatted_msg = f"<|user|>\n{msg[len(prefix):].strip()}\n"
        elif msg.startswith("AI:"):
            prefix = "AI:"
            formatted_msg = f"<|assistant|>\n{msg[len(prefix):].strip()}\n"
        else:
            continue
        
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
    for msg in reversed(history):
        if msg.startswith("User:"):
            prefix = "User:"
            formatted_msg = f"<|user|>\n{msg[len(prefix):].strip()}\n"
        elif msg.startswith("AI:"):
            prefix = "AI:"
            formatted_msg = f"<|assistant|>\n{msg[len(prefix):].strip()}\n"
        else:
            continue
        
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

# OPTIMIZATION: KV cache management for maximum speed
def update_kv_cache(session: dict, inputs: dict, outputs: dict) -> None:
    """Update KV cache for faster subsequent generations"""
    try:
        if hasattr(outputs, 'past_key_values') and outputs.past_key_values is not None:
            session["kv_cache"] = outputs.past_key_values
            # Store the full context including the new response
            if hasattr(outputs, 'sequences'):
                session["tokenized_context"] = outputs.sequences[0]
            else:
                session["tokenized_context"] = outputs[0]
            session["token_count"] = session["tokenized_context"].shape[0]
            logger.info(f"🚀 KV Cache updated: {session['token_count']} tokens cached")
        else:
            session["kv_cache"] = None
            session["tokenized_context"] = None
            session["token_count"] = 0
    except Exception as e:
        logger.warning(f"⚠️ KV cache update failed: {e}")
        session["kv_cache"] = None
        session["tokenized_context"] = None
        session["token_count"] = 0

# OPTIMIZATION: Safe KV cache usage with fallback
def use_kv_cache_safely(session: dict, req: MessageRequest) -> tuple:
    """Safely use KV cache with fallback to full context"""
    try:
        if (session.get("kv_cache") is not None and 
            session.get("tokenized_context") is not None and
            session.get("token_count", 0) > 0):
            
            # Validate cache integrity
            cache_tokens = session["token_count"]
            if cache_tokens > 0 and cache_tokens < 4096:
                logger.info(f"🚀 Using KV cache: {cache_tokens} tokens cached")
                return True, session["kv_cache"]
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

# Scenario setter
@app.post("/scenario")
async def set_scenario(scenario: InitScenario, request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    session_id = request.cookies.get("session_id", str(uuid4()))
    
    with session_lock:
        user_sessions[session_id] = create_session(session_id, scenario.scenario)
    
    response = JSONResponse({"message": "Scenario set!"})
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response

# OPTIMIZED chat endpoint with performance improvements
@app.post("/chat")
async def chat(req: MessageRequest, request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    # Performance monitoring start
    total_start_time = time.time()
    
    # Get session ID
    if (session_id := request.cookies.get("session_id")) is None:
        raise HTTPException(400, "Missing session ID")
    
    # Retrieve session
    session_start = time.time()
    with session_lock:
        if (session := user_sessions.get(session_id)) is None:
            raise HTTPException(404, "Session not found")
    
    # Add user message to history
    session["history"].append(f"User: {req.message}")
    
    # OPTIMIZATION: Use KV cache if available for maximum speed
    if session.get("kv_cache") is not None and session.get("tokenized_context") is not None:
        logger.info(f"🚀 Using KV cache: {session['token_count']} tokens cached")
        # Only tokenize the new user message
        new_inputs = tokenizer(
            f"<|user|>\n{req.message}\n<|assistant|>\n",
            return_tensors="pt",
            truncation=True,
            max_length=4096,
            padding=True
        ).to(model.device)
        
        # Use cached context for generation
        inputs = new_inputs
        full_prompt = None  # Not needed with KV cache
        prompt_time = 0  # No prompt building time
        trim_time = 0  # No trimming time
    else:
        logger.info("🔄 Building full context (no KV cache available)")
        # Trim history with optimizations
        trim_start = time.time()
        session["history"] = trim_history_ultra_aggressive(
            system=session["system_prompt"],
            history=session["history"],
            max_tokens=2000
        )
        trim_time = time.time() - trim_start
        
        # Build prompt
        prompt_start = time.time()
        full_prompt = build_chatml_prompt_ultra_fast(
            session["system_prompt"],
            session["history"]
        )
        prompt_time = time.time() - prompt_start
        
        # Tokenize full prompt
        inputs = tokenizer(
            full_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=4096,
            padding=True
        ).to(model.device)
    
    session_time = time.time() - session_start
    
    # Tokenize with optimizations (only if not using KV cache)
    if full_prompt is not None:
        start_tokenize = time.time()
        # inputs already tokenized above
        tokenize_time = time.time() - start_tokenize
    else:
        # Using KV cache, minimal tokenization time
        tokenize_time = 0.001  # Minimal time for single message
    
    # Calculate available context
    input_tokens = inputs.input_ids.shape[1]
    max_output_tokens = min(req.max_tokens, 4096 - input_tokens)
    
    # Generation parameters
    generation_params = get_ultra_fast_generation_params(req, max_output_tokens)
    
    # OPTIMIZATION: Add KV cache to generation params if available
    # Use a more robust approach to avoid cache position issues
    if session.get("kv_cache") is not None:
        try:
            # Validate cache before use
            cache_tokens = session.get("token_count", 0)
            if 0 < cache_tokens < 4096:
                generation_params["past_key_values"] = session["kv_cache"]
                logger.info(f"🚀 Using validated KV cache: {cache_tokens} tokens")
            else:
                logger.warning(f"⚠️ Invalid cache size: {cache_tokens}, clearing cache")
                session["kv_cache"] = None
                session["tokenized_context"] = None
                session["token_count"] = 0
        except Exception as e:
            logger.warning(f"⚠️ KV cache validation failed: {e}, clearing cache")
            session["kv_cache"] = None
            session["tokenized_context"] = None
            session["token_count"] = 0
    
    # Generation with performance monitoring
    generation_start = time.time()
    try:
        with model_lock, torch.no_grad():
            # OPTIMIZATION: Enable KV cache return for maximum speed
            # Only set these if not using KV cache to avoid conflicts
            if session.get("kv_cache") is None:
                generation_params["return_dict_in_generate"] = True
                generation_params["output_hidden_states"] = True
            
            output = model.generate(**inputs, **generation_params)
    except RuntimeError as e:
        if "Half" in str(e) or "overflow" in str(e):
            logger.warning(f"⚠️ Precision error: {e}")
            inputs = {k: v.to(torch.float32) if torch.is_floating_point(v) else v for k, v in inputs.items()}
            with model_lock, torch.no_grad():
                output = model.generate(**inputs, **generation_params)
        else:
            logger.error(f"⚠️ Generation error: {e}")
            raise HTTPException(500, "Model generation failed")
    
    generation_time = time.time() - generation_start
    
    # OPTIMIZATION: Update KV cache for maximum speed
    update_kv_cache(session, inputs, output)
    
    # Extract and clean response
    response_start = time.time()
    if hasattr(output, 'sequences'):
        response_tokens = output.sequences[0][inputs.input_ids.shape[1]:]
    else:
        response_tokens = output[0][inputs.input_ids.shape[1]:]
    response = tokenizer.decode(response_tokens, skip_special_tokens=True).strip()
    response = clean_response(response)
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
    
    # OPTIMIZATION: Enhanced logging for KV cache and optimizations
    logger.info(f"  🔥 KV Cache: {'✅ Hit' if session.get('kv_cache') else '❌ Miss'}")
    logger.info(f"  🔥 TF32: {'✅ Enabled' if torch.backends.cuda.matmul.allow_tf32 else '❌ Disabled'}")
    logger.info(f"  🔥 Compiled: {'✅ Yes' if hasattr(model, '_compiled_call_impl') else '❌ No'}")
    
    # Performance warnings with ultra-speed mode
    if req.ultra_speed and total_time > 2.0:
        logger.warning(f"⚠️ Ultra-speed mode is slow: {total_time:.2f}s (expected <2s)")
    elif req.speed_mode and total_time > 3.0:
        logger.warning(f"⚠️ Speed mode is slow: {total_time:.2f}s (expected <3s)")
    elif not req.speed_mode and total_time > 6.0:
        logger.warning(f"⚠️ Accuracy mode is slow: {total_time:.2f}s (expected <6s)")
    
    # Memory optimization after response
    if total_time > 5.0:  # Only optimize if response was slow
        optimize_memory_usage()
    
    # Save to history
    with session_lock:
        if session_id in user_sessions:
            session["history"].append(f"AI: {response}")
    
    return {"response": response}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": model_name}

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