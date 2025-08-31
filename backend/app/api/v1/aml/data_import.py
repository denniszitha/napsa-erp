"""
Batch import functionality for AML data
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import csv
import json
import io
from datetime import datetime

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.aml import CustomerProfile, Transaction
from app.services.aml import RiskScoringService, TransactionMonitoringService

router = APIRouter()


@router.post("/customers/import")
async def import_customers(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Import customers from CSV file"""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # Read file content
    content = await file.read()
    csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
    
    results = {
        "total": 0,
        "imported": 0,
        "updated": 0,
        "failed": 0,
        "errors": []
    }
    
    risk_service = RiskScoringService(db)
    
    for row in csv_reader:
        results["total"] += 1
        
        try:
            # Check if customer exists
            existing = db.query(CustomerProfile).filter(
                CustomerProfile.customer_id == row.get('customer_id')
            ).first()
            
            if existing:
                # Update existing customer
                for key, value in row.items():
                    if hasattr(existing, key) and value:
                        setattr(existing, key, value)
                existing.updated_by = current_user.id
                existing.updated_at = datetime.utcnow()
                results["updated"] += 1
                
                # Recalculate risk score in background
                background_tasks.add_task(
                    risk_service.calculate_customer_risk_score,
                    existing.id
                )
            else:
                # Create new customer
                customer = CustomerProfile(
                    customer_id=row.get('customer_id'),
                    account_number=row.get('account_number'),
                    account_name=row.get('account_name'),
                    customer_type=row.get('customer_type', 'individual'),
                    first_name=row.get('first_name'),
                    last_name=row.get('last_name'),
                    company_name=row.get('company_name'),
                    email=row.get('email'),
                    phone_primary=row.get('phone_primary'),
                    address_line1=row.get('address_line1'),
                    city=row.get('city'),
                    country=row.get('country'),
                    kyc_status=row.get('kyc_status', 'pending'),
                    created_by=current_user.id
                )
                db.add(customer)
                db.flush()
                results["imported"] += 1
                
                # Calculate initial risk score in background
                background_tasks.add_task(
                    risk_service.calculate_customer_risk_score,
                    customer.id
                )
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "row": results["total"],
                "customer_id": row.get('customer_id'),
                "error": str(e)
            })
            db.rollback()
            continue
    
    db.commit()
    
    return {
        "message": "Customer import completed",
        "results": results
    }


