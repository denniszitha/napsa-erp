from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base

class PolicyStatus(str, enum.Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    published = "published"
    archived = "archived"
    expired = "expired"

class PolicyCategory(str, enum.Enum):
    governance = "governance"
    risk_management = "risk_management"
    compliance = "compliance"
    security = "security"
    operational = "operational"
    financial = "financial"
    hr = "hr"
    it = "it"

class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_number = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    content = Column(Text)  # Full policy text
    
    # Categorization
    category = Column(Enum(PolicyCategory), nullable=False)
    risk_category = Column(String)
    department = Column(String)
    
    # Status and versioning
    status = Column(Enum(PolicyStatus), default=PolicyStatus.draft)
    version = Column(String, default="1.0")
    is_current = Column(Boolean, default=True)
    
    # Dates
    effective_date = Column(DateTime)
    expiry_date = Column(DateTime)
    review_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    archived_at = Column(DateTime)
    
    # Ownership
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by = Column(String)
    modified_by = Column(String)
    approved_by = Column(String)
    
    # Compliance
    compliance_frameworks = Column(JSON)  # List of framework IDs
    controls = Column(JSON)  # List of control IDs
    
    # Metadata
    tags = Column(JSON)  # List of tags
    attachments = Column(JSON)  # List of attachment URLs
    references = Column(JSON)  # External references
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    reviews = relationship("PolicyReview", back_populates="policy")
    approvals = relationship("PolicyApproval", back_populates="policy")

class PolicyReview(Base):
    __tablename__ = "policy_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"))
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    review_date = Column(DateTime, default=datetime.utcnow)
    next_review_date = Column(DateTime)
    
    comments = Column(Text)
    recommendations = Column(Text)
    status = Column(String)  # approved, needs_revision, rejected
    
    # Relationships
    policy = relationship("Policy", back_populates="reviews")
    reviewer = relationship("User")

class PolicyApproval(Base):
    __tablename__ = "policy_approvals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"))
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    approval_date = Column(DateTime, default=datetime.utcnow)
    action = Column(String)  # approved, rejected
    comments = Column(Text)
    
    # Relationships
    policy = relationship("Policy", back_populates="approvals")
    approver = relationship("User")

class PolicyTemplate(Base):
    __tablename__ = "policy_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    category = Column(Enum(PolicyCategory))
    description = Column(Text)
    
    template_content = Column(Text)  # Template with placeholders
    fields = Column(JSON)  # Required fields for the template
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)