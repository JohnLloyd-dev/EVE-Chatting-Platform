"""
Extract and process Tally form data to generate story scenarios
"""
import json
import random

class FantasyStoryGenerator:
    def __init__(self, json_data):
        self.data = json_data
        # Extract ALL fields dynamically instead of hardcoding specific ones
        self.all_fields = self.extract_all_fields()
        
        # Keep the original story elements for backward compatibility
        # but now they're populated from the dynamic extraction
        self.story_elements = self.map_story_elements()
        self.names = {
            "Man": ["Alex", "Marcus", "Daniel", "Jake", "Ryan"],
            "Woman": ["L", "Sophia", "Mia", "Emma", "Olivia"],
            "Police": ["Riley", "Jordan", "Casey", "Morgan", "Taylor"]
        }
    
    def extract_all_fields(self):
        """
        Extract ALL fields from the Tally form dynamically
        Returns a dictionary with field_key -> {label, type, value, options}
        """
        extracted_fields = {}
        
        for field in self.data.get('fields', []):
            field_key = field.get('key')
            if not field_key:
                continue
                
            field_info = {
                'label': field.get('label', '').strip(),
                'type': field.get('type'),
                'raw_value': field.get('value'),
                'options': field.get('options', []),
                'processed_value': None
            }
            
            # Process the value based on field type
            if field.get('value'):
                if field.get('type') == 'MULTIPLE_CHOICE' and isinstance(field.get('value'), list):
                    # Map option IDs to their text values
                    option_map = {opt['id']: opt['text'] for opt in field.get('options', [])}
                    selected_options = [option_map.get(val_id, val_id) for val_id in field['value']]
                    field_info['processed_value'] = selected_options[0] if len(selected_options) == 1 else selected_options
                    
                elif field.get('type') in ['TEXTAREA', 'INPUT_PHONE_NUMBER', 'EMAIL']:
                    # Text-based fields
                    field_info['processed_value'] = field['value']
                    
                elif field.get('type') == 'PAYMENT':
                    # Payment fields
                    field_info['processed_value'] = field['value']
                    
                else:
                    # Default: use raw value
                    field_info['processed_value'] = field['value']
            
            extracted_fields[field_key] = field_info
            
        return extracted_fields
    
    def map_story_elements(self):
        """
        Map the dynamically extracted fields to story elements
        This maintains backward compatibility while using the new extraction
        """
        story_elements = {}
        
        # Find fields by their labels (more reliable than hardcoded keys)
        for field_key, field_info in self.all_fields.items():
            label = field_info['label'].lower()
            value = field_info['processed_value']
            
            # Map based on question content
            if 'fantasy are you a man or a woman' in label:
                story_elements['my_gender'] = value
            elif 'gender of the other person' in label:
                story_elements['partner_gender'] = value
            elif 'how old are they' in label and value:  # Only take first age question with value
                if 'partner_age' not in story_elements:
                    story_elements['partner_age'] = value
            elif 'ethnicity' in label and value:  # Only take first ethnicity question with value
                if 'partner_ethnicity' not in story_elements:
                    story_elements['partner_ethnicity'] = value
            elif 'am i alone' in label:
                story_elements['companion_status'] = value
            elif 'where does this take place' in label and value:
                if 'location' not in story_elements:
                    story_elements['location'] = value
            elif 'who is in control' in label and value:
                if 'dominance' not in story_elements:
                    story_elements['dominance'] = value
            elif 'what would you like to do with me' in label:
                story_elements['primary_action'] = value
            elif 'what else' in label and value:
                if 'secondary_action' not in story_elements:
                    story_elements['secondary_action'] = value
            elif 'anything else' in label:
                story_elements['anything_else'] = value
            elif 'how would you like to experience' in label:
                story_elements['experience_type'] = value
            elif 'phone number' in label:
                story_elements['phone_number'] = value
                
        # Also capture clothing from "Pick One" fields (need to identify which one)
        # Look for the first "Pick One" field that has a value
        for field_key, field_info in self.all_fields.items():
            if field_info['label'] == 'Pick One ' and field_info['processed_value']:
                if 'clothing' not in story_elements:
                    story_elements['clothing'] = field_info['processed_value']
                    
        return story_elements
        
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
    
    def debug_form_data(self):
        """Debug function to show all available form fields"""
        print("=== TALLY FORM DEBUG ===")
        print(f"Total fields: {len(self.data.get('fields', []))}")
        
        print("\n=== ALL EXTRACTED FIELDS ===")
        for field_key, field_info in self.all_fields.items():
            print(f"Key: {field_key}")
            print(f"   Label: '{field_info['label']}'")
            print(f"   Type: {field_info['type']}")
            print(f"   Raw Value: {field_info['raw_value']}")
            print(f"   Processed Value: {field_info['processed_value']}")
            if field_info['options']:
                print(f"   Options: {[opt.get('text') for opt in field_info['options']]}")
            print()
        
        print("=== MAPPED STORY ELEMENTS ===")
        for key, value in self.story_elements.items():
            print(f"{key}: {value}")
        
        print("\n=== FIELDS WITH VALUES ===")
        fields_with_values = {k: v for k, v in self.all_fields.items() if v['processed_value'] is not None}
        print(f"Total fields with values: {len(fields_with_values)}")
        for field_key, field_info in fields_with_values.items():
            print(f"{field_key}: '{field_info['label']}' = {field_info['processed_value']}")
        print("========================")
        
    def generate_name(self, gender, role=None):
        """Generate a random name based on gender and potential role"""
        pool = self.names.get(gender, []) + self.names.get("Police", [])
        return random.choice(pool)
        
    def create_story(self):
        """Generate a narrative story that flows naturally like the example provided"""
        
        # Try to generate scenario with whatever data we have
        # Only return fallback if we have absolutely no usable data
        if not any(self.story_elements.values()):
            return ""  # Return empty string instead of default message
        
        # Character setup - handle missing data gracefully
        my_role = "man" if self.story_elements.get("my_gender") == "Man" else "woman"
        partner_role = "man" if self.story_elements.get("partner_gender") == "Man" else "woman"
        
        # Generate name based on available gender info
        partner_gender = self.story_elements.get("partner_gender", "Man")  # Default to Man if missing
        partner_name = self.generate_name(partner_gender)
        
        # Age and ethnicity with defaults and null checks
        age = self.story_elements.get("partner_age", "25")
        ethnicity = self.story_elements.get("partner_ethnicity")
        
        # Start the narrative - build character description
        story_parts = [f"Your name is {partner_name}."]
        
        if ethnicity and ethnicity.strip():
            story_parts.append(f"You are a {age} year old {ethnicity.lower()} {partner_role}.")
        else:
            story_parts.append(f"You are a {age} year old {partner_role}.")
        
        story = " ".join(story_parts)
        
        # Location context - only add if we have location data
        location_text = ""
        if self.story_elements.get("location"):
            location_map = {
                "In a public place": "in a public place",
                "In nature": "in a forest",
                "At home": "at home", 
                "In a dungeon": "in a dungeon"
            }
            location = location_map.get(self.story_elements["location"], self.story_elements["location"])
            location_text = f" {location}"
        
        # Meeting context - build based on available data
        if location_text:
            story += f" I am a {my_role} who you just met{location_text}."
        else:
            story += f" I am a {my_role}."
        
        # Create narrative flow based on dominance and actions
        if self.story_elements.get("dominance") == "You will be in control of me":
            story += " When we meet"
            
            # Convert actions to narrative flow
            action_phrases = []
            
            if self.story_elements.get("primary_action"):
                action = self.story_elements["primary_action"]
                if action and "Undress me slowly" in action:
                    action_phrases.append("you slowly undress me")
                elif action and "Instruct me" in action:
                    action_phrases.append("you give me commands")
                elif action and "Gag me" in action:
                    action_phrases.append("you gag me")
                elif action and "Look me in the eyes" in action:
                    action_phrases.append("you stare into my eyes")
                elif action and "Blindfold me" in action:
                    action_phrases.append("you blindfold me")
                elif action and "Caress me gently" in action:
                    action_phrases.append("you caress me gently")
                elif action and "Go down on me" in action:
                    action_phrases.append("you go down on me")
                elif action:
                    action_phrases.append(f"you {action.lower()}")
            
            if self.story_elements.get("secondary_action"):
                action = self.story_elements["secondary_action"]
                if action and "Bring me close to orgasm then stop" in action:
                    action_phrases.append("bring me close to orgasm then stop")
                elif action and "Tie me up" in action:
                    action_phrases.append("tie me up")
                elif action and "Seduce me" in action:
                    action_phrases.append("seduce me")
                elif action and "Take me against my will" in action:
                    action_phrases.append("force me to have sex with you")
                elif action and "Indulge my every whim" in action:
                    action_phrases.append("indulge my every whim")
                elif action and "Punish me" in action:
                    action_phrases.append("punish me")
                elif action and "Tease me" in action:
                    action_phrases.append("tease me")
                elif action:
                    action_phrases.append(f"{action.lower()}")
            
            # Combine actions into flowing narrative
            if action_phrases:
                if len(action_phrases) == 1:
                    story += f" {action_phrases[0]}."
                elif len(action_phrases) == 2:
                    story += f" {action_phrases[0]} and {action_phrases[1]}."
                else:
                    story += f" {', '.join(action_phrases[:-1])}, and {action_phrases[-1]}."
                
                # Add resistance element for certain actions
                resistance_actions = ["tie me up", "gag me", "force me", "blindfold me"]
                if any(resist in ' '.join(action_phrases) for resist in resistance_actions):
                    story += " You don't let me go when I ask you to."
            else:
                story += " we begin our encounter."
        
        elif self.story_elements.get("dominance") == "I will be in control of you":
            story += " I take control and"
            # Similar logic but with reversed roles - convert "me" to "you"
            action_phrases = []
            
            if self.story_elements.get("primary_action"):
                action = self.story_elements["primary_action"]
                if action:
                    action = action.replace("me", "you").replace("my", "your")
                    action_phrases.append(action.lower())
            
            if self.story_elements.get("secondary_action"):
                action = self.story_elements["secondary_action"]
                if action:
                    action = action.replace("me", "you").replace("my", "your")
                    action_phrases.append(action.lower())
            
            if action_phrases:
                story += f" {' and '.join(action_phrases)}."
            else:
                story += " we begin our encounter."
        
        else:  # equals or other dominance
            story += " We explore together"
            action_phrases = []
            
            if self.story_elements.get("primary_action"):
                action = self.story_elements["primary_action"]
                if action:
                    action_phrases.append(action.lower())
            
            if self.story_elements.get("secondary_action"):
                action = self.story_elements["secondary_action"]
                if action:
                    action_phrases.append(action.lower())
            
            if action_phrases:
                story += f" through {' and '.join(action_phrases)}."
            else:
                story += "."
        
        return story
    
    def create_comprehensive_prompt(self):
        """
        Create a comprehensive prompt that includes ALL extracted field data
        This ensures no Tally form data is lost in the final prompt
        """
        prompt_parts = []
        
        # Start with the processed story
        story = self.create_story()
        if story and story != "Welcome! I'm here to help you with any questions or conversations you'd like to have.":
            prompt_parts.append(f"SCENARIO: {story}")
        
        # Add ALL fields with values in a structured format
        fields_with_values = {k: v for k, v in self.all_fields.items() if v['processed_value'] is not None}
        
        if fields_with_values:
            prompt_parts.append("\nCOMPLETE TALLY FORM DATA:")
            
            # Group fields by type for better organization
            multiple_choice_fields = []
            text_fields = []
            payment_fields = []
            other_fields = []
            
            for field_key, field_info in fields_with_values.items():
                field_entry = f"- {field_info['label']}: {field_info['processed_value']}"
                
                if field_info['type'] == 'MULTIPLE_CHOICE':
                    multiple_choice_fields.append(field_entry)
                elif field_info['type'] in ['TEXTAREA', 'INPUT_PHONE_NUMBER', 'EMAIL']:
                    text_fields.append(field_entry)
                elif field_info['type'] == 'PAYMENT':
                    payment_fields.append(field_entry)
                else:
                    other_fields.append(field_entry)
            
            # Add organized sections
            if multiple_choice_fields:
                prompt_parts.append("\nUser Selections:")
                prompt_parts.extend(multiple_choice_fields)
            
            if text_fields:
                prompt_parts.append("\nUser Text Input:")
                prompt_parts.extend(text_fields)
            
            if payment_fields:
                prompt_parts.append("\nPayment Information:")
                prompt_parts.extend(payment_fields)
            
            if other_fields:
                prompt_parts.append("\nOther Data:")
                prompt_parts.extend(other_fields)
        
        # Add field summary
        total_fields = len(self.all_fields)
        fields_with_data = len(fields_with_values)
        prompt_parts.append(f"\nFORM SUMMARY: {fields_with_data}/{total_fields} fields completed")
        
        # Add raw field keys for reference (useful for debugging)
        if fields_with_values:
            field_keys = list(fields_with_values.keys())
            prompt_parts.append(f"Active field keys: {', '.join(field_keys[:10])}{'...' if len(field_keys) > 10 else ''}")
        
        return "\n".join(prompt_parts)
    
    def create_clean_scenario(self):
        """
        Create a clean scenario narrative for the AI model
        Returns only the essential story without debug info or metadata
        """
        return self.create_story()

