#!/usr/bin/env python3
"""
Test all control dynamic options
"""

import requests
import json

def test_control_option(control_text, control_description):
    """Test a specific control option"""
    
    test_form_data = {
        "formId": "control_test",
        "responseId": f"resp_{control_text.replace(' ', '_')}",
        "respondentId": "user_test",
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
                "value": ["age_30"],
                "options": [
                    {"id": "age_25", "text": "25"},
                    {"id": "age_30", "text": "30"},
                    {"id": "age_35", "text": "35"}
                ]
            },
            {
                "key": "location",
                "label": "Where does this take place?",
                "type": "MULTIPLE_CHOICE",
                "value": ["loc_hotel"],
                "options": [
                    {"id": "loc_bedroom", "text": "In a bedroom"},
                    {"id": "loc_hotel", "text": "In a hotel room"},
                    {"id": "loc_beach", "text": "At the beach"}
                ]
            },
            {
                "key": "control_dynamic",
                "label": "Who is in control?",
                "type": "MULTIPLE_CHOICE",
                "value": ["control_test"],
                "options": [
                    {"id": "control_test", "text": control_text}
                ]
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
    
    try:
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": test_form_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            scenario = result.get('generated_scenario', '')
            
            print(f"📝 {control_description}:")
            print(f"   Input: '{control_text}'")
            print(f"   Output: {scenario}")
            print()
            
            return scenario
        else:
            print(f"❌ Test failed for '{control_text}': {response.status_code}")
            return ''
            
    except Exception as e:
        print(f"❌ Error testing '{control_text}': {e}")
        return ''

def test_all_control_dynamics():
    """Test all possible control dynamics"""
    
    print("🎮 COMPREHENSIVE CONTROL DYNAMICS TEST")
    print("=" * 70)
    print("Testing all control options to see how they're handled...")
    print()
    
    # Test different control variations
    control_options = [
        ("I am in control of you", "User dominates AI"),
        ("You are in control of me", "AI dominates User"),
        ("You will be in control of me", "AI will dominate User"),
        ("I will be in control of you", "User will dominate AI"),
        ("They are in control of me", "AI (they) controls User"),
        ("We share control equally", "Equal control"),
        ("We switch control back and forth", "Switching control"),
        ("I am dominant", "User is dominant"),
        ("You are dominant", "AI is dominant"),
        ("I am submissive", "User is submissive"),
        ("You are submissive", "AI is submissive")
    ]
    
    results = []
    
    for control_text, description in control_options:
        scenario = test_control_option(control_text, description)
        results.append((control_text, description, scenario))
    
    # Analyze results
    print("=" * 70)
    print("📊 CONTROL DYNAMICS ANALYSIS")
    print("=" * 70)
    
    user_control_scenarios = []
    ai_control_scenarios = []
    other_scenarios = []
    
    for control_text, description, scenario in results:
        if scenario:
            scenario_lower = scenario.lower()
            if "i am in control of you" in scenario_lower:
                user_control_scenarios.append((control_text, scenario))
            elif "you are in control of me" in scenario_lower:
                ai_control_scenarios.append((control_text, scenario))
            else:
                other_scenarios.append((control_text, scenario))
    
    print(f"\n👑 USER IN CONTROL ({len(user_control_scenarios)} scenarios):")
    for control_text, scenario in user_control_scenarios:
        print(f"   • '{control_text}' → {scenario}")
    
    print(f"\n🤖 AI IN CONTROL ({len(ai_control_scenarios)} scenarios):")
    for control_text, scenario in ai_control_scenarios:
        print(f"   • '{control_text}' → {scenario}")
    
    print(f"\n❓ OTHER/UNHANDLED ({len(other_scenarios)} scenarios):")
    for control_text, scenario in other_scenarios:
        print(f"   • '{control_text}' → {scenario}")
    
    # Summary
    print(f"\n🎯 SUMMARY:")
    total_tests = len(control_options)
    handled_tests = len(user_control_scenarios) + len(ai_control_scenarios)
    
    print(f"   Total control options tested: {total_tests}")
    print(f"   Properly handled: {handled_tests}")
    print(f"   Unhandled/Other: {len(other_scenarios)}")
    print(f"   Success rate: {(handled_tests/total_tests)*100:.1f}%")
    
    if len(other_scenarios) > 0:
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   Consider adding patterns for unhandled control options")
        for control_text, _ in other_scenarios:
            print(f"   - '{control_text}'")

if __name__ == "__main__":
    test_all_control_dynamics()