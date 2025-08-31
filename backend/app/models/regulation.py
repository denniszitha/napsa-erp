"""
Regulation model for regulatory compliance management
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.core.database import Base

class Regulation(Base):
    __tablename__ = "regulations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    framework = Column(String(100), nullable=False, index=True)  # e.g., BASEL_III, IFRS, BOZ
    description = Column(Text)
    compliance_status = Column(String(20), default="draft", index=True)  # draft, compliant, partial, non_compliant
    
    # Regulatory details
    regulatory_body = Column(String(200))  # e.g., Bank of Zambia, SEC
    jurisdiction = Column(String(100), default="Zambia")
    effective_date = Column(DateTime)
    next_review = Column(DateTime)
    
    # Compliance tracking
    requirements_count = Column(Integer, default=0)
    controls_mapped = Column(Integer, default=0)
    last_assessment_date = Column(DateTime)
    
    # Metadata
    tags = Column(JSON)  # Array of tags for categorization
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now())
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    # Status tracking
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")

    def __repr__(self):
        return f"<Regulation(id={self.id}, title={self.title}, framework={self.framework})>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "title": self.title,
            "framework": self.framework,
            "description": self.description,
            "compliance_status": self.compliance_status,
            "regulatory_body": self.regulatory_body,
            "jurisdiction": self.jurisdiction,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "next_review": self.next_review.isoformat() if self.next_review else None,
            "requirements_count": self.requirements_count,
            "controls_mapped": self.controls_mapped,
            "last_assessment_date": self.last_assessment_date.isoformat() if self.last_assessment_date else None,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "is_active": self.is_active,
            "version": self.version
        }