"""
Venue repository for database operations.
Handles all database interactions for Venue model.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.venue import Venue
import uuid


class VenueRepository:
    """Repository for Venue database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_id(self, venue_id: str) -> Optional[Venue]:
        """
        Get venue by ID.
        
        Args:
            venue_id: Venue ID
            
        Returns:
            Optional[Venue]: Venue if found, None otherwise
        """
        return self.db.query(Venue).filter(Venue.id == venue_id).first()
    
    def get_all(self, active_only: bool = True) -> List[Venue]:
        """
        Get all venues.
        
        Args:
            active_only: If True, return only active venues
            
        Returns:
            List[Venue]: List of venues
        """
        query = self.db.query(Venue)
        if active_only:
            query = query.filter(Venue.is_active == True)
        return query.order_by(Venue.name).all()
    
    def create(
        self,
        name: str,
        building: str,
        capacity: Optional[int] = None,
        facilities: Optional[List[str]] = None
    ) -> Venue:
        """
        Create a new venue.
        
        Args:
            name: Venue name
            building: Building name
            capacity: Maximum capacity (optional)
            facilities: List of available facilities (optional)
            
        Returns:
            Venue: Created venue
        """
        venue_id = str(uuid.uuid4())
        
        venue = Venue(
            id=venue_id,
            name=name,
            building=building,
            capacity=capacity,
            facilities=facilities if facilities else [],
            is_active=True
        )
        
        try:
            self.db.add(venue)
            self.db.commit()
            self.db.refresh(venue)
            return venue
        except IntegrityError:
            self.db.rollback()
            raise
    
    def update(self, venue: Venue, **kwargs) -> Venue:
        """
        Update venue fields.
        
        Args:
            venue: Venue to update
            **kwargs: Fields to update
            
        Returns:
            Venue: Updated venue
        """
        for key, value in kwargs.items():
            if hasattr(venue, key) and key != 'id':
                setattr(venue, key, value)
        
        self.db.commit()
        self.db.refresh(venue)
        return venue
    
    def toggle_active(self, venue: Venue) -> Venue:
        """
        Toggle venue active status.
        
        Args:
            venue: Venue to toggle
            
        Returns:
            Venue: Updated venue
        """
        venue.is_active = not venue.is_active
        self.db.commit()
        self.db.refresh(venue)
        return venue

