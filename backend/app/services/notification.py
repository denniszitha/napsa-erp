from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime

from .email import email_service
from .sms import sms_service

logger = logging.getLogger(__name__)

class NotificationService:
    """Unified notification service for email and SMS alerts"""
    
    def __init__(self):
        self.email_service = email_service
        self.sms_service = sms_service

    async def send_notification(
        self,
        recipients: Dict[str, List[str]],  # {'email': [...], 'sms': [...]}
        subject: str,
        message: str,
        notification_type: str = 'general',
        priority: str = 'normal',
        **kwargs
    ) -> Dict[str, Any]:
        """Send unified notification via email and/or SMS"""
        
        results = {
            'email': {'success': False, 'results': []},
            'sms': {'success': False, 'results': []},
            'timestamp': datetime.now().isoformat(),
            'notification_type': notification_type,
            'priority': priority
        }
        
        try:
            # Send email notifications
            if recipients.get('email'):
                try:
                    html_body = kwargs.get('html_body')
                    await self.email_service.send_email(
                        to_emails=recipients['email'],
                        subject=subject,
                        body=message,
                        html_body=html_body
                    )
                    results['email']['success'] = True
                    results['email']['results'] = [{'status': 'sent', 'recipients': recipients['email']}]
                except Exception as e:
                    logger.error(f"Email notification failed: {str(e)}")
                    results['email']['error'] = str(e)
            
            # Send SMS notifications  
            if recipients.get('sms'):
                try:
                    # Truncate message for SMS (160 char limit)
                    sms_message = message[:160] if len(message) > 160 else message
                    sms_results = await self.sms_service.send_sms(
                        phone_numbers=recipients['sms'],
                        message=sms_message,
                        sender_id=kwargs.get('sender_id')
                    )
                    results['sms']['success'] = True
                    results['sms']['results'] = sms_results
                except Exception as e:
                    logger.error(f"SMS notification failed: {str(e)}")
                    results['sms']['error'] = str(e)
                    
        except Exception as e:
            logger.error(f"Notification service error: {str(e)}")
            results['general_error'] = str(e)
        
        return results

    async def send_kri_breach_alert(
        self,
        kri_name: str,
        current_value: float,
        threshold: float,
        status: str,
        risk_title: str,
        recipients: Dict[str, List[str]]
    ):
        """Send KRI breach alert via email and SMS"""
        
        subject = f"⚠️ KRI Alert: {kri_name} - {status.upper()}"
        
        # Email message (detailed)
        email_message = f"""
KRI BREACH NOTIFICATION

KRI Name: {kri_name}
Current Value: {current_value}
Threshold: {threshold}
Status: {status.upper()}
Associated Risk: {risk_title}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please review and take appropriate action immediately.

Best regards,
NAPSA ERM System
"""

        # HTML email body
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: {'#dc3545' if status == 'critical' else '#ffc107'};">
        ⚠️ KRI Breach Alert
    </h2>
    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
        <tr>
            <td style="padding: 12px; border: 1px solid #ddd; background: #f8f9fa;"><strong>KRI Name:</strong></td>
            <td style="padding: 12px; border: 1px solid #ddd;">{kri_name}</td>
        </tr>
        <tr>
            <td style="padding: 12px; border: 1px solid #ddd; background: #f8f9fa;"><strong>Current Value:</strong></td>
            <td style="padding: 12px; border: 1px solid #ddd;">{current_value}</td>
        </tr>
        <tr>
            <td style="padding: 12px; border: 1px solid #ddd; background: #f8f9fa;"><strong>Threshold:</strong></td>
            <td style="padding: 12px; border: 1px solid #ddd;">{threshold}</td>
        </tr>
        <tr>
            <td style="padding: 12px; border: 1px solid #ddd; background: #f8f9fa;"><strong>Status:</strong></td>
            <td style="padding: 12px; border: 1px solid #ddd; color: {'#dc3545' if status == 'critical' else '#ffc107'};">
                <strong>{status.upper()}</strong>
            </td>
        </tr>
        <tr>
            <td style="padding: 12px; border: 1px solid #ddd; background: #f8f9fa;"><strong>Associated Risk:</strong></td>
            <td style="padding: 12px; border: 1px solid #ddd;">{risk_title}</td>
        </tr>
    </table>
    
    <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p><strong>Action Required:</strong> Please review and take appropriate action immediately.</p>
    </div>
    
    <hr style="margin: 30px 0;">
    <p style="color: #6c757d; font-size: 12px;">
        This is an automated notification from NAPSA ERM System<br>
        Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S CAT')}
    </p>
