#!/usr/bin/env python3
"""
Create initial admin user for NAPSA ERM System
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.core.database import Base
import uuid
from datetime import datetime

def create_admin_user():
    """Create the initial admin user"""
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.email == "admin@napsa.co.zm").first()
        
        if existing_admin:
            print("❌ Admin user already exists!")
            print(f"   Email: admin@napsa.co.zm")
            print(f"   Role: {existing_admin.role}")
            return False
        
        # Create admin user
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@napsa.co.zm",
            username="admin",
            full_name="System Administrator",
            hashed_password=get_password_hash("Admin@2024!"),
            role=UserRole.admin,
            is_active=True,
            is_superuser=True,
            department="IT Department",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print("\n" + "="*50)
        print("ADMIN USER CREDENTIALS")
        print("="*50)
        print(f"Email:    admin@napsa.co.zm")
        print(f"Username: admin")
        print(f"Password: Admin@2024!")
        print(f"Role:     ADMIN (Superuser)")
        print(f"ID:       {admin_user.id}")
        print("="*50)
        print("\n⚠️  Please change the password after first login!")
        
        # Create additional test users
        test_users = [
            {
                "email": "risk.manager@napsa.co.zm",
                "username": "riskmanager",
                "full_name": "Risk Manager",
                "password": "RiskManager@2024!",
                "role": UserRole.risk_manager,
                "department": "Risk Management"
            },
            {
                "email": "auditor@napsa.co.zm",
                "username": "auditor",
                "full_name": "Internal Auditor",
                "password": "Auditor@2024!",
                "role": UserRole.auditor,
                "department": "Internal Audit"
            },
            {
                "email": "risk.owner@napsa.co.zm",
                "username": "riskowner",
                "full_name": "Risk Owner",
                "password": "RiskOwner@2024!",
                "role": UserRole.risk_owner,
                "department": "Operations"
            },
            {
                "email": "viewer@napsa.co.zm",
                "username": "viewer",
                "full_name": "Report Viewer",
                "password": "Viewer@2024!",
                "role": UserRole.viewer,
                "department": "Finance"
            }
        ]
        
        print("\n📝 Creating additional test users...")
        
        for user_data in test_users:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing:
                user = User(
                    id=uuid.uuid4(),
                    email=user_data["email"],
                    username=user_data["username"],
                    full_name=user_data["full_name"],
                    hashed_password=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                    is_active=True,
                    is_superuser=False,
                    department=user_data["department"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(user)
                print(f"   ✅ Created: {user_data['email']} (Role: {user_data['role'].value})")
            else:
                print(f"   ⏭️  Skipped: {user_data['email']} (already exists)")
        
        db.commit()
        
        print("\n" + "="*50)
        print("TEST USER ACCOUNTS")
        print("="*50)
        print("Role: RISK_MANAGER")
        print("  Email: risk.manager@napsa.co.zm")
        print("  Pass:  RiskManager@2024!")
        print("\nRole: AUDITOR")
        print("  Email: auditor@napsa.co.zm")
        print("  Pass:  Auditor@2024!")
        print("\nRole: RISK_OWNER")
        print("  Email: risk.owner@napsa.co.zm")
        print("  Pass:  RiskOwner@2024!")
        print("\nRole: VIEWER")
        print("  Email: viewer@napsa.co.zm")
        print("  Pass:  Viewer@2024!")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = create_admin_user()
    sys.exit(0 if success else 1)