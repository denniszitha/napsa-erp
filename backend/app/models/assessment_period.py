"""
Assessment Period Model
For managing assessment cycles and periods
"""

from sqlalchemy import Column, Integer, String, Text, Date, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum

class AssessmentType(str, Enum):
    """Assessment Type Enum matching database values"""
    INITIAL_ASSESSMENT = "Initial Assessment"
    PERIODIC_REVIEW = "Periodic Review"
    TRIGGERED_ASSESSMENT = "Triggered Assessment"
    INTERIM_ASSESSMENT = "Interim Assessment"


class AssessmentPeriod(Base):
    """Assessment periods for risk assessment cycles"""
    __tablename__ = "assessment_periods"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    assessment_type = Column(String(50), default="Periodic Review")
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_by_id = Column(String(50), ForeignKey("users.id"))  # UUID as string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    risk_assessments = relationship("RiskAssessment", back_populates="assessment_period")