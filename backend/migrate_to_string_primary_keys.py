#!/usr/bin/env python3
"""
Migration script to change primary keys from UUID to human-readable string codes
"""

import psycopg2
from psycopg2 import sql
import sys

# Database connection parameters
DB_CONFIG = {
    'host': '102.23.120.243',
    'port': 58002,
    'database': 'napsa_erm',
    'user': 'napsa_admin',
    'password': 'napsa2024'
}

def execute_migration():
    """Execute the migration to change primary keys"""
    conn = None
    cur = None
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Starting migration to human-readable primary keys...")
        
        # Start transaction
        conn.autocommit = False
        
        # Step 1: Ensure all records have human-readable codes
        print("\n1. Checking if all records have human-readable codes...")
        
        # Check risks
        cur.execute("SELECT COUNT(*) FROM risks WHERE risk_code IS NULL")
        null_risks = cur.fetchone()[0]
        if null_risks > 0:
            print(f"ERROR: {null_risks} risks don't have risk_code. Please run the previous migration first.")
            return False
        
        # Check assessments
        cur.execute("SELECT COUNT(*) FROM risk_assessments WHERE assessment_code IS NULL")
        null_assessments = cur.fetchone()[0]
        if null_assessments > 0:
            print(f"ERROR: {null_assessments} assessments don't have assessment_code. Please run the previous migration first.")
            return False
        
        print("✓ All records have human-readable codes")
        
        # Step 2: Drop ALL foreign key constraints that reference risks table
        print("\n2. Dropping ALL foreign key constraints referencing risks...")
        
        # Find all foreign key constraints that reference the risks table
        cur.execute("""
            SELECT 
                tc.table_name,
                tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.referential_constraints rc 
                ON tc.constraint_name = rc.constraint_name
            WHERE rc.unique_constraint_name = 'risks_pkey'
                OR tc.constraint_name LIKE '%risk%fkey%'
        """)
        
        constraints = cur.fetchall()
        for table_name, constraint_name in constraints:
            try:
                cur.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}")
                print(f"  ✓ Dropped {constraint_name} from {table_name}")
            except Exception as e:
                print(f"  - Error dropping {constraint_name}: {e}")
        
        # Also drop constraints from risk_assessments that reference other tables
        cur.execute("""
            SELECT 
                constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'risk_assessments'
                AND constraint_type = 'FOREIGN KEY'
        """)
        
        for (constraint_name,) in cur.fetchall():
            try:
                cur.execute(f"ALTER TABLE risk_assessments DROP CONSTRAINT IF EXISTS {constraint_name}")
                print(f"  ✓ Dropped {constraint_name} from risk_assessments")
            except Exception as e:
                print(f"  - Error: {e}")
        
        # Step 3: Add new columns for string-based foreign keys
        print("\n3. Adding new columns for string-based foreign keys...")
        
        add_columns = [
            ("risk_assessments", "risk_code", "VARCHAR(20)"),
            ("risk_controls", "risk_code", "VARCHAR(20)"),
            ("risk_treatments", "risk_code", "VARCHAR(20)"),
            ("incidents", "risk_code", "VARCHAR(20)"),
            ("key_risk_indicators", "risk_code", "VARCHAR(20)"),
            ("rcsa_assessments", "risk_code", "VARCHAR(20)"),
            ("compliance_mappings", "risk_code", "VARCHAR(20)"),
        ]
        
        for table, column, dtype in add_columns:
            try:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {dtype}")
                print(f"  ✓ Added {column} to {table}")
            except Exception as e:
                print(f"  - {table}.{column}: {e}")
        
        # Step 4: Update foreign key values to use codes
        print("\n4. Updating foreign key values to use codes...")
        
        # Update risk_assessments
        cur.execute("""
            UPDATE risk_assessments ra
            SET risk_code = r.risk_code
            FROM risks r
            WHERE ra.risk_id = r.id AND ra.risk_code IS NULL
        """)
        print(f"  ✓ Updated {cur.rowcount} risk_assessments")
        
        # Update risk_controls
        cur.execute("""
            UPDATE risk_controls rc
            SET risk_code = r.risk_code
            FROM risks r
            WHERE rc.risk_id = r.id AND rc.risk_code IS NULL
        """)
        print(f"  ✓ Updated {cur.rowcount} risk_controls")
        
        # Update risk_treatments
        cur.execute("""
            UPDATE risk_treatments rt
            SET risk_code = r.risk_code
            FROM risks r
            WHERE rt.risk_id = r.id AND rt.risk_code IS NULL
        """)
        print(f"  ✓ Updated {cur.rowcount} risk_treatments")
        
        # Update incidents
        cur.execute("""
            UPDATE incidents i
            SET risk_code = r.risk_code
            FROM risks r
            WHERE i.risk_id = r.id AND i.risk_code IS NULL
        """)
        print(f"  ✓ Updated {cur.rowcount} incidents")
        
        # Update key_risk_indicators
        cur.execute("""
            UPDATE key_risk_indicators kri
            SET risk_code = r.risk_code
            FROM risks r
            WHERE kri.risk_id = r.id AND kri.risk_code IS NULL
        """)
        print(f"  ✓ Updated {cur.rowcount} key_risk_indicators")
        
        # Skip rcsa_assessments if it doesn't have risk_id
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'rcsa_assessments' AND column_name = 'risk_id'
        """)
        if cur.fetchone():
            cur.execute("""
                UPDATE rcsa_assessments rcsa
                SET risk_code = r.risk_code
                FROM risks r
                WHERE rcsa.risk_id = r.id AND rcsa.risk_code IS NULL
            """)
            print(f"  ✓ Updated {cur.rowcount} rcsa_assessments")
        else:
            print("  - Skipped rcsa_assessments (no risk_id column)")
        
        # Update compliance_mappings
        cur.execute("""
            UPDATE compliance_mappings cm
            SET risk_code = r.risk_code
            FROM risks r
            WHERE cm.risk_id = r.id AND cm.risk_code IS NULL
        """)
        print(f"  ✓ Updated {cur.rowcount} compliance_mappings")
        
        # Step 5: Drop old UUID columns and rename code columns
        print("\n5. Dropping UUID primary keys and setting new primary keys...")
        
        # For risks table
        cur.execute("ALTER TABLE risks DROP CONSTRAINT IF EXISTS risks_pkey")
        cur.execute("ALTER TABLE risks ALTER COLUMN risk_code SET NOT NULL")
        cur.execute("ALTER TABLE risks ADD PRIMARY KEY (risk_code)")
        cur.execute("ALTER TABLE risks DROP COLUMN IF EXISTS id")
        cur.execute("ALTER TABLE risks RENAME COLUMN risk_code TO id")
        print("  ✓ Risks table: UUID replaced with risk_code as primary key")
        
        # For risk_assessments table
        cur.execute("ALTER TABLE risk_assessments DROP CONSTRAINT IF EXISTS risk_assessments_pkey")
        cur.execute("ALTER TABLE risk_assessments ALTER COLUMN assessment_code SET NOT NULL")
        cur.execute("ALTER TABLE risk_assessments ADD PRIMARY KEY (assessment_code)")
        cur.execute("ALTER TABLE risk_assessments DROP COLUMN IF EXISTS id")
        cur.execute("ALTER TABLE risk_assessments RENAME COLUMN assessment_code TO id")
        print("  ✓ Risk assessments table: UUID replaced with assessment_code as primary key")
        
        # Step 6: Drop old UUID foreign key columns and rename new ones
        print("\n6. Updating foreign key columns...")
        
        # Update risk_assessments
        cur.execute("ALTER TABLE risk_assessments DROP COLUMN IF EXISTS risk_id")
        cur.execute("ALTER TABLE risk_assessments RENAME COLUMN risk_code TO risk_id")
        
        # Update risk_controls
        cur.execute("ALTER TABLE risk_controls DROP COLUMN IF EXISTS risk_id")
        cur.execute("ALTER TABLE risk_controls RENAME COLUMN risk_code TO risk_id")
        
        # Update risk_treatments
        cur.execute("ALTER TABLE risk_treatments DROP COLUMN IF EXISTS risk_id")
        cur.execute("ALTER TABLE risk_treatments RENAME COLUMN risk_code TO risk_id")
        
        # Update incidents
        cur.execute("ALTER TABLE incidents DROP COLUMN IF EXISTS risk_id")
        cur.execute("ALTER TABLE incidents RENAME COLUMN risk_code TO risk_id")
        
        # Update key_risk_indicators
        cur.execute("ALTER TABLE key_risk_indicators DROP COLUMN IF EXISTS risk_id")
        cur.execute("ALTER TABLE key_risk_indicators RENAME COLUMN risk_code TO risk_id")
        
        # Update rcsa_assessments only if it has these columns
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'rcsa_assessments' AND column_name = 'risk_code'
        """)
        if cur.fetchone():
            cur.execute("ALTER TABLE rcsa_assessments DROP COLUMN IF EXISTS risk_id")
            cur.execute("ALTER TABLE rcsa_assessments RENAME COLUMN risk_code TO risk_id")
        
        # Update compliance_mappings
        cur.execute("ALTER TABLE compliance_mappings DROP COLUMN IF EXISTS risk_id")
        cur.execute("ALTER TABLE compliance_mappings RENAME COLUMN risk_code TO risk_id")
        
        print("  ✓ Foreign key columns updated")
        
        # Step 7: Re-create foreign key constraints
        print("\n7. Re-creating foreign key constraints...")
        
        new_constraints = [
            "ALTER TABLE risk_assessments ADD CONSTRAINT risk_assessments_risk_id_fkey FOREIGN KEY (risk_id) REFERENCES risks(id)",
            "ALTER TABLE risk_controls ADD CONSTRAINT risk_controls_risk_id_fkey FOREIGN KEY (risk_id) REFERENCES risks(id)",
            "ALTER TABLE risk_treatments ADD CONSTRAINT risk_treatments_risk_id_fkey FOREIGN KEY (risk_id) REFERENCES risks(id)",
            "ALTER TABLE incidents ADD CONSTRAINT incidents_risk_id_fkey FOREIGN KEY (risk_id) REFERENCES risks(id)",
            "ALTER TABLE key_risk_indicators ADD CONSTRAINT key_risk_indicators_risk_id_fkey FOREIGN KEY (risk_id) REFERENCES risks(id)",
            "ALTER TABLE compliance_mappings ADD CONSTRAINT compliance_mappings_risk_id_fkey FOREIGN KEY (risk_id) REFERENCES risks(id)",
        ]
        
        # Only add rcsa constraint if the column exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'rcsa_assessments' AND column_name = 'risk_id'
        """)
        if cur.fetchone():
            new_constraints.append("ALTER TABLE rcsa_assessments ADD CONSTRAINT rcsa_assessments_risk_id_fkey FOREIGN KEY (risk_id) REFERENCES risks(id)")
        
        for constraint in new_constraints:
            try:
                cur.execute(constraint)
                print(f"  ✓ Created: {constraint.split('ADD CONSTRAINT')[1].split()[0]}")
            except Exception as e:
                print(f"  - Error: {e}")
        
        # Commit transaction
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nNOTE: You need to update the SQLAlchemy models to reflect these changes:")
        print("  - Risk.id should be String(20), not UUID")
        print("  - RiskAssessment.id should be String(20), not UUID")
        print("  - All foreign keys referencing these should be String(20)")
        
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    success = execute_migration()
    sys.exit(0 if success else 1)