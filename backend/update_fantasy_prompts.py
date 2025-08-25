#!/usr/bin/env python3
"""
Script to update system prompts with optimized fantasy partner prompts
Run this to update your database with the new immersive prompts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, SystemPrompt
from optimized_prompts import FANTASY_PARTNER_PROMPTS
import uuid

def update_fantasy_prompts():
    """Update system prompts with optimized fantasy partner prompts"""
    db = SessionLocal()
    
    try:
        # Get the immersive partner prompt (recommended for most scenarios)
        head_prompt = FANTASY_PARTNER_PROMPTS["immersive_partner"]["head"]
        rule_prompt = FANTASY_PARTNER_PROMPTS["immersive_partner"]["rules"]
        
        # Check if prompt already exists
        existing_prompt = db.query(SystemPrompt).filter(
            SystemPrompt.name == "Optimized Fantasy Partner"
        ).first()
        
        if existing_prompt:
            # Update existing prompt
            existing_prompt.head_prompt = head_prompt
            existing_prompt.rule_prompt = rule_prompt
            print("✅ Updated existing 'Optimized Fantasy Partner' prompt")
        else:
            # Create new prompt
            new_prompt = SystemPrompt(
                id=uuid.uuid4(),
                name="Optimized Fantasy Partner",
                head_prompt=head_prompt,
                rule_prompt=rule_prompt,
                is_active=True,
                created_by=uuid.uuid4()  # You'll need to set this to an actual admin ID
            )
            db.add(new_prompt)
            print("✅ Created new 'Optimized Fantasy Partner' prompt")
        
        # Also create dominant and passionate variants
        variants = [
            ("Dominant Fantasy Partner", "dominant_partner"),
            ("Passionate Fantasy Partner", "passionate_partner")
        ]
        
        for name, key in variants:
            existing = db.query(SystemPrompt).filter(SystemPrompt.name == name).first()
            if existing:
                existing.head_prompt = FANTASY_PARTNER_PROMPTS[key]["head"]
                existing.rule_prompt = FANTASY_PARTNER_PROMPTS[key]["rules"]
                print(f"✅ Updated existing '{name}' prompt")
            else:
                new_variant = SystemPrompt(
                    id=uuid.uuid4(),
                    name=name,
                    head_prompt=FANTASY_PARTNER_PROMPTS[key]["head"],
                    rule_prompt=FANTASY_PARTNER_PROMPTS[key]["rules"],
                    is_active=False,  # Set to False by default
                    created_by=uuid.uuid4()  # You'll need to set this to an actual admin ID
                )
                db.add(new_variant)
                print(f"✅ Created new '{name}' prompt")
        
        db.commit()
        print("\n🎉 Successfully updated fantasy partner prompts!")
        print("\n📋 Available prompts:")
        print("1. 'Optimized Fantasy Partner' (ACTIVE) - Best for most scenarios")
        print("2. 'Dominant Fantasy Partner' - For dominant scenarios")
        print("3. 'Passionate Fantasy Partner' - For passionate scenarios")
        print("\n💡 To activate a different prompt, use the admin dashboard or set is_active=True")
        
    except Exception as e:
        print(f"❌ Error updating prompts: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_fantasy_prompts() 