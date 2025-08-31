"""
SMS Notification Service for NAPSA ERM
Supports multiple SMS providers and notification templates
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import httpx
import os

logger = logging.getLogger(__name__)

class SMSProvider(str, Enum):
    TWILIO = "twilio"
    NEXMO = "nexmo"
    AWS_SNS = "aws_sns"
    AFRICA_TALKING = "africa_talking"
    CLICKATELL = "clickatell"

class SMSStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    QUEUED = "queued"

class SMSNotificationType(str, Enum):
    RCSA_DUE = "rcsa_due_notification"
    RCSA_OVERDUE = "rcsa_overdue"
    KRI_BREACH = "kri_breach"
    INCIDENT_CRITICAL = "incident_critical"
    RISK_ESCALATION = "risk_escalation"
    SYSTEM_ALERT = "system_alert"

class SMSService:
    """SMS notification service with multiple provider support"""
    
    def __init__(self):
        self.config = self._load_config()
        self.provider = self.config.get('provider', SMSProvider.TWILIO)
        self.enabled = self.config.get('enabled', True)
        self.rate_limit = self.config.get('rate_limit', 100)
        self.sent_count = 0
        self.templates = self.config.get('templates', {})
        
    def _load_config(self) -> Dict[str, Any]:
        """Load SMS configuration"""
        try:
            config_path = '/app/sms_config.json'
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading SMS config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default SMS configuration"""
        return {
            "provider": SMSProvider.TWILIO,
            "api_key": os.getenv("SMS_API_KEY", ""),
            "api_secret": os.getenv("SMS_API_SECRET", ""),
            "sender_id": "NAPSA-ERM",
            "enabled": True,
            "rate_limit": 100,
            "templates": {
                "rcsa_due_notification": "NAPSA ERM: Your RCSA assessment '{assessment_title}' is due on {due_date}. Complete at: {assessment_url}",
                "rcsa_overdue": "NAPSA ERM: URGENT - RCSA assessment '{assessment_title}' is OVERDUE. Complete immediately.",
                "kri_breach": "NAPSA ERM: ALERT - KRI '{kri_name}' breached threshold. Value: {current_value}, Threshold: {threshold}",
                "incident_critical": "NAPSA ERM: CRITICAL INCIDENT - {incident_title}. Immediate attention required.",
                "risk_escalation": "NAPSA ERM: Risk '{risk_title}' escalated. Score: {risk_score}. Review required.",
                "system_alert": "NAPSA ERM: System Alert - {alert_message}"
            }
        }
    
    async def send_sms(
        self, 
        phone_number: str, 
        message: str, 
        notification_type: SMSNotificationType = SMSNotificationType.SYSTEM_ALERT
    ) -> Dict[str, Any]:
        """Send SMS message"""
        
        if not self.enabled:
            logger.info(f"SMS service disabled, skipping message to {phone_number}")
            return {"status": "disabled", "message": "SMS service is disabled"}
        
        if self.sent_count >= self.rate_limit:
            logger.warning(f"SMS rate limit exceeded ({self.rate_limit})")
            return {"status": "rate_limited", "message": "Rate limit exceeded"}
        
        # Validate phone number
        if not self._validate_phone_number(phone_number):
            return {"status": "invalid_phone", "message": "Invalid phone number format"}
        
        try:
            # Send based on provider
            if self.provider == SMSProvider.TWILIO:
                result = await self._send_twilio(phone_number, message)
            elif self.provider == SMSProvider.AFRICA_TALKING:
                result = await self._send_africa_talking(phone_number, message)
            elif self.provider == SMSProvider.CLICKATELL:
                result = await self._send_clickatell(phone_number, message)
            else:
                result = await self._send_mock(phone_number, message)
            
            self.sent_count += 1
            
            # Log the SMS
            self._log_sms(phone_number, message, notification_type, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending SMS to {phone_number}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def send_templated_sms(
        self, 
        phone_number: str, 
        notification_type: SMSNotificationType,
        template_vars: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send SMS using predefined template"""
        
        template = self.templates.get(notification_type.value)
        if not template:
            return {"status": "no_template", "message": f"No template found for {notification_type}"}
        
        try:
            message = template.format(**template_vars)
            return await self.send_sms(phone_number, message, notification_type)
        except KeyError as e:
            return {"status": "template_error", "message": f"Missing template variable: {e}"}
    
    async def send_bulk_sms(
        self, 
        phone_numbers: List[str], 
        message: str,
        notification_type: SMSNotificationType = SMSNotificationType.SYSTEM_ALERT
    ) -> Dict[str, Any]:
        """Send SMS to multiple recipients"""
        
        results = []
        for phone_number in phone_numbers:
            result = await self.send_sms(phone_number, message, notification_type)
            results.append({
                "phone_number": phone_number,
                "result": result
            })
            
            # Small delay between messages to avoid rate limiting
            await asyncio.sleep(0.1)
        
        success_count = sum(1 for r in results if r["result"].get("status") == "sent")
        
        return {
            "total_sent": len(phone_numbers),
            "successful": success_count,
            "failed": len(phone_numbers) - success_count,
            "results": results
        }
    
    async def _send_twilio(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        try:
            # Mock Twilio implementation for now
            # In production, use actual Twilio API
            await asyncio.sleep(0.1)  # Simulate API call
            
            return {
                "status": "sent",
                "provider": "twilio",
                "message_id": f"tw_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _send_africa_talking(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via Africa's Talking"""
        try:
            # Mock implementation - replace with actual API call
            await asyncio.sleep(0.1)
            
            return {
                "status": "sent",
                "provider": "africa_talking",
                "message_id": f"at_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _send_clickatell(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via Clickatell"""
        try:
            # Mock implementation
            await asyncio.sleep(0.1)
            
            return {
                "status": "sent",
                "provider": "clickatell",
                "message_id": f"cl_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _send_mock(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Mock SMS sending for development"""
        logger.info(f"MOCK SMS to {phone_number}: {message}")
        
        return {
            "status": "sent",
            "provider": "mock",
            "message_id": f"mock_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
            "mock": True
        }
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        # Remove common formatting characters
        cleaned = phone_number.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        
        # Check if it's all digits and has reasonable length
        if not cleaned.isdigit():
            return False
        
        # Length check (7-15 digits is typical for international numbers)
        if len(cleaned) < 7 or len(cleaned) > 15:
            return False
        
        return True
    
    def _log_sms(self, phone_number: str, message: str, notification_type: SMSNotificationType, result: Dict[str, Any]):
        """Log SMS sending attempt"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "phone_number": phone_number[:3] + "****" + phone_number[-3:],  # Mask phone number
            "message_length": len(message),
            "notification_type": notification_type.value,
            "provider": self.provider.value,
            "status": result.get("status"),
            "message_id": result.get("message_id")
        }
        
        logger.info(f"SMS Log: {log_entry}")

# Notification helper functions
class SMSNotificationHelper:
    """Helper class for common SMS notification scenarios"""
    
    def __init__(self, sms_service: SMSService):
        self.sms_service = sms_service
    
    async def notify_rcsa_due(self, user_phone: str, assessment_title: str, due_date: str, assessment_url: str):
        """Notify user about RCSA due date"""
        template_vars = {
            "assessment_title": assessment_title,
            "due_date": due_date,
            "assessment_url": assessment_url
        }
        
        return await self.sms_service.send_templated_sms(
            user_phone, 
            SMSNotificationType.RCSA_DUE, 
            template_vars
        )
    
    async def notify_kri_breach(self, user_phone: str, kri_name: str, current_value: float, threshold: float):
        """Notify user about KRI threshold breach"""
        template_vars = {
            "kri_name": kri_name,
            "current_value": current_value,
            "threshold": threshold
        }
        
        return await self.sms_service.send_templated_sms(
            user_phone,
            SMSNotificationType.KRI_BREACH,
            template_vars
        )
    
    async def notify_critical_incident(self, user_phones: List[str], incident_title: str):
        """Notify multiple users about critical incident"""
        template_vars = {"incident_title": incident_title}
        
        results = []
        for phone in user_phones:
            result = await self.sms_service.send_templated_sms(
                phone,
                SMSNotificationType.INCIDENT_CRITICAL,
                template_vars
            )
            results.append({"phone": phone, "result": result})
        
        return results

# Global SMS service instance
sms_service = SMSService()
notification_helper = SMSNotificationHelper(sms_service)

# Convenience functions
async def send_sms(phone_number: str, message: str) -> Dict[str, Any]:
    """Quick SMS sending function"""
    return await sms_service.send_sms(phone_number, message)

async def send_rcsa_due_notification(user_phone: str, assessment_title: str, due_date: str, assessment_url: str):
    """Send RCSA due notification"""
    return await notification_helper.notify_rcsa_due(user_phone, assessment_title, due_date, assessment_url)

async def send_kri_breach_alert(user_phone: str, kri_name: str, current_value: float, threshold: float):
    """Send KRI breach alert"""
    return await notification_helper.notify_kri_breach(user_phone, kri_name, current_value, threshold)

async def send_critical_incident_alert(user_phones: List[str], incident_title: str):
    """Send critical incident alert to multiple users"""
    return await notification_helper.notify_critical_incident(user_phones, incident_title)