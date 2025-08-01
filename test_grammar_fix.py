#!/usr/bin/env python3
"""
Test the grammar fix function specifically
"""

import sys
sys.path.append('/home/dev/Work/eve/backend')

from ai_tally_extractor import TallyDataExtractor

def test_grammar_fix():
    """Test the grammar fix function"""
    
    print("🔧 TESTING GRAMMAR FIX FUNCTION")
    print("=" * 50)
    
    extractor = TallyDataExtractor()
    
    # Test problematic activities from real Tally data
    test_activities = [
        "Blindfold you",
        "Gag you", 
        "Take your against your willl",
        "Punish you",
        ["Blindfold you", "Gag you"],
        ["Take your against your willl", "Punish you"]
    ]
    
    for activity in test_activities:
        print(f"Input: {activity}")
        fixed = extractor.fix_broken_grammar(activity)
        print(f"Fixed: {fixed}")
        print()
    
    # Test the conversion functions
    print("🔄 TESTING CONVERSION FUNCTIONS")
    print("=" * 50)
    
    # Test with User Controls AI (should use reverse conversion)
    test_text = "blindfold you, gag you, take you against your will, punish you"
    print(f"Input: {test_text}")
    
    reverse_result = extractor.convert_to_present_continuous_reverse(test_text)
    print(f"Reverse (User controls AI): {reverse_result}")
    
    normal_result = extractor.convert_to_present_continuous(test_text)
    print(f"Normal (AI controls User): {normal_result}")
    
    mutual_result = extractor.convert_to_present_continuous_mutual(test_text)
    print(f"Mutual (Equal control): {mutual_result}")

if __name__ == "__main__":
    test_grammar_fix()