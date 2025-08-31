"""
Advanced Analytics API using ClickHouse for high-performance queries
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from pydantic import BaseModel

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.core.clickhouse import get_clickhouse_client
from app.services.data_pipeline import get_data_pipeline

router = APIRouter()

# Response models
class TransactionAnalytics(BaseModel):
    date: date
    transaction_count: int
    total_volume: float
    avg_amount: float
    max_amount: float
    high_risk_count: int
    avg_risk_score: float
    unique_customers: int

class CustomerRiskDistribution(BaseModel):
    risk_level: str
    customer_count: int
    avg_score: float
    total_transactions: int
    total_volume: float

class AlertMetrics(BaseModel):
    date: date
    alert_type: str
    severity: str
    alert_count: int
    resolved_count: int
    false_positive_count: int
    avg_resolution_hours: Optional[float]

class PatternAnalysis(BaseModel):
    customer_id: int
    velocity_patterns: List[Dict[str, Any]]
    type_patterns: List[Dict[str, Any]]
    geographic_patterns: List[Dict[str, Any]]
    time_patterns: List[Dict[str, Any]]


@router.get("/transactions/summary", response_model=List[TransactionAnalytics])
def get_transaction_analytics(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed transaction analytics using ClickHouse"""
    
    clickhouse = get_clickhouse_client()
    
    # Convert dates to datetime for ClickHouse query
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    try:
        analytics_data = clickhouse.get_transaction_analytics(
            start_datetime, end_datetime, customer_id
        )
        
        return [TransactionAnalytics(**item) for item in analytics_data]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics query failed: {str(e)}")


