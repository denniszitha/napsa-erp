from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum, JSON, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class ListType(str, enum.Enum):
    SANCTIONS = "sanctions"
    PEP = "pep"
    WATCHLIST = "watchlist"
    INTERNAL = "internal"
    ADVERSE_MEDIA = "adverse_media"


class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED_MATCH = "confirmed_match"
    FALSE_POSITIVE = "false_positive"
    POSSIBLE_MATCH = "possible_match"
    NO_MATCH = "no_match"


class SanctionsList(Base):
    __tablename__ = "sanctions_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    list_code = Column(String(50), unique=True, index=True, nullable=False)
    list_name = Column(String(200), nullable=False)
    list_type = Column(Enum(ListType), nullable=False)
    
    # List Information
    source = Column(String(200))  # e.g., "OFAC", "UN", "EU", "Internal"
    description = Column(Text)
    url = Column(String(500))
    
    # Update Information
    last_updated = Column(DateTime)
    update_frequency = Column(String(50))  # e.g., "daily", "weekly", "monthly"
    next_update = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    auto_update = Column(Boolean, default=False)
    
    # Statistics
    total_entries = Column(Integer, default=0)
    active_entries = Column(Integer, default=0)
    
    # System Fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    entries = relationship("WatchlistEntry", back_populates="sanctions_list", cascade="all, delete-orphan")


class WatchlistEntry(Base):
    __tablename__ = "watchlist_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(String(100), unique=True, index=True, nullable=False)
    list_id = Column(Integer, ForeignKey("sanctions_lists.id"), nullable=False)
    
    # Entity Information
    entity_type = Column(String(50))  # "individual", "entity", "vessel", "aircraft"
    full_name = Column(String(500), nullable=False, index=True)
    first_name = Column(String(200))
    last_name = Column(String(200))
    middle_name = Column(String(200))
    
    # Aliases
    aliases = Column(JSON)  # Store as JSON array
    aka = Column(Text)  # Also Known As
    
    # Identification
    date_of_birth = Column(Date)
    place_of_birth = Column(String(200))
    nationality = Column(String(100))
    passport_numbers = Column(JSON)
    national_ids = Column(JSON)
    tax_ids = Column(JSON)
    
    # Address Information
    addresses = Column(JSON)  # Store multiple addresses as JSON
    countries = Column(JSON)  # Associated countries
    
    # Entity Details (for organizations)
    registration_number = Column(String(100))
    registration_country = Column(String(2))
    business_type = Column(String(100))
    
    # Sanction Details
    listing_date = Column(Date)
    programs = Column(JSON)  # Sanction programs
    remarks = Column(Text)
    additional_info = Column(JSON)
    
    # Risk Information
    risk_score = Column(Float)
    categories = Column(JSON)  # e.g., ["terrorism", "narcotics", "proliferation"]
    
    # Status
    is_active = Column(Boolean, default=True)
    delisted = Column(Boolean, default=False)
    delisted_date = Column(Date)
    
    # System Fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_updated_at = Column(DateTime)
    
    # Relationships
    sanctions_list = relationship("SanctionsList", back_populates="entries")
    screening_results = relationship("ScreeningResult", back_populates="watchlist_entry")


class ScreeningResult(Base):
    __tablename__ = "screening_results"
    
    id = Column(Integer, primary_key=True, index=True)
    screening_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Screening Target
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"))
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    
    # Screening Details
    screening_type = Column(String(50))  # "customer", "transaction", "periodic"
    screening_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Searched Information
    searched_name = Column(String(500), nullable=False)
    searched_data = Column(JSON)  # Additional search parameters
    
    # Match Information
    watchlist_entry_id = Column(Integer, ForeignKey("watchlist_entries.id"))
    match_score = Column(Float)  # Similarity score (0-100)
    match_status = Column(Enum(MatchStatus), default=MatchStatus.PENDING)
    
    # Match Details
    matched_fields = Column(JSON)  # Which fields matched
    match_reasons = Column(Text)
    algorithm_used = Column(String(50))  # e.g., "fuzzy", "phonetic", "exact"
    
    # Review Information
    reviewed = Column(Boolean, default=False)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    
    # Disposition
    disposition = Column(String(100))  # e.g., "true_match", "false_positive"
    disposition_reason = Column(Text)
    
    # Case Management
    case_created = Column(Boolean, default=False)
    case_id = Column(Integer, ForeignKey("compliance_cases.id"))
    
    # Whitelisting
    whitelisted = Column(Boolean, default=False)
    whitelist_reason = Column(Text)
    whitelist_expiry = Column(DateTime)
    
    # System Fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("CustomerProfile", back_populates="screening_results")
    transaction = relationship("Transaction")
    watchlist_entry = relationship("WatchlistEntry", back_populates="screening_results")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    case = relationship("ComplianceCase", back_populates="screening_results")