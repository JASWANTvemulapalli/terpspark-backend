"""
Registration repository for database operations.
Handles all database interactions for Registration model.
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.models.registration import Registration, RegistrationStatus, CheckInStatus
import uuid


class RegistrationRepository:
    """Repository for Registration database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_id(self, registration_id: str, include_relations: bool = True) -> Optional[Registration]:
        """
        Get registration by ID.
        
        Args:
            registration_id: Registration ID
            include_relations: Whether to eagerly load related objects
            
        Returns:
            Optional[Registration]: Registration if found, None otherwise
        """
        query = self.db.query(Registration).filter(Registration.id == registration_id)
        if include_relations:
            query = query.options(
                joinedload(Registration.user),
                joinedload(Registration.event)
            )
        return query.first()
    
    def get_by_user_and_event(
        self,
        user_id: str,
        event_id: str
    ) -> Optional[Registration]:
        """
        Get registration by user and event.
        
        Args:
            user_id: User ID
            event_id: Event ID
            
        Returns:
            Optional[Registration]: Registration if found, None otherwise
        """
        return self.db.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.event_id == event_id,
            Registration.status == RegistrationStatus.CONFIRMED
        ).first()
    
    def get_user_registrations(
        self,
        user_id: str,
        status: Optional[RegistrationStatus] = None,
        include_past: bool = False
    ) -> List[Registration]:
        """
        Get all registrations for a user.
        
        Args:
            user_id: User ID
            status: Filter by status (optional)
            include_past: Whether to include past events
            
        Returns:
            List[Registration]: List of registrations
        """
        from app.models.event import Event
        from datetime import date
        
        query = self.db.query(Registration).join(Event).filter(
            Registration.user_id == user_id
        )
        
        if status:
            query = query.filter(Registration.status == status)
        
        if not include_past:
            query = query.filter(Event.date >= date.today())
        
        return query.options(
            joinedload(Registration.event).joinedload(Event.organizer)
        ).order_by(Event.date, Event.start_time).all()
    
    def get_event_registrations(
        self,
        event_id: str,
        status: Optional[RegistrationStatus] = None,
        check_in_status: Optional[CheckInStatus] = None
    ) -> List[Registration]:
        """
        Get all registrations for an event.
        
        Args:
            event_id: Event ID
            status: Filter by registration status (optional)
            check_in_status: Filter by check-in status (optional)
            
        Returns:
            List[Registration]: List of registrations
        """
        query = self.db.query(Registration).filter(
            Registration.event_id == event_id
        )
        
        if status:
            query = query.filter(Registration.status == status)
        
        if check_in_status:
            query = query.filter(Registration.check_in_status == check_in_status)
        
        return query.options(joinedload(Registration.user)).order_by(
            Registration.registered_at
        ).all()
    
    def create(
        self,
        user_id: str,
        event_id: str,
        ticket_code: str,
        qr_code: Optional[str] = None,
        guests: Optional[List[dict]] = None,
        sessions: Optional[List[str]] = None
    ) -> Registration:
        """
        Create a new registration.
        
        Args:
            user_id: User ID
            event_id: Event ID
            ticket_code: Unique ticket code
            qr_code: QR code data (optional)
            guests: List of guest dictionaries (optional)
            sessions: List of session IDs (optional)
            
        Returns:
            Registration: Created registration
        """
        registration_id = str(uuid.uuid4())
        
        registration = Registration(
            id=registration_id,
            user_id=user_id,
            event_id=event_id,
            status=RegistrationStatus.CONFIRMED,
            ticket_code=ticket_code,
            qr_code=qr_code,
            check_in_status=CheckInStatus.NOT_CHECKED_IN,
            guests=guests if guests else [],
            sessions=sessions if sessions else [],
            reminder_sent=False
        )
        
        try:
            self.db.add(registration)
            self.db.commit()
            self.db.refresh(registration)
            return registration
        except IntegrityError:
            self.db.rollback()
            raise
    
    def cancel(self, registration: Registration) -> Registration:
        """
        Cancel a registration.
        
        Args:
            registration: Registration to cancel
            
        Returns:
            Registration: Cancelled registration
        """
        registration.status = RegistrationStatus.CANCELLED
        registration.cancelled_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(registration)
        return registration
    
    def check_in(self, registration: Registration) -> Registration:
        """
        Mark registration as checked in.
        
        Args:
            registration: Registration to check in
            
        Returns:
            Registration: Updated registration
        """
        registration.check_in_status = CheckInStatus.CHECKED_IN
        registration.checked_in_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(registration)
        return registration
    
    def mark_reminder_sent(self, registration: Registration) -> Registration:
        """
        Mark reminder as sent.
        
        Args:
            registration: Registration to update
            
        Returns:
            Registration: Updated registration
        """
        registration.reminder_sent = True
        self.db.commit()
        self.db.refresh(registration)
        return registration
    
    def count_event_registrations(
        self,
        event_id: str,
        status: RegistrationStatus = RegistrationStatus.CONFIRMED
    ) -> int:
        """
        Count registrations for an event.
        
        Args:
            event_id: Event ID
            status: Registration status to count
            
        Returns:
            int: Count of registrations
        """
        return self.db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.status == status
        ).count()
    
    def get_registrations_needing_reminder(self, event_date) -> List[Registration]:
        """
        Get registrations that need reminders sent.
        
        Args:
            event_date: Date to filter events
            
        Returns:
            List[Registration]: List of registrations
        """
        from app.models.event import Event
        
        return self.db.query(Registration).join(Event).filter(
            Event.date == event_date,
            Registration.status == RegistrationStatus.CONFIRMED,
            Registration.reminder_sent == False
        ).all()

