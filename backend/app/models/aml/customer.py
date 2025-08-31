from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CustomerType(str, enum.Enum):
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(100), unique=True, index=True, nullable=False)
    account_number = Column(String(50), unique=True, index=True)
    account_name = Column(String(200), nullable=False)
    customer_type = Column(Enum(CustomerType), default=CustomerType.INDIVIDUAL)
    
    # Personal/Corporate Information
    first_name = Column(String(100))
    last_name = Column(String(100))
    company_name = Column(String(200))
    date_of_birth = Column(Date)
    incorporation_date = Column(Date)
    
    # Identification
    national_id = Column(String(50))
    passport_number = Column(String(50))
    tax_id = Column(String(50))
    business_registration = Column(String(100))
    
    # Contact Information
    email = Column(String(100))
    phone_primary = Column(String(20))
    phone_secondary = Column(String(20))
    
    # Address Information
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2))  # ISO country code
    
    # Account Information
    account_open_date = Column(DateTime)
    account_status = Column(String(50), default="active")
    branch_code = Column(String(20))
    relationship_manager = Column(String(100))
    
    # KYC Information
    kyc_status = Column(String(50), default="pending")
    kyc_completed_date = Column(DateTime)
    kyc_review_date = Column(DateTime)
    occupation = Column(String(100))
    employer = Column(String(200))
    income_source = Column(String(200))
    annual_income = Column(Float)
    net_worth = Column(Float)
    
    # Risk Assessment
    risk_score = Column(Float, default=0.0)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    pep_status = Column(Boolean, default=False)
    pep_details = Column(Text)
    high_risk_country = Column(Boolean, default=False)
    high_risk_business = Column(Boolean, default=False)
    
    # Enhanced Due Diligence
    edd_required = Column(Boolean, default=False)
    edd_completed = Column(Boolean, default=False)
    edd_notes = Column(Text)
    
    # System Fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")
    risk_profile = relationship("CustomerRiskProfile", back_populates="customer", uselist=False)
    screening_results = relationship("ScreeningResult", back_populates="customer")
    cases = relationship("ComplianceCase", back_populates="customer")


class CustomerRiskProfile(Base):
    __tablename__ = "customer_risk_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"), unique=True)
    
    # Risk Factors
    geographic_risk = Column(Float, default=0.0)
    product_risk = Column(Float, default=0.0)
    channel_risk = Column(Float, default=0.0)
    customer_type_risk = Column(Float, default=0.0)
    transaction_risk = Column(Float, default=0.0)
    
    # Behavioral Metrics
    avg_monthly_transactions = Column(Float, default=0.0)
    avg_transaction_amount = Column(Float, default=0.0)
    total_transaction_volume = Column(Float, default=0.0)
    unusual_pattern_count = Column(Integer, default=0)
    
    # Compliance Metrics
    str_count = Column(Integer, default=0)  # Suspicious Transaction Reports
    ctr_count = Column(Integer, default=0)  # Currency Transaction Reports
    alert_count = Column(Integer, default=0)
    false_positive_count = Column(Integer, default=0)
    
    # Review Information
    last_review_date = Column(DateTime)
    next_review_date = Column(DateTime)
    review_frequency_days = Column(Integer, default=365)
    
    # Calculated Scores
    composite_risk_score = Column(Float, default=0.0)
    ml_risk_score = Column(Float)  # Machine Learning model score
    rule_based_score = Column(Float)  # Rule-based scoring
    
    # System Fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("CustomerProfile", back_populates="risk_profile")