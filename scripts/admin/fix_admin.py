#!/usr/bin/env python3
"""
Fix admin login by creating a new admin user with working password hash
"""
import hashlib
import uuid
import psycopg2
from datetime import datetime

def create_simple_hash(password: str) -> str:
    """Create a simple but secure hash for the password"""
    # Using SHA-256 with salt for simplicity
    salt = "chatting_platform_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_simple_hash(password: str, hashed: str) -> bool:
    """Verify password against simple hash"""
    salt = "chatting_platform_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest() == hashed

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
        cur = conn.cursor()
        
        # Delete existing admin user
        cur.execute("DELETE FROM admin_users WHERE username = 'admin'")
        
        # Create new admin user with simple hash
        admin_id = str(uuid.uuid4())
        username = "admin"
        password = "admin123"
        email = "admin@chatplatform.com"
        password_hash = create_simple_hash(password)
        created_at = datetime.utcnow()
        
        cur.execute("""
            INSERT INTO admin_users (id, username, email, password_hash, created_at, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (admin_id, username, email, password_hash, created_at, True))
        
        conn.commit()
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   ID: {admin_id}")
        
        # Test the hash
        if verify_simple_hash(password, password_hash):
            print("✅ Password hash verification works!")
        else:
            print("❌ Password hash verification failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()