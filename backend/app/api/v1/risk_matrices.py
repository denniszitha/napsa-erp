from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_active_user
from app.models.risk_matrix import RiskMatrix, RiskAppetite, MatrixTemplate
from app.schemas.risk_matrix import (
    RiskMatrixCreate, RiskMatrixUpdate, RiskMatrixResponse,
    RiskAppetiteCreate, RiskAppetiteUpdate, RiskAppetiteResponse,
    MatrixTemplateCreate, MatrixTemplateResponse,
    MatrixConfigurationResponse, MatrixValidationResponse,
    RiskCalculationRequest, RiskCalculationResponse, StandardMatrixTemplates
)
from app.models.user import User

router = APIRouter()

# Default matrix configurations
DEFAULT_STANDARD_MATRIX = {
    "name": "Standard 5x5 Risk Matrix",
    "description": "Standard organizational risk matrix based on ISO 31000",
    "likelihood_levels": 5,
    "impact_levels": 5,
    "likelihood_labels": ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"],
    "impact_labels": ["Insignificant", "Minor", "Moderate", "Major", "Catastrophic"],
    "likelihood_descriptions": [
        "May occur only in exceptional circumstances (0-5%)",
        "Could occur at some time (5-25%)",
        "Might occur at some time (25-50%)",
        "Will probably occur in most circumstances (50-75%)",
        "Expected to occur in most circumstances (75-100%)"
    ],
    "impact_descriptions": [
        "Minimal impact on operations, reputation, or finances",
        "Minor impact with limited consequences",
        "Moderate impact requiring management attention",
        "Major impact with significant consequences",
        "Catastrophic impact threatening organizational survival"
    ],
    "risk_levels": {
        "low": {
            "name": "Low",
            "color": "#28a745",
            "description": "Acceptable risk level",
            "treatment_strategy": "Accept"
        },
        "medium": {
            "name": "Medium", 
            "color": "#ffc107",
            "description": "Monitor and review",
            "treatment_strategy": "Monitor"
        },
        "high": {
            "name": "High",
            "color": "#fd7e14",
            "description": "Requires mitigation",
            "treatment_strategy": "Mitigate"
        },
        "very_high": {
            "name": "Very High",
            "color": "#dc3545",
            "description": "Urgent action required",
            "treatment_strategy": "Urgent Action"
        },
        "critical": {
            "name": "Critical",
            "color": "#6f42c1",
            "description": "Immediate action required",
            "treatment_strategy": "Immediate Action"
        }
    },
    "risk_thresholds": {
        "low": {"min": 1, "max": 4},
        "medium": {"min": 5, "max": 9},
        "high": {"min": 10, "max": 14},
        "very_high": {"min": 15, "max": 19},
        "critical": {"min": 20, "max": 25}
    }
}

@router.get("/", response_model=List[RiskMatrixResponse])
def get_risk_matrices(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all risk matrices"""
    query = db.query(RiskMatrix)
    
    if active_only:
        query = query.filter(RiskMatrix.is_active == True)
    
    matrices = query.offset(skip).limit(limit).all()
    return matrices

@router.get("/default", response_model=RiskMatrixResponse)
def get_default_matrix(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get the default risk matrix"""
    matrix = db.query(RiskMatrix).filter(RiskMatrix.is_default == True).first()
    
    if not matrix:
        # Create default matrix if it doesn't exist
        matrix = RiskMatrix(**DEFAULT_STANDARD_MATRIX)
        matrix.is_default = True
        matrix.created_by_id = current_user.id
        db.add(matrix)
        db.commit()
        db.refresh(matrix)
    
    return matrix

@router.get("/{matrix_id}", response_model=RiskMatrixResponse)
def get_risk_matrix(
    matrix_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific risk matrix"""
    matrix = db.query(RiskMatrix).filter(RiskMatrix.id == matrix_id).first()
    
    if not matrix:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk matrix not found"
        )
    
    return matrix

@router.post("/", response_model=RiskMatrixResponse)
def create_risk_matrix(
    matrix: RiskMatrixCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new risk matrix"""
    # Validate matrix configuration
    validation = validate_matrix_config(matrix.dict())
    if not validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid matrix configuration: {', '.join(validation['errors'])}"
        )
    
    # Create the matrix
    db_matrix = RiskMatrix(**matrix.dict())
    db_matrix.created_by_id = current_user.id
    
    # Set as default if no other default exists
    if not db.query(RiskMatrix).filter(RiskMatrix.is_default == True).first():
        db_matrix.is_default = True
    
    db.add(db_matrix)
    db.commit()
    db.refresh(db_matrix)
    
    return db_matrix

@router.put("/{matrix_id}", response_model=RiskMatrixResponse)
def update_risk_matrix(
    matrix_id: UUID,
    matrix_update: RiskMatrixUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a risk matrix"""
    matrix = db.query(RiskMatrix).filter(RiskMatrix.id == matrix_id).first()
    
    if not matrix:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk matrix not found"
        )
    
    # Update matrix fields
    update_data = matrix_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(matrix, field, value)
    
    db.commit()
    db.refresh(matrix)
    
    return matrix

@router.delete("/{matrix_id}")
def delete_risk_matrix(
    matrix_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a risk matrix"""
    matrix = db.query(RiskMatrix).filter(RiskMatrix.id == matrix_id).first()
    
    if not matrix:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk matrix not found"
        )
    
    if matrix.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the default risk matrix"
        )
    
    db.delete(matrix)
    db.commit()
    
    return {"message": "Risk matrix deleted successfully"}

