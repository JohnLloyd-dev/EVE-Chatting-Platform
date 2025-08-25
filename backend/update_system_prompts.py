#!/usr/bin/env python3
"""
Script to update system prompts with optimized versions for better AI responses
Run this to update your database with improved prompts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, SystemPrompt
from optimized_prompts import FANTASY_PARTNER_PROMPTS, RECOMMENDED_COMBINATIONS
import uuid

def update_system_prompts():
    """Update system prompts with optimized versions for better results"""
    db = SessionLocal()
    
    try:
        print("🔄 Updating system prompts with optimized versions...")
        
        # Get admin user ID (assuming admin exists)
        admin_result = db.execute("SELECT id FROM admin_users WHERE username = 'admin' LIMIT 1").fetchone()
        if not admin_result:
            print("❌ No admin user found. Please create an admin user first.")
            return
        
        admin_id = admin_result[0]
        
        # 1. Update the default prompt with the immersive partner version
        default_prompt = db.query(SystemPrompt).filter(
            SystemPrompt.name == "Default Sexual Fantasy Assistant"
        ).first()
        
        if default_prompt:
            # Use the immersive partner prompt (best for most scenarios)
            default_prompt.head_prompt = FANTASY_PARTNER_PROMPTS["immersive_partner"]["head"]
            default_prompt.rule_prompt = FANTASY_PARTNER_PROMPTS["immersive_partner"]["rules"]
            print("✅ Updated 'Default Sexual Fantasy Assistant' with immersive partner prompt")
        else:
            # Create new default prompt
            new_default = SystemPrompt(
                id=uuid.uuid4(),
                name="Default Sexual Fantasy Assistant",
                head_prompt=FANTASY_PARTNER_PROMPTS["immersive_partner"]["head"],
                rule_prompt=FANTASY_PARTNER_PROMPTS["immersive_partner"]["rules"],
                is_active=True,
                created_by=admin_id
            )
            db.add(new_default)
            print("✅ Created new 'Default Sexual Fantasy Assistant' with immersive partner prompt")
        
        # 2. Create additional optimized prompts
        additional_prompts = [
            {
                "name": "Dominant Fantasy Partner",
                "head": FANTASY_PARTNER_PROMPTS["dominant_partner"]["head"],
                "rules": FANTASY_PARTNER_PROMPTS["dominant_partner"]["rules"],
                "active": False
            },
            {
                "name": "Passionate Fantasy Partner", 
                "head": FANTASY_PARTNER_PROMPTS["passionate_partner"]["head"],
                "rules": FANTASY_PARTNER_PROMPTS["passionate_partner"]["rules"],
                "active": False
            }
        ]
        
        for prompt_data in additional_prompts:
            existing = db.query(SystemPrompt).filter(
                SystemPrompt.name == prompt_data["name"]
            ).first()
            
            if existing:
                existing.head_prompt = prompt_data["head"]
                existing.rule_prompt = prompt_data["rules"]
                print(f"✅ Updated '{prompt_data['name']}' prompt")
            else:
                new_prompt = SystemPrompt(
                    id=uuid.uuid4(),
                    name=prompt_data["name"],
                    head_prompt=prompt_data["head"],
                    rule_prompt=prompt_data["rules"],
                    is_active=prompt_data["active"],
                    created_by=admin_id
                )
                db.add(new_prompt)
                print(f"✅ Created '{prompt_data['name']}' prompt")
        
        # 3. Create a high-quality general assistant prompt
        general_prompt = db.query(SystemPrompt).filter(
            SystemPrompt.name == "High-Quality General Assistant"
        ).first()
        
        if not general_prompt:
            new_general = SystemPrompt(
                id=uuid.uuid4(),
                name="High-Quality General Assistant",
                head_prompt=RECOMMENDED_COMBINATIONS["balanced_quality"]["head"],
                rule_prompt=RECOMMENDED_COMBINATIONS["balanced_quality"]["rules"],
                is_active=False,
                created_by=admin_id
            )
            db.add(new_general)
            print("✅ Created 'High-Quality General Assistant' prompt")
        
        db.commit()
        print("\n🎉 System prompts updated successfully!")
        print("\n📋 Available prompts:")
        
        # List all prompts
        all_prompts = db.query(SystemPrompt).all()
        for prompt in all_prompts:
            status = "🟢 ACTIVE" if prompt.is_active else "⚪ INACTIVE"
            print(f"  - {prompt.name} ({status})")
        
        print(f"\n💡 To activate a different prompt, use the admin dashboard or run:")
        print(f"   UPDATE system_prompts SET is_active = false WHERE is_active = true;")
        print(f"   UPDATE system_prompts SET is_active = true WHERE name = 'Your Preferred Prompt Name';")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating prompts: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_system_prompts() 