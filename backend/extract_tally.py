"""
Extract and process Tally form data to generate story scenarios
"""
import json
import random

class FantasyStoryGenerator:
    def __init__(self, json_data):
        self.data = json_data
        self.story_elements = {
            "my_gender": self.get_answer('question_zMKJN1'),
            "partner_gender": self.get_answer('question_59dv4M'),
            "partner_age": self.get_answer('question_d0YjNz'),
            "partner_ethnicity": self.get_answer('question_YGZYRq'),
            "alone_status": self.get_answer('question_DpVDKb'),
            "location": self.get_answer('question_KxMXVD'),
            "control_dynamic": self.get_answer('question_LKd8PJ'),
            "primary_action": self.get_answer('question_poLgDP'),
            "secondary_action": self.get_answer('question_14rj9b'),
            "experience_with": self.get_answer('question_lOVNqo'),
            "anything_else": self.get_text_answer('question_Dp0VKl')
        }
        self.names = {
            "Man": ["Alex", "Marcus", "Daniel", "Jake", "Ryan"],
            "Woman": ["L", "Sophia", "Mia", "Emma", "Olivia"],
            "Police": ["Riley", "Jordan", "Casey", "Morgan", "Taylor"]
        }
        
    def get_answer(self, field_key):
        """Extract answer text for a given field key"""
        for field in self.data['fields']:
            if field['key'] == field_key and field.get('value'):
                option_map = {opt['id']: opt['text'] for opt in field['options']}
                return [option_map[id] for id in field['value']][0]
        return None
        
    def get_text_answer(self, field_key):
        """Extract text answer for textarea fields"""
        for field in self.data['fields']:
            if field['key'] == field_key and field.get('value'):
                return field['value']
        return None
        
    def generate_name(self, gender, role=None):
        """Generate a random name based on gender and potential role"""
        pool = self.names.get(gender, []) + self.names.get("Police", [])
        return random.choice(pool)
        
    def create_story(self):
        """Generate a custom story based on form selections"""
        # Determine roles and names
        my_role = "man" if self.story_elements["my_gender"] == "Man" else "woman"
        partner_role = "policeman" if self.story_elements["partner_gender"] == "Man" else "policewoman"
        partner_name = self.generate_name(self.story_elements["partner_gender"], "Police")
        
        # Map locations to descriptive phrases
        location_map = {
            "In a public place": "a public park",
            "In nature": "a secluded forest",
            "At home": "my home",
            "In a dungeon": "a secret dungeon"
        }
        location = location_map.get(self.story_elements["location"], "an unknown location")
        
        # Build story components
        story = f"Your name is {partner_name}. "
        story += f"You are a {self.story_elements['partner_age']} year old {self.story_elements['partner_ethnicity'].lower()} {partner_role}. "
        story += f"I am a {my_role} who you just met in {location}. "
        
        # Power dynamic description
        if "control of me" in self.story_elements["control_dynamic"]:
            story += "When we meet, you immediately take control. "
        elif "control of you" in self.story_elements["control_dynamic"]:
            story += "When we meet, I take control of you. "
        else:
            story += "When we meet, we connect as equals. "
        
        # Action sequences
        actions = []
        if self.story_elements["primary_action"]:
            actions.append(self.story_elements["primary_action"].lower())
        if self.story_elements["secondary_action"]:
            actions.append(self.story_elements["secondary_action"].lower())
        
        # Add any additional actions from the example
        actions.extend(["tie me up", "force me to have sex with you", "gag me", 
                       "blindfold me", "don't let me go when I ask you to", 
                       "go down on me", "tease me"])
        
        # Build action sequence
        for i, action in enumerate(actions):
            if i == 0:
                story += f"You {action} "
            elif i == len(actions) - 1:
                story += f"and {action}. "
            else:
                story += f", {action} "
        
        # Add custom elements if provided
        if self.story_elements["anything_else"]:
            story += f"\n\nAdditionally, {self.story_elements['anything_else']}"
            
        return story

def generate_story_from_json(form_data):
    """
    Generate a story scenario from Tally form data
    
    Args:
        form_data: Dictionary containing form submission data
        
    Returns:
        str: Generated story scenario
    """
    if not form_data:
        return "Welcome! I'm here to help you with any questions or conversations you'd like to have."
    
    # Handle Tally webhook format
    if isinstance(form_data, dict) and 'data' in form_data:
        # Extract the actual form data from Tally webhook structure
        tally_data = form_data.get('data', {})
        
        generator = FantasyStoryGenerator(tally_data)
        return generator.create_story()
    
    else:
        # Handle simple key-value form data or fallback
        return "Welcome! I'm here to help you with any questions or conversations you'd like to have. What would you like to talk about?"