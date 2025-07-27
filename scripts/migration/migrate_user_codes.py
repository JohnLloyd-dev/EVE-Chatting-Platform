#!/usr/bin/env python3
"""
Migration script to add user_code column and populate it
"""

import sys
import os
sys.path.append('/app')

from sqlalchemy import create_engine, text
from database import SessionLocal, User
from config import settings

def migrate_user_codes():
    """Add user_code column and populate it for existing users"""
    
    # Create engine and session
    engine = create_engine(settings.database_url)
    db = SessionLocal()
    
    try:
        print("Starting user codes migration...")
        
        # Check if user_code column exists
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'user_code';
            """))
            column_exists = result.fetchone() is not None
        
        if not column_exists:
            print("Adding user_code column...")
            with engine.connect() as connection:
                with connection.begin():
                    connection.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN user_code VARCHAR(20);
                    """))
            print("Column added successfully!")
        else:
            print("user_code column already exists")
        
        # Get all users without user_code
        users_without_code = db.query(User).filter(
            (User.user_code.is_(None)) | (User.user_code == '')
        ).all()
        print(f"Found {len(users_without_code)} users without user codes")
        
        if users_without_code:
            # Find the highest existing user code number
            existing_codes = db.query(User.user_code).filter(
                User.user_code.like('EVE%')
            ).all()
            
            max_num = 0
            for (code,) in existing_codes:
                if code and code.startswith('EVE'):
                    try:
                        num = int(code[3:])
                        max_num = max(max_num, num)
                    except ValueError:
                        continue
            
            # Assign codes starting from max_num + 1
            for i, user in enumerate(users_without_code, max_num + 1):
                user_code = f"EVE{i:03d}"
                
                # Make sure code doesn't exist
                while db.query(User).filter(User.user_code == user_code).first():
                    i += 1
                    user_code = f"EVE{i:03d}"
                
                user.user_code = user_code
                print(f"Assigned {user_code} to user {user.id}")
            
            # Commit all changes
            db.commit()
            print("User codes assigned successfully!")
        
        # Make the column NOT NULL
        print("Making user_code column NOT NULL...")
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(text("""
                    ALTER TABLE users 
                    ALTER COLUMN user_code SET NOT NULL;
                """))
                
                # Add unique constraint (check if it exists first)
                try:
                    connection.execute(text("""
                        ALTER TABLE users 
                        ADD CONSTRAINT users_user_code_unique UNIQUE (user_code);
                    """))
                    print("Unique constraint added successfully!")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print("Unique constraint already exists, skipping...")
                    else:
                        raise
                
                # Add index for better performance
                try:
                    connection.execute(text("""
                        CREATE INDEX idx_users_user_code ON users(user_code);
                    """))
                    print("Index created successfully!")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print("Index already exists, skipping...")
                    else:
                        print(f"Index creation warning: {e}")
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_user_codes()