#!/usr/bin/env python3
"""
Test script to verify AI session reuse fix
"""
import httpx
import json
import time

# Configuration
AI_MODEL_URL = "http://localhost:8000"  # Adjust if different
AUTH_USERNAME = "adam"
AUTH_PASSWORD = "eve2025"

def test_ai_session_reuse():
    """Test that AI sessions are reused instead of creating new ones"""
    
    print("🧪 Testing AI session reuse...")
    
    with httpx.Client(timeout=30.0) as client:
        # Step 1: Set initial scenario
        print("1️⃣ Setting initial scenario...")
        scenario_response = client.post(
            f"{AI_MODEL_URL}/scenario",
            json={"scenario": "You are a helpful AI assistant. Keep responses short."},
            auth=(AUTH_USERNAME, AUTH_PASSWORD)
        )
        
        if scenario_response.status_code != 200:
            print(f"❌ Failed to set scenario: {scenario_response.text}")
            return
        
        # Get session cookie
        session_cookie = scenario_response.cookies.get("session_id")
        if not session_cookie:
            print("❌ No session ID received")
            return
        
        print(f"✅ Created session: {session_cookie}")
        
        # Step 2: Send first message
        print("2️⃣ Sending first message...")
        chat_response1 = client.post(
            f"{AI_MODEL_URL}/chat",
            json={"message": "Hello", "max_tokens": 50},
            cookies={"session_id": session_cookie},
            auth=(AUTH_USERNAME, AUTH_PASSWORD)
        )
        
        if chat_response1.status_code != 200:
            print(f"❌ First chat failed: {chat_response1.text}")
            return
        
        response1 = chat_response1.json()
        print(f"✅ First response: {response1.get('response', 'No response')}")
        
        # Step 3: Send second message (should reuse same session)
        print("3️⃣ Sending second message (should reuse session)...")
        chat_response2 = client.post(
            f"{AI_MODEL_URL}/chat",
            json={"message": "What did I just say?", "max_tokens": 50},
            cookies={"session_id": session_cookie},
            auth=(AUTH_USERNAME, AUTH_PASSWORD)
        )
        
        if chat_response2.status_code != 200:
            print(f"❌ Second chat failed: {chat_response2.text}")
            return
        
        response2 = chat_response2.json()
        print(f"✅ Second response: {response2.get('response', 'No response')}")
        
        # Step 4: Check if responses are different (indicating context is maintained)
        if response1.get('response') != response2.get('response'):
            print("✅ SUCCESS: AI maintained context between messages!")
        else:
            print("⚠️  WARNING: AI responses are identical - context may not be maintained")
        
        print(f"🎯 Final session ID: {session_cookie}")

if __name__ == "__main__":
    try:
        test_ai_session_reuse()
    except Exception as e:
        print(f"❌ Test failed: {e}") 