"""
Risk Calculation Service
Handles dynamic calculation of risk scores based on control effectiveness
"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.risk import Risk
from app.models.control import Control, RiskControl, ControlType
from app.models.assessment import RiskAssessment

logger = logging.getLogger(__name__)


class RiskCalculationService:
    """Service for calculating risk scores with control effectiveness"""
    
    # Control type effectiveness multipliers (how much each type contributes)
    CONTROL_TYPE_WEIGHTS = {
        "preventive": 0.40,    # 40% - Prevents risk from occurring
        "detective": 0.25,     # 25% - Detects when risk occurs
        "corrective": 0.20,    # 20% - Corrects after occurrence
        "compensating": 0.15   # 15% - Alternative controls
    }
    
    # Control overlap factors (combined effectiveness when multiple types exist)
    CONTROL_OVERLAP_BONUS = {
        ("preventive", "detective"): 0.10,      # 10% bonus for P+D combination
        ("preventive", "corrective"): 0.05,     # 5% bonus for P+C combination
        ("detective", "corrective"): 0.08,      # 8% bonus for D+C combination
        ("preventive", "detective", "corrective"): 0.15  # 15% bonus for all three
    }
    
    @classmethod
    def calculate_aggregate_control_effectiveness(
        cls, 
        db: Session, 
        risk_id: str
    ) -> Dict[str, any]:
        """
        Calculate the aggregate effectiveness of all controls for a risk
        
        Returns:
            Dict containing:
            - aggregate_effectiveness: Overall effectiveness percentage (0-100)
            - control_count: Number of controls
            - by_type: Effectiveness breakdown by control type
            - coverage_weighted: Coverage-weighted effectiveness
            - overlap_bonus: Bonus from control type combinations
        """
        # Get all controls mapped to this risk
        risk_controls = db.query(RiskControl).filter(
            RiskControl.risk_id == risk_id
        ).all()
        
        if not risk_controls:
            return {
                "aggregate_effectiveness": 0,
                "control_count": 0,
                "by_type": {},
                "coverage_weighted": 0,
                "overlap_bonus": 0,
                "details": "No controls mapped to this risk"
            }
        
        # Get control details
        control_data = []
        control_types = set()
        effectiveness_by_type = {}
        
        for rc in risk_controls:
            control = db.query(Control).filter(Control.id == rc.control_id).first()
            if control and control.effectiveness_rating is not None:
                # Use coverage_percentage if set, otherwise default to 100%
                coverage = rc.coverage_percentage if rc.coverage_percentage else 100.0
                
                control_data.append({
                    "control": control,
                    "coverage": coverage,
                    "weighted_effectiveness": (control.effectiveness_rating * coverage / 100)
                })
                
                # Track control types for overlap calculation
                if control.type:
                    control_type = control.type.value if hasattr(control.type, 'value') else str(control.type)
                    control_types.add(control_type)
                    
                    if control_type not in effectiveness_by_type:
                        effectiveness_by_type[control_type] = []
                    effectiveness_by_type[control_type].append(
                        control.effectiveness_rating * coverage / 100
                    )
        
        if not control_data:
            return {
                "aggregate_effectiveness": 0,
                "control_count": len(risk_controls),
                "by_type": {},
                "coverage_weighted": 0,
                "overlap_bonus": 0,
                "details": "Controls exist but have no effectiveness ratings"
            }
        
        # Calculate base aggregate effectiveness
        total_weighted_effectiveness = sum(cd["weighted_effectiveness"] for cd in control_data)
        base_effectiveness = total_weighted_effectiveness / len(control_data)
        
        # Calculate type-weighted effectiveness
        type_weighted_effectiveness = 0
        for control_type, effectivenesses in effectiveness_by_type.items():
            avg_type_effectiveness = sum(effectivenesses) / len(effectivenesses)
            weight = cls.CONTROL_TYPE_WEIGHTS.get(control_type, 0.25)
            type_weighted_effectiveness += avg_type_effectiveness * weight
        
        # Calculate overlap bonus
        overlap_bonus = cls._calculate_overlap_bonus(control_types)
        
        # Final aggregate effectiveness (capped at 95% to maintain residual risk)
        aggregate_effectiveness = min(
            base_effectiveness * (1 + overlap_bonus),
            95.0  # Cap at 95% effectiveness
        )
        
        return {
            "aggregate_effectiveness": round(aggregate_effectiveness, 2),
            "control_count": len(control_data),
            "by_type": {
                k: round(sum(v) / len(v), 2) 
                for k, v in effectiveness_by_type.items()
            },
            "coverage_weighted": round(base_effectiveness, 2),
            "overlap_bonus": round(overlap_bonus * 100, 2),  # As percentage
            "type_weighted": round(type_weighted_effectiveness, 2)
        }
    
    @classmethod
    def _calculate_overlap_bonus(cls, control_types: set) -> float:
        """Calculate bonus effectiveness from control type combinations"""
        control_types = set(control_types)
        
        # Check for specific combinations
        for combo, bonus in cls.CONTROL_OVERLAP_BONUS.items():
            if set(combo).issubset(control_types):
                return bonus
        
        return 0.0
    
    @classmethod
    def calculate_residual_risk(
        cls,
        inherent_risk: float,
        aggregate_control_effectiveness: float
    ) -> float:
        """
        Calculate residual risk based on inherent risk and control effectiveness
        
        Args:
            inherent_risk: The inherent risk score (likelihood * impact)
            aggregate_control_effectiveness: Overall control effectiveness (0-100)
        
        Returns:
            Residual risk score
        """
        if aggregate_control_effectiveness >= 100:
            # Even with perfect controls, maintain minimum residual risk
            return inherent_risk * 0.05
        
        reduction_factor = 1 - (aggregate_control_effectiveness / 100)
        return inherent_risk * reduction_factor
    
    @classmethod
    def update_risk_scores(cls, db: Session, risk_id: str) -> Dict[str, any]:
        """
        Update risk scores based on current control effectiveness
        
        This method:
        1. Calculates aggregate control effectiveness
        2. Updates residual risk score in the risk record
        3. Returns the updated scores
        """
        risk = db.query(Risk).filter(Risk.id == risk_id).first()
        if not risk:
            return {"error": "Risk not found"}
        
        # Calculate aggregate control effectiveness
        effectiveness_data = cls.calculate_aggregate_control_effectiveness(db, risk_id)
        aggregate_effectiveness = effectiveness_data["aggregate_effectiveness"]
        
        # Calculate inherent risk if not set
        if risk.inherent_risk_score is None:
            if risk.likelihood and risk.impact:
                risk.inherent_risk_score = float(risk.likelihood * risk.impact)
            else:
                # Get from latest assessment if available
                latest_assessment = db.query(RiskAssessment).filter(
                    RiskAssessment.risk_id == risk_id
                ).order_by(RiskAssessment.assessment_date.desc()).first()
                
                if latest_assessment:
                    risk.inherent_risk_score = latest_assessment.inherent_risk
                else:
                    risk.inherent_risk_score = 0
        
        # Calculate new residual risk
        old_residual = risk.residual_risk_score
        new_residual = cls.calculate_residual_risk(
            risk.inherent_risk_score,
            aggregate_effectiveness
        )
        risk.residual_risk_score = new_residual
        
        # Commit the changes
        db.commit()
        
        return {
            "risk_id": risk_id,
            "risk_title": risk.title,
            "inherent_risk": risk.inherent_risk_score,
            "old_residual_risk": old_residual,
            "new_residual_risk": round(new_residual, 2),
            "aggregate_control_effectiveness": aggregate_effectiveness,
            "control_details": effectiveness_data,
            "risk_reduction": round(
                ((risk.inherent_risk_score - new_residual) / risk.inherent_risk_score * 100) 
                if risk.inherent_risk_score > 0 else 0, 
                2
            )
        }
    
    @classmethod
    def recalculate_all_risks(cls, db: Session) -> List[Dict]:
        """
        Recalculate residual risk for all risks with controls
        Used for batch updates or system maintenance
        """
        # Get all risks with controls
        risks_with_controls = db.query(Risk.id).join(
            RiskControl, RiskControl.risk_id == Risk.id
        ).distinct().all()
        
        results = []
        for (risk_id,) in risks_with_controls:
            try:
                result = cls.update_risk_scores(db, risk_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Error updating risk {risk_id}: {str(e)}")
                results.append({
                    "risk_id": risk_id,
                    "error": str(e)
                })
        
        return results
    
    @classmethod
    def get_control_contribution(
        cls, 
        db: Session, 
        risk_id: str, 
        control_id: str
    ) -> Dict[str, any]:
        """
        Calculate how much a specific control contributes to risk reduction
        """
        # Get current effectiveness with the control
        current_effectiveness = cls.calculate_aggregate_control_effectiveness(db, risk_id)
        
        # Temporarily remove the control mapping to calculate without it
        risk_control = db.query(RiskControl).filter(
            and_(
                RiskControl.risk_id == risk_id,
                RiskControl.control_id == control_id
            )
        ).first()
        
        if not risk_control:
            return {
                "error": "Control not mapped to this risk"
            }
        
        # Remove from session without deleting
        db.expunge(risk_control)
        
        # Calculate effectiveness without this control
        effectiveness_without = cls.calculate_aggregate_control_effectiveness(db, risk_id)
        
        # Re-add to session
        db.add(risk_control)
        
        contribution = current_effectiveness["aggregate_effectiveness"] - \
                      effectiveness_without["aggregate_effectiveness"]
        
        return {
            "control_id": control_id,
            "risk_id": risk_id,
            "contribution_percentage": round(contribution, 2),
            "with_control": current_effectiveness["aggregate_effectiveness"],
            "without_control": effectiveness_without["aggregate_effectiveness"]
        }