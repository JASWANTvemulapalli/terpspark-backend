"""
Pydantic schemas for organizer approval requests and responses.
Provides data validation and serialization for approval endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional


class OrganizerApprovalCreate(BaseModel):
    """Schema for creating organizer approval request."""
    reason: str = Field(..., min_length=20, max_length=2000, description="Reason for wanting to become organizer")


class OrganizerApprovalAction(BaseModel):
    """Schema for approving/rejecting organizer request."""
    notes: Optional[str] = Field(None, max_length=2000)


class OrganizerApprovalReject(BaseModel):
    """Schema for rejecting organizer request."""
    notes: str = Field(..., min_length=10, max_length=2000, description="Reason for rejection (required)")


class ReviewerInfo(BaseModel):
    """Reviewer information."""
    id: str
    name: str
    email: str


class OrganizerApprovalResponse(BaseModel):
    """Schema for organizer approval request in responses."""
    id: str
    userId: str
    name: str
    email: str
    department: Optional[str] = None
    reason: str
    status: str
    reviewedBy: Optional[str] = None
    reviewer: Optional[ReviewerInfo] = None
    notes: Optional[str] = None
    requestedAt: str
    reviewedAt: Optional[str] = None
    
    class Config:
        from_attributes = True


class OrganizerApprovalsListResponse(BaseModel):
    """Schema for list of approval requests response."""
    success: bool = True
    requests: list[OrganizerApprovalResponse]


class OrganizerApprovalActionResponse(BaseModel):
    """Schema for approval action response."""
    success: bool = True
    message: str

