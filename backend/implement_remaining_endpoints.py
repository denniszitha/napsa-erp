#!/usr/bin/env python3
"""
Implement the remaining missing endpoints for NAPSA ERM API
"""

import os

def add_imports_to_file(filepath, imports):
    """Add imports to a file if they don't exist"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    last_import_idx = 0
    
    for i, line in enumerate(lines):
        if line.strip().startswith('from ') or line.strip().startswith('import '):
            last_import_idx = i
    
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

print("🚀 Implementing Remaining Missing Endpoints")
print("=" * 60)

# 1. Analytics - Add 4 missing endpoints
print("\n📁 Analytics Module")
print("-" * 40)

analytics_file = "app/api/v1/analytics.py"

# Add required imports
add_imports_to_file(analytics_file, [
    "from typing import Dict, Any, List, Optional",
    "from datetime import datetime, timedelta, timezone",
    "from fastapi import Query"
])

# Risk Summary endpoint
risk_summary = '''@router.get("/risk-summary", response_model=Dict[str, Any])
def get_risk_summary_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get comprehensive risk summary"""
    risks = db.query(Risk).all()
    
    if not risks:
        return {"total_risks": 0, "average_risk_score": 0}
    
    risk_scores = [(r.likelihood or 0) * (r.impact or 0) for r in risks]
    
    # Top risks
    sorted_risks = sorted(risks, key=lambda r: (r.likelihood or 0) * (r.impact or 0), reverse=True)[:5]
    top_risks = [
        {
            "id": str(r.id),
            "title": r.title,
            "score": (r.likelihood or 0) * (r.impact or 0),
            "category": r.category.value if r.category else None
        } for r in sorted_risks
    ]
    
    return {
        "total_risks": len(risks),
        "average_risk_score": round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else 0,
        "high_risks": len([s for s in risk_scores if s >= 15]),
        "medium_risks": len([s for s in risk_scores if 10 <= s < 15]),
        "low_risks": len([s for s in risk_scores if s < 10]),
        "top_risks": top_risks
    }'''

# Department Risks endpoint
dept_risks = '''@router.get("/department-risks", response_model=Dict[str, Any])
def get_department_risk_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    department: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Get risk analytics by department"""
    query = db.query(Risk)
    if department:
        query = query.filter(Risk.department == department)
    
    risks = query.all()
    departments = {}
    
    for risk in risks:
        if risk.department:
            if risk.department not in departments:
                departments[risk.department] = {
                    "total_risks": 0,
                    "high_risks": 0,
                    "total_score": 0
                }
            
            score = (risk.likelihood or 0) * (risk.impact or 0)
            departments[risk.department]["total_risks"] += 1
            departments[risk.department]["total_score"] += score
            if score >= 15:
                departments[risk.department]["high_risks"] += 1
    
    # Calculate averages
    for dept, data in departments.items():
        data["average_score"] = round(data["total_score"] / data["total_risks"], 2) if data["total_risks"] else 0
    
    return {"departments": departments}'''

# KRI Status endpoint
kri_status = '''@router.get("/kri-status", response_model=Dict[str, Any])
def get_kri_status_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get KRI status analytics"""
    kris = db.query(KeyRiskIndicator).all()
    
    by_status = {}
    for status in KRIStatus:
        by_status[status.value] = len([k for k in kris if k.status == status])
    
    return {
        "total_kris": len(kris),
        "by_status": by_status,
        "threshold_analysis": {
            "within_threshold": len([k for k in kris if k.threshold_lower <= k.current_value <= k.threshold_upper]),
            "breached": len([k for k in kris if k.current_value > k.threshold_upper or k.current_value < k.threshold_lower])
        }
    }'''

# Compliance Score endpoint
compliance_score = '''@router.get("/compliance-score", response_model=Dict[str, Any])
def get_compliance_score_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get compliance score analytics"""
    requirements = db.query(ComplianceRequirement).all()
    mappings = db.query(ComplianceMapping).all()
    
    if not requirements:
        return {"overall_score": 0, "by_framework": {}}
    
    mapped_count = len(set(m.requirement_id for m in mappings))
    overall_score = round((mapped_count / len(requirements)) * 100, 2)
    
    # By framework
    by_framework = {}
    frameworks = set(r.framework for r in requirements)
    
    for framework in frameworks:
        framework_reqs = [r for r in requirements if r.framework == framework]
        framework_mapped = len([m for m in mappings if m.requirement_id in [r.id for r in framework_reqs]])
        
        by_framework[framework] = {
            "score": round((framework_mapped / len(framework_reqs)) * 100, 2) if framework_reqs else 0,
            "total_requirements": len(framework_reqs),
            "mapped": framework_mapped
        }
    
    return {
        "overall_score": overall_score,
        "by_framework": by_framework,
        "total_gaps": len(requirements) - mapped_count
    }'''

# Add all analytics endpoints
with open(analytics_file, 'r') as f:
    content = f.read()
    
if '/risk-summary' not in content:
    append_endpoint_to_file(analytics_file, risk_summary)
    print("✅ Added /risk-summary endpoint")
    
if '/department-risks' not in content:
    append_endpoint_to_file(analytics_file, dept_risks)
    print("✅ Added /department-risks endpoint")
    
if '/kri-status' not in content:
    append_endpoint_to_file(analytics_file, kri_status)
    print("✅ Added /kri-status endpoint")
    
if '/compliance-score' not in content:
    append_endpoint_to_file(analytics_file, compliance_score)
    print("✅ Added /compliance-score endpoint")

# 2. Dashboard - Add 3 missing endpoints
print("\n📁 Dashboard Module")
print("-" * 40)

dashboard_file = "app/api/v1/dashboard.py"

# Add required imports
add_imports_to_file(dashboard_file, [
    "from typing import Dict, Any, List",
    "from datetime import datetime, timedelta, timezone",
    "from fastapi import Query"
])

# Recent Activities endpoint
recent_activities = '''@router.get("/recent-activities", response_model=List[Dict[str, Any]])
def get_recent_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(20, le=100)
) -> List[Dict[str, Any]]:
    """Get recent activities"""
    activities = []
    
    # Recent risks
    recent_risks = db.query(Risk).order_by(Risk.created_at.desc()).limit(5).all()
    for risk in recent_risks:
        activities.append({
            "type": "risk_created",
            "title": f"New risk: {risk.title}",
            "timestamp": risk.created_at.isoformat(),
            "user": risk.owner.full_name if risk.owner else "System"
        })
    
    # Recent incidents
    recent_incidents = db.query(Incident).order_by(Incident.created_at.desc()).limit(5).all()
    for incident in recent_incidents:
        activities.append({
            "type": "incident_reported",
            "title": f"Incident: {incident.title}",
            "timestamp": incident.created_at.isoformat(),
            "severity": incident.severity.value if incident.severity else None
        })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return activities[:limit]'''

# My Tasks endpoint
my_tasks = '''@router.get("/my-tasks", response_model=Dict[str, Any])
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get tasks for current user"""
    # Get risks owned by user
    user_risks = db.query(Risk).filter(Risk.owner_id == current_user.id).all()
    
    # Get open incidents assigned to user
    open_incidents = db.query(Incident).filter(
        Incident.assigned_to_id == current_user.id,
        Incident.status.in_([IncidentStatus.open, IncidentStatus.investigating])
    ).all()
    
    # Get KRIs owned by user
    user_kris = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.owner_id == current_user.id).all()
    
    return {
        "assigned_risks": len(user_risks),
        "open_incidents": len(open_incidents),
        "kris_to_measure": len(user_kris),
        "total_tasks": len(user_risks) + len(open_incidents) + len(user_kris)
    }'''

# Risk Metrics endpoint
risk_metrics = '''@router.get("/risk-metrics", response_model=Dict[str, Any])
def get_risk_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get risk metrics"""
    risks = db.query(Risk).all()
    controls = db.query(Control).all()
    
    if not risks:
        return {"risk_scores": {}, "control_coverage": {}}
    
    risk_scores = [(r.likelihood or 0) * (r.impact or 0) for r in risks]
    
    return {
        "risk_scores": {
            "average": round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else 0,
            "highest": max(risk_scores) if risk_scores else 0,
            "lowest": min(risk_scores) if risk_scores else 0
        },
        "control_coverage": {
            "total_controls": len(controls),
            "average_effectiveness": round(sum(c.effectiveness or 0 for c in controls) / len(controls), 2) if controls else 0
        }
    }'''

# Add all dashboard endpoints
with open(dashboard_file, 'r') as f:
    content = f.read()
    
if '/recent-activities' not in content:
    append_endpoint_to_file(dashboard_file, recent_activities)
    print("✅ Added /recent-activities endpoint")
    
if '/my-tasks' not in content:
    append_endpoint_to_file(dashboard_file, my_tasks)
    print("✅ Added /my-tasks endpoint")
    
if '/risk-metrics' not in content:
    append_endpoint_to_file(dashboard_file, risk_metrics)
    print("✅ Added /risk-metrics endpoint")

# 3. Reports - Add 2 missing endpoints
print("\n📁 Reports Module")
print("-" * 40)

reports_file = "app/api/v1/reports.py"

# Add required imports
add_imports_to_file(reports_file, [
    "from typing import Dict, Any, List, Optional",
    "from datetime import datetime, timezone",
    "import csv",
    "import io"
])

# Risk Register endpoint
risk_register = '''@router.get("/risk-register", response_model=Dict[str, Any])
def generate_risk_register(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Generate risk register report"""
    risks = db.query(Risk).all()
    
    risk_register_data = []
    for risk in risks:
        risk_entry = {
            "id": str(risk.id),
            "title": risk.title,
            "category": risk.category.value if risk.category else None,
            "department": risk.department,
            "owner": risk.owner.full_name if risk.owner else None,
            "likelihood": risk.likelihood,
            "impact": risk.impact,
            "risk_score": (risk.likelihood or 0) * (risk.impact or 0),
            "status": risk.status.value if risk.status else None
        }
        risk_register_data.append(risk_entry)
    
    # Sort by risk score
    risk_register_data.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return {
        "title": "Risk Register Report",
        "generated_date": datetime.now(timezone.utc).isoformat(),
        "generated_by": current_user.full_name,
        "total_risks": len(risk_register_data),
        "risks": risk_register_data
    }'''

# Compliance Report endpoint
compliance_report = '''@router.get("/compliance", response_model=Dict[str, Any])
def generate_compliance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    framework: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Generate compliance report"""
    query = db.query(ComplianceRequirement)
    if framework:
        query = query.filter(ComplianceRequirement.framework == framework)
    
    requirements = query.all()
    mappings = db.query(ComplianceMapping).all()
    
    compliance_data = {}
    for req in requirements:
        if req.framework not in compliance_data:
            compliance_data[req.framework] = {
                "framework_name": req.framework,
                "total_requirements": 0,
                "mapped_requirements": 0
            }
        
        compliance_data[req.framework]["total_requirements"] += 1
        
        if any(m.requirement_id == req.id for m in mappings):
            compliance_data[req.framework]["mapped_requirements"] += 1
    
    # Calculate percentages
    for framework_data in compliance_data.values():
        framework_data["compliance_percentage"] = round(
            (framework_data["mapped_requirements"] / framework_data["total_requirements"]) * 100, 2
        ) if framework_data["total_requirements"] else 0
    
    return {
        "title": "Compliance Status Report",
        "generated_date": datetime.now(timezone.utc).isoformat(),
        "generated_by": current_user.full_name,
        "frameworks": list(compliance_data.values())
    }'''

# Add report endpoints
with open(reports_file, 'r') as f:
    content = f.read()
    
if '/risk-register' not in content:
    append_endpoint_to_file(reports_file, risk_register)
    print("✅ Added /risk-register endpoint")
    
if '"/compliance"' not in content and "'/compliance'" not in content:
    append_endpoint_to_file(reports_file, compliance_report)
    print("✅ Added /compliance endpoint")

# 4. Audit - Add 3 missing endpoints
print("\n📁 Audit Module")
print("-" * 40)

audit_file = "app/api/v1/audit.py"

# Add required imports
add_imports_to_file(audit_file, [
    "from typing import Dict, Any, List, Optional",
    "from datetime import datetime, timedelta, timezone",
    "from fastapi import Query"
])

# Logs endpoint
logs_endpoint = '''@router.get("/logs", response_model=Dict[str, Any])
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000)
) -> Dict[str, Any]:
    """Get audit logs with pagination"""
    query = db.query(AuditLog)
    total = query.count()
    
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "user": log.user.full_name if log.user else "System",
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id
            } for log in logs
        ]
    }'''

# User Activities endpoint
user_activities = '''@router.get("/user-activities", response_model=Dict[str, Any])
def get_user_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_id: Optional[str] = None,
    days: int = Query(30)
) -> Dict[str, Any]:
    """Get user activity summary"""
    target_user_id = user_id if user_id else str(current_user.id)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    logs = db.query(AuditLog).filter(
        AuditLog.user_id == target_user_id,
        AuditLog.timestamp >= cutoff_date
    ).all()
    
    activities_by_type = {}
    for log in logs:
        if log.action not in activities_by_type:
            activities_by_type[log.action] = 0
        activities_by_type[log.action] += 1
    
    return {
        "user_id": target_user_id,
        "period_days": days,
        "total_activities": len(logs),
        "activities_by_type": activities_by_type
    }'''

# Changes endpoint
changes_endpoint = '''@router.get("/changes", response_model=List[Dict[str, Any]])
def get_recent_changes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days: int = Query(7)
) -> List[Dict[str, Any]]:
    """Get recent changes"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    changes = db.query(AuditLog).filter(
        AuditLog.timestamp >= cutoff_date,
        AuditLog.action.in_(["created", "updated", "deleted"])
    ).order_by(AuditLog.timestamp.desc()).all()
    
    return [
        {
            "id": str(change.id),
            "timestamp": change.timestamp.isoformat(),
            "user": change.user.full_name if change.user else "System",
            "action": change.action,
            "resource_type": change.resource_type,
            "resource_id": change.resource_id
        } for change in changes
    ]'''

# Add audit endpoints
with open(audit_file, 'r') as f:
    content = f.read()
    
if '"/logs"' not in content and "'/logs'" not in content:
    append_endpoint_to_file(audit_file, logs_endpoint)
    print("✅ Added /logs endpoint")
    
if '/user-activities' not in content:
    append_endpoint_to_file(audit_file, user_activities)
    print("✅ Added /user-activities endpoint")
    
if '/changes' not in content:
    append_endpoint_to_file(audit_file, changes_endpoint)
    print("✅ Added /changes endpoint")

# 5. Simulation - Add scenario analysis endpoint
print("\n📁 Simulation Module")
print("-" * 40)

simulation_file = "app/api/v1/simulation.py"

# Add required imports
add_imports_to_file(simulation_file, [
    "from typing import Dict, Any, List"
])

# Scenario Analysis endpoint
scenario_analysis = '''@router.post("/scenario-analysis", response_model=Dict[str, Any])
def run_scenario_analysis(
    scenario_input: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Run scenario analysis"""
    scenario_name = scenario_input.get("name", "Custom Scenario")
    risk_adjustments = scenario_input.get("risk_adjustments", [])
    
    all_risks = db.query(Risk).all()
    baseline_score = sum((r.likelihood or 0) * (r.impact or 0) for r in all_risks)
    
    # Apply adjustments
    scenario_score = baseline_score
    adjusted_risks = []
    
    for adjustment in risk_adjustments:
        risk_id = adjustment.get("risk_id")
        new_likelihood = adjustment.get("likelihood")
        new_impact = adjustment.get("impact")
        
        risk = next((r for r in all_risks if str(r.id) == risk_id), None)
        if risk:
            original = (risk.likelihood or 0) * (risk.impact or 0)
            adjusted = (new_likelihood or risk.likelihood or 0) * (new_impact or risk.impact or 0)
            scenario_score = scenario_score - original + adjusted
            
            adjusted_risks.append({
                "risk_id": risk_id,
                "risk_title": risk.title,
                "original_score": original,
                "scenario_score": adjusted,
                "change": adjusted - original
            })
    
    return {
        "scenario_name": scenario_name,
        "baseline_risk_score": baseline_score,
        "scenario_risk_score": scenario_score,
        "risk_score_change": scenario_score - baseline_score,
        "adjusted_risks": adjusted_risks
    }'''

# Add simulation endpoint
with open(simulation_file, 'r') as f:
    if '/scenario-analysis' not in f.read():
        append_endpoint_to_file(simulation_file, scenario_analysis)
        print("✅ Added /scenario-analysis endpoint")

print("\n✅ All missing endpoints have been implemented!")
print("\nNext steps:")
print("1. Restart the server: pkill -f uvicorn && uvicorn app.main:app --reload")
print("2. Test endpoints: ./test_new_endpoints.sh")
print("3. Check API docs: http://localhost:8000/docs")
