from sqlalchemy import Column, String, Boolean, Enum, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    risk_manager = "risk_manager"
    risk_owner = "risk_owner"
    viewer = "viewer"
    auditor = "auditor"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.viewer)
    department = Column(String)
    phone = Column(String(20), nullable=True)
    position = Column(String(100), nullable=True)
    last_login = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)
    session_token = Column(String(255), nullable=True)
    theme = Column(String(20), default='light')
    language = Column(String(10), default='en')
    timezone = Column(String(50), default='UTC')
    notifications_enabled = Column(Boolean, default=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    must_change_password = Column(Boolean, default=False)
    profile_picture = Column(String(255), nullable=True)
    preferences = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owned_risks = relationship("Risk", back_populates="owner")
    risk_assessments = relationship("RiskAssessment", back_populates="assessor")