@router.post("/{matrix_id}/set-default")
def set_default_matrix(
    matrix_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Set a matrix as the default"""
    matrix = db.query(RiskMatrix).filter(RiskMatrix.id == matrix_id).first()
    
    if not matrix:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk matrix not found"
        )
    
    # Remove default from other matrices
    db.query(RiskMatrix).update({"is_default": False})
    
    # Set this matrix as default
    matrix.is_default = True
    db.commit()
    
    return {"message": "Matrix set as default successfully"}

@router.post("/{matrix_id}/duplicate", response_model=RiskMatrixResponse)
def duplicate_matrix(
    matrix_id: UUID,
    new_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Duplicate an existing risk matrix"""
    original = db.query(RiskMatrix).filter(RiskMatrix.id == matrix_id).first()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk matrix not found"
        )
    
    # Create duplicate
    duplicate_data = {
        "name": new_name,
        "description": f"Copy of {original.description}" if original.description else None,
        "matrix_type": "custom",
        "likelihood_levels": original.likelihood_levels,
        "impact_levels": original.impact_levels,
        "likelihood_labels": original.likelihood_labels,
        "impact_labels": original.impact_labels,
        "likelihood_descriptions": original.likelihood_descriptions,
        "impact_descriptions": original.impact_descriptions,
        "risk_levels": original.risk_levels,
        "risk_thresholds": original.risk_thresholds,
        "created_by_id": current_user.id
    }
    
    duplicate = RiskMatrix(**duplicate_data)
    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)
    
    return duplicate

# Risk Appetite Endpoints
@router.get("/{matrix_id}/appetite", response_model=RiskAppetiteResponse)
def get_risk_appetite(
    matrix_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get risk appetite for a matrix"""
    appetite = db.query(RiskAppetite).filter(RiskAppetite.matrix_id == matrix_id).first()
    
    if not appetite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk appetite not found"
        )
    
    return appetite

@router.post("/{matrix_id}/appetite", response_model=RiskAppetiteResponse)
def create_risk_appetite(
    matrix_id: UUID,
    appetite: RiskAppetiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create risk appetite for a matrix"""
    # Check if matrix exists
    matrix = db.query(RiskMatrix).filter(RiskMatrix.id == matrix_id).first()
    if not matrix:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk matrix not found"
        )
    
    # Check if appetite already exists
    existing = db.query(RiskAppetite).filter(RiskAppetite.matrix_id == matrix_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Risk appetite already exists for this matrix"
        )
    
    db_appetite = RiskAppetite(**appetite.dict())
    db_appetite.matrix_id = matrix_id
    db.add(db_appetite)
    db.commit()
    db.refresh(db_appetite)
    
    return db_appetite

