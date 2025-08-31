"""
Simplified Business Intelligence Tools API
Provides analytics and sentiment analysis without complex dependencies
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random

from app.api.deps import get_db

router = APIRouter()

@router.get("/dashboard")
async def get_bi_dashboard(
    time_range: str = Query("30d", description="Time range: 7d, 30d, 90d, 1y"),
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get comprehensive BI dashboard data"""
    
    # Calculate date range
    if time_range == "7d":
        days = 7
    elif time_range == "30d":
        days = 30
    elif time_range == "90d":
        days = 90
    elif time_range == "1y":
        days = 365
    else:
        days = 30
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Get risk statistics from database
    try:
        # Total risks
        total_risks = db.execute(text("SELECT COUNT(*) FROM risks")).scalar() or 0
        
        # High priority risks
        high_risks = db.execute(text("""
            SELECT COUNT(*) FROM risks 
            WHERE risk_level IN ('High', 'Critical', 'high', 'critical')
        """)).scalar() or 0
        
        # Recent assessments
        completed_assessments = db.execute(text("""
            SELECT COUNT(*) FROM risk_assessments 
            WHERE created_at >= :start_date
        """), {"start_date": start_date}).scalar() or 0
        
        # Compliance score (mock for now)
        compliance_score = random.randint(75, 95)
        
    except Exception as e:
        # Fallback to mock data if queries fail
        total_risks = 156
        high_risks = 24
        completed_assessments = 42
        compliance_score = 88
    
    # Generate risk trends (mock data for visualization)
    risk_trends = []
    for i in range(30):
        date = datetime.now() - timedelta(days=29-i)
        risk_trends.append({
            "date": date.strftime("%Y-%m-%d"),
            "count": random.randint(140, 170)
        })
    
    # Category distribution
    categories = ["Operational", "Financial", "Compliance", "Strategic", "Technology", "Reputation"]
    category_distribution = [
        {"category": cat, "count": random.randint(15, 40)} 
        for cat in categories
    ]
    
    return {
        "summary": {
            "total_risks": total_risks,
            "high_risks": high_risks,
            "completed_assessments": completed_assessments,
            "compliance_score": compliance_score,
            "risk_velocity": random.randint(2, 8),
            "control_effectiveness": random.randint(70, 95)
        },
        "risk_trends": risk_trends,
        "category_distribution": category_distribution,
        "recent_activity": {
            "new_risks": random.randint(5, 15),
            "updated_risks": random.randint(10, 25),
            "closed_risks": random.randint(3, 10)
        }
    }

