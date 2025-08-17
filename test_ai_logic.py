#!/usr/bin/env python3
"""
AI Logic Verification Test
Tests the complete AI integration flow to identify any issues
"""

import sys
import os
import time
from typing import Dict, Any

# Add backend to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_ai_model_manager_import():
    """Test if AI model manager can be imported"""
    print("🔍 Testing AI Model Manager Import...")
    try:
        from ai_model_manager import ai_model_manager
        print("✅ AI Model Manager imported successfully")
        return True
    except Exception as e:
        print(f"❌ AI Model Manager import failed: {e}")
        return False

def test_ai_model_manager_structure():
    """Test AI model manager class structure"""
    print("\n🔍 Testing AI Model Manager Structure...")
    try:
        from ai_model_manager import AIModelManager
        
        # Check if class exists
        if not hasattr(AIModelManager, '__init__'):
            print("❌ AIModelManager missing __init__ method")
            return False
        
        # Check required methods
        required_methods = [
            'create_session',
            'get_session', 
            'add_user_message',
            'add_assistant_message',
            'build_chatml_prompt',
            'generate_response',
            'optimize_memory_usage',
            'get_health_status'
        ]
        
        for method in required_methods:
            if not hasattr(AIModelManager, method):
                print(f"❌ AIModelManager missing {method} method")
                return False
        
        print("✅ AI Model Manager structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ AI Model Manager structure test failed: {e}")
        return False

def test_chatml_prompt_building():
    """Test ChatML prompt building logic"""
    print("\n🔍 Testing ChatML Prompt Building...")
    try:
        from ai_model_manager import AIModelManager
        
        # Create instance (without loading model)
        manager = AIModelManager.__new__(AIModelManager)
        manager.user_sessions = {}
        
        # Test prompt building
        system_prompt = "You are a helpful assistant."
        history = ["Hello", "Hi there!", "How are you?"]
        message_roles = ["user", "assistant", "user"]
        
        prompt = manager.build_chatml_prompt(system_prompt, history, message_roles)
        
        # Verify prompt structure
        expected_parts = [
            "<|im_start|>system",
            "You are a helpful assistant.",
            "<|im_end|>",
            "<|im_start|>user",
            "Hello",
            "<|im_end|>",
            "<|im_start|>assistant", 
            "Hi there!",
            "<|im_end|>",
            "<|im_start|>user",
            "How are you?",
            "<|im_end|>",
            "<|im_start|>assistant"
        ]
        
        for part in expected_parts:
            if part not in prompt:
                print(f"❌ Missing expected part in prompt: {part}")
                return False
        
        print("✅ ChatML prompt building works correctly")
        print(f"   Prompt length: {len(prompt)} characters")
        print(f"   Prompt preview: {prompt[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ ChatML prompt building test failed: {e}")
        return False

def test_session_management():
    """Test session management logic"""
    print("\n🔍 Testing Session Management...")
    try:
        from ai_model_manager import AIModelManager
        
        # Create instance (without loading model)
        manager = AIModelManager.__new__(AIModelManager)
        manager.user_sessions = {}
        
        # Test session creation
        session_id = "test_session_123"
        system_prompt = "You are a helpful assistant."
        
        session = manager.create_session(session_id, system_prompt)
        
        # Verify session structure
        required_keys = ['system_prompt', 'history', 'message_roles', 'created_at', 'last_updated']
        for key in required_keys:
            if key not in session:
                print(f"❌ Session missing key: {key}")
                return False
        
        # Verify session data
        if session['system_prompt'] != system_prompt:
            print(f"❌ Session system_prompt mismatch: {session['system_prompt']} != {system_prompt}")
            return False
        
        if len(session['history']) != 0:
            print(f"❌ New session should have empty history: {len(session['history'])}")
            return False
        
        if len(session['message_roles']) != 0:
            print(f"❌ New session should have empty message_roles: {len(session['message_roles'])}")
            return False
        
        # Test message addition
        manager.add_user_message(session_id, "Hello")
        manager.add_assistant_message(session_id, "Hi there!")
        
        # Verify messages were added
        session = manager.get_session(session_id)
        if len(session['history']) != 2:
            print(f"❌ Expected 2 messages, got {len(session['history'])}")
            return False
        
        if session['history'][0] != "Hello":
            print(f"❌ First message mismatch: {session['history'][0]}")
            return False
        
        if session['history'][1] != "Hi there!":
            print(f"❌ Second message mismatch: {session['history'][1]}")
            return False
        
        if session['message_roles'] != ["user", "assistant"]:
            print(f"❌ Message roles mismatch: {session['message_roles']}")
            return False
        
        print("✅ Session management works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Session management test failed: {e}")
        return False

