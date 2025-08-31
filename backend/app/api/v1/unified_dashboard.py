"""
Unified Dashboard API for combined ERM and AML view
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.risk import Risk, RiskStatus
from app.models.incident import Incident, IncidentStatus
from app.models.control import Control, ControlStatus
from app.models.kri import KeyRiskIndicator
from app.models.aml import (
    CustomerProfile, Transaction, TransactionAlert,
    ComplianceCase, SuspiciousActivityReport, CurrencyTransactionReport
)
from app.models.aml.transaction import AlertStatus, TransactionStatus
from app.models.aml.case import CaseStatus
from app.services.integration import AMLERMIntegrationService

router = APIRouter()


@router.get("/overview")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive dashboard overview combining ERM and AML metrics"""
    
    # ERM Metrics
    total_risks = db.query(Risk).count()
    active_risks = db.query(Risk).filter(Risk.status == RiskStatus.ACTIVE).count()
    high_risks = db.query(Risk).filter(
        Risk.status == RiskStatus.ACTIVE,
        Risk.risk_score >= 15
    ).count()
    
    total_incidents = db.query(Incident).count()
    open_incidents = db.query(Incident).filter(
        Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.INVESTIGATING])
    ).count()
    
    total_controls = db.query(Control).count()
    effective_controls = db.query(Control).filter(
        Control.status == ControlStatus.ACTIVE,
        Control.effectiveness >= 80
    ).count()
    
    total_kris = db.query(KeyRiskIndicator).count()
    breached_kris = db.query(KeyRiskIndicator).filter(
        KeyRiskIndicator.status == "breached"
    ).count()
    
    # AML Metrics
    total_customers = db.query(CustomerProfile).count()
    high_risk_customers = db.query(CustomerProfile).filter(
        CustomerProfile.risk_level.in_(["high", "critical"])
    ).count()
    
    total_transactions = db.query(Transaction).count()
    flagged_transactions = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.FLAGGED
    ).count()
    
    total_alerts = db.query(TransactionAlert).count()
    open_alerts = db.query(TransactionAlert).filter(
        TransactionAlert.status == AlertStatus.OPEN
    ).count()
    
    total_cases = db.query(ComplianceCase).count()
    open_cases = db.query(ComplianceCase).filter(
        ComplianceCase.status.in_([CaseStatus.OPEN, CaseStatus.INVESTIGATING])
    ).count()
    
    # Reports
    total_sars = db.query(SuspiciousActivityReport).count()
    total_ctrs = db.query(CurrencyTransactionReport).count()
    
    # Calculate combined risk score
    combined_risk_score = _calculate_combined_risk_score(
        high_risks, open_incidents, high_risk_customers, open_alerts
    )
    
    return {
        "overview": {
            "combined_risk_score": combined_risk_score,
            "risk_level": _determine_risk_level(combined_risk_score),
            "last_updated": datetime.utcnow().isoformat()
        },
        "erm_metrics": {
            "risks": {
                "total": total_risks,
                "active": active_risks,
                "high_priority": high_risks
            },
            "incidents": {
                "total": total_incidents,
                "open": open_incidents
            },
            "controls": {
                "total": total_controls,
                "effective": effective_controls,
                "effectiveness_rate": (effective_controls / total_controls * 100) if total_controls > 0 else 0
            },
            "kris": {
                "total": total_kris,
                "breached": breached_kris
            }
        },
        "aml_metrics": {
            "customers": {
                "total": total_customers,
                "high_risk": high_risk_customers,
                "high_risk_percentage": (high_risk_customers / total_customers * 100) if total_customers > 0 else 0
            },
            "transactions": {
                "total": total_transactions,
                "flagged": flagged_transactions
            },
            "alerts": {
                "total": total_alerts,
                "open": open_alerts
            },
            "cases": {
                "total": total_cases,
                "open": open_cases
            },
            "reports": {
                "sars": total_sars,
                "ctrs": total_ctrs
            }
        }
    }


@router.get("/trends")
def get_dashboard_trends(
    days: int = Query(30, description="Number of days for trend analysis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get trend data for the dashboard"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Daily risk trend
    risk_trend = db.query(
        func.date(Risk.created_at).label('date'),
        func.count(Risk.id).label('count')
    ).filter(
        Risk.created_at >= start_date
    ).group_by(
        func.date(Risk.created_at)
    ).all()
    
    # Daily incident trend
    incident_trend = db.query(
        func.date(Incident.incident_date).label('date'),
        func.count(Incident.id).label('count')
    ).filter(
        Incident.incident_date >= start_date
    ).group_by(
        func.date(Incident.incident_date)
    ).all()
    
    # Daily transaction trend
    transaction_trend = db.query(
        func.date(Transaction.transaction_date).label('date'),
        func.count(Transaction.id).label('count'),
        func.sum(Transaction.amount).label('volume')
    ).filter(
        Transaction.transaction_date >= start_date
    ).group_by(
        func.date(Transaction.transaction_date)
    ).all()
    
    # Daily alert trend
    alert_trend = db.query(
        func.date(TransactionAlert.created_at).label('date'),
        func.count(TransactionAlert.id).label('count')
    ).filter(
        TransactionAlert.created_at >= start_date
    ).group_by(
        func.date(TransactionAlert.created_at)
    ).all()
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": datetime.utcnow().isoformat(),
            "days": days
        },
        "trends": {
            "risks": [
                {"date": r.date.isoformat(), "count": r.count}
                for r in risk_trend
            ],
            "incidents": [
                {"date": i.date.isoformat(), "count": i.count}
                for i in incident_trend
            ],
            "transactions": [
                {
                    "date": t.date.isoformat(),
                    "count": t.count,
                    "volume": float(t.volume) if t.volume else 0
                }
                for t in transaction_trend
            ],
            "alerts": [
                {"date": a.date.isoformat(), "count": a.count}
                for a in alert_trend
            ]
        }
    }


