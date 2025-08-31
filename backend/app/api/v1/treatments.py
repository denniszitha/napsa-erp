from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone

from app.api.deps import get_db, get_current_active_user
from app.models.workflow import RiskTreatment, TreatmentAction, WorkflowStatus
from app.models.risk import Risk
from app.models.user import User
from app.schemas.treatment import (
    TreatmentCreate, TreatmentUpdate, TreatmentResponse,
    TreatmentActionCreate, TreatmentActionResponse
)
from app.services.audit import audit_service
from app.services.email import email_service

router = APIRouter()

@router.get("/")
def read_treatments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[WorkflowStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get risk treatments with risk details"""
    query = db.query(RiskTreatment).join(Risk)
    
    if status:
        query = query.filter(RiskTreatment.status == status)
    
    treatments = query.offset(skip).limit(limit).all()
    
    # Convert to response format with risk details
    result = []
    for treatment in treatments:
        treatment_data = TreatmentResponse.model_validate(treatment)
        # Add risk title to the response
        treatment_dict = treatment_data.model_dump()
        treatment_dict['risk_title'] = treatment.risk.title if treatment.risk else 'Unknown Risk'
        result.append(treatment_dict)
    
    return result

@router.post("/", response_model=TreatmentResponse)
async def create_treatment(
    treatment_in: TreatmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create risk treatment plan"""
    # Verify risk exists
    risk = db.query(Risk).filter(Risk.id == treatment_in.risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    treatment = RiskTreatment(
        **treatment_in.model_dump(),
        created_by_id=current_user.id,
        status=WorkflowStatus.draft
    )
    db.add(treatment)
    db.commit()
    db.refresh(treatment)
    
    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="CREATE",
        entity_type="treatment",
        entity_id=str(treatment.id),
        entity_name=treatment.title,
        new_values=treatment_in.model_dump(),
        description=f"Created treatment plan for risk: {risk.title}",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return TreatmentResponse.model_validate(treatment)

@router.post("/{treatment_id}/submit-for-approval")
async def submit_for_approval(
    treatment_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Submit treatment for approval"""
    treatment = db.query(RiskTreatment).filter(RiskTreatment.id == treatment_id).first()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    if treatment.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if treatment.status != WorkflowStatus.draft:
        raise HTTPException(status_code=400, detail="Treatment not in draft status")
    
    treatment.status = WorkflowStatus.pending_approval
    db.commit()
    
    # Send email notification to approvers
    approvers = db.query(User).filter(User.role.in_(["admin", "risk_manager"])).all()
    approver_emails = [u.email for u in approvers]
    
    if approver_emails:
        await email_service.send_email(
            to_emails=approver_emails,
            subject=f"Risk Treatment Approval Required: {treatment.title}",
            body=f"A new risk treatment plan requires your approval.\n\nTitle: {treatment.title}\nStrategy: {treatment.strategy.value}\nSubmitted by: {current_user.full_name}",
            html_body=f"""
            <h3>Risk Treatment Approval Required</h3>
            <p>A new risk treatment plan has been submitted for approval.</p>
            <ul>
                <li><strong>Title:</strong> {treatment.title}</li>
                <li><strong>Strategy:</strong> {treatment.strategy.value}</li>
                <li><strong>Submitted by:</strong> {current_user.full_name}</li>
                <li><strong>Target Date:</strong> {treatment.target_date.strftime('%Y-%m-%d')}</li>
            </ul>
            <p>Please log in to the ERM system to review and approve.</p>
            """
        )
    
    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="UPDATE",
        entity_type="treatment",
        entity_id=str(treatment.id),
        entity_name=treatment.title,
        old_values={"status": "draft"},
        new_values={"status": "pending_approval"},
        description="Submitted treatment for approval",
        ip_address=request.client.host
    )
    
    return {"message": "Treatment submitted for approval"}

@router.post("/{treatment_id}/approve")
async def approve_treatment(
    treatment_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Approve treatment plan"""
    if current_user.role not in ["admin", "risk_manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to approve")
    
    treatment = db.query(RiskTreatment).filter(RiskTreatment.id == treatment_id).first()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    if treatment.status != WorkflowStatus.pending_approval:
        raise HTTPException(status_code=400, detail="Treatment not pending approval")
    
    treatment.status = WorkflowStatus.approved
    treatment.approved_by_id = current_user.id
    treatment.approved_at = datetime.now(timezone.utc)
    db.commit()
    
    # Notify creator
    creator = db.query(User).filter(User.id == treatment.created_by_id).first()
    if creator:
        await email_service.send_email(
            to_emails=[creator.email],
            subject=f"Treatment Plan Approved: {treatment.title}",
            body=f"Your risk treatment plan has been approved by {current_user.full_name}.",
            html_body=f"""
            <h3>Treatment Plan Approved</h3>
            <p>Your risk treatment plan "<strong>{treatment.title}</strong>" has been approved.</p>
            <p>Approved by: {current_user.full_name}</p>
            <p>You can now proceed with implementation.</p>
            """
        )
    
    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="APPROVE",
        entity_type="treatment",
        entity_id=str(treatment.id),
        entity_name=treatment.title,
        description=f"Approved treatment plan",
        ip_address=request.client.host
    )
    
    return {"message": "Treatment approved successfully"}
