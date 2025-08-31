from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class CaseStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    PENDING_REVIEW = "pending_review"
    ESCALATED = "escalated"
    CLOSED_REPORTED = "closed_reported"
    CLOSED_NO_ACTION = "closed_no_action"
    CLOSED_FALSE_POSITIVE = "closed_false_positive"


class CasePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceCase(Base):
    __tablename__ = "compliance_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(100), unique=True, index=True, nullable=False)
    
    # Case Information
    title = Column(String(200), nullable=False)
    description = Column(Text)
    case_type = Column(String(50))  # "AML", "Fraud", "Sanctions", "KYC"
    
    # Customer Information
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"))
    customer_name = Column(String(200))
    customer_account = Column(String(50))
    
    # Risk Assessment
    risk_level = Column(String(50))
    risk_score = Column(Float)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM)
    
    # Investigation Details
    status = Column(Enum(CaseStatus), default=CaseStatus.OPEN)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_date = Column(DateTime)
    
    # Alerts and Transactions
    alert_count = Column(Integer, default=0)
    transaction_count = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    
    # Investigation Summary
    investigation_summary = Column(Text)
    findings = Column(Text)
    recommendations = Column(Text)
    
    # Evidence and Documents
    evidence = Column(JSON)  # Store evidence references
    documents = Column(JSON)  # Store document references
    
    # Decision
    decision = Column(String(100))  # "file_sar", "close", "escalate"
    decision_reason = Column(Text)
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    decided_date = Column(DateTime)
    
    # Reporting
    sar_filed = Column(Boolean, default=False)
    sar_number = Column(String(100))
    reported_to_authorities = Column(Boolean, default=False)
    
    # Timeline
    created_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    closed_date = Column(DateTime)
    
    # Escalation
    escalated = Column(Boolean, default=False)
    escalated_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    escalated_date = Column(DateTime)
    escalation_reason = Column(Text)
    
    # Quality Review
    reviewed = Column(Boolean, default=False)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_date = Column(DateTime)
    review_notes = Column(Text)
    
    # Metrics
    investigation_hours = Column(Float, default=0.0)
    false_positive = Column(Boolean, default=False)
    
    # System Fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    customer = relationship("CustomerProfile", back_populates="cases")
    alerts = relationship("TransactionAlert", back_populates="case")
    sars = relationship("SuspiciousActivityReport", back_populates="case")
    screening_results = relationship("ScreeningResult", back_populates="case")
    comments = relationship("CaseComment", back_populates="case", cascade="all, delete-orphan")
    
    assignee = relationship("User", foreign_keys=[assigned_to])
    decider = relationship("User", foreign_keys=[decided_by])
    escalated_user = relationship("User", foreign_keys=[escalated_to])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    creator = relationship("User", foreign_keys=[created_by])


class CaseComment(Base):
    __tablename__ = "case_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("compliance_cases.id"), nullable=False)
    
    # Comment Details
    comment_type = Column(String(50))  # "note", "action", "decision", "escalation"
    comment_text = Column(Text, nullable=False)
    
    # Attachments
    attachments = Column(JSON)
    
    # Visibility
    is_internal = Column(Boolean, default=True)
    is_confidential = Column(Boolean, default=False)
    
    # System Fields
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    case = relationship("ComplianceCase", back_populates="comments")
    author = relationship("User", foreign_keys=[created_by])