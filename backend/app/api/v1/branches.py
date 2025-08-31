"""
NAPSA Branch Management API
Handles branch operations, assignments, and performance metrics
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from pydantic import BaseModel, Field

from app.api import deps
from app.core.database import get_db
from app.models.user import User

router = APIRouter()

# Pydantic models
class BranchBase(BaseModel):
    unit_code: str
    unit_name: str
    unit_type: str = "Station"
    parent_id: Optional[int] = None
    location: Optional[str] = None
    contact_info: Optional[str] = None
    risk_appetite: str = "conservative"
    review_frequency: str = "monthly"

class BranchCreate(BranchBase):
    pass

class BranchUpdate(BaseModel):
    unit_name: Optional[str] = None
    location: Optional[str] = None
    contact_info: Optional[str] = None
    risk_appetite: Optional[str] = None
    review_frequency: Optional[str] = None

class BranchResponse(BranchBase):
    id: int
    level: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class BranchAssignment(BaseModel):
    employee_id: int
    branch_id: int
    role: str
    assignment_type: str = Field(..., pattern="^(permanent|temporary|rotational)$")
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None

class BranchMetrics(BaseModel):
    branch_id: int
    metric_date: date
    registered_members: Optional[int] = 0
    active_employers: Optional[int] = 0
    contributions_collected: Optional[float] = 0.0
    benefits_paid: Optional[float] = 0.0
    compliance_rate: Optional[float] = None
    customer_satisfaction_score: Optional[float] = None
    processing_time_days: Optional[float] = None
    staff_count: Optional[int] = 0

class BranchPerformance(BaseModel):
    unit_code: str
    unit_name: str
    location: Optional[str]
    registered_members: int
    active_employers: int
    contributions_collected: float
    benefits_paid: float
    compliance_rate: Optional[float]
    customer_satisfaction_score: Optional[float]
    active_staff: int
    branch_risks: int
    avg_risk_score: Optional[float]

# API Endpoints

@router.get("/", response_model=List[Dict[str, Any]])
def get_all_branches(
    region: Optional[str] = Query(None, description="Filter by region code"),
    include_metrics: bool = Query(False, description="Include latest metrics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get all NAPSA branches with optional filtering"""
    query = """
        SELECT 
            ou.*,
            parent.unit_name as region_name,
            COUNT(DISTINCT ba.id) as active_staff,
            bm.registered_members,
            bm.active_employers,
            bm.compliance_rate
        FROM organizational_units ou
        LEFT JOIN organizational_units parent ON ou.parent_id = parent.id
        LEFT JOIN branch_assignments ba ON ba.branch_id = ou.id AND ba.is_active = true
        LEFT JOIN branch_metrics bm ON bm.branch_id = ou.id 
            AND bm.metric_date = (SELECT MAX(metric_date) FROM branch_metrics WHERE branch_id = ou.id)
        WHERE (ou.unit_code LIKE 'BR-%' OR ou.unit_code LIKE 'REG-%')
    """
    
    params = {}
    if region:
        query += " AND parent.unit_code = :region"
        params['region'] = region
    
    query += " GROUP BY ou.id, parent.unit_name, bm.registered_members, bm.active_employers, bm.compliance_rate"
    query += " ORDER BY ou.unit_name"
    
    result = db.execute(query, params)
    branches = []
    for row in result:
        branch = dict(row)
        branches.append(branch)
    
    return branches