@router.get("/customers/risk-distribution", response_model=List[CustomerRiskDistribution])
def get_customer_risk_distribution(
    snapshot_date: Optional[date] = Query(None, description="Snapshot date (defaults to today)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get customer risk distribution analytics"""
    
    clickhouse = get_clickhouse_client()
    
    if not snapshot_date:
        snapshot_date = datetime.utcnow().date()
    
    query = """
        SELECT
            risk_level,
            count() as customer_count,
            avg(risk_score) as avg_score,
            sum(transaction_count) as total_transactions,
            sum(total_volume) as total_volume
        FROM customer_risk_analytics
        WHERE snapshot_date = %(snapshot_date)s
        GROUP BY risk_level
        ORDER BY avg_score DESC
    """
    
    try:
        result = clickhouse.execute(query, {'snapshot_date': snapshot_date})
        
        return [
            CustomerRiskDistribution(
                risk_level=row[0],
                customer_count=row[1],
                avg_score=float(row[2]),
                total_transactions=row[3],
                total_volume=float(row[4])
            )
            for row in result
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk distribution query failed: {str(e)}")


@router.get("/alerts/metrics", response_model=List[AlertMetrics])
def get_alert_metrics(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get alert resolution and performance metrics"""
    
    clickhouse = get_clickhouse_client()
    
    query = """
        SELECT
            toDate(created_date) as date,
            alert_type,
            severity,
            count() as alert_count,
            countIf(status IN ('closed_confirmed', 'closed_false_positive')) as resolved_count,
            countIf(false_positive = 1) as false_positive_count,
            avg(resolution_time_hours) as avg_resolution_hours
        FROM alert_analytics
        WHERE created_date >= %(start_date)s
            AND created_date <= %(end_date)s
            {alert_type_filter}
        GROUP BY date, alert_type, severity
        ORDER BY date DESC, alert_count DESC
    """
    
    params = {
        'start_date': datetime.combine(start_date, datetime.min.time()),
        'end_date': datetime.combine(end_date, datetime.max.time())
    }
    
    alert_type_filter = ""
    if alert_type:
        alert_type_filter = "AND alert_type = %(alert_type)s"
        params['alert_type'] = alert_type
    
    query = query.format(alert_type_filter=alert_type_filter)
    
    try:
        result = clickhouse.execute(query, params)
        
        return [
            AlertMetrics(
                date=row[0],
                alert_type=row[1],
                severity=row[2],
                alert_count=row[3],
                resolved_count=row[4],
                false_positive_count=row[5],
                avg_resolution_hours=float(row[6]) if row[6] else None
            )
            for row in result
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert metrics query failed: {str(e)}")


@router.get("/customers/{customer_id}/patterns", response_model=PatternAnalysis)
def analyze_customer_patterns(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Analyze detailed transaction patterns for a customer using ClickHouse"""
    
    clickhouse = get_clickhouse_client()
    
    try:
        patterns = clickhouse.get_pattern_analysis(customer_id)
        
        return PatternAnalysis(
            customer_id=customer_id,
            velocity_patterns=patterns['velocity'],
            type_patterns=patterns['patterns_by_type'],
            geographic_patterns=patterns['geographic_distribution'],
            time_patterns=patterns['hourly_patterns']
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern analysis failed: {str(e)}")


@router.get("/transactions/velocity")
def get_transaction_velocity(
    lookback_hours: int = Query(24, description="Hours to look back"),
    threshold_multiplier: float = Query(3.0, description="Velocity threshold multiplier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Detect high-velocity transaction patterns"""
    
    clickhouse = get_clickhouse_client()
    
    query = """
        WITH customer_averages AS (
            SELECT
                customer_id,
                avg(hourly_count) as avg_hourly_transactions,
                stddevPop(hourly_count) as stddev_hourly_transactions
            FROM (
                SELECT
                    customer_id,
                    toStartOfHour(transaction_date) as hour,
                    count() as hourly_count
                FROM transactions_analytics
                WHERE transaction_date >= now() - INTERVAL 7 DAY
                GROUP BY customer_id, hour
            )
            GROUP BY customer_id
            HAVING count() >= 10  -- At least 10 data points
        ),
        recent_velocity AS (
            SELECT
                customer_id,
                count() as recent_count,
                max(amount) as max_amount,
                sum(amount) as total_amount
            FROM transactions_analytics
            WHERE transaction_date >= now() - INTERVAL %(lookback_hours)s HOUR
            GROUP BY customer_id
        )
        SELECT
            rv.customer_id,
            rv.recent_count,
            rv.max_amount,
            rv.total_amount,
            ca.avg_hourly_transactions * %(lookback_hours)s as expected_count,
            rv.recent_count / (ca.avg_hourly_transactions * %(lookback_hours)s) as velocity_ratio
        FROM recent_velocity rv
        JOIN customer_averages ca ON rv.customer_id = ca.customer_id
        WHERE rv.recent_count > ca.avg_hourly_transactions * %(lookback_hours)s * %(threshold_multiplier)s
        ORDER BY velocity_ratio DESC
        LIMIT 100
    """
    
    params = {
        'lookback_hours': lookback_hours,
        'threshold_multiplier': threshold_multiplier
    }
    
    try:
        result = clickhouse.execute(query, params)
        
        return {
            "high_velocity_customers": [
                {
                    "customer_id": row[0],
                    "recent_count": row[1],
                    "max_amount": float(row[2]),
                    "total_amount": float(row[3]),
                    "expected_count": float(row[4]),
                    "velocity_ratio": float(row[5])
                }
                for row in result
            ],
            "analysis_params": {
                "lookback_hours": lookback_hours,
                "threshold_multiplier": threshold_multiplier,
                "total_flagged": len(result)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Velocity analysis failed: {str(e)}")


@router.get("/transactions/anomalies")
def detect_transaction_anomalies(
    days: int = Query(30, description="Days to analyze"),
    sensitivity: float = Query(2.0, description="Anomaly detection sensitivity (standard deviations)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Detect transaction amount anomalies using statistical analysis"""
    
    clickhouse = get_clickhouse_client()
    
    query = """
        WITH customer_stats AS (
            SELECT
                customer_id,
                avg(amount) as avg_amount,
                stddevPop(amount) as stddev_amount,
                count() as transaction_count
            FROM transactions_analytics
            WHERE transaction_date >= now() - INTERVAL %(days)s DAY
            GROUP BY customer_id
            HAVING transaction_count >= 5  -- At least 5 transactions for statistical significance
        ),
        anomalies AS (
            SELECT
                t.customer_id,
                t.transaction_id,
                t.amount,
                t.transaction_date,
                t.transaction_type,
                cs.avg_amount,
                cs.stddev_amount,
                abs(t.amount - cs.avg_amount) / cs.stddev_amount as z_score
            FROM transactions_analytics t
            JOIN customer_stats cs ON t.customer_id = cs.customer_id
            WHERE t.transaction_date >= now() - INTERVAL 7 DAY
                AND cs.stddev_amount > 0
                AND abs(t.amount - cs.avg_amount) / cs.stddev_amount > %(sensitivity)s
        )
        SELECT
            customer_id,
            transaction_id,
            amount,
            transaction_date,
            transaction_type,
            avg_amount,
            z_score
        FROM anomalies
        ORDER BY z_score DESC
        LIMIT 100
    """
    
    params = {
        'days': days,
        'sensitivity': sensitivity
    }
    
    try:
        result = clickhouse.execute(query, params)
        
        return {
            "anomalous_transactions": [
                {
                    "customer_id": row[0],
                    "transaction_id": row[1],
                    "amount": float(row[2]),
                    "transaction_date": row[3].isoformat(),
                    "transaction_type": row[4],
                    "customer_avg_amount": float(row[5]),
                    "z_score": float(row[6])
                }
                for row in result
            ],
            "analysis_params": {
                "days_analyzed": days,
                "sensitivity_threshold": sensitivity,
                "total_anomalies": len(result)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")


@router.get("/geographic/risk-analysis")
def get_geographic_risk_analysis(
    days: int = Query(30, description="Days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Analyze geographic risk patterns"""
    
    clickhouse = get_clickhouse_client()
    
    query = """
        SELECT
            counterparty_country,
            count() as transaction_count,
            sum(amount) as total_amount,
            avg(amount) as avg_amount,
            countIf(is_high_risk = 1) as high_risk_count,
            avg(risk_score) as avg_risk_score,
            uniqExact(customer_id) as unique_customers,
            countIf(is_high_risk = 1) / count() as risk_ratio
        FROM transactions_analytics
        WHERE transaction_date >= now() - INTERVAL %(days)s DAY
            AND counterparty_country != ''
        GROUP BY counterparty_country
        HAVING transaction_count >= 5
        ORDER BY avg_risk_score DESC, risk_ratio DESC
        LIMIT 50
    """
    
    try:
        result = clickhouse.execute(query, {'days': days})
        
        return {
            "geographic_analysis": [
                {
                    "country": row[0],
                    "transaction_count": row[1],
                    "total_amount": float(row[2]),
                    "avg_amount": float(row[3]),
                    "high_risk_count": row[4],
                    "avg_risk_score": float(row[5]),
                    "unique_customers": row[6],
                    "risk_ratio": float(row[7])
                }
                for row in result
            ],
            "summary": {
                "analysis_period_days": days,
                "countries_analyzed": len(result)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geographic analysis failed: {str(e)}")


@router.get("/performance/metrics")
def get_performance_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get ClickHouse performance metrics"""
    
    clickhouse = get_clickhouse_client()
    
    try:
        # Get table sizes
        table_sizes = clickhouse.execute("""
            SELECT
                table,
                formatReadableSize(sum(bytes_on_disk)) as size,
                sum(rows) as rows,
                count() as parts
            FROM system.parts
            WHERE database = 'napsa_analytics'
                AND active = 1
            GROUP BY table
            ORDER BY sum(bytes_on_disk) DESC
        """)
        
        # Get query performance
        recent_queries = clickhouse.execute("""
            SELECT
                query_duration_ms,
                memory_usage,
                read_rows,
                read_bytes,
                result_rows
            FROM system.query_log
            WHERE event_time >= now() - INTERVAL 1 HOUR
                AND type = 'QueryFinish'
                AND query NOT LIKE '%system.%'
            ORDER BY query_duration_ms DESC
            LIMIT 10
        """)
        
        return {
            "table_metrics": [
                {
                    "table": row[0],
                    "size": row[1],
                    "rows": row[2],
                    "parts": row[3]
                }
                for row in table_sizes
            ],
            "query_performance": [
                {
                    "duration_ms": row[0],
                    "memory_usage": row[1],
                    "read_rows": row[2],
                    "read_bytes": row[3],
                    "result_rows": row[4]
                }
                for row in recent_queries
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance metrics failed: {str(e)}")


@router.post("/pipeline/sync")
def trigger_data_sync(
    full_sync: bool = Query(False, description="Perform full data sync"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Manually trigger data pipeline sync"""
    
    pipeline = get_data_pipeline()
    
    try:
        if full_sync:
            pipeline.perform_initial_sync()
            return {"message": "Full data sync completed"}
        else:
            pipeline.sync_all_data()
            return {"message": "Incremental data sync completed"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data sync failed: {str(e)}")