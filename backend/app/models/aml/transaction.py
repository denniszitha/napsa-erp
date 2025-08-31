from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    WIRE = "wire"
    CHECK = "check"
    CASH = "cash"
    ACH = "ach"
    CARD = "card"
    OTHER = "other"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"
    FLAGGED = "flagged"
    BLOCKED = "blocked"
    UNDER_REVIEW = "under_review"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    ESCALATED = "escalated"
    CLOSED_CONFIRMED = "closed_confirmed"
    CLOSED_FALSE_POSITIVE = "closed_false_positive"


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Customer Information
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"))
    account_number = Column(String(50), index=True)
    account_name = Column(String(200))
    
    # Counterparty Information
    counterparty_account = Column(String(50))
    counterparty_name = Column(String(200))
    counterparty_bank = Column(String(200))
    counterparty_country = Column(String(2))  # ISO country code
    
    # Transaction Details
    transaction_type = Column(Enum(TransactionType), nullable=False)
    transaction_date = Column(DateTime, nullable=False, index=True)
    value_date = Column(DateTime)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)  # ISO currency code
    amount_usd = Column(Float)  # USD equivalent for reporting
    
    # Transaction Metadata
    reference_number = Column(String(100))
    description = Column(Text)
    purpose_code = Column(String(50))
    branch_code = Column(String(20))
    channel = Column(String(50))  # ATM, Online, Branch, Mobile
    
    # Location Information
    originating_country = Column(String(2))
    destination_country = Column(String(2))
    transaction_location = Column(String(200))
    ip_address = Column(String(45))
    device_id = Column(String(100))
    
    # Risk Scoring
    risk_score = Column(Float, default=0.0)
    ml_score = Column(Float)  # Machine Learning score
    rule_score = Column(Float)  # Rule-based score
    risk_factors = Column(JSON)  # Store risk factors as JSON
    
    # Compliance Flags
    is_high_risk = Column(Boolean, default=False)
    is_cash = Column(Boolean, default=False)
    exceeds_threshold = Column(Boolean, default=False)
    is_structured = Column(Boolean, default=False)
    requires_review = Column(Boolean, default=False)
    
    # Screening Results
    sanctions_hit = Column(Boolean, default=False)
    watchlist_hit = Column(Boolean, default=False)
    adverse_media_hit = Column(Boolean, default=False)
    
    # Status
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    review_status = Column(String(50))
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    
    # System Fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    customer = relationship("CustomerProfile", back_populates="transactions")
    alerts = relationship("TransactionAlert", back_populates="transaction", cascade="all, delete-orphan")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class TransactionAlert(Base):
    __tablename__ = "transaction_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Transaction Reference
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"))
    
    # Alert Details
    alert_type = Column(String(100), nullable=False)  # e.g., "High Amount", "Velocity", "Pattern"
    alert_category = Column(String(100))  # e.g., "AML", "Fraud", "Sanctions"
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.MEDIUM)
    score = Column(Float)
    
    # Alert Description
    title = Column(String(200), nullable=False)
    description = Column(Text)
    details = Column(JSON)  # Store detailed alert information
    
    # Rules/Scenarios Triggered
    rule_id = Column(String(50))
    rule_name = Column(String(200))
    scenario_id = Column(String(50))
    scenario_name = Column(String(200))
    
    # Investigation
    status = Column(Enum(AlertStatus), default=AlertStatus.OPEN)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    investigation_notes = Column(Text)
    
    # Case Management
    case_id = Column(Integer, ForeignKey("compliance_cases.id"))
    escalated = Column(Boolean, default=False)
    escalated_at = Column(DateTime)
    escalated_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Resolution
    resolution = Column(String(100))
    resolution_notes = Column(Text)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    
    # Reporting
    sar_filed = Column(Boolean, default=False)
    ctr_filed = Column(Boolean, default=False)
    
    # System Fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="alerts")
    assignee = relationship("User", foreign_keys=[assigned_to])
    escalated_user = relationship("User", foreign_keys=[escalated_to])
    resolver = relationship("User", foreign_keys=[resolved_by])
    case = relationship("ComplianceCase", back_populates="alerts")