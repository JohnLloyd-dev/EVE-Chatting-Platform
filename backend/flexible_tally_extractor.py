"""
Flexible Tally Form Extractor
Dynamically extracts meaningful information from any custom Tally form
"""

import re
import random
from typing import Dict, List, Any, Optional

class FlexibleTallyExtractor:
    """
    Flexible extractor that can handle any custom Tally form structure
    Uses pattern matching and semantic analysis to extract story elements
    """
    
    def __init__(self, form_data: Dict):
        self.form_data = form_data
        self.fields = self.extract_all_fields()
        self.story_elements = self.extract_story_elements()
        
        # Name pools for character generation
        self.names = {
            "male": ["Alex", "Jordan", "Casey", "Ryan", "Blake", "Cameron", "Taylor", "Morgan", "Avery", "Quinn"],
            "female": ["Alex", "Jordan", "Casey", "Taylor", "Morgan", "Avery", "Quinn", "Riley", "Sage", "River"],
            "neutral": ["Alex", "Jordan", "Casey", "Taylor", "Morgan", "Avery", "Quinn", "River", "Sage", "Blake"]
        }
    
    def extract_all_fields(self) -> Dict[str, Dict]:
        """Extract all fields with their labels and values"""
        fields = {}
        
        if not self.form_data or 'fields' not in self.form_data:
            return fields
            
        for field in self.form_data['fields']:
            field_key = field.get('key', '')
            field_info = {
                'label': field.get('label', ''),
                'type': field.get('type', ''),
                'value': field.get('value', []),
                'options': field.get('options', []),
                'processed_value': None
            }
            
            # Process the value based on field type
            if field.get('type') == 'MULTIPLE_CHOICE' and field.get('options'):
                # Find selected option text
                selected_values = field.get('value', [])
                if selected_values:
                    selected_texts = []
                    for option in field.get('options', []):
                        if option.get('id') in selected_values:
                            selected_texts.append(option.get('text', ''))
                    
                    # Store both joined and individual values for flexibility
                    field_info['processed_value'] = ', '.join(selected_texts) if selected_texts else None
                    field_info['selected_options'] = selected_texts  # Store individual options
            else:
                # For other field types, use the value directly
                value = field.get('value')
                if isinstance(value, list) and value:
                    field_info['processed_value'] = value[0] if len(value) == 1 else ', '.join(str(v) for v in value if v)
                elif value:
                    field_info['processed_value'] = str(value)
            
            fields[field_key] = field_info
        
        return fields
    
    def extract_story_elements(self) -> Dict[str, Any]:
        """
        Dynamically extract story elements from any form structure
        Uses semantic pattern matching instead of hardcoded labels
        """
        elements = {}
        
        # Analyze each field for story-relevant information
        for field_key, field_info in self.fields.items():
            label = field_info['label'].lower()
            value = field_info['processed_value']
            
            if not value or value == 'None':
                continue
                
            # Character gender detection
            if self.is_gender_question(label):
                if self.is_asking_about_user(label):
                    elements['user_gender'] = self.normalize_gender(value)
                else:
                    elements['partner_gender'] = self.normalize_gender(value)
            
            # Age detection
            elif self.is_age_question(label):
                elements['age'] = self.extract_age(value)
            
            # Ethnicity/race detection
            elif self.is_ethnicity_question(label):
                # Handle multiple ethnicities - use the first one for character description
                if field_info.get('selected_options'):
                    elements['ethnicity'] = self.normalize_ethnicity(field_info['selected_options'][0])
                    if len(field_info['selected_options']) > 1:
                        elements['ethnicity_options'] = [self.normalize_ethnicity(opt) for opt in field_info['selected_options']]
                else:
                    elements['ethnicity'] = self.normalize_ethnicity(value)
            
            # Location detection
            elif self.is_location_question(label):
                # Handle multiple locations - use the first one for meeting context
                if field_info.get('selected_options'):
                    elements['location'] = self.normalize_location(field_info['selected_options'][0])
                    if len(field_info['selected_options']) > 1:
                        elements['location_options'] = [self.normalize_location(opt) for opt in field_info['selected_options']]
                else:
                    elements['location'] = self.normalize_location(value)
            
            # Role/profession detection
            elif self.is_role_question(label):
                if self.is_asking_about_user(label):
                    elements['user_role'] = self.normalize_role(value)
                else:
                    elements['partner_role'] = self.normalize_role(value)
            
            # Control/dominance detection
            elif self.is_control_question(label):
                elements['control'] = self.normalize_control(value)
            
            # Activity/action detection
            elif self.is_activity_question(label):
                if 'activities' not in elements:
                    elements['activities'] = []
                
                # Handle multiple activities properly
                if field_info.get('selected_options'):
                    # Add each selected activity as a separate item
                    elements['activities'].extend(field_info['selected_options'])
                else:
                    # Single activity or comma-separated string
                    if ',' in value:
                        # Split comma-separated activities
                        activities = [act.strip() for act in value.split(',')]
                        elements['activities'].extend(activities)
                    else:
                        elements['activities'].append(value)
            
            # Scenario/setting detection
            elif self.is_scenario_question(label):
                elements['scenario'] = value
            
            # Custom/other meaningful content
            else:
                # Store any other meaningful content
                if len(value.strip()) > 2:  # Ignore very short values
                    if 'custom_details' not in elements:
                        elements['custom_details'] = []
                    elements['custom_details'].append(f"{field_info['label']}: {value}")
        
        return elements
    
    def is_gender_question(self, label: str) -> bool:
        """Detect if a question is asking about gender"""
        gender_patterns = [
            r'\b(gender|sex)\b',
            r'\b(man|woman|male|female)\b',
            r'\b(boy|girl|guy|gal)\b',
            r'\bare you.*?(man|woman)\b'
        ]
        return any(re.search(pattern, label) for pattern in gender_patterns)
    
    def is_asking_about_user(self, label: str) -> bool:
        """Detect if question is asking about the user vs partner"""
        user_patterns = [
            r'\bare you\b',
            r'\byou are\b',
            r'\byour\b',
            r'\bin this.*you\b',
            r'\byou want\b',
            r'\bdo you\b'
        ]
        return any(re.search(pattern, label) for pattern in user_patterns)
    
    def is_age_question(self, label: str) -> bool:
        """Detect age-related questions"""
        age_patterns = [
            r'\bage\b',
            r'\bold\b',
            r'\byears?\b',
            r'\byoung\b',
            r'\bmature\b'
        ]
        return any(re.search(pattern, label) for pattern in age_patterns)
    
    def is_ethnicity_question(self, label: str) -> bool:
        """Detect ethnicity/race questions"""
        ethnicity_patterns = [
            r'\bethnicity\b',
            r'\brace\b',
            r'\b(asian|black|white|hispanic|latino|indian|middle eastern)\b',
            r'\bnationality\b',
            r'\bbackground\b'
        ]
        return any(re.search(pattern, label) for pattern in ethnicity_patterns)
    
    def is_location_question(self, label: str) -> bool:
        """Detect location/setting questions"""
        location_patterns = [
            r'\bwhere\b',
            r'\blocation\b',
            r'\bplace\b',
            r'\bsetting\b',
            r'\btake place\b',
            r'\bhappen\b',
            r'\bmeet\b'
        ]
        return any(re.search(pattern, label) for pattern in location_patterns)
    
    def is_role_question(self, label: str) -> bool:
        """Detect role/profession questions"""
        role_patterns = [
            r'\brole\b',
            r'\bjob\b',
            r'\bprofession\b',
            r'\boccupation\b',
            r'\bwork\b',
            r'\bcareer\b',
            r'\b(teacher|doctor|nurse|police|student|boss|employee)\b'
        ]
        return any(re.search(pattern, label) for pattern in role_patterns)
    
    def is_control_question(self, label: str) -> bool:
        """Detect control/dominance questions"""
        control_patterns = [
            r'\bcontrol\b',
            r'\bdominant\b',
            r'\bsubmissive\b',
            r'\bin charge\b',
            r'\blead\b',
            r'\bcommand\b',
            r'\bobey\b'
        ]
        return any(re.search(pattern, label) for pattern in control_patterns)
    
    def is_activity_question(self, label: str) -> bool:
        """Detect activity/action questions"""
        activity_patterns = [
            r'\bdo\b',
            r'\bactivity\b',
            r'\bactivities\b',
            r'\baction\b',
            r'\bwant\b',
            r'\blike to\b',
            r'\bhappen\b',
            r'\bexperience\b',
            r'\binterest\b',
            r'\bprefer\b',
            r'\benjoy\b',
            r'\bshould.*do\b',
            r'\bwould.*like\b'
        ]
        return any(re.search(pattern, label) for pattern in activity_patterns)
    
    def is_scenario_question(self, label: str) -> bool:
        """Detect scenario/fantasy questions"""
        scenario_patterns = [
            r'\bscenario\b',
            r'\bfantasy\b',
            r'\bstory\b',
            r'\bimagine\b',
            r'\bdream\b',
            r'\bsituation\b'
        ]
        return any(re.search(pattern, label) for pattern in scenario_patterns)
    
    def normalize_gender(self, value: str) -> str:
        """Normalize gender values"""
        value = value.lower().strip()
        if any(word in value for word in ['man', 'male', 'boy', 'guy']):
            return 'man'
        elif any(word in value for word in ['woman', 'female', 'girl', 'gal']):
            return 'woman'
        return value
    
    def normalize_ethnicity(self, value: str) -> str:
        """Normalize ethnicity values"""
        value = value.lower().strip()
        ethnicity_map = {
            'asian': 'asian',
            'black': 'black', 
            'african': 'black',
            'white': 'white',
            'caucasian': 'white',
            'hispanic': 'hispanic',
            'latino': 'hispanic',
            'indian': 'indian',
            'middle eastern': 'middle eastern',
            'arab': 'middle eastern'
        }
        
        for key, normalized in ethnicity_map.items():
            if key in value:
                return normalized
        return value
    
    def normalize_location(self, value: str) -> str:
        """Normalize location values"""
        value = value.lower().strip()
        location_map = {
            'public': 'in a public place',
            'nature': 'in nature',
            'forest': 'in a forest',
            'park': 'in a park',
            'home': 'at home',
            'house': 'at home',
            'bedroom': 'in the bedroom',
            'office': 'at the office',
            'school': 'at school',
            'dungeon': 'in a dungeon',
            'club': 'at a club'
        }
        
        for key, normalized in location_map.items():
            if key in value:
                return normalized
        return value
    
    def normalize_role(self, value: str) -> str:
        """Normalize role/profession values"""
        return value.lower().strip()
    
    def normalize_control(self, value: str) -> str:
        """Normalize control/dominance values"""
        value = value.lower().strip()
        
        # Check for partner dominance
        if any(phrase in value for phrase in ['they control me', 'partner control', 'them control', 'you control']):
            return 'partner_dominant'
        elif any(phrase in value for phrase in ['i control them', 'i control', 'me control', 'user control']):
            return 'user_dominant'
        elif any(word in value for word in ['equal', 'both', 'together', 'mutual']):
            return 'equal'
        
        # Fallback pattern matching
        if 'control' in value:
            if any(word in value for word in ['they', 'them', 'partner', 'other']):
                return 'partner_dominant'
            elif any(word in value for word in ['i', 'me', 'myself']):
                return 'user_dominant'
        
        return 'equal'  # Default to equal if unclear
    
    def extract_age(self, value: str) -> str:
        """Extract age from value"""
        # Look for numbers in the value
        numbers = re.findall(r'\d+', str(value))
        if numbers:
            return numbers[0]
        
        # Map age ranges or descriptive terms
        age_map = {
            'young': '22',
            'teen': '19',
            'adult': '25',
            'mature': '35',
            'older': '40'
        }
        
        value_lower = str(value).lower()
        for key, age in age_map.items():
            if key in value_lower:
                return age
        
        return '25'  # Default age
    
    def generate_name(self, gender: str = None) -> str:
        """Generate a random name based on gender"""
        if gender == 'man':
            pool = self.names['male'] + self.names['neutral']
        elif gender == 'woman':
            pool = self.names['female'] + self.names['neutral']
        else:
            pool = self.names['neutral']
        
        return random.choice(pool)
    
    def create_narrative_scenario(self) -> str:
        """
        Create a natural narrative scenario from extracted elements
        Works with any custom form structure
        """
        if not self.story_elements:
            return ""
        
        # Build character
        partner_gender = self.story_elements.get('partner_gender', 'person')
        user_gender = self.story_elements.get('user_gender', 'person')
        name = self.generate_name(partner_gender)
        
        # Start narrative
        story_parts = [f"Your name is {name}."]
        
        # Add character details
        age = self.story_elements.get('age', '25')
        ethnicity = self.story_elements.get('ethnicity')
        partner_role = self.story_elements.get('partner_role')
        user_role = self.story_elements.get('user_role')
        
        char_desc = f"You are a {age} year old"
        if ethnicity:
            char_desc += f" {ethnicity}"
        if partner_role:
            char_desc += f" {partner_role}"
        elif partner_gender != 'person':
            char_desc += f" {partner_gender}"
        else:
            char_desc += " person"
        char_desc += "."
        
        story_parts.append(char_desc)
        
        # Add meeting context
        location = self.story_elements.get('location', 'somewhere')
        location_options = self.story_elements.get('location_options', [])
        user_desc = user_role if user_role else user_gender
        
        if location != 'somewhere':
            if location_options and len(location_options) > 1:
                # Multiple locations - mention the primary one but hint at variety
                story_parts.append(f"I am a {user_desc} who you just met {location}.")
            else:
                story_parts.append(f"I am a {user_desc} who you just met {location}.")
        else:
            story_parts.append(f"I am a {user_desc}.")
        
        # Add scenario context first if it exists
        scenario = self.story_elements.get('scenario')
        if scenario and len(scenario.strip()) > 10:  # Only meaningful scenarios
            story_parts.append(scenario)
        
        # Add control dynamic and activities
        control = self.story_elements.get('control')
        activities = self.story_elements.get('activities', [])
        
        if control == 'partner_dominant':
            if activities:
                activity_text = self.format_activities_partner_dominant(activities)
                story_parts.append(f"When we meet {activity_text}.")
            else:
                story_parts.append("When we meet you take control.")
        elif control == 'user_dominant':
            if activities:
                activity_text = self.format_activities_user_dominant(activities)
                story_parts.append(f"I take control and {activity_text}.")
            else:
                story_parts.append("I take control of the situation.")
        else:
            if activities:
                activity_text = self.format_activities_equal(activities)
                story_parts.append(f"We explore together through {activity_text}.")
            else:
                story_parts.append("We explore together.")
        
        # Add custom details if they provide additional context
        custom_details = self.story_elements.get('custom_details', [])
        if custom_details and not activities and not scenario:
            # Only add custom details if we don't have activities or scenario
            relevant_detail = custom_details[0]
            if len(relevant_detail) < 100:  # Keep it concise
                story_parts.append(relevant_detail)
        
        return " ".join(story_parts)
    
    def format_activities_partner_dominant(self, activities: List[str]) -> str:
        """
        Format activities for partner-dominant scenarios
        Partner is in control, so: "you [action] me"
        """
        formatted = []
        for activity in activities:
            activity = activity.lower().strip()
            
            # Convert all activities to "you [action] me" format
            if 'me' in activity:
                # Activity already has "me" - convert to "you [action] me"
                if activity.startswith('tie me'):
                    formatted.append("you tie me up")
                elif activity.startswith('gag me'):
                    formatted.append("you gag me")
                elif activity.startswith('blindfold me'):
                    formatted.append("you blindfold me")
                elif activity.startswith('undress me'):
                    formatted.append("you undress me slowly")
                elif activity.startswith('tease me'):
                    formatted.append("you tease me")
                elif activity.startswith('force me'):
                    formatted.append("you force me to have sex")
                elif 'command' in activity or 'instruct' in activity:
                    formatted.append("you give me commands")
                else:
                    # Generic: ensure it starts with "you"
                    if not activity.startswith('you'):
                        formatted.append(f"you {activity}")
                    else:
                        formatted.append(activity)
            else:
                # Activity doesn't have "me" - add proper subject/object
                if any(word in activity for word in ['tie', 'bind']):
                    formatted.append("you tie me up")
                elif any(word in activity for word in ['gag']):
                    formatted.append("you gag me")
                elif any(word in activity for word in ['blindfold']):
                    formatted.append("you blindfold me")
                elif any(word in activity for word in ['undress', 'strip']):
                    formatted.append("you undress me slowly")
                elif any(word in activity for word in ['tease']):
                    formatted.append("you tease me")
                elif any(word in activity for word in ['force', 'rape']):
                    formatted.append("you force me to have sex")
                elif any(word in activity for word in ['command', 'instruct', 'order']):
                    formatted.append("you give me commands")
                elif any(word in activity for word in ['control', 'dominate']):
                    formatted.append("you control me")
                else:
                    # Generic activity - make it "you [action] me"
                    formatted.append(f"you {activity} me")
        
        # Create natural narrative flow
        return self.create_natural_flow(formatted, "partner_dominant")
    
    def format_activities_user_dominant(self, activities: List[str]) -> str:
        """
        Format activities for user-dominant scenarios
        User is in control, so: "I [action] you"
        """
        formatted = []
        for activity in activities:
            activity = activity.lower().strip()
            
            # Convert all activities to "I [action] you" format
            if 'me' in activity:
                # Convert "me" activities to "I [action] you"
                if 'tie me' in activity:
                    formatted.append("tie you up")
                elif 'gag me' in activity:
                    formatted.append("gag you")
                elif 'blindfold me' in activity:
                    formatted.append("blindfold you")
                elif 'undress me' in activity:
                    formatted.append("undress you slowly")
                elif 'tease me' in activity:
                    formatted.append("tease you")
                elif 'force me' in activity:
                    formatted.append("force you to have sex")
                elif 'go down' in activity or 'oral' in activity:
                    formatted.append("go down on you")
                elif 'command' in activity or 'instruct' in activity:
                    formatted.append("give you commands")
                else:
                    # Generic: convert "X me" to "X you"
                    converted = activity.replace(' me', ' you').replace(' my', ' your')
                    formatted.append(converted)
            elif 'them' in activity or 'they' in activity:
                # Convert "them/they" to "you" for direct roleplay
                converted = activity.replace('them', 'you').replace('they', 'you')
                if converted.startswith('go down'):
                    formatted.append("go down on you")
                else:
                    formatted.append(converted)
            else:
                # Activity without clear object - add proper subject/object
                if any(word in activity for word in ['tie', 'bind']):
                    formatted.append("tie you up")
                elif any(word in activity for word in ['gag']):
                    formatted.append("gag you")
                elif any(word in activity for word in ['blindfold']):
                    formatted.append("blindfold you")
                elif any(word in activity for word in ['undress', 'strip']):
                    formatted.append("undress you slowly")
                elif any(word in activity for word in ['tease']):
                    formatted.append("tease you")
                elif any(word in activity for word in ['force', 'rape']):
                    formatted.append("force you to have sex")
                elif any(word in activity for word in ['go down', 'oral']):
                    formatted.append("go down on you")
                elif any(word in activity for word in ['command', 'instruct', 'order']):
                    formatted.append("give you commands")
                elif any(word in activity for word in ['control', 'dominate']):
                    formatted.append("control you")
                else:
                    # Generic activity - make it "[action] you"
                    formatted.append(f"{activity} you")
        
        # Create natural narrative flow
        return self.create_natural_flow(formatted, "user_dominant")
    
    def format_activities_equal(self, activities: List[str]) -> str:
        """
        Format activities for equal control scenarios
        Both participate equally, so: "we [action]" or neutral phrasing
        """
        formatted = []
        for activity in activities:
            activity = activity.lower().strip()
            
            # Convert activities to mutual/equal format
            if 'me' in activity:
                # Convert "X me" to mutual activity
                if 'tie me' in activity:
                    formatted.append("bondage play")
                elif 'gag me' in activity:
                    formatted.append("gag play")
                elif 'blindfold me' in activity:
                    formatted.append("blindfold play")
                elif 'undress me' in activity:
                    formatted.append("undressing each other")
                elif 'tease me' in activity:
                    formatted.append("teasing each other")
                elif 'force me' in activity:
                    formatted.append("intense passion")
                elif 'command' in activity or 'instruct' in activity:
                    formatted.append("power exchange")
                else:
                    # Generic: make it mutual
                    base_activity = activity.replace(' me', '').replace(' my', '')
                    formatted.append(f"{base_activity} together")
            elif 'them' in activity or 'they' in activity:
                # Convert to mutual
                base_activity = activity.replace('them', '').replace('they', '').strip()
                formatted.append(f"{base_activity} together")
            else:
                # Activity without clear subject/object - make it mutual
                if any(word in activity for word in ['tie', 'bind']):
                    formatted.append("bondage play")
                elif any(word in activity for word in ['gag']):
                    formatted.append("gag play")
                elif any(word in activity for word in ['blindfold']):
                    formatted.append("blindfold play")
                elif any(word in activity for word in ['undress', 'strip']):
                    formatted.append("undressing each other")
                elif any(word in activity for word in ['tease']):
                    formatted.append("teasing each other")
                elif any(word in activity for word in ['force', 'rape']):
                    formatted.append("intense passion")
                elif any(word in activity for word in ['command', 'instruct', 'order']):
                    formatted.append("power exchange")
                elif any(word in activity for word in ['control', 'dominate']):
                    formatted.append("power play")
                else:
                    # Generic activity - keep as is or make mutual
                    if len(activity.split()) == 1:
                        formatted.append(f"{activity} together")
                    else:
                        formatted.append(activity)
        
        # Create natural narrative flow
        return self.create_natural_flow(formatted, "equal")
    
    def create_natural_flow(self, activities: List[str], control_type: str) -> str:
        """
        Create natural narrative flow instead of robotic lists
        """
        if not activities:
            return ""
        
        if len(activities) == 1:
            if control_type == "user_dominant":
                return f"I {activities[0]}"
            else:
                return activities[0]
        
        elif len(activities) == 2:
            if control_type == "user_dominant":
                return f"I {activities[0]} and {activities[1]}"
            elif control_type == "partner_dominant":
                return f"{activities[0]} and {activities[1]}"
            else:
                return f"{activities[0]} and {activities[1]}"
        
        else:  # 3+ activities - create natural sequence
            if control_type == "user_dominant":
                # Create flowing narrative for user dominance
                first = activities[0]
                middle = activities[1:-1]
                last = activities[-1]
                
                if len(middle) == 0:
                    return f"I start by {self.add_ing(first)}, then {last}"
                elif len(middle) == 1:
                    return f"I start by {self.add_ing(first)}, then {middle[0]} before {self.add_ing(last)}"
                else:
                    middle_text = ", ".join(middle)
                    return f"I start by {self.add_ing(first)}, then {middle_text} before {self.add_ing(last)}"
            
            elif control_type == "partner_dominant":
                # Create flowing narrative for partner dominance
                first = activities[0]
                middle = activities[1:-1]
                last = activities[-1]
                
                if len(middle) == 0:
                    return f"{first}, then {last}"
                elif len(middle) == 1:
                    return f"{first}, then {middle[0]} before {last}"
                else:
                    middle_text = ", ".join(middle)
                    return f"{first}, then {middle_text} before {last}"
            
            else:  # equal control
                # Simple joining for mutual activities
                return f"{', '.join(activities[:-1])}, and {activities[-1]}"
    
    def add_ing(self, verb_phrase: str) -> str:
        """
        Convert verb phrase to -ing form for natural flow
        """
        verb_phrase = verb_phrase.strip()
        
        # Handle common patterns
        if verb_phrase.startswith('go down on'):
            return 'going down on you'
        elif verb_phrase.startswith('tie you'):
            return 'tying you up'
        elif verb_phrase.startswith('gag you'):
            return 'gagging you'
        elif verb_phrase.startswith('undress you'):
            return 'undressing you'
        elif verb_phrase.startswith('tease you'):
            return 'teasing you'
        elif verb_phrase.startswith('blindfold you'):
            return 'blindfolding you'
        elif verb_phrase.startswith('force you'):
            return 'forcing you to have sex'
        elif verb_phrase.startswith('give you'):
            return 'giving you commands'
        elif verb_phrase.endswith(' you'):
            # Generic: "action you" -> "actioning you"
            base = verb_phrase[:-4]  # Remove " you"
            if base.endswith('e'):
                return f"{base[:-1]}ing you"
            else:
                return f"{base}ing you"
        else:
            # Fallback: just add -ing to the first word
            words = verb_phrase.split()
            if words:
                first_word = words[0]
                if first_word.endswith('e'):
                    first_word = first_word[:-1] + 'ing'
                else:
                    first_word = first_word + 'ing'
                return ' '.join([first_word] + words[1:])
            return verb_phrase


