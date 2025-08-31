from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
import enum

from app.api.deps import get_db, get_current_active_user
from app.models.kri import KeyRiskIndicator, KRIStatus, KRIMeasurement
from app.models.user import User
from app.models.risk import Risk
from app.schemas.base import PaginatedResponse

# Enums
class KRICategory(str, enum.Enum):
    operational = "operational"
    financial = "financial"
    compliance = "compliance"
    strategic = "strategic"
    cyber = "cyber"

# Schemas
class KRICreate(BaseModel):
    risk_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    metric_type: str  # percentage, count, ratio, etc.
    lower_threshold: Optional[float] = None
    upper_threshold: Optional[float] = None
    target_value: Optional[float] = None
    current_value: float
    measurement_frequency: Optional[str] = None
    data_source: Optional[str] = None
    responsible_party: Optional[str] = None

class KRIUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    lower_threshold: Optional[float] = None
    upper_threshold: Optional[float] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    measurement_frequency: Optional[str] = None
    data_source: Optional[str] = None
    responsible_party: Optional[str] = None

class KRIResponse(BaseModel):
    id: UUID
    risk_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    metric_type: Optional[str] = None
    lower_threshold: Optional[float] = None
    upper_threshold: Optional[float] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    status: Optional[KRIStatus] = None
    trend: Optional[str] = None
    measurement_frequency: Optional[str] = None
    data_source: Optional[str] = None
    responsible_party: Optional[str] = None
    last_updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class KRIMeasurementCreate(BaseModel):
    value: float
    notes: Optional[str] = None

class KRIMeasurementResponse(BaseModel):
    id: UUID
    kri_id: UUID
    value: float
    status: Optional[KRIStatus] = None
    measured_at: datetime
    recorded_by_id: Optional[UUID] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True

router = APIRouter()

def calculate_kri_status(value: float, lower_threshold: float = None, 
                        upper_threshold: float = None, target_value: float = None) -> KRIStatus:
    """Calculate KRI status based on value and thresholds"""
    if lower_threshold is not None and upper_threshold is not None:
        if lower_threshold <= value <= upper_threshold:
            return KRIStatus.normal
        elif value < lower_threshold * 0.8 or value > upper_threshold * 1.2:
            return KRIStatus.critical
        else:
            return KRIStatus.warning
    elif target_value is not None:
        deviation = abs(value - target_value) / target_value
        if deviation <= 0.1:  # Within 10% of target
            return KRIStatus.normal
        elif deviation <= 0.25:  # Within 25% of target
            return KRIStatus.warning
        else:
            return KRIStatus.critical
    else:
        return KRIStatus.normal

def calculate_trend(current_value: float, previous_values: List[float]) -> str:
    """Calculate trend based on recent values"""
    if not previous_values:
        return "stable"
    
    avg_previous = sum(previous_values) / len(previous_values)
    change_percent = ((current_value - avg_previous) / avg_previous) * 100 if avg_previous != 0 else 0
    
    if change_percent > 5:
        return "increasing"
    elif change_percent < -5:
        return "decreasing"
    else:
        return "stable"

@router.get("/", response_model=PaginatedResponse)
def get_kris(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    risk_id: Optional[UUID] = None,
    status: Optional[KRIStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get all KRIs with pagination"""
    query = db.query(KeyRiskIndicator)
    
    # Apply filters
    if risk_id:
        query = query.filter(KeyRiskIndicator.risk_id == risk_id)
    if status:
        query = query.filter(KeyRiskIndicator.status == status)
    if search:
        query = query.filter(KeyRiskIndicator.name.ilike(f"%{search}%"))
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    kris = query.order_by(desc(KeyRiskIndicator.last_updated)).offset(skip).limit(limit).all()
    
    # Convert to response format
    kri_responses = []
    for kri in kris:
        kri_dict = KRIResponse.model_validate(kri).model_dump()
        # Add risk title if available
        if hasattr(kri, 'risk') and kri.risk:
            kri_dict["risk_title"] = kri.risk.title
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
    """Create new KRI"""
    # Validate risk exists if provided
    if kri_in.risk_id:
        risk = db.query(Risk).filter(Risk.id == kri_in.risk_id).first()
        if not risk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Risk not found"
            )
    
    # Calculate initial status
    status = calculate_kri_status(
        kri_in.current_value,
        kri_in.lower_threshold,
        kri_in.upper_threshold,
        kri_in.target_value
    )
    
    # Create KRI
    kri = KeyRiskIndicator(
        **kri_in.model_dump(),
        status=status,
        trend="stable",
        last_updated=datetime.utcnow()
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
    """Get KRI by ID with detailed information"""
    kri = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.id == kri_id).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    # Get recent measurements
    measurements = db.query(KRIMeasurement)\
        .filter(KRIMeasurement.kri_id == kri_id)\
        .order_by(desc(KRIMeasurement.measured_at))\
        .limit(30)\
        .all()
    
    # Calculate statistics
    breach_count = len([m for m in measurements if m.status in [KRIStatus.warning, KRIStatus.critical]])
    values = [m.value for m in measurements]
    avg_value = sum(values) / len(values) if values else kri.current_value
    
    # Prepare response
    kri_data = KRIResponse.model_validate(kri).model_dump()
    
    # Add additional information
    kri_data.update({
        "risk_title": kri.risk.title if hasattr(kri, 'risk') and kri.risk else None,
        "measurement_count": len(measurements),
        "breach_count": breach_count,
        "average_value": avg_value,
        "recent_measurements": [
            {
                "value": m.value,
                "status": m.status.value if m.status else None,
                "measured_at": m.measured_at.isoformat()
            } for m in measurements[:10]
        ]
    })
    
    return kri_data

@router.put("/{kri_id}", response_model=KRIResponse)
def update_kri(
    kri_id: UUID,
    kri_update: KRIUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update KRI"""
    kri = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.id == kri_id).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    # Update fields
    update_data = kri_update.model_dump(exclude_unset=True)
    
    # Recalculate status if value or thresholds changed
    if any(field in update_data for field in ['current_value', 'lower_threshold', 'upper_threshold', 'target_value']):
        current_value = update_data.get('current_value', kri.current_value)
        lower_threshold = update_data.get('lower_threshold', kri.lower_threshold)
        upper_threshold = update_data.get('upper_threshold', kri.upper_threshold)
        target_value = update_data.get('target_value', kri.target_value)
        
        status = calculate_kri_status(current_value, lower_threshold, upper_threshold, target_value)
        update_data['status'] = status
    
    # Update trend if value changed
    if 'current_value' in update_data:
        # Get last 5 measurements
        recent_measurements = db.query(KRIMeasurement.value)\
            .filter(KRIMeasurement.kri_id == kri_id)\
            .order_by(desc(KRIMeasurement.measured_at))\
            .limit(5)\
            .all()
        
        if recent_measurements:
            previous_values = [m[0] for m in recent_measurements]
            update_data['trend'] = calculate_trend(update_data['current_value'], previous_values)
    
    update_data['last_updated'] = datetime.utcnow()
    
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
    """Delete KRI"""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete KRIs"
        )
    
    kri = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.id == kri_id).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    db.delete(kri)
    db.commit()
    
    return {"message": "KRI deleted successfully"}

