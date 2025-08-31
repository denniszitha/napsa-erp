from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func
import re

from app.models.aml import Transaction, TransactionAlert, CustomerProfile
from app.models.aml.transaction import AlertSeverity, TransactionType


class TransactionMonitoringService:
    """Service for monitoring transactions and detecting suspicious patterns"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Define monitoring rules
        self.rules = [
            {
                "id": "R001",
                "name": "Large Cash Transaction",
                "type": "amount_threshold",
                "params": {"amount": 10000, "types": ["cash", "deposit", "withdrawal"]}
            },
            {
                "id": "R002",
                "name": "Rapid Movement of Funds",
                "type": "velocity",
                "params": {"hours": 24, "count": 5, "amount": 5000}
            },
            {
                "id": "R003",
                "name": "Structuring Pattern",
                "type": "structuring",
                "params": {"threshold": 10000, "margin": 500, "period_hours": 24}
            },
            {
                "id": "R004",
                "name": "High Risk Country",
                "type": "geographic",
                "params": {"countries": ["IR", "KP", "SY", "YE", "AF", "MM"]}
            },
            {
                "id": "R005",
                "name": "Unusual Time Pattern",
                "type": "timing",
                "params": {"hours": [2, 3, 4, 5]}
            },
            {
                "id": "R006",
                "name": "Round Amount Pattern",
                "type": "round_amount",
                "params": {"divisor": 1000, "min_amount": 5000}
            },
            {
                "id": "R007",
                "name": "Dormant Account Sudden Activity",
                "type": "dormancy",
                "params": {"dormant_days": 180, "amount": 5000}
            }
        ]
    
    def monitor_transaction(self, transaction_id: int) -> Dict[str, Any]:
        """Monitor a single transaction for suspicious patterns"""
        
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        alerts = []
        risk_indicators = []
        
        # Apply each rule
        for rule in self.rules:
            result = self._apply_rule(transaction, rule)
            if result["triggered"]:
                alerts.append({
                    "alert_type": rule["type"],
                    "title": rule["name"],
                    "description": result["description"],
                    "severity": result["severity"],
                    "rule_id": rule["id"],
                    "rule_name": rule["name"],
                    "score": result.get("score", 50),
                    "details": result.get("details", {})
                })
                risk_indicators.append(rule["name"])
        
        # Check for pattern combinations
        pattern_alerts = self._check_pattern_combinations(transaction, risk_indicators)
        alerts.extend(pattern_alerts)
        
        return {
            "transaction_id": transaction_id,
            "alerts": alerts,
            "risk_indicators": risk_indicators,
            "total_alerts": len(alerts),
            "max_severity": max([a["severity"] for a in alerts]) if alerts else None
        }
    
    def _apply_rule(self, transaction: Transaction, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a specific monitoring rule to a transaction"""
        
        rule_type = rule["type"]
        params = rule["params"]
        
        if rule_type == "amount_threshold":
            return self._check_amount_threshold(transaction, params)
        elif rule_type == "velocity":
            return self._check_velocity(transaction, params)
        elif rule_type == "structuring":
            return self._check_structuring(transaction, params)
        elif rule_type == "geographic":
            return self._check_geographic(transaction, params)
        elif rule_type == "timing":
            return self._check_timing(transaction, params)
        elif rule_type == "round_amount":
            return self._check_round_amount(transaction, params)
        elif rule_type == "dormancy":
            return self._check_dormancy(transaction, params)
        else:
            return {"triggered": False}
    
    def _check_amount_threshold(self, transaction: Transaction, params: Dict) -> Dict[str, Any]:
        """Check if transaction exceeds amount threshold"""
        
        if transaction.transaction_type.value in params.get("types", []):
            if transaction.amount >= params["amount"]:
                return {
                    "triggered": True,
                    "description": f"Large {transaction.transaction_type.value} transaction of {transaction.amount} {transaction.currency}",
                    "severity": AlertSeverity.HIGH if transaction.amount >= params["amount"] * 2 else AlertSeverity.MEDIUM,
                    "score": min(100, (transaction.amount / params["amount"]) * 50),
                    "details": {
                        "amount": transaction.amount,
                        "threshold": params["amount"],
                        "type": transaction.transaction_type.value
                    }
                }
        
        return {"triggered": False}
    
    def _check_velocity(self, transaction: Transaction, params: Dict) -> Dict[str, Any]:
        """Check for rapid movement of funds"""
        
        if not transaction.customer_id:
            return {"triggered": False}
        
        time_threshold = datetime.utcnow() - timedelta(hours=params["hours"])
        
        recent_transactions = self.db.query(Transaction).filter(
            Transaction.customer_id == transaction.customer_id,
            Transaction.transaction_date >= time_threshold,
            Transaction.id != transaction.id
        ).all()
        
        if len(recent_transactions) >= params["count"]:
            total_amount = sum(t.amount for t in recent_transactions) + transaction.amount
            if total_amount >= params["amount"]:
                return {
                    "triggered": True,
                    "description": f"Rapid movement of funds: {len(recent_transactions)+1} transactions totaling {total_amount} in {params['hours']} hours",
                    "severity": AlertSeverity.HIGH,
                    "score": min(100, (len(recent_transactions) / params["count"]) * 60),
                    "details": {
                        "transaction_count": len(recent_transactions) + 1,
                        "total_amount": total_amount,
                        "period_hours": params["hours"]
                    }
                }
        
        return {"triggered": False}
    
    def _check_structuring(self, transaction: Transaction, params: Dict) -> Dict[str, Any]:
        """Check for potential structuring patterns"""
        
        threshold = params["threshold"]
        margin = params["margin"]
        
        # Check if amount is just below threshold
        if threshold - margin <= transaction.amount < threshold:
            # Look for similar transactions
            time_threshold = datetime.utcnow() - timedelta(hours=params["period_hours"])
            
            similar_transactions = self.db.query(Transaction).filter(
                Transaction.customer_id == transaction.customer_id,
                Transaction.transaction_date >= time_threshold,
                Transaction.amount >= threshold - margin,
                Transaction.amount < threshold,
                Transaction.id != transaction.id
            ).count()
            
            if similar_transactions > 0:
                return {
                    "triggered": True,
                    "description": f"Potential structuring: Multiple transactions just below {threshold} threshold",
                    "severity": AlertSeverity.HIGH,
                    "score": 80,
                    "details": {
                        "amount": transaction.amount,
                        "threshold": threshold,
                        "similar_count": similar_transactions
                    }
                }
        
        return {"triggered": False}
    
    def _check_geographic(self, transaction: Transaction, params: Dict) -> Dict[str, Any]:
        """Check for high-risk geographic locations"""
        
        high_risk_countries = params["countries"]
        
        countries_to_check = [
            transaction.originating_country,
            transaction.destination_country,
            transaction.counterparty_country
        ]
        
        for country in countries_to_check:
            if country in high_risk_countries:
                return {
                    "triggered": True,
                    "description": f"Transaction involves high-risk country: {country}",
                    "severity": AlertSeverity.HIGH,
                    "score": 90,
                    "details": {
                        "country": country,
                        "field": "originating" if country == transaction.originating_country 
                                else "destination" if country == transaction.destination_country 
                                else "counterparty"
                    }
                }
        
        return {"triggered": False}
    
    def _check_timing(self, transaction: Transaction, params: Dict) -> Dict[str, Any]:
        """Check for unusual transaction timing"""
        
        hour = transaction.transaction_date.hour
        
        if hour in params["hours"]:
            return {
                "triggered": True,
                "description": f"Transaction at unusual hour: {hour:02d}:00",
                "severity": AlertSeverity.MEDIUM,
                "score": 60,
                "details": {
                    "hour": hour,
                    "timestamp": transaction.transaction_date.isoformat()
                }
            }
        
        return {"triggered": False}
    
    def _check_round_amount(self, transaction: Transaction, params: Dict) -> Dict[str, Any]:
        """Check for round amount patterns"""
        
        if transaction.amount >= params["min_amount"]:
            if transaction.amount % params["divisor"] == 0:
                return {
                    "triggered": True,
                    "description": f"Round amount transaction: {transaction.amount}",
                    "severity": AlertSeverity.LOW,
                    "score": 40,
                    "details": {
                        "amount": transaction.amount,
                        "divisor": params["divisor"]
                    }
                }
        
        return {"triggered": False}
    
    def _check_dormancy(self, transaction: Transaction, params: Dict) -> Dict[str, Any]:
        """Check for sudden activity in dormant accounts"""
        
        if not transaction.customer_id:
            return {"triggered": False}
        
        # Get last transaction before this one
        last_transaction = self.db.query(Transaction).filter(
            Transaction.customer_id == transaction.customer_id,
            Transaction.id != transaction.id,
            Transaction.transaction_date < transaction.transaction_date
        ).order_by(Transaction.transaction_date.desc()).first()
        
        if last_transaction:
            days_dormant = (transaction.transaction_date - last_transaction.transaction_date).days
            
            if days_dormant >= params["dormant_days"] and transaction.amount >= params["amount"]:
                return {
                    "triggered": True,
                    "description": f"Sudden activity in dormant account: {days_dormant} days inactive",
                    "severity": AlertSeverity.HIGH,
                    "score": 75,
                    "details": {
                        "days_dormant": days_dormant,
                        "amount": transaction.amount,
                        "last_activity": last_transaction.transaction_date.isoformat()
                    }
                }
        
        return {"triggered": False}
    
    def _check_pattern_combinations(
        self,
        transaction: Transaction,
        risk_indicators: List[str]
    ) -> List[Dict[str, Any]]:
        """Check for combinations of patterns that increase risk"""
        
        alerts = []
        
        # High-risk combination: Large cash + Round amount
        if "Large Cash Transaction" in risk_indicators and "Round Amount Pattern" in risk_indicators:
            alerts.append({
                "alert_type": "pattern_combination",
                "title": "High Risk Pattern Combination",
                "description": "Large cash transaction with round amount - potential money laundering indicator",
                "severity": AlertSeverity.CRITICAL,
                "rule_id": "C001",
                "rule_name": "Pattern Combination - Cash + Round",
                "score": 95,
                "details": {
                    "patterns": ["Large Cash Transaction", "Round Amount Pattern"]
                }
            })
        
        # Structuring + Velocity
        if "Structuring Pattern" in risk_indicators and "Rapid Movement of Funds" in risk_indicators:
            alerts.append({
                "alert_type": "pattern_combination",
                "title": "Potential Structuring Scheme",
                "description": "Multiple structured transactions with rapid movement - high risk of intentional structuring",
                "severity": AlertSeverity.CRITICAL,
                "rule_id": "C002",
                "rule_name": "Pattern Combination - Structuring + Velocity",
                "score": 98,
                "details": {
                    "patterns": ["Structuring Pattern", "Rapid Movement of Funds"]
                }
            })
        
        return alerts
    
    def get_customer_transaction_patterns(
        self,
        customer_id: int,
        days: int = 90
    ) -> Dict[str, Any]:
        """Analyze transaction patterns for a customer"""
        
        time_threshold = datetime.utcnow() - timedelta(days=days)
        
        transactions = self.db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.transaction_date >= time_threshold
        ).all()
        
        if not transactions:
            return {
                "customer_id": customer_id,
                "period_days": days,
                "transaction_count": 0,
                "patterns": []
            }
        
        # Calculate statistics
        amounts = [t.amount for t in transactions]
        avg_amount = sum(amounts) / len(amounts)
        max_amount = max(amounts)
        min_amount = min(amounts)
        
        # Detect patterns
        patterns = []
        
        # Check for regular amounts
        amount_counts = {}
        for amount in amounts:
            amount_counts[amount] = amount_counts.get(amount, 0) + 1
        
        for amount, count in amount_counts.items():
            if count >= 3:
                patterns.append({
                    "type": "recurring_amount",
                    "description": f"Recurring amount {amount} appeared {count} times",
                    "risk_level": "medium"
                })
        
        # Check for time patterns
        hour_counts = {}
        for t in transactions:
            hour = t.transaction_date.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        for hour, count in hour_counts.items():
            if count > len(transactions) * 0.3:  # More than 30% at same hour
                patterns.append({
                    "type": "time_pattern",
                    "description": f"Frequent transactions at {hour:02d}:00 ({count} times)",
                    "risk_level": "low"
                })
        
        return {
            "customer_id": customer_id,
            "period_days": days,
            "transaction_count": len(transactions),
            "total_volume": sum(amounts),
            "avg_amount": avg_amount,
            "max_amount": max_amount,
            "min_amount": min_amount,
            "patterns": patterns
        }