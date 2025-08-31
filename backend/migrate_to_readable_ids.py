#!/usr/bin/env python3
"""
Migration script to add human-readable IDs to existing records
This will ADD new ID fields without changing existing UUID primary keys
"""

import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, Column, String, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration - use from environment or default
import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://napsa_admin@postgres:5432/napsa_erm")

# Create engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class IDMigration:
    """Handle migration of IDs to human-readable format"""
    
    def __init__(self):
        self.session = Session()
        self.counters = {}
    
    def add_columns_if_not_exist(self):
        """Add new ID columns to tables if they don't exist"""
        
        migrations = [
            # Risks table
            """
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='risks' AND column_name='risk_code') THEN
                    ALTER TABLE risks ADD COLUMN risk_code VARCHAR(20) UNIQUE;
                    CREATE INDEX idx_risk_code ON risks(risk_code);
                END IF;
            END $$;
            """,
            
            # Risk Assessments table
            """
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='risk_assessments' AND column_name='assessment_code') THEN
                    ALTER TABLE risk_assessments ADD COLUMN assessment_code VARCHAR(20) UNIQUE;
                    CREATE INDEX idx_assessment_code ON risk_assessments(assessment_code);
                END IF;
            END $$;
            """,
            
            # Controls table
            """
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='controls' AND column_name='control_code') THEN
                    ALTER TABLE controls ADD COLUMN control_code VARCHAR(20) UNIQUE;
                    CREATE INDEX idx_control_code ON controls(control_code);
                END IF;
            END $$;
            """,
            
            # Incidents table
            """
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='incidents' AND column_name='incident_code') THEN
                    ALTER TABLE incidents ADD COLUMN incident_code VARCHAR(20) UNIQUE;
                    CREATE INDEX idx_incident_code ON incidents(incident_code);
                END IF;
            END $$;
            """,
            
            # KRIs table
            """
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='key_risk_indicators' AND column_name='kri_code') THEN
                    ALTER TABLE key_risk_indicators ADD COLUMN kri_code VARCHAR(20) UNIQUE;
                    CREATE INDEX idx_kri_code ON key_risk_indicators(kri_code);
                END IF;
            END $$;
            """,
            
            # RCSA Assessments table
            """
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='rcsa_assessments' AND column_name='rcsa_code') THEN
                    ALTER TABLE rcsa_assessments ADD COLUMN rcsa_code VARCHAR(20) UNIQUE;
                    CREATE INDEX idx_rcsa_code ON rcsa_assessments(rcsa_code);
                END IF;
            END $$;
            """
        ]
        
        logger.info("Adding new ID columns to tables...")
        for migration_sql in migrations:
            try:
                self.session.execute(text(migration_sql))
                self.session.commit()
                logger.info(f"✓ Column migration executed successfully")
            except Exception as e:
                logger.error(f"Error in migration: {e}")
                self.session.rollback()
    
    def create_sequence_table(self):
        """Create table to track ID sequences"""
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS id_sequences (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_type VARCHAR(50) NOT NULL,
            prefix VARCHAR(10) NOT NULL,
            year INTEGER NOT NULL,
            last_number INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(entity_type, year)
        );
        """
        
        try:
            self.session.execute(text(create_table_sql))
            self.session.commit()
            logger.info("✓ ID sequences table created/verified")
        except Exception as e:
            logger.error(f"Error creating sequences table: {e}")
            self.session.rollback()
    
    def migrate_risks(self):
        """Assign human-readable IDs to all existing risks"""
        
        logger.info("Migrating Risk IDs...")
        
        # Get all risks without risk_code
        result = self.session.execute(text("""
            SELECT id, created_at, title, risk_code 
            FROM risks 
            WHERE risk_code IS NULL OR risk_code = ''
            ORDER BY created_at, id
        """))
        
        risks = result.fetchall()
        
        if not risks:
            logger.info("No risks to migrate or all risks already have codes")
            return
        
        # Group by year
        risks_by_year = {}
        for risk in risks:
            year = risk.created_at.year if risk.created_at else 2025
            if year not in risks_by_year:
                risks_by_year[year] = []
            risks_by_year[year].append(risk)
        
        # Update each risk with new code
        for year, year_risks in risks_by_year.items():
            # Get starting number for this year
            existing_max = self.session.execute(text("""
                SELECT MAX(CAST(SUBSTRING(risk_code FROM 'RISK-\d{4}-(\d{4})') AS INTEGER))
                FROM risks 
                WHERE risk_code LIKE :pattern
            """), {"pattern": f"RISK-{year}-%"}).scalar()
            
            start_num = (existing_max or 0) + 1
            
            for idx, risk in enumerate(year_risks, start=start_num):
                risk_code = f"RISK-{year}-{idx:04d}"
                self.session.execute(text("""
                    UPDATE risks 
                    SET risk_code = :risk_code 
                    WHERE id = :id
                """), {"risk_code": risk_code, "id": risk.id})
                logger.info(f"  → Updated risk '{risk.title[:30]}...' with code: {risk_code}")
            
            # Update sequence tracker
            self.session.execute(text("""
                INSERT INTO id_sequences (entity_type, prefix, year, last_number)
                VALUES ('risk', 'RISK', :year, :last_num)
                ON CONFLICT (entity_type, year) 
                DO UPDATE SET last_number = :last_num, updated_at = NOW()
            """), {"year": year, "last_num": start_num + len(year_risks) - 1})
        
        self.session.commit()
        logger.info(f"✓ Migrated {len(risks)} risks")
    
    def migrate_assessments(self):
        """Assign human-readable IDs to all existing assessments"""
        
        logger.info("Migrating Assessment IDs...")
        
        # Check if risk_assessments table exists
        table_exists = self.session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'risk_assessments'
            )
        """)).scalar()
        
        if not table_exists:
            logger.info("Risk assessments table not found, skipping...")
            return
        
        result = self.session.execute(text("""
            SELECT id, created_at, assessment_date, assessment_code 
            FROM risk_assessments 
            WHERE assessment_code IS NULL OR assessment_code = ''
            ORDER BY COALESCE(assessment_date, created_at), id
        """))
        
        assessments = result.fetchall()
        
        if not assessments:
            logger.info("No assessments to migrate or all assessments already have codes")
            return
        
        # Group by year
        assessments_by_year = {}
        for assessment in assessments:
            date_to_use = assessment.assessment_date or assessment.created_at
            year = date_to_use.year if date_to_use else 2025
            if year not in assessments_by_year:
                assessments_by_year[year] = []
            assessments_by_year[year].append(assessment)
        
        # Update each assessment
        for year, year_assessments in assessments_by_year.items():
            # Get starting number
            existing_max = self.session.execute(text("""
                SELECT MAX(CAST(SUBSTRING(assessment_code FROM 'ASMT-\d{4}-(\d{4})') AS INTEGER))
                FROM risk_assessments 
                WHERE assessment_code LIKE :pattern
            """), {"pattern": f"ASMT-{year}-%"}).scalar()
            
            start_num = (existing_max or 0) + 1
            
            for idx, assessment in enumerate(year_assessments, start=start_num):
                assessment_code = f"ASMT-{year}-{idx:04d}"
                self.session.execute(text("""
                    UPDATE risk_assessments 
                    SET assessment_code = :assessment_code 
                    WHERE id = :id
                """), {"assessment_code": assessment_code, "id": assessment.id})
                logger.info(f"  → Updated assessment with code: {assessment_code}")
            
            # Update sequence tracker
            self.session.execute(text("""
                INSERT INTO id_sequences (entity_type, prefix, year, last_number)
                VALUES ('assessment', 'ASMT', :year, :last_num)
                ON CONFLICT (entity_type, year) 
                DO UPDATE SET last_number = :last_num, updated_at = NOW()
            """), {"year": year, "last_num": start_num + len(year_assessments) - 1})
        
        self.session.commit()
        logger.info(f"✓ Migrated {len(assessments)} assessments")
    
    def migrate_other_entities(self):
        """Migrate IDs for other entities (controls, incidents, KRIs)"""
        
        entities = [
            ('controls', 'control_code', 'CTRL', 'control'),
            ('incidents', 'incident_code', 'INC', 'incident'),
            ('key_risk_indicators', 'kri_code', 'KRI', 'kri'),
            ('rcsa_assessments', 'rcsa_code', 'RCSA', 'rcsa')
        ]
        
        for table_name, code_column, prefix, entity_type in entities:
            logger.info(f"Migrating {table_name} IDs...")
            
            # Check if table exists
            table_exists = self.session.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                )
            """)).scalar()
            
            if not table_exists:
                logger.info(f"  {table_name} table not found, skipping...")
                continue
            
            try:
                result = self.session.execute(text(f"""
                    SELECT id, created_at, {code_column}
                    FROM {table_name}
                    WHERE {code_column} IS NULL OR {code_column} = ''
                    ORDER BY created_at, id
                """))
                
                records = result.fetchall()
                
                if not records:
                    logger.info(f"  No {table_name} to migrate")
                    continue
                
                # Group by year
                records_by_year = {}
                for record in records:
                    year = record.created_at.year if record.created_at else 2025
                    if year not in records_by_year:
                        records_by_year[year] = []
                    records_by_year[year].append(record)
                
                # Update each record
                for year, year_records in records_by_year.items():
                    # Get starting number
                    existing_max = self.session.execute(text(f"""
                        SELECT MAX(CAST(SUBSTRING({code_column} FROM '{prefix}-\d{{4}}-(\\d{{4}})') AS INTEGER))
                        FROM {table_name}
                        WHERE {code_column} LIKE :pattern
                    """), {"pattern": f"{prefix}-{year}-%"}).scalar()
                    
                    start_num = (existing_max or 0) + 1
                    
                    for idx, record in enumerate(year_records, start=start_num):
                        new_code = f"{prefix}-{year}-{idx:04d}"
                        self.session.execute(text(f"""
                            UPDATE {table_name}
                            SET {code_column} = :new_code 
                            WHERE id = :id
                        """), {"new_code": new_code, "id": record.id})
                    
                    # Update sequence tracker
                    self.session.execute(text("""
                        INSERT INTO id_sequences (entity_type, prefix, year, last_number)
                        VALUES (:entity_type, :prefix, :year, :last_num)
                        ON CONFLICT (entity_type, year) 
                        DO UPDATE SET last_number = :last_num, updated_at = NOW()
                    """), {
                        "entity_type": entity_type, 
                        "prefix": prefix,
                        "year": year, 
                        "last_num": start_num + len(year_records) - 1
                    })
                
                self.session.commit()
                logger.info(f"  ✓ Migrated {len(records)} {table_name}")
                
            except Exception as e:
                logger.error(f"  Error migrating {table_name}: {e}")
                self.session.rollback()
    
    def verify_migration(self):
        """Verify the migration was successful"""
        
        logger.info("\nVerifying migration results...")
        
        tables = [
            ('risks', 'risk_code'),
            ('risk_assessments', 'assessment_code'),
            ('controls', 'control_code'),
            ('incidents', 'incident_code'),
            ('key_risk_indicators', 'kri_code'),
            ('rcsa_assessments', 'rcsa_code')
        ]
        
        for table_name, code_column in tables:
            try:
                # Check if table exists
                table_exists = self.session.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table_name}'
                    )
                """)).scalar()
                
                if not table_exists:
                    continue
                
                # Count records with and without codes
                total = self.session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                with_code = self.session.execute(
                    text(f"SELECT COUNT(*) FROM {table_name} WHERE {code_column} IS NOT NULL AND {code_column} != ''")
                ).scalar()
                
                if total > 0:
                    logger.info(f"  {table_name}: {with_code}/{total} records have readable IDs ({with_code*100/total:.1f}%)")
                    
                    # Show some examples
                    examples = self.session.execute(text(f"""
                        SELECT id, {code_column} 
                        FROM {table_name} 
                        WHERE {code_column} IS NOT NULL 
                        LIMIT 3
                    """)).fetchall()
                    
                    for example in examples:
                        logger.info(f"    Example: {example[1]} (UUID: {str(example[0])[:8]}...)")
                        
            except Exception as e:
                logger.error(f"  Error verifying {table_name}: {e}")
    
    def run(self):
        """Run the complete migration"""
        
        logger.info("="*60)
        logger.info("Starting Human-Readable ID Migration")
        logger.info("="*60)
        
        try:
            # Step 1: Add columns
            self.add_columns_if_not_exist()
            
            # Step 2: Create sequence tracking table
            self.create_sequence_table()
            
            # Step 3: Migrate each entity type
            self.migrate_risks()
            self.migrate_assessments()
            self.migrate_other_entities()
            
            # Step 4: Verify results
            self.verify_migration()
            
            logger.info("\n" + "="*60)
            logger.info("✅ Migration completed successfully!")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.session.rollback()
            raise
        finally:
            self.session.close()

if __name__ == "__main__":
    migration = IDMigration()
    migration.run()