"""
AML Reports Schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class SARBase(BaseModel):
    """Base Suspicious Activity Report schema"""
    customer_id: int
    transaction_ids: List[int] = []
    report_type: str = "SAR"
    suspicious_activity_type: str
    description: str
    narrative: str
    amount_involved: Optional[Decimal] = None
    date_of_suspicious_activity: datetime
    reporter_name: str
    reporter_title: str


class SARCreate(SARBase):
    """Schema for creating SAR reports"""
    pass


class SARUpdate(BaseModel):
    """Schema for updating SAR reports"""
    suspicious_activity_type: Optional[str] = None
    description: Optional[str] = None
    narrative: Optional[str] = None
    amount_involved: Optional[Decimal] = None
    status: Optional[str] = None


class SuspiciousActivityReport(SARBase):
    """Schema for SAR API responses"""
    id: int
    report_number: str
    status: str = "draft"  # draft, submitted, filed
    filing_date: Optional[datetime] = None
    regulatory_reference: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    
    class Config:
        from_attributes = True


class CTRBase(BaseModel):
    """Base Currency Transaction Report schema"""
    customer_id: int
    transaction_id: int
    transaction_date: datetime
    transaction_amount: Decimal
    currency: str = "USD"
    transaction_type: str
    cash_in_amount: Optional[Decimal] = None
    cash_out_amount: Optional[Decimal] = None
    method_of_payment: str
    purpose_of_transaction: Optional[str] = None


class CTRCreate(CTRBase):
    """Schema for creating CTR reports"""
    pass


class CurrencyTransactionReport(CTRBase):
    """Schema for CTR API responses"""
    id: int
    report_number: str
    status: str = "draft"  # draft, submitted, filed
    filing_date: Optional[datetime] = None
    regulatory_reference: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    
    class Config:
        from_attributes = True


class ReportingMetrics(BaseModel):
    """Schema for reporting metrics"""
    total_sars: int
    total_ctrs: int
    pending_reports: int
    filed_reports: int
    period_start: datetime
    period_end: datetime


class ReportGenerationRequest(BaseModel):
    """Schema for report generation requests"""
    report_type: str  # "SAR", "CTR", "SUMMARY"
    customer_id: Optional[int] = None
    transaction_ids: Optional[List[int]] = []
    date_range: Optional[Dict[str, datetime]] = None
    format: str = "PDF"  # PDF, XML, CSV
    include_attachments: bool = False
    

class ReportGenerationResponse(BaseModel):
    """Schema for report generation responses"""
    report_id: str
    status: str  # "generating", "completed", "failed"
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    generated_at: Optional[datetime] = None
    error_message: Optional[str] = None