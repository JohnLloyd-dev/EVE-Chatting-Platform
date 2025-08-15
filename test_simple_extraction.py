#!/usr/bin/env python3
"""
Simple test of Tally extraction logic with current form data
"""

def test_extraction_manually():
    """Test the extraction logic manually step by step"""
    print("🔍 Testing Tally Extraction Logic Manually...")
    
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
    
    print("📊 Testing with current form data structure...")
    
    # Simulate the process_field logic manually
    def process_field_manually(field):
        field_type = field.get('type', '')
        label = field.get('label', '').strip()
        raw_value = field.get('value')
        options = field.get('options', [])
        
        if not label or not raw_value:
            return None
        
        if field_type == 'MULTIPLE_CHOICE' and options:
            if isinstance(raw_value, list):
                selected_texts = []
                option_map = {opt['id']: opt['text'] for opt in options}
                
                for value_id in raw_value:
                    if value_id in option_map:
                        selected_texts.append(option_map[value_id])
                
                if selected_texts:
                    return {
                        'question': label,
                        'answer': selected_texts[0] if len(selected_texts) == 1 else selected_texts
                    }
        return None
    
    # Process each field manually
    print("\n🔍 Processing fields manually:")
    processed_fields = []
    
    for field in current_form_data['data']['fields']:
        processed = process_field_manually(field)
        if processed:
            processed_fields.append(processed)
            print(f"✅ {processed['question']} → {processed['answer']}")
        else:
            print(f"❌ Skipped: {field.get('label', '')}")
    
    print(f"\n📊 Total processed fields: {len(processed_fields)}")
    
    # Now test the extraction logic manually
    print("\n🔍 Testing extraction logic:")
    
    user_gender = None
    ai_gender = None
    ai_age = None
    ai_ethnicity = None
    location = None
    control = None
    activities = []
    
    for qa in processed_fields:
        question = qa['question'].lower()
        answer = qa['answer']
        
        print(f"\nQuestion: '{question}'")
        print(f"Answer: {answer}")
        
        # Test each condition
        if 'are you a man or a woman' in question:
            user_gender = str(answer) if answer else ""
            print(f"✅ MATCHES user gender: {user_gender}")
        elif 'who do you want me to be' in question:
            ai_gender = str(answer) if answer else ""
            print(f"✅ MATCHES ai gender: {ai_gender}")
        elif 'how old am i' in question:
            ai_age = str(answer) if answer else ""
            print(f"✅ MATCHES ai age: {ai_age}")
        elif 'what is my ethnicity' in question:
            ai_ethnicity = str(answer) if answer else ""
            print(f"✅ MATCHES ai ethnicity: {ai_ethnicity}")
        elif 'where does this take place' in question:
            location = str(answer) if answer else ""
            print(f"✅ MATCHES location: {location}")
        elif 'who is in control' in question:
            control = str(answer) if answer else ""
            print(f"✅ MATCHES control: {control}")
        elif 'describe to me in detail what would you like me to do to you' in question:
            if isinstance(answer, list):
                for activity in answer:
                    activities.append(activity)
            elif answer:
                activities.append(answer)
            print(f"✅ MATCHES activities: {activities}")
        elif 'what else' in question:
            if isinstance(answer, list):
                for activity in answer:
                    activities.append(activity)
            elif answer:
                activities.append(answer)
            print(f"✅ MATCHES additional activities: {activities}")
        else:
            print(f"❌ NO MATCH")
    
    # Build scenario manually
    print(f"\n🎯 Extracted values:")
    print(f"  User gender: {user_gender}")
    print(f"  AI gender: {ai_gender}")
    print(f"  AI age: {ai_age}")
    print(f"  AI ethnicity: {ai_ethnicity}")
    print(f"  Location: {location}")
    print(f"  Control: {control}")
    print(f"  Activities: {activities}")
    
    # Build template manually
    template_parts = []
    
    # AI character setup (the "other person" from the form)
    if ai_gender and ai_age and ai_ethnicity:
        # Handle "a woman" vs "a man" properly
        if ai_gender.lower().startswith('a '):
            template_parts.append(f"You are an {ai_age} year old {ai_ethnicity.lower()} {ai_gender.lower()[2:]}.")
        else:
            template_parts.append(f"You are an {ai_age} year old {ai_ethnicity.lower()} {ai_gender.lower()}.")
    elif ai_gender and ai_age:
        if ai_gender.lower().startswith('a '):
            template_parts.append(f"You are an {ai_age} year old {ai_gender.lower()[2:]}.")
        else:
            template_parts.append(f"You are an {ai_age} year old {ai_gender.lower()}.")
    elif ai_age and ai_ethnicity:
        template_parts.append(f"You are an {ai_age} year old {ai_ethnicity.lower()} person.")
    elif ai_gender and ai_ethnicity:
        if ai_gender.lower().startswith('a '):
            template_parts.append(f"You are a {ai_ethnicity.lower()} {ai_gender.lower()[2:]}.")
        else:
            template_parts.append(f"You are a {ai_ethnicity.lower()} {ai_gender.lower()}.")
    elif ai_gender:
        if ai_gender.lower().startswith('a '):
            template_parts.append(f"You are {ai_gender.lower()[2:]}.")
        else:
            template_parts.append(f"You are a {ai_gender.lower()}.")
    elif ai_age:
        template_parts.append(f"You are {ai_age} years old.")
    elif ai_ethnicity:
        template_parts.append(f"You are {ai_ethnicity.lower()}.")
    else:
        template_parts.append("You are a person.")
    
    # User and meeting context
    if user_gender and location:
        template_parts.append(f"I am a {user_gender.lower()} who meets you {location.lower()}.")
    elif user_gender:
        template_parts.append(f"I am a {user_gender.lower()}.")
    elif location:
        template_parts.append(f"We meet {location.lower()}.")
    
    # Control dynamic
    if control:
        if "you will be in control" in control.lower():
            template_parts.append("You are in control of me.")
        elif "i will be in control" in control.lower():
            template_parts.append("I am in control of you.")
        else:
            template_parts.append("We share control equally.")
    
    # Activities
    if activities:
        if len(activities) == 1:
            template_parts.append(f"I am {activities[0].lower()}.")
        elif len(activities) == 2:
            template_parts.append(f"I am {activities[0].lower()} and {activities[1].lower()}.")
        else:
            activity_text = ", ".join(activities[:-1]) + f" and {activities[-1]}"
            template_parts.append(f"I am {activity_text.lower()}.")
    
    # Final scenario
    scenario_text = " ".join(template_parts)
    
    print(f"\n📝 Generated scenario:")
    print(f"Length: {len(scenario_text)} characters")
    print(f"Scenario: {scenario_text}")
    
    return scenario_text

def main():
    """Run the test"""
    print("🚀 Testing Tally Extraction Logic Manually...\n")
    
    scenario = test_extraction_manually()
    
    if scenario:
        print(f"\n🎉 Success! Generated scenario with {len(scenario)} characters")
    else:
        print("\n❌ Failed to generate scenario")
    
    return scenario is not None

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 