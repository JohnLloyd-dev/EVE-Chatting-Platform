#!/usr/bin/env python3
"""
Test script for GGUF model integration
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gguf_model():
    """Test GGUF model loading and basic inference"""
    try:
        # Import the GGUF model manager
        from ai_model_manager_gguf import gguf_model_manager
        
        logger.info("🧪 Testing GGUF model...")
        
        # Check if model is loaded
        if not gguf_model_manager.model_loaded:
            logger.error("❌ GGUF model not loaded")
            return False
        
        logger.info("✅ GGUF model loaded successfully")
        
        # Test basic inference
        test_prompt = "Hello, how are you today?"
        logger.info(f"🧪 Testing with prompt: '{test_prompt}'")
        
        # Create a test session
        session_id = "test_session"
        system_prompt = "You are a helpful AI assistant."
        gguf_model_manager.create_session(session_id, system_prompt)
        
        # Generate response
        response = gguf_model_manager.generate_response(session_id, test_prompt)
        
        logger.info(f"✅ GGUF response: '{response}'")
        logger.info(f"📊 Response length: {len(response)} characters")
        
        # Test health status
        health = gguf_model_manager.get_health_status()
        logger.info(f"📊 Health status: {health}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ GGUF test failed: {str(e)}", exc_info=True)
        return False

def test_model_file_exists():
    """Test if the GGUF model file exists"""
    try:
        from config import settings
        
        model_path = os.path.join(settings.ai_model_cache_dir, settings.ai_model_file)
        logger.info(f"🔍 Checking for model file: {model_path}")
        
        if os.path.exists(model_path):
            file_size = os.path.getsize(model_path) / (1024**3)
            logger.info(f"✅ Model file found: {file_size:.2f}GB")
            return True
        else:
            logger.error(f"❌ Model file not found: {model_path}")
            logger.info("💡 Run ./download_gguf_model.sh to download the model")
            return False
            
    except Exception as e:
        logger.error(f"❌ Model file check failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting GGUF model tests...")
    
    # Test 1: Check if model file exists
    if not test_model_file_exists():
        sys.exit(1)
    
    # Test 2: Test GGUF model loading and inference
    if not test_gguf_model():
        sys.exit(1)
    
    logger.info("🎉 All GGUF tests passed!") 