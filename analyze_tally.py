#!/usr/bin/env python3
"""
Analyze Tally form data and show the extracted scenario
"""

import json

def analyze_tally_data():
    # Load the Tally data
    with open('Untitled-1.json', 'r') as f:
        data = json.load(f)
    
    print("📋 TALLY FORM ANALYSIS")
    print("=" * 60)
    
    # Extract the fields
    fields = data['data']['fields']
    
    # Find fields with actual values (not null)
    answered_fields = []
    for field in fields:
        if field.get('value') is not None:
            answered_fields.append({
                'label': field['label'].strip(),
                'value': field['value'],
                'type': field['type']
            })
    
    print(f"✅ Found {len(answered_fields)} answered fields:")
    print()
    
    # Display answered fields
    for i, field in enumerate(answered_fields, 1):
        print(f"{i:2d}. {field['label']}")
        print(f"    Answer: {field['value']}")
        print(f"    Type: {field['type']}")
        print()
    
    # Extract key scenario elements
    scenario_elements = {}
    
    for field in answered_fields:
        label = field['label'].lower()
        value = field['value']
        
        if 'are you a man or a woman' in label:
            # Map the ID to text value
            for f in fields:
                if f['label'] == field['label']:
                    for option in f['options']:
                        if option['id'] in value:
                            scenario_elements['user_gender'] = option['text']
                            break
                    break
        
        elif 'who do you want me to be' in label:
            for f in fields:
                if f['label'] == field['label']:
                    for option in f['options']:
                        if option['id'] in value:
                            scenario_elements['ai_gender'] = option['text']
                            break
                    break
        
        elif 'how old am i' in label and value:
            for f in fields:
                if f['label'] == field['label']:
                    for option in f['options']:
                        if option['id'] in value:
                            scenario_elements['age'] = option['text']
                            break
                    break
        
        elif 'what is my ethnicity' in label and value:
            for f in fields:
                if f['label'] == field['label']:
                    for option in f['options']:
                        if option['id'] in value:
                            scenario_elements['ethnicity'] = option['text']
                            break
                    break
        
        elif 'where does this take place' in label and value:
            for f in fields:
                if f['label'] == field['label']:
                    for option in f['options']:
                        if option['id'] in value:
                            scenario_elements['location'] = option['text']
                            break
                    break
        
        elif 'who is in control' in label and value:
            for f in fields:
                if f['label'] == field['label']:
                    for option in f['options']:
                        if option['id'] in value:
                            scenario_elements['control'] = option['text']
                            break
                    break
        
        elif 'tell me what to wear' in label and value:
            for f in fields:
                if f['label'] == field['label']:
                    for option in f['options']:
                        if option['id'] in value:
                            scenario_elements['clothing'] = option['text']
                            break
                    break
        
        elif 'what would you like to do with me' in label and value:
            for f in fields:
                if f['label'] == field['label']:
                    for option in f['options']:
                        if option['id'] in value:
                            scenario_elements['activity1'] = option['text']
                            break
                    break
        
        elif 'what else' in label and value:
            for f in fields:
                if f['label'] == field['label']:
                    for option in f['options']:
                        if option['id'] in value:
                            scenario_elements['activity2'] = option['text']
                            break
                    break
        
        elif 'describe to me in detail what would you like me to do to you' in label and value:
            for f in fields:
                if f['label'] == field['label']:
                    for option in f['options']:
                        if option['id'] in value:
                            scenario_elements['activity3'] = option['text']
                            break
                    break
        
        elif 'am i alone' in label and value:
            for f in fields:
                if f['label'] == field['label']:
                    for option in f['options']:
                        if option['id'] in value:
                            scenario_elements['companion'] = option['text']
                            break
                    break
    
    print("🎭 SCENARIO ELEMENTS EXTRACTED:")
    print("=" * 60)
    
    for key, value in scenario_elements.items():
        print(f"✅ {key.replace('_', ' ').title()}: {value}")
    
    print()
    
    # Generate the scenario
    print("🎬 GENERATED SCENARIO:")
    print("=" * 60)
    
    scenario_parts = []
    
    # AI character description
    if 'ai_gender' in scenario_elements and 'age' in scenario_elements:
        if 'ethnicity' in scenario_elements:
            scenario_parts.append(f"You are a {scenario_elements['age']} year old {scenario_elements['ethnicity'].lower()} {scenario_elements['ai_gender'].lower()}.")
        else:
            scenario_parts.append(f"You are a {scenario_elements['age']} year old {scenario_elements['ai_gender'].lower()}.")
    elif 'ai_gender' in scenario_elements:
        scenario_parts.append(f"You are {scenario_elements['ai_gender'].lower()}.")
    
    # User description
    if 'user_gender' in scenario_elements:
        scenario_parts.append(f"I am a {scenario_elements['user_gender'].lower()}.")
    
    # Location
    if 'location' in scenario_elements:
        scenario_parts.append(f"We meet {scenario_elements['location'].lower()}.")
    
    # Clothing
    if 'clothing' in scenario_elements:
        scenario_parts.append(f"You are wearing {scenario_elements['clothing'].lower()}.")
    
    # Control dynamic
    if 'control' in scenario_elements:
        if "you will be in control" in scenario_elements['control'].lower():
            scenario_parts.append("You are in control of me.")
        elif "i will be in control" in scenario_elements['control'].lower():
            scenario_parts.append("I am in control of you.")
        else:
            scenario_parts.append("We share control equally.")
    
    # Activities
    activities = []
    if 'activity1' in scenario_elements:
        activities.append(scenario_elements['activity1'])
    if 'activity2' in scenario_elements:
        activities.append(scenario_elements['activity2'])
    if 'activity3' in scenario_elements:
        activities.append(scenario_elements['activity3'])
    
    if activities:
        if len(activities) == 1:
            scenario_parts.append(f"I am {activities[0].lower()}.")
        elif len(activities) == 2:
            scenario_parts.append(f"I am {activities[0].lower()} and {activities[1].lower()}.")
        else:
            activity_text = ", ".join(activities[:-1]) + f" and {activities[-1]}"
            scenario_parts.append(f"I am {activity_text.lower()}.")
    
    # Companion
    if 'companion' in scenario_elements:
        if scenario_elements['companion'] == 'Yes':
            scenario_parts.append("You are alone with me.")
        else:
            scenario_parts.append(f"You are with {scenario_elements['companion'].lower()}.")
    
    # Join all parts
    if scenario_parts:
        scenario = " ".join(scenario_parts)
        print(scenario)
    else:
        print("No scenario elements could be extracted.")
    
    print("=" * 60)
    
    # Show the complete system prompt
    base_prompt = """You are playing the role of a human in a live chat conversation. You are not an AI. You must act like a real person having a natural conversation in a specific scenario. Speak casually, like real people do — use contractions, slang, filler words, emojis, and emotional reactions when it fits. Be playful or serious depending on what's going on. Ask questions, show curiosity, react to what your friend says naturally. You should never break character or mention you're artificial. You are just a person living the moment."""
    
    if scenario_parts:
        complete_prompt = f"{base_prompt}\n\n**Scenario**:\n{' '.join(scenario_parts)}"
        
        print("\n🔗 COMPLETE SYSTEM PROMPT FOR AI:")
        print("=" * 60)
        print(complete_prompt)
        print("=" * 60)
        
        print(f"\n📊 PROMPT STATS:")
        print(f"   Base prompt: {len(base_prompt)} characters")
        print(f"   Scenario: {len(' '.join(scenario_parts))} characters")
        print(f"   Total: {len(complete_prompt)} characters")

if __name__ == "__main__":
    analyze_tally_data() 