"""
ZPPA (Zambia Public Procurement Authority) Integration Service
Handles supplier registration, procurement compliance, and performance tracking
"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.integrations import ZPPAIntegration, IntegrationAuditLog
from app.core.config import settings

logger = logging.getLogger(__name__)

class ZPPAIntegrationService:
    """Service for ZPPA API integration and procurement compliance management"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'ZPPA_API_BASE_URL', 'https://api.zppa.org.zm/v1')
        self.api_key = getattr(settings, 'ZPPA_API_KEY', 'demo-key-zppa-2024')
        self.timeout = 30
        
    async def verify_supplier_registration(self, registration_number: str, db: Session) -> Dict[str, Any]:
        """Verify supplier registration with ZPPA"""
        try:
            # Mock ZPPA API call - replace with actual ZPPA API
            mock_response = self._mock_supplier_verification(registration_number)
            
            self._log_integration_activity(
                db, 'zppa', 'supplier_verification', 'success',
                request_data={'registration_number': registration_number},
                response_data=mock_response
            )
            
            return {
                'valid': mock_response['valid'],
                'company_name': mock_response.get('company_name'),
                'registration_status': mock_response.get('status'),
                'supplier_category': mock_response.get('supplier_category')
            }
            
        except Exception as e:
            logger.error(f"ZPPA supplier verification failed for {registration_number}: {str(e)}")
            self._log_integration_activity(
                db, 'zppa', 'supplier_verification', 'failed',
                request_data={'registration_number': registration_number},
                error_message=str(e)
            )
            return {
                'valid': False,
                'error': str(e)
            }
    
    async def get_supplier_profile(self, registration_number: str, db: Session) -> Dict[str, Any]:
        """Get comprehensive supplier profile from ZPPA"""
        try:
            mock_response = self._mock_supplier_profile(registration_number)
            
            # Update or create ZPPA integration record
            zppa_record = db.query(ZPPAIntegration).filter(
                ZPPAIntegration.supplier_registration_number == registration_number
            ).first()
            
            if not zppa_record:
                zppa_record = ZPPAIntegration(
                    supplier_registration_number=registration_number,
                    company_name=mock_response['company_name'],
                    registration_status=mock_response['registration_status'],
                    supplier_category=mock_response['supplier_category'],
                    business_sector=mock_response['business_sector'],
                    company_size=mock_response['company_size'],
                    local_content_score=Decimal(str(mock_response['local_content_score'])),
                    total_contracts_awarded=mock_response['total_contracts_awarded'],
                    total_contract_value=Decimal(str(mock_response['total_contract_value'])),
                    active_contracts_count=mock_response['active_contracts_count'],
                    completed_contracts_count=mock_response['completed_contracts_count'],
                    tax_clearance_valid=mock_response['tax_clearance_valid'],
                    napsa_certificate_valid=mock_response['napsa_certificate_valid'],
                    pacra_registration_valid=mock_response['pacra_registration_valid'],
                    compliance_certificate_status=mock_response['compliance_certificate_status'],
                    performance_rating=Decimal(str(mock_response['performance_rating'])),
                    delivery_performance_score=Decimal(str(mock_response['delivery_performance_score'])),
                    quality_performance_score=Decimal(str(mock_response['quality_performance_score'])),
                    contract_dispute_count=mock_response['contract_dispute_count'],
                    last_sync_date=datetime.utcnow(),
                    sync_status='success',
                    api_response=mock_response
                )
                db.add(zppa_record)
            else:
                # Update existing record
                zppa_record.company_name = mock_response['company_name']
                zppa_record.registration_status = mock_response['registration_status']
                zppa_record.compliance_certificate_status = mock_response['compliance_certificate_status']
                zppa_record.performance_rating = Decimal(str(mock_response['performance_rating']))
                zppa_record.total_contracts_awarded = mock_response['total_contracts_awarded']
                zppa_record.total_contract_value = Decimal(str(mock_response['total_contract_value']))
                zppa_record.last_sync_date = datetime.utcnow()
                zppa_record.sync_status = 'success'
                zppa_record.api_response = mock_response
                zppa_record.updated_at = datetime.utcnow()
            
            db.commit()
            
            self._log_integration_activity(
                db, 'zppa', 'supplier_profile_check', 'success',
                request_data={'registration_number': registration_number},
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"ZPPA supplier profile check failed for {registration_number}: {str(e)}")
            self._log_integration_activity(
                db, 'zppa', 'supplier_profile_check', 'failed',
                request_data={'registration_number': registration_number},
                error_message=str(e)
            )
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    async def get_procurement_opportunities(self, supplier_category: str, db: Session) -> List[Dict[str, Any]]:
        """Get available procurement opportunities for supplier category"""
        try:
            # Mock procurement opportunities
            mock_opportunities = [
                {
                    'tender_id': 'ZPPA-T-2024-001',
                    'title': 'Supply of Office Furniture and Equipment',
                    'category': 'goods',
                    'sector': 'government',
                    'estimated_value': 500000.00,
                    'currency': 'ZMW',
                    'publication_date': '2024-08-01',
                    'closing_date': '2024-08-30',
                    'status': 'open',
                    'procuring_entity': 'Ministry of Health',
                    'requirements': [
                        'Tax Clearance Certificate',
                        'NAPSA Certificate',
                        'PACRA Certificate of Good Standing',
                        'ZPPA Registration Certificate'
                    ]
                },
                {
                    'tender_id': 'ZPPA-T-2024-002',
                    'title': 'Construction of Rural Health Posts',
                    'category': 'works',
                    'sector': 'health',
                    'estimated_value': 2500000.00,
                    'currency': 'ZMW',
                    'publication_date': '2024-08-05',
                    'closing_date': '2024-09-15',
                    'status': 'open',
                    'procuring_entity': 'Ministry of Infrastructure',
                    'requirements': [
                        'Tax Clearance Certificate',
                        'NAPSA Certificate',
                        'PACRA Certificate of Good Standing',
                        'ZPPA Registration Certificate',
                        'NCC Registration Grade 1'
                    ]
                }
            ]
            
            # Filter by supplier category if specified
            if supplier_category and supplier_category != 'all':
                mock_opportunities = [
                    opp for opp in mock_opportunities 
                    if opp['category'].lower() == supplier_category.lower()
                ]
            
            self._log_integration_activity(
                db, 'zppa', 'procurement_opportunities_check', 'success',
                request_data={'supplier_category': supplier_category},
                response_data={'opportunities_count': len(mock_opportunities)}
            )
            
            return mock_opportunities
            
        except Exception as e:
            logger.error(f"ZPPA procurement opportunities check failed: {str(e)}")
            return []
    
    async def get_contract_performance(self, registration_number: str, db: Session) -> Dict[str, Any]:
        """Get supplier contract performance history"""
        try:
            mock_performance = {
                'supplier_registration_number': registration_number,
                'overall_performance_rating': 4.2,
                'total_contracts': 15,
                'completed_contracts': 12,
                'active_contracts': 3,
                'cancelled_contracts': 0,
                'contract_performance': {
                    'delivery_performance': 92.5,
                    'quality_performance': 88.0,
                    'time_performance': 95.0,
                    'cost_performance': 87.5
                },
                'financial_performance': {
                    'total_contract_value': 1250000.00,
                    'completed_value': 950000.00,
                    'pending_payments': 25000.00,
                    'disputed_amounts': 0.00
                },
                'compliance_history': [
                    {
                        'contract_id': 'ZPPA-C-2024-001',
                        'completion_date': '2024-07-15',
                        'performance_score': 4.5,
                        'delivery_status': 'on_time',
                        'quality_rating': 'excellent'
                    },
                    {
                        'contract_id': 'ZPPA-C-2024-002',
                        'completion_date': '2024-06-30',
                        'performance_score': 3.8,
                        'delivery_status': 'delayed',
                        'quality_rating': 'good'
                    }
                ],
                'recommendations': [
                    'Maintain excellent delivery performance',
                    'Improve quality control processes',
                    'Consider expanding to additional categories'
                ]
            }
            
            self._log_integration_activity(
                db, 'zppa', 'contract_performance_check', 'success',
                request_data={'registration_number': registration_number},
                response_data={'contracts_reviewed': mock_performance['total_contracts']}
            )
            
            return mock_performance
            
        except Exception as e:
            logger.error(f"ZPPA contract performance check failed for {registration_number}: {str(e)}")
            return {}
    
    async def submit_procurement_application(self, registration_number: str, tender_id: str, application_data: Dict, db: Session) -> Dict[str, Any]:
        """Submit procurement application to ZPPA"""
        try:
            # Mock application submission
            mock_response = {
                'application_id': f'ZPPA-APP-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
                'tender_id': tender_id,
                'supplier_registration_number': registration_number,
                'status': 'submitted',
                'submission_date': datetime.utcnow().isoformat(),
                'reference_number': f'APP-{tender_id}-{registration_number}',
                'documents_received': len(application_data.get('documents', [])),
                'compliance_check_status': 'pending',
                'estimated_evaluation_completion': (datetime.utcnow() + timedelta(days=14)).isoformat(),
                'next_steps': [
                    'Document verification in progress',
                    'Technical evaluation scheduled',
                    'Results notification within 14 days'
                ]
            }
            
            self._log_integration_activity(
                db, 'zppa', 'procurement_application_submission', 'success',
                request_data={'registration_number': registration_number, 'tender_id': tender_id},
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"ZPPA procurement application submission failed: {str(e)}")
            self._log_integration_activity(
                db, 'zppa', 'procurement_application_submission', 'failed',
                request_data={'registration_number': registration_number, 'tender_id': tender_id},
                error_message=str(e)
            )
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _mock_supplier_verification(self, registration_number: str) -> Dict[str, Any]:
        """Mock supplier verification response"""
        if registration_number.startswith('ZPPA'):
            return {
                'valid': True,
                'company_name': 'ZAMBIA CONSTRUCTION COMPANY LIMITED',
                'status': 'active',
                'supplier_category': 'works',
                'registration_date': '2020-01-15'
            }
        else:
            return {
                'valid': len(registration_number) >= 6,
                'company_name': f'SUPPLIER {registration_number} LIMITED',
                'status': 'active' if len(registration_number) >= 6 else 'invalid',
                'supplier_category': 'goods',
                'registration_date': '2022-01-01'
            }
    
    def _mock_supplier_profile(self, registration_number: str) -> Dict[str, Any]:
        """Mock comprehensive supplier profile"""
        return {
            'registration_number': registration_number,
            'company_name': f'SUPPLIER {registration_number} LIMITED',
            'registration_status': 'active',
            'supplier_category': 'goods',
            'business_sector': 'manufacturing',
            'company_size': 'medium',
            'local_content_score': 85.0,
            'total_contracts_awarded': 12,
            'total_contract_value': 850000.00,
            'active_contracts_count': 2,
            'completed_contracts_count': 10,
            'tax_clearance_valid': True,
            'napsa_certificate_valid': True,
            'pacra_registration_valid': True,
            'compliance_certificate_status': 'valid',
            'performance_rating': 4.2,
            'delivery_performance_score': 92.5,
            'quality_performance_score': 88.0,
            'contract_dispute_count': 0,
            'annual_turnover': 1200000.00,
            'bank_guarantee_capacity': 500000.00,
            'credit_rating': 'B+',
            'initial_registration_date': '2020-01-15',
            'registration_expiry_date': '2024-12-31',
            'last_renewal_date': '2024-01-15',
            'next_renewal_due': '2025-01-15'
        }
    
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
                system_component='zppa_service',
                timestamp=datetime.utcnow()
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log integration activity: {str(e)}")

# Global service instance
zppa_service = ZPPAIntegrationService()