</body>
</html>
"""

        # SMS message (short)
        sms_message = f"⚠️ KRI ALERT: {kri_name} - {status.upper()}\nValue: {current_value} (Limit: {threshold})\nRisk: {risk_title[:30]}...\nReview required - NAPSA ERM"
        
        return await self.send_notification(
            recipients=recipients,
            subject=subject,
            message=email_message,
            notification_type='kri_breach',
            priority='high',
            html_body=html_body,
            sms_message=sms_message
        )

    async def send_incident_alert(
        self,
        incident_title: str,
        severity: str,
        description: str,
        recipients: Dict[str, List[str]]
    ):
        """Send incident notification via email and SMS"""
        
        subject = f"🚨 Incident Alert: {incident_title} - {severity.upper()}"
        
        email_message = f"""
INCIDENT NOTIFICATION

Title: {incident_title}
Severity: {severity.upper()}
Description: {description}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Immediate attention required. Please review and respond accordingly.

Best regards,
NAPSA ERM System
"""

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #dc3545;">🚨 Incident Alert</h2>
    <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h3>{incident_title}</h3>
        <p><strong>Severity:</strong> <span style="color: #721c24;">{severity.upper()}</span></p>
        <p><strong>Description:</strong> {description}</p>
        <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S CAT')}</p>
    </div>
    <p><strong>Immediate attention required.</strong> Please review and respond accordingly.</p>
</body>
</html>
"""

        sms_message = f"🚨 INCIDENT: {incident_title}\nSeverity: {severity.upper()}\nImmediate attention required - NAPSA ERM"
        
        return await self.send_notification(
            recipients=recipients,
            subject=subject,
            message=email_message,
            notification_type='incident',
            priority='critical',
            html_body=html_body,
            sms_message=sms_message
        )

    async def send_aml_alert(
        self,
        customer_name: str,
        match_type: str,
        risk_score: float,
        match_details: str,
        recipients: Dict[str, List[str]]
    ):
        """Send AML screening alert"""
        
        subject = f"🔍 AML Alert: {match_type} Match for {customer_name}"
        
        email_message = f"""
AML SCREENING ALERT

Customer: {customer_name}
Match Type: {match_type}
Risk Score: {risk_score:.1f}%
Match Details: {match_details}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please review the match and determine appropriate action.

Best regards,
NAPSA ERM System
"""

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #856404;">🔍 AML Screening Alert</h2>
    <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p><strong>Customer:</strong> {customer_name}</p>
        <p><strong>Match Type:</strong> {match_type}</p>
        <p><strong>Risk Score:</strong> {risk_score:.1f}%</p>
        <p><strong>Match Details:</strong> {match_details}</p>
        <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S CAT')}</p>
    </div>
    <p>Please review the match and determine appropriate action.</p>
</body>
</html>
"""

        sms_message = f"🔍 AML ALERT: {customer_name}\nMatch: {match_type} (Risk: {risk_score:.1f}%)\nReview required - NAPSA ERM"
        
        return await self.send_notification(
            recipients=recipients,
            subject=subject,
            message=email_message,
            notification_type='aml_alert',
            priority='high',
            html_body=html_body,
            sms_message=sms_message
        )

    async def send_policy_notification(
        self,
        policy_title: str,
        action: str,
        approver: str,
        recipients: Dict[str, List[str]]
    ):
        """Send policy management notification"""
        
        subject = f"📋 Policy {action.title()}: {policy_title}"
        
        email_message = f"""
POLICY NOTIFICATION

Policy: {policy_title}
Action: {action.title()}
Approver: {approver}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please review the policy changes in the NAPSA ERM system.

Best regards,
NAPSA ERM System
"""

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #0d6efd;">📋 Policy Notification</h2>
    <div style="background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p><strong>Policy:</strong> {policy_title}</p>
        <p><strong>Action:</strong> {action.title()}</p>
        <p><strong>By:</strong> {approver}</p>
        <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S CAT')}</p>
    </div>
</body>
</html>
"""

        sms_message = f"📋 POLICY {action.upper()}: {policy_title}\nBy: {approver}\nReview in NAPSA ERM"
        
        return await self.send_notification(
            recipients=recipients,
            subject=subject,
            message=email_message,
            notification_type='policy',
            priority='normal',
            html_body=html_body,
            sms_message=sms_message
        )

    async def test_notification_system(self, email: str, phone: str):
        """Test both email and SMS notification systems"""
        
        recipients = {
            'email': [email] if email else [],
            'sms': [phone] if phone else []
        }
        
        return await self.send_notification(
            recipients=recipients,
            subject="NAPSA ERM - Notification System Test",
            message="This is a test notification from NAPSA ERM System. All systems are working correctly.",
            notification_type='test',
            priority='low',
            html_body="<html><body><h3>Test Notification</h3><p>This is a test notification from NAPSA ERM System. All systems are working correctly.</p></body></html>"
        )

# Global notification service instance
notification_service = NotificationService()