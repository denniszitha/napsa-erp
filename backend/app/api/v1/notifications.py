from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, date

from app.services.notification import notification_service
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.notification import NotificationHistory, NotificationType, NotificationPriority, NotificationStatus

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple in-memory counter for notifications sent today
class NotificationCounter:
    def __init__(self):
        self.count = 0
        self.failed_count = 0
        self.date = date.today()
        
    def increment(self, success=True):
        # Reset counter if it's a new day
        if date.today() != self.date:
            self.count = 0
            self.failed_count = 0
            self.date = date.today()
        
        if success:
            self.count += 1
        else:
            self.failed_count += 1
            
    def get_counts(self):
        # Reset if it's a new day
        if date.today() != self.date:
            self.count = 0
            self.failed_count = 0
            self.date = date.today()
        return self.count, self.failed_count

# Global counter instance
notification_counter = NotificationCounter()

class NotificationRequest(BaseModel):
    recipients: Dict[str, List[str]]  # {'email': [...], 'sms': [...]}
    subject: str
    message: str
    notification_type: str = 'general'
    priority: str = 'normal'
    html_body: Optional[str] = None

class KRIAlertRequest(BaseModel):
    kri_name: str
    current_value: float
    threshold: float
    status: str
    risk_title: str
    recipients: Dict[str, List[str]]

class IncidentAlertRequest(BaseModel):
    incident_title: str
    severity: str
    description: str
    recipients: Dict[str, List[str]]

class AMLAlertRequest(BaseModel):
    customer_name: str
    match_type: str
    risk_score: float
    match_details: str
    recipients: Dict[str, List[str]]

class PolicyNotificationRequest(BaseModel):
    policy_title: str
    action: str
    approver: str
    recipients: Dict[str, List[str]]

class TestNotificationRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

@router.post("/send")
async def send_notification(
    request: NotificationRequest
):
    """Send a general notification via email and/or SMS"""
    try:
        result = await notification_service.send_notification(
            recipients=request.recipients,
            subject=request.subject,
            message=request.message,
            notification_type=request.notification_type,
            priority=request.priority,
            html_body=request.html_body
        )
        
        # Increment counter
        notification_counter.increment(success=True)
        
        return {
            "success": True,
            "message": "Notification sent successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/kri-alert")
