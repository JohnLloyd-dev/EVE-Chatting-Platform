#!/usr/bin/env python3
"""
Script to create database tables based on SQLAlchemy models
"""

from database import Base, engine
from sqlalchemy import text

def create_tables():
    """Create all tables defined in the models"""
    print("Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ All tables created successfully!")
    
    # Verify tables were created
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result]
        print(f"📋 Created tables: {', '.join(tables)}")

if __name__ == "__main__":
    create_tables() 