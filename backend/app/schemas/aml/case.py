"""
AML Case Management Schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class CaseStatus(str, Enum):
    """Case status enumeration"""
    NEW = "new"
    ASSIGNED = "assigned" 
    INVESTIGATING = "investigating"
    ESCALATED = "escalated"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"


class CasePriority(str, Enum):
    """Case priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceCaseBase(BaseModel):
    """Base compliance case schema"""
    case_type: str  # "suspicious_activity", "sanctions_match", "kyc_review", "pep_review"
    title: str
    description: str
    priority: CasePriority = CasePriority.MEDIUM
    customer_id: Optional[int] = None
    transaction_ids: Optional[List[int]] = []
    alert_ids: Optional[List[int]] = []
    due_date: Optional[datetime] = None


class ComplianceCaseCreate(ComplianceCaseBase):
    """Schema for creating compliance cases"""
    assigned_to: Optional[int] = None


class ComplianceCaseUpdate(BaseModel):
    """Schema for updating compliance cases"""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[CasePriority] = None
    status: Optional[CaseStatus] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class ComplianceCase(ComplianceCaseBase):
    """Schema for compliance case API responses"""
    id: int
    case_number: str  # Auto-generated unique case number
    status: CaseStatus = CaseStatus.NEW
    assigned_to: Optional[int] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    escalation_level: int = 0
    
    class Config:
        from_attributes = True


class CaseCommentBase(BaseModel):
    """Base case comment schema"""
    comment_text: str
    is_internal: bool = True  # Internal vs external comments
    action_taken: Optional[str] = None  # Action associated with comment


class CaseCommentCreate(CaseCommentBase):
    """Schema for creating case comments"""
    case_id: int


class CaseComment(CaseCommentBase):
    """Schema for case comment API responses"""
    id: int
    case_id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CaseAssignmentRequest(BaseModel):
    """Schema for case assignment requests"""
    case_id: int
    assigned_to: int
    assignment_notes: Optional[str] = None


class CaseEscalationRequest(BaseModel):
    """Schema for case escalation requests"""
    case_id: int
    escalation_reason: str
    escalate_to: int
    priority: Optional[CasePriority] = None


class CaseStatistics(BaseModel):
    """Schema for case management statistics"""
    total_cases: int
    new_cases: int
    assigned_cases: int
    investigating_cases: int
    escalated_cases: int
    closed_cases: int
    overdue_cases: int
    avg_resolution_time: Optional[float] = None  # in days
    case_by_type: Dict[str, int] = {}
    case_by_priority: Dict[str, int] = {}


class CaseActivityLog(BaseModel):
    """Schema for case activity logging"""
    case_id: int
    activity_type: str  # "created", "assigned", "updated", "commented", "escalated", "closed"
    description: str
    performed_by: int
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = {}
    
    class Config:
        from_attributes = True