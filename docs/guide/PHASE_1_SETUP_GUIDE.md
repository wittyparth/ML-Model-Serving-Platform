# 📚 Phase 1: Setup & Infrastructure - Learning Guide

**What You'll Learn:**
- Project structure organization
- Database setup with PostgreSQL
- Alembic migrations
- Environment configuration
- Docker multi-container setup

---

## 🎯 What We Built in Phase 1

### 1. Project Structure
```
ML-Model-Serving-Platform/
├── app/
│   ├── __init__.py           # Makes 'app' a Python package
│   ├── main.py               # FastAPI application entry point
│   ├── api/
│   │   ├── v1/               # API version 1 endpoints
│   │   └── dependencies.py   # Shared dependencies (auth, db)
│   ├── core/
│   │   ├── config.py         # Settings and configuration
│   │   ├── security.py       # Auth utilities (JWT, passwords)
│   │   └── logging.py        # Logging configuration
│   ├── db/
│   │   ├── base.py           # SQLAlchemy Base class
│   │   └── session.py        # Database session management
│   ├── models/               # Database models (SQLAlchemy ORM)
│   └── schemas/              # Pydantic schemas (request/response)
├── alembic/                  # Database migrations
├── tests/                    # Test files
├── docker-compose.yml        # Multi-container orchestration
├── Dockerfile                # API container definition
└── requirements.txt          # Python dependencies
```

**Why This Structure?**
- **Separation of Concerns**: Each folder has a specific purpose
- **Scalability**: Easy to add new features without breaking existing code
- **Testability**: Clear boundaries make testing easier
- **Maintainability**: New developers can understand the codebase quickly

---

## 🐘 PostgreSQL Database Setup

### What is PostgreSQL?
PostgreSQL is a powerful, open-source relational database. We chose it because:
- ✅ ACID compliant (Atomic, Consistent, Isolated, Durable)
- ✅ Supports complex queries and relationships
- ✅ JSON support for flexible data
- ✅ UUID type for unique IDs
- ✅ Production-ready and scalable

### Docker Setup (docker-compose.yml)
```yaml
services:
  db:
    image: postgres:15                    # PostgreSQL version 15
    container_name: mlplatform_db
    environment:
      POSTGRES_USER: mluser               # Database username
      POSTGRES_PASSWORD: mlpassword       # Database password
      POSTGRES_DB: mlplatform            # Database name
    ports:
      - "5432:5432"                       # Host:Container port mapping
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Persist data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mluser -d mlplatform"]
      interval: 10s                       # Check every 10 seconds
      timeout: 5s
      retries: 5
```

**Key Concepts:**
1. **Ports**: `5432:5432` means host port 5432 maps to container port 5432
2. **Volumes**: Data persists even when container stops
3. **Health Checks**: Ensures database is ready before starting API
4. **Environment Variables**: Configuration without hardcoding

**Common Mistakes:**
❌ Not using volumes → Data lost when container restarts
❌ Using weak passwords → Security risk
❌ No health checks → API starts before DB is ready
❌ Hardcoding credentials → Can't change without rebuilding

---

## 🔄 Alembic Database Migrations

### What are Migrations?
Migrations are version control for your database schema. They track changes like:
- Creating tables
- Adding columns
- Modifying relationships
- Renaming fields

**Why Use Migrations?**
- ✅ Track database changes over time
- ✅ Rollback if something goes wrong
- ✅ Team collaboration (everyone has same schema)
- ✅ Deploy changes safely to production

### Setup Alembic

#### 1. Initialize Alembic
```bash
alembic init alembic
```

This creates:
```
alembic/
├── env.py              # Migration environment configuration
├── script.py.mako      # Template for new migrations
└── versions/           # Migration files go here
```

#### 2. Configure `alembic/env.py`

**Before** (default):
```python
target_metadata = None
```

**After** (our setup):
```python
from app.db.base import Base
from app.models.user import User
from app.models.model import Model
from app.models.prediction import Prediction
from app.models.api_key import APIKey

target_metadata = Base.metadata
```

**Why?** Alembic needs to know about your models to auto-generate migrations.

#### 3. Configure `alembic.ini`

Change:
```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

To:
```ini
sqlalchemy.url = postgresql://mluser:mlpassword@db:5432/mlplatform
```

Or better, use environment variables:
```python
# In alembic/env.py
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

### Creating Migrations

#### Auto-generate from models:
```bash
alembic revision --autogenerate -m "Initial migration"
```

