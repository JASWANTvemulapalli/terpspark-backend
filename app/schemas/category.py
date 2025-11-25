"""
Pydantic schemas for category requests and responses.
Provides data validation and serialization for category endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional


class CategoryBase(BaseModel):
    """Base category schema with common fields."""
    name: str = Field(..., min_length=2, max_length=100)
    color: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=100)


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    slug: Optional[str] = Field(None, max_length=100, description="Auto-generated if not provided")


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, min_length=3, max_length=50)
    icon: Optional[str] = Field(None, max_length=100)


class CategoryResponse(BaseModel):
    """Schema for category data in responses."""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    color: str
    icon: Optional[str] = None
    isActive: bool
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    
    class Config:
        from_attributes = True


class CategoriesResponse(BaseModel):
    """Schema for list of categories response."""
    success: bool = True
    categories: list[CategoryResponse]

