from sqlalchemy import Column, String, Float, Enum, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base

class KRIStatus(str, enum.Enum):
    normal = "normal"
    warning = "warning"
    critical = "critical"

class KeyRiskIndicator(Base):
    __tablename__ = "key_risk_indicators"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id"))
    
    # KRI Details
    name = Column(String, nullable=False)
    description = Column(String)
    metric_type = Column(String)  # percentage, count, ratio, etc.
    
    # Thresholds
    lower_threshold = Column(Float)
    upper_threshold = Column(Float)
    target_value = Column(Float)
    current_value = Column(Float)
    
    # Status
    status = Column(Enum(KRIStatus), default=KRIStatus.normal)
    trend = Column(String)  # increasing, decreasing, stable
    
    # Monitoring
    measurement_frequency = Column(String)
    data_source = Column(String)
    responsible_party = Column(String)
    
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    risk = relationship("Risk", back_populates="kris")
    measurements = relationship("KRIMeasurement", back_populates="kri")

class KRIMeasurement(Base):
    __tablename__ = "kri_measurements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kri_id = Column(UUID(as_uuid=True), ForeignKey("key_risk_indicators.id"))
    
    value = Column(Float, nullable=False)
    status = Column(Enum(KRIStatus))
    measurement_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(String)
    
    # Relationships
    kri = relationship("KeyRiskIndicator", back_populates="measurements")
