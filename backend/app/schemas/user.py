from typing import Optional, Union
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, validator
from uuid import UUID
from enum import Enum

class UserRole(str, Enum):
    admin = "admin"
    risk_manager = "risk_manager"
    risk_owner = "risk_owner"
    viewer = "viewer"
    auditor = "auditor"

# Token schemas
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: Union[UserRole, str] = UserRole.viewer
    department: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    is_active: bool = True
    
    @validator('role', pre=True)
    def validate_role(cls, v):
        if isinstance(v, str):
            try:
                return UserRole(v)
            except ValueError:
                raise ValueError(f"Invalid user role: {v}. Must be one of: {[e.value for e in UserRole]}")
        return v

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[Union[UserRole, str]] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('role', pre=True)
    def validate_role(cls, v):
        if v is not None and isinstance(v, str):
            try:
                return UserRole(v)
            except ValueError:
                raise ValueError(f"Invalid user role: {v}. Must be one of: {[e.value for e in UserRole]}")
        return v

class UserInDBBase(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    locked_until: Optional[datetime] = None

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str

# Password schemas
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class PasswordReset(BaseModel):
    token: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

# Add UserResponse as an alias for compatibility
UserResponse = User
