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

# Load model
model_name = "teknium/OpenHermes-2.5-Mistral-7B"

# Check if GPU is available
gpu_available = torch.cuda.is_available()
logger.info(f"GPU available: {gpu_available}")

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token  # Set pad token

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
except Exception as e:
    logger.critical(f"❌ Model loading failed: {e}")
    raise RuntimeError(f"Failed to load model: {e}")

model.eval()
logger.info("🎯 Model ready for inference")

# OPTIMIZATION: Cache tokenizer results for common phrases
CLEAN_PATTERN = re.compile(r'<\|[\w]+\|>$')
COMMON_PHRASES = {
    "User:": tokenizer("User:")["input_ids"],
    "AI:": tokenizer("AI:")["input_ids"],
    "<|system|>": tokenizer("<|system|>")["input_ids"],
    "<|user|>": tokenizer("<|user|>")["input_ids"],
    "<|assistant|>": tokenizer("<|assistant|>")["input_ids"],
}

# Enhanced prompt engineering with caching
def build_chatml_prompt(system: str, history: list) -> str:
    """Optimized prompt building with caching"""
    prompt = f"<|system|>\n{system.strip()}\n"
    
    # Ensure we have some context
    if not history:
        return prompt + "<|user|>\nHello\n<|assistant|>\nHi! I'm ready to help.\n<|assistant|>\n"
    
    # Build conversation context
    for entry in history:
        if entry.startswith("User:"):
            user_msg = entry[5:].strip()
            if user_msg:
                prompt += f"<|user|>\n{user_msg}\n"
        elif entry.startswith("AI:"):
            ai_msg = entry[3:].strip()
            if ai_msg:
                prompt += f"<|assistant|>\n{ai_msg}\n"
    
    prompt += "<|assistant|>\n"
    return prompt

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

# OPTIMIZATION: Faster token counting with caching
def count_tokens(text: str) -> int:
    """Fast token counting using caching"""
    # Check for common phrases first
    for phrase, tokens in COMMON_PHRASES.items():
        if text.startswith(phrase):
            return len(tokens) + count_tokens(text[len(phrase):])
    
    # Fallback to tokenizer for remaining text
    return len(tokenizer(text)["input_ids"])

# Context-aware history trimming with optimizations
def trim_history(system: str, history: list, max_tokens: int = 3500) -> list:
    """Optimized history trimming"""
    # Calculate system tokens
    system_tokens = count_tokens(f"<|system|>\n{system.strip()}\n")
    total_tokens = system_tokens
    keep_messages = []
    
    # Reserve tokens for new interaction
    reserved_tokens = 500
    
    # Process in chronological order
    for msg in history:
        if msg.startswith("User:"):
            prefix = "User:"
            formatted_msg = f"<|user|>\n{msg[len(prefix):].strip()}\n"
        elif msg.startswith("AI:"):
            prefix = "AI:"
            formatted_msg = f"<|assistant|>\n{msg[len(prefix):].strip()}\n"
        else:
            continue
        
        # Fast token counting
        msg_tokens = count_tokens(formatted_msg)
        
        # Check token budget
        if total_tokens + msg_tokens + reserved_tokens > max_tokens:
            if not keep_messages:
                # If we have no messages, add the most recent one anyway
                keep_messages.append(msg)
            break
            
        total_tokens += msg_tokens
        keep_messages.append(msg)
    
    return keep_messages

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
        user_sessions[session_id] = {
            "system_prompt": scenario.scenario,
            "history": []
        }
    
    response = JSONResponse({"message": "Scenario set!"})
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response

