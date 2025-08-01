#!/usr/bin/env python3
"""
Simple test of grammar fix logic
"""

def fix_single_activity_grammar(activity: str) -> str:
    """
    Fix grammar issues in a single activity string
    """
    # Common grammar fixes
    fixes = {
        'take your against your willl': 'take you against your will',
        'take your against your will': 'take you against your will',
        'punish you me': 'punish you',
        'blindfold you me': 'blindfold you',
        'gag you me': 'gag you',
        'your against your': 'you against your',
        'willl': 'will',
        'you me': 'you',
        'me you': 'you'
    }
    
    fixed_text = activity.lower().strip()
    
    # Apply specific fixes
    for broken, fixed in fixes.items():
        fixed_text = fixed_text.replace(broken, fixed)
    
    # Remove duplicate pronouns at the end
    if fixed_text.endswith(' me') and ' you' in fixed_text:
        # If it has both 'you' and ends with 'me', remove the 'me'
        if 'you' in fixed_text[:-3]:  # Check if 'you' appears before the final ' me'
            fixed_text = fixed_text[:-3].strip()
    
    return fixed_text

def test_grammar_fixes():
    """Test grammar fixes"""
    
    print("🔧 TESTING GRAMMAR FIXES")
    print("=" * 40)
    
    # Test cases from real Tally data
    test_cases = [
        "Blindfold you",
        "Gag you",
        "Take your against your willl",
        "Punish you",
        "blindfold you me",
        "gag you me", 
        "take your against your will me",
        "punish you me"
    ]
    
    for test in test_cases:
        fixed = fix_single_activity_grammar(test)
        print(f"'{test}' → '{fixed}'")
    
    print()
    print("🎯 EXPECTED RESULTS:")
    print("'Take your against your willl' → 'take you against your will'")
    print("'Punish you' → 'punish you'")
    print("'Blindfold you' → 'blindfold you'")
    print("'Gag you' → 'gag you'")

if __name__ == "__main__":
    test_grammar_fixes()