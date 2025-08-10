# FIXED: Resolved PyTorch Half precision overflow error by using float32 consistently
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

import secrets
import torch
from uuid import uuid4

app = FastAPI()
security = HTTPBasic()
# Per-user session storage
user_sessions = {}

# Input schemas
class InitScenario(BaseModel):
    scenario: str = Field(..., min_length=1)

class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    max_tokens: int = Field(150, ge=10, le=500)

# Load model
model_name = "teknium/OpenHermes-2.5-Mistral-7B"

# Check if GPU is available
gpu_available = torch.cuda.is_available()
print(f"GPU available: {gpu_available}")

tokenizer = AutoTokenizer.from_pretrained(model_name)

if gpu_available:
    # Use GPU with maximum efficiency for RTX 4060 (8GB VRAM)
    print("Loading model with GPU optimization for RTX 4060 (8GB VRAM)...")
    
    # Set environment variables for optimal GPU performance
    import os
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"
    os.environ["CUDA_LAUNCH_BLOCKING"] = "0"
    os.environ["TORCH_CUDNN_V8_API_ENABLED"] = "1"
    
    # Optimized quantization config for maximum GPU utilization - FIXED for Half precision overflow
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float32,  # Changed from float16 to prevent Half overflow
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_quant_storage=torch.float32   # Changed from float16 to prevent Half overflow
    )
    
    # Optimized device map to use maximum GPU memory efficiently
    device_map = {
        "model.embed_tokens": "cuda:0",  # Keep embeddings on GPU for speed
        "model.norm": "cuda:0",          # Keep normalization on GPU
        "lm_head": "cuda:0",             # Keep output layer on GPU
        "model.layers.0": "cuda:0",
        "model.layers.1": "cuda:0",
        "model.layers.2": "cuda:0",
        "model.layers.3": "cuda:0",
        "model.layers.4": "cuda:0",
        "model.layers.5": "cuda:0",
        "model.layers.6": "cuda:0",
        "model.layers.7": "cuda:0",
        "model.layers.8": "cuda:0",
        "model.layers.9": "cuda:0",
        "model.layers.10": "cuda:0",
        "model.layers.11": "cuda:0",
        "model.layers.12": "cuda:0",
        "model.layers.13": "cuda:0",
        "model.layers.14": "cuda:0",
        "model.layers.15": "cuda:0",
        "model.layers.16": "cuda:0",
        "model.layers.17": "cuda:0",
        "model.layers.18": "cuda:0",
        "model.layers.19": "cuda:0",
        "model.layers.20": "cuda:0",
        "model.layers.21": "cuda:0",
        "model.layers.22": "cuda:0",
        "model.layers.23": "cuda:0",
        "model.layers.24": "cuda:0",
        "model.layers.25": "cuda:0",
        "model.layers.26": "cuda:0",
        "model.layers.27": "cuda:0",
        "model.layers.28": "cuda:0",
        "model.layers.29": "cuda:0",
        "model.layers.30": "cuda:0",
        "model.layers.31": "cuda:0"
    }
    
    # Load model with maximum GPU utilization
    try:
        print("Loading model with full GPU optimization...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map=device_map,
            quantization_config=bnb_config,
            torch_dtype=torch.float32,  # Changed from float16 to prevent Half overflow
            low_cpu_mem_usage=True,
            max_memory={0: "7.5GB", "cpu": "4GB"}  # Use 7.5GB GPU, leave 0.5GB buffer
        )
        print("✅ Model loaded successfully with full GPU optimization!")
        
    except Exception as e:
        print(f"⚠️  Full GPU optimization failed: {e}")
        print("🔄 Trying with balanced GPU/CPU distribution...")
        
        # Fallback to balanced approach
        try:
            balanced_device_map = {
                "model.embed_tokens": "cpu",
                "model.norm": "cpu", 
                "lm_head": "cpu",
                "model.layers.0": "cuda:0",
                "model.layers.1": "cuda:0",
                "model.layers.2": "cuda:0",
                "model.layers.3": "cuda:0",
                "model.layers.4": "cuda:0",
                "model.layers.5": "cuda:0",
                "model.layers.6": "cuda:0",
                "model.layers.7": "cuda:0",
                "model.layers.8": "cuda:0",
                "model.layers.9": "cuda:0",
                "model.layers.10": "cuda:0",
                "model.layers.11": "cuda:0",
                "model.layers.12": "cuda:0",
                "model.layers.13": "cuda:0",
                "model.layers.14": "cuda:0",
                "model.layers.15": "cuda:0",
                "model.layers.16": "cuda:0",
                "model.layers.17": "cuda:0",
                "model.layers.18": "cuda:0",
                "model.layers.19": "cuda:0",
                "model.layers.20": "cuda:0",
                "model.layers.21": "cuda:0",
                "model.layers.22": "cuda:0",
                "model.layers.23": "cuda:0",
                "model.layers.24": "cuda:0",
                "model.layers.25": "cuda:0",
                "model.layers.26": "cuda:0",
                "model.layers.27": "cuda:0",
                "model.layers.28": "cuda:0",
                "model.layers.29": "cuda:0",
                "model.layers.30": "cuda:0",
                "model.layers.31": "cuda:0"
            }
            
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map=balanced_device_map,
                quantization_config=bnb_config,
                torch_dtype=torch.float32,  # Changed from float16 to prevent Half overflow
                low_cpu_mem_usage=True,
                max_memory={0: "6GB", "cpu": "8GB"}
            )
            print("✅ Model loaded with balanced GPU/CPU distribution!")
            
        except Exception as e2:
            print(f"❌ Balanced approach failed: {e2}")
            print("🔄 Falling back to CPU-only mode...")
            # Final fallback to CPU
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="cpu",
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            print("✅ Model loaded on CPU (fallback mode)")
else:
    # Use CPU without quantization
    print("Loading model on CPU (no quantization)...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="cpu",
        torch_dtype=torch.float32
    )

