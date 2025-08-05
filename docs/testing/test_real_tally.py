#!/usr/bin/env python3
"""
Test with real Tally form data
"""

import requests
import json

def test_with_real_tally_data():
    """Test with the actual Tally form data"""
    
    try:
        # Load the real Tally form data
        with open("scripts/data/tally_form.json", "r") as f:
            real_tally_data = json.load(f)
        
        form_data = real_tally_data.get("data", {})
        
        print("Testing with real Tally form data...")
        print(f"Form has {len(form_data.get('fields', []))} fields")
        
        # Show what answers are in the form
        print("\nAnswers found in form:")
        for field in form_data.get('fields', []):
            if field.get('value') and field.get('label'):
                label = field['label']
                value = field['value']
                
                if field.get('type') == 'MULTIPLE_CHOICE' and field.get('options'):
                    # Map option IDs to text
                    option_map = {opt['id']: opt['text'] for opt in field['options']}
                    if isinstance(value, list):
                        selected_texts = [option_map.get(v, v) for v in value]
                        print(f"- {label}: {', '.join(selected_texts)}")
                else:
                    print(f"- {label}: {value}")
        
        # Test the AI extraction
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": form_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ AI Extraction Successful!")
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
    print("Real Tally Data Test")
    print("=" * 30)
    
    success = test_with_real_tally_data()
    
    if success:
        print("\n🎉 Real Tally data processing successful!")
    else:
        print("\n❌ Test failed")