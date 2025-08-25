#!/usr/bin/env python3
"""
Advanced script to update system prompts with highly optimized versions
This should completely fix character breaking and get natural responses
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, SystemPrompt
import uuid

def update_prompts_advanced():
    """Update system prompts with advanced versions for perfect character immersion"""
    db = SessionLocal()
    
    try:
        print("🔄 Updating system prompts with advanced character immersion versions...")
        
        # Get admin user ID
        admin_result = db.execute("SELECT id FROM admin_users WHERE username = 'admin' LIMIT 1").fetchone()
        if not admin_result:
            print("❌ No admin user found. Please create an admin user first.")
            return
        
        admin_id = admin_result[0]
        
        # Advanced head prompt - very direct and clear
        advanced_head_prompt = """You are a real person in a live chat conversation. You are NOT an AI. You are the character described in the scenario. You are living this moment right now. Respond exactly as this person would respond in this situation."""

        # Advanced rule prompt - very specific about what NOT to do
        advanced_rule_prompt = """CRITICAL RULES - FOLLOW EXACTLY:
- You ARE the character - not an AI, not an assistant
- NEVER say "I'm not an AI" or "I'm a real person" - just BE the character
- NEVER describe your character or situation - just respond naturally
- Keep responses under 100 characters - short and natural
- Use casual language with contractions (I'm, you're, don't, etc.)
- Respond to what the other person says - don't describe yourself
- Show emotion through your words, not by describing emotions
- Don't repeat character details - just react to the moment
- Be the person in the situation, not someone describing the situation
- Use natural speech patterns - like a real person would talk
- Don't explain or narrate - just respond as the character would
- Focus on the immediate interaction, not background details"""

        # Update or create the main prompt
        main_prompt = db.query(SystemPrompt).filter(
            SystemPrompt.name == "Default Sexual Fantasy Assistant"
        ).first()
        
        if main_prompt:
            main_prompt.head_prompt = advanced_head_prompt
            main_prompt.rule_prompt = advanced_rule_prompt
            print("✅ Updated 'Default Sexual Fantasy Assistant' with advanced prompts")
        else:
            new_main = SystemPrompt(
                id=uuid.uuid4(),
                name="Default Sexual Fantasy Assistant",
                head_prompt=advanced_head_prompt,
                rule_prompt=advanced_rule_prompt,
                is_active=True,
                created_by=admin_id
            )
            db.add(new_main)
            print("✅ Created new 'Default Sexual Fantasy Assistant' with advanced prompts")
        
        # Create a "Natural Response" variant
        natural_prompt = db.query(SystemPrompt).filter(
            SystemPrompt.name == "Natural Response Partner"
        ).first()
        
        if natural_prompt:
            natural_prompt.head_prompt = advanced_head_prompt
            natural_prompt.rule_prompt = advanced_rule_prompt
            print("✅ Updated 'Natural Response Partner' with advanced prompts")
        else:
            new_natural = SystemPrompt(
                id=uuid.uuid4(),
                name="Natural Response Partner",
                head_prompt=advanced_head_prompt,
                rule_prompt=advanced_rule_prompt,
                is_active=False,
                created_by=admin_id
            )
            db.add(new_natural)
            print("✅ Created 'Natural Response Partner' with advanced prompts")
        
        # Update all active prompts
        active_prompts = db.query(SystemPrompt).filter(SystemPrompt.is_active == True).all()
        for prompt in active_prompts:
            if prompt.name not in ["Default Sexual Fantasy Assistant", "Natural Response Partner"]:
                prompt.head_prompt = advanced_head_prompt
                prompt.rule_prompt = advanced_rule_prompt
                print(f"✅ Updated '{prompt.name}' with advanced prompts")
        
        db.commit()
        print("\n🎉 Advanced prompts updated successfully!")
        print("\n🔧 Key improvements:")
        print("  - Removed ALL character-breaking phrases")
        print("  - Emphasized being the character, not describing them")
        print("  - Limited response length to 100 characters")
        print("  - Focused on natural speech patterns")
        print("  - Prevented scenario description and narration")
        print("  - Emphasized immediate reactions over explanations")
        
        print("\n💡 Expected behavior:")
        print("  - Short, natural responses (under 100 chars)")
        print("  - No character description or narration")
        print("  - Direct responses to what you say")
        print("  - Natural speech with contractions")
        print("  - Emotional responses without describing emotions")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating prompts: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_prompts_advanced()
