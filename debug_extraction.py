#!/usr/bin/env python3
"""
Debug the extraction process
"""

import requests
import json

def debug_extraction():
    """Debug what's being extracted from the real Tally data"""
    
    try:
        # Load the real Tally form data
        with open("scripts/data/tally_form.json", "r") as f:
            real_tally_data = json.load(f)
        
        form_data = real_tally_data.get("data", {})
        
        # Test the debug endpoint
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": form_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            debug_info = result.get('debug_info', {})
            
            print("=== Extracted Questions and Answers ===")
            if debug_info.get('cleaned_data', {}).get('questions_and_answers'):
                for i, qa in enumerate(debug_info['cleaned_data']['questions_and_answers'], 1):
                    print(f"{i}. Q: {qa['question']}")
                    print(f"   A: {qa['answer']}")
                    print()
            
            print("=== AI Prompt ===")
            if debug_info.get('ai_prompt'):
                print(debug_info['ai_prompt'])
            
            return True
        else:
            print(f"❌ Test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Debug error: {e}")
        return False

if __name__ == "__main__":
    debug_extraction()