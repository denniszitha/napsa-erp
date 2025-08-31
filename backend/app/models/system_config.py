"""
System Configuration Model
For runtime configuration management
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class SystemConfiguration(Base):
    """System configuration settings"""
    __tablename__ = "system_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(255), unique=True, nullable=False, index=True)
    config_value = Column(Text)
    config_type = Column(String(50))  # 'string', 'integer', 'boolean', 'json', 'float'
    category = Column(String(100))  # 'Security', 'Risk Management', 'Notifications', etc.
    display_name = Column(String(255))
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)  # Encrypt if True
    validation_rules = Column(JSON)  # JSON schema for validation
    default_value = Column(Text)
    is_active = Column(Boolean, default=True)
    requires_restart = Column(Boolean, default=False)
    
    # Audit fields
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    
    @property
    def typed_value(self):
        """Return config value in its proper type"""
        if self.config_type == 'integer':
            return int(self.config_value) if self.config_value else None
        elif self.config_type == 'float':
            return float(self.config_value) if self.config_value else None
        elif self.config_type == 'boolean':
            return self.config_value.lower() in ('true', '1', 'yes') if self.config_value else False
        elif self.config_type == 'json':
            import json
            return json.loads(self.config_value) if self.config_value else None
        else:
            return self.config_value