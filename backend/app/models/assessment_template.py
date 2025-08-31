"""
Assessment Template Model
For standardized risk assessment templates
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import AssessmentType, AssessmentMethod, AssessmentPriority


class AssessmentTemplate(Base):
    """Templates for standardized risk assessments"""
    __tablename__ = "assessment_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(50), default="1.0")
    template_type = Column(Enum(AssessmentType), nullable=False)
    default_method = Column(Enum(AssessmentMethod), default=AssessmentMethod.QUALITATIVE)
    default_priority = Column(Enum(AssessmentPriority), default=AssessmentPriority.MEDIUM)
    
    # Requirements
    requires_financial_analysis = Column(Boolean, default=False)
    requires_control_assessment = Column(Boolean, default=True)
    requires_quality_review = Column(Boolean, default=False)
    
    # Template content
    assessment_summary_template = Column(Text)
    key_questions = Column(JSON)  # List of assessment questions
    required_evidence = Column(JSON)  # List of required evidence types
    standard_controls = Column(JSON)  # List of standard controls to assess
    
    # Thresholds
    minimum_control_effectiveness = Column(Integer, default=3)
    required_completion_percentage = Column(Float, default=80.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Categorization
    industry_specific = Column(String(100))
    regulatory_framework = Column(String(100))
    
    # Audit fields
    created_by_id = Column(Integer, ForeignKey("users.id"))
    updated_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])