"""
Organizational Units CRUD API
Complete CRUD operations for NAPSA organizational structure
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_active_user
from app.models.user import User

router = APIRouter()

# Pydantic Models
class OrganizationalUnitBase(BaseModel):
    unit_code: str = Field(..., max_length=20)
    unit_name: str = Field(..., max_length=255)
    unit_type: str = Field(..., pattern="^(Executive|Directorate|Department|Unit|Station|Section)$")
    parent_id: Optional[int] = None
    level: int = Field(ge=1, le=5)
    description: Optional[str] = None
    risk_appetite: str = Field(default="moderate", pattern="^(conservative|moderate|aggressive)$")
    review_frequency: str = Field(default="monthly", pattern="^(daily|weekly|monthly|quarterly|annually)$")
    location: Optional[str] = None
    contact_info: Optional[str] = None

class OrganizationalUnitCreate(OrganizationalUnitBase):
    pass

class OrganizationalUnitUpdate(BaseModel):
    unit_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    risk_appetite: Optional[str] = Field(None, pattern="^(conservative|moderate|aggressive)$")
    review_frequency: Optional[str] = Field(None, pattern="^(daily|weekly|monthly|quarterly|annually)$")
    location: Optional[str] = None
    contact_info: Optional[str] = None
    parent_id: Optional[int] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")

class OrganizationalUnitResponse(OrganizationalUnitBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# CRUD Endpoints

@router.get("/", response_model=List[Dict[str, Any]])
def get_organizational_units(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    unit_type: Optional[str] = Query(None, description="Filter by unit type"),
    parent_id: Optional[int] = Query(None, description="Filter by parent unit"),
    status: Optional[str] = Query("active", description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in unit name and description"),
    include_hierarchy: bool = Query(False, description="Include full hierarchy path"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all organizational units with filtering and pagination"""
    
    base_query = """
        SELECT 
            ou.*,
            parent.unit_name as parent_name,
            COUNT(DISTINCT children.id) as child_count,
            COUNT(DISTINCT r.id) as risk_count,
            AVG(r.inherent_risk_score) as avg_risk_score
        FROM organizational_units ou
        LEFT JOIN organizational_units parent ON ou.parent_id = parent.id
        LEFT JOIN organizational_units children ON children.parent_id = ou.id
        LEFT JOIN risks r ON r.organizational_unit_id = ou.id
        WHERE 1=1
    """
    
    params = {"skip": skip, "limit": limit}
    
    if unit_type:
        base_query += " AND ou.unit_type = :unit_type"
        params["unit_type"] = unit_type
    
    if parent_id is not None:
        base_query += " AND ou.parent_id = :parent_id"
        params["parent_id"] = parent_id
    
    if status:
        base_query += " AND ou.status = :status"
        params["status"] = status
    
    if search:
        base_query += " AND (ou.unit_name ILIKE :search OR ou.description ILIKE :search)"
        params["search"] = f"%{search}%"
    
    base_query += """
        GROUP BY ou.id, parent.unit_name
        ORDER BY ou.level, ou.unit_name
        LIMIT :limit OFFSET :skip
    """
    
    result = db.execute(base_query, params)
    units = []
    
    for row in result:
        unit = dict(row)
        
        if include_hierarchy:
            # Get full hierarchy path
            hierarchy_query = """
                WITH RECURSIVE hierarchy AS (
                    SELECT id, unit_name, parent_id, unit_name::VARCHAR(500) as path
                    FROM organizational_units
                    WHERE id = :unit_id
                    
                    UNION ALL
                    
                    SELECT ou.id, ou.unit_name, ou.parent_id, 
                           (ou.unit_name || ' > ' || h.path)::VARCHAR(500)
                    FROM organizational_units ou
                    JOIN hierarchy h ON ou.id = h.parent_id
                )
                SELECT path FROM hierarchy
                WHERE parent_id IS NULL
            """
            hierarchy_result = db.execute(hierarchy_query, {"unit_id": unit['id']}).first()
            if hierarchy_result:
                unit['hierarchy_path'] = hierarchy_result['path']
        
        units.append(unit)
    
    return units

