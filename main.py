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


# Database events initialization endpoint (UNPROTECTED - Remove after use in production!)
@app.post("/init-db-events")
async def initialize_events():
    """
    Initialize database with 25 realistic events distributed among approved organizers.

    **WARNING**: This endpoint will DELETE ALL EXISTING EVENTS and create new sample events.
    Available in all environments - REMOVE THIS ENDPOINT after running in production!

    **What it does:**
    - Deletes all existing events
    - Creates 25 realistic events with researched data
    - Distributes events among all approved organizers
    - Uses existing categories and venues from database
    - Sets 2 events with only 1 seat remaining
    - Sets 3 events as fully booked
    - All events are in PUBLISHED status
    """

    try:
        from app.core.database import SessionLocal
        from app.models.user import User, UserRole
        from app.models.category import Category
        from app.models.venue import Venue
        from app.models.event import Event, EventStatus
        from datetime import datetime, date, time, timedelta
        import uuid

        logger.info("Starting events initialization...")

        db = SessionLocal()

        try:
            # Get all approved organizers
            organizers = db.query(User).filter(
                User.role == UserRole.ORGANIZER,
                User.is_approved == True
            ).all()

            if not organizers:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "error": "No approved organizers found in database",
                        "code": "NO_ORGANIZERS"
                    }
                )

            # Get all active categories
            categories = db.query(Category).filter(Category.is_active == True).all()
            if not categories:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "error": "No active categories found in database",
                        "code": "NO_CATEGORIES"
                    }
                )

            # Get all active venues
            venues = db.query(Venue).filter(Venue.is_active == True).all()
            if not venues:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "error": "No active venues found in database",
                        "code": "NO_VENUES"
                    }
                )

            # Helper function to find category by name
            def get_category(name):
                return next((c for c in categories if c.name.lower() == name.lower()), categories[0])

            # Helper function to find venue by capacity
            def get_venue_by_capacity(min_capacity):
                suitable = [v for v in venues if v.capacity >= min_capacity]
                return suitable[0] if suitable else venues[-1]

            # Delete all existing registrations first (due to foreign key constraints)
            logger.info("Deleting existing registrations...")
            from app.models.registration import Registration
            db.query(Registration).delete()
            db.commit()

            # Delete all existing events
            logger.info("Deleting existing events...")
            db.query(Event).delete()
            db.commit()

            # Create 25 realistic events
            logger.info("Creating 25 realistic events...")
            today = date.today()

            events_data = [
                {
                    "title": "Introduction to Quantum Computing",
                    "description": "Explore the fascinating world of quantum computing! Learn about qubits, quantum gates, and quantum algorithms. This workshop covers the basics of quantum mechanics as applied to computation, including hands-on exercises with IBM Quantum Experience. Perfect for students interested in cutting-edge technology.",
                    "category": "Technology",
                    "date_offset": 7,
                    "start_time": "14:00",
                    "end_time": "16:30",
                    "capacity": 80,
                    "registered": 0,
                    "tags": ["Quantum Computing", "Technology", "Workshop", "IBM"],
                    "image_url": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=800"
                },
                {
                    "title": "Annual College Park Half Marathon",
                    "description": "Join us for the 15th Annual College Park Half Marathon! This scenic 13.1-mile race takes runners through the beautiful UMD campus and surrounding neighborhoods. All skill levels welcome. Race includes timing chips, finisher medals, post-race refreshments, and live entertainment. Proceeds benefit local charities.",
                    "category": "Sports",
                    "date_offset": 21,
                    "start_time": "07:00",
                    "end_time": "12:00",
                    "capacity": 500,
                    "registered": 500,  # Fully booked
                    "tags": ["Marathon", "Running", "Sports", "Charity", "Fitness"],
                    "image_url": "https://images.unsplash.com/photo-1452626038306-9aae5e071dd3?w=800"
                },
                {
                    "title": "Cultural Night: Taste of Asia",
                    "description": "Experience the rich diversity of Asian cultures! This immersive cultural celebration features traditional performances including Chinese lion dance, Indian classical music, Japanese taiko drumming, and Korean K-pop. Enjoy authentic cuisine from various Asian countries, interactive cultural booths, and language workshops.",
                    "category": "Cultural",
                    "date_offset": 14,
                    "start_time": "18:00",
                    "end_time": "22:00",
                    "capacity": 300,
                    "registered": 300,  # Fully booked
                    "tags": ["Cultural", "Food", "Performance", "International", "Asia"],
                    "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800"
                },
                {
                    "title": "Cybersecurity Bootcamp: Ethical Hacking",
                    "description": "Learn the fundamentals of cybersecurity and ethical hacking in this intensive bootcamp. Topics include network security, penetration testing, vulnerability assessment, and security best practices. Hands-on labs include Kali Linux, Metasploit, and Wireshark. Led by industry professionals with real-world experience.",
                    "category": "Technology",
                    "date_offset": 10,
                    "start_time": "13:00",
                    "end_time": "17:00",
                    "capacity": 50,
                    "registered": 49,  # 1 seat left
                    "tags": ["Cybersecurity", "Hacking", "Security", "Bootcamp", "Networking"],
                    "image_url": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800"
                },
                {
                    "title": "Python Programming Fundamentals",
                    "description": "Master Python programming from scratch! This comprehensive course covers variables, data types, control structures, functions, object-oriented programming, and popular libraries like NumPy and Pandas. Includes hands-on coding exercises and real-world projects. No prior programming experience required.",
                    "category": "Technology",
                    "date_offset": 5,
                    "start_time": "15:00",
                    "end_time": "18:00",
                    "capacity": 60,
                    "registered": 59,  # 1 seat left
                    "tags": ["Python", "Programming", "Coding", "Beginner-Friendly"],
                    "image_url": "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800"
                },
                {
                    "title": "Resume Building & Interview Skills Workshop",
                    "description": "Land your dream job with expert guidance! Learn how to craft a compelling resume, write effective cover letters, and ace behavioral interviews. Includes one-on-one resume reviews, mock interview practice, and networking tips. Featuring recruiters from Fortune 500 companies sharing insider perspectives.",
                    "category": "Career",
                    "date_offset": 12,
                    "start_time": "16:00",
                    "end_time": "19:00",
                    "capacity": 100,
                    "registered": 82,
                    "tags": ["Career", "Resume", "Interview", "Professional Development"],
                    "image_url": "https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=800"
                },
                {
                    "title": "Mental Health Awareness Week Opening",
                    "description": "Join us for the launch of Mental Health Awareness Week! This opening event features keynote speakers discussing mental health on campus, stress management techniques, mindfulness meditation sessions, and resource fair with campus counseling services. Free wellness kits for all attendees.",
                    "category": "Wellness",
                    "date_offset": 8,
                    "start_time": "12:00",
                    "end_time": "15:00",
                    "capacity": 200,
                    "registered": 156,
                    "tags": ["Mental Health", "Wellness", "Mindfulness", "Self-Care"],
                    "image_url": "https://images.unsplash.com/photo-1545205597-3d9d02c29597?w=800"
                },
                {
                    "title": "Sustainability Summit: Campus Goes Green",
                    "description": "Explore innovative solutions for environmental sustainability! This summit brings together students, faculty, and environmental experts to discuss climate action, renewable energy, waste reduction, and sustainable living. Features panel discussions, eco-innovation showcase, and campus sustainability project presentations.",
                    "category": "Environmental",
                    "date_offset": 18,
                    "start_time": "09:00",
                    "end_time": "16:00",
                    "capacity": 150,
                    "registered": 128,
                    "tags": ["Sustainability", "Environment", "Climate", "Green Energy"],
                    "image_url": "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=800"
                },
                {
                    "title": "Basketball Tournament: Terps Challenge",
                    "description": "Show your basketball skills in the annual Terps Challenge! 3v3 tournament open to all students. Compete for prizes and bragging rights. Professional referees, tournament bracket system, and championship trophy for winners. Food trucks and DJ entertainment throughout the day. Team registration or individual sign-up available.",
                    "category": "Sports",
                    "date_offset": 25,
                    "start_time": "10:00",
                    "end_time": "18:00",
                    "capacity": 120,
                    "registered": 96,
                    "tags": ["Basketball", "Tournament", "Competition", "Sports"],
                    "image_url": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800"
                },
                {
                    "title": "Data Science Career Panel",
                    "description": "Get insights from data science professionals working at leading tech companies! Panel includes data scientists from Google, Amazon, Microsoft, and local startups. Discussion topics: career paths in data science, required skills, portfolio building, and industry trends in AI/ML. Q&A session and networking reception to follow.",
                    "category": "Career",
                    "date_offset": 15,
                    "start_time": "17:00",
                    "end_time": "19:30",
                    "capacity": 90,
                    "registered": 67,
                    "tags": ["Data Science", "Career", "Panel", "Technology", "AI"],
                    "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800"
                },
                {
                    "title": "Contemporary Art Exhibition Opening",
                    "description": "Celebrate creativity at our Contemporary Art Exhibition featuring works by talented UMD student artists! The exhibition showcases diverse media including painting, sculpture, photography, digital art, and mixed media installations. Opening reception includes artist talks, live music, and refreshments. Exhibition runs for two weeks.",
                    "category": "Arts",
                    "date_offset": 9,
                    "start_time": "18:30",
                    "end_time": "21:00",
                    "capacity": 75,
                    "registered": 58,
                    "tags": ["Art", "Exhibition", "Gallery", "Student Work", "Creative"],
                    "image_url": "https://images.unsplash.com/photo-1561214115-f2f134cc4912?w=800"
                },
                {
                    "title": "Startup Pitch Competition",
                    "description": "Present your startup idea to real investors! Students pitch innovative business ideas to a panel of venture capitalists and successful entrepreneurs. Winner receives $10,000 seed funding, mentorship, and office space. All participants get feedback and networking opportunities. Open to all majors and disciplines.",
                    "category": "Career",
                    "date_offset": 28,
                    "start_time": "14:00",
                    "end_time": "18:00",
                    "capacity": 200,
                    "registered": 175,
                    "tags": ["Startup", "Entrepreneurship", "Pitch", "Investment", "Innovation"],
                    "image_url": "https://images.unsplash.com/photo-1556761175-b413da4baf72?w=800"
                },
                {
                    "title": "Latin Dance Night: Salsa & Bachata",
                    "description": "Get ready to move! Learn salsa and bachata from professional dance instructors in this high-energy cultural celebration. Beginner-friendly with separate instruction sessions for different skill levels. Live Latin music band, dance performances, and social dancing. No partner required - we rotate throughout the evening!",
                    "category": "Cultural",
                    "date_offset": 11,
                    "start_time": "19:00",
                    "end_time": "23:00",
                    "capacity": 180,
                    "registered": 142,
                    "tags": ["Dance", "Latin", "Salsa", "Bachata", "Cultural", "Music"],
                    "image_url": "https://images.unsplash.com/photo-1504609773096-104ff2c73ba4?w=800"
                },
                {
                    "title": "Machine Learning Research Symposium",
                    "description": "Discover cutting-edge ML research happening at UMD! Faculty and graduate students present their latest research in deep learning, computer vision, natural language processing, and reinforcement learning. Poster session, networking with researchers, and discussion of collaboration opportunities. Great for undergrads considering research or grad school.",
                    "category": "Academic",
                    "date_offset": 20,
                    "start_time": "13:00",
                    "end_time": "17:30",
                    "capacity": 120,
                    "registered": 94,
                    "tags": ["Machine Learning", "Research", "AI", "Academic", "Symposium"],
                    "image_url": "https://images.unsplash.com/photo-1527474305487-b87b222841cc?w=800"
                },
                {
                    "title": "Yoga & Meditation Retreat",
                    "description": "Escape campus stress with a rejuvenating wellness retreat! Full day of guided yoga sessions (suitable for all levels), meditation workshops, mindfulness practices, and relaxation techniques. Includes healthy lunch, aromatherapy, sound healing, and take-home wellness toolkit. Perfect for stress relief during midterms.",
                    "category": "Wellness",
                    "date_offset": 13,
                    "start_time": "08:00",
                    "end_time": "16:00",
                    "capacity": 40,
                    "registered": 38,
                    "tags": ["Yoga", "Meditation", "Wellness", "Mindfulness", "Retreat"],
                    "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=800"
                },
                {
                    "title": "Gaming Tournament: League of Legends",
                    "description": "Battle for the championship in the UMD League of Legends Tournament! 5v5 competitive matches with prize pool totaling $2,000. Professional casters, live streaming, and viewing party. All ranks welcome with separate brackets for different skill tiers. Registration includes tournament jersey and exclusive in-game rewards.",
                    "category": "Sports",
                    "date_offset": 30,
                    "start_time": "11:00",
                    "end_time": "20:00",
                    "capacity": 100,
                    "registered": 100,  # Fully booked
                    "tags": ["Gaming", "Esports", "League of Legends", "Tournament", "Competition"],
                    "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800"
                },
                {
                    "title": "Photography Workshop: Portrait Lighting",
                    "description": "Master the art of portrait photography! Learn professional lighting techniques, camera settings, composition, and post-processing. Hands-on practice with studio equipment including softboxes, reflectors, and backdrops. Models provided for practice shots. Bring your DSLR or mirrorless camera. Beginner to intermediate level.",
                    "category": "Arts",
                    "date_offset": 16,
                    "start_time": "14:30",
                    "end_time": "18:30",
                    "capacity": 25,
                    "registered": 21,
                    "tags": ["Photography", "Portrait", "Lighting", "Workshop", "Arts"],
                    "image_url": "https://images.unsplash.com/photo-1554048612-b6a482bc67e5?w=800"
                },
                {
                    "title": "Climate Action Workshop",
                    "description": "Learn how to make a real environmental impact! Workshop covers carbon footprint reduction, sustainable lifestyle changes, campus composting program, renewable energy advocacy, and environmental policy. Interactive activities include building a terrarium and making eco-friendly products. Take action on climate change today!",
                    "category": "Environmental",
                    "date_offset": 22,
                    "start_time": "15:00",
                    "end_time": "18:00",
                    "capacity": 60,
                    "registered": 47,
                    "tags": ["Climate Change", "Environment", "Sustainability", "Workshop"],
                    "image_url": "https://images.unsplash.com/photo-1569163139394-de4798aa62b0?w=800"
                },
                {
                    "title": "Research Methods in Social Sciences",
                    "description": "Essential research methodology course for social science students! Topics include research design, quantitative and qualitative methods, statistical analysis with SPSS, survey design, interview techniques, and academic writing. Guest lectures from published researchers and hands-on data analysis projects. Earn research methodology certificate.",
                    "category": "Academic",
                    "date_offset": 6,
                    "start_time": "10:00",
                    "end_time": "14:00",
                    "capacity": 80,
                    "registered": 64,
                    "tags": ["Research", "Social Science", "Methodology", "Statistics"],
                    "image_url": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=800"
                },
                {
                    "title": "Jazz Night: Student Ensemble Performance",
                    "description": "Enjoy an evening of sophisticated jazz performed by the UMD Student Jazz Ensemble! The concert features classic jazz standards, contemporary compositions, and student arrangements. Showcases talented musicians on saxophone, trumpet, piano, bass, and drums. Wine and cheese reception follows the performance.",
                    "category": "Arts",
                    "date_offset": 19,
                    "start_time": "20:00",
                    "end_time": "22:30",
                    "capacity": 150,
                    "registered": 118,
                    "tags": ["Jazz", "Music", "Performance", "Concert", "Student"],
                    "image_url": "https://images.unsplash.com/photo-1415201364774-f6f0bb35f28f?w=800"
                },
                {
                    "title": "Blockchain & Cryptocurrency Seminar",
                    "description": "Understand the technology behind Bitcoin and blockchain! This seminar explains blockchain fundamentals, cryptocurrency economics, smart contracts, DeFi (Decentralized Finance), and NFTs. Industry experts discuss real-world applications and career opportunities. Learn about blockchain development and crypto investing basics.",
                    "category": "Technology",
                    "date_offset": 24,
                    "start_time": "16:30",
                    "end_time": "19:00",
                    "capacity": 110,
                    "registered": 89,
                    "tags": ["Blockchain", "Cryptocurrency", "Bitcoin", "Technology", "Finance"],
                    "image_url": "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800"
                },
                {
                    "title": "International Food Festival",
                    "description": "Taste the world at UMD! This spectacular food festival features authentic cuisine from 30+ countries prepared by international student organizations. Live cultural performances throughout the day including traditional music, dance, and fashion shows. Cooking demonstrations, cultural trivia, and recipe exchange. All-you-can-taste ticket includes sampling from all booths!",
                    "category": "Cultural",
                    "date_offset": 27,
                    "start_time": "11:00",
                    "end_time": "17:00",
                    "capacity": 400,
                    "registered": 362,
                    "tags": ["Food", "International", "Cultural", "Festival", "Diversity"],
                    "image_url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800"
                },
                {
                    "title": "Mock Interview Day with Industry Professionals",
                    "description": "Practice makes perfect! Get real interview experience with professionals from top companies. One-on-one mock interviews tailored to your field (technical, behavioral, or case interviews). Receive detailed feedback and improvement strategies. Industries represented: tech, finance, consulting, healthcare, and engineering. Limited spots available!",
                    "category": "Career",
                    "date_offset": 17,
                    "start_time": "09:00",
                    "end_time": "17:00",
                    "capacity": 50,
                    "registered": 45,
                    "tags": ["Career", "Interview", "Professional Development", "Networking"],
                    "image_url": "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=800"
                },
                {
                    "title": "Science Communication Workshop",
                    "description": "Learn to explain complex science to everyone! Workshop teaches effective science communication for diverse audiences. Topics include storytelling techniques, visual design, social media for science, public speaking, and science journalism. Perfect for STEM students, researchers, and aspiring science communicators. Practice sessions with feedback from communication professionals.",
                    "category": "Academic",
                    "date_offset": 23,
                    "start_time": "13:30",
                    "end_time": "17:00",
                    "capacity": 45,
                    "registered": 36,
                    "tags": ["Science", "Communication", "Public Speaking", "Academic"],
                    "image_url": "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800"
                },
                {
                    "title": "Ultimate Frisbee Spring League Kickoff",
                    "description": "Start of the Spring Ultimate Frisbee intramural season! Join teams for weekly games throughout the semester. All skill levels welcome - beginner clinic before first game. League includes regular season games, playoffs, and championship tournament. Make new friends while staying active. Equipment provided, just bring enthusiasm!",
                    "category": "Sports",
                    "date_offset": 4,
                    "start_time": "16:00",
                    "end_time": "19:00",
                    "capacity": 80,
                    "registered": 68,
                    "tags": ["Ultimate Frisbee", "Sports", "Intramural", "Recreation"],
                    "image_url": "https://images.unsplash.com/photo-1587280501635-68a0e82cd5ff?w=800"
                }
            ]

            # Distribute events among organizers
            events = []
            for i, event_data in enumerate(events_data):
                organizer = organizers[i % len(organizers)]
                category = get_category(event_data["category"])

                # Calculate venue based on capacity
                venue = get_venue_by_capacity(event_data["capacity"])

                event_date = today + timedelta(days=event_data["date_offset"])
                start_hour, start_min = map(int, event_data["start_time"].split(":"))
                end_hour, end_min = map(int, event_data["end_time"].split(":"))

                event = Event(
                    id=str(uuid.uuid4()),
                    title=event_data["title"],
                    description=event_data["description"],
                    category_id=category.id,
                    organizer_id=organizer.id,
                    date=event_date,
                    start_time=time(start_hour, start_min),
                    end_time=time(end_hour, end_min),
                    venue=venue.name,
                    location=f"{venue.building}, {venue.name}",
                    capacity=event_data["capacity"],
                    registered_count=event_data["registered"],
                    waitlist_count=0,
                    status=EventStatus.PUBLISHED,
                    tags=event_data["tags"],
                    image_url=event_data.get("image_url"),
                    is_featured=True,
                    published_at=datetime.utcnow()
                )
                db.add(event)
                events.append(event)

            db.commit()
            logger.info(f"Created {len(events)} events")

            # Count special events
            one_seat_left = len([e for e in events if e.capacity - e.registered_count == 1])
            fully_booked = len([e for e in events if e.registered_count >= e.capacity])

            return {
                "success": True,
                "message": "Events initialized successfully",
                "summary": {
                    "total_events": len(events),
                    "published_events": len(events),
                    "organizers_used": len(organizers),
                    "events_with_one_seat_left": one_seat_left,
                    "fully_booked_events": fully_booked,
                    "categories_used": len(set(e.category_id for e in events)),
                    "venues_used": len(set(e.venue for e in events))
                },
                "organizer_distribution": {
                    org.email: len([e for e in events if e.organizer_id == org.id])
                    for org in organizers
                }
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error during events initialization: {str(e)}")
            raise
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to initialize events: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": f"Failed to initialize events: {str(e)}",
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