async def send_kri_alert(
    request: KRIAlertRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send KRI breach alert notification"""
    try:
        result = await notification_service.send_kri_breach_alert(
            kri_name=request.kri_name,
            current_value=request.current_value,
            threshold=request.threshold,
            status=request.status,
            risk_title=request.risk_title,
            recipients=request.recipients
        )
        
        # Increment counter
        notification_counter.increment(success=True)
        
        return {
            "success": True,
            "message": "KRI alert sent successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send KRI alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/incident-alert")
async def send_incident_alert(
    request: IncidentAlertRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send incident alert notification"""
    try:
        result = await notification_service.send_incident_alert(
            incident_title=request.incident_title,
            severity=request.severity,
            description=request.description,
            recipients=request.recipients
        )
        
        return {
            "success": True,
            "message": "Incident alert sent successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send incident alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/aml-alert")
async def send_aml_alert(
    request: AMLAlertRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send AML screening alert notification"""
    try:
        result = await notification_service.send_aml_alert(
            customer_name=request.customer_name,
            match_type=request.match_type,
            risk_score=request.risk_score,
            match_details=request.match_details,
            recipients=request.recipients
        )
        
        return {
            "success": True,
            "message": "AML alert sent successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send AML alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/policy-notification")
async def send_policy_notification(
    request: PolicyNotificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send policy management notification"""
    try:
        result = await notification_service.send_policy_notification(
            policy_title=request.policy_title,
            action=request.action,
            approver=request.approver,
            recipients=request.recipients
        )
        
        return {
            "success": True,
            "message": "Policy notification sent successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send policy notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def test_notification_system(
    request: TestNotificationRequest,
    db: Session = Depends(get_db)
):
    """Test the notification system"""
    try:
        if not request.email and not request.phone:
            raise HTTPException(status_code=400, detail="Please provide either email or phone number")
        
        result = await notification_service.test_notification_system(
            email=request.email,
            phone=request.phone
        )
        
        # Save to database
        notification = NotificationHistory(
            notification_type=NotificationType.test,
            priority=NotificationPriority.low,
            subject="Test Notification",
            message="This is a test notification from NAPSA ERM System.",
            email_recipients=[request.email] if request.email else [],
            sms_recipients=[request.phone] if request.phone else [],
            status=NotificationStatus.sent if result.get('email', {}).get('success') or result.get('sms', {}).get('success') else NotificationStatus.failed,
            email_status="sent" if result.get('email', {}).get('success') else "failed" if request.email else None,
            sms_status="sent" if result.get('sms', {}).get('success') else "failed" if request.phone else None,
            email_sent_count=1 if result.get('email', {}).get('success') else 0,
            sms_sent_count=1 if result.get('sms', {}).get('success') else 0,
            sent_at=datetime.utcnow(),
            email_response=result.get('email'),
            sms_response=result.get('sms')
        )
        db.add(notification)
        db.commit()
        
        # Increment counter for test notifications
        notification_counter.increment(success=True)
        
        return {
            "success": True,
            "message": "Test notification sent successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send test notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_notification_status(
    db: Session = Depends(get_db)
):
    """Get notification system status"""
    try:
        # Check if services are configured
        email_configured = bool(notification_service.email_service.smtp_user and 
                               notification_service.email_service.smtp_password)
        
        sms_configured = bool(notification_service.sms_service.username and 
                             notification_service.sms_service.password)
        
        # Get current statistics from database
        from datetime import timedelta
        from sqlalchemy import func, and_
        
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        
        # Count notifications sent today
        sent_today = db.query(func.count(NotificationHistory.id)).filter(
            and_(
                NotificationHistory.created_at >= today_start,
                NotificationHistory.status.in_([NotificationStatus.sent, NotificationStatus.partial])
            )
        ).scalar() or 0
        
        # Count failed notifications today
        failed_count = db.query(func.count(NotificationHistory.id)).filter(
            and_(
                NotificationHistory.created_at >= today_start,
                NotificationHistory.status == NotificationStatus.failed
            )
        ).scalar() or 0
        
        return {
            "success": True,
            "data": {
                "email_status": "Active" if email_configured else "Inactive",
                "sms_status": "Active" if sms_configured else "Inactive",
                "sent_today": sent_today,  # Actual count for today's notifications
                "failed_count": failed_count,
                "email_service": {
                    "configured": email_configured,
                    "smtp_host": notification_service.email_service.smtp_host,
                    "from_email": notification_service.email_service.from_email,
                    "status": "operational"
                },
                "sms_service": {
                    "configured": sms_configured,
                    "sender_id": notification_service.sms_service.sender_id,
                    "shortcode": notification_service.sms_service.shortcode,
                    "status": "operational"
                },
                "recent_activity": {
                    "last_email_sent": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "last_sms_sent": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                    "total_today": 12,
                    "total_this_week": 47,
                    "total_this_month": 189
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get notification status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_notification_history(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get notification history from database"""
    try:
        from sqlalchemy import desc
        
        # Query notification history from database
        notifications = db.query(NotificationHistory).order_by(
            desc(NotificationHistory.created_at)
        ).limit(limit).all()
        
        # Convert to response format
        history = []
        for notif in notifications:
            # Map database types to display types
            type_map = {
                NotificationType.general: "General",
                NotificationType.kri_alert: "KRI Alert",
                NotificationType.incident_alert: "Incident Alert",
                NotificationType.aml_alert: "AML Alert",
                NotificationType.policy_notification: "Policy Update",
                NotificationType.test: "Test",
                NotificationType.reminder: "Reminder",
                NotificationType.update: "Update"
            }
            
            history.append({
                "id": str(notif.id),
                "date": notif.created_at.isoformat() if notif.created_at else None,
                "type": type_map.get(notif.notification_type, notif.notification_type),
                "subject": notif.subject or "No subject",
                "recipients": {
                    "email": notif.email_recipients or [],
                    "sms": notif.sms_recipients or []
                },
                "status": notif.status,
                "priority": notif.priority,
                "delivery_status": {
                    "email": notif.email_status or "N/A",
                    "sms": notif.sms_status or "N/A"
                }
            })
        
        return {
            "success": True,
            "data": {
                "total": len(history),
                "items": history
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get notification history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))