"""
Main FastAPI application for TerpSpark Backend API.
Initializes the application, configures middleware, and includes routers.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
from app.core.config import settings
from app.core.database import engine, Base
from app.api import api_router

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Event management system for University of Maryland students",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
# Allow all origins in development for easier testing
cors_origins = settings.cors_origins_list if not settings.DEBUG else [
    "http://localhost:3000",
    "http://localhost:3030",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3030",
    "http://127.0.0.1:5173",
    "*",  # Allow all origins in development (includes localtunnel/ngrok)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else cors_origins,  # Allow all in debug mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with custom response format."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation failed",
            "code": "VALIDATION_FAILED",
            "details": exc.errors()
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Database error occurred",
            "code": "DATABASE_ERROR"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "An unexpected error occurred",
            "code": "INTERNAL_ERROR"
        }
    )


# Lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info(f"Shutting down {settings.APP_NAME}")


# Include API routers
app.include_router(api_router)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Database initialization endpoint (UNPROTECTED - Only use in development!)
@app.post("/init-db")
async def initialize_database():
    """
    Initialize database with sample data.

    **WARNING**: This endpoint will DROP ALL EXISTING DATA and recreate tables with dummy data.
    Only available in DEBUG mode for development purposes.

    **What it does:**
    - Drops all existing database tables
    - Recreates all tables from scratch
    - Populates with sample users, events, categories, and venues

    **Sample Credentials Created:**
    - Admin: admin@umd.edu / admin123
    - Organizers: organizer@umd.edu, techclub@umd.edu, sportsclub@umd.edu, artscenter@umd.edu / organizer123
    - Students: student@umd.edu, jane.smith@umd.edu, mike.wilson@umd.edu / student123
    - Pending Organizer: pending@umd.edu / pending123 (cannot login until approved)
    """
    if not settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "error": "Database initialization is only available in DEBUG mode",
                "code": "FORBIDDEN"
            }
        )

    try:
        from app.core.database import SessionLocal
        from app.models.user import User, UserRole
        from app.models.category import Category
        from app.models.venue import Venue
        from app.models.event import Event, EventStatus
        from app.core.security import get_password_hash
        from datetime import datetime, date, time, timedelta
        import uuid

        logger.info("Starting database initialization...")

        # Drop all tables
        logger.info("Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)

        # Recreate all tables
        logger.info("Creating fresh tables...")
        Base.metadata.create_all(bind=engine)

        db = SessionLocal()

        try:
            # Create sample users
            logger.info("Creating sample users...")
            users = []

            # Admin
            admin = User(
                id=str(uuid.uuid4()),
                email="admin@umd.edu",
                password=get_password_hash("admin123"),
                name="Admin User",
                role=UserRole.ADMIN,
                is_approved=True,
                department="Computer Science"
            )
            db.add(admin)
            users.append(admin)

            # Approved organizers
            organizers_data = [
                {"email": "organizer@umd.edu", "name": "Sarah Johnson", "department": "Student Affairs"},
                {"email": "techclub@umd.edu", "name": "Tech Club Organizer", "department": "Computer Science"},
                {"email": "sportsclub@umd.edu", "name": "Sports Events Team", "department": "Athletics"},
                {"email": "artscenter@umd.edu", "name": "Arts Center", "department": "Fine Arts"}
            ]

            for org_data in organizers_data:
                organizer = User(
                    id=str(uuid.uuid4()),
                    email=org_data["email"],
                    password=get_password_hash("organizer123"),
                    name=org_data["name"],
                    role=UserRole.ORGANIZER,
                    is_approved=True,
                    department=org_data["department"]
                )
                db.add(organizer)
                users.append(organizer)

            # Pending organizer
            pending_organizer = User(
                id=str(uuid.uuid4()),
                email="pending@umd.edu",
                password=get_password_hash("pending123"),
                name="Pending Organizer",
                role=UserRole.ORGANIZER,
                is_approved=False,
                department="Student Activities"
            )
            db.add(pending_organizer)
            users.append(pending_organizer)

            # Students
            students_data = [
                {"email": "student@umd.edu", "name": "John Student", "department": "Engineering", "grad_year": "2026"},
                {"email": "jane.smith@umd.edu", "name": "Jane Smith", "department": "Business", "grad_year": "2025"},
                {"email": "mike.wilson@umd.edu", "name": "Mike Wilson", "department": "Computer Science", "grad_year": "2026"},
                {"email": "emily.brown@umd.edu", "name": "Emily Brown", "department": "Biology", "grad_year": "2027"},
                {"email": "alex.davis@umd.edu", "name": "Alex Davis", "department": "Mathematics", "grad_year": "2025"}
            ]

            for student_data in students_data:
                student = User(
                    id=str(uuid.uuid4()),
                    email=student_data["email"],
                    password=get_password_hash("student123"),
                    name=student_data["name"],
                    role=UserRole.STUDENT,
                    is_approved=True,
                    department=student_data["department"],
                    graduation_year=student_data["grad_year"]
                )
                db.add(student)
                users.append(student)

            db.commit()
            logger.info(f"Created {len(users)} users")

            # Create categories
            logger.info("Creating categories...")
            categories_data = [
                {"name": "Academic", "slug": "academic", "color": "blue", "icon": "📚", "description": "Academic events, workshops, and lectures"},
                {"name": "Career", "slug": "career", "color": "green", "icon": "💼", "description": "Career fairs, networking events, and job opportunities"},
                {"name": "Cultural", "slug": "cultural", "color": "purple", "icon": "🌍", "description": "Cultural celebrations and multicultural events"},
                {"name": "Sports", "slug": "sports", "color": "red", "icon": "⚽", "description": "Sports events, tournaments, and fitness activities"},
                {"name": "Arts", "slug": "arts", "color": "pink", "icon": "🎨", "description": "Art exhibitions, performances, and creative workshops"},
                {"name": "Technology", "slug": "technology", "color": "indigo", "icon": "💻", "description": "Tech talks, hackathons, and innovation events"},
                {"name": "Wellness", "slug": "wellness", "color": "teal", "icon": "🧘", "description": "Health, wellness, and mindfulness events"},
                {"name": "Environmental", "slug": "environmental", "color": "emerald", "icon": "🌱", "description": "Environmental awareness and sustainability events"}
            ]

            categories = []
            for cat_data in categories_data:
                category = Category(
                    id=str(uuid.uuid4()),
                    name=cat_data["name"],
                    slug=cat_data["slug"],
                    color=cat_data["color"],
                    icon=cat_data["icon"],
                    description=cat_data["description"],
                    is_active=True
                )
                db.add(category)
                categories.append(category)

            db.commit()
            logger.info(f"Created {len(categories)} categories")

            # Create venues
            logger.info("Creating venues...")
            venues_data = [
                {"name": "Grand Ballroom", "building": "Stamp Student Union", "capacity": 500, "facilities": ["Projector", "Sound System", "WiFi", "Stage", "Microphones"]},
                {"name": "Auditorium", "building": "Edward St. John Learning & Teaching Center", "capacity": 300, "facilities": ["Projector", "Sound System", "WiFi", "Recording Equipment"]},
                {"name": "Conference Room A", "building": "Stamp Student Union", "capacity": 50, "facilities": ["Projector", "WiFi", "Whiteboard", "Conference Table"]},
                {"name": "Outdoor Amphitheater", "building": "Campus Drive", "capacity": 1000, "facilities": ["Sound System", "Stage", "Outdoor Seating"]},
                {"name": "McKeldin Library - Room 6137", "building": "McKeldin Library", "capacity": 100, "facilities": ["Projector", "WiFi", "Whiteboard"]},
                {"name": "Eppley Recreation Center - Gymnasium", "building": "Eppley Recreation Center", "capacity": 200, "facilities": ["Sound System", "Scoreboard", "Bleachers"]},
                {"name": "Engineering Classroom Building - Room 1180", "building": "Engineering Classroom Building", "capacity": 150, "facilities": ["Projector", "WiFi", "Recording Equipment", "Lab Equipment"]},
                {"name": "Art-Sociology Building - Gallery", "building": "Art-Sociology Building", "capacity": 75, "facilities": ["Gallery Lighting", "Display Walls", "WiFi"]}
            ]

            venues = []
            for venue_data in venues_data:
                venue = Venue(
                    id=str(uuid.uuid4()),
                    name=venue_data["name"],
                    building=venue_data["building"],
                    capacity=venue_data["capacity"],
                    facilities=venue_data["facilities"],
                    is_active=True
                )
                db.add(venue)
                venues.append(venue)

            db.commit()
            logger.info(f"Created {len(venues)} venues")

            # Create sample events
            logger.info("Creating sample events...")
            today = date.today()
            organizers = [u for u in users if u.role == UserRole.ORGANIZER and u.is_approved]

            events_data = [
                {
                    "title": "AI & Machine Learning Workshop",
                    "description": "Join us for an intensive hands-on workshop covering the fundamentals of AI and Machine Learning. Learn about neural networks, deep learning, and practical applications.",
                    "category": "Technology",
                    "organizer_email": "techclub@umd.edu",
                    "date": today + timedelta(days=7),
                    "start_time": "14:00",
                    "end_time": "17:00",
                    "venue": "Engineering Classroom Building - Room 1180",
                    "location": "Engineering Classroom Building, Room 1180, UMD Campus",
                    "capacity": 100,
                    "tags": ["AI", "Machine Learning", "Workshop", "Technology"],
                    "status": EventStatus.PUBLISHED
                },
                {
                    "title": "Spring Career Fair 2025",
                    "description": "Meet with top employers from various industries! Over 100 companies looking to hire UMD students for internships and full-time positions.",
                    "category": "Career",
                    "organizer_email": "organizer@umd.edu",
                    "date": today + timedelta(days=14),
                    "start_time": "10:00",
                    "end_time": "16:00",
                    "venue": "Grand Ballroom",
                    "location": "Stamp Student Union, Grand Ballroom",
                    "capacity": 500,
                    "tags": ["Career", "Job Fair", "Networking"],
                    "status": EventStatus.PUBLISHED
                },
                {
                    "title": "Hackathon 2025",
                    "description": "Join us for a 24-hour coding marathon! Build innovative solutions and compete for prizes.",
                    "category": "Technology",
                    "organizer_email": "techclub@umd.edu",
                    "date": today + timedelta(days=30),
                    "start_time": "09:00",
                    "end_time": "09:00",
                    "venue": "Grand Ballroom",
                    "location": "Stamp Student Union, Grand Ballroom",
                    "capacity": 200,
                    "tags": ["Hackathon", "Coding", "Technology"],
                    "status": EventStatus.PENDING
                }
            ]

            events = []
            for event_data in events_data:
                category = next(c for c in categories if c.name == event_data["category"])
                organizer = next(u for u in organizers if u.email == event_data["organizer_email"])

                start_hour, start_min = map(int, event_data["start_time"].split(":"))
                end_hour, end_min = map(int, event_data["end_time"].split(":"))

                event = Event(
                    id=str(uuid.uuid4()),
                    title=event_data["title"],
                    description=event_data["description"],
                    category_id=category.id,
                    organizer_id=organizer.id,
                    date=event_data["date"],
                    start_time=time(start_hour, start_min),
                    end_time=time(end_hour, end_min),
                    venue=event_data["venue"],
                    location=event_data["location"],
                    capacity=event_data["capacity"],
                    registered_count=0,
                    waitlist_count=0,
                    status=event_data["status"],
                    tags=event_data["tags"],
                    is_featured=event_data["status"] == EventStatus.PUBLISHED,
                    published_at=datetime.utcnow() if event_data["status"] == EventStatus.PUBLISHED else None
                )
                db.add(event)
                events.append(event)

            db.commit()
            logger.info(f"Created {len(events)} events")

            return {
                "success": True,
                "message": "Database initialized successfully with sample data",
                "summary": {
                    "users": len(users),
                    "admins": 1,
                    "organizers": len([u for u in users if u.role == UserRole.ORGANIZER and u.is_approved]),
                    "pending_organizers": 1,
                    "students": len([u for u in users if u.role == UserRole.STUDENT]),
                    "categories": len(categories),
                    "venues": len(venues),
                    "events": len(events),
                    "published_events": len([e for e in events if e.status == EventStatus.PUBLISHED]),
                    "pending_events": len([e for e in events if e.status == EventStatus.PENDING])
                },
                "credentials": {
                    "admin": {"email": "admin@umd.edu", "password": "admin123"},
                    "organizers": [
                        {"email": "organizer@umd.edu", "password": "organizer123"},
                        {"email": "techclub@umd.edu", "password": "organizer123"},
                        {"email": "sportsclub@umd.edu", "password": "organizer123"},
                        {"email": "artscenter@umd.edu", "password": "organizer123"}
                    ],
                    "students": [
                        {"email": "student@umd.edu", "password": "student123"},
                        {"email": "jane.smith@umd.edu", "password": "student123"},
                        {"email": "mike.wilson@umd.edu", "password": "student123"}
                    ],
                    "pending_organizer": {"email": "pending@umd.edu", "password": "pending123", "note": "Cannot login until approved"}
                }
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error during database initialization: {str(e)}")
            raise
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": f"Failed to initialize database: {str(e)}",
                "code": "INITIALIZATION_FAILED"
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