@router.get("/hierarchy", response_model=List[Dict[str, Any]])
def get_branch_hierarchy(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get hierarchical view of all branches"""
    query = """
        SELECT * FROM v_branch_hierarchy
        ORDER BY full_path
    """
    result = db.execute(query)
    return [dict(row) for row in result]

@router.get("/{branch_id}", response_model=Dict[str, Any])
def get_branch_details(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get detailed information about a specific branch"""
    query = """
        SELECT 
            ou.*,
            parent.unit_name as region_name,
            COUNT(DISTINCT ba.id) as active_staff,
            COUNT(DISTINCT r.id) as total_risks,
            AVG(r.inherent_risk_score) as avg_risk_score,
            bm.*
        FROM organizational_units ou
        LEFT JOIN organizational_units parent ON ou.parent_id = parent.id
        LEFT JOIN branch_assignments ba ON ba.branch_id = ou.id AND ba.is_active = true
        LEFT JOIN risks r ON r.organizational_unit_id = ou.id
        LEFT JOIN branch_metrics bm ON bm.branch_id = ou.id 
            AND bm.metric_date = (SELECT MAX(metric_date) FROM branch_metrics WHERE branch_id = ou.id)
        WHERE ou.id = :branch_id
        GROUP BY ou.id, parent.unit_name, bm.id
    """
    
    result = db.execute(query, {"branch_id": branch_id}).first()
    if not result:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    return dict(result)

@router.post("/", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(
    branch: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Create a new branch office"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to create branches")
    
    query = """
        INSERT INTO organizational_units 
        (unit_code, unit_name, unit_type, parent_id, level, location, contact_info, risk_appetite, review_frequency)
        VALUES (:unit_code, :unit_name, :unit_type, :parent_id, 3, :location, :contact_info, :risk_appetite, :review_frequency)
        RETURNING *
    """
    
    result = db.execute(query, {
        "unit_code": branch.unit_code,
        "unit_name": branch.unit_name,
        "unit_type": branch.unit_type,
        "parent_id": branch.parent_id,
        "location": branch.location,
        "contact_info": branch.contact_info,
        "risk_appetite": branch.risk_appetite,
        "review_frequency": branch.review_frequency
    }).first()
    
    db.commit()
    return dict(result)

@router.put("/{branch_id}", response_model=BranchResponse)
def update_branch(
    branch_id: int,
    branch_update: BranchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Update branch information"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to update branches")
    
    # Build dynamic update query
    update_fields = []
    params = {"branch_id": branch_id}
    
    if branch_update.unit_name is not None:
        update_fields.append("unit_name = :unit_name")
        params["unit_name"] = branch_update.unit_name
    
    if branch_update.location is not None:
        update_fields.append("location = :location")
        params["location"] = branch_update.location
    
    if branch_update.contact_info is not None:
        update_fields.append("contact_info = :contact_info")
        params["contact_info"] = branch_update.contact_info
    
    if branch_update.risk_appetite is not None:
        update_fields.append("risk_appetite = :risk_appetite")
        params["risk_appetite"] = branch_update.risk_appetite
    
    if branch_update.review_frequency is not None:
        update_fields.append("review_frequency = :review_frequency")
        params["review_frequency"] = branch_update.review_frequency
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    query = f"""
        UPDATE organizational_units 
        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = :branch_id
        RETURNING *
    """
    
    result = db.execute(query, params).first()
    if not result:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    db.commit()
    return dict(result)

# Branch Assignment Endpoints

@router.post("/assignments", status_code=status.HTTP_201_CREATED)
def create_branch_assignment(
    assignment: BranchAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Assign an employee to a branch"""
    query = """
        INSERT INTO branch_assignments 
        (employee_id, branch_id, role, assignment_type, start_date, end_date, is_active, created_by, notes)
        VALUES (:employee_id, :branch_id, :role, :assignment_type, :start_date, :end_date, true, :created_by, :notes)
        RETURNING *
    """
    
    result = db.execute(query, {
        "employee_id": assignment.employee_id,
        "branch_id": assignment.branch_id,
        "role": assignment.role,
        "assignment_type": assignment.assignment_type,
        "start_date": assignment.start_date,
        "end_date": assignment.end_date,
        "created_by": current_user.id,
        "notes": assignment.notes
    }).first()
    
    db.commit()
    return {"message": "Assignment created successfully", "assignment_id": result['id']}

@router.get("/assignments/{branch_id}", response_model=List[Dict[str, Any]])
def get_branch_assignments(
    branch_id: int,
    active_only: bool = Query(True, description="Show only active assignments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get all assignments for a branch"""
    query = """
        SELECT 
            ba.*,
            u.full_name as employee_name,
            u.email as employee_email,
            creator.full_name as created_by_name
        FROM branch_assignments ba
        JOIN users u ON ba.employee_id = u.id
        LEFT JOIN users creator ON ba.created_by = creator.id
        WHERE ba.branch_id = :branch_id
    """
    
    params = {"branch_id": branch_id}
    if active_only:
        query += " AND ba.is_active = true"
    
    query += " ORDER BY ba.start_date DESC"
    
    result = db.execute(query, params)
    return [dict(row) for row in result]

# Branch Metrics Endpoints

@router.post("/metrics", status_code=status.HTTP_201_CREATED)
def record_branch_metrics(
    metrics: BranchMetrics,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Record performance metrics for a branch"""
    query = """
        INSERT INTO branch_metrics 
        (branch_id, metric_date, registered_members, active_employers, contributions_collected, 
         benefits_paid, compliance_rate, customer_satisfaction_score, processing_time_days, staff_count)
        VALUES (:branch_id, :metric_date, :registered_members, :active_employers, :contributions_collected,
                :benefits_paid, :compliance_rate, :customer_satisfaction_score, :processing_time_days, :staff_count)
        ON CONFLICT (branch_id, metric_date) 
        DO UPDATE SET
            registered_members = EXCLUDED.registered_members,
            active_employers = EXCLUDED.active_employers,
            contributions_collected = EXCLUDED.contributions_collected,
            benefits_paid = EXCLUDED.benefits_paid,
            compliance_rate = EXCLUDED.compliance_rate,
            customer_satisfaction_score = EXCLUDED.customer_satisfaction_score,
            processing_time_days = EXCLUDED.processing_time_days,
            staff_count = EXCLUDED.staff_count,
            created_at = CURRENT_TIMESTAMP
        RETURNING id
    """
    
    result = db.execute(query, metrics.dict()).first()
    db.commit()
    return {"message": "Metrics recorded successfully", "metrics_id": result['id']}

@router.get("/metrics/{branch_id}", response_model=List[Dict[str, Any]])
def get_branch_metrics(
    branch_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get historical metrics for a branch"""
    query = """
        SELECT * FROM branch_metrics
        WHERE branch_id = :branch_id
    """
    
    params = {"branch_id": branch_id}
    
    if start_date:
        query += " AND metric_date >= :start_date"
        params["start_date"] = start_date
    
    if end_date:
        query += " AND metric_date <= :end_date"
        params["end_date"] = end_date
    
    query += " ORDER BY metric_date DESC"
    
    result = db.execute(query, params)
    return [dict(row) for row in result]

@router.get("/performance/summary", response_model=List[BranchPerformance])
def get_branch_performance_summary(
    region: Optional[str] = Query(None, description="Filter by region"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get performance summary for all branches"""
    query = "SELECT * FROM v_branch_performance"
    
    params = {}
    if region:
        query += " WHERE unit_code IN (SELECT unit_code FROM organizational_units WHERE parent_id = (SELECT id FROM organizational_units WHERE unit_code = :region))"
        params['region'] = region
    
    result = db.execute(query, params)
    return [dict(row) for row in result]

@router.get("/performance/rankings", response_model=Dict[str, Any])
def get_branch_rankings(
    metric: str = Query("compliance_rate", description="Metric to rank by"),
    period: str = Query("current", description="Period: current, month, quarter, year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get branch rankings by various metrics"""
    valid_metrics = ["compliance_rate", "contributions_collected", "customer_satisfaction_score", "registered_members"]
    if metric not in valid_metrics:
        raise HTTPException(status_code=400, detail=f"Invalid metric. Must be one of: {valid_metrics}")
    
    query = f"""
        WITH ranked_branches AS (
            SELECT 
                ou.unit_code,
                ou.unit_name,
                bm.{metric} as metric_value,
                RANK() OVER (ORDER BY bm.{metric} DESC NULLS LAST) as rank
            FROM organizational_units ou
            LEFT JOIN branch_metrics bm ON bm.branch_id = ou.id
                AND bm.metric_date = (SELECT MAX(metric_date) FROM branch_metrics WHERE branch_id = ou.id)
            WHERE ou.unit_code LIKE 'BR-%'
        )
        SELECT * FROM ranked_branches
        ORDER BY rank
    """
    
    result = db.execute(query)
    rankings = [dict(row) for row in result]
    
    return {
        "metric": metric,
        "period": period,
        "rankings": rankings,
        "generated_at": datetime.now()
    }