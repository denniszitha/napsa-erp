import requests
import urllib.parse
from typing import List, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        self.api_url = "https://www.cloudservicezm.com/smsservice/httpapi"
        self.username = getattr(settings, 'SMS_USERNAME', 'Chileshe')
        self.password = getattr(settings, 'SMS_PASSWORD', 'Chileshe1')
        self.shortcode = getattr(settings, 'SMS_SHORTCODE', '388')
        self.sender_id = getattr(settings, 'SMS_SENDER_ID', 'ONTECH')
        self.api_key = getattr(settings, 'SMS_API_KEY', 'use_preshared')

    async def send_sms(
        self,
        phone_numbers: List[str],
        message: str,
        sender_id: Optional[str] = None
    ):
        """Send SMS to phone numbers"""
        try:
            sender = sender_id or self.sender_id
            
            results = []
            for phone in phone_numbers:
                # Clean phone number (remove spaces, ensure format)
                clean_phone = phone.replace(' ', '').replace('-', '')
                if not clean_phone.startswith('260'):
                    if clean_phone.startswith('0'):
                        clean_phone = '260' + clean_phone[1:]
                    elif len(clean_phone) == 9:
                        clean_phone = '260' + clean_phone
                
                # Prepare parameters
                params = {
                    'username': self.username,
                    'password': self.password,
                    'msg': message,
                    'shortcode': self.shortcode,
                    'sender_id': sender,
                    'phone': clean_phone,
                    'api_key': self.api_key
                }
                
                # Send SMS
                response = requests.get(self.api_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"SMS sent successfully to {clean_phone}")
                    results.append({
                        'phone': clean_phone,
                        'status': 'success',
                        'response': response.text
                    })
                else:
                    logger.error(f"Failed to send SMS to {clean_phone}: {response.status_code}")
                    results.append({
                        'phone': clean_phone,
                        'status': 'failed',
                        'error': f"HTTP {response.status_code}: {response.text}"
                    })
                    
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return [{'status': 'error', 'error': str(e)}]
            
        return results

    async def send_kri_breach_sms(
        self,
        kri_name: str,
        current_value: float,
        threshold: float,
        status: str,
        risk_title: str,
        phone_numbers: List[str]
    ):
        """Send KRI breach notification via SMS"""
        message = f"⚠️ KRI ALERT: {kri_name} - {status.upper()}\n"
        message += f"Value: {current_value} (Threshold: {threshold})\n"
        message += f"Risk: {risk_title}\n"
        message += "Review required - NAPSA ERM"
        
        return await self.send_sms(phone_numbers, message)

    async def send_incident_notification(
        self,
        incident_title: str,
        severity: str,
        phone_numbers: List[str]
    ):
        """Send incident notification via SMS"""
        message = f"🚨 INCIDENT: {incident_title}\n"
        message += f"Severity: {severity.upper()}\n"
        message += "Immediate attention required - NAPSA ERM"
        
        return await self.send_sms(phone_numbers, message)

    async def send_policy_approval_sms(
        self,
        policy_title: str,
        action: str,
        phone_numbers: List[str]
    ):
        """Send policy approval notification via SMS"""
        message = f"📋 POLICY {action.upper()}: {policy_title}\n"
        message += "Please review in NAPSA ERM system"
        
        return await self.send_sms(phone_numbers, message)

    async def send_aml_alert_sms(
        self,
        customer_name: str,
        match_type: str,
        risk_score: float,
        phone_numbers: List[str]
    ):
        """Send AML screening alert via SMS"""
        message = f"🔍 AML ALERT: {customer_name}\n"
        message += f"Match: {match_type} (Risk: {risk_score:.1f}%)\n"
        message += "Review required - NAPSA ERM"
        
        return await self.send_sms(phone_numbers, message)

    async def send_compliance_reminder(
        self,
        framework: str,
        due_date: str,
        phone_numbers: List[str]
    ):
        """Send compliance deadline reminder via SMS"""
        message = f"📅 COMPLIANCE REMINDER: {framework}\n"
        message += f"Due: {due_date}\n"
        message += "Action required - NAPSA ERM"
        
        return await self.send_sms(phone_numbers, message)

    async def test_sms_service(self, test_phone: str):
        """Test SMS service with a single message"""
        message = "Test message from NAPSA ERM System. SMS service is working correctly."
        result = await self.send_sms([test_phone], message)
        return result

sms_service = SMSService()