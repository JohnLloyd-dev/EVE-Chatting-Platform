"""
Extract and process Tally form data to generate story scenarios
"""

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
        fields = tally_data.get('fields', [])
        
        # Parse Tally form fields
        parsed_answers = {}
        for field in fields:
            if field.get('value') and field.get('label'):
                label = field['label'].strip()
                value = field['value']
                
                # Handle multiple choice answers
                if isinstance(value, list) and len(value) > 0:
                    # Find the selected option text
                    selected_option_id = value[0]
                    options = field.get('options', [])
                    for option in options:
                        if option.get('id') == selected_option_id:
                            parsed_answers[label] = option.get('text', '')
                            break
                else:
                    parsed_answers[label] = str(value)
        
        # Generate scenario based on parsed answers
        scenario_parts = []
        
        # Look for gender/character information
        for label, answer in parsed_answers.items():
            if 'fantasy' in label.lower() and ('man' in label.lower() or 'woman' in label.lower()):
                scenario_parts.append(f"In this fantasy scenario, you are a {answer.lower()}.")
            elif 'gender' in label.lower() and 'other person' in label.lower():
                scenario_parts.append(f"The other person in this scenario is a {answer.lower()}.")
            elif 'old' in label.lower() and 'they' in label.lower():
                scenario_parts.append(f"They are approximately {answer} years old.")
            elif 'ethnicity' in label.lower():
                scenario_parts.append(f"Their ethnicity is {answer}.")
        
        # Create the final scenario
        if scenario_parts:
            scenario = " ".join(scenario_parts) + " Let's explore this fantasy scenario together. What would you like to happen next?"
        else:
            # Fallback for forms we don't recognize
            scenario = f"Based on your form responses, I'm ready to engage in a personalized conversation with you. What would you like to discuss?"
    
    else:
        # Handle simple key-value form data
        scenario_parts = []
        
        if isinstance(form_data, dict):
            # Look for name fields
            name = form_data.get('name') or form_data.get('Name') or form_data.get('full_name')
            if name:
                scenario_parts.append(f"Hello {name}!")
            
            # Look for age or demographic info
            age = form_data.get('age') or form_data.get('Age')
            if age:
                scenario_parts.append(f"I understand you're {age} years old.")
            
            # Look for interests or topics
            interests = form_data.get('interests') or form_data.get('topics') or form_data.get('preferences')
            if interests:
                scenario_parts.append(f"I see you're interested in {interests}.")
            
            # Look for specific questions or concerns
            question = form_data.get('question') or form_data.get('concern') or form_data.get('topic')
            if question:
                scenario_parts.append(f"You mentioned: {question}")
        
        # If we have specific information, create a personalized scenario
        if scenario_parts:
            scenario = " ".join(scenario_parts) + " How can I help you today?"
        else:
            # Default scenario if no specific data is available
            scenario = "Welcome! I'm here to help you with any questions or conversations you'd like to have. What would you like to talk about?"
    
    return scenario