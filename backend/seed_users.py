#!/usr/bin/env python3
"""
Quick user seeder for NAPSA ERM
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

# Database connection - using correct credentials and port
DATABASE_URL = "postgresql://napsa_admin:napsa2024@localhost:58002/napsa_erm"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test users
USERS = [
    {
        "username": "admin",
        "email": "admin@napsa.co.zm",
        "full_name": "System Administrator",
        "role": "admin",
        "department": "IT",
        "password": "admin123"
    },
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
        "full_name": "Chief Risk Officer",
        "role": "risk_manager",
        "department": "Risk and Compliance",
        "password": "napsa2025"
    }
]

def seed_users():
    session = SessionLocal()
    try:
        # Check if users already exist
        existing = session.query(User).filter(User.username == "admin").first()
        if existing:
            print("Users already exist. Skipping...")
            return
        
        # Create users
        for user_data in USERS:
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
            print(f"Created user: {user.username}")
        
        session.commit()
        print("✅ Users created successfully!")
        print("\nLogin credentials:")
        print("-" * 40)
        for user in USERS:
            print(f"Username: {user['username']}")
            print(f"Password: {user['password']}")
            print("-" * 40)
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_users()