from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, Boolean, JSON, Enum, Float, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base

class ComplianceFramework(str, enum.Enum):
    iso_27001 = "ISO 27001"
    sox = "SOX"
    gdpr = "GDPR"
    basel_iii = "Basel III"
    coso = "COSO"
    nist = "NIST"

class ComplianceStatus(str, enum.Enum):
    compliant = "compliant"
    non_compliant = "non_compliant"
    partially_compliant = "partially_compliant"
    not_applicable = "not_applicable"

class ComplianceRequirement(Base):
    __tablename__ = "compliance_requirements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework = Column(Enum(ComplianceFramework), nullable=False)
    requirement_id = Column(String, nullable=False)  # e.g., "A.5.1.1"
    title = Column(String, nullable=False)
    description = Column(Text)
    
    # Compliance details
    category = Column(String)
    criticality = Column(String)  # high, medium, low
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    mappings = relationship("ComplianceMapping", back_populates="requirement")

class ComplianceMapping(Base):
    __tablename__ = "compliance_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("compliance_requirements.id"))
    
    # Mapped entities
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=True)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id"), nullable=True)
    
    # Compliance status
    status = Column(Enum(ComplianceStatus), default=ComplianceStatus.not_applicable)
    evidence = Column(JSON)  # List of evidence documents/links
    notes = Column(Text)
    
    # Assessment
    last_assessment_date = Column(DateTime)
    next_assessment_date = Column(DateTime)
    assessed_by = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requirement = relationship("ComplianceRequirement", back_populates="mappings")
    control = relationship("Control")
    risk = relationship("Risk")

class ComplianceAssessment(Base):
    __tablename__ = "compliance_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework = Column(Enum(ComplianceFramework), nullable=False)
    
    # Assessment details
    assessment_date = Column(DateTime, default=datetime.utcnow)
    assessor = Column(String)
    
    # Results
    total_requirements = Column(Integer)
    compliant_count = Column(Integer)
    non_compliant_count = Column(Integer)
    partially_compliant_count = Column(Integer)
    not_applicable_count = Column(Integer)
    
    compliance_score = Column(Float)  # Percentage
    
    # Findings
    findings = Column(JSON)
    recommendations = Column(JSON)
    action_items = Column(JSON)
    
    # Report
    report_url = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
