"""
Risk Management API with Human-Readable IDs
This version uses ONLY human-readable IDs (e.g., RISK-2025-0001)
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, and_
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.risk import Risk, RiskStatus, RiskCategoryEnum
from app.models.assessment import RiskAssessment
from app.schemas.risk import RiskCreate, RiskUpdate, RiskResponse
from app.schemas.base import PaginatedResponse

router = APIRouter()

def format_risk_response(risk: Risk, db: Session) -> Dict[str, Any]:
    """Format risk response with human-readable IDs only"""
    # Build basic response
    response = {
        "id": risk.risk_code if risk.risk_code else str(risk.id),  # Use risk_code as ID
        "title": risk.title,
        "description": risk.description,
        "category": risk.category.value if risk.category else None,
        "status": risk.status.value if risk.status else None,
        "likelihood": risk.likelihood,
        "impact": risk.impact,
        "risk_source": risk.risk_source,
        "department": risk.department,
        "inherent_risk_score": risk.inherent_risk_score,
        "residual_risk_score": risk.residual_risk_score,
        "created_at": risk.created_at,
        "updated_at": risk.updated_at
    }
    
    # Add owner information
    if risk.risk_owner_id:
        owner = db.query(User).filter(User.id == risk.risk_owner_id).first()
        if owner:
            response["risk_owner_name"] = owner.full_name
            # Use user code if available, otherwise department/role
            response["risk_owner_id"] = f"USER-{owner.id.hex[:8]}" if owner else None
        else:
            response["risk_owner_name"] = None
            response["risk_owner_id"] = None
    else:
        response["risk_owner_name"] = None
        response["risk_owner_id"] = None
    
    return response

@router.get("/", response_model=Dict[str, Any])
def read_risks(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[RiskCategory] = None,
    status: Optional[RiskStatus] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = Query("created_at", pattern="^(created_at|title|inherent_risk_score|status)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
):
    """
    Retrieve risks with human-readable IDs only
    
    Returns risks with IDs in format: RISK-YYYY-NNNN
    """
    query = db.query(Risk)
    
    # Apply filters
    if category:
        query = query.filter(Risk.category == category)
    if status:
        query = query.filter(Risk.status == status)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Risk.title.ilike(search_filter),
                Risk.description.ilike(search_filter),
                Risk.risk_code.ilike(search_filter)  # Allow search by risk code
            )
        )
    
    # Apply sorting
    sort_column = getattr(Risk, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    risks = query.offset(skip).limit(limit).all()
    
    # Convert to human-readable format
    risk_responses = []
    for risk in risks:
        risk_responses.append(format_risk_response(risk, db))
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": risk_responses
    }

@router.get("/{risk_code}", response_model=Dict[str, Any])
def read_risk(
    risk_code: str,
    db: Session = Depends(get_db),
):
    """
    Get risk by human-readable code
    
    Example: /risks/RISK-2025-0001
    """
    # Find risk by code
    risk = db.query(Risk).filter(Risk.risk_code == risk_code).first()
    
    # If not found by code, try treating as UUID for backward compatibility
    if not risk and len(risk_code) == 36:
        try:
            risk_uuid = UUID(risk_code)
            risk = db.query(Risk).filter(Risk.id == risk_uuid).first()
        except ValueError:
            pass
    
    if not risk:
        raise HTTPException(status_code=404, detail=f"Risk {risk_code} not found")
    
    # Get detailed information
    response = format_risk_response(risk, db)
    
    # Add additional details
    latest_assessment = db.query(RiskAssessment)\
        .filter(RiskAssessment.risk_id == risk.id)\
        .order_by(desc(RiskAssessment.assessment_date))\
        .first()
    
    if latest_assessment:
        response["latest_assessment"] = {
            "id": latest_assessment.assessment_code if hasattr(latest_assessment, 'assessment_code') and latest_assessment.assessment_code else str(latest_assessment.id),
            "assessment_date": latest_assessment.assessment_date,
            "likelihood_score": latest_assessment.likelihood_score,
            "impact_score": latest_assessment.impact_score,
            "residual_risk": latest_assessment.residual_risk
        }
    else:
        response["latest_assessment"] = None
    
    return response

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_risk(
    risk_in: RiskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create new risk with auto-generated human-readable ID
    
    Returns risk with ID in format: RISK-YYYY-NNNN
    """
    # Generate next risk code
    year = datetime.now().year
    
    # Get the last risk code for this year
    last_risk = db.query(Risk).filter(
        Risk.risk_code.like(f'RISK-{year}-%')
    ).order_by(desc(Risk.risk_code)).first()
    
    if last_risk and last_risk.risk_code:
        # Extract number and increment
        last_num = int(last_risk.risk_code.split('-')[-1])
        new_num = last_num + 1
    else:
        # First risk of the year
        new_num = 1
    
    risk_code = f"RISK-{year}-{new_num:04d}"
    
    # Create risk object
    risk_dict = risk_in.dict()
    risk = Risk(**risk_dict)
    risk.risk_code = risk_code
    
    # Calculate inherent risk score
    if risk.likelihood and risk.impact:
        risk.inherent_risk_score = risk.likelihood * risk.impact
    
    db.add(risk)
    db.commit()
    db.refresh(risk)
    
    return format_risk_response(risk, db)

@router.put("/{risk_code}", response_model=Dict[str, Any])
def update_risk(
    risk_code: str,
    risk_in: RiskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update risk by human-readable code
    
    Example: PUT /risks/RISK-2025-0001
    """
    # Find risk by code
    risk = db.query(Risk).filter(Risk.risk_code == risk_code).first()
    
    # If not found by code, try UUID for backward compatibility
    if not risk and len(risk_code) == 36:
        try:
            risk_uuid = UUID(risk_code)
            risk = db.query(Risk).filter(Risk.id == risk_uuid).first()
        except ValueError:
            pass
    
    if not risk:
        raise HTTPException(status_code=404, detail=f"Risk {risk_code} not found")
    
    # Update risk fields
    update_data = risk_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(risk, field, value)
    
    # Recalculate inherent risk score
    if risk.likelihood and risk.impact:
        risk.inherent_risk_score = risk.likelihood * risk.impact
    
    risk.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(risk)
    
    return format_risk_response(risk, db)

@router.delete("/{risk_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_risk(
    risk_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete risk by human-readable code
    
    Example: DELETE /risks/RISK-2025-0001
    """
    # Check authorization
    if current_user.role not in ["admin", "risk_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete risks"
        )
    
    # Find risk by code
    risk = db.query(Risk).filter(Risk.risk_code == risk_code).first()
    
    # If not found by code, try UUID for backward compatibility
    if not risk and len(risk_code) == 36:
        try:
            risk_uuid = UUID(risk_code)
            risk = db.query(Risk).filter(Risk.id == risk_uuid).first()
        except ValueError:
            pass
    
    if not risk:
        raise HTTPException(status_code=404, detail=f"Risk {risk_code} not found")
    
    db.delete(risk)
    db.commit()
    
    return None