def test_backend_ai_endpoints():
    """Test backend AI endpoint definitions"""
    print("\n🔍 Testing Backend AI Endpoints...")
    try:
        # Read main.py to check endpoint definitions
        with open('backend/main.py', 'r') as f:
            content = f.read()
        
        # Check for required endpoints
        required_endpoints = [
            '@app.post("/ai/init-session")',
            '@app.post("/ai/chat")',
            '@app.get("/ai/health")',
            '@app.post("/ai/optimize-memory")'
        ]
        
        for endpoint in required_endpoints:
            if endpoint not in content:
                print(f"❌ Missing endpoint: {endpoint}")
                return False
        
        # Check for AI model manager usage
        if 'ai_model_manager.create_session' not in content:
            print("❌ Missing ai_model_manager.create_session usage")
            return False
        
        if 'ai_model_manager.generate_response' not in content:
            print("❌ Missing ai_model_manager.generate_response usage")
            return False
        
        if 'ai_model_manager.get_health_status' not in content:
            print("❌ Missing ai_model_manager.get_health_status usage")
            return False
        
        print("✅ Backend AI endpoints are properly defined")
        return True
        
    except Exception as e:
        print(f"❌ Backend AI endpoints test failed: {e}")
        return False

def test_schema_compatibility():
    """Test schema compatibility with AI endpoints"""
    print("\n🔍 Testing Schema Compatibility...")
    try:
        from schemas import ChatMessageRequest
        
        # Check if ChatMessageRequest has required fields
        required_fields = ['session_id', 'message', 'max_tokens', 'temperature']
        
        # Get field names from the class (Pydantic v2 compatible)
        field_names = list(ChatMessageRequest.model_fields.keys())
        
        for field in required_fields:
            if field not in field_names:
                print(f"❌ ChatMessageRequest missing field: {field}")
                return False
        
        print("✅ Schema compatibility is correct")
        print(f"   Available fields: {field_names}")
        return True
        
    except Exception as e:
        print(f"❌ Schema compatibility test failed: {e}")
        return False

def test_frontend_api_integration():
    """Test frontend API integration"""
    print("\n🔍 Testing Frontend API Integration...")
    try:
        # Read api.ts to check AI endpoint usage
        with open('frontend/lib/api.ts', 'r') as f:
            content = f.read()
        
        # Check for required API functions
        required_functions = [
            'initAISession:',
            'sendMessage:',
            'getAIHealth:'
        ]
        
        for func in required_functions:
            if func not in content:
                print(f"❌ Missing API function: {func}")
                return False
        
        # Check for AI endpoint calls
        required_endpoints = [
            '"/ai/init-session"',
            '"/ai/chat"',
            '"/ai/health"'
        ]
        
        for endpoint in required_endpoints:
            if endpoint not in content:
                print(f"❌ Missing API endpoint: {endpoint}")
                return False
        
        print("✅ Frontend API integration is correct")
        return True
        
    except Exception as e:
        print(f"❌ Frontend API integration test failed: {e}")
        return False

def run_ai_logic_tests():
    """Run all AI logic tests"""
    print("🚀 Starting AI Logic Verification Tests")
    print("=" * 60)
    
    tests = [
        ("AI Model Manager Import", test_ai_model_manager_import),
        ("AI Model Manager Structure", test_ai_model_manager_structure),
        ("ChatML Prompt Building", test_chatml_prompt_building),
        ("Session Management", test_session_management),
        ("Backend AI Endpoints", test_backend_ai_endpoints),
        ("Schema Compatibility", test_schema_compatibility),
        ("Frontend API Integration", test_frontend_api_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 AI LOGIC TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All AI logic tests passed! The integration is solid!")
        return True
    else:
        print("⚠️ Some AI logic tests failed. Check the details above.")
        return False

if __name__ == "__main__":
    try:
        success = run_ai_logic_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1) 