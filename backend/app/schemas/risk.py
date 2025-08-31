from pydantic import BaseModel, Field, validator
from typing import Optional, Union
from datetime import datetime
# UUID removed - using string IDs now
from app.models.risk import RiskCategoryEnum, RiskStatus
from app.schemas.base import BaseResponse

class RiskBase(BaseModel):
    title: str
    description: str
    category: Union[RiskCategoryEnum, str]
    category_id: Optional[int] = None  # New field for dynamic categories
    status: Union[RiskStatus, str] = RiskStatus.draft
    likelihood: int = Field(..., ge=1, le=5)
    impact: int = Field(..., ge=1, le=5)
    risk_source: Optional[str] = None
    risk_owner_id: Optional[str] = None  # User ID as string
    department: str
    
    @validator('category', pre=True)
    def validate_category(cls, v):
        if isinstance(v, str):
            try:
                return RiskCategoryEnum(v)
            except ValueError:
                raise ValueError(f"Invalid risk category: {v}. Must be one of: {[e.value for e in RiskCategoryEnum]}")
        return v
    
    @validator('status', pre=True)
    def validate_status(cls, v):
        if isinstance(v, str):
            try:
                return RiskStatus(v)
            except ValueError:
                raise ValueError(f"Invalid risk status: {v}. Must be one of: {[e.value for e in RiskStatus]}")
        return v
    
    @validator('likelihood', 'impact', pre=True)
    def validate_scores(cls, v):
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError(f"Score must be an integer between 1 and 5")
        return v

class RiskCreate(RiskBase):
    pass

class RiskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[Union[RiskCategoryEnum, str]] = None
    category_id: Optional[int] = None  # New field for dynamic categories
    status: Optional[Union[RiskStatus, str]] = None
    likelihood: Optional[int] = Field(None, ge=1, le=5)
    impact: Optional[int] = Field(None, ge=1, le=5)
    risk_source: Optional[str] = None
    risk_owner_id: Optional[str] = None  # User ID as string
    department: Optional[str] = None
    
    @validator('category', pre=True)
    def validate_category(cls, v):
        if v is not None and isinstance(v, str):
            try:
                return RiskCategoryEnum(v)
            except ValueError:
                # If it's not a valid enum value, just return the string
                # This allows for backward compatibility
                return v
        return v
    
    @validator('status', pre=True)
    def validate_status(cls, v):
        if v is not None and isinstance(v, str):
            try:
                return RiskStatus(v)
            except ValueError:
                raise ValueError(f"Invalid risk status: {v}. Must be one of: {[e.value for e in RiskStatus]}")
        return v
    
    @validator('likelihood', 'impact', pre=True)
    def validate_scores(cls, v):
        if v is not None and isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError(f"Score must be an integer between 1 and 5")
        return v

class RiskResponse(RiskBase, BaseResponse):
    risk_code: Optional[str] = None  # Human-readable ID
    inherent_risk_score: Optional[float] = None
    residual_risk_score: Optional[float] = None
    risk_owner_name: Optional[str] = None

# If you need a Risk class for compatibility, you can alias it
Risk = RiskResponse  # or RiskBase, depending on your needs