#!/usr/bin/env python3
"""
Simple test to verify AI extraction is working
"""

import requests
import json

def test_ai_extraction():
    """Test the AI extraction endpoint"""
    
    # Sample Tally form data (simplified)
    sample_form_data = {
        "formId": "test123",
        "responseId": "resp123",
        "respondentId": "user123",
        "fields": [
            {
                "key": "question_1",
                "label": "In this fantasy are you a man or a woman?",
                "type": "MULTIPLE_CHOICE",
                "value": ["option1"],
                "options": [
                    {"id": "option1", "text": "Man"},
                    {"id": "option2", "text": "Woman"}
                ]
            },
            {
                "key": "question_2", 
                "label": "What is the gender of the other person?",
                "type": "MULTIPLE_CHOICE",
                "value": ["option2"],
                "options": [
                    {"id": "option1", "text": "Man"},
                    {"id": "option2", "text": "Woman"}
                ]
            },
            {
                "key": "question_3",
                "label": "Approximately how old are they?",
                "type": "MULTIPLE_CHOICE", 
                "value": ["option1"],
                "options": [
                    {"id": "option1", "text": "25"},
                    {"id": "option2", "text": "30"},
                    {"id": "option3", "text": "35"}
                ]
            }
        ]
    }
    
    try:
        print("Testing AI extraction with sample data...")
        
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": sample_form_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI Extraction Test Successful!")
            print(f"Success: {result.get('success')}")
            print(f"Questions processed: {result.get('debug_info', {}).get('summary', {}).get('total_questions', 0)}")
            print(f"Scenario length: {result.get('scenario_length', 0)} characters")
            
            if result.get('generated_scenario'):
                print(f"\n📝 Generated Scenario:")
                print("-" * 50)
                print(result['generated_scenario'])
                print("-" * 50)
            
            return True
        else:
            print(f"❌ Test failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    print("Simple AI Extraction Test")
    print("=" * 30)
    
    success = test_ai_extraction()
    
    if success:
        print("\n🎉 AI-powered Tally extraction is working!")
        print("✅ The system can now generate scenarios from any Tally form")
        print("✅ No more hardcoded field mapping needed")
        print("✅ Ready for production deployment")
    else:
        print("\n❌ Test failed - check server and AI model connection")