@router.get("/tree", response_model=List[Dict[str, Any]])
def get_organizational_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get organizational units in tree structure"""
    
    query = """
        WITH RECURSIVE org_tree AS (
            SELECT 
                id, unit_code, unit_name, unit_type, parent_id, level,
                description, risk_appetite, location, status,
                ARRAY[id] as path,
                0 as depth
            FROM organizational_units
            WHERE parent_id IS NULL
            
            UNION ALL
            
            SELECT 
                ou.id, ou.unit_code, ou.unit_name, ou.unit_type, ou.parent_id, ou.level,
                ou.description, ou.risk_appetite, ou.location, ou.status,
                ot.path || ou.id,
                ot.depth + 1
            FROM organizational_units ou
            JOIN org_tree ot ON ou.parent_id = ot.id
        )
        SELECT * FROM org_tree
        ORDER BY path
    """
    
    result = db.execute(query)
    
    # Build tree structure
    units_dict = {}
    root_units = []
    
    for row in result:
        unit = dict(row)
        unit['children'] = []
        units_dict[unit['id']] = unit
        
        if unit['parent_id'] is None:
            root_units.append(unit)
        elif unit['parent_id'] in units_dict:
            units_dict[unit['parent_id']]['children'].append(unit)
    
    return root_units

@router.get("/{unit_id}", response_model=Dict[str, Any])
def get_organizational_unit(
    unit_id: int,
    include_children: bool = Query(False, description="Include child units"),
    include_risks: bool = Query(False, description="Include associated risks"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific organizational unit"""
    
    query = """
        SELECT 
            ou.*,
            parent.unit_name as parent_name,
            COUNT(DISTINCT children.id) as child_count,
            COUNT(DISTINCT r.id) as risk_count,
            AVG(r.inherent_risk_score) as avg_risk_score,
            MAX(r.inherent_risk_score) as max_risk_score
        FROM organizational_units ou
        LEFT JOIN organizational_units parent ON ou.parent_id = parent.id
        LEFT JOIN organizational_units children ON children.parent_id = ou.id
        LEFT JOIN risks r ON r.organizational_unit_id = ou.id
        WHERE ou.id = :unit_id
        GROUP BY ou.id, parent.unit_name
    """
    
    result = db.execute(query, {"unit_id": unit_id}).first()
    if not result:
        raise HTTPException(status_code=404, detail="Organizational unit not found")
    
    unit = dict(result)
    
    if include_children:
        children_query = """
            SELECT id, unit_code, unit_name, unit_type, status
            FROM organizational_units
            WHERE parent_id = :unit_id
            ORDER BY unit_name
        """
        children = db.execute(children_query, {"unit_id": unit_id})
        unit['children'] = [dict(child) for child in children]
    
    if include_risks:
        risks_query = """
            SELECT id, title, category, inherent_risk_score, residual_risk_score, status
            FROM risks
            WHERE organizational_unit_id = :unit_id
            ORDER BY inherent_risk_score DESC
            LIMIT 10
        """
        risks = db.execute(risks_query, {"unit_id": unit_id})
        unit['top_risks'] = [dict(risk) for risk in risks]
    
    return unit

