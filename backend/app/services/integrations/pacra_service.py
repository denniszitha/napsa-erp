"""
PACRA (Patents and Companies Registration Agency) Integration Service
Handles company registration verification, business license checks, and annual return compliance
"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.integrations import PACRAIntegration, IntegrationAuditLog
from app.core.config import settings

logger = logging.getLogger(__name__)

class PACRAIntegrationService:
    """Service for PACRA API integration and company registration management"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'PACRA_API_BASE_URL', 'https://api.pacra.org.zm/v1')
        self.api_key = getattr(settings, 'PACRA_API_KEY', 'demo-key-pacra-2024')
        self.timeout = 30
        
    async def verify_company_registration(self, registration_number: str, db: Session) -> Dict[str, Any]:
        """Verify company registration with PACRA"""
        try:
            # Mock PACRA API call - replace with actual PACRA API
            mock_response = self._mock_company_verification(registration_number)
            
            self._log_integration_activity(
                db, 'pacra', 'company_verification', 'success',
                request_data={'registration_number': registration_number},
                response_data=mock_response
            )
            
            return {
                'valid': mock_response['valid'],
                'company_name': mock_response.get('company_name'),
                'registration_status': mock_response.get('status'),
                'incorporation_date': mock_response.get('incorporation_date'),
                'company_type': mock_response.get('company_type')
            }
            
        except Exception as e:
            logger.error(f"PACRA company verification failed for {registration_number}: {str(e)}")
            self._log_integration_activity(
                db, 'pacra', 'company_verification', 'failed',
                request_data={'registration_number': registration_number},
                error_message=str(e)
            )
            return {
                'valid': False,
                'error': str(e)
            }
    
    async def get_company_details(self, registration_number: str, db: Session) -> Dict[str, Any]:
        """Get comprehensive company details from PACRA"""
        try:
            mock_response = self._mock_company_details(registration_number)
            
            # Update or create PACRA integration record
            pacra_record = db.query(PACRAIntegration).filter(
                PACRAIntegration.company_registration_number == registration_number
            ).first()
            
            if not pacra_record:
                pacra_record = PACRAIntegration(
                    company_registration_number=registration_number,
                    company_name=mock_response['company_name'],
                    company_type=mock_response['company_type'],
                    registration_status=mock_response['registration_status'],
                    business_license_number=mock_response.get('business_license_number'),
                    license_category=mock_response.get('license_category'),
                    license_status=mock_response.get('license_status'),
                    authorized_share_capital=Decimal(str(mock_response.get('authorized_capital', 0))),
                    paid_up_capital=Decimal(str(mock_response.get('paid_up_capital', 0))),
                    number_of_directors=mock_response.get('directors_count', 0),
                    number_of_shareholders=mock_response.get('shareholders_count', 0),
                    registered_address=mock_response.get('registered_address'),
                    postal_address=mock_response.get('postal_address'),
                    contact_email=mock_response.get('contact_email'),
                    contact_phone=mock_response.get('contact_phone'),
                    annual_return_filed=mock_response.get('annual_return_filed', False),
                    compliance_status=mock_response.get('compliance_status'),
                    penalty_amount=Decimal(str(mock_response.get('penalty_amount', 0))),
                    last_sync_date=datetime.utcnow(),
                    sync_status='success',
                    api_response=mock_response
                )
                db.add(pacra_record)
            else:
                # Update existing record
                pacra_record.company_name = mock_response['company_name']
                pacra_record.registration_status = mock_response['registration_status']
                pacra_record.license_status = mock_response.get('license_status')
                pacra_record.compliance_status = mock_response.get('compliance_status')
                pacra_record.annual_return_filed = mock_response.get('annual_return_filed', False)
                pacra_record.penalty_amount = Decimal(str(mock_response.get('penalty_amount', 0)))
                pacra_record.last_sync_date = datetime.utcnow()
                pacra_record.sync_status = 'success'
                pacra_record.api_response = mock_response
                pacra_record.updated_at = datetime.utcnow()
            
            db.commit()
            
            self._log_integration_activity(
                db, 'pacra', 'company_details_check', 'success',
                request_data={'registration_number': registration_number},
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"PACRA company details check failed for {registration_number}: {str(e)}")
            self._log_integration_activity(
                db, 'pacra', 'company_details_check', 'failed',
                request_data={'registration_number': registration_number},
                error_message=str(e)
            )
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    async def check_business_license_status(self, license_number: str, db: Session) -> Dict[str, Any]:
        """Check business license status with PACRA"""
        try:
            mock_response = {
                'license_number': license_number,
                'license_status': 'valid',
                'license_category': 'GENERAL_BUSINESS',
                'business_name': f'BUSINESS {license_number}',
                'issue_date': '2024-01-01',
                'expiry_date': '2024-12-31',
                'renewal_due': '2024-11-30',
                'license_conditions': [],
                'valid_for_operations': True,
                'penalty_amount': 0.00
            }
            
            self._log_integration_activity(
                db, 'pacra', 'license_status_check', 'success',
                request_data={'license_number': license_number},
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"PACRA license status check failed for {license_number}: {str(e)}")
            return {
                'license_status': 'unknown',
                'error': str(e)
            }
    
    async def submit_annual_return(self, registration_number: str, return_data: Dict, db: Session) -> Dict[str, Any]:
        """Submit annual return to PACRA"""
        try:
            # Mock submission - replace with actual PACRA API
            mock_response = {
                'submission_id': f'PACRA-AR-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
                'status': 'accepted',
                'receipt_number': f'AR-{registration_number}-{datetime.utcnow().year}',
                'submission_date': datetime.utcnow().isoformat(),
                'filing_fee': 500.00,
                'penalty_amount': 0.00,
                'total_amount': 500.00,
                'payment_reference': f'PAY-{registration_number}-AR',
                'processing_status': 'under_review',
                'expected_completion': (datetime.utcnow() + timedelta(days=5)).isoformat()
            }
            
            self._log_integration_activity(
                db, 'pacra', 'annual_return_submission', 'success',
                request_data={'registration_number': registration_number, 'return_data': return_data},
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"PACRA annual return submission failed for {registration_number}: {str(e)}")
            self._log_integration_activity(
                db, 'pacra', 'annual_return_submission', 'failed',
                request_data={'registration_number': registration_number},
                error_message=str(e)
            )
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def get_director_information(self, registration_number: str, db: Session) -> List[Dict[str, Any]]:
        """Get company director information from PACRA"""
        try:
            # Mock director information
            mock_directors = [
                {
                    'director_id': 'DIR001',
                    'full_name': 'JOHN MWANZA PHIRI',
                    'nrc_number': '123456/78/1',
                    'nationality': 'Zambian',
                    'appointment_date': '2020-01-15',
                    'designation': 'Managing Director',
                    'status': 'active',
                    'residential_address': 'Plot 123, Kabulonga, Lusaka'
                },
                {
                    'director_id': 'DIR002',
                    'full_name': 'MARY CHANDA BANDA',
                    'nrc_number': '234567/89/1',
                    'nationality': 'Zambian',
                    'appointment_date': '2020-01-15',
                    'designation': 'Finance Director',
                    'status': 'active',
                    'residential_address': 'Plot 456, Roma, Lusaka'
                }
            ]
            
            self._log_integration_activity(
                db, 'pacra', 'director_info_check', 'success',
                request_data={'registration_number': registration_number},
                response_data={'directors_count': len(mock_directors)}
            )
            
            return mock_directors
            
        except Exception as e:
            logger.error(f"PACRA director information check failed for {registration_number}: {str(e)}")
            return []
    
    async def get_compliance_obligations(self, registration_number: str, db: Session) -> List[Dict[str, Any]]:
        """Get upcoming PACRA compliance obligations"""
        try:
            # Mock compliance obligations
            mock_obligations = [
                {
                    'obligation_type': 'ANNUAL_RETURN',
                    'period': '2024',
                    'due_date': '2024-08-31',
                    'status': 'pending',
                    'filing_fee': 500.00,
                    'penalty_amount': 0.00
                },
                {
                    'obligation_type': 'BUSINESS_LICENSE_RENEWAL',
                    'period': '2024',
                    'due_date': '2024-11-30',
                    'status': 'upcoming',
                    'renewal_fee': 750.00,
                    'penalty_amount': 0.00
                },
                {
                    'obligation_type': 'CHANGE_OF_PARTICULARS',
                    'period': 'ongoing',
                    'due_date': 'within_30_days_of_change',
                    'status': 'not_applicable',
                    'filing_fee': 100.00,
                    'penalty_amount': 0.00
                }
            ]
            
            self._log_integration_activity(
                db, 'pacra', 'compliance_obligations_check', 'success',
                request_data={'registration_number': registration_number},
                response_data={'obligations_count': len(mock_obligations)}
            )
            
            return mock_obligations
            
        except Exception as e:
            logger.error(f"PACRA compliance obligations check failed for {registration_number}: {str(e)}")
            return []
    
    async def search_companies(self, search_criteria: Dict, db: Session) -> List[Dict[str, Any]]:
        """Search for companies in PACRA database"""
        try:
            # Mock company search results
            mock_results = [
                {
                    'registration_number': '123456',
                    'company_name': 'EXAMPLE MINING CORPORATION LIMITED',
                    'company_type': 'Private Limited Company',
                    'registration_status': 'active',
                    'incorporation_date': '2015-03-20',
                    'registered_address': 'Plot 789, Industrial Area, Kitwe'
                },
                {
                    'registration_number': '234567',
                    'company_name': 'ZAMBIA TRADING COMPANY LIMITED',
                    'company_type': 'Private Limited Company',
                    'registration_status': 'active',
                    'incorporation_date': '2018-07-12',
                    'registered_address': 'Plot 101, Cairo Road, Lusaka'
                }
            ]
            
            self._log_integration_activity(
                db, 'pacra', 'company_search', 'success',
                request_data={'search_criteria': search_criteria},
                response_data={'results_count': len(mock_results)}
            )
            
            return mock_results
            
        except Exception as e:
            logger.error(f"PACRA company search failed: {str(e)}")
            return []
    
    def _mock_company_verification(self, registration_number: str) -> Dict[str, Any]:
        """Mock company verification response"""
        if registration_number.startswith('12345'):
            return {
                'valid': True,
                'company_name': 'NAPSA ZAMBIA LIMITED',
                'status': 'active',
                'incorporation_date': '2010-01-15',
                'company_type': 'Private Limited Company'
            }
        else:
            return {
                'valid': len(registration_number) >= 6,
                'company_name': f'COMPANY {registration_number} LIMITED',
                'status': 'active' if len(registration_number) >= 6 else 'invalid',
                'incorporation_date': '2020-01-01',
                'company_type': 'Private Limited Company'
            }
    
    def _mock_company_details(self, registration_number: str) -> Dict[str, Any]:
        """Mock comprehensive company details"""
        return {
            'registration_number': registration_number,
            'company_name': f'COMPANY {registration_number} LIMITED',
            'company_type': 'Private Limited Company',
            'registration_status': 'active',
            'incorporation_date': '2020-01-15',
            'business_license_number': f'BL-{registration_number}',
            'license_category': 'GENERAL_BUSINESS',
            'license_status': 'valid',
            'authorized_capital': 100000.00,
            'paid_up_capital': 50000.00,
            'directors_count': 2,
            'shareholders_count': 2,
            'registered_address': f'Plot {registration_number}, Business District, Lusaka',
            'postal_address': f'P.O. Box {registration_number}, Lusaka',
            'contact_email': f'info@company{registration_number}.co.zm',
            'contact_phone': '+260-97-1234567',
            'annual_return_filed': True,
            'annual_return_due_date': '2024-08-31',
            'compliance_status': 'compliant',
            'penalty_amount': 0.00,
            'last_filing_date': '2024-07-15',
            'compliance_score': 92
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
                system_component='pacra_service',
                timestamp=datetime.utcnow()
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log integration activity: {str(e)}")

# Global service instance
pacra_service = PACRAIntegrationService()