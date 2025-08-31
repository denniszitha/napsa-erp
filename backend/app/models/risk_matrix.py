from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base

class MatrixType(str, enum.Enum):
    standard = "standard"
    custom = "custom"
    template = "template"

class RiskMatrix(Base):
    __tablename__ = "risk_matrices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    matrix_type = Column(String, default="standard")  # standard, custom, template
    
    # Matrix dimensions
    likelihood_levels = Column(Integer, default=5)  # Number of likelihood levels (3-7)
    impact_levels = Column(Integer, default=5)      # Number of impact levels (3-7)
    
    # Matrix configuration (stored as JSON)
    likelihood_labels = Column(JSON)  # ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
    impact_labels = Column(JSON)      # ["Insignificant", "Minor", "Moderate", "Major", "Catastrophic"]
    likelihood_descriptions = Column(JSON)  # Detailed descriptions for each level
    impact_descriptions = Column(JSON)      # Detailed descriptions for each level
    
    # Risk level configuration
    risk_levels = Column(JSON)        # Risk level definitions and colors
    risk_thresholds = Column(JSON)    # Score ranges for each risk level
    
    # Organization settings
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    organization_id = Column(UUID(as_uuid=True), nullable=True)  # For multi-tenant support
    
    # Metadata
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])

class MatrixTemplate(Base):
    __tablename__ = "matrix_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    industry = Column(String)  # Financial, Healthcare, Manufacturing, etc.
    
    # Template configuration
    template_config = Column(JSON)  # Complete matrix configuration
    
    # Metadata
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class RiskAppetite(Base):
    __tablename__ = "risk_appetites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matrix_id = Column(UUID(as_uuid=True), ForeignKey("risk_matrices.id"))
    
    # Risk appetite configuration
    low_threshold = Column(Integer, default=4)     # Scores 1-4: Low risk
    medium_threshold = Column(Integer, default=9)  # Scores 5-9: Medium risk
    high_threshold = Column(Integer, default=14)   # Scores 10-14: High risk
    very_high_threshold = Column(Integer, default=19)  # Scores 15-19: Very High risk
    # Scores 20+: Critical risk
    
    # Risk treatment strategies
    low_strategy = Column(String, default="Accept")
    medium_strategy = Column(String, default="Monitor")
    high_strategy = Column(String, default="Mitigate")
    very_high_strategy = Column(String, default="Urgent Action")
    critical_strategy = Column(String, default="Immediate Action")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    matrix = relationship("RiskMatrix", back_populates="appetite")

# Add relationship back to RiskMatrix
RiskMatrix.appetite = relationship("RiskAppetite", back_populates="matrix", uselist=False)