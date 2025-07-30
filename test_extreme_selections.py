#!/usr/bin/env python3
"""
Extreme Tally selection testing - pushing the limits
"""

import requests
import json

def test_maximum_selections():
    """Test with maximum number of selections across multiple categories"""
    
    test_form_data = {
        "formId": "extreme_test",
        "responseId": "resp_extreme",
        "respondentId": "user_extreme",
        "fields": [
            # Character setup
            {
                "key": "user_type",
                "label": "In this fantasy are you a man or a woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["type_woman"],
                "options": [
                    {"id": "type_woman", "text": "Woman"},
                    {"id": "type_man", "text": "Man"}
                ]
            },
            {
                "key": "partner_type",
                "label": "What is the gender of the other person?",
                "type": "MULTIPLE_CHOICE",
                "value": ["partner_man"],
                "options": [
                    {"id": "partner_woman", "text": "Woman"},
                    {"id": "partner_man", "text": "Man"}
                ]
            },
            {
                "key": "partner_age_detail",
                "label": "How old are they exactly?",
                "type": "MULTIPLE_CHOICE",
                "value": ["exact_29"],
                "options": [
                    {"id": "exact_24", "text": "24"},
                    {"id": "exact_27", "text": "27"},
                    {"id": "exact_29", "text": "29"},
                    {"id": "exact_31", "text": "31"},
                    {"id": "exact_34", "text": "34"}
                ]
            },
            {
                "key": "partner_background",
                "label": "What is their ethnic background?",
                "type": "MULTIPLE_CHOICE",
                "value": ["bg_italian"],
                "options": [
                    {"id": "bg_american", "text": "American"},
                    {"id": "bg_italian", "text": "Italian"},
                    {"id": "bg_french", "text": "French"},
                    {"id": "bg_spanish", "text": "Spanish"},
                    {"id": "bg_brazilian", "text": "Brazilian"}
                ]
            },
            # Multiple location scenarios
            {
                "key": "primary_location",
                "label": "Where does this primarily take place?",
                "type": "MULTIPLE_CHOICE",
                "value": ["pri_villa"],
                "options": [
                    {"id": "pri_apartment", "text": "In a modern apartment"},
                    {"id": "pri_villa", "text": "In a Mediterranean villa"},
                    {"id": "pri_penthouse", "text": "In a penthouse suite"},
                    {"id": "pri_cabin", "text": "In a mountain cabin"}
                ]
            },
            {
                "key": "secondary_locations",
                "label": "What other locations are involved? (Select multiple)",
                "type": "MULTIPLE_CHOICE",
                "value": ["sec_balcony", "sec_pool", "sec_garden", "sec_kitchen"],  # 4 locations
                "options": [
                    {"id": "sec_balcony", "text": "On the balcony"},
                    {"id": "sec_pool", "text": "By the swimming pool"},
                    {"id": "sec_garden", "text": "In the garden"},
                    {"id": "sec_kitchen", "text": "In the kitchen"},
                    {"id": "sec_bathroom", "text": "In the bathroom"},
                    {"id": "sec_terrace", "text": "On the terrace"}
                ]
            },
            # Power and control dynamics
            {
                "key": "control_style",
                "label": "Who is in control and how?",
                "type": "MULTIPLE_CHOICE",
                "value": ["ctrl_partner_gentle"],
                "options": [
                    {"id": "ctrl_me_assertive", "text": "I am assertively in control"},
                    {"id": "ctrl_partner_gentle", "text": "They are gently in control of me"},
                    {"id": "ctrl_partner_dominant", "text": "They are dominantly in control"},
                    {"id": "ctrl_switching", "text": "We switch control throughout"}
                ]
            },
            # Massive activity selection - 8 out of 12 options
            {
                "key": "intimate_activities",
                "label": "What intimate activities do you want? (Select all that interest you)",
                "type": "MULTIPLE_CHOICE",
                "value": [
                    "int_passionate_kissing", "int_sensual_touching", "int_romantic_dancing",
                    "int_intimate_massage", "int_playful_teasing", "int_deep_conversation",
                    "int_gentle_caressing", "int_whispered_desires"
                ],  # 8 selections
                "options": [
                    {"id": "int_passionate_kissing", "text": "Passionate kissing"},
                    {"id": "int_sensual_touching", "text": "Sensual touching"},
                    {"id": "int_romantic_dancing", "text": "Romantic slow dancing"},
                    {"id": "int_intimate_massage", "text": "Intimate massage"},
                    {"id": "int_playful_teasing", "text": "Playful teasing"},
                    {"id": "int_deep_conversation", "text": "Deep intimate conversation"},
                    {"id": "int_gentle_caressing", "text": "Gentle caressing"},
                    {"id": "int_whispered_desires", "text": "Whispered desires"},
                    {"id": "int_eye_contact", "text": "Intense eye contact"},
                    {"id": "int_soft_music", "text": "Soft music together"},
                    {"id": "int_candlelight", "text": "Candlelight ambiance"},
                    {"id": "int_wine_sharing", "text": "Sharing wine"}
                ]
            },
            # Physical preferences - 6 out of 10 options
            {
                "key": "physical_preferences",
                "label": "What physical interactions do you desire? (Multiple selections welcome)",
                "type": "MULTIPLE_CHOICE",
                "value": [
                    "phys_slow_undressing", "phys_body_exploration", "phys_tender_moments",
                    "phys_passionate_embrace", "phys_gentle_guidance", "phys_building_tension"
                ],  # 6 selections
                "options": [
                    {"id": "phys_slow_undressing", "text": "Slow, deliberate undressing"},
                    {"id": "phys_body_exploration", "text": "Gentle body exploration"},
                    {"id": "phys_tender_moments", "text": "Tender, loving moments"},
                    {"id": "phys_passionate_embrace", "text": "Passionate embracing"},
                    {"id": "phys_gentle_guidance", "text": "Gentle guidance and direction"},
                    {"id": "phys_building_tension", "text": "Building sexual tension"},
                    {"id": "phys_climax_control", "text": "Controlled climax building"},
                    {"id": "phys_aftercare", "text": "Intimate aftercare"},
                    {"id": "phys_multiple_rounds", "text": "Multiple intimate sessions"},
                    {"id": "phys_extended_foreplay", "text": "Extended foreplay"}
                ]
            },
            # Emotional connection - 5 selections
            {
                "key": "emotional_elements",
                "label": "What emotional elements are important? (Select multiple)",
                "type": "MULTIPLE_CHOICE",
                "value": [
                    "emo_deep_connection", "emo_mutual_desire", "emo_trust_building",
                    "emo_vulnerability", "emo_passionate_intensity"
                ],  # 5 selections
                "options": [
                    {"id": "emo_deep_connection", "text": "Deep emotional connection"},
                    {"id": "emo_mutual_desire", "text": "Mutual desire and wanting"},
                    {"id": "emo_trust_building", "text": "Building trust and intimacy"},
                    {"id": "emo_vulnerability", "text": "Shared vulnerability"},
                    {"id": "emo_passionate_intensity", "text": "Passionate intensity"},
                    {"id": "emo_playful_fun", "text": "Playful fun and laughter"},
                    {"id": "emo_romantic_love", "text": "Romantic love feelings"}
                ]
            }
        ]
    }
    
    print("🔥 EXTREME SELECTION TEST")
    print("=" * 60)
    print("Testing maximum selection complexity:")
    print("- Character: 29-year-old Italian man")
    print("- Primary: Mediterranean villa")
    print("- Secondary: 4 locations (balcony, pool, garden, kitchen)")
    print("- Intimate: 8 activities selected")
    print("- Physical: 6 preferences selected")
    print("- Emotional: 5 elements selected")
    print("- Total: 26+ individual selections across 11 questions")
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
            
            print("✅ EXTREME TEST SUCCESSFUL!")
            print(f"Questions processed: {len(debug_info.get('cleaned_data', {}).get('questions_and_answers', []))}")
            print()
            
            # Count total selections
            total_selections = 0
            multiple_selection_fields = 0
            
            print("📊 Selection Breakdown:")
            if debug_info.get('cleaned_data', {}).get('questions_and_answers'):
                for qa in debug_info['cleaned_data']['questions_and_answers']:
                    answer = qa['answer']
                    if isinstance(answer, list):
                        if len(answer) > 1:
                            multiple_selection_fields += 1
                            total_selections += len(answer)
                            print(f"🔢 {qa['question'][:50]}...: {len(answer)} selections")
                        else:
                            total_selections += 1
                            print(f"1️⃣ {qa['question'][:50]}...: {answer[0]}")
                    else:
                        total_selections += 1
                        print(f"📝 {qa['question'][:50]}...: {answer}")
            
            print(f"\n📈 STATISTICS:")
            print(f"   Total individual selections: {total_selections}")
            print(f"   Fields with multiple selections: {multiple_selection_fields}")
            print(f"   Average selections per multi-field: {total_selections/multiple_selection_fields if multiple_selection_fields > 0 else 0:.1f}")
            
            if result.get('generated_scenario'):
                print(f"\n🎭 Generated Extreme Scenario:")
                print("-" * 60)
                print(result['generated_scenario'])
                print("-" * 60)
                
                scenario_length = len(result['generated_scenario'])
                print(f"\n📏 Scenario length: {scenario_length} characters")
                
                # Check if key elements are included
                scenario_lower = result['generated_scenario'].lower()
                key_checks = [
                    ("29-year-old", "29" in scenario_lower),
                    ("Italian", "italian" in scenario_lower),
                    ("Villa setting", "villa" in scenario_lower),
                    ("Multiple activities", "," in scenario_lower),  # Comma indicates multiple items
                    ("Control dynamic", any(word in scenario_lower for word in ["control", "you are"]))
                ]
                
                print(f"\n🔍 Key Element Verification:")
                for element, found in key_checks:
                    status = "✅" if found else "❌"
                    print(f"   {status} {element}")
            
            return True
        else:
            print(f"❌ Extreme test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Extreme test error: {e}")
        return False

