"""
User repository for database operations.
Handles all database interactions for User model.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User, UserRole
from app.core.security import get_password_hash
import uuid


class UserRepository:
    """Repository for User database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email.lower()).first()
    
    def create(
        self,
        email: str,
        password: str,
        name: str,
        role: UserRole = UserRole.STUDENT,
        department: Optional[str] = None,
        phone: Optional[str] = None
    ) -> User:
        """
        Create a new user.
        
        Args:
            email: User email
            password: Plain text password (will be hashed)
            name: User name
            role: User role (default: STUDENT)
            department: User department (optional)
            phone: User phone (optional)
            
        Returns:
            User: Created user
            
        Raises:
            IntegrityError: If email already exists
        """
        # Generate UUID for user ID
        user_id = str(uuid.uuid4())
        
        # Hash password
        hashed_password = get_password_hash(password)
        
        # Create user
        user = User(
            id=user_id,
            email=email.lower(),
            password=hashed_password,
            name=name,
            role=role,
            department=department,
            phone=phone,
            is_approved=(role == UserRole.STUDENT or role == UserRole.ADMIN)
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise
    
    def update(self, user: User, **kwargs) -> User:
        """
        Update user fields.
        
        Args:
            user: User to update
            **kwargs: Fields to update
            
        Returns:
            User: Updated user
        """
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_last_login(self, user: User) -> User:
        """
        Update user's last login timestamp.
        
        Args:
            user: User to update
            
        Returns:
            User: Updated user
        """
        from datetime import datetime
        user.last_login = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def approve_organizer(self, user: User) -> User:
        """
        Approve an organizer user.
        
        Args:
            user: User to approve
            
        Returns:
            User: Approved user
        """
        user.is_approved = True
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def deactivate(self, user: User) -> User:
        """
        Deactivate a user.
        
        Args:
            user: User to deactivate
            
        Returns:
            User: Deactivated user
        """
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def activate(self, user: User) -> User:
        """
        Activate a user.
        
        Args:
            user: User to activate
            
        Returns:
            User: Activated user
        """
        user.is_active = True
        self.db.commit()
        self.db.refresh(user)
        return user
