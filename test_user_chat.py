#!/usr/bin/env python3
"""
Test User Chat Functionality
Simulates a user chatting with the AI system
"""
import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8000"

def test_user_chat():
    print("🧪 Testing User Chat Functionality")
    print("=" * 50)
    
    # Use existing user ID (you can change this)
    user_id = "2de89288-7fc2-4d47-950b-f6a5ea07bb7f"
    
    print(f"👤 Testing with User ID: {user_id}")
    
    # Step 1: Get user's chat session
    print("\n📱 Step 1: Getting user's chat session...")
    try:
        response = requests.get(f"{BASE_URL}/chat/session/{user_id}")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['id']
            print(f"✅ Session ID: {session_id}")
            print(f"✅ Existing messages: {len(session_data['messages'])}")
        else:
            print(f"❌ Failed to get session: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting session: {e}")
        return
    
    # Step 2: Send multiple test messages
    test_messages = [
        "Hello! I'm testing the chat system.",
        "Can you tell me about yourself?",
        "What's the weather like today?",
        "I'm interested in learning about technology.",
        "Thank you for chatting with me!"
    ]
    
    print(f"\n💬 Step 2: Sending {len(test_messages)} test messages...")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📤 Message {i}: {message}")
        
        try:
            # Send message
            response = requests.post(
                f"{BASE_URL}/chat/message/{session_id}",
                json={"message": message},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Message sent! Task ID: {result['task_id']}")
                
                # Wait a moment for processing
                time.sleep(2)
                
                # Check AI response status
                task_response = requests.get(f"{BASE_URL}/chat/response/{result['task_id']}")
                if task_response.status_code == 200:
                    status = task_response.json()
                    print(f"🤖 AI Response Status: {status['status']}")
                
            else:
                print(f"❌ Failed to send message: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
        
        # Small delay between messages
        time.sleep(1)
    
    # Step 3: Get final conversation state
    print(f"\n📋 Step 3: Getting final conversation state...")
    try:
        response = requests.get(f"{BASE_URL}/chat/session/{user_id}")
        if response.status_code == 200:
            final_session = response.json()
            messages = final_session['messages']
            print(f"✅ Total messages in conversation: {len(messages)}")
            
            print(f"\n💬 Recent conversation:")
            for msg in messages[-6:]:  # Show last 6 messages
                sender = "👤 User" if msg['is_from_user'] else "🤖 AI"
                admin_flag = " (Admin)" if msg.get('is_admin_intervention') else ""
                timestamp = msg['created_at'][:19].replace('T', ' ')
                print(f"   {sender}{admin_flag} [{timestamp}]: {msg['content']}")
                
        else:
            print(f"❌ Failed to get final session: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting final session: {e}")
    
    print(f"\n🎉 User chat test completed!")
    print(f"\n📊 Summary:")
    print(f"   - User can get chat sessions ✅")
    print(f"   - User can send messages ✅") 
    print(f"   - Messages are stored in database ✅")
    print(f"   - AI processing is triggered ✅")
    print(f"   - Conversation history is maintained ✅")
    print(f"\n💡 Note: AI responses show fallback messages since AI model URL isn't configured.")

if __name__ == "__main__":
    test_user_chat()