from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from app.api.deps import get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class DepartmentBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    budget: Optional[float] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    budget: Optional[float] = None
    is_active: Optional[bool] = None

class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    level: int = 0
    full_path: str
    children_count: int = 0
    risk_count: int = 0

# Mock storage (in production, this would be in database)
department_storage: Dict[str, Dict[str, Any]] = {}

def calculate_department_level(dept_id: str) -> int:
    """Calculate department level in hierarchy"""
    if dept_id not in department_storage:
        return 0
    
    dept = department_storage[dept_id]
    if not dept.get('parent_id'):
        return 0
    
    return calculate_department_level(dept['parent_id']) + 1

def get_department_path(dept_id: str) -> str:
    """Get full path of department"""
    if dept_id not in department_storage:
        return ""
    
    dept = department_storage[dept_id]
    if not dept.get('parent_id'):
        return dept['name']
    
    parent_path = get_department_path(dept['parent_id'])
    return f"{parent_path} / {dept['name']}"

def count_children(dept_id: str) -> int:
    """Count direct children of department"""
    count = 0
    for dept in department_storage.values():
        if dept.get('parent_id') == dept_id:
            count += 1
    return count

@router.get("/", response_model=List[DepartmentResponse])
async def get_departments(
    parent_id: Optional[str] = None,
    include_inactive: bool = False,
    # current_user: User = Depends(get_current_active_user)
):
    """Get all departments with optional filtering"""
    try:
        departments = []
        for dept_id, dept_data in department_storage.items():
            # Filter by parent
            if parent_id is not None and dept_data.get('parent_id') != parent_id:
                continue
            
            # Filter by active status
            if not include_inactive and not dept_data.get('is_active', True):
                continue
            
            # Calculate additional fields
            dept_data['level'] = calculate_department_level(dept_id)
            dept_data['full_path'] = get_department_path(dept_id)
            dept_data['children_count'] = count_children(dept_id)
            dept_data['risk_count'] = 0  # TODO: Count risks assigned to department
            
            departments.append(dept_data)
        
        # Sort by name
        departments.sort(key=lambda x: x.get('name', ''))
        
        return departments
    except Exception as e:
        logger.error(f"Error getting departments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hierarchy")
async def get_department_hierarchy(
    # current_user: User = Depends(get_current_active_user)
):
    """Get complete department hierarchy tree"""
    try:
        def build_tree(parent_id: Optional[str] = None):
            children = []
            for dept_id, dept_data in department_storage.items():
                if dept_data.get('parent_id') == parent_id and dept_data.get('is_active', True):
                    dept_copy = dict(dept_data)
                    dept_copy['children'] = build_tree(dept_id)
                    dept_copy['level'] = calculate_department_level(dept_id)
                    dept_copy['full_path'] = get_department_path(dept_id)
                    children.append(dept_copy)
            
            children.sort(key=lambda x: x.get('name', ''))
            return children
        
        hierarchy = build_tree()
        
        return {
            "success": True,
            "data": hierarchy
        }
    except Exception as e:
        logger.error(f"Error getting department hierarchy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dept_id}", response_model=DepartmentResponse)
async def get_department(
    dept_id: str,
    # current_user: User = Depends(get_current_active_user)
):
    """Get specific department"""
    try:
        if dept_id not in department_storage:
            raise HTTPException(status_code=404, detail="Department not found")
        
        dept_data = department_storage[dept_id]
        dept_data['level'] = calculate_department_level(dept_id)
        dept_data['full_path'] = get_department_path(dept_id)
        dept_data['children_count'] = count_children(dept_id)
        dept_data['risk_count'] = 0  # TODO: Count risks assigned to department
        
        return dept_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting department {dept_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=DepartmentResponse)
