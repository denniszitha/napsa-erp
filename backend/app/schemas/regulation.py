"""
Regulation schemas for API request/response models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class RegulationBase(BaseModel):
    title: str = Field(..., max_length=500, description="Regulation title")
    framework: str = Field(..., max_length=100, description="Regulatory framework")
    description: Optional[str] = Field(None, description="Detailed description")
    compliance_status: Optional[str] = Field("draft", description="Compliance status")
    regulatory_body: Optional[str] = Field(None, max_length=200, description="Regulatory authority")
    jurisdiction: Optional[str] = Field("Zambia", max_length=100, description="Jurisdiction")
    effective_date: Optional[datetime] = Field(None, description="Effective date")
    next_review: Optional[datetime] = Field(None, description="Next review date")
    requirements_count: Optional[int] = Field(0, description="Number of requirements")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    created_by: Optional[str] = Field(None, max_length=100, description="Created by")

class RegulationCreate(RegulationBase):
    """Schema for creating a new regulation"""
    pass

class RegulationUpdate(BaseModel):
    """Schema for updating an existing regulation"""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None)
    compliance_status: Optional[str] = Field(None)
    regulatory_body: Optional[str] = Field(None, max_length=200)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    effective_date: Optional[datetime] = Field(None)
    next_review: Optional[datetime] = Field(None)
    requirements_count: Optional[int] = Field(None)
    tags: Optional[List[str]] = Field(None)

class RegulationResponse(RegulationBase):
    """Schema for regulation response"""
    id: UUID
    controls_mapped: int = Field(0, description="Number of mapped controls")
    last_assessment_date: Optional[datetime] = Field(None)
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_active: bool = True
    version: str = "1.0"

    class Config:
        from_attributes = True

class RegulationSummary(BaseModel):
    """Schema for regulation summary/list view"""
    id: UUID
    title: str
    framework: str
    compliance_status: str
    regulatory_body: Optional[str]
    effective_date: Optional[datetime]
    next_review: Optional[datetime]
    requirements_count: int
    controls_mapped: int

class RegulationStats(BaseModel):
    """Schema for regulation statistics"""
    total_regulations: int
    compliant: int
    partial: int
    non_compliant: int
    compliance_rate: float
    frameworks: dict
    last_updated: datetime

class ComplianceStatus(BaseModel):
    """Schema for compliance status response"""
    overall_compliance: float
    frameworks: dict
    total_regulations: int
    trend: str
    last_assessment: datetime