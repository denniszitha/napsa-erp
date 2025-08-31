from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.compliance import (
    ComplianceFramework, 
    ComplianceStatus,
    ComplianceRequirement,
    ComplianceMapping,
    ComplianceAssessment
)
from app.services.compliance import compliance_service

router = APIRouter()

@router.get("/dashboard")
def get_compliance_dashboard(
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_user),
    ):
    """Get compliance dashboard with all frameworks"""
    return compliance_service.get_compliance_dashboard(db)

@router.post("/assess/{framework}")
def perform_compliance_assessment(
    framework: ComplianceFramework,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_user),
    ):
    """Perform compliance assessment for a framework"""
    # if current_user.role not in ["admin", "risk_manager", "auditor"]:
    #     raise HTTPException(status_code=403, detail="Not authorized to perform assessments")
    
    return compliance_service.perform_compliance_assessment(
        db, framework, "System Admin"
    )

@router.get("/requirements/{framework}")
def get_framework_requirements(
    framework: ComplianceFramework,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_user),
    ):
    """Get all requirements for a compliance framework"""
    requirements = db.query(ComplianceRequirement).filter(
        ComplianceRequirement.framework == framework
    ).all()
    
    return [
        {
            "id": str(req.id),
            "requirement_id": req.requirement_id,
            "title": req.title,
            "description": req.description,
            "category": req.category,
            "criticality": req.criticality
        }
        for req in requirements
    ]

@router.post("/mappings")
def create_compliance_mapping(
    mapping_data: dict,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_user),
    ):
    """Create or update compliance mapping"""
    # Check if mapping exists
    existing = db.query(ComplianceMapping).filter(
        ComplianceMapping.requirement_id == mapping_data["requirement_id"]
    ).first()
    
    if existing:
        # Update existing
        existing.control_id = mapping_data.get("control_id")
        existing.risk_id = mapping_data.get("risk_id")
        existing.status = ComplianceStatus(mapping_data["status"])
        existing.evidence = mapping_data.get("evidence", [])
        existing.notes = mapping_data.get("notes")
        existing.assessed_by = "System Admin"
        existing.last_assessment_date = datetime.now(timezone.utc)
    else:
        # Create new
        mapping = ComplianceMapping(
            **mapping_data,
            assessed_by="System Admin",
            last_assessment_date=datetime.now(timezone.utc)
        )
        db.add(mapping)
    
    db.commit()
    
    return {"message": "Compliance mapping saved successfully"}

@router.get("/frameworks", response_model=List[Dict[str, Any]])
def get_compliance_frameworks(
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_user)
    ) -> List[Dict[str, Any]]:
    """Get list of available compliance frameworks"""
    frameworks = [
        {
            "id": "iso_27001",
            "name": "ISO 27001:2013",
            "description": "Information Security Management System",
            "categories": ["Information Security", "Risk Management"],
            "total_requirements": 114
        },
        {
            "id": "nist",
            "name": "NIST Cybersecurity Framework",
            "description": "Framework for Improving Critical Infrastructure Cybersecurity",
            "categories": ["Cybersecurity", "Risk Management"],
            "total_requirements": 108
        },
        {
            "id": "coso",
            "name": "COSO Framework",
            "description": "Internal Control - Integrated Framework",
            "categories": ["Internal Controls", "Risk Management"],
            "total_requirements": 40
        },
        {
            "id": "gdpr",
            "name": "GDPR",
            "description": "General Data Protection Regulation",
            "categories": ["Data Privacy", "Data Protection"],
            "total_requirements": 99
        },
        {
            "id": "sox",
            "name": "SOX",
            "description": "Sarbanes-Oxley Act",
            "categories": ["Financial Reporting", "Internal Controls"],
            "total_requirements": 404
        },
        {
            "id": "basel_iii",
            "name": "Basel III",
            "description": "International regulatory framework for banks",
            "categories": ["Financial Risk", "Capital Adequacy"],
            "total_requirements": 25
        }
    ]
    
    # Add implementation status for each framework
    for framework in frameworks:
        requirements = db.query(ComplianceRequirement)\
            .filter(ComplianceRequirement.framework == framework["id"])\
            .all()
        
        if requirements:
            implemented = len([r for r in requirements if hasattr(r, 'implementation_status') and r.implementation_status == "implemented"])
            framework["implementation_percentage"] = round((implemented / len(requirements)) * 100, 2)
            framework["implemented_requirements"] = implemented
        else:
            framework["implementation_percentage"] = 0
            framework["implemented_requirements"] = 0
    
    return frameworks

@router.get("/status", response_model=Dict[str, Any])
def get_overall_compliance_status(
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
    """Get overall compliance status across all frameworks"""
    requirements = db.query(ComplianceRequirement).all()
    mappings = db.query(ComplianceMapping).all()
    
    # Calculate overall compliance
    total_requirements = len(requirements)
    mapped_requirements = len(set(m.requirement_id for m in mappings))
    
    # Group by framework
    by_framework = {}
    frameworks = set(r.framework for r in requirements)
    
    for framework in frameworks:
        framework_reqs = [r for r in requirements if r.framework == framework]
        framework_mapped = len([m for m in mappings if m.requirement_id in [r.id for r in framework_reqs]])
        
        by_framework[framework] = {
            "total_requirements": len(framework_reqs),
            "mapped_requirements": framework_mapped,
            "compliance_percentage": round((framework_mapped / len(framework_reqs)) * 100, 2) if framework_reqs else 0
        }
    
    # Get recent assessments
    recent_assessments = db.query(ComplianceAssessment)\
        .order_by(ComplianceAssessment.assessment_date.desc())\
        .limit(5)\
        .all()
    
    return {
        "overall_compliance": round((mapped_requirements / total_requirements) * 100, 2) if total_requirements else 0,
        "total_requirements": total_requirements,
        "mapped_requirements": mapped_requirements,
        "by_framework": by_framework,
        "recent_assessments": [
            {
                "id": str(a.id),
                "framework": a.framework,
                "compliance_score": a.compliance_score,
                "assessment_date": a.assessment_date.isoformat(),
                "status": a.status.value if hasattr(a.status, 'value') else a.status
            } for a in recent_assessments
        ],
        "compliance_gaps": total_requirements - mapped_requirements,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }