from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class RiskCategory(Base):
    """
    Model for managing risk categories dynamically.
    Supports hierarchical categories with parent-child relationships.
    """
    __tablename__ = "risk_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("risk_categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)  # To enable/disable categories
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referential relationship for parent-child categories
    parent = relationship("RiskCategory", remote_side=[id], backref="children")
    
    # Relationship with risks
    risks = relationship("Risk", back_populates="risk_category")
    
    def __repr__(self):
        return f"<RiskCategory(id={self.id}, name='{self.name}')>"
    
    @property
    def full_path(self):
        """Get the full category path (e.g., 'Parent > Child > Grandchild')"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name