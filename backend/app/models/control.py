from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base

class ControlType(str, enum.Enum):
    preventive = "preventive"
    detective = "detective"
    corrective = "corrective"
    compensating = "compensating"

class ControlStatus(str, enum.Enum):
    effective = "effective"
    partially_effective = "partially_effective"
    ineffective = "ineffective"
    not_tested = "not_tested"

class Control(Base):
    __tablename__ = "controls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    type = Column(Enum(ControlType), nullable=False)
    status = Column(Enum(ControlStatus), default=ControlStatus.not_tested)
    
    # Control Details
    control_owner = Column(String)
    implementation_status = Column(String)
    testing_frequency = Column(String)
    last_test_date = Column(DateTime)
    next_test_date = Column(DateTime)
    
    # Effectiveness
    effectiveness_rating = Column(Float)  # 0-100%
    cost_of_control = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    risk_controls = relationship("RiskControl", back_populates="control")

class RiskControl(Base):
    __tablename__ = "risk_controls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(String(20), ForeignKey("risks.id"))  # Changed to match Risk.id type
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"))
    
    # Mapping Details
    coverage_percentage = Column(Float)
    criticality = Column(String)
    
    # Relationships
    risk = relationship("Risk", back_populates="controls")
    control = relationship("Control", back_populates="risk_controls")
