"""
Risk Scoring Scales Models
For Impact and Likelihood definitions
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class ImpactScale(Base):
    """Impact scale definitions for risk scoring"""
    __tablename__ = "impact_scales"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    financial_min = Column(Float)
    financial_max = Column(Float)
    operational_impact = Column(Text)
    reputational_impact = Column(Text)
    regulatory_impact = Column(Text)
    color_code = Column(String(7))  # Hex color code
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class LikelihoodScale(Base):
    """Likelihood/Probability scale definitions for risk scoring"""
    __tablename__ = "likelihood_scales"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    probability_min = Column(Float)  # 0.0 to 1.0
    probability_max = Column(Float)  # 0.0 to 1.0
    frequency_description = Column(Text)
    color_code = Column(String(7))  # Hex color code
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())