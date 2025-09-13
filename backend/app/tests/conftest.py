import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db import Base, get_db
from app import models, security

#test database setup
#use an in-memory sqlite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Fixture to create a fresh database for the entire test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
def override_get_db():
    """Dependency override to use the test database instead of the real one."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    """Provides a TestClient instance for making API requests in tests."""
    return TestClient(app)

@pytest.fixture(scope="function")
def test_user(client):
    """Creates a test user in the database for use in auth tests."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "role": "admin"
    }
    
    db = TestingSessionLocal()
    existing_user = db.query(models.User).filter(models.User.username == user_data["username"]).first()
    if existing_user:
        db.delete(existing_user)
        db.commit()

    hashed_password = security.get_password_hash(user_data["password"])
    new_user = models.User(
        username=user_data["username"], 
        email=user_data["email"],
        hashed_password=hashed_password,
        role=user_data["role"]
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    

    return user_data 