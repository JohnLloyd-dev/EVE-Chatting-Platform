#!/usr/bin/env python3
"""
Simple database connection test to diagnose the connection issue
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import time

# Test the database connection
database_url = "postgresql://adam2025man:adam2025@postgres:5432/chatting_platform"

print(f"Testing database connection to: {database_url}")

# Try to connect multiple times with retries
max_retries = 5
retry_delay = 2

for attempt in range(max_retries):
    try:
        print(f"Attempt {attempt + 1}/{max_retries}...")
        
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Connection successful! Test query result: {row[0]}")
            
            # Test if tables exist
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Available tables: {tables}")
            
            break
            
    except OperationalError as e:
        print(f"❌ Connection failed (attempt {attempt + 1}): {e}")
        if attempt < max_retries - 1:
            print(f"Waiting {retry_delay} seconds before retry...")
            time.sleep(retry_delay)
        else:
            print("❌ All connection attempts failed")
            exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        exit(1)

print("✅ Database connection test completed successfully!") 