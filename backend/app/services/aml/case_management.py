from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.aml import (
    ComplianceCase, CaseComment, TransactionAlert,
    CustomerProfile, Transaction
)
from app.models.aml.case import CaseStatus, CasePriority


class CaseManagementService:
    """Service for managing compliance cases"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_case_from_alert(
        self,
        alert_id: int,
        user_id: int,
        title: str,
        description: str = None
    ) -> ComplianceCase:
        """Create a compliance case from an alert"""
        
        # Get alert details
        alert = self.db.query(TransactionAlert).filter(
            TransactionAlert.id == alert_id
        ).first()
        
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")
        
        # Get transaction details
        transaction = self.db.query(Transaction).filter(
            Transaction.id == alert.transaction_id
        ).first()
        
        # Get customer details
        customer = None
        if alert.customer_id:
            customer = self.db.query(CustomerProfile).filter(
                CustomerProfile.id == alert.customer_id
            ).first()
        
        # Generate case number
        case_number = self._generate_case_number()
        
        # Determine priority based on alert severity
        priority = self._determine_priority(alert.severity.value)
        
        # Create case
        case = ComplianceCase(
            case_number=case_number,
            title=title,
            description=description or alert.description,
            case_type="AML",
            customer_id=alert.customer_id,
            customer_name=customer.account_name if customer else transaction.account_name,
            customer_account=transaction.account_number,
            risk_level=customer.risk_level.value if customer else "medium",
            risk_score=transaction.risk_score,
            priority=priority,
            status=CaseStatus.OPEN,
            assigned_to=user_id,
            assigned_date=datetime.utcnow(),
            alert_count=1,
            transaction_count=1,
            total_amount=transaction.amount,
            created_by=user_id,
            due_date=self._calculate_due_date(priority)
        )
        
        self.db.add(case)
        self.db.flush()
        
        # Link alert to case
        alert.case_id = case.id
        
        # Add initial comment
        comment = CaseComment(
            case_id=case.id,
            comment_type="note",
            comment_text=f"Case created from alert {alert.alert_id}",
            created_by=user_id
        )
        self.db.add(comment)
        
        self.db.commit()
        
        return case
    
    def escalate_case(
        self,
        case_id: int,
        escalated_to: int,
        reason: str,
        user_id: int
    ) -> ComplianceCase:
        """Escalate a case to higher authority"""
        
        case = self.db.query(ComplianceCase).filter(
            ComplianceCase.id == case_id
        ).first()
        
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        # Update case
        case.status = CaseStatus.ESCALATED
        case.escalated = True
        case.escalated_to = escalated_to
        case.escalated_date = datetime.utcnow()
        case.escalation_reason = reason
        
        # Add comment
        comment = CaseComment(
            case_id=case_id,
            comment_type="escalation",
            comment_text=f"Case escalated: {reason}",
            created_by=user_id
        )
        self.db.add(comment)
        
        self.db.commit()
        
        return case
    
    def close_case(
        self,
        case_id: int,
        decision: str,
        decision_reason: str,
        user_id: int,
        file_sar: bool = False
    ) -> ComplianceCase:
        """Close a compliance case"""
        
        case = self.db.query(ComplianceCase).filter(
            ComplianceCase.id == case_id
        ).first()
        
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        # Update case
        case.decision = decision
        case.decision_reason = decision_reason
        case.decided_by = user_id
        case.decided_date = datetime.utcnow()
        case.closed_date = datetime.utcnow()
        
        if file_sar:
            case.status = CaseStatus.CLOSED_REPORTED
            case.sar_filed = True
        elif decision == "false_positive":
            case.status = CaseStatus.CLOSED_FALSE_POSITIVE
            case.false_positive = True
        else:
            case.status = CaseStatus.CLOSED_NO_ACTION
        
        # Add comment
        comment = CaseComment(
            case_id=case_id,
            comment_type="decision",
            comment_text=f"Case closed: {decision} - {decision_reason}",
            created_by=user_id
        )
        self.db.add(comment)
        
        self.db.commit()
        
        return case
    
    def _generate_case_number(self) -> str:
        """Generate a unique case number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M")
        count = self.db.query(ComplianceCase).count() + 1
        return f"CASE-{timestamp}-{count:04d}"
    
    def _determine_priority(self, severity: str) -> CasePriority:
        """Determine case priority based on alert severity"""
        severity_priority_map = {
            "critical": CasePriority.CRITICAL,
            "high": CasePriority.HIGH,
            "medium": CasePriority.MEDIUM,
            "low": CasePriority.LOW
        }
        return severity_priority_map.get(severity, CasePriority.MEDIUM)
    
    def _calculate_due_date(self, priority: CasePriority) -> datetime:
        """Calculate due date based on priority"""
        days_map = {
            CasePriority.CRITICAL: 1,
            CasePriority.HIGH: 3,
            CasePriority.MEDIUM: 7,
            CasePriority.LOW: 14
        }
        return datetime.utcnow() + timedelta(days=days_map[priority])