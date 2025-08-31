#!/usr/bin/env python3
"""
Add Zambian users to NAPSA ERM database
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from uuid import uuid4
from datetime import datetime

# Import the User model
from app.models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Database connection
DATABASE_URL = "postgresql://napsa_admin:napsa2024@localhost:58002/napsa_erm"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Zambian users for NAPSA
ZAMBIAN_USERS = [
    {
        "username": "director.general",
        "email": "dg@napsa.co.zm",
        "full_name": "Dr. Yollard Kachinda",
        "role": "admin",
        "department": "Executive",
        "password": "napsa2025"
    },
    {
        "username": "chief.risk",
        "email": "cro@napsa.co.zm",
        "full_name": "Mrs. Chabota Kaleza",
        "role": "risk_manager",
        "department": "Risk and Compliance",
        "password": "napsa2025"
    },
    {
        "username": "m.banda",
        "email": "m.banda@napsa.co.zm",
        "full_name": "Mr. Mwansa Banda",
        "role": "risk_owner",
        "department": "Investments",
        "password": "napsa2025"
    },
    {
        "username": "c.mwale",
        "email": "c.mwale@napsa.co.zm",
        "full_name": "Mrs. Chanda Mwale",
        "role": "risk_owner",
        "department": "Benefits Administration",
        "password": "napsa2025"
    },
    {
        "username": "j.phiri",
        "email": "j.phiri@napsa.co.zm",
        "full_name": "Mr. Joseph Phiri",
        "role": "auditor",
        "department": "Internal Audit",
        "password": "napsa2025"
    },
    {
        "username": "s.tembo",
        "email": "s.tembo@napsa.co.zm",
        "full_name": "Ms. Serah Tembo",
        "role": "viewer",
        "department": "Human Resources",
        "password": "napsa2025"
    },
    {
        "username": "b.chulu",
        "email": "b.chulu@napsa.co.zm",
        "full_name": "Mr. Brian Chulu",
        "role": "risk_owner",
        "department": "Information Technology",
        "password": "napsa2025"
    },
    {
        "username": "n.zulu",
        "email": "n.zulu@napsa.co.zm",
        "full_name": "Mrs. Natasha Zulu",
        "role": "risk_manager",
        "department": "Legal and Compliance",
        "password": "napsa2025"
    },
    {
        "username": "k.musonda",
        "email": "k.musonda@napsa.co.zm",
        "full_name": "Mr. Kelvin Musonda",
        "role": "viewer",
        "department": "Risk and Compliance",
        "password": "napsa2025"
    },
    {
        "username": "l.ngoma",
        "email": "l.ngoma@napsa.co.zm",
        "full_name": "Ms. Linda Ngoma",
        "role": "risk_owner",
        "department": "Finance",
        "password": "napsa2025"
    }
]

def add_zambian_users():
    session = SessionLocal()
    try:
        created_count = 0
        skipped_count = 0
        
        for user_data in ZAMBIAN_USERS:
            # Check if user already exists
            existing = session.query(User).filter(
                (User.username == user_data["username"]) | 
                (User.email == user_data["email"])
            ).first()
            
            if existing:
                print(f"⏭️  User {user_data['username']} already exists. Skipping...")
                skipped_count += 1
                continue
            
            # Create new user
            user = User(
                id=str(uuid4()),
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=get_password_hash(user_data["password"]),
                role=user_data["role"],
                department=user_data["department"],
                is_active=True,
                created_at=datetime.utcnow()
            )
            session.add(user)
            print(f"✅ Created user: {user.full_name} ({user.username}) - {user.role}")
            created_count += 1
        
        session.commit()
        
        print(f"\n{'='*50}")
        print(f"Summary: Created {created_count} users, Skipped {skipped_count} existing users")
        
        if created_count > 0:
            print(f"\n{'='*50}")
            print("Login Credentials for New Users:")
            print(f"{'='*50}")
            for user in ZAMBIAN_USERS:
                print(f"Username: {user['username']:<20} Password: {user['password']}")
            print(f"{'='*50}")
        
        # Show total users in system
        total_users = session.query(User).count()
        print(f"\nTotal users in system: {total_users}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    add_zambian_users()