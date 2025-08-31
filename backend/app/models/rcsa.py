from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, Boolean, JSON, Float, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base

class RCSAStatus(str, enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    in_progress = "in_progress"  
    submitted = "submitted"
    approved = "approved"
    overdue = "overdue"

class RCSAFrequency(str, enum.Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    semi_annual = "semi_annual"
    annual = "annual"

class RCSASeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class RCSATemplate(Base):
    __tablename__ = "rcsa_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    department = Column(String)
    frequency = Column(Enum(RCSAFrequency), default=RCSAFrequency.quarterly)
    
    # Template configuration
    questions = relationship("RCSAQuestion", back_populates="template", cascade="all, delete-orphan")
    assessments = relationship("RCSAAssessment", back_populates="template")
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

class RCSAQuestion(Base):
    __tablename__ = "rcsa_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("rcsa_templates.id"), nullable=False)
    
    # Question details
    question_text = Column(Text, nullable=False)
    category = Column(String)  # e.g., "Risk Identification", "Control Effectiveness"
    question_type = Column(String, default="text")  # text, rating, boolean, multiple_choice
    options = Column(JSON)  # For multiple choice questions
    is_mandatory = Column(Boolean, default=True)
    weight = Column(Float, default=1.0)  # For scoring
    order_number = Column(Integer, default=0)
    
    # Relationships
    template = relationship("RCSATemplate", back_populates="questions")
    responses = relationship("RCSAResponse", back_populates="question", cascade="all, delete-orphan")

class RCSAAssessment(Base):
    __tablename__ = "rcsa_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("rcsa_templates.id"), nullable=False)
    
    # Assessment details
    title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    assessment_period = Column(String)  # e.g., "Q1 2025", "January 2025"
    status = Column(Enum(RCSAStatus), default=RCSAStatus.draft)
    
    # Timeline
    scheduled_date = Column(DateTime)
    started_date = Column(DateTime)
    due_date = Column(DateTime)
    completed_date = Column(DateTime)
    
    # Participants
    assessor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Scoring
    total_score = Column(Float)
    max_possible_score = Column(Float)
    completion_percentage = Column(Float, default=0.0)
    
    # Notes and findings
    executive_summary = Column(Text)
    key_findings = Column(JSON)  # Array of key findings
    recommendations = Column(JSON)  # Array of recommendations
    
    # Relationships
    template = relationship("RCSATemplate", back_populates="assessments")
    responses = relationship("RCSAResponse", back_populates="assessment", cascade="all, delete-orphan")
    action_items = relationship("RCSAActionItem", back_populates="assessment", cascade="all, delete-orphan")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RCSAResponse(Base):
    __tablename__ = "rcsa_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("rcsa_assessments.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("rcsa_questions.id"), nullable=False)
    
    # Response data
    response_text = Column(Text)
    rating_value = Column(Integer)  # For rating questions (1-5)
    boolean_value = Column(Boolean)  # For yes/no questions
    selected_options = Column(JSON)  # For multiple choice
    
    # Response metadata
    score = Column(Float)  # Calculated score for this response
    evidence_files = Column(JSON)  # Array of file references
    comments = Column(Text)
    
    # Relationships
    assessment = relationship("RCSAAssessment", back_populates="responses")
    question = relationship("RCSAQuestion", back_populates="responses")
    
    # Metadata
    responded_at = Column(DateTime, default=datetime.utcnow)
    responded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

class RCSAActionItem(Base):
    __tablename__ = "rcsa_action_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("rcsa_assessments.id"), nullable=False)
    
    # Action item details
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)  # e.g., "Control Enhancement", "Risk Mitigation"
    severity = Column(Enum(RCSASeverity), default=RCSASeverity.medium)
    
    # Assignment and timeline
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    due_date = Column(DateTime)
    completed_date = Column(DateTime)
    
    # Status tracking
    status = Column(String, default="open")  # open, in_progress, completed, overdue
    progress_percentage = Column(Float, default=0.0)
    
    # Implementation details
    proposed_solution = Column(Text)
    implementation_notes = Column(Text)
    verification_criteria = Column(Text)
    
    # Relationships
    assessment = relationship("RCSAAssessment", back_populates="action_items")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RCSASchedule(Base):
    __tablename__ = "rcsa_schedule"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("rcsa_templates.id"), nullable=False)
    
    # Scheduling details
    department = Column(String, nullable=False)
    frequency = Column(Enum(RCSAFrequency), nullable=False)
    next_due_date = Column(DateTime, nullable=False)
    
    # Assignment
    default_assessor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    default_reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Configuration
    auto_create = Column(Boolean, default=True)  # Auto-create assessments when due
    notification_days = Column(Integer, default=7)  # Notify X days before due
    
    # Status
    is_active = Column(Boolean, default=True)
    last_generated = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)