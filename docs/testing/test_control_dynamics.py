#!/usr/bin/env python3
"""
Test different control dynamics in Tally forms
"""

import requests
import json

def test_user_in_control():
    """Test when user selects 'I am in control of you'"""
    
    test_form_data = {
        "formId": "control_test_user",
        "responseId": "resp_user_control",
        "respondentId": "user_control",
        "fields": [
            {
                "key": "user_gender",
                "label": "In this fantasy are you a man or a woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["gender_woman"],
                "options": [
                    {"id": "gender_woman", "text": "Woman"},
                    {"id": "gender_man", "text": "Man"}
                ]
            },
            {
                "key": "partner_gender",
                "label": "What is the gender of the other person?",
                "type": "MULTIPLE_CHOICE",
                "value": ["partner_man"],
                "options": [
                    {"id": "partner_woman", "text": "Woman"},
                    {"id": "partner_man", "text": "Man"}
                ]
            },
            {
                "key": "partner_age",
                "label": "How old are they?",
                "type": "MULTIPLE_CHOICE",
                "value": ["age_25"],
                "options": [
                    {"id": "age_22", "text": "22"},
                    {"id": "age_25", "text": "25"},
                    {"id": "age_28", "text": "28"}
                ]
            },
            {
                "key": "partner_ethnicity",
                "label": "What is their ethnicity?",
                "type": "MULTIPLE_CHOICE",
                "value": ["eth_italian"],
                "options": [
                    {"id": "eth_white", "text": "White"},
                    {"id": "eth_italian", "text": "Italian"},
                    {"id": "eth_asian", "text": "Asian"}
                ]
            },
            {
                "key": "location",
                "label": "Where does this take place?",
                "type": "MULTIPLE_CHOICE",
                "value": ["loc_bedroom"],
                "options": [
                    {"id": "loc_bedroom", "text": "In a bedroom"},
                    {"id": "loc_hotel", "text": "In a hotel"},
                    {"id": "loc_beach", "text": "At the beach"}
                ]
            },
            {
                "key": "control_dynamic",
                "label": "Who is in control?",
                "type": "MULTIPLE_CHOICE",
                "value": ["control_user"],  # USER IN CONTROL
                "options": [
                    {"id": "control_user", "text": "I am in control of you"},
                    {"id": "control_partner", "text": "You are in control of me"},
                    {"id": "control_equal", "text": "We share control equally"}
                ]
            },
            {
                "key": "activities",
                "label": "What would you like to do?",
                "type": "MULTIPLE_CHOICE",
                "value": ["act_kiss", "act_touch", "act_guide"],
                "options": [
                    {"id": "act_kiss", "text": "Kiss me passionately"},
                    {"id": "act_touch", "text": "Touch me gently"},
                    {"id": "act_guide", "text": "Let me guide you"},
                    {"id": "act_whisper", "text": "Whisper to me"}
                ]
            }
        ]
    }
    
    print("👑 USER IN CONTROL TEST")
    print("=" * 50)
    print("Testing scenario where USER is in control:")
    print("- User: Woman")
    print("- AI: 25-year-old Italian man")
    print("- Location: Bedroom")
    print("- Control: 'I am in control of you' (USER controls AI)")
    print("- Activities: Kiss, Touch, Guide")
    print()
    
    try:
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": test_form_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Test Successful!")
            
            if result.get('generated_scenario'):
                print("🎭 Generated Scenario (User in Control):")
                print("-" * 60)
                print(result['generated_scenario'])
                print("-" * 60)
                
                scenario = result['generated_scenario'].lower()
                
                # Check control indicators
                control_indicators = [
                    ("User controls AI", "i am in control" in scenario),
                    ("Activities present", any(word in scenario for word in ["kissing", "touching", "guiding"])),
                    ("Proper roles", "you are a" in scenario and "i am a" in scenario)
                ]
                
                print("\n🔍 Control Dynamic Analysis:")
                for indicator, found in control_indicators:
                    status = "✅" if found else "❌"
                    print(f"   {status} {indicator}")
            
            return result.get('generated_scenario', '')
        else:
            print(f"❌ Test failed: {response.status_code}")
            return ''
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return ''

