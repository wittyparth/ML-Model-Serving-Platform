"""Test configuration and fixtures"""
import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.model import Model
from app.core.security import get_password_hash

# Use PostgreSQL test database (same as dev but different schema)
SQLALCHEMY_DATABASE_URL = "postgresql://mluser:mlpassword@db:5432/mlplatform"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup test database before all tests"""
    # Drop all tables and recreate them
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup after all tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database session with automatic cleanup"""
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        # Clean up all data after each test (in reverse order to handle foreign keys)
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture(scope="function")
def client(db):
    """Create test client"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        is_active=True,
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session):
    """Create an admin user"""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Admin User",
        is_active=True,
        is_admin=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient, test_user: User):
    """Get authentication headers for test user"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client: TestClient, admin_user: User):
    """Get authentication headers for admin user"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def temp_model_file():
    """Create a temporary model file for testing"""
    import joblib
    from sklearn.linear_model import LogisticRegression
    
    # Create a simple model
    model = LogisticRegression()
    
    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.pkl', delete=False)
    joblib.dump(model, temp_file.name)
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


@pytest.fixture
def test_model(db: Session, test_user: User, temp_model_file: str):
    """Create a test model in the database"""
    model = Model(
        user_id=test_user.id,
        name="test_model",
        description="Test model for testing",
        model_type="sklearn",
        version=1,
        file_path=temp_model_file,
        file_size=1024,
        status="active"
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
