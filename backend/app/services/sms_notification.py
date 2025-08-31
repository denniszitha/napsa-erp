"""
SMS Notification Service
Integrates with multiple SMS providers for NAPSA notifications
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from enum import Enum

logger = logging.getLogger(__name__)

class SMSProvider(str, Enum):
    TWILIO = "twilio"
    AFRICASTALKING = "africastalking"
    ZAMTEL = "zamtel"
    MTN = "mtn"
    AIRTEL = "airtel"

class SMSNotificationService:
    """
    Multi-provider SMS notification service for NAPSA
    Supports Zambian telecom providers and international services
    """
    
    def __init__(self):
        # Load configuration from environment
        self.provider = os.getenv("SMS_PROVIDER", SMSProvider.AFRICASTALKING)
        self.api_key = os.getenv("SMS_API_KEY", "")
        self.api_secret = os.getenv("SMS_API_SECRET", "")
        self.sender_id = os.getenv("SMS_SENDER_ID", "NAPSA-ERM")
        self.base_url = self._get_base_url()
        
        # Zambian phone number prefixes
        self.zambian_prefixes = {
            "mtn": ["096", "076"],
            "airtel": ["097", "077"],
            "zamtel": ["095", "075"]
        }
    
    def _get_base_url(self) -> str:
        """Get base URL for SMS provider"""
        urls = {
            SMSProvider.TWILIO: "https://api.twilio.com/2010-04-01",
            SMSProvider.AFRICASTALKING: "https://api.africastalking.com/version1",
            SMSProvider.ZAMTEL: "https://api.zamtel.co.zm/sms/v1",
            SMSProvider.MTN: "https://api.mtn.co.zm/sms/v1",
            SMSProvider.AIRTEL: "https://api.airtel.co.zm/sms/v1"
        }
        return urls.get(self.provider, "")
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number to international format"""
        # Remove spaces and special characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Add Zambian country code if needed
        if phone.startswith("0"):
            phone = "260" + phone[1:]
        elif not phone.startswith("260"):
            phone = "260" + phone
        
        return "+" + phone
    
    def _get_network_provider(self, phone: str) -> str:
        """Determine network provider from phone number"""
        if phone.startswith("+260"):
            prefix = phone[4:7]
            for provider, prefixes in self.zambian_prefixes.items():
                if prefix in prefixes:
                    return provider
        return "unknown"
    
    async def send_sms(
        self,
        to: str,
        message: str,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Send SMS to a single recipient
        
        Args:
            to: Recipient phone number
            message: SMS message content (max 160 chars for single SMS)
            priority: Message priority (normal, high, urgent)
        
        Returns:
            Response with delivery status
        """
        formatted_phone = self._format_phone_number(to)
        
        try:
            if self.provider == SMSProvider.TWILIO:
                return await self._send_via_twilio(formatted_phone, message)
            elif self.provider == SMSProvider.AFRICASTALKING:
                return await self._send_via_africastalking(formatted_phone, message)
            elif self.provider in [SMSProvider.ZAMTEL, SMSProvider.MTN, SMSProvider.AIRTEL]:
                return await self._send_via_local_provider(formatted_phone, message)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported provider: {self.provider}"
                }
        except Exception as e:
            logger.error(f"SMS send failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_bulk_sms(
        self,
        recipients: List[str],
        message: str,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Send SMS to multiple recipients
        
        Args:
            recipients: List of phone numbers
            message: SMS message content
            batch_size: Number of messages per batch
        
        Returns:
            Bulk send report
        """
        results = {
            "total": len(recipients),
            "sent": 0,
            "failed": 0,
            "details": []
        }
        
        # Process in batches
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            
            for phone in batch:
                result = await self.send_sms(phone, message)
                
                if result.get("success"):
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                
                results["details"].append({
                    "phone": phone,
                    "status": "sent" if result.get("success") else "failed",
                    "error": result.get("error")
                })
        
        return results
    
    async def _send_via_twilio(self, to: str, message: str) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/Accounts/{self.api_key}/Messages.json",
                auth=(self.api_key, self.api_secret),
                data={
                    "From": self.sender_id,
                    "To": to,
                    "Body": message
                }
            )
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "message_id": response.json().get("sid"),
                    "status": "sent"
                }
            else:
                return {
                    "success": False,
                    "error": response.json().get("message", "Failed to send SMS")
                }
    
    async def _send_via_africastalking(self, to: str, message: str) -> Dict[str, Any]:
        """Send SMS via Africa's Talking"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messaging",
                headers={
                    "apiKey": self.api_key,
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "username": self.api_secret,
                    "to": to,
                    "message": message,
                    "from": self.sender_id
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                recipients = data.get("SMSMessageData", {}).get("Recipients", [])
                
                if recipients and recipients[0].get("status") == "Success":
                    return {
                        "success": True,
                        "message_id": recipients[0].get("messageId"),
                        "status": "sent"
                    }
            
            return {
                "success": False,
                "error": "Failed to send SMS via Africa's Talking"
            }
    
    async def _send_via_local_provider(self, to: str, message: str) -> Dict[str, Any]:
        """Send SMS via local Zambian provider"""
        # Determine the provider based on phone number
        network = self._get_network_provider(to)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "sender": self.sender_id,
            "recipient": to,
            "message": message,
            "type": "text"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/send",
                headers=headers,
                json=payload
            )
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "message_id": response.json().get("message_id"),
                    "status": "sent",
                    "network": network
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to send via {network}",
                    "status_code": response.status_code
                }
    
    async def send_risk_alert(
        self,
        phone: str,
        risk_id: str,
        risk_title: str,
        risk_level: str
    ) -> Dict[str, Any]:
        """Send risk alert SMS"""
        message = f"NAPSA ALERT: {risk_level.upper()} risk detected - {risk_title[:50]}. Please review risk {risk_id} in the ERM system."
        
        # Truncate to 160 chars
        if len(message) > 160:
            message = message[:157] + "..."
        
        return await self.send_sms(phone, message, priority="high")
    
    async def send_kri_breach_alert(
        self,
        phone: str,
        kri_name: str,
        current_value: float,
        threshold: float
    ) -> Dict[str, Any]:
        """Send KRI threshold breach alert"""
        message = f"NAPSA KRI ALERT: {kri_name} has breached threshold. Current: {current_value:.2f}, Threshold: {threshold:.2f}. Immediate action required."
        
        if len(message) > 160:
            message = f"NAPSA KRI: {kri_name[:30]} breached. Value: {current_value:.1f}, Limit: {threshold:.1f}. Action required."
        
        return await self.send_sms(phone, message, priority="urgent")
    
    async def send_incident_notification(
        self,
        phone: str,
        incident_id: str,
        incident_title: str,
        severity: str
    ) -> Dict[str, Any]:
        """Send incident notification SMS"""
        message = f"NAPSA INCIDENT: {severity.upper()} - {incident_title[:40]}. ID: {incident_id}. Please respond immediately."
        
        return await self.send_sms(phone, message, priority="urgent" if severity == "critical" else "high")
    
    async def send_assessment_reminder(
        self,
        phone: str,
        assessment_type: str,
        due_date: datetime
    ) -> Dict[str, Any]:
        """Send assessment reminder SMS"""
        due_str = due_date.strftime("%d/%m/%Y")
        message = f"NAPSA REMINDER: {assessment_type} assessment due on {due_str}. Please complete in the ERM system."
        
        return await self.send_sms(phone, message, priority="normal")
    
    async def send_otp(
        self,
        phone: str,
        otp_code: str
    ) -> Dict[str, Any]:
        """Send OTP for two-factor authentication"""
        message = f"NAPSA ERM: Your verification code is {otp_code}. Valid for 5 minutes. Do not share this code."
        
        return await self.send_sms(phone, message, priority="high")
    
    def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Check SMS delivery status"""
        # Implementation depends on provider
        # This is a placeholder
        return {
            "message_id": message_id,
            "status": "delivered",
            "delivered_at": datetime.utcnow().isoformat()
        }

# Singleton instance
sms_service = SMSNotificationService()

async def send_sms_notification(
    to: str,
    message: str,
    notification_type: str = "general"
) -> Dict[str, Any]:
    """
    Convenience function to send SMS notifications
    
    Args:
        to: Recipient phone number
        message: Message content
        notification_type: Type of notification (general, risk, incident, kri, assessment)
    
    Returns:
        Send status
    """
    return await sms_service.send_sms(to, message)