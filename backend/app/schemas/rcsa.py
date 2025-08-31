from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.rcsa import RCSAStatus, RCSAFrequency, RCSASeverity

# Base schemas
class RCSATemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    department: Optional[str] = None
    frequency: RCSAFrequency = RCSAFrequency.quarterly

class RCSATemplateCreate(RCSATemplateBase):
    pass

class RCSATemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    frequency: Optional[RCSAFrequency] = None
    is_active: Optional[bool] = None

class RCSATemplateResponse(RCSATemplateBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    questions_count: Optional[int] = 0
    assessments_count: Optional[int] = 0

    class Config:
        from_attributes = True

# Question schemas
class RCSAQuestionBase(BaseModel):
    question_text: str
    category: Optional[str] = None
    question_type: str = "text"
    options: Optional[Dict[str, Any]] = None
    is_mandatory: bool = True
    weight: float = 1.0
    order_number: int = 0

class RCSAQuestionCreate(RCSAQuestionBase):
    template_id: UUID

class RCSAQuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    category: Optional[str] = None
    question_type: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    is_mandatory: Optional[bool] = None
    weight: Optional[float] = None
    order_number: Optional[int] = None

class RCSAQuestionResponse(RCSAQuestionBase):
    id: UUID
    template_id: UUID

    class Config:
        from_attributes = True

# Assessment schemas  
class RCSAAssessmentBase(BaseModel):
    title: str
    department: str
    assessment_period: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    due_date: Optional[datetime] = None

class RCSAAssessmentCreate(RCSAAssessmentBase):
    template_id: UUID
    assessor_id: Optional[UUID] = None
    reviewer_id: Optional[UUID] = None

class RCSAAssessmentUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    assessment_period: Optional[str] = None
    status: Optional[RCSAStatus] = None
    scheduled_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    assessor_id: Optional[UUID] = None
    reviewer_id: Optional[UUID] = None
    approver_id: Optional[UUID] = None
    executive_summary: Optional[str] = None
    key_findings: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

class RCSAAssessmentResponse(RCSAAssessmentBase):
    id: UUID
    template_id: UUID
    status: RCSAStatus
    started_date: Optional[datetime]
    completed_date: Optional[datetime]
    assessor_id: Optional[UUID]
    reviewer_id: Optional[UUID]
    approver_id: Optional[UUID]
    total_score: Optional[float]
    max_possible_score: Optional[float]
    completion_percentage: float
    executive_summary: Optional[str]
    key_findings: Optional[List[str]]
    recommendations: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    # Related data
    template_name: Optional[str] = None
    assessor_name: Optional[str] = None
    reviewer_name: Optional[str] = None
    questions_count: Optional[int] = 0
    responses_count: Optional[int] = 0
    action_items_count: Optional[int] = 0

    class Config:
        from_attributes = True

# Response schemas
class RCSAResponseBase(BaseModel):
    response_text: Optional[str] = None
    rating_value: Optional[int] = Field(None, ge=1, le=5)
    boolean_value: Optional[bool] = None
    selected_options: Optional[List[str]] = None
    comments: Optional[str] = None

class RCSAResponseCreate(RCSAResponseBase):
    assessment_id: UUID
    question_id: UUID
    evidence_files: Optional[List[str]] = None

class RCSAResponseUpdate(RCSAResponseBase):
    evidence_files: Optional[List[str]] = None

class RCSAResponseResponse(RCSAResponseBase):
    id: UUID
    assessment_id: UUID
    question_id: UUID
    score: Optional[float]
    evidence_files: Optional[List[str]]
    responded_at: datetime
    responded_by_id: Optional[UUID]
    
    # Related data
    question_text: Optional[str] = None
    question_category: Optional[str] = None
    question_weight: Optional[float] = None

    class Config:
        from_attributes = True

# Action Item schemas
class RCSAActionItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    severity: RCSASeverity = RCSASeverity.medium
    due_date: Optional[datetime] = None
    proposed_solution: Optional[str] = None
    verification_criteria: Optional[str] = None

class RCSAActionItemCreate(RCSAActionItemBase):
    assessment_id: UUID
    assigned_to_id: Optional[UUID] = None

class RCSAActionItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[RCSASeverity] = None
    assigned_to_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    proposed_solution: Optional[str] = None
    implementation_notes: Optional[str] = None
    verification_criteria: Optional[str] = None

class RCSAActionItemResponse(RCSAActionItemBase):
    id: UUID
    assessment_id: UUID
    assigned_to_id: Optional[UUID]
    completed_date: Optional[datetime]
    status: str
    progress_percentage: float
    implementation_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Related data
    assessment_title: Optional[str] = None
    assigned_to_name: Optional[str] = None

    class Config:
        from_attributes = True

# Schedule schemas
class RCSAScheduleBase(BaseModel):
    department: str
    frequency: RCSAFrequency
    next_due_date: datetime
    notification_days: int = 7
    auto_create: bool = True

class RCSAScheduleCreate(RCSAScheduleBase):
    template_id: UUID
    default_assessor_id: Optional[UUID] = None
    default_reviewer_id: Optional[UUID] = None

class RCSAScheduleUpdate(BaseModel):
    department: Optional[str] = None
    frequency: Optional[RCSAFrequency] = None
    next_due_date: Optional[datetime] = None
    default_assessor_id: Optional[UUID] = None
    default_reviewer_id: Optional[UUID] = None
    notification_days: Optional[int] = None
    auto_create: Optional[bool] = None
    is_active: Optional[bool] = None

class RCSAScheduleResponse(RCSAScheduleBase):
    id: UUID
    template_id: UUID
    default_assessor_id: Optional[UUID]
    default_reviewer_id: Optional[UUID]
    is_active: bool
    last_generated: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Related data
    template_name: Optional[str] = None
    assessor_name: Optional[str] = None
    reviewer_name: Optional[str] = None

    class Config:
        from_attributes = True

# Dashboard and summary schemas
class RCSADashboardSummary(BaseModel):
    total_templates: int = 0
    total_assessments: int = 0
    pending_assessments: int = 0
    overdue_assessments: int = 0
    completed_this_month: int = 0
    action_items_open: int = 0
    action_items_overdue: int = 0
    completion_rate: float = 0.0
    
class RCSADepartmentSummary(BaseModel):
    department: str
    total_assessments: int = 0
    completed_assessments: int = 0
    pending_assessments: int = 0
    overdue_assessments: int = 0
    avg_completion_time: Optional[float] = None
    last_assessment_date: Optional[datetime] = None

# Bulk operation schemas
class RCSABulkCreateAssessments(BaseModel):
    template_id: UUID
    departments: List[str]
    assessment_period: str
    due_date: datetime
    assessor_assignments: Optional[Dict[str, UUID]] = None  # department -> assessor_id mapping