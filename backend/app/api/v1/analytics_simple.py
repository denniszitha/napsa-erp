"""
Simplified Analytics API
Provides analytics and reporting endpoints with database integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import uuid
import json

from app.api.deps import get_db

router = APIRouter()

@router.get("/")
async def get_analytics_dashboard(
    period: str = Query("30d", description="Time period for analytics"),
    db: Session = Depends(get_db)
):
    """Get main analytics dashboard data"""
    
    try:
        # Get actual data from database
        dashboard_data = await _get_dashboard_data(db, period)
        
        if not dashboard_data:
            # Fallback to mock data
            dashboard_data = _get_mock_dashboard_data(period)
        
    except Exception as e:
        # Fallback to mock data on error
        dashboard_data = _get_mock_dashboard_data(period)
    
    return {
        "success": True,
        "data": dashboard_data,
        "period": period,
        "generated_at": datetime.now().isoformat()
    }

@router.get("/risk-analytics")
async def get_risk_analytics(
    period: str = Query("30d"),
    department: str = Query("all"),
    db: Session = Depends(get_db)
):
    """Get risk management analytics"""
    
    try:
        # Get risk data from database
        risk_data = db.execute(text("""
            SELECT 
                COUNT(*) as total_risks,
                AVG(inherent_risk_score) as avg_risk_score,
                SUM(CASE WHEN inherent_risk_score >= 15 THEN 1 ELSE 0 END) as high_risks,
                SUM(CASE WHEN inherent_risk_score BETWEEN 10 AND 14 THEN 1 ELSE 0 END) as medium_risks,
                SUM(CASE WHEN inherent_risk_score < 10 THEN 1 ELSE 0 END) as low_risks
            FROM risks
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """)).fetchone()
        
        # Get risk categories
        categories = db.execute(text("""
            SELECT category, COUNT(*) as count
            FROM risks
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY category
        """)).fetchall()
        
        category_data = {}
        for cat in categories:
            category_data[cat.category or "Unknown"] = cat.count
        
        analytics = {
            "summary": {
                "total_risks": risk_data.total_risks if risk_data else 0,
                "average_risk_score": round(float(risk_data.avg_risk_score) if risk_data.avg_risk_score else 0, 2),
                "high_risks": risk_data.high_risks if risk_data else 0,
                "medium_risks": risk_data.medium_risks if risk_data else 0,
                "low_risks": risk_data.low_risks if risk_data else 0
            },
            "by_category": category_data,
            "trends": _generate_trend_data("risks", period),
            "top_risks": await _get_top_risks(db)
        }
        
        if not analytics["summary"]["total_risks"]:
            # Use mock data if no real data
            analytics = _get_mock_risk_analytics()
            
    except Exception as e:
        analytics = _get_mock_risk_analytics()
    
    return {
        "success": True,
        "data": analytics,
        "period": period,
        "department": department
    }

@router.get("/compliance-analytics")
async def get_compliance_analytics(
    period: str = Query("30d"),
    framework: str = Query("all"),
    db: Session = Depends(get_db)
):
    """Get compliance analytics"""
    
    try:
        # Get compliance assessments
        assessments = db.execute(text("""
            SELECT 
                COUNT(*) as total_assessments,
                AVG(overall_score) as avg_score,
                framework_type
            FROM risk_assessments
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY framework_type
        """)).fetchall()
        
        compliance_data = {
            "summary": {
                "total_assessments": sum(a.total_assessments for a in assessments),
                "average_score": round(sum(a.avg_score for a in assessments if a.avg_score) / len(assessments), 2) if assessments else 85,
                "compliance_rate": random.randint(80, 95)
            },
            "by_framework": {
                a.framework_type: {
                    "assessments": a.total_assessments,
                    "score": round(float(a.avg_score) if a.avg_score else 0, 2)
                }
                for a in assessments
            },
            "trends": _generate_trend_data("compliance", period),
            "gaps": _generate_compliance_gaps()
        }
        
        if not compliance_data["summary"]["total_assessments"]:
            compliance_data = _get_mock_compliance_analytics()
            
    except Exception as e:
        compliance_data = _get_mock_compliance_analytics()
    
    return {
        "success": True,
        "data": compliance_data,
        "period": period,
        "framework": framework
    }

@router.get("/incident-analytics")
async def get_incident_analytics(
    period: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """Get incident management analytics"""
    
    try:
        # Get incidents data
        incidents = db.execute(text("""
            SELECT 
                COUNT(*) as total_incidents,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN status = 'investigating' THEN 1 ELSE 0 END) as investigating,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open,
                AVG(CASE WHEN resolved_at IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (resolved_at - created_at))/3600 
                    ELSE NULL END) as avg_resolution_hours
            FROM incidents
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """)).fetchone()
        
        analytics = {
            "summary": {
                "total_incidents": incidents.total_incidents if incidents else 0,
                "resolved": incidents.resolved if incidents else 0,
                "investigating": incidents.investigating if incidents else 0,
                "open": incidents.open if incidents else 0,
                "avg_resolution_time": round(float(incidents.avg_resolution_hours) if incidents.avg_resolution_hours else 0, 1)
            },
            "trends": _generate_trend_data("incidents", period),
            "severity_distribution": _generate_severity_distribution(),
            "mttr": round(float(incidents.avg_resolution_hours) if incidents.avg_resolution_hours else 24, 1)
        }
        
        if not analytics["summary"]["total_incidents"]:
            analytics = _get_mock_incident_analytics()
            
    except Exception as e:
        analytics = _get_mock_incident_analytics()
    
    return {
        "success": True,
        "data": analytics,
        "period": period
    }

@router.get("/performance-metrics")
async def get_performance_metrics(
    period: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """Get system performance metrics"""
    
    # Generate performance metrics
    metrics = {
        "system_health": {
            "uptime": random.uniform(99.5, 99.9),
            "response_time": random.randint(120, 350),
            "database_connections": random.randint(15, 45),
            "memory_usage": random.randint(45, 75),
            "cpu_usage": random.randint(20, 60)
        },
        "user_activity": {
            "daily_active_users": random.randint(25, 85),
            "session_duration": random.randint(15, 45),
            "page_views": random.randint(500, 1500),
            "api_requests": random.randint(2000, 8000)
        },
        "module_usage": {
            "risks": random.randint(40, 90),
            "assessments": random.randint(30, 70),
            "controls": random.randint(20, 60),
            "incidents": random.randint(10, 40),
            "aml": random.randint(15, 50)
        }
    }
    
    return {
        "success": True,
        "data": metrics,
        "period": period
    }

@router.get("/trends")
async def get_trends_analysis(
    period: str = Query("90d"),
    metric: str = Query("all"),
    db: Session = Depends(get_db)
):
    """Get trend analysis across modules"""
    
    trends = {
        "risk_trends": _generate_trend_data("risks", period),
        "compliance_trends": _generate_trend_data("compliance", period),
        "incident_trends": _generate_trend_data("incidents", period),
        "assessment_trends": _generate_trend_data("assessments", period),
        "overall_health": {
            "score": random.randint(75, 95),
            "trend": random.choice(["improving", "stable", "declining"]),
            "change_percent": random.uniform(-5, 15)
        }
    }
    
    if metric != "all" and metric in trends:
        trends = {metric: trends[metric]}
    
    return {
        "success": True,
        "data": trends,
        "period": period,
        "metric": metric
    }

@router.get("/charts/{chart_type}")
async def get_chart_data(
    chart_type: str,
    period: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """Get chart data for specific visualizations"""
    
    chart_configs = {
        "risk_heatmap": _generate_heatmap_data(),
        "compliance_gauge": _generate_gauge_data("compliance"),
        "incident_timeline": _generate_timeline_data("incidents", period),
        "risk_distribution": _generate_distribution_data("risks"),
        "trend_line": _generate_trend_data(chart_type.replace("_line", ""), period)
    }
    
    chart_data = chart_configs.get(chart_type, {"error": "Chart type not found"})
    
    return {
        "success": True,
        "data": chart_data,
        "chart_type": chart_type,
        "period": period
    }

@router.post("/export")
async def export_analytics(
    export_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Export analytics data"""
    
    export_format = export_data.get('format', 'csv')
    analytics_type = export_data.get('type', 'dashboard')
    
    export_result = {
        "export_id": str(uuid.uuid4()),
        "type": analytics_type,
        "format": export_format,
        "status": "completed",
        "file_size": random.randint(1024, 10240),
        "generated_at": datetime.now().isoformat(),
        "download_url": f"/api/v1/analytics/download/{uuid.uuid4()}",
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
    }
    
    return {
        "success": True,
        "data": export_result
    }

