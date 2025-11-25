"""
Pydantic schemas for waitlist requests and responses.
Provides data validation and serialization for waitlist endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional


class WaitlistCreate(BaseModel):
    """Schema for joining waitlist."""
    eventId: str
    notificationPreference: str = Field("email", pattern="^(email|sms|both)$")


class EventWaitlistInfo(BaseModel):
    """Basic event information in waitlist response."""
    id: str
    title: str
    date: str
    capacity: int
    registeredCount: int


class WaitlistResponse(BaseModel):
    """Schema for waitlist entry in responses."""
    id: str
    userId: str
    eventId: str
    position: int
    joinedAt: str
    notificationPreference: str
    event: Optional[EventWaitlistInfo] = None
    
    class Config:
        from_attributes = True


class WaitlistCreateResponse(BaseModel):
    """Schema for waitlist join response."""
    success: bool = True
    message: str
    waitlistEntry: WaitlistResponse


class WaitlistListResponse(BaseModel):
    """Schema for list of waitlist entries response."""
    success: bool = True
    waitlist: list[WaitlistResponse]

