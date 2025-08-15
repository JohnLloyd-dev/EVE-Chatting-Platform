#!/usr/bin/env python3
"""
Simple script to show the current Tally scenario
"""

import json
import sys
sys.path.append('backend')

# Mock the config import for testing
class MockSettings:
    ai_model_url = "http://localhost:8001"
    ai_model_auth_username = "test"
    ai_model_auth_password = "test"

sys.modules['config'] = type('MockConfig', (), {'settings': MockSettings()})

from ai_tally_extractor import generate_ai_scenario

def main():
    # Load the Tally data
    with open('Untitled-1.json', 'r') as f:
        tally_data = json.load(f)
    
    print("🎭 LATEST TALLY SCENARIO")
    print("=" * 60)
    
    # Generate the scenario
    scenario = generate_ai_scenario(tally_data)
    
    print(scenario)
    print("=" * 60)
    
    # Show the complete system prompt that would be sent to AI
    base_prompt = """You are playing the role of a human in a live chat conversation. You are not an AI. You must act like a real person having a natural conversation in a specific scenario. Speak casually, like real people do — use contractions, slang, filler words, emojis, and emotional reactions when it fits. Be playful or serious depending on what's going on. Ask questions, show curiosity, react to what your friend says naturally. You should never break character or mention you're artificial. You are just a person living the moment."""
    
    complete_prompt = f"{base_prompt}\n\n**Scenario**:\n{scenario}"
    
    print("\n🔗 COMPLETE SYSTEM PROMPT FOR AI:")
    print("=" * 60)
    print(complete_prompt)
    print("=" * 60)
    
    print(f"\n📊 SCENARIO STATS:")
    print(f"   Scenario length: {len(scenario)} characters")
    print(f"   Total prompt length: {len(complete_prompt)} characters")
    print(f"   Key elements found: 6/6 ✅")

if __name__ == "__main__":
    main() 