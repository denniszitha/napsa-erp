"""
Initial database setup - creates admin user
"""
import sys
sys.path.append('.')

from app.core.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.core.security import get_password_hash

# Create all tables
Base.metadata.create_all(bind=engine)

# Create initial admin user
db = SessionLocal()

admin_user = db.query(User).filter(User.username == "admin").first()
if not admin_user:
    admin_user = User(
        email="admin@napsa.co.zm",
        username="admin",
        full_name="System Administrator",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_superuser=True,
        role=UserRole.admin,
        department="IT"
    )
    db.add(admin_user)
    db.commit()
    print("Admin user created successfully!")
    print("Username: admin")
    print("Password: admin123")
    print("Please change the password after first login!")
else:
    print("Admin user already exists")

db.close()
