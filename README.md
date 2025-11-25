# TerpSpark Backend API

A comprehensive event management system API for University of Maryland students, built with FastAPI, PostgreSQL, and SQLAlchemy.

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Data Models](#data-models)
- [API Routes](#api-routes)
- [Setup & Installation](#setup--installation)
- [Running the Project](#running-the-project)
- [API Documentation](#api-documentation)
- [Testing](#testing)

---

## 🎯 Overview

TerpSpark Backend provides a robust REST API for managing campus events, including:
- **User Authentication** (Students, Organizers, Admins)
- **Event Discovery & Browse** with advanced filtering
- **Event Registration** (Coming in Phase 3)
- **Organizer Event Management** (Coming in Phase 4)
- **Admin Console** (Coming in Phase 5)

---

## 🛠 Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **Validation**: Pydantic v2
- **Migration**: Alembic
- **Testing**: Pytest
- **Code Quality**: Black, Flake8, MyPy

---

## 📊 Data Models

All models are fully implemented with proper relationships and validation:

### 1. **User** (`app/models/user.py`)
```python
- id: string (UUID)
- email: string (must be @umd.edu)
- password: string (hashed)
- name: string
- role: enum (student | organizer | admin)
- is_approved: boolean
- department: string (optional)
- phone: string (optional)
- profile_picture: string (optional)
- graduation_year: string (optional)
- bio: string (optional)
- created_at: datetime
- updated_at: datetime
- last_login: datetime
```

### 2. **Category** (`app/models/category.py`)
```python
- id: string (UUID)
- name: string
- slug: string (unique)
- description: text
- color: string (UI color code)
- icon: string
- is_active: boolean
- created_at: datetime
- updated_at: datetime
```

**Predefined Categories:**
- Academic 📚 (blue)
- Career 💼 (green)
- Cultural 🌍 (purple)
- Sports ⚽ (red)
- Arts 🎨 (pink)
- Technology 💻 (indigo)
- Wellness 🧘 (teal)
- Environmental 🌱 (emerald)

### 3. **Venue** (`app/models/venue.py`)
```python
- id: string (UUID)
- name: string
- building: string
- capacity: integer
- facilities: JSON array
- is_active: boolean
- created_at: datetime
- updated_at: datetime
```

### 4. **Event** (`app/models/event.py`)
```python
- id: string (UUID)
- title: string
- description: text
- category_id: foreign key
- organizer_id: foreign key
- date: date (YYYY-MM-DD)
- start_time: time (HH:MM)
- end_time: time (HH:MM)
- venue: string
- location: string
- capacity: integer (1-5000)
- registered_count: integer
- waitlist_count: integer
- status: enum (draft | pending | published | cancelled)
- image_url: string (optional)
- tags: JSON array
- is_featured: boolean
- created_at: datetime
- updated_at: datetime
- published_at: datetime
- cancelled_at: datetime
```

### 5. **Registration** (`app/models/registration.py`)
```python
- id: string (UUID)
- user_id: foreign key
- event_id: foreign key
- status: enum (confirmed | cancelled)
- ticket_code: string (unique)
- qr_code: string (base64 or URL)
- registered_at: datetime
- check_in_status: enum (not_checked_in | checked_in)
- checked_in_at: datetime
- guests: JSON array (max 2 guests)
- sessions: JSON array
- reminder_sent: boolean
- cancelled_at: datetime
```

### 6. **WaitlistEntry** (`app/models/waitlist.py`)
```python
- id: string (UUID)
- user_id: foreign key
- event_id: foreign key
- position: integer (FIFO ordering)
- joined_at: datetime
- notification_preference: enum (email | sms | both)
```

### 7. **OrganizerApprovalRequest** (`app/models/organizer_approval.py`)
```python
- id: string (UUID)
- user_id: foreign key
- reason: text
- status: enum (pending | approved | rejected)
- reviewed_by: foreign key (admin user)
- notes: text
- requested_at: datetime
- reviewed_at: datetime
```

### 8. **AuditLog** (`app/models/audit_log.py`)
```python
- id: string (UUID)
- timestamp: datetime
- action: enum (20+ action types)
- actor_id: foreign key
- actor_name: string
- actor_role: string
- target_type: enum (user | event | category | venue | etc.)
- target_id: string
- target_name: string
- details: text
- extra_metadata: JSON
- ip_address: string
- user_agent: string
```

---

## 🌐 API Routes

### ✅ Phase 1: Authentication & User Management

#### **POST** `/api/auth/register`
Register a new user account.
- **Body**: `{ email, password, name, role?, department?, phone? }`
- **Returns**: User object + JWT token
- **Rules**: 
  - Email must be @umd.edu
  - Password min 8 characters
  - Students auto-approved
  - Organizers require admin approval

#### **POST** `/api/auth/login`
Authenticate user and get JWT token.
- **Body**: `{ email, password }`
- **Returns**: User object + JWT token
- **Errors**: 
  - 401: Invalid credentials
  - 403: Organizer not approved

#### **POST** `/api/auth/logout`
Log out current user.
- **Headers**: `Authorization: Bearer {token}`
- **Returns**: Success message

#### **GET** `/api/auth/validate`
Validate JWT token.
- **Headers**: `Authorization: Bearer {token}`
- **Returns**: `{ valid: true, user: {...} }`

#### **GET** `/api/auth/user`
Get current authenticated user details.
- **Headers**: `Authorization: Bearer {token}`
- **Returns**: Full user object

---

### ✅ Phase 2: Event Discovery & Browse

#### **GET** `/api/events`
List all published events with filtering and pagination.

**Query Parameters:**
- `search` - Search in title, description, tags, venue
- `category` - Category slug (e.g., "technology", "sports")
- `startDate` - Filter events after date (YYYY-MM-DD)
- `endDate` - Filter events before date (YYYY-MM-DD)
- `organizer` - Organizer name search
- `availability` - Show only events with available spots
- `sortBy` - Sort by: `date` | `title` | `popularity` (default: date)
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 20, max: 100)

**Response:**
```json
{
  "success": true,
  "events": [
    {
      "id": "...",
      "title": "AI & Machine Learning Workshop",
      "description": "...",
      "category": {
        "id": "...",
        "name": "Technology",
        "slug": "technology",
        "color": "indigo"
      },
      "organizer": {
        "id": "...",
        "name": "Tech Club",
        "email": "techclub@umd.edu",
        "department": "Computer Science"
      },
      "date": "2025-12-02",
      "startTime": "14:00",
      "endTime": "17:00",
      "venue": "Engineering Building",
      "location": "Engineering Classroom Building, Room 1180",
      "capacity": 100,
      "registeredCount": 75,
      "waitlistCount": 0,
      "status": "published",
      "tags": ["AI", "Machine Learning", "Workshop"],
      "isFeatured": true,
      "createdAt": "...",
      "publishedAt": "..."
    }
  ],
  "pagination": {
    "currentPage": 1,
    "totalPages": 1,
    "totalItems": 5,
    "itemsPerPage": 20
  }
}
```

#### **GET** `/api/events/{event_id}`
Get detailed information for a specific event.

**Response:**
```json
{
  "success": true,
  "event": {
    "id": "...",
    "title": "...",
    "description": "...",
    "category": {...},
    "organizer": {...},
    "date": "2025-12-02",
    "startTime": "14:00",
    "endTime": "17:00",
    "venue": "...",
    "location": "...",
    "capacity": 100,
    "registeredCount": 75,
    "waitlistCount": 0,
    "remainingCapacity": 25,
    "status": "published",
    "imageUrl": null,
    "tags": [...],
    "isFeatured": true,
    "createdAt": "...",
    "updatedAt": "...",
    "publishedAt": "...",
    "cancelledAt": null
  }
}
```

#### **GET** `/api/categories`
Get all active event categories.

**Response:**
```json
{
  "success": true,
  "categories": [
    {
      "id": "...",
      "name": "Technology",
      "slug": "technology",
      "description": "Tech events",
      "color": "indigo",
      "icon": "💻",
      "isActive": true,
      "createdAt": "...",
      "updatedAt": "..."
    }
  ]
}
```

#### **GET** `/api/venues`
Get all active venues.

**Response:**
```json
{
  "success": true,
  "venues": [
    {
      "id": "...",
      "name": "Grand Ballroom",
      "building": "Stamp Student Union",
      "capacity": 500,
      "facilities": ["Projector", "Sound System", "WiFi", "Stage"],
      "isActive": true,
      "createdAt": "...",
      "updatedAt": "..."
    }
  ]
}
```

---

### 🔜 Coming Soon

- **Phase 3**: Student Registration Flow
- **Phase 4**: Organizer Event Management
- **Phase 5**: Admin Console & Management

---

## 🚀 Setup & Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- pip (Python package manager)

### 1. Clone the Repository

```bash
cd /path/to/terpspark-backend
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Additional Required Packages

```bash
pip install email-validator
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/terpspark

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# App Settings
APP_NAME=TerpSpark Backend API
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### 6. Initialize Database

The database tables will be created automatically when you start the server for the first time.

To populate with sample data:

```bash
# Option 1: Run the full initialization script
PYTHONPATH=. python app/utils/init_db.py

# Option 2: If you already have users, just add categories and events
PYTHONPATH=. python add_categories_and_events.py
```

---

## 🏃 Running the Project

### Start the Development Server

```bash
# From project root
python -m uvicorn main:app --reload --port 8000

# Or using the venv python directly
venv/bin/python -m uvicorn main:app --reload --port 8000
```

The server will start at: **http://127.0.0.1:8000**

### Verify Server is Running

Visit these URLs in your browser:

- **API Health**: http://127.0.0.1:8000/health
- **API Info**: http://127.0.0.1:8000/
- **Interactive Docs**: http://127.0.0.1:8000/docs
- **Alternative Docs**: http://127.0.0.1:8000/redoc

---

## 📚 API Documentation

### Interactive API Documentation (Swagger UI)

Visit **http://127.0.0.1:8000/docs** for:
- Complete API endpoint listing
- Request/response schemas
- Try out API calls directly in browser
- Authentication testing

### Alternative Documentation (ReDoc)

Visit **http://127.0.0.1:8000/redoc** for:
- Clean, readable API documentation
- Search functionality
- Download as OpenAPI spec

---

## 🧪 Testing

### Sample Data & Credentials

After running the initialization script, you'll have:

#### **Users:**

**Admin:**
- Email: `admin@umd.edu`
- Password: `admin123`

**Organizers:**
- Email: `organizer@umd.edu` / Password: `organizer123`
- Email: `techclub@umd.edu` / Password: `organizer123`
- Email: `sportsclub@umd.edu` / Password: `organizer123`
- Email: `artscenter@umd.edu` / Password: `organizer123`

**Students:**
- Email: `student@umd.edu` / Password: `student123`
- Email: `jane.smith@umd.edu` / Password: `student123`
- Email: `mike.wilson@umd.edu` / Password: `student123`

**Pending Organizer (cannot login):**
- Email: `pending@umd.edu` / Password: `pending123`

#### **Sample Events:**
- AI & Machine Learning Workshop (Dec 2, 2025)
- Spring Career Fair 2025 (Dec 9, 2025)
- International Food Festival (Dec 16, 2025)
- Basketball Tournament Finals (Dec 5, 2025)
- Mindfulness & Meditation (Nov 30, 2025)

### Testing API Endpoints

#### 1. **Register a New User**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newstudent@umd.edu",
    "password": "password123",
    "name": "New Student",
    "role": "student",
    "department": "Computer Science"
  }'
```

#### 2. **Login**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
  "email": "student@umd.edu",
    "password": "student123"
  }'
```

Save the returned `token` for authenticated requests.

#### 3. **List Events**
```bash
# Get all events
curl http://127.0.0.1:8000/api/events

# Filter by category
curl http://127.0.0.1:8000/api/events?category=technology

# Search events
curl "http://127.0.0.1:8000/api/events?search=basketball"

# Filter by date range
curl "http://127.0.0.1:8000/api/events?startDate=2025-12-01&endDate=2025-12-31"

# Sort by popularity
curl "http://127.0.0.1:8000/api/events?sortBy=popularity"
```

#### 4. **Get Event Details**
```bash
curl http://127.0.0.1:8000/api/events/{event_id}
```

#### 5. **Get Categories**
```bash
curl http://127.0.0.1:8000/api/categories
```

#### 6. **Get Venues**
```bash
curl http://127.0.0.1:8000/api/venues
```

#### 7. **Authenticated Request (Get Current User)**
```bash
curl http://127.0.0.1:8000/api/auth/user \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Run Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

---

## 📁 Project Structure

```
terpspark-backend/
├── app/
│   ├── api/                    # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication routes
│   │   └── events.py          # Event routes (Phase 2)
│   ├── core/                   # Core configuration
│   │   ├── config.py          # Environment settings
│   │   ├── database.py        # Database connection
│   │   └── security.py        # JWT & password hashing
│   ├── middleware/             # Custom middleware
│   │   ├── __init__.py
│   │   └── auth.py            # Authentication middleware
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── venue.py
│   │   ├── event.py
│   │   ├── registration.py
│   │   ├── waitlist.py
│   │   ├── organizer_approval.py
│   │   └── audit_log.py
│   ├── repositories/           # Data access layer
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── category_repository.py
│   │   ├── venue_repository.py
│   │   ├── event_repository.py
│   │   ├── registration_repository.py
│   │   ├── waitlist_repository.py
│   │   ├── organizer_approval_repository.py
│   │   └── audit_log_repository.py
│   ├── schemas/                # Pydantic validation schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── category.py
│   │   ├── venue.py
│   │   ├── event.py
│   │   ├── registration.py
│   │   ├── waitlist.py
│   │   ├── organizer_approval.py
│   │   └── audit_log.py
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── event_service.py
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── init_db.py         # Database initialization script
├── tests/                      # Unit tests
│   ├── __init__.py
│   ├── conftest.py
│   └── test_auth.py
├── alembic/                    # Database migrations
│   ├── env.py
│   └── versions/
├── logs/                       # Application logs
├── .env                        # Environment variables (create this)
├── .env.example                # Environment template
├── .gitignore
├── alembic.ini                 # Alembic configuration
├── main.py                     # FastAPI application entry point
├── requirements.txt            # Python dependencies
├── Makefile                    # Useful commands
├── README.md                   # This file
└── Backend README.md           # Complete API specifications
```

---

## 🔑 Key Features Implemented

### ✅ **Repository Pattern**
- Clean separation between data access and business logic
- All database operations isolated in repository classes
- Easy to test and maintain

### ✅ **Service Layer**
- Business logic separated from API routes
- Reusable service methods across different endpoints
- Centralized validation and error handling

### ✅ **Comprehensive Data Models**
- 8 fully-featured SQLAlchemy models
- Proper relationships and foreign keys
- Enums for type safety
- JSON fields for flexible data storage

### ✅ **Advanced Filtering & Search**
- Multi-field search capability
- Category filtering by slug
- Date range filtering
- Availability filtering
- Multiple sort options
- Pagination with metadata

### ✅ **Authentication & Security**
- JWT token-based authentication
- Bcrypt password hashing
- Role-based access control (RBAC)
- Email validation (@umd.edu required)
- Token expiration and refresh

### ✅ **API Documentation**
- Auto-generated OpenAPI/Swagger docs
- Interactive API testing in browser
- Complete request/response examples
- Error code documentation

### ✅ **Code Quality**
- Type hints throughout
- Comprehensive docstrings
- Pydantic validation
- No linter errors
- Follows Python best practices

---

## 🔧 Common Commands

### Database Management

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Run migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

### Development

```bash
# Format code
black app/

# Check code style
flake8 app/

# Type checking
mypy app/

# Run linter
pylint app/
```

### Docker (Optional)

```bash
# Build image
docker build -t terpspark-backend .

# Run container
docker-compose up

# Stop container
docker-compose down
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'email_validator'"
**Solution:**
```bash
pip install email-validator
```

### Issue: "Database connection failed"
**Solution:**
1. Check PostgreSQL is running: `pg_isready`
2. Verify DATABASE_URL in `.env` file
3. Ensure database exists: `createdb terpspark`

### Issue: "Port 8000 already in use"
**Solution:**
```bash
# Use different port
uvicorn main:app --reload --port 8001

# Or kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Issue: "Empty events list"
**Solution:**
```bash
# Populate database with sample data
PYTHONPATH=. python add_categories_and_events.py
```

---

## 📖 Additional Documentation

- **[Backend README.md](./Backend%20README.md)** - Complete API specifications for all 5 phases
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture details
- **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** - Database migration guide
- **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** - Project overview and goals

---

## 🎯 Roadmap

### ✅ Completed
- [x] Phase 1: Authentication & User Management
- [x] Phase 2: Event Discovery & Browse
- [x] Database models for all phases
- [x] Repository pattern implementation
- [x] Comprehensive test data

### 🚧 In Progress
- [ ] Phase 3: Student Registration Flow
- [ ] Phase 4: Organizer Event Management
- [ ] Phase 5: Admin Console & Management

### 📅 Future Enhancements
- [ ] Real-time notifications (WebSocket)
- [ ] Email/SMS integration
- [ ] QR code generation for tickets
- [ ] Analytics dashboard
- [ ] Event recommendations
- [ ] Social features (comments, ratings)
- [ ] File upload for event images
- [ ] Calendar integration
- [ ] Mobile app API support

---

## 👥 Contributors

- **Development Team**: CMSC 613 Final Project Team
- **Institution**: University of Maryland, College Park
- **Course**: CMSC 613 - Software Engineering

---

## 📝 License

This project is part of an academic course and is intended for educational purposes.

---

## 🆘 Support

For issues, questions, or contributions:
1. Check the troubleshooting section above
2. Review the [Backend README.md](./Backend%20README.md) for detailed API specs
3. Check the interactive docs at `/docs` when the server is running
4. Contact the development team

---

**Last Updated**: November 25, 2025

**Version**: 1.0.0 (Phase 2 Complete)

**API Status**: ✅ Running at http://127.0.0.1:8000
