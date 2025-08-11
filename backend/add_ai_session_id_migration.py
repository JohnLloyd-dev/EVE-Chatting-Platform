#!/usr/bin/env python3
"""
Migration script to add ai_session_id field to chat_sessions table
"""
import os
import sys
from sqlalchemy import create_engine, text
from config import settings

def run_migration():
    """Add ai_session_id column to chat_sessions table"""
    try:
        # Create engine
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'chat_sessions' 
                AND column_name = 'ai_session_id'
            """))
            
            if result.fetchone():
                print("✅ ai_session_id column already exists")
                return
            
            # Add the column
            print("🔄 Adding ai_session_id column to chat_sessions table...")
            conn.execute(text("""
                ALTER TABLE chat_sessions 
                ADD COLUMN ai_session_id VARCHAR(255)
            """))
            
            # Commit the change
            conn.commit()
            print("✅ Successfully added ai_session_id column")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration() 