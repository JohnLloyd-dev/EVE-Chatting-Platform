#!/usr/bin/env python3
"""
Fix user codes migration - handle the current state
"""

from sqlalchemy import create_engine, text
from database import SessionLocal, User
from config import settings

def fix_user_codes():
    """Fix user codes for the current database state"""
    
    # Create engine and session
    engine = create_engine(settings.database_url)
    db = SessionLocal()
    
    try:
        print("Checking current database state...")
        
        # Check if user_code column exists and has data
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT column_name, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'user_code';
            """))
            column_info = result.fetchone()
            
            if not column_info:
                print("user_code column doesn't exist, creating it...")
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN user_code VARCHAR(20);
                """))
                print("Column created!")
            else:
                print(f"user_code column exists: nullable={column_info[1]}")
        
        # Get all users without user_code
        users_without_code = db.query(User).filter(
            (User.user_code.is_(None)) | (User.user_code == '')
        ).all()
        print(f"Found {len(users_without_code)} users without user codes")
        
        # Generate user codes for users that need them
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
        
        # Try to add constraints if they don't exist
        print("Adding constraints...")
        with engine.connect() as connection:
            with connection.begin():
                # Try to make NOT NULL
                try:
                    connection.execute(text("""
                        ALTER TABLE users 
                        ALTER COLUMN user_code SET NOT NULL;
                    """))
                    print("Column set to NOT NULL")
                except Exception as e:
                    print(f"NOT NULL constraint: {e}")
                
                # Try to add unique constraint
                try:
                    connection.execute(text("""
                        ALTER TABLE users 
                        ADD CONSTRAINT users_user_code_unique UNIQUE (user_code);
                    """))
                    print("Unique constraint added")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print("Unique constraint already exists")
                    else:
                        print(f"Unique constraint error: {e}")
                
                # Try to add index
                try:
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_users_user_code ON users(user_code);
                    """))
                    print("Index created")
                except Exception as e:
                    print(f"Index error: {e}")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_user_codes()