"""
Base schemas for human-readable ID responses
Replaces UUID with human-readable codes
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class BaseHumanSchema(BaseModel):
    """Base schema with from_attributes config"""
    model_config = ConfigDict(from_attributes=True)

class BaseHumanResponse(BaseHumanSchema):
    """Base response with human-readable ID instead of UUID"""
    # Note: We don't include 'id' field here - each model will define its own code field
    created_at: datetime
    updated_at: Optional[datetime] = None

class RiskHumanResponse(BaseHumanSchema):
    """Risk response with only human-readable ID"""
    id: str = Field(alias="risk_code")  # Map risk_code to id in response
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    likelihood: Optional[int] = None
    impact: Optional[int] = None
    risk_source: Optional[str] = None
    department: Optional[str] = None
    inherent_risk_score: Optional[float] = None
    residual_risk_score: Optional[float] = None
    risk_owner_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class AssessmentHumanResponse(BaseHumanSchema):
    """Assessment response with only human-readable ID"""
    id: str = Field(alias="assessment_code")  # Map assessment_code to id in response
    risk_id: str = Field(default=None)  # Will be populated with risk_code
    likelihood_score: int
    impact_score: int
    control_effectiveness: float
    assessment_criteria: Optional[dict] = None
    notes: Optional[str] = None
    evidence_links: Optional[list] = None
    next_review_date: Optional[datetime] = None
    assessor_id: str = Field(default=None)  # Will be populated with user code if available
    inherent_risk: float
    residual_risk: float
    risk_appetite_status: str
    assessment_date: datetime
    risk_title: Optional[str] = None
    assessor_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )