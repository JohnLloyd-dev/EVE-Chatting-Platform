#!/usr/bin/env python3
"""
Migration script to add user_code column and populate it for existing users
"""

from sqlalchemy import create_engine, text
from database import SessionLocal, User
from config import settings

def migrate_user_codes():
    """Add user_code column and populate it for existing users"""
    
    # Create engine and session
    engine = create_engine(settings.database_url)
    db = SessionLocal()
    
    try:
        # Add the user_code column
        print("Adding user_code column...")
        with engine.connect() as connection:
            with connection.begin():
                # Add column (will be nullable initially)
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS user_code VARCHAR(20);
                """))
                
                # Create index
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_users_user_code ON users(user_code);
                """))
        
        print("Column added successfully!")
        
        # Get all users without user_code
        users_without_code = db.query(User).filter(User.user_code.is_(None)).all()
        print(f"Found {len(users_without_code)} users without user codes")
        
        # Generate user codes for existing users
        for i, user in enumerate(users_without_code, 1):
            user_code = f"EVE{i:03d}"
            
            # Check if code already exists (shouldn't happen but be safe)
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
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_user_codes()