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
    
    # Extract relevant information from form data
    scenario_parts = []
    
    # Try to extract common form fields
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