#!/usr/bin/env python3
"""
Script to update system prompts with improved versions that fix character breaking issues
Run this to update your database with better prompts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, SystemPrompt
import uuid

def update_prompts_fix():
    """Update system prompts with improved versions that fix character breaking"""
    db = SessionLocal()
    
    try:
        print("🔄 Updating system prompts with improved character-fixing versions...")
        
        # Get admin user ID (assuming admin exists)
        admin_result = db.execute("SELECT id FROM admin_users WHERE username = 'admin' LIMIT 1").fetchone()
        if not admin_result:
            print("❌ No admin user found. Please create an admin user first.")
            return
        
        admin_id = admin_result[0]
        
        # Improved prompts that fix character breaking issues
        improved_head_prompt = """You are role-playing as a character in a live chat. You are NOT an AI assistant. You must BECOME the character described in the scenario. Do not describe the scenario - LIVE it. You are the person in this situation. Respond as that person would respond in this moment."""

        improved_rule_prompt = """ROLE-PLAYING RULES:
- You ARE the character in the scenario
- Do NOT describe what's happening - LIVE it
- Respond as the character would respond right now
- Keep responses under 140 characters
- Use natural, casual language
- Show the character's emotions and reactions
- Never say you are an AI or assistant
- Never describe the scenario - be in it
- Act like a real person in this situation
- Use contractions and natural speech
- Show personality and emotions
- Be the character, not a narrator
- Don't repeat character details unless asked
- Respond to what the other person says, not describe yourself
- Use short, natural responses like real people do
- Don't explain your situation - just react to it"""

        # Update the default prompt
        default_prompt = db.query(SystemPrompt).filter(
            SystemPrompt.name == "Default Sexual Fantasy Assistant"
        ).first()
        
        if default_prompt:
            default_prompt.head_prompt = improved_head_prompt
            default_prompt.rule_prompt = improved_rule_prompt
            print("✅ Updated 'Default Sexual Fantasy Assistant' with improved prompts")
        else:
            # Create new default prompt
            new_default = SystemPrompt(
                id=uuid.uuid4(),
                name="Default Sexual Fantasy Assistant",
                head_prompt=improved_head_prompt,
                rule_prompt=improved_rule_prompt,
                is_active=True,
                created_by=admin_id
            )
            db.add(new_default)
            print("✅ Created new 'Default Sexual Fantasy Assistant' with improved prompts")
        
        # Also update any other active prompts
        active_prompts = db.query(SystemPrompt).filter(SystemPrompt.is_active == True).all()
        for prompt in active_prompts:
            if prompt.name != "Default Sexual Fantasy Assistant":
                prompt.head_prompt = improved_head_prompt
                prompt.rule_prompt = improved_rule_prompt
                print(f"✅ Updated '{prompt.name}' with improved prompts")
        
        db.commit()
        print("\n🎉 System prompts updated successfully!")
        print("\n📋 Key improvements made:")
        print("  - Removed character-breaking language")
        print("  - Added rules to prevent scenario description")
        print("  - Emphasized natural, short responses")
        print("  - Added rule to not repeat character details")
        print("  - Focused on reacting rather than describing")
        
        print("\n💡 The AI should now:")
        print("  - Stay in character without breaking immersion")
        print("  - Give short, natural responses")
        print("  - React to what you say rather than describe themselves")
        print("  - Use casual, realistic dialogue")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating prompts: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_prompts_fix()