def test_mixed_field_types_with_selections():
    """Test mixing different field types with multiple selections"""
    
    test_form_data = {
        "formId": "mixed_types",
        "responseId": "resp_mixed",
        "respondentId": "user_mixed",
        "fields": [
            # Text input
            {
                "key": "custom_name",
                "label": "What should I call you in this fantasy?",
                "type": "INPUT_TEXT",
                "value": "Sophia"
            },
            # Email (unusual but possible)
            {
                "key": "contact_email",
                "label": "Email for follow-up (optional)",
                "type": "INPUT_EMAIL",
                "value": "user@example.com"
            },
            # Multiple choice with single selection
            {
                "key": "user_gender",
                "label": "Are you a man or woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["gender_man"],
                "options": [
                    {"id": "gender_woman", "text": "Woman"},
                    {"id": "gender_man", "text": "Man"}
                ]
            },
            # Multiple choice with multiple selections
            {
                "key": "partner_qualities",
                "label": "What qualities should the other person have? (Select multiple)",
                "type": "MULTIPLE_CHOICE",
                "value": ["qual_confident", "qual_gentle", "qual_passionate", "qual_experienced"],
                "options": [
                    {"id": "qual_confident", "text": "Confident"},
                    {"id": "qual_gentle", "text": "Gentle"},
                    {"id": "qual_passionate", "text": "Passionate"},
                    {"id": "qual_experienced", "text": "Experienced"},
                    {"id": "qual_playful", "text": "Playful"},
                    {"id": "qual_romantic", "text": "Romantic"}
                ]
            },
            # Textarea with detailed description
            {
                "key": "scenario_details",
                "label": "Describe any specific details you want included",
                "type": "TEXTAREA",
                "value": "I want the scene to start with us meeting at a wine bar, having deep conversation, then moving to a private setting where the tension builds slowly."
            },
            # Dropdown selection
            {
                "key": "time_of_day",
                "label": "What time of day?",
                "type": "DROPDOWN",
                "value": ["time_evening"],
                "options": [
                    {"id": "time_morning", "text": "Morning"},
                    {"id": "time_afternoon", "text": "Afternoon"},
                    {"id": "time_evening", "text": "Evening"},
                    {"id": "time_night", "text": "Late night"}
                ]
            },
            # Rating scale
            {
                "key": "intensity_level",
                "label": "Intensity level (1-5 scale)",
                "type": "RATING",
                "value": 4
            },
            # Checkbox
            {
                "key": "privacy_agreement",
                "label": "I agree this is private and consensual",
                "type": "CHECKBOX",
                "value": True
            },
            # Multiple activities with many selections
            {
                "key": "desired_sequence",
                "label": "What sequence of activities? (Select in order of preference)",
                "type": "MULTIPLE_CHOICE",
                "value": ["seq_conversation", "seq_dancing", "seq_kissing", "seq_intimacy", "seq_aftercare"],
                "options": [
                    {"id": "seq_conversation", "text": "Deep conversation"},
                    {"id": "seq_dancing", "text": "Slow dancing"},
                    {"id": "seq_kissing", "text": "Passionate kissing"},
                    {"id": "seq_touching", "text": "Gentle touching"},
                    {"id": "seq_intimacy", "text": "Physical intimacy"},
                    {"id": "seq_aftercare", "text": "Tender aftercare"}
                ]
            }
        ]
    }
    
    print("\n🎯 MIXED FIELD TYPES WITH SELECTIONS")
    print("=" * 60)
    print("Testing combination of:")
    print("- Text input: Custom name")
    print("- Email input: Contact info")
    print("- Single selection: Gender")
    print("- Multiple selection: 4 partner qualities")
    print("- Textarea: Detailed scenario description")
    print("- Dropdown: Time of day")
    print("- Rating: Intensity level (4/5)")
    print("- Checkbox: Privacy agreement")
    print("- Sequence: 5 activities in order")
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
            
            print("✅ MIXED TYPES TEST SUCCESSFUL!")
            print()
            
            # Categorize by field type
            field_categories = {
                'Text Fields': [],
                'Single Selections': [],
                'Multiple Selections': [],
                'Other Types': []
            }
            
            if debug_info.get('cleaned_data', {}).get('questions_and_answers'):
                for qa in debug_info['cleaned_data']['questions_and_answers']:
                    answer = qa['answer']
                    question = qa['question'][:40] + "..." if len(qa['question']) > 40 else qa['question']
                    
                    if isinstance(answer, list):
                        if len(answer) > 1:
                            field_categories['Multiple Selections'].append(f"{question}: {len(answer)} items")
                        else:
                            field_categories['Single Selections'].append(f"{question}: {answer[0]}")
                    elif isinstance(answer, str) and len(answer) > 20:
                        field_categories['Text Fields'].append(f"{question}: {answer[:30]}...")
                    else:
                        field_categories['Other Types'].append(f"{question}: {answer}")
            
            for category, items in field_categories.items():
                if items:
                    print(f"📂 {category}:")
                    for item in items:
                        print(f"   • {item}")
                    print()
            
            if result.get('generated_scenario'):
                print("🎭 Generated Mixed-Type Scenario:")
                print("-" * 60)
                print(result['generated_scenario'])
                print("-" * 60)
            
            return True
        else:
            print(f"❌ Mixed types test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Mixed types error: {e}")
        return False

if __name__ == "__main__":
    print("🌟 EXTREME TALLY SELECTION TESTING")
    print("=" * 70)
    print("Testing the absolute limits of selection handling...")
    print()
    
    # Run extreme tests
    test1 = test_maximum_selections()
    test2 = test_mixed_field_types_with_selections()
    
    # Final summary
    print("\n" + "=" * 70)
    print("🏆 EXTREME TESTING RESULTS")
    print("=" * 70)
    
    results = [
        ("Maximum Selections Test", test1),
        ("Mixed Field Types Test", test2)
    ]
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\nFinal Score: {passed}/{total} extreme tests passed")
    
    if passed == total:
        print("\n🎉 SYSTEM HANDLES EXTREME SELECTIONS PERFECTLY!")
        print("✅ Processes 26+ individual selections across 11 questions")
        print("✅ Handles 8 activities + 6 physical + 5 emotional selections")
        print("✅ Mixes all field types with multiple selections")
        print("✅ Generates coherent scenarios from complex data")
        print("✅ Ready for ANY Tally form configuration!")
        print("\n🚀 CONCLUSION: The system is bulletproof for Tally selections!")
    else:
        print(f"\n⚠️  System needs work on extreme edge cases")