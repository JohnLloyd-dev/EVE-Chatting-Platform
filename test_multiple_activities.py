#!/usr/bin/env python3
"""
Test multiple activities and selections
"""

import requests
import json

def test_multiple_activities():
    """Test form with multiple activity selections"""
    
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
                    {"id": "option1", "text": "Woman"},
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
                    {"id": "option2", "text": "Man"}
                ]
            },
            {
                "key": "ai_age",
                "label": "Approximately how old are they?",
                "type": "MULTIPLE_CHOICE",
                "value": ["option1"], 
                "options": [
                    {"id": "option1", "text": "25"},
                    {"id": "option2", "text": "30"}
                ]
            },
            {
                "key": "location",
                "label": "Where does this take place?",
                "type": "MULTIPLE_CHOICE", 
                "value": ["option1"],
                "options": [
                    {"id": "option1", "text": "At the beach"},
                    {"id": "option2", "text": "At home"}
                ]
            },
            {
                "key": "activities1",
                "label": "What would you like to do with me?",
                "type": "MULTIPLE_CHOICE",
                "value": ["act1", "act2", "act3"],  # Multiple activities
                "options": [
                    {"id": "act1", "text": "Kiss me passionately"},
                    {"id": "act2", "text": "Hold me close"},
                    {"id": "act3", "text": "Whisper in my ear"},
                    {"id": "act4", "text": "Dance with me"}
                ]
            },
            {
                "key": "activities2",
                "label": "What else would you like?",
                "type": "MULTIPLE_CHOICE",
                "value": ["more1", "more2"],  # More multiple activities
                "options": [
                    {"id": "more1", "text": "Touch me gently"},
                    {"id": "more2", "text": "Look into my eyes"},
                    {"id": "more3", "text": "Smile at me"}
                ]
            }
        ]
    }
    
    print("=== Testing Multiple Activities ===")
    print("Expected:")
    print("- AI: 25-year-old man")
    print("- User: Woman")
    print("- Location: At the beach")
    print("- Activities: Kiss me passionately, Hold me close, Whisper in my ear, Touch me gently, Look into my eyes")
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
                
                # Check if multiple activities are included
                activities_found = []
                expected_activities = [
                    'kiss me passionately', 'hold me close', 'whisper in my ear',
                    'touch me gently', 'look into my eyes'
                ]
                
                for activity in expected_activities:
                    if activity in scenario:
                        activities_found.append(activity)
                
                print(f"\n🔍 Multiple Activities Check:")
                print(f"Activities found: {len(activities_found)}/{len(expected_activities)}")
                for activity in activities_found:
                    print(f"✅ {activity}")
                
                missing = [act for act in expected_activities if act not in activities_found]
                if missing:
                    print("Missing activities:")
                    for activity in missing:
                        print(f"❌ {activity}")
                
            return True
        else:
            print(f"❌ Test failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_multiple_activities()
    
    if success:
        print(f"\n🎉 Multiple activities test completed!")
    else:
        print(f"\n❌ Test failed")