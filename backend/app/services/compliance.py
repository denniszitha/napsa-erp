from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta, timezone
import json

from app.models.compliance import (
    ComplianceRequirement, ComplianceMapping, ComplianceAssessment,
    ComplianceFramework, ComplianceStatus
)
from app.models.control import Control
from app.models.risk import Risk

class ComplianceService:
    
    @staticmethod
    def get_compliance_dashboard(db: Session) -> Dict[str, Any]:
        """Get comprehensive compliance dashboard data"""
        frameworks_data = {}
        
        for framework in ComplianceFramework:
            # Get requirements for this framework
            requirements = db.query(ComplianceRequirement).filter(
                ComplianceRequirement.framework == framework
            ).all()
            
            if not requirements:
                continue
            
            # Get mappings and calculate compliance
            mappings = db.query(ComplianceMapping).join(ComplianceRequirement).filter(
                ComplianceRequirement.framework == framework
            ).all()
            
            status_counts = {
                "compliant": 0,
                "non_compliant": 0,
                "partially_compliant": 0,
                "not_applicable": 0
            }
            
            for mapping in mappings:
                status_counts[mapping.status.value] += 1
            
            total_applicable = len(mappings) - status_counts["not_applicable"]
            compliance_score = 0
            if total_applicable > 0:
                compliance_score = (
                    (status_counts["compliant"] + status_counts["partially_compliant"] * 0.5) 
                    / total_applicable * 100
                )
            
            frameworks_data[framework.value] = {
                "total_requirements": len(requirements),
                "mapped_requirements": len(mappings),
                "status_distribution": status_counts,
                "compliance_score": round(compliance_score, 2),
                "last_assessment": ComplianceService._get_last_assessment_date(db, framework)
            }
        
        # Overall compliance score
        overall_score = 0
        if frameworks_data:
            overall_score = sum(f["compliance_score"] for f in frameworks_data.values()) / len(frameworks_data)
        
        return {
            "overall_compliance_score": round(overall_score, 2),
            "frameworks": frameworks_data,
            "compliance_gaps": ComplianceService._get_compliance_gaps(db),
            "upcoming_assessments": ComplianceService._get_upcoming_assessments(db)
        }
    
    @staticmethod
    def _get_last_assessment_date(db: Session, framework: ComplianceFramework) -> Optional[str]:
        """Get the date of the last assessment for a framework"""
        last_assessment = db.query(ComplianceAssessment).filter(
            ComplianceAssessment.framework == framework
        ).order_by(ComplianceAssessment.assessment_date.desc()).first()
        
        return last_assessment.assessment_date.isoformat() if last_assessment else None
    
    @staticmethod
    def _get_compliance_gaps(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top compliance gaps"""
        gaps = []
        
        non_compliant_mappings = db.query(ComplianceMapping).filter(
            ComplianceMapping.status == ComplianceStatus.non_compliant
        ).join(ComplianceRequirement).all()
        
        for mapping in non_compliant_mappings[:limit]:
            gap = {
                "requirement": {
                    "id": str(mapping.requirement.id),
                    "framework": mapping.requirement.framework.value,
                    "requirement_id": mapping.requirement.requirement_id,
                    "title": mapping.requirement.title,
                    "criticality": mapping.requirement.criticality
                },
                "status": mapping.status.value,
                "notes": mapping.notes,
                "last_assessment": mapping.last_assessment_date.isoformat() if mapping.last_assessment_date else None
            }
            
            # Add associated risk if exists
            if mapping.risk:
                gap["associated_risk"] = {
                    "id": str(mapping.risk.id),
                    "title": mapping.risk.title,
                    "risk_score": mapping.risk.inherent_risk_score
                }
            
            gaps.append(gap)
        
        # Sort by criticality
        criticality_order = {"high": 0, "medium": 1, "low": 2}
        gaps.sort(key=lambda x: criticality_order.get(x["requirement"]["criticality"], 3))
        
        return gaps
    
    @staticmethod
    def _get_upcoming_assessments(db: Session, days: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming compliance assessments"""
        upcoming = []
        future_date = datetime.now(timezone.utc) + timedelta(days=days)
        
        mappings_due = db.query(ComplianceMapping).filter(
            and_(
                ComplianceMapping.next_assessment_date.isnot(None),
                ComplianceMapping.next_assessment_date <= future_date
            )
        ).join(ComplianceRequirement).all()
        
        for mapping in mappings_due:
            upcoming.append({
                "requirement_id": str(mapping.requirement.id),
                "framework": mapping.requirement.framework.value,
                "requirement": mapping.requirement.title,
                "due_date": mapping.next_assessment_date.isoformat(),
                "days_until_due": (mapping.next_assessment_date - datetime.now(timezone.utc)).days
            })
        
        upcoming.sort(key=lambda x: x["days_until_due"])
        
        return upcoming
    
    @staticmethod
    def perform_compliance_assessment(
        db: Session,
        framework: ComplianceFramework,
        assessor: str
    ) -> Dict[str, Any]:
        """Perform a compliance assessment for a framework"""
        # Get all requirements for the framework
        requirements = db.query(ComplianceRequirement).filter(
            ComplianceRequirement.framework == framework
        ).all()
        
        # Get all mappings
        mappings = db.query(ComplianceMapping).join(ComplianceRequirement).filter(
            ComplianceRequirement.framework == framework
        ).all()
        
        # Calculate results
        status_counts = {
            ComplianceStatus.compliant: 0,
            ComplianceStatus.non_compliant: 0,
            ComplianceStatus.partially_compliant: 0,
            ComplianceStatus.not_applicable: 0
        }
        
        findings = []
        recommendations = []
        
        for mapping in mappings:
            status_counts[mapping.status] += 1
            
            # Generate findings for non-compliant items
            if mapping.status in [ComplianceStatus.non_compliant, ComplianceStatus.partially_compliant]:
                finding = {
                    "requirement_id": mapping.requirement.requirement_id,
                    "title": mapping.requirement.title,
                    "status": mapping.status.value,
                    "gap": mapping.notes or "No specific details provided"
                }
                findings.append(finding)
                
                # Generate recommendations
                if mapping.control:
                    recommendations.append({
                        "requirement": mapping.requirement.requirement_id,
                        "recommendation": f"Improve effectiveness of control: {mapping.control.name}",
                        "priority": mapping.requirement.criticality
                    })
        
        # Calculate compliance score
        total_applicable = len(mappings) - status_counts[ComplianceStatus.not_applicable]
        compliance_score = 0
        if total_applicable > 0:
            compliance_score = (
                (status_counts[ComplianceStatus.compliant] + 
                 status_counts[ComplianceStatus.partially_compliant] * 0.5) 
                / total_applicable * 100
            )
        
        # Create assessment record
        assessment = ComplianceAssessment(
            framework=framework,
            assessor=assessor,
            total_requirements=len(requirements),
            compliant_count=status_counts[ComplianceStatus.compliant],
            non_compliant_count=status_counts[ComplianceStatus.non_compliant],
            partially_compliant_count=status_counts[ComplianceStatus.partially_compliant],
            not_applicable_count=status_counts[ComplianceStatus.not_applicable],
            compliance_score=compliance_score,
            findings=findings,
            recommendations=recommendations
        )
        
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        return {
            "assessment_id": str(assessment.id),
            "framework": framework.value,
            "compliance_score": round(compliance_score, 2),
            "summary": {
                "total_requirements": assessment.total_requirements,
                "compliant": assessment.compliant_count,
                "non_compliant": assessment.non_compliant_count,
                "partially_compliant": assessment.partially_compliant_count,
                "not_applicable": assessment.not_applicable_count
            },
            "findings_count": len(findings),
            "recommendations_count": len(recommendations)
        }

compliance_service = ComplianceService()
