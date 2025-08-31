"""
File Management Models
For document storage and management
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class FileCategory(Base):
    """Categories for organizing uploaded files"""
    __tablename__ = "file_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    allowed_extensions = Column(JSON, default=["pdf", "docx", "xlsx", "png", "jpg"])
    max_file_size = Column(Integer, default=10485760)  # 10MB in bytes
    storage_path = Column(String(500))
    requires_approval = Column(Boolean, default=False)
    retention_period_days = Column(Integer)
    is_sensitive = Column(Boolean, default=False)
    access_level = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    files = relationship("File", back_populates="category")


class File(Base):
    """File/Document storage records"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("file_categories.id"))
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    file_extension = Column(String(50))
    mime_type = Column(String(255))
    file_hash = Column(String(255))  # SHA-256 hash for integrity
    description = Column(Text)
    tags = Column(JSON)
    is_public = Column(Boolean, default=False)
    access_level = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_processed = Column(Boolean, default=False)
    
    # Polymorphic relationship fields
    related_entity_type = Column(String(100))  # 'risk', 'incident', 'assessment', etc.
    related_entity_id = Column(Integer)
    
    # Audit fields
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category = relationship("FileCategory", back_populates="files")
    uploaded_by = relationship("User")