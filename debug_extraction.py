#!/usr/bin/env python3
"""
Debug script to see what values are being extracted
"""

import json
import sys
sys.path.append('backend')

from ai_tally_extractor import AITallyExtractor

def main():
    # Load the Tally data
    with open('Untitled-1.json', 'r') as f:
        tally_data = json.load(f)
    
    # Create extractor
    extractor = AITallyExtractor(tally_data)
    
    print("🔍 DEBUGGING EXTRACTION")
    print("=" * 50)
    
    # Check what questions and answers we have
    print("Questions and answers:")
    for i, qa in enumerate(extractor.cleaned_data.get('questions_and_answers', [])):
        print(f"  {i+1}. Q: {qa['question']}")
        print(f"     A: {qa['answer']} (type: {type(qa['answer'])})")
        print()
    
    # Now let's manually check the specific fields
    print("🔍 MANUAL FIELD CHECK:")
    print("=" * 50)
    
    ai_gender = None
    ai_age = None
    ai_ethnicity = None
    
    for qa in extractor.cleaned_data.get('questions_and_answers', []):
        question = qa['question'].lower()
        answer = qa['answer']
        
        if 'who do you want me to be' in question:
            ai_gender = answer
            print(f"AI Gender: {answer} (type: {type(answer)})")
        elif 'how old am i' in question:
            ai_age = answer
            print(f"AI Age: {answer} (type: {type(answer)})")
        elif 'what is my ethnicity' in question:
            ai_ethnicity = answer
            print(f"AI Ethnicity: {answer} (type: {type(answer)})")
    
    print()
    print("🔍 CONDITION CHECK:")
    print("=" * 50)
    print(f"ai_gender: {ai_gender} (truthy: {bool(ai_gender)})")
    print(f"ai_age: {ai_age} (truthy: {bool(ai_age)})")
    print(f"ai_ethnicity: {ai_ethnicity} (truthy: {bool(ai_ethnicity)})")
    print(f"All three truthy: {bool(ai_gender and ai_age and ai_ethnicity)}")
    
    if ai_gender and ai_age and ai_ethnicity:
        print("✅ Condition met - should use the fixed logic")
        # Test the fix manually
        gender_str = ai_gender[0] if isinstance(ai_gender, list) else str(ai_gender)
        gender_text = gender_str.lower()[2:] if gender_str.lower().startswith('a ') else gender_str.lower()
        print(f"Manual fix result: gender='{ai_gender}' -> '{gender_text}'")
    else:
        print("❌ Condition not met - using fallback logic")

if __name__ == "__main__":
    main() 