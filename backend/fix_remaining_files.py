#!/usr/bin/env python3
"""
Fix remaining files with errors
"""

import os

print("🔧 Fixing Remaining API Files")
print("=" * 50)

# 1. Fix compliance.py - add missing imports
print("\n📝 Fixing compliance.py...")
compliance_file = "app/api/v1/compliance.py"

with open(compliance_file, 'r') as f:
    content = f.read()

# Check if Dict import is missing
if "from typing import" not in content:
    # Add at the beginning after other imports
    lines = content.split('\n')
    import_added = False
    
    for i, line in enumerate(lines):
        if line.startswith('from ') and not import_added:
            lines.insert(i, 'from typing import Dict, List, Any, Optional')
            import_added = True
            break
    
    if not import_added:
        lines.insert(2, 'from typing import Dict, List, Any, Optional')
    
    content = '\n'.join(lines)
else:
    # Add Dict to existing typing import
    content = content.replace('from typing import', 'from typing import Dict, List, Any, Optional,')
    content = content.replace('from typing import Dict, List, Any, Optional, Dict', 'from typing import Dict, List, Any, Optional')

with open(compliance_file, 'w') as f:
    f.write(content)

print("✅ Fixed compliance.py imports")

# 2. Fix incidents.py - fix the syntax error at line 68
print("\n📝 Fixing incidents.py...")
incidents_file = "app/api/v1/incidents.py"

# Create a clean version of incidents.py
clean_incidents = '''from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
import random

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.incident import Incident, IncidentStatus, IncidentSeverity, IncidentType, IncidentTimelineEvent
from app.schemas.incident import IncidentCreate, IncidentUpdate, IncidentResponse, TimelineEventCreate

router = APIRouter()

@router.get("/", response_model=List[IncidentResponse])
def get_incidents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Incident]:
    """Get list of incidents"""
    incidents = db.query(Incident).offset(skip).limit(limit).all()
    return incidents

@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    incident: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Incident:
    """Create a new incident"""
    # Generate incident number
    incident_number = f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    
    db_incident = Incident(
        **incident.model_dump(),
        incident_number=incident_number,
        reporter_id=current_user.id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Incident:
    """Get specific incident"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.get("/{incident_id}/timeline", response_model=List[Dict[str, Any]])
def get_incident_timeline(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Get incident timeline"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    timeline_events = db.query(IncidentTimelineEvent).filter(
        IncidentTimelineEvent.incident_id == incident_id
    ).order_by(IncidentTimelineEvent.event_time.desc()).all()
    
    return [
        {
            "id": str(event.id),
            "event_time": event.event_time.isoformat(),
            "event_type": event.event_type,
            "description": event.description,
            "user": event.user.full_name if event.user else None
        } for event in timeline_events
    ]

@router.post("/{incident_id}/timeline", response_model=Dict[str, Any])
def add_timeline_event(
    incident_id: str,
    event: TimelineEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Add timeline event to incident"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    timeline_event = IncidentTimelineEvent(
        incident_id=incident_id,
        event_type=event.event_type,
        description=event.description,
        event_time=datetime.now(timezone.utc),
        user_id=current_user.id
    )
    db.add(timeline_event)
    db.commit()
    
    return {"message": "Timeline event added successfully"}

@router.patch("/{incident_id}/status", response_model=IncidentResponse)
def update_incident_status(
    incident_id: str,
    status_update: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Incident:
    """Update incident status"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    new_status = status_update.get("status")
    if new_status and hasattr(IncidentStatus, new_status):
        incident.status = IncidentStatus[new_status]
        incident.updated_at = datetime.now(timezone.utc)
        
        if incident.status in [IncidentStatus.resolved, IncidentStatus.closed]:
            incident.resolved_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(incident)
    
    return incident

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
    
    # Group by status
    by_status = {}
    for status in IncidentStatus:
        count = len([i for i in all_incidents if i.status == status])
        by_status[status.value] = count
    
    # Group by severity
    by_severity = {}
    for severity in IncidentSeverity:
        incidents = [i for i in all_incidents if i.severity == severity]
        by_severity[severity.value] = {
            "count": len(incidents),
            "recent": len([i for i in incidents if i in recent_incidents])
        }
    
    # Group by type
    by_type = {}
    for inc_type in IncidentType:
        count = len([i for i in all_incidents if i.incident_type == inc_type])
        if count > 0:
            by_type[inc_type.value] = count
    
    return {
        "total_incidents": len(all_incidents),
        "recent_incidents": len(recent_incidents),
        "period_days": days,
        "by_status": by_status,
        "by_severity": by_severity,
        "by_type": by_type
    }
'''

# Backup and write
if os.path.exists(incidents_file):
    with open(incidents_file + '.backup', 'w') as f:
        with open(incidents_file, 'r') as orig:
            f.write(orig.read())

with open(incidents_file, 'w') as f:
    f.write(clean_incidents)

print("✅ Fixed incidents.py")

# 3. Check if analytics.py was already fixed
analytics_file = "app/api/v1/analytics.py"
print("\n📝 Checking analytics.py...")

try:
    with open(analytics_file, 'r') as f:
        compile(f.read(), analytics_file, 'exec')
    print("✅ analytics.py is already fixed")
except SyntaxError as e:
    print(f"❌ analytics.py still has error at line {e.lineno}")
    print("Running simple_syntax_fix.py...")
    os.system("python simple_syntax_fix.py")

# 4. Final check
print("\n🧪 Final compilation check...")
files_to_check = [
    "app/api/v1/analytics.py",
    "app/api/v1/compliance.py",
    "app/api/v1/incidents.py"
]

all_good = True
for filepath in files_to_check:
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        print(f"✅ {filepath}")
    except Exception as e:
        print(f"❌ {filepath}: {str(e)}")
        all_good = False

if all_good:
    print("\n✅ All files fixed!")
    print("\nNow start the server:")
    print("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
else:
    print("\n⚠️ Some files still have issues")