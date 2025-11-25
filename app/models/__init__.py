"""
Models package initialization.
Imports all models for easy access.
"""
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.venue import Venue
from app.models.event import Event, EventStatus
from app.models.registration import Registration, CheckInStatus, RegistrationStatus
from app.models.waitlist import WaitlistEntry, NotificationPreference
from app.models.organizer_approval import OrganizerApprovalRequest, ApprovalStatus
from app.models.audit_log import AuditLog, AuditAction, TargetType

__all__ = [
    # User
    "User",
    "UserRole",
    # Category
    "Category",
    # Venue
    "Venue",
    # Event
    "Event",
    "EventStatus",
    # Registration
    "Registration",
    "CheckInStatus",
    "RegistrationStatus",
    # Waitlist
    "WaitlistEntry",
    "NotificationPreference",
    # Organizer Approval
    "OrganizerApprovalRequest",
    "ApprovalStatus",
    # Audit Log
    "AuditLog",
    "AuditAction",
    "TargetType",
]
