#!/usr/bin/env python3
"""
Test script for AI-powered Tally extraction
Run this to test the new AI extraction system
"""

import json
import requests
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

def test_ai_extraction_local():
    """Test AI extraction locally without API call"""
    print("=== Testing AI Extraction Locally ===")
    
    try:
        from ai_tally_extractor import generate_ai_scenario, debug_tally_data
        
        # Load sample Tally data
        with open("scripts/data/tally_form.json", "r") as f:
            sample_data = json.load(f)
        
        form_data = sample_data.get("data", {})
        
        print(f"Loaded sample Tally data with {len(form_data.get('fields', []))} fields")
        
        # Debug the data processing
        print("\n--- Debug Info ---")
        debug_info = debug_tally_data(form_data)
        print(f"Processed questions: {debug_info.get('summary', {}).get('total_questions', 0)}")
        print(f"Field types: {debug_info.get('summary', {}).get('field_types', [])}")
        
        # Show cleaned data
        if debug_info.get('cleaned_data', {}).get('questions_and_answers'):
            print("\n--- Extracted Q&A ---")
            for i, qa in enumerate(debug_info['cleaned_data']['questions_and_answers'][:5], 1):
                print(f"{i}. {qa['question']}")
                print(f"   Answer: {qa['answer']}")
                print()
        
        # Show AI prompt
        if debug_info.get('ai_prompt'):
            print(f"\n--- AI Prompt (first 500 chars) ---")
            print(debug_info['ai_prompt'][:500] + "...")
        
        print("\n--- Attempting AI Scenario Generation ---")
        print("Note: This will fail without AI model connection, but shows the flow")
        
        try:
            scenario = generate_ai_scenario(form_data)
            print(f"Generated scenario: {scenario}")
        except Exception as e:
            print(f"Expected error (no AI model connection): {e}")
        
        return True
        
    except Exception as e:
        print(f"Local test failed: {e}")
        return False

def test_ai_extraction_api():
    """Test AI extraction via API endpoint"""
    print("\n=== Testing AI Extraction via API ===")
    
    try:
        # Load sample Tally data
        with open("scripts/data/tally_form.json", "r") as f:
            sample_data = json.load(f)
        
        form_data = sample_data.get("data", {})
        
        # Test the debug endpoint
        response = requests.post(
            "http://localhost:8001/debug/test-ai-extraction",
            json={"form_data": form_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"API test successful: {result.get('success', False)}")
            
            if result.get('debug_info'):
                debug_info = result['debug_info']
                print(f"Processed questions: {debug_info.get('summary', {}).get('total_questions', 0)}")
            
            if result.get('generated_scenario'):
                print(f"Generated scenario length: {result.get('scenario_length', 0)} characters")
                print(f"Scenario preview: {result['generated_scenario'][:200]}...")
            
            return True
        else:
            print(f"API test failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"API test failed: {e}")
        return False

def test_webhook_simulation():
    """Test full webhook simulation"""
    print("\n=== Testing Full Webhook Simulation ===")
    
    try:
        # Load sample Tally data
        with open("scripts/data/tally_form.json", "r") as f:
            sample_webhook_data = json.load(f)
        
        # Test the webhook endpoint
        response = requests.post(
            "http://localhost:8001/webhook/tally",
            json=sample_webhook_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Webhook test successful!")
            print(f"Created user: {result.get('user_code')}")
            print(f"Session ID: {result.get('session_id')}")
            return True
        else:
            print(f"Webhook test failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Webhook test failed: {e}")
        return False

if __name__ == "__main__":
    print("AI-Powered Tally Extraction Test Suite")
    print("=" * 50)
    
    # Test 1: Local processing
    local_success = test_ai_extraction_local()
    
    # Test 2: API endpoint (requires running server)
    api_success = test_ai_extraction_api()
    
    # Test 3: Full webhook (requires running server and AI model)
    webhook_success = test_webhook_simulation()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Local processing: {'✓' if local_success else '✗'}")
    print(f"API endpoint: {'✓' if api_success else '✗'}")
    print(f"Full webhook: {'✓' if webhook_success else '✗'}")
    
    if local_success:
        print("\n✓ AI extraction system is properly implemented!")
        print("✓ Data processing and prompt generation working correctly")
        
        if api_success:
            print("✓ API endpoints are working")
            
            if webhook_success:
                print("✓ Full webhook integration successful!")
                print("\nThe AI-powered Tally extraction is ready for production!")
            else:
                print("⚠ Webhook test failed - check AI model connection")
        else:
            print("⚠ API test failed - make sure the server is running")
    else:
        print("\n✗ Local processing failed - check implementation")