from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CustomerType(str, Enum):
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"


class CustomerProfileBase(BaseModel):
    customer_id: str
    account_number: Optional[str] = None
    account_name: str
    customer_type: CustomerType = CustomerType.INDIVIDUAL
    
    # Personal/Corporate Information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    incorporation_date: Optional[date] = None
    
    # Identification
    national_id: Optional[str] = None
    passport_number: Optional[str] = None
    tax_id: Optional[str] = None
    business_registration: Optional[str] = None
    
    # Contact Information
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    
    # Address Information
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = Field(None, max_length=2)
    
    # KYC Information
    occupation: Optional[str] = None
    employer: Optional[str] = None
    income_source: Optional[str] = None
    annual_income: Optional[float] = None
    net_worth: Optional[float] = None


class CustomerProfileCreate(CustomerProfileBase):
    branch_code: Optional[str] = None
    relationship_manager: Optional[str] = None
    
    @validator('customer_type')
    def validate_customer_type(cls, v, values):
        if v == CustomerType.INDIVIDUAL:
            if not values.get('first_name') or not values.get('last_name'):
                raise ValueError('First name and last name required for individual customers')
        elif v == CustomerType.CORPORATE:
            if not values.get('company_name'):
                raise ValueError('Company name required for corporate customers')
        return v


class CustomerProfileUpdate(BaseModel):
    account_name: Optional[str] = None
    customer_type: Optional[CustomerType] = None
    
    # Personal/Corporate Information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    incorporation_date: Optional[date] = None
    
    # Contact Information
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    
    # Address Information
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = Field(None, max_length=2)
    
    # KYC Information
    kyc_status: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    income_source: Optional[str] = None
    annual_income: Optional[float] = None
    net_worth: Optional[float] = None
    
    # Risk Assessment
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    pep_status: Optional[bool] = None
    pep_details: Optional[str] = None
    
    # Enhanced Due Diligence
    edd_required: Optional[bool] = None
    edd_completed: Optional[bool] = None
    edd_notes: Optional[str] = None


class CustomerProfile(CustomerProfileBase):
    id: int
    account_open_date: Optional[datetime] = None
    account_status: str = "active"
    branch_code: Optional[str] = None
    relationship_manager: Optional[str] = None
    
    # KYC Status
    kyc_status: str = "pending"
    kyc_completed_date: Optional[datetime] = None
    kyc_review_date: Optional[datetime] = None
    
    # Risk Assessment
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    pep_status: bool = False
    pep_details: Optional[str] = None
    high_risk_country: bool = False
    high_risk_business: bool = False
    
    # Enhanced Due Diligence
    edd_required: bool = False
    edd_completed: bool = False
    edd_notes: Optional[str] = None
    
    # System Fields
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
    # Related Data
    risk_profile: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class CustomerRiskProfileBase(BaseModel):
    # Risk Factors
    geographic_risk: float = 0.0
    product_risk: float = 0.0
    channel_risk: float = 0.0
    customer_type_risk: float = 0.0
    transaction_risk: float = 0.0
    
    # Behavioral Metrics
    avg_monthly_transactions: float = 0.0
    avg_transaction_amount: float = 0.0
    total_transaction_volume: float = 0.0
    unusual_pattern_count: int = 0
    
    # Review Information
    review_frequency_days: int = 365


class CustomerRiskProfile(CustomerRiskProfileBase):
    id: int
    customer_id: int
    
    # Compliance Metrics
    str_count: int = 0
    ctr_count: int = 0
    alert_count: int = 0
    false_positive_count: int = 0
    
    # Review Information
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    
    # Calculated Scores
    composite_risk_score: float = 0.0
    ml_risk_score: Optional[float] = None
    rule_based_score: Optional[float] = None
    
    # System Fields
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True