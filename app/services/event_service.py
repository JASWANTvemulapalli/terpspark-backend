"""
Event service for business logic.
Handles event operations and business rules for Phase 2: Event Discovery & Browse.
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date
from app.models.event import Event, EventStatus
from app.models.category import Category
from app.models.venue import Venue
from app.repositories.event_repository import EventRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.venue_repository import VenueRepository


class EventService:
    """Service for event discovery and browsing operations."""
    
    def __init__(self, db: Session):
        """
        Initialize service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.event_repo = EventRepository(db)
        self.category_repo = CategoryRepository(db)
        self.venue_repo = VenueRepository(db)
    
    def get_published_events(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        organizer: Optional[str] = None,
        availability: Optional[bool] = None,
        sort_by: str = "date",
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Event], int]:
        """
        Get paginated list of published events with filters.
        
        Args:
            search: Search term for title, description, tags, venue
            category: Category slug
            start_date: Filter events after this date (YYYY-MM-DD)
            end_date: Filter events before this date (YYYY-MM-DD)
            organizer: Organizer name search
            availability: If True, only show events with available spots
            sort_by: Sort field ('date', 'title', 'popularity')
            page: Page number (1-indexed)
            limit: Items per page
            
        Returns:
            Tuple[List[Event], int]: List of events and total count
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate page and limit
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be at least 1"
            )
        
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        # Convert category slug to ID if provided
        category_id = None
        if category:
            cat = self.category_repo.get_by_slug(category)
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category '{category}' not found"
                )
            category_id = cat.id
        
        # Parse dates if provided
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            try:
                start_date_obj = date.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start_date must be in YYYY-MM-DD format"
                )
        
        if end_date:
            try:
                end_date_obj = date.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="end_date must be in YYYY-MM-DD format"
                )
        
        # Validate sort_by
        valid_sort_options = ["date", "title", "popularity"]
        if sort_by not in valid_sort_options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"sort_by must be one of: {', '.join(valid_sort_options)}"
            )
        
        # Get events from repository
        try:
            events, total_count = self.event_repo.get_all_published(
                search=search,
                category_id=category_id,
                start_date=start_date_obj,
                end_date=end_date_obj,
                organizer_id=None,  # Organizer search by name not implemented yet
                availability=availability,
                sort_by=sort_by,
                page=page,
                limit=limit
            )
            
            return events, total_count
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve events: {str(e)}"
            )
    
    def get_event_by_id(self, event_id: str) -> Event:
        """
        Get event details by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Event: Event details
            
        Raises:
            HTTPException: If event not found or not published
        """
        event = self.event_repo.get_by_id(event_id, include_relations=True)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Only return published events for public API
        # (Organizers and admins can see their own events regardless of status)
        if event.status != EventStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        return event
    
    def get_event_by_id_for_user(
        self,
        event_id: str,
        user_id: Optional[str] = None,
        is_admin: bool = False
    ) -> Event:
        """
        Get event details by ID with user-specific permissions.
        
        Args:
            event_id: Event ID
            user_id: Current user ID (optional)
            is_admin: Whether user is admin
            
        Returns:
            Event: Event details
            
        Raises:
            HTTPException: If event not found or user lacks permission
        """
        event = self.event_repo.get_by_id(event_id, include_relations=True)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Check permissions
        if event.status == EventStatus.PUBLISHED:
            # Published events are visible to everyone
            return event
        elif is_admin or (user_id and event.organizer_id == user_id):
            # Admins and event organizers can see any status
            return event
        else:
            # Other users can't see non-published events
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
    
    def get_all_categories(self, active_only: bool = True) -> List[Category]:
        """
        Get all event categories.
        
        Args:
            active_only: If True, return only active categories
            
        Returns:
            List[Category]: List of categories
        """
        try:
            return self.category_repo.get_all(active_only=active_only)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve categories: {str(e)}"
            )
    
    def get_all_venues(self, active_only: bool = True) -> List[Venue]:
        """
        Get all venues.
        
        Args:
            active_only: If True, return only active venues
            
        Returns:
            List[Venue]: List of venues
        """
        try:
            return self.venue_repo.get_all(active_only=active_only)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve venues: {str(e)}"
            )

