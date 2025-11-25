# TerpSpark Backend - Architecture & Implementation Guide

## 🏗️ Architecture Overview

### Design Principles

1. **Separation of Concerns**: Clear separation between API, business logic, and data access
2. **Dependency Injection**: FastAPI's dependency system for clean, testable code
3. **Type Safety**: Pydantic schemas for request/response validation
4. **Security First**: JWT authentication, password hashing, RBAC middleware
5. **Scalability**: Repository pattern and service layer for easy extension

### Layer Architecture

```
┌─────────────────────────────────────┐
│   API Layer (FastAPI Routes)       │  ← HTTP requests/responses
├─────────────────────────────────────┤
│   Middleware Layer (RBAC)           │  ← Authentication & Authorization
├─────────────────────────────────────┤
│   Service Layer (Business Logic)    │  ← Business rules & workflows
├─────────────────────────────────────┤
│   Repository Layer (Data Access)    │  ← Database operations
├─────────────────────────────────────┤
│   Model Layer (SQLAlchemy ORM)      │  ← Database schema
└─────────────────────────────────────┘
```

## 📁 Project Structure

```
terpspark-backend/
│
├── app/                              # Main application package
│   ├── __init__.py
│   │
│   ├── api/                          # API route handlers
│   │   ├── __init__.py               # Router aggregation
│   │   └── auth.py                   # Authentication routes (Phase 1)
│   │   # Future: events.py, registrations.py, organizer.py, admin.py
│   │
│   ├── core/                         # Core configurations
│   │   ├── __init__.py
│   │   ├── config.py                 # Settings & environment variables
│   │   ├── database.py               # Database connection & session
│   │   └── security.py               # Password hashing & JWT
│   │
│   ├── middleware/                   # Middleware & dependencies
│   │   ├── __init__.py
│   │   └── auth.py                   # RBAC & authentication
│   │
│   ├── models/                       # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── user.py                   # User model
│   │   # Future: event.py, registration.py, category.py, etc.
│   │
│   ├── repositories/                 # Data access layer
│   │   ├── __init__.py
│   │   └── user_repository.py        # User CRUD operations
│   │   # Future: event_repository.py, etc.
│   │
│   ├── schemas/                      # Pydantic schemas
│   │   ├── __init__.py
│   │   └── auth.py                   # Auth request/response schemas
│   │   # Future: event.py, registration.py, etc.
│   │
│   ├── services/                     # Business logic
│   │   ├── __init__.py
│   │   └── auth_service.py           # Authentication business logic
│   │   # Future: event_service.py, etc.
│   │
│   └── utils/                        # Utility functions
│       ├── __init__.py
│       └── init_db.py                # Database initialization script
│
├── alembic/                          # Database migrations
│   ├── versions/                     # Migration files
│   ├── env.py                        # Alembic environment
│   └── script.py.mako                # Migration template
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   └── test_auth.py                  # Authentication tests
│
├── logs/                             # Application logs
│
├── .env                              # Environment variables (gitignored)
├── .env.example                      # Environment template
├── .gitignore                        # Git ignore rules
├── alembic.ini                       # Alembic configuration
├── docker-compose.yml                # Docker Compose setup
├── Dockerfile                        # Docker image definition
├── main.py                           # FastAPI application entry point
├── Makefile                          # Common development tasks
├── QUICKSTART.md                     # Quick start guide
├── README.md                         # Comprehensive documentation
└── requirements.txt                  # Python dependencies
```

## 🔑 Key Components

### 1. Authentication Flow

```python
User Request (login)
    ↓
API Route (auth.py)
    ↓
Auth Service (auth_service.py)
    ↓
User Repository (user_repository.py)
    ↓
Database (PostgreSQL)
    ↓
Generate JWT Token
    ↓
Return Token + User Info
```

### 2. RBAC (Role-Based Access Control)