@router.post("/", response_model=OrganizationalUnitResponse, status_code=status.HTTP_201_CREATED)
def create_organizational_unit(
    unit: OrganizationalUnitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new organizational unit"""
    
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to create organizational units")
    
    # Check if unit_code already exists
    existing = db.execute(
        "SELECT id FROM organizational_units WHERE unit_code = :code",
        {"code": unit.unit_code}
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Unit code already exists")
    
    # Validate parent exists if provided
    if unit.parent_id:
        parent = db.execute(
            "SELECT id, level FROM organizational_units WHERE id = :id",
            {"id": unit.parent_id}
        ).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent unit not found")
    
    query = """
        INSERT INTO organizational_units 
        (unit_code, unit_name, unit_type, parent_id, level, description, 
         risk_appetite, review_frequency, location, contact_info, status)
        VALUES (:unit_code, :unit_name, :unit_type, :parent_id, :level, :description,
                :risk_appetite, :review_frequency, :location, :contact_info, 'active')
        RETURNING *
    """
    
    result = db.execute(query, unit.dict()).first()
    db.commit()
    
    return dict(result)

@router.put("/{unit_id}", response_model=OrganizationalUnitResponse)
def update_organizational_unit(
    unit_id: int,
    unit_update: OrganizationalUnitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an organizational unit"""
    
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to update organizational units")
    
    # Check unit exists
    existing = db.execute(
        "SELECT * FROM organizational_units WHERE id = :id",
        {"id": unit_id}
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Organizational unit not found")
    
    # Build update query dynamically
    update_fields = []
    params = {"unit_id": unit_id}
    
    for field, value in unit_update.dict(exclude_unset=True).items():
        if value is not None:
            update_fields.append(f"{field} = :{field}")
            params[field] = value
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Validate parent if changing
    if unit_update.parent_id is not None:
        if unit_update.parent_id == unit_id:
            raise HTTPException(status_code=400, detail="Unit cannot be its own parent")
        
        # Check for circular reference
        circular_check = """
            WITH RECURSIVE parents AS (
                SELECT id, parent_id FROM organizational_units WHERE id = :parent_id
                UNION ALL
                SELECT ou.id, ou.parent_id 
                FROM organizational_units ou
                JOIN parents p ON ou.id = p.parent_id
            )
            SELECT 1 FROM parents WHERE id = :unit_id
        """
        circular = db.execute(circular_check, {
            "parent_id": unit_update.parent_id,
            "unit_id": unit_id
        }).first()
        
        if circular:
            raise HTTPException(status_code=400, detail="Circular reference detected")
    
    query = f"""
        UPDATE organizational_units 
        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = :unit_id
        RETURNING *
    """
    
    result = db.execute(query, params).first()
    db.commit()
    
    return dict(result)

@router.delete("/{unit_id}")
def delete_organizational_unit(
    unit_id: int,
    cascade: bool = Query(False, description="Cascade delete to children"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an organizational unit"""
    
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete organizational units")
    
    # Check if unit exists
    existing = db.execute(
        "SELECT * FROM organizational_units WHERE id = :id",
        {"id": unit_id}
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Organizational unit not found")
    
    # Check for children
    children = db.execute(
        "SELECT COUNT(*) as count FROM organizational_units WHERE parent_id = :id",
        {"id": unit_id}
    ).first()
    
    if children['count'] > 0 and not cascade:
        raise HTTPException(
            status_code=400,
            detail=f"Unit has {children['count']} child units. Use cascade=true to delete all"
        )
    
    # Check for associated risks
    risks = db.execute(
        "SELECT COUNT(*) as count FROM risks WHERE organizational_unit_id = :id",
        {"id": unit_id}
    ).first()
    
    if risks['count'] > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Unit has {risks['count']} associated risks. Reassign risks before deletion"
        )
    
    if cascade:
        # Delete children first
        db.execute(
            "DELETE FROM organizational_units WHERE parent_id = :id",
            {"id": unit_id}
        )
    
    # Delete the unit
    db.execute(
        "DELETE FROM organizational_units WHERE id = :id",
        {"id": unit_id}
    )
    db.commit()
    
    return {"message": "Organizational unit deleted successfully"}

@router.post("/{unit_id}/move")
def move_organizational_unit(
    unit_id: int,
    new_parent_id: Optional[int] = Body(None, description="New parent ID (null for root)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Move an organizational unit to a different parent"""
    
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to move organizational units")
    
    # Validate unit exists
    unit = db.execute(
        "SELECT * FROM organizational_units WHERE id = :id",
        {"id": unit_id}
    ).first()
    
    if not unit:
        raise HTTPException(status_code=404, detail="Organizational unit not found")
    
    # Validate new parent if provided
    if new_parent_id:
        if new_parent_id == unit_id:
            raise HTTPException(status_code=400, detail="Unit cannot be its own parent")
        
        new_parent = db.execute(
            "SELECT id, level FROM organizational_units WHERE id = :id",
            {"id": new_parent_id}
        ).first()
        
        if not new_parent:
            raise HTTPException(status_code=400, detail="New parent unit not found")
        
        # Check for circular reference
        circular_check = """
            WITH RECURSIVE descendants AS (
                SELECT id FROM organizational_units WHERE id = :unit_id
                UNION ALL
                SELECT ou.id FROM organizational_units ou
                JOIN descendants d ON ou.parent_id = d.id
            )
            SELECT 1 FROM descendants WHERE id = :new_parent_id
        """
        circular = db.execute(circular_check, {
            "unit_id": unit_id,
            "new_parent_id": new_parent_id
        }).first()
        
        if circular:
            raise HTTPException(status_code=400, detail="Moving would create circular reference")
        
        new_level = new_parent['level'] + 1
    else:
        new_level = 1
    
    # Update the unit and all descendants' levels
    update_query = """
        WITH RECURSIVE affected_units AS (
            SELECT id, :new_level as new_level
            FROM organizational_units WHERE id = :unit_id
            
            UNION ALL
            
            SELECT ou.id, au.new_level + 1
            FROM organizational_units ou
            JOIN affected_units au ON ou.parent_id = au.id
        )
        UPDATE organizational_units
        SET parent_id = :new_parent_id,
            level = au.new_level,
            updated_at = CURRENT_TIMESTAMP
        FROM affected_units au
        WHERE organizational_units.id = au.id
    """
    
    db.execute(update_query, {
        "unit_id": unit_id,
        "new_parent_id": new_parent_id,
        "new_level": new_level
    })
    db.commit()
    
    return {"message": "Organizational unit moved successfully"}

@router.get("/{unit_id}/statistics", response_model=Dict[str, Any])
def get_unit_statistics(
    unit_id: int,
    include_descendants: bool = Query(False, description="Include statistics from descendant units"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive statistics for an organizational unit"""
    
    if include_descendants:
        units_query = """
            WITH RECURSIVE unit_tree AS (
                SELECT id FROM organizational_units WHERE id = :unit_id
                UNION ALL
                SELECT ou.id FROM organizational_units ou
                JOIN unit_tree ut ON ou.parent_id = ut.id
            )
            SELECT array_agg(id) as unit_ids FROM unit_tree
        """
        result = db.execute(units_query, {"unit_id": unit_id}).first()
        unit_ids = result['unit_ids']
    else:
        unit_ids = [unit_id]
    
    stats_query = """
        SELECT 
            COUNT(DISTINCT r.id) as total_risks,
            COUNT(DISTINCT r.id) FILTER (WHERE r.status = 'active') as active_risks,
            COUNT(DISTINCT r.id) FILTER (WHERE r.inherent_risk_score >= 15) as high_risks,
            AVG(r.inherent_risk_score) as avg_inherent_score,
            AVG(r.residual_risk_score) as avg_residual_score,
            COUNT(DISTINCT c.id) as total_controls,
            COUNT(DISTINCT i.id) as total_incidents,
            COUNT(DISTINCT kri.id) as total_kris,
            COUNT(DISTINCT ra.id) as total_assessments
        FROM organizational_units ou
        LEFT JOIN risks r ON r.organizational_unit_id = ANY(:unit_ids)
        LEFT JOIN control_risk_associations cra ON cra.risk_id = r.id
        LEFT JOIN controls c ON c.id = cra.control_id
        LEFT JOIN incidents i ON i.department = ou.unit_name
        LEFT JOIN key_risk_indicators kri ON kri.department = ou.unit_name
        LEFT JOIN risk_assessments ra ON ra.risk_id = r.id
        WHERE ou.id = ANY(:unit_ids)
    """
    
    stats = db.execute(stats_query, {"unit_ids": unit_ids}).first()
    
    return {
        "unit_id": unit_id,
        "include_descendants": include_descendants,
        "statistics": dict(stats),
        "generated_at": datetime.now()
    }