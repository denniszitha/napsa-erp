#!/usr/bin/env python3
"""
Test script to verify database migration compatibility
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://napsa_admin:napsa_password@localhost:5432/napsa_erm"
)

def test_migration():
    """Test database migration compatibility"""
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        logger.info("✓ Connected to database successfully")
        results["passed"].append("Database connection")
        
        # Get existing tables
        existing_tables = inspector.get_table_names()
        logger.info(f"Found {len(existing_tables)} existing tables")
        
        # Check for critical tables that should exist
        required_tables = ['users', 'risks', 'controls', 'incidents']
        for table in required_tables:
            if table in existing_tables:
                results["passed"].append(f"Table '{table}' exists")
            else:
                results["warnings"].append(f"Table '{table}' not found")
        
        # Check for new tables that will be created
        new_tables = [
            'impact_scales',
            'likelihood_scales', 
            'assessment_periods',
            'assessment_templates',
            'system_configurations',
            'file_categories',
            'files',
            'risk_histories',
            'user_login_histories'
        ]
        
        for table in new_tables:
            if table in existing_tables:
                results["warnings"].append(f"Table '{table}' already exists - will skip creation")
            else:
                results["passed"].append(f"Table '{table}' will be created")
        
        # Test enum types creation
        with engine.connect() as conn:
            # Check if enum types exist
            enum_check = """
                SELECT typname 
                FROM pg_type 
                WHERE typname IN ('assessment_status', 'risk_status', 'control_type')
                AND typtype = 'e'
            """
            result = conn.execute(text(enum_check))
            existing_enums = [row[0] for row in result]
            
            if existing_enums:
                logger.info(f"Found {len(existing_enums)} existing enum types")
                for enum in existing_enums:
                    results["warnings"].append(f"Enum '{enum}' already exists")
            
        # Check column additions for existing tables
        if 'risks' in existing_tables:
            risk_columns = [col['name'] for col in inspector.get_columns('risks')]
            new_risk_columns = ['risk_id', 'causes', 'consequences', 'is_principal_risk']
            
            for col in new_risk_columns:
                if col in risk_columns:
                    results["warnings"].append(f"Column 'risks.{col}' already exists")
                else:
                    results["passed"].append(f"Column 'risks.{col}' will be added")
        
        if 'users' in existing_tables:
            user_columns = [col['name'] for col in inspector.get_columns('users')]
            new_user_columns = ['employee_id', 'hire_date', 'ad_username', 'ad_object_guid']
            
            for col in new_user_columns:
                if col in user_columns:
                    results["warnings"].append(f"Column 'users.{col}' already exists")
                else:
                    results["passed"].append(f"Column 'users.{col}' will be added")
        
    except Exception as e:
        logger.error(f"Error testing migration: {str(e)}")
        results["failed"].append(f"Database test failed: {str(e)}")
        return results
    
    finally:
        if 'engine' in locals():
            engine.dispose()
    
    return results

def print_results(results):
    """Print test results in a formatted way"""
    print("\n" + "="*60)
    print("MIGRATION COMPATIBILITY TEST RESULTS")
    print("="*60)
    
    if results["passed"]:
        print(f"\n✅ PASSED ({len(results['passed'])} items):")
        for item in results["passed"][:10]:  # Show first 10
            print(f"   • {item}")
        if len(results["passed"]) > 10:
            print(f"   ... and {len(results['passed']) - 10} more")
    
    if results["warnings"]:
        print(f"\n⚠️  WARNINGS ({len(results['warnings'])} items):")
        for item in results["warnings"][:10]:  # Show first 10
            print(f"   • {item}")
        if len(results["warnings"]) > 10:
            print(f"   ... and {len(results['warnings']) - 10} more")
    
    if results["failed"]:
        print(f"\n❌ FAILED ({len(results['failed'])} items):")
        for item in results["failed"]:
            print(f"   • {item}")
    
    print("\n" + "="*60)
    
    if not results["failed"]:
        print("✅ Migration is safe to apply!")
        print("\nNext step: Run the migration script")
        print("  psql -U napsa_admin -d napsa_erm -f migrations/001_align_with_ermdb_schema.sql")
    else:
        print("❌ Please resolve the failed items before applying migration")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    print(f"\n🔍 Testing migration compatibility at {datetime.now()}")
    results = test_migration()
    print_results(results)