async def create_department(
    department: DepartmentCreate,
    # current_user: User = Depends(get_current_active_user)
):
    """Create new department"""
    try:
        # Validate parent exists
        if department.parent_id and department.parent_id not in department_storage:
            raise HTTPException(status_code=400, detail="Parent department not found")
        
        # Check for duplicate code
        for dept in department_storage.values():
            if dept.get('code') == department.code:
                raise HTTPException(status_code=400, detail="Department code already exists")
        
        dept_id = str(uuid.uuid4())
        now = datetime.now()
        
        dept_data = {
            "id": dept_id,
            **department.dict(),
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "level": 0,
            "full_path": "",
            "children_count": 0,
            "risk_count": 0
        }
        
        department_storage[dept_id] = dept_data
        
        # Calculate additional fields after storage
        dept_data['level'] = calculate_department_level(dept_id)
        dept_data['full_path'] = get_department_path(dept_id)
        
        return dept_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating department: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: str,
    department_update: DepartmentUpdate,
    # current_user: User = Depends(get_current_active_user)
):
    """Update department"""
    try:
        if dept_id not in department_storage:
            raise HTTPException(status_code=404, detail="Department not found")
        
        dept_data = department_storage[dept_id]
        
        # Validate parent exists and prevent circular reference
        if department_update.parent_id:
            if department_update.parent_id not in department_storage:
                raise HTTPException(status_code=400, detail="Parent department not found")
            if department_update.parent_id == dept_id:
                raise HTTPException(status_code=400, detail="Department cannot be its own parent")
        
        # Check for duplicate code
        if department_update.code:
            for other_id, other_dept in department_storage.items():
                if other_id != dept_id and other_dept.get('code') == department_update.code:
                    raise HTTPException(status_code=400, detail="Department code already exists")
        
        # Update fields
        update_data = department_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                dept_data[field] = value
        
        dept_data["updated_at"] = datetime.now()
        
        # Recalculate additional fields
        dept_data['level'] = calculate_department_level(dept_id)
        dept_data['full_path'] = get_department_path(dept_id)
        dept_data['children_count'] = count_children(dept_id)
        
        department_storage[dept_id] = dept_data
        
        return dept_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating department {dept_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{dept_id}")
async def delete_department(
    dept_id: str,
    force: bool = False,
    # current_user: User = Depends(get_current_active_user)
):
    """Delete department (soft delete unless forced)"""
    try:
        if dept_id not in department_storage:
            raise HTTPException(status_code=404, detail="Department not found")
        
        # Check for children
        children_count = count_children(dept_id)
        if children_count > 0 and not force:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete department with {children_count} children. Use force=true to delete."
            )
        
        if force:
            del department_storage[dept_id]
            return {"message": "Department permanently deleted"}
        else:
            department_storage[dept_id]["is_active"] = False
            department_storage[dept_id]["updated_at"] = datetime.now()
            return {"message": "Department deactivated"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting department {dept_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dept_id}/children", response_model=List[DepartmentResponse])
async def get_department_children(
    dept_id: str,
    # current_user: User = Depends(get_current_active_user)
):
    """Get direct children of department"""
    try:
        if dept_id not in department_storage:
            raise HTTPException(status_code=404, detail="Department not found")
        
        children = []
        for child_id, child_data in department_storage.items():
            if child_data.get('parent_id') == dept_id and child_data.get('is_active', True):
                child_data['level'] = calculate_department_level(child_id)
                child_data['full_path'] = get_department_path(child_id)
                child_data['children_count'] = count_children(child_id)
                child_data['risk_count'] = 0  # TODO: Count risks
                children.append(child_data)
        
        children.sort(key=lambda x: x.get('name', ''))
        return children
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting department children {dept_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_department_stats():
    """Get department statistics"""
    try:
        total_departments = len([d for d in department_storage.values() if d.get('is_active', True)])
        
        # Count by level
        level_counts = {}
        location_counts = {}
        
        for dept in department_storage.values():
            if dept.get('is_active', True):
                level = calculate_department_level(dept['id'])
                level_counts[f"Level {level}"] = level_counts.get(f"Level {level}", 0) + 1
                
                location = dept.get('location', 'Unknown')
                location_counts[location] = location_counts.get(location, 0) + 1
        
        return {
            "success": True,
            "data": {
                "total_departments": total_departments,
                "level_breakdown": level_counts,
                "location_breakdown": location_counts,
                "active_departments": total_departments,
                "inactive_departments": len(department_storage) - total_departments
            }
        }
    except Exception as e:
        logger.error(f"Error getting department stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Initialize with NAPSA organizational structure
def init_napsa_departments():
    """Initialize with NAPSA organizational structure"""
    if not department_storage:
        napsa_departments = [
            # Executive Level
            {
                "id": "dir-001",
                "name": "Director General Office",
                "code": "DG",
                "description": "Office of the Director General",
                "parent_id": None,
                "manager_name": "Director General",
                "manager_email": "dg@napsa.co.zm",
                "location": "Head Office",
                "cost_center": "DG001",
                "budget": 50000000.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            },
            
            # Deputy Directors
            {
                "id": "dd-ops-001",
                "name": "Deputy Director Operations",
                "code": "DD-OPS",
                "description": "Operations and Member Services",
                "parent_id": "dir-001",
                "manager_name": "Deputy Director Operations",
                "manager_email": "dd.ops@napsa.co.zm",
                "location": "Head Office",
                "cost_center": "DD001",
                "budget": 30000000.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            },
            {
                "id": "dd-fin-001",
                "name": "Deputy Director Finance",
                "code": "DD-FIN",
                "description": "Finance and Investment Management",
                "parent_id": "dir-001",
                "manager_name": "Deputy Director Finance",
                "manager_email": "dd.finance@napsa.co.zm",
                "location": "Head Office",
                "cost_center": "DD002",
                "budget": 25000000.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            },
            
            # Operational Departments
            {
                "id": "dept-member-001",
                "name": "Member Services Department",
                "code": "MSD",
                "description": "Member registration, contributions, and benefits",
                "parent_id": "dd-ops-001",
                "manager_name": "Manager Member Services",
                "manager_email": "manager.members@napsa.co.zm",
                "location": "Head Office",
                "cost_center": "MSD001",
                "budget": 8000000.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            },
            {
                "id": "dept-it-001",
                "name": "Information Technology Department",
                "code": "ITD",
                "description": "IT infrastructure, systems, and cybersecurity",
                "parent_id": "dd-ops-001",
                "manager_name": "Manager IT",
                "manager_email": "manager.it@napsa.co.zm",
                "location": "Head Office",
                "cost_center": "ITD001",
                "budget": 12000000.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            },
            {
                "id": "dept-hr-001",
                "name": "Human Resources Department",
                "code": "HRD",
                "description": "Human resources and organizational development",
                "parent_id": "dd-ops-001",
                "manager_name": "Manager HR",
                "manager_email": "manager.hr@napsa.co.zm",
                "location": "Head Office",
                "cost_center": "HRD001",
                "budget": 6000000.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            },
            
            # Financial Departments
            {
                "id": "dept-finance-001",
                "name": "Finance Department",
                "code": "FIN",
                "description": "Financial management and accounting",
                "parent_id": "dd-fin-001",
                "manager_name": "Manager Finance",
                "manager_email": "manager.finance@napsa.co.zm",
                "location": "Head Office",
                "cost_center": "FIN001",
                "budget": 5000000.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            },
            {
                "id": "dept-invest-001",
                "name": "Investment Department",
                "code": "INV",
                "description": "Investment management and portfolio oversight",
                "parent_id": "dd-fin-001",
                "manager_name": "Manager Investments",
                "manager_email": "manager.investments@napsa.co.zm",
                "location": "Head Office",
                "cost_center": "INV001",
                "budget": 15000000.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            },
            
            # Support Departments
            {
                "id": "dept-legal-001",
                "name": "Legal Department",
                "code": "LEG",
                "description": "Legal affairs and compliance",
                "parent_id": "dir-001",
                "manager_name": "Manager Legal",
                "manager_email": "manager.legal@napsa.co.zm",
                "location": "Head Office",
                "cost_center": "LEG001",
                "budget": 3000000.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            },
            {
                "id": "dept-audit-001",
                "name": "Internal Audit Department",
                "code": "AUD",
                "description": "Internal audit and risk assurance",
                "parent_id": "dir-001",
                "manager_name": "Manager Internal Audit",
                "manager_email": "manager.audit@napsa.co.zm",
                "location": "Head Office",
                "cost_center": "AUD001",
                "budget": 4000000.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            },
            
            # Regional Offices
            {
                "id": "region-lsk-001",
                "name": "Lusaka Regional Office",
                "code": "LSK-REG",
                "description": "Regional operations for Lusaka Province",
                "parent_id": "dd-ops-001",
                "manager_name": "Regional Manager Lusaka",
                "manager_email": "regional.lusaka@napsa.co.zm",
                "location": "Lusaka",
                "cost_center": "LSK001",
                "budget": 4000000.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            },
            {
                "id": "region-cop-001",
                "name": "Copperbelt Regional Office",
                "code": "COP-REG",
                "description": "Regional operations for Copperbelt Province",
                "parent_id": "dd-ops-001",
                "manager_name": "Regional Manager Copperbelt",
                "manager_email": "regional.copperbelt@napsa.co.zm",
                "location": "Kitwe",
                "cost_center": "COP001",
                "budget": 3500000.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            }
        ]
        
        for dept_data in napsa_departments:
            department_storage[dept_data["id"]] = dept_data

# Initialize NAPSA departments
init_napsa_departments()