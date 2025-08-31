#!/usr/bin/env python3
"""
Fix database schema - adds missing columns and updates tables
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import ProgrammingError

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://napsa_admin@localhost:58002/napsa_erm")

def fix_database_schema():
    """Add missing columns to existing tables"""
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check if users table exists
            if 'users' in inspector.get_table_names():
                # Get existing columns
                existing_columns = [col['name'] for col in inspector.get_columns('users')]
                
                # Add missing columns
                columns_to_add = [
                    ("last_login", "TIMESTAMP"),
                    ("phone", "VARCHAR(20)"),
                    ("position", "VARCHAR(100)"),
                    ("failed_login_attempts", "INTEGER DEFAULT 0"),
                    ("locked_until", "TIMESTAMP"),
                    ("password_changed_at", "TIMESTAMP"),
                    ("must_change_password", "BOOLEAN DEFAULT FALSE"),
                    ("profile_picture", "VARCHAR(255)"),
                    ("preferences", "TEXT"),
                    ("notifications_enabled", "BOOLEAN DEFAULT TRUE")
                ]
                
                for column_name, column_type in columns_to_add:
                    if column_name not in existing_columns:
                        try:
                            print(f"Adding column {column_name} to users table...")
                            conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_type}"))
                            print(f"✓ Added {column_name}")
                        except ProgrammingError as e:
                            if "already exists" not in str(e):
                                print(f"✗ Error adding {column_name}: {e}")
            
            # Check other tables for missing columns
            tables_to_check = {
                'risks': [
                    ("created_by_id", "UUID"),
                    ("approved_by_id", "UUID"),
                    ("review_date", "TIMESTAMP"),
                    ("next_review_date", "TIMESTAMP"),
                    ("risk_appetite", "VARCHAR(50)"),
                    ("risk_tolerance", "VARCHAR(50)"),
                    ("escalation_required", "BOOLEAN DEFAULT FALSE"),
                    ("escalated_to_id", "UUID"),
                    ("attachments", "TEXT"),
                    ("tags", "TEXT")
                ],
                'risk_assessments': [
                    ("approved_by_id", "UUID"),
                    ("approval_date", "TIMESTAMP"),
                    ("comments", "TEXT"),
                    ("action_items", "TEXT"),
                    ("next_assessment_date", "TIMESTAMP")
                ],
                'incidents': [
                    ("resolution_date", "TIMESTAMP"),
                    ("root_cause", "TEXT"),
                    ("lessons_learned", "TEXT"),
                    ("financial_impact", "DECIMAL(15,2)"),
                    ("reputational_impact", "VARCHAR(50)"),
                    ("regulatory_breach", "BOOLEAN DEFAULT FALSE"),
                    ("external_parties_involved", "TEXT")
                ],
                'controls': [
                    ("control_owner_id", "UUID"),
                    ("testing_frequency", "VARCHAR(50)"),
                    ("last_tested_date", "TIMESTAMP"),
                    ("next_test_date", "TIMESTAMP"),
                    ("automation_level", "VARCHAR(50)"),
                    ("cost_of_control", "DECIMAL(15,2)")
                ]
            }
            
            for table_name, columns in tables_to_check.items():
                if table_name in inspector.get_table_names():
                    existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
                    
                    for column_name, column_type in columns:
                        if column_name not in existing_columns:
                            try:
                                print(f"Adding column {column_name} to {table_name} table...")
                                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type}"))
                                print(f"✓ Added {column_name} to {table_name}")
                            except ProgrammingError as e:
                                if "already exists" not in str(e):
                                    print(f"✗ Error adding {column_name} to {table_name}: {e}")
            
            # Create any missing indexes
            print("\nCreating indexes...")
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
                "CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login)",
                "CREATE INDEX IF NOT EXISTS idx_risks_status ON risks(status)",
                "CREATE INDEX IF NOT EXISTS idx_risks_category ON risks(category)",
                "CREATE INDEX IF NOT EXISTS idx_risks_owner ON risks(risk_owner_id)",
                "CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)",
                "CREATE INDEX IF NOT EXISTS idx_incidents_risk ON incidents(risk_id)"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    index_name = index_sql.split("INDEX IF NOT EXISTS ")[1].split(" ON")[0]
                    print(f"✓ Created index {index_name}")
                except Exception as e:
                    if "already exists" not in str(e):
                        print(f"✗ Error creating index: {e}")
            
            # Commit transaction
            trans.commit()
            print("\n✅ Database schema updated successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Error updating schema: {e}")
            raise
        
    return True

if __name__ == "__main__":
    try:
        fix_database_schema()
        print("\nDatabase schema is now up to date!")
        sys.exit(0)
    except Exception as e:
        print(f"Failed to update database schema: {e}")
        sys.exit(1)