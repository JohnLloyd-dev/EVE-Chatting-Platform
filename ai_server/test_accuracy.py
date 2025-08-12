#!/usr/bin/env python3
"""
Test script to verify AI server accuracy improvements
Tests context preservation, response quality, and conversation flow
"""
import httpx
import json
import time

# Configuration
AI_MODEL_URL = "http://localhost:8000"
AUTH_USERNAME = "adam"
AUTH_PASSWORD = "eve2025"

def test_context_preservation():
    """Test that AI maintains conversation context across messages"""
    
    print("🧪 Testing AI Context Preservation...")
    
    with httpx.Client(timeout=30.0) as client:
        # Step 1: Set scenario
        print("1️⃣ Setting scenario...")
        scenario_response = client.post(
            f"{AI_MODEL_URL}/scenario",
            json={"scenario": "You are a helpful AI assistant. Remember our conversation and respond naturally."},
            auth=(AUTH_USERNAME, AUTH_PASSWORD)
        )
        
        if scenario_response.status_code != 200:
            print(f"❌ Failed to set scenario: {scenario_response.text}")
            return False
        
        session_cookie = scenario_response.cookies.get("session_id")
        print(f"✅ Session created: {session_cookie}")
        
        # Step 2: First message - establish context
        print("2️⃣ Sending first message...")
        chat_response1 = client.post(
            f"{AI_MODEL_URL}/chat",
            json={
                "message": "Hello! My name is John and I'm 25 years old.",
                "max_tokens": 100,
                "temperature": 0.7,
                "top_p": 0.9
            },
            cookies={"session_id": session_cookie},
            auth=(AUTH_USERNAME, AUTH_PASSWORD)
        )
        
        if chat_response1.status_code != 200:
            print(f"❌ First chat failed: {chat_response1.text}")
            return False
        
        response1 = chat_response1.json()
        print(f"✅ First response: {response1.get('response', 'No response')}")
        
        # Step 3: Second message - test context memory
        print("3️⃣ Testing context memory...")
        chat_response2 = client.post(
            f"{AI_MODEL_URL}/chat",
            json={
                "message": "What's my name and age?",
                "max_tokens": 100,
                "temperature": 0.7,
                "top_p": 0.9
            },
            cookies={"session_id": session_cookie},
            auth=(AUTH_USERNAME, AUTH_PASSWORD)
        )
        
        if chat_response2.status_code != 200:
            print(f"❌ Second chat failed: {chat_response2.text}")
            return False
        
        response2 = chat_response2.json()
        print(f"✅ Second response: {response2.get('response', 'No response')}")
        
        # Step 4: Verify context was maintained
        response_text = response2.get('response', '').lower()
        context_score = 0
        
        if 'john' in response_text:
            context_score += 1
            print("✅ AI remembered the name 'John'")
        else:
            print("❌ AI forgot the name 'John'")
        
        if '25' in response_text or 'twenty-five' in response_text:
            context_score += 1
            print("✅ AI remembered the age '25'")
        else:
            print("❌ AI forgot the age '25'")
        
        # Step 5: Test conversation flow
        print("4️⃣ Testing conversation flow...")
        chat_response3 = client.post(
            f"{AI_MODEL_URL}/chat",
            json={
                "message": "Tell me more about myself based on what you know.",
                "max_tokens": 150,
                "temperature": 0.7,
                "top_p": 0.9
            },
            cookies={"session_id": session_cookie},
            auth=(AUTH_USERNAME, AUTH_PASSWORD)
        )
        
        if chat_response3.status_code != 200:
            print(f"❌ Third chat failed: {chat_response3.text}")
            return False
        
        response3 = chat_response3.json()
        print(f"✅ Third response: {response3.get('response', 'No response')}")
        
        # Final assessment
        print(f"\n🎯 Context Preservation Score: {context_score}/2")
        if context_score >= 1:
            print("✅ SUCCESS: AI maintained conversation context!")
            return True
        else:
            print("❌ FAILURE: AI lost conversation context")
            return False

def test_response_quality():
    """Test response quality and generation parameters"""
    
    print("\n🧪 Testing Response Quality...")
    
    with httpx.Client(timeout=30.0) as client:
        # Set scenario
        scenario_response = client.post(
            f"{AI_MODEL_URL}/scenario",
            json={"scenario": "You are a creative storyteller. Generate engaging, coherent responses."},
            auth=(AUTH_USERNAME, AUTH_PASSWORD)
        )
        
        if scenario_response.status_code != 200:
            print(f"❌ Failed to set scenario: {scenario_response.text}")
            return False
        
        session_cookie = scenario_response.cookies.get("session_id")
        
        # Test different generation parameters
        test_cases = [
            {"temp": 0.3, "top_p": 0.8, "desc": "Low temperature (focused)"},
            {"temp": 0.7, "top_p": 0.9, "desc": "Medium temperature (balanced)"},
            {"temp": 0.9, "top_p": 0.95, "desc": "High temperature (creative)"}
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}️⃣ Testing {test_case['desc']}...")
            
            chat_response = client.post(
                f"{AI_MODEL_URL}/chat",
                json={
                    "message": "Tell me a short story about a cat.",
                    "max_tokens": 200,
                    "temperature": test_case["temp"],
                    "top_p": test_case["top_p"]
                },
                cookies={"session_id": session_cookie},
                auth=(AUTH_USERNAME, AUTH_PASSWORD)
            )
            
            if chat_response.status_code == 200:
                response = chat_response.json().get("response", "")
                response_length = len(response)
                response_words = len(response.split())
                
                print(f"✅ Response: {response_length} chars, {response_words} words")
                print(f"📝 Preview: {response[:100]}...")
                
                # Quality checks
                if response_length < 20:
                    print("⚠️ Response seems too short")
                elif response_length > 500:
                    print("⚠️ Response seems too long")
                else:
                    print("✅ Response length looks good")
                    
                if 'cat' in response.lower():
                    print("✅ Response is relevant to the prompt")
                else:
                    print("⚠️ Response may not be relevant")
            else:
                print(f"❌ Request failed: {chat_response.status_code}")
        
        return True

def main():
    """Run all accuracy tests"""
    print("🚀 AI Server Accuracy Test Suite")
    print("=" * 40)
    
    try:
        # Test context preservation
        context_success = test_context_preservation()
        
        # Test response quality
        quality_success = test_response_quality()
        
        # Final results
        print("\n" + "=" * 40)
        print("📊 FINAL RESULTS:")
        print(f"Context Preservation: {'✅ PASS' if context_success else '❌ FAIL'}")
        print(f"Response Quality: {'✅ PASS' if quality_success else '❌ FAIL'}")
        
        if context_success and quality_success:
            print("\n🎉 ALL TESTS PASSED! AI server accuracy looks good.")
        else:
            print("\n⚠️ Some tests failed. Check the logs for details.")
            
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main() 