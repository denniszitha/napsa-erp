"""
History and Audit Trail Models
For detailed change tracking and user activity monitoring
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RiskHistory(Base):
    """Detailed risk change history"""
    __tablename__ = "risk_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    risk_id = Column(Integer, ForeignKey("risks.id"), nullable=False, index=True)
    change_type = Column(String(50), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE', 'STATUS_CHANGE'
    field_name = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    change_reason = Column(Text)
    change_description = Column(Text)
    
    # Tracking fields
    changed_by_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    risk = relationship("Risk")
    changed_by = relationship("User")


class UserLoginHistory(Base):
    """User login/logout history for security audit"""
    __tablename__ = "user_login_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    login_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    logout_at = Column(DateTime(timezone=True))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    location = Column(String(255))  # Geo-location if available
    successful = Column(Boolean, default=True)
    failure_reason = Column(String(255))
    session_id = Column(String(255))
    
    # Relationships
    user = relationship("User", back_populates="login_histories")


class TreatmentPlanUpdate(Base):
    """Progress updates for treatment plans"""
    __tablename__ = "treatment_plan_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    treatment_plan_id = Column(Integer, nullable=False)  # FK to be added when treatment_plans table exists
    update_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), nullable=False)  # TreatmentUpdateStatus enum
    progress_percentage = Column(Integer)
    activities_completed = Column(Text)
    challenges_encountered = Column(Text)
    next_steps = Column(Text)
    current_risk_level = Column(String(50))
    risk_change_notes = Column(Text)
    revised_completion_date = Column(DateTime(timezone=True))
    delay_reason = Column(Text)
    costs_incurred = Column(Float)
    budget_variance = Column(Float)
    
    # Audit fields
    updated_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    updated_by = relationship("User")


class IncidentTimelineEvent(Base):
    """Timeline events for incident management"""
    __tablename__ = "incident_timeline_events"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    event_type = Column(String(100))
    description = Column(Text)
    performed_by = Column(String(255))
    performed_by_id = Column(Integer, ForeignKey("users.id"))
    event_time = Column(DateTime(timezone=True), server_default=func.now())
    duration_minutes = Column(Integer)
    attachments = Column(JSON)  # List of file references
    
    # Relationships
    incident = relationship("Incident", back_populates="timeline_events")
    performer = relationship("User")


class OperationalLoss(Base):
    """Financial losses from operational incidents"""
    __tablename__ = "operational_losses"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    loss_type = Column(String(100))
    amount = Column(Float)
    currency = Column(String(3), default='ZMW')
    basel_event_type = Column(String(100))  # Basel II/III event categories
    business_line = Column(String(255))
    loss_date = Column(DateTime(timezone=True))
    discovery_date = Column(DateTime(timezone=True))
    reporting_date = Column(DateTime(timezone=True))
    is_confirmed = Column(Boolean, default=False)
    is_recovered = Column(Boolean, default=False)
    recovery_amount = Column(Float)
    recovery_date = Column(DateTime(timezone=True))
    insurance_claimed = Column(Boolean, default=False)
    insurance_recovered = Column(Float)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    incident = relationship("Incident", back_populates="operational_losses")