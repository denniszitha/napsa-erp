from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, validator
from enum import Enum

class IncidentType(str, Enum):
    security_breach = "security_breach"
    data_loss = "data_loss"
    system_failure = "system_failure"
    compliance_violation = "compliance_violation"
    operational_error = "operational_error"
    third_party_issue = "third_party_issue"
    fraud_suspected = "fraud_suspected"
    regulatory_breach = "regulatory_breach"
    member_complaint = "member_complaint"

class IncidentSeverity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class IncidentStatus(str, Enum):
    open = "open"
    investigating = "investigating"
    contained = "contained"
    resolved = "resolved"
    closed = "closed"

class ReputationalImpact(str, Enum):
    severe = "severe"
    high = "high"
    medium = "medium"
    low = "low"
    minimal = "minimal"

class IncidentBase(BaseModel):
    title: str
    description: str
    type: IncidentType  # Changed from incident_type to match DB
    severity: IncidentSeverity
    risk_id: Optional[str] = None  # Link to risk
    detected_at: datetime
    
    # NAPSA-specific fields
    affected_systems: Optional[List[str]] = None
    affected_users_count: Optional[int] = None
    financial_impact: Optional[float] = None
    data_compromised: Optional[bool] = False
    regulatory_breach: Optional[bool] = False
    reputational_impact: Optional[ReputationalImpact] = None
    external_parties_involved: Optional[str] = None
    
    # Member impact (NAPSA-specific)
    affected_member_accounts: Optional[List[str]] = None
    benefit_payments_delayed: Optional[bool] = False
    contribution_processing_affected: Optional[bool] = False

class IncidentCreate(IncidentBase):
    assigned_to_id: Optional[str] = None
    initial_response: Optional[str] = None
    
    @validator('risk_id')
    def validate_risk_id(cls, v):
        # Handle empty strings as None
        if v == '':
            return None
        # Ensure risk_id follows valid patterns: RISK-YYYY-XXXX or NAPSA-XXX-NNN
        if v and not (v.startswith('RISK-') or v.startswith('NAPSA-')):
            raise ValueError('Invalid risk ID format')
        return v

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[IncidentType] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    assigned_to_id: Optional[str] = None
    contained_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Resolution details
    root_cause: Optional[str] = None
    corrective_actions: Optional[List[Dict[str, Any]]] = None
    preventive_actions: Optional[List[Dict[str, Any]]] = None
    lessons_learned: Optional[str] = None
    
    # Impact updates
    financial_impact: Optional[float] = None
    affected_users_count: Optional[int] = None
    reputational_impact: Optional[ReputationalImpact] = None

class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    incident_number: str
    incident_code: Optional[str] = None
    title: str
    description: Optional[str] = None
    type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    
    # IDs as strings (converted from UUID)
    risk_id: Optional[str] = None
    reported_by_id: Optional[str] = None
    assigned_to_id: Optional[str] = None
    
    # Timestamps
    detected_at: datetime
    reported_at: Optional[datetime] = None
    contained_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Impact fields
    affected_systems: Optional[List[Any]] = None
    affected_users_count: Optional[int] = None
    financial_impact: Optional[float] = None
    data_compromised: Optional[bool] = None
    regulatory_breach: Optional[bool] = None
    reputational_impact: Optional[str] = None
    external_parties_involved: Optional[str] = None
    
    # Response fields
    initial_response: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_actions: Optional[List[Any]] = None
    preventive_actions: Optional[List[Any]] = None
    lessons_learned: Optional[str] = None
    
    # Related data (populated in API)
    risk_title: Optional[str] = None
    reporter_name: Optional[str] = None
    assignee_name: Optional[str] = None
    
    @validator('id', 'reported_by_id', 'assigned_to_id', pre=True)
    def convert_uuid_to_string(cls, v):
        if v:
            return str(v)
        return v

class TimelineEventCreate(BaseModel):
    event_type: str
    description: str
    performed_by: Optional[str] = None

class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    incident_id: str
    event_type: str
    description: str
    event_time: datetime
    performed_by: Optional[str] = None
    
    @validator('id', 'incident_id', pre=True)
    def convert_uuid_to_string(cls, v):
        if v:
            return str(v)
        return v

class IncidentCommunicationCreate(BaseModel):
    communication_type: str  # internal_update, stakeholder_notice, regulatory_report
    recipients: List[str]
    subject: str
    message: str

class IncidentCommunicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    incident_id: str
    communication_type: str
    recipients: List[Any]
    subject: str
    message: str
    sent_at: datetime
    sent_by: str
    
    @validator('id', 'incident_id', pre=True)
    def convert_uuid_to_string(cls, v):
        if v:
            return str(v)
        return v

# NAPSA-specific schemas
class IncidentImpactCalculation(BaseModel):
    """Calculate total impact of an incident"""
    direct_financial_loss: float = 0
    recovery_costs: float = 0
    regulatory_penalties: float = 0
    reputational_damage_estimate: float = 0
    operational_disruption_cost: float = 0
    total_impact: float = 0
    
    affected_members_count: int = 0
    benefit_payments_delayed_amount: float = 0
    contribution_processing_delayed_amount: float = 0

class IncidentEscalation(BaseModel):
    """Escalation criteria and thresholds"""
    escalate_to: str
    escalation_reason: str
    escalation_threshold_breached: str
    escalated_at: datetime

class RegulatoryReporting(BaseModel):
    """Track regulatory reporting requirements"""
    regulator: str  # PIA, BOZ, SEC
    reporting_deadline: datetime
    report_submitted: bool = False
    submission_date: Optional[datetime] = None
    reference_number: Optional[str] = None
    penalties_imposed: Optional[float] = None