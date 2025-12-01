"""
Authentication service for business logic.
Handles authentication operations and business rules.
"""
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.repositories.organizer_approval_repository import OrganizerApprovalRepository
from app.core.security import verify_password, create_access_token
from app.schemas.auth import UserLogin, UserCreate


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: Session):
        """
        Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.user_repo = UserRepository(db)
        self.approval_repo = OrganizerApprovalRepository(db)
    
    def authenticate_user(self, credentials: UserLogin) -> Tuple[User, str]:
        """
        Authenticate user with email and password.
        
        Args:
            credentials: Login credentials
            
        Returns:
            Tuple[User, str]: Authenticated user and JWT token
            
        Raises:
            HTTPException: If authentication fails
        """
        # Get user by email
        user = self.user_repo.get_by_email(credentials.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Please check your email and password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(credentials.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Please check your email and password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user can login
        if not user.can_login:
            if user.is_organizer and not user.is_approved:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your organizer account is pending approval. Please contact an administrator."
                )
            elif not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your account has been deactivated. Please contact an administrator."
                )
        
        # Update last login
        self.user_repo.update_last_login(user)
        
        # Create JWT token
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "is_approved": user.is_approved
        }
        token = create_access_token(token_data)
        
        return user, token
    
    def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            User: Created user
            
        Raises:
            HTTPException: If email already exists
        """
        # Check if email already exists
        existing_user = self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered."
            )
        
        # Create user
        try:
            user = self.user_repo.create(
                email=user_data.email,
                password=user_data.password,
                name=user_data.name,
                role=user_data.role,
                department=user_data.department,
                phone=user_data.phone
            )

            # If user is organizer, create approval request
            if user.role == UserRole.ORGANIZER:
                reason = (
                    f"User {user.name} ({user.email}) from {user.department} department "
                    "requested organizer access during registration."
                )
                self.approval_repo.create(
                    user_id=user.id,
                    reason=reason
                )

            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        return self.user_repo.get_by_id(user_id)
