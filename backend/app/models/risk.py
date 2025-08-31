from sqlalchemy import Column, String, Text, Integer, Float, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base

# Keep the old enum for backward compatibility (can be removed later)
class RiskCategoryEnum(str, enum.Enum):
    strategic = "strategic"
    operational = "operational"
    financial = "financial"
    compliance = "compliance"
    cyber = "cyber"
    reputational = "reputational"

class RiskStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    under_review = "under_review"
    closed = "closed"
    archived = "archived"

class Risk(Base):
    __tablename__ = "risks"
    
    id = Column(String(20), primary_key=True)  # Human-readable ID (e.g., RISK-2025-0001)
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(Enum(RiskCategoryEnum), nullable=True)  # Keep for backward compatibility
    category_id = Column(Integer, ForeignKey("risk_categories.id"), nullable=True)  # New foreign key
    status = Column(Enum(RiskStatus), default=RiskStatus.draft)
    
    # Risk Scores
    likelihood = Column(Integer)  # 1-5
    impact = Column(Integer)  # 1-5
    inherent_risk_score = Column(Float)
    residual_risk_score = Column(Float)
    
    # Matrix relationship
    matrix_id = Column(String(20), ForeignKey("risk_matrices.id"), nullable=True)
    
    # Metadata
    risk_source = Column(String)
    risk_owner_id = Column(String(50), ForeignKey("users.id"))  # Keep as UUID string for users
    department = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="owned_risks")
    matrix = relationship("RiskMatrix")
    risk_category = relationship("RiskCategory", back_populates="risks")  # New relationship
    assessments = relationship("RiskAssessment", back_populates="risk")
    controls = relationship("RiskControl", back_populates="risk")
    kris = relationship("KeyRiskIndicator", back_populates="risk")

    # Add this to the Risk class relationships
    treatments = relationship("RiskTreatment", back_populates="risk", lazy="dynamic")
