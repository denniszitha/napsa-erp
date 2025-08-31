#!/usr/bin/env python3
"""
Clean implementation of all missing endpoints for NAPSA ERM API
This script will add the missing endpoints one by one with proper error handling
"""

import os
import re

def add_imports_to_file(filepath, imports):
    """Add imports to a file if they don't exist"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find the last import line
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('from ') or line.strip().startswith('import '):
            last_import_idx = i
    
    # Add imports after the last import
    for imp in imports:
        if imp not in content:
            lines.insert(last_import_idx + 1, imp)
            last_import_idx += 1
            print(f"  ✅ Added import: {imp}")
    
    with open(filepath, 'w') as f:
        f.write('\n'.join(lines))
    
    return True

def append_endpoint_to_file(filepath, endpoint_code):
    """Append endpoint code to the end of a file"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    with open(filepath, 'a') as f:
        f.write('\n\n' + endpoint_code)
    
    return True

print("🚀 Implementing Missing Endpoints for NAPSA ERM API")
print("=" * 60)

# 1. Controls - Add effectiveness endpoint
print("\n📁 Controls Module")
print("-" * 40)

controls_file = "app/api/v1/controls.py"

# First, fix the imports
print(f"Fixing imports in {controls_file}...")
with open(controls_file, 'r') as f:
    content = f.read()

# Fix RiskControl import
if "from app.models.risk import Risk, RiskControl" in content:
    content = content.replace(
        "from app.models.risk import Risk, RiskControl",
        "from app.models.risk import Risk\nfrom app.models.control import RiskControl"
    )
    with open(controls_file, 'w') as f:
        f.write(content)
    print("  ✅ Fixed RiskControl import")

# Add required imports
add_imports_to_file(controls_file, [
    "from typing import Dict, Any, List",
    "from app.models.control import Control, ControlType, ControlStatus, RiskControl"
])

# Add effectiveness endpoint
effectiveness_endpoint = '''@router.get("/effectiveness", response_model=Dict[str, Any])
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
    
    # Calculate metrics
    controls_with_eff = [c for c in controls if c.effectiveness is not None]
    avg_effectiveness = sum(c.effectiveness for c in controls_with_eff) / len(controls_with_eff) if controls_with_eff else 0
    
    # Group by type
    by_type = {}
    for control_type in ControlType:
        typed = [c for c in controls if c.control_type == control_type]
        if typed:
            typed_with_eff = [c for c in typed if c.effectiveness is not None]
            by_type[control_type.value] = {
                "count": len(typed),
                "average_effectiveness": round(sum(c.effectiveness for c in typed_with_eff) / len(typed_with_eff), 2) if typed_with_eff else 0
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
    }'''

# Check if endpoint already exists
with open(controls_file, 'r') as f:
    if '/effectiveness' not in f.read():
        append_endpoint_to_file(controls_file, effectiveness_endpoint)
        print("✅ Added /effectiveness endpoint")

# 2. KRIs - Add breached and dashboard endpoints
print("\n📁 KRI Module")
print("-" * 40)

kris_file = "app/api/v1/kris.py"

# Add required imports
add_imports_to_file(kris_file, [
    "from datetime import datetime, timedelta, timezone",
    "from typing import Dict, Any, List"
])

# Add breached endpoint
breached_endpoint = '''@router.get("/breached", response_model=List[Dict[str, Any]])
def get_breached_kris(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Get all KRIs that have breached their thresholds"""
    kris = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.status == KRIStatus.breached).all()
    
    breached_list = []
    for kri in kris:
        latest = db.query(KRIMeasurement).filter(KRIMeasurement.kri_id == kri.id).order_by(KRIMeasurement.measurement_date.desc()).first()
        
        breached_list.append({
            "id": str(kri.id),
            "name": kri.name,
            "current_value": kri.current_value,
            "threshold_upper": kri.threshold_upper,
            "threshold_lower": kri.threshold_lower,
            "breach_type": "upper" if kri.current_value > kri.threshold_upper else "lower",
            "risk_id": str(kri.risk_id),
            "owner": kri.owner.full_name if kri.owner else None,
            "latest_measurement": {
                "value": latest.value,
                "date": latest.measurement_date.isoformat()
            } if latest else None
        })
    
    return breached_list'''

# Add dashboard endpoint  
dashboard_endpoint = '''@router.get("/dashboard", response_model=Dict[str, Any])
def get_kri_dashboard_detailed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get detailed KRI dashboard"""
    kris = db.query(KeyRiskIndicator).all()
    
    total = len(kris)
    active = len([k for k in kris if k.status == KRIStatus.active])
    breached = len([k for k in kris if k.status == KRIStatus.breached])
    warning = len([k for k in kris if k.status == KRIStatus.warning])
    
    return {
        "summary": {
            "total": total,
            "active": active,
            "breached": breached,
            "warning": warning
        },
        "health_score": round((active - breached) / total * 100, 2) if total > 0 else 0
    }'''

with open(kris_file, 'r') as f:
    content = f.read()
    if '/breached' not in content:
        append_endpoint_to_file(kris_file, breached_endpoint)
        print("✅ Added /breached endpoint")
    if '/dashboard"' not in content and '/dashboard\'' not in content:
        append_endpoint_to_file(kris_file, dashboard_endpoint)
        print("✅ Added /dashboard endpoint")

