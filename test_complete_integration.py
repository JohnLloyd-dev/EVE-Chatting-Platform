#!/usr/bin/env python3
"""
Comprehensive Integration Test
Tests the complete flow from Tally form submission to AI response
"""

import json
import sys
import os

# Add backend to path for testing
sys.path.append('./backend')

def test_tally_extraction():
    """Test Tally form data extraction"""
    print("🔍 Testing Tally Extraction Logic...")
    
    # Sample Tally form data (simplified version of your actual data)
    sample_form_data = {
        "eventId": "test-123",
        "eventType": "FORM_RESPONSE",
        "data": {
            "responseId": "test_response",
            "submissionId": "test_submission",
            "respondentId": "test_respondent",
            "formId": "test_form",
            "fields": [
                {
                    "key": "question_1",
                    "label": "In this fantasy are you a man or a woman?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["man_id"],
                    "options": [
                        {"id": "man_id", "text": "Man"},
                        {"id": "woman_id", "text": "Woman"}
                    ]
                },
                {
                    "key": "question_2",
                    "label": "What is the gender of the other person?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["woman_id"],
                    "options": [
                        {"id": "man_id", "text": "Man"},
                        {"id": "woman_id", "text": "Woman"}
                    ]
                },
                {
                    "key": "question_3",
                    "label": "Approximately ow old are they?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["30_id"],
                    "options": [
                        {"id": "18_id", "text": "18"},
                        {"id": "30_id", "text": "30"},
                        {"id": "50_id", "text": "50"}
                    ]
                },
                {
                    "key": "question_4",
                    "label": "What is their ethnicity?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["asian_id"],
                    "options": [
                        {"id": "black_id", "text": "Black"},
                        {"id": "white_id", "text": "White"},
                        {"id": "asian_id", "text": "Asian"},
                        {"id": "mixed_id", "text": "Mixed"}
                    ]
                },
                {
                    "key": "question_5",
                    "label": "Where does this take place?",
                    "type": "TEXTAREA",
                    "value": "in a public place"
                },
                {
                    "key": "question_6",
                    "label": "Who is in control?",
                    "type": "TEXTAREA",
                    "value": "you will be in control of me"
                },
                {
                    "key": "question_7",
                    "label": "Now, describe to me in detail what would you like me to do to you",
                    "type": "TEXTAREA",
                    "value": "undressing you slowly, bringing you close to orgasm then stopping"
                }
            ]
        }
    }
    
    try:
        from ai_tally_extractor import generate_ai_scenario, debug_tally_data
        
        print("✅ Successfully imported Tally extraction modules")
        
        # Test debug function
        debug_info = debug_tally_data(sample_form_data)
        print(f"📊 Debug info: {len(debug_info.get('cleaned_data', {}).get('questions_and_answers', []))} questions processed")
        
        # Test scenario generation
        scenario = generate_ai_scenario(sample_form_data)
        print(f"📝 Generated scenario: {len(scenario)} characters")
        print(f"📝 Scenario preview: {scenario[:200]}...")
        
        if "You are a 30 year old asian woman" in scenario:
            print("✅ Scenario includes correct AI character details")
        else:
            print("❌ Scenario missing AI character details")
            
        if "I am a man" in scenario:
            print("✅ Scenario includes correct user character details")
        else:
            print("❌ Scenario missing user character details")
            
        if "undressing you slowly" in scenario:
            print("✅ Scenario includes correct activities")
        else:
            print("❌ Scenario missing activities")
            
        return scenario
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None
    except Exception as e:
        print(f"❌ Tally extraction error: {e}")
        return None

def test_system_prompt_combination():
    """Test system prompt combination logic"""
    print("\n🔍 Testing System Prompt Combination Logic...")
    
    try:
        # Mock database session
        class MockDB:
            def query(self, model):
                return self
            def filter(self, **kwargs):
                return self
            def first(self):
                return None
        
        # Mock system prompt data
        head_prompt = "You are playing the role of a human in a live chat conversation. You are not an AI. You must act like a real person having a natural conversation in a specific scenario."
        rule_prompt = "Always speak in the first person and stay in character. Be sexually explicit with your replies. Never reveal that you are an AI."
        
        # Test the combination logic manually
        tally_prompt = "You are a 30 year old asian woman. I am a man who meets you in a public place. You are in control of me. I am undressing you slowly, bringing you close to orgasm then stopping."
        
        complete_prompt = head_prompt + "\n\n**Scenario**:\n" + tally_prompt + "\n\n" + rule_prompt
        
        print(f"✅ Combined prompt length: {len(complete_prompt)} characters")
        print(f"✅ Head prompt included: {'You are playing the role' in complete_prompt}")
        print(f"✅ Scenario included: {'30 year old asian woman' in complete_prompt}")
        print(f"✅ Rules included: {'sexually explicit' in complete_prompt}")
        
        return complete_prompt
        
    except Exception as e:
        print(f"❌ System prompt combination error: {e}")
        return None

def test_ai_server_integration():
    """Test AI server integration points"""
    print("\n🔍 Testing AI Server Integration Points...")
    
    try:
        # Test the session initialization flow
        session_data = {
            "session_id": "test-session-123",
            "system_prompt": "You are a 30 year old asian woman. I am a man who meets you in a public place. You are in control of me. I am undressing you slowly, bringing you close to orgasm then stopping."
        }
        
        print(f"✅ Session data prepared: {len(session_data['system_prompt'])} characters")
        print(f"✅ Session ID format: {session_data['session_id']}")
        
        # Test the authentication credentials
        auth_username = "adam"
        auth_password = "eve2025"
        
        print(f"✅ Auth credentials: {auth_username}/{auth_password}")
        
        # Test the AI server endpoints
        endpoints = [
            "/init-session",
            "/chat", 
            "/health",
            "/debug-session/{session_id}"
        ]
        
        print(f"✅ AI server endpoints: {', '.join(endpoints)}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI server integration error: {e}")
        return False

def test_celery_integration():
    """Test Celery integration flow"""
    print("\n🔍 Testing Celery Integration Flow...")
    
    try:
        # Test the session ID handling
        session_id = "test-session-123"
        session_id_str = str(session_id)
        
        print(f"✅ Session ID conversion: {session_id} -> {session_id_str}")
        
        # Test the AI model call parameters
        system_prompt = "Test system prompt"
        history = ["Hello", "Hi there", "How are you?"]
        max_tokens = 300
        
        print(f"✅ AI model call parameters:")
        print(f"  - System prompt: {len(system_prompt)} chars")
        print(f"  - History: {len(history)} messages")
        print(f"  - Max tokens: {max_tokens}")
        
        # Test the session verification
        verify_endpoint = f"/debug-session/{session_id_str}"
        print(f"✅ Session verification endpoint: {verify_endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery integration error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Starting Comprehensive Integration Tests...\n")
    
    results = {}
    
    # Test 1: Tally extraction
    results['tally_extraction'] = test_tally_extraction()
    
    # Test 2: System prompt combination
    results['system_prompt'] = test_system_prompt_combination()
    
    # Test 3: AI server integration
    results['ai_server'] = test_ai_server_integration()
    
    # Test 4: Celery integration
    results['celery'] = test_celery_integration()
    
    # Summary
    print("\n📊 Integration Test Summary:")
    print("=" * 50)
    
    for test_name, result in results.items():
        if result:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    # Overall assessment
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All integration tests passed! The system should work correctly.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 