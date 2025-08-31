"""
Pydantic schemas for Assessment Period
"""

from typing import Optional, List, Union
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
from uuid import UUID

class AssessmentType(str, Enum):
    """Assessment Type Enum matching database values"""
    INITIAL_ASSESSMENT = "Initial Assessment"
    PERIODIC_REVIEW = "Periodic Review"
    TRIGGERED_ASSESSMENT = "Triggered Assessment"
    INTERIM_ASSESSMENT = "Interim Assessment"


class AssessmentPeriodBase(BaseModel):
    """Base schema for Assessment Period"""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the assessment period")
    description: Optional[str] = Field(None, description="Description of the period")
    start_date: date = Field(..., description="Start date of the period")
    end_date: date = Field(..., description="End date of the period")
    assessment_type: AssessmentType = Field(
        default=AssessmentType.PERIODIC_REVIEW,
        description="Type of assessment for this period"
    )
    is_active: bool = Field(default=True, description="Whether the period is active")
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class AssessmentPeriodCreate(AssessmentPeriodBase):
    """Schema for creating Assessment Period"""
    pass


class AssessmentPeriodUpdate(BaseModel):
    """Schema for updating Assessment Period"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    assessment_type: Optional[AssessmentType] = None
    is_active: Optional[bool] = None


class AssessmentPeriodResponse(AssessmentPeriodBase):
    """Schema for Assessment Period response"""
    id: int
    created_by_id: Optional[Union[str, UUID]] = None  # UUID or string
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    total_assessments: Optional[int] = Field(default=0, description="Total assessments in this period")
    days_remaining: Optional[int] = Field(default=0, description="Days remaining in the period")
    progress_percentage: Optional[float] = Field(default=0.0, description="Progress percentage of the period")
    
    class Config:
        orm_mode = True
        from_attributes = True
        
    @validator('total_assessments', always=True)
    def calculate_total_assessments(cls, v, values, **kwargs):
        # This will be calculated in the API endpoint
        return v or 0
    
    @validator('days_remaining', always=True)
    def calculate_days_remaining(cls, v, values):
        if 'end_date' in values:
            from datetime import date as dt
            today = dt.today()
            end_date = values['end_date']
            if isinstance(end_date, dt):
                remaining = (end_date - today).days
                return max(0, remaining)
        return 0
    
    @validator('progress_percentage', always=True)
    def calculate_progress(cls, v, values):
        if 'start_date' in values and 'end_date' in values:
            from datetime import date as dt
            today = dt.today()
            start = values['start_date']
            end = values['end_date']
            
            if isinstance(start, dt) and isinstance(end, dt):
                if today < start:
                    return 0.0
                elif today > end:
                    return 100.0
                else:
                    total_days = (end - start).days
                    elapsed_days = (today - start).days
                    if total_days > 0:
                        return round((elapsed_days / total_days) * 100, 2)
        return 0.0


class AssessmentPeriodList(BaseModel):
    """Schema for paginated list of Assessment Periods"""
    data: List[AssessmentPeriodResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        orm_mode = True


class AssessmentPeriodStatistics(BaseModel):
    """Schema for Assessment Period statistics"""
    period_id: int
    period_name: str
    start_date: date
    end_date: date
    total_assessments: int
    completed_assessments: int
    pending_assessments: int
    in_progress_assessments: int
    is_active: bool
    days_remaining: int
    progress_percentage: float
    average_risk_score: Optional[float] = None
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0