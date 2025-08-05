#!/usr/bin/env python3
"""
Test extraction from the real Tally JSON data provided
"""

import json
import requests

def analyze_real_tally_data():
    """Analyze the real Tally JSON data to see what we can extract"""
    
    print("🔍 ANALYZING REAL TALLY JSON DATA")
    print("=" * 70)
    
    # Load the real Tally data
    try:
        with open('/home/dev/Work/eve/tally_json.json', 'r') as f:
            tally_data = json.load(f)
    except FileNotFoundError:
        print("❌ tally_json.json file not found")
        return
    
    print("📊 TALLY FORM ANALYSIS:")
    print(f"   Event Type: {tally_data.get('eventType')}")
    print(f"   Form ID: {tally_data['data']['formId']}")
    print(f"   Response ID: {tally_data['data']['responseId']}")
    print(f"   Total Fields: {len(tally_data['data']['fields'])}")
    print()
    
    # Analyze each field
    print("📋 FIELD ANALYSIS:")
    print("-" * 50)
    
    answered_fields = []
    unanswered_fields = []
    
    for i, field in enumerate(tally_data['data']['fields'], 1):
        label = field.get('label', 'No label')
        value = field.get('value')
        has_answer = value is not None and value != []
        
        if has_answer:
            # Get the actual text value
            if isinstance(value, list) and len(value) > 0:
                option_id = value[0]
                # Find the matching option text
                option_text = "Unknown"
                for option in field.get('options', []):
                    if option['id'] == option_id:
                        option_text = option['text']
                        break
                answered_fields.append((label, option_text))
                print(f"   ✅ {i:2d}. {label}: {option_text}")
            else:
                answered_fields.append((label, str(value)))
                print(f"   ✅ {i:2d}. {label}: {value}")
        else:
            unanswered_fields.append(label)
            print(f"   ❌ {i:2d}. {label}: (No answer)")
    
    print()
    print("📊 EXTRACTION SUMMARY:")
    print(f"   ✅ Answered fields: {len(answered_fields)}")
    print(f"   ❌ Unanswered fields: {len(unanswered_fields)}")
    print()
    
    # Map to the 10 key data points
    print("🎯 MAPPING TO 10 KEY DATA POINTS:")
    print("-" * 50)
    
    key_mappings = {
        "1. My gender": None,
        "2. Your gender": None,
        "3. Your Age": None,
        "4. Your Race": None,
        "5. What you are wearing": None,
        "6. Who you are with": None,
        "7. Where are you?": None,
        "8. Who is dominant?": None,
        "9. What will I/you do?": None,
        "10. What else together?": None
    }
    
    for label, answer in answered_fields:
        label_lower = label.lower()
        
        if "fantasy are you a man or a woman" in label_lower:
            key_mappings["1. My gender"] = answer
        elif "gender of the other person" in label_lower:
            key_mappings["2. Your gender"] = answer
        elif "how old are they" in label_lower or "ow old are they" in label_lower:
            key_mappings["3. Your Age"] = answer
        elif "ethnicity" in label_lower:
            key_mappings["4. Your Race"] = answer
        elif "pick one" in label_lower:
            # These might be the A/B/C/D questions
            if not key_mappings["5. What you are wearing"]:
                key_mappings["5. What you are wearing"] = f"Option {answer}"
            elif not key_mappings["6. Who you are with"]:
                key_mappings["6. Who you are with"] = f"Option {answer}"
            elif not key_mappings["7. Where are you?"]:
                key_mappings["7. Where are you?"] = f"Option {answer}"
        elif "am i alone" in label_lower:
            key_mappings["6. Who you are with"] = f"Alone: {answer}"
        elif "where does this take place" in label_lower:
            key_mappings["7. Where are you?"] = answer
        elif "who is in control" in label_lower:
            key_mappings["8. Who is dominant?"] = answer
        elif "what would you like me to do" in label_lower or "describe to me in detail" in label_lower:
            key_mappings["9. What will I/you do?"] = answer
        elif ("what else" in label_lower or "anything else" in label_lower) and key_mappings["9. What will I/you do?"]:
            key_mappings["10. What else together?"] = answer
    
    for key, value in key_mappings.items():
        status = "✅" if value else "❌"
        print(f"   {status} {key}: {value or 'Not found'}")
    
    print()
    print("🔧 TESTING CURRENT EXTRACTION SYSTEM:")
    print("-" * 50)
    
    # Test with current system
    try:
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": tally_data['data']},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            scenario = result.get('generated_scenario', '')
            debug_info = result.get('debug_info', {})
            
            print(f"✅ Current System Result:")
            print(f"   Scenario: {scenario}")
            print(f"   Debug Info: {debug_info}")
            
            # Check what's missing
            print()
            print("🎯 WHAT'S MISSING FROM CURRENT EXTRACTION:")
            missing_elements = []
            
            if "uniform" not in scenario.lower() and "bondage" not in scenario.lower():
                missing_elements.append("Clothing/Wearing info")
            if "alone" not in scenario.lower() and "girlfriend" not in scenario.lower():
                missing_elements.append("Who you're with info")
            if "dungeon" not in scenario.lower() and "home" not in scenario.lower():
                missing_elements.append("Specific location details")
            
            for element in missing_elements:
                print(f"   ❌ Missing: {element}")
            
            if not missing_elements:
                print("   ✅ All key elements seem to be extracted!")
        
        else:
            print(f"❌ Current system test failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error testing current system: {e}")

if __name__ == "__main__":
    analyze_real_tally_data()