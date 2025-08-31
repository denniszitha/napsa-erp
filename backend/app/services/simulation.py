import numpy as np
from typing import Dict, List, Any
from sqlalchemy.orm import Session
import random
from datetime import datetime, timedelta, timezone

from app.models.risk import Risk
from app.models.control import Control, RiskControl
from app.models.kri import KeyRiskIndicator

class SimulationService:
    
    @staticmethod
    def run_monte_carlo_simulation(
        db: Session,
        risk_id: str,
        iterations: int = 1000
    ) -> Dict[str, Any]:
        """Run Monte Carlo simulation for risk impact"""
        risk = db.query(Risk).filter(Risk.id == risk_id).first()
        if not risk:
            return {"error": "Risk not found"}
        
        # Get controls for this risk
        risk_controls = db.query(RiskControl).filter(
            RiskControl.risk_id == risk_id
        ).join(Control).all()
        
        # Simulation parameters
        base_likelihood = risk.likelihood
        base_impact = risk.impact
        
        # Run simulations
        results = []
        for _ in range(iterations):
            # Add randomness to likelihood and impact
            likelihood_variation = np.random.normal(0, 0.5)
            impact_variation = np.random.normal(0, 0.5)
            
            sim_likelihood = max(1, min(5, base_likelihood + likelihood_variation))
            sim_impact = max(1, min(5, base_impact + impact_variation))
            
            # Apply control effectiveness
            control_reduction = 0
            for rc in risk_controls:
                if rc.control.effectiveness_rating:
                    control_reduction += (rc.control.effectiveness_rating / 100) * 0.2
            
            # Calculate risk score
            inherent_score = sim_likelihood * sim_impact
            residual_score = inherent_score * (1 - min(control_reduction, 0.8))
            
            results.append({
                "inherent": inherent_score,
                "residual": residual_score
            })
        
        # Analyze results
        inherent_scores = [r["inherent"] for r in results]
        residual_scores = [r["residual"] for r in results]
        
        return {
            "risk_id": str(risk_id),
            "risk_title": risk.title,
            "iterations": iterations,
            "inherent_risk": {
                "mean": np.mean(inherent_scores),
                "std": np.std(inherent_scores),
                "min": np.min(inherent_scores),
                "max": np.max(inherent_scores),
                "percentiles": {
                    "p10": np.percentile(inherent_scores, 10),
                    "p50": np.percentile(inherent_scores, 50),
                    "p90": np.percentile(inherent_scores, 90),
                    "p95": np.percentile(inherent_scores, 95)
                }
            },
            "residual_risk": {
                "mean": np.mean(residual_scores),
                "std": np.std(residual_scores),
                "min": np.min(residual_scores),
                "max": np.max(residual_scores),
                "percentiles": {
                    "p10": np.percentile(residual_scores, 10),
                    "p50": np.percentile(residual_scores, 50),
                    "p90": np.percentile(residual_scores, 90),
                    "p95": np.percentile(residual_scores, 95)
                }
            },
            "risk_reduction": {
                "average": np.mean(inherent_scores) - np.mean(residual_scores),
                "percentage": ((np.mean(inherent_scores) - np.mean(residual_scores)) / 
                             np.mean(inherent_scores) * 100)
            }
        }
    
    @staticmethod
    def simulate_risk_scenarios(
        db: Session,
        scenario_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate different risk scenarios"""
        results = []
        
        # Get all active risks
        risks = db.query(Risk).filter(Risk.status == "active").all()
        
        scenarios = [
            {
                "name": "Best Case",
                "likelihood_modifier": -1,
                "impact_modifier": -1,
                "control_effectiveness": 90
            },
            {
                "name": "Expected Case",
                "likelihood_modifier": 0,
                "impact_modifier": 0,
                "control_effectiveness": 70
            },
            {
                "name": "Worst Case",
                "likelihood_modifier": 1,
                "impact_modifier": 1,
                "control_effectiveness": 30
            }
        ]
        
        for scenario in scenarios:
            scenario_results = {
                "scenario_name": scenario["name"],
                "total_risk_score": 0,
                "high_risks_count": 0,
                "critical_risks_count": 0,
                "risk_details": []
            }
            
            for risk in risks:
                # Apply scenario modifiers
                adj_likelihood = max(1, min(5, risk.likelihood + scenario["likelihood_modifier"]))
                adj_impact = max(1, min(5, risk.impact + scenario["impact_modifier"]))
                
                inherent = adj_likelihood * adj_impact
                residual = inherent * (1 - scenario["control_effectiveness"] / 100)
                
                scenario_results["total_risk_score"] += residual
                
                if residual >= 15:
                    scenario_results["critical_risks_count"] += 1
                elif residual >= 10:
                    scenario_results["high_risks_count"] += 1
                
                scenario_results["risk_details"].append({
                    "risk_id": str(risk.id),
                    "risk_title": risk.title,
                    "scenario_score": residual
                })
            
            results.append(scenario_results)
        
        return {
            "simulation_date": datetime.now(timezone.utc).isoformat(),
            "total_risks_analyzed": len(risks),
            "scenarios": results,
            "recommendations": SimulationService._generate_recommendations(results)
        }
    
    @staticmethod
    def _generate_recommendations(scenario_results: List[Dict]) -> List[str]:
        """Generate recommendations based on simulation results"""
        recommendations = []
        
        worst_case = next(s for s in scenario_results if s["scenario_name"] == "Worst Case")
        best_case = next(s for s in scenario_results if s["scenario_name"] == "Best Case")
        
        if worst_case["critical_risks_count"] > 5:
            recommendations.append(
                "Critical Alert: More than 5 risks could become critical in worst-case scenario. "
                "Consider implementing additional preventive controls."
            )
        
        risk_variance = worst_case["total_risk_score"] - best_case["total_risk_score"]
        if risk_variance > 100:
            recommendations.append(
                "High Volatility: Large variance between best and worst case scenarios. "
                "Focus on stabilizing controls and reducing uncertainty."
            )
        
        return recommendations

simulation_service = SimulationService()