@router.get("/risk-heatmap")
def get_risk_heatmap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get risk heatmap data combining ERM and AML risks"""
    
    # Get ERM risks by category
    erm_risks = db.query(
        Risk.category,
        func.avg(Risk.likelihood).label('avg_likelihood'),
        func.avg(Risk.impact).label('avg_impact'),
        func.count(Risk.id).label('count')
    ).filter(
        Risk.status == RiskStatus.ACTIVE
    ).group_by(Risk.category).all()
    
    # Get AML risks by type
    aml_customer_risk = db.query(
        func.avg(CustomerProfile.risk_score).label('avg_score'),
        func.count(CustomerProfile.id).label('count')
    ).filter(
        CustomerProfile.risk_level.in_(["high", "critical"])
    ).first()
    
    aml_transaction_risk = db.query(
        func.avg(Transaction.risk_score).label('avg_score'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.is_high_risk == True
    ).first()
    
    # Build heatmap data
    heatmap = []
    
    # Add ERM risks
    for risk in erm_risks:
        heatmap.append({
            "category": risk.category.value,
            "type": "ERM",
            "likelihood": float(risk.avg_likelihood) if risk.avg_likelihood else 0,
            "impact": float(risk.avg_impact) if risk.avg_impact else 0,
            "count": risk.count,
            "risk_score": (float(risk.avg_likelihood) * float(risk.avg_impact)) if risk.avg_likelihood and risk.avg_impact else 0
        })
    
    # Add AML risks
    if aml_customer_risk:
        heatmap.append({
            "category": "Customer Risk",
            "type": "AML",
            "likelihood": min(5, aml_customer_risk.avg_score / 20) if aml_customer_risk.avg_score else 0,
            "impact": 4,  # Customer risks typically have high impact
            "count": aml_customer_risk.count,
            "risk_score": (min(5, aml_customer_risk.avg_score / 20) * 4) if aml_customer_risk.avg_score else 0
        })
    
    if aml_transaction_risk:
        heatmap.append({
            "category": "Transaction Risk",
            "type": "AML",
            "likelihood": min(5, aml_transaction_risk.avg_score / 20) if aml_transaction_risk.avg_score else 0,
            "impact": 3,  # Transaction risks have moderate impact
            "count": aml_transaction_risk.count,
            "risk_score": (min(5, aml_transaction_risk.avg_score / 20) * 3) if aml_transaction_risk.avg_score else 0
        })
    
    return {
        "heatmap": heatmap,
        "legend": {
            "likelihood": "1-5 scale (1=Very Low, 5=Very High)",
            "impact": "1-5 scale (1=Very Low, 5=Very High)",
            "risk_score": "Likelihood × Impact (max 25)"
        }
    }


@router.get("/alerts-summary")
def get_alerts_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get summary of all alerts from both ERM and AML systems"""
    
    integration_service = AMLERMIntegrationService(db)
    aml_metrics = integration_service.get_aml_risk_metrics()
    
    # Get KRI alerts
    kri_alerts = db.query(KeyRiskIndicator).filter(
        KeyRiskIndicator.status == "breached"
    ).limit(5).all()
    
    # Get recent AML alerts
    recent_aml_alerts = db.query(TransactionAlert).filter(
        TransactionAlert.status == AlertStatus.OPEN
    ).order_by(TransactionAlert.created_at.desc()).limit(5).all()
    
    # Get high priority incidents
    high_priority_incidents = db.query(Incident).filter(
        Incident.status == IncidentStatus.OPEN,
        Incident.severity.in_(["high", "critical"])
    ).limit(5).all()
    
    return {
        "summary": {
            "total_alerts": len(kri_alerts) + len(recent_aml_alerts) + len(high_priority_incidents),
            "kri_breaches": len(kri_alerts),
            "aml_alerts": aml_metrics["aml_risks"]["open_alerts"],
            "high_priority_incidents": len(high_priority_incidents)
        },
        "recent_alerts": {
            "kri_alerts": [
                {
                    "id": kri.id,
                    "name": kri.name,
                    "current_value": kri.current_value,
                    "threshold": kri.threshold_value,
                    "status": kri.status
                }
                for kri in kri_alerts
            ],
            "aml_alerts": [
                {
                    "id": alert.id,
                    "alert_id": alert.alert_id,
                    "title": alert.title,
                    "severity": alert.severity.value,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in recent_aml_alerts
            ],
            "incidents": [
                {
                    "id": incident.id,
                    "title": incident.title,
                    "severity": incident.severity.value,
                    "status": incident.status.value,
                    "incident_date": incident.incident_date.isoformat()
                }
                for incident in high_priority_incidents
            ]
        },
        "risk_indicators": aml_metrics["risk_indicators"]
    }


@router.get("/compliance-status")
def get_compliance_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get overall compliance status"""
    
    # KYC Compliance
    total_customers = db.query(CustomerProfile).count()
    kyc_complete = db.query(CustomerProfile).filter(
        CustomerProfile.kyc_status == "completed"
    ).count()
    
    # EDD Compliance
    edd_required = db.query(CustomerProfile).filter(
        CustomerProfile.edd_required == True
    ).count()
    edd_complete = db.query(CustomerProfile).filter(
        CustomerProfile.edd_required == True,
        CustomerProfile.edd_completed == True
    ).count()
    
    # Reporting Compliance
    from app.models.aml.reports import ReportStatus
    pending_sars = db.query(SuspiciousActivityReport).filter(
        SuspiciousActivityReport.status.in_([ReportStatus.DRAFT, ReportStatus.PENDING_REVIEW])
    ).count()
    
    pending_ctrs = db.query(CurrencyTransactionReport).filter(
        CurrencyTransactionReport.status.in_([ReportStatus.DRAFT, ReportStatus.PENDING_REVIEW])
    ).count()
    
    # Case Resolution
    total_cases = db.query(ComplianceCase).count()
    resolved_cases = db.query(ComplianceCase).filter(
        ComplianceCase.status.in_([
            CaseStatus.CLOSED_REPORTED,
            CaseStatus.CLOSED_NO_ACTION,
            CaseStatus.CLOSED_FALSE_POSITIVE
        ])
    ).count()
    
    # Control Compliance
    total_controls = db.query(Control).count()
    compliant_controls = db.query(Control).filter(
        Control.status == ControlStatus.ACTIVE,
        Control.effectiveness >= 70
    ).count()
    
    return {
        "kyc_compliance": {
            "total_customers": total_customers,
            "kyc_complete": kyc_complete,
            "compliance_rate": (kyc_complete / total_customers * 100) if total_customers > 0 else 0
        },
        "edd_compliance": {
            "required": edd_required,
            "completed": edd_complete,
            "compliance_rate": (edd_complete / edd_required * 100) if edd_required > 0 else 100
        },
        "reporting_compliance": {
            "pending_sars": pending_sars,
            "pending_ctrs": pending_ctrs,
            "total_pending": pending_sars + pending_ctrs
        },
        "case_resolution": {
            "total_cases": total_cases,
            "resolved": resolved_cases,
            "resolution_rate": (resolved_cases / total_cases * 100) if total_cases > 0 else 100
        },
        "control_compliance": {
            "total_controls": total_controls,
            "compliant": compliant_controls,
            "compliance_rate": (compliant_controls / total_controls * 100) if total_controls > 0 else 0
        },
        "overall_compliance_score": _calculate_compliance_score(
            kyc_complete, total_customers,
            edd_complete, edd_required,
            pending_sars + pending_ctrs,
            resolved_cases, total_cases,
            compliant_controls, total_controls
        )
    }


def _calculate_combined_risk_score(
    high_risks: int,
    open_incidents: int,
    high_risk_customers: int,
    open_alerts: int
) -> float:
    """Calculate a combined risk score from various metrics"""
    
    # Weighted calculation
    risk_score = (
        (high_risks * 0.3) +
        (open_incidents * 0.2) +
        (high_risk_customers * 0.3) +
        (open_alerts * 0.2)
    )
    
    # Normalize to 0-100 scale
    return min(100, risk_score)


def _determine_risk_level(score: float) -> str:
    """Determine risk level from score"""
    if score >= 75:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 25:
        return "Medium"
    else:
        return "Low"


def _calculate_compliance_score(
    kyc_complete: int, total_customers: int,
    edd_complete: int, edd_required: int,
    pending_reports: int,
    resolved_cases: int, total_cases: int,
    compliant_controls: int, total_controls: int
) -> float:
    """Calculate overall compliance score"""
    
    scores = []
    
    # KYC compliance (weight: 25%)
    if total_customers > 0:
        scores.append((kyc_complete / total_customers) * 25)
    else:
        scores.append(25)
    
    # EDD compliance (weight: 20%)
    if edd_required > 0:
        scores.append((edd_complete / edd_required) * 20)
    else:
        scores.append(20)
    
    # Reporting compliance (weight: 20%)
    # Inverse - fewer pending is better
    if pending_reports == 0:
        scores.append(20)
    else:
        scores.append(max(0, 20 - pending_reports))
    
    # Case resolution (weight: 20%)
    if total_cases > 0:
        scores.append((resolved_cases / total_cases) * 20)
    else:
        scores.append(20)
    
    # Control compliance (weight: 15%)
    if total_controls > 0:
        scores.append((compliant_controls / total_controls) * 15)
    else:
        scores.append(15)
    
    return sum(scores)