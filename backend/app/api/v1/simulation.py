from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any, List

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.risk import Risk
from app.services.simulation import simulation_service

router = APIRouter()

@router.post("/monte-carlo/{risk_id}")
def run_monte_carlo_simulation(
    risk_id: UUID,
    iterations: int = Query(1000, ge=100, le=10000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    ):
    """Run Monte Carlo simulation for a specific risk"""
    return simulation_service.run_monte_carlo_simulation(db, str(risk_id), iterations)

@router.post("/scenarios")
def simulate_risk_scenarios(
    scenario_config: dict = {},
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    ):
    """Simulate different risk scenarios (best/expected/worst case)"""
    return simulation_service.simulate_risk_scenarios(db, scenario_config)

@router.get("/what-if/{risk_id}")
def what_if_analysis(
    risk_id: UUID,
    new_likelihood: int = Query(..., ge=1, le=5),
    new_impact: int = Query(..., ge=1, le=5),
    control_improvement: float = Query(0, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    ):
    """Perform what-if analysis for risk changes"""
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        return {"error": "Risk not found"}
    
    # Current state
    current_score = risk.inherent_risk_score
    current_residual = risk.residual_risk_score or current_score
    
    # What-if state
    new_inherent = new_likelihood * new_impact
    new_residual = new_inherent * (1 - control_improvement / 100)
    
    return {
        "risk_id": str(risk_id),
        "risk_title": risk.title,
        "current_state": {
            "likelihood": risk.likelihood,
            "impact": risk.impact,
            "inherent_score": current_score,
            "residual_score": current_residual
        },
        "what_if_state": {
            "likelihood": new_likelihood,
            "impact": new_impact,
            "inherent_score": new_inherent,
            "residual_score": new_residual,
            "control_improvement": control_improvement
        },
        "changes": {
            "inherent_change": new_inherent - current_score,
            "inherent_change_percent": ((new_inherent - current_score) / current_score * 100) if current_score > 0 else 0,
            "residual_change": new_residual - current_residual,
            "residual_change_percent": ((new_residual - current_residual) / current_residual * 100) if current_residual > 0 else 0
        },
        "recommendation": "Implement changes" if new_residual < current_residual else "Maintain current state"
    }

@router.post("/scenario-analysis", response_model=Dict[str, Any])
def run_scenario_analysis(
    scenario_input: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
    """Run scenario analysis on multiple risks"""
    scenario_name = scenario_input.get("name", "Custom Scenario")
    description = scenario_input.get("description", "")
    risk_adjustments = scenario_input.get("risk_adjustments", [])
    
    # Get current risk baseline
    all_risks = db.query(Risk).all()
    baseline_score = sum((r.likelihood or 0) * (r.impact or 0) for r in all_risks)
    
    # Apply scenario adjustments
    scenario_results = {
        "scenario_name": scenario_name,
        "description": description,
        "baseline_risk_score": baseline_score,
        "scenario_risk_score": 0,
        "impacted_risks": [],
        "risk_score_change": 0,
        "risk_score_change_percentage": 0,
        "category_impact": {},
        "department_impact": {},
        "recommendations": []
    }
    
    # Track adjusted scores
    adjusted_scores = {}
    
    for adjustment in risk_adjustments:
        risk_id = adjustment.get("risk_id")
        new_likelihood = adjustment.get("likelihood")
        new_impact = adjustment.get("impact")
        
        risk = db.query(Risk).filter(Risk.id == risk_id).first()
        if risk:
            original_score = (risk.likelihood or 0) * (risk.impact or 0)
            adjusted_score = (new_likelihood or risk.likelihood or 0) * (new_impact or risk.impact or 0)
            adjusted_scores[risk_id] = adjusted_score
            
            scenario_results["impacted_risks"].append({
                "risk_id": str(risk_id),
                "risk_title": risk.title,
                "original_likelihood": risk.likelihood,
                "original_impact": risk.impact,
                "original_score": original_score,
                "scenario_likelihood": new_likelihood or risk.likelihood,
                "scenario_impact": new_impact or risk.impact,
                "scenario_score": adjusted_score,
                "score_change": adjusted_score - original_score,
                "change_percentage": round(((adjusted_score - original_score) / original_score * 100) if original_score else 0, 2)
            })
    
    # Calculate scenario total
    scenario_total = baseline_score
    for risk in all_risks:
        if str(risk.id) in adjusted_scores:
            # Replace original score with adjusted score
            original_score = (risk.likelihood or 0) * (risk.impact or 0)
            scenario_total = scenario_total - original_score + adjusted_scores[str(risk.id)]
    
    scenario_results["scenario_risk_score"] = scenario_total
    scenario_results["risk_score_change"] = scenario_total - baseline_score
    scenario_results["risk_score_change_percentage"] = round(
        ((scenario_total - baseline_score) / baseline_score * 100) if baseline_score else 0, 2
    )
    
    # Analyze impact by category
    categories = {}
    for risk in all_risks:
        if risk.category:
            cat = risk.category.value
            if cat not in categories:
                categories[cat] = {"original": 0, "scenario": 0}
            
            original = (risk.likelihood or 0) * (risk.impact or 0)
            scenario = adjusted_scores.get(str(risk.id), original)
            
            categories[cat]["original"] += original
            categories[cat]["scenario"] += scenario
    
    for cat, scores in categories.items():
        scenario_results["category_impact"][cat] = {
            "original_score": scores["original"],
            "scenario_score": scores["scenario"],
            "change": scores["scenario"] - scores["original"],
            "change_percentage": round(
                ((scores["scenario"] - scores["original"]) / scores["original"] * 100) 
                if scores["original"] else 0, 2
            )
        }
    
    # Analyze impact by department
    departments = {}
    for risk in all_risks:
        if risk.department:
            dept = risk.department
            if dept not in departments:
                departments[dept] = {"original": 0, "scenario": 0}
            
            original = (risk.likelihood or 0) * (risk.impact or 0)
            scenario = adjusted_scores.get(str(risk.id), original)
            
            departments[dept]["original"] += original
            departments[dept]["scenario"] += scenario
    
    for dept, scores in departments.items():
        scenario_results["department_impact"][dept] = {
            "original_score": scores["original"],
            "scenario_score": scores["scenario"],
            "change": scores["scenario"] - scores["original"]
        }
    
    # Generate recommendations
    if scenario_results["risk_score_change_percentage"] > 20:
        scenario_results["recommendations"].append(
            "Significant risk increase detected. Consider implementing additional controls."
        )
    
    # Find most impacted risks
    most_impacted = sorted(
        scenario_results["impacted_risks"], 
        key=lambda x: abs(x["score_change"]), 
        reverse=True
    )[:3]
    
    for risk in most_impacted:
        if risk["score_change"] > 0:
            scenario_results["recommendations"].append(
                f"Priority attention needed for '{risk['risk_title']}' - risk increased by {risk['change_percentage']}%"
            )
    
    # Category-specific recommendations
    for cat, impact in scenario_results["category_impact"].items():
        if impact["change_percentage"] > 30:
            scenario_results["recommendations"].append(
                f"Critical attention needed for {cat} risks - increased by {impact['change_percentage']}%"
            )
    
    return scenario_results