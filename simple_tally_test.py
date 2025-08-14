#!/usr/bin/env python3
"""
Simple test script to debug Tally extraction logic
"""

def test_extraction_logic():
    """Test the extraction logic directly"""
    
    # Sample data that should work - using EXACT questions from your form
    sample_data = {
        "questions_and_answers": [
            {
                "question": "In your fantasy, are you a man or a woman?",
                "answer": "man"
            },
            {
                "question": "What is the gender of the other person?",
                "answer": "man"
            },
            {
                "question": "How old is the other person?",
                "answer": "18"
            },
            {
                "question": "What is the ethnicity of the other person?",
                "answer": "black"
            },
            {
                "question": "Where does this take place?",
                "answer": "in a public place"
            },
            {
                "question": "Who is in control?",
                "answer": "you will be in control of me"
            },
            {
                "question": "Now, describe to me in detail what would you like me to do to you",
                "answer": "undress you slowly"
            },
            {
                "question": "What else?",
                "answer": "bring you close to orgasm then stopping"
            }
        ]
    }
    
    print("🧪 Testing Tally Extraction Logic")
    print("=" * 50)
    
    # Test the extraction logic step by step
    user_gender = ""
    ai_gender = ""
    ai_age = ""
    ai_ethnicity = ""
    location = ""
    control = ""
    activities = []
    
    for qa in sample_data['questions_and_answers']:
        question = qa['question'].lower()
        answer = qa['answer']
        
        print(f"🔍 Processing: {question}")
        print(f"   Answer: {answer}")
        
        # Map the actual questions from your Tally form
        if 'fantasy are you a man or a woman' in question or 'are you a man or woman' in question:
            user_gender = str(answer) if answer else ""
            print(f"   → user_gender = {user_gender}")
        elif 'gender of the other person' in question or 'other person' in question:
            ai_gender = str(answer) if answer else ""
            print(f"   → ai_gender = {ai_gender}")
        elif 'old' in question or 'age' in question:
            ai_age = str(answer) if answer else ""
            print(f"   → ai_age = {ai_age}")
        elif 'ethnicity' in question or 'race' in question:
            ai_ethnicity = str(answer) if answer else ""
            print(f"   → ai_ethnicity = {ai_ethnicity}")
        elif 'where' in question or 'take place' in question or 'location' in question:
            location = str(answer) if answer else ""
            print(f"   → location = {location}")
        elif 'who is in control' in question or 'control' in question:
            control = str(answer) if answer else ""
            print(f"   → control = {control}")
        elif 'describe to me in detail what would you like me to do to you' in question:
            if isinstance(answer, list):
                for activity in answer:
                    activities.append(activity)
            elif answer:
                activities.append(answer)
            print(f"   → activities = {activities}")
        elif 'what else' in question:
            if isinstance(answer, list):
                for activity in answer:
                    activities.append(activity)
            elif answer:
                activities.append(answer)
            print(f"   → activities = {activities}")
        else:
            print(f"   → NO MATCH!")
        
        print()
    
    print("📊 EXTRACTION RESULTS:")
    print(f"  user_gender: {user_gender}")
    print(f"  ai_gender: {ai_gender}")
    print(f"  ai_age: {ai_age}")
    print(f"  ai_ethnicity: {ai_ethnicity}")
    print(f"  location: {location}")
    print(f"  control: {control}")
    print(f"  activities: {activities}")
    
    # Build template
    template_parts = []
    
    # AI character setup
    if ai_gender and ai_age:
        if ai_ethnicity:
            template_parts.append(f"You are a {ai_age} year old {ai_ethnicity.lower()} {ai_gender.lower()}.")
        else:
            template_parts.append(f"You are a {ai_age} year old {ai_gender.lower()}.")
    elif ai_gender:
        template_parts.append(f"You are a {ai_gender.lower()}.")
    elif ai_age:
        template_parts.append(f"You are {ai_age} years old.")
    elif ai_ethnicity:
        template_parts.append(f"You are {ai_ethnicity.lower()}.")
    
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
    
    print("\n📝 TEMPLATE PARTS:")
    for i, part in enumerate(template_parts):
        print(f"  {i+1}. {part}")
    
    if template_parts:
        scenario_text = " ".join(template_parts)
        print(f"\n🎯 FINAL SCENARIO:")
        print(scenario_text)
    else:
        print("\n❌ No template parts generated!")

if __name__ == "__main__":
    test_extraction_logic() 