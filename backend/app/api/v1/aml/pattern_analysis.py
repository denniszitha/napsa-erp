"""
Pattern Analysis API endpoints using ClickHouse
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.aml.pattern_analyzer import TransactionPatternAnalyzer, PatternType

router = APIRouter()

class PatternMatchResponse(BaseModel):
    pattern_type: str
    customer_id: int
    confidence_score: float
    details: Dict[str, Any]
    transactions_involved: List[str]
    risk_score: float
    detected_at: datetime

class PatternSummaryResponse(BaseModel):
    total_patterns: int
    by_type: Dict[str, int]
    high_risk_customers: List[Dict[str, Any]]
    avg_confidence: float
    avg_risk_score: float


@router.get("/analyze/all", response_model=List[PatternMatchResponse])
def analyze_all_patterns(
    days: int = Query(30, description="Days to analyze"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    min_risk_score: float = Query(0, description="Minimum risk score threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Run comprehensive pattern analysis using ClickHouse"""
    
    analyzer = TransactionPatternAnalyzer()
    
    try:
        patterns = analyzer.analyze_all_patterns(days, customer_id)
        
        # Filter by minimum risk score
        if min_risk_score > 0:
            patterns = [p for p in patterns if p.risk_score >= min_risk_score]
        
        return [
            PatternMatchResponse(
                pattern_type=p.pattern_type.value,
                customer_id=p.customer_id,
                confidence_score=p.confidence_score,
                details=p.details,
                transactions_involved=p.transactions_involved,
                risk_score=p.risk_score,
                detected_at=p.detected_at
            )
            for p in patterns
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern analysis failed: {str(e)}")


@router.get("/analyze/summary", response_model=PatternSummaryResponse)
def get_pattern_summary(
    days: int = Query(30, description="Days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get summary of all detected patterns"""
    
    analyzer = TransactionPatternAnalyzer()
    
    try:
        summary = analyzer.get_pattern_summary(days)
        return PatternSummaryResponse(**summary)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern summary failed: {str(e)}")


@router.get("/analyze/structuring")
def detect_structuring_patterns(
    days: int = Query(30, description="Days to analyze"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Detect structuring patterns specifically"""
    
    analyzer = TransactionPatternAnalyzer()
    
    try:
        patterns = analyzer._detect_structuring(days, customer_id)
        
        return {
            "pattern_type": "structuring",
            "analysis_period_days": days,
            "matches_found": len(patterns),
            "patterns": [
                {
                    "customer_id": p.customer_id,
                    "confidence_score": p.confidence_score,
                    "risk_score": p.risk_score,
                    "details": p.details,
                    "transaction_count": len(p.transactions_involved)
                }
                for p in patterns
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Structuring analysis failed: {str(e)}")


@router.get("/analyze/layering")
def detect_layering_patterns(
    days: int = Query(30, description="Days to analyze"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Detect layering patterns specifically"""
    
    analyzer = TransactionPatternAnalyzer()
    
    try:
        patterns = analyzer._detect_layering(days, customer_id)
        
        return {
            "pattern_type": "layering",
            "analysis_period_days": days,
            "matches_found": len(patterns),
            "patterns": [
                {
                    "customer_id": p.customer_id,
                    "confidence_score": p.confidence_score,
                    "risk_score": p.risk_score,
                    "details": p.details,
                    "transaction_count": len(p.transactions_involved)
                }
                for p in patterns
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Layering analysis failed: {str(e)}")


@router.get("/analyze/velocity")
def detect_velocity_patterns(
    days: int = Query(30, description="Days to analyze"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Detect transaction velocity anomalies"""
    
    analyzer = TransactionPatternAnalyzer()
    
    try:
        patterns = analyzer._detect_velocity_patterns(days, customer_id)
        
        return {
            "pattern_type": "velocity_anomaly",
            "analysis_period_days": days,
            "matches_found": len(patterns),
            "patterns": [
                {
                    "customer_id": p.customer_id,
                    "confidence_score": p.confidence_score,
                    "risk_score": p.risk_score,
                    "details": p.details,
                    "anomaly_date": p.details.get("anomaly_date"),
                    "z_score": p.details.get("anomaly_z_score")
                }
                for p in patterns
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Velocity analysis failed: {str(e)}")


@router.get("/analyze/dormant")
def detect_dormant_reactivation(
    days: int = Query(30, description="Days to analyze"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Detect dormant account reactivation patterns"""
    
    analyzer = TransactionPatternAnalyzer()
    
    try:
        patterns = analyzer._detect_dormant_reactivation(days, customer_id)
        
        return {
            "pattern_type": "dormant_reactivation",
            "analysis_period_days": days,
            "matches_found": len(patterns),
            "patterns": [
                {
                    "customer_id": p.customer_id,
                    "confidence_score": p.confidence_score,
                    "risk_score": p.risk_score,
                    "dormant_days": p.details.get("dormant_days"),
                    "recent_volume": p.details.get("recent_volume"),
                    "recent_transactions": p.details.get("recent_transaction_count")
                }
                for p in patterns
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dormant analysis failed: {str(e)}")


@router.get("/analyze/round-amounts")
def detect_round_amount_patterns(
    days: int = Query(30, description="Days to analyze"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Detect excessive round amount usage patterns"""
    
    analyzer = TransactionPatternAnalyzer()
    
    try:
        patterns = analyzer._detect_round_amounts(days, customer_id)
        
        return {
            "pattern_type": "round_amounts",
            "analysis_period_days": days,
            "matches_found": len(patterns),
            "patterns": [
                {
                    "customer_id": p.customer_id,
                    "confidence_score": p.confidence_score,
                    "risk_score": p.risk_score,
                    "round_ratio": p.details.get("round_ratio"),
                    "total_transactions": p.details.get("total_transactions"),
                    "round_transactions": p.details.get("round_transactions")
                }
                for p in patterns
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Round amount analysis failed: {str(e)}")


@router.get("/analyze/customer/{customer_id}")
def analyze_customer_patterns(
    customer_id: int,
    days: int = Query(30, description="Days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Comprehensive pattern analysis for a specific customer"""
    
    analyzer = TransactionPatternAnalyzer()
    
    try:
        patterns = analyzer.analyze_all_patterns(days, customer_id)
        
        # Group patterns by type
        patterns_by_type = {}
        for pattern in patterns:
            pattern_type = pattern.pattern_type.value
            if pattern_type not in patterns_by_type:
                patterns_by_type[pattern_type] = []
            
            patterns_by_type[pattern_type].append({
                "confidence_score": pattern.confidence_score,
                "risk_score": pattern.risk_score,
                "details": pattern.details,
                "detected_at": pattern.detected_at.isoformat()
            })
        
        # Calculate overall risk assessment
        if patterns:
            max_risk = max(p.risk_score for p in patterns)
            avg_confidence = sum(p.confidence_score for p in patterns) / len(patterns)
            risk_level = "critical" if max_risk > 80 else "high" if max_risk > 60 else "medium" if max_risk > 40 else "low"
        else:
            max_risk = 0
            avg_confidence = 0
            risk_level = "low"
        
        return {
            "customer_id": customer_id,
            "analysis_period_days": days,
            "overall_assessment": {
                "max_risk_score": max_risk,
                "avg_confidence": avg_confidence,
                "risk_level": risk_level,
                "patterns_detected": len(patterns)
            },
            "patterns_by_type": patterns_by_type,
            "recommendations": _generate_recommendations(patterns_by_type, max_risk)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Customer pattern analysis failed: {str(e)}")


def _generate_recommendations(patterns_by_type: Dict, max_risk_score: float) -> List[str]:
    """Generate recommendations based on detected patterns"""
    
    recommendations = []
    
    if "structuring" in patterns_by_type:
        recommendations.append("Consider filing CTR/STR due to potential structuring activity")
        recommendations.append("Enhanced monitoring for transactions near reporting thresholds")
    
    if "layering" in patterns_by_type:
        recommendations.append("Investigate complex transaction chains for money laundering")
        recommendations.append("Review relationships with counterparties in the chain")
    
    if "velocity" in patterns_by_type:
        recommendations.append("Review recent high-velocity transaction periods")
        recommendations.append("Consider temporary transaction limits pending investigation")
    
    if "dormant_reactivation" in patterns_by_type:
        recommendations.append("Conduct enhanced due diligence on recently reactivated dormant accounts")
        recommendations.append("Verify source of funds for sudden large deposits")
    
    if "round_amounts" in patterns_by_type:
        recommendations.append("Investigate excessive use of round amounts")
        recommendations.append("Check for coordination with other customers using similar patterns")
    
    if max_risk_score > 80:
        recommendations.append("URGENT: Escalate to compliance manager for immediate review")
        recommendations.append("Consider account restrictions pending investigation")
    elif max_risk_score > 60:
        recommendations.append("Schedule enhanced monitoring and review within 48 hours")
    
    return recommendations