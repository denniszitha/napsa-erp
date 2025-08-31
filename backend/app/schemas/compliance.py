from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ComplianceBase(BaseModel):
    """Base compliance schema"""
    pass

class ComplianceCreate(ComplianceBase):
    """Create compliance schema"""
    pass

class ComplianceUpdate(BaseModel):
    """Update compliance schema"""
    pass

class ComplianceResponse(ComplianceBase):
    """Response compliance schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
