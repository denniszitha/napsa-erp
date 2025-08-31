from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import numpy as np

from app.models.aml import CustomerProfile, CustomerRiskProfile, Transaction
from app.models.aml.customer import RiskLevel


class RiskScoringService:
    """Service for calculating and managing risk scores for customers and transactions"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Risk weights configuration
        self.weights = {
            "geographic": 0.25,
            "product": 0.15,
            "channel": 0.15,
            "customer_type": 0.20,
            "transaction": 0.25
        }
        
        # High risk countries (ISO codes)
        self.high_risk_countries = [
            "IR", "KP", "SY", "YE", "AF", "MM", "LA", "VU", "GN", "GW"
        ]
        
        # High risk business types
        self.high_risk_businesses = [
            "money_services", "cryptocurrency", "gambling", "precious_metals",
            "arms_dealing", "marijuana", "shell_company"
        ]
    
    def calculate_customer_risk_score(
        self,
        customer_id: int,
        update_profile: bool = True
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk score for a customer"""
        
        customer = self.db.query(CustomerProfile).filter(
            CustomerProfile.id == customer_id
        ).first()
        
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Get or create risk profile
        risk_profile = self.db.query(CustomerRiskProfile).filter(
            CustomerRiskProfile.customer_id == customer_id
        ).first()
        
        if not risk_profile:
            risk_profile = CustomerRiskProfile(customer_id=customer_id)
            self.db.add(risk_profile)
        
        # Calculate individual risk factors
        geographic_risk = self._calculate_geographic_risk(customer)
        product_risk = self._calculate_product_risk(customer)
        channel_risk = self._calculate_channel_risk(customer)
        customer_type_risk = self._calculate_customer_type_risk(customer)
        transaction_risk = self._calculate_transaction_risk(customer)
        
        # Update risk profile
        risk_profile.geographic_risk = geographic_risk
        risk_profile.product_risk = product_risk
        risk_profile.channel_risk = channel_risk
        risk_profile.customer_type_risk = customer_type_risk
        risk_profile.transaction_risk = transaction_risk
        
        # Calculate composite score
        composite_score = (
            geographic_risk * self.weights["geographic"] +
            product_risk * self.weights["product"] +
            channel_risk * self.weights["channel"] +
            customer_type_risk * self.weights["customer_type"] +
            transaction_risk * self.weights["transaction"]
        )
        
        risk_profile.composite_risk_score = composite_score
        
        # Determine risk level
        risk_level = self._determine_risk_level(composite_score)
        
        if update_profile:
            customer.risk_score = composite_score
            customer.risk_level = risk_level
            risk_profile.last_review_date = datetime.utcnow()
            risk_profile.next_review_date = self._calculate_next_review_date(risk_level)
            self.db.commit()
        
        return {
            "customer_id": customer_id,
            "composite_score": composite_score,
            "risk_level": risk_level.value,
            "factors": {
                "geographic": geographic_risk,
                "product": product_risk,
                "channel": channel_risk,
                "customer_type": customer_type_risk,
                "transaction": transaction_risk
            },
            "high_risk_indicators": self._get_high_risk_indicators(customer, risk_profile)
        }
    
    def calculate_transaction_risk_score(
        self,
        transaction_id: int,
        apply_ml_model: bool = False
    ) -> Dict[str, Any]:
        """Calculate risk score for a specific transaction"""
        
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        risk_factors = []
        base_score = 0
        
        # Amount-based risk
        amount_risk = self._calculate_amount_risk(transaction)
        base_score += amount_risk * 20
        if amount_risk > 0.7:
            risk_factors.append("high_amount")
        
        # Velocity risk
        velocity_risk = self._calculate_velocity_risk(transaction)
        base_score += velocity_risk * 15
        if velocity_risk > 0.7:
            risk_factors.append("high_velocity")
        
        # Pattern risk
        pattern_risk = self._calculate_pattern_risk(transaction)
        base_score += pattern_risk * 15
        if pattern_risk > 0.7:
            risk_factors.append("unusual_pattern")
        
        # Geographic risk
        geo_risk = self._calculate_transaction_geo_risk(transaction)
        base_score += geo_risk * 25
        if geo_risk > 0.7:
            risk_factors.append("high_risk_geography")
        
        # Counterparty risk
        counterparty_risk = self._calculate_counterparty_risk(transaction)
        base_score += counterparty_risk * 15
        if counterparty_risk > 0.7:
            risk_factors.append("high_risk_counterparty")
        
        # Time-based risk
        time_risk = self._calculate_time_risk(transaction)
        base_score += time_risk * 10
        if time_risk > 0.7:
            risk_factors.append("unusual_timing")
        
        # Apply ML model if requested
        ml_score = None
        if apply_ml_model:
            ml_score = self._apply_ml_model(transaction)
            # Blend ML score with rule-based score
            final_score = (base_score * 0.6) + (ml_score * 0.4)
        else:
            final_score = base_score
        
        # Update transaction
        transaction.risk_score = final_score
        transaction.rule_score = base_score
        transaction.ml_score = ml_score
        transaction.risk_factors = {"factors": risk_factors}
        transaction.is_high_risk = final_score > 70
        transaction.requires_review = final_score > 60
        
        self.db.commit()
        
        return {
            "transaction_id": transaction_id,
            "risk_score": final_score,
            "rule_score": base_score,
            "ml_score": ml_score,
            "risk_factors": risk_factors,
            "is_high_risk": final_score > 70,
            "requires_review": final_score > 60
        }
    
    def _calculate_geographic_risk(self, customer: CustomerProfile) -> float:
        """Calculate geographic risk based on customer's country and related factors"""
        risk = 0.0
        
        # Country risk
        if customer.country in self.high_risk_countries:
            risk = 80.0
            customer.high_risk_country = True
        elif customer.country:
            # Assign moderate risk for certain regions
            risk = 30.0
        
        # PEP status adds to geographic risk
        if customer.pep_status:
            risk = min(100, risk + 30)
        
        return risk
    
    def _calculate_product_risk(self, customer: CustomerProfile) -> float:
        """Calculate risk based on products and services used"""
        # This would typically check account types, products used, etc.
        # For now, returning a moderate default
        return 40.0
    
    def _calculate_channel_risk(self, customer: CustomerProfile) -> float:
        """Calculate risk based on banking channels used"""
        # Online-only customers might have higher risk
        # For now, returning a moderate default
        return 35.0
    
    def _calculate_customer_type_risk(self, customer: CustomerProfile) -> float:
        """Calculate risk based on customer type and business"""
        risk = 0.0
        
        if customer.customer_type == "corporate":
            risk = 50.0
            
            # Check for high-risk business types
            if customer.occupation in self.high_risk_businesses:
                risk = 80.0
                customer.high_risk_business = True
        else:
            risk = 30.0
        
        # Adjust for missing KYC
        if customer.kyc_status != "completed":
            risk = min(100, risk + 20)
        
        return risk
    
    def _calculate_transaction_risk(self, customer: CustomerProfile) -> float:
        """Calculate risk based on transaction history and patterns"""
        # Query recent transactions
        recent_transactions = self.db.query(Transaction).filter(
            Transaction.customer_id == customer.id,
            Transaction.transaction_date >= datetime.utcnow() - timedelta(days=90)
        ).all()
        
        if not recent_transactions:
            return 20.0  # Low risk for new customers
        
        # Calculate transaction metrics
        amounts = [t.amount for t in recent_transactions]
        avg_amount = np.mean(amounts)
        std_amount = np.std(amounts)
        
        risk = 30.0  # Base risk
        
        # High average transaction amount
        if avg_amount > 10000:
            risk += 20
        
        # High variance in amounts (potential structuring)
        if std_amount > avg_amount * 0.5:
            risk += 15
        
        # Many cash transactions
        cash_ratio = sum(1 for t in recent_transactions if t.is_cash) / len(recent_transactions)
        if cash_ratio > 0.5:
            risk += 20
        
        return min(100, risk)
    
    def _calculate_amount_risk(self, transaction: Transaction) -> float:
        """Calculate risk based on transaction amount"""
        # Define thresholds
        if transaction.amount >= 50000:
            return 1.0
        elif transaction.amount >= 10000:
            return 0.7
        elif transaction.amount >= 5000:
            return 0.5
        else:
            return transaction.amount / 10000  # Linear scale for smaller amounts
    
    def _calculate_velocity_risk(self, transaction: Transaction) -> float:
        """Calculate risk based on transaction velocity"""
        if not transaction.customer_id:
            return 0.3
        
        # Check recent transactions
        recent_count = self.db.query(Transaction).filter(
            Transaction.customer_id == transaction.customer_id,
            Transaction.transaction_date >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        if recent_count > 10:
            return 1.0
        elif recent_count > 5:
            return 0.7
        else:
            return recent_count / 10
    
    def _calculate_pattern_risk(self, transaction: Transaction) -> float:
        """Detect unusual patterns in transaction"""
        risk = 0.0
        
        # Round amount detection (potential structuring)
        if transaction.amount % 1000 == 0:
            risk += 0.3
        
        # Just under reporting threshold
        if 9900 <= transaction.amount <= 9999:
            risk += 0.5
            transaction.is_structured = True
        
        return min(1.0, risk)
    
    def _calculate_transaction_geo_risk(self, transaction: Transaction) -> float:
        """Calculate geographic risk for transaction"""
        risk = 0.0
        
        if transaction.destination_country in self.high_risk_countries:
            risk = 1.0
        elif transaction.originating_country in self.high_risk_countries:
            risk = 0.8
        elif transaction.counterparty_country in self.high_risk_countries:
            risk = 0.7
        
        return risk
    
    def _calculate_counterparty_risk(self, transaction: Transaction) -> float:
        """Calculate risk based on counterparty information"""
        # This would check counterparty against watchlists, etc.
        # For now, return moderate risk if counterparty is unknown
        if not transaction.counterparty_name:
            return 0.5
        return 0.3
    
    def _calculate_time_risk(self, transaction: Transaction) -> float:
        """Calculate risk based on transaction timing"""
        hour = transaction.transaction_date.hour
        
        # Unusual hours (late night/early morning)
        if 2 <= hour <= 5:
            return 0.7
        elif 22 <= hour or hour <= 6:
            return 0.5
        
        # Weekend transactions
        if transaction.transaction_date.weekday() >= 5:
            return 0.4
        
        return 0.2
    
    def _apply_ml_model(self, transaction: Transaction) -> float:
        """Apply machine learning model for risk scoring"""
        # Placeholder for ML model integration
        # In production, this would call an actual ML model
        return np.random.uniform(30, 80)
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level based on score"""
        if score >= 75:
            return RiskLevel.CRITICAL
        elif score >= 50:
            return RiskLevel.HIGH
        elif score >= 25:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_next_review_date(self, risk_level: RiskLevel) -> datetime:
        """Calculate next review date based on risk level"""
        days_map = {
            RiskLevel.CRITICAL: 30,
            RiskLevel.HIGH: 90,
            RiskLevel.MEDIUM: 180,
            RiskLevel.LOW: 365
        }
        return datetime.utcnow() + timedelta(days=days_map[risk_level])
    
    def _get_high_risk_indicators(
        self,
        customer: CustomerProfile,
        risk_profile: CustomerRiskProfile
    ) -> List[str]:
        """Get list of high risk indicators for customer"""
        indicators = []
        
        if customer.pep_status:
            indicators.append("PEP")
        if customer.high_risk_country:
            indicators.append("High Risk Country")
        if customer.high_risk_business:
            indicators.append("High Risk Business")
        if customer.kyc_status != "completed":
            indicators.append("Incomplete KYC")
        if risk_profile.str_count > 0:
            indicators.append(f"STR Filed ({risk_profile.str_count})")
        if risk_profile.alert_count > 10:
            indicators.append("High Alert Count")
        
        return indicators