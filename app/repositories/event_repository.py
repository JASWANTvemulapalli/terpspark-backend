"""
Event repository for database operations.
Handles all database interactions for Event model.
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_, func
from datetime import date, datetime
from app.models.event import Event, EventStatus
import uuid


class EventRepository:
    """Repository for Event database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_id(self, event_id: str, include_relations: bool = True) -> Optional[Event]:
        """
        Get event by ID.
        
        Args:
            event_id: Event ID
            include_relations: Whether to eagerly load related objects
            
        Returns:
            Optional[Event]: Event if found, None otherwise
        """
        query = self.db.query(Event).filter(Event.id == event_id)
        if include_relations:
            query = query.options(
                joinedload(Event.category),
                joinedload(Event.organizer)
            )
        return query.first()
    
    def get_all_published(
        self,
        search: Optional[str] = None,
        category_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        organizer_id: Optional[str] = None,
        availability: Optional[bool] = None,
        sort_by: str = "date",
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Event], int]:
        """
        Get paginated list of published events with filters.
        
        Args:
            search: Search term for title, description, tags, venue
            category_id: Filter by category ID
            start_date: Filter events after this date
            end_date: Filter events before this date
            organizer_id: Filter by organizer ID
            availability: If True, only show events with available spots
            sort_by: Sort field ('date', 'title', 'popularity')
            page: Page number (1-indexed)
            limit: Items per page
            
        Returns:
            Tuple[List[Event], int]: List of events and total count
        """
        query = self.db.query(Event).filter(Event.status == EventStatus.PUBLISHED)
        
        # Apply filters
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Event.title.ilike(search_pattern),
                    Event.description.ilike(search_pattern),
                    Event.venue.ilike(search_pattern),
                    Event.location.ilike(search_pattern)
                )
            )
        
        if category_id:
            query = query.filter(Event.category_id == category_id)
        
        if start_date:
            query = query.filter(Event.date >= start_date)
        
        if end_date:
            query = query.filter(Event.date <= end_date)
        
        if organizer_id:
            query = query.filter(Event.organizer_id == organizer_id)
        
        if availability:
            query = query.filter(Event.registered_count < Event.capacity)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting
        if sort_by == "title":
            query = query.order_by(Event.title)
        elif sort_by == "popularity":
            query = query.order_by(Event.registered_count.desc())
        else:  # Default: date
            query = query.order_by(Event.date, Event.start_time)
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.options(
            joinedload(Event.category),
            joinedload(Event.organizer)
        ).offset(offset).limit(limit)
        
        events = query.all()
        return events, total_count
    
    def get_by_organizer(
        self,
        organizer_id: str,
        status: Optional[EventStatus] = None
    ) -> List[Event]:
        """
        Get all events created by an organizer.
        
        Args:
            organizer_id: Organizer user ID
            status: Filter by event status (optional)
            
        Returns:
            List[Event]: List of events
        """
        query = self.db.query(Event).filter(Event.organizer_id == organizer_id)
        
        if status:
            query = query.filter(Event.status == status)
        
        return query.options(joinedload(Event.category)).order_by(Event.date.desc()).all()
    
    def create(
        self,
        title: str,
        description: str,
        category_id: str,
        organizer_id: str,
        event_date: date,
        start_time: str,
        end_time: str,
        venue: str,
        location: str,
        capacity: int,
        image_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: EventStatus = EventStatus.PENDING
    ) -> Event:
        """
        Create a new event.
        
        Args:
            title: Event title
            description: Event description
            category_id: Category ID
            organizer_id: Organizer user ID
            event_date: Event date
            start_time: Start time (HH:MM)
            end_time: End time (HH:MM)
            venue: Venue name
            location: Detailed location
            capacity: Maximum capacity
            image_url: Image URL (optional)
            tags: List of tags (optional)
            status: Event status (default: PENDING)
            
        Returns:
            Event: Created event
        """
        from datetime import time
        
        event_id = str(uuid.uuid4())
        
        # Parse time strings
        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour, end_minute = map(int, end_time.split(':'))
        
        event = Event(
            id=event_id,
            title=title,
            description=description,
            category_id=category_id,
            organizer_id=organizer_id,
            date=event_date,
            start_time=time(start_hour, start_minute),
            end_time=time(end_hour, end_minute),
            venue=venue,
            location=location,
            capacity=capacity,
            registered_count=0,
            waitlist_count=0,
            status=status,
            image_url=image_url,
            tags=tags if tags else [],
            is_featured=False
        )
        
        try:
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return event
        except IntegrityError:
            self.db.rollback()
            raise
    
    def update(self, event: Event, **kwargs) -> Event:
        """
        Update event fields.
        
        Args:
            event: Event to update
            **kwargs: Fields to update
            
        Returns:
            Event: Updated event
        """
        from datetime import time
        
        for key, value in kwargs.items():
            if hasattr(event, key) and key not in ['id', 'registered_count', 'waitlist_count']:
                # Parse time strings if updating times
                if key in ['start_time', 'end_time'] and isinstance(value, str):
                    hour, minute = map(int, value.split(':'))
                    value = time(hour, minute)
                setattr(event, key, value)
        
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def publish(self, event: Event) -> Event:
        """
        Publish an event.
        
        Args:
            event: Event to publish
            
        Returns:
            Event: Published event
        """
        event.status = EventStatus.PUBLISHED
        event.published_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def cancel(self, event: Event) -> Event:
        """
        Cancel an event.
        
        Args:
            event: Event to cancel
            
        Returns:
            Event: Cancelled event
        """
        event.status = EventStatus.CANCELLED
        event.cancelled_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def increment_registered_count(self, event: Event, count: int = 1) -> Event:
        """
        Increment registered count.
        
        Args:
            event: Event to update
            count: Number to increment by
            
        Returns:
            Event: Updated event
        """
        event.registered_count += count
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def decrement_registered_count(self, event: Event, count: int = 1) -> Event:
        """
        Decrement registered count.
        
        Args:
            event: Event to update
            count: Number to decrement by
            
        Returns:
            Event: Updated event
        """
        event.registered_count = max(0, event.registered_count - count)
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def increment_waitlist_count(self, event: Event, count: int = 1) -> Event:
        """
        Increment waitlist count.
        
        Args:
            event: Event to update
            count: Number to increment by
            
        Returns:
            Event: Updated event
        """
        event.waitlist_count += count
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def decrement_waitlist_count(self, event: Event, count: int = 1) -> Event:
        """
        Decrement waitlist count.
        
        Args:
            event: Event to update
            count: Number to decrement by
            
        Returns:
            Event: Updated event
        """
        event.waitlist_count = max(0, event.waitlist_count - count)
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def get_pending_events(self) -> List[Event]:
        """
        Get all events pending approval.
        
        Returns:
            List[Event]: List of pending events
        """
        return self.db.query(Event).filter(
            Event.status == EventStatus.PENDING
        ).options(
            joinedload(Event.category),
            joinedload(Event.organizer)
        ).order_by(Event.created_at).all()
    
    def get_organizer_statistics(self, organizer_id: str) -> dict:
        """
        Get statistics for an organizer's events.
        
        Args:
            organizer_id: Organizer user ID
            
        Returns:
            dict: Statistics dictionary
        """
        from sqlalchemy import func
        
        total = self.db.query(func.count(Event.id)).filter(
            Event.organizer_id == organizer_id
        ).scalar()
        
        by_status = self.db.query(
            Event.status, func.count(Event.id)
        ).filter(
            Event.organizer_id == organizer_id
        ).group_by(Event.status).all()
        
        upcoming = self.db.query(func.count(Event.id)).filter(
            Event.organizer_id == organizer_id,
            Event.status == EventStatus.PUBLISHED,
            Event.date >= date.today()
        ).scalar()
        
        total_registrations = self.db.query(func.sum(Event.registered_count)).filter(
            Event.organizer_id == organizer_id
        ).scalar() or 0
        
        return {
            "total": total,
            "upcoming": upcoming,
            "total_registrations": total_registrations,
            "by_status": {status.value: count for status, count in by_status}
        }

