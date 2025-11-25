"""
Pydantic schemas for venue requests and responses.
Provides data validation and serialization for venue endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class VenueBase(BaseModel):
    """Base venue schema with common fields."""
    name: str = Field(..., min_length=2, max_length=200)
    building: str = Field(..., min_length=2, max_length=200)
    capacity: Optional[int] = Field(None, ge=1, description="Maximum capacity")
    facilities: Optional[List[str]] = Field(default_factory=list)


class VenueCreate(VenueBase):
    """Schema for creating a new venue."""
    pass


class VenueUpdate(BaseModel):
    """Schema for updating a venue."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    building: Optional[str] = Field(None, min_length=2, max_length=200)
    capacity: Optional[int] = Field(None, ge=1)
    facilities: Optional[List[str]] = None


class VenueResponse(BaseModel):
    """Schema for venue data in responses."""
    id: str
    name: str
    building: str
    capacity: Optional[int] = None
    facilities: List[str] = []
    isActive: bool
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    
    class Config:
        from_attributes = True


class VenuesResponse(BaseModel):
    """Schema for list of venues response."""
    success: bool = True
    venues: List[VenueResponse]

