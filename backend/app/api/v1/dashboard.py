from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.risk import Risk, RiskStatus, RiskCategoryEnum
from app.models.control import Control, ControlStatus
from app.models.kri import KeyRiskIndicator, KRIStatus
from app.models.assessment import RiskAssessment
from typing import Dict, Any, List
from app.models.workflow import RiskTreatment, WorkflowStatus
from app.models.incident import Incident, IncidentStatus
from fastapi import Query
from app.models.control import RiskControl

router = APIRouter()

@router.get("/overview")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get comprehensive dashboard data"""
    
    # Risk statistics
    risk_stats = {
        "total": db.query(Risk).count(),
        "by_status": {},
        "by_category": {},
        "recent": db.query(Risk).filter(
            Risk.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
        ).count()
    }
    
    # Get risks by status
    for status in RiskStatus:
        count = db.query(Risk).filter(Risk.status == status).count()
        risk_stats["by_status"][status.value] = count
    
    # Get risks by category
    for category in RiskCategory:
        count = db.query(Risk).filter(Risk.category == category).count()
        risk_stats["by_category"][category.value] = count
    
    # Control effectiveness
    total_controls = db.query(Control).count()
    control_stats = {
        "total": total_controls,
        "by_status": {}
    }
    
    for status in ControlStatus:
        count = db.query(Control).filter(Control.status == status).count()
        control_stats["by_status"][status.value] = count
    
    # KRI health
    kri_stats = {
        "total": db.query(KeyRiskIndicator).count(),
        "by_status": {}
    }
    
    for status in KRIStatus:
        count = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.status == status).count()
        kri_stats["by_status"][status.value] = count
    
    # Recent assessments
    recent_assessments = db.query(RiskAssessment).order_by(
        RiskAssessment.assessment_date.desc()
    ).limit(5).all()
    
    assessment_list = []
    for assessment in recent_assessments:
        assessment_list.append({
            "id": str(assessment.id),
            "risk_id": str(assessment.risk_id),
            "inherent_risk": assessment.inherent_risk,
            "residual_risk": assessment.residual_risk,
            "date": assessment.assessment_date.isoformat()
        })
    
    return {
        "risks": risk_stats,
        "controls": control_stats,
        "kris": kri_stats,
        "recent_assessments": assessment_list,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

@router.get("/risk-matrix")
def get_risk_matrix(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get risk matrix data for heatmap"""
    matrix_data = []
    
    for likelihood in range(1, 6):
        for impact in range(1, 6):
            count = db.query(Risk).filter(
                Risk.likelihood == likelihood,
                Risk.impact == impact,
                Risk.status == RiskStatus.active
            ).count()
            
            if count > 0:
                matrix_data.append({
                    "likelihood": likelihood,
                    "impact": impact,
                    "count": count,
                    "risk_score": likelihood * impact
                })
    
    return {"matrix": matrix_data}