@router.post("/{kri_id}/measurements", response_model=KRIMeasurementResponse)
def record_measurement(
    kri_id: UUID,
    measurement_in: KRIMeasurementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record a new KRI measurement"""
    kri = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.id == kri_id).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    # Calculate status for this measurement
    status = calculate_kri_status(
        measurement_in.value,
        kri.lower_threshold,
        kri.upper_threshold,
        kri.target_value
    )
    
    # Create measurement
    measurement = KRIMeasurement(
        kri_id=kri_id,
        value=measurement_in.value,
        status=status,
        measured_at=datetime.utcnow(),
        recorded_by_id=current_user.id,
        notes=measurement_in.notes
    )
    
    # Update KRI current value and status
    kri.current_value = measurement_in.value
    kri.status = status
    kri.last_updated = datetime.utcnow()
    
    # Update trend
    recent_measurements = db.query(KRIMeasurement.value)\
        .filter(KRIMeasurement.kri_id == kri_id)\
        .order_by(desc(KRIMeasurement.measured_at))\
        .limit(5)\
        .all()
    
    if recent_measurements:
        previous_values = [m[0] for m in recent_measurements]
        kri.trend = calculate_trend(measurement_in.value, previous_values)
    
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    
    return KRIMeasurementResponse.model_validate(measurement)

@router.get("/{kri_id}/measurements", response_model=List[KRIMeasurementResponse])
def get_measurements(
    kri_id: UUID,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
):
    """Get KRI measurements history"""
    kri = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.id == kri_id).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    measurements = db.query(KRIMeasurement)\
        .filter(KRIMeasurement.kri_id == kri_id)\
        .order_by(desc(KRIMeasurement.measured_at))\
        .limit(limit)\
        .all()
    
    return [KRIMeasurementResponse.model_validate(m) for m in measurements]

@router.get("/dashboard/summary", response_model=Dict[str, Any])
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get KRI dashboard summary"""
    # Total KRIs
    total_kris = db.query(KeyRiskIndicator).count()
    
    # KRIs by status
    kris_by_status = db.query(
        KeyRiskIndicator.status,
        func.count(KeyRiskIndicator.id)
    ).group_by(KeyRiskIndicator.status).all()
    
    # Breached KRIs
    breached_kris = db.query(KeyRiskIndicator).filter(
        KeyRiskIndicator.status.in_([KRIStatus.warning, KRIStatus.critical])
    ).count()
    
    # Critical KRIs
    critical_kris = db.query(KeyRiskIndicator).filter(
        KeyRiskIndicator.status == KRIStatus.critical
    ).count()
    
    # Compliance rate
    compliance_rate = ((total_kris - breached_kris) / total_kris * 100) if total_kris > 0 else 0
    
    # Recent critical KRIs
    critical_kri_list = db.query(KeyRiskIndicator)\
        .filter(KeyRiskIndicator.status == KRIStatus.critical)\
        .order_by(desc(KeyRiskIndicator.last_updated))\
        .limit(5)\
        .all()
    
    return {
        "summary": {
            "total_kris": total_kris,
            "breached_kris": breached_kris,
            "critical_kris": critical_kris,
            "compliance_rate": round(compliance_rate, 2)
        },
        "by_status": {
            status.value if status else "unknown": count 
            for status, count in kris_by_status
        },
        "critical_kris": [
            {
                "id": str(kri.id),
                "name": kri.name,
                "current_value": kri.current_value,
                "risk_id": str(kri.risk_id) if kri.risk_id else None
            } for kri in critical_kri_list
        ]
    }