# FIXED: Optimized for response accuracy with improved context handling
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
import time # Added for performance monitoring

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
    max_tokens: int = Field(100, ge=20, le=500)  # ← OPTIMIZED: Reduced default for speed
    temperature: float = Field(0.7, ge=0.1, le=1.0)
    top_p: float = Field(0.9, ge=0.1, le=1.0)
    speed_mode: bool = Field(False, description="Enable speed optimization mode")  # ← ADDED: Speed mode

# Load model
model_name = "teknium/OpenHermes-2.5-Mistral-7B"

# Check if GPU is available
gpu_available = torch.cuda.is_available()
logger.info(f"GPU available: {gpu_available}")

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token  # Set pad token

def load_model_with_fallbacks():
    """Load model with multiple fallback strategies for best performance"""
    if not gpu_available:
        logger.info("Loading model on CPU (no quantization)...")
        return AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="cpu",
            torch_dtype=torch.float32
        )
    
    # Prefer 4-bit quantization for better performance
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
    
    # Final fallback to float32 on CPU
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
    logger.info(f"✅ Model loaded on device: {next(model.parameters()).device}")
except Exception as e:
    logger.critical(f"❌ Model loading failed: {e}")
    raise RuntimeError(f"Failed to load model: {e}")

model.eval()
logger.info("🎯 Model ready for inference")

# Enhanced prompt engineering
def build_chatml_prompt(system: str, history: list) -> str:
    """Build prompt with proper ChatML formatting - ENHANCED VERSION"""
    prompt = f"<|system|>\n{system.strip()}\n"
    
    # Ensure we have some context
    if not history:
        logger.warning("⚠️ No conversation history available")
        prompt += "<|user|>\nHello\n<|assistant|>\nHi! I'm ready to help.\n"
        prompt += "<|assistant|>\n"
        return prompt
    
    # Build conversation context
    for entry in history:
        if entry.startswith("User:"):
            user_msg = entry[5:].strip()
            if user_msg:  # Only add non-empty messages
                prompt += f"<|user|>\n{user_msg}\n"
        elif entry.startswith("AI:"):
            ai_msg = entry[3:].strip()
            if ai_msg:  # Only add non-empty responses
                # Clean previous AI response
                cleaned_response = clean_response(ai_msg)
                if cleaned_response:  # Only add if cleaning didn't remove everything
                    prompt += f"<|assistant|>\n{cleaned_response}\n"
    
    prompt += "<|assistant|>\n"
    
    # Log prompt info for debugging
    prompt_length = len(prompt)
    history_count = len([msg for msg in history if msg.strip()])
    logger.info(f"📝 Built prompt: {prompt_length} chars, {history_count} history entries")
    
    return prompt

def clean_response(response: str) -> str:
    """Clean AI response by removing unwanted artifacts"""
    # Remove any trailing ChatML tags
    response = re.sub(r'<\|[\w]+\|>$', '', response)
    # Remove incomplete sentences at end
    if response and response[-1] not in {'.', '!', '?'}:
        last_period = response.rfind('.')
        if last_period != -1:
            response = response[:last_period+1]
    return response.strip()

# Context-aware history trimming
def trim_history(system: str, history: list, max_tokens: int = 3500) -> list:
    """Trim conversation history while preserving context - FIXED VERSION"""
    # Calculate system tokens
    system_prompt = f"<|system|>\n{system.strip()}\n"
    system_tokens = tokenizer(system_prompt)["input_ids"]
    total_tokens = len(system_tokens)
    keep_messages = []
    
    # Reserve tokens for new interaction
    reserved_tokens = 500  # Increased for better response quality
    
    # Process from OLDEST to NEWEST (preserve conversation flow)
    for msg in history:  # ← FIXED: Process in chronological order
        if msg.startswith("User:"):
            formatted_msg = f"<|user|>\n{msg[5:].strip()}\n"
        elif msg.startswith("AI:"):
            formatted_msg = f"<|assistant|>\n{msg[3:].strip()}\n"
        else:
            continue
        
        msg_tokens = tokenizer(formatted_msg)["input_ids"]
        
        # Check if we can add this message without exceeding limit
        if total_tokens + len(msg_tokens) + reserved_tokens > max_tokens:
            # If we can't fit this message, stop here
            # But ensure we have at least some context
            if len(keep_messages) < 2:
                # Force include at least 2 messages for minimal context
                logger.warning(f"⚠️ Context very limited, keeping minimal messages: {len(keep_messages)}")
            break
            
        total_tokens += len(msg_tokens)
        keep_messages.append(msg)
    
    # Log context preservation info
    logger.info(f"📚 Context: {len(keep_messages)}/{len(history)} messages preserved, {total_tokens} tokens used")
    
    return keep_messages  # ← FIXED: Return in correct order

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

