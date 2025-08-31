"""
SMS Notification API endpoints
Handles SMS notifications for NAPSA ERM system
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.notification import NotificationHistory
from app.services.sms_notification import sms_service
from pydantic import BaseModel

router = APIRouter(prefix="/sms", tags=["SMS Notifications"])

class SMSRequest(BaseModel):
    to: str
    message: str
    priority: str = "normal"

class BulkSMSRequest(BaseModel):
    recipients: List[str]
    message: str
    batch_size: int = 100

class RiskAlertSMS(BaseModel):
    phone: str
    risk_id: str
    risk_title: str
    risk_level: str

class KRIAlertSMS(BaseModel):
    phone: str
    kri_name: str
    current_value: float
    threshold: float

class IncidentAlertSMS(BaseModel):
    phone: str
    incident_id: str
    incident_title: str
    severity: str

@router.post("/send", response_model=Dict[str, Any])
async def send_sms(
    request: SMSRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send single SMS notification"""
    
    # Send SMS
    result = await sms_service.send_sms(
        to=request.to,
        message=request.message,
        priority=request.priority
    )
    
    # Log notification in background
    if result.get("success"):
        background_tasks.add_task(
            log_sms_notification,
            db=db,
            user_id=current_user.id,
            recipient=request.to,
            message=request.message,
            status="sent",
            message_id=result.get("message_id")
        )
    
    return result

@router.post("/send-bulk", response_model=Dict[str, Any])
async def send_bulk_sms(
    request: BulkSMSRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send bulk SMS notifications"""
    
    # Validate recipients
    if len(request.recipients) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Maximum 1000 recipients allowed per request"
        )
    
    # Send bulk SMS
    result = await sms_service.send_bulk_sms(
        recipients=request.recipients,
        message=request.message,
        batch_size=request.batch_size
    )
    
    # Log in background
    background_tasks.add_task(
        log_bulk_sms,
        db=db,
        user_id=current_user.id,
        result=result
    )
    
    return result

@router.post("/risk-alert", response_model=Dict[str, Any])
async def send_risk_alert(
    request: RiskAlertSMS,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send risk alert SMS"""
    
    result = await sms_service.send_risk_alert(
        phone=request.phone,
        risk_id=request.risk_id,
        risk_title=request.risk_title,
        risk_level=request.risk_level
    )
    
    # Log notification
    log_sms_notification(
        db=db,
        user_id=current_user.id,
        recipient=request.phone,
        message=f"Risk Alert: {request.risk_title}",
        status="sent" if result.get("success") else "failed",
        notification_type="risk_alert"
    )
    
    return result

@router.post("/kri-breach-alert", response_model=Dict[str, Any])
async def send_kri_breach_alert(
    request: KRIAlertSMS,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send KRI threshold breach alert SMS"""
    
    result = await sms_service.send_kri_breach_alert(
        phone=request.phone,
        kri_name=request.kri_name,
        current_value=request.current_value,
        threshold=request.threshold
    )
    
    # Log notification
    log_sms_notification(
        db=db,
        user_id=current_user.id,
        recipient=request.phone,
        message=f"KRI Alert: {request.kri_name}",
        status="sent" if result.get("success") else "failed",
        notification_type="kri_breach"
    )
    
    return result

@router.post("/incident-alert", response_model=Dict[str, Any])
async def send_incident_alert(
    request: IncidentAlertSMS,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send incident notification SMS"""
    
    result = await sms_service.send_incident_notification(
        phone=request.phone,
        incident_id=request.incident_id,
        incident_title=request.incident_title,
        severity=request.severity
    )
    
    # Log notification
    log_sms_notification(
        db=db,
        user_id=current_user.id,
        recipient=request.phone,
        message=f"Incident Alert: {request.incident_title}",
        status="sent" if result.get("success") else "failed",
        notification_type="incident"
    )
    
    return result

@router.get("/history", response_model=List[Dict[str, Any]])
def get_sms_history(
    skip: int = 0,
    limit: int = 100,
    phone: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get SMS notification history"""
    
    query = db.query(NotificationHistory).filter(
        NotificationHistory.channel == "sms"
    )
    
    if phone:
        query = query.filter(NotificationHistory.recipient == phone)
    if status:
        query = query.filter(NotificationHistory.status == status)
    
    notifications = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": n.id,
            "recipient": n.recipient,
            "message": n.message,
            "status": n.status,
            "sent_at": n.created_at.isoformat() if n.created_at else None,
            "notification_type": n.notification_type
        }
        for n in notifications
    ]

@router.get("/statistics", response_model=Dict[str, Any])
def get_sms_statistics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get SMS notification statistics"""
    
    query = db.query(NotificationHistory).filter(
        NotificationHistory.channel == "sms"
    )
    
    if date_from:
        query = query.filter(NotificationHistory.created_at >= date_from)
    if date_to:
        query = query.filter(NotificationHistory.created_at <= date_to)
    
    total = query.count()
    sent = query.filter(NotificationHistory.status == "sent").count()
    failed = query.filter(NotificationHistory.status == "failed").count()
    
    # Get statistics by type
    risk_alerts = query.filter(NotificationHistory.notification_type == "risk_alert").count()
    kri_alerts = query.filter(NotificationHistory.notification_type == "kri_breach").count()
    incident_alerts = query.filter(NotificationHistory.notification_type == "incident").count()
    
    return {
        "total_messages": total,
        "sent": sent,
        "failed": failed,
        "success_rate": (sent / total * 100) if total > 0 else 0,
        "by_type": {
            "risk_alerts": risk_alerts,
            "kri_alerts": kri_alerts,
            "incident_alerts": incident_alerts,
            "general": total - (risk_alerts + kri_alerts + incident_alerts)
        }
    }

@router.post("/test", response_model=Dict[str, Any])
async def test_sms_service(
    phone: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test SMS service configuration"""
    
    test_message = f"NAPSA ERM Test: SMS service is configured correctly. Time: {datetime.utcnow().strftime('%H:%M')}"
    
    result = await sms_service.send_sms(
        to=phone,
        message=test_message,
        priority="normal"
    )
    
    return {
        "test_successful": result.get("success"),
        "provider": sms_service.provider,
        "message": "SMS test completed",
        "details": result
    }

# Helper functions
def log_sms_notification(
    db: Session,
    user_id: str,
    recipient: str,
    message: str,
    status: str,
    notification_type: str = "general",
    message_id: str = None
):
    """Log SMS notification to database"""
    try:
        notification = NotificationHistory(
            user_id=user_id,
            channel="sms",
            recipient=recipient,
            message=message,
            status=status,
            notification_type=notification_type,
            external_id=message_id,
            created_at=datetime.utcnow()
        )
        db.add(notification)
        db.commit()
    except Exception as e:
        # Log error but don't fail the main operation
        print(f"Failed to log SMS notification: {e}")

def log_bulk_sms(
    db: Session,
    user_id: str,
    result: Dict[str, Any]
):
    """Log bulk SMS results"""
    try:
        for detail in result.get("details", []):
            log_sms_notification(
                db=db,
                user_id=user_id,
                recipient=detail.get("phone"),
                message="Bulk SMS",
                status=detail.get("status"),
                notification_type="bulk"
            )
    except Exception as e:
        print(f"Failed to log bulk SMS: {e}")