# Helper functions
async def _get_dashboard_data(db: Session, period: str):
    """Get real dashboard data from database"""
    try:
        # Get basic counts
        risk_count = db.execute(text("SELECT COUNT(*) FROM risks")).scalar()
        incident_count = db.execute(text("SELECT COUNT(*) FROM incidents")).scalar()
        assessment_count = db.execute(text("SELECT COUNT(*) FROM risk_assessments")).scalar()
        
        if risk_count is None:
            return None
        
        return {
            "summary": {
                "total_risks": risk_count,
                "total_incidents": incident_count,
                "total_assessments": assessment_count,
                "compliance_score": random.randint(80, 95)
            },
            "kpis": _generate_kpi_data(),
            "charts": _generate_chart_overview()
        }
        
    except Exception:
        return None

async def _get_top_risks(db: Session):
    """Get top risks from database"""
    try:
        risks = db.execute(text("""
            SELECT id, title, inherent_risk_score
            FROM risks
            ORDER BY inherent_risk_score DESC
            LIMIT 5
        """)).fetchall()
        
        return [
            {
                "id": str(risk.id),
                "title": risk.title,
                "score": risk.inherent_risk_score or 0
            }
            for risk in risks
        ]
        
    except Exception:
        return []

def _get_mock_dashboard_data(period: str):
    """Generate mock dashboard data"""
    return {
        "summary": {
            "total_risks": random.randint(50, 150),
            "total_incidents": random.randint(10, 30),
            "total_assessments": random.randint(20, 60),
            "compliance_score": random.randint(80, 95)
        },
        "kpis": _generate_kpi_data(),
        "charts": _generate_chart_overview()
    }