def test_ai_in_control():
    """Test when user selects 'You are in control of me' for comparison"""
    
    test_form_data = {
        "formId": "control_test_ai",
        "responseId": "resp_ai_control",
        "respondentId": "ai_control",
        "fields": [
            {
                "key": "user_gender",
                "label": "In this fantasy are you a man or a woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["gender_woman"],
                "options": [
                    {"id": "gender_woman", "text": "Woman"},
                    {"id": "gender_man", "text": "Man"}
                ]
            },
            {
                "key": "partner_gender",
                "label": "What is the gender of the other person?",
                "type": "MULTIPLE_CHOICE",
                "value": ["partner_man"],
                "options": [
                    {"id": "partner_woman", "text": "Woman"},
                    {"id": "partner_man", "text": "Man"}
                ]
            },
            {
                "key": "partner_age",
                "label": "How old are they?",
                "type": "MULTIPLE_CHOICE",
                "value": ["age_25"],
                "options": [
                    {"id": "age_22", "text": "22"},
                    {"id": "age_25", "text": "25"},
                    {"id": "age_28", "text": "28"}
                ]
            },
            {
                "key": "partner_ethnicity",
                "label": "What is their ethnicity?",
                "type": "MULTIPLE_CHOICE",
                "value": ["eth_italian"],
                "options": [
                    {"id": "eth_white", "text": "White"},
                    {"id": "eth_italian", "text": "Italian"},
                    {"id": "eth_asian", "text": "Asian"}
                ]
            },
            {
                "key": "location",
                "label": "Where does this take place?",
                "type": "MULTIPLE_CHOICE",
                "value": ["loc_bedroom"],
                "options": [
                    {"id": "loc_bedroom", "text": "In a bedroom"},
                    {"id": "loc_hotel", "text": "In a hotel"},
                    {"id": "loc_beach", "text": "At the beach"}
                ]
            },
            {
                "key": "control_dynamic",
                "label": "Who is in control?",
                "type": "MULTIPLE_CHOICE",
                "value": ["control_partner"],  # AI IN CONTROL
                "options": [
                    {"id": "control_user", "text": "I am in control of you"},
                    {"id": "control_partner", "text": "You are in control of me"},
                    {"id": "control_equal", "text": "We share control equally"}
                ]
            },
            {
                "key": "activities",
                "label": "What would you like to do?",
                "type": "MULTIPLE_CHOICE",
                "value": ["act_kiss", "act_touch", "act_guide"],
                "options": [
                    {"id": "act_kiss", "text": "Kiss me passionately"},
                    {"id": "act_touch", "text": "Touch me gently"},
                    {"id": "act_guide", "text": "Let me guide you"},
                    {"id": "act_whisper", "text": "Whisper to me"}
                ]
            }
        ]
    }
    
    print("\n🤖 AI IN CONTROL TEST")
    print("=" * 50)
    print("Testing scenario where AI is in control:")
    print("- User: Woman")
    print("- AI: 25-year-old Italian man")
    print("- Location: Bedroom")
    print("- Control: 'You are in control of me' (AI controls USER)")
    print("- Activities: Kiss, Touch, Guide")
    print()
    
    try:
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": test_form_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Test Successful!")
            
            if result.get('generated_scenario'):
                print("🎭 Generated Scenario (AI in Control):")
                print("-" * 60)
                print(result['generated_scenario'])
                print("-" * 60)
            
            return result.get('generated_scenario', '')
        else:
            print(f"❌ Test failed: {response.status_code}")
            return ''
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return ''

def compare_control_dynamics():
    """Compare both control scenarios side by side"""
    
    print("🔄 CONTROL DYNAMICS COMPARISON")
    print("=" * 70)
    
    user_control_scenario = test_user_in_control()
    ai_control_scenario = test_ai_in_control()
    
    print("\n" + "=" * 70)
    print("📊 SIDE-BY-SIDE COMPARISON")
    print("=" * 70)
    
    print("\n👑 USER IN CONTROL:")
    print(f"   {user_control_scenario}")
    
    print("\n🤖 AI IN CONTROL:")
    print(f"   {ai_control_scenario}")
    
    print("\n🔍 KEY DIFFERENCES:")
    if user_control_scenario and ai_control_scenario:
        user_lower = user_control_scenario.lower()
        ai_lower = ai_control_scenario.lower()
        
        differences = []
        
        if "i am in control" in user_lower and "you are in control" in ai_lower:
            differences.append("✅ Control statements are different")
        
        if "i am" in user_lower and "i am" in ai_lower:
            differences.append("✅ Both use 'I am' for user actions")
        
        if len(differences) == 0:
            differences.append("⚠️  Need to check control logic implementation")
        
        for diff in differences:
            print(f"   {diff}")
    
    print(f"\n🎯 CONCLUSION:")
    print(f"   The system should handle both control dynamics appropriately")
    print(f"   User activities remain in present continuous regardless of control")

if __name__ == "__main__":
    compare_control_dynamics()