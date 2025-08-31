#!/usr/bin/env python3
"""
Fix the controls.py file by rewriting the problematic section
"""

import os

# Read the current controls.py file
controls_file = "app/api/v1/controls.py"

print(f"🔧 Fixing {controls_file}...")

# Read the file
with open(controls_file, 'r') as f:
    lines = f.readlines()

# Find the problematic line (line 67 with the indentation error)
print(f"📝 Locating error at line 67...")

# Check what's around line 67
for i in range(max(0, 66-5), min(len(lines), 67+5)):
    print(f"{i+1}: {repr(lines[i])}")

# The issue is likely in the map-to-risk endpoint
# Let's rewrite the entire file with proper structure

new_content = '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.control import Control, ControlType, ControlStatus
from app.schemas.control import ControlCreate, ControlUpdate, ControlResponse
from app.models.risk import Risk, RiskControl

router = APIRouter()

@router.get("/", response_model=List[ControlResponse])
def get_controls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
        **control.model_dump(),
        created_by_id=current_user.id
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
    
    # Create the mapping
    risk_control = RiskControl(
        risk_id=risk_id,
        control_id=control_id
    )
    db.add(risk_control)
    db.commit()
    
    return {
        "message": "Control successfully mapped to risk",
        "risk_id": str(risk_id),
        "control_id": str(control_id),
        "risk_title": risk.title,
        "control_name": control.name
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
    controls_with_effectiveness = [c for c in controls if c.effectiveness is not None]
    if controls_with_effectiveness:
        total_effectiveness = sum(c.effectiveness for c in controls_with_effectiveness)
        avg_effectiveness = total_effectiveness / len(controls_with_effectiveness)
    else:
        avg_effectiveness = 0
    
    # Group by type
    by_type = {}
    for control_type in ControlType:
        type_controls = [c for c in controls if c.control_type == control_type]
        if type_controls:
            type_controls_with_eff = [c for c in type_controls if c.effectiveness is not None]
            if type_controls_with_eff:
                type_effectiveness = sum(c.effectiveness for c in type_controls_with_eff)
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
        status_controls = [c for c in controls if c.implementation_status == status]
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
        "highly_effective": len([c for c in controls if c.effectiveness and c.effectiveness >= 80]),
        "needs_improvement": len([c for c in controls if c.effectiveness and c.effectiveness < 60])
    }
'''

# Write the fixed content
with open(controls_file, 'w') as f:
    f.write(new_content)

print("✅ Fixed controls.py")

# Now let's also check and fix the incidents.py file
incidents_file = "app/api/v1/incidents.py"
if os.path.exists(incidents_file):
    print(f"\n🔧 Checking {incidents_file}...")
    
    with open(incidents_file, 'r') as f:
        content = f.read()
    
    # If the stats endpoint is missing or malformed, add it
    if "@router.get(\"/stats\"" not in content:
        print("📝 Adding missing stats endpoint...")
        
        # Find where to insert (before the last line or after the last endpoint)
        lines = content.split('\n')
        insert_position = len(lines) - 1
        
        # Find the last router definition
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('@router.'):
                # Find the end of this function
                for j in range(i + 1, len(lines)):
                    if j < len(lines) - 1 and lines[j].strip() and not lines[j].startswith(' '):
                        insert_position = j
                        break
                break
        
        stats_endpoint = '''
@router.get("/stats", response_model=Dict[str, Any])
def get_incident_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days: int = Query(30, description="Number of days to analyze")
) -> Dict[str, Any]:
    """Get incident statistics and trends"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    all_incidents = db.query(Incident).all()
    recent_incidents = [i for i in all_incidents if i.created_at >= cutoff_date]
    
    stats = {
        "total_incidents": len(all_incidents),
        "recent_incidents": len(recent_incidents),
        "period_days": days,
        "by_status": {},
        "by_severity": {},
        "by_type": {},
        "by_department": {},
        "resolution_metrics": {},
        "trends": {}
    }
    
    # Group by status
    for status in IncidentStatus:
        count = len([i for i in all_incidents if i.status == status])
        stats["by_status"][status.value] = count
    
    # Group by severity
    for severity in IncidentSeverity:
        incidents = [i for i in all_incidents if i.severity == severity]
        stats["by_severity"][severity.value] = {
            "count": len(incidents),
            "recent": len([i for i in incidents if i in recent_incidents])
        }
    
    # Group by type
    for inc_type in IncidentType:
        count = len([i for i in all_incidents if i.incident_type == inc_type])
        if count > 0:
            stats["by_type"][inc_type.value] = count
    
    # Group by department
    departments = set(i.department for i in all_incidents if i.department)
    for dept in departments:
        stats["by_department"][dept] = len([i for i in all_incidents if i.department == dept])
    
    # Calculate resolution metrics
    resolved_incidents = [i for i in all_incidents if i.status in [IncidentStatus.resolved, IncidentStatus.closed]]
    if resolved_incidents:
        resolution_times = []
        for incident in resolved_incidents:
            if hasattr(incident, 'resolved_at') and incident.resolved_at and incident.created_at:
                resolution_time = (incident.resolved_at - incident.created_at).total_seconds() / 3600
                resolution_times.append(resolution_time)
        
        if resolution_times:
            stats["resolution_metrics"] = {
                "average_hours": round(sum(resolution_times) / len(resolution_times), 2),
                "min_hours": round(min(resolution_times), 2),
                "max_hours": round(max(resolution_times), 2),
                "resolved_count": len(resolved_incidents)
            }
    
    # Calculate trends
    previous_cutoff = cutoff_date - timedelta(days=days)
    previous_incidents = [i for i in all_incidents if previous_cutoff <= i.created_at < cutoff_date]
    
    stats["trends"] = {
        "current_period": len(recent_incidents),
        "previous_period": len(previous_incidents),
        "change_percentage": round(((len(recent_incidents) - len(previous_incidents)) / len(previous_incidents) * 100) if previous_incidents else 0, 2)
    }
    
    return stats'''
        
        lines.insert(insert_position, stats_endpoint)
        
        with open(incidents_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print("✅ Added stats endpoint to incidents.py")

print("\n✅ All fixes applied!")
print("Now you can restart the server.")
