from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta

from app.models.aml import (
    SuspiciousActivityReport, CurrencyTransactionReport,
    CustomerProfile, Transaction, TransactionAlert, ComplianceCase
)
from app.models.aml.reports import ReportStatus, ReportType


class ReportingService:
    """Service for generating and managing regulatory reports"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ctr_threshold = 10000  # CTR threshold amount
    
    def create_sar(
        self,
        case_id: int,
        user_id: int,
        activity_description: str,
        suspicious_reason: str,
        action_taken: str = None
    ) -> SuspiciousActivityReport:
        """Create a Suspicious Activity Report"""
        
        # Get case details
        case = self.db.query(ComplianceCase).filter(
            ComplianceCase.id == case_id
        ).first()
        
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        # Generate report number
        report_number = self._generate_report_number("SAR")
        
        # Calculate transaction details
        transactions = self._get_case_transactions(case_id)
        total_amount = sum(t.amount for t in transactions)
        
        # Create SAR
        sar = SuspiciousActivityReport(
            report_number=report_number,
            report_type=ReportType.SAR,
            case_id=case_id,
            case_number=case.case_number,
            customer_id=case.customer_id,
            customer_name=case.customer_name,
            customer_account=case.customer_account,
            filing_date=date.today(),
            activity_date_start=min(t.transaction_date for t in transactions).date() if transactions else None,
            activity_date_end=max(t.transaction_date for t in transactions).date() if transactions else None,
            total_amount=total_amount,
            currency="USD",
            transaction_count=len(transactions),
            activity_description=activity_description,
            suspicious_reason=suspicious_reason,
            action_taken=action_taken,
            status=ReportStatus.DRAFT,
            prepared_by=user_id,
            prepared_date=datetime.utcnow()
        )
        
        self.db.add(sar)
        self.db.commit()
        
        return sar
    
    def create_ctr(
        self,
        transaction_id: int,
        user_id: int
    ) -> CurrencyTransactionReport:
        """Create a Currency Transaction Report"""
        
        # Get transaction details
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        # Get customer details
        customer = self.db.query(CustomerProfile).filter(
            CustomerProfile.id == transaction.customer_id
        ).first()
        
        # Generate report number
        report_number = self._generate_report_number("CTR")
        
        # Create CTR
        ctr = CurrencyTransactionReport(
            report_number=report_number,
            customer_id=transaction.customer_id,
            customer_name=customer.account_name if customer else transaction.account_name,
            customer_account=transaction.account_number,
            transaction_date=transaction.transaction_date.date(),
            transaction_type=transaction.transaction_type.value,
            total_cash_in=transaction.amount if transaction.transaction_type.value == "deposit" else 0,
            total_cash_out=transaction.amount if transaction.transaction_type.value == "withdrawal" else 0,
            currency=transaction.currency,
            branch_code=transaction.branch_code,
            filing_date=date.today(),
            filing_deadline=date.today() + timedelta(days=15),
            status=ReportStatus.DRAFT,
            filed_by=user_id
        )
        
        self.db.add(ctr)
        self.db.commit()
        
        return ctr
    
    def _generate_report_number(self, report_type: str) -> str:
        """Generate a unique report number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"{report_type}-{timestamp}"
    
    def _get_case_transactions(self, case_id: int) -> List[Transaction]:
        """Get all transactions related to a case"""
        # Get alerts for the case
        alerts = self.db.query(TransactionAlert).filter(
            TransactionAlert.case_id == case_id
        ).all()
        
        transaction_ids = [alert.transaction_id for alert in alerts]
        
        if transaction_ids:
            return self.db.query(Transaction).filter(
                Transaction.id.in_(transaction_ids)
            ).all()
        
        return []