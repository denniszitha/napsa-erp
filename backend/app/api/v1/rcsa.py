from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid
import logging

from app.api.deps import get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class RCSABase(BaseModel):
    title: str
    description: Optional[str] = None
    department: str
    business_unit: str
    risk_category: str
    assessment_type: str = "annual"  # annual, quarterly, monthly
    scheduled_date: date
    due_date: date
    assigned_to: str
    status: str = "pending"  # pending, in_progress, completed, overdue

class RCSACreate(RCSABase):
    pass

class RCSAUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    business_unit: Optional[str] = None
    risk_category: Optional[str] = None
    assessment_type: Optional[str] = None
    scheduled_date: Optional[date] = None
    due_date: Optional[date] = None
    assigned_to: Optional[str] = None
    status: Optional[str] = None
    completion_date: Optional[date] = None
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    overall_rating: Optional[str] = None

class RCSAResponse(RCSABase):
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    completion_date: Optional[date] = None
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    overall_rating: Optional[str] = None

# Mock storage (in production, this would be in database)
rcsa_storage: Dict[str, Dict[str, Any]] = {}

@router.get("/", response_model=List[RCSAResponse])
async def get_rcsas(
    status: Optional[str] = None,
    department: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get all RCSA assessments with optional filtering"""
    try:
        rcsas = []
        for rcsa_id, rcsa_data in rcsa_storage.items():
            # Apply filters
            if status and rcsa_data.get('status') != status:
                continue
            if department and rcsa_data.get('department') != department:
                continue
                
            rcsas.append(rcsa_data)
        
        # Sort by due date
        rcsas.sort(key=lambda x: x.get('due_date', '9999-12-31'))
        
        return rcsas
    except Exception as e:
        logger.error(f"Error getting RCSAs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{rcsa_id}", response_model=RCSAResponse)
async def get_rcsa(
    rcsa_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get specific RCSA assessment"""
    try:
        if rcsa_id not in rcsa_storage:
            raise HTTPException(status_code=404, detail="RCSA not found")
        
        return rcsa_storage[rcsa_id]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RCSA {rcsa_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=RCSAResponse)
async def create_rcsa(
    rcsa: RCSACreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new RCSA assessment"""
    try:
        rcsa_id = str(uuid.uuid4())
        now = datetime.now()
        
        rcsa_data = {
            "id": rcsa_id,
            **rcsa.dict(),
            "created_at": now,
            "updated_at": now,
            "created_by": current_user.id,
            "completion_date": None,
            "findings": None,
            "recommendations": None,
            "overall_rating": None
        }
        
        # Convert dates to strings for storage
        rcsa_data["scheduled_date"] = rcsa_data["scheduled_date"].isoformat()
        rcsa_data["due_date"] = rcsa_data["due_date"].isoformat()
        
        rcsa_storage[rcsa_id] = rcsa_data
        
        # TODO: Schedule notification for due date
        
        return rcsa_data
    except Exception as e:
        logger.error(f"Error creating RCSA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{rcsa_id}", response_model=RCSAResponse)
async def update_rcsa(
    rcsa_id: str,
    rcsa_update: RCSAUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update RCSA assessment"""
    try:
        if rcsa_id not in rcsa_storage:
            raise HTTPException(status_code=404, detail="RCSA not found")
        
        rcsa_data = rcsa_storage[rcsa_id]
        
        # Update fields
        update_data = rcsa_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                if field in ["scheduled_date", "due_date", "completion_date"] and value:
                    rcsa_data[field] = value.isoformat() if hasattr(value, 'isoformat') else value
                else:
                    rcsa_data[field] = value
        
        rcsa_data["updated_at"] = datetime.now()
        
        # Auto-update status based on completion
        if rcsa_update.completion_date:
            rcsa_data["status"] = "completed"
        elif rcsa_data.get("due_date") and datetime.now().date() > datetime.fromisoformat(rcsa_data["due_date"]).date():
            rcsa_data["status"] = "overdue"
        
        rcsa_storage[rcsa_id] = rcsa_data
        
        return rcsa_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating RCSA {rcsa_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{rcsa_id}")
async def delete_rcsa(
    rcsa_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete RCSA assessment"""
    try:
        if rcsa_id not in rcsa_storage:
            raise HTTPException(status_code=404, detail="RCSA not found")
        
        del rcsa_storage[rcsa_id]
        
        return {"message": "RCSA deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting RCSA {rcsa_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/stats")
async def get_rcsa_dashboard(
    current_user: User = Depends(get_current_active_user)
):
    """Get RCSA dashboard statistics"""
    try:
        total_rcsas = len(rcsa_storage)
        
        status_counts = {"pending": 0, "in_progress": 0, "completed": 0, "overdue": 0}
        due_this_week = 0
        due_this_month = 0
        
        now = datetime.now()
        week_end = now + datetime.timedelta(days=7)
        month_end = now + datetime.timedelta(days=30)
        
        for rcsa_data in rcsa_storage.values():
            status = rcsa_data.get("status", "pending")
            status_counts[status] += 1
            
            due_date_str = rcsa_data.get("due_date")
            if due_date_str:
                due_date = datetime.fromisoformat(due_date_str)
                if due_date <= week_end:
                    due_this_week += 1
                if due_date <= month_end:
                    due_this_month += 1
        
        # Calculate completion rate
        completion_rate = (status_counts["completed"] / total_rcsas * 100) if total_rcsas > 0 else 0
        
        return {
            "success": True,
            "data": {
                "total_rcsas": total_rcsas,
                "status_breakdown": status_counts,
                "due_this_week": due_this_week,
                "due_this_month": due_this_month,
                "completion_rate": round(completion_rate, 1),
                "overdue_count": status_counts["overdue"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting RCSA dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedule/upcoming")
async def get_upcoming_rcsas(
    days: int = 30,
    current_user: User = Depends(get_current_active_user)
):
    """Get upcoming RCSA assessments"""
    try:
        upcoming = []
        cutoff_date = datetime.now() + datetime.timedelta(days=days)
        
        for rcsa_data in rcsa_storage.values():
            due_date_str = rcsa_data.get("due_date")
            if due_date_str and rcsa_data.get("status") not in ["completed"]:
                due_date = datetime.fromisoformat(due_date_str)
                if due_date <= cutoff_date:
                    upcoming.append({
                        **rcsa_data,
                        "days_until_due": (due_date.date() - datetime.now().date()).days
                    })
        
        # Sort by due date
        upcoming.sort(key=lambda x: x.get("due_date", "9999-12-31"))
        
        return {
            "success": True,
            "data": upcoming
        }
    except Exception as e:
        logger.error(f"Error getting upcoming RCSAs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedule/bulk")
async def create_bulk_rcsas(
    rcsas: List[RCSACreate],
    current_user: User = Depends(get_current_active_user)
):
    """Create multiple RCSA assessments"""
    try:
        created_rcsas = []
        
        for rcsa in rcsas:
            rcsa_id = str(uuid.uuid4())
            now = datetime.now()
            
            rcsa_data = {
                "id": rcsa_id,
                **rcsa.dict(),
                "created_at": now,
                "updated_at": now,
                "created_by": current_user.id,
                "completion_date": None,
                "findings": None,
                "recommendations": None,
                "overall_rating": None
            }
            
            # Convert dates to strings for storage
            rcsa_data["scheduled_date"] = rcsa_data["scheduled_date"].isoformat()
            rcsa_data["due_date"] = rcsa_data["due_date"].isoformat()
            
            rcsa_storage[rcsa_id] = rcsa_data
            created_rcsas.append(rcsa_data)
        
        return {
            "success": True,
            "message": f"Created {len(created_rcsas)} RCSA assessments",
            "data": created_rcsas
        }
    except Exception as e:
        logger.error(f"Error creating bulk RCSAs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Initialize with sample data
def init_sample_rcsas():
    """Initialize with sample RCSA data"""
    if not rcsa_storage:
        sample_rcsas = [
            {
                "id": str(uuid.uuid4()),
                "title": "Annual Risk Control Assessment - IT Department",
                "description": "Comprehensive assessment of IT controls and risk management processes",
                "department": "Information Technology",
                "business_unit": "Technology Services",
                "risk_category": "Cyber Security",
                "assessment_type": "annual",
                "scheduled_date": "2025-09-01",
                "due_date": "2025-09-30",
                "assigned_to": "IT Risk Manager",
                "status": "pending",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "created_by": "system",
                "completion_date": None,
                "findings": None,
                "recommendations": None,
                "overall_rating": None
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Quarterly Financial Controls Review",
                "description": "Review of financial controls and compliance procedures",
                "department": "Finance",
                "business_unit": "Finance and Administration",
                "risk_category": "Financial",
                "assessment_type": "quarterly",
                "scheduled_date": "2025-08-15",
                "due_date": "2025-08-30",
                "assigned_to": "Finance Manager",
                "status": "in_progress",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "created_by": "system",
                "completion_date": None,
                "findings": None,
                "recommendations": None,
                "overall_rating": None
            }
        ]
        
        for rcsa_data in sample_rcsas:
            rcsa_storage[rcsa_data["id"]] = rcsa_data

# Initialize sample data
init_sample_rcsas()