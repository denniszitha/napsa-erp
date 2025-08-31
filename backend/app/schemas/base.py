from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Union

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class BaseResponse(BaseSchema):
    id: Union[str, object]  # Can be string (for risks/assessments) or UUID (for users)
    created_at: datetime
    updated_at: Optional[datetime] = None

class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 100
    
class PaginatedResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list
