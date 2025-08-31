from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    WIRE = "wire"
    CHECK = "check"
    CASH = "cash"
    ACH = "ach"
    CARD = "card"
    OTHER = "other"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"
    FLAGGED = "flagged"
    BLOCKED = "blocked"
    UNDER_REVIEW = "under_review"


class AlertStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    ESCALATED = "escalated"
    CLOSED_CONFIRMED = "closed_confirmed"
    CLOSED_FALSE_POSITIVE = "closed_false_positive"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TransactionBase(BaseModel):
    transaction_id: str
    account_number: str
    account_name: str
    
    # Counterparty Information
    counterparty_account: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_bank: Optional[str] = None
    counterparty_country: Optional[str] = Field(None, max_length=2)
    
    # Transaction Details
    transaction_type: TransactionType
    transaction_date: datetime
    value_date: Optional[datetime] = None
    amount: float = Field(..., gt=0)
    currency: str = Field(..., max_length=3)
    
    # Transaction Metadata
    reference_number: Optional[str] = None
    description: Optional[str] = None
    purpose_code: Optional[str] = None
    branch_code: Optional[str] = None
    channel: Optional[str] = None
    
    # Location Information
    originating_country: Optional[str] = Field(None, max_length=2)
    destination_country: Optional[str] = Field(None, max_length=2)
    transaction_location: Optional[str] = None


class TransactionCreate(TransactionBase):
    customer_id: Optional[int] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        if len(v) != 3:
            raise ValueError('Currency must be 3-letter ISO code')
        return v.upper()


class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    risk_score: Optional[float] = None
    review_status: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    
    # Compliance Flags
    is_high_risk: Optional[bool] = None
    requires_review: Optional[bool] = None
    
    # Screening Results
    sanctions_hit: Optional[bool] = None
    watchlist_hit: Optional[bool] = None
    adverse_media_hit: Optional[bool] = None


class Transaction(TransactionBase):
    id: int
    customer_id: Optional[int] = None
    
    # USD Equivalent
    amount_usd: Optional[float] = None
    
    # Additional Metadata
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    
    # Risk Scoring
    risk_score: float = 0.0
    ml_score: Optional[float] = None
    rule_score: Optional[float] = None
    risk_factors: Optional[Dict[str, Any]] = None
    
    # Compliance Flags
    is_high_risk: bool = False
    is_cash: bool = False
    exceeds_threshold: bool = False
    is_structured: bool = False
    requires_review: bool = False
    
    # Screening Results
    sanctions_hit: bool = False
    watchlist_hit: bool = False
    adverse_media_hit: bool = False
    
    # Status
    status: TransactionStatus = TransactionStatus.PENDING
    review_status: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    
    # System Fields
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    
    # Related Data
    alerts: List["TransactionAlert"] = []
    
    class Config:
        from_attributes = True


class TransactionAlertBase(BaseModel):
    alert_type: str
    alert_category: Optional[str] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    title: str
    description: Optional[str] = None
    
    # Rules/Scenarios
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    scenario_id: Optional[str] = None
    scenario_name: Optional[str] = None


class TransactionAlertCreate(TransactionAlertBase):
    transaction_id: int
    customer_id: Optional[int] = None
    score: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class TransactionAlert(TransactionAlertBase):
    id: int
    alert_id: str
    transaction_id: int
    customer_id: Optional[int] = None
    
    # Alert Details
    score: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    
    # Investigation
    status: AlertStatus = AlertStatus.OPEN
    assigned_to: Optional[int] = None
    investigation_notes: Optional[str] = None
    
    # Case Management
    case_id: Optional[int] = None
    escalated: bool = False
    escalated_at: Optional[datetime] = None
    escalated_to: Optional[int] = None
    
    # Resolution
    resolution: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    
    # Reporting
    sar_filed: bool = False
    ctr_filed: bool = False
    
    # System Fields
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True