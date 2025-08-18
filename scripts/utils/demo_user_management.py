#!/usr/bin/env python3
"""
Demo: User & Scenario Management System
"""
import requests
import json

BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0YzcxNGE4MS05MTE0LTRjMDMtYTMzNi0yOWY4NDExMzAyMzciLCJleHAiOjE3NTM0Mjc4MzN9.7D__xzsD6-A_Gs6yacpCvE9bwZ_v3B0g21fWc0FSbWU"

def demo_user_scenario_system():
    print("🎯 User & Scenario Management Demo")
    print("=" * 50)
    
    # 1. Show current users
    print("\n1️⃣ Current Users in System:")
    try:
        response = requests.get(
            f"{BASE_URL}/admin/conversations",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )
        
        if response.status_code == 200:
            conversations = response.json()
            print(f"   ✅ Found {len(conversations)} users with active sessions")
            
            for i, conv in enumerate(conversations[:3], 1):  # Show first 3
                print(f"\n   👤 User #{i}:")
                print(f"      🆔 User ID: {conv['user_id']}")
                print(f"      📧 Email: {conv.get('user_email', 'Not provided')}")
                print(f"      💬 Session ID: {conv['session_id']}")
                print(f"      📊 Messages: {conv['message_count']}")
                print(f"      🔒 Blocked: {conv['user_blocked']}")
                
        else:
            print(f"   ❌ Failed to get users: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Show scenario mapping for first user
    print(f"\n2️⃣ Scenario Mapping Example:")
    try:
        # Get first user
        user_id = "2de89288-7fc2-4d47-950b-f6a5ea07bb7f"  # Known user
        
        response = requests.get(f"{BASE_URL}/chat/session/{user_id}")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['id']
            
            print(f"   👤 User ID: {user_id}")
            print(f"   💬 Session ID: {session_id}")
            print(f"   📅 Created: {session_data['created_at']}")
            print(f"   📊 Total Messages: {len(session_data['messages'])}")
            
            # Show recent messages
            print(f"\n   📝 Recent Messages:")
            for msg in session_data['messages'][-3:]:
                sender = "👤 User" if msg['is_from_user'] else "🤖 AI"
                content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
                print(f"      {sender}: {content}")
                
        else:
            print(f"   ❌ Failed to get session: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Show AI model integration
    print(f"\n3️⃣ AI Model Integration:")
    AI_MODEL_URL = "http://204.12.223.76:8000"
    AUTH = ("adam", "eve2025")
    
    try:
        print(f"   🤖 AI Model URL: {AI_MODEL_URL}")
        print(f"   🔑 Authentication: {AUTH[0]}/***")
        
        # Test scenario setting
        test_scenario = "You are a helpful AI assistant named Demo."
        response = requests.post(
            f"{AI_MODEL_URL}/scenario",
            json={"scenario": test_scenario},
            auth=AUTH
        )
        
        if response.status_code == 200:
            print(f"   ✅ Scenario setting: Working")
            session_cookie = response.cookies.get("session_id")
            print(f"   🍪 AI Session Cookie: {session_cookie[:20]}..." if session_cookie else "   ❌ No session cookie")
        else:
            print(f"   ❌ Scenario setting failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ AI Model Error: {e}")
    
    # 4. Show data flow
    print(f"\n4️⃣ Data Flow Summary:")
    print(f"   📋 Tally Form → extract_tally.py → Generate Scenario")
    print(f"   👤 Create User → Create ChatSession (with scenario)")
    print(f"   💬 User Message → Celery Worker → AI Model")
    print(f"   🤖 AI Model: Set Scenario → Get Session Cookie → Chat")
    print(f"   💾 AI Response → Save to Database → Return to User")

if __name__ == "__main__":
    demo_user_scenario_system()