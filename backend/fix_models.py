#!/usr/bin/env python3
"""
Script to fix UUID type mismatches in the database
"""
import os
import sys
from sqlalchemy import create_engine, text

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://napsa_admin:napsa2024@localhost:58002/napsa_db")

def fix_uuid_types():
    """Fix UUID type mismatches in database"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Drop all tables to start fresh
            print("Dropping existing tables...")
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO napsa_admin"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            conn.commit()
            print("Tables dropped successfully")
            
            # Create extensions
            print("Creating extensions...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            conn.commit()
            print("Extensions created")
            
            print("Database reset complete. Tables will be recreated by SQLAlchemy.")
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
            return False

if __name__ == "__main__":
    if fix_uuid_types():
        print("✓ Database fixed successfully")
        sys.exit(0)
    else:
        print("✗ Failed to fix database")
        sys.exit(1)