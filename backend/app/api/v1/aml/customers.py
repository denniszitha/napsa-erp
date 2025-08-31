from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.aml import CustomerProfile, CustomerRiskProfile
from app.schemas.aml import (
    CustomerProfileCreate, CustomerProfileUpdate, 
    CustomerProfile as CustomerProfileSchema,
    CustomerRiskProfile as CustomerRiskProfileSchema
)
from app.services.aml import RiskScoringService

router = APIRouter()


@router.post("/", response_model=CustomerProfileSchema)
def create_customer(
    customer: CustomerProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new customer profile"""
    
    # Check if customer already exists
    existing = db.query(CustomerProfile).filter(
        CustomerProfile.customer_id == customer.customer_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Customer already exists")
    
    # Create customer
    db_customer = CustomerProfile(**customer.dict())
    db_customer.created_by = current_user.id
    
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    # Calculate initial risk score
    risk_service = RiskScoringService(db)
    risk_service.calculate_customer_risk_score(db_customer.id)
    
    return db_customer


@router.get("/{customer_id}", response_model=CustomerProfileSchema)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get customer profile by ID"""
    
    customer = db.query(CustomerProfile).filter(
        CustomerProfile.id == customer_id
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer


@router.get("/", response_model=List[CustomerProfileSchema])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    risk_level: Optional[str] = None,
    kyc_status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List customers with filtering options"""
    
    query = db.query(CustomerProfile)
    
    if risk_level:
        query = query.filter(CustomerProfile.risk_level == risk_level)
    if kyc_status:
        query = query.filter(CustomerProfile.kyc_status == kyc_status)
    if search:
        query = query.filter(
            (CustomerProfile.account_name.contains(search)) |
            (CustomerProfile.account_number.contains(search)) |
            (CustomerProfile.customer_id.contains(search))
        )
    
    return query.offset(skip).limit(limit).all()


@router.patch("/{customer_id}", response_model=CustomerProfileSchema)
def update_customer(
    customer_id: int,
    customer_update: CustomerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update customer profile"""
    
    customer = db.query(CustomerProfile).filter(
        CustomerProfile.id == customer_id
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update fields
    update_data = customer_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    customer.updated_by = current_user.id
    
    # Recalculate risk if KYC or other risk factors changed
    if any(k in update_data for k in ["kyc_status", "pep_status", "country", "occupation"]):
        risk_service = RiskScoringService(db)
        risk_service.calculate_customer_risk_score(customer.id)
    
    db.commit()
    db.refresh(customer)
    
    return customer


@router.get("/{customer_id}/risk-profile", response_model=CustomerRiskProfileSchema)
def get_customer_risk_profile(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get customer risk profile"""
    
    risk_profile = db.query(CustomerRiskProfile).filter(
        CustomerRiskProfile.customer_id == customer_id
    ).first()
    
    if not risk_profile:
        raise HTTPException(status_code=404, detail="Risk profile not found")
    
    return risk_profile