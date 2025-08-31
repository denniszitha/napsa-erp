from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import uuid

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.incident import (
    Incident, IncidentStatus, IncidentSeverity, IncidentType,
    IncidentTimelineEvent, IncidentCommunication
)
from app.models.risk import Risk
from app.schemas.incident import (
    IncidentCreate, IncidentUpdate, IncidentResponse,
    TimelineEventCreate, TimelineEventResponse,
    IncidentCommunicationCreate, IncidentCommunicationResponse,
    IncidentImpactCalculation, RegulatoryReporting
)
from app.schemas.base import PaginatedResponse

router = APIRouter()

def generate_incident_code(db: Session) -> tuple[str, str]:
    """Generate both incident number and code"""
    year = datetime.now().year
    
    # Get the latest incident number for the year
    latest_incident = db.query(Incident).filter(
        Incident.incident_code.like(f"INC-{year}-%")
    ).order_by(desc(Incident.created_at)).first()
    
    if latest_incident and latest_incident.incident_code:
        try:
            last_num = int(latest_incident.incident_code.split('-')[-1])
            new_num = last_num + 1
        except:
            new_num = 1
    else:
        new_num = 1
    
    incident_code = f"INC-{year}-{new_num:04d}"
    incident_number = f"INC{year}{new_num:06d}"  # Legacy format
    
    return incident_code, incident_number