def generate_story_from_json(form_data):
    """
    Generate a story scenario from Tally form data
    
    Args:
        form_data: Dictionary containing form submission data
        
    Returns:
        str: Generated story scenario with complete field data
    """
    if not form_data:
        return ""  # Return empty string instead of default message
    
    # Handle Tally webhook format (full webhook with 'data' key)
    if isinstance(form_data, dict) and 'data' in form_data:
        # Extract the actual form data from Tally webhook structure
        tally_data = form_data.get('data', {})
        
        generator = FantasyStoryGenerator(tally_data)
        
        # Debug logging disabled for production
        # Uncomment the lines below for debugging:
        # try:
        #     generator.debug_form_data()
        # except Exception as e:
        #     print(f"Debug logging failed: {e}")
        
        # Return clean scenario for AI model (comprehensive data stored separately)
        return generator.create_clean_scenario()
    
    # Handle direct form data (just the 'data' section with 'fields')
    elif isinstance(form_data, dict) and 'fields' in form_data:
        generator = FantasyStoryGenerator(form_data)
        
        # Debug logging disabled for production
        # Uncomment the lines below for debugging:
        # try:
        #     generator.debug_form_data()
        # except Exception as e:
        #     print(f"Debug logging failed: {e}")
            
        # Return clean scenario for AI model (comprehensive data stored separately)
        return generator.create_clean_scenario()
    
    else:
        # Handle simple key-value form data or fallback
        return ""  # Return empty string instead of default message