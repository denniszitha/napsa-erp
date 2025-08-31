from typing import Dict, List, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

from app.models.risk import Risk, RiskCategoryEnum
from app.models.control import RiskControl
from app.models.assessment import RiskAssessment

class CorrelationService:
    
    @staticmethod
    def calculate_risk_correlations(db: Session) -> Dict[str, Any]:
        """Calculate correlations between risks based on various factors"""
        risks = db.query(Risk).all()
        correlations = []
        
        for i, risk1 in enumerate(risks):
            for risk2 in risks[i+1:]:
                correlation = CorrelationService._calculate_correlation(risk1, risk2, db)
                if correlation["score"] > 0.3:  # Only include significant correlations
                    correlations.append({
                        "risk1": {
                            "id": str(risk1.id),
                            "title": risk1.title,
                            "category": risk1.category.value
                        },
                        "risk2": {
                            "id": str(risk2.id),
                            "title": risk2.title,
                            "category": risk2.category.value
                        },
                        "correlation_score": correlation["score"],
                        "factors": correlation["factors"]
                    })
        
        # Sort by correlation score
        correlations.sort(key=lambda x: x["correlation_score"], reverse=True)
        
        return {
            "correlations": correlations[:20],  # Top 20 correlations
            "risk_clusters": CorrelationService._identify_risk_clusters(correlations),
            "summary": {
                "total_correlations": len(correlations),
                "high_correlations": len([c for c in correlations if c["correlation_score"] > 0.7]),
                "medium_correlations": len([c for c in correlations if 0.4 <= c["correlation_score"] <= 0.7])
            }
        }
    
    @staticmethod
    def _calculate_correlation(risk1: Risk, risk2: Risk, db: Session) -> Dict[str, Any]:
        """Calculate correlation between two risks"""
        factors = []
        scores = []
        
        # Category correlation
        if risk1.category == risk2.category:
            factors.append("same_category")
            scores.append(0.3)
        
        # Department correlation
        if risk1.department == risk2.department:
            factors.append("same_department")
            scores.append(0.2)
        
        # Shared controls correlation
        risk1_controls = db.query(RiskControl).filter(RiskControl.risk_id == risk1.id).all()
        risk2_controls = db.query(RiskControl).filter(RiskControl.risk_id == risk2.id).all()
        
        risk1_control_ids = {rc.control_id for rc in risk1_controls}
        risk2_control_ids = {rc.control_id for rc in risk2_controls}
        
        shared_controls = risk1_control_ids.intersection(risk2_control_ids)
        if shared_controls:
            factors.append(f"shared_controls_{len(shared_controls)}")
            scores.append(min(0.4, len(shared_controls) * 0.1))
        
        # Risk score similarity
        score_diff = abs(risk1.inherent_risk_score - risk2.inherent_risk_score)
        if score_diff <= 5:
            factors.append("similar_risk_score")
            scores.append(0.2)
        
        # Impact correlation (if both high impact)
        if risk1.impact >= 4 and risk2.impact >= 4:
            factors.append("both_high_impact")
            scores.append(0.3)
        
        return {
            "score": min(1.0, sum(scores)),
            "factors": factors
        }
    
    @staticmethod
    def _identify_risk_clusters(correlations: List[Dict]) -> List[Dict[str, Any]]:
        """Identify clusters of related risks"""
        # Build adjacency graph
        risk_connections = defaultdict(set)
        
        for corr in correlations:
            if corr["correlation_score"] > 0.5:
                risk1_id = corr["risk1"]["id"]
                risk2_id = corr["risk2"]["id"]
                risk_connections[risk1_id].add(risk2_id)
                risk_connections[risk2_id].add(risk1_id)
        
        # Find clusters using simple connected components
        visited = set()
        clusters = []
        
        for risk_id in risk_connections:
            if risk_id not in visited:
                cluster = CorrelationService._dfs_cluster(risk_id, risk_connections, visited)
                if len(cluster) > 2:  # Only include clusters with 3+ risks
                    clusters.append({
                        "cluster_id": len(clusters) + 1,
                        "risk_ids": list(cluster),
                        "size": len(cluster)
                    })
        
        return clusters
    
    @staticmethod
    def _dfs_cluster(start: str, connections: Dict, visited: set) -> set:
        """Depth-first search to find connected components"""
        cluster = set()
        stack = [start]
        
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                cluster.add(node)
                stack.extend(connections[node] - visited)
        
        return cluster
    
    @staticmethod
    def get_risk_impact_analysis(db: Session, risk_id: str) -> Dict[str, Any]:
        """Analyze the potential cascade impact of a risk"""
        risk = db.query(Risk).filter(Risk.id == risk_id).first()
        if not risk:
            return {"error": "Risk not found"}
        
        # Get directly connected risks
        risk_controls = db.query(RiskControl).filter(RiskControl.risk_id == risk_id).all()
        control_ids = [rc.control_id for rc in risk_controls]
        
        # Find other risks affected by same controls
        affected_risks = db.query(Risk).join(RiskControl).filter(
            and_(
                RiskControl.control_id.in_(control_ids),
                Risk.id != risk_id
            )
        ).distinct().all()
        
        # Calculate impact scores
        impact_analysis = {
            "source_risk": {
                "id": str(risk.id),
                "title": risk.title,
                "inherent_score": risk.inherent_risk_score
            },
            "directly_affected_risks": [
                {
                    "id": str(r.id),
                    "title": r.title,
                    "impact_score": CorrelationService._calculate_impact_score(risk, r),
                    "shared_controls": len([rc for rc in risk_controls if rc.risk_id == r.id])
                }
                for r in affected_risks
            ],
            "total_potential_impact": sum([r.inherent_risk_score for r in affected_risks]) + risk.inherent_risk_score,
            "cascade_risk_level": "high" if len(affected_risks) > 5 else "medium" if len(affected_risks) > 2 else "low"
        }
        
        return impact_analysis
    
    @staticmethod
    def _calculate_impact_score(source_risk: Risk, target_risk: Risk) -> float:
        """Calculate impact score between risks"""
        base_impact = target_risk.inherent_risk_score
        
        # Adjust based on categories
        if source_risk.category == target_risk.category:
            base_impact *= 1.2
        
        # Adjust based on departments
        if source_risk.department == target_risk.department:
            base_impact *= 1.1
        
        return round(base_impact, 2)

correlation_service = CorrelationService()
