#!/usr/bin/env python3
"""
Test how control dynamics should affect object/subject relationships
"""

import requests
import json

def test_control_logic():
    """Test the logic of who does what based on control"""
    
    print("🧠 CONTROL LOGIC ANALYSIS")
    print("=" * 60)
    print("Understanding who should do what based on control...")
    print()
    
    print("💭 LOGICAL EXPECTATIONS:")
    print()
    print("1️⃣ When USER is in control ('I am in control of you'):")
    print("   - User controls the AI")
    print("   - User tells AI what to do")
    print("   - Activities should be: 'You are [doing to me]'")
    print("   - Example: 'You are kissing me passionately'")
    print()
    
    print("2️⃣ When AI is in control ('You are in control of me'):")
    print("   - AI controls the User")
    print("   - AI tells User what they're doing")
    print("   - Activities should be: 'I am [doing to you]'")
    print("   - Example: 'I am kissing you passionately'")
    print()
    
    print("3️⃣ When Equal control ('We share control equally'):")
    print("   - Both participate equally")
    print("   - Could be: 'We are [doing together]'")
    print("   - Example: 'We are kissing passionately'")
    print()

def test_current_vs_expected():
    """Test current behavior vs expected behavior"""
    
    # Test User in Control
    user_control_data = {
        "formId": "test_user_control",
        "responseId": "resp_user",
        "respondentId": "user_test",
        "fields": [
            {
                "key": "user_gender",
                "label": "In this fantasy are you a man or a woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["gender_woman"],
                "options": [{"id": "gender_woman", "text": "Woman"}, {"id": "gender_man", "text": "Man"}]
            },
            {
                "key": "partner_gender",
                "label": "What is the gender of the other person?",
                "type": "MULTIPLE_CHOICE",
                "value": ["partner_man"],
                "options": [{"id": "partner_woman", "text": "Woman"}, {"id": "partner_man", "text": "Man"}]
            },
            {
                "key": "partner_age",
                "label": "How old are they?",
                "type": "MULTIPLE_CHOICE",
                "value": ["age_28"],
                "options": [{"id": "age_28", "text": "28"}]
            },
            {
                "key": "location",
                "label": "Where does this take place?",
                "type": "MULTIPLE_CHOICE",
                "value": ["loc_bedroom"],
                "options": [{"id": "loc_bedroom", "text": "In a bedroom"}]
            },
            {
                "key": "control_dynamic",
                "label": "Who is in control?",
                "type": "MULTIPLE_CHOICE",
                "value": ["control_user"],
                "options": [{"id": "control_user", "text": "I am in control of you"}]
            },
            {
                "key": "activities",
                "label": "What would you like to do?",
                "type": "MULTIPLE_CHOICE",
                "value": ["act_kiss", "act_touch"],
                "options": [
                    {"id": "act_kiss", "text": "Kiss me passionately"},
                    {"id": "act_touch", "text": "Touch me gently"}
                ]
            }
        ]
    }
    
    # Test AI in Control
    ai_control_data = {
        "formId": "test_ai_control",
        "responseId": "resp_ai",
        "respondentId": "ai_test",
        "fields": [
            {
                "key": "user_gender",
                "label": "In this fantasy are you a man or a woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["gender_woman"],
                "options": [{"id": "gender_woman", "text": "Woman"}, {"id": "gender_man", "text": "Man"}]
            },
            {
                "key": "partner_gender",
                "label": "What is the gender of the other person?",
                "type": "MULTIPLE_CHOICE",
                "value": ["partner_man"],
                "options": [{"id": "partner_woman", "text": "Woman"}, {"id": "partner_man", "text": "Man"}]
            },
            {
                "key": "partner_age",
                "label": "How old are they?",
                "type": "MULTIPLE_CHOICE",
                "value": ["age_28"],
                "options": [{"id": "age_28", "text": "28"}]
            },
            {
                "key": "location",
                "label": "Where does this take place?",
                "type": "MULTIPLE_CHOICE",
                "value": ["loc_bedroom"],
                "options": [{"id": "loc_bedroom", "text": "In a bedroom"}]
            },
            {
                "key": "control_dynamic",
                "label": "Who is in control?",
                "type": "MULTIPLE_CHOICE",
                "value": ["control_ai"],
                "options": [{"id": "control_ai", "text": "You are in control of me"}]
            },
            {
                "key": "activities",
                "label": "What would you like to do?",
                "type": "MULTIPLE_CHOICE",
                "value": ["act_kiss", "act_touch"],
                "options": [
                    {"id": "act_kiss", "text": "Kiss me passionately"},
                    {"id": "act_touch", "text": "Touch me gently"}
                ]
            }
        ]
    }
    
    print("🔬 CURRENT BEHAVIOR TEST")
    print("=" * 60)
    
    # Test User Control
    try:
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": user_control_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            user_scenario = result.get('generated_scenario', '')
            
            print("👑 USER IN CONTROL:")
            print(f"   Current Output: {user_scenario}")
            print(f"   Expected Logic: You are a 28 year old man. I am a woman. We meet in a bedroom. I am in control of you. You are kissing me passionately, touching me gently.")
            print()
        
    except Exception as e:
        print(f"❌ User control test error: {e}")
    
    # Test AI Control
    try:
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": ai_control_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_scenario = result.get('generated_scenario', '')
            
            print("🤖 AI IN CONTROL:")
            print(f"   Current Output: {ai_scenario}")
            print(f"   Expected Logic: You are a 28 year old man. I am a woman. We meet in a bedroom. You are in control of me. I am kissing you passionately, touching you gently.")
            print()
        
    except Exception as e:
        print(f"❌ AI control test error: {e}")
    
    print("🎯 ANALYSIS:")
    print("   The current system always uses 'I am [doing]' regardless of control")
    print("   But logically, when User controls AI, it should be 'You are [doing]'")
    print("   This needs to be fixed to match the control dynamic!")

if __name__ == "__main__":
    test_control_logic()
    test_current_vs_expected()