from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
# UUID removed - using string IDs now
from app.schemas.base import BaseResponse

class AssessmentBase(BaseModel):
    risk_id: str  # Risk ID (e.g., RISK-2025-0001)
    assessment_period_id: Optional[int] = None  # Assessment Period ID
    likelihood_score: int = Field(..., ge=1, le=5)
    impact_score: int = Field(..., ge=1, le=5)
    control_effectiveness: float = Field(..., ge=0, le=100)
    assessment_criteria: Optional[Dict] = None
    notes: Optional[str] = None
    evidence_links: Optional[List[str]] = None
    next_review_date: Optional[datetime] = None

class AssessmentCreate(AssessmentBase):
    assessment_period_id: int  # Required for creation

class AssessmentUpdate(BaseModel):
    likelihood_score: Optional[int] = Field(None, ge=1, le=5)
    impact_score: Optional[int] = Field(None, ge=1, le=5)
    control_effectiveness: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    evidence_links: Optional[List[str]] = None
    next_review_date: Optional[datetime] = None

class AssessmentResponse(AssessmentBase, BaseResponse):
    assessment_code: Optional[str] = None  # Human-readable ID
    assessor_id: str  # User ID as string
    assessment_period_id: Optional[int] = None  # Assessment Period ID
    assessment_period_name: Optional[str] = None  # Period name for display
    inherent_risk: float
    residual_risk: float
    risk_appetite_status: str
    assessment_date: datetime
    risk_title: Optional[str] = None
    assessor_name: Optional[str] = None
