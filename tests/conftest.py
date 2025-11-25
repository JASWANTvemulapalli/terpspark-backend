"""
Pytest configuration file.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from main import app
import uuid

# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create test client."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_student(db):
    """Create a sample student user."""
    user = User(
        id=str(uuid.uuid4()),
        email="teststudent@umd.edu",
        password=get_password_hash("password123"),
        name="Test Student",
        role=UserRole.STUDENT,
        is_approved=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_organizer(db):
    """Create a sample approved organizer."""
    user = User(
        id=str(uuid.uuid4()),
        email="testorganizer@umd.edu",
        password=get_password_hash("password123"),
        name="Test Organizer",
        role=UserRole.ORGANIZER,
        is_approved=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_admin(db):
    """Create a sample admin user."""
    user = User(
        id=str(uuid.uuid4()),
        email="testadmin@umd.edu",
        password=get_password_hash("password123"),
        name="Test Admin",
        role=UserRole.ADMIN,
        is_approved=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
