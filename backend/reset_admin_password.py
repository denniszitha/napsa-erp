#!/usr/bin/env python3
"""Reset admin password"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def reset_admin_password():
    db = SessionLocal()
    try:
        # Find admin user
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("Admin user not found. Creating one...")
            admin = User(
                username="admin",
                email="admin@napsa.co.zm",
                full_name="System Administrator",
                hashed_password=get_password_hash("Admin@123"),
                is_active=True,
                is_superuser=True,
                role="admin"
            )
            db.add(admin)
        else:
            print(f"Found admin user: {admin.email}")
            admin.hashed_password = get_password_hash("Admin@123")
            admin.is_active = True
            admin.is_superuser = True
            admin.failed_login_attempts = 0
            admin.locked_until = None
            
        db.commit()
        print("✓ Admin password reset to: Admin@123")
        print("  Username: admin")
        print("  Email: admin@napsa.co.zm")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()