This creates a file like `versions/abc123_initial_migration.py`:
```python
def upgrade():
    # Creates tables, adds columns, etc.
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Reverts the changes
    op.drop_table('users')
```

#### Apply migrations:
```bash
alembic upgrade head
```

#### Rollback:
```bash
alembic downgrade -1  # Go back 1 migration
```

**Common Mistakes:**
❌ Not importing all models in `env.py` → Tables not created
❌ Editing migrations after they're applied → Inconsistent state
❌ Not reviewing auto-generated migrations → May create wrong schema
❌ Running migrations directly on production → Use CI/CD instead

---

## ⚙️ Environment Configuration

### Why Use Environment Variables?
- ✅ Different configs for dev/staging/prod
- ✅ Keep secrets out of code
- ✅ Easy to change without redeploying

### Using Pydantic Settings

**`app/core/config.py`:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://mluser:mlpassword@db:5432/mlplatform"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # App
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"  # Load from .env file
        case_sensitive = True

settings = Settings()
```

**`.env` file:**
```env
DATABASE_URL=postgresql://mluser:mlpassword@db:5432/mlplatform
SECRET_KEY=super-secret-key-change-me
REDIS_URL=redis://redis:6379/0
DEBUG=True
```

**Benefits:**
- Type validation (Pydantic checks types)
- Default values
- Environment variable override
- Auto-completion in IDE

**Common Mistakes:**
❌ Committing `.env` to git → Secrets exposed
❌ Not using `.env.example` → Team doesn't know what vars are needed
❌ Hardcoding secrets → Can't change without code deploy
❌ No validation → Wrong types cause runtime errors

---

## 🐳 Docker Multi-Container Setup

### What We're Running

**3 Containers:**
1. **PostgreSQL** - Database
2. **Redis** - Cache & rate limiting
3. **FastAPI** - Web API

### Complete `docker-compose.yml` Explained

```yaml
services:
  # PostgreSQL Database
  db:
    image: postgres:15                      # Pre-built image
    container_name: mlplatform_db           # Custom name
    environment:                            # Environment variables
      POSTGRES_USER: mluser
      POSTGRES_PASSWORD: mlpassword
      POSTGRES_DB: mlplatform
    ports:
      - "5432:5432"                         # Expose to host
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Named volume
    healthcheck:                            # Check if ready
      test: ["CMD-SHELL", "pg_isready -U mluser -d mlplatform"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine                   # Lightweight Redis
    container_name: mlplatform_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data                    # Persist cache
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # FastAPI Application
  api:
    build: .                                # Build from Dockerfile
    container_name: mlplatform_api
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app                              # Bind mount (live reload)
      - ./models:/app/models                # Model storage
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://mluser:mlpassword@db:5432/mlplatform
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=True
    depends_on:                             # Wait for these
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:                                    # Named volumes
  postgres_data:
  redis_data:
```

### Dockerfile for API

```dockerfile
FROM python:3.11-slim                       # Base image

WORKDIR /app                                # Set working directory

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \                                   # For compiling packages
    postgresql-client \                     # For psql commands
    && rm -rf /var/lib/apt/lists/*          # Clean up

# Copy requirements first (caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p /app/models

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Why This Order?**
1. Base image → Foundation
2. System deps → Needed for Python packages
3. Requirements → Changes less often (cached)
4. App code → Changes most often
5. CMD → How to run

**Docker Layer Caching:**
- Each instruction creates a layer
- Unchanged layers are cached
- Put least-changing things first

### Docker Commands

```bash
# Build and start all containers
docker-compose up -d --build

# View logs
docker-compose logs -f api

# Execute command in container
docker-compose exec api bash

# Stop all containers
docker-compose down

# Remove volumes (⚠️ deletes data)
docker-compose down -v

# Restart specific service
docker-compose restart api
```

**Common Mistakes:**
❌ Not using `depends_on` with `condition` → API starts before DB ready
❌ Mounting entire project as volume in production → Security risk
❌ Not using `.dockerignore` → Copies unnecessary files
❌ Running as root → Security vulnerability
❌ Not using health checks → Services fail silently

---

## 🗄️ Database Models with SQLAlchemy

### What is SQLAlchemy ORM?
**ORM (Object-Relational Mapping)** = Python classes ↔ Database tables

Instead of SQL:
```sql
SELECT * FROM users WHERE email = 'test@example.com';
```

You write:
```python
user = db.query(User).filter(User.email == 'test@example.com').first()
```

### Base Model Setup

**`app/db/base.py`:**
```python
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

**`app/db/session.py`:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Test connections before using
    echo=settings.DEBUG  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Example Model: User

**`app/models/user.py`:**
```python
import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    # Primary key (UUID instead of auto-increment)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Fields
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    models = relationship("Model", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
```

**Key Concepts:**
1. **`__tablename__`**: Database table name
2. **Column types**: `String`, `Boolean`, `Integer`, `DateTime`, `UUID`
3. **Constraints**: `unique`, `nullable`, `index`, `primary_key`
4. **Relationships**: Connect tables (like foreign keys)
5. **`cascade`**: What happens when parent is deleted

**Common Mistakes:**
❌ Not setting `nullable=False` → NULL values slip through
❌ Missing indexes on queried columns → Slow queries
❌ Not using UUID for IDs → Predictable/sequential IDs (security)
❌ Circular imports between models → Import errors
❌ Not using `back_populates` → One-way relationships

---

## 🔗 Database Relationships

### One-to-Many (User → Models)

**User Model:**
```python
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    models = relationship("Model", back_populates="user")
```

**Model Model:**
```python
class Model(Base):
    __tablename__ = "models"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    user = relationship("User", back_populates="models")
```

**Usage:**
```python
# Get all models for a user
user = db.query(User).filter(User.email == "test@example.com").first()
user_models = user.models  # List of Model objects

# Get user from model
model = db.query(Model).first()
owner = model.user  # User object
```

### Cascade Delete

```python
models = relationship("Model", back_populates="user", cascade="all, delete-orphan")
```

**What it means:**
- When user is deleted → All their models are deleted too
- Prevents orphaned records

**Common Mistakes:**
❌ Forgetting `ForeignKey` → No database constraint
❌ Wrong cascade setting → Can't delete parent
❌ Not using `back_populates` → Relationship works only one way
❌ Circular references → Stack overflow

---

## 🧪 Testing Database Setup

### Test Database Configuration

**`tests/conftest.py`:**
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.main import app
from app.db.session import get_db

# Use same database but clean after each test
SQLALCHEMY_DATABASE_URL = "postgresql://mluser:mlpassword@db:5432/mlplatform"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup test database before all tests"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db():
    """Create test database session"""
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        # Clean up all data after each test
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()
```

**Why Clean After Each Test?**
- Tests don't interfere with each other
- Predictable state
- Can run tests in any order

---

## 🚀 Putting It All Together

### Startup Sequence

1. **Docker Compose** starts containers
2. **PostgreSQL** initializes (health check passes)
3. **Redis** starts (health check passes)
4. **API container** starts:
   - Installs dependencies
   - Loads environment variables
   - Connects to database
   - Runs Alembic migrations (optional)
   - Starts FastAPI server

### Running the Platform

```bash
# First time setup
docker-compose up -d --build

# Apply migrations
docker-compose exec api alembic upgrade head

# View logs
docker-compose logs -f api

# Access API docs
# Open browser: http://localhost:8000/docs
```

---

## 📚 Key Takeaways

### Concepts Learned
1. **Project Structure**: Separation of concerns, scalability
2. **PostgreSQL**: Relational database, ACID compliance
3. **Alembic**: Database version control
4. **SQLAlchemy ORM**: Python ↔ Database mapping
5. **Docker Compose**: Multi-container orchestration
6. **Environment Config**: Pydantic settings
7. **Health Checks**: Ensure services are ready
8. **Relationships**: Foreign keys, cascading

### Best Practices
✅ Use environment variables for config
✅ Version control your database (migrations)
✅ Use health checks in docker-compose
✅ Persist data with volumes
✅ Use UUIDs for primary keys
✅ Index frequently queried columns
✅ Test with same database as production
✅ Clean test data after each test

### Common Pitfalls to Avoid
❌ No database migrations
❌ Hardcoded credentials
❌ Missing health checks
❌ No test database isolation
❌ Root user in containers
❌ Not using volumes
❌ Circular imports in models
❌ Missing foreign key constraints

---

## 🔗 Related Documentation

- See `DOCKER_MASTERY.md` for advanced Docker concepts
- See `PYDANTIC_ORM_MASTERY.md` for SQLAlchemy deep dive
- See `DATABASE_SCHEMA.md` for complete schema

**Next:** [Phase 2: Authentication System →](PHASE_2_AUTH_GUIDE.md)
