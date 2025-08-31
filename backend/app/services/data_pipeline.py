"""
Data pipeline service for syncing data between PostgreSQL and ClickHouse
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import asyncio
from threading import Thread
import time

from app.core.database import SessionLocal
from app.core.clickhouse import get_clickhouse_client
from app.models.aml import (
    Transaction, CustomerProfile, TransactionAlert, 
    CustomerRiskProfile, ComplianceCase
)

logger = logging.getLogger(__name__)


class DataPipelineService:
    """Service for managing data pipeline between PostgreSQL and ClickHouse"""
    
    def __init__(self):
        self.clickhouse = get_clickhouse_client()
        self.batch_size = 1000
        self.sync_interval = 300  # 5 minutes
        self.running = False
        self.last_sync = {}
    
    def start_pipeline(self):
        """Start the data pipeline in background"""
        if self.running:
            logger.warning("Pipeline already running")
            return
        
        self.running = True
        thread = Thread(target=self._pipeline_worker, daemon=True)
        thread.start()
        logger.info("Data pipeline started")
    
    def stop_pipeline(self):
        """Stop the data pipeline"""
        self.running = False
        logger.info("Data pipeline stopped")
    
    def _pipeline_worker(self):
        """Background worker for data pipeline"""
        while self.running:
            try:
                self.sync_all_data()
                time.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Pipeline error: {e}")
                time.sleep(60)  # Wait a minute before retry
    
    def sync_all_data(self):
        """Sync all data types"""
        logger.info("Starting full data sync")
        
        with SessionLocal() as db:
            # Sync transactions
            self.sync_transactions(db)
            
            # Sync customer risk data
            self.sync_customer_risk(db)
            
            # Sync alerts
            self.sync_alerts(db)
            
            # Update metrics
            self.update_risk_metrics(db)
        
        logger.info("Data sync completed")
    
    def sync_transactions(self, db: Session):
        """Sync transaction data to ClickHouse"""
        logger.info("Syncing transactions")
        
        # Get last sync timestamp
        last_sync = self.last_sync.get('transactions', datetime.min)
        
        # Query new/updated transactions
        transactions = db.query(Transaction).filter(
            Transaction.updated_at > last_sync
        ).limit(self.batch_size).all()
        
        if not transactions:
            return
        
        # Transform data for ClickHouse
        ch_data = []
        for txn in transactions:
            ch_data.append({
                'transaction_id': txn.transaction_id,
                'customer_id': txn.customer_id or 0,
                'account_number': txn.account_number or '',
                'account_name': txn.account_name or '',
                'transaction_date': txn.transaction_date,
                'amount': float(txn.amount),
                'currency': txn.currency,
                'transaction_type': txn.transaction_type.value,
                'risk_score': txn.risk_score or 0.0,
                'is_high_risk': 1 if txn.is_high_risk else 0,
                'is_flagged': 1 if txn.status and 'flagged' in txn.status.value else 0,
                'country': txn.originating_country or '',
                'counterparty_country': txn.counterparty_country or '',
                'channel': txn.channel or '',
                'created_at': datetime.utcnow()
            })
        
        # Insert into ClickHouse (using INSERT with ON DUPLICATE KEY semantics)
        if ch_data:
            self._upsert_transactions(ch_data)
            self.last_sync['transactions'] = max(txn.updated_at for txn in transactions)
            logger.info(f"Synced {len(ch_data)} transactions")
    
    def sync_customer_risk(self, db: Session):
        """Sync customer risk data to ClickHouse"""
        logger.info("Syncing customer risk data")
        
        last_sync = self.last_sync.get('customer_risk', datetime.min)
        
        # Get updated customer profiles with risk data
        query = db.query(CustomerProfile, CustomerRiskProfile).join(
            CustomerRiskProfile, 
            CustomerProfile.id == CustomerRiskProfile.customer_id,
            isouter=True
        ).filter(
            CustomerProfile.updated_at > last_sync
        )
        
        results = query.limit(self.batch_size).all()
        
        if not results:
            return
        
        ch_data = []
        for customer, risk_profile in results:
            # Calculate transaction metrics for this customer
            txn_metrics = db.query(
                Transaction.customer_id,
                db.func.count(Transaction.id).label('txn_count'),
                db.func.sum(Transaction.amount).label('total_volume'),
                db.func.count(TransactionAlert.id).label('alert_count')
            ).outerjoin(
                TransactionAlert,
                Transaction.id == TransactionAlert.transaction_id
            ).filter(
                Transaction.customer_id == customer.id,
                Transaction.transaction_date >= datetime.utcnow() - timedelta(days=90)
            ).group_by(Transaction.customer_id).first()
            
            case_count = db.query(ComplianceCase).filter(
                ComplianceCase.customer_id == customer.id
            ).count()
            
            ch_data.append({
                'customer_id': customer.id,
                'snapshot_date': datetime.utcnow().date(),
                'risk_score': customer.risk_score or 0.0,
                'risk_level': customer.risk_level.value if customer.risk_level else 'low',
                'transaction_count': txn_metrics.txn_count if txn_metrics else 0,
                'total_volume': float(txn_metrics.total_volume) if txn_metrics and txn_metrics.total_volume else 0.0,
                'alert_count': txn_metrics.alert_count if txn_metrics else 0,
                'case_count': case_count,
                'kyc_status': customer.kyc_status or 'pending',
                'pep_status': 1 if customer.pep_status else 0,
                'high_risk_country': 1 if customer.high_risk_country else 0,
                'created_at': datetime.utcnow()
            })
        
        if ch_data:
            self.clickhouse.insert('customer_risk_analytics', ch_data)
            self.last_sync['customer_risk'] = max(
                customer.updated_at for customer, _ in results
            )
            logger.info(f"Synced {len(ch_data)} customer risk records")
    
    def sync_alerts(self, db: Session):
        """Sync alert data to ClickHouse"""
        logger.info("Syncing alerts")
        
        last_sync = self.last_sync.get('alerts', datetime.min)
        
        alerts = db.query(TransactionAlert).filter(
            TransactionAlert.updated_at > last_sync
        ).limit(self.batch_size).all()
        
        if not alerts:
            return
        
        ch_data = []
        for alert in alerts:
            resolution_time = None
            if alert.resolved_at and alert.created_at:
                resolution_time = (alert.resolved_at - alert.created_at).total_seconds() / 3600
            
            ch_data.append({
                'alert_id': alert.alert_id,
                'transaction_id': alert.transaction.transaction_id if alert.transaction else '',
                'customer_id': alert.customer_id or 0,
                'alert_type': alert.alert_type,
                'severity': alert.severity.value,
                'score': alert.score or 0.0,
                'rule_id': alert.rule_id or '',
                'created_date': alert.created_at,
                'resolved_date': alert.resolved_at,
                'resolution_time_hours': resolution_time,
                'status': alert.status.value,
                'false_positive': 1 if alert.resolution == 'false_positive' else 0
            })
        
        if ch_data:
            self._upsert_alerts(ch_data)
            self.last_sync['alerts'] = max(alert.updated_at for alert in alerts)
            logger.info(f"Synced {len(ch_data)} alerts")
    
    def update_risk_metrics(self, db: Session):
        """Update risk metrics time series in ClickHouse"""
        logger.info("Updating risk metrics")
        
        now = datetime.utcnow()
        
        # Calculate various risk metrics
        metrics = []
        
        # Transaction volume metrics
        total_volume = db.query(db.func.sum(Transaction.amount)).filter(
            Transaction.transaction_date >= now - timedelta(days=1)
        ).scalar() or 0
        
        metrics.append({
            'timestamp': now,
            'metric_type': 'transaction',
            'metric_name': 'daily_volume',
            'value': float(total_volume),
            'dimensions.key': ['currency'],
            'dimensions.value': ['ALL']
        })
        
        # High risk transaction count
        high_risk_count = db.query(Transaction).filter(
            Transaction.transaction_date >= now - timedelta(days=1),
            Transaction.is_high_risk == True
        ).count()
        
        metrics.append({
            'timestamp': now,
            'metric_type': 'risk',
            'metric_name': 'high_risk_transactions',
            'value': high_risk_count,
            'dimensions.key': ['period'],
            'dimensions.value': ['daily']
        })
        
        # Alert generation rate
        alert_count = db.query(TransactionAlert).filter(
            TransactionAlert.created_at >= now - timedelta(hours=1)
        ).count()
        
        metrics.append({
            'timestamp': now,
            'metric_type': 'alert',
            'metric_name': 'hourly_generation_rate',
            'value': alert_count,
            'dimensions.key': ['period'],
            'dimensions.value': ['hourly']
        })
        
        # Customer risk distribution
        for risk_level in ['low', 'medium', 'high', 'critical']:
            count = db.query(CustomerProfile).filter(
                CustomerProfile.risk_level == risk_level
            ).count()
            
            metrics.append({
                'timestamp': now,
                'metric_type': 'customer_risk',
                'metric_name': 'distribution',
                'value': count,
                'dimensions.key': ['risk_level'],
                'dimensions.value': [risk_level]
            })
        
        if metrics:
            self.clickhouse.insert('risk_metrics_timeseries', metrics)
            logger.info(f"Updated {len(metrics)} risk metrics")
    
    def _upsert_transactions(self, data: List[Dict]):
        """Upsert transactions with deduplication"""
        if not data:
            return
        
        # Delete existing records first (ClickHouse doesn't have native UPSERT)
        transaction_ids = [f"'{d['transaction_id']}'" for d in data]
        delete_query = f"ALTER TABLE transactions_analytics DELETE WHERE transaction_id IN ({','.join(transaction_ids)})"
        
        try:
            self.clickhouse.execute(delete_query)
        except Exception as e:
            logger.warning(f"Delete operation failed (may be expected): {e}")
        
        # Insert new data
        self.clickhouse.insert('transactions_analytics', data)
    
    def _upsert_alerts(self, data: List[Dict]):
        """Upsert alerts with deduplication"""
        if not data:
            return
        
        alert_ids = [f"'{d['alert_id']}'" for d in data]
        delete_query = f"ALTER TABLE alert_analytics DELETE WHERE alert_id IN ({','.join(alert_ids)})"
        
        try:
            self.clickhouse.execute(delete_query)
        except Exception as e:
            logger.warning(f"Delete operation failed (may be expected): {e}")
        
        self.clickhouse.insert('alert_analytics', data)
    
    def perform_initial_sync(self):
        """Perform initial data sync for historical data"""
        logger.info("Starting initial data sync")
        
        with SessionLocal() as db:
            # Reset sync timestamps for full sync
            self.last_sync = {}
            
            # Sync in batches to avoid memory issues
            batch_count = 0
            while True:
                # Sync transactions in batches
                transactions = db.query(Transaction).offset(
                    batch_count * self.batch_size
                ).limit(self.batch_size).all()
                
                if not transactions:
                    break
                
                ch_data = []
                for txn in transactions:
                    ch_data.append({
                        'transaction_id': txn.transaction_id,
                        'customer_id': txn.customer_id or 0,
                        'account_number': txn.account_number or '',
                        'account_name': txn.account_name or '',
                        'transaction_date': txn.transaction_date,
                        'amount': float(txn.amount),
                        'currency': txn.currency,
                        'transaction_type': txn.transaction_type.value,
                        'risk_score': txn.risk_score or 0.0,
                        'is_high_risk': 1 if txn.is_high_risk else 0,
                        'is_flagged': 1 if txn.status and 'flagged' in txn.status.value else 0,
                        'country': txn.originating_country or '',
                        'counterparty_country': txn.counterparty_country or '',
                        'channel': txn.channel or '',
                        'created_at': datetime.utcnow()
                    })
                
                if ch_data:
                    self.clickhouse.insert('transactions_analytics', ch_data)
                
                batch_count += 1
                logger.info(f"Synced batch {batch_count} ({len(ch_data)} transactions)")
        
        # Sync other data types
        with SessionLocal() as db:
            self.sync_customer_risk(db)
            self.sync_alerts(db)
        
        logger.info("Initial data sync completed")


# Global pipeline instance
data_pipeline = None


def get_data_pipeline() -> DataPipelineService:
    """Get or create data pipeline instance"""
    global data_pipeline
    if data_pipeline is None:
        data_pipeline = DataPipelineService()
    return data_pipeline