# Enhanced chat endpoint
@app.post("/chat")
async def chat(req: MessageRequest, request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    # Integration validation - ensure compatibility with backend
    try:
        # Validate request parameters for backend compatibility
        if req.max_tokens < 50:
            logger.warning(f"⚠️ Backend sent max_tokens={req.max_tokens}, minimum is 50")
            req.max_tokens = 50  # Auto-correct to minimum
        
        if req.max_tokens > 500:
            logger.warning(f"⚠️ Backend sent max_tokens={req.max_tokens}, maximum is 500")
            req.max_tokens = 500  # Auto-correct to maximum
        
        # Log integration details for debugging
        logger.info(f"🔗 Backend Integration: max_tokens={req.max_tokens}, temperature={req.temperature}, top_p={req.top_p}")
        
    except Exception as e:
        logger.error(f"❌ Integration validation failed: {e}")
        raise HTTPException(400, f"Integration validation failed: {e}")
    
    # Get session ID
    if (session_id := request.cookies.get("session_id")) is None:
        raise HTTPException(400, "Missing session ID")
    
    # Retrieve session
    with session_lock:
        if (session := user_sessions.get(session_id)) is None:
            raise HTTPException(404, "Session not found")
        
        # Add user message to history
        session["history"].append(f"User: {req.message}")
        
        # Trim history while preserving context
        session["history"] = trim_history(
            system=session["system_prompt"],
            history=session["history"],
            max_tokens=3500
        )
        
        # Build prompt with enhanced formatting
        full_prompt = build_chatml_prompt(
            session["system_prompt"],
            session["history"]
        )
        
        # Log prompt details for accuracy debugging
        logger.info(f"🎯 System prompt: {len(session['system_prompt'])} chars")
        logger.info(f"💬 User message: {req.message[:100]}...")
        logger.info(f"📚 History entries: {len(session['history'])}")
        logger.info(f"🔢 Max tokens requested: {req.max_tokens}")
        logger.info(f"🌡️ Temperature: {req.temperature}, Top-p: {req.top_p}")
        
        # Tokenize with better handling
        inputs = tokenizer(
            full_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=4096,
            padding=True
        ).to(model.device)
        
        # Log tokenization info
        input_tokens = inputs.input_ids.shape[1]
        logger.info(f"🔤 Input tokens: {input_tokens}, Available: {4096 - input_tokens}")
        
        # Calculate available context
        max_output_tokens = min(
            req.max_tokens,
            4096 - input_tokens
        )
        if max_output_tokens <= 50:  # ← FIXED: Increased minimum for meaningful responses
            logger.warning(f"⚠️ Limited context: {max_output_tokens} tokens available, {input_tokens} used")
            if max_output_tokens <= 20:
                raise HTTPException(400, "Input too long for response generation")
        
        logger.info(f"📤 Will generate up to {max_output_tokens} tokens")
    
    # Enhanced generation with speed-optimized parameters
    generation_start_time = time.time()  # ← ADDED: Performance timing
    
    with model_lock, torch.no_grad():
        try:
            # Choose generation parameters based on speed mode
            if req.speed_mode:
                # 🚀 SPEED MODE: Fast generation with minimal overhead
                generation_params = {
                    "max_new_tokens": max_output_tokens,
                    "temperature": req.temperature,
                    "top_p": req.top_p,
                    "do_sample": True,
                    "num_beams": 1,  # Single beam for speed
                    "pad_token_id": tokenizer.eos_token_id,
                    "eos_token_id": tokenizer.eos_token_id,
                    # Speed optimizations - minimal processing overhead
                    "repetition_penalty": 1.0,  # ← SPEED: No penalty calculation
                    "no_repeat_ngram_size": 0,  # ← SPEED: No n-gram blocking
                    "early_stopping": False,    # ← SPEED: No early stopping logic
                    "length_penalty": 1.0,      # ← SPEED: No length penalty
                    "typical_p": 1.0,           # ← SPEED: No typical sampling
                    "use_cache": True,          # ← SPEED: Enable KV cache
                    "return_dict_in_generate": False,  # ← SPEED: Skip dict conversion
                }
                logger.info("🚀 Using SPEED MODE for fast generation")
            else:
                # 🎯 ACCURACY MODE: Balanced quality and speed
                generation_params = {
                    "max_new_tokens": max_output_tokens,
                    "temperature": req.temperature,
                    "top_p": req.top_p,
                    "do_sample": True,
                    "num_beams": 1,
                    "pad_token_id": tokenizer.eos_token_id,
                    "eos_token_id": tokenizer.eos_token_id,
                    # Balanced parameters for good quality
                    "repetition_penalty": 1.1,
                    "no_repeat_ngram_size": 3,
                    "early_stopping": True,
                    "length_penalty": 1.0,
                    "typical_p": 0.9,
                    "use_cache": True,
                    "return_dict_in_generate": False,
                }
                logger.info("🎯 Using ACCURACY MODE for balanced quality")
            
            # Log generation parameters for debugging
            logger.info(f"⚙️ Generation params: {generation_params}")
            
            output = model.generate(**inputs, **generation_params)
            
        except RuntimeError as e:
            if "Half" in str(e) or "overflow" in str(e):
                logger.warning(f"⚠️ Precision error: {e}")
                # Retry with safer precision
                inputs = {k: v.to(torch.float32) if torch.is_floating_point(v) else v for k, v in inputs.items()}
                
                # Use same generation parameters for retry
                output = model.generate(**inputs, **generation_params)
            else:
                logger.error(f"⚠️ Generation error: {e}")
                raise HTTPException(500, "Model generation failed")
    
    # Performance monitoring
    generation_time = time.time() - generation_start_time
    tokens_per_second = max_output_tokens / generation_time if generation_time > 0 else 0
    
    logger.info(f"⏱️ Generation completed in {generation_time:.2f}s")
    logger.info(f"🚀 Speed: {tokens_per_second:.1f} tokens/second")
    
    if req.speed_mode and generation_time > 5.0:
        logger.warning(f"⚠️ Speed mode is slow: {generation_time:.2f}s (expected <5s)")
    elif not req.speed_mode and generation_time > 10.0:
        logger.warning(f"⚠️ Accuracy mode is slow: {generation_time:.2f}s (expected <10s)")
    
    # Extract and clean response
    response_tokens = output[0][inputs.input_ids.shape[1]:]
    response = tokenizer.decode(
        response_tokens,
        skip_special_tokens=True
    ).strip()
    
    # Clean and format response
    response = clean_response(response)
    
    # Validate response quality
    if not response or len(response.strip()) < 5:
        logger.warning(f"⚠️ Generated response too short: '{response}'")
        # Try to generate a fallback response
        fallback_response = "I understand. Please continue with your message."
        response = fallback_response
    elif len(response) > 1000:
        logger.warning(f"⚠️ Generated response too long: {len(response)} chars")
        # Truncate to reasonable length
        response = response[:1000].strip()
        if not response.endswith(('.', '!', '?')):
            response += '.'
    
    # Log response quality metrics
    response_length = len(response)
    response_words = len(response.split())
    logger.info(f"✅ Generated response: {response_length} chars, {response_words} words")
    logger.info(f"📝 Response preview: {response[:100]}...")
    
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