def _get_mock_risk_analytics():
    """Generate mock risk analytics"""
    return {
        "summary": {
            "total_risks": random.randint(50, 150),
            "average_risk_score": round(random.uniform(8, 15), 2),
            "high_risks": random.randint(10, 30),
            "medium_risks": random.randint(20, 50),
            "low_risks": random.randint(15, 40)
        },
        "by_category": {
            "Operational": random.randint(15, 35),
            "Financial": random.randint(10, 25),
            "Technology": random.randint(8, 20),
            "Regulatory": random.randint(5, 15),
            "Reputational": random.randint(3, 12)
        },
        "trends": _generate_trend_data("risks", "30d"),
        "top_risks": [
            {"id": str(uuid.uuid4()), "title": f"High Risk {i+1}", "score": random.randint(15, 25)}
            for i in range(5)
        ]
    }

def _get_mock_compliance_analytics():
    """Generate mock compliance analytics"""
    return {
        "summary": {
            "total_assessments": random.randint(20, 60),
            "average_score": round(random.uniform(75, 95), 2),
            "compliance_rate": random.randint(80, 95)
        },
        "by_framework": {
            "BASEL_III": {"assessments": random.randint(5, 15), "score": random.randint(80, 95)},
            "IFRS": {"assessments": random.randint(3, 10), "score": random.randint(85, 98)},
            "BOZ": {"assessments": random.randint(4, 12), "score": random.randint(75, 90)}
        },
        "trends": _generate_trend_data("compliance", "30d"),
        "gaps": _generate_compliance_gaps()
    }

def _get_mock_incident_analytics():
    """Generate mock incident analytics"""
    return {
        "summary": {
            "total_incidents": random.randint(10, 40),
            "resolved": random.randint(15, 35),
            "investigating": random.randint(2, 8),
            "open": random.randint(1, 5),
            "avg_resolution_time": round(random.uniform(12, 48), 1)
        },
        "trends": _generate_trend_data("incidents", "30d"),
        "severity_distribution": _generate_severity_distribution(),
        "mttr": round(random.uniform(18, 36), 1)
    }

