"""
Enhanced Risk Model with all ermdb.sql fields
This can replace the existing risk.py model after migration
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from app.models.enums import RiskStatus, RiskLevel, RiskCategory, ReviewFrequency


class Risk(Base):
    """Enhanced Risk model with comprehensive fields"""
    __tablename__ = "risks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(String(50), unique=True, index=True)  # Unique business identifier
    title = Column(String(500), nullable=False)
    description = Column(Text)
    causes = Column(Text)  # Root causes
    consequences = Column(Text)  # Potential consequences
    
    # Status and Category
    status = Column(Enum(RiskStatus), default=RiskStatus.OPEN)
    category = Column(Enum(RiskCategory), nullable=False)
    is_principal_risk = Column(Boolean, default=False)
    
    # Risk Scoring - Inherent (before controls)
    inherent_impact_id = Column(Integer, ForeignKey("impact_scales.id"))
    inherent_likelihood_id = Column(Integer, ForeignKey("likelihood_scales.id"))
    inherent_risk_level = Column(Enum(RiskLevel))
    inherent_risk_score = Column(Float)
    inherent_risk_rating = Column(Float)
    
    # Risk Scoring - Residual (with current controls)
    residual_impact_id = Column(Integer, ForeignKey("impact_scales.id"))
    residual_likelihood_id = Column(Integer, ForeignKey("likelihood_scales.id"))
    residual_risk_level = Column(Enum(RiskLevel))
    residual_risk_score = Column(Float)
    residual_risk_rating = Column(Float)
    
    # Risk Scoring - Target (with planned controls)
    target_impact_id = Column(Integer, ForeignKey("impact_scales.id"))
    target_likelihood_id = Column(Integer, ForeignKey("likelihood_scales.id"))
    target_risk_level = Column(Enum(RiskLevel))
    target_risk_score = Column(Float)
    target_risk_rating = Column(Float)
    
    # Risk Appetite and Tolerance
    risk_appetite = Column(String(50))
    risk_tolerance = Column(String(50))
    
    # Ownership and Organization
    risk_owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    risk_champion_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    department = Column(String(255))
    organizational_unit_id = Column(UUID(as_uuid=True), ForeignKey("organizational_units.id"))
    
    # Review Management
    review_frequency = Column(Enum(ReviewFrequency))
    next_review_date = Column(Date)
    last_review_date = Column(Date)
    
    # Additional Metadata
    risk_source = Column(String(255))
    detection_date = Column(Date)
    mitigation_plan = Column(Text)
    contingency_plan = Column(Text)
    
    # Financial Impact
    estimated_financial_impact = Column(Float)
    currency = Column(String(3), default='ZMW')
    
    # Audit Fields
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", foreign_keys=[risk_owner_id], back_populates="owned_risks")
    champion = relationship("User", foreign_keys=[risk_champion_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    
    # Impact and Likelihood scales
    inherent_impact = relationship("ImpactScale", foreign_keys=[inherent_impact_id])
    inherent_likelihood = relationship("LikelihoodScale", foreign_keys=[inherent_likelihood_id])
    residual_impact = relationship("ImpactScale", foreign_keys=[residual_impact_id])
    residual_likelihood = relationship("LikelihoodScale", foreign_keys=[residual_likelihood_id])
    target_impact = relationship("ImpactScale", foreign_keys=[target_impact_id])
    target_likelihood = relationship("LikelihoodScale", foreign_keys=[target_likelihood_id])
    
    # Related entities
    risk_assessments = relationship("RiskAssessment", back_populates="risk")
    controls = relationship("RiskControl", back_populates="risk")
    incidents = relationship("Incident", back_populates="risk")
    key_risk_indicators = relationship("KeyRiskIndicator", back_populates="risk")
    treatments = relationship("RiskTreatment", back_populates="risk")
    history = relationship("RiskHistory", back_populates="risk")
    
    def calculate_risk_score(self, impact: int, likelihood: int) -> float:
        """Calculate risk score based on impact and likelihood"""
        return impact * likelihood
    
    def generate_risk_id(self):
        """Generate unique risk ID if not set"""
        if not self.risk_id:
            # Get the next sequence number (in production, use a proper sequence)
            self.risk_id = f"RISK-{str(uuid.uuid4())[:8].upper()}"