from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, Boolean, JSON, Float, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base

class IncidentSeverity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class IncidentStatus(str, enum.Enum):
    open = "open"
    investigating = "investigating"
    contained = "contained"
    resolved = "resolved"
    closed = "closed"

class IncidentType(str, enum.Enum):
    security_breach = "security_breach"
    data_loss = "data_loss"
    system_failure = "system_failure"
    compliance_violation = "compliance_violation"
    operational_error = "operational_error"
    third_party_issue = "third_party_issue"

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_number = Column(String, unique=True, nullable=False)
    
    # Incident details
    title = Column(String, nullable=False)
    description = Column(Text)
    type = Column(Enum(IncidentType), nullable=False)
    severity = Column(Enum(IncidentSeverity), nullable=False)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.open)
    
    # Related entities
    risk_id = Column(String(20), ForeignKey("risks.id"))  # Changed to String to match risks table
    reported_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Timeline
    detected_at = Column(DateTime, nullable=False)
    reported_at = Column(DateTime, default=datetime.utcnow)
    contained_at = Column(DateTime)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)
    
    # Impact
    affected_systems = Column(JSON)
    affected_users_count = Column(Integer)
    financial_impact = Column(Float)
    data_compromised = Column(Boolean, default=False)
    
    # Response
    initial_response = Column(Text)
    root_cause = Column(Text)
    corrective_actions = Column(JSON)
    preventive_actions = Column(JSON)
    lessons_learned = Column(Text)
    
    # NAPSA-specific fields
    regulatory_breach = Column(Boolean, default=False)
    reputational_impact = Column(String(50))
    external_parties_involved = Column(Text)
    incident_code = Column(String(20), unique=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    risk = relationship("Risk")
    reported_by = relationship("User", foreign_keys=[reported_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    timeline_events = relationship("IncidentTimelineEvent", back_populates="incident")
    communications = relationship("IncidentCommunication", back_populates="incident")

class IncidentTimelineEvent(Base):
    __tablename__ = "incident_timeline_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"))
    
    event_type = Column(String)  # detection, escalation, action_taken, etc.
    description = Column(Text)
    performed_by = Column(String)
    event_time = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    incident = relationship("Incident", back_populates="timeline_events")

class IncidentCommunication(Base):
    __tablename__ = "incident_communications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"))
    
    communication_type = Column(String)  # internal_update, stakeholder_notice, etc.
    recipients = Column(JSON)
    subject = Column(String)
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    sent_by = Column(String)
    
    # Relationships
    incident = relationship("Incident", back_populates="communications")