def generate_flexible_scenario(form_data: Dict) -> str:
    """
    Main function to generate scenario from any custom Tally form
    
    Args:
        form_data: Dictionary containing Tally form submission data
        
    Returns:
        str: Generated narrative scenario
    """
    if not form_data:
        return ""
    
    try:
        extractor = FlexibleTallyExtractor(form_data)
        return extractor.create_narrative_scenario()
    except Exception as e:
        # Fallback: try to extract any meaningful text from the form
        try:
            return extract_fallback_scenario(form_data)
        except:
            return ""


def extract_fallback_scenario(form_data: Dict) -> str:
    """
    Fallback extraction when main extraction fails
    Just concatenate any meaningful text found in the form
    """
    meaningful_texts = []
    
    if 'fields' in form_data:
        for field in form_data['fields']:
            label = field.get('label', '')
            value = field.get('value', [])
            
            # Skip empty or very short values
            if not value or (isinstance(value, list) and not any(value)):
                continue
            
            # Process value
            if isinstance(value, list):
                value_text = ', '.join(str(v) for v in value if v and str(v).strip())
            else:
                value_text = str(value).strip()
            
            if len(value_text) > 2:  # Only meaningful content
                meaningful_texts.append(value_text)
    
    if meaningful_texts:
        return f"In this scenario: {' '.join(meaningful_texts[:3])}."  # Limit to first 3 meaningful items
    
    return ""