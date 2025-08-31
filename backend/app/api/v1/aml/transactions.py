from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.aml import Transaction, TransactionAlert, CustomerProfile
from app.schemas.aml import (
    TransactionCreate, TransactionUpdate, Transaction as TransactionSchema,
    TransactionAlertCreate, TransactionAlert as TransactionAlertSchema
)
from app.services.aml import RiskScoringService, TransactionMonitoringService

router = APIRouter()


@router.post("/", response_model=TransactionSchema)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new transaction and perform initial risk assessment"""
    
    # Create transaction record
    db_transaction = Transaction(**transaction.dict())
    
    # Link to customer if account number provided
    if transaction.account_number:
        customer = db.query(CustomerProfile).filter(
            CustomerProfile.account_number == transaction.account_number
        ).first()
        if customer:
            db_transaction.customer_id = customer.id
    
    # Set transaction flags
    db_transaction.is_cash = transaction.transaction_type in ["cash", "deposit", "withdrawal"]
    db_transaction.exceeds_threshold = transaction.amount >= 10000
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    # Calculate risk score
    risk_service = RiskScoringService(db)
    risk_result = risk_service.calculate_transaction_risk_score(db_transaction.id)
    
    # Monitor transaction for suspicious patterns
    monitoring_service = TransactionMonitoringService(db)
    monitoring_result = monitoring_service.monitor_transaction(db_transaction.id)
    
    # Create alerts if needed
    if monitoring_result.get("alerts"):
        for alert_data in monitoring_result["alerts"]:
            alert = TransactionAlert(
                transaction_id=db_transaction.id,
                customer_id=db_transaction.customer_id,
                alert_id=f"ALT-{db_transaction.id}-{datetime.utcnow().timestamp()}",
                **alert_data
            )
            db.add(alert)
        db.commit()
    
    return db_transaction


@router.get("/{transaction_id}", response_model=TransactionSchema)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific transaction by ID"""
    
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction


@router.get("/", response_model=List[TransactionSchema])
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    customer_id: Optional[int] = None,
    account_number: Optional[str] = None,
    status: Optional[str] = None,
    is_high_risk: Optional[bool] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List transactions with filtering options"""
    
    query = db.query(Transaction)
    
    # Apply filters
    if customer_id:
        query = query.filter(Transaction.customer_id == customer_id)
    if account_number:
        query = query.filter(Transaction.account_number == account_number)
    if status:
        query = query.filter(Transaction.status == status)
    if is_high_risk is not None:
        query = query.filter(Transaction.is_high_risk == is_high_risk)
    if date_from:
        query = query.filter(Transaction.transaction_date >= date_from)
    if date_to:
        query = query.filter(Transaction.transaction_date <= date_to)
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)
    
    # Order by date descending
    query = query.order_by(Transaction.transaction_date.desc())
    
    return query.offset(skip).limit(limit).all()


@router.patch("/{transaction_id}", response_model=TransactionSchema)
def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update transaction details and review status"""
    
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update fields
    update_data = transaction_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)
    
    # Set reviewer if status is being updated
    if "status" in update_data:
        transaction.reviewed_by = current_user.id
        transaction.reviewed_at = datetime.utcnow()
    
    transaction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.post("/{transaction_id}/recalculate-risk", response_model=Dict[str, Any])
def recalculate_transaction_risk(
    transaction_id: int,
    apply_ml: bool = Query(False, description="Apply ML model for scoring"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Recalculate risk score for a transaction"""
    
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    risk_service = RiskScoringService(db)
    risk_result = risk_service.calculate_transaction_risk_score(
        transaction_id,
        apply_ml_model=apply_ml
    )
    
    return risk_result


@router.get("/{transaction_id}/alerts", response_model=List[TransactionAlertSchema])
def get_transaction_alerts(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all alerts for a specific transaction"""
    
    alerts = db.query(TransactionAlert).filter(
        TransactionAlert.transaction_id == transaction_id
    ).all()
    
    return alerts


@router.post("/{transaction_id}/alerts", response_model=TransactionAlertSchema)
def create_transaction_alert(
    transaction_id: int,
    alert: TransactionAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Manually create an alert for a transaction"""
    
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Create alert
    db_alert = TransactionAlert(
        transaction_id=transaction_id,
        customer_id=transaction.customer_id,
        alert_id=f"ALT-{transaction_id}-{datetime.utcnow().timestamp()}",
        **alert.dict()
    )
    
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    
    return db_alert


@router.post("/batch", response_model=Dict[str, Any])
def process_batch_transactions(
    transactions: List[TransactionCreate] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Process multiple transactions in batch"""
    
    results = {
        "processed": 0,
        "failed": 0,
        "high_risk": 0,
        "alerts_generated": 0,
        "transactions": []
    }
    
    monitoring_service = TransactionMonitoringService(db)
    risk_service = RiskScoringService(db)
    
    for trans_data in transactions:
        try:
            # Create transaction
            db_transaction = Transaction(**trans_data.dict())
            
            # Link to customer
            if trans_data.account_number:
                customer = db.query(CustomerProfile).filter(
                    CustomerProfile.account_number == trans_data.account_number
                ).first()
                if customer:
                    db_transaction.customer_id = customer.id
            
            db.add(db_transaction)
            db.flush()
            
            # Calculate risk
            risk_result = risk_service.calculate_transaction_risk_score(db_transaction.id)
            
            # Monitor for suspicious patterns
            monitoring_result = monitoring_service.monitor_transaction(db_transaction.id)
            
            # Create alerts
            if monitoring_result.get("alerts"):
                for alert_data in monitoring_result["alerts"]:
                    alert = TransactionAlert(
                        transaction_id=db_transaction.id,
                        customer_id=db_transaction.customer_id,
                        alert_id=f"ALT-{db_transaction.id}-{datetime.utcnow().timestamp()}",
                        **alert_data
                    )
                    db.add(alert)
                    results["alerts_generated"] += 1
            
            if db_transaction.is_high_risk:
                results["high_risk"] += 1
            
            results["processed"] += 1
            results["transactions"].append({
                "id": db_transaction.id,
                "transaction_id": db_transaction.transaction_id,
                "risk_score": db_transaction.risk_score,
                "is_high_risk": db_transaction.is_high_risk
            })
            
        except Exception as e:
            results["failed"] += 1
            db.rollback()
            continue
    
    db.commit()
    
    return results