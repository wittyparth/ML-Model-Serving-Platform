# 🚀 Quick Start Guide

This guide will help you set up and run the ML Model Serving Platform on your local machine.

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **PostgreSQL 15+** - [Download](https://www.postgresql.org/download/)
- **Redis 7.0+** - [Download](https://redis.io/download) or use Docker
- **Git** - [Download](https://git-scm.com/downloads)

**Optional:**
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop/)

---

## Option 1: Quick Start with Docker (Recommended)

The easiest way to get started is using Docker Compose:

```bash
# 1. Clone the repository
git clone https://github.com/wittyparth/ML-Model-Serving-Platform.git
cd ML-Model-Serving-Platform

# 2. Start all services (API, PostgreSQL, Redis)
docker-compose up -d

# 3. Check if services are running
docker-compose ps

# 4. View logs
docker-compose logs -f api

# 5. Access the API
# - API: http://localhost:8000
# - Docs: http://localhost:8000/api/v1/docs
# - Health: http://localhost:8000/health
```

That's it! The platform is now running.

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

---

## Option 2: Manual Setup (For Development)

### Step 1: Set Up PostgreSQL

```bash
# Start PostgreSQL (if installed locally)
# On Mac: brew services start postgresql
# On Ubuntu: sudo service postgresql start
# On Windows: Start via Services

# Create database
psql postgres
CREATE DATABASE mlplatform;
CREATE USER mluser WITH PASSWORD 'mlpassword';
GRANT ALL PRIVILEGES ON DATABASE mlplatform TO mluser;
\q
```

### Step 2: Set Up Redis

```bash
# Start Redis
# On Mac: brew services start redis
# On Ubuntu: sudo service redis-server start
# On Windows: Use Docker or WSL

# Or run Redis in Docker
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### Step 3: Clone and Set Up Project

```bash
# Clone repository
git clone https://github.com/wittyparth/ML-Model-Serving-Platform.git
cd ML-Model-Serving-Platform

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# Update DATABASE_URL and REDIS_URL if needed
```

Example `.env` file:
```env
DATABASE_URL=postgresql://mluser:mlpassword@localhost:5432/mlplatform
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=True
```

### Step 5: Run Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### Step 6: Start the Application

```bash
# Start development server
uvicorn app.main:app --reload

# Or run directly
python -m app.main
```

The API will be available at:
- **API:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/api/v1/docs
- **Alternative Docs:** http://localhost:8000/api/v1/redoc
- **Health Check:** http://localhost:8000/health

---

## Testing the API

### 1. Check Health

```bash
curl http://localhost:8000/health
```

### 2. Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User"
  }'
```

### 3. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

Save the `access_token` from the response.

### 4. Access Protected Endpoint

```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

---

## Development Workflow

### 1. Making Code Changes

```bash
# The server auto-reloads when files change (--reload flag)
# Edit files and see changes immediately
```

### 2. Database Schema Changes

```bash
# After modifying models in app/models/
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head

# To rollback
alembic downgrade -1
```

### 3. Adding New Dependencies

```bash
# Install new package
pip install package_name

# Update requirements.txt
pip freeze > requirements.txt
```

---

## Useful Commands

### Database

```bash
# Access PostgreSQL shell
psql -U mluser -d mlplatform

# View tables
\dt

# View users table
SELECT * FROM users;

# Drop and recreate database (WARNING: deletes all data)
dropdb mlplatform
createdb mlplatform
alembic upgrade head
```

### Redis

```bash
# Access Redis CLI
redis-cli

# View all keys
KEYS *

# Get value
GET key_name

# Clear all data
FLUSHALL
```

### Docker

```bash
# View running containers
docker ps

# View logs for specific service
docker-compose logs api
docker-compose logs db
docker-compose logs redis

# Restart a service
docker-compose restart api

# Rebuild and restart
docker-compose up -d --build

# Execute command in container
docker-compose exec api bash
docker-compose exec db psql -U mluser -d mlplatform
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
# On Mac/Linux:
lsof -i :8000
kill -9 <PID>

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Database Connection Error

```bash
# Check if PostgreSQL is running
# On Mac: brew services list
# On Ubuntu: sudo service postgresql status

# Check connection
psql -U mluser -d mlplatform -h localhost

# Update DATABASE_URL in .env if needed
```

### Redis Connection Error

```bash
# Check if Redis is running
redis-cli ping

# Should return "PONG"

# If not running:
# Docker: docker start redis
# Or: redis-server
```

### Import Errors

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Next Steps

1. ✅ **Read the Documentation**
   - [Architecture](docs/ARCHITECTURE.md)
   - [API Design](docs/API_DESIGN.md)
   - [Database Schema](docs/DATABASE_SCHEMA.md)

2. ✅ **Explore the API**
   - Visit http://localhost:8000/api/v1/docs
   - Try different endpoints
   - Test authentication flow

3. ✅ **Start Building**
   - Implement ML model loading
   - Add prediction caching
   - Build frontend (optional)

---

## Additional Resources

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **PostgreSQL Documentation:** https://www.postgresql.org/docs/
- **Redis Documentation:** https://redis.io/documentation

---

## Getting Help

- **Issues:** Open an issue on GitHub
- **Docs:** Check the [docs/](docs/) folder
- **Logs:** Check application logs for errors

---

**You're all set! 🎉**

Start building your ML Model Serving Platform!
