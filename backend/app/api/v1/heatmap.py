"""
Risk Heat Map API endpoints
Provides data for 5x5 risk matrix visualization
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, and_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.risk import Risk, RiskStatus
from app.models.risk_category import RiskCategory

router = APIRouter(prefix="/heatmap", tags=["Heat Map"])

@router.get("/matrix", response_model=Dict[str, Any])
def get_risk_heat_map(
    department_id: Optional[int] = None,
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    risk_type: str = Query(default="inherent", description="inherent or residual"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get risk heat map data for 5x5 matrix visualization.
    Returns risk counts and details for each cell in the matrix.
    """
    
    # Base query
    query = db.query(Risk)
    
    # Apply filters
    if department_id:
        query = query.filter(Risk.organizational_unit_id == department_id)
    if category_id:
        query = query.filter(Risk.category_id == category_id)
    if status:
        query = query.filter(Risk.status == status)
    
    # Get all matching risks
    risks = query.all()
    
    # Initialize 5x5 matrix (likelihood x impact)
    matrix = {}
    for likelihood in range(1, 6):
        for impact in range(1, 6):
            matrix[f"{likelihood},{impact}"] = {
                "likelihood": likelihood,
                "impact": impact,
                "count": 0,
                "risks": [],
                "risk_score": likelihood * impact,
                "risk_level": get_risk_level(likelihood * impact)
            }
    
    # Populate matrix with risks
    for risk in risks:
        if risk_type == "inherent":
            likelihood = risk.likelihood or 1
            impact = risk.impact or 1
        else:  # residual
            # Calculate residual likelihood and impact based on residual score
            if risk.residual_risk_score:
                # Approximate residual likelihood and impact
                residual_total = risk.residual_risk_score
                likelihood = min(5, max(1, int(residual_total / 5) + 1))
                impact = min(5, max(1, int(residual_total / likelihood)))
            else:
                likelihood = risk.likelihood or 1
                impact = risk.impact or 1
        
        key = f"{likelihood},{impact}"
        if key in matrix:
            matrix[key]["count"] += 1
            matrix[key]["risks"].append({
                "id": risk.id,
                "title": risk.title,
                "department": risk.department,
                "category": risk.category,
                "status": risk.status,
                "inherent_score": risk.inherent_risk_score,
                "residual_score": risk.residual_risk_score
            })
    
    # Calculate statistics
    total_risks = len(risks)
    high_risks = sum(1 for r in risks if (r.inherent_risk_score or 0) >= 15)
    medium_risks = sum(1 for r in risks if 8 <= (r.inherent_risk_score or 0) < 15)
    low_risks = sum(1 for r in risks if (r.inherent_risk_score or 0) < 8)
    
    return {
        "matrix": matrix,
        "statistics": {
            "total_risks": total_risks,
            "high_risks": high_risks,
            "medium_risks": medium_risks,
            "low_risks": low_risks,
            "risk_type": risk_type
        },
        "legend": {
            "low": {"range": "1-7", "color": "#28a745", "description": "Low Risk"},
            "medium": {"range": "8-14", "color": "#ffc107", "description": "Medium Risk"},
            "high": {"range": "15-19", "color": "#fd7e14", "description": "High Risk"},
            "critical": {"range": "20-25", "color": "#dc3545", "description": "Critical Risk"}
        }
    }

