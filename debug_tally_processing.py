#!/usr/bin/env python3
"""
Debug Tally data processing to see exactly what's happening
"""

import sys
import os

# Add backend to path
sys.path.append('./backend')

def debug_tally_processing():
    """Debug the Tally data processing step by step"""
    print("🔍 Debugging Tally Data Processing...")
    
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
                }
            ]
        }
    }
    
    try:
        from ai_tally_extractor import AITallyExtractor
        
        print("✅ Successfully imported AITallyExtractor")
        
        # Create extractor
        extractor = AITallyExtractor(current_form_data)
        
        print(f"\n📊 Raw cleaned data:")
        print(f"Number of questions: {len(extractor.cleaned_data.get('questions_and_answers', []))}")
        
        # Show each question and answer
        for i, qa in enumerate(extractor.cleaned_data.get('questions_and_answers', [])):
            print(f"\nQ{i+1}: '{qa.get('question', '')}'")
            print(f"  Answer: {qa.get('answer', '')}")
            print(f"  Answer type: {type(qa.get('answer', '')).__name__}")
            if isinstance(qa.get('answer', ''), list):
                print(f"  Answer list items: {[type(item).__name__ for item in qa.get('answer', [])]}")
        
        # Test the specific question matching
        print(f"\n🔍 Testing question matching:")
        
        for qa in extractor.cleaned_data.get('questions_and_answers', []):
            question = qa['question'].lower()
            answer = qa['answer']
            
            print(f"\nQuestion: '{question}'")
            print(f"Answer: {answer}")
            
            # Test each condition
            if 'are you a man or a woman' in question:
                print(f"✅ MATCHES user gender: {answer}")
            elif 'who do you want me to be' in question:
                print(f"✅ MATCHES ai gender: {answer}")
            elif 'how old am i' in question:
                print(f"✅ MATCHES ai age: {answer}")
            elif 'what is my ethnicity' in question:
                print(f"✅ MATCHES ai ethnicity: {answer}")
            else:
                print(f"❌ NO MATCH")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the debug"""
    print("🚀 Debugging Tally Processing...\n")
    
    success = debug_tally_processing()
    
    if success:
        print("\n🎉 Debug completed successfully!")
    else:
        print("\n❌ Debug failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 