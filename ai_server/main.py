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
    max_tokens: int = Field(200, ge=50, le=500)  # Increased min tokens for better responses
    temperature: float = Field(0.7, ge=0.1, le=1.0)  # Added temperature control
    top_p: float = Field(0.9, ge=0.1, le=1.0)  # Added top-p sampling

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
    """Build prompt with proper ChatML formatting"""
    prompt = f"<|system|>\n{system.strip()}\n"
    
    for entry in history:
        if entry.startswith("User:"):
            prompt += f"<|user|>\n{entry[5:].strip()}\n"
        elif entry.startswith("AI:"):
            # Clean previous AI response
            cleaned_response = clean_response(entry[3:].strip())
            prompt += f"<|assistant|>\n{cleaned_response}\n"
    
    prompt += "<|assistant|>\n"
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
    """Trim conversation history while preserving context"""
    # Calculate system tokens
    system_prompt = f"<|system|>\n{system.strip()}\n"
    system_tokens = tokenizer(system_prompt)["input_ids"]
    total_tokens = len(system_tokens)
    keep_messages = []
    
    # Reserve tokens for new interaction
    reserved_tokens = 300  # For new user message + AI response prefix
    
    # Process from newest to oldest (keep most recent interactions)
    for msg in reversed(history):
        if msg.startswith("User:"):
            formatted_msg = f"<|user|>\n{msg[5:].strip()}\n"
        elif msg.startswith("AI:"):
            formatted_msg = f"<|assistant|>\n{msg[3:].strip()}\n"
        else:
            continue
        
        msg_tokens = tokenizer(formatted_msg)["input_ids"]
        
        # Check if we can add this message without exceeding limit
        if total_tokens + len(msg_tokens) + reserved_tokens > max_tokens:
            break
            
        total_tokens += len(msg_tokens)
        keep_messages.append(msg)
    
    # Return in chronological order
    return list(reversed(keep_messages))

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
    
    # Tokenize with better handling
    inputs = tokenizer(
        full_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=4096,
        padding=True
    ).to(model.device)
    
    # Calculate available context
    max_output_tokens = min(
        req.max_tokens,
        4096 - inputs.input_ids.shape[1]
    )
    if max_output_tokens <= 10:
        # Preserve at least 10 tokens for meaningful response
        raise HTTPException(400, "Input too long for response generation")
    
    # Enhanced generation with optimized parameters
    with model_lock, torch.no_grad():
        try:
            output = model.generate(
                **inputs,
                max_new_tokens=max_output_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                do_sample=True,
                num_beams=1,  # Disable beam search for more natural responses
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                repetition_penalty=1.15,  # Slightly reduced repetition penalty
                no_repeat_ngram_size=4,  # Slightly larger n-gram blocking
                early_stopping=True
            )
        except RuntimeError as e:
            if "Half" in str(e) or "overflow" in str(e):
                logger.warning(f"⚠️ Precision error: {e}")
                # Retry with safer precision
                inputs = {k: v.to(torch.float32) if torch.is_floating_point(v) else v for k, v in inputs.items()}
                output = model.generate(
                    **inputs,
                    max_new_tokens=max_output_tokens,
                    temperature=req.temperature,
                    top_p=req.top_p,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.15,
                    no_repeat_ngram_size=4,
                    early_stopping=True
                )
            else:
                logger.error(f"⚠️ Generation error: {e}")
                raise HTTPException(500, "Model generation failed")
    
    # Extract and clean response
    response_tokens = output[0][inputs.input_ids.shape[1]:]
    response = tokenizer.decode(
        response_tokens,
        skip_special_tokens=True
    ).strip()
    
    # Clean and format response
    response = clean_response(response)
    
    # Save to history
    with session_lock:
        if session_id in user_sessions:
            session["history"].append(f"AI: {response}")
    
    return {"response": response}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": model_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1) 