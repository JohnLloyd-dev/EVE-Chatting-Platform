#!/usr/bin/env python3
"""
Test script for the fixed Tally extraction
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from ai_tally_extractor import generate_ai_scenario, debug_tally_data

# Current Tally form data from the logs
current_form_data = {
    "eventId": "ac6d9f96-9630-4fd5-927a-1b535bcafbe7",
    "eventType": "FORM_RESPONSE",
    "createdAt": "2025-08-15T02:34:17.567Z",
    "data": {
        "responseId": "WOpdMzQ",
        "submissionId": "WOpdMzQ",
        "respondentId": "4ebGvY",
        "formId": "mZXRPo",
        "formName": None,
        "createdAt": "2025-08-15T02:34:17.000Z",
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
                "value": ["546a5346-358a-4f83-835e-e085af434711"],
                "options": [
                    {"id": "331e6ff0-5ef4-4c0f-8116-22ec36c376de", "text": "A woman"},
                    {"id": "546a5346-358a-4f83-835e-e085af434711", "text": "A man"}
                ]
            },
            {
                "key": "question_d0YjNz",
                "label": "How old am I?",
                "type": "MULTIPLE_CHOICE",
                "value": ["da0a26d8-3351-4ed7-8fdc-89c6f77f5007"],
                "options": [
                    {"id": "da0a26d8-3351-4ed7-8fdc-89c6f77f5007", "text": "18"},
                    {"id": "59bddcb9-08b5-41b2-b4db-3ab7a693ca32", "text": "30"},
                    {"id": "54e81687-8c2c-49e9-975f-a284b6b59a93", "text": "50+"}
                ]
            },
            {
                "key": "question_YGZYRq",
                "label": "What is my ethnicity?",
                "type": "MULTIPLE_CHOICE",
                "value": ["c3f4a2b0-5944-457e-b705-f88f77da88fd"],
                "options": [
                    {"id": "c3f4a2b0-5944-457e-b705-f88f77da88fd", "text": "Black"},
                    {"id": "c68ed072-de43-4282-9f5f-6a81d5cd0197", "text": "White "},
                    {"id": "15cd9530-fde4-4285-8c3b-0867927475e7", "text": "Asian"},
                    {"id": "3781dd7a-831c-4d8e-9ce5-8b7dc9178591", "text": "Mixed"}
                ]
            },
            {
                "key": "question_JlLod7",
                "label": "Tell me what to wear (pick one):",
                "type": "MULTIPLE_CHOICE",
                "value": ["0da05f9e-21cb-426b-9e1d-046ca547415f"],
                "options": [
                    {"id": "0da05f9e-21cb-426b-9e1d-046ca547415f", "text": "A"},
                    {"id": "00833868-4bf5-4940-8c82-0e876a13fd47", "text": "B"},
                    {"id": "45e5e9a4-008a-44b3-b4b0-9169862c3cd9", "text": "C"},
                    {"id": "9e75ce79-5d15-4456-abd7-8a69ef86ced2", "text": "D"}
                ]
            },
            {
                "key": "question_DpVDKb",
                "label": "So, in this fantasy am I alone?",
                "type": "MULTIPLE_CHOICE",
                "value": ["99780e81-aa00-42f7-954a-f720aa2b0e04"],
                "options": [
                    {"id": "99780e81-aa00-42f7-954a-f720aa2b0e04", "text": "Yes"},
                    {"id": "19502d1b-d2f2-42bd-8cc6-58fbb12a6ca8", "text": "No - I am with another woman"},
                    {"id": "c32ab752-8c4d-4c10-be76-99c66e0370dd", "text": "No - I am with another man"},
                    {"id": "e7aede7b-0dca-46fd-b4c0-60be190099d9", "text": "No - I am in a group"}
                ]
            },
            {
                "key": "question_KxMXVD",
                "label": "Where does this take place?",
                "type": "MULTIPLE_CHOICE",
                "value": ["d63cb877-5b9d-432b-8f87-55f1356629f2"],
                "options": [
                    {"id": "d63cb877-5b9d-432b-8f87-55f1356629f2", "text": "In a public place"},
                    {"id": "a5761ab0-c92c-45a4-904a-efbd7c6fa616", "text": "In nature"},
                    {"id": "b7df93ff-8093-426a-b388-31cf40d26ae8", "text": "At home"},
                    {"id": "b2b1e617-fd65-4407-9040-7114a04420b2", "text": "In a dungeon "}
                ]
            },
            {
                "key": "question_LKd8PJ",
                "label": "Who is in control?",
                "type": "MULTIPLE_CHOICE",
                "value": ["5a52f4c1-1609-4f7f-9109-36542fb5489b"],
                "options": [
                    {"id": "5a52f4c1-1609-4f7f-9109-36542fb5489b", "text": "You will be in control of me"},
                    {"id": "558f8555-b45b-4132-830a-aeff564d6efd", "text": "I will be in control of you"},
                    {"id": "ca9a5283-d653-46ef-8a81-f9bbd1207cb4", "text": "We will be equals"}
                ]
            }
        ]
    }
}

def main():
    print("🧪 Testing Fixed Tally Extraction")
    print("=" * 50)
    
    # Test debug function first
    print("\n🔍 Debug Tally Data:")
    debug_result = debug_tally_data(current_form_data)
    print(f"Debug result: {debug_result}")
    
    # Test scenario generation
    print("\n🚀 Generating AI Scenario:")
    scenario = generate_ai_scenario(current_form_data)
    print(f"Generated scenario: '{scenario}'")
    print(f"Scenario length: {len(scenario)} characters")
    print(f"Is empty: {not scenario or not scenario.strip()}")

if __name__ == "__main__":
    main() 