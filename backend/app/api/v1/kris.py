from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone

from app.api.deps import get_db, get_current_active_user
from app.models.kri import KeyRiskIndicator, KRIMeasurement, KRIStatus
from app.models.risk import Risk
from app.models.user import User
from app.schemas.kri import KRICreate, KRIUpdate, KRIResponse, KRIMeasurementCreate, KRIMeasurementResponse
from app.schemas.base import PaginatedResponse
from app.services.email import email_service
from app.services.audit import audit_service
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from app.models.kri import KeyRiskIndicator, KRIStatus, KRIMeasurement

router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
def read_kris(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    risk_id: Optional[UUID] = None,
    status: Optional[KRIStatus] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve KRIs with pagination and filtering"""
    query = db.query(KeyRiskIndicator)
    
    if risk_id:
        query = query.filter(KeyRiskIndicator.risk_id == risk_id)
    if status:
        query = query.filter(KeyRiskIndicator.status == status)
    
    total = query.count()
    kris = query.offset(skip).limit(limit).all()
    
    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        data=[KRIResponse.model_validate(k) for k in kris]
    )

@router.post("/", response_model=KRIResponse)
def create_kri(
    kri_in: KRICreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create new KRI"""
    kri = KeyRiskIndicator(**kri_in.model_dump())
    db.add(kri)
    db.commit()
    db.refresh(kri)
    
    return KRIResponse.model_validate(kri)

@router.post("/measurements", response_model=KRIMeasurementResponse)
async def add_measurement(
    measurement_in: KRIMeasurementCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add KRI measurement with breach notifications"""
    # Get KRI
    kri = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.id == measurement_in.kri_id).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    # Store previous status for comparison
    previous_status = kri.status
    
    # Determine new status based on thresholds
    value = measurement_in.value
    if value <= kri.lower_threshold or value >= kri.upper_threshold:
        status = KRIStatus.critical
    elif abs(value - kri.target_value) > (kri.upper_threshold - kri.target_value) * 0.7:
        status = KRIStatus.warning
    else:
        status = KRIStatus.normal
    
    # Create measurement
    measurement = KRIMeasurement(
        **measurement_in.model_dump(),
        status=status,
        measurement_date=datetime.now(timezone.utc)
    )
    db.add(measurement)
    
    # Update KRI current value and status
    kri.current_value = value
    kri.status = status
    kri.last_updated = datetime.now(timezone.utc)
    
    # Send notification if status changed to warning or critical
    if status != previous_status and status in [KRIStatus.warning, KRIStatus.critical]:
        # Get risk details
        risk = db.query(Risk).filter(Risk.id == kri.risk_id).first()
        
        # Get responsible parties
        recipients = []
        if kri.responsible_party:
            user = db.query(User).filter(User.full_name == kri.responsible_party).first()
            if user:
                recipients.append(user.email)
        
        # Add risk owner
        if risk and risk.owner:
            recipients.append(risk.owner.email)
        
        # Add risk managers
        risk_managers = db.query(User).filter(User.role == "risk_manager").all()
        recipients.extend([rm.email for rm in risk_managers])
        
        # Remove duplicates
        recipients = list(set(recipients))
        
        if recipients:
            await email_service.send_kri_breach_notification(
                kri_name=kri.name,
                current_value=value,
                threshold=kri.upper_threshold if value >= kri.upper_threshold else kri.lower_threshold,
                status=status.value,
                risk_title=risk.title if risk else "Unknown",
                recipients=recipients
            )
    
    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="CREATE",
        entity_type="kri_measurement",
        entity_id=str(measurement.id),
        entity_name=f"Measurement for {kri.name}",
        new_values={"value": value, "status": status.value},
        description=f"Added KRI measurement: {value} ({status.value})",
        ip_address=request.client.host
    )
    
    db.commit()
    db.refresh(measurement)
    
    return KRIMeasurementResponse.model_validate(measurement)

@router.get("/dashboard-summary")
def get_kri_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get KRI dashboard summary"""
    total_kris = db.query(KeyRiskIndicator).count()
    normal = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.status == KRIStatus.normal).count()
    warning = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.status == KRIStatus.warning).count()
    critical = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.status == KRIStatus.critical).count()
    
    return {
        "total_kris": total_kris,
        "by_status": {
            "normal": normal,
            "warning": warning,
            "critical": critical
        },
        "health_percentage": round((normal / total_kris * 100) if total_kris > 0 else 0, 1)
    }

@router.get("/breached", response_model=List[Dict[str, Any]])
def get_breached_kris(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Get all KRIs that have breached their thresholds"""
    kris = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.status == KRIStatus.breached).all()
    
    breached_kris = []
    for kri in kris:
        # Get latest measurement
        latest_measurement = db.query(KRIMeasurement)\
            .filter(KRIMeasurement.kri_id == kri.id)\
            .order_by(KRIMeasurement.measurement_date.desc())\
            .first()
        
        breached_kris.append({
            "id": str(kri.id),
            "name": kri.name,
            "current_value": kri.current_value,
            "threshold_upper": kri.threshold_upper,
            "threshold_lower": kri.threshold_lower,
            "breach_type": "upper" if kri.current_value > kri.threshold_upper else "lower",
            "breach_severity": "critical" if abs(kri.current_value - (kri.threshold_upper if kri.current_value > kri.threshold_upper else kri.threshold_lower)) > 20 else "warning",
            "days_in_breach": (datetime.now(timezone.utc) - kri.last_updated).days if kri.last_updated else 0,
            "risk_id": str(kri.risk_id),
            "owner": kri.owner.full_name if kri.owner else None,
            "latest_measurement": {
                "value": latest_measurement.value,
                "date": latest_measurement.measurement_date.isoformat(),
                "notes": latest_measurement.notes
            } if latest_measurement else None
        })
    
    return breached_kris

@router.get("/dashboard", response_model=Dict[str, Any])
def get_kri_dashboard_detailed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get detailed KRI dashboard with trends and analysis"""
    kris = db.query(KeyRiskIndicator).all()
    
    # Calculate KRI statistics
    total_kris = len(kris)
    active_kris = len([k for k in kris if k.status == KRIStatus.active])
    breached_kris = len([k for k in kris if k.status == KRIStatus.breached])
    warning_kris = len([k for k in kris if k.status == KRIStatus.warning])
    
    # Get recent measurements for trend analysis
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_measurements = db.query(KRIMeasurement)\
        .filter(KRIMeasurement.measurement_date >= thirty_days_ago)\
        .all()
    
    # Group by frequency
    by_frequency = {}
    for kri in kris:
        freq = kri.frequency
        if freq not in by_frequency:
            by_frequency[freq] = {"count": 0, "breached": 0}
        by_frequency[freq]["count"] += 1
        if kri.status == KRIStatus.breached:
            by_frequency[freq]["breached"] += 1
    
    return {
        "summary": {
            "total": total_kris,
            "active": active_kris,
            "breached": breached_kris,
            "warning": warning_kris,
            "inactive": total_kris - active_kris
        },
        "by_frequency": by_frequency,
        "recent_measurements": len(recent_measurements),
        "health_score": round((active_kris - breached_kris) / total_kris * 100, 2) if total_kris > 0 else 0,
        "trends": {
            "improving": len([k for k in kris if k.trend == "improving"]) if hasattr(kris[0], 'trend') else 0,
            "stable": len([k for k in kris if k.trend == "stable"]) if hasattr(kris[0], 'trend') else 0,
            "deteriorating": len([k for k in kris if k.trend == "deteriorating"]) if hasattr(kris[0], 'trend') else 0
        }
    }
