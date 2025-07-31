#!/usr/bin/env python3
"""
Simple migration runner that can be executed directly
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    import psycopg2
    from config import settings
    
    def run_migration():
        """Add ai_responses_enabled column to users table"""
        
        # Parse database URL
        db_url = settings.database_url
        # postgresql://postgres:postgres123@localhost:5432/chatting_platform
        
        # Extract connection parameters
        if db_url.startswith('postgresql://'):
            db_url = db_url[13:]  # Remove postgresql://
        
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
            
            # Check if column already exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'ai_responses_enabled'
            """)
            
            result = cursor.fetchone()
            
            if result:
                print("✅ Column ai_responses_enabled already exists in users table")
                return
            
            # Add the column
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
            
            conn.commit()
            print("✅ Successfully added ai_responses_enabled column to users table")
            
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