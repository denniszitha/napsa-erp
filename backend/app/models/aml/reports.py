from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum, JSON, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class ReportStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"


class ReportType(str, enum.Enum):
    SAR = "sar"  # Suspicious Activity Report
    STR = "str"  # Suspicious Transaction Report
    CTR = "ctr"  # Currency Transaction Report
    NTR = "ntr"  # Nil Transaction Report
    OTHER = "other"


class SuspiciousActivityReport(Base):
    __tablename__ = "suspicious_activity_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_number = Column(String(100), unique=True, index=True, nullable=False)
    report_type = Column(Enum(ReportType), default=ReportType.SAR)
    
    # Case Information
    case_id = Column(Integer, ForeignKey("compliance_cases.id"))
    case_number = Column(String(100))
    
    # Customer Information
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"))
    customer_name = Column(String(200))
    customer_account = Column(String(50))
    
    # Report Details
    filing_date = Column(Date, nullable=False)
    reporting_period_start = Column(Date)
    reporting_period_end = Column(Date)
    
    # Suspicious Activity Details
    activity_date_start = Column(Date)
    activity_date_end = Column(Date)
    total_amount = Column(Float)
    currency = Column(String(3))
    transaction_count = Column(Integer)
    
    # Narrative
    activity_description = Column(Text, nullable=False)
    suspicious_reason = Column(Text, nullable=False)
    action_taken = Column(Text)
    
    # Categories and Typologies
    activity_categories = Column(JSON)  # e.g., ["money_laundering", "terrorist_financing"]
    typologies = Column(JSON)  # Specific typologies identified
    red_flags = Column(JSON)  # Red flags identified
    
    # Related Entities
    related_parties = Column(JSON)  # Other parties involved
    related_accounts = Column(JSON)  # Other accounts involved
    related_transactions = Column(JSON)  # Transaction IDs
    
    # Supporting Documentation
    supporting_documents = Column(JSON)  # File references
    attachments = Column(JSON)
    
    # Review and Approval
    status = Column(Enum(ReportStatus), default=ReportStatus.DRAFT)
    prepared_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    prepared_date = Column(DateTime)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_date = Column(DateTime)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_date = Column(DateTime)
    
    # Submission Details
    submitted_to = Column(String(200))  # Regulatory authority
    submitted_date = Column(DateTime)
    submission_reference = Column(String(100))
    acknowledgment_number = Column(String(100))
    acknowledgment_date = Column(DateTime)
    
    # Follow-up
    requires_follow_up = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    follow_up_notes = Column(Text)
    
    # Quality Review
    quality_score = Column(Float)
    quality_notes = Column(Text)
    
    # System Fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    case = relationship("ComplianceCase", back_populates="sars")
    customer = relationship("CustomerProfile")
    preparer = relationship("User", foreign_keys=[prepared_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    approver = relationship("User", foreign_keys=[approved_by])


class CurrencyTransactionReport(Base):
    __tablename__ = "currency_transaction_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_number = Column(String(100), unique=True, index=True, nullable=False)
    
    # Customer Information
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"))
    customer_name = Column(String(200), nullable=False)
    customer_account = Column(String(50))
    customer_id_type = Column(String(50))
    customer_id_number = Column(String(100))
    
    # Transaction Information
    transaction_date = Column(Date, nullable=False)
    transaction_type = Column(String(50))  # deposit, withdrawal, exchange
    
    # Amount Information
    total_cash_in = Column(Float, default=0.0)
    total_cash_out = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    
    # Multiple Transactions
    aggregated = Column(Boolean, default=False)
    transaction_count = Column(Integer, default=1)
    transactions = Column(JSON)  # Store transaction IDs or details
    
    # Person Conducting Transaction (if different from account holder)
    conductor_name = Column(String(200))
    conductor_id_type = Column(String(50))
    conductor_id_number = Column(String(100))
    on_behalf_of = Column(String(200))
    
    # Location Information
    branch_code = Column(String(20))
    branch_name = Column(String(200))
    teller_id = Column(String(50))
    
    # Filing Information
    filing_date = Column(Date, nullable=False)
    filing_deadline = Column(Date)
    
    # Status
    status = Column(Enum(ReportStatus), default=ReportStatus.DRAFT)
    filed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    filed_date = Column(DateTime)
    
    # Regulatory Information
    regulatory_reference = Column(String(100))
    batch_number = Column(String(100))
    
    # Exemption Information
    exempted = Column(Boolean, default=False)
    exemption_type = Column(String(100))
    exemption_reference = Column(String(100))
    
    # System Fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("CustomerProfile")
    filer = relationship("User", foreign_keys=[filed_by])