@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get dashboard summary data"""
    # Risk summary
    total_risks = db.query(Risk).count()
    active_risks = db.query(Risk).filter(Risk.status == RiskStatus.active).count()
    high_risks = db.query(Risk).filter(Risk.inherent_risk_score >= 15).count()
    
    # Control summary
    total_controls = db.query(Control).count()
    effective_controls = db.query(Control).filter(Control.status == ControlStatus.effective).count()
    
    # KRI summary
    total_kris = db.query(KeyRiskIndicator).count()
    critical_kris = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.status == KRIStatus.critical).count()
    
    return {
        "risks": {
            "total": total_risks,
            "active": active_risks,
            "high_priority": high_risks
        },
        "controls": {
            "total": total_controls,
            "effective": effective_controls,
            "effectiveness_rate": round((effective_controls / total_controls * 100) if total_controls > 0 else 0, 1)
        },
        "kris": {
            "total": total_kris,
            "critical": critical_kris,
            "require_attention": critical_kris
        }
    }

@router.get("/recent-activities", response_model=List[Dict[str, Any]])
def get_recent_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(20, le=100)
) -> List[Dict[str, Any]]:
    """Get recent activities across the system"""
    activities = []
    
    # Get recent risks
    recent_risks = db.query(Risk)\
        .order_by(Risk.created_at.desc())\
        .limit(5)\
        .all()
    
    for risk in recent_risks:
        activities.append({
            "type": "risk_created",
            "title": f"New risk: {risk.title}",
            "description": risk.description[:100] + "..." if len(risk.description) > 100 else risk.description,
            "timestamp": risk.created_at.isoformat(),
            "user": risk.owner.full_name if risk.owner else "System",
            "entity_type": "risk",
            "entity_id": str(risk.id)
        })
    
    # Get recent assessments
    recent_assessments = db.query(RiskAssessment)\
        .order_by(RiskAssessment.assessment_date.desc())\
        .limit(5)\
        .all()
    
    for assessment in recent_assessments:
        activities.append({
            "type": "assessment_completed",
            "title": f"Risk assessed: {assessment.risk.title if assessment.risk else 'Unknown'}",
            "description": f"Likelihood: {assessment.likelihood}, Impact: {assessment.impact}",
            "timestamp": assessment.assessment_date.isoformat(),
            "user": assessment.assessed_by.full_name if assessment.assessed_by else "System",
            "entity_type": "assessment",
            "entity_id": str(assessment.id)
        })
    
    # Get recent incidents
    recent_incidents = db.query(Incident)\
        .order_by(Incident.created_at.desc())\
        .limit(5)\
        .all()
    
    for incident in recent_incidents:
        activities.append({
            "type": "incident_reported",
            "title": f"Incident: {incident.title}",
            "description": f"Severity: {incident.severity.value if incident.severity else 'Unknown'}",
            "timestamp": incident.created_at.isoformat(),
            "user": incident.reporter.full_name if incident.reporter else "System",
            "entity_type": "incident",
            "entity_id": str(incident.id)
        })
    
    # Get recent KRI measurements
    recent_measurements = db.query(KRIMeasurement)\
        .order_by(KRIMeasurement.measurement_date.desc())\
        .limit(5)\
        .all()
    
    for measurement in recent_measurements:
        activities.append({
            "type": "kri_measured",
            "title": f"KRI updated: {measurement.kri.name if measurement.kri else 'Unknown'}",
            "description": f"New value: {measurement.value}",
            "timestamp": measurement.measurement_date.isoformat(),
            "user": measurement.measured_by.full_name if measurement.measured_by else "System",
            "entity_type": "kri",
            "entity_id": str(measurement.kri_id)
        })
    
    # Sort all activities by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return activities[:limit]

@router.get("/my-tasks", response_model=Dict[str, Any])
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get tasks assigned to the current user"""
    tasks = {
        "pending_assessments": [],
        "assigned_risks": [],
        "pending_treatments": [],
        "open_incidents": [],
        "kri_measurements_due": [],
        "total_tasks": 0
    }
    
    # Get risks owned by user that need assessment
    user_risks = db.query(Risk).filter(Risk.owner_id == current_user.id).all()
    for risk in user_risks:
        # Check if risk needs assessment (no assessment in last 90 days)
        latest_assessment = db.query(RiskAssessment)\
            .filter(RiskAssessment.risk_id == risk.id)\
            .order_by(RiskAssessment.assessment_date.desc())\
            .first()
        
        if not latest_assessment or (datetime.now(timezone.utc) - latest_assessment.assessment_date).days > 90:
            tasks["pending_assessments"].append({
                "id": str(risk.id),
                "title": risk.title,
                "days_overdue": (datetime.now(timezone.utc) - latest_assessment.assessment_date).days - 90 if latest_assessment else 0,
                "priority": "high" if not latest_assessment else "medium"
            })
    
    tasks["assigned_risks"] = [
        {
            "id": str(r.id),
            "title": r.title,
            "status": r.status.value if r.status else "unknown",
            "risk_score": (r.likelihood or 0) * (r.impact or 0)
        } for r in user_risks
    ]
    
    # Get pending treatments
    pending_treatments = db.query(RiskTreatment)\
        .filter(RiskTreatment.owner_id == current_user.id)\
        .filter(RiskTreatment.status.in_([WorkflowStatus.draft, WorkflowStatus.in_progress]))\
        .all()
    
    tasks["pending_treatments"] = [
        {
            "id": str(t.id),
            "risk_title": t.risk.title if t.risk else "Unknown",
            "strategy": t.strategy.value if t.strategy else "unknown",
            "target_date": t.target_date.isoformat() if t.target_date else None,
            "days_until_target": (t.target_date - datetime.now(timezone.utc)).days if t.target_date else None
        } for t in pending_treatments
    ]
    
    # Get open incidents assigned to user
    open_incidents = db.query(Incident)\
        .filter(Incident.assigned_to_id == current_user.id)\
        .filter(Incident.status.in_([IncidentStatus.open, IncidentStatus.investigating]))\
        .all()
    
    tasks["open_incidents"] = [
        {
            "id": str(i.id),
            "title": i.title,
            "severity": i.severity.value if i.severity else "unknown",
            "days_open": (datetime.now(timezone.utc) - i.created_at).days
        } for i in open_incidents
    ]
    
    # Get KRIs that need measurement
    user_kris = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.owner_id == current_user.id).all()
    for kri in user_kris:
        latest_measurement = db.query(KRIMeasurement)\
            .filter(KRIMeasurement.kri_id == kri.id)\
            .order_by(KRIMeasurement.measurement_date.desc())\
            .first()
        
        needs_measurement = False
        if not latest_measurement:
            needs_measurement = True
        else:
            days_since = (datetime.now(timezone.utc) - latest_measurement.measurement_date).days
            if kri.frequency == "daily" and days_since >= 1:
                needs_measurement = True
            elif kri.frequency == "weekly" and days_since >= 7:
                needs_measurement = True
            elif kri.frequency == "monthly" and days_since >= 30:
                needs_measurement = True
        
        if needs_measurement:
            tasks["kri_measurements_due"].append({
                "id": str(kri.id),
                "name": kri.name,
                "frequency": kri.frequency,
                "last_measured": latest_measurement.measurement_date.isoformat() if latest_measurement else None,
                "days_overdue": days_since if latest_measurement else 0
            })
    
    # Calculate total tasks
    tasks["total_tasks"] = (
        len(tasks["pending_assessments"]) +
        len(tasks["pending_treatments"]) +
        len(tasks["open_incidents"]) +
        len(tasks["kri_measurements_due"])
    )
    
    return tasks

