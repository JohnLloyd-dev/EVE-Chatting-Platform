#!/usr/bin/env python3
"""
Test script to verify the chatting platform setup
"""
import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """Test backend health endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            print("✅ Backend health check passed")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False

def test_tally_webhook():
    """Test Tally webhook endpoint with sample data"""
    try:
        # Load sample Tally data
        with open('tally_form.json', 'r') as f:
            sample_data = json.load(f)
        
        response = requests.post(f"{BACKEND_URL}/webhook/tally", json=sample_data)
        if response.status_code == 200:
            print("✅ Tally webhook test passed")
            result = response.json()
            print(f"   User ID: {result.get('user_id')}")
            print(f"   Session ID: {result.get('session_id')}")
            return result.get('user_id'), result.get('session_id')
        else:
            print(f"❌ Tally webhook test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Tally webhook test failed: {e}")
        return None, None

def test_chat_session(user_id):
    """Test chat session retrieval"""
    if not user_id:
        return False
    
    try:
        response = requests.get(f"{BACKEND_URL}/chat/session/{user_id}")
        if response.status_code == 200:
            print("✅ Chat session retrieval test passed")
            return True
        else:
            print(f"❌ Chat session test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat session test failed: {e}")
        return False

def test_admin_login():
    """Test admin login"""
    try:
        response = requests.post(f"{BACKEND_URL}/admin/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            print("✅ Admin login test passed")
            result = response.json()
            return result.get('access_token')
        else:
            print(f"❌ Admin login test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Admin login test failed: {e}")
        return None

def test_admin_stats(token):
    """Test admin dashboard stats"""
    if not token:
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/admin/stats", headers=headers)
        if response.status_code == 200:
            print("✅ Admin stats test passed")
            stats = response.json()
            print(f"   Total users: {stats.get('total_users')}")
            print(f"   Active sessions: {stats.get('active_sessions')}")
            return True
        else:
            print(f"❌ Admin stats test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Admin stats test failed: {e}")
        return False

def test_frontend():
    """Test frontend accessibility"""
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print("✅ Frontend accessibility test passed")
            return True
        else:
            print(f"❌ Frontend test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

def main():
    print("🚀 Starting Chatting Platform Setup Test")
    print("=" * 50)
    
    # Test backend
    print("\n📡 Testing Backend...")
    backend_ok = test_backend_health()
    
    if backend_ok:
        # Test Tally webhook
        print("\n📝 Testing Tally Integration...")
        user_id, session_id = test_tally_webhook()
        
        # Test chat session
        if user_id:
            print("\n💬 Testing Chat Session...")
            test_chat_session(user_id)
        
        # Test admin functionality
        print("\n👨‍💼 Testing Admin Features...")
        admin_token = test_admin_login()
        if admin_token:
            test_admin_stats(admin_token)
    
    # Test frontend
    print("\n🌐 Testing Frontend...")
    test_frontend()
    
    print("\n" + "=" * 50)
    print("✨ Test completed!")
    print("\nNext steps:")
    print("1. Update AI_MODEL_URL in backend/.env with your VPS URL")
    print("2. Configure Tally webhook to point to your domain")
    print("3. Access admin dashboard at http://localhost:3000/admin")
    print("4. Test chat interface at http://localhost:3000")

if __name__ == "__main__":
    main()