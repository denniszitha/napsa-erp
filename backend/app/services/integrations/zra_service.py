"""
Zambia Revenue Authority (ZRA) Integration Service
Handles tax compliance, TPIN validation, and tax clearance verification
"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.integrations import ZRAIntegration, IntegrationAuditLog
from app.core.config import settings

logger = logging.getLogger(__name__)

class ZRAIntegrationService:
    """Service for ZRA API integration and tax compliance management"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'ZRA_API_BASE_URL', 'https://api.zra.zm/v1')
        self.api_key = getattr(settings, 'ZRA_API_KEY', 'demo-key-zra-2024')
        self.timeout = 30
        
    async def validate_tpin(self, tpin: str, db: Session) -> Dict[str, Any]:
        """Validate Tax Payer Identification Number with ZRA"""
        try:
            # Mock ZRA API call - replace with actual ZRA API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                    'X-ZRA-Client': 'NAPSA-ERM'
                }
                
                # Simulate API call (replace with actual ZRA endpoint)
                mock_response = self._mock_tpin_validation(tpin)
                
                # Log the integration attempt
                self._log_integration_activity(
                    db, 'zra', 'tpin_validation', 'success',
                    request_data={'tpin': tpin},
                    response_data=mock_response
                )
                
                return {
                    'valid': mock_response['valid'],
                    'taxpayer_name': mock_response.get('taxpayer_name'),
                    'registration_status': mock_response.get('status'),
                    'registration_date': mock_response.get('registration_date')
                }
                
        except Exception as e:
            logger.error(f"ZRA TPIN validation failed for {tpin}: {str(e)}")
            self._log_integration_activity(
                db, 'zra', 'tpin_validation', 'failed',
                request_data={'tpin': tpin},
                error_message=str(e)
            )
            return {
                'valid': False,
                'error': str(e)
            }
    
    async def get_tax_clearance_status(self, tpin: str, db: Session) -> Dict[str, Any]:
        """Get tax clearance certificate status"""
        try:
            # Mock API response - replace with actual ZRA API
            mock_response = self._mock_tax_clearance_status(tpin)
            
            self._log_integration_activity(
                db, 'zra', 'tax_clearance_check', 'success',
                request_data={'tpin': tpin},
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"ZRA tax clearance check failed for {tpin}: {str(e)}")
            self._log_integration_activity(
                db, 'zra', 'tax_clearance_check', 'failed',
                request_data={'tpin': tpin},
                error_message=str(e)
            )
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    async def get_compliance_status(self, tpin: str, db: Session) -> Dict[str, Any]:
        """Get comprehensive tax compliance status"""
        try:
            # Mock comprehensive compliance data
            mock_response = self._mock_compliance_status(tpin)
            
            # Update or create ZRA integration record
            zra_record = db.query(ZRAIntegration).filter(
                ZRAIntegration.taxpayer_tpin == tpin
            ).first()
            
            if not zra_record:
                zra_record = ZRAIntegration(
                    taxpayer_tpin=tpin,
                    company_name=mock_response['company_name'],
                    registration_status=mock_response['registration_status'],
                    tax_clearance_status=mock_response['tax_clearance_status'],
                    vat_registration=mock_response['vat_registered'],
                    paye_registration=mock_response['paye_registered'],
                    withholding_tax_agent=mock_response['withholding_agent'],
                    outstanding_tax_amount=mock_response['outstanding_amount'],
                    compliance_rating=mock_response['compliance_rating'],
                    last_sync_date=datetime.utcnow(),
                    sync_status='success',
                    api_response=mock_response
                )
                db.add(zra_record)
            else:
                # Update existing record
                zra_record.company_name = mock_response['company_name']
                zra_record.registration_status = mock_response['registration_status']
                zra_record.tax_clearance_status = mock_response['tax_clearance_status']
                zra_record.outstanding_tax_amount = mock_response['outstanding_amount']
                zra_record.compliance_rating = mock_response['compliance_rating']
                zra_record.last_sync_date = datetime.utcnow()
                zra_record.sync_status = 'success'
                zra_record.api_response = mock_response
                zra_record.updated_at = datetime.utcnow()
            
            db.commit()
            
            self._log_integration_activity(
                db, 'zra', 'compliance_status_check', 'success',
                request_data={'tpin': tpin},
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"ZRA compliance status check failed for {tpin}: {str(e)}")
            self._log_integration_activity(
                db, 'zra', 'compliance_status_check', 'failed',
                request_data={'tpin': tpin},
                error_message=str(e)
            )
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    async def submit_tax_return_notification(self, tpin: str, return_data: Dict, db: Session) -> Dict[str, Any]:
        """Submit tax return filing notification to ZRA"""
        try:
            # Mock submission - replace with actual ZRA API
            mock_response = {
                'submission_id': f'ZRA-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
                'status': 'accepted',
                'receipt_number': f'RCP-{tpin}-{datetime.utcnow().year}',
                'submission_date': datetime.utcnow().isoformat(),
                'processing_status': 'under_review'
            }
            
            self._log_integration_activity(
                db, 'zra', 'tax_return_submission', 'success',
                request_data={'tpin': tpin, 'return_data': return_data},
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"ZRA tax return submission failed for {tpin}: {str(e)}")
            self._log_integration_activity(
                db, 'zra', 'tax_return_submission', 'failed',
                request_data={'tpin': tpin},
                error_message=str(e)
            )
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def get_tax_obligations(self, tpin: str, db: Session) -> List[Dict[str, Any]]:
        """Get upcoming tax obligations and deadlines"""
        try:
            # Mock tax obligations data
            mock_obligations = [
                {
                    'obligation_type': 'VAT_RETURN',
                    'period': '2024-07',
                    'due_date': '2024-08-15',
                    'status': 'overdue',
                    'penalty_amount': 500.00
                },
                {
                    'obligation_type': 'PAYE_RETURN',
                    'period': '2024-07',
                    'due_date': '2024-08-09',
                    'status': 'due_today',
                    'penalty_amount': 0.00
                },
                {
                    'obligation_type': 'ANNUAL_RETURN',
                    'period': '2024',
                    'due_date': '2024-12-31',
                    'status': 'pending',
                    'penalty_amount': 0.00
                }
            ]
            
            self._log_integration_activity(
                db, 'zra', 'tax_obligations_check', 'success',
                request_data={'tpin': tpin},
                response_data={'obligations_count': len(mock_obligations)}
            )
            
            return mock_obligations
            
        except Exception as e:
            logger.error(f"ZRA tax obligations check failed for {tpin}: {str(e)}")
            return []
    
    def _mock_tpin_validation(self, tpin: str) -> Dict[str, Any]:
        """Mock TPIN validation response - replace with actual ZRA API"""
        # Simulate different validation scenarios based on TPIN pattern
        if tpin.startswith('1001'):
            return {
                'valid': True,
                'taxpayer_name': 'NAPSA ZAMBIA LIMITED',
                'status': 'active',
                'registration_date': '2010-01-15',
                'taxpayer_type': 'company'
            }
        elif tpin.startswith('2002'):
            return {
                'valid': True,
                'taxpayer_name': 'EXAMPLE MINING CORPORATION',
                'status': 'active',
                'registration_date': '2015-03-20',
                'taxpayer_type': 'company'
            }
        else:
            return {
                'valid': len(tpin) == 10 and tpin.isdigit(),
                'taxpayer_name': f'COMPANY {tpin}',
                'status': 'active' if len(tpin) == 10 else 'invalid',
                'registration_date': '2020-01-01',
                'taxpayer_type': 'company'
            }
    
    def _mock_tax_clearance_status(self, tpin: str) -> Dict[str, Any]:
        """Mock tax clearance status - replace with actual ZRA API"""
        return {
            'tpin': tpin,
            'clearance_status': 'valid',
            'certificate_number': f'TCC-{tpin}-2024',
            'issue_date': '2024-01-01',
            'expiry_date': '2024-12-31',
            'valid_for_tender': True,
            'restrictions': []
        }
    
    def _mock_compliance_status(self, tpin: str) -> Dict[str, Any]:
        """Mock comprehensive compliance status - replace with actual ZRA API"""
        return {
            'tpin': tpin,
            'company_name': f'COMPANY {tpin}',
            'registration_status': 'active',
            'tax_clearance_status': 'valid',
            'vat_registered': True,
            'paye_registered': True,
            'withholding_agent': True,
            'outstanding_amount': 0.00,
            'compliance_rating': 'excellent',
            'last_return_filed': '2024-07-31',
            'next_return_due': '2024-08-31',
            'compliance_score': 95,
            'risk_category': 'low'
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
                system_component='zra_service',
                timestamp=datetime.utcnow()
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log integration activity: {str(e)}")

# Global service instance
zra_service = ZRAIntegrationService()