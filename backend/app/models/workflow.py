from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base

class WorkflowType(str, enum.Enum):
    risk_treatment = "risk_treatment"
    risk_approval = "risk_approval"
    control_change = "control_change"

class WorkflowStatus(str, enum.Enum):
    draft = "draft"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    in_progress = "in_progress"
    completed = "completed"

class TreatmentStrategy(str, enum.Enum):
    accept = "accept"
    mitigate = "mitigate"
    transfer = "transfer"
    avoid = "avoid"

class RiskTreatment(Base):
    __tablename__ = "risk_treatments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(String, ForeignKey("risks.id"), nullable=False)
    
    # Treatment details
    strategy = Column(Enum(TreatmentStrategy), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    
    # Plan details
    action_plan = Column(Text)
    responsible_party = Column(String)
    target_date = Column(DateTime)
    
    # Cost-benefit
    estimated_cost = Column(Float)
    expected_risk_reduction = Column(Float)  # Percentage
    
    # Status
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.draft)
    
    # Metadata
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime)
    
    # Relationships
    risk = relationship("Risk", back_populates="treatments")
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    action_items = relationship("TreatmentAction", back_populates="treatment")

class TreatmentAction(Base):
    __tablename__ = "treatment_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    treatment_id = Column(UUID(as_uuid=True), ForeignKey("risk_treatments.id"))
    
    # Action details
    action = Column(String, nullable=False)
    description = Column(Text)
    assigned_to = Column(String)
    due_date = Column(DateTime)
    
    # Status
    is_completed = Column(Boolean, default=False)
    completed_date = Column(DateTime)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    treatment = relationship("RiskTreatment", back_populates="action_items")
