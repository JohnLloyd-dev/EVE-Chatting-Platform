#!/usr/bin/env python3
"""
Simple user codes migration
"""

import sys
import os
sys.path.append('/app')

from database import SessionLocal, User

def main():
    print("Starting user codes migration...")
    db = SessionLocal()
    
    try:
        # Get all users
        users = db.query(User).all()
        print(f"Found {len(users)} total users")
        
        # Find users without user_code
        users_without_code = []
        for user in users:
            if not hasattr(user, 'user_code') or not user.user_code:
                users_without_code.append(user)
        
        print(f"Found {len(users_without_code)} users without user codes")
        
        if not users_without_code:
            print("All users already have user codes!")
            return
        
        # Assign user codes
        for i, user in enumerate(users_without_code, 1):
            user_code = f"EVE{i:03d}"
            
            # Check if code already exists
            existing = db.query(User).filter(User.user_code == user_code).first()
            while existing:
                i += 1
                user_code = f"EVE{i:03d}"
                existing = db.query(User).filter(User.user_code == user_code).first()
            
            user.user_code = user_code
            print(f"Assigned {user_code} to user {user.id}")
        
        # Commit changes
        db.commit()
        print("✅ User codes assigned successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()