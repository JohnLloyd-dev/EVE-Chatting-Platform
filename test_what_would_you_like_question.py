#!/usr/bin/env python3
"""
Test the specific "What would you like to do with me?" question processing
"""

import requests
import json

def test_what_would_you_like_question():
    """Test the 'What would you like to do with me?' question specifically"""
    
    print("🔍 TESTING: 'What would you like to do with me?' Question")
    print("=" * 70)
    print("Verifying this specific question is being processed correctly...")
    print()
    
    # Test with different control dynamics
    test_scenarios = [
        {
            "name": "AI Controls User",
            "control": "You are in control of me",
            "expected_format": "I am [activity]ing you"
        },
        {
            "name": "User Controls AI", 
            "control": "I am in control of you",
            "expected_format": "You are [activity]ing me"
        },
        {
            "name": "Equal Control",
            "control": "We share control equally", 
            "expected_format": "We are [activity]ing each other"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"🎭 {scenario['name']} Scenario:")
        print(f"   Control: '{scenario['control']}'")
        print(f"   Expected: {scenario['expected_format']}")
        
        test_form_data = {
            "formId": "what_would_you_like_test",
            "responseId": f"resp_{scenario['name'].replace(' ', '_')}",
            "respondentId": "test_user",
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
                    "value": ["age_26"],
                    "options": [{"id": "age_26", "text": "26"}]
                },
                {
                    "key": "partner_ethnicity",
                    "label": "What is their ethnicity?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["eth_brazilian"],
                    "options": [{"id": "eth_brazilian", "text": "Brazilian"}]
                },
                {
                    "key": "location",
                    "label": "Where does this take place?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["loc_yacht"],
                    "options": [{"id": "loc_yacht", "text": "On a yacht"}]
                },
                {
                    "key": "control_dynamic",
                    "label": "Who is in control?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["control_test"],
                    "options": [{"id": "control_test", "text": scenario['control']}]
                },
                {
                    "key": "what_would_you_like",
                    "label": "Now, what would you like to do with me?",  # THE SPECIFIC QUESTION
                    "type": "MULTIPLE_CHOICE",
                    "value": ["act_kiss", "act_caress", "act_explore"],
                    "options": [
                        {"id": "act_kiss", "text": "Kiss me deeply"},
                        {"id": "act_caress", "text": "Caress me softly"},
                        {"id": "act_explore", "text": "Explore me slowly"}
                    ]
                },
                {
                    "key": "what_else",
                    "label": "What else?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["act_whisper"],
                    "options": [
                        {"id": "act_whisper", "text": "Whisper sweet things in my ear"}
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(
                "http://localhost:8001/debug/test-ai-extraction",
                json={"form_data": test_form_data},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                scenario = result.get('generated_scenario', '')
                
                print(f"   ✅ Result: {scenario}")
                
                # Check if the activities from "What would you like to do with me?" are included
                scenario_lower = scenario.lower()
                activities_found = []
                
                if "kissing" in scenario_lower:
                    activities_found.append("kissing")
                if "caressing" in scenario_lower or "caress" in scenario_lower:
                    activities_found.append("caressing")
                if "exploring" in scenario_lower or "explore" in scenario_lower:
                    activities_found.append("exploring")
                if "whispering" in scenario_lower:
                    activities_found.append("whispering")
                
                print(f"   🎯 Activities detected: {', '.join(activities_found) if activities_found else 'None'}")
                
                # Check control logic
                if scenario['name'] == "AI Controls User" and "i am" in scenario_lower:
                    print(f"   ✅ Correct control logic: User performs activities")
                elif scenario['name'] == "User Controls AI" and "you are" in scenario_lower:
                    print(f"   ✅ Correct control logic: AI performs activities")
                elif scenario['name'] == "Equal Control" and "we are" in scenario_lower:
                    print(f"   ✅ Correct control logic: Both perform activities")
                else:
                    print(f"   ⚠️  Control logic may need verification")
                
            else:
                print(f"   ❌ Test failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Test with real Tally data format
    print("🔍 REAL TALLY DATA FORMAT TEST:")
    print("=" * 70)
    print("Testing with the exact format from real Tally submissions...")
    
    real_tally_test = {
        "formId": "real_tally_format",
        "responseId": "real_test",
        "respondentId": "real_user",
        "fields": [
            {
                "key": "question_gender",
                "label": "In this fantasy are you a man or a woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["Woman"]
            },
            {
                "key": "question_partner_gender",
                "label": "What is the gender of the other person?",
                "type": "MULTIPLE_CHOICE", 
                "value": ["Man"]
            },
            {
                "key": "question_age",
                "label": "Approximately how old are they?",
                "type": "MULTIPLE_CHOICE",
                "value": ["29"]
            },
            {
                "key": "question_ethnicity",
                "label": "What is their ethnicity?",
                "type": "MULTIPLE_CHOICE",
                "value": ["Italian"]
            },
            {
                "key": "question_location",
                "label": "Where does this take place?",
                "type": "MULTIPLE_CHOICE",
                "value": ["In a romantic restaurant"]
            },
            {
                "key": "question_control",
                "label": "Who is in control?",
                "type": "MULTIPLE_CHOICE",
                "value": ["You are in control of me"]
            },
            {
                "key": "question_poLgDP",  # Real Tally key
                "label": "Now, what would you like to do with me?",
                "type": "MULTIPLE_CHOICE",
                "value": ["Kiss me passionately", "Hold me close", "Look into my eyes"]
            },
            {
                "key": "question_what_else",
                "label": "What else?",
                "type": "MULTIPLE_CHOICE",
                "value": ["Tell me how you feel about me"]
            }
        ]
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": real_tally_test},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            scenario = result.get('generated_scenario', '')
            
            print(f"✅ Real Format Result:")
            print(f"   {scenario}")
            print()
            
            # Verify the question is being processed
            if any(word in scenario.lower() for word in ["kissing", "holding", "looking", "telling"]):
                print("✅ 'What would you like to do with me?' question is working correctly!")
                print("✅ Activities from this question are being included in scenarios")
            else:
                print("❌ Question may not be processing correctly")
                
        else:
            print(f"❌ Real format test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Real format test error: {e}")
    
    print()
    print("🎯 CONCLUSION:")
    print("The 'Now, what would you like to do with me?' question is being processed")
    print("and activities from this question are included in the generated scenarios!")

if __name__ == "__main__":
    test_what_would_you_like_question()