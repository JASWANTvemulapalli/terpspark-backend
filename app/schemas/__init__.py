"""
Schemas package initialization.
Imports all schemas for easy access.
"""
# Auth schemas
from app.schemas.auth import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenValidateResponse,
    LogoutResponse,
    ErrorResponse,
    MessageResponse
)

# Category schemas
from app.schemas.category import (
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoriesResponse
)

# Venue schemas
from app.schemas.venue import (
    VenueBase,
    VenueCreate,
    VenueUpdate,
    VenueResponse,
    VenuesResponse
)

# Event schemas
from app.schemas.event import (
    EventBase,
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
    EventsListResponse,
    EventDetailResponse,
    EventStatistics,
    OrganizerEventsResponse,
    PaginationInfo,
    OrganizerInfo,
    CategoryInfo
)

# Registration schemas
from app.schemas.registration import (
    GuestInfo,
    RegistrationCreate,
    RegistrationResponse,
    RegistrationCreateResponse,
    RegistrationsListResponse,
    AttendeeInfo,
    AttendeeStatistics,
    AttendeesResponse
)

# Waitlist schemas
from app.schemas.waitlist import (
    WaitlistCreate,
    WaitlistResponse,
    WaitlistCreateResponse,
    WaitlistListResponse
)

# Organizer Approval schemas
from app.schemas.organizer_approval import (
    OrganizerApprovalCreate,
    OrganizerApprovalAction,
    OrganizerApprovalReject,
    OrganizerApprovalResponse,
    OrganizerApprovalsListResponse,
    OrganizerApprovalActionResponse
)

# Audit Log schemas
from app.schemas.audit_log import (
    AuditLogResponse,
    AuditLogsListResponse
)

__all__ = [
    # Auth
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "TokenValidateResponse",
    "LogoutResponse",
    "ErrorResponse",
    "MessageResponse",
    # Category
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "CategoriesResponse",
    # Venue
    "VenueBase",
    "VenueCreate",
    "VenueUpdate",
    "VenueResponse",
    "VenuesResponse",
    # Event
    "EventBase",
    "EventCreate",
    "EventUpdate",
    "EventResponse",
    "EventListResponse",
    "EventsListResponse",
    "EventDetailResponse",
    "EventStatistics",
    "OrganizerEventsResponse",
    "PaginationInfo",
    "OrganizerInfo",
    "CategoryInfo",
    # Registration
    "GuestInfo",
    "RegistrationCreate",
    "RegistrationResponse",
    "RegistrationCreateResponse",
    "RegistrationsListResponse",
    "AttendeeInfo",
    "AttendeeStatistics",
    "AttendeesResponse",
    # Waitlist
    "WaitlistCreate",
    "WaitlistResponse",
    "WaitlistCreateResponse",
    "WaitlistListResponse",
    # Organizer Approval
    "OrganizerApprovalCreate",
    "OrganizerApprovalAction",
    "OrganizerApprovalReject",
    "OrganizerApprovalResponse",
    "OrganizerApprovalsListResponse",
    "OrganizerApprovalActionResponse",
    # Audit Log
    "AuditLogResponse",
    "AuditLogsListResponse",
]
