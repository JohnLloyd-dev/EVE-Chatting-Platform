#!/usr/bin/env python3
"""
Script to fix the admin password hash in the database
"""
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor

def create_simple_hash(password: str) -> str:
    """Create a simple but secure hash for the password"""
    salt = "chatting_platform_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def main():
    # Database connection
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="chatting_platform",
        user="postgres",
        password="postgres123"
    )
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check current admin user
            cur.execute("SELECT username, password_hash FROM admin_users WHERE username = 'admin'")
            admin = cur.fetchone()
            
            if admin:
                print(f"Current admin user: {admin['username']}")
                print(f"Current password hash: {admin['password_hash'][:50]}...")
                
                # Generate new hash for 'admin123'
                new_hash = create_simple_hash("admin123")
                print(f"New password hash: {new_hash[:50]}...")
                
                # Update the password hash
                cur.execute(
                    "UPDATE admin_users SET password_hash = %s WHERE username = 'admin'",
                    (new_hash,)
                )
                conn.commit()
                print("✅ Admin password hash updated successfully!")
                
                # Verify the update
                cur.execute("SELECT username, password_hash FROM admin_users WHERE username = 'admin'")
                updated_admin = cur.fetchone()
                print(f"Updated password hash: {updated_admin['password_hash'][:50]}...")
                
            else:
                print("❌ Admin user not found!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()