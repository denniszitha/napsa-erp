from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta, timezone
import numpy as np
from collections import defaultdict

from app.models.risk import Risk, RiskStatus, RiskCategoryEnum
from app.models.assessment import RiskAssessment
from app.models.control import Control, ControlStatus
from app.models.kri import KeyRiskIndicator, KRIStatus, KRIMeasurement

class AnalyticsService:
    
    @staticmethod
    def calculate_risk_heatmap(db: Session) -> Dict[str, Any]:
        """Generate risk heatmap data with detailed statistics"""
        heatmap_data = []
        risk_details = defaultdict(list)
        
        # Get all active risks
        risks = db.query(Risk).filter(Risk.status == RiskStatus.active).all()
        
        # Group risks by likelihood and impact
        for risk in risks:
            key = f"{risk.likelihood}_{risk.impact}"
            risk_details[key].append({
                "id": str(risk.id),
                "title": risk.title,
                "category": risk.category.value,
                "inherent_score": risk.inherent_risk_score,
                "residual_score": risk.residual_risk_score or risk.inherent_risk_score
            })
        
        # Create heatmap matrix
        for likelihood in range(1, 6):
            for impact in range(1, 6):
                key = f"{likelihood}_{impact}"
                cell_risks = risk_details.get(key, [])
                
                heatmap_data.append({
                    "likelihood": likelihood,
                    "impact": impact,
                    "risk_count": len(cell_risks),
                    "risk_score": likelihood * impact,
                    "risks": cell_risks,
                    "color": AnalyticsService._get_risk_color(likelihood * impact)
                })
        
        return {
            "heatmap": heatmap_data,
            "total_risks": len(risks),
            "risk_distribution": AnalyticsService._calculate_risk_distribution(risks)
        }
    
    @staticmethod
    def _get_risk_color(score: int) -> str:
        """Get color code based on risk score"""
        if score <= 5:
            return "#4CAF50"  # Green - Low
        elif score <= 10:
            return "#FFEB3B"  # Yellow - Medium
        elif score <= 15:
            return "#FF9800"  # Orange - High
        else:
            return "#F44336"  # Red - Critical
    
    @staticmethod
    def _calculate_risk_distribution(risks: List[Risk]) -> Dict[str, int]:
        """Calculate risk distribution by severity"""
        distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for risk in risks:
            score = risk.inherent_risk_score
            if score <= 5:
                distribution["low"] += 1
            elif score <= 10:
                distribution["medium"] += 1
            elif score <= 15:
                distribution["high"] += 1
            else:
                distribution["critical"] += 1
        
        return distribution
    
    @staticmethod
    def calculate_risk_trends(db: Session, days: int = 30) -> Dict[str, Any]:
        """Calculate risk trends over time"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get assessments over time
        assessments = db.query(
            func.date(RiskAssessment.assessment_date).label('date'),
            func.avg(RiskAssessment.inherent_risk).label('avg_inherent'),
            func.avg(RiskAssessment.residual_risk).label('avg_residual'),
            func.count(RiskAssessment.id).label('count')
        ).filter(
            RiskAssessment.assessment_date >= start_date
        ).group_by(
            func.date(RiskAssessment.assessment_date)
        ).all()
        
        trends = []
        for assessment in assessments:
            trends.append({
                "date": assessment.date.isoformat(),
                "avg_inherent_risk": float(assessment.avg_inherent),
                "avg_residual_risk": float(assessment.avg_residual),
                "assessment_count": assessment.count
            })
        
        return {
            "period_days": days,
            "trends": trends,
            "summary": {
                "trend_direction": AnalyticsService._calculate_trend_direction(trends),
                "risk_reduction": AnalyticsService._calculate_risk_reduction(db)
            }
        }
    
    @staticmethod
    def _calculate_trend_direction(trends: List[Dict]) -> str:
        """Determine if risks are increasing or decreasing"""
        if len(trends) < 2:
            return "stable"
        
        first_avg = trends[0]["avg_inherent_risk"]
        last_avg = trends[-1]["avg_inherent_risk"]
        
        if last_avg > first_avg * 1.1:
            return "increasing"
        elif last_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    @staticmethod
    def _calculate_risk_reduction(db: Session) -> float:
        """Calculate overall risk reduction from controls"""
        risks_with_assessments = db.query(Risk).join(RiskAssessment).all()
        
        if not risks_with_assessments:
            return 0.0
        
        total_reduction = 0
        for risk in risks_with_assessments:
            if risk.assessments:
                latest_assessment = max(risk.assessments, key=lambda a: a.assessment_date)
                if risk.inherent_risk_score > 0:
                    reduction = ((risk.inherent_risk_score - latest_assessment.residual_risk) / 
                               risk.inherent_risk_score) * 100
                    total_reduction += reduction
        
        return round(total_reduction / len(risks_with_assessments), 2)
    
    @staticmethod
    def get_control_effectiveness_analysis(db: Session) -> Dict[str, Any]:
        """Analyze control effectiveness across the organization"""
        controls = db.query(Control).all()
        
        effectiveness_by_type = defaultdict(list)
        effectiveness_by_status = defaultdict(int)
        
        for control in controls:
            effectiveness_by_type[control.type.value].append(
                control.effectiveness_rating or 0
            )
            effectiveness_by_status[control.status.value] += 1
        
        # Calculate averages
        type_analysis = {}
        for control_type, ratings in effectiveness_by_type.items():
            type_analysis[control_type] = {
                "average_effectiveness": np.mean(ratings) if ratings else 0,
                "count": len(ratings),
                "min": min(ratings) if ratings else 0,
                "max": max(ratings) if ratings else 0
            }
        
        return {
            "by_type": type_analysis,
            "by_status": dict(effectiveness_by_status),
            "overall_effectiveness": np.mean([c.effectiveness_rating or 0 for c in controls if c.effectiveness_rating]),
            "controls_needing_attention": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "effectiveness": c.effectiveness_rating,
                    "status": c.status.value
                }
                for c in controls 
                if c.effectiveness_rating and c.effectiveness_rating < 60
            ]
        }
    
    @staticmethod
    def get_kri_analytics(db: Session) -> Dict[str, Any]:
        """Comprehensive KRI analytics"""
        kris = db.query(KeyRiskIndicator).all()
        
        # Status distribution
        status_dist = defaultdict(int)
        breached_kris = []
        trending_kris = []
        
        for kri in kris:
            status_dist[kri.status.value] += 1
            
            # Check if breached
            if kri.status in [KRIStatus.warning, KRIStatus.critical]:
                breached_kris.append({
                    "id": str(kri.id),
                    "name": kri.name,
                    "current_value": kri.current_value,
                    "target_value": kri.target_value,
                    "status": kri.status.value,
                    "breach_percentage": abs((kri.current_value - kri.target_value) / kri.target_value * 100) if kri.current_value and kri.target_value else 0
                })
            
            # Analyze trends
            recent_measurements = db.query(KRIMeasurement).filter(
                KRIMeasurement.kri_id == kri.id
            ).order_by(KRIMeasurement.measurement_date.desc()).limit(10).all()
            
            if len(recent_measurements) >= 3:
                values = [m.value for m in recent_measurements]
                trend = "improving" if values[0] < values[-1] else "deteriorating"
                trending_kris.append({
                    "id": str(kri.id),
                    "name": kri.name,
                    "trend": trend,
                    "measurements": len(recent_measurements)
                })
        
        return {
            "total_kris": len(kris),
            "status_distribution": dict(status_dist),
            "breached_kris": breached_kris,
            "trending_kris": trending_kris,
            "health_score": (status_dist.get("normal", 0) / len(kris) * 100) if kris else 0
        }

analytics_service = AnalyticsService()