```python
# Protect endpoint with role requirement
@router.get("/admin-only")
async def admin_endpoint(user: User = Depends(require_admin)):
    return {"message": "Admin access granted"}

# Multiple roles allowed
@router.get("/organizer-or-admin")
async def org_endpoint(user: User = Depends(require_organizer)):
    return {"message": "Organizer or admin access"}
```

### 3. Request/Response Flow

```
Client Request
    ↓
FastAPI Route
    ↓
Pydantic Schema Validation
    ↓
JWT Token Verification (if required)
    ↓
RBAC Check (if required)
    ↓
Service Layer (business logic)
    ↓
Repository Layer (database)
    ↓
Response Schema Serialization
    ↓
JSON Response
```

## 🛠️ Implementation Guide

### Adding a New Feature (Example: Events)

#### Step 1: Create Model

```python
# app/models/event.py
from sqlalchemy import Column, String, Integer, DateTime, Enum
from app.core.database import Base
import enum

class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PUBLISHED = "published"
    CANCELLED = "cancelled"

class Event(Base):
    __tablename__ = "events"
    
    id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False)
    # ... more fields
```

#### Step 2: Create Schemas

```python
# app/schemas/event.py
from pydantic import BaseModel
from typing import Optional

class EventCreate(BaseModel):
    title: str
    description: str
    # ... more fields

class EventResponse(BaseModel):
    id: str
    title: str
    # ... more fields
    
    class Config:
        from_attributes = True
```

#### Step 3: Create Repository

```python
# app/repositories/event_repository.py
from sqlalchemy.orm import Session
from app.models.event import Event

class EventRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(Event).offset(skip).limit(limit).all()
    
    def create(self, event_data: dict):
        event = Event(**event_data)
        self.db.add(event)
        self.db.commit()
        return event
```

#### Step 4: Create Service

```python
# app/services/event_service.py
from sqlalchemy.orm import Session
from app.repositories.event_repository import EventRepository

class EventService:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)
    
    def create_event(self, event_data):
        # Business logic here
        return self.event_repo.create(event_data)
```

#### Step 5: Create API Routes

```python
# app/api/events.py
from fastapi import APIRouter, Depends
from app.middleware.auth import require_organizer
from app.services.event_service import EventService

router = APIRouter(prefix="/api/events", tags=["Events"])

@router.post("/")
async def create_event(
    event: EventCreate,
    user: User = Depends(require_organizer),
    db: Session = Depends(get_db)
):
    service = EventService(db)
    return service.create_event(event.dict())
```

#### Step 6: Register Router

```python
# app/api/__init__.py
from app.api import auth, events

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(events.router)  # Add new router
```

#### Step 7: Create Migration

```bash
alembic revision --autogenerate -m "Add events table"
alembic upgrade head
```

## 🔐 Security Best Practices

### 1. Password Security
- Passwords hashed with bcrypt (12 rounds)
- Never store plain text passwords
- Never return passwords in API responses

### 2. JWT Tokens
- 24-hour expiration
- Include minimal data (user_id, email, role)
- Verify signature on every request
- Stateless (no server-side session storage)

### 3. RBAC Implementation
- Middleware-based authorization
- Role checked on every protected endpoint
- Granular permission control

### 4. Input Validation
- Pydantic schemas validate all inputs
- Email format validation
- UMD email domain check
- Password strength requirements

## 📊 Database Design

### Current Schema (Phase 1)

```sql
users
├── id (PK, UUID)
├── email (UNIQUE)
├── password (HASHED)
├── name
├── role (ENUM: student, organizer, admin)
├── is_approved (BOOLEAN)
├── is_active (BOOLEAN)
├── phone
├── department
├── profile_picture
├── graduation_year
├── bio
├── created_at
├── updated_at
└── last_login
```

### Future Schema (Phases 2-6)

