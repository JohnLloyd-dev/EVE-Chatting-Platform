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
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    quantization_config=bnb_config
)
model.eval()  # Enable evaluation mode

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
    
    # Generate response
    with torch.no_grad():
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