@router.get("/", response_model=PaginatedResponse)
def get_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[IncidentStatus] = None,
    severity: Optional[IncidentSeverity] = None,
    type: Optional[IncidentType] = None,
    risk_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> PaginatedResponse:
    """Get list of incidents with filtering and pagination"""
    
    query = db.query(Incident)
    
    # Apply filters
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)
    if type:
        query = query.filter(Incident.type == type)
    if risk_id:
        query = query.filter(Incident.risk_id == risk_id)
    if search:
        query = query.filter(
            or_(
                Incident.title.ilike(f"%{search}%"),
                Incident.description.ilike(f"%{search}%"),
                Incident.incident_code.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    total = query.count()
    
    # Get incidents with pagination
    incidents = query.order_by(desc(Incident.created_at)).offset(skip).limit(limit).all()
    
    # Prepare response with additional data
    incident_responses = []
    for incident in incidents:
        incident_dict = {
            "id": str(incident.id),
            "incident_number": incident.incident_number,
            "incident_code": incident.incident_code,
            "title": incident.title,
            "description": incident.description,
            "type": incident.type,
            "severity": incident.severity,
            "status": incident.status,
            "risk_id": incident.risk_id,
            "reported_by_id": str(incident.reported_by_id) if incident.reported_by_id else None,
            "assigned_to_id": str(incident.assigned_to_id) if incident.assigned_to_id else None,
            "detected_at": incident.detected_at,
            "reported_at": incident.reported_at,
            "contained_at": incident.contained_at,
            "resolved_at": incident.resolved_at,
            "closed_at": incident.closed_at,
            "created_at": incident.created_at,
            "updated_at": incident.updated_at,
            "affected_systems": incident.affected_systems,
            "affected_users_count": incident.affected_users_count,
            "financial_impact": incident.financial_impact,
            "data_compromised": incident.data_compromised,
            "regulatory_breach": incident.regulatory_breach if hasattr(incident, 'regulatory_breach') else False,
            "reputational_impact": incident.reputational_impact if hasattr(incident, 'reputational_impact') else None,
            "external_parties_involved": incident.external_parties_involved if hasattr(incident, 'external_parties_involved') else None,
            "initial_response": incident.initial_response,
            "root_cause": incident.root_cause,
            "corrective_actions": incident.corrective_actions,
            "preventive_actions": incident.preventive_actions,
            "lessons_learned": incident.lessons_learned
        }
        
        # Add risk title if risk exists
        if incident.risk_id:
            risk = db.query(Risk).filter(Risk.id == incident.risk_id).first()
            if risk:
                incident_dict["risk_title"] = risk.title
        
        # Add reporter name
        if incident.reported_by_id:
            reporter = db.query(User).filter(User.id == incident.reported_by_id).first()
            if reporter:
                incident_dict["reporter_name"] = reporter.full_name or reporter.username
        
        # Add assignee name
        if incident.assigned_to_id:
            assignee = db.query(User).filter(User.id == incident.assigned_to_id).first()
            if assignee:
                incident_dict["assignee_name"] = assignee.full_name or assignee.username
        
        incident_responses.append(incident_dict)
    
    return PaginatedResponse(
        data=incident_responses,
        total=total,
        skip=skip,
        limit=limit
    )

@router.get("/risks", response_model=List[Dict[str, Any]])
def get_available_risks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Get all available risks for incident association"""
    risks = db.query(Risk).filter(Risk.status == "active").all()
    
    return [
        {
            "id": risk.id,
            "title": risk.title,
            "category": risk.category if hasattr(risk, 'category') else None,
            "inherent_risk_score": risk.inherent_risk_score,
            "residual_risk_score": risk.residual_risk_score
        }
        for risk in risks
    ]

@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    incident: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> IncidentResponse:
    """Create a new incident with automatic risk association"""
    
    # Generate incident codes
    incident_code, incident_number = generate_incident_code(db)
    
    # Validate risk exists if provided
    if incident.risk_id:
        risk = db.query(Risk).filter(Risk.id == incident.risk_id).first()
        if not risk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Risk with ID {incident.risk_id} not found"
            )
    
    # Create incident
    db_incident = Incident(
        incident_code=incident_code,
        incident_number=incident_number,
        title=incident.title,
        description=incident.description,
        type=incident.type,
        severity=incident.severity,
        risk_id=incident.risk_id if incident.risk_id else None,
        reported_by_id=current_user.id,
        assigned_to_id=incident.assigned_to_id if incident.assigned_to_id else None,
        detected_at=incident.detected_at,
        reported_at=datetime.now(timezone.utc),
        affected_systems=incident.affected_systems,
        affected_users_count=incident.affected_users_count,
        financial_impact=incident.financial_impact,
        data_compromised=incident.data_compromised,
        regulatory_breach=incident.regulatory_breach,
        reputational_impact=str(incident.reputational_impact.value) if incident.reputational_impact else None,
        external_parties_involved=incident.external_parties_involved,
        initial_response=incident.initial_response,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    db.add(db_incident)
    
    # Add initial timeline event
    initial_event = IncidentTimelineEvent(
        incident_id=db_incident.id,
        event_type="incident_created",
        description=f"Incident created by {current_user.full_name or current_user.username}",
        performed_by=current_user.full_name or current_user.username,
        event_time=datetime.now(timezone.utc)
    )
    db.add(initial_event)
    
    # If risk is associated, update risk's incident count or status
    if incident.risk_id and incident.severity in ['critical', 'high']:
        # Add timeline event for risk association
        risk_event = IncidentTimelineEvent(
            incident_id=db_incident.id,
            event_type="risk_associated",
            description=f"Associated with risk: {risk.title}",
            performed_by="System",
            event_time=datetime.now(timezone.utc)
        )
        db.add(risk_event)
    
    # Check if regulatory reporting is required
    if incident.regulatory_breach or incident.type in ['compliance_violation', 'regulatory_breach']:
        # Add timeline event for regulatory requirement
        reg_event = IncidentTimelineEvent(
            incident_id=db_incident.id,
            event_type="regulatory_reporting_required",
            description="Regulatory reporting required - PIA notification pending",
            performed_by="System",
            event_time=datetime.now(timezone.utc)
        )
        db.add(reg_event)
    
    db.commit()
    db.refresh(db_incident)
    
    # Prepare response
    response = IncidentResponse.model_validate(db_incident)
    if incident.risk_id and risk:
        response.risk_title = risk.title
    response.reporter_name = current_user.full_name or current_user.username
    
    return response

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> IncidentResponse:
    """Get specific incident with all details"""
    
    incident = db.query(Incident).filter(
        or_(
            Incident.id == incident_id,
            Incident.incident_code == incident_id
        )
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Prepare response with additional data
    response = IncidentResponse.model_validate(incident)
    
    # Add risk title
    if incident.risk_id:
        risk = db.query(Risk).filter(Risk.id == incident.risk_id).first()
        if risk:
            response.risk_title = risk.title
    
    # Add reporter name
    if incident.reported_by_id:
        reporter = db.query(User).filter(User.id == incident.reported_by_id).first()
        if reporter:
            response.reporter_name = reporter.full_name or reporter.username
    
    # Add assignee name
    if incident.assigned_to_id:
        assignee = db.query(User).filter(User.id == incident.assigned_to_id).first()
        if assignee:
            response.assignee_name = assignee.full_name or assignee.username
    
    return response

@router.get("/{incident_id}/timeline", response_model=List[TimelineEventResponse])
def get_incident_timeline(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[TimelineEventResponse]:
    """Get incident timeline events"""
    
    incident = db.query(Incident).filter(
        or_(
            Incident.id == incident_id,
            Incident.incident_code == incident_id
        )
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    timeline_events = db.query(IncidentTimelineEvent).filter(
        IncidentTimelineEvent.incident_id == incident.id
    ).order_by(desc(IncidentTimelineEvent.event_time)).all()
    
    return [TimelineEventResponse.model_validate(event) for event in timeline_events]

@router.post("/{incident_id}/timeline", response_model=TimelineEventResponse)
def add_timeline_event(
    incident_id: str,
    event: TimelineEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> TimelineEventResponse:
    """Add timeline event to incident"""
    
    incident = db.query(Incident).filter(
        or_(
            Incident.id == incident_id,
            Incident.incident_code == incident_id
        )
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    timeline_event = IncidentTimelineEvent(
        incident_id=incident.id,
        event_type=event.event_type,
        description=event.description,
        performed_by=event.performed_by or current_user.full_name or current_user.username,
        event_time=datetime.now(timezone.utc)
    )
    
    db.add(timeline_event)
    db.commit()
    db.refresh(timeline_event)
    
    return TimelineEventResponse.model_validate(timeline_event)

@router.get("/{incident_id}/communications", response_model=List[IncidentCommunicationResponse])
def get_incident_communications(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[IncidentCommunicationResponse]:
    """Get all communications for an incident"""
    
    incident = db.query(Incident).filter(
        or_(
            Incident.id == incident_id,
            Incident.incident_code == incident_id
        )
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    communications = db.query(IncidentCommunication).filter(
        IncidentCommunication.incident_id == incident.id
    ).order_by(desc(IncidentCommunication.sent_at)).all()
    
    return [IncidentCommunicationResponse.model_validate(comm) for comm in communications]

@router.post("/{incident_id}/communications", response_model=IncidentCommunicationResponse)
def add_incident_communication(
    incident_id: str,
    communication: IncidentCommunicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> IncidentCommunicationResponse:
    """Add communication record to incident"""
    
    incident = db.query(Incident).filter(
        or_(
            Incident.id == incident_id,
            Incident.incident_code == incident_id
        )
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    db_communication = IncidentCommunication(
        incident_id=incident.id,
        communication_type=communication.communication_type,
        recipients=communication.recipients,
        subject=communication.subject,
        message=communication.message,
        sent_at=datetime.now(timezone.utc),
        sent_by=current_user.full_name or current_user.username
    )
    
    db.add(db_communication)
    
    # Add timeline event for communication
    timeline_event = IncidentTimelineEvent(
        incident_id=incident.id,
        event_type="communication_sent",
        description=f"{communication.communication_type}: {communication.subject}",
        performed_by=current_user.full_name or current_user.username,
        event_time=datetime.now(timezone.utc)
    )
    db.add(timeline_event)
    
    db.commit()
    db.refresh(db_communication)
    
    return IncidentCommunicationResponse.model_validate(db_communication)

@router.patch("/{incident_id}/status", response_model=IncidentResponse)
def update_incident_status(
    incident_id: str,
    status_update: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> IncidentResponse:
    """Update incident status with lifecycle management"""
    
    incident = db.query(Incident).filter(
        or_(
            Incident.id == incident_id,
            Incident.incident_code == incident_id
        )
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    new_status = status_update.get("status")
    notes = status_update.get("notes", "")
    
    if new_status and hasattr(IncidentStatus, new_status):
        old_status = incident.status
        incident.status = IncidentStatus[new_status]
        incident.updated_at = datetime.now(timezone.utc)
        
        # Update lifecycle timestamps
        if incident.status == IncidentStatus.investigating and not incident.reported_at:
            incident.reported_at = datetime.now(timezone.utc)
        elif incident.status == IncidentStatus.contained and not incident.contained_at:
            incident.contained_at = datetime.now(timezone.utc)
        elif incident.status == IncidentStatus.resolved and not incident.resolved_at:
            incident.resolved_at = datetime.now(timezone.utc)
        elif incident.status == IncidentStatus.closed and not incident.closed_at:
            incident.closed_at = datetime.now(timezone.utc)
        
        # Add timeline event for status change
        timeline_event = IncidentTimelineEvent(
            incident_id=incident.id,
            event_type="status_changed",
            description=f"Status changed from {old_status} to {new_status}. {notes}",
            performed_by=current_user.full_name or current_user.username,
            event_time=datetime.now(timezone.utc)
        )
        db.add(timeline_event)
        
        db.commit()
        db.refresh(incident)
    
    return IncidentResponse.model_validate(incident)

@router.put("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: str,
    incident_update: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> IncidentResponse:
    """Update an incident"""
    
    incident = db.query(Incident).filter(
        or_(
            Incident.id == incident_id,
            Incident.incident_code == incident_id
        )
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    update_data = incident_update.model_dump(exclude_unset=True)
    
    # Track significant changes for timeline
    significant_changes = []
    
    for field, value in update_data.items():
        old_value = getattr(incident, field)
        if old_value != value:
            if field in ['severity', 'type', 'assigned_to_id']:
                significant_changes.append(f"{field}: {old_value} → {value}")
            setattr(incident, field, value)
    
    incident.updated_at = datetime.now(timezone.utc)
    
    # Add timeline event for significant changes
    if significant_changes:
        timeline_event = IncidentTimelineEvent(
            incident_id=incident.id,
            event_type="incident_updated",
            description=f"Updated: {', '.join(significant_changes)}",
            performed_by=current_user.full_name or current_user.username,
            event_time=datetime.now(timezone.utc)
        )
        db.add(timeline_event)
    
    db.commit()
    db.refresh(incident)
    
    return IncidentResponse.model_validate(incident)

@router.post("/{incident_id}/calculate-impact", response_model=IncidentImpactCalculation)
def calculate_incident_impact(
    incident_id: str,
    impact_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> IncidentImpactCalculation:
    """Calculate total financial and operational impact of an incident"""
    
    incident = db.query(Incident).filter(
        or_(
            Incident.id == incident_id,
            Incident.incident_code == incident_id
        )
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Base calculation from incident data
    calculation = IncidentImpactCalculation(
        direct_financial_loss=incident.financial_impact or 0,
        affected_members_count=incident.affected_users_count or 0
    )
    
    # Add provided impact data
    if impact_data:
        calculation.recovery_costs = impact_data.get("recovery_costs", 0)
        calculation.regulatory_penalties = impact_data.get("regulatory_penalties", 0)
        calculation.operational_disruption_cost = impact_data.get("operational_disruption_cost", 0)
        calculation.benefit_payments_delayed_amount = impact_data.get("benefit_payments_delayed_amount", 0)
        calculation.contribution_processing_delayed_amount = impact_data.get("contribution_processing_delayed_amount", 0)
    
    # Calculate reputational damage based on severity and type
    if incident.severity == IncidentSeverity.critical:
        calculation.reputational_damage_estimate = 500000  # ZMW
    elif incident.severity == IncidentSeverity.high:
        calculation.reputational_damage_estimate = 200000
    elif incident.severity == IncidentSeverity.medium:
        calculation.reputational_damage_estimate = 50000
    else:
        calculation.reputational_damage_estimate = 10000
    
    # Adjust for regulatory breaches
    if incident.regulatory_breach:
        calculation.reputational_damage_estimate *= 2
        if calculation.regulatory_penalties == 0:
            # Estimate penalties based on incident type
            if incident.type == IncidentType.regulatory_breach:
                calculation.regulatory_penalties = 1000000  # ZMW
            elif incident.type == IncidentType.compliance_violation:
                calculation.regulatory_penalties = 500000
    
    # Calculate total impact
    calculation.total_impact = (
        calculation.direct_financial_loss +
        calculation.recovery_costs +
        calculation.regulatory_penalties +
        calculation.reputational_damage_estimate +
        calculation.operational_disruption_cost +
        calculation.benefit_payments_delayed_amount +
        calculation.contribution_processing_delayed_amount
    )
    
    # Update incident with calculated impact
    incident.financial_impact = calculation.total_impact
    db.commit()
    
    return calculation

@router.get("/stats/summary", response_model=Dict[str, Any])
def get_incidents_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get incident statistics and summary"""
    
    # Get counts by status
    total_incidents = db.query(Incident).count()
    open_incidents = db.query(Incident).filter(Incident.status == IncidentStatus.open).count()
    investigating = db.query(Incident).filter(Incident.status == IncidentStatus.investigating).count()
    resolved = db.query(Incident).filter(Incident.status == IncidentStatus.resolved).count()
    closed = db.query(Incident).filter(Incident.status == IncidentStatus.closed).count()
    
    # Get counts by severity
    critical = db.query(Incident).filter(Incident.severity == IncidentSeverity.critical).count()
    high = db.query(Incident).filter(Incident.severity == IncidentSeverity.high).count()
    medium = db.query(Incident).filter(Incident.severity == IncidentSeverity.medium).count()
    low = db.query(Incident).filter(Incident.severity == IncidentSeverity.low).count()
    
    # Calculate MTTR for resolved incidents
    resolved_incidents = db.query(Incident).filter(
        and_(
            Incident.status.in_([IncidentStatus.resolved, IncidentStatus.closed]),
            Incident.resolved_at.isnot(None)
        )
    ).all()
    
    if resolved_incidents:
        total_resolution_time = sum(
            (inc.resolved_at - inc.created_at).total_seconds() / 3600  # in hours
            for inc in resolved_incidents
            if inc.resolved_at and inc.created_at
        )
        mttr = total_resolution_time / len(resolved_incidents)
    else:
        mttr = 0
    
    # Get regulatory breaches
    regulatory_breaches = db.query(Incident).filter(
        Incident.regulatory_breach == True
    ).count()
    
    # Get total financial impact
    total_impact = db.query(func.sum(Incident.financial_impact)).scalar() or 0
    
    # Get recent incidents
    recent_incidents = db.query(Incident).order_by(
        desc(Incident.created_at)
    ).limit(5).all()
    
    return {
        "total_incidents": total_incidents,
        "by_status": {
            "open": open_incidents,
            "investigating": investigating,
            "resolved": resolved,
            "closed": closed
        },
        "by_severity": {
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low
        },
        "mttr_hours": round(mttr, 2),
        "regulatory_breaches": regulatory_breaches,
        "total_financial_impact": float(total_impact),
        "recent_incidents": [
            {
                "id": str(inc.id),
                "incident_code": inc.incident_code,
                "title": inc.title,
                "severity": inc.severity.value if inc.severity else None,
                "status": inc.status.value if inc.status else None,
                "created_at": inc.created_at.isoformat() if inc.created_at else None
            }
            for inc in recent_incidents
        ]
    }

@router.delete("/{incident_id}")
def delete_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Delete an incident (admin only)"""
    
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete incidents"
        )
    
    incident = db.query(Incident).filter(
        or_(
            Incident.id == incident_id,
            Incident.incident_code == incident_id
        )
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Delete related timeline events and communications first
    db.query(IncidentTimelineEvent).filter(
        IncidentTimelineEvent.incident_id == incident.id
    ).delete()
    
    db.query(IncidentCommunication).filter(
        IncidentCommunication.incident_id == incident.id
    ).delete()
    
    db.delete(incident)
    db.commit()
    
    return {"message": f"Incident {incident.incident_code} deleted successfully"}