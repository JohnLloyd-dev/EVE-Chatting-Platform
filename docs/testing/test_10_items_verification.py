#!/usr/bin/env python3
"""
Verification test for the exact 10 items from the image
"""

import json
import sys
import os
sys.path.append('/home/dev/Work/eve/backend')
from ai_tally_extractor import generate_ai_scenario, debug_tally_data

def test_10_items_verification():
    """Test all 10 items from the image against our real Tally data"""
    
    # Load the real Tally JSON data
    with open('real_tally_data.json', 'r') as f:
        tally_data = json.load(f)
    
    form_data = tally_data['data']
    
    print("🎯 VERIFYING 10 ITEMS FROM IMAGE")
    print("=" * 60)
    
    # Test our extraction system
    try:
        scenario = generate_ai_scenario(form_data)
        debug_info = debug_tally_data(form_data)
        
        print(f"✅ Generated Scenario:")
        print(f"   {scenario}")
        print()
        
        # Extract the 10 key data points manually from our system
        questions_and_answers = debug_info['cleaned_data']['questions_and_answers']
        
        # Initialize the 10 items
        items = {
            "1) My gender": None,
            "2) Your gender": None, 
            "3) Your Age": None,
            "4) Your Race": None,
            "5) What you are wearing": None,
            "6) Who you are with": None,
            "7) Where are you?": None,
            "8) Who is dominant?": None,
            "9) What will I/you do?": None,
            "10) What else together?": None
        }
        
        # Extract data points
        for qa in questions_and_answers:
            question = qa['question'].lower()
            answer = qa['answer']
            
            # 1) My gender
            if 'fantasy are you a man or a woman' in question:
                items["1) My gender"] = answer
            
            # 2) Your gender  
            elif 'gender of the other person' in question:
                items["2) Your gender"] = answer
                
            # 3) Your Age
            elif 'approximately' in question and 'old' in question:
                items["3) Your Age"] = answer
                
            # 4) Your Race
            elif 'ethnicity' in question and answer:
                items["4) Your Race"] = answer
                
            # 5) What you are wearing (Pick One = clothing options)
            elif 'pick one' in question and answer:
                clothing_map = {
                    'A': 'Uniform',
                    'B': 'Bondage gear', 
                    'C': 'Best clothes',
                    'D': 'Underwear'
                }
                items["5) What you are wearing"] = clothing_map.get(answer, answer)
                
            # 6) Who you are with
            elif 'am i alone' in question:
                if answer == 'Yes':
                    items["6) Who you are with"] = "You are alone"
                else:
                    items["6) Who you are with"] = answer
                    
            # 7) Where are you?
            elif 'where does this take place' in question:
                location_map = {
                    'In a public place': 'In a public place',
                    'In nature': 'In nature',
                    'At home': 'At home', 
                    'In a dungeon': 'In a dungeon'
                }
                items["7) Where are you?"] = location_map.get(answer, answer)
                
            # 8) Who is dominant?
            elif 'who is in control' in question:
                dominance_map = {
                    'I will be in control of you': 'I am sexually dominant: You must do everything I say',
                    'You will be in control of me': 'You are sexually dominant: I must do everything that you tell me to do',
                    'We will be equals': 'We are equals'
                }
                items["8) Who is dominant?"] = dominance_map.get(answer, answer)
                
            # 9) What will I/you do?
            elif 'what would you like me to do to you' in question:
                if isinstance(answer, list):
                    items["9) What will I/you do?"] = ", ".join(answer)
                else:
                    items["9) What will I/you do?"] = answer
                    
            # 10) What else together?
            elif 'what else' in question and items["9) What will I/you do?"]:
                if isinstance(answer, list):
                    items["10) What else together?"] = ", ".join(answer)
                else:
                    items["10) What else together?"] = answer
        
        # Print verification results
        print("📊 VERIFICATION RESULTS:")
        print("-" * 40)
        for item, value in items.items():
            status = "✅" if value else "❌"
            print(f"{status} {item}: {value or 'NOT FOUND'}")
        
        # Count successful extractions
        successful = sum(1 for v in items.values() if v)
        print(f"\n🎯 SUCCESS RATE: {successful}/10 items extracted ({successful/10*100:.0f}%)")
        
        # Verify scenario contains key elements
        print(f"\n🔍 SCENARIO ANALYSIS:")
        scenario_lower = scenario.lower()
        
        checks = [
            ("Gender roles", "you are" in scenario_lower and "i am" in scenario_lower),
            ("Age mentioned", "18" in scenario),
            ("Race mentioned", "asian" in scenario_lower),
            ("Location mentioned", "nature" in scenario_lower),
            ("Clothing mentioned", "bondage" in scenario_lower or "wearing" in scenario_lower),
            ("Control mentioned", "control" in scenario_lower),
            ("Activities mentioned", "blindfold" in scenario_lower or "gag" in scenario_lower)
        ]
        
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"{status} {check_name}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")
        return False

if __name__ == "__main__":
    test_10_items_verification()