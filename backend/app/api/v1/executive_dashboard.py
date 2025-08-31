"""
NAPSA Executive Dashboard API
Provides executive-level views and analytics for Board reporting
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.core.database import get_db
from app.models.user import User

router = APIRouter()

# Response Models
class RiskSummary(BaseModel):
    category_name: str
    risk_count: int
    avg_inherent_score: float
    avg_residual_score: float
    high_risks: int
    medium_risks: int
    low_risks: int
    overall_risk_level: str

class InvestmentRiskSummary(BaseModel):
    total_investment_risks: int
    high_risk_investments: int
    avg_investment_risk: float
    equity_risks: int
    real_estate_risks: int
    fixed_income_risks: int
    affected_units: int

class ComplianceSummary(BaseModel):
    total_compliance_risks: int
    compliant_items: int
    partially_compliant: int
    non_compliant: int
    not_assessed: int
    compliance_rate: float
    units_assessed: int

class KRIPerformance(BaseModel):
    category: str
    total_kris: int
    green_kris: int
    amber_kris: int
    red_kris: int
    performance_rate: float

class ExecutiveSummary(BaseModel):
    total_active_risks: int
    critical_risks: int
    avg_risk_score: float
    compliance_rate: float
    total_kris: int
    kris_on_target: int
    investment_risk_level: float
    open_incidents: int
    treatments_in_progress: int
    total_units: int
    units_with_risks: int
    dashboard_updated: datetime

# API Endpoints

@router.get("/summary", response_model=ExecutiveSummary)
def get_executive_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get consolidated executive dashboard summary"""
    query = """
        SELECT * FROM v_executive_dashboard
    """
    result = db.execute(query).first()
    if not result:
        raise HTTPException(status_code=404, detail="Executive summary not available")
    
    return dict(result)

@router.get("/risk-summary", response_model=List[RiskSummary])
def get_risk_summary(
    category: Optional[str] = Query(None, description="Filter by risk category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get risk summary by category"""
    query = "SELECT * FROM v_executive_risk_summary"
    
    params = {}
    if category:
        query += " WHERE category_name = :category"
        params['category'] = category
    
    result = db.execute(query, params)
    return [dict(row) for row in result]

@router.get("/investment-risks", response_model=InvestmentRiskSummary)
def get_investment_risk_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get investment portfolio risk summary"""
    query = """
        SELECT * FROM v_investment_risk_dashboard
    """
    result = db.execute(query).first()
    if not result:
        return InvestmentRiskSummary(
            total_investment_risks=0,
            high_risk_investments=0,
            avg_investment_risk=0.0,
            equity_risks=0,
            real_estate_risks=0,
            fixed_income_risks=0,
            affected_units=0
        )
    
    return dict(result)

@router.get("/compliance", response_model=ComplianceSummary)
def get_compliance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get compliance status summary"""
    query = """
        SELECT * FROM v_compliance_dashboard
    """
    result = db.execute(query).first()
    if not result:
        return ComplianceSummary(
            total_compliance_risks=0,
            compliant_items=0,
            partially_compliant=0,
            non_compliant=0,
            not_assessed=0,
            compliance_rate=0.0,
            units_assessed=0
        )
    
    return dict(result)

@router.get("/kri-performance", response_model=List[KRIPerformance])
def get_kri_performance(
    category: Optional[str] = Query(None, description="Filter by KRI category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get KRI performance by category"""
    query = "SELECT * FROM v_kri_performance_dashboard"
    
    params = {}
    if category:
        query += " WHERE category = :category"
        params['category'] = category
    
    result = db.execute(query, params)
    return [dict(row) for row in result]

@router.get("/heat-map-data", response_model=List[Dict[str, Any]])
def get_heat_map_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get heat map data for Board reporting"""
    query = """
        SELECT * FROM v_board_heat_map
        ORDER BY risk_score DESC
    """
    result = db.execute(query)
    return [dict(row) for row in result]

@router.get("/directorate-profiles", response_model=List[Dict[str, Any]])
def get_directorate_risk_profiles(
    directorate: Optional[str] = Query(None, description="Filter by directorate name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get risk profiles for all directorates"""
    query = "SELECT * FROM v_directorate_risk_profile"
    
    params = {}
    if directorate:
        query += " WHERE directorate = :directorate"
        params['directorate'] = directorate
    
    result = db.execute(query, params)
    return [dict(row) for row in result]

@router.get("/trend-analysis", response_model=Dict[str, Any])
def get_trend_analysis(
    period_days: int = Query(90, description="Number of days for trend analysis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get risk trend analysis over specified period"""
    query = """
        WITH trend_data AS (
            SELECT 
                DATE_TRUNC('week', created_at) as week,
                COUNT(*) as new_risks,
                AVG(inherent_risk_score) as avg_score
            FROM risks
            WHERE created_at >= CURRENT_DATE - INTERVAL ':period_days days'
            GROUP BY DATE_TRUNC('week', created_at)
            ORDER BY week
        ),
        kri_trends AS (
            SELECT 
                DATE_TRUNC('week', last_updated) as week,
                AVG(CASE WHEN current_value >= threshold_green THEN 1 ELSE 0 END) * 100 as kri_performance
            FROM key_risk_indicators
            WHERE last_updated >= CURRENT_DATE - INTERVAL ':period_days days'
            GROUP BY DATE_TRUNC('week', last_updated)
        )
        SELECT 
            td.week,
            td.new_risks,
            td.avg_score,
            kt.kri_performance
        FROM trend_data td
        LEFT JOIN kri_trends kt ON td.week = kt.week
        ORDER BY td.week
    """
    
    result = db.execute(query, {"period_days": period_days})
    trends = [dict(row) for row in result]
    
    return {
        "period_days": period_days,
        "trends": trends,
        "generated_at": datetime.now()
    }

@router.get("/top-risks", response_model=List[Dict[str, Any]])
def get_top_risks(
    limit: int = Query(10, description="Number of top risks to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get top risks by inherent risk score"""
    query = """
        SELECT 
            r.id,
            r.title,
            r.description,
            r.category,
            r.inherent_risk_score,
            r.residual_risk_score,
            r.status,
            ou.unit_name as department,
            u.full_name as risk_owner
        FROM risks r
        LEFT JOIN organizational_units ou ON r.organizational_unit_id = ou.id
        LEFT JOIN users u ON r.risk_owner_id = u.id
        WHERE r.status = 'active'
    """
    
    params = {"limit": limit}
    if category:
        query += " AND r.category = :category"
        params['category'] = category
    
    query += " ORDER BY r.inherent_risk_score DESC LIMIT :limit"
    
    result = db.execute(query, params)
    return [dict(row) for row in result]

@router.get("/critical-kris", response_model=List[Dict[str, Any]])
def get_critical_kris(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get KRIs in critical or red status"""
    query = """
        SELECT 
            kri.id,
            kri.name,
            kri.description,
            kri.category,
            kri.department,
            kri.current_value,
            kri.target_value,
            kri.threshold_red,
            CASE 
                WHEN kri.current_value < kri.threshold_red THEN 'Critical'
                ELSE 'Red'
            END as status,
            kri.last_updated
        FROM key_risk_indicators kri
        WHERE kri.is_active = true
        AND kri.current_value < kri.threshold_amber
        ORDER BY (kri.threshold_red - kri.current_value) DESC
    """
    
    result = db.execute(query)
    return [dict(row) for row in result]

@router.get("/operational-metrics", response_model=Dict[str, Any])
def get_operational_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get operational metrics for benefits and contributions"""
    query = """
        SELECT * FROM v_benefits_operations_dashboard
    """
    result = db.execute(query).first()
    if not result:
        return {
            "operational_risks": 0,
            "benefit_risks": 0,
            "member_risks": 0,
            "technology_risks": 0,
            "avg_operational_risk": 0.0,
            "risks_under_review": 0,
            "mitigated_risks": 0
        }
    
    return dict(result)

@router.get("/board-report", response_model=Dict[str, Any])
def generate_board_report(
    report_date: date = Query(date.today(), description="Report date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Generate comprehensive Board report data"""
    
    # Get all dashboard data
    executive_summary = db.execute("SELECT * FROM v_executive_dashboard").first()
    risk_summary = db.execute("SELECT * FROM v_executive_risk_summary LIMIT 5").fetchall()
    investment_risks = db.execute("SELECT * FROM v_investment_risk_dashboard").first()
    compliance = db.execute("SELECT * FROM v_compliance_dashboard").first()
    kri_performance = db.execute("SELECT * FROM v_kri_performance_dashboard").fetchall()
    top_risks = db.execute("""
        SELECT title, inherent_risk_score, category 
        FROM risks 
        WHERE status = 'active' 
        ORDER BY inherent_risk_score DESC 
        LIMIT 5
    """).fetchall()
    
    return {
        "report_date": report_date,
        "executive_summary": dict(executive_summary) if executive_summary else {},
        "risk_categories": [dict(r) for r in risk_summary],
        "investment_portfolio": dict(investment_risks) if investment_risks else {},
        "compliance_status": dict(compliance) if compliance else {},
        "kri_performance": [dict(k) for k in kri_performance],
        "top_risks": [dict(r) for r in top_risks],
        "generated_at": datetime.now(),
        "report_period": f"{report_date - timedelta(days=30)} to {report_date}"
    }

@router.get("/alerts", response_model=List[Dict[str, Any]])
def get_executive_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: high, medium, low"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get alerts requiring executive attention"""
    query = """
        WITH alerts AS (
            -- High risk alerts
            SELECT 
                'RISK' as alert_type,
                'HIGH' as severity,
                CONCAT('High Risk: ', title) as message,
                created_at as alert_date
            FROM risks
            WHERE inherent_risk_score >= 20
            AND status = 'active'
            AND created_at >= CURRENT_DATE - INTERVAL '7 days'
            
            UNION ALL
            
            -- Critical KRI alerts
            SELECT 
                'KRI' as alert_type,
                'HIGH' as severity,
                CONCAT('Critical KRI: ', name, ' - Current: ', current_value, ' Target: ', target_value) as message,
                last_updated as alert_date
            FROM key_risk_indicators
            WHERE current_value < threshold_red
            AND is_active = true
            AND last_updated >= CURRENT_DATE - INTERVAL '7 days'
            
            UNION ALL
            
            -- Compliance alerts
            SELECT 
                'COMPLIANCE' as alert_type,
                'MEDIUM' as severity,
                'Non-compliance detected in regulatory requirements' as message,
                created_at as alert_date
            FROM compliance_assessments
            WHERE status = 'non_compliant'
            AND created_at >= CURRENT_DATE - INTERVAL '7 days'
        )
        SELECT * FROM alerts
    """
    
    params = {}
    if severity:
        query += " WHERE severity = :severity"
        params['severity'] = severity.upper()
    
    query += " ORDER BY alert_date DESC LIMIT 50"
    
    result = db.execute(query, params)
    return [dict(row) for row in result]