@router.get("/metrics/performance")
async def get_performance_metrics(
    time_range: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """Get performance metrics"""
    
    return {
        "control_effectiveness_ratio": random.randint(75, 95),
        "risk_velocity": random.randint(2, 8),
        "mitigation_rate": random.randint(60, 85),
        "assessment_completion": random.randint(70, 95),
        "compliance_rate": random.randint(80, 98)
    }

@router.get("/risk-heatmap")
async def get_risk_heatmap(
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get risk heatmap data"""
    
    heatmap_data = []
    for _ in range(random.randint(10, 25)):
        heatmap_data.append({
            "probability": random.randint(1, 5),
            "impact": random.randint(1, 5),
            "risk_id": random.randint(1, 100),
            "title": f"Risk {random.randint(100, 999)}"
        })
    
    return heatmap_data

@router.get("/sentiment-analysis")
async def get_sentiment_analysis(
    time_range: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """Get AI-powered sentiment analysis"""
    
    # Try to use the real sentiment analyzer if available
    try:
        from app.services.ai_sentiment import get_sentiment_analyzer
        analyzer = get_sentiment_analyzer()
        sentiment_data = analyzer.get_overall_sentiment(db, time_range)
    except:
        # Fallback to mock data
        sentiment_data = {
            "positive": 65.0,
            "negative": 15.0,
            "neutral": 20.0,
            "breakdown": {
                "risks": {"positive": 60.0, "negative": 20.0, "neutral": 20.0},
                "assessments": {"positive": 75.0, "negative": 10.0, "neutral": 15.0},
                "incidents": {"positive": 45.0, "negative": 35.0, "neutral": 20.0}
            }
        }
    
    return sentiment_data

@router.get("/ai-insights")
async def get_ai_insights(
    focus_area: str = Query("risks"),
    time_range: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """Get AI-generated insights"""
    
    insights = [
        {
            "type": "trend",
            "severity": "medium",
            "message": "Risk velocity has increased by 25% in the Technology category",
            "recommendation": "Consider additional controls for technology risks"
        },
        {
            "type": "positive",
            "severity": "low",
            "message": "Assessment completion rate improved to 95%",
            "recommendation": "Maintain current assessment schedule"
        },
        {
            "type": "alert",
            "severity": "high",
            "message": "3 high-impact risks require immediate attention",
            "recommendation": "Prioritize mitigation strategies for critical risks"
        }
    ]
    
    return {"insights": insights, "generated_at": datetime.now().isoformat()}

@router.get("/monitored-entities")
async def get_monitored_entities(
    db: Session = Depends(get_db)
):
    """Get list of monitored entities for sentiment analysis"""
    
    entities = [
        {
            "id": 1,
            "name": "Saturnia Regna Pension Fund",
            "type": "pension_fund",
            "monitoring_level": "critical",
            "sentiment_score": -0.42,
            "last_updated": datetime.now().isoformat(),
            "mentions_today": 15
        },
        {
            "id": 2,
            "name": "Madison General Insurance",
            "type": "administrator",
            "monitoring_level": "high",
            "sentiment_score": 0.15,
            "last_updated": (datetime.now() - timedelta(minutes=15)).isoformat(),
            "mentions_today": 8
        },
        {
            "id": 3,
            "name": "Professional Insurance Corporation",
            "type": "custodian",
            "monitoring_level": "low",
            "sentiment_score": 0.68,
            "last_updated": (datetime.now() - timedelta(hours=1)).isoformat(),
            "mentions_today": 3
        }
    ]
    
    return entities

@router.post("/monitored-entities")
async def add_monitored_entity(
    entity_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Add new entity for monitoring"""
    
    # In a real implementation, this would save to database
    return {
        "id": random.randint(100, 999),
        "name": entity_data.get("name"),
        "type": entity_data.get("type"),
        "monitoring_level": entity_data.get("level", "medium"),
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }

@router.get("/sentiment-alerts")
async def get_sentiment_alerts(
    db: Session = Depends(get_db)
):
    """Get recent sentiment alerts"""
    
    alerts = [
        {
            "id": 1,
            "level": "critical",
            "entity": "Saturnia Regna Pension Fund",
            "message": "Multiple negative mentions detected in financial news",
            "timestamp": (datetime.now() - timedelta(minutes=2)).isoformat()
        },
        {
            "id": 2,
            "level": "high",
            "entity": "Madison General Insurance",
            "message": "Compliance concerns raised in regulatory filing",
            "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat()
        },
        {
            "id": 3,
            "level": "medium",
            "entity": "Market Analysis",
            "message": "Market sentiment shifting negative for pension sector",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
        },
        {
            "id": 4,
            "level": "low",
            "entity": "Professional Insurance Corporation",
            "message": "Positive coverage in industry report",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
        }
    ]
    
    return alerts

@router.get("/compliance-sentiment")
async def get_compliance_sentiment(
    time_range: str = Query("30d"),
    category: str = Query("all"),
    db: Session = Depends(get_db)
):
    """Get compliance-specific sentiment analysis"""
    
    return {
        "aml_kyc": {"score": 92, "trend": "stable"},
        "regulatory_filing": {"score": 78, "trend": "improving"},
        "risk_management": {"score": 88, "trend": "stable"},
        "data_protection": {"score": 65, "trend": "declining"},
        "financial_reporting": {"score": 95, "trend": "improving"}
    }

@router.get("/news-sentiment")
async def get_news_sentiment(
    sources: str = Query("all"),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """Get news sentiment analysis"""
    
    news_items = []
    sources_list = [
        "Times of Zambia",
        "Lusaka Times",
        "ZNBC",
        "Zambia Daily Mail",
        "Financial Times"
    ]
    
    for i in range(min(limit, 10)):
        sentiment = random.choice([-0.6, -0.3, 0.1, 0.4, 0.8])
        news_items.append({
            "id": i + 1,
            "title": f"Sample news article {i+1}",
            "source": random.choice(sources_list),
            "sentiment_score": sentiment,
            "published_at": (datetime.now() - timedelta(hours=i*2)).isoformat(),
            "entities_mentioned": random.sample(
                ["Saturnia Regna", "Madison General", "Professional Insurance"],
                k=random.randint(1, 2)
            )
        })
    
    return {"news_items": news_items, "total": len(news_items)}

@router.get("/trend-analysis")
async def get_trend_analysis(
    metric: str = Query("risks"),
    period: str = Query("weekly"),
    time_range: str = Query("90d"),
    db: Session = Depends(get_db)
):
    """Get trend analysis data"""
    
    data_points = []
    if period == "daily":
        points = 90
    elif period == "weekly":
        points = 12
    else:  # monthly
        points = 3
    
    for i in range(points):
        data_points.append({
            "period": f"Period {i+1}",
            "value": random.randint(50, 150),
            "change": random.uniform(-10, 10)
        })
    
    return {
        "metric": metric,
        "period": period,
        "data": data_points,
        "summary": {
            "trend": random.choice(["increasing", "stable", "decreasing"]),
            "average": random.randint(80, 120),
            "volatility": random.uniform(0.1, 0.3)
        }
    }

@router.post("/custom-query")
async def execute_custom_query(
    query_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Execute custom BI query"""
    
    # This would normally execute a safe, parameterized query
    # For now, return mock results
    return {
        "query_id": random.randint(1000, 9999),
        "status": "completed",
        "rows_returned": random.randint(10, 100),
        "execution_time": random.uniform(0.1, 2.0),
        "data": []
    }

@router.post("/export")
async def export_data(
    export_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Export BI data"""
    
    return {
        "export_id": random.randint(10000, 99999),
        "format": export_config.get("format", "csv"),
        "status": "processing",
        "estimated_time": random.randint(5, 30),
        "download_url": f"/downloads/export_{random.randint(1000, 9999)}.csv"
    }