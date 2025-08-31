from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class RiskCategoryBase(BaseModel):
    """Base schema for risk category"""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    parent_id: Optional[int] = Field(None, description="Parent category ID for hierarchical structure")
    is_active: bool = Field(True, description="Whether the category is active")


class RiskCategoryCreate(RiskCategoryBase):
    """Schema for creating a risk category"""
    pass


class RiskCategoryUpdate(BaseModel):
    """Schema for updating a risk category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None


class RiskCategoryInDB(RiskCategoryBase):
    """Schema for risk category in database"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RiskCategoryResponse(RiskCategoryInDB):
    """Schema for risk category API response"""
    full_path: Optional[str] = Field(None, description="Full hierarchical path of the category")
    children_count: int = Field(0, description="Number of child categories")
    risks_count: int = Field(0, description="Number of associated risks")
    
    class Config:
        from_attributes = True


class RiskCategoryTree(RiskCategoryResponse):
    """Schema for hierarchical category tree"""
    children: List['RiskCategoryTree'] = Field([], description="Child categories")
    
    class Config:
        from_attributes = True


# Update forward references
RiskCategoryTree.model_rebuild()


class RiskCategoryList(BaseModel):
    """Response schema for list of categories"""
    total: int = Field(..., description="Total number of categories")
    items: List[RiskCategoryResponse] = Field(..., description="List of categories")
    
    class Config:
        from_attributes = True