#!/usr/bin/env python3
"""
Test problematic activities that might cause grammar issues
"""

import requests
import json

def test_problematic_activities():
    """Test activities that might cause grammar problems"""
    
    print("🔍 TESTING PROBLEMATIC ACTIVITIES")
    print("=" * 60)
    print("Testing activities that might cause grammar issues...")
    print()
    
    # Test potentially problematic activities
    problematic_activities = [
        "Take me against my will",
        "Punish me",
        "Force me to do things",
        "Make me submit",
        "Control me completely",
        "Dominate me roughly"
    ]
    
    for activity in problematic_activities:
        print(f"🎭 Testing Activity: '{activity}'")
        
        test_form_data = {
            "formId": "problematic_test",
            "responseId": f"resp_{activity.replace(' ', '_')}",
            "respondentId": "test_user",
            "fields": [
                {
                    "key": "user_gender",
                    "label": "In this fantasy are you a man or a woman?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["gender_man"],
                    "options": [{"id": "gender_woman", "text": "Woman"}, {"id": "gender_man", "text": "Man"}]
                },
                {
                    "key": "partner_gender",
                    "label": "What is the gender of the other person?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["partner_woman"],
                    "options": [{"id": "partner_woman", "text": "Woman"}, {"id": "partner_man", "text": "Man"}]
                },
                {
                    "key": "partner_age",
                    "label": "How old are they?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["age_18"],
                    "options": [{"id": "age_18", "text": "18"}]
                },
                {
                    "key": "partner_ethnicity",
                    "label": "What is their ethnicity?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["eth_asian"],
                    "options": [{"id": "eth_asian", "text": "Asian"}]
                },
                {
                    "key": "location",
                    "label": "Where does this take place?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["loc_nature"],
                    "options": [{"id": "loc_nature", "text": "In nature"}]
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
                    "label": "Now, what would you like to do with me?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["act_test"],
                    "options": [{"id": "act_test", "text": activity}]
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
                
                print(f"   Input: '{activity}'")
                print(f"   Result: {scenario}")
                
                # Check for grammar issues
                grammar_issues = []
                scenario_lower = scenario.lower()
                
                if " your " in scenario_lower and " me" in scenario_lower:
                    grammar_issues.append("Mixed pronouns (your + me)")
                if "you me" in scenario_lower:
                    grammar_issues.append("Double pronouns (you me)")
                if "your against your" in scenario_lower:
                    grammar_issues.append("Repeated 'your'")
                if "willl" in scenario_lower:
                    grammar_issues.append("Typo (willl)")
                
                if grammar_issues:
                    print(f"   ❌ Grammar Issues: {', '.join(grammar_issues)}")
                else:
                    print(f"   ✅ Grammar looks good")
                
            else:
                print(f"   ❌ Test failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()

def test_specific_broken_example():
    """Test the specific broken example from the user"""
    
    print("🔍 TESTING SPECIFIC BROKEN EXAMPLE")
    print("=" * 60)
    print("Reproducing the exact scenario that produced broken grammar...")
    print()
    
    # Try to reproduce the broken scenario
    test_form_data = {
        "formId": "broken_example_test",
        "responseId": "broken_test",
        "respondentId": "broken_user",
        "fields": [
            {
                "key": "user_gender",
                "label": "In this fantasy are you a man or a woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["gender_man"],
                "options": [{"id": "gender_woman", "text": "Woman"}, {"id": "gender_man", "text": "Man"}]
            },
            {
                "key": "partner_gender",
                "label": "What is the gender of the other person?",
                "type": "MULTIPLE_CHOICE",
                "value": ["partner_woman"],
                "options": [{"id": "partner_woman", "text": "Woman"}, {"id": "partner_man", "text": "Man"}]
            },
            {
                "key": "partner_age",
                "label": "How old are they?",
                "type": "MULTIPLE_CHOICE",
                "value": ["age_18"],
                "options": [{"id": "age_18", "text": "18"}]
            },
            {
                "key": "partner_ethnicity",
                "label": "What is their ethnicity?",
                "type": "MULTIPLE_CHOICE",
                "value": ["eth_asian"],
                "options": [{"id": "eth_asian", "text": "Asian"}]
            },
            {
                "key": "location",
                "label": "Where does this take place?",
                "type": "MULTIPLE_CHOICE",
                "value": ["loc_nature"],
                "options": [{"id": "loc_nature", "text": "In nature"}]
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
                "label": "Now, what would you like to do with me?",
                "type": "MULTIPLE_CHOICE",
                "value": ["act_take", "act_punish"],
                "options": [
                    {"id": "act_take", "text": "Take me against my will"},
                    {"id": "act_punish", "text": "Punish me"}
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
            
            print(f"🎭 Reproduced Scenario:")
            print(f"   {scenario}")
            print()
            
            # Compare with the broken example
            broken_example = "You are taking your against your willl me, punishing you me"
            
            if "taking your against your" in scenario.lower():
                print("❌ CONFIRMED: The system is producing broken grammar!")
                print("❌ Issue found in activity conversion logic")
            else:
                print("✅ Current system produces correct grammar")
                print("✅ The issue may have been fixed")
            
        else:
            print(f"❌ Test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_problematic_activities()
    test_specific_broken_example()