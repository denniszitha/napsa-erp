from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json
from enum import Enum

from app.models.audit import AuditLog
from app.models.user import User

def json_serializer(obj):
    """JSON serializer for datetime and enum objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Enum):
        return obj.value
    return str(obj)

class AuditService:
    @staticmethod
    async def log_action(
        db: Session,
        user: User,
        action: str,
        entity_type: str,
        entity_id: str,
        entity_name: str = None,
        old_values: Dict[str, Any] = None,
        new_values: Dict[str, Any] = None,
        description: str = None,
        ip_address: str = None,
        user_agent: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Log an audit entry"""
        
        # Serialize values to handle datetime and enum objects
        def serialize_values(values):
            if values is None:
                return None
            return {k: json_serializer(v) for k, v in values.items()}
        
        audit_entry = AuditLog(
            user_id=user.id,
            user_email=user.email,
            user_role=user.role.value,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            old_values=serialize_values(old_values),
            new_values=serialize_values(new_values),
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            audit_metadata=serialize_values(metadata),
            timestamp=datetime.now(timezone.utc)
        )
        
        db.add(audit_entry)
        db.commit()
        
        return audit_entry
    
    @staticmethod
    def get_entity_history(
        db: Session,
        entity_type: str,
        entity_id: str,
        limit: int = 50
    ):
        """Get audit history for a specific entity"""
        return db.query(AuditLog).filter(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()

audit_service = AuditService()
