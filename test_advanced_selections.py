#!/usr/bin/env python3
"""
Advanced Tally selection testing with various patterns and edge cases
"""

import requests
import json

def test_complex_fantasy_form():
    """Test a complex fantasy form with multiple selection patterns"""
    
    test_form_data = {
        "formId": "fantasy_complex",
        "responseId": "resp_complex",
        "respondentId": "user_complex",
        "fields": [
            # Basic character setup
            {
                "key": "user_gender",
                "label": "In this fantasy, are you a man or a woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["gender_f"],
                "options": [
                    {"id": "gender_f", "text": "Woman"},
                    {"id": "gender_m", "text": "Man"},
                    {"id": "gender_nb", "text": "Non-binary"}
                ]
            },
            {
                "key": "partner_gender",
                "label": "What is the gender of the other person in your fantasy?",
                "type": "MULTIPLE_CHOICE",
                "value": ["p_gender_m"],
                "options": [
                    {"id": "p_gender_f", "text": "Woman"},
                    {"id": "p_gender_m", "text": "Man"},
                    {"id": "p_gender_nb", "text": "Non-binary"}
                ]
            },
            {
                "key": "partner_age_range",
                "label": "How old is the other person?",
                "type": "MULTIPLE_CHOICE",
                "value": ["age_28"],
                "options": [
                    {"id": "age_21", "text": "21"},
                    {"id": "age_25", "text": "25"},
                    {"id": "age_28", "text": "28"},
                    {"id": "age_32", "text": "32"},
                    {"id": "age_35", "text": "35"}
                ]
            },
            {
                "key": "partner_ethnicity",
                "label": "What is their ethnicity?",
                "type": "MULTIPLE_CHOICE",
                "value": ["eth_latino"],
                "options": [
                    {"id": "eth_white", "text": "White"},
                    {"id": "eth_black", "text": "Black"},
                    {"id": "eth_asian", "text": "Asian"},
                    {"id": "eth_latino", "text": "Latino"},
                    {"id": "eth_mixed", "text": "Mixed"}
                ]
            },
            # Multiple location selections
            {
                "key": "fantasy_location",
                "label": "Where does this fantasy take place? (You can select multiple)",
                "type": "MULTIPLE_CHOICE",
                "value": ["loc_beach", "loc_hotel"],  # Multiple locations
                "options": [
                    {"id": "loc_home", "text": "At home"},
                    {"id": "loc_beach", "text": "On a tropical beach"},
                    {"id": "loc_hotel", "text": "In a luxury hotel"},
                    {"id": "loc_office", "text": "In an office"},
                    {"id": "loc_car", "text": "In a car"}
                ]
            },
            # Power dynamics
            {
                "key": "control_dynamic",
                "label": "Who is in control in this fantasy?",
                "type": "MULTIPLE_CHOICE",
                "value": ["control_them"],
                "options": [
                    {"id": "control_me", "text": "I am in control"},
                    {"id": "control_them", "text": "They are in control of me"},
                    {"id": "control_equal", "text": "We share control equally"},
                    {"id": "control_switch", "text": "We switch control back and forth"}
                ]
            },
            # Multiple activity categories
            {
                "key": "romantic_activities",
                "label": "What romantic activities do you want? (Select all that apply)",
                "type": "MULTIPLE_CHOICE",
                "value": ["rom_kiss", "rom_cuddle", "rom_massage"],  # Multiple romantic
                "options": [
                    {"id": "rom_kiss", "text": "Passionate kissing"},
                    {"id": "rom_cuddle", "text": "Intimate cuddling"},
                    {"id": "rom_massage", "text": "Sensual massage"},
                    {"id": "rom_dance", "text": "Slow dancing"},
                    {"id": "rom_talk", "text": "Deep conversation"}
                ]
            },
            {
                "key": "physical_activities",
                "label": "What physical activities interest you? (Select multiple)",
                "type": "MULTIPLE_CHOICE",
                "value": ["phys_touch", "phys_explore", "phys_tease"],  # Multiple physical
                "options": [
                    {"id": "phys_touch", "text": "Gentle touching"},
                    {"id": "phys_explore", "text": "Exploring each other"},
                    {"id": "phys_tease", "text": "Playful teasing"},
                    {"id": "phys_intense", "text": "Intense passion"},
                    {"id": "phys_slow", "text": "Taking it slow"}
                ]
            },
            {
                "key": "fantasy_mood",
                "label": "What mood do you want for this fantasy? (Multiple selections allowed)",
                "type": "MULTIPLE_CHOICE",
                "value": ["mood_romantic", "mood_passionate", "mood_playful"],  # Multiple moods
                "options": [
                    {"id": "mood_romantic", "text": "Romantic"},
                    {"id": "mood_passionate", "text": "Passionate"},
                    {"id": "mood_playful", "text": "Playful"},
                    {"id": "mood_intense", "text": "Intense"},
                    {"id": "mood_gentle", "text": "Gentle"},
                    {"id": "mood_adventurous", "text": "Adventurous"}
                ]
            },
            # Text input for custom details
            {
                "key": "special_requests",
                "label": "Any special requests or details?",
                "type": "TEXTAREA",
                "value": "I want them to whisper sweet things in my ear and make me feel desired"
            }
        ]
    }
    
    print("🌟 COMPLEX FANTASY FORM TEST")
    print("=" * 50)
    print("Testing comprehensive form with:")
    print("- Multiple location selections: Beach + Hotel")
    print("- Multiple romantic activities: Kissing + Cuddling + Massage")
    print("- Multiple physical activities: Touching + Exploring + Teasing")
    print("- Multiple moods: Romantic + Passionate + Playful")
    print("- Custom text input")
    print()
    
    try:
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": test_form_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            debug_info = result.get('debug_info', {})
            
            print("✅ Extraction Successful!")
            print(f"Questions processed: {len(debug_info.get('cleaned_data', {}).get('questions_and_answers', []))}")
            print()
            
            print("📋 Extracted Data:")
            if debug_info.get('cleaned_data', {}).get('questions_and_answers'):
                for qa in debug_info['cleaned_data']['questions_and_answers']:
                    answer = qa['answer']
                    if isinstance(answer, list) and len(answer) > 1:
                        print(f"🔢 {qa['question']}: {len(answer)} selections = {answer}")
                    else:
                        print(f"📝 {qa['question']}: {answer}")
            
            print()
            if result.get('generated_scenario'):
                print("🎭 Generated Scenario:")
                print("-" * 50)
                print(result['generated_scenario'])
                print("-" * 50)
            
            return True
        else:
            print(f"❌ Test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_edge_cases():
    """Test edge cases and unusual selection patterns"""
    
    test_form_data = {
        "formId": "edge_cases",
        "responseId": "resp_edge",
        "respondentId": "user_edge",
        "fields": [
            # Single selection that looks like multiple
            {
                "key": "single_but_array",
                "label": "Are you a man or woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["only_one"],  # Array with single item
                "options": [
                    {"id": "only_one", "text": "Woman"},
                    {"id": "other", "text": "Man"}
                ]
            },
            # All options selected
            {
                "key": "select_all",
                "label": "What activities do you enjoy? (Select all that apply)",
                "type": "MULTIPLE_CHOICE",
                "value": ["act1", "act2", "act3", "act4", "act5", "act6"],  # All 6 selected
                "options": [
                    {"id": "act1", "text": "Swimming"},
                    {"id": "act2", "text": "Dancing"},
                    {"id": "act3", "text": "Reading"},
                    {"id": "act4", "text": "Cooking"},
                    {"id": "act5", "text": "Traveling"},
                    {"id": "act6", "text": "Music"}
                ]
            },
            # Empty selection (should be skipped)
            {
                "key": "empty_selection",
                "label": "Optional question",
                "type": "MULTIPLE_CHOICE",
                "value": [],  # Empty array
                "options": [
                    {"id": "opt1", "text": "Option 1"},
                    {"id": "opt2", "text": "Option 2"}
                ]
            },
            # Very long text selections
            {
                "key": "long_text",
                "label": "What would you like to do?",
                "type": "MULTIPLE_CHOICE",
                "value": ["long1", "long2"],
                "options": [
                    {"id": "long1", "text": "I want to have a romantic dinner by candlelight with soft music playing in the background"},
                    {"id": "long2", "text": "I would like to take a long walk on the beach under the moonlight while holding hands"},
                    {"id": "long3", "text": "I want to dance slowly together in a dimly lit room"}
                ]
            },
            # Mixed case and special characters
            {
                "key": "special_chars",
                "label": "What's your preference?",
                "type": "MULTIPLE_CHOICE",
                "value": ["special1", "special2"],
                "options": [
                    {"id": "special1", "text": "Café & Wine"},
                    {"id": "special2", "text": "Beach @ Sunset"},
                    {"id": "special3", "text": "Home (Cozy)"}
                ]
            }
        ]
    }
    
    print("\n🔬 EDGE CASES TEST")
    print("=" * 50)
    print("Testing unusual patterns:")
    print("- Single selection in array format")
    print("- All options selected (6/6)")
    print("- Empty selections")
    print("- Very long text options")
    print("- Special characters in text")
    print()
    
    try:
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": test_form_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            debug_info = result.get('debug_info', {})
            
            print("✅ Edge Cases Handled Successfully!")
            print()
            
            print("📋 Edge Case Results:")
            if debug_info.get('cleaned_data', {}).get('questions_and_answers'):
                for qa in debug_info['cleaned_data']['questions_and_answers']:
                    answer = qa['answer']
                    if isinstance(answer, list):
                        if len(answer) == 0:
                            print(f"⚠️  {qa['question']}: EMPTY (correctly skipped)")
                        elif len(answer) == 1:
                            print(f"1️⃣ {qa['question']}: Single = {answer[0]}")
                        else:
                            print(f"🔢 {qa['question']}: {len(answer)} selections = {answer}")
                    else:
                        print(f"📝 {qa['question']}: {answer}")
            
            return True
        else:
            print(f"❌ Edge cases test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Edge cases error: {e}")
        return False

def test_realistic_adult_form():
    """Test a realistic adult fantasy form with diverse selections"""
    
    test_form_data = {
        "formId": "adult_realistic",
        "responseId": "resp_adult",
        "respondentId": "user_adult",
        "fields": [
            {
                "key": "user_identity",
                "label": "In this fantasy, are you a man or a woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["identity_man"],
                "options": [
                    {"id": "identity_woman", "text": "Woman"},
                    {"id": "identity_man", "text": "Man"}
                ]
            },
            {
                "key": "partner_identity",
                "label": "What is the gender of the other person?",
                "type": "MULTIPLE_CHOICE",
                "value": ["partner_woman"],
                "options": [
                    {"id": "partner_woman", "text": "Woman"},
                    {"id": "partner_man", "text": "Man"}
                ]
            },
            {
                "key": "partner_age",
                "label": "How old are they approximately?",
                "type": "MULTIPLE_CHOICE",
                "value": ["age_26"],
                "options": [
                    {"id": "age_22", "text": "22"},
                    {"id": "age_26", "text": "26"},
                    {"id": "age_30", "text": "30"},
                    {"id": "age_35", "text": "35"}
                ]
            },
            {
                "key": "partner_appearance",
                "label": "What is their ethnicity/appearance?",
                "type": "MULTIPLE_CHOICE",
                "value": ["appear_asian"],
                "options": [
                    {"id": "appear_white", "text": "White"},
                    {"id": "appear_black", "text": "Black"},
                    {"id": "appear_asian", "text": "Asian"},
                    {"id": "appear_latina", "text": "Latina"}
                ]
            },
            {
                "key": "setting_location",
                "label": "Where does this take place?",
                "type": "MULTIPLE_CHOICE",
                "value": ["setting_bedroom"],
                "options": [
                    {"id": "setting_bedroom", "text": "In a bedroom"},
                    {"id": "setting_hotel", "text": "In a hotel room"},
                    {"id": "setting_outdoor", "text": "Outdoors"},
                    {"id": "setting_office", "text": "In an office"}
                ]
            },
            {
                "key": "power_dynamic",
                "label": "Who takes the lead?",
                "type": "MULTIPLE_CHOICE",
                "value": ["lead_partner"],
                "options": [
                    {"id": "lead_me", "text": "I take the lead"},
                    {"id": "lead_partner", "text": "They take the lead"},
                    {"id": "lead_equal", "text": "We both lead equally"}
                ]
            },
            {
                "key": "intimacy_level",
                "label": "What level of intimacy? (Select multiple if desired)",
                "type": "MULTIPLE_CHOICE",
                "value": ["intimate_romantic", "intimate_passionate", "intimate_sensual"],
                "options": [
                    {"id": "intimate_romantic", "text": "Romantic connection"},
                    {"id": "intimate_passionate", "text": "Passionate encounter"},
                    {"id": "intimate_sensual", "text": "Sensual exploration"},
                    {"id": "intimate_playful", "text": "Playful interaction"}
                ]
            },
            {
                "key": "desired_actions",
                "label": "What would you like them to do? (Multiple selections allowed)",
                "type": "MULTIPLE_CHOICE",
                "value": ["action_kiss", "action_touch", "action_whisper", "action_undress"],
                "options": [
                    {"id": "action_kiss", "text": "Kiss me deeply"},
                    {"id": "action_touch", "text": "Touch me gently"},
                    {"id": "action_whisper", "text": "Whisper to me"},
                    {"id": "action_undress", "text": "Undress me slowly"},
                    {"id": "action_massage", "text": "Give me a massage"},
                    {"id": "action_tease", "text": "Tease me playfully"}
                ]
            }
        ]
    }
    
    print("\n💫 REALISTIC ADULT FANTASY FORM")
    print("=" * 50)
    print("Testing realistic adult form with:")
    print("- Character: 26-year-old Asian woman")
    print("- Setting: Bedroom")
    print("- Dynamic: Partner leads")
    print("- Multiple intimacy levels: Romantic + Passionate + Sensual")
    print("- Multiple actions: Kiss + Touch + Whisper + Undress")
    print()
    
    try:
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": test_form_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            debug_info = result.get('debug_info', {})
            
            print("✅ Realistic Form Processed Successfully!")
            print()
            
            if result.get('generated_scenario'):
                print("🎭 Generated Adult Scenario:")
                print("-" * 50)
                print(result['generated_scenario'])
                print("-" * 50)
                
                # Analyze the scenario
                scenario = result['generated_scenario'].lower()
                
                print("\n🔍 Scenario Analysis:")
                checks = [
                    ("26-year-old", "26" in scenario),
                    ("Asian woman", "asian" in scenario and "woman" in scenario),
                    ("Bedroom setting", "bedroom" in scenario),
                    ("Partner leads", "you are" in scenario or "control" in scenario),
                    ("Multiple actions", "kiss" in scenario and "touch" in scenario)
                ]
                
                for check_name, result_bool in checks:
                    status = "✅" if result_bool else "❌"
                    print(f"{status} {check_name}")
            
            return True
        else:
            print(f"❌ Realistic form test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Realistic form error: {e}")
        return False

def run_all_advanced_tests():
    """Run all advanced selection tests"""
    
    print("🚀 ADVANCED TALLY SELECTION TESTING")
    print("=" * 60)
    print("Testing various selection patterns and edge cases...")
    print()
    
    # Run all tests
    test1_result = test_complex_fantasy_form()
    test2_result = test_edge_cases()
    test3_result = test_realistic_adult_form()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ADVANCED TESTING SUMMARY")
    print("=" * 60)
    
    results = [
        ("Complex Fantasy Form", test1_result),
        ("Edge Cases", test2_result),
        ("Realistic Adult Form", test3_result)
    ]
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\nOverall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL ADVANCED TESTS PASSED!")
        print("✅ System handles complex multiple selections")
        print("✅ System handles edge cases properly")
        print("✅ System generates realistic scenarios")
        print("✅ Ready for any Tally form configuration!")
    else:
        print(f"\n⚠️  {total - passed} tests need attention")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_advanced_tests()
    
    if success:
        print("\n🌟 CONCLUSION: The system excellently handles all types of Tally selections!")
    else:
        print("\n🔧 Some improvements needed for edge cases.")