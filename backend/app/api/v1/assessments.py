from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.api.deps import get_db, get_current_active_user
from app.models.assessment import RiskAssessment
from app.models.assessment_period import AssessmentPeriod
from app.models.risk import Risk
from app.models.user import User
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate, AssessmentResponse
from app.schemas.base import PaginatedResponse
from app.services.risk_calculation import RiskCalculationService

router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
def read_assessments(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    risk_id: Optional[str] = None,  # Now using string ID (e.g., RISK-2025-0001)
    # current_user: User = Depends(get_current_active_user),  # Temporarily disabled for testing
):
    """Retrieve assessments with pagination"""
    query = db.query(RiskAssessment)
    
    if risk_id:
        query = query.filter(RiskAssessment.risk_id == risk_id)
    
    total = query.count()
    assessments = query.offset(skip).limit(limit).all()
    
    # Build response
    assessment_responses = []
    for assessment in assessments:
        # Convert UUID fields to strings before validation
        if assessment.assessor_id:
            assessment.assessor_id = str(assessment.assessor_id)
        
        assessment_dict = AssessmentResponse.model_validate(assessment).model_dump()
        
        # Remove the assessment_code field (no longer needed)
        assessment_dict.pop("assessment_code", None)
        
        # Add risk title
        if assessment.risk_id:
            risk = db.query(Risk).filter(Risk.id == assessment.risk_id).first()
            if risk:
                assessment_dict["risk_title"] = risk.title
        
        # Add assessor name
        if assessment.assessor_id:
            assessor = db.query(User).filter(User.id == assessment.assessor_id).first()
            if assessor:
                assessment_dict["assessor_name"] = assessor.full_name or assessor.username
        
        # Add assessment period name
        if assessment.assessment_period_id:
            period = db.query(AssessmentPeriod).filter(AssessmentPeriod.id == assessment.assessment_period_id).first()
            if period:
                assessment_dict["assessment_period_name"] = period.name
        
        assessment_responses.append(assessment_dict)
    
    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        data=assessment_responses
    )

