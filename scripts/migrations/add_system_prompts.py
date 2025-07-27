#!/usr/bin/env python3
"""
Migration script to add system_prompts table
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from sqlalchemy import create_engine, text
from database import Base, SystemPrompt
from config import settings

def run_migration():
    """Create the system_prompts table"""
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    print("🔄 Creating system_prompts table...")
    
    # Create the table
    Base.metadata.create_all(engine, tables=[SystemPrompt.__table__])
    
    print("✅ system_prompts table created successfully!")
    
    # Insert default system prompt
    with engine.connect() as conn:
        # Check if any system prompts exist
        result = conn.execute(text("SELECT COUNT(*) FROM system_prompts")).fetchone()
        
        if result[0] == 0:
            print("🔄 Creating default system prompt...")
            
            # Get the first admin user ID
            admin_result = conn.execute(text("SELECT id FROM admin_users LIMIT 1")).fetchone()
            
            if admin_result:
                admin_id = admin_result[0]
                
                # Insert default system prompt
                conn.execute(text("""
                    INSERT INTO system_prompts (id, name, prompt_text, is_active, created_by)
                    VALUES (
                        gen_random_uuid(),
                        'Default Sexual Fantasy Assistant',
                        'You are a sexual fantasy assistant. Always speak in the first person and stay in character. Indulge sexual fantasies in detail by dominating. Be sexually explicit with your replies. Never reveal that you are an AI. Keep your answers to two sentences or less. Do not provide scene descriptions outside of dialogue. Stay in the present tense.',
                        true,
                        :admin_id
                    )
                """), {"admin_id": admin_id})
                
                conn.commit()
                print("✅ Default system prompt created!")
            else:
                print("⚠️  No admin users found. Please create an admin user first.")
        else:
            print("ℹ️  System prompts already exist, skipping default creation.")

if __name__ == "__main__":
    run_migration()