import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging
from jinja2 import Template

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = getattr(settings, 'SMTP_HOST', None)
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_user = getattr(settings, 'SMTP_USER', None)
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        self.from_email = getattr(settings, 'EMAILS_FROM_EMAIL', 'noreply@napsa.co.zm')

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ):
        """Send email to recipients"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)

            # Add plain text part
            part1 = MIMEText(body, 'plain')
            msg.attach(part1)

            # Add HTML part if provided
            if html_body:
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)

            # Send email
            if self.smtp_user and self.smtp_password and self.smtp_host:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                logger.info(f"Email sent successfully to {to_emails}")
            else:
                logger.warning("Email not sent - SMTP credentials not configured")
                
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")

    async def send_kri_breach_notification(
        self,
        kri_name: str,
        current_value: float,
        threshold: float,
        status: str,
        risk_title: str,
        recipients: List[str]
    ):
        """Send KRI breach notification"""
        subject = f"⚠️ KRI Alert: {kri_name} - {status.upper()}"
        
        body = f"""
KRI BREACH NOTIFICATION

KRI Name: {kri_name}
Current Value: {current_value}
Threshold: {threshold}
Status: {status.upper()}
Associated Risk: {risk_title}

Please review and take appropriate action.

Best regards,
NAPSA ERM System
"""

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: {'#ff6b6b' if status == 'critical' else '#ffd93d'};">
        ⚠️ KRI Breach Alert
    </h2>
    <table style="border-collapse: collapse; width: 100%;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>KRI Name:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{kri_name}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Current Value:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{current_value}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Threshold:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{threshold}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Status:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd; color: {'#ff6b6b' if status == 'critical' else '#ffd93d'};">
                <strong>{status.upper()}</strong>
            </td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Associated Risk:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{risk_title}</td>
        </tr>
    </table>
    <p>Please review and take appropriate action.</p>
    <hr>
    <p style="color: #666; font-size: 12px;">
        This is an automated notification from NAPSA ERM System
    </p>
</body>
</html>
"""
        
        await self.send_email(recipients, subject, body, html_body)

email_service = EmailService()
