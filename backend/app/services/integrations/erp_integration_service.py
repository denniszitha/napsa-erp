"""
ERP Integration Service
Handles integration with various ERP systems (SAP, Oracle, Sage, etc.)
"""
import httpx
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.integrations import ERPIntegration, IntegrationAuditLog
from app.core.config import settings

logger = logging.getLogger(__name__)

class ERPIntegrationService:
    """Service for ERP system integration and data synchronization"""
    
    def __init__(self):
        self.timeout = 60
        
        # Supported ERP systems configuration
        self.erp_systems = {
            'SAP': {
                'name': 'SAP ERP',
                'default_modules': ['FI', 'CO', 'HR', 'MM', 'SD'],
                'auth_methods': ['oauth2', 'basic_auth', 'api_key']
            },
            'ORACLE': {
                'name': 'Oracle ERP Cloud',
                'default_modules': ['Financials', 'HCM', 'Procurement', 'Supply Chain'],
                'auth_methods': ['oauth2', 'basic_auth']
            },
            'SAGE': {
                'name': 'Sage ERP',
                'default_modules': ['Accounting', 'Payroll', 'CRM', 'Inventory'],
                'auth_methods': ['api_key', 'basic_auth']
            },
            'DYNAMICS': {
                'name': 'Microsoft Dynamics 365',
                'default_modules': ['Finance', 'Operations', 'Sales', 'Customer Service'],
                'auth_methods': ['oauth2', 'api_key']
            },
            'NETSUITE': {
                'name': 'NetSuite ERP',
                'default_modules': ['Financials', 'CRM', 'E-commerce', 'Inventory'],
                'auth_methods': ['oauth2', 'token_based']
            }
        }
    
    async def register_erp_system(self, erp_config: Dict, db: Session) -> Dict[str, Any]:
        """Register a new ERP system for integration"""
        try:
            erp_record = ERPIntegration(
                erp_system_name=erp_config['system_name'],
                integration_type=erp_config.get('integration_type', 'api'),
                endpoint_url=erp_config.get('endpoint_url'),
                database_connection_string=erp_config.get('db_connection'),
                authentication_method=erp_config.get('auth_method', 'api_key'),
                sync_frequency=erp_config.get('sync_frequency', 'daily'),
                sync_direction=erp_config.get('sync_direction', 'inbound'),
                data_mapping_config=erp_config.get('data_mapping', {}),
                financial_data_sync=erp_config.get('sync_financial', False),
                hr_data_sync=erp_config.get('sync_hr', False),
                procurement_sync=erp_config.get('sync_procurement', False),
                inventory_sync=erp_config.get('sync_inventory', False),
                customer_data_sync=erp_config.get('sync_customer', False),
                sync_status='active',
                next_sync_timestamp=self._calculate_next_sync(erp_config.get('sync_frequency', 'daily'))
            )
            
            db.add(erp_record)
            db.commit()
            
            self._log_integration_activity(
                db, 'erp', 'system_registration', 'success',
                request_data=erp_config,
                response_data={'erp_id': erp_record.id}
            )
            
            return {
                'status': 'success',
                'erp_id': erp_record.id,
                'system_name': erp_config['system_name'],
                'message': 'ERP system registered successfully'
            }
            
        except Exception as e:
            logger.error(f"ERP system registration failed: {str(e)}")
            self._log_integration_activity(
                db, 'erp', 'system_registration', 'failed',
                request_data=erp_config,
                error_message=str(e)
            )
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def sync_financial_data(self, erp_id: int, db: Session) -> Dict[str, Any]:
        """Synchronize financial data from ERP system"""
        try:
            erp_record = db.query(ERPIntegration).filter(ERPIntegration.id == erp_id).first()
            if not erp_record:
                return {'status': 'failed', 'error': 'ERP system not found'}
            
            # Mock financial data sync - replace with actual ERP API calls
            mock_financial_data = self._mock_financial_data_sync(erp_record.erp_system_name)
            
            # Update sync statistics
            erp_record.last_sync_timestamp = datetime.utcnow()
            erp_record.next_sync_timestamp = self._calculate_next_sync(erp_record.sync_frequency)
            erp_record.total_records_synced += mock_financial_data['records_synced']
            erp_record.sync_success_rate = self._calculate_success_rate(erp_record, True)
            
            db.commit()
            
            self._log_integration_activity(
                db, 'erp', 'financial_data_sync', 'success',
                request_data={'erp_id': erp_id, 'erp_system': erp_record.erp_system_name},
                response_data=mock_financial_data
            )
            
            return {
                'status': 'success',
                'erp_system': erp_record.erp_system_name,
                'sync_summary': mock_financial_data,
                'next_sync': erp_record.next_sync_timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Financial data sync failed for ERP {erp_id}: {str(e)}")
            
            # Update error count
            if 'erp_record' in locals():
                erp_record.error_count_24h += 1
                erp_record.last_error_message = str(e)
                db.commit()
            
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def sync_hr_data(self, erp_id: int, db: Session) -> Dict[str, Any]:
        """Synchronize HR data from ERP system"""
        try:
            erp_record = db.query(ERPIntegration).filter(ERPIntegration.id == erp_id).first()
            if not erp_record:
                return {'status': 'failed', 'error': 'ERP system not found'}
            
            # Mock HR data sync
            mock_hr_data = self._mock_hr_data_sync(erp_record.erp_system_name)
            
            # Update sync statistics
            erp_record.last_sync_timestamp = datetime.utcnow()
            erp_record.total_records_synced += mock_hr_data['records_synced']
            
            db.commit()
            
            self._log_integration_activity(
                db, 'erp', 'hr_data_sync', 'success',
                request_data={'erp_id': erp_id},
                response_data=mock_hr_data
            )
            
            return {
                'status': 'success',
                'erp_system': erp_record.erp_system_name,
                'sync_summary': mock_hr_data
            }
            
        except Exception as e:
            logger.error(f"HR data sync failed for ERP {erp_id}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def sync_procurement_data(self, erp_id: int, db: Session) -> Dict[str, Any]:
        """Synchronize procurement data from ERP system"""
        try:
            erp_record = db.query(ERPIntegration).filter(ERPIntegration.id == erp_id).first()
            if not erp_record:
                return {'status': 'failed', 'error': 'ERP system not found'}
            
            # Mock procurement data sync
            mock_procurement_data = self._mock_procurement_data_sync(erp_record.erp_system_name)
            
            # Update sync statistics
            erp_record.last_sync_timestamp = datetime.utcnow()
            erp_record.total_records_synced += mock_procurement_data['records_synced']
            
            db.commit()
            
            self._log_integration_activity(
                db, 'erp', 'procurement_data_sync', 'success',
                request_data={'erp_id': erp_id},
                response_data=mock_procurement_data
            )
            
            return {
                'status': 'success',
                'erp_system': erp_record.erp_system_name,
                'sync_summary': mock_procurement_data
            }
            
        except Exception as e:
            logger.error(f"Procurement data sync failed for ERP {erp_id}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def get_erp_status(self, erp_id: int, db: Session) -> Dict[str, Any]:
        """Get comprehensive status of ERP integration"""
        try:
            erp_record = db.query(ERPIntegration).filter(ERPIntegration.id == erp_id).first()
            if not erp_record:
                return {'status': 'not_found', 'error': 'ERP system not found'}
            
            return {
                'erp_id': erp_record.id,
                'system_name': erp_record.erp_system_name,
                'integration_type': erp_record.integration_type,
                'sync_status': erp_record.sync_status,
                'last_sync': erp_record.last_sync_timestamp.isoformat() if erp_record.last_sync_timestamp else None,
                'next_sync': erp_record.next_sync_timestamp.isoformat() if erp_record.next_sync_timestamp else None,
                'sync_frequency': erp_record.sync_frequency,
                'total_records_synced': erp_record.total_records_synced,
                'sync_success_rate': float(erp_record.sync_success_rate or 0),
                'error_count_24h': erp_record.error_count_24h,
                'last_error': erp_record.last_error_message,
                'enabled_modules': {
                    'financial_data': erp_record.financial_data_sync,
                    'hr_data': erp_record.hr_data_sync,
                    'procurement': erp_record.procurement_sync,
                    'inventory': erp_record.inventory_sync,
                    'customer_data': erp_record.customer_data_sync
                }
            }
            
        except Exception as e:
            logger.error(f"ERP status check failed for ERP {erp_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def test_erp_connection(self, erp_id: int, db: Session) -> Dict[str, Any]:
        """Test connectivity to ERP system"""
        try:
            erp_record = db.query(ERPIntegration).filter(ERPIntegration.id == erp_id).first()
            if not erp_record:
                return {'status': 'failed', 'error': 'ERP system not found'}
            
            # Mock connection test - replace with actual connectivity test
            connection_test_result = {
                'connection_status': 'success',
                'response_time_ms': 150,
                'authentication_valid': True,
                'endpoint_accessible': True,
                'test_timestamp': datetime.utcnow().isoformat()
            }
            
            self._log_integration_activity(
                db, 'erp', 'connection_test', 'success',
                request_data={'erp_id': erp_id},
                response_data=connection_test_result
            )
            
            return {
                'status': 'success',
                'erp_system': erp_record.erp_system_name,
                'connection_test': connection_test_result
            }
            
        except Exception as e:
            logger.error(f"ERP connection test failed for ERP {erp_id}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def get_all_erp_systems(self, db: Session) -> List[Dict[str, Any]]:
        """Get all registered ERP systems"""
        try:
            erp_records = db.query(ERPIntegration).all()
            
            systems = []
            for record in erp_records:
                systems.append({
                    'erp_id': record.id,
                    'system_name': record.erp_system_name,
                    'integration_type': record.integration_type,
                    'sync_status': record.sync_status,
                    'last_sync': record.last_sync_timestamp.isoformat() if record.last_sync_timestamp else None,
                    'sync_frequency': record.sync_frequency,
                    'success_rate': float(record.sync_success_rate or 0),
                    'total_records_synced': record.total_records_synced
                })
            
            return systems
            
        except Exception as e:
            logger.error(f"Failed to get ERP systems: {str(e)}")
            return []
    
    def _mock_financial_data_sync(self, erp_system: str) -> Dict[str, Any]:
        """Mock financial data synchronization"""
        return {
            'records_synced': 250,
            'sync_duration_seconds': 45,
            'modules_synced': ['General Ledger', 'Accounts Payable', 'Accounts Receivable'],
            'data_types': ['Invoices', 'Payments', 'Journal Entries', 'Budget Data'],
            'success_count': 248,
            'error_count': 2,
            'warnings_count': 5,
            'total_amount_synced': 1250000.00,
            'currency': 'ZMW',
            'period_from': '2024-07-01',
            'period_to': '2024-07-31'
        }
    
    def _mock_hr_data_sync(self, erp_system: str) -> Dict[str, Any]:
        """Mock HR data synchronization"""
        return {
            'records_synced': 180,
            'sync_duration_seconds': 30,
            'modules_synced': ['Employee Master', 'Payroll', 'Time & Attendance'],
            'data_types': ['Employee Records', 'Salary Data', 'Benefits', 'Leave Records'],
            'success_count': 178,
            'error_count': 2,
            'warnings_count': 3,
            'employees_synced': 145,
            'payroll_period': '2024-07'
        }
    
    def _mock_procurement_data_sync(self, erp_system: str) -> Dict[str, Any]:
        """Mock procurement data synchronization"""
        return {
            'records_synced': 95,
            'sync_duration_seconds': 25,
            'modules_synced': ['Purchase Orders', 'Vendor Master', 'Receipts'],
            'data_types': ['Purchase Orders', 'Vendor Information', 'Purchase Receipts', 'Invoice Matching'],
            'success_count': 94,
            'error_count': 1,
            'warnings_count': 2,
            'total_po_value': 850000.00,
            'vendors_synced': 45,
            'currency': 'ZMW'
        }
    
    def _calculate_next_sync(self, frequency: str) -> datetime:
        """Calculate next sync timestamp based on frequency"""
        now = datetime.utcnow()
        if frequency == 'hourly':
            return now + timedelta(hours=1)
        elif frequency == 'daily':
            return now + timedelta(days=1)
        elif frequency == 'weekly':
            return now + timedelta(weeks=1)
        else:
            return now + timedelta(days=1)  # Default to daily
    
    def _calculate_success_rate(self, erp_record, last_sync_successful: bool) -> Decimal:
        """Calculate sync success rate"""
        # Simple calculation - in production, maintain more detailed metrics
        current_rate = erp_record.sync_success_rate or Decimal('100.0')
        if last_sync_successful:
            return min(current_rate + Decimal('1.0'), Decimal('100.0'))
        else:
            return max(current_rate - Decimal('5.0'), Decimal('0.0'))
    
    def _log_integration_activity(
        self, db: Session, integration_type: str, activity_type: str,
        status: str, request_data: Dict = None, response_data: Dict = None,
        error_message: str = None
    ):
        """Log integration activity to audit table"""
        try:
            audit_log = IntegrationAuditLog(
                integration_type=integration_type,
                activity_type=activity_type,
                status=status,
                request_data=request_data,
                response_data=response_data,
                error_message=error_message,
                system_component='erp_integration_service',
                timestamp=datetime.utcnow()
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log integration activity: {str(e)}")

# Global service instance
erp_integration_service = ERPIntegrationService()