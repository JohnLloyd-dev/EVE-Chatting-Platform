#!/usr/bin/env python3
"""
Migration script to add ai_responses_enabled column to users table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from config import settings

def run_migration():
    """Add ai_responses_enabled column to users table"""
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'ai_responses_enabled'
            """)).fetchone()
            
            if result:
                print("✅ Column ai_responses_enabled already exists in users table")
                return
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN ai_responses_enabled BOOLEAN DEFAULT TRUE
            """))
            
            # Update existing users to have AI responses enabled by default
            conn.execute(text("""
                UPDATE users 
                SET ai_responses_enabled = TRUE 
                WHERE ai_responses_enabled IS NULL
            """))
            
            conn.commit()
            print("✅ Successfully added ai_responses_enabled column to users table")
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()