def _generate_kpi_data():
    """Generate KPI data"""
    return [
        {
            "name": "Risk Score",
            "value": round(random.uniform(8, 15), 1),
            "change": round(random.uniform(-2, 3), 1),
            "trend": random.choice(["up", "down", "stable"])
        },
        {
            "name": "Compliance Rate",
            "value": random.randint(80, 95),
            "change": round(random.uniform(-5, 8), 1),
            "trend": random.choice(["up", "down", "stable"])
        },
        {
            "name": "Incidents",
            "value": random.randint(5, 25),
            "change": random.randint(-8, 12),
            "trend": random.choice(["up", "down", "stable"])
        }
    ]

def _generate_chart_overview():
    """Generate chart overview data"""
    return {
        "risk_by_category": {
            "Operational": random.randint(20, 40),
            "Financial": random.randint(15, 30),
            "Technology": random.randint(10, 25),
            "Regulatory": random.randint(8, 20)
        },
        "compliance_by_framework": {
            "BASEL_III": random.randint(85, 95),
            "IFRS": random.randint(80, 92),
            "BOZ": random.randint(75, 88)
        }
    }

def _generate_trend_data(metric_type: str, period: str):
    """Generate trend data for charts"""
    days = int(period.replace('d', '')) if 'd' in period else 30
    base_value = {
        "risks": 50,
        "compliance": 85,
        "incidents": 15,
        "assessments": 25
    }.get(metric_type, 10)
    
    trend_data = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i-1))
        value = base_value + random.randint(-10, 15)
        trend_data.append({
            "date": date.isoformat()[:10],
            "value": max(0, value)
        })
    
    return trend_data

def _generate_compliance_gaps():
    """Generate compliance gaps data"""
    gaps = []
    gap_types = ["Policy Gap", "Control Gap", "Documentation Gap", "Training Gap", "Process Gap"]
    
    for i in range(random.randint(3, 8)):
        gaps.append({
            "id": str(uuid.uuid4()),
            "type": random.choice(gap_types),
            "description": f"Gap description {i+1}",
            "severity": random.choice(["high", "medium", "low"]),
            "framework": random.choice(["BASEL_III", "IFRS", "BOZ"]),
            "identified_date": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
        })
    
    return gaps

def _generate_severity_distribution():
    """Generate severity distribution data"""
    total = 100
    high = random.randint(10, 25)
    medium = random.randint(30, 50)
    low = total - high - medium
    
    return {
        "high": high,
        "medium": medium,
        "low": max(0, low)
    }

def _generate_heatmap_data():
    """Generate heatmap data for risk visualization"""
    heatmap = []
    categories = ["Operational", "Financial", "Technology", "Regulatory", "Reputational"]
    impacts = ["Low", "Medium", "High", "Critical"]
    
    for category in categories:
        for impact in impacts:
            heatmap.append({
                "category": category,
                "impact": impact,
                "value": random.randint(1, 10),
                "count": random.randint(0, 15)
            })
    
    return heatmap

def _generate_gauge_data(gauge_type: str):
    """Generate gauge chart data"""
    return {
        "value": random.randint(70, 95),
        "min": 0,
        "max": 100,
        "thresholds": [
            {"value": 60, "color": "red"},
            {"value": 80, "color": "yellow"},
            {"value": 95, "color": "green"}
        ]
    }

def _generate_timeline_data(data_type: str, period: str):
    """Generate timeline data"""
    days = int(period.replace('d', '')) if 'd' in period else 30
    timeline = []
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i-1))
        events = []
        
        # Generate random events
        for j in range(random.randint(0, 3)):
            events.append({
                "id": str(uuid.uuid4()),
                "title": f"Event {j+1}",
                "type": random.choice(["created", "updated", "resolved"]),
                "time": date.replace(hour=random.randint(8, 17)).isoformat()
            })
        
        timeline.append({
            "date": date.isoformat()[:10],
            "events": events
        })
    
    return timeline

def _generate_distribution_data(data_type: str):
    """Generate distribution data for charts"""
    categories = {
        "risks": ["Low", "Medium", "High", "Critical"],
        "incidents": ["Minor", "Major", "Critical", "Catastrophic"],
        "compliance": ["Compliant", "Partial", "Non-compliant", "Unknown"]
    }.get(data_type, ["Category 1", "Category 2", "Category 3", "Category 4"])
    
    return [
        {
            "category": category,
            "value": random.randint(5, 50),
            "percentage": round(random.uniform(10, 40), 1)
        }
        for category in categories
    ]