# 3. Incidents - Add stats endpoint
print("\n📁 Incidents Module")
print("-" * 40)

incidents_file = "app/api/v1/incidents.py"

# Add required imports
add_imports_to_file(incidents_file, [
    "from datetime import datetime, timedelta, timezone",
    "from typing import Dict, Any, List",
    "from fastapi import Query"
])

# Add stats endpoint
stats_endpoint = '''@router.get("/stats", response_model=Dict[str, Any])
def get_incident_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days: int = Query(30, description="Number of days to analyze")
) -> Dict[str, Any]:
    """Get incident statistics"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    all_incidents = db.query(Incident).all()
    recent = [i for i in all_incidents if i.created_at >= cutoff_date]
    
    # Group by status
    by_status = {}
    for status in IncidentStatus:
        by_status[status.value] = len([i for i in all_incidents if i.status == status])
    
    # Group by severity
    by_severity = {}
    for severity in IncidentSeverity:
        incidents = [i for i in all_incidents if i.severity == severity]
        by_severity[severity.value] = {
            "count": len(incidents),
            "recent": len([i for i in incidents if i in recent])
        }
    
    return {
        "total_incidents": len(all_incidents),
        "recent_incidents": len(recent),
        "period_days": days,
        "by_status": by_status,
        "by_severity": by_severity
    }'''

with open(incidents_file, 'r') as f:
    if '/stats' not in f.read():
        append_endpoint_to_file(incidents_file, stats_endpoint)
        print("✅ Added /stats endpoint")

# 4. Compliance - Add frameworks and status endpoints
print("\n📁 Compliance Module")
print("-" * 40)

compliance_file = "app/api/v1/compliance.py"

# Add required imports
add_imports_to_file(compliance_file, [
    "from typing import Dict, Any, List, Optional",
    "from datetime import datetime, timezone"
])

# Add frameworks endpoint
frameworks_endpoint = '''@router.get("/frameworks", response_model=List[Dict[str, Any]])
def get_compliance_frameworks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Get list of compliance frameworks"""
    return [
        {
            "id": "ISO27001",
            "name": "ISO 27001:2013",
            "description": "Information Security Management System",
            "categories": ["Information Security", "Risk Management"],
            "total_requirements": 114
        },
        {
            "id": "NIST",
            "name": "NIST Cybersecurity Framework",
            "description": "Framework for Improving Critical Infrastructure Cybersecurity",
            "categories": ["Cybersecurity", "Risk Management"],
            "total_requirements": 108
        },
        {
            "id": "COBIT",
            "name": "COBIT 2019",
            "description": "Control Objectives for Information and Related Technologies",
            "categories": ["IT Governance", "Risk Management"],
            "total_requirements": 40
        }
    ]'''

# Add status endpoint
status_endpoint = '''@router.get("/status", response_model=Dict[str, Any])
def get_compliance_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get overall compliance status"""
    requirements = db.query(ComplianceRequirement).all()
    mappings = db.query(ComplianceMapping).all()
    
    total_reqs = len(requirements)
    mapped_reqs = len(set(m.requirement_id for m in mappings))
    
    return {
        "overall_compliance": round((mapped_reqs / total_reqs) * 100, 2) if total_reqs else 0,
        "total_requirements": total_reqs,
        "mapped_requirements": mapped_reqs,
        "compliance_gaps": total_reqs - mapped_reqs
    }'''

with open(compliance_file, 'r') as f:
    content = f.read()
    if '/frameworks' not in content:
        append_endpoint_to_file(compliance_file, frameworks_endpoint)
        print("✅ Added /frameworks endpoint")
    if '/status"' not in content and '/status\'' not in content:
        append_endpoint_to_file(compliance_file, status_endpoint)
        print("✅ Added /status endpoint")

# Continue with other modules...
print("\n✅ Basic endpoints added successfully!")
print("\nTo add the remaining endpoints, run: python implement_remaining_endpoints.py")

# Create a test script
test_script = '''#!/bin/bash
# Test the newly added endpoints

echo "Testing new endpoints..."

# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "username=admin&password=admin123&grant_type=password" | \\
  python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

# Test each endpoint
echo "Controls /effectiveness:"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/controls/effectiveness | python3 -m json.tool | head -10

echo -e "\\nKRIs /breached:"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/kris/breached | python3 -m json.tool | head -10

echo -e "\\nKRIs /dashboard:"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/kris/dashboard | python3 -m json.tool | head -10

echo -e "\\nIncidents /stats:"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/incidents/stats | python3 -m json.tool | head -10

echo -e "\\nCompliance /frameworks:"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/compliance/frameworks | python3 -m json.tool | head -10

echo -e "\\nCompliance /status:"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/compliance/status | python3 -m json.tool | head -10
'''

with open('test_new_endpoints.sh', 'w') as f:
    f.write(test_script)

print("\n📝 Created test_new_endpoints.sh")
print("Run: chmod +x test_new_endpoints.sh && ./test_new_endpoints.sh")
