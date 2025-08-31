"""
CCPC (Competition and Consumer Protection Commission) Integration Service
Handles business registration, consumer protection compliance, and competition monitoring
"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.integrations import CCPCIntegration, IntegrationAuditLog
from app.core.config import settings

logger = logging.getLogger(__name__)

class CCPCIntegrationService:
    """Service for CCPC API integration and consumer protection compliance"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'CCPC_API_BASE_URL', 'https://api.ccpc.org.zm/v1')
        self.api_key = getattr(settings, 'CCPC_API_KEY', 'demo-key-ccpc-2024')
        self.timeout = 30
        
    async def verify_business_registration(self, registration_number: str, db: Session) -> Dict[str, Any]:
        """Verify business registration with CCPC"""
        try:
            # Mock CCPC API call - replace with actual CCPC API
            mock_response = self._mock_business_verification(registration_number)
            
            self._log_integration_activity(
                db, 'ccpc', 'business_verification', 'success',
                request_data={'registration_number': registration_number},
                response_data=mock_response
            )
            
            return {
                'valid': mock_response['valid'],
                'company_name': mock_response.get('company_name'),
                'registration_status': mock_response.get('status'),
                'business_type': mock_response.get('business_type')
            }
            
        except Exception as e:
            logger.error(f"CCPC business verification failed for {registration_number}: {str(e)}")
            self._log_integration_activity(
                db, 'ccpc', 'business_verification', 'failed',
                request_data={'registration_number': registration_number},
                error_message=str(e)
            )
            return {
                'valid': False,
                'error': str(e)
            }
    
    async def get_consumer_protection_status(self, registration_number: str, db: Session) -> Dict[str, Any]:
        """Get consumer protection compliance status"""
        try:
            mock_response = self._mock_consumer_protection_status(registration_number)
            
            # Update or create CCPC integration record
            ccpc_record = db.query(CCPCIntegration).filter(
                CCPCIntegration.business_registration_number == registration_number
            ).first()
            
            if not ccpc_record:
                ccpc_record = CCPCIntegration(
                    business_registration_number=registration_number,
                    company_name=mock_response['company_name'],
                    business_type=mock_response['business_type'],
                    industry_sector=mock_response['industry_sector'],
                    business_activity_code=mock_response['business_activity_code'],
                    registration_status=mock_response['registration_status'],
                    consumer_complaints_count=mock_response['consumer_complaints_count'],
                    resolved_complaints_count=mock_response['resolved_complaints_count'],
                    pending_complaints_count=mock_response['pending_complaints_count'],
                    consumer_satisfaction_rating=Decimal(str(mock_response['consumer_satisfaction_rating'])),
                    market_share_percentage=Decimal(str(mock_response['market_share_percentage'])),
                    anti_competitive_practices_reported=mock_response['anti_competitive_practices_reported'],
                    price_control_applicable=mock_response['price_control_applicable'],
                    price_compliance_score=Decimal(str(mock_response['price_compliance_score'])),
                    pricing_violations_count=mock_response['pricing_violations_count'],
                    trade_license_number=mock_response['trade_license_number'],
                    trade_license_status=mock_response['trade_license_status'],
                    annual_revenue=Decimal(str(mock_response['annual_revenue'])),
                    number_of_employees=mock_response['number_of_employees'],
                    branches_count=mock_response['branches_count'],
                    last_sync_date=datetime.utcnow(),
                    sync_status='success',
                    api_response=mock_response
                )
                db.add(ccpc_record)
            else:
                # Update existing record
                ccpc_record.company_name = mock_response['company_name']
                ccpc_record.registration_status = mock_response['registration_status']
                ccpc_record.consumer_complaints_count = mock_response['consumer_complaints_count']
                ccpc_record.resolved_complaints_count = mock_response['resolved_complaints_count']
                ccpc_record.pending_complaints_count = mock_response['pending_complaints_count']
                ccpc_record.consumer_satisfaction_rating = Decimal(str(mock_response['consumer_satisfaction_rating']))
                ccpc_record.price_compliance_score = Decimal(str(mock_response['price_compliance_score']))
                ccpc_record.pricing_violations_count = mock_response['pricing_violations_count']
                ccpc_record.last_sync_date = datetime.utcnow()
                ccpc_record.sync_status = 'success'
                ccpc_record.api_response = mock_response
                ccpc_record.updated_at = datetime.utcnow()
            
            db.commit()
            
            self._log_integration_activity(
                db, 'ccpc', 'consumer_protection_status_check', 'success',
                request_data={'registration_number': registration_number},
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"CCPC consumer protection status check failed for {registration_number}: {str(e)}")
            self._log_integration_activity(
                db, 'ccpc', 'consumer_protection_status_check', 'failed',
                request_data={'registration_number': registration_number},
                error_message=str(e)
            )
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    async def submit_consumer_complaint(self, complaint_data: Dict, db: Session) -> Dict[str, Any]:
        """Submit consumer complaint to CCPC"""
        try:
            # Mock complaint submission
            mock_response = {
                'complaint_id': f'CCPC-COMP-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
                'status': 'received',
                'reference_number': f'COMP-{datetime.utcnow().strftime("%Y%m%d")}',
                'submission_date': datetime.utcnow().isoformat(),
                'complaint_category': complaint_data.get('category', 'general'),
                'complainant_reference': complaint_data.get('complainant_id'),
                'business_involved': complaint_data.get('business_name'),
                'priority_level': 'medium',
                'acknowledgment_sent': True,
                'estimated_resolution_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                'next_steps': [
                    'Complaint registered in CCPC system',
                    'Acknowledgment sent to complainant',
                    'Investigation team assigned',
                    'Business will be notified within 5 working days'
                ]
            }
            
            self._log_integration_activity(
                db, 'ccpc', 'consumer_complaint_submission', 'success',
                request_data=complaint_data,
                response_data=mock_response
            )
            
            return mock_response
            
        except Exception as e:
            logger.error(f"CCPC consumer complaint submission failed: {str(e)}")
            self._log_integration_activity(
                db, 'ccpc', 'consumer_complaint_submission', 'failed',
                request_data=complaint_data,
                error_message=str(e)
            )
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def get_market_competition_analysis(self, industry_sector: str, db: Session) -> Dict[str, Any]:
        """Get market competition analysis for industry sector"""
        try:
            mock_analysis = {
                'industry_sector': industry_sector,
                'analysis_date': datetime.utcnow().isoformat(),
                'market_overview': {
                    'total_businesses': 156,
                    'market_concentration': 'moderate',
                    'hhi_index': 0.15,  # Herfindahl-Hirschman Index
                    'dominant_players': 3,
                    'market_share_top_3': 65.2
                },
                'competition_indicators': {
                    'market_entry_barriers': 'medium',
                    'price_competition_level': 'high',
                    'product_differentiation': 'medium',
                    'innovation_activity': 'high',
                    'merger_activity': 'low'
                },
                'regulatory_concerns': [
                    {
                        'concern_type': 'price_fixing',
                        'severity': 'low',
                        'businesses_involved': 0,
                        'investigation_status': 'none'
                    },
                    {
                        'concern_type': 'market_dominance',
                        'severity': 'medium',
                        'businesses_involved': 2,
                        'investigation_status': 'ongoing'
                    }
                ],
                'consumer_welfare_metrics': {
                    'price_trend': 'stable',
                    'quality_trend': 'improving',
                    'service_satisfaction': 3.8,
                    'complaint_rate': 2.5  # per 100 consumers
                },
                'recommendations': [
                    'Monitor pricing practices of dominant players',
                    'Encourage new market entrants',
                    'Strengthen consumer protection measures',
                    'Regular market structure reviews'
                ]
            }
            
            self._log_integration_activity(
                db, 'ccpc', 'market_competition_analysis', 'success',
                request_data={'industry_sector': industry_sector},
                response_data={'businesses_analyzed': mock_analysis['market_overview']['total_businesses']}
            )
            
            return mock_analysis
            
        except Exception as e:
            logger.error(f"CCPC market competition analysis failed for {industry_sector}: {str(e)}")
            return {}
    
    async def check_price_control_compliance(self, registration_number: str, product_categories: List[str], db: Session) -> Dict[str, Any]:
        """Check price control compliance for specified products"""
        try:
            mock_compliance = {
                'business_registration_number': registration_number,
                'assessment_date': datetime.utcnow().isoformat(),
                'price_control_applicable': True,
                'controlled_products_count': len(product_categories),
                'compliance_status': 'compliant',
                'product_compliance': [],
                'violations_found': 0,
                'total_penalty_amount': 0.00,
                'last_inspection_date': '2024-06-15',
                'next_inspection_due': '2024-09-15',
                'compliance_score': 95.0,
                'recommendations': [
                    'Continue current pricing practices',
                    'Maintain proper price display',
                    'Regular price monitoring recommended'
                ]
            }
            
            # Mock product-specific compliance
            for product in product_categories:
                mock_compliance['product_compliance'].append({
                    'product_category': product,
                    'controlled': True,
                    'current_price': 25.50,
                    'maximum_allowed_price': 26.00,
                    'compliance_status': 'compliant',
                    'price_variance_percentage': -1.9,
                    'last_price_update': '2024-08-01'
                })
            
            self._log_integration_activity(
                db, 'ccpc', 'price_control_compliance_check', 'success',
                request_data={'registration_number': registration_number, 'products': product_categories},
                response_data={'compliance_status': mock_compliance['compliance_status']}
            )
            
            return mock_compliance
            
        except Exception as e:
            logger.error(f"CCPC price control compliance check failed: {str(e)}")
            return {}
    
    def _mock_business_verification(self, registration_number: str) -> Dict[str, Any]:
        """Mock business verification response"""
        if registration_number.startswith('CCPC'):
            return {
                'valid': True,
                'company_name': 'ZAMBIA TRADING COMPANY LIMITED',
                'status': 'active',
                'business_type': 'private_company',
                'registration_date': '2020-01-15'
            }
        else:
            return {
                'valid': len(registration_number) >= 6,
                'company_name': f'BUSINESS {registration_number} LIMITED',
                'status': 'active' if len(registration_number) >= 6 else 'invalid',
                'business_type': 'private_company',
                'registration_date': '2022-01-01'
            }
    
    def _mock_consumer_protection_status(self, registration_number: str) -> Dict[str, Any]:
        """Mock consumer protection status response"""
        return {
            'business_registration_number': registration_number,
            'company_name': f'BUSINESS {registration_number} LIMITED',
            'business_type': 'private_company',
            'industry_sector': 'retail',
            'business_activity_code': 'G4711',
            'registration_status': 'active',
            'consumer_complaints_count': 2,
            'resolved_complaints_count': 2,
            'pending_complaints_count': 0,
            'consumer_satisfaction_rating': 4.1,
            'market_share_percentage': 8.5,
            'anti_competitive_practices_reported': False,
            'merger_notification_status': 'not_applicable',
            'dominance_assessment_required': False,
            'price_control_applicable': True,
            'controlled_products_list': ['essential_goods', 'pharmaceuticals'],
            'price_compliance_score': 92.0,
            'pricing_violations_count': 0,
            'product_quality_certification': 'ZABS_ISO9001',
            'safety_standards_compliance': True,
            'trade_license_number': f'TL-{registration_number}',
            'trade_license_status': 'valid',
            'trade_license_expiry': '2024-12-31',
            'annual_revenue': 2500000.00,
            'number_of_employees': 45,
            'branches_count': 3,
            'operational_locations': [
                {'city': 'Lusaka', 'type': 'head_office'},
                {'city': 'Kitwe', 'type': 'branch'},
                {'city': 'Ndola', 'type': 'branch'}
            ]
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
                system_component='ccpc_service',
                timestamp=datetime.utcnow()
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log integration activity: {str(e)}")

# Global service instance
ccpc_service = CCPCIntegrationService()