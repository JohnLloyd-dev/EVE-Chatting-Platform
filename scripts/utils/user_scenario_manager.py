#!/usr/bin/env python3
"""
User & Scenario Management System
Shows how users, scenarios, and AI sessions are managed
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0YzcxNGE4MS05MTE0LTRjMDMtYTMzNi0yOWY4NDExMzAyMzciLCJleHAiOjE3NTM0Mjc4MzN9.7D__xzsD6-A_Gs6yacpCvE9bwZ_v3B0g21fWc0FSbWU"

def get_all_users():
    """Get all users and their scenarios"""
    print("🔍 Fetching all users and their scenarios...")
    
    try:
        # Get conversations (which include user info)
        response = requests.get(
            f"{BASE_URL}/admin/conversations",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )
        
        if response.status_code == 200:
            conversations = response.json()
            print(f"✅ Found {len(conversations)} users with chat sessions")
            
            for conv in conversations:
                print(f"\n👤 User ID: {conv['user_id']}")
                print(f"   📧 Email: {conv.get('user_email', 'Not provided')}")
                print(f"   💬 Session ID: {conv['session_id']}")
                print(f"   📅 Created: {conv['created_at']}")
                print(f"   📊 Messages: {conv['message_count']}")
                print(f"   🔒 Blocked: {conv['user_blocked']}")
                print(f"   ⚡ Active: {conv['is_active']}")
                
                # Get detailed conversation to see scenario
                detail_response = requests.get(
                    f"{BASE_URL}/admin/conversation/{conv['session_id']}",
                    headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
                )
                
                if detail_response.status_code == 200:
                    details = detail_response.json()
                    print(f"   📝 Last Message: {details['messages'][-1]['content'][:100]}..." if details['messages'] else "   📝 No messages")
                
        else:
            print(f"❌ Failed to get users: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def show_user_scenario_mapping(user_id):
    """Show how a specific user's scenario maps to AI model"""
    print(f"\n🔍 Analyzing User Scenario Mapping for: {user_id}")
    
    try:
        # Get user's chat session
        response = requests.get(f"{BASE_URL}/chat/session/{user_id}")
        
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['id']
            
            print(f"✅ Chat Session ID: {session_id}")
            print(f"✅ Created: {session_data['created_at']}")
            print(f"✅ Messages: {len(session_data['messages'])}")
            
            # Get detailed conversation info (includes scenario)
            detail_response = requests.get(
                f"{BASE_URL}/admin/conversation/{session_id}",
                headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
            )
            
            if detail_response.status_code == 200:
                details = detail_response.json()
                
                print(f"\n📋 User Information:")
                print(f"   👤 User ID: {details['user_info']['id']}")
                print(f"   📧 Email: {details['user_info'].get('email', 'Not provided')}")
                print(f"   📅 User Created: {details['user_info']['created_at']}")
                print(f"   🔒 Blocked: {details['user_info']['is_blocked']}")
                
                print(f"\n💬 Session Information:")
                print(f"   🆔 Session ID: {details['session_info']['id']}")
                print(f"   📅 Session Created: {details['session_info']['created_at']}")
                print(f"   🔄 Last Updated: {details['session_info']['updated_at']}")
                print(f"   ⚡ Active: {details['session_info']['is_active']}")
                
                print(f"\n📝 Recent Messages:")
                for msg in details['messages'][-5:]:  # Last 5 messages
                    sender = "👤 User" if msg['is_from_user'] else "🤖 AI"
                    admin_flag = " (Admin)" if msg.get('is_admin_intervention') else ""
                    timestamp = msg['created_at'][:19].replace('T', ' ')
                    content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                    print(f"   {sender}{admin_flag} [{timestamp}]: {content}")
                
        else:
            print(f"❌ Failed to get session: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def simulate_ai_session_creation(scenario_text):
    """Simulate how AI model session is created"""
    print(f"\n🤖 Simulating AI Model Session Creation")
    print("=" * 50)
    
    AI_MODEL_URL = "http://204.12.223.76:8000"
    AUTH = ("adam", "eve2025")
    
    try:
        print(f"📡 Step 1: Setting scenario on AI model...")
        print(f"   URL: {AI_MODEL_URL}/scenario")
        print(f"   Scenario: {scenario_text[:200]}...")
        
        # Set scenario
        response = requests.post(
            f"{AI_MODEL_URL}/scenario",
            json={"scenario": scenario_text},
            auth=AUTH
        )
        
        if response.status_code == 200:
            print(f"✅ Scenario set successfully!")
            
            # Get session cookie
            session_cookie = response.cookies.get("session_id")
            if session_cookie:
                print(f"🍪 AI Session Cookie: {session_cookie}")
                
                # Test chat
                print(f"\n📡 Step 2: Testing chat with AI model...")
                chat_response = requests.post(
                    f"{AI_MODEL_URL}/chat",
                    json={"message": "Hello, introduce yourself", "max_tokens": 100},
                    cookies={"session_id": session_cookie},
                    auth=AUTH
                )
                
                if chat_response.status_code == 200:
                    ai_response = chat_response.json()
                    print(f"✅ AI Response: {ai_response.get('response', 'No response')[:200]}...")
                else:
                    print(f"❌ Chat failed: {chat_response.status_code}")
            else:
                print(f"❌ No session cookie received")
        else:
            print(f"❌ Failed to set scenario: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def create_test_user_with_scenario():
    """Create a test user with custom scenario"""
    print(f"\n🧪 Creating Test User with Custom Scenario")
    print("=" * 50)
    
    # Sample Tally form data
    test_form_data = {
        "eventId": "test_scenario_demo",
        "eventType": "FORM_RESPONSE",
        "createdAt": datetime.now().isoformat(),
        "data": {
            "responseId": f"TEST_SCENARIO_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "submissionId": "test_submission_scenario",
            "respondentId": "test_respondent_scenario",
            "formId": "test_form_scenario",
            "formName": "Scenario Test Form",
            "createdAt": datetime.now().isoformat(),
            "fields": [
                {
                    "key": "question_zMKJN1",
                    "label": "My gender",
                    "type": "MULTIPLE_CHOICE",
                    "value": "Man",
                    "options": [
                        {"id": "man", "text": "Man"},
                        {"id": "woman", "text": "Woman"}
                    ]
                },
                {
                    "key": "question_59dv4M",
                    "label": "Partner gender",
                    "type": "MULTIPLE_CHOICE", 
                    "value": "Police",
                    "options": [
                        {"id": "police", "text": "Police"},
                        {"id": "woman", "text": "Woman"}
                    ]
                },
                {
                    "key": "question_d0YjNz",
                    "label": "Partner age",
                    "type": "MULTIPLE_CHOICE",
                    "value": "25-35",
                    "options": [
                        {"id": "18-25", "text": "18-25"},
                        {"id": "25-35", "text": "25-35"}
                    ]
                }
            ]
        }
    }
    
    try:
        print(f"📡 Sending test form data to Tally webhook...")
        response = requests.post(
            f"{BASE_URL}/webhook/tally",
            json=test_form_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test user created!")
            print(f"   User ID: {result.get('user_id', 'Not provided')}")
            print(f"   Session ID: {result.get('session_id', 'Not provided')}")
            
            if result.get('user_id'):
                # Show the mapping
                show_user_scenario_mapping(result['user_id'])
                
        else:
            print(f"❌ Failed to create test user: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🎯 User & Scenario Management System")
    print("=" * 60)
    
    while True:
        print(f"\n📋 Available Options:")
        print(f"1. 👥 Show all users and their scenarios")
        print(f"2. 🔍 Analyze specific user scenario mapping")
        print(f"3. 🤖 Simulate AI model session creation")
        print(f"4. 🧪 Create test user with scenario")
        print(f"5. 🚪 Exit")
        
        choice = input(f"\n👉 Enter your choice (1-5): ").strip()
        
        if choice == "1":
            get_all_users()
            
        elif choice == "2":
            user_id = input(f"👤 Enter User ID: ").strip()
            if user_id:
                show_user_scenario_mapping(user_id)
            else:
                print("❌ Please provide a valid User ID")
                
        elif choice == "3":
            scenario = input(f"📝 Enter scenario text (or press Enter for default): ").strip()
            if not scenario:
                scenario = "You are a helpful AI assistant named Taylor, a 25-year-old police officer."
            simulate_ai_session_creation(scenario)
            
        elif choice == "4":
            create_test_user_with_scenario()
            
        elif choice == "5":
            print(f"👋 Goodbye!")
            break
            
        else:
            print(f"❌ Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()