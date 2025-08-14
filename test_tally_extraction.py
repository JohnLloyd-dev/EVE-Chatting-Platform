#!/usr/bin/env python3
"""
Simple test script to debug Tally extraction
"""

import json
import sys
import os

# Add backend to path
sys.path.append('backend')

from ai_tally_extractor import AITallyExtractor

def test_tally_extraction():
    """Test the tally extraction with sample data"""
    
    # Sample data that should work
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
    
    print("🧪 Testing Tally Extraction")
    print("=" * 50)
    
    # Create extractor
    extractor = AITallyExtractor()
    extractor.cleaned_data = sample_data
    
    print("📋 Sample Data:")
    for qa in sample_data['questions_and_answers']:
        print(f"  Q: {qa['question']}")
        print(f"  A: {qa['answer']}")
        print()
    
    print("🔍 Testing create_ai_prompt method...")
    try:
        result = extractor.create_ai_prompt()
        print("✅ SUCCESS!")
        print("📝 Result:")
        print(result)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🔍 Testing generate_scenario_with_ai method...")
    try:
        result = extractor.generate_scenario_with_ai()
        print("✅ SUCCESS!")
        print("📝 Result:")
        print(result)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tally_extraction() 