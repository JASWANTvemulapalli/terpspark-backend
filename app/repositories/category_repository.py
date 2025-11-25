"""
Category repository for database operations.
Handles all database interactions for Category model.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.category import Category
import uuid


class CategoryRepository:
    """Repository for Category database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_id(self, category_id: str) -> Optional[Category]:
        """
        Get category by ID.
        
        Args:
            category_id: Category ID
            
        Returns:
            Optional[Category]: Category if found, None otherwise
        """
        return self.db.query(Category).filter(Category.id == category_id).first()
    
    def get_by_slug(self, slug: str) -> Optional[Category]:
        """
        Get category by slug.
        
        Args:
            slug: Category slug
            
        Returns:
            Optional[Category]: Category if found, None otherwise
        """
        return self.db.query(Category).filter(Category.slug == slug).first()
    
    def get_all(self, active_only: bool = True) -> List[Category]:
        """
        Get all categories.
        
        Args:
            active_only: If True, return only active categories
            
        Returns:
            List[Category]: List of categories
        """
        query = self.db.query(Category)
        if active_only:
            query = query.filter(Category.is_active == True)
        return query.order_by(Category.name).all()
    
    def create(
        self,
        name: str,
        slug: str,
        color: str,
        description: Optional[str] = None,
        icon: Optional[str] = None
    ) -> Category:
        """
        Create a new category.
        
        Args:
            name: Category name
            slug: Category slug (must be unique)
            color: Color code for UI
            description: Category description (optional)
            icon: Icon identifier (optional)
            
        Returns:
            Category: Created category
            
        Raises:
            IntegrityError: If slug already exists
        """
        category_id = str(uuid.uuid4())
        
        category = Category(
            id=category_id,
            name=name,
            slug=slug,
            color=color,
            description=description,
            icon=icon,
            is_active=True
        )
        
        try:
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
            return category
        except IntegrityError:
            self.db.rollback()
            raise
    
    def update(self, category: Category, **kwargs) -> Category:
        """
        Update category fields.
        
        Args:
            category: Category to update
            **kwargs: Fields to update
            
        Returns:
            Category: Updated category
        """
        for key, value in kwargs.items():
            if hasattr(category, key) and key != 'id':
                setattr(category, key, value)
        
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def toggle_active(self, category: Category) -> Category:
        """
        Toggle category active status.
        
        Args:
            category: Category to toggle
            
        Returns:
            Category: Updated category
        """
        category.is_active = not category.is_active
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def count_events_using_category(self, category_id: str) -> int:
        """
        Count number of events using this category.
        
        Args:
            category_id: Category ID
            
        Returns:
            int: Number of events
        """
        from app.models.event import Event
        return self.db.query(Event).filter(Event.category_id == category_id).count()