@router.get("/department-comparison", response_model=Dict[str, Any])
def get_department_heat_map_comparison(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get heat map comparison across all departments.
    Shows risk distribution for each department.
    """
    
    # Query to get risk counts by department and risk level
    results = db.query(
        Risk.department,
        Risk.organizational_unit_id,
        func.count(Risk.id).label('total'),
        func.sum(case((Risk.inherent_risk_score >= 15, 1), else_=0)).label('high'),
        func.sum(case((and_(Risk.inherent_risk_score >= 8, Risk.inherent_risk_score < 15), 1), else_=0)).label('medium'),
        func.sum(case((Risk.inherent_risk_score < 8, 1), else_=0)).label('low')
    ).group_by(Risk.department, Risk.organizational_unit_id).all()
    
    departments = []
    for result in results:
        departments.append({
            "department": result.department,
            "department_id": result.organizational_unit_id,
            "total_risks": result.total,
            "high_risks": result.high or 0,
            "medium_risks": result.medium or 0,
            "low_risks": result.low or 0,
            "risk_distribution": {
                "high_percentage": ((result.high or 0) / result.total * 100) if result.total > 0 else 0,
                "medium_percentage": ((result.medium or 0) / result.total * 100) if result.total > 0 else 0,
                "low_percentage": ((result.low or 0) / result.total * 100) if result.total > 0 else 0
            }
        })
    
    return {
        "departments": departments,
        "total_departments": len(departments)
    }

@router.get("/trend", response_model=Dict[str, Any])
def get_heat_map_trend(
    months: int = Query(default=6, description="Number of months to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get heat map trend data over time.
    Shows how risk distribution has changed.
    """
    
    trends = []
    current_date = datetime.utcnow()
    
    for i in range(months):
        # Calculate date for each month
        month_date = current_date - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        
        # Get risks created up to this month
        risks = db.query(Risk).filter(Risk.created_at <= month_date).all()
        
        # Calculate risk distribution
        high = sum(1 for r in risks if (r.inherent_risk_score or 0) >= 15)
        medium = sum(1 for r in risks if 8 <= (r.inherent_risk_score or 0) < 15)
        low = sum(1 for r in risks if (r.inherent_risk_score or 0) < 8)
        total = len(risks)
        
        trends.append({
            "month": month_start.strftime("%B %Y"),
            "total_risks": total,
            "high_risks": high,
            "medium_risks": medium,
            "low_risks": low,
            "average_risk_score": sum((r.inherent_risk_score or 0) for r in risks) / total if total > 0 else 0
        })
    
    # Reverse to show chronological order
    trends.reverse()
    
    return {
        "trend_data": trends,
        "period": f"Last {months} months",
        "analysis": {
            "risk_growth": trends[-1]["total_risks"] - trends[0]["total_risks"] if trends else 0,
            "high_risk_change": trends[-1]["high_risks"] - trends[0]["high_risks"] if trends else 0,
            "trend_direction": "increasing" if trends and trends[-1]["total_risks"] > trends[0]["total_risks"] else "decreasing"
        }
    }

@router.get("/category-matrix", response_model=Dict[str, Any])
def get_category_heat_map(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get heat map data grouped by risk categories.
    """
    
    # Get all risk categories
    categories = db.query(RiskCategory).all()
    
    category_data = []
    for category in categories:
        # Get risks for this category
        risks = db.query(Risk).filter(Risk.category_id == category.id).all()
        
        # Build mini heat map for category
        matrix = {}
        for likelihood in range(1, 6):
            for impact in range(1, 6):
                key = f"{likelihood},{impact}"
                matrix[key] = 0
        
        for risk in risks:
            key = f"{risk.likelihood or 1},{risk.impact or 1}"
            if key in matrix:
                matrix[key] += 1
        
        category_data.append({
            "category_id": category.id,
            "category_name": category.name,
            "total_risks": len(risks),
            "matrix": matrix,
            "average_score": sum((r.inherent_risk_score or 0) for r in risks) / len(risks) if risks else 0
        })
    
    return {
        "categories": category_data,
        "total_categories": len(categories)
    }

@router.get("/risk-velocity", response_model=Dict[str, Any])
def get_risk_velocity_heat_map(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get heat map with risk velocity (speed of risk materialization).
    """
    
    # Get risks with velocity information
    risks = db.query(Risk).filter(Risk.status == 'active').all()
    
    velocity_matrix = {
        "slow": [],  # > 6 months
        "medium": [],  # 3-6 months
        "fast": [],  # 1-3 months
        "very_fast": []  # < 1 month
    }
    
    for risk in risks:
        # Calculate velocity based on various factors
        # This is a simplified calculation - you may want to add a velocity field to the Risk model
        risk_data = {
            "id": risk.id,
            "title": risk.title,
            "likelihood": risk.likelihood,
            "impact": risk.impact,
            "score": risk.inherent_risk_score
        }
        
        # Assign velocity based on risk characteristics
        if risk.likelihood >= 4 and risk.impact >= 4:
            velocity_matrix["very_fast"].append(risk_data)
        elif risk.likelihood >= 3 and risk.impact >= 3:
            velocity_matrix["fast"].append(risk_data)
        elif risk.likelihood >= 2:
            velocity_matrix["medium"].append(risk_data)
        else:
            velocity_matrix["slow"].append(risk_data)
    
    return {
        "velocity_matrix": velocity_matrix,
        "statistics": {
            "slow_velocity": len(velocity_matrix["slow"]),
            "medium_velocity": len(velocity_matrix["medium"]),
            "fast_velocity": len(velocity_matrix["fast"]),
            "very_fast_velocity": len(velocity_matrix["very_fast"]),
            "total_active_risks": len(risks)
        }
    }

def get_risk_level(score: int) -> str:
    """Determine risk level based on score"""
    if score >= 20:
        return "critical"
    elif score >= 15:
        return "high"
    elif score >= 8:
        return "medium"
    else:
        return "low"