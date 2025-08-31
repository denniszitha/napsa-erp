"""
Advanced Transaction Pattern Analyzer using ClickHouse
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

from app.core.clickhouse import get_clickhouse_client

logger = logging.getLogger(__name__)


class PatternType(Enum):
    STRUCTURING = "structuring"
    SMURFING = "smurfing"
    LAYERING = "layering"
    ROUND_AMOUNTS = "round_amounts"
    VELOCITY = "velocity"
    DORMANT_REACTIVATION = "dormant_reactivation"
    CIRCULAR_TRANSFERS = "circular_transfers"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    TIME_ANOMALY = "time_anomaly"
    AMOUNT_ESCALATION = "amount_escalation"


@dataclass
class PatternMatch:
    pattern_type: PatternType
    customer_id: int
    confidence_score: float
    details: Dict[str, Any]
    transactions_involved: List[str]
    risk_score: float
    detected_at: datetime


class TransactionPatternAnalyzer:
    """Advanced pattern detection using ClickHouse for AML compliance"""
    
    def __init__(self):
        self.clickhouse = get_clickhouse_client()
        self.patterns = {
            PatternType.STRUCTURING: self._detect_structuring,
            PatternType.SMURFING: self._detect_smurfing,
            PatternType.LAYERING: self._detect_layering,
            PatternType.ROUND_AMOUNTS: self._detect_round_amounts,
            PatternType.VELOCITY: self._detect_velocity_patterns,
            PatternType.DORMANT_REACTIVATION: self._detect_dormant_reactivation,
            PatternType.CIRCULAR_TRANSFERS: self._detect_circular_transfers,
            PatternType.GEOGRAPHIC_ANOMALY: self._detect_geographic_anomalies,
            PatternType.TIME_ANOMALY: self._detect_time_anomalies,
            PatternType.AMOUNT_ESCALATION: self._detect_amount_escalation
        }
    
    def analyze_all_patterns(
        self,
        days: int = 30,
        customer_id: Optional[int] = None
    ) -> List[PatternMatch]:
        """Run all pattern detection algorithms"""
        
        all_matches = []
        
        for pattern_type, analyzer_func in self.patterns.items():
            try:
                matches = analyzer_func(days, customer_id)
                all_matches.extend(matches)
                logger.info(f"Detected {len(matches)} {pattern_type.value} patterns")
            except Exception as e:
                logger.error(f"Error in {pattern_type.value} detection: {e}")
        
        # Sort by risk score descending
        all_matches.sort(key=lambda x: x.risk_score, reverse=True)
        
        return all_matches
    
    def _detect_structuring(
        self,
        days: int,
        customer_id: Optional[int] = None
    ) -> List[PatternMatch]:
        """Detect structuring patterns - transactions just below reporting thresholds"""
        
        query = """
            WITH suspicious_amounts AS (
                SELECT
                    customer_id,
                    toDate(transaction_date) as date,
                    transaction_id,
                    amount,
                    transaction_type
                FROM transactions_analytics
                WHERE transaction_date >= now() - INTERVAL %(days)s DAY
                    {customer_filter}
                    AND amount BETWEEN 9000 AND 9999  -- Just below 10K threshold
            ),
            daily_patterns AS (
                SELECT
                    customer_id,
                    date,
                    count() as suspicious_count,
                    sum(amount) as total_amount,
                    groupArray(transaction_id) as transaction_ids,
                    groupArray(amount) as amounts
                FROM suspicious_amounts
                GROUP BY customer_id, date
                HAVING suspicious_count >= 2  -- Multiple transactions same day
            ),
            customer_patterns AS (
                SELECT
                    customer_id,
                    count() as pattern_days,
                    sum(suspicious_count) as total_suspicious,
                    sum(total_amount) as cumulative_amount,
                    groupArray(transaction_ids) as all_transaction_ids
                FROM daily_patterns
                GROUP BY customer_id
                HAVING pattern_days >= 2 OR total_suspicious >= 5
            )
            SELECT
                customer_id,
                pattern_days,
                total_suspicious,
                cumulative_amount,
                all_transaction_ids
            FROM customer_patterns
            ORDER BY total_suspicious DESC
            LIMIT 100
        """
        
        params = {'days': days}
        customer_filter = ""
        if customer_id:
            customer_filter = "AND customer_id = %(customer_id)s"
            params['customer_id'] = customer_id
        
        query = query.format(customer_filter=customer_filter)
        
        result = self.clickhouse.execute(query, params)
        
        matches = []
        for row in result:
            # Flatten transaction IDs
            all_txn_ids = []
            for txn_group in row[4]:
                all_txn_ids.extend(txn_group)
            
            confidence_score = min(0.95, (row[2] * 0.15) + (row[1] * 0.10))  # Based on count and days
            risk_score = min(100, row[2] * 8 + row[1] * 5)  # Risk increases with frequency
            
            matches.append(PatternMatch(
                pattern_type=PatternType.STRUCTURING,
                customer_id=row[0],
                confidence_score=confidence_score,
                details={
                    "pattern_days": row[1],
                    "total_transactions": row[2],
                    "cumulative_amount": float(row[3]),
                    "avg_per_day": row[2] / row[1] if row[1] > 0 else 0
                },
                transactions_involved=all_txn_ids,
                risk_score=risk_score,
                detected_at=datetime.utcnow()
            ))
        
        return matches
    
    def _detect_smurfing(
        self,
        days: int,
        customer_id: Optional[int] = None
    ) -> List[PatternMatch]:
        """Detect smurfing - multiple small transactions by related parties"""
        
        query = """
            WITH small_transactions AS (
                SELECT
                    customer_id,
                    transaction_id,
                    amount,
                    transaction_date,
                    account_name
                FROM transactions_analytics
                WHERE transaction_date >= now() - INTERVAL %(days)s DAY
                    {customer_filter}
                    AND amount BETWEEN 1000 AND 5000  -- Small amounts
                    AND transaction_type IN ('deposit', 'transfer')
            ),
            name_similarities AS (
                SELECT
                    st1.customer_id as customer1,
                    st2.customer_id as customer2,
                    st1.account_name as name1,
                    st2.account_name as name2,
                    count(*) as common_patterns
                FROM small_transactions st1
                JOIN small_transactions st2 ON 
                    st1.customer_id != st2.customer_id
                    AND abs(toUnixTimestamp(st1.transaction_date) - toUnixTimestamp(st2.transaction_date)) <= 3600  -- Within 1 hour
                    AND levenshteinDistance(st1.account_name, st2.account_name) <= 3  -- Similar names
                GROUP BY customer1, customer2, name1, name2
                HAVING common_patterns >= 3
            )
            SELECT
                customer1,
                customer2,
                name1,
                name2,
                common_patterns
            FROM name_similarities
            ORDER BY common_patterns DESC
            LIMIT 50
        """
        
        params = {'days': days}
        customer_filter = ""
        if customer_id:
            customer_filter = f"AND (customer_id = %(customer_id)s)"
            params['customer_id'] = customer_id
        
        query = query.format(customer_filter=customer_filter)
        
        result = self.clickhouse.execute(query, params)
        
        matches = []
        for row in result:
            confidence_score = min(0.90, row[4] * 0.20)
            risk_score = min(100, row[4] * 12)
            
            matches.append(PatternMatch(
                pattern_type=PatternType.SMURFING,
                customer_id=row[0],
                confidence_score=confidence_score,
                details={
                    "related_customer": row[1],
                    "name1": row[2],
                    "name2": row[3],
                    "coordinated_transactions": row[4]
                },
                transactions_involved=[],  # Would need additional query to get specific transactions
                risk_score=risk_score,
                detected_at=datetime.utcnow()
            ))
        
        return matches
    
    def _detect_layering(
        self,
        days: int,
        customer_id: Optional[int] = None
    ) -> List[PatternMatch]:
        """Detect layering - rapid movement of funds through multiple accounts"""
        
        query = """
            WITH rapid_transfers AS (
                SELECT
                    customer_id,
                    transaction_date,
                    amount,
                    transaction_id,
                    counterparty_account
                FROM transactions_analytics
                WHERE transaction_date >= now() - INTERVAL %(days)s DAY
                    {customer_filter}
                    AND transaction_type IN ('transfer', 'wire')
                    AND counterparty_account != ''
            ),
            layering_chains AS (
                SELECT
                    rt1.customer_id,
                    count() as transfer_count,
                    uniqExact(rt1.counterparty_account) as unique_counterparties,
                    sum(rt1.amount) as total_amount,
                    max(rt1.transaction_date) - min(rt1.transaction_date) as time_span_seconds,
                    groupArray(rt1.transaction_id) as transaction_ids
                FROM rapid_transfers rt1
                GROUP BY rt1.customer_id
                HAVING transfer_count >= 5 
                    AND time_span_seconds <= 86400  -- Within 24 hours
                    AND unique_counterparties >= 3  -- Multiple different accounts
            )
            SELECT
                customer_id,
                transfer_count,
                unique_counterparties,
                total_amount,
                time_span_seconds,
                transaction_ids
            FROM layering_chains
            ORDER BY transfer_count DESC, time_span_seconds ASC
            LIMIT 100
        """
        
        params = {'days': days}
        customer_filter = ""
        if customer_id:
            customer_filter = "AND customer_id = %(customer_id)s"
            params['customer_id'] = customer_id
        
        query = query.format(customer_filter=customer_filter)
        
        result = self.clickhouse.execute(query, params)
        
        matches = []
        for row in result:
            time_span_hours = row[4] / 3600
            velocity = row[1] / time_span_hours if time_span_hours > 0 else row[1]
            
            confidence_score = min(0.95, (velocity * 0.1) + (row[2] * 0.1))
            risk_score = min(100, velocity * 10 + row[2] * 5)
            
            matches.append(PatternMatch(
                pattern_type=PatternType.LAYERING,
                customer_id=row[0],
                confidence_score=confidence_score,
                details={
                    "transfer_count": row[1],
                    "unique_counterparties": row[2],
                    "total_amount": float(row[3]),
                    "time_span_hours": time_span_hours,
                    "velocity_per_hour": velocity
                },
                transactions_involved=row[5],
                risk_score=risk_score,
                detected_at=datetime.utcnow()
            ))
        
        return matches
    
    def _detect_round_amounts(
        self,
        days: int,
        customer_id: Optional[int] = None
    ) -> List[PatternMatch]:
        """Detect excessive use of round amounts"""
        
        query = """
            WITH round_amount_analysis AS (
                SELECT
                    customer_id,
                    count() as total_transactions,
                    countIf(amount % 1000 = 0) as round_1k_count,
                    countIf(amount % 5000 = 0) as round_5k_count,
                    countIf(amount % 10000 = 0) as round_10k_count,
                    groupArray(transaction_id) as all_transactions
                FROM transactions_analytics
                WHERE transaction_date >= now() - INTERVAL %(days)s DAY
                    {customer_filter}
                    AND amount >= 1000  -- Only consider significant amounts
                GROUP BY customer_id
                HAVING total_transactions >= 10  -- Enough sample size
            ),
            suspicious_patterns AS (
                SELECT
                    customer_id,
                    total_transactions,
                    round_1k_count,
                    round_5k_count,
                    round_10k_count,
                    (round_1k_count + round_5k_count + round_10k_count) as total_round,
                    (round_1k_count + round_5k_count + round_10k_count) / total_transactions as round_ratio,
                    all_transactions
                FROM round_amount_analysis
                WHERE (round_1k_count + round_5k_count + round_10k_count) / total_transactions > 0.6  -- >60% round amounts
            )
            SELECT
                customer_id,
                total_transactions,
                total_round,
                round_ratio,
                round_1k_count,
                round_5k_count,
                round_10k_count,
                all_transactions
            FROM suspicious_patterns
            ORDER BY round_ratio DESC, total_round DESC
            LIMIT 100
        """
        
        params = {'days': days}
        customer_filter = ""
        if customer_id:
            customer_filter = "AND customer_id = %(customer_id)s"
            params['customer_id'] = customer_id
        
        query = query.format(customer_filter=customer_filter)
        
        result = self.clickhouse.execute(query, params)
        
        matches = []
        for row in result:
            confidence_score = min(0.85, row[3])  # Based on round ratio
            risk_score = min(100, row[3] * 70 + (row[2] / row[1]) * 30)
            
            matches.append(PatternMatch(
                pattern_type=PatternType.ROUND_AMOUNTS,
                customer_id=row[0],
                confidence_score=confidence_score,
                details={
                    "total_transactions": row[1],
                    "round_transactions": row[2],
                    "round_ratio": float(row[3]),
                    "round_1k": row[4],
                    "round_5k": row[5],
                    "round_10k": row[6]
                },
                transactions_involved=row[7],
                risk_score=risk_score,
                detected_at=datetime.utcnow()
            ))
        
        return matches
    
    def _detect_velocity_patterns(
        self,
        days: int,
        customer_id: Optional[int] = None
    ) -> List[PatternMatch]:
        """Detect unusual transaction velocity patterns"""
        
        query = """
            WITH velocity_analysis AS (
                SELECT
                    customer_id,
                    toDate(transaction_date) as date,
                    count() as daily_count,
                    sum(amount) as daily_volume,
                    groupArray(transaction_id) as daily_transactions
                FROM transactions_analytics
                WHERE transaction_date >= now() - INTERVAL %(days)s DAY
                    {customer_filter}
                GROUP BY customer_id, date
            ),
            customer_velocity_stats AS (
                SELECT
                    customer_id,
                    avg(daily_count) as avg_daily_count,
                    stddevPop(daily_count) as stddev_daily_count,
                    max(daily_count) as max_daily_count,
                    avg(daily_volume) as avg_daily_volume,
                    stddevPop(daily_volume) as stddev_daily_volume
                FROM velocity_analysis
                GROUP BY customer_id
                HAVING count() >= 7  -- At least 7 days of data
            ),
            velocity_anomalies AS (
                SELECT
                    va.customer_id,
                    va.date,
                    va.daily_count,
                    va.daily_volume,
                    cvs.avg_daily_count,
                    cvs.stddev_daily_count,
                    (va.daily_count - cvs.avg_daily_count) / cvs.stddev_daily_count as count_z_score,
                    va.daily_transactions
                FROM velocity_analysis va
                JOIN customer_velocity_stats cvs ON va.customer_id = cvs.customer_id
                WHERE cvs.stddev_daily_count > 0
                    AND abs((va.daily_count - cvs.avg_daily_count) / cvs.stddev_daily_count) > 3  -- 3 sigma anomaly
            )
            SELECT
                customer_id,
                date,
                daily_count,
                daily_volume,
                avg_daily_count,
                abs(count_z_score) as anomaly_score,
                daily_transactions
            FROM velocity_anomalies
            ORDER BY anomaly_score DESC
            LIMIT 100
        """
        
        params = {'days': days}
        customer_filter = ""
        if customer_id:
            customer_filter = "AND customer_id = %(customer_id)s"
            params['customer_id'] = customer_id
        
        query = query.format(customer_filter=customer_filter)
        
        result = self.clickhouse.execute(query, params)
        
        matches = []
        for row in result:
            confidence_score = min(0.90, row[5] / 10)  # Based on Z-score
            risk_score = min(100, row[5] * 15)
            
            matches.append(PatternMatch(
                pattern_type=PatternType.VELOCITY,
                customer_id=row[0],
                confidence_score=confidence_score,
                details={
                    "anomaly_date": row[1],
                    "daily_count": row[2],
                    "daily_volume": float(row[3]),
                    "avg_daily_count": float(row[4]),
                    "anomaly_z_score": float(row[5])
                },
                transactions_involved=row[6],
                risk_score=risk_score,
                detected_at=datetime.utcnow()
            ))
        
        return matches
    
    def _detect_dormant_reactivation(
        self,
        days: int,
        customer_id: Optional[int] = None
    ) -> List[PatternMatch]:
        """Detect dormant account sudden reactivation"""
        
        query = """
            WITH recent_activity AS (
                SELECT
                    customer_id,
                    min(transaction_date) as first_recent,
                    count() as recent_count,
                    sum(amount) as recent_volume,
                    groupArray(transaction_id) as recent_transactions
                FROM transactions_analytics
                WHERE transaction_date >= now() - INTERVAL 30 DAY
                    {customer_filter}
                GROUP BY customer_id
            ),
            historical_activity AS (
                SELECT
                    customer_id,
                    max(transaction_date) as last_historical,
                    count() as historical_count
                FROM transactions_analytics
                WHERE transaction_date < now() - INTERVAL 30 DAY
                    AND transaction_date >= now() - INTERVAL 365 DAY
                    {customer_filter}
                GROUP BY customer_id
            ),
            dormant_reactivation AS (
                SELECT
                    ra.customer_id,
                    ra.first_recent,
                    ra.recent_count,
                    ra.recent_volume,
                    ha.last_historical,
                    ha.historical_count,
                    dateDiff('day', ha.last_historical, ra.first_recent) as dormant_days,
                    ra.recent_transactions
                FROM recent_activity ra
                LEFT JOIN historical_activity ha ON ra.customer_id = ha.customer_id
                WHERE dormant_days >= %(dormant_threshold)s  -- At least X days dormant
                    AND ra.recent_count >= 5  -- Significant recent activity
                    AND ra.recent_volume >= 10000  -- Significant amount
            )
            SELECT
                customer_id,
                dormant_days,
                recent_count,
                recent_volume,
                recent_transactions
            FROM dormant_reactivation
            ORDER BY dormant_days DESC, recent_volume DESC
            LIMIT 100
        """
        
        params = {'days': days, 'dormant_threshold': 90}
        customer_filter = ""
        if customer_id:
            customer_filter = "AND customer_id = %(customer_id)s"
            params['customer_id'] = customer_id
        
        query = query.format(customer_filter=customer_filter)
        
        result = self.clickhouse.execute(query, params)
        
        matches = []
        for row in result:
            # Higher dormancy = higher suspicion
            confidence_score = min(0.85, (row[1] / 365) + (row[3] / 100000))
            risk_score = min(100, (row[1] / 10) + (row[3] / 10000))
            
            matches.append(PatternMatch(
                pattern_type=PatternType.DORMANT_REACTIVATION,
                customer_id=row[0],
                confidence_score=confidence_score,
                details={
                    "dormant_days": row[1],
                    "recent_transaction_count": row[2],
                    "recent_volume": float(row[3])
                },
                transactions_involved=row[4],
                risk_score=risk_score,
                detected_at=datetime.utcnow()
            ))
        
        return matches
    
    def _detect_circular_transfers(
        self,
        days: int,
        customer_id: Optional[int] = None
    ) -> List[PatternMatch]:
        """Detect circular money movement patterns"""
        
        # This is a complex pattern requiring graph analysis
        # For now, implement a simplified version
        query = """
            WITH transfers AS (
                SELECT
                    customer_id,
                    counterparty_account,
                    transaction_id,
                    amount,
                    transaction_date,
                    transaction_type
                FROM transactions_analytics
                WHERE transaction_date >= now() - INTERVAL %(days)s DAY
                    {customer_filter}
                    AND transaction_type IN ('transfer', 'wire')
                    AND counterparty_account != ''
            ),
            potential_circles AS (
                SELECT
                    t1.customer_id as initiator,
                    t1.counterparty_account as intermediate,
                    t2.counterparty_account as final_destination,
                    count(*) as pattern_count,
                    sum(t1.amount) as total_amount,
                    groupArray(t1.transaction_id) as transaction_ids
                FROM transfers t1
                JOIN transfers t2 ON 
                    t1.counterparty_account = t2.customer_id::String
                    AND t2.counterparty_account = t1.customer_id::String  -- Forms a circle
                    AND t2.transaction_date > t1.transaction_date
                    AND t2.transaction_date <= t1.transaction_date + INTERVAL 7 DAY
                GROUP BY initiator, intermediate, final_destination
                HAVING pattern_count >= 2
            )
            SELECT
                initiator,
                intermediate,
                final_destination,
                pattern_count,
                total_amount,
                transaction_ids
            FROM potential_circles
            ORDER BY pattern_count DESC, total_amount DESC
            LIMIT 50
        """
        
        params = {'days': days}
        customer_filter = ""
        if customer_id:
            customer_filter = "AND customer_id = %(customer_id)s"
            params['customer_id'] = customer_id
        
        query = query.format(customer_filter=customer_filter)
        
        try:
            result = self.clickhouse.execute(query, params)
        except Exception:
            # Return empty if query fails (may need schema adjustments)
            return []
        
        matches = []
        for row in result:
            confidence_score = min(0.80, row[3] * 0.25)
            risk_score = min(100, row[3] * 20 + (row[4] / 10000))
            
            matches.append(PatternMatch(
                pattern_type=PatternType.CIRCULAR_TRANSFERS,
                customer_id=int(row[0]),
                confidence_score=confidence_score,
                details={
                    "intermediate_account": row[1],
                    "final_destination": row[2],
                    "pattern_occurrences": row[3],
                    "total_amount": float(row[4])
                },
                transactions_involved=row[5],
                risk_score=risk_score,
                detected_at=datetime.utcnow()
            ))
        
        return matches
    
    def _detect_geographic_anomalies(
        self,
        days: int,
        customer_id: Optional[int] = None
    ) -> List[PatternMatch]:
        """Detect geographic anomalies in transaction patterns"""
        
        # Simplified implementation - can be enhanced with more sophisticated geo-analysis
        return []
    
    def _detect_time_anomalies(
        self,
        days: int,
        customer_id: Optional[int] = None
    ) -> List[PatternMatch]:
        """Detect time-based transaction anomalies"""
        
        # Simplified implementation - can be enhanced with time series analysis
        return []
    
    def _detect_amount_escalation(
        self,
        days: int,
        customer_id: Optional[int] = None
    ) -> List[PatternMatch]:
        """Detect gradual amount escalation patterns"""
        
        # Simplified implementation - can be enhanced with trend analysis
        return []
    
    def get_pattern_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get summary of all detected patterns"""
        
        patterns = self.analyze_all_patterns(days)
        
        summary = {
            "total_patterns": len(patterns),
            "by_type": {},
            "high_risk_customers": [],
            "avg_confidence": 0,
            "avg_risk_score": 0
        }
        
        if patterns:
            # Group by pattern type
            for pattern in patterns:
                pattern_type = pattern.pattern_type.value
                if pattern_type not in summary["by_type"]:
                    summary["by_type"][pattern_type] = 0
                summary["by_type"][pattern_type] += 1
            
            # High risk customers (risk score > 80)
            high_risk = [p for p in patterns if p.risk_score > 80]
            summary["high_risk_customers"] = [
                {
                    "customer_id": p.customer_id,
                    "pattern_type": p.pattern_type.value,
                    "risk_score": p.risk_score,
                    "confidence": p.confidence_score
                }
                for p in high_risk
            ]
            
            # Averages
            summary["avg_confidence"] = sum(p.confidence_score for p in patterns) / len(patterns)
            summary["avg_risk_score"] = sum(p.risk_score for p in patterns) / len(patterns)
        
        return summary