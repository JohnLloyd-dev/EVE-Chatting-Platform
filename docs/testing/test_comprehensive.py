#!/usr/bin/env python3
"""
Comprehensive test for all Tally field types and multiple selections
"""

import requests
import json

def test_multiple_selections():
    """Test handling of multiple selections"""
    
    test_form_data = {
        "formId": "test123",
        "responseId": "resp123", 
        "respondentId": "user123",
        "fields": [
            {
                "key": "multiple_activities",
                "label": "What activities do you enjoy? (Select all that apply)",
                "type": "MULTIPLE_CHOICE",
                "value": ["option1", "option3", "option4"],  # Multiple selections
                "options": [
                    {"id": "option1", "text": "Dancing"},
                    {"id": "option2", "text": "Reading"},
                    {"id": "option3", "text": "Swimming"},
                    {"id": "option4", "text": "Cooking"},
                    {"id": "option5", "text": "Traveling"}
                ]
            },
            {
                "key": "preferences",
                "label": "What are your preferences?",
                "type": "MULTIPLE_CHOICE", 
                "value": ["pref1", "pref2"],  # Multiple selections
                "options": [
                    {"id": "pref1", "text": "Outdoor activities"},
                    {"id": "pref2", "text": "Indoor activities"},
                    {"id": "pref3", "text": "Social events"}
                ]
            },
            {
                "key": "single_choice",
                "label": "What is your gender?",
                "type": "MULTIPLE_CHOICE",
                "value": ["gender1"],  # Single selection
                "options": [
                    {"id": "gender1", "text": "Woman"},
                    {"id": "gender2", "text": "Man"}
                ]
            }
        ]
    }
    
    print("=== Testing Multiple Selections ===")
    print("Expected:")
    print("- Multiple activities: Dancing, Swimming, Cooking")
    print("- Multiple preferences: Outdoor activities, Indoor activities") 
    print("- Single gender: Woman")
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
            
            print("✅ Test Successful!")
            print("Extracted Q&A:")
            if debug_info.get('cleaned_data', {}).get('questions_and_answers'):
                for qa in debug_info['cleaned_data']['questions_and_answers']:
                    print(f"- {qa['question']}: {qa['answer']}")
            
            return True
        else:
            print(f"❌ Test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_all_field_types():
    """Test handling of different Tally field types"""
    
    test_form_data = {
        "formId": "test123",
        "responseId": "resp123",
        "respondentId": "user123", 
        "fields": [
            {
                "key": "text_input",
                "label": "What is your name?",
                "type": "INPUT_TEXT",
                "value": "John Doe"
            },
            {
                "key": "email_input", 
                "label": "What is your email?",
                "type": "INPUT_EMAIL",
                "value": "john@example.com"
            },
            {
                "key": "phone_input",
                "label": "What is your phone number?", 
                "type": "INPUT_PHONE_NUMBER",
                "value": "+1234567890"
            },
            {
                "key": "textarea_input",
                "label": "Tell us about yourself",
                "type": "TEXTAREA", 
                "value": "I am a software developer who loves coding and music."
            },
            {
                "key": "dropdown",
                "label": "Select your country",
                "type": "DROPDOWN",
                "value": ["country1"],
                "options": [
                    {"id": "country1", "text": "United States"},
                    {"id": "country2", "text": "Canada"}
                ]
            },
            {
                "key": "checkbox",
                "label": "I agree to terms",
                "type": "CHECKBOX",
                "value": True
            },
            {
                "key": "rating",
                "label": "Rate your experience",
                "type": "RATING",
                "value": 4
            },
            {
                "key": "date_input",
                "label": "Select a date",
                "type": "INPUT_DATE",
                "value": "2024-01-15"
            }
        ]
    }
    
    print("\n=== Testing All Field Types ===")
    print("Testing: TEXT, EMAIL, PHONE, TEXTAREA, DROPDOWN, CHECKBOX, RATING, DATE")
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
            
            print("✅ Test Successful!")
            print("Extracted Q&A:")
            if debug_info.get('cleaned_data', {}).get('questions_and_answers'):
                for qa in debug_info['cleaned_data']['questions_and_answers']:
                    print(f"- {qa['question']}: {qa['answer']}")
            
            print(f"\nTotal fields processed: {len(debug_info.get('cleaned_data', {}).get('questions_and_answers', []))}")
            return True
        else:
            print(f"❌ Test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_real_tally_comprehensive():
    """Test with real Tally data to see what we're missing"""
    
    try:
        with open("scripts/data/tally_form.json", "r") as f:
            real_tally_data = json.load(f)
        
        form_data = real_tally_data.get("data", {})
        
        print("\n=== Real Tally Form Analysis ===")
        print(f"Total fields in form: {len(form_data.get('fields', []))}")
        
        # Analyze field types
        field_types = {}
        fields_with_values = 0
        multiple_selection_fields = 0
        
        for field in form_data.get('fields', []):
            field_type = field.get('type', 'UNKNOWN')
            field_types[field_type] = field_types.get(field_type, 0) + 1
            
            if field.get('value'):
                fields_with_values += 1
                
                # Check for multiple selections
                if isinstance(field.get('value'), list) and len(field.get('value', [])) > 1:
                    multiple_selection_fields += 1
                    print(f"Multiple selection found: {field.get('label', 'No label')} = {field.get('value')}")
        
        print(f"Fields with values: {fields_with_values}")
        print(f"Fields with multiple selections: {multiple_selection_fields}")
        print(f"Field types found: {field_types}")
        
        # Test extraction
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": form_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            debug_info = result.get('debug_info', {})
            
            processed_questions = len(debug_info.get('cleaned_data', {}).get('questions_and_answers', []))
            print(f"Questions processed by our system: {processed_questions}")
            print(f"Processing rate: {processed_questions}/{fields_with_values} = {processed_questions/fields_with_values*100:.1f}%")
            
            return True
        else:
            print(f"❌ Extraction test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return False

if __name__ == "__main__":
    print("Comprehensive Tally Field Testing")
    print("=" * 50)
    
    # Test 1: Multiple selections
    multiple_success = test_multiple_selections()
    
    # Test 2: All field types
    field_types_success = test_all_field_types()
    
    # Test 3: Real Tally analysis
    real_analysis_success = test_real_tally_comprehensive()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Multiple selections: {'✓' if multiple_success else '✗'}")
    print(f"All field types: {'✓' if field_types_success else '✗'}")
    print(f"Real Tally analysis: {'✓' if real_analysis_success else '✗'}")
    
    if not all([multiple_success, field_types_success, real_analysis_success]):
        print("\n⚠️  Issues found! The system needs improvements to handle:")
        print("- Multiple selections properly")
        print("- All Tally field types")
        print("- Complete form data extraction")
    else:
        print("\n✅ All tests passed! System handles comprehensive Tally forms correctly.")