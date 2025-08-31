from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.kri import KRIStatus
from app.schemas.base import BaseResponse

class KRIBase(BaseModel):
    risk_id: UUID
    name: str
    description: Optional[str] = None
    metric_type: str
    lower_threshold: float
    upper_threshold: float
    target_value: float
    measurement_frequency: str
    data_source: str
    responsible_party: str

class KRICreate(KRIBase):
    pass

class KRIUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    lower_threshold: Optional[float] = None
    upper_threshold: Optional[float] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None

class KRIResponse(KRIBase, BaseResponse):
    current_value: Optional[float] = None
    status: KRIStatus
    trend: Optional[str] = None
    last_updated: datetime

class KRIMeasurementCreate(BaseModel):
    kri_id: UUID
    value: float
    notes: Optional[str] = None

class KRIMeasurementResponse(BaseResponse):
    kri_id: UUID
    value: float
    status: KRIStatus
    measurement_date: datetime
    notes: Optional[str] = None
