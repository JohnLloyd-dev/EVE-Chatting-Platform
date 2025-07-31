#!/usr/bin/env python3
"""
Comprehensive migration runner that creates missing tables and columns
"""

import sys
import os

try:
    import psycopg2
    from config import settings
    
    def run_migration():
        """Run all necessary database migrations"""
        
        # Parse database URL
        db_url = settings.database_url
        # Handle both postgresql:// and postgres:// schemes
        if db_url.startswith('postgresql://'):
            db_url = db_url[13:]  # Remove postgresql://
        elif db_url.startswith('postgres://'):
            db_url = db_url[11:]  # Remove postgres://
        
        parts = db_url.split('@')
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        host_port = host_db[0].split(':')
        
        user = user_pass[0]
        password = user_pass[1]
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 5432
        database = host_db[1]
        
        print(f"Connecting to database: {host}:{port}/{database} as {user}")
        
        try:
            # Connect to database
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            )
            
            cursor = conn.cursor()
            
            # Migration 1: Add ai_responses_enabled column to users table
            print("🔄 Checking ai_responses_enabled column...")
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'ai_responses_enabled'
            """)
            
            result = cursor.fetchone()
            
            if not result:
                print("🔄 Adding ai_responses_enabled column to users table...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN ai_responses_enabled BOOLEAN DEFAULT TRUE
                """)
                
                # Update existing users to have AI responses enabled by default
                cursor.execute("""
                    UPDATE users 
                    SET ai_responses_enabled = TRUE 
                    WHERE ai_responses_enabled IS NULL
                """)
                print("✅ Successfully added ai_responses_enabled column to users table")
            else:
                print("✅ Column ai_responses_enabled already exists in users table")
            
            # Migration 2: Create active_ai_tasks table if it doesn't exist
            print("🔄 Checking active_ai_tasks table...")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'active_ai_tasks'
            """)
            
            result = cursor.fetchone()
            
            if not result:
                print("🔄 Creating active_ai_tasks table...")
                cursor.execute("""
                    CREATE TABLE active_ai_tasks (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        task_id VARCHAR(255) UNIQUE NOT NULL,
                        session_id UUID NOT NULL REFERENCES chat_sessions(id),
                        user_id UUID NOT NULL REFERENCES users(id),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        is_cancelled BOOLEAN DEFAULT FALSE
                    )
                """)
                print("✅ Successfully created active_ai_tasks table")
            else:
                print("✅ Table active_ai_tasks already exists")
            
            # Migration 3: Check if system_prompts table exists and has all required columns
            print("🔄 Checking system_prompts table...")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'system_prompts'
            """)
            
            result = cursor.fetchone()
            
            if not result:
                print("🔄 Creating system_prompts table...")
                cursor.execute("""
                    CREATE TABLE system_prompts (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(255) NOT NULL,
                        content TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT FALSE,
                        admin_id UUID REFERENCES admin_users(id),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        user_id UUID REFERENCES users(id)
                    )
                """)
                print("✅ Successfully created system_prompts table")
            else:
                print("✅ Table system_prompts already exists")
            
            conn.commit()
            print("🎉 All migrations completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    if __name__ == "__main__":
        run_migration()
        
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Please install required packages or run this from the backend environment")
    sys.exit(1)