```
events
├── id
├── title
├── description
├── category_id (FK)
├── organizer_id (FK → users.id)
├── date, start_time, end_time
├── venue, location
├── capacity
├── status
└── timestamps

registrations
├── id
├── user_id (FK → users.id)
├── event_id (FK → events.id)
├── status
├── ticket_code
├── qr_code
└── timestamps

categories, venues, waitlist, notifications, etc.
```

## 🧪 Testing Strategy

### Unit Tests
- Test individual functions in services
- Mock database calls
- Test business logic

### Integration Tests
- Test API endpoints end-to-end
- Use test database
- Verify request/response flow

### Test Structure

```python
# tests/test_events.py
class TestEventCreation:
    def test_create_event_success(self, client, sample_organizer):
        # Arrange
        token = get_token(sample_organizer)
        
        # Act
        response = client.post(
            "/api/events",
            json={"title": "Test Event"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Assert
        assert response.status_code == 201
```

## 🚀 Deployment

### Environment Variables (Production)

```env
# Set strong values in production!
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=<strong-random-32+-char-string>
DEBUG=False
ENVIRONMENT=production
CORS_ORIGINS=https://terpspark.umd.edu
```

### Docker Deployment

```bash
# Build image
docker build -t terpspark-backend:v1 .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  terpspark-backend:v1
```

### Database Migrations in Production

```bash
# Always backup before migrations!
pg_dump terpspark_db > backup.sql

# Run migrations
alembic upgrade head

# Verify
alembic current
```

## 📈 Performance Considerations

### 1. Database Indexing
```python
# Add indexes for frequently queried fields
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_events_status ON events(status);
```

### 2. Connection Pooling
- Configured in `database.py`
- Pool size: 20
- Max overflow: 10

### 3. Caching Strategy
- JWT tokens cached client-side
- Future: Redis for session data
- Future: Cache frequently accessed data

## 🔄 Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/event-management

# 2. Implement feature (see guide above)

# 3. Write tests
pytest tests/test_events.py

# 4. Run linters
make lint

# 5. Format code
make format

# 6. Create migration
alembic revision --autogenerate -m "Add events"

# 7. Test migration
alembic upgrade head
alembic downgrade -1
alembic upgrade head

# 8. Commit and push
git add .
git commit -m "feat: add event management endpoints"
git push origin feature/event-management

# 9. Create pull request
```

## 📝 Code Style Guidelines

### Python Style
- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints
- Write docstrings for all functions

### Naming Conventions
- Classes: `PascalCase`
- Functions/Methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Example

```python
from typing import Optional

class UserService:
    """Service for user-related operations."""
    
    def __init__(self, db: Session):
        """
        Initialize service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()
```

## 🎯 Next Steps

### Immediate (Phase 2)
- [ ] Event model, repository, service
- [ ] Event browse/search endpoints
- [ ] Category and venue management
- [ ] Filtering and pagination

### Short-term (Phases 3-4)
- [ ] Registration system
- [ ] Waitlist management
- [ ] QR code generation
- [ ] Email notifications

### Long-term (Phases 5-6)
- [ ] Admin console
- [ ] Analytics dashboard
- [ ] Check-in system
- [ ] Real-time notifications (WebSocket)

---

## 💡 Tips for New Developers

1. **Start with tests**: Write tests first to understand expected behavior
2. **Read the docs**: Check FastAPI, SQLAlchemy, Pydantic docs
3. **Use the debugger**: Set breakpoints to understand flow
4. **Check logs**: Application logs are your friend
5. **Ask questions**: Better to clarify than assume

## 🐛 Common Issues & Solutions

**Issue**: `ModuleNotFoundError`
**Solution**: Ensure you're in the right directory and packages are installed

**Issue**: Database connection error
**Solution**: Check PostgreSQL is running and DATABASE_URL is correct

**Issue**: Alembic can't detect changes
**Solution**: Ensure models are imported in `alembic/env.py`

**Issue**: JWT token invalid
**Solution**: Check JWT_SECRET_KEY matches between token creation and validation

---

**Happy Coding! 🚀**
