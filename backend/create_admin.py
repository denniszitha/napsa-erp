import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.core.security import get_password_hash
from app.db.base import Base

# Create tables
Base.metadata.create_all(bind=engine)

# Create admin user
db = SessionLocal()

try:
    # Check if admin exists
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        print("Admin user already exists!")
        print(f"Username: {admin.username}")
        print(f"Email: {admin.email}")
        print(f"Active: {admin.is_active}")
        
        # Update password to be sure
        admin.hashed_password = get_password_hash("admin123")
        db.commit()
        print("Password reset to: admin123")
    else:
        # Create admin user
        admin = User(
            username="admin",
            email="admin@napsa.co.zm",
            full_name="System Administrator",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True,
            role="admin",
            department="IT"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        
    # List all users
    print("\nAll users in database:")
    users = db.query(User).all()
    for user in users:
        print(f"- {user.username} ({user.email}) - Active: {user.is_active}")
        
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
