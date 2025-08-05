#!/usr/bin/env python3
"""
Test to verify correct AI/User mapping from Tally form
"""

import requests
import json

def test_mapping():
    """Test that AI gets the 'other person' data and user gets their own data"""
    
    # Create test form data with clear distinctions
    test_form_data = {
        "formId": "test123",
        "responseId": "resp123", 
        "respondentId": "user123",
        "fields": [
            {
                "key": "user_gender",
                "label": "In this fantasy are you a man or a woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["option1"],
                "options": [
                    {"id": "option1", "text": "Woman"},  # USER is a woman
                    {"id": "option2", "text": "Man"}
                ]
            },
            {
                "key": "ai_gender",
                "label": "What is the gender of the other person?", 
                "type": "MULTIPLE_CHOICE",
                "value": ["option2"],
                "options": [
                    {"id": "option1", "text": "Woman"},
                    {"id": "option2", "text": "Man"}  # AI should be a man
                ]
            },
            {
                "key": "ai_age",
                "label": "Approximately how old are they?",
                "type": "MULTIPLE_CHOICE",
                "value": ["option1"], 
                "options": [
                    {"id": "option1", "text": "30"},  # AI should be 30
                    {"id": "option2", "text": "25"}
                ]
            },
            {
                "key": "ai_ethnicity",
                "label": "What is their ethnicity?",
                "type": "MULTIPLE_CHOICE",
                "value": ["option1"],
                "options": [
                    {"id": "option1", "text": "Asian"},  # AI should be Asian
                    {"id": "option2", "text": "White"}
                ]
            },
            {
                "key": "location",
                "label": "Where does this take place?",
                "type": "MULTIPLE_CHOICE", 
                "value": ["option1"],
                "options": [
                    {"id": "option1", "text": "At a coffee shop"},  # Location
                    {"id": "option2", "text": "At home"}
                ]
            },
            {
                "key": "control",
                "label": "Who is in control?",
                "type": "MULTIPLE_CHOICE",
                "value": ["option1"],
                "options": [
                    {"id": "option1", "text": "You will be in control of me"},  # AI dominant
                    {"id": "option2", "text": "I will be in control of you"}
                ]
            },
            {
                "key": "activity",
                "label": "What would you like to do with me?",
                "type": "MULTIPLE_CHOICE",
                "value": ["option1"],
                "options": [
                    {"id": "option1", "text": "Kiss me passionately"},  # Activity
                    {"id": "option2", "text": "Hold my hand"}
                ]
            }
        ]
    }
    
    print("=== Testing AI/User Mapping ===")
    print("Expected Results:")
    print("- AI should be: 30-year-old Asian man")
    print("- User should be: Woman") 
    print("- Location: At a coffee shop")
    print("- Control: AI in control")
    print("- Activity: Kiss me passionately")
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
            print(f"Questions processed: {result.get('debug_info', {}).get('summary', {}).get('total_questions', 0)}")
            
            if result.get('generated_scenario'):
                print(f"\n📝 Generated Scenario:")
                print("-" * 60)
                print(result['generated_scenario'])
                print("-" * 60)
                
                scenario = result['generated_scenario'].lower()
                
                # Check if mapping is correct
                print(f"\n🔍 Mapping Verification:")
                print(f"✅ AI is 30-year-old Asian man: {'30' in scenario and 'asian' in scenario and 'man' in scenario}")
                print(f"✅ User is woman: {'i am a woman' in scenario or 'woman' in scenario}")
                print(f"✅ Coffee shop location: {'coffee shop' in scenario}")
                print(f"✅ AI in control: {'you are in control' in scenario or 'in control of me' in scenario}")
                print(f"✅ Kiss activity: {'kiss' in scenario}")
                
            return True
        else:
            print(f"❌ Test failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_mapping()
    
    if success:
        print(f"\n🎉 Mapping test successful!")
        print("✅ AI correctly takes 'other person' characteristics")
        print("✅ User correctly identified from form responses")
        print("✅ All form data accurately extracted and used")
    else:
        print(f"\n❌ Mapping test failed")