model.eval()  # Enable evaluation mode
print(f"Model loaded on device: {model.device}")

# Helper to build ChatML format prompt
def build_chatml_prompt(system, history):
    prompt = f"<|system|>\n{system.strip()}\n"
    for entry in history:
        if entry.startswith("User:"):
            prompt += f"<|user|>\n{entry[5:].strip()}\n"
        elif entry.startswith("AI:"):
            prompt += f"<|assistant|>\n{entry[3:].strip()}\n"
    prompt += "<|assistant|>\n"
    return prompt

# Token-based history trimming
def trim_history(system: str, history: list, max_tokens: int = 3500) -> list:
    """Trim conversation history to fit within token budget"""
    system_tokens = tokenizer(system)["input_ids"]
    total_tokens = len(system_tokens)
    keep_messages = []
    
    # Process from newest to oldest
    for msg in reversed(history):
        msg_tokens = tokenizer(msg)["input_ids"]
        if total_tokens + len(msg_tokens) > max_tokens:
            break
        total_tokens += len(msg_tokens)
        keep_messages.append(msg)
    
    # Return kept messages in chronological order
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
    
    user_sessions[session_id] = {
        "system_prompt": scenario.scenario,
        "history": []
    }
    #print("scenario", scenario.scenario)
    response = JSONResponse({"message": "Scenario set!"})
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response

# Chat endpoint
@app.post("/chat")
async def chat(req: MessageRequest, request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    # Get session ID from cookies
    if (session_id := request.cookies.get("session_id")) is None:
        raise HTTPException(400, "Missing session ID")
    
    # Retrieve session data
    if (session := user_sessions.get(session_id)) is None:
        raise HTTPException(404, "Session not found")
    
    # Add user message to history
    session["history"].append(f"User: {req.message}")
    
    # Trim history to fit context window
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
    print('prompt'+full_prompt)
    # Tokenize with truncation
    inputs = tokenizer(
        full_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=4096
    ).to(model.device)
    
    # Adjust max tokens to available space
    max_output_tokens = min(
        req.max_tokens,
        4096 - inputs.input_ids.shape[1]
    )
    if max_output_tokens <= 0:
        raise HTTPException(400, "Input too long for response generation")
    
    # Generate response - FIXED with error handling for Half precision overflow
    with torch.no_grad():
        try:
            output = model.generate(
                **inputs,
                max_new_tokens=max_output_tokens,
                temperature=0.8,
                do_sample=True,
                top_p=0.95,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                repetition_penalty=1.2,
                no_repeat_ngram_size=3
            )
        except RuntimeError as e:
            if "at::Half" in str(e) or "Half" in str(e):
                print(f"⚠️  Half precision error detected: {e}")
                print("🔄 Retrying with explicit float32 conversion...")
                # Convert inputs to float32 and retry
                inputs = {k: v.to(torch.float32) if torch.is_tensor(v) else v for k, v in inputs.items()}
                output = model.generate(
                    **inputs,
                    max_new_tokens=max_output_tokens,
                    temperature=0.8,
                    do_sample=True,
                    top_p=0.95,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=3
                )
            else:
                raise e
    
    # Extract only new tokens
    response_tokens = output[0][inputs.input_ids.shape[1]:]
    response = tokenizer.decode(
        response_tokens,
        skip_special_tokens=True
    ).strip()
    
    # Save AI response to history
    session["history"].append(f"AI: {response}")
    return {"response": response}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": model_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 