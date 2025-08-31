"""
AML Sanctions Schemas
"""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class SanctionsListBase(BaseModel):
    """Base sanctions list schema"""
    list_name: str
    list_type: str  # OFAC, UN, EU, etc.
    description: Optional[str] = None
    last_updated: Optional[datetime] = None


class SanctionsListCreate(SanctionsListBase):
    """Schema for creating sanctions lists"""
    pass


class SanctionsList(SanctionsListBase):
    """Schema for sanctions list API responses"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class WatchlistEntryBase(BaseModel):
    """Base watchlist entry schema"""
    entity_name: str
    entity_type: str  # person, organization, vessel
    list_id: int
    reference_number: Optional[str] = None
    aliases: Optional[List[str]] = []
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    address: Optional[str] = None


class WatchlistEntryCreate(WatchlistEntryBase):
    """Schema for creating watchlist entries"""
    pass


class WatchlistEntry(WatchlistEntryBase):
    """Schema for watchlist entry API responses"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ScreeningResultBase(BaseModel):
    """Base screening result schema"""
    entity_name: str
    entity_type: str
    screening_type: str = "sanctions"  # sanctions, pep, adverse_media
    match_score: float
    is_match: bool
    matches: List[dict] = []


class ScreeningResultCreate(ScreeningResultBase):
    """Schema for creating screening results"""
    customer_id: Optional[int] = None
    transaction_id: Optional[int] = None


class ScreeningResult(ScreeningResultBase):
    """Schema for screening result API responses"""
    id: int
    customer_id: Optional[int] = None
    transaction_id: Optional[int] = None
    screening_date: datetime
    reviewed: bool = False
    reviewer_id: Optional[int] = None
    
    class Config:
        from_attributes = True