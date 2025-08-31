from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base


class NotificationType(str, enum.Enum):
    general = "general"
    kri_alert = "kri_alert"
    incident_alert = "incident_alert"
    aml_alert = "aml_alert"
    policy_notification = "policy_notification"
    test = "test"
    reminder = "reminder"
    update = "update"


class NotificationPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
    partial = "partial"  # Some recipients received, others failed


class NotificationHistory(Base):
    __tablename__ = "notification_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic notification info
    notification_type = Column(SQLEnum(NotificationType), default=NotificationType.general)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.normal)
    subject = Column(String(255))
    message = Column(Text)
    html_body = Column(Text, nullable=True)
    
    # Recipients
    email_recipients = Column(JSON, default=list)  # List of email addresses
    sms_recipients = Column(JSON, default=list)    # List of phone numbers
    
    # Status tracking
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.pending)
    email_status = Column(String(50), nullable=True)  # "sent", "failed", "pending"
    sms_status = Column(String(50), nullable=True)    # "sent", "failed", "pending"
    
    # Delivery details
    email_sent_count = Column(Integer, default=0)
    email_failed_count = Column(Integer, default=0)
    sms_sent_count = Column(Integer, default=0)
    sms_failed_count = Column(Integer, default=0)
    
    # Response data from services
    email_response = Column(JSON, nullable=True)
    sms_response = Column(JSON, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    
    # Additional notification details
    notification_data = Column(JSON, nullable=True)  # For storing KRI details, incident info, etc.
    
    # User tracking (optional)
    created_by = Column(String(255), nullable=True)  # Email or username of sender
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "notification_type": self.notification_type,
            "priority": self.priority,
            "subject": self.subject,
            "message": self.message[:100] + "..." if len(self.message) > 100 else self.message,
            "email_recipients": self.email_recipients,
            "sms_recipients": self.sms_recipients,
            "status": self.status,
            "email_status": self.email_status,
            "sms_status": self.sms_status,
            "email_sent_count": self.email_sent_count,
            "sms_sent_count": self.sms_sent_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "notification_data": self.notification_data
        }