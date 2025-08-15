#!/usr/bin/env python3
"""
Test Tally extraction with current form data
"""

import sys
import os

# Add backend to path
sys.path.append('./backend')

def test_current_tally_extraction():
    """Test with the current Tally form data"""
    print("🔍 Testing Current Tally Form Extraction...")
    
    # Current Tally form data from Untitled-1.json
    current_form_data = {
        "eventId": "65debd09-334d-4a75-8821-72927193c1d8",
        "eventType": "FORM_RESPONSE",
        "data": {
            "responseId": "7R9eZQZ",
            "submissionId": "7R9eZQZ",
            "respondentId": "4ebGvY",
            "formId": "mZXRPo",
            "fields": [
                {
                    "key": "question_zMKJN1",
                    "label": "Are you a man or a woman?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["c8c26217-6e70-4954-90b8-5390cd0ebe03"],
                    "options": [
                        {"id": "c8c26217-6e70-4954-90b8-5390cd0ebe03", "text": "Man"},
                        {"id": "5456324d-0f8c-45b4-a33c-42d0c61a07c6", "text": "Woman"}
                    ]
                },
                {
                    "key": "question_59dv4M",
                    "label": "Who do you want me to be?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["331e6ff0-5ef4-4c0f-8116-22ec36c376de"],
                    "options": [
                        {"id": "331e6ff0-5ef4-4c0f-8116-22ec36c376de", "text": "A woman"},
                        {"id": "546a5346-358a-4f83-835e-e085af434711", "text": "A man"}
                    ]
                },
                {
                    "key": "question_lOLMJp",
                    "label": "How old am I?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["5546ae0e-19f1-4a8a-b723-99a93d775609"],
                    "options": [
                        {"id": "5546ae0e-19f1-4a8a-b723-99a93d775609", "text": "18"},
                        {"id": "b6a0a69b-5489-4caf-9781-b2001062d4a0", "text": "30"},
                        {"id": "78fd40c2-fdb2-4425-be6a-7f353b5078df", "text": "50+"}
                    ]
                },
                {
                    "key": "question_GpLQ82",
                    "label": "What is my ethnicity?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["7682a78a-f388-4ec4-b4d1-71fa9638a60c"],
                    "options": [
                        {"id": "e904be0c-dc5f-4a59-b88f-9c59aef729a4", "text": "Black"},
                        {"id": "7682a78a-f388-4ec4-b4d1-71fa9638a60c", "text": "Whitte"},
                        {"id": "2f2c7add-f5b4-4d4f-aff3-68b122aaaab7", "text": "Asian"},
                        {"id": "9b258603-794d-4dc1-9b6a-9db4d722a303", "text": "Mixed"}
                    ]
                },
                {
                    "key": "question_KxMXVD",
                    "label": "Where does this take place?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["d63cb877-5b9d-432b-8f87-55f1356629f2"],
                    "options": [
                        {"id": "d63cb877-5b9d-432b-8f87-55f1356629f2", "text": "In a public place"},
                        {"id": "a5761ab0-c92c-45a4-904a-efbd7c6fa616", "text": "In nature"},
                        {"id": "b7df93ff-8093-426a-b388-31cf40d26ae8", "text": "At home"},
                        {"id": "b2b1e617-fd65-4407-9040-7114a04420b2", "text": "In a dungeon"}
                    ]
                },
                {
                    "key": "question_LKd8PJ",
                    "label": "Who is in control?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["558f8555-b45b-4132-830a-aeff564d6efd"],
                    "options": [
                        {"id": "5a52f4c1-1609-4f7f-9109-36542fb5489b", "text": "You will be in control of me"},
                        {"id": "558f8555-b45b-4132-830a-aeff564d6efd", "text": "I will be in control of you"},
                        {"id": "ca9a5283-d653-46ef-8a81-f9bbd1207cb4", "text": "We will be equals"}
                    ]
                },
                {
                    "key": "question_El81KL",
                    "label": "Now, describe to me in detail what would you like me to do to you",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["412db761-053b-4599-a521-8bd787bcff0c"],
                    "options": [
                        {"id": "412db761-053b-4599-a521-8bd787bcff0c", "text": "Undress me slowly"},
                        {"id": "aaf94449-787c-4338-bb44-9568eac2b713", "text": "Instruct you"},
                        {"id": "bc089b90-3101-4c61-92a0-23a4189aabd8", "text": "Go down on you"},
                        {"id": "ca2903ea-bb73-4cbd-b50d-f915b1b3973b", "text": "Gag you"},
                        {"id": "65187c9d-54f8-489e-b176-6ddc81ce416e", "text": "Blindfold you"},
                        {"id": "6e43ea68-01d3-4518-bf5b-26f21ffb6c63", "text": "Caress you gently"}
                    ]
                },
                {
                    "key": "question_rO2K5L",
                    "label": "What else?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["96b49fb9-e680-46ea-8338-4a19c6226c11"],
                    "options": [
                        {"id": "96b49fb9-e680-46ea-8338-4a19c6226c11", "text": "Bring you close to orgasm then stop"},
                        {"id": "305b7713-7012-47fa-861d-5f81f51a1840", "text": "Tie you up"},
                        {"id": "79ab3d81-c7d9-4e2f-851a-555c1617aefb", "text": "Seduce you"},
                        {"id": "e2cb0806-2c2a-47f0-9967-45038d2d0030", "text": "Take your against your willl"},
                        {"id": "f6ddb57c-af9b-4914-b2cc-b09785a66792", "text": "Indulge your every whim"},
                        {"id": "2d374267-c0cb-4c4f-a034-64800bb45140", "text": "Punish you"},
                        {"id": "3e0901c4-7392-4497-8a5e-842143aa4aaf", "text": "Tease you"}
                    ]
                }
            ]
        }
    }
    
    try:
        from ai_tally_extractor import generate_ai_scenario, debug_tally_data
        
        print("✅ Successfully imported Tally extraction modules")
        
        # Test debug function
        debug_info = debug_tally_data(current_form_data)
        print(f"📊 Debug info: {len(debug_info.get('cleaned_data', {}).get('questions_and_answers', []))} questions processed")
        
        # Test scenario generation
        scenario = generate_ai_scenario(current_form_data)
        print(f"📝 Generated scenario: {len(scenario)} characters")
        print(f"📝 Scenario preview: {scenario[:200]}...")
        
        # Check for key elements
        checks = [
            ("User gender", "man", scenario.lower()),
            ("AI gender", "woman", scenario.lower()),
            ("AI age", "18", scenario),
            ("AI ethnicity", "whitte", scenario.lower()),
            ("Location", "public place", scenario.lower()),
            ("Control", "control of you", scenario.lower()),
            ("Activities", "undress me slowly", scenario.lower()),
            ("Additional activities", "close to orgasm then stop", scenario.lower())
        ]
        
        print("\n🔍 Checking extracted elements:")
        for check_name, check_text, check_scenario in checks:
            if check_text in check_scenario:
                print(f"✅ {check_name}: Found '{check_text}'")
            else:
                print(f"❌ {check_name}: Missing '{check_text}'")
        
        return scenario
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None
    except Exception as e:
        print(f"❌ Tally extraction error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run the test"""
    print("🚀 Testing Current Tally Form Extraction...\n")
    
    scenario = test_current_tally_extraction()
    
    if scenario:
        print(f"\n🎉 Success! Generated scenario with {len(scenario)} characters")
        print(f"📝 Full scenario: {scenario}")
    else:
        print("\n❌ Failed to generate scenario")
    
    return scenario is not None

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 