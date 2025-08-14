#!/usr/bin/env python3
"""
Integration Test Suite for AI Server + Backend + Frontend
Tests all communication paths and compatibility
"""
import httpx
import json
import time
import sys

# Configuration
BACKEND_URL = "http://localhost:8001"
AI_SERVER_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

# Test credentials
AUTH_USERNAME = "adam"
AUTH_PASSWORD = "eve2025"

def test_ai_server_health():
    """Test AI server health endpoint"""
    print("🏥 Testing AI Server Health...")
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{AI_SERVER_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ AI Server Healthy: {data}")
                return True
            else:
                print(f"❌ AI Server Health Check Failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ AI Server Health Check Error: {e}")
        return False

def test_backend_health():
    """Test backend health endpoint"""
    print("\n🏥 Testing Backend Health...")
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{BACKEND_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backend Healthy: {data}")
                return True
            else:
                print(f"❌ Backend Health Check Failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Backend Health Check Error: {e}")
        return False

def test_ai_server_authentication():
    """Test AI server authentication"""
    print("\n🔐 Testing AI Server Authentication...")
    
    try:
        with httpx.Client(timeout=10.0) as client:
            # Test without auth (should fail)
            response = client.post(f"{AI_SERVER_URL}/scenario", json={"scenario": "test"})
            if response.status_code == 401:
                print("✅ Authentication required (good)")
            else:
                print(f"⚠️ Unexpected auth response: {response.status_code}")
            
            # Test with auth (should work)
            response = client.post(
                f"{AI_SERVER_URL}/scenario",
                json={"scenario": "You are a helpful AI assistant."},
                auth=(AUTH_USERNAME, AUTH_PASSWORD)
            )
            
            if response.status_code == 200:
                session_cookie = response.cookies.get("session_id")
                print(f"✅ Authentication successful, session: {session_cookie}")
                return session_cookie
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"❌ Authentication Test Error: {e}")
        return None

def test_ai_server_parameter_validation():
    """Test AI server parameter validation"""
    print("\n🔍 Testing AI Server Parameter Validation...")
    
    try:
        with httpx.Client(timeout=10.0) as client:
            # First create a session
            scenario_response = client.post(
                f"{AI_SERVER_URL}/scenario",
                json={"scenario": "You are a helpful AI assistant."},
                auth=(AUTH_USERNAME, AUTH_PASSWORD)
            )
            
            if scenario_response.status_code != 200:
                print(f"❌ Failed to create session: {scenario_response.status_code}")
                return False
            
            session_cookie = scenario_response.cookies.get("session_id")
            
            # Test invalid max_tokens (too low)
            print("  Testing max_tokens < 50...")
            response = client.post(
                f"{AI_SERVER_URL}/chat",
                json={
                    "message": "Hello",
                    "max_tokens": 10,  # Below minimum
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                cookies={"session_id": session_cookie},
                auth=(AUTH_USERNAME, AUTH_PASSWORD)
            )
            
            if response.status_code == 200:
                print("✅ AI server auto-corrected low max_tokens")
            else:
                print(f"⚠️ AI server rejected low max_tokens: {response.status_code}")
            
            # Test valid parameters
            print("  Testing valid parameters...")
            response = client.post(
                f"{AI_SERVER_URL}/chat",
                json={
                    "message": "Hello, how are you?",
                    "max_tokens": 100,
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                cookies={"session_id": session_cookie},
                auth=(AUTH_USERNAME, AUTH_PASSWORD)
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Valid parameters accepted, response: {data.get('response', 'No response')[:100]}...")
                return True
            else:
                print(f"❌ Valid parameters rejected: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Parameter Validation Test Error: {e}")
        return False

def test_backend_ai_integration():
    """Test backend calling AI server"""
    print("\n🔗 Testing Backend-AI Server Integration...")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            # Create a device session through backend
            print("  Creating device session...")
            response = client.post(
                f"{BACKEND_URL}/user/device-session",
                json={
                    "device_id": "integration_test",
                    "custom_prompt": "You are a helpful AI assistant for testing."
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to create device session: {response.status_code}")
                return False
            
            data = response.json()
            session_id = data.get("session_id")
            print(f"✅ Device session created: {session_id}")
            
            # Send a message through backend
            print("  Sending message through backend...")
            response = client.post(
                f"{BACKEND_URL}/chat/message/{session_id}",
                json={
                    "message": "Hello, this is an integration test!",
                    "max_tokens": 150
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to send message: {response.status_code}")
                return False
            
            data = response.json()
            task_id = data.get("task_id")
            print(f"✅ Message sent, task ID: {task_id}")
            
            # Wait for AI response
            print("  Waiting for AI response...")
            for i in range(10):  # Wait up to 10 seconds
                time.sleep(1)
                
                response = client.get(f"{BACKEND_URL}/chat/response/{task_id}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        ai_response = data.get("response", "No response")
                        print(f"✅ AI Response received: {ai_response[:100]}...")
                        return True
                    elif data.get("error"):
                        print(f"❌ AI Response error: {data.get('error')}")
                        return False
                
                print(f"    Waiting... ({i+1}/10)")
            
            print("❌ give me a minute")
            return False
                
    except Exception as e:
        print(f"❌ Backend-AI Integration Test Error: {e}")
        return False

def test_frontend_connectivity():
    """Test frontend connectivity"""
    print("\n🌐 Testing Frontend Connectivity...")
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(FRONTEND_URL)
            
            if response.status_code == 200:
                print("✅ Frontend accessible")
                return True
            else:
                print(f"⚠️ Frontend status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Frontend connectivity error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 AI Server Integration Test Suite")
    print("=" * 50)
    
    test_results = []
    
    # Run all tests
    test_results.append(("AI Server Health", test_ai_server_health()))
    test_results.append(("Backend Health", test_backend_health()))
    test_results.append(("AI Server Auth", test_ai_server_authentication() is not None))
    test_results.append(("Parameter Validation", test_ai_server_parameter_validation()))
    test_results.append(("Backend-AI Integration", test_backend_ai_integration()))
    test_results.append(("Frontend Connectivity", test_frontend_connectivity()))
    
    # Display results
    print("\n" + "=" * 50)
    print("📊 INTEGRATION TEST RESULTS:")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ AI Server is fully compatible with Backend and Frontend")
        return True
    else:
        print(f"\n⚠️ {total - passed} integration tests failed")
        print("❌ There are compatibility issues that need to be resolved")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1) 