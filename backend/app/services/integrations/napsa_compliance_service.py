"""
NAPSA Compliance Integration Service
Handles social security compliance, contribution tracking, and employee verification
"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.integrations import NAPSAComplianceIntegration, IntegrationAuditLog
from app.core.config import settings

logger = logging.getLogger(__name__)

class NAPSAComplianceService:
    """Service for NAPSA compliance integration and social security management"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'NAPSA_API_BASE_URL', 'https://api.napsa.co.zm/v1')
        self.api_key = getattr(settings, 'NAPSA_API_KEY', 'demo-key-napsa-2024')
        self.timeout = 30
        
    async def validate_employer_number(self, employer_number: str, db: Session) -> Dict[str, Any]:
        """Validate employer registration number with NAPSA"""
        try:
            # Mock NAPSA API call - replace with actual NAPSA API
            mock_response = self._mock_employer_validation(employer_number)
            
            self._log_integration_activity(
                db, 'napsa', 'employer_validation', 'success',
                request_data={'employer_number': employer_number},
                response_data=mock_response
            )
            
            return {
                'valid': mock_response['valid'],
                'employer_name': mock_response.get('employer_name'),
                'registration_status': mock_response.get('status'),
                'registration_date': mock_response.get('registration_date')
            }
            
        except Exception as e:
            logger.error(f"NAPSA employer validation failed for {employer_number}: {str(e)}")
            self._log_integration_activity(
                db, 'napsa', 'employer_validation', 'failed',
                request_data={'employer_number': employer_number},
                error_message=str(e)
            )
            return {
                'valid': False,
                'error': str(e)
            }
    
    async def get_contribution_status(self, employer_number: str, db: Session) -> Dict[str, Any]:
        """Get employer contribution compliance status"""
        try:
            mock_response = self._mock_contribution_status(employer_number)
            
            # Update or create NAPSA compliance record
            napsa_record = db.query(NAPSAComplianceIntegration).filter(
                NAPSAComplianceIntegration.employer_number == employer_number
            ).first()
            
            if not napsa_record:
                napsa_record = NAPSAComplianceIntegration(
                    employer_number=employer_number,
                    company_name=mock_response['company_name'],
                    registration_status=mock_response['registration_status'],
                    compliance_status=mock_response['compliance_status'],
                    total_employees=mock_response['total_employees'],
                    active_employees=mock_response['active_employees'],
                    monthly_contribution=Decimal(str(mock_response['monthly_contribution'])),
                    outstanding_contributions=Decimal(str(mock_response['outstanding_contributions'])),
                    contribution_compliance_rate=Decimal(str(mock_response['compliance_rate'])),
                    penalty_amount=Decimal(str(mock_response['penalty_amount'])),
                    compliance_certificate_valid=mock_response['certificate_valid'],
                    last_sync_date=datetime.utcnow(),
                    sync_status='success',
                    api_response=mock_response
                )
                db.add(napsa_record)
            else:
                # Update existing record
                napsa_record.company_name = mock_response['company_name']
                napsa_record.compliance_status = mock_response['compliance_status']
                napsa_record.total_employees = mock_response['total_employees']
                napsa_record.active_employees = mock_response['active_employees']
                napsa_record.monthly_contribution = Decimal(str(mock_response['monthly_contribution']))
                napsa_record.outstanding_contributions = Decimal(str(mock_response['outstanding_contributions']))
                napsa_record.contribution_compliance_rate = Decimal(str(mock_response['compliance_rate']))
                napsa_record.penalty_amount = Decimal(str(mock_response['penalty_amount']))
                napsa_record.compliance_certificate_valid = mock_response['certificate_valid']
                napsa_record.last_sync_date = datetime.utcnow()
                napsa_record.sync_status = 'success'
                napsa_record.api_response = mock_response
                napsa_record.updated_at = datetime.utcnow()
            
            db.commit()
            
            self._log_integration_activity(
                db, 'napsa', 'contribution_status_check', 'success',
                request_data={'employer_number': employer_number},
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"NAPSA contribution status check failed for {employer_number}: {str(e)}")
            self._log_integration_activity(
                db, 'napsa', 'contribution_status_check', 'failed',
                request_data={'employer_number': employer_number},
                error_message=str(e)
            )
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    async def submit_contribution_data(self, employer_number: str, contribution_data: Dict, db: Session) -> Dict[str, Any]:
        """Submit employee contribution data to NAPSA"""
        try:
            # Mock submission - replace with actual NAPSA API
            mock_response = {
                'submission_id': f'NAPSA-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
                'status': 'accepted',
                'receipt_number': f'CONT-{employer_number}-{datetime.utcnow().strftime("%Y%m")}',
                'submission_date': datetime.utcnow().isoformat(),
                'total_employees': contribution_data.get('employee_count', 0),
                'total_contribution': contribution_data.get('total_contribution', 0),
                'processing_status': 'processed',
                'confirmation_message': 'Contribution data successfully submitted'
            }
            
            self._log_integration_activity(
                db, 'napsa', 'contribution_submission', 'success',
                request_data={'employer_number': employer_number, 'contribution_data': contribution_data},
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"NAPSA contribution submission failed for {employer_number}: {str(e)}")
            self._log_integration_activity(
                db, 'napsa', 'contribution_submission', 'failed',
                request_data={'employer_number': employer_number},
                error_message=str(e)
            )
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def verify_employee_membership(self, nrc_number: str, db: Session) -> Dict[str, Any]:
        """Verify employee NAPSA membership status"""
        try:
            # Mock employee verification
            mock_response = {
                'nrc_number': nrc_number,
                'member_status': 'active',
                'membership_number': f'MEM-{nrc_number[-6:]}',
                'registration_date': '2015-01-15',
                'last_contribution_date': '2024-07-31',
                'total_contributions': 25000.00,
                'benefit_eligibility': {
                    'retirement': True,
                    'invalidity': True,
                    'survivors': True
                },
                'employer_history': [
                    {
                        'employer_number': '123456',
                        'employer_name': 'PREVIOUS EMPLOYER LTD',
                        'period_from': '2015-01-15',
                        'period_to': '2020-12-31'
                    },
                    {
                        'employer_number': '789012',
                        'employer_name': 'CURRENT EMPLOYER LTD',
                        'period_from': '2021-01-01',
                        'period_to': 'current'
                    }
                ]
            }
            
            self._log_integration_activity(
                db, 'napsa', 'employee_verification', 'success',
                request_data={'nrc_number': nrc_number},
                response_data={'member_status': mock_response['member_status']}
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"NAPSA employee verification failed for {nrc_number}: {str(e)}")
            return {
                'member_status': 'unknown',
                'error': str(e)
            }
    
    async def get_compliance_obligations(self, employer_number: str, db: Session) -> List[Dict[str, Any]]:
        """Get upcoming NAPSA compliance obligations"""
        try:
            # Mock compliance obligations
            mock_obligations = [
                {
                    'obligation_type': 'MONTHLY_CONTRIBUTION',
                    'period': '2024-07',
                    'due_date': '2024-08-15',
                    'status': 'pending',
                    'estimated_amount': 15000.00
                },
                {
                    'obligation_type': 'ANNUAL_RETURN',
                    'period': '2024',
                    'due_date': '2024-03-31',
                    'status': 'overdue',
                    'penalty_amount': 500.00
                },
                {
                    'obligation_type': 'AUDIT_SUBMISSION',
                    'period': '2024',
                    'due_date': '2024-09-30',
                    'status': 'upcoming',
                    'estimated_amount': 0.00
                }
            ]
            
            self._log_integration_activity(
                db, 'napsa', 'compliance_obligations_check', 'success',
                request_data={'employer_number': employer_number},
                response_data={'obligations_count': len(mock_obligations)}
            )
            
            return mock_obligations
            
        except Exception as e:
            logger.error(f"NAPSA compliance obligations check failed for {employer_number}: {str(e)}")
            return []
    
    async def get_certificate_status(self, employer_number: str, db: Session) -> Dict[str, Any]:
        """Get NAPSA compliance certificate status"""
        try:
            mock_response = {
                'employer_number': employer_number,
                'certificate_status': 'valid',
                'certificate_number': f'NAPSA-CERT-{employer_number}-2024',
                'issue_date': '2024-01-01',
                'expiry_date': '2024-12-31',
                'valid_for_tender': True,
                'compliance_score': 92,
                'conditions': [],
                'renewal_due': '2024-11-30'
            }
            
            self._log_integration_activity(
                db, 'napsa', 'certificate_status_check', 'success',
                request_data={'employer_number': employer_number},
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"NAPSA certificate status check failed for {employer_number}: {str(e)}")
            return {
                'certificate_status': 'unknown',
                'error': str(e)
            }
    
    def _mock_employer_validation(self, employer_number: str) -> Dict[str, Any]:
        """Mock employer validation response"""
        if employer_number.startswith('EMP'):
            return {
                'valid': True,
                'employer_name': 'NAPSA ZAMBIA LIMITED',
                'status': 'active',
                'registration_date': '2010-01-15',
                'employer_type': 'private_company'
            }
        else:
            return {
                'valid': len(employer_number) >= 6,
                'employer_name': f'EMPLOYER {employer_number}',
                'status': 'active' if len(employer_number) >= 6 else 'invalid',
                'registration_date': '2020-01-01',
                'employer_type': 'private_company'
            }
    
    def _mock_contribution_status(self, employer_number: str) -> Dict[str, Any]:
        """Mock contribution status response"""
        return {
            'employer_number': employer_number,
            'company_name': f'COMPANY {employer_number}',
            'registration_status': 'active',
            'compliance_status': 'compliant',
            'total_employees': 150,
            'active_employees': 145,
            'monthly_contribution': 28000.00,
            'outstanding_contributions': 0.00,
            'compliance_rate': 98.5,
            'penalty_amount': 0.00,
            'certificate_valid': True,
            'last_contribution_date': '2024-07-31',
            'next_contribution_due': '2024-08-15',
            'contribution_score': 95
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
                system_component='napsa_compliance_service',
                timestamp=datetime.utcnow()
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log integration activity: {str(e)}")

# Global service instance
napsa_compliance_service = NAPSAComplianceService()