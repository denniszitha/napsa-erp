from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.api.deps import get_db, get_current_active_user
from app.models.workflow import RiskTreatment, TreatmentStrategy, WorkflowStatus, TreatmentAction
from app.models.risk import Risk
from app.models.user import User
from app.schemas.base import PaginatedResponse

# Schemas
class TreatmentCreate(BaseModel):
    risk_id: str  # Changed from UUID to str to match RISK-XXXX format
    strategy: TreatmentStrategy
    title: str
    description: Optional[str] = None
    action_plan: Optional[str] = None
    responsible_party: Optional[str] = None
    target_date: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    expected_risk_reduction: Optional[float] = None

class TreatmentUpdate(BaseModel):
    strategy: Optional[TreatmentStrategy] = None
    title: Optional[str] = None
    description: Optional[str] = None
    action_plan: Optional[str] = None
    responsible_party: Optional[str] = None
    target_date: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    expected_risk_reduction: Optional[float] = None
    status: Optional[WorkflowStatus] = None

class TreatmentResponse(BaseModel):
    id: UUID
    risk_id: Optional[str] = None  # Made optional to handle existing NULL values
    strategy: TreatmentStrategy
    title: str
    description: Optional[str] = None
    action_plan: Optional[str] = None
    responsible_party: Optional[str] = None
    target_date: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    expected_risk_reduction: Optional[float] = None
    status: WorkflowStatus
    created_at: datetime
    created_by_id: Optional[UUID] = None
    risk_title: Optional[str] = None
    
    class Config:
        from_attributes = True

router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
def get_treatments(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    risk_id: Optional[UUID] = None,
    status: Optional[WorkflowStatus] = None,
    # current_user: User = Depends(get_current_active_user),  # Temporarily disabled for testing
):
    """Get risk treatments with pagination"""
    query = db.query(RiskTreatment)
    
    # Apply filters
    if risk_id:
        query = query.filter(RiskTreatment.risk_id == risk_id)
    if status:
        query = query.filter(RiskTreatment.status == status)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    treatments = query.order_by(desc(RiskTreatment.created_at)).offset(skip).limit(limit).all()
    
    # Convert to response format
    treatment_responses = []
    for treatment in treatments:
        treatment_dict = TreatmentResponse.model_validate(treatment).model_dump()
        # Add risk title if available
        if hasattr(treatment, 'risk') and treatment.risk:
            treatment_dict["risk_title"] = treatment.risk.title
        treatment_responses.append(treatment_dict)
    
    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        data=treatment_responses
    )

@router.post("/", response_model=TreatmentResponse, status_code=status.HTTP_201_CREATED)
def create_treatment(
    treatment_in: TreatmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create new risk treatment"""
    # Verify risk exists
    risk = db.query(Risk).filter(Risk.id == treatment_in.risk_id).first()
    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk not found"
        )
    
    # Create treatment
    treatment = RiskTreatment(
        **treatment_in.model_dump(),
        created_by_id=current_user.id,
        status=WorkflowStatus.draft,
        created_at=datetime.utcnow()
    )
    
    db.add(treatment)
    db.commit()
    db.refresh(treatment)
    
    # Prepare response
    response = TreatmentResponse.model_validate(treatment)
    response_dict = response.model_dump()
    response_dict["risk_title"] = risk.title
    
    return response_dict

@router.get("/{treatment_id}", response_model=Dict[str, Any])
def get_treatment(
    treatment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get treatment by ID"""
    treatment = db.query(RiskTreatment).filter(RiskTreatment.id == treatment_id).first()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    # Get action items count
    action_items_count = db.query(TreatmentAction).filter(
        TreatmentAction.treatment_id == treatment_id
    ).count()
    
    # Prepare response
    treatment_data = TreatmentResponse.model_validate(treatment).model_dump()
    
    # Add additional information
    treatment_data.update({
        "risk_title": treatment.risk.title if hasattr(treatment, 'risk') and treatment.risk else None,
        "created_by_name": treatment.created_by.full_name if hasattr(treatment, 'created_by') and treatment.created_by else None,
        "approved_by_name": treatment.approved_by.full_name if hasattr(treatment, 'approved_by') and treatment.approved_by else None,
        "action_items_count": action_items_count
    })
    
    return treatment_data

@router.put("/{treatment_id}", response_model=TreatmentResponse)
def update_treatment(
    treatment_id: UUID,
    treatment_update: TreatmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update treatment"""
    treatment = db.query(RiskTreatment).filter(RiskTreatment.id == treatment_id).first()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    # Update fields
    update_data = treatment_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(treatment, field, value)
    
    db.commit()
    db.refresh(treatment)
    
    return TreatmentResponse.model_validate(treatment)

@router.delete("/{treatment_id}")
def delete_treatment(
    treatment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete treatment"""
    # Check if user is admin or creator
    treatment = db.query(RiskTreatment).filter(RiskTreatment.id == treatment_id).first()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    if current_user.role != "admin" and treatment.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this treatment"
        )
    
    db.delete(treatment)
    db.commit()
    
    return {"message": "Treatment deleted successfully"}

@router.post("/{treatment_id}/submit-for-approval")
def submit_for_approval(
    treatment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Submit treatment for approval"""
    treatment = db.query(RiskTreatment).filter(RiskTreatment.id == treatment_id).first()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    if treatment.status != WorkflowStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft treatments can be submitted for approval"
        )
    
    treatment.status = WorkflowStatus.pending_approval
    db.commit()
    
    return {"message": "Treatment submitted for approval"}

@router.post("/{treatment_id}/approve")
def approve_treatment(
    treatment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Approve treatment"""
    # Check if user has approval rights
    if current_user.role not in ["admin", "risk_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to approve treatments"
        )
    
    treatment = db.query(RiskTreatment).filter(RiskTreatment.id == treatment_id).first()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    if treatment.status != WorkflowStatus.pending_approval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending treatments can be approved"
        )
    
    treatment.status = WorkflowStatus.approved
    treatment.approved_by_id = current_user.id
    treatment.approved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Treatment approved successfully"}

@router.post("/{treatment_id}/reject")
def reject_treatment(
    treatment_id: UUID,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Reject treatment"""
    # Check if user has approval rights
    if current_user.role not in ["admin", "risk_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reject treatments"
        )
    
    treatment = db.query(RiskTreatment).filter(RiskTreatment.id == treatment_id).first()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    if treatment.status != WorkflowStatus.pending_approval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending treatments can be rejected"
        )
    
    treatment.status = WorkflowStatus.rejected
    db.commit()
    
    return {"message": "Treatment rejected"}