from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.workflow import TreatmentStrategy, WorkflowStatus
from app.schemas.base import BaseResponse

class TreatmentBase(BaseModel):
    risk_id: Optional[str] = None  # Made optional to handle existing NULL values
    strategy: TreatmentStrategy
    title: str
    description: Optional[str] = None
    action_plan: str
    responsible_party: str
    target_date: datetime
    estimated_cost: Optional[float] = None
    expected_risk_reduction: Optional[float] = Field(None, ge=0, le=100)

class TreatmentCreate(TreatmentBase):
    risk_id: str  # Required for new treatments

class TreatmentUpdate(BaseModel):
    strategy: Optional[TreatmentStrategy] = None
    title: Optional[str] = None
    description: Optional[str] = None
    action_plan: Optional[str] = None
    responsible_party: Optional[str] = None
    target_date: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    expected_risk_reduction: Optional[float] = Field(None, ge=0, le=100)

class TreatmentResponse(TreatmentBase, BaseResponse):
    status: WorkflowStatus
    created_by_id: UUID
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None

class TreatmentActionCreate(BaseModel):
    treatment_id: str  # Changed from UUID to str
    action: str
    description: Optional[str] = None
    assigned_to: str
    due_date: datetime

class TreatmentActionResponse(BaseResponse):
    treatment_id: str  # Changed from UUID to str
    action: str
    description: Optional[str] = None
    assigned_to: str
    due_date: datetime
    is_completed: bool
    completed_date: Optional[datetime] = None
    notes: Optional[str] = None
