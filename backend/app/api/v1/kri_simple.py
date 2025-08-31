from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.base import PaginatedResponse

# Simple schemas for KRI
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

router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
def get_kris(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
):
    """Get all KRIs - simplified version with mock data"""
    # Return mock KRI data
    kris = [
        {
            "id": str(uuid4()),
            "name": "System Uptime",
            "status": "green",
            "current_value": 99.95
        },
        {
            "id": str(uuid4()),
            "name": "Failed Login Attempts",
            "status": "amber",
            "current_value": 45
        },
        {
            "id": str(uuid4()),
            "name": "Payment Processing Time",
            "status": "red",
            "current_value": 8.5
        }
    ]
    
    return PaginatedResponse(
        total=len(kris),
        skip=skip,
        limit=limit,
        data=kris[skip:skip+limit]
    )

@router.post("/", response_model=KRIResponse, status_code=status.HTTP_201_CREATED)
def create_kri(
    kri_in: KRICreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create new KRI - simplified version"""
    # Calculate status
    status = "green"
    if kri_in.is_lower_better:
        if kri_in.current_value > kri_in.threshold_red:
            status = "red"
        elif kri_in.current_value > kri_in.threshold_amber:
            status = "amber"
    else:
        if kri_in.current_value < kri_in.threshold_red:
            status = "red"
        elif kri_in.current_value < kri_in.threshold_amber:
            status = "amber"
    
    # Return mock response
    return KRIResponse(
        id=uuid4(),
        name=kri_in.name,
        status=status,
        current_value=kri_in.current_value
    )

@router.get("/{kri_id}", response_model=Dict[str, Any])
def get_kri(
    kri_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get KRI by ID - simplified version"""
    # Return mock KRI detail
    return {
        "id": str(kri_id),
        "name": "System Uptime",
        "status": "green",
        "current_value": 99.95,
        "risk_title": "System Availability Risk",
        "owner_name": "IT Operations",
        "historical_values": [],
        "breach_count": 0,
        "average_value": 99.95
    }

@router.put("/{kri_id}", response_model=KRIResponse)
def update_kri(
    kri_id: UUID,
    kri_update: KRIUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update KRI - simplified version"""
    # Return mock updated KRI
    return KRIResponse(
        id=kri_id,
        name="Updated KRI",
        status="amber",
        current_value=kri_update.current_value or 88.5
    )

@router.delete("/{kri_id}")
def delete_kri(
    kri_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete KRI - simplified version"""
    return {"message": "KRI deleted successfully"}

@router.get("/dashboard/summary", response_model=Dict[str, Any])
def get_kri_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get KRI dashboard summary - simplified version"""
    return {
        "summary": {
            "total_kris": 12,
            "breached_kris": 3,
            "critical_kris": 1,
            "compliance_rate": 75.0
        },
        "by_status": {"green": 9, "amber": 2, "red": 1},
        "recent_measurements": []
    }