@router.put("/{matrix_id}/appetite", response_model=RiskAppetiteResponse)
def update_risk_appetite(
    matrix_id: UUID,
    appetite_update: RiskAppetiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update risk appetite"""
    appetite = db.query(RiskAppetite).filter(RiskAppetite.matrix_id == matrix_id).first()
    
    if not appetite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk appetite not found"
        )
    
    update_data = appetite_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appetite, field, value)
    
    db.commit()
    db.refresh(appetite)
    
    return appetite

# Matrix Templates
@router.get("/templates/", response_model=List[MatrixTemplateResponse])
def get_matrix_templates(
    industry: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get available matrix templates"""
    query = db.query(MatrixTemplate).filter(MatrixTemplate.is_public == True)
    
    if industry:
        query = query.filter(MatrixTemplate.industry == industry)
    
    templates = query.all()
    return templates

@router.get("/templates/standard", response_model=StandardMatrixTemplates)
def get_standard_templates(
    current_user: User = Depends(get_current_active_user)
):
    """Get standard matrix templates"""
    return {
        "iso31000": DEFAULT_STANDARD_MATRIX,
        "coso": {
            "name": "COSO Risk Matrix",
            "description": "Committee of Sponsoring Organizations framework",
            # ... COSO specific configuration
        },
        "nist": {
            "name": "NIST Risk Matrix", 
            "description": "National Institute of Standards and Technology framework",
            # ... NIST specific configuration
        },
        "financial_services": {
            "name": "Financial Services Risk Matrix",
            "description": "Tailored for banking and financial institutions",
            # ... Financial services specific configuration
        },
        "healthcare": {
            "name": "Healthcare Risk Matrix",
            "description": "Designed for healthcare organizations",
            # ... Healthcare specific configuration
        },
        "manufacturing": {
            "name": "Manufacturing Risk Matrix",
            "description": "Optimized for manufacturing environments",
            # ... Manufacturing specific configuration
        }
    }

@router.post("/from-template/{template_id}", response_model=RiskMatrixResponse)
def create_from_template(
    template_id: UUID,
    matrix_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a matrix from a template"""
    template = db.query(MatrixTemplate).filter(MatrixTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Create matrix from template
    matrix_data = template.template_config.copy()
    matrix_data["name"] = matrix_name
    matrix_data["matrix_type"] = "custom"
    matrix_data["created_by_id"] = current_user.id
    
    matrix = RiskMatrix(**matrix_data)
    db.add(matrix)
    db.commit()
    db.refresh(matrix)
    
    return matrix

# Utility endpoints
@router.post("/validate", response_model=MatrixValidationResponse)
def validate_matrix(
    matrix_config: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Validate a matrix configuration"""
    return validate_matrix_config(matrix_config)

@router.post("/calculate-risk", response_model=RiskCalculationResponse)
def calculate_risk_score(
    calculation: RiskCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Calculate risk score and level"""
    matrix_id = calculation.matrix_id
    if not matrix_id:
        # Use default matrix
        matrix = db.query(RiskMatrix).filter(RiskMatrix.is_default == True).first()
    else:
        matrix = db.query(RiskMatrix).filter(RiskMatrix.id == matrix_id).first()
    
    if not matrix:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk matrix not found"
        )
    
    # Calculate risk score
    risk_score = calculation.likelihood * calculation.impact
    
    # Determine risk level
    risk_level = "low"
    for level, thresholds in matrix.risk_thresholds.items():
        if thresholds["min"] <= risk_score <= thresholds["max"]:
            risk_level = level
            break
    
    risk_config = matrix.risk_levels[risk_level]
    
    return {
        "risk_score": risk_score,
        "risk_level": risk_config["name"],
        "risk_color": risk_config["color"],
        "treatment_strategy": risk_config["treatment_strategy"],
        "description": risk_config["description"]
    }

def validate_matrix_config(config: dict) -> dict:
    """Validate matrix configuration"""
    errors = []
    warnings = []
    
    # Check required fields
    required_fields = ["name", "likelihood_levels", "impact_levels", "likelihood_labels", "impact_labels"]
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate dimensions
    if "likelihood_levels" in config:
        if not 3 <= config["likelihood_levels"] <= 7:
            errors.append("Likelihood levels must be between 3 and 7")
    
    if "impact_levels" in config:
        if not 3 <= config["impact_levels"] <= 7:
            errors.append("Impact levels must be between 3 and 7")
    
    # Validate labels match dimensions
    if "likelihood_labels" in config and "likelihood_levels" in config:
        if len(config["likelihood_labels"]) != config["likelihood_levels"]:
            errors.append("Number of likelihood labels must match likelihood levels")
    
    if "impact_labels" in config and "impact_levels" in config:
        if len(config["impact_labels"]) != config["impact_levels"]:
            errors.append("Number of impact labels must match impact levels")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }