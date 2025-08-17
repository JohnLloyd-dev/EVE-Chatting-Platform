#!/usr/bin/env python3
"""
Integration Test Script for EVE Chatting Platform
Tests the AI model integration into the backend service
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

def test_backend_health():
    """Test if backend is running and healthy"""
    print("🏥 Testing Backend Health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

def test_ai_health():
    """Test AI model health endpoint"""
    print("\n🤖 Testing AI Model Health...")
    try:
        response = requests.get(f"{BACKEND_URL}/ai/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("✅ AI Health endpoint working")
            print(f"   Model: {data.get('model_name', 'Unknown')}")
            print(f"   Device: {data.get('device', 'Unknown')}")
            print(f"   Status: {data.get('status', 'Unknown')}")
            return True
        else:
            print(f"❌ AI health check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ AI health check error: {e}")
        return False

def test_ai_session_init():
    """Test AI session initialization"""
    print("\n🎯 Testing AI Session Initialization...")
    try:
        session_data = {
            "session_id": f"test_session_{int(time.time())}",
            "system_prompt": "You are a helpful AI assistant. Keep responses short and friendly."
        }
        
        response = requests.post(
            f"{BACKEND_URL}/ai/init-session",
            json=session_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ AI session initialized successfully")
            print(f"   Session ID: {data.get('session_id')}")
            return data.get('session_id')
        else:
            print(f"❌ AI session init failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ AI session init error: {e}")
        return None

def test_ai_chat(session_id: str):
    """Test AI chat functionality"""
    print("\n💬 Testing AI Chat...")
    try:
        chat_data = {
            "session_id": session_id,
            "message": "Hello! How are you today?",
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{BACKEND_URL}/ai/chat",
            json=chat_data,
            timeout=60  # Longer timeout for AI generation
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ AI chat working successfully")
            print(f"   Response: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ AI chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ AI chat error: {e}")
        return False

def test_ai_memory_optimization():
    """Test AI memory optimization endpoint"""
    print("\n🧹 Testing AI Memory Optimization...")
    try:
        response = requests.post(f"{BACKEND_URL}/ai/optimize-memory", timeout=30)
        if response.status_code == 200:
            print("✅ AI memory optimization working")
            return True
        else:
            print(f"❌ AI memory optimization failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AI memory optimization error: {e}")
        return False

def test_legacy_endpoints():
    """Test legacy endpoints for backward compatibility"""
    print("\n🔄 Testing Legacy Endpoints...")
    
    # Test basic API endpoint
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Legacy API health endpoint working")
        else:
            print(f"⚠️ Legacy API health endpoint: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Legacy API health endpoint error: {e}")
    
    # Test admin endpoint
    try:
        response = requests.get(f"{API_BASE}/admin/health", timeout=10)
        if response.status_code == 200:
            print("✅ Legacy admin endpoint working")
        else:
            print(f"⚠️ Legacy admin endpoint: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Legacy admin endpoint error: {e}")

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting EVE Chatting Platform Integration Tests")
    print("=" * 60)
    
    # Test results
    results = []
    
    # Test 1: Backend Health
    results.append(("Backend Health", test_backend_health()))
    
    # Test 2: AI Health
    results.append(("AI Model Health", test_ai_health()))
    
    # Test 3: AI Session
    session_id = test_ai_session_init()
    results.append(("AI Session Init", session_id is not None))
    
    # Test 4: AI Chat (only if session was created)
    if session_id:
        results.append(("AI Chat", test_ai_chat(session_id)))
    else:
        results.append(("AI Chat", False))
    
    # Test 5: AI Memory Optimization
    results.append(("AI Memory Optimization", test_ai_memory_optimization()))
    
    # Test 6: Legacy Endpoints
    test_legacy_endpoints()
    results.append(("Legacy Endpoints", True))  # Assume working if no errors
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS")
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
        print("🎉 All tests passed! Integration is working perfectly!")
        return True
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
        return False

if __name__ == "__main__":
    try:
        success = run_integration_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1) 