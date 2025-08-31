"""
Government Bus Integration Service
Handles inter-agency communication between Zambian government institutions
"""
import httpx
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.integrations import GovernmentBusIntegration, IntegrationAuditLog
from app.core.config import settings

logger = logging.getLogger(__name__)

class GovernmentBusService:
    """Service for Government Bus integration and inter-agency communication"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'GOVT_BUS_BASE_URL', 'https://govbus.gov.zm/api/v1')
        self.client_id = getattr(settings, 'GOVT_BUS_CLIENT_ID', 'napsa-erm-client')
        self.client_secret = getattr(settings, 'GOVT_BUS_CLIENT_SECRET', 'demo-secret-2024')
        self.timeout = 45  # Longer timeout for government services
        
        # Supported government agencies
        self.agencies = {
            'ZRA': 'Zambia Revenue Authority',
            'PACRA': 'Patents and Companies Registration Agency',
            'BOZ': 'Bank of Zambia',
            'NAPSA': 'National Pension Scheme Authority',
            'ZICA': 'Zambia Institute of Chartered Accountants',
            'ZCCM': 'Zambia Competition and Consumer Protection Commission',
            'ECZ': 'Energy Regulation Board',
            'ZEMA': 'Zambia Environmental Management Agency'
        }
    
    async def authenticate_with_bus(self, db: Session) -> str:
        """Authenticate with Government Bus and get access token"""
        try:
            # Mock authentication - replace with actual Government Bus OAuth
            mock_token = f"govbus_token_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            self._log_bus_activity(
                db, 'AUTH', 'authentication', 'success',
                request_data={'client_id': self.client_id},
                response_data={'token_obtained': True}
            )
            
            return mock_token
            
        except Exception as e:
            logger.error(f"Government Bus authentication failed: {str(e)}")
            self._log_bus_activity(
                db, 'AUTH', 'authentication', 'failed',
                error_message=str(e)
            )
            raise
    
    async def query_agency_data(
        self, agency_code: str, service_code: str, 
        query_params: Dict, db: Session
    ) -> Dict[str, Any]:
        """Query data from a government agency via Government Bus"""
        try:
            transaction_id = str(uuid.uuid4())
            
            # Mock agency query - replace with actual Government Bus API
            mock_response = self._mock_agency_query(agency_code, service_code, query_params)
            
            # Record the transaction
            bus_record = GovernmentBusIntegration(
                agency_code=agency_code,
                service_code=service_code,
                transaction_id=transaction_id,
                request_type='query',
                request_payload=query_params,
                response_payload=mock_response,
                status='completed',
                request_timestamp=datetime.utcnow(),
                response_timestamp=datetime.utcnow(),
                processing_time_ms=150
            )
            db.add(bus_record)
            db.commit()
            
            self._log_bus_activity(
                db, agency_code, 'data_query', 'success',
                request_data={'service_code': service_code, 'transaction_id': transaction_id},
                response_data={'status': 'completed'}
            )
            
            return {
                'transaction_id': transaction_id,
                'status': 'success',
                'data': mock_response,
                'agency': self.agencies.get(agency_code, agency_code),
                'service': service_code,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Government Bus query failed for {agency_code}/{service_code}: {str(e)}")
            
            # Record failed transaction
            bus_record = GovernmentBusIntegration(
                agency_code=agency_code,
                service_code=service_code,
                transaction_id=str(uuid.uuid4()),
                request_type='query',
                request_payload=query_params,
                status='failed',
                error_message=str(e),
                request_timestamp=datetime.utcnow()
            )
            db.add(bus_record)
            db.commit()
            
            return {
                'status': 'failed',
                'error': str(e),
                'agency': agency_code,
                'service': service_code
            }
    
    async def submit_data_to_agency(
        self, agency_code: str, service_code: str,
        submission_data: Dict, db: Session
    ) -> Dict[str, Any]:
        """Submit data to a government agency via Government Bus"""
        try:
            transaction_id = str(uuid.uuid4())
            
            # Mock data submission - replace with actual Government Bus API
            mock_response = self._mock_data_submission(agency_code, service_code, submission_data)
            
            # Record the transaction
            bus_record = GovernmentBusIntegration(
                agency_code=agency_code,
                service_code=service_code,
                transaction_id=transaction_id,
                request_type='update',
                request_payload=submission_data,
                response_payload=mock_response,
                status='completed',
                request_timestamp=datetime.utcnow(),
                response_timestamp=datetime.utcnow(),
                processing_time_ms=250
            )
            db.add(bus_record)
            db.commit()
            
            self._log_bus_activity(
                db, agency_code, 'data_submission', 'success',
                request_data={'service_code': service_code, 'transaction_id': transaction_id},
                response_data=mock_response
            )
            
            return {
                'transaction_id': transaction_id,
                'status': 'success',
                'submission_id': mock_response.get('submission_id'),
                'receipt_number': mock_response.get('receipt_number'),
                'agency': self.agencies.get(agency_code, agency_code),
                'service': service_code,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Government Bus submission failed for {agency_code}/{service_code}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'agency': agency_code,
                'service': service_code
            }
    
    async def get_transaction_status(self, transaction_id: str, db: Session) -> Dict[str, Any]:
        """Get status of a Government Bus transaction"""
        try:
            bus_record = db.query(GovernmentBusIntegration).filter(
                GovernmentBusIntegration.transaction_id == transaction_id
            ).first()
            
            if not bus_record:
                return {
                    'status': 'not_found',
                    'error': 'Transaction not found'
                }
            
            return {
                'transaction_id': transaction_id,
                'agency': bus_record.agency_code,
                'service': bus_record.service_code,
                'status': bus_record.status,
                'request_type': bus_record.request_type,
                'processing_time_ms': bus_record.processing_time_ms,
                'created_at': bus_record.request_timestamp.isoformat(),
                'completed_at': bus_record.response_timestamp.isoformat() if bus_record.response_timestamp else None,
                'error_message': bus_record.error_message
            }
            
        except Exception as e:
            logger.error(f"Transaction status check failed for {transaction_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def get_agency_services(self, agency_code: str, db: Session) -> List[Dict[str, Any]]:
        """Get available services for a government agency"""
        try:
            # Mock service discovery - replace with actual Government Bus API
            services_map = {
                'ZRA': [
                    {'code': 'TPIN_VALIDATION', 'name': 'TPIN Validation', 'description': 'Validate Tax Payer Identification Number'},
                    {'code': 'TAX_CLEARANCE', 'name': 'Tax Clearance Check', 'description': 'Check tax clearance certificate status'},
                    {'code': 'COMPLIANCE_STATUS', 'name': 'Tax Compliance Status', 'description': 'Get comprehensive tax compliance information'},
                    {'code': 'TAX_RETURN_SUBMIT', 'name': 'Tax Return Submission', 'description': 'Submit tax return data'}
                ],
                'PACRA': [
                    {'code': 'COMPANY_VERIFICATION', 'name': 'Company Verification', 'description': 'Verify company registration'},
                    {'code': 'COMPANY_DETAILS', 'name': 'Company Details', 'description': 'Get comprehensive company information'},
                    {'code': 'DIRECTOR_INFO', 'name': 'Director Information', 'description': 'Get company director details'},
                    {'code': 'ANNUAL_RETURN_SUBMIT', 'name': 'Annual Return Submission', 'description': 'Submit annual return'}
                ],
                'NAPSA': [
                    {'code': 'EMPLOYER_VALIDATION', 'name': 'Employer Validation', 'description': 'Validate employer registration'},
                    {'code': 'CONTRIBUTION_STATUS', 'name': 'Contribution Status', 'description': 'Check contribution compliance'},
                    {'code': 'EMPLOYEE_VERIFICATION', 'name': 'Employee Verification', 'description': 'Verify employee NAPSA membership'},
                    {'code': 'CONTRIBUTION_SUBMIT', 'name': 'Contribution Submission', 'description': 'Submit contribution data'}
                ]
            }
            
            services = services_map.get(agency_code, [])
            
            self._log_bus_activity(
                db, agency_code, 'service_discovery', 'success',
                request_data={'agency_code': agency_code},
                response_data={'services_count': len(services)}
            )
            
            return services
            
        except Exception as e:
            logger.error(f"Service discovery failed for {agency_code}: {str(e)}")
            return []
    
    async def bulk_query_agencies(self, queries: List[Dict], db: Session) -> List[Dict[str, Any]]:
        """Perform bulk queries across multiple agencies"""
        try:
            results = []
            
            for query in queries:
                result = await self.query_agency_data(
                    query['agency_code'],
                    query['service_code'],
                    query['params'],
                    db
                )
                results.append(result)
            
            self._log_bus_activity(
                db, 'BULK', 'bulk_query', 'success',
                request_data={'queries_count': len(queries)},
                response_data={'results_count': len(results)}
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk query failed: {str(e)}")
            return []
    
    def _mock_agency_query(self, agency_code: str, service_code: str, params: Dict) -> Dict[str, Any]:
        """Mock agency query response based on agency and service"""
        responses = {
            'ZRA': {
                'TPIN_VALIDATION': {
                    'valid': True,
                    'taxpayer_name': 'SAMPLE COMPANY LIMITED',
                    'status': 'active'
                },
                'TAX_CLEARANCE': {
                    'clearance_status': 'valid',
                    'certificate_number': 'TCC-123456-2024',
                    'expiry_date': '2024-12-31'
                }
            },
            'PACRA': {
                'COMPANY_VERIFICATION': {
                    'valid': True,
                    'company_name': 'SAMPLE COMPANY LIMITED',
                    'registration_status': 'active'
                },
                'COMPANY_DETAILS': {
                    'registration_number': params.get('registration_number', '123456'),
                    'company_name': 'SAMPLE COMPANY LIMITED',
                    'status': 'active'
                }
            },
            'NAPSA': {
                'EMPLOYER_VALIDATION': {
                    'valid': True,
                    'employer_name': 'SAMPLE EMPLOYER LIMITED',
                    'status': 'active'
                },
                'CONTRIBUTION_STATUS': {
                    'compliance_status': 'compliant',
                    'outstanding_amount': 0.00
                }
            }
        }
        
        return responses.get(agency_code, {}).get(service_code, {'status': 'service_not_found'})
    
    def _mock_data_submission(self, agency_code: str, service_code: str, data: Dict) -> Dict[str, Any]:
        """Mock data submission response"""
        return {
            'submission_id': f'{agency_code}-{service_code}-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
            'receipt_number': f'RCP-{agency_code}-{datetime.utcnow().strftime("%Y%m%d")}',
            'status': 'accepted',
            'processing_status': 'under_review',
            'estimated_completion': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
    
    def _log_bus_activity(
        self, db: Session, agency_code: str, activity_type: str,
        status: str, request_data: Dict = None, response_data: Dict = None,
        error_message: str = None
    ):
        """Log Government Bus activity to audit table"""
        try:
            audit_log = IntegrationAuditLog(
                integration_type='gov_bus',
                activity_type=f'{agency_code}_{activity_type}',
                status=status,
                request_data=request_data,
                response_data=response_data,
                error_message=error_message,
                system_component='government_bus_service',
                timestamp=datetime.utcnow()
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log Government Bus activity: {str(e)}")

# Global service instance
government_bus_service = GovernmentBusService()