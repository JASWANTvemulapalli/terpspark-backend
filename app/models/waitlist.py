"""
Waitlist database model.
Represents waitlist entries for events that are at capacity.
"""
from sqlalchemy import Column, String, DateTime, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class NotificationPreference(str, enum.Enum):
    """Enum for notification preferences."""
    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"


class WaitlistEntry(Base):
    """
    Waitlist Entry model for managing event waitlists.
    Uses FIFO (First In, First Out) ordering based on position.
    """
    __tablename__ = "waitlist"
    
    # Primary Key
    id = Column(String(36), primary_key=True, index=True)
    
    # Foreign Keys
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    event_id = Column(String(36), ForeignKey("events.id"), nullable=False, index=True)
    
    # Position in Waitlist
    position = Column(
        Integer,
        nullable=False,
        index=True,
        comment="Position in waitlist (lower number = higher priority)"
    )
    
    # Notification Preference
    notification_preference = Column(
        SQLEnum(NotificationPreference),
        nullable=False,
        default=NotificationPreference.EMAIL
    )
    
    # Timestamps
    joined_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    # Relationships
    user = relationship("User", backref="waitlist_entries")
    event = relationship("Event", back_populates="waitlist")
    
    def __repr__(self) -> str:
        return f"<WaitlistEntry(id={self.id}, user_id={self.user_id}, event_id={self.event_id}, position={self.position})>"
    
    def to_dict(self, include_event: bool = False, include_user: bool = False) -> dict:
        """
        Convert waitlist entry to dictionary.
        
        Args:
            include_event: Whether to include event details
            include_user: Whether to include user details
            
        Returns:
            dict: Waitlist entry data as dictionary
        """
        waitlist_dict = {
            "id": self.id,
            "userId": self.user_id,
            "eventId": self.event_id,
            "position": self.position,
            "joinedAt": self.joined_at.isoformat() if self.joined_at else None,
            "notificationPreference": self.notification_preference.value,
        }
        
        if include_event and self.event:
            waitlist_dict["event"] = {
                "id": self.event.id,
                "title": self.event.title,
                "date": self.event.date.isoformat() if self.event.date else None,
                "capacity": self.event.capacity,
                "registeredCount": self.event.registered_count
            }
        
        if include_user and self.user:
            waitlist_dict["user"] = {
                "id": self.user.id,
                "name": self.user.name,
                "email": self.user.email
            }
        
        return waitlist_dict

