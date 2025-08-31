"""
ClickHouse connection and configuration for analytics
"""
from typing import Dict, Any, List, Optional
from clickhouse_driver import Client
from contextlib import contextmanager
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """ClickHouse client for analytics operations"""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None
    ):
        self.host = host or os.getenv("CLICKHOUSE_HOST", "localhost")
        self.port = port or int(os.getenv("CLICKHOUSE_PORT", "9000"))
        self.database = database or os.getenv("CLICKHOUSE_DATABASE", "napsa_analytics")
        self.user = user or os.getenv("CLICKHOUSE_USER", "default")
        self.password = password or os.getenv("CLICKHOUSE_PASSWORD", "")
        
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to ClickHouse"""
        try:
            self.client = Client(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                settings={
                    'use_numpy': True,
                    'max_block_size': 100000
                }
            )
            logger.info(f"Connected to ClickHouse at {self.host}:{self.port}/{self.database}")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            raise
    
    @contextmanager
    def get_client(self):
        """Context manager for ClickHouse client"""
        try:
            yield self.client
        except Exception as e:
            logger.error(f"ClickHouse operation failed: {e}")
            raise
    
    def execute(self, query: str, params: Dict = None) -> Any:
        """Execute a ClickHouse query"""
        try:
            return self.client.execute(query, params or {})
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def insert(self, table: str, data: List[Dict], column_names: List[str] = None) -> int:
        """Insert data into ClickHouse table"""
        if not data:
            return 0
        
        if column_names is None:
            column_names = list(data[0].keys())
        
        values = [[row.get(col) for col in column_names] for row in data]
        
        query = f"INSERT INTO {table} ({','.join(column_names)}) VALUES"
        
        try:
            self.client.execute(query, values)
            return len(values)
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise
    
    def create_database(self):
        """Create the analytics database if it doesn't exist"""
        try:
            self.client.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            logger.info(f"Database {self.database} created or already exists")
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            raise
    
    def init_schema(self):
        """Initialize ClickHouse schema for AML/ERM analytics"""
        
        # Create database
        self.create_database()
        
        # Transaction analytics table
        self.execute("""
            CREATE TABLE IF NOT EXISTS transactions_analytics (
                transaction_id String,
                customer_id UInt32,
                account_number String,
                account_name String,
                transaction_date DateTime,
                amount Decimal(18, 2),
                currency FixedString(3),
                transaction_type String,
                risk_score Float32,
                is_high_risk UInt8,
                is_flagged UInt8,
                country String,
                counterparty_country String,
                channel String,
                created_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(transaction_date)
            ORDER BY (transaction_date, customer_id, transaction_id)
            SETTINGS index_granularity = 8192
        """)
        
        # Customer risk analytics table
        self.execute("""
            CREATE TABLE IF NOT EXISTS customer_risk_analytics (
                customer_id UInt32,
                snapshot_date Date,
                risk_score Float32,
                risk_level String,
                transaction_count UInt32,
                total_volume Decimal(18, 2),
                alert_count UInt32,
                case_count UInt32,
                kyc_status String,
                pep_status UInt8,
                high_risk_country UInt8,
                created_at DateTime DEFAULT now()
            ) ENGINE = ReplacingMergeTree(created_at)
            PARTITION BY toYYYYMM(snapshot_date)
            ORDER BY (snapshot_date, customer_id)
            SETTINGS index_granularity = 8192
        """)
        
        # Alert analytics table
        self.execute("""
            CREATE TABLE IF NOT EXISTS alert_analytics (
                alert_id String,
                transaction_id String,
                customer_id UInt32,
                alert_type String,
                severity String,
                score Float32,
                rule_id String,
                created_date DateTime,
                resolved_date Nullable(DateTime),
                resolution_time_hours Nullable(Float32),
                status String,
                false_positive UInt8
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(created_date)
            ORDER BY (created_date, customer_id, alert_id)
            SETTINGS index_granularity = 8192
        """)
        
        # Risk metrics time series
        self.execute("""
            CREATE TABLE IF NOT EXISTS risk_metrics_timeseries (
                timestamp DateTime,
                metric_type String,
                metric_name String,
                value Float64,
                dimensions Nested(
                    key String,
                    value String
                )
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(timestamp)
            ORDER BY (timestamp, metric_type, metric_name)
            TTL timestamp + INTERVAL 90 DAY
            SETTINGS index_granularity = 8192
        """)
        
        # Create materialized views for common queries
        self._create_materialized_views()
        
        logger.info("ClickHouse schema initialized successfully")
    
    def _create_materialized_views(self):
        """Create materialized views for performance optimization"""
        
        # Daily transaction summary
        self.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS daily_transaction_summary
            ENGINE = SummingMergeTree()
            PARTITION BY toYYYYMM(date)
            ORDER BY (date, transaction_type, currency)
            AS SELECT
                toDate(transaction_date) as date,
                transaction_type,
                currency,
                count() as transaction_count,
                sum(amount) as total_amount,
                avg(amount) as avg_amount,
                max(amount) as max_amount,
                countIf(is_high_risk = 1) as high_risk_count,
                avgIf(risk_score, risk_score > 0) as avg_risk_score
            FROM transactions_analytics
            GROUP BY date, transaction_type, currency
        """)
        
        # Customer transaction patterns
        self.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS customer_transaction_patterns
            ENGINE = AggregatingMergeTree()
            PARTITION BY toYYYYMM(month)
            ORDER BY (month, customer_id)
            AS SELECT
                toStartOfMonth(transaction_date) as month,
                customer_id,
                count() as transaction_count,
                sum(amount) as total_volume,
                avg(amount) as avg_transaction,
                stddevPop(amount) as stddev_amount,
                max(amount) as max_transaction,
                countIf(is_high_risk = 1) as high_risk_transactions,
                uniqExact(toDate(transaction_date)) as active_days,
                uniqExact(counterparty_country) as unique_countries,
                avgIf(risk_score, risk_score > 0) as avg_risk_score
            FROM transactions_analytics
            GROUP BY month, customer_id
        """)
        
        # Alert resolution metrics
        self.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS alert_resolution_metrics
            ENGINE = SummingMergeTree()
            PARTITION BY toYYYYMM(date)
            ORDER BY (date, alert_type, severity)
            AS SELECT
                toDate(created_date) as date,
                alert_type,
                severity,
                count() as alert_count,
                countIf(status = 'resolved') as resolved_count,
                countIf(false_positive = 1) as false_positive_count,
                avg(resolution_time_hours) as avg_resolution_hours,
                median(resolution_time_hours) as median_resolution_hours
            FROM alert_analytics
            GROUP BY date, alert_type, severity
        """)
        
        # Risk score distribution
        self.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS risk_score_distribution
            ENGINE = SummingMergeTree()
            ORDER BY (date, risk_band)
            AS SELECT
                toDate(snapshot_date) as date,
                multiIf(
                    risk_score < 25, 'Low',
                    risk_score < 50, 'Medium',
                    risk_score < 75, 'High',
                    'Critical'
                ) as risk_band,
                count() as customer_count,
                avg(risk_score) as avg_score,
                sum(transaction_count) as total_transactions,
                sum(total_volume) as total_volume
            FROM customer_risk_analytics
            GROUP BY date, risk_band
        """)
    
    def get_transaction_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        customer_id: Optional[int] = None
    ) -> List[Dict]:
        """Get transaction analytics for a period"""
        
        query = """
            SELECT
                toDate(transaction_date) as date,
                count() as transaction_count,
                sum(amount) as total_volume,
                avg(amount) as avg_amount,
                max(amount) as max_amount,
                countIf(is_high_risk = 1) as high_risk_count,
                avg(risk_score) as avg_risk_score,
                uniqExact(customer_id) as unique_customers
            FROM transactions_analytics
            WHERE transaction_date >= %(start_date)s
                AND transaction_date <= %(end_date)s
                {customer_filter}
            GROUP BY date
            ORDER BY date DESC
        """
        
        customer_filter = ""
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        if customer_id:
            customer_filter = "AND customer_id = %(customer_id)s"
            params['customer_id'] = customer_id
        
        query = query.format(customer_filter=customer_filter)
        
        result = self.execute(query, params)
        
        return [
            {
                'date': row[0],
                'transaction_count': row[1],
                'total_volume': float(row[2]),
                'avg_amount': float(row[3]),
                'max_amount': float(row[4]),
                'high_risk_count': row[5],
                'avg_risk_score': float(row[6]) if row[6] else 0,
                'unique_customers': row[7]
            }
            for row in result
        ]
    
    def get_pattern_analysis(self, customer_id: int) -> Dict[str, Any]:
        """Analyze transaction patterns for a customer using ClickHouse"""
        
        # Get transaction velocity
        velocity_query = """
            SELECT
                toDate(transaction_date) as date,
                count() as daily_count,
                sum(amount) as daily_volume
            FROM transactions_analytics
            WHERE customer_id = %(customer_id)s
                AND transaction_date >= now() - INTERVAL 30 DAY
            GROUP BY date
            ORDER BY date DESC
        """
        
        velocity_result = self.execute(velocity_query, {'customer_id': customer_id})
        
        # Get transaction patterns
        pattern_query = """
            SELECT
                transaction_type,
                count() as count,
                avg(amount) as avg_amount,
                stddevPop(amount) as stddev_amount,
                max(amount) as max_amount,
                min(amount) as min_amount
            FROM transactions_analytics
            WHERE customer_id = %(customer_id)s
                AND transaction_date >= now() - INTERVAL 90 DAY
            GROUP BY transaction_type
        """
        
        pattern_result = self.execute(pattern_query, {'customer_id': customer_id})
        
        # Get geographic distribution
        geo_query = """
            SELECT
                counterparty_country,
                count() as transaction_count,
                sum(amount) as total_amount
            FROM transactions_analytics
            WHERE customer_id = %(customer_id)s
                AND transaction_date >= now() - INTERVAL 90 DAY
                AND counterparty_country != ''
            GROUP BY counterparty_country
            ORDER BY transaction_count DESC
            LIMIT 10
        """
        
        geo_result = self.execute(geo_query, {'customer_id': customer_id})
        
        # Get time-based patterns
        time_query = """
            SELECT
                toHour(transaction_date) as hour,
                count() as transaction_count,
                avg(amount) as avg_amount
            FROM transactions_analytics
            WHERE customer_id = %(customer_id)s
                AND transaction_date >= now() - INTERVAL 30 DAY
            GROUP BY hour
            ORDER BY hour
        """
        
        time_result = self.execute(time_query, {'customer_id': customer_id})
        
        return {
            'velocity': [
                {
                    'date': row[0],
                    'count': row[1],
                    'volume': float(row[2])
                }
                for row in velocity_result
            ],
            'patterns_by_type': [
                {
                    'type': row[0],
                    'count': row[1],
                    'avg_amount': float(row[2]),
                    'stddev': float(row[3]),
                    'max': float(row[4]),
                    'min': float(row[5])
                }
                for row in pattern_result
            ],
            'geographic_distribution': [
                {
                    'country': row[0],
                    'count': row[1],
                    'amount': float(row[2])
                }
                for row in geo_result
            ],
            'hourly_patterns': [
                {
                    'hour': row[0],
                    'count': row[1],
                    'avg_amount': float(row[2])
                }
                for row in time_result
            ]
        }


# Global ClickHouse client instance
clickhouse_client = None


def get_clickhouse_client() -> ClickHouseClient:
    """Get or create ClickHouse client instance"""
    global clickhouse_client
    if clickhouse_client is None:
        clickhouse_client = ClickHouseClient()
    return clickhouse_client


def init_clickhouse():
    """Initialize ClickHouse connection and schema"""
    client = get_clickhouse_client()
    client.init_schema()
    return client