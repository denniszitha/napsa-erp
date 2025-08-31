from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.control import Control, ControlType, ControlStatus
from app.schemas.control import ControlCreate, ControlUpdate, ControlResponse
from app.models.risk import Risk
from app.models.control import RiskControl
from typing import Dict, Any, List
from app.models.control import Control, ControlType, ControlStatus, RiskControl
from app.services.risk_calculation import RiskCalculationService

router = APIRouter()

@router.get("/", response_model=List[ControlResponse])
def get_controls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_user)  # Temporarily disabled for testing
) -> List[Control]:
    """Get list of controls"""
    controls = db.query(Control).offset(skip).limit(limit).all()
    return controls

@router.post("/", response_model=ControlResponse, status_code=status.HTTP_201_CREATED)
def create_control(
    control: ControlCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Control:
    """Create a new control"""
    db_control = Control(
        **control.model_dump()
    )
    db.add(db_control)
    db.commit()
    db.refresh(db_control)
    return db_control

@router.post("/map-to-risk", response_model=Dict[str, Any])
def map_control_to_risk(
    mapping: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Map a control to a risk"""
    control_id = mapping.get("control_id")
    risk_id = mapping.get("risk_id")
    
    # Validate control exists
    control = db.query(Control).filter(Control.id == control_id).first()
    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control not found"
        )
    
    # Validate risk exists
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk not found"
        )
    
    # Check if mapping already exists
    existing = db.query(RiskControl).filter(
        RiskControl.risk_id == risk_id,
        RiskControl.control_id == control_id
    ).first()
    
    if existing:
        return {
            "message": "Control already mapped to this risk",
            "risk_id": str(risk_id),
            "control_id": str(control_id)
        }
    
    # Create the mapping with coverage percentage
    risk_control = RiskControl(
        risk_id=risk_id,
        control_id=control_id,
        coverage_percentage=mapping.get("coverage_percentage", 100.0),
        criticality=mapping.get("criticality", "High")
    )
    db.add(risk_control)
    db.commit()
    
    # Recalculate risk scores after mapping
    risk_update = RiskCalculationService.update_risk_scores(db, risk_id)
    
    return {
        "message": "Control successfully mapped to risk and risk scores updated",
        "risk_id": str(risk_id),
        "control_id": str(control_id),
        "risk_title": risk.title,
        "control_name": control.name,
        "risk_update": risk_update
    }

@router.get("/risk/{risk_id}", response_model=List[ControlResponse])
def get_controls_for_risk(
    risk_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Control]:
    """Get all controls mapped to a specific risk"""
    # Get control IDs mapped to this risk
    risk_controls = db.query(RiskControl).filter(RiskControl.risk_id == risk_id).all()
    control_ids = [rc.control_id for rc in risk_controls]
    
    # Get the actual control objects
    if control_ids:
        controls = db.query(Control).filter(Control.id.in_(control_ids)).all()
        return controls
    return []

@router.delete("/unmap-from-risk", response_model=Dict[str, Any])
def unmap_control_from_risk(
    mapping: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Remove a control-risk mapping"""
    control_id = mapping.get("control_id")
    risk_id = mapping.get("risk_id")
    
    # Find and delete the mapping
    risk_control = db.query(RiskControl).filter(
        RiskControl.risk_id == risk_id,
        RiskControl.control_id == control_id
    ).first()
    
    if not risk_control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )
    
    db.delete(risk_control)
    db.commit()
    
    # Recalculate risk scores after unmapping
    risk_update = RiskCalculationService.update_risk_scores(db, risk_id)
    
    return {
        "message": "Control unmapped from risk successfully and risk scores updated",
        "risk_id": str(risk_id),
        "control_id": str(control_id),
        "risk_update": risk_update
    }

@router.get("/effectiveness", response_model=Dict[str, Any])
def get_control_effectiveness_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get overall control effectiveness summary"""
    controls = db.query(Control).all()
    
    if not controls:
        return {
            "average_effectiveness": 0,
            "total_controls": 0,
            "by_type": {},
            "by_status": {}
        }
    
    # Calculate average effectiveness
    controls_with_effectiveness = [c for c in controls if c.effectiveness_rating is not None]
    if controls_with_effectiveness:
        total_effectiveness = sum(c.effectiveness_rating for c in controls_with_effectiveness)
        avg_effectiveness = total_effectiveness / len(controls_with_effectiveness)
    else:
        avg_effectiveness = 0
    
    # Group by type
    by_type = {}
    for control_type in ControlType:
        type_controls = [c for c in controls if c.type == control_type]
        if type_controls:
            type_controls_with_eff = [c for c in type_controls if c.effectiveness_rating is not None]
            if type_controls_with_eff:
                type_effectiveness = sum(c.effectiveness_rating for c in type_controls_with_eff)
                avg_type_effectiveness = type_effectiveness / len(type_controls_with_eff)
            else:
                avg_type_effectiveness = 0
            
            by_type[control_type.value] = {
                "count": len(type_controls),
                "average_effectiveness": round(avg_type_effectiveness, 2)
            }
    
    # Group by status
    by_status = {}
    for status in ControlStatus:
        status_controls = [c for c in controls if c.status == status]
        if status_controls:
            by_status[status.value] = {
                "count": len(status_controls),
                "percentage": round((len(status_controls) / len(controls)) * 100, 2)
            }
    
    return {
        "average_effectiveness": round(avg_effectiveness, 2),
        "total_controls": len(controls),
        "by_type": by_type,
        "by_status": by_status,
        "highly_effective": len([c for c in controls if c.effectiveness_rating and c.effectiveness_rating >= 80]),
        "needs_improvement": len([c for c in controls if c.effectiveness_rating and c.effectiveness_rating < 60])
    }

@router.get("/risk/{risk_id}/effectiveness", response_model=Dict[str, Any])
def get_risk_control_effectiveness(
    risk_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get aggregate control effectiveness for a specific risk"""
    effectiveness_data = RiskCalculationService.calculate_aggregate_control_effectiveness(db, risk_id)
    
    # Get current risk scores
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk not found"
        )
    
    return {
        "risk_id": risk_id,
        "risk_title": risk.title,
        "inherent_risk": risk.inherent_risk_score,
        "residual_risk": risk.residual_risk_score,
        **effectiveness_data
    }

@router.post("/risk/{risk_id}/recalculate", response_model=Dict[str, Any])
def recalculate_risk_scores(
    risk_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Manually trigger recalculation of risk scores based on current controls"""
    result = RiskCalculationService.update_risk_scores(db, risk_id)
    return result

@router.post("/recalculate-all", response_model=List[Dict[str, Any]])
def recalculate_all_risk_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Recalculate risk scores for all risks with controls"""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can trigger batch recalculation"
        )
    
    results = RiskCalculationService.recalculate_all_risks(db)
    return results

@router.get("/control/{control_id}/contribution/{risk_id}", response_model=Dict[str, Any])
def get_control_contribution(
    control_id: str,
    risk_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get how much a specific control contributes to risk reduction"""
    contribution = RiskCalculationService.get_control_contribution(db, risk_id, control_id)
    return contribution
