#!/usr/bin/env python3
"""
Quick AI Model Loading Test
Tests if the AI model can load successfully without the full backend
"""

import os
import sys
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def test_ai_model_loading():
    """Test AI model loading directly"""
    print("🤖 Testing AI Model Loading...")
    print("=" * 50)
    
    # Check CUDA
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU Device: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
        print(f"CUDA Version: {torch.version.cuda}")
    
    # Model configuration
    model_name = "teknium/OpenHermes-2.5-Mistral-7B"
    cache_dir = "/tmp/hf_cache"
    
    print(f"\n📥 Loading model: {model_name}")
    print(f"📁 Cache directory: {cache_dir}")
    
    try:
        # Test tokenizer loading
        print("\n🔤 Loading tokenizer...")
        start_time = time.time()
        
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            local_files_only=False,
            trust_remote_code=True
        )
        
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer_time = time.time() - start_time
        print(f"✅ Tokenizer loaded in {tokenizer_time:.2f}s")
        
        # Test model loading
        print("\n🧠 Loading model...")
        start_time = time.time()
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            low_cpu_mem_usage=True,
            cache_dir=cache_dir,
            local_files_only=False,
            trust_remote_code=True
        )
        
        model_time = time.time() - start_time
        print(f"✅ Model loaded in {model_time:.2f}s")
        
        # Move to GPU if available
        if torch.cuda.is_available():
            print("\n🚀 Moving model to GPU...")
            start_time = time.time()
            
            model = model.cuda()
            
            gpu_time = time.time() - start_time
            print(f"✅ Model moved to GPU in {gpu_time:.2f}s")
            print(f"📊 GPU Memory: {torch.cuda.memory_allocated() / 1024**3:.1f}GB allocated")
        
        # Set to evaluation mode
        model.eval()
        
        # Test simple inference
        print("\n🧪 Testing simple inference...")
        test_text = "Hello, how are you?"
        inputs = tokenizer(test_text, return_tensors="pt")
        
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=20,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"✅ Test inference successful: {response}")
        
        print(f"\n🎉 AI Model Loading Test PASSED!")
        print(f"Total time: {tokenizer_time + model_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"\n❌ AI Model Loading Test FAILED!")
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Provide specific guidance
        if "CUDA" in str(e):
            print("💡 CUDA Error: Check GPU drivers and CUDA installation")
        elif "out of memory" in str(e).lower():
            print("💡 Memory Error: Model too large for GPU memory")
        elif "timeout" in str(e).lower():
            print("💡 Timeout Error: Model download taking too long")
        elif "connection" in str(e).lower():
            print("💡 Connection Error: Check internet connection for model download")
        
        return False

if __name__ == "__main__":
    print("🚀 Starting AI Model Loading Test...")
    print("This will test if the AI model can load successfully")
    print("=" * 60)
    
    success = test_ai_model_loading()
    
    if success:
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1) 