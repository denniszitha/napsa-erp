from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.control import ControlType, ControlStatus
from app.schemas.base import BaseResponse

class ControlBase(BaseModel):
    name: str
    description: str
    type: ControlType
    control_owner: str
    implementation_status: str
    testing_frequency: str

class ControlCreate(ControlBase):
    pass

class ControlUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[ControlType] = None
    status: Optional[ControlStatus] = None
    control_owner: Optional[str] = None
    implementation_status: Optional[str] = None
    testing_frequency: Optional[str] = None
    effectiveness_rating: Optional[float] = Field(None, ge=0, le=100)

class ControlResponse(ControlBase, BaseResponse):
    status: ControlStatus
    effectiveness_rating: Optional[float] = None
    last_test_date: Optional[datetime] = None
    next_test_date: Optional[datetime] = None

class RiskControlMapping(BaseModel):
    risk_id: UUID
    control_id: UUID
    coverage_percentage: float = Field(..., ge=0, le=100)
    criticality: str
