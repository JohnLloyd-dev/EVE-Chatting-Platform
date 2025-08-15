#!/usr/bin/env python3
"""
Test script to verify Tally extraction and AI server integration
"""

import json
import sys
import os

# Add backend to path
sys.path.append('backend')

from ai_tally_extractor import AITallyExtractor

def test_tally_extraction():
    """Test the Tally extraction with the sample data"""
    
    # Load the sample Tally data
    with open('Untitled-1.json', 'r') as f:
        tally_data = json.load(f)
    
    print("🧪 Testing Tally Extraction")
    print("=" * 50)
    
    # Create extractor instance with the tally data
    extractor = AITallyExtractor(tally_data)
    
    # Test data cleaning and structuring
    print("\n1. Testing data cleaning and structuring...")
    try:
        # The cleaned_data is already available from the constructor
        cleaned_data = extractor.cleaned_data
        print(f"✅ Data cleaned successfully")
        print(f"   Fields found: {len(cleaned_data.get('questions_and_answers', []))}")
        
        # Show some key fields
        questions = cleaned_data.get('questions_and_answers', [])
        for qa in questions[:5]:  # Show first 5 questions
            print(f"   - {qa.get('question', 'No question')}: {qa.get('answer', 'No answer')}")
            
    except Exception as e:
        print(f"❌ Data cleaning failed: {e}")
        return False
    
    # Test scenario generation
    print("\n2. Testing scenario generation...")
    try:
        # Use the standalone function
        from ai_tally_extractor import generate_ai_scenario
        scenario = generate_ai_scenario(tally_data)
        print(f"✅ Scenario generated successfully")
        print(f"   Scenario length: {len(scenario)} characters")
        print(f"   Scenario preview: {scenario[:200]}...")
        
        # Check if key elements are present
        key_elements = ['18 year old', 'public place', 'uniform', 'control', 'undress', 'orgasm']
        found_elements = []
        for element in key_elements:
            if element.lower() in scenario.lower():
                found_elements.append(element)
        
        print(f"   Key elements found: {len(found_elements)}/{len(key_elements)}")
        for element in found_elements:
            print(f"     ✅ {element}")
        for element in key_elements:
            if element not in found_elements:
                print(f"     ❌ {element}")
                
    except Exception as e:
        print(f"❌ Scenario generation failed: {e}")
        return False
    
    # Test AI prompt creation
    print("\n3. Testing AI prompt creation...")
    try:
        ai_prompt = extractor.create_ai_prompt()
        print(f"✅ AI prompt created successfully")
        print(f"   Prompt length: {len(ai_prompt)} characters")
        print(f"   Prompt preview: {ai_prompt[:200]}...")
        
    except Exception as e:
        print(f"❌ AI prompt creation failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Tally extraction is working correctly.")
    return True

def test_system_prompt_integration():
    """Test that the system prompt integrates correctly with the scenario"""
    
    print("\n🔗 Testing System Prompt Integration")
    print("=" * 50)
    
    # Load the sample Tally data
    with open('Untitled-1.json', 'r') as f:
        tally_data = json.load(f)
    
    # Create extractor and generate scenario
    extractor = AITallyExtractor(tally_data)
    from ai_tally_extractor import generate_ai_scenario
    scenario = generate_ai_scenario(tally_data)
    
    # Create the complete system prompt (like the backend does)
    base_prompt = """You are playing the role of a human in a live chat conversation. You are not an AI. You must act like a real person having a natural conversation in a specific scenario. Speak casually, like real people do — use contractions, slang, filler words, emojis, and emotional reactions when it fits. Be playful or serious depending on what's going on. Ask questions, show curiosity, react to what your friend says naturally. You should never break character or mention you're artificial. You are just a person living the moment."""
    
    complete_prompt = f"{base_prompt}\n\n**Scenario**:\n{scenario}"
    
    print(f"✅ Complete system prompt created")
    print(f"   Base prompt length: {len(base_prompt)} characters")
    print(f"   Scenario length: {len(scenario)} characters")
    print(f"   Total prompt length: {len(complete_prompt)} characters")
    
    # Check if the scenario is properly integrated
    if "**Scenario**:\n" in complete_prompt:
        print("   ✅ Scenario properly integrated with **Scenario**: marker")
    else:
        print("   ❌ Scenario not properly integrated")
        return False
    
    # Check if key scenario elements are preserved
    if "18 year old" in complete_prompt and "public place" in complete_prompt:
        print("   ✅ Key scenario elements preserved in final prompt")
    else:
        print("   ❌ Key scenario elements missing from final prompt")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 System prompt integration test passed!")
    return True

if __name__ == "__main__":
    print("🚀 Starting Tally Integration Tests")
    print("=" * 60)
    
    # Test 1: Tally extraction
    test1_passed = test_tally_extraction()
    
    # Test 2: System prompt integration
    test2_passed = test_system_prompt_integration()
    
    # Final results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Tally extraction is working correctly")
        print("✅ System prompt integration is working correctly")
        print("✅ AI server should now receive proper scenario details")
        print("\n🚀 Ready to test on VPS!")
    else:
        print("❌ SOME TESTS FAILED")
        if not test1_passed:
            print("   ❌ Tally extraction test failed")
        if not test2_passed:
            print("   ❌ System prompt integration test failed")
        print("\n🔧 Please check the errors above before testing on VPS")
    
    print("=" * 60) 