"""
Organizer Approval repository for database operations.
Handles all database interactions for OrganizerApprovalRequest model.
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.models.organizer_approval import OrganizerApprovalRequest, ApprovalStatus
import uuid


class OrganizerApprovalRepository:
    """Repository for OrganizerApprovalRequest database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_id(self, request_id: str, include_relations: bool = True) -> Optional[OrganizerApprovalRequest]:
        """
        Get approval request by ID.
        
        Args:
            request_id: Request ID
            include_relations: Whether to eagerly load related objects
            
        Returns:
            Optional[OrganizerApprovalRequest]: Request if found, None otherwise
        """
        query = self.db.query(OrganizerApprovalRequest).filter(
            OrganizerApprovalRequest.id == request_id
        )
        if include_relations:
            query = query.options(
                joinedload(OrganizerApprovalRequest.user),
                joinedload(OrganizerApprovalRequest.reviewer)
            )
        return query.first()
    
    def get_by_user(self, user_id: str) -> Optional[OrganizerApprovalRequest]:
        """
        Get approval request by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[OrganizerApprovalRequest]: Most recent request if found
        """
        return self.db.query(OrganizerApprovalRequest).filter(
            OrganizerApprovalRequest.user_id == user_id
        ).order_by(OrganizerApprovalRequest.requested_at.desc()).first()
    
    def get_all(self, status: Optional[ApprovalStatus] = None) -> List[OrganizerApprovalRequest]:
        """
        Get all approval requests.
        
        Args:
            status: Filter by status (optional)
            
        Returns:
            List[OrganizerApprovalRequest]: List of requests
        """
        query = self.db.query(OrganizerApprovalRequest)
        
        if status:
            query = query.filter(OrganizerApprovalRequest.status == status)
        
        return query.options(
            joinedload(OrganizerApprovalRequest.user)
        ).order_by(OrganizerApprovalRequest.requested_at).all()
    
    def get_pending(self) -> List[OrganizerApprovalRequest]:
        """
        Get all pending approval requests.
        
        Returns:
            List[OrganizerApprovalRequest]: List of pending requests
        """
        return self.get_all(status=ApprovalStatus.PENDING)
    
    def create(self, user_id: str, reason: str) -> OrganizerApprovalRequest:
        """
        Create a new approval request.
        
        Args:
            user_id: User ID
            reason: Reason for wanting to become organizer
            
        Returns:
            OrganizerApprovalRequest: Created request
        """
        request_id = str(uuid.uuid4())
        
        request = OrganizerApprovalRequest(
            id=request_id,
            user_id=user_id,
            reason=reason,
            status=ApprovalStatus.PENDING
        )
        
        try:
            self.db.add(request)
            self.db.commit()
            self.db.refresh(request)
            return request
        except IntegrityError:
            self.db.rollback()
            raise
    
    def approve(
        self,
        request: OrganizerApprovalRequest,
        reviewer_id: str,
        notes: Optional[str] = None
    ) -> OrganizerApprovalRequest:
        """
        Approve an organizer request.
        
        Args:
            request: Request to approve
            reviewer_id: Admin user ID who approved
            notes: Admin notes (optional)
            
        Returns:
            OrganizerApprovalRequest: Updated request
        """
        request.status = ApprovalStatus.APPROVED
        request.reviewed_by = reviewer_id
        request.reviewed_at = datetime.utcnow()
        request.notes = notes
        
        self.db.commit()
        self.db.refresh(request)
        return request
    
    def reject(
        self,
        request: OrganizerApprovalRequest,
        reviewer_id: str,
        notes: str
    ) -> OrganizerApprovalRequest:
        """
        Reject an organizer request.
        
        Args:
            request: Request to reject
            reviewer_id: Admin user ID who rejected
            notes: Reason for rejection (required)
            
        Returns:
            OrganizerApprovalRequest: Updated request
        """
        request.status = ApprovalStatus.REJECTED
        request.reviewed_by = reviewer_id
        request.reviewed_at = datetime.utcnow()
        request.notes = notes
        
        self.db.commit()
        self.db.refresh(request)
        return request
    
    def count_pending(self) -> int:
        """
        Count pending approval requests.
        
        Returns:
            int: Count of pending requests
        """
        return self.db.query(OrganizerApprovalRequest).filter(
            OrganizerApprovalRequest.status == ApprovalStatus.PENDING
        ).count()

