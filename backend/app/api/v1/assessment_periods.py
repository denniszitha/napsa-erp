"""
Assessment Periods API Endpoints
Manages assessment cycles and periods
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.api import deps
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.assessment_period import AssessmentPeriod
from app.models.user import User
from app.schemas.assessment_period import (
    AssessmentPeriodCreate,
    AssessmentPeriodUpdate,
    AssessmentPeriodResponse,
    AssessmentPeriodList
)

router = APIRouter()


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Check if current user is admin"""
    if current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_current_admin_or_risk_manager(
    current_user: User = Depends(get_current_user)
) -> User:
    """Check if current user is admin or risk manager"""
    if current_user.role not in ['admin', 'super_admin', 'risk_manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


@router.get("/", response_model=AssessmentPeriodList)
def get_assessment_periods(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get list of assessment periods with optional filtering
    """
    query = db.query(AssessmentPeriod)
    
    # Filter by active status if specified
    if is_active is not None:
        query = query.filter(AssessmentPeriod.is_active == is_active)
    
    # Search filter
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                AssessmentPeriod.name.ilike(search_filter),
                AssessmentPeriod.description.ilike(search_filter)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    periods = query.order_by(AssessmentPeriod.start_date.desc()).offset(skip).limit(limit).all()
    
    return {
        "data": periods,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/active", response_model=List[AssessmentPeriodResponse])
def get_active_periods(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[AssessmentPeriod]:
    """
    Get all currently active assessment periods
    """
    today = date.today()
    periods = db.query(AssessmentPeriod).filter(
        and_(
            AssessmentPeriod.is_active == True,
            AssessmentPeriod.start_date <= today,
            AssessmentPeriod.end_date >= today
        )
    ).order_by(AssessmentPeriod.start_date).all()
    
    return periods


@router.get("/upcoming", response_model=List[AssessmentPeriodResponse])
def get_upcoming_periods(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[AssessmentPeriod]:
    """
    Get upcoming assessment periods within specified days
    """
    today = date.today()
    periods = db.query(AssessmentPeriod).filter(
        and_(
            AssessmentPeriod.is_active == True,
            AssessmentPeriod.start_date > today,
            AssessmentPeriod.start_date <= today + timedelta(days=days)
        )
    ).order_by(AssessmentPeriod.start_date).all()
    
    return periods


@router.get("/{period_id}", response_model=AssessmentPeriodResponse)
def get_assessment_period(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AssessmentPeriod:
    """
    Get specific assessment period by ID
    """
    period = db.query(AssessmentPeriod).filter(AssessmentPeriod.id == period_id).first()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment period not found"
        )
    
    return period


@router.post("/", response_model=AssessmentPeriodResponse, status_code=status.HTTP_201_CREATED)
def create_assessment_period(
    period_data: AssessmentPeriodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_risk_manager)
) -> AssessmentPeriod:
    """
    Create new assessment period
    Only admins and risk managers can create periods
    """
    # Validate dates
    if period_data.end_date <= period_data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )
    
    # Check for overlapping periods of the SAME TYPE only
    # Different assessment types can overlap (e.g., quarterly within annual)
    overlapping = db.query(AssessmentPeriod).filter(
        and_(
            AssessmentPeriod.is_active == True,
            AssessmentPeriod.assessment_type == period_data.assessment_type,  # Only check same type
            or_(
                and_(
                    AssessmentPeriod.start_date <= period_data.start_date,
                    AssessmentPeriod.end_date >= period_data.start_date
                ),
                and_(
                    AssessmentPeriod.start_date <= period_data.end_date,
                    AssessmentPeriod.end_date >= period_data.end_date
                ),
                and_(
                    AssessmentPeriod.start_date >= period_data.start_date,
                    AssessmentPeriod.end_date <= period_data.end_date
                )
            )
        )
    ).first()
    
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Period overlaps with existing {period_data.assessment_type}: {overlapping.name}. Different assessment types can overlap."
        )
    
    # Create new period
    period = AssessmentPeriod(
        **period_data.dict(),
        created_by_id=current_user.id
    )
    
    db.add(period)
    db.commit()
    db.refresh(period)
    
    return period


@router.put("/{period_id}", response_model=AssessmentPeriodResponse)
def update_assessment_period(
    period_id: int,
    period_update: AssessmentPeriodUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_risk_manager)
) -> AssessmentPeriod:
    """
    Update assessment period
    Only admins and risk managers can update periods
    """
    period = db.query(AssessmentPeriod).filter(AssessmentPeriod.id == period_id).first()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment period not found"
        )
    
    update_data = period_update.dict(exclude_unset=True)
    
    # Validate dates if being updated
    if 'start_date' in update_data or 'end_date' in update_data:
        start_date = update_data.get('start_date', period.start_date)
        end_date = update_data.get('end_date', period.end_date)
        
        if end_date <= start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
    
    # Update fields
    for field, value in update_data.items():
        setattr(period, field, value)
    
    period.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(period)
    
    return period


@router.delete("/{period_id}")
def delete_assessment_period(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> dict:
    """
    Delete assessment period
    Only admins can delete periods
    """
    period = db.query(AssessmentPeriod).filter(AssessmentPeriod.id == period_id).first()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment period not found"
        )
    
    # Check if period has assessments
    if period.risk_assessments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete period with {len(period.risk_assessments)} assessments. Deactivate instead."
        )
    
    db.delete(period)
    db.commit()
    
    return {"message": "Assessment period deleted successfully"}


@router.post("/{period_id}/deactivate")
def deactivate_assessment_period(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_risk_manager)
) -> dict:
    """
    Deactivate assessment period instead of deleting
    """
    period = db.query(AssessmentPeriod).filter(AssessmentPeriod.id == period_id).first()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment period not found"
        )
    
    period.is_active = False
    period.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Assessment period deactivated successfully"}


@router.post("/{period_id}/activate")
def activate_assessment_period(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_risk_manager)
) -> dict:
    """
    Activate assessment period
    """
    period = db.query(AssessmentPeriod).filter(AssessmentPeriod.id == period_id).first()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment period not found"
        )
    
    period.is_active = True
    period.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Assessment period activated successfully"}


@router.get("/{period_id}/statistics")
def get_period_statistics(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get statistics for a specific assessment period
    """
    period = db.query(AssessmentPeriod).filter(AssessmentPeriod.id == period_id).first()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment period not found"
        )
    
    # Calculate statistics
    total_assessments = len(period.risk_assessments) if period.risk_assessments else 0
    
    stats = {
        "period_id": period.id,
        "period_name": period.name,
        "start_date": period.start_date.isoformat(),
        "end_date": period.end_date.isoformat(),
        "total_assessments": total_assessments,
        "is_active": period.is_active,
        "days_remaining": (period.end_date - date.today()).days if period.end_date > date.today() else 0,
        "progress_percentage": calculate_period_progress(period.start_date, period.end_date)
    }
    
    return stats


def calculate_period_progress(start_date: date, end_date: date) -> float:
    """Calculate percentage progress of assessment period"""
    today = date.today()
    
    if today < start_date:
        return 0.0
    elif today > end_date:
        return 100.0
    else:
        total_days = (end_date - start_date).days
        elapsed_days = (today - start_date).days
        return round((elapsed_days / total_days) * 100, 2) if total_days > 0 else 0.0


# Import required for timedelta
from datetime import timedelta