from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.risk import Risk, RiskCategoryEnum, RiskStatus
from app.models.kri import KeyRiskIndicator, KRIStatus
from app.models.compliance import ComplianceRequirement, ComplianceMapping
from app.models.assessment import RiskAssessment
from app.models.control import RiskControl

router = APIRouter()

# Add your existing endpoints here...

@router.get("/risk-summary", response_model=Dict[str, Any])
def get_risk_summary_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get comprehensive risk summary analytics"""
    risks = db.query(Risk).all()
    
    if not risks:
        return {
            "total_risks": 0,
            "average_risk_score": 0,
            "by_category": {},
            "by_status": {},
            "top_risks": []
        }
    
    risk_scores = [(r.likelihood or 0) * (r.impact or 0) for r in risks]
    
    # Top 5 risks
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
    }