# OPTIMIZED chat endpoint with performance improvements
@app.post("/chat")
async def chat(req: MessageRequest, request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    # Get session ID
    if (session_id := request.cookies.get("session_id")) is None:
        raise HTTPException(400, "Missing session ID")
    
    # Retrieve session
    with session_lock:
        if (session := user_sessions.get(session_id)) is None:
            raise HTTPException(404, "Session not found")
        
        # Add user message to history
        session["history"].append(f"User: {req.message}")
        
        # Trim history with optimizations
        session["history"] = trim_history(
            system=session["system_prompt"],
            history=session["history"],
            max_tokens=3500
        )
        
        # Build prompt
        full_prompt = build_chatml_prompt(
            session["system_prompt"],
            session["history"]
        )
    
    # Tokenize with optimizations
    start_tokenize = time.time()
    inputs = tokenizer(
        full_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=4096,
        padding=True
    ).to(model.device)
    tokenize_time = time.time() - start_tokenize
    
    # Calculate available context
    input_tokens = inputs.input_ids.shape[1]
    max_output_tokens = min(req.max_tokens, 4096 - input_tokens)
    
    # Generation parameters
    generation_params = {
        "max_new_tokens": max_output_tokens,
        "temperature": req.temperature,
        "top_p": req.top_p,
        "do_sample": True,
        "pad_token_id": tokenizer.eos_token_id,
        "eos_token_id": tokenizer.eos_token_id,
        "use_cache": True,
    }
    
    # Speed mode optimizations
    if req.speed_mode:
        generation_params.update({
            "num_beams": 1,
            "repetition_penalty": 1.0,
            "no_repeat_ngram_size": 0,
            "early_stopping": False,
        })
    else:
        generation_params.update({
            "repetition_penalty": 1.1,
            "no_repeat_ngram_size": 3,
            "early_stopping": True,
        })
    
    # Generation with performance monitoring
    generation_start = time.time()
    try:
        with model_lock, torch.no_grad():
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
    
    # Extract and clean response
    response_tokens = output[0][inputs.input_ids.shape[1]:]
    response = tokenizer.decode(response_tokens, skip_special_tokens=True).strip()
    response = clean_response(response)
    
    # Performance logging
    total_time = time.time() - start_tokenize
    tokens_per_sec = max_output_tokens / generation_time if generation_time > 0 else 0
    logger.info(f"⏱️ Tokenize: {tokenize_time:.3f}s | "
                f"Generate: {generation_time:.3f}s | "
                f"Total: {total_time:.3f}s | "
                f"Speed: {tokens_per_sec:.1f} tokens/s")
    
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
    """Test AI generation speed with different parameters"""
    try:
        test_prompts = [
            "Hello, how are you?",
            "What is the weather like today?",
            "Explain quantum computing in simple terms.",
            "Write a short poem about technology."
        ]
        
        results = []
        
        for i, prompt in enumerate(test_prompts):
            logger.info(f"🧪 Speed test {i+1}/4: {prompt}")
            
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
                "speed_mode": {
                    "time": round(speed_time, 2),
                    "response": speed_response.get("response", "")[:100]
                },
                "accuracy_mode": {
                    "time": round(accuracy_time, 2),
                    "response": accuracy_response.get("response", "")[:100]
                },
                "speedup": round(accuracy_time / speed_time, 2) if speed_time > 0 else 0
            })
        
        # Calculate averages
        avg_speed_time = sum(r["speed_mode"]["time"] for r in results) / len(results)
        avg_accuracy_time = sum(r["accuracy_mode"]["time"] for r in results) / len(results)
        avg_speedup = avg_accuracy_time / avg_speed_time if avg_speed_time > 0 else 0
        
        return {
            "test_results": results,
            "summary": {
                "average_speed_mode_time": round(avg_speed_time, 2),
                "average_accuracy_mode_time": round(avg_accuracy_time, 2),
                "average_speedup": round(avg_speedup, 2),
                "recommendation": "Use speed_mode=True for faster responses" if avg_speedup > 1.5 else "Speed mode provides minimal benefit"
            }
        }
        
    except Exception as e:
        logger.error(f"Speed test failed: {e}")
        raise HTTPException(500, f"Speed test failed: {str(e)}")

# Mock request for speed testing
class MockRequest:
    def __init__(self):
        self.cookies = {"session_id": "speed_test_session"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1) 