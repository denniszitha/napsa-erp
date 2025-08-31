from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    
    id = Column(String(20), primary_key=True)  # Human-readable ID (e.g., ASMT-2025-0001)
    risk_id = Column(String(20), ForeignKey("risks.id"), nullable=False)
    assessor_id = Column(String(50), ForeignKey("users.id"), nullable=False)  # Keep as UUID string for users
    assessment_period_id = Column(Integer, ForeignKey("assessment_periods.id"), nullable=True)
    
    # Assessment Details
    likelihood_score = Column(Integer)  # 1-5
    impact_score = Column(Integer)  # 1-5
    control_effectiveness = Column(Float)  # 0-100%
    
    # Calculations
    inherent_risk = Column(Float)
    residual_risk = Column(Float)
    risk_appetite_status = Column(String)  # within/exceeds
    
    # Additional Data
    assessment_criteria = Column(JSON)
    notes = Column(Text)
    evidence_links = Column(JSON)
    
    assessment_date = Column(DateTime, default=datetime.utcnow)
    next_review_date = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    risk = relationship("Risk", back_populates="assessments")
    assessor = relationship("User", back_populates="risk_assessments")
    assessment_period = relationship("AssessmentPeriod", back_populates="risk_assessments")
