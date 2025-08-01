"""
AI-Powered Tally Form Extractor
Uses the custom AI model to intelligently generate scenarios from any Tally form data
"""

import json
import logging
import httpx
from typing import Dict, List, Any, Optional
from config import settings

logger = logging.getLogger(__name__)

class AITallyExtractor:
    """
    AI-powered extractor that uses the custom AI model to generate scenarios
    from any Tally form structure without hardcoded rules
    """
    
    def __init__(self, form_data: Dict):
        self.form_data = form_data
        self.cleaned_data = self.clean_and_structure_data()
    
    def clean_and_structure_data(self) -> Dict[str, Any]:
        """
        Clean and structure the raw Tally data for AI processing
        Extracts meaningful information while preserving context
        """
        if not self.form_data or 'fields' not in self.form_data:
            return {}
        
        structured_data = {
            'form_metadata': {
                'form_id': self.form_data.get('formId'),
                'response_id': self.form_data.get('responseId'),
                'respondent_id': self.form_data.get('respondentId'),
                'created_at': self.form_data.get('createdAt')
            },
            'questions_and_answers': [],
            'summary': {
                'total_fields': 0,
                'answered_fields': 0,
                'field_types': set()
            }
        }
        
        for field in self.form_data['fields']:
            field_data = self.process_field(field)
            if field_data:
                structured_data['questions_and_answers'].append(field_data)
                structured_data['summary']['answered_fields'] += 1
            
            structured_data['summary']['total_fields'] += 1
            if field.get('type'):
                structured_data['summary']['field_types'].add(field['type'])
        
        # Convert set to list for JSON serialization
        structured_data['summary']['field_types'] = list(structured_data['summary']['field_types'])
        
        return structured_data
    
    def process_field(self, field: Dict) -> Optional[Dict]:
        """
        Process individual field and extract meaningful data
        """
        field_key = field.get('key', '')
        field_type = field.get('type', '')
        label = field.get('label', '').strip()
        raw_value = field.get('value')
        options = field.get('options', [])
        
        # Skip fields without labels or values
        if not label or not raw_value:
            return None
        
        processed_field = {
            'question': label,
            'field_type': field_type,
            'raw_value': raw_value
        }
        
        # Process value based on field type
        if field_type == 'MULTIPLE_CHOICE' and options:
            # Map selected option IDs to their text values
            if isinstance(raw_value, list):
                selected_texts = []
                option_map = {opt['id']: opt['text'] for opt in options}
                
                for value_id in raw_value:
                    if value_id in option_map:
                        selected_texts.append(option_map[value_id])
                
                if selected_texts:
                    processed_field['answer'] = selected_texts[0] if len(selected_texts) == 1 else selected_texts
                    processed_field['all_options'] = [opt['text'] for opt in options]
                else:
                    return None
            else:
                return None
        
        elif field_type in ['TEXTAREA', 'INPUT_TEXT', 'INPUT_EMAIL', 'INPUT_PHONE_NUMBER']:
            # Text-based fields
            if isinstance(raw_value, str) and raw_value.strip():
                processed_field['answer'] = raw_value.strip()
            elif isinstance(raw_value, list) and raw_value:
                processed_field['answer'] = ' '.join(str(v) for v in raw_value if v)
            else:
                return None
        
        elif field_type == 'PAYMENT':
            # Payment fields - just note that payment was made
            processed_field['answer'] = f"Payment: {raw_value}"
        
        else:
            # Other field types - try to extract meaningful value
            if isinstance(raw_value, list) and raw_value:
                processed_field['answer'] = raw_value[0] if len(raw_value) == 1 else raw_value
            elif raw_value:
                processed_field['answer'] = str(raw_value)
            else:
                return None
        
        return processed_field
    
    def create_ai_prompt(self) -> str:
        """
        Create a focused prompt that forces AI to use the actual form data
        """
        if not self.cleaned_data or not self.cleaned_data.get('questions_and_answers'):
            return ""
        
        # Extract key information from the form
        # Note: AI will be the "other person", user will be "I"
        user_gender = None          # What the user is (I am...)
        ai_gender = None           # What the AI is (You are... - the "other person")
        ai_age = None              # AI's age (the "other person's" age)
        ai_ethnicity = None        # AI's ethnicity (the "other person's" ethnicity)
        location = None
        control = None
        activities = []
        
        for qa in self.cleaned_data['questions_and_answers']:
            question = qa['question'].lower()
            answer = str(qa['answer']) if qa['answer'] else ""
            
            if 'fantasy are you a man or a woman' in question or 'are you a man or woman' in question:
                user_gender = answer  # This is what the USER is
            elif 'gender of the other person' in question or 'other person' in question:
                ai_gender = answer    # This is what the AI should be
            elif 'old' in question or 'age' in question:
                ai_age = answer       # This is the AI's age
            elif 'ethnicity' in question or 'race' in question:
                ai_ethnicity = answer # This is the AI's ethnicity
            elif 'where' in question or 'take place' in question or 'location' in question:
                location = answer
            elif 'who is in control' in question or 'control' in question:
                control = answer
            elif 'what would you like to do' in question or 'what else' in question:
                activities.append(answer)
        
        # Build a comprehensive template that uses all available data
        template_parts = []
        
        # AI character setup (the "other person" from the form)
        if ai_gender and ai_age:
            if ai_ethnicity:
                template_parts.append(f"You are a {ai_age} year old {ai_ethnicity.lower()} {ai_gender.lower()}.")
            else:
                template_parts.append(f"You are a {ai_age} year old {ai_gender.lower()}.")
        elif ai_gender:
            template_parts.append(f"You are a {ai_gender.lower()}.")
        elif ai_age:
            template_parts.append(f"You are {ai_age} years old.")
        elif ai_ethnicity:
            template_parts.append(f"You are {ai_ethnicity.lower()}.")
        
        # User and meeting context
        if user_gender and location:
            template_parts.append(f"I am a {user_gender.lower()} who meets you {location.lower()}.")
        elif user_gender:
            template_parts.append(f"I am a {user_gender.lower()}.")
        elif location:
            template_parts.append(f"We meet {location.lower()}.")
        
        # Control dynamic (from the user's perspective in the form)
        if control:
            if "you will be in control" in control.lower():
                # User said "you will be in control of me" - so AI is dominant
                template_parts.append("You are in control of me.")
            elif "i will be in control" in control.lower():
                # User said "I will be in control" - so user is dominant
                template_parts.append("I am in control of you.")
            else:
                template_parts.append("We share control equally.")
        
        # Activities (from user's perspective - what they want to happen)
        if activities:
            activity_text = " and ".join(activities[:2])
            template_parts.append(f"I want you to: {activity_text.lower()}.")
        
        if not template_parts:
            return "You are in a roleplay scenario with me."
        
        # Create a direct, factual scenario from the template
        scenario_text = " ".join(template_parts)
        
        # Simple prompt that just asks for natural flow without changing facts
        prompt_parts = [
            "Make this text flow naturally as one paragraph, but do not change any facts:",
            "",
            scenario_text
        ]
        
        return "\n".join(prompt_parts)
    
    def generate_scenario_with_ai(self) -> str:
        """
        Generate scenario directly from form data without AI interpretation
        This ensures 100% accuracy to the user's form responses
        """
        if not self.cleaned_data or not self.cleaned_data.get('questions_and_answers'):
            logger.warning("No meaningful data found in Tally form")
            return ""
        
        try:
            # Create the scenario directly from the form data
            scenario = self.create_direct_scenario()
            
            if scenario and len(scenario.strip()) > 10:
                logger.info(f"Successfully generated direct scenario: {len(scenario)} characters")
                return scenario.strip()
            else:
                logger.warning("No scenario could be generated from form data")
                return self.create_fallback_scenario()
                
        except Exception as e:
            logger.error(f"Failed to generate scenario: {str(e)}")
            return self.create_fallback_scenario()
    
    def create_direct_scenario(self) -> str:
        """
        Create scenario directly from form data without AI processing
        This ensures 100% accuracy to user responses
        """
        if not self.cleaned_data or not self.cleaned_data.get('questions_and_answers'):
            return ""
        
        # Extract key information using improved pattern matching
        info = self.extract_key_information(self.cleaned_data['questions_and_answers'])
        
        user_gender = info['user_gender']
        ai_gender = info['ai_gender']
        ai_age = info['ai_age']
        ai_ethnicity = info['ai_ethnicity']
        location = info['location']
        control = info['control']
        activities = info['activities']
        clothing = info['clothing']
        companion = info['companion']
        
        # Build the scenario directly
        scenario_parts = []
        
        # AI character description
        ai_description = "You are"
        if ai_age and ai_ethnicity and ai_gender:
            ai_description += f" a {ai_age} year old {ai_ethnicity.lower()} {ai_gender.lower()}"
        elif ai_age and ai_gender:
            ai_description += f" a {ai_age} year old {ai_gender.lower()}"
        elif ai_ethnicity and ai_gender:
            ai_description += f" a {ai_ethnicity.lower()} {ai_gender.lower()}"
        elif ai_age:
            ai_description += f" {ai_age} years old"
        elif ai_ethnicity:
            ai_description += f" {ai_ethnicity.lower()}"
        elif ai_gender:
            ai_description += f" a {ai_gender.lower()}"
        
        if ai_description != "You are":
            scenario_parts.append(ai_description + ".")
        else:
            scenario_parts.append("You are a person.")
        
        # User and context
        if user_gender:
            scenario_parts.append(f"I am a {user_gender.lower()}.")
        
        if location:
            scenario_parts.append(f"We meet {location.lower()}.")
        
        # Clothing information
        if clothing:
            scenario_parts.append(f"You are wearing {clothing.lower()}.")
        
        # Companion information
        if companion:
            companion_lower = companion.lower()
            if "another woman" in companion_lower:
                scenario_parts.append("Another woman is with us.")
            elif "another man" in companion_lower:
                scenario_parts.append("Another man is with us.")
            elif "group" in companion_lower:
                scenario_parts.append("We are in a group setting.")
            elif companion_lower == "yes":
                # "Yes" to "am I alone?" means they are alone - no additional text needed
                pass
            elif "no" in companion_lower:
                # "No" to "am I alone?" but no specific companion mentioned
                scenario_parts.append("We are not alone.")
        
        # Control dynamics
        if control:
            control_lower = control.lower()
            if any(phrase in control_lower for phrase in [
                "you will be in control", "you are in control of me", "they are in control"
            ]):
                scenario_parts.append("You are in control of me.")
            elif any(phrase in control_lower for phrase in [
                "i will be in control", "i am in control of you", "i am in control"
            ]):
                scenario_parts.append("I am in control of you.")
        
        # Activities (handle both single and multiple selections)
        if activities:
            all_activities = []
            for activity in activities:
                if isinstance(activity, list):
                    # Multiple selections
                    all_activities.extend(activity)
                else:
                    # Single selection
                    all_activities.append(activity)
            
            if all_activities:
                # Limit to most important activities and join naturally
                activity_text = ", ".join(all_activities[:3])  # Take up to 3 activities
                
                # Determine who performs the activities based on control dynamic
                user_controls = False
                equal_control = False
                
                if control:
                    control_lower = control.lower()
                    if any(phrase in control_lower for phrase in [
                        "i will be in control", "i am in control of you", "i am in control"
                    ]):
                        user_controls = True
                    elif any(phrase in control_lower for phrase in [
                        "we share control", "equal control", "we both", "shared control", 
                        "we switch control", "mutual control"
                    ]):
                        equal_control = True
                
                # Fix broken grammar first
                fixed_activity_text = self.fix_broken_grammar(activity_text)
                
                # Convert activities based on control dynamic
                if user_controls:
                    # User controls AI, so AI performs activities on User (following user's commands)
                    continuous_activities = self.convert_to_present_continuous_reverse(fixed_activity_text)
                    scenario_parts.append(f"You are {continuous_activities}.")
                elif equal_control:
                    # Equal control, so both participate together
                    continuous_activities = self.convert_to_present_continuous_mutual(fixed_activity_text)
                    scenario_parts.append(f"We are {continuous_activities}.")
                else:
                    # AI controls User, so User performs activities on AI
                    continuous_activities = self.convert_to_present_continuous(fixed_activity_text)
                    scenario_parts.append(f"I am {continuous_activities}.")
        
        return " ".join(scenario_parts)
    
    def convert_to_present_continuous(self, activity_text: str) -> str:
        """
        Convert activity text to present continuous tense
        """
        # Common conversions for sexual/romantic activities
        conversions = {
            'undress me slowly': 'undressing you slowly',
            'bring me close to orgasm then stop': 'bringing you close to orgasm then stopping',
            'kiss me passionately': 'kissing you passionately',
            'kiss me deeply': 'kissing you deeply',
            'touch me gently': 'touching you gently',
            'hold me close': 'holding you close',
            'whisper in my ear': 'whispering in your ear',
            'whisper to me': 'whispering to you',
            'massage me': 'massaging you',
            'tease me': 'teasing you',
            'caress me': 'caressing you',
            'embrace me': 'embracing you',
            'pleasure me': 'pleasuring you',
            'seduce me': 'seducing you',
            'dominate me': 'dominating you',
            'control me': 'controlling you',
            'guide me': 'guiding you',
            'lead me': 'leading you',
            'passionate kissing': 'kissing passionately',
            'intimate cuddling': 'cuddling intimately',
            'sensual massage': 'giving a sensual massage',
            'gentle touching': 'touching gently',
            'exploring each other': 'exploring each other',
            'playful teasing': 'teasing playfully'
        }
        
        # Split by comma and convert each activity
        activities = [act.strip() for act in activity_text.split(',')]
        converted_activities = []
        
        for activity in activities:
            activity_lower = activity.lower()
            
            # Check for direct conversions first
            converted = None
            for original, continuous in conversions.items():
                if original in activity_lower:
                    converted = continuous
                    break
            
            if not converted:
                # General conversion rules
                if activity_lower.endswith(' me'):
                    # "touch me" -> "touching you"
                    base_verb = activity_lower[:-3].strip()
                    if base_verb.endswith('e'):
                        converted = f"{base_verb[:-1]}ing you"
                    else:
                        converted = f"{base_verb}ing you"
                elif 'me' in activity_lower:
                    # Replace "me" with "you" and try to add -ing
                    converted = activity_lower.replace(' me ', ' you ').replace(' me,', ' you,').replace(' me.', ' you.')
                    # Try to convert first word to -ing form
                    words = converted.split()
                    if words:
                        first_word = words[0]
                        if first_word.endswith('e'):
                            words[0] = first_word[:-1] + 'ing'
                        else:
                            words[0] = first_word + 'ing'
                        converted = ' '.join(words)
                else:
                    # Default: try to add -ing to first word
                    words = activity.split()
                    if words:
                        first_word = words[0].lower()
                        if first_word.endswith('e'):
                            words[0] = first_word[:-1] + 'ing'
                        else:
                            words[0] = first_word + 'ing'
                        converted = ' '.join(words)
                    else:
                        converted = activity
            
            converted_activities.append(converted)
        
        return ', '.join(converted_activities)
    
    def fix_broken_grammar(self, activity_text: str) -> str:
        """
        Fix broken grammar in activity text from Tally forms
        """
        if isinstance(activity_text, list):
            # Handle list of activities
            fixed_activities = []
            for activity in activity_text:
                fixed_activities.append(self.fix_single_activity_grammar(str(activity)))
            return ', '.join(fixed_activities)
        else:
            return self.fix_single_activity_grammar(str(activity_text))
    
    def fix_single_activity_grammar(self, activity: str) -> str:
        """
        Fix grammar issues in a single activity string
        """
        # Common grammar fixes
        fixes = {
            'take your against your willl': 'take you against your will',
            'take your against your will': 'take you against your will',
            'punish you me': 'punish you',
            'blindfold you me': 'blindfold you',
            'gag you me': 'gag you',
            'your against your': 'you against your',
            'willl': 'will',
            'you me': 'you',
            'me you': 'you'
        }
        
        fixed_text = activity.lower().strip()
        
        # Apply specific fixes
        for broken, fixed in fixes.items():
            fixed_text = fixed_text.replace(broken, fixed)
        
        # Remove duplicate pronouns at the end
        if fixed_text.endswith(' me') and ' you' in fixed_text:
            # If it has both 'you' and ends with 'me', remove the 'me'
            if 'you' in fixed_text[:-3]:  # Check if 'you' appears before the final ' me'
                fixed_text = fixed_text[:-3].strip()
        
        return fixed_text
    
    def convert_to_present_continuous_reverse(self, activity_text: str) -> str:
        """
        Convert activity text to present continuous tense from AI's perspective
        When User controls AI, AI performs activities on User
        """
        # Handle comma-separated activities
        if ',' in activity_text:
            activities = [act.strip() for act in activity_text.split(',')]
            converted_activities = []
            for activity in activities:
                converted = self.convert_single_activity_reverse(activity)
                converted_activities.append(converted)
            return ', '.join(converted_activities)
        else:
            return self.convert_single_activity_reverse(activity_text)
    
    def convert_single_activity_reverse(self, activity_text: str) -> str:
        """
        Convert a single activity to present continuous tense from AI's perspective
        """
        # Reverse conversions - AI doing to User
        reverse_conversions = {
            'undress me slowly': 'undressing me slowly',
            'bring me close to orgasm then stop': 'bringing me close to orgasm then stopping',
            'kiss me passionately': 'kissing me passionately',
            'kiss me deeply': 'kissing me deeply',
            'touch me gently': 'touching me gently',
            'hold me close': 'holding me close',
            'whisper in my ear': 'whispering in my ear',
            'whisper to me': 'whispering to me',
            'massage me': 'massaging me',
            'tease me': 'teasing me',
            'caress me': 'caressing me',
            'embrace me': 'embracing me',
            'pleasure me': 'pleasuring me',
            'seduce me': 'seducing me',
            'dominate me': 'dominating me',
            'control me': 'controlling me',
            'guide me': 'guiding me',
            'lead me': 'leading me',
            'passionate kissing': 'kissing me passionately',
            'intimate cuddling': 'cuddling me intimately',
            'sensual massage': 'giving me a sensual massage',
            'gentle touching': 'touching me gently',
            'exploring each other': 'exploring me',
            'playful teasing': 'teasing me playfully',
            # Specific fixes for Tally data issues - AI doing to User
            'blindfold you': 'blindfolding me',
            'gag you': 'gagging me',
            'take you against your will': 'taking me against my will',
            'punish you': 'punishing me',
            'tie you up': 'tying me up',
            'instruct you': 'instructing me',
            'go down on you': 'going down on me',
            'caress you gently': 'caressing me gently'
        }
        
        activity_lower = activity_text.lower()
        
        # Check for direct conversions first
        converted = None
        for original, continuous in reverse_conversions.items():
            if original in activity_lower:
                converted = continuous
                break
        
        if not converted:
            # General conversion rules for reverse (AI doing to User)
            if activity_lower.endswith(' me'):
                # "touch me" -> "touching me" (AI touching User)
                base_verb = activity_lower[:-3].strip()
                if base_verb.endswith('e'):
                    converted = f"{base_verb[:-1]}ing me"
                else:
                    converted = f"{base_verb}ing me"
            elif 'you' in activity_lower:
                # Convert "you" to "me" since AI is doing to User
                words = activity_lower.split()
                if words:
                    first_word = words[0]
                    if first_word.endswith('e'):
                        words[0] = first_word[:-1] + 'ing'
                    else:
                        words[0] = first_word + 'ing'
                    # Replace "you" with "me"
                    converted_words = []
                    for word in words:
                        if word == 'you':
                            converted_words.append('me')
                        elif word == 'your':
                            converted_words.append('my')
                        else:
                            converted_words.append(word)
                    converted = ' '.join(converted_words)
            elif 'me' in activity_lower:
                # Keep "me" as is since AI is doing to User
                words = activity_lower.split()
                if words:
                    first_word = words[0]
                    if first_word.endswith('e'):
                        words[0] = first_word[:-1] + 'ing'
                    else:
                        words[0] = first_word + 'ing'
                    converted = ' '.join(words)
            else:
                # Default: try to add -ing to first word and add "me"
                words = activity_text.split()
                if words:
                    first_word = words[0].lower()
                    if first_word.endswith('e'):
                        words[0] = first_word[:-1] + 'ing'
                    else:
                        words[0] = first_word + 'ing'
                    converted = ' '.join(words) + ' me'
                else:
                    converted = activity_text
        
        return converted if converted else activity_text
    
    def convert_to_present_continuous_mutual(self, activity_text: str) -> str:
        """
        Convert activity text to present continuous tense for mutual/shared activities
        When control is equal, both participate together
        """
        # Mutual conversions - both doing together
        mutual_conversions = {
            'undress me slowly': 'undressing each other slowly',
            'bring me close to orgasm then stop': 'bringing each other close to orgasm then stopping',
            'kiss me passionately': 'kissing passionately',
            'kiss me deeply': 'kissing deeply',
            'touch me gently': 'touching each other gently',
            'hold me close': 'holding each other close',
            'whisper in my ear': 'whispering to each other',
            'whisper to me': 'whispering to each other',
            'massage me': 'massaging each other',
            'tease me': 'teasing each other',
            'caress me': 'caressing each other',
            'embrace me': 'embracing each other',
            'pleasure me': 'pleasuring each other',
            'seduce me': 'seducing each other',
            'dominate me': 'taking turns dominating',
            'control me': 'sharing control',
            'guide me': 'guiding each other',
            'lead me': 'taking turns leading',
            'passionate kissing': 'kissing passionately',
            'intimate cuddling': 'cuddling intimately',
            'sensual massage': 'giving each other sensual massages',
            'gentle touching': 'touching each other gently',
            'exploring each other': 'exploring each other',
            'playful teasing': 'teasing each other playfully'
        }
        
        # Split by comma and convert each activity
        activities = [act.strip() for act in activity_text.split(',')]
        converted_activities = []
        
        for activity in activities:
            activity_lower = activity.lower()
            
            # Check for direct conversions first
            converted = None
            for original, continuous in mutual_conversions.items():
                if original in activity_lower:
                    converted = continuous
                    break
            
            if not converted:
                # General conversion rules for mutual activities
                if activity_lower.endswith(' me'):
                    # "touch me" -> "touching each other"
                    base_verb = activity_lower[:-3].strip()
                    if base_verb.endswith('e'):
                        converted = f"{base_verb[:-1]}ing each other"
                    else:
                        converted = f"{base_verb}ing each other"
                elif 'me' in activity_lower:
                    # Replace "me" with "each other" and add -ing
                    converted = activity_lower.replace(' me ', ' each other ').replace(' me,', ' each other,').replace(' me.', ' each other.')
                    # Try to convert first word to -ing form
                    words = converted.split()
                    if words:
                        first_word = words[0]
                        if first_word.endswith('e'):
                            words[0] = first_word[:-1] + 'ing'
                        else:
                            words[0] = first_word + 'ing'
                        converted = ' '.join(words)
                else:
                    # Default: try to add -ing to first word
                    words = activity.split()
                    if words:
                        first_word = words[0].lower()
                        if first_word.endswith('e'):
                            words[0] = first_word[:-1] + 'ing'
                        else:
                            words[0] = first_word + 'ing'
                        converted = ' '.join(words)
                    else:
                        converted = activity
            
            converted_activities.append(converted)
        
        return ', '.join(converted_activities)
    
    def extract_key_information(self, questions_and_answers):
        """
        Extract key information from Q&A with improved pattern matching
        Enhanced to handle all 10 key data points from Tally form
        """
        user_gender = None
        ai_gender = None
        ai_age = None
        ai_ethnicity = None
        location = None
        control = None
        activities = []
        
        # New data points
        clothing = None
        companion = None
        pick_one_answers = []
        
        for qa in questions_and_answers:
            question = qa['question'].lower()
            answer = qa['answer'] if qa['answer'] else ""
            
            # User gender patterns
            if any(pattern in question for pattern in [
                'fantasy are you a man or a woman', 'are you a man or woman', 
                'your gender', 'you are a', 'are you male or female'
            ]):
                user_gender = str(answer) if not isinstance(answer, list) else str(answer[0])
            
            # AI gender patterns (the "other person")
            elif any(pattern in question for pattern in [
                'gender of the other person', 'other person', 'their gender',
                'he or she', 'man or woman they', 'gender are they'
            ]):
                ai_gender = str(answer) if not isinstance(answer, list) else str(answer[0])
            
            # AI age patterns
            elif any(pattern in question for pattern in [
                'old', 'age', 'years old', 'how old are they'
            ]):
                ai_age = str(answer) if not isinstance(answer, list) else str(answer[0])
            
            # AI ethnicity patterns  
            elif any(pattern in question for pattern in [
                'ethnicity', 'race', 'ethnic background', 'their race'
            ]):
                ai_ethnicity = str(answer) if not isinstance(answer, list) else str(answer[0])
            
            # Location patterns
            elif any(pattern in question for pattern in [
                'where', 'take place', 'location', 'place', 'setting'
            ]):
                location = str(answer) if not isinstance(answer, list) else str(answer[0])
            
            # Control patterns
            elif any(pattern in question for pattern in [
                'who is in control', 'control', 'dominant', 'submissive', 'in charge'
            ]):
                control = str(answer) if not isinstance(answer, list) else str(answer[0])
            
            # Companion patterns (who you are with)
            elif any(pattern in question for pattern in [
                'am i alone', 'are you alone', 'who are you with', 'with another'
            ]):
                companion = str(answer) if not isinstance(answer, list) else str(answer[0])
            
            # Pick One patterns (for clothing, etc.)
            elif 'pick one' in question:
                pick_one_answer = str(answer) if not isinstance(answer, list) else str(answer[0])
                pick_one_answers.append(pick_one_answer)
            
            # Activity patterns
            elif any(pattern in question for pattern in [
                'what would you like to do', 'what else', 'activity', 'activities',
                'what do you want', 'would you like them to', 'what should they do',
                'describe to me in detail', 'what would you like me to do'
            ]):
                activities.append(answer)  # Keep as-is to handle multiple selections
        
        # Map Pick One answers to clothing if we have them
        if pick_one_answers:
            # First Pick One is usually clothing
            if len(pick_one_answers) > 0:
                clothing_map = {
                    'A': 'Uniform',
                    'B': 'Bondage gear', 
                    'C': 'Best clothes',
                    'D': 'Underwear'
                }
                clothing = clothing_map.get(pick_one_answers[0], pick_one_answers[0])
        
        return {
            'user_gender': user_gender,
            'ai_gender': ai_gender,
            'ai_age': ai_age,
            'ai_ethnicity': ai_ethnicity,
            'location': location,
            'control': control,
            'activities': activities,
            'clothing': clothing,
            'companion': companion,
            'pick_one_answers': pick_one_answers
        }
    
    def call_ai_model_for_scenario(self, prompt: str) -> str:
        """
        Call the AI model API to generate a scenario
        Uses the same flow as the chat system: set scenario, then chat
        """
        try:
            with httpx.Client(timeout=30.0) as client:
                # First, set a system prompt for scenario generation
                scenario_generation_prompt = (
                    "You are a scenario generator that creates roleplay scenarios based STRICTLY on user form responses. "
                    "You must use ONLY the information provided in the form answers. "
                    "Do not add fantasy elements, made-up names, or details not specified by the user. "
                    "Use their exact gender choices, ages, ethnicities, locations, and activities. "
                    "Write realistic scenarios in second person (You are...) format."
                )
                
                scenario_response = client.post(
                    f"{settings.ai_model_url}/scenario",
                    json={"scenario": scenario_generation_prompt},
                    auth=(settings.ai_model_auth_username, settings.ai_model_auth_password)
                )
                
                if scenario_response.status_code != 200:
                    raise Exception(f"Failed to set scenario generation prompt: {scenario_response.text}")
                
                # Get session cookie
                session_cookie = scenario_response.cookies.get("session_id")
                if not session_cookie:
                    raise Exception("No session ID received from AI model")
                
                # Now send the user's form data as a chat message to generate the scenario
                chat_response = client.post(
                    f"{settings.ai_model_url}/chat",
                    json={
                        "message": prompt,
                        "max_tokens": 300  # Allow longer response for scenario generation
                    },
                    cookies={"session_id": session_cookie},
                    auth=(settings.ai_model_auth_username, settings.ai_model_auth_password)
                )
                
                if chat_response.status_code != 200:
                    raise Exception(f"AI model chat request failed: {chat_response.text}")
                
                response_data = chat_response.json()
                scenario = response_data.get("response", "")
                
                # Clean the response
                return self.clean_ai_response(scenario)
                
        except Exception as e:
            raise Exception(f"AI model call failed: {str(e)}")
    
    def clean_ai_response(self, raw_response: str) -> str:
        """
        Clean the AI response to extract only the scenario content
        """
        if not raw_response:
            return ""
        
        # Remove common AI response artifacts
        lines = raw_response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines at the start
            if not line and not cleaned_lines:
                continue
            
            # Stop at common AI markers or meta-commentary
            if any(marker in line.lower() for marker in [
                'generate the scenario now:',
                'here is the scenario:',
                'scenario:',
                'instructions:',
                'note:',
                'remember:',
                'important:'
            ]):
                continue
            
            # Skip lines that look like instructions or meta-commentary
            if line.startswith(('*', '-', '•')) and any(word in line.lower() for word in ['instruction', 'note', 'remember', 'important']):
                continue
            
            cleaned_lines.append(line)
        
        # Join and clean up
        scenario = '\n'.join(cleaned_lines).strip()
        
        # Remove any remaining instruction artifacts
        if scenario.lower().startswith('generate'):
            # Find the first sentence that doesn't start with instruction words
            sentences = scenario.split('.')
            for i, sentence in enumerate(sentences):
                if not any(word in sentence.lower() for word in ['generate', 'create', 'write', 'make']):
                    scenario = '.'.join(sentences[i:]).strip()
                    break
        
        return scenario
    
    def create_fallback_scenario(self) -> str:
        """
        Create a basic fallback scenario when AI generation fails
        """
        if not self.cleaned_data or not self.cleaned_data.get('questions_and_answers'):
            return ""
        
        # Extract basic information for a simple scenario
        scenario_parts = []
        character_details = []
        preferences = []
        
        for qa in self.cleaned_data['questions_and_answers']:
            question = qa['question'].lower()
            answer = qa['answer']
            
            if isinstance(answer, list):
                answer = answer[0] if answer else ""
            answer = str(answer)
            
            # Basic character building
            if 'gender' in question or 'man' in question or 'woman' in question:
                character_details.append(f"gender: {answer}")
            elif 'age' in question or 'old' in question:
                character_details.append(f"age: {answer}")
            elif 'ethnicity' in question or 'race' in question:
                character_details.append(f"ethnicity: {answer}")
            elif len(answer) > 5:  # Capture other meaningful responses
                preferences.append(answer)
        
        # Build basic scenario
        if character_details:
            scenario_parts.append(f"You are a character with the following traits: {', '.join(character_details)}.")
        
        if preferences:
            scenario_parts.append(f"The scenario involves: {', '.join(preferences[:3])}.")
        
        if scenario_parts:
            return " ".join(scenario_parts)
        else:
            return "You are in an interactive roleplay scenario."


def generate_ai_scenario(form_data: Dict) -> str:
    """
    Main function to generate scenario using AI from Tally form data
    
    Args:
        form_data: Dictionary containing Tally form submission data
        
    Returns:
        str: AI-generated scenario narrative
    """
    if not form_data:
        return ""
    
    try:
        extractor = AITallyExtractor(form_data)
        return extractor.generate_scenario_with_ai()
    except Exception as e:
        logger.error(f"AI scenario generation failed: {str(e)}")
        return ""


def debug_tally_data(form_data: Dict) -> Dict:
    """
    Debug function to inspect processed Tally data
    """
    if not form_data:
        return {"error": "No form data provided"}
    
    try:
        extractor = AITallyExtractor(form_data)
        return {
            "cleaned_data": extractor.cleaned_data,
            "ai_prompt": extractor.create_ai_prompt(),
            "summary": {
                "total_questions": len(extractor.cleaned_data.get('questions_and_answers', [])),
                "form_metadata": extractor.cleaned_data.get('form_metadata', {}),
                "field_types": extractor.cleaned_data.get('summary', {}).get('field_types', [])
            }
        }
    except Exception as e:
        return {"error": str(e)}