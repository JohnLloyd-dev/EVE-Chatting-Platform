# FIXED: Resolved PyTorch Half precision overflow error by using proper data type handling
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

import secrets
import torch
from uuid import uuid4
import os
from typing import Dict, List, Optional
import json
import logging

# Check if accelerate is available
try:
    import accelerate
    ACCELERATE_AVAILABLE = True
    print("✅ Accelerate library available")
except ImportError:
    ACCELERATE_AVAILABLE = False
    print("⚠️  Accelerate library not available - some strategies will be skipped")

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

def load_model_with_fallbacks():
    """Load model with multiple fallback strategies to handle Half precision overflow"""
    if not gpu_available:
        print("Loading model on CPU (no quantization)...")
        return AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="cpu",
            torch_dtype=torch.float32
        )
    
    # Strategy 1: Simple GPU loading without device_map (no accelerate required)
    try:
        print("🔄 Strategy 1: Loading directly to GPU (no device_map)...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
        model = model.to("cuda:0")
        print("✅ Strategy 1 successful: Direct GPU loading")
        return model
    except Exception as e:
        print(f"❌ Strategy 1 failed: {e}")
    
    # Strategy 2: Try with auto device mapping and no quantization (only if accelerate available)
    if ACCELERATE_AVAILABLE:
        try:
            print("🔄 Strategy 2: Loading with auto device mapping (no quantization)...")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
                max_memory={0: "7.5GB", "cpu": "4GB"}
            )
            print("✅ Strategy 2 successful: Auto device mapping")
            return model
        except Exception as e:
            print(f"❌ Strategy 2 failed: {e}")
    else:
        print("⏭️  Strategy 2 skipped: accelerate not available")
    
    # Strategy 3: 8-bit quantization (more stable than 4-bit) - only if accelerate available
    if ACCELERATE_AVAILABLE:
        try:
            print("🔄 Strategy 3: Loading with 8-bit quantization...")
            bnb_config_8bit = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0
            )
            
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                quantization_config=bnb_config_8bit,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
                max_memory={0: "7.5GB", "cpu": "4GB"}
            )
            print("✅ Strategy 3 successful: 8-bit quantization")
            return model
        except Exception as e:
            print(f"❌ Strategy 3 failed: {e}")
    else:
        print("⏭️  Strategy 3 skipped: accelerate not available")
    
    # Strategy 4: 4-bit quantization with conservative settings
    try:
        print("🔄 Strategy 4: Loading with 4-bit quantization (conservative)...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="cpu",
            quantization_config=bnb_config,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
        model = model.to("cuda:0")
        print("✅ Strategy 4 successful: 4-bit quantization")
        return model
    except Exception as e:
        print(f"❌ Strategy 4 failed: {e}")
    
    # Strategy 5: Manual device mapping with mixed precision (only if accelerate available)
    if ACCELERATE_AVAILABLE:
        try:
            print("🔄 Strategy 5: Loading with manual device mapping...")
            device_map = {
                "model.embed_tokens": "cuda:0",
                "model.norm": "cuda:0",
                "lm_head": "cuda:0"
            }
            # Add layers with GPU allocation
            for i in range(32):
                device_map[f"model.layers.{i}"] = "cuda:0"
            
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map=device_map,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
                max_memory={0: "7.5GB", "cpu": "4GB"}
            )
            print("✅ Strategy 5 successful: Manual device mapping")
            return model
        except Exception as e:
            print(f"❌ Strategy 5 failed: {e}")
    else:
        print("⏭️  Strategy 5 skipped: accelerate not available")
    
    # Strategy 6: CPU fallback
    print("🔄 Strategy 6: Falling back to CPU...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="cpu",
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True
    )
    print("✅ Strategy 6 successful: CPU fallback")
    return model

# Load the model using the fallback strategy
print("🚀 Starting model loading process...")
print(f"Model: {model_name}")
print(f"GPU available: {gpu_available}")
if gpu_available:
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

try:
    model = load_model_with_fallbacks()
    print(f"✅ Model loaded successfully on device: {next(model.parameters()).device}")
except Exception as e:
    print(f"❌ All model loading strategies failed: {e}")
    print("🔄 Attempting emergency CPU fallback...")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="cpu",
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )
        print("✅ Emergency CPU fallback successful")
    except Exception as e2:
        print(f"❌ Emergency fallback also failed: {e2}")
        raise RuntimeError(f"Failed to load model: {e2}")

model.eval()  # Enable evaluation mode
print(f"🎯 Model ready for inference on device: {next(model.parameters()).device}")

# FIXED: Add function to check and fix potential data type issues
def check_and_fix_model_dtypes():
    """Check and fix potential data type issues in the model"""
    print("🔍 Checking model data types...")
    try:
        # Check if model has any problematic dtypes
        for name, param in model.named_parameters():
            if param.dtype == torch.float16:
                # Check if parameter has any NaN or inf values
                if torch.isnan(param).any() or torch.isinf(param).any():
                    print(f"⚠️  Found NaN/inf in {name}, converting to float32")
                    param.data = param.data.to(torch.float32)
        
        # Check model's compute dtype
        if hasattr(model, 'config') and hasattr(model.config, 'torch_dtype'):
            print(f"Model config torch_dtype: {model.config.torch_dtype}")
        
        print("✅ Model data type check completed")
    except Exception as e:
        print(f"⚠️  Data type check failed: {e}")

# Run the data type check
check_and_fix_model_dtypes()

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
            if "at::Half" in str(e) or "Half" in str(e) or "overflow" in str(e):
                print(f"⚠️  Half precision error detected: {e}")
                print("🔄 Retrying with explicit float32 conversion...")
                try:
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
                except Exception as e2:
                    print(f"⚠️  Float32 conversion failed: {e2}")
                    print("🔄 Trying with CPU fallback...")
                    # Move model to CPU temporarily for this generation
                    original_device = next(model.parameters()).device
                    model.to("cpu")
                    inputs = {k: v.to("cpu") if torch.is_tensor(v) else v for k, v in inputs.items()}
                    
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
                    
                    # Move model back to original device
                    model.to(original_device)
                    print("✅ CPU fallback successful")
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