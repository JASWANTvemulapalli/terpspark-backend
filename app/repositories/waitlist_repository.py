"""
Waitlist repository for database operations.
Handles all database interactions for WaitlistEntry model.
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app.models.waitlist import WaitlistEntry, NotificationPreference
import uuid


class WaitlistRepository:
    """Repository for WaitlistEntry database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_id(self, waitlist_id: str, include_relations: bool = True) -> Optional[WaitlistEntry]:
        """
        Get waitlist entry by ID.
        
        Args:
            waitlist_id: Waitlist entry ID
            include_relations: Whether to eagerly load related objects
            
        Returns:
            Optional[WaitlistEntry]: Waitlist entry if found, None otherwise
        """
        query = self.db.query(WaitlistEntry).filter(WaitlistEntry.id == waitlist_id)
        if include_relations:
            query = query.options(
                joinedload(WaitlistEntry.user),
                joinedload(WaitlistEntry.event)
            )
        return query.first()
    
    def get_by_user_and_event(
        self,
        user_id: str,
        event_id: str
    ) -> Optional[WaitlistEntry]:
        """
        Get waitlist entry by user and event.
        
        Args:
            user_id: User ID
            event_id: Event ID
            
        Returns:
            Optional[WaitlistEntry]: Waitlist entry if found, None otherwise
        """
        return self.db.query(WaitlistEntry).filter(
            WaitlistEntry.user_id == user_id,
            WaitlistEntry.event_id == event_id
        ).first()
    
    def get_user_waitlist_entries(self, user_id: str) -> List[WaitlistEntry]:
        """
        Get all waitlist entries for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[WaitlistEntry]: List of waitlist entries
        """
        return self.db.query(WaitlistEntry).filter(
            WaitlistEntry.user_id == user_id
        ).options(
            joinedload(WaitlistEntry.event)
        ).order_by(WaitlistEntry.joined_at).all()
    
    def get_event_waitlist(self, event_id: str) -> List[WaitlistEntry]:
        """
        Get waitlist for an event, ordered by position.
        
        Args:
            event_id: Event ID
            
        Returns:
            List[WaitlistEntry]: List of waitlist entries ordered by position
        """
        return self.db.query(WaitlistEntry).filter(
            WaitlistEntry.event_id == event_id
        ).options(
            joinedload(WaitlistEntry.user)
        ).order_by(WaitlistEntry.position).all()
    
    def get_next_position(self, event_id: str) -> int:
        """
        Get the next available position for an event's waitlist.
        
        Args:
            event_id: Event ID
            
        Returns:
            int: Next position number
        """
        from sqlalchemy import func
        
        max_position = self.db.query(
            func.max(WaitlistEntry.position)
        ).filter(
            WaitlistEntry.event_id == event_id
        ).scalar()
        
        return (max_position or 0) + 1
    
    def create(
        self,
        user_id: str,
        event_id: str,
        notification_preference: NotificationPreference = NotificationPreference.EMAIL
    ) -> WaitlistEntry:
        """
        Create a new waitlist entry.
        
        Args:
            user_id: User ID
            event_id: Event ID
            notification_preference: Notification preference
            
        Returns:
            WaitlistEntry: Created waitlist entry
        """
        waitlist_id = str(uuid.uuid4())
        position = self.get_next_position(event_id)
        
        entry = WaitlistEntry(
            id=waitlist_id,
            user_id=user_id,
            event_id=event_id,
            position=position,
            notification_preference=notification_preference
        )
        
        try:
            self.db.add(entry)
            self.db.commit()
            self.db.refresh(entry)
            return entry
        except IntegrityError:
            self.db.rollback()
            raise
    
    def remove(self, entry: WaitlistEntry) -> None:
        """
        Remove a waitlist entry and update positions.
        
        Args:
            entry: Waitlist entry to remove
        """
        event_id = entry.event_id
        position = entry.position
        
        # Delete the entry
        self.db.delete(entry)
        self.db.commit()
        
        # Update positions for remaining entries
        self.db.query(WaitlistEntry).filter(
            WaitlistEntry.event_id == event_id,
            WaitlistEntry.position > position
        ).update(
            {WaitlistEntry.position: WaitlistEntry.position - 1},
            synchronize_session=False
        )
        self.db.commit()
    
    def get_first_in_line(self, event_id: str) -> Optional[WaitlistEntry]:
        """
        Get the first person in line for an event.
        
        Args:
            event_id: Event ID
            
        Returns:
            Optional[WaitlistEntry]: First waitlist entry or None
        """
        return self.db.query(WaitlistEntry).filter(
            WaitlistEntry.event_id == event_id
        ).order_by(WaitlistEntry.position).first()
    
    def count_event_waitlist(self, event_id: str) -> int:
        """
        Count waitlist entries for an event.
        
        Args:
            event_id: Event ID
            
        Returns:
            int: Count of waitlist entries
        """
        return self.db.query(WaitlistEntry).filter(
            WaitlistEntry.event_id == event_id
        ).count()

