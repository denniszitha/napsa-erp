from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from uuid import UUID
from datetime import datetime

from app.api.deps import get_db, get_current_active_user
from app.models.kri import KeyRiskIndicator as KRI, KRIStatus, KRIMeasurement as KRIValue
from app.models.user import User
from app.models.risk import Risk
# Use simple schemas for now
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class KRICategory(str):
    operational = "operational"
    financial = "financial"
    compliance = "compliance"
    strategic = "strategic"

class KRICreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    metric_type: Optional[str] = None
    current_value: float
    threshold_green: float
    threshold_amber: float
    threshold_red: float
    is_lower_better: bool = False
    frequency: Optional[str] = None
    unit: Optional[str] = None
    risk_id: Optional[UUID] = None

class KRIUpdate(BaseModel):
    current_value: Optional[float] = None
    notes: Optional[str] = None

class KRIResponse(BaseModel):
    id: UUID
    name: str
    status: Optional[str] = None
    current_value: Optional[float] = None
    
    class Config:
        from_attributes = True

class KRIValueCreate(BaseModel):
    value: float
    measured_at: Optional[datetime] = None
    notes: Optional[str] = None

class KRIValueResponse(BaseModel):
    id: UUID
    value: float
    measured_at: datetime
    
    class Config:
        from_attributes = True
from app.schemas.base import PaginatedResponse

router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
def get_kris(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[KRICategory] = None,
    status: Optional[KRIStatus] = None,
    risk_id: Optional[UUID] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all KRIs with pagination and filtering
    """
    query = db.query(KRI)
    
    # Apply filters
    if category:
        query = query.filter(KRI.category == category)
    if status:
        query = query.filter(KRI.status == status)
    if risk_id:
        query = query.filter(KRI.risk_id == risk_id)
    if search:
        query = query.filter(KRI.name.ilike(f"%{search}%"))
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    kris = query.offset(skip).limit(limit).all()
    
    # Convert to response format
    kri_responses = []
    for kri in kris:
        kri_dict = KRIResponse.model_validate(kri).model_dump()
        # Add related info
        if hasattr(kri, 'risk') and kri.risk:
            kri_dict["risk_title"] = kri.risk.title
        if hasattr(kri, 'owner') and kri.owner:
            kri_dict["owner_name"] = kri.owner.full_name
        kri_responses.append(kri_dict)
    
    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        data=kri_responses
    )

@router.post("/", response_model=KRIResponse, status_code=status.HTTP_201_CREATED)
def create_kri(
    kri_in: KRICreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create new KRI
    """
    # Check if user has permission
    if current_user.role not in ["admin", "risk_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create KRIs"
        )
    
    # Validate risk exists if provided
    if kri_in.risk_id:
        risk = db.query(Risk).filter(Risk.id == kri_in.risk_id).first()
        if not risk:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Risk not found"
            )
    
    # Create KRI
    kri = KRI(**kri_in.model_dump())
    kri.created_at = datetime.utcnow()
    kri.updated_at = datetime.utcnow()
    
    # Calculate initial status based on current value
    kri.status = calculate_kri_status(
        kri.current_value,
        kri.threshold_green,
        kri.threshold_amber,
        kri.threshold_red,
        kri.is_lower_better
    )
    
    db.add(kri)
    db.commit()
    db.refresh(kri)
    
    return KRIResponse.model_validate(kri)

