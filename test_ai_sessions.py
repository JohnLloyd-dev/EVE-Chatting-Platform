#!/usr/bin/env python3
"""
Test script to debug AI server sessions and see why the Tally scenario is missing
"""

import httpx
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AI server configuration
AI_SERVER_URL = os.getenv("AI_MODEL_URL", "http://localhost:8001")
AI_USERNAME = os.getenv("AI_MODEL_AUTH_USERNAME", "admin")
AI_PASSWORD = os.getenv("AI_MODEL_AUTH_PASSWORD", "admin123")

def test_ai_sessions():
    """Test AI server sessions to see what's stored"""
    
    print("🔍 Testing AI Server Sessions...")
    print(f"AI Server URL: {AI_SERVER_URL}")
    print(f"Username: {AI_USERNAME}")
    print()
    
    try:
        with httpx.Client(timeout=10.0) as client:
            # Test 1: Check AI server health
            print("1️⃣ Testing AI server health...")
            health_response = client.get(
                f"{AI_SERVER_URL}/health",
                auth=(AI_USERNAME, AI_PASSWORD)
            )
            
            if health_response.status_code == 200:
                print("✅ AI server is healthy")
            else:
                print(f"❌ AI server health check failed: {health_response.status_code}")
                return
            
            print()
            
            # Test 2: List all active sessions
            print("2️⃣ Listing all active sessions...")
            sessions_response = client.get(
                f"{AI_SERVER_URL}/debug-sessions",
                auth=(AI_USERNAME, AI_PASSWORD)
            )
            
            if sessions_response.status_code == 200:
                sessions_data = sessions_response.json()
                print(f"📊 Total sessions: {sessions_data.get('total_sessions', 0)}")
                
                if sessions_data.get('sessions'):
                    print("\n📋 Active Sessions:")
                    for session_id, session_info in sessions_data['sessions'].items():
                        print(f"\n🆔 Session ID: {session_id}")
                        print(f"   📝 System prompt length: {session_info['system_prompt_length']} chars")
                        print(f"   📚 History length: {session_info['history_length']} messages")
                        print(f"   🎯 Has Tally scenario: {session_info['has_tally_scenario']}")
                        print(f"   📖 Preview: {session_info['system_prompt_preview']}")
                else:
                    print("❌ No active sessions found")
            else:
                print(f"❌ Failed to get sessions: {sessions_response.status_code}")
                print(f"Response: {sessions_response.text}")
            
            print()
            
            # Test 3: Try to find the specific session from backend logs
            print("3️⃣ Looking for specific session from backend logs...")
            target_session_id = "a95ddda9-4d29-4bd8-8b6f-8d4df8a9beb1"
            
            debug_response = client.get(
                f"{AI_SERVER_URL}/debug-session/{target_session_id}",
                auth=(AI_USERNAME, AI_PASSWORD)
            )
            
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                print(f"✅ Found session {target_session_id}")
                print(f"   📝 System prompt length: {debug_data.get('system_prompt_length', 0)} chars")
                print(f"   🎯 Has Tally scenario: {'**Scenario**:' in debug_data.get('system_prompt', '')}")
                print(f"   📖 System prompt preview: {debug_data.get('system_prompt', '')[:300]}...")
            else:
                print(f"❌ Session {target_session_id} not found: {debug_response.status_code}")
                if debug_response.status_code == 404:
                    print("   This explains why the AI server shows the wrong system prompt!")
                    print("   The session was created but not found during chat requests.")
            
    except Exception as e:
        print(f"❌ Error testing AI server: {e}")

if __name__ == "__main__":
    test_ai_sessions() 