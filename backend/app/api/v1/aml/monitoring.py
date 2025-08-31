from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.aml import TransactionMonitoringService, RiskScoringService

router = APIRouter()


@router.post("/webhook/transaction")
def receive_transaction_webhook(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint to receive real-time transaction data from core banking system.
    This mimics the Laravel webhook functionality.
    """
    
    try:
        # Process incoming transaction data
        monitoring_service = TransactionMonitoringService(db)
        risk_service = RiskScoringService(db)
        
        # Extract transaction data
        transaction_data = data.get("current_transaction", {})
        case_number = data.get("case_number")
        compliance_category = data.get("compliance_category")
        compliance_issue = data.get("compliance_issue")
        
        # Create transaction record
        from app.models.aml import Transaction, CustomerProfile
        
        # Find or create customer
        account_number = transaction_data.get("acct_no")
        customer = db.query(CustomerProfile).filter(
            CustomerProfile.account_number == account_number
        ).first()
        
        if not customer:
            customer = CustomerProfile(
                customer_id=f"CUST-{account_number}",
                account_number=account_number,
                account_name=transaction_data.get("acct_name"),
                account_open_date=datetime.strptime(
                    transaction_data.get("acct_opn_date", "2020-01-01 00:00:00"),
                    "%Y-%m-%d %H:%M:%S"
                ) if transaction_data.get("acct_opn_date") else None,
                branch_code=transaction_data.get("branch", "").split("-")[0] if transaction_data.get("branch") else None
            )
            db.add(customer)
            db.flush()
        
        # Create transaction
        transaction = Transaction(
            transaction_id=transaction_data.get("tran_id", f"TXN-{datetime.utcnow().timestamp()}"),
            customer_id=customer.id,
            account_number=account_number,
            account_name=transaction_data.get("acct_name"),
            transaction_type="deposit" if transaction_data.get("dr_cr_indicator") == "C" else "withdrawal",
            transaction_date=datetime.strptime(
                transaction_data.get("tran_date", datetime.utcnow().strftime("%d-%m-%Y")),
                "%d-%m-%Y"
            ) if transaction_data.get("tran_date") else datetime.utcnow(),
            amount=float(transaction_data.get("tran_amt", 0)),
            currency=transaction_data.get("tran_crncy_code", "ZMW"),
            description=transaction_data.get("tran_particular"),
            branch_code=transaction_data.get("branch", "").split("-")[0] if transaction_data.get("branch") else None
        )
        
        db.add(transaction)
        db.flush()
        
        # Calculate risk score
        risk_result = risk_service.calculate_transaction_risk_score(transaction.id)
        
        # Monitor for suspicious patterns
        monitoring_result = monitoring_service.monitor_transaction(transaction.id)
        
        # Create alerts if needed
        if monitoring_result.get("alerts"):
            from app.models.aml import TransactionAlert
            for alert_data in monitoring_result["alerts"]:
                alert = TransactionAlert(
                    transaction_id=transaction.id,
                    customer_id=customer.id,
                    alert_id=f"ALT-{transaction.id}-{datetime.utcnow().timestamp()}",
                    **alert_data
                )
                db.add(alert)
        
        # Check if SAR/STR needs to be filed
        should_file_sar = (
            compliance_category == "Not Compliant" or
            transaction.risk_score > 75 or
            len(monitoring_result.get("alerts", [])) > 2
        )
        
        db.commit()
        
        return {
            "success": True,
            "message": "Transaction processed",
            "case_number": case_number,
            "transaction_id": transaction.transaction_id,
            "risk_score": transaction.risk_score,
            "is_high_risk": transaction.is_high_risk,
            "alerts_generated": len(monitoring_result.get("alerts", [])),
            "should_file_sar": should_file_sar,
            "compliance_status": compliance_category,
            "compliance_issues": compliance_issue
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/pattern")
def analyze_customer_patterns(
    customer_id: int,
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Analyze transaction patterns for a customer"""
    
    monitoring_service = TransactionMonitoringService(db)
    patterns = monitoring_service.get_customer_transaction_patterns(customer_id, days)
    
    return patterns


@router.post("/alerts/bulk-review")
def bulk_review_alerts(
    alert_ids: List[int] = Body(...),
    action: str = Body(..., description="close_false_positive, escalate, or assign"),
    notes: str = Body(None),
    assigned_to: int = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk review and update multiple alerts"""
    
    from app.models.aml import TransactionAlert
    from app.models.aml.transaction import AlertStatus
    
    updated_count = 0
    
    for alert_id in alert_ids:
        alert = db.query(TransactionAlert).filter(
            TransactionAlert.id == alert_id
        ).first()
        
        if alert:
            if action == "close_false_positive":
                alert.status = AlertStatus.CLOSED_FALSE_POSITIVE
                alert.resolution = "False Positive"
                alert.resolution_notes = notes
                alert.resolved_by = current_user.id
                alert.resolved_at = datetime.utcnow()
            elif action == "escalate":
                alert.status = AlertStatus.ESCALATED
                alert.escalated = True
                alert.escalated_at = datetime.utcnow()
                alert.escalated_to = assigned_to or current_user.id
            elif action == "assign":
                alert.assigned_to = assigned_to
                alert.status = AlertStatus.INVESTIGATING
            
            updated_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "updated_count": updated_count,
        "action": action
    }


@router.get("/dashboard/stats")
def get_monitoring_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get AML monitoring dashboard statistics"""
    
    from app.models.aml import Transaction, TransactionAlert, CustomerProfile, ComplianceCase
    from app.models.aml.transaction import AlertStatus, TransactionStatus
    from sqlalchemy import func
    from datetime import timedelta
    
    today = datetime.utcnow().date()
    last_30_days = datetime.utcnow() - timedelta(days=30)
    
    # Transaction statistics
    total_transactions = db.query(Transaction).count()
    high_risk_transactions = db.query(Transaction).filter(
        Transaction.is_high_risk == True
    ).count()
    flagged_transactions = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.FLAGGED
    ).count()
    
    # Alert statistics
    total_alerts = db.query(TransactionAlert).count()
    open_alerts = db.query(TransactionAlert).filter(
        TransactionAlert.status == AlertStatus.OPEN
    ).count()
    escalated_alerts = db.query(TransactionAlert).filter(
        TransactionAlert.escalated == True
    ).count()
    
    # Customer statistics
    total_customers = db.query(CustomerProfile).count()
    high_risk_customers = db.query(CustomerProfile).filter(
        CustomerProfile.risk_level.in_(["high", "critical"])
    ).count()
    pep_customers = db.query(CustomerProfile).filter(
        CustomerProfile.pep_status == True
    ).count()
    
    # Case statistics
    from app.models.aml.case import CaseStatus
    total_cases = db.query(ComplianceCase).count()
    open_cases = db.query(ComplianceCase).filter(
        ComplianceCase.status.in_([CaseStatus.OPEN, CaseStatus.INVESTIGATING])
    ).count()
    
    # Recent activity
    recent_transactions = db.query(Transaction).filter(
        Transaction.created_at >= last_30_days
    ).count()
    
    recent_alerts = db.query(TransactionAlert).filter(
        TransactionAlert.created_at >= last_30_days
    ).count()
    
    return {
        "transactions": {
            "total": total_transactions,
            "high_risk": high_risk_transactions,
            "flagged": flagged_transactions,
            "recent_30_days": recent_transactions
        },
        "alerts": {
            "total": total_alerts,
            "open": open_alerts,
            "escalated": escalated_alerts,
            "recent_30_days": recent_alerts
        },
        "customers": {
            "total": total_customers,
            "high_risk": high_risk_customers,
            "pep": pep_customers
        },
        "cases": {
            "total": total_cases,
            "open": open_cases
        },
        "risk_distribution": {
            "low": db.query(CustomerProfile).filter(CustomerProfile.risk_level == "low").count(),
            "medium": db.query(CustomerProfile).filter(CustomerProfile.risk_level == "medium").count(),
            "high": db.query(CustomerProfile).filter(CustomerProfile.risk_level == "high").count(),
            "critical": db.query(CustomerProfile).filter(CustomerProfile.risk_level == "critical").count()
        }
    }