@router.post("/transactions/import")
async def import_transactions(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Import transactions from CSV or JSON file"""
    
    if not (file.filename.endswith('.csv') or file.filename.endswith('.json')):
        raise HTTPException(status_code=400, detail="Only CSV and JSON files are supported")
    
    content = await file.read()
    
    results = {
        "total": 0,
        "imported": 0,
        "flagged": 0,
        "alerts_generated": 0,
        "failed": 0,
        "errors": []
    }
    
    risk_service = RiskScoringService(db)
    monitoring_service = TransactionMonitoringService(db)
    
    # Parse file based on type
    if file.filename.endswith('.csv'):
        csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
        transactions_data = list(csv_reader)
    else:
        transactions_data = json.loads(content)
    
    for row in transactions_data:
        results["total"] += 1
        
        try:
            # Find customer by account number
            customer = None
            if row.get('account_number'):
                customer = db.query(CustomerProfile).filter(
                    CustomerProfile.account_number == row.get('account_number')
                ).first()
            
            # Create transaction
            transaction = Transaction(
                transaction_id=row.get('transaction_id', f"TXN-{datetime.utcnow().timestamp()}"),
                customer_id=customer.id if customer else None,
                account_number=row.get('account_number'),
                account_name=row.get('account_name'),
                transaction_type=row.get('transaction_type', 'transfer'),
                transaction_date=datetime.fromisoformat(row.get('transaction_date')) if row.get('transaction_date') else datetime.utcnow(),
                amount=float(row.get('amount', 0)),
                currency=row.get('currency', 'USD'),
                description=row.get('description'),
                branch_code=row.get('branch_code'),
                counterparty_account=row.get('counterparty_account'),
                counterparty_name=row.get('counterparty_name'),
                counterparty_bank=row.get('counterparty_bank'),
                counterparty_country=row.get('counterparty_country')
            )
            
            # Set flags
            transaction.is_cash = transaction.transaction_type in ['cash', 'deposit', 'withdrawal']
            transaction.exceeds_threshold = transaction.amount >= 10000
            
            db.add(transaction)
            db.flush()
            results["imported"] += 1
            
            # Process in background
            background_tasks.add_task(
                process_transaction_async,
                transaction.id,
                db,
                risk_service,
                monitoring_service
            )
            
            if transaction.is_high_risk:
                results["flagged"] += 1
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "row": results["total"],
                "transaction_id": row.get('transaction_id'),
                "error": str(e)
            })
            db.rollback()
            continue
    
    db.commit()
    
    return {
        "message": "Transaction import completed",
        "results": results
    }


@router.post("/bulk/process")
def process_bulk_data(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Process bulk data from core banking system"""
    
    results = {
        "customers": {"processed": 0, "failed": 0},
        "transactions": {"processed": 0, "failed": 0},
        "alerts_generated": 0
    }
    
    risk_service = RiskScoringService(db)
    monitoring_service = TransactionMonitoringService(db)
    
    # Process customers if provided
    if "customers" in data:
        for customer_data in data["customers"]:
            try:
                # Create or update customer
                customer = db.query(CustomerProfile).filter(
                    CustomerProfile.customer_id == customer_data.get("customer_id")
                ).first()
                
                if not customer:
                    customer = CustomerProfile(**customer_data)
                    customer.created_by = current_user.id
                    db.add(customer)
                else:
                    for key, value in customer_data.items():
                        if hasattr(customer, key):
                            setattr(customer, key, value)
                    customer.updated_by = current_user.id
                
                db.flush()
                
                # Calculate risk score
                risk_service.calculate_customer_risk_score(customer.id)
                results["customers"]["processed"] += 1
                
            except Exception as e:
                results["customers"]["failed"] += 1
                continue
    
    # Process transactions if provided
    if "transactions" in data:
        for trans_data in data["transactions"]:
            try:
                # Create transaction
                transaction = Transaction(**trans_data)
                
                # Link to customer
                if trans_data.get("account_number"):
                    customer = db.query(CustomerProfile).filter(
                        CustomerProfile.account_number == trans_data["account_number"]
                    ).first()
                    if customer:
                        transaction.customer_id = customer.id
                
                db.add(transaction)
                db.flush()
                
                # Calculate risk and monitor
                risk_service.calculate_transaction_risk_score(transaction.id)
                monitoring_result = monitoring_service.monitor_transaction(transaction.id)
                
                if monitoring_result.get("alerts"):
                    results["alerts_generated"] += len(monitoring_result["alerts"])
                
                results["transactions"]["processed"] += 1
                
            except Exception as e:
                results["transactions"]["failed"] += 1
                continue
    
    db.commit()
    
    return {
        "message": "Bulk processing completed",
        "results": results
    }


def process_transaction_async(
    transaction_id: int,
    db: Session,
    risk_service: RiskScoringService,
    monitoring_service: TransactionMonitoringService
):
    """Process transaction asynchronously"""
    try:
        # Calculate risk score
        risk_service.calculate_transaction_risk_score(transaction_id)
        
        # Monitor for suspicious patterns
        monitoring_result = monitoring_service.monitor_transaction(transaction_id)
        
        # Create alerts if needed
        if monitoring_result.get("alerts"):
            from app.models.aml import TransactionAlert
            
            transaction = db.query(Transaction).filter(
                Transaction.id == transaction_id
            ).first()
            
            for alert_data in monitoring_result["alerts"]:
                alert = TransactionAlert(
                    transaction_id=transaction_id,
                    customer_id=transaction.customer_id,
                    alert_id=f"ALT-{transaction_id}-{datetime.utcnow().timestamp()}",
                    **alert_data
                )
                db.add(alert)
            
            db.commit()
            
    except Exception as e:
        print(f"Error processing transaction {transaction_id}: {e}")
        db.rollback()