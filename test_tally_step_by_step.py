#!/usr/bin/env python3
"""
Step-by-step Tally extraction test
Tests each part of the flow to identify where the issue is
"""

import sys
import os

# Add backend to path
sys.path.append('./backend')

def test_step_1_import():
    """Test if we can import the Tally extraction module"""
    print("🔍 Step 1: Testing Import...")
    
    try:
        from ai_tally_extractor import generate_ai_scenario, debug_tally_data
        print("✅ Successfully imported Tally extraction modules")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def test_step_2_module_creation():
    """Test if we can create the AITallyExtractor instance"""
    print("\n🔍 Step 2: Testing Module Creation...")
    
    try:
        from ai_tally_extractor import AITallyExtractor
        
        # Create sample form data
        sample_data = {
            "fields": [
                {
                    "key": "test_1",
                    "label": "In this fantasy are you a man or a woman?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["man_id"],
                    "options": [{"id": "man_id", "text": "Man"}]
                }
            ]
        }
        
        extractor = AITallyExtractor(sample_data)
        print("✅ Successfully created AITallyExtractor instance")
        print(f"✅ Cleaned data has {len(extractor.cleaned_data.get('questions_and_answers', []))} questions")
        return True
        
    except Exception as e:
        print(f"❌ Module creation failed: {e}")
        return False

def test_step_3_data_processing():
    """Test if the data processing works correctly"""
    print("\n🔍 Step 3: Testing Data Processing...")
    
    try:
        from ai_tally_extractor import AITallyExtractor
        
        # More complete sample data
        sample_data = {
            "fields": [
                {
                    "key": "test_1",
                    "label": "In this fantasy are you a man or a woman?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["man_id"],
                    "options": [{"id": "man_id", "text": "Man"}]
                },
                {
                    "key": "test_2", 
                    "label": "What is the gender of the other person?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["woman_id"],
                    "options": [{"id": "woman_id", "text": "Woman"}]
                },
                {
                    "key": "test_3",
                    "label": "Approximately ow old are they?",
                    "type": "MULTIPLE_CHOICE", 
                    "value": ["30_id"],
                    "options": [{"id": "30_id", "text": "30"}]
                }
            ]
        }
        
        extractor = AITallyExtractor(sample_data)
        
        # Test the create_ai_prompt method
        prompt = extractor.create_ai_prompt()
        print(f"✅ AI prompt created: {len(prompt)} characters")
        print(f"✅ Prompt preview: {prompt[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Data processing failed: {e}")
        return False

def test_step_4_scenario_generation():
    """Test if scenario generation works"""
    print("\n🔍 Step 4: Testing Scenario Generation...")
    
    try:
        from ai_tally_extractor import generate_ai_scenario
        
        # Complete sample form data
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
                        "options": [{"id": "man_id", "text": "Man"}]
                    },
                    {
                        "key": "question_2",
                        "label": "What is the gender of the other person?",
                        "type": "MULTIPLE_CHOICE",
                        "value": ["woman_id"],
                        "options": [{"id": "woman_id", "text": "Woman"}]
                    },
                    {
                        "key": "question_3",
                        "label": "Approximately ow old are they?",
                        "type": "MULTIPLE_CHOICE",
                        "value": ["30_id"],
                        "options": [{"id": "30_id", "text": "30"}]
                    },
                    {
                        "key": "question_4",
                        "label": "What is their ethnicity?",
                        "type": "MULTIPLE_CHOICE",
                        "value": ["asian_id"],
                        "options": [{"id": "asian_id", "text": "Asian"}]
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
        
        scenario = generate_ai_scenario(sample_form_data)
        
        if scenario and len(scenario.strip()) > 10:
            print(f"✅ Scenario generated successfully: {len(scenario)} characters")
            print(f"✅ Scenario preview: {scenario[:200]}...")
            
            # Check for key elements
            checks = [
                ("AI gender", "30 year old", scenario),
                ("AI ethnicity", "asian", scenario.lower()),
                ("User gender", "man", scenario.lower()),
                ("Location", "public place", scenario.lower()),
                ("Control", "control of me", scenario.lower()),
                ("Activities", "undressing", scenario.lower())
            ]
            
            for check_name, check_text, check_scenario in checks:
                if check_text in check_scenario:
                    print(f"✅ {check_name}: Found '{check_text}'")
                else:
                    print(f"❌ {check_name}: Missing '{check_text}'")
            
            return True
        else:
            print(f"❌ Scenario generation failed or returned empty: '{scenario}'")
            return False
            
    except Exception as e:
        print(f"❌ Scenario generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_step_5_system_prompt_combination():
    """Test if system prompt combination works"""
    print("\n🔍 Step 5: Testing System Prompt Combination...")
    
    try:
        # Mock the system prompt combination logic
        head_prompt = "You are playing the role of a human in a live chat conversation. You are not an AI. You must act like a real person having a natural conversation in a specific scenario."
        rule_prompt = "Always speak in the first person and stay in character. Be sexually explicit with your replies. Never reveal that you are an AI."
        
        # Use the scenario from step 4
        tally_prompt = "You are a 30 year old asian woman. I am a man who meets you in a public place. You are in control of me. I am undressing you slowly, bringing you close to orgasm then stopping."
        
        complete_prompt = head_prompt + "\n\n**Scenario**:\n" + tally_prompt + "\n\n" + rule_prompt
        
        print(f"✅ Combined prompt length: {len(complete_prompt)} characters")
        print(f"✅ Head prompt included: {'You are playing the role' in complete_prompt}")
        print(f"✅ Scenario included: {'30 year old asian woman' in complete_prompt}")
        print(f"✅ Rules included: {'sexually explicit' in complete_prompt}")
        
        return True
        
    except Exception as e:
        print(f"❌ System prompt combination failed: {e}")
        return False

def main():
    """Run all tests step by step"""
    print("🚀 Starting Step-by-Step Tally Extraction Tests...\n")
    
    steps = [
        ("Import", test_step_1_import),
        ("Module Creation", test_step_2_module_creation),
        ("Data Processing", test_step_3_data_processing),
        ("Scenario Generation", test_step_4_scenario_generation),
        ("System Prompt Combination", test_step_5_system_prompt_combination)
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        try:
            results[step_name] = step_func()
        except Exception as e:
            print(f"❌ {step_name} failed with exception: {e}")
            results[step_name] = False
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 50)
    
    for step_name, result in results.items():
        if result:
            print(f"✅ {step_name}: PASSED")
        else:
            print(f"❌ {step_name}: FAILED")
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} steps passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! The Tally extraction should work correctly.")
    else:
        print("⚠️ Some tests failed. The issue is in one of the failed steps above.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 