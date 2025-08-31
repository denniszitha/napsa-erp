"""
Integration service between AML and ERM modules
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.risk import Risk, RiskCategoryEnum, RiskStatus
from app.models.incident import Incident, IncidentStatus, IncidentSeverity
from app.models.aml import ComplianceCase, TransactionAlert, CustomerProfile
from app.models.aml.case import CaseStatus, CasePriority


class AMLERMIntegrationService:
    """Service for integrating AML events with ERM risk management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_risk_from_aml_case(
        self,
        case_id: int,
        user_id: int
    ) -> Risk:
        """Create an ERM risk entry from an AML compliance case"""
        
        # Get AML case
        case = self.db.query(ComplianceCase).filter(
            ComplianceCase.id == case_id
        ).first()
        
        if not case:
            raise ValueError(f"AML Case {case_id} not found")
        
        # Determine risk category based on case type
        risk_category = self._map_case_to_risk_category(case.case_type)
        
        # Calculate risk metrics
        likelihood = self._calculate_likelihood_from_case(case)
        impact = self._calculate_impact_from_case(case)
        
        # Create risk entry
        risk = Risk(
            name=f"AML Risk: {case.title}",
            description=f"Risk identified from AML case {case.case_number}. {case.description}",
            category=risk_category,
            likelihood=likelihood,
            impact=impact,
            risk_score=likelihood * impact,
            status=RiskStatus.ACTIVE if case.status != CaseStatus.CLOSED_NO_ACTION else RiskStatus.CLOSED,
            owner_id=case.assigned_to or user_id,
            department_id=1,  # Compliance department
            identified_date=case.created_date or datetime.utcnow(),
            review_date=datetime.utcnow(),
            mitigation_strategy=f"Investigation and resolution of AML case {case.case_number}",
            aml_case_id=case.id,  # Link to AML case
            created_by=user_id
        )
        
        self.db.add(risk)
        self.db.commit()
        
        return risk
    
    def create_incident_from_alert(
        self,
        alert_id: int,
        user_id: int
    ) -> Incident:
        """Create an ERM incident from an AML alert"""
        
        # Get AML alert
        alert = self.db.query(TransactionAlert).filter(
            TransactionAlert.id == alert_id
        ).first()
        
        if not alert:
            raise ValueError(f"AML Alert {alert_id} not found")
        
        # Determine incident severity
        severity = self._map_alert_to_incident_severity(alert.severity.value)
        
        # Create incident
        incident = Incident(
            title=f"AML Alert: {alert.title}",
            description=alert.description or f"Alert {alert.alert_id} triggered",
            incident_date=alert.created_at,
            detected_date=alert.created_at,
            severity=severity,
            status=IncidentStatus.OPEN if alert.status.value == "open" else IncidentStatus.INVESTIGATING,
            reporter_id=user_id,
            assigned_to=alert.assigned_to,
            department_id=1,  # Compliance department
            financial_impact=alert.transaction.amount if alert.transaction else 0,
            operational_impact="Potential regulatory compliance issue",
            reputational_impact="Possible reputational risk if not addressed",
            root_cause=f"Triggered by rule: {alert.rule_name}" if alert.rule_name else "System detected anomaly",
            aml_alert_id=alert.id,  # Link to AML alert
            created_by=user_id
        )
        
        self.db.add(incident)
        self.db.commit()
        
        return incident
    
    def sync_customer_risk_to_erm(
        self,
        customer_id: int,
        user_id: int
    ) -> Optional[Risk]:
        """Sync high-risk customer profiles to ERM risk registry"""
        
        # Get customer profile
        customer = self.db.query(CustomerProfile).filter(
            CustomerProfile.id == customer_id
        ).first()
        
        if not customer:
            return None
        
        # Only create risk for high-risk customers
        if customer.risk_level.value not in ["high", "critical"]:
            return None
        
        # Check if risk already exists
        existing_risk = self.db.query(Risk).filter(
            Risk.name == f"High Risk Customer: {customer.customer_id}"
        ).first()
        
        if existing_risk:
            # Update existing risk
            existing_risk.likelihood = self._calculate_customer_likelihood(customer)
            existing_risk.impact = self._calculate_customer_impact(customer)
            existing_risk.risk_score = existing_risk.likelihood * existing_risk.impact
            existing_risk.review_date = datetime.utcnow()
            self.db.commit()
            return existing_risk
        
        # Create new risk
        risk = Risk(
            name=f"High Risk Customer: {customer.customer_id}",
            description=f"High risk customer profile: {customer.account_name}. Risk factors: "
                       f"PEP={customer.pep_status}, High-risk country={customer.high_risk_country}, "
                       f"Risk score={customer.risk_score}",
            category=RiskCategory.COMPLIANCE,
            likelihood=self._calculate_customer_likelihood(customer),
            impact=self._calculate_customer_impact(customer),
            risk_score=0,  # Will be calculated
            status=RiskStatus.ACTIVE,
            owner_id=user_id,
            department_id=1,
            identified_date=datetime.utcnow(),
            review_date=datetime.utcnow(),
            mitigation_strategy="Enhanced due diligence and continuous monitoring",
            created_by=user_id
        )
        
        risk.risk_score = risk.likelihood * risk.impact
        
        self.db.add(risk)
        self.db.commit()
        
        return risk
    
    def get_aml_risk_metrics(self) -> Dict[str, Any]:
        """Get AML-related risk metrics for ERM dashboard"""
        
        from app.models.aml.transaction import AlertStatus, TransactionStatus
        from sqlalchemy import func
        
        # Count active AML risks
        active_cases = self.db.query(ComplianceCase).filter(
            ComplianceCase.status.in_([CaseStatus.OPEN, CaseStatus.INVESTIGATING])
        ).count()
        
        # Count high-risk customers
        high_risk_customers = self.db.query(CustomerProfile).filter(
            CustomerProfile.risk_level.in_(["high", "critical"])
        ).count()
        
        # Count open alerts
        open_alerts = self.db.query(TransactionAlert).filter(
            TransactionAlert.status == AlertStatus.OPEN
        ).count()
        
        # Calculate total exposure
        flagged_transactions = self.db.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.status == TransactionStatus.FLAGGED
        ).scalar() or 0
        
        return {
            "aml_risks": {
                "active_cases": active_cases,
                "high_risk_customers": high_risk_customers,
                "open_alerts": open_alerts,
                "total_exposure": flagged_transactions
            },
            "risk_indicators": {
                "compliance_risk_level": "high" if active_cases > 10 else "medium" if active_cases > 5 else "low",
                "customer_risk_level": "high" if high_risk_customers > 50 else "medium" if high_risk_customers > 20 else "low",
                "operational_risk_level": "high" if open_alerts > 100 else "medium" if open_alerts > 50 else "low"
            }
        }
    
    def _map_case_to_risk_category(self, case_type: str) -> RiskCategoryEnum:
        """Map AML case type to ERM risk category"""
        mapping = {
            "AML": RiskCategoryEnum.COMPLIANCE,
            "Fraud": RiskCategoryEnum.OPERATIONAL,
            "Sanctions": RiskCategoryEnum.COMPLIANCE,
            "KYC": RiskCategoryEnum.COMPLIANCE
        }
        return mapping.get(case_type, RiskCategoryEnum.COMPLIANCE)
    
    def _map_alert_to_incident_severity(self, alert_severity: str) -> IncidentSeverity:
        """Map AML alert severity to incident severity"""
        mapping = {
            "critical": IncidentSeverity.CRITICAL,
            "high": IncidentSeverity.HIGH,
            "medium": IncidentSeverity.MEDIUM,
            "low": IncidentSeverity.LOW
        }
        return mapping.get(alert_severity, IncidentSeverity.MEDIUM)
    
    def _calculate_likelihood_from_case(self, case: ComplianceCase) -> int:
        """Calculate risk likelihood from AML case"""
        if case.priority == CasePriority.CRITICAL:
            return 5
        elif case.priority == CasePriority.HIGH:
            return 4
        elif case.priority == CasePriority.MEDIUM:
            return 3
        else:
            return 2
    
    def _calculate_impact_from_case(self, case: ComplianceCase) -> int:
        """Calculate risk impact from AML case"""
        # Based on total amount and alert count
        if case.total_amount > 1000000 or case.alert_count > 10:
            return 5
        elif case.total_amount > 100000 or case.alert_count > 5:
            return 4
        elif case.total_amount > 10000 or case.alert_count > 2:
            return 3
        else:
            return 2
    
    def _calculate_customer_likelihood(self, customer: CustomerProfile) -> int:
        """Calculate risk likelihood from customer profile"""
        if customer.risk_score > 80:
            return 5
        elif customer.risk_score > 60:
            return 4
        elif customer.risk_score > 40:
            return 3
        else:
            return 2
    
    def _calculate_customer_impact(self, customer: CustomerProfile) -> int:
        """Calculate risk impact from customer profile"""
        # Based on customer type and special statuses
        impact = 2
        
        if customer.customer_type.value == "corporate":
            impact += 1
        if customer.pep_status:
            impact += 2
        if customer.high_risk_country:
            impact += 1
        
        return min(5, impact)