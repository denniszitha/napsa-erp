"""
AML (Anti-Money Laundering) Models
Database models for AML screening, KYC, and compliance monitoring
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base

class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium" 
    high = "high"
    critical = "critical"

class ScreeningStatus(str, enum.Enum):
    pending = "pending"
    pending_review = "pending_review"
    cleared = "cleared"
    blocked = "blocked"
    false_positive = "false_positive"

class KYCStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"
    expired = "expired"
    under_review = "under_review"

class AMLScreening(Base):
    """AML Screening records"""
    __tablename__ = "aml_screenings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Entity information
    entity_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50))  # Person, Company, etc.
    identification_number = Column(String(100))
    country = Column(String(100))
    
    # Screening results
    match_score = Column(Float, default=0.0)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.low)
    status = Column(SQLEnum(ScreeningStatus), default=ScreeningStatus.pending)
    
    # Additional data
    screening_data = Column(JSON)  # Stores matches, datasets checked, etc.
    notes = Column(Text)
    
    # Audit fields
    screened_by = Column(String(255))
    reviewed_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WatchlistEntry(Base):
    """Internal watchlist entries"""
    __tablename__ = "watchlist_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Entity information
    name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50))
    aliases = Column(JSON)  # List of alternative names
    
    # Watchlist details
    reason = Column(Text, nullable=False)
    risk_level = Column(String(50))
    source = Column(String(255))  # Source of information
    reference_number = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    
    # Audit fields
    added_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class KYCVerification(Base):
    """KYC (Know Your Customer) verification records"""
    __tablename__ = "kyc_verifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Customer information
    customer_name = Column(String(255), nullable=False)
    customer_id = Column(String(100), unique=True, index=True)
    document_type = Column(String(50))  # Passport, ID Card, etc.
    document_number = Column(String(100))
    
    # Verification details
    verification_type = Column(String(50))  # Standard, Enhanced
    status = Column(SQLEnum(KYCStatus), default=KYCStatus.pending)
    verification_score = Column(Float)
    
    # Verification data
    verification_data = Column(JSON)  # Stores address, DOB, nationality, etc.
    documents = Column(JSON)  # List of document references
    
    # Dates
    verified_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Audit fields
    verified_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SuspiciousActivity(Base):
    """Suspicious Activity Reports (SAR)"""
    __tablename__ = "suspicious_activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Entity information
    entity_name = Column(String(255))
    entity_id = Column(String(100))
    entity_type = Column(String(50))
    
    # Activity details
    activity_type = Column(String(100))  # unusual_transaction, pattern_detected, etc.
    description = Column(Text, nullable=False)
    amount = Column(Float)
    currency = Column(String(10))
    
    # Risk assessment
    severity = Column(String(50))  # low, medium, high, critical
    status = Column(String(50))  # reported, under_review, escalated, closed
    
    # Additional data
    activity_data = Column(JSON)  # Transaction details, patterns, etc.
    
    # STR (Suspicious Transaction Report) filing
    str_filed = Column(Boolean, default=False)
    str_reference = Column(String(100))
    str_filed_date = Column(DateTime)
    
    # Audit fields
    reported_by = Column(String(255))
    reviewed_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TransactionMonitoring(Base):
    """Transaction monitoring records"""
    __tablename__ = "transaction_monitoring"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Transaction details
    transaction_id = Column(String(100), unique=True)
    customer_id = Column(String(100))
    account_number = Column(String(50))
    
    # Transaction data
    amount = Column(Float, nullable=False)
    currency = Column(String(10))
    transaction_type = Column(String(50))  # deposit, withdrawal, transfer, etc.
    source_account = Column(String(100))
    destination_account = Column(String(100))
    
    # Risk assessment
    risk_score = Column(Float)
    risk_indicators = Column(JSON)  # List of triggered rules
    alert_generated = Column(Boolean, default=False)
    
    # Status
    status = Column(String(50))  # normal, flagged, blocked, cleared
    
    # Timestamps
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SanctionsList(Base):
    """Sanctions list entries"""
    __tablename__ = "sanctions_lists"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # List information
    list_name = Column(String(255))  # OFAC, UN, EU, etc.
    list_type = Column(String(50))  # sanctions, pep, etc.
    
    # Entity information
    entity_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50))
    aliases = Column(JSON)
    
    # Additional details
    nationality = Column(String(100))
    date_of_birth = Column(String(50))
    place_of_birth = Column(String(255))
    identification_numbers = Column(JSON)
    
    # Sanction details
    programs = Column(JSON)  # List of sanction programs
    remarks = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    effective_date = Column(DateTime)
    expiry_date = Column(DateTime)
    
    # Audit fields
    source_reference = Column(String(255))
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)