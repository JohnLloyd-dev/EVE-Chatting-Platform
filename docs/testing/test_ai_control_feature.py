#!/usr/bin/env python3
"""
Test script to verify AI response control feature is working
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8001"  # Adjust if needed
ADMIN_EMAIL = "admin@example.com"   # Replace with your admin email
ADMIN_PASSWORD = "admin123"         # Replace with your admin password

def test_ai_control_feature():
    """Test the AI response control feature end-to-end"""
    
    print("🧪 Testing AI Response Control Feature")
    print("=" * 50)
    
    # Step 1: Admin login
    print("1. 🔐 Testing admin login...")
    login_response = requests.post(f"{BASE_URL}/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if login_response.status_code != 200:
        print(f"❌ Admin login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Admin login successful")
    
    # Step 2: Get conversations
    print("\n2. 📋 Getting conversations...")
    conversations_response = requests.get(f"{BASE_URL}/admin/conversations", headers=headers)
    
    if conversations_response.status_code != 200:
        print(f"❌ Failed to get conversations: {conversations_response.status_code}")
        return False
    
    conversations = conversations_response.json()
    if not conversations:
        print("⚠️  No conversations found. Create a conversation first to test.")
        return True
    
    print(f"✅ Found {len(conversations)} conversations")
    
    # Step 3: Check if ai_responses_enabled field exists
    first_conversation = conversations[0]
    if 'ai_responses_enabled' not in first_conversation:
        print("❌ ai_responses_enabled field missing from conversation data")
        return False
    
    print(f"✅ ai_responses_enabled field present: {first_conversation['ai_responses_enabled']}")
    
    # Step 4: Get conversation details
    print("\n3. 🔍 Getting conversation details...")
    conv_id = first_conversation['id']
    details_response = requests.get(f"{BASE_URL}/admin/conversation/{conv_id}", headers=headers)
    
    if details_response.status_code != 200:
        print(f"❌ Failed to get conversation details: {details_response.status_code}")
        return False
    
    details = details_response.json()
    user_info = details['user_info']
    user_id = user_info['id']
    current_ai_status = user_info['ai_responses_enabled']
    
    print(f"✅ User {user_info['user_code']} - AI responses currently: {'enabled' if current_ai_status else 'disabled'}")
    
    # Step 5: Test toggling AI responses
    print("\n4. 🔄 Testing AI response toggle...")
    new_ai_status = not current_ai_status
    
    toggle_response = requests.post(f"{BASE_URL}/admin/toggle-ai-responses", 
        headers=headers,
        json={
            "user_id": user_id,
            "ai_responses_enabled": new_ai_status
        }
    )
    
    if toggle_response.status_code != 200:
        print(f"❌ Failed to toggle AI responses: {toggle_response.status_code}")
        print(f"Response: {toggle_response.text}")
        return False
    
    print(f"✅ AI responses {'enabled' if new_ai_status else 'disabled'} successfully")
    
    # Step 6: Verify the change
    print("\n5. ✅ Verifying the change...")
    verify_response = requests.get(f"{BASE_URL}/admin/conversation/{conv_id}", headers=headers)
    
    if verify_response.status_code != 200:
        print(f"❌ Failed to verify change: {verify_response.status_code}")
        return False
    
    verify_details = verify_response.json()
    updated_ai_status = verify_details['user_info']['ai_responses_enabled']
    
    if updated_ai_status == new_ai_status:
        print(f"✅ Change verified! AI responses are now {'enabled' if updated_ai_status else 'disabled'}")
    else:
        print(f"❌ Change not applied. Expected: {new_ai_status}, Got: {updated_ai_status}")
        return False
    
    # Step 7: Toggle back to original state
    print("\n6. 🔄 Restoring original state...")
    restore_response = requests.post(f"{BASE_URL}/admin/toggle-ai-responses", 
        headers=headers,
        json={
            "user_id": user_id,
            "ai_responses_enabled": current_ai_status
        }
    )
    
    if restore_response.status_code == 200:
        print("✅ Original state restored")
    else:
        print(f"⚠️  Failed to restore original state: {restore_response.status_code}")
    
    print("\n🎉 AI Response Control Feature Test PASSED!")
    print("\nFeature Summary:")
    print("✅ Admin can view AI response status in conversations")
    print("✅ Admin can toggle AI responses via API")
    print("✅ Changes are persisted in database")
    print("✅ API endpoints are working correctly")
    
    return True

if __name__ == "__main__":
    try:
        success = test_ai_control_feature()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the backend is running on http://localhost:8001")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        sys.exit(1)