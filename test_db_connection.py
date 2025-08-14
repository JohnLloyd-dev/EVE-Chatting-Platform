#!/usr/bin/env python3

import os
from urllib.parse import urlparse

# Test the database URL parsing
database_url = "postgresql://adam2025man:adam2025@postgres:5432/chatting_platform"

print("🔍 Testing Database URL Parsing:")
print(f"Original URL: {database_url}")

try:
    parsed = urlparse(database_url)
    print(f"✅ Parsed successfully:")
    print(f"  Scheme: {parsed.scheme}")
    print(f"  Username: {parsed.username}")
    print(f"  Password: {parsed.password}")
    print(f"  Hostname: {parsed.hostname}")
    print(f"  Port: {parsed.port}")
    print(f"  Database: {parsed.path.lstrip('/')}")
    
    # Check if database name is correct
    db_name = parsed.path.lstrip('/')
    if db_name == "chatting_platform":
        print("✅ Database name is correct: chatting_platform")
    else:
        print(f"❌ Database name is wrong: {db_name}")
        
except Exception as e:
    print(f"❌ Failed to parse URL: {e}")

print("\n🔍 Environment Variables:")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")

# Test SQLAlchemy connection
try:
    from sqlalchemy import create_engine
    print("\n🔍 Testing SQLAlchemy Connection:")
    
    engine = create_engine(database_url)
    print("✅ Engine created successfully")
    
    # Try to connect
    with engine.connect() as conn:
        print("✅ Database connection successful!")
        
        # Check what database we're actually connected to
        result = conn.execute("SELECT current_database()")
        actual_db = result.scalar()
        print(f"✅ Connected to database: {actual_db}")
        
        if actual_db == "chatting_platform":
            print("✅ Connected to correct database!")
        else:
            print(f"❌ Connected to wrong database: {actual_db}")
            
except Exception as e:
    print(f"❌ SQLAlchemy connection failed: {e}") 