@router.post("/", response_model=AssessmentResponse)
def create_assessment(
    assessment_in: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create new risk assessment"""
    # Check if risk exists
    risk = db.query(Risk).filter(Risk.id == assessment_in.risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    # Check if assessment period exists and is active
    if assessment_in.assessment_period_id:
        period = db.query(AssessmentPeriod).filter(
            AssessmentPeriod.id == assessment_in.assessment_period_id
        ).first()
        if not period:
            raise HTTPException(status_code=404, detail="Assessment period not found")
        if not period.is_active:
            raise HTTPException(status_code=400, detail="Assessment period is not active")
    
    # Generate human-readable assessment ID
    year = datetime.now().year
    # Get the last assessment ID for this year
    last_assessment = db.query(RiskAssessment).filter(
        RiskAssessment.id.like(f'ASMT-{year}-%')
    ).order_by(RiskAssessment.id.desc()).first()
    
    if last_assessment:
        # Extract number and increment
        last_num = int(last_assessment.id.split('-')[-1])
        new_num = last_num + 1
    else:
        # First assessment of the year
        new_num = 1
    
    assessment_id = f"ASMT-{year}-{new_num:04d}"
    
    # Calculate inherent risk
    inherent_risk = assessment_in.likelihood_score * assessment_in.impact_score
    
    # Use provided control effectiveness or calculate from mapped controls
    control_effectiveness = assessment_in.control_effectiveness
    if control_effectiveness is None or control_effectiveness < 0:
        # Calculate from mapped controls
        effectiveness_data = RiskCalculationService.calculate_aggregate_control_effectiveness(
            db, assessment_in.risk_id
        )
        control_effectiveness = effectiveness_data["aggregate_effectiveness"]
    
    # Calculate residual risk
    residual_risk = inherent_risk * (1 - control_effectiveness / 100)
    
    # Determine risk appetite status
    risk_appetite_status = "within" if residual_risk <= 12 else "exceeds"
    
    # Create assessment with calculated values
    assessment_data = assessment_in.model_dump()
    assessment_data['control_effectiveness'] = control_effectiveness  # Use calculated value
    
    assessment = RiskAssessment(
        **assessment_data,
        id=assessment_id,  # Use human-readable code as primary key
        assessor_id=str(current_user.id),  # Convert UUID to string
        inherent_risk=inherent_risk,
        residual_risk=residual_risk,
        risk_appetite_status=risk_appetite_status,
        assessment_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(assessment)
    
    # Update risk scores
    risk.inherent_risk_score = inherent_risk
    risk.residual_risk_score = residual_risk
    
    db.commit()
    db.refresh(assessment)
    
    # Create response dictionary with all required fields
    response_data = {
        "id": assessment.id,
        "risk_id": assessment.risk_id,
        "assessor_id": str(assessment.assessor_id) if assessment.assessor_id else None,
        "assessment_period_id": assessment.assessment_period_id,
        "likelihood_score": assessment.likelihood_score,
        "impact_score": assessment.impact_score,
        "control_effectiveness": assessment.control_effectiveness,
        "inherent_risk": assessment.inherent_risk,
        "residual_risk": assessment.residual_risk,
        "risk_appetite_status": assessment.risk_appetite_status,
        "assessment_date": assessment.assessment_date,
        "assessment_criteria": assessment.assessment_criteria,
        "notes": assessment.notes,
        "evidence_links": assessment.evidence_links,
        "next_review_date": assessment.next_review_date,
        "created_at": assessment.created_at if hasattr(assessment, 'created_at') else assessment.assessment_date,
        "updated_at": assessment.updated_at if hasattr(assessment, 'updated_at') else assessment.assessment_date,
        "risk_title": risk.title,  # Add risk title
        "assessor_name": current_user.full_name or current_user.username  # Add assessor name
    }
    
    # Add assessment period name
    if assessment.assessment_period_id:
        period = db.query(AssessmentPeriod).filter(AssessmentPeriod.id == assessment.assessment_period_id).first()
        if period:
            response_data["assessment_period_name"] = period.name
    
    return AssessmentResponse(**response_data)

@router.get("/{assessment_id}", response_model=AssessmentResponse)
def read_assessment(
    assessment_id: str,  # Now using string ID (e.g., ASMT-2025-0001)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get assessment by ID"""
    assessment = db.query(RiskAssessment).filter(RiskAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Convert UUID fields to strings before validation
    if assessment.assessor_id:
        assessment.assessor_id = str(assessment.assessor_id)
    
    # Build response with risk title and assessor name
    assessment_dict = AssessmentResponse.model_validate(assessment).model_dump()
    
    # Add risk title
    if assessment.risk_id:
        risk = db.query(Risk).filter(Risk.id == assessment.risk_id).first()
        if risk:
            assessment_dict["risk_title"] = risk.title
    
    # Add assessor name
    if assessment.assessor_id:
        assessor = db.query(User).filter(User.id == assessment.assessor_id).first()
        if assessor:
            assessment_dict["assessor_name"] = assessor.full_name or assessor.username
    
    # Add assessment period name
    if assessment.assessment_period_id:
        period = db.query(AssessmentPeriod).filter(AssessmentPeriod.id == assessment.assessment_period_id).first()
        if period:
            assessment_dict["assessment_period_name"] = period.name
    
    return assessment_dict

@router.put("/{assessment_id}", response_model=AssessmentResponse)
def update_assessment(
    assessment_id: str,  # Now using string ID (e.g., ASMT-2025-0001)
    assessment_update: AssessmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update existing assessment"""
    # Get existing assessment
    assessment = db.query(RiskAssessment).filter(RiskAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Update fields
    update_data = assessment_update.model_dump(exclude_unset=True)
    
    # Recalculate scores if likelihood or impact changed
    if 'likelihood_score' in update_data or 'impact_score' in update_data:
        likelihood = update_data.get('likelihood_score', assessment.likelihood_score)
        impact = update_data.get('impact_score', assessment.impact_score)
        update_data['inherent_risk'] = likelihood * impact
        
        # Recalculate residual risk
        control_effectiveness = update_data.get('control_effectiveness', assessment.control_effectiveness)
        update_data['residual_risk'] = update_data['inherent_risk'] * (1 - control_effectiveness / 100)
        
        # Update risk appetite status
        update_data['risk_appetite_status'] = "within" if update_data['residual_risk'] <= 12 else "exceeds"
        
        # Update risk's residual score
        risk = db.query(Risk).filter(Risk.id == assessment.risk_id).first()
        if risk:
            risk.residual_risk_score = update_data['residual_risk']
    
    # Update timestamp
    update_data['updated_at'] = datetime.now(timezone.utc)
    
    # Apply updates
    for field, value in update_data.items():
        setattr(assessment, field, value)
    
    db.commit()
    db.refresh(assessment)
    
    # Convert UUID fields to strings before validation
    if assessment.assessor_id:
        assessment.assessor_id = str(assessment.assessor_id)
    
    # Build response with risk title and assessor name
    assessment_dict = AssessmentResponse.model_validate(assessment).model_dump()
    
    # Add risk title
    if assessment.risk_id:
        risk = db.query(Risk).filter(Risk.id == assessment.risk_id).first()
        if risk:
            assessment_dict["risk_title"] = risk.title
    
    # Add assessor name
    if assessment.assessor_id:
        assessor = db.query(User).filter(User.id == assessment.assessor_id).first()
        if assessor:
            assessment_dict["assessor_name"] = assessor.full_name or assessor.username
    
    # Add assessment period name
    if assessment.assessment_period_id:
        period = db.query(AssessmentPeriod).filter(AssessmentPeriod.id == assessment.assessment_period_id).first()
        if period:
            assessment_dict["assessment_period_name"] = period.name
    
    return assessment_dict

@router.delete("/{assessment_id}")
def delete_assessment(
    assessment_id: str,  # Now using string ID (e.g., ASMT-2025-0001)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete assessment"""
    # Check if user is admin or the assessor
    assessment = db.query(RiskAssessment).filter(RiskAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Only admin or the original assessor can delete
    if current_user.role != "admin" and assessment.assessor_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this assessment"
        )
    
    db.delete(assessment)
    db.commit()
    
    return {"message": "Assessment deleted successfully"}
