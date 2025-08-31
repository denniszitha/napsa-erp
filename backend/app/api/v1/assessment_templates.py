"""
Assessment Templates and Risk Scales API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_active_user
from app.models.user import User

router = APIRouter()

# Pydantic Models
class ImpactScaleBase(BaseModel):
    level: int = Field(..., ge=1, le=5)
    name: str
    description: Optional[str] = None
    color_code: Optional[str] = None
    
class ImpactScaleResponse(ImpactScaleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class LikelihoodScaleBase(BaseModel):
    level: int = Field(..., ge=1, le=5)
    name: str
    description: Optional[str] = None
    probability_range: Optional[str] = None
    
class LikelihoodScaleResponse(LikelihoodScaleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AssessmentCriterion(BaseModel):
    name: str
    weight: int = Field(..., ge=0, le=100)
    description: Optional[str] = None

class AssessmentTemplateCreate(BaseModel):
    name: str
    type: str = Field(default="standard")
    description: Optional[str] = None
    criteria: List[AssessmentCriterion] = []
    is_active: bool = True
    
class AssessmentTemplateResponse(BaseModel):
    id: int
    name: str
    type: str
    description: Optional[str]
    criteria: List[AssessmentCriterion]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by_id: int
    
    class Config:
        from_attributes = True

# Test endpoint
@router.get("/test")
def test_endpoint():
    """Test endpoint to verify routing works"""
    return {"message": "Assessment templates module is working!"}

# Impact Scales Endpoints
@router.get("/impact-scales", response_model=List[ImpactScaleResponse])
def get_impact_scales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all impact scales"""
    # Return default scales (mock data for now)
    return [
        {"id": 1, "level": 1, "name": "Negligible", "description": "Minimal impact on objectives", "color_code": "#10b981", "created_at": datetime.utcnow()},
        {"id": 2, "level": 2, "name": "Minor", "description": "Limited impact, easily manageable", "color_code": "#84cc16", "created_at": datetime.utcnow()},
        {"id": 3, "level": 3, "name": "Moderate", "description": "Noticeable impact, some disruption", "color_code": "#eab308", "created_at": datetime.utcnow()},
        {"id": 4, "level": 4, "name": "Major", "description": "Significant impact, major disruption", "color_code": "#f97316", "created_at": datetime.utcnow()},
        {"id": 5, "level": 5, "name": "Catastrophic", "description": "Severe impact, critical failure", "color_code": "#ef4444", "created_at": datetime.utcnow()}
    ]

# Likelihood Scales Endpoints
@router.get("/likelihood-scales", response_model=List[LikelihoodScaleResponse])
def get_likelihood_scales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all likelihood scales"""
    # Return default scales (mock data for now)
    return [
        {"id": 1, "level": 1, "name": "Rare", "description": "Very unlikely to occur", "probability_range": "<10%", "created_at": datetime.utcnow()},
        {"id": 2, "level": 2, "name": "Unlikely", "description": "Could occur but doubtful", "probability_range": "10-30%", "created_at": datetime.utcnow()},
        {"id": 3, "level": 3, "name": "Possible", "description": "Might occur", "probability_range": "30-50%", "created_at": datetime.utcnow()},
        {"id": 4, "level": 4, "name": "Likely", "description": "Will probably occur", "probability_range": "50-80%", "created_at": datetime.utcnow()},
        {"id": 5, "level": 5, "name": "Almost Certain", "description": "Expected to occur", "probability_range": ">80%", "created_at": datetime.utcnow()}
    ]

# Assessment Templates Endpoints
@router.get("/assessment-templates", response_model=List[AssessmentTemplateResponse])
def get_assessment_templates(
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all assessment templates"""
    # Return mock templates for now
    return [
        {
            "id": 1,
            "name": "Standard Risk Assessment",
            "type": "standard",
            "description": "Default template for general risk assessments",
            "criteria": [
                {"name": "Impact on Operations", "weight": 30},
                {"name": "Financial Impact", "weight": 25},
                {"name": "Regulatory Compliance", "weight": 20},
                {"name": "Reputational Risk", "weight": 15},
                {"name": "Recovery Time", "weight": 10}
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by_id": current_user.id if current_user else 1
        },
        {
            "id": 2,
            "name": "Cyber Security Assessment",
            "type": "custom",
            "description": "Specialized template for cyber security risks",
            "criteria": [
                {"name": "Data Sensitivity", "weight": 35},
                {"name": "System Criticality", "weight": 30},
                {"name": "Threat Likelihood", "weight": 20},
                {"name": "Control Effectiveness", "weight": 15}
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by_id": current_user.id if current_user else 1
        }
    ]

@router.get("/assessment-templates/{template_id}", response_model=AssessmentTemplateResponse)
def get_assessment_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific assessment template"""
    if template_id == 1:
        return {
            "id": 1,
            "name": "Standard Risk Assessment",
            "type": "standard",
            "description": "Default template for general risk assessments",
            "criteria": [
                {"name": "Impact on Operations", "weight": 30},
                {"name": "Financial Impact", "weight": 25},
                {"name": "Regulatory Compliance", "weight": 20},
                {"name": "Reputational Risk", "weight": 15},
                {"name": "Recovery Time", "weight": 10}
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by_id": current_user.id if current_user else 1
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Assessment template not found"
    )

@router.post("/assessment-templates", response_model=AssessmentTemplateResponse)
def create_assessment_template(
    template: AssessmentTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new assessment template"""
    # Mock creation - return the template with an ID
    return {
        "id": 3,
        **template.dict(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by_id": current_user.id if current_user else 1
    }

# File Categories endpoint
@router.get("/file-categories")
def get_file_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get file categories"""
    return [
        {"id": 1, "name": "Risk Assessments", "allowed_extensions": ["pdf", "docx"], "is_active": True},
        {"id": 2, "name": "Policies", "allowed_extensions": ["pdf", "docx"], "is_active": True},
        {"id": 3, "name": "Incidents", "allowed_extensions": ["pdf", "xlsx"], "is_active": True},
        {"id": 4, "name": "Evidence", "allowed_extensions": ["png", "jpg", "pdf"], "is_active": True},
        {"id": 5, "name": "Audits", "allowed_extensions": ["pdf", "xlsx"], "is_active": True},
        {"id": 6, "name": "General", "allowed_extensions": ["pdf", "docx", "xlsx"], "is_active": True}
    ]