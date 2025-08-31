"""
Enhanced KRI CRUD API
Complete CRUD operations for Key Risk Indicators with advanced features
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from pydantic import BaseModel, Field, validator

from app.api.deps import get_db, get_current_active_user
from app.models.user import User

router = APIRouter()

# Pydantic Models
class KRIBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    category: str = Field(..., pattern="^(Operational|Financial|Compliance|Strategic|Technology|Reputational|Risk)$")
    unit_of_measure: str = Field(..., max_length=50)
    target_value: float
    threshold_green: float
    threshold_amber: float
    threshold_red: float
    frequency: str = Field(..., pattern="^(Daily|Weekly|Monthly|Quarterly|Annually)$")
    owner_id: int
    department: str
    data_source: Optional[str] = None
    calculation_method: Optional[str] = None
    
    @validator('threshold_green')
    def validate_thresholds(cls, v, values):
        if 'threshold_amber' in values and v <= values['threshold_amber']:
            raise ValueError('Green threshold must be better than amber threshold')
        if 'threshold_red' in values and v <= values['threshold_red']:
            raise ValueError('Green threshold must be better than red threshold')
        return v

class KRICreate(KRIBase):
    pass

class KRIUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: Optional[str] = None
    target_value: Optional[float] = None
    threshold_green: Optional[float] = None
    threshold_amber: Optional[float] = None
    threshold_red: Optional[float] = None
    frequency: Optional[str] = None
    owner_id: Optional[int] = None
    department: Optional[str] = None
    data_source: Optional[str] = None
    calculation_method: Optional[str] = None
    is_active: Optional[bool] = None

class KRIValue(BaseModel):
    kri_id: int
    value: float
    period_date: date
    notes: Optional[str] = None
    data_quality: str = Field(default="Good", pattern="^(Excellent|Good|Fair|Poor)$")

class KRIResponse(KRIBase):
    id: int
    current_value: Optional[float]
    previous_value: Optional[float]
    trend: Optional[str]
    status: str
    last_updated: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# CRUD Endpoints

@router.get("/", response_model=List[Dict[str, Any]])
def get_kris(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter by status: Green, Amber, Red, Critical"),
    is_active: bool = Query(True),
    frequency: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    include_history: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all KRIs with filtering and pagination"""
    
    query = """
        SELECT 
            kri.*,
            u.full_name as owner_name,
            CASE 
                WHEN kri.current_value >= kri.threshold_green THEN 'Green'
                WHEN kri.current_value >= kri.threshold_amber THEN 'Amber'
                WHEN kri.current_value >= kri.threshold_red THEN 'Red'
                ELSE 'Critical'
            END as status,
            CASE 
                WHEN kri.previous_value IS NULL THEN 'Stable'
                WHEN kri.current_value > kri.previous_value THEN 'Improving'
                WHEN kri.current_value < kri.previous_value THEN 'Declining'
                ELSE 'Stable'
            END as trend
        FROM key_risk_indicators kri
        LEFT JOIN users u ON kri.owner_id = u.id
        WHERE 1=1
    """
    
    params = {"skip": skip, "limit": limit}
    
    if category:
        query += " AND kri.category = :category"
        params["category"] = category
    
    if department:
        query += " AND kri.department = :department"
        params["department"] = department
    
    if is_active is not None:
        query += " AND kri.is_active = :is_active"
        params["is_active"] = is_active
    
    if frequency:
        query += " AND kri.frequency = :frequency"
        params["frequency"] = frequency
    
    if search:
        query += " AND (kri.name ILIKE :search OR kri.description ILIKE :search)"
        params["search"] = f"%{search}%"
    
    if status:
        status_conditions = {
            "Green": "kri.current_value >= kri.threshold_green",
            "Amber": "kri.current_value >= kri.threshold_amber AND kri.current_value < kri.threshold_green",
            "Red": "kri.current_value >= kri.threshold_red AND kri.current_value < kri.threshold_amber",
            "Critical": "kri.current_value < kri.threshold_red"
        }
        if status in status_conditions:
            query += f" AND {status_conditions[status]}"
    
    query += " ORDER BY kri.name LIMIT :limit OFFSET :skip"
    
    result = db.execute(query, params)
    kris = []
    
    for row in result:
        kri = dict(row)
        
        if include_history:
            # Get last 6 values
            history_query = """
                SELECT period_date, value, data_quality
                FROM kri_values
                WHERE kri_id = :kri_id
                ORDER BY period_date DESC
                LIMIT 6
            """
            history = db.execute(history_query, {"kri_id": kri['id']})
            kri['history'] = [dict(h) for h in history]
        
        kris.append(kri)
    
    return kris

@router.get("/dashboard", response_model=Dict[str, Any])
def get_kri_dashboard(
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get KRI dashboard summary"""
    
    base_condition = "WHERE is_active = true"
    params = {}
    
    if department:
        base_condition += " AND department = :department"
        params["department"] = department
    
    summary_query = f"""
        SELECT 
            COUNT(*) as total_kris,
            COUNT(*) FILTER (WHERE current_value >= threshold_green) as green_count,
            COUNT(*) FILTER (WHERE current_value >= threshold_amber AND current_value < threshold_green) as amber_count,
            COUNT(*) FILTER (WHERE current_value >= threshold_red AND current_value < threshold_amber) as red_count,
            COUNT(*) FILTER (WHERE current_value < threshold_red) as critical_count,
            AVG(CASE WHEN target_value > 0 THEN (current_value / target_value * 100) ELSE NULL END) as avg_performance
        FROM key_risk_indicators
        {base_condition}
    """
    
    by_category_query = f"""
        SELECT 
            category,
            COUNT(*) as count,
            AVG(CASE WHEN target_value > 0 THEN (current_value / target_value * 100) ELSE NULL END) as avg_performance
        FROM key_risk_indicators
        {base_condition}
        GROUP BY category
    """
    
    critical_kris_query = f"""
        SELECT id, name, department, current_value, threshold_red
        FROM key_risk_indicators
        {base_condition} AND current_value < threshold_red
        ORDER BY (threshold_red - current_value) DESC
        LIMIT 5
    """
    
    summary = db.execute(summary_query, params).first()
    by_category = db.execute(by_category_query, params).fetchall()
    critical = db.execute(critical_kris_query, params).fetchall()
    
    return {
        "summary": dict(summary),
        "by_category": [dict(row) for row in by_category],
        "critical_kris": [dict(row) for row in critical],
        "generated_at": datetime.now()
    }

@router.get("/{kri_id}", response_model=Dict[str, Any])
def get_kri(
    kri_id: int,
    include_history: bool = Query(True),
    include_associations: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific KRI"""
    
    query = """
        SELECT 
            kri.*,
            u.full_name as owner_name,
            u.email as owner_email,
            CASE 
                WHEN kri.current_value >= kri.threshold_green THEN 'Green'
                WHEN kri.current_value >= kri.threshold_amber THEN 'Amber'
                WHEN kri.current_value >= kri.threshold_red THEN 'Red'
                ELSE 'Critical'
            END as status
        FROM key_risk_indicators kri
        LEFT JOIN users u ON kri.owner_id = u.id
        WHERE kri.id = :kri_id
    """
    
    result = db.execute(query, {"kri_id": kri_id}).first()
    if not result:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    kri = dict(result)
    
    if include_history:
        history_query = """
            SELECT 
                kv.*,
                u.full_name as recorded_by_name
            FROM kri_values kv
            LEFT JOIN users u ON kv.recorded_by = u.id
            WHERE kv.kri_id = :kri_id
            ORDER BY kv.period_date DESC
            LIMIT 12
        """
        history = db.execute(history_query, {"kri_id": kri_id})
        kri['value_history'] = [dict(h) for h in history]
    
    if include_associations:
        # Get associated risks
        risks_query = """
            SELECT r.id, r.title, r.inherent_risk_score
            FROM kri_risk_associations kra
            JOIN risks r ON kra.risk_id = r.id
            WHERE kra.kri_id = :kri_id
        """
        risks = db.execute(risks_query, {"kri_id": kri_id})
        kri['associated_risks'] = [dict(r) for r in risks]
    
    return kri

@router.post("/", response_model=KRIResponse, status_code=status.HTTP_201_CREATED)
def create_kri(
    kri: KRICreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new KRI"""
    
    # Check if KRI name already exists
    existing = db.execute(
        "SELECT id FROM key_risk_indicators WHERE name = :name",
        {"name": kri.name}
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="KRI with this name already exists")
    
    query = """
        INSERT INTO key_risk_indicators 
        (name, description, category, unit_of_measure, target_value, threshold_green,
         threshold_amber, threshold_red, frequency, owner_id, department, data_source,
         calculation_method, is_active)
        VALUES (:name, :description, :category, :unit_of_measure, :target_value, :threshold_green,
                :threshold_amber, :threshold_red, :frequency, :owner_id, :department, :data_source,
                :calculation_method, true)
        RETURNING *
    """
    
    result = db.execute(query, kri.dict()).first()
    db.commit()
    
    return dict(result)

@router.put("/{kri_id}", response_model=KRIResponse)
def update_kri(
    kri_id: int,
    kri_update: KRIUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a KRI"""
    
    # Check KRI exists
    existing = db.execute(
        "SELECT * FROM key_risk_indicators WHERE id = :id",
        {"id": kri_id}
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    # Build update query
    update_fields = []
    params = {"kri_id": kri_id}
    
    for field, value in kri_update.dict(exclude_unset=True).items():
        if value is not None:
            update_fields.append(f"{field} = :{field}")
            params[field] = value
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Validate thresholds if being updated
    if any(f in params for f in ['threshold_green', 'threshold_amber', 'threshold_red']):
        thresholds = {
            'threshold_green': params.get('threshold_green', existing['threshold_green']),
            'threshold_amber': params.get('threshold_amber', existing['threshold_amber']),
            'threshold_red': params.get('threshold_red', existing['threshold_red'])
        }
        
        if not (thresholds['threshold_green'] > thresholds['threshold_amber'] > thresholds['threshold_red']):
            raise HTTPException(status_code=400, detail="Invalid threshold values")
    
    query = f"""
        UPDATE key_risk_indicators 
        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = :kri_id
        RETURNING *
    """
    
    result = db.execute(query, params).first()
    db.commit()
    
    return dict(result)

@router.delete("/{kri_id}")
def delete_kri(
    kri_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a KRI"""
    
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete KRIs")
    
    # Check if KRI exists
    existing = db.execute(
        "SELECT * FROM key_risk_indicators WHERE id = :id",
        {"id": kri_id}
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    # Check for associated values
    values = db.execute(
        "SELECT COUNT(*) as count FROM kri_values WHERE kri_id = :id",
        {"id": kri_id}
    ).first()
    
    if values['count'] > 0:
        # Soft delete by deactivating
        db.execute(
            "UPDATE key_risk_indicators SET is_active = false WHERE id = :id",
            {"id": kri_id}
        )
        db.commit()
        return {"message": f"KRI deactivated (has {values['count']} historical values)"}
    
    # Hard delete if no values
    db.execute(
        "DELETE FROM key_risk_indicators WHERE id = :id",
        {"id": kri_id}
    )
    db.commit()
    
    return {"message": "KRI deleted successfully"}

@router.post("/{kri_id}/values", status_code=status.HTTP_201_CREATED)
def record_kri_value(
    kri_id: int,
    value: KRIValue,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Record a new value for a KRI"""
    
    # Check KRI exists
    kri = db.execute(
        "SELECT * FROM key_risk_indicators WHERE id = :id",
        {"id": kri_id}
    ).first()
    
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    
    # Store previous value
    db.execute(
        "UPDATE key_risk_indicators SET previous_value = current_value WHERE id = :id",
        {"id": kri_id}
    )
    
    # Update current value
    db.execute(
        """UPDATE key_risk_indicators 
           SET current_value = :value, last_updated = CURRENT_TIMESTAMP 
           WHERE id = :id""",
        {"id": kri_id, "value": value.value}
    )
    
    # Insert value history
    query = """
        INSERT INTO kri_values 
        (kri_id, value, period_date, notes, data_quality, recorded_by, created_at)
        VALUES (:kri_id, :value, :period_date, :notes, :data_quality, :recorded_by, CURRENT_TIMESTAMP)
        RETURNING id
    """
    
    result = db.execute(query, {
        "kri_id": kri_id,
        "value": value.value,
        "period_date": value.period_date,
        "notes": value.notes,
        "data_quality": value.data_quality,
        "recorded_by": current_user.id
    }).first()
    
    db.commit()
    
    # Check for threshold breaches and create alerts
    if value.value < kri['threshold_red']:
        alert_query = """
            INSERT INTO kri_alerts 
            (kri_id, alert_type, severity, message, created_at)
            VALUES (:kri_id, 'THRESHOLD_BREACH', 'CRITICAL', :message, CURRENT_TIMESTAMP)
        """
        db.execute(alert_query, {
            "kri_id": kri_id,
            "message": f"KRI '{kri['name']}' breached critical threshold. Value: {value.value}, Threshold: {kri['threshold_red']}"
        })
        db.commit()
    
    return {"message": "KRI value recorded successfully", "value_id": result['id']}

@router.get("/{kri_id}/trend", response_model=Dict[str, Any])
def get_kri_trend(
    kri_id: int,
    period_days: int = Query(90, description="Number of days for trend analysis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get trend analysis for a KRI"""
    
    query = """
        SELECT 
            kv.period_date,
            kv.value,
            kri.threshold_green,
            kri.threshold_amber,
            kri.threshold_red,
            kri.target_value
        FROM kri_values kv
        JOIN key_risk_indicators kri ON kv.kri_id = kri.id
        WHERE kv.kri_id = :kri_id
        AND kv.period_date >= CURRENT_DATE - INTERVAL ':period_days days'
        ORDER BY kv.period_date
    """
    
    result = db.execute(query, {"kri_id": kri_id, "period_days": period_days})
    values = [dict(row) for row in result]
    
    if not values:
        raise HTTPException(status_code=404, detail="No data available for trend analysis")
    
    # Calculate trend statistics
    trend_values = [v['value'] for v in values]
    avg_value = sum(trend_values) / len(trend_values)
    min_value = min(trend_values)
    max_value = max(trend_values)
    
    # Determine trend direction
    if len(trend_values) >= 2:
        recent_avg = sum(trend_values[-3:]) / len(trend_values[-3:])
        older_avg = sum(trend_values[:3]) / len(trend_values[:3])
        trend_direction = "Improving" if recent_avg > older_avg else "Declining" if recent_avg < older_avg else "Stable"
    else:
        trend_direction = "Insufficient data"
    
    return {
        "kri_id": kri_id,
        "period_days": period_days,
        "data_points": values,
        "statistics": {
            "average": avg_value,
            "minimum": min_value,
            "maximum": max_value,
            "trend": trend_direction,
            "data_points_count": len(values)
        },
        "generated_at": datetime.now()
    }

@router.post("/bulk-update", response_model=Dict[str, Any])
def bulk_update_kri_values(
    updates: List[KRIValue],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk update KRI values"""
    
    success_count = 0
    failed_updates = []
    
    for update in updates:
        try:
            # Check KRI exists
            kri = db.execute(
                "SELECT id FROM key_risk_indicators WHERE id = :id",
                {"id": update.kri_id}
            ).first()
            
            if not kri:
                failed_updates.append({
                    "kri_id": update.kri_id,
                    "error": "KRI not found"
                })
                continue
            
            # Update current value
            db.execute(
                """UPDATE key_risk_indicators 
                   SET current_value = :value, last_updated = CURRENT_TIMESTAMP 
                   WHERE id = :id""",
                {"id": update.kri_id, "value": update.value}
            )
            
            # Insert value history
            db.execute(
                """INSERT INTO kri_values 
                   (kri_id, value, period_date, notes, data_quality, recorded_by, created_at)
                   VALUES (:kri_id, :value, :period_date, :notes, :data_quality, :recorded_by, CURRENT_TIMESTAMP)""",
                {
                    "kri_id": update.kri_id,
                    "value": update.value,
                    "period_date": update.period_date,
                    "notes": update.notes,
                    "data_quality": update.data_quality,
                    "recorded_by": current_user.id
                }
            )
            
            success_count += 1
            
        except Exception as e:
            failed_updates.append({
                "kri_id": update.kri_id,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "success_count": success_count,
        "failed_count": len(failed_updates),
        "failed_updates": failed_updates,
        "timestamp": datetime.now()
    }