from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who
    user_id = Column(UUID(as_uuid=True))
    user_email = Column(String)
    user_role = Column(String)
    
    # What
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE, VIEW
    entity_type = Column(String, nullable=False)  # risk, control, kri, etc.
    entity_id = Column(UUID(as_uuid=True))
    entity_name = Column(String)
    
    # Changes
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    # When & Where
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Additional context
    description = Column(Text)
    audit_metadata = Column(JSON)  # Renamed from 'metadata' to avoid conflict