@router.get("/risk-metrics", response_model=Dict[str, Any])
def get_risk_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get comprehensive risk metrics for dashboard"""
    risks = db.query(Risk).all()
    controls = db.query(Control).all()
    incidents = db.query(Incident).all()
    
    metrics = {
        "risk_scores": {
            "average": 0,
            "highest": 0,
            "lowest": 25,
            "median": 0
        },
        "risk_velocity": {
            "increasing": 0,
            "stable": 0,
            "decreasing": 0
        },
        "control_coverage": {
            "fully_controlled": 0,
            "partially_controlled": 0,
            "uncontrolled": 0
        },
        "incident_correlation": {
            "risks_with_incidents": 0,
            "incident_rate": 0
        },
        "risk_appetite": {
            "within_appetite": 0,
            "exceeds_appetite": 0,
            "risk_appetite_utilization": 0
        }
    }
    
    if risks:
        # Calculate risk scores
        risk_scores = [(r.likelihood or 0) * (r.impact or 0) for r in risks]
        metrics["risk_scores"]["average"] = round(sum(risk_scores) / len(risk_scores), 2)
        metrics["risk_scores"]["highest"] = max(risk_scores) if risk_scores else 0
        metrics["risk_scores"]["lowest"] = min(risk_scores) if risk_scores else 0
        metrics["risk_scores"]["median"] = sorted(risk_scores)[len(risk_scores)//2] if risk_scores else 0
        
        # Risk velocity (compare current vs previous assessments)
        for risk in risks:
            assessments = db.query(RiskAssessment)\
                .filter(RiskAssessment.risk_id == risk.id)\
                .order_by(RiskAssessment.assessment_date.desc())\
                .limit(2)\
                .all()
            
            if len(assessments) >= 2:
                current_score = assessments[0].likelihood * assessments[0].impact
                previous_score = assessments[1].likelihood * assessments[1].impact
                
                if current_score > previous_score:
                    metrics["risk_velocity"]["increasing"] += 1
                elif current_score < previous_score:
                    metrics["risk_velocity"]["decreasing"] += 1
                else:
                    metrics["risk_velocity"]["stable"] += 1
            else:
                metrics["risk_velocity"]["stable"] += 1
        
        # Control coverage
        for risk in risks:
            risk_controls = db.query(RiskControl).filter(RiskControl.risk_id == risk.id).all()
            if len(risk_controls) >= 2:
                metrics["control_coverage"]["fully_controlled"] += 1
            elif len(risk_controls) == 1:
                metrics["control_coverage"]["partially_controlled"] += 1
            else:
                metrics["control_coverage"]["uncontrolled"] += 1
        
        # Incident correlation
        risk_ids_with_incidents = set()
        for incident in incidents:
            if hasattr(incident, 'related_risk_id') and incident.related_risk_id:
                risk_ids_with_incidents.add(incident.related_risk_id)
        
        metrics["incident_correlation"]["risks_with_incidents"] = len(risk_ids_with_incidents)
        metrics["incident_correlation"]["incident_rate"] = round(
            (len(risk_ids_with_incidents) / len(risks)) * 100, 2
        ) if risks else 0
        
        # Risk appetite (assuming appetite threshold is 15)
        risk_appetite_threshold = 15
        within_appetite = len([r for r in risk_scores if r <= risk_appetite_threshold])
        exceeds_appetite = len([r for r in risk_scores if r > risk_appetite_threshold])
        
        metrics["risk_appetite"]["within_appetite"] = within_appetite
        metrics["risk_appetite"]["exceeds_appetite"] = exceeds_appetite
        metrics["risk_appetite"]["risk_appetite_utilization"] = round(
            (sum(risk_scores) / (risk_appetite_threshold * len(risks))) * 100, 2
        ) if risks else 0
    
    return metrics