@router.get("/{kri_id}", response_model=Dict[str, Any])
def get_kri(
    kri_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get KRI by ID with detailed information
    """
    kri = db.query(KRI).filter(KRI.id == kri_id).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    # Get historical values (last 30)
    historical_values = db.query(KRIValue)\
        .filter(KRIValue.kri_id == kri_id)\
        .order_by(desc(KRIValue.measured_at))\
        .limit(30)\
        .all()
    
    # Prepare response
    kri_data = KRIResponse.model_validate(kri).model_dump()
    
    # Add additional information
    kri_data.update({
        "risk_title": kri.risk.title if hasattr(kri, 'risk') and kri.risk else None,
        "owner_name": kri.owner.full_name if hasattr(kri, 'owner') and kri.owner else None,
        "historical_values": [
            {
                "value": v.value,
                "measured_at": v.measured_at.isoformat(),
                "status": v.status.value if v.status else None
            } for v in historical_values
        ],
        "breach_count": len([v for v in historical_values if v.status in [KRIStatus.amber, KRIStatus.red]]),
        "average_value": sum(v.value for v in historical_values) / len(historical_values) if historical_values else 0
    })
    
    return kri_data

@router.put("/{kri_id}", response_model=KRIResponse)
def update_kri(
    kri_id: UUID,
    kri_update: KRIUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update KRI
    """
    # Check permissions
    if current_user.role not in ["admin", "risk_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update KRIs"
        )
    
    kri = db.query(KRI).filter(KRI.id == kri_id).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    # Update fields
    update_data = kri_update.model_dump(exclude_unset=True)
    update_data['updated_at'] = datetime.utcnow()
    
    # Recalculate status if thresholds or current value changed
    if any(field in update_data for field in ['current_value', 'threshold_green', 'threshold_amber', 'threshold_red', 'is_lower_better']):
        current_value = update_data.get('current_value', kri.current_value)
        threshold_green = update_data.get('threshold_green', kri.threshold_green)
        threshold_amber = update_data.get('threshold_amber', kri.threshold_amber)
        threshold_red = update_data.get('threshold_red', kri.threshold_red)
        is_lower_better = update_data.get('is_lower_better', kri.is_lower_better)
        
        update_data['status'] = calculate_kri_status(
            current_value,
            threshold_green,
            threshold_amber,
            threshold_red,
            is_lower_better
        )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(kri, field, value)
    
    db.commit()
    db.refresh(kri)
    
    return KRIResponse.model_validate(kri)

@router.delete("/{kri_id}")
def delete_kri(
    kri_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete KRI
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete KRIs"
        )
    
    kri = db.query(KRI).filter(KRI.id == kri_id).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    db.delete(kri)
    db.commit()
    
    return {"message": "KRI deleted successfully"}

@router.post("/{kri_id}/values", response_model=KRIValueResponse)
def record_kri_value(
    kri_id: UUID,
    value_in: KRIValueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Record a new KRI value measurement
    """
    kri = db.query(KRI).filter(KRI.id == kri_id).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    # Calculate status for this value
    status = calculate_kri_status(
        value_in.value,
        kri.threshold_green,
        kri.threshold_amber,
        kri.threshold_red,
        kri.is_lower_better
    )
    
    # Create KRI value record
    kri_value = KRIValue(
        kri_id=kri_id,
        value=value_in.value,
        measured_at=value_in.measured_at or datetime.utcnow(),
        status=status,
        recorded_by_id=current_user.id,
        notes=value_in.notes
    )
    
    # Update KRI current value and status
    kri.current_value = value_in.value
    kri.status = status
    kri.last_measured_at = kri_value.measured_at
    kri.updated_at = datetime.utcnow()
    
    db.add(kri_value)
    db.commit()
    db.refresh(kri_value)
    
    return KRIValueResponse.model_validate(kri_value)

@router.get("/{kri_id}/values", response_model=List[KRIValueResponse])
def get_kri_values(
    kri_id: UUID,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get historical values for a KRI
    """
    kri = db.query(KRI).filter(KRI.id == kri_id).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    values = db.query(KRIValue)\
        .filter(KRIValue.kri_id == kri_id)\
        .order_by(desc(KRIValue.measured_at))\
        .limit(limit)\
        .all()
    
    return [KRIValueResponse.model_validate(v) for v in values]

@router.get("/dashboard/summary", response_model=Dict[str, Any])
def get_kri_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get KRI dashboard summary statistics
    """
    # Total KRIs
    total_kris = db.query(KRI).count()
    
    # KRIs by status
    kris_by_status = db.query(
        KRI.status,
        func.count(KRI.id)
    ).group_by(KRI.status).all()
    
    # Breached KRIs (amber or red)
    breached_kris = db.query(KRI).filter(
        KRI.status.in_([KRIStatus.amber, KRIStatus.red])
    ).count()
    
    # Critical KRIs (red)
    critical_kris = db.query(KRI).filter(KRI.status == KRIStatus.red).count()
    
    # Compliance rate
    compliance_rate = ((total_kris - breached_kris) / total_kris * 100) if total_kris > 0 else 0
    
    # Recent measurements
    recent_measurements = db.query(KRIValue)\
        .order_by(desc(KRIValue.measured_at))\
        .limit(10)\
        .all()
    
    return {
        "summary": {
            "total_kris": total_kris,
            "breached_kris": breached_kris,
            "critical_kris": critical_kris,
            "compliance_rate": round(compliance_rate, 2)
        },
        "by_status": {status.value: count for status, count in kris_by_status},
        "recent_measurements": [
            {
                "kri_id": str(m.kri_id),
                "value": m.value,
                "status": m.status.value if m.status else None,
                "measured_at": m.measured_at.isoformat()
            } for m in recent_measurements
        ]
    }

# Utility functions
def calculate_kri_status(value: float, threshold_green: float, threshold_amber: float, 
                        threshold_red: float, is_lower_better: bool = False) -> KRIStatus:
    """Calculate KRI status based on value and thresholds"""
    if is_lower_better:
        # Lower values are better (e.g., error rates)
        if value <= threshold_green:
            return KRIStatus.green
        elif value <= threshold_amber:
            return KRIStatus.amber
        else:
            return KRIStatus.red
    else:
        # Higher values are better (e.g., uptime percentage)
        if value >= threshold_green:
            return KRIStatus.green
        elif value >= threshold_amber:
            return KRIStatus.amber
        else:
            return KRIStatus.red