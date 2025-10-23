# 🏭 Phase 8: Production Preparation - Learning Guide

**What You'll Learn:**
- Environment configuration
- Security hardening
- Performance optimization
- Health checks and monitoring
- Backup strategies
- SSL/HTTPS setup
- Database optimization
- Error handling for production

---

## 🎯 What We Build in Phase 8

### Production Readiness Checklist
```
✅ Environment-based configuration
✅ Security headers and HTTPS
✅ Database connection pooling
✅ Health check endpoints
✅ Graceful shutdown handling
✅ Static file serving (if needed)
✅ CORS configuration
✅ Database backups
✅ Logging to files
✅ Error tracking (Sentry)
✅ Performance monitoring
✅ Docker optimization
```

---

## 🔧 Environment Configuration

### Why Different Environments?

**Development:**
- Debug mode ON
- Detailed error messages
- Auto-reload on code changes
- SQLite or local PostgreSQL

**Production:**
- Debug mode OFF
- Generic error messages
- No auto-reload
- Production PostgreSQL with backups
- SSL/HTTPS required
- Monitoring and alerting

### Configuration Management

**`app/core/config.py`:**
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings
    
    Reads from environment variables with .env file fallback
    """
    
    # Application
    APP_NAME: str = "ML Model Serving Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False  # Production: False
    ENVIRONMENT: str = "production"  # development, staging, production
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4  # Gunicorn workers
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    
    # Security
    SECRET_KEY: str  # For JWT signing
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: list[str] = ["https://yourdomain.com"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "models"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    DEFAULT_RATE_LIMIT: int = 100  # per minute
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None  # Error tracking
    SENTRY_ENVIRONMENT: str = "production"
    
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_FILE: str = "logs/app.log"
    LOG_ROTATION: str = "500 MB"  # Rotate when file reaches size
    LOG_RETENTION: str = "30 days"  # Keep logs for 30 days
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Load settings
settings = Settings()
```

### Environment Files

**`.env.development`:**
```env
# Development environment
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG

DATABASE_URL=postgresql://user:pass@localhost:5432/mlplatform_dev
REDIS_URL=redis://localhost:6379

SECRET_KEY=dev-secret-key-not-secure
ACCESS_TOKEN_EXPIRE_MINUTES=60

CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

RATE_LIMIT_ENABLED=false
```

**`.env.production`:**
```env
# Production environment
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=INFO

DATABASE_URL=postgresql://user:secure_pass@prod-db:5432/mlplatform
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=10

REDIS_URL=redis://prod-redis:6379

SECRET_KEY=your-very-secure-random-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]

RATE_LIMIT_ENABLED=true
DEFAULT_RATE_LIMIT=100

SENTRY_DSN=https://your-sentry-dsn@sentry.io/123456
SENTRY_ENVIRONMENT=production

WORKERS=4
```

**Loading the right config:**
```bash
# Development
export ENV_FILE=.env.development
python -m uvicorn app.main:app --reload

# Production
export ENV_FILE=.env.production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**Common Mistakes:**
❌ Same config for dev and prod → Insecure
❌ Hardcoded secrets → Git commits expose them
❌ Debug mode in production → Exposes stack traces
❌ No environment validation → Crashes on startup
❌ Committing .env files → Secrets in version control

---

## 🔒 Security Hardening

### Security Headers

**Add security headers middleware:**
```python
from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# Only allow specific hosts (prevent host header attacks)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "www.yourdomain.com", "api.yourdomain.com"]
)

# Redirect HTTP to HTTPS in production
if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Add security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Strict transport security (HTTPS only)
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Content security policy
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response
```

### CORS Configuration

**Configure CORS properly:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specific methods
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    max_age=3600  # Cache preflight for 1 hour
)
```

**Production CORS (restrictive):**
```python
# Only your frontend domain
allow_origins=["https://yourdomain.com"]
```

**Development CORS (permissive):**
```python
# Allow local development
allow_origins=["http://localhost:3000", "http://localhost:8080"]
```

### Input Validation

**Validate all inputs with Pydantic:**
```python
from pydantic import BaseModel, Field, validator
from typing import List

class PredictionRequest(BaseModel):
    model_id: UUID
    input_data: List[float] = Field(..., min_items=1, max_items=1000)
    
    @validator('input_data')
    def validate_input_data(cls, v):
        """Validate input data"""
        # Check for NaN or Inf
        if any(not isinstance(x, (int, float)) or math.isnan(x) or math.isinf(x) for x in v):
            raise ValueError("Input contains invalid values (NaN or Inf)")
        
        # Check range (example)
        if any(x < -1000 or x > 1000 for x in v):
            raise ValueError("Input values out of acceptable range")
        
        return v
```

### SQL Injection Prevention

**Always use ORM (not raw SQL):**
```python
# ✅ SAFE: Using SQLAlchemy ORM
user = db.query(User).filter(User.email == email).first()

# ❌ UNSAFE: Raw SQL with string formatting
result = db.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

**If you must use raw SQL:**
```python
# Use parameterized queries
result = db.execute(
    "SELECT * FROM users WHERE email = :email",
    {"email": email}
)
```

**Common Mistakes:**
❌ Allowing all CORS origins (`*`) → CSRF attacks
❌ No security headers → Vulnerable to attacks
❌ Not validating input → Injection attacks
❌ Exposing stack traces → Information leakage
❌ Using HTTP in production → Man-in-the-middle attacks

---

## ⚡ Performance Optimization

### Database Connection Pooling

**Optimize SQLAlchemy engine:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    settings.DATABASE_URL,
    
    # Connection pool settings
    pool_size=settings.DATABASE_POOL_SIZE,  # 20 connections
    max_overflow=settings.DATABASE_MAX_OVERFLOW,  # 10 extra if needed
    pool_timeout=30,  # Wait 30s for connection
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Test connection before use
    
    # Performance
    echo=False,  # Don't log SQL in production
    future=True  # Use SQLAlchemy 2.0 style
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
```

### Database Indexing

**Add indexes for frequently queried columns:**
```python
from sqlalchemy import Index

class Model(Base):
    __tablename__ = "models"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"), index=True)  # Index!
    name = Column(String, index=True)  # Index!
    status = Column(String, index=True)  # Index!
    created_at = Column(DateTime, index=True)  # Index!
    
    # Composite index for common query pattern
    __table_args__ = (
        Index('ix_user_status', 'user_id', 'status'),
    )
```

**When to add indexes:**
- Columns in WHERE clauses
- Foreign key columns
- Columns used for sorting (ORDER BY)
- Columns used in JOINs

**When NOT to index:**
- Small tables (< 1000 rows)
- Columns that change frequently
- Columns with low cardinality (few unique values)

### Query Optimization

**Load relationships efficiently:**
```python
# ❌ N+1 queries problem
models = db.query(Model).all()
for model in models:
    print(model.user.email)  # Separate query for each user!

# ✅ Eager loading - one query
from sqlalchemy.orm import joinedload

models = db.query(Model).options(joinedload(Model.user)).all()
for model in models:
    print(model.user.email)  # Already loaded!
```

**Pagination:**
```python
# ✅ Limit results
models = db.query(Model).offset(skip).limit(limit).all()

# ❌ Don't load everything
models = db.query(Model).all()  # Could be millions!
```

### Caching Strategy

**Cache expensive operations:**
```python
from functools import lru_cache

# Cache model loading
@lru_cache(maxsize=10)
def load_model_cached(file_path: str):
    """Load model with in-memory cache"""
    return joblib.load(file_path)

# Cache database queries
async def get_user_models_cached(user_id: str, db: Session):
    """Get user's models with Redis cache"""
    cache_key = f"user_models:{user_id}"
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Query database
    models = db.query(Model).filter(Model.user_id == user_id).all()
    
    # Cache for 5 minutes
    cache.set(cache_key, models, ttl=300)
    
    return models
```

### Async Operations

**Use async for I/O-bound operations:**
```python
import aiofiles
import httpx

# ✅ Async file operations
async def load_model_async(file_path: str):
    async with aiofiles.open(file_path, 'rb') as f:
        content = await f.read()
        return pickle.loads(content)

# ✅ Async HTTP requests
async def fetch_external_data(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# ✅ Concurrent operations
import asyncio

async def process_batch(items: list):
    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

**Common Mistakes:**
❌ No connection pooling → Database bottleneck
❌ No indexes → Slow queries
❌ N+1 queries → Performance degradation
❌ Loading all data → Out of memory
❌ Synchronous I/O → Slow response times

---

## 🏥 Health Checks

### Health Check Endpoint

**Basic health check:**
```python
from fastapi import APIRouter, status

router = APIRouter(tags=["Health"])

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check
    
    Returns 200 OK if service is running
    """
    return {
        "status": "healthy",
        "service": "ml-platform-api",
        "version": settings.VERSION
    }
```

**Detailed health check:**
```python
@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with dependencies
    
    Checks:
    - API is running
    - Database connection
    - Redis connection
    - Disk space
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        health["checks"]["database"] = "healthy"
    except Exception as e:
        health["checks"]["database"] = f"unhealthy: {str(e)}"
        health["status"] = "unhealthy"
    
    # Check Redis
    try:
        cache.redis.ping()
        health["checks"]["redis"] = "healthy"
    except Exception as e:
        health["checks"]["redis"] = f"unhealthy: {str(e)}"
        health["status"] = "unhealthy"
    
    # Check disk space
    import shutil
    try:
        total, used, free = shutil.disk_usage("/")
        free_percent = (free / total) * 100
        
        if free_percent < 10:
            health["checks"]["disk"] = f"warning: {free_percent:.1f}% free"
            health["status"] = "degraded"
        else:
            health["checks"]["disk"] = f"healthy: {free_percent:.1f}% free"
    except Exception as e:
        health["checks"]["disk"] = f"unhealthy: {str(e)}"
    
    # Set status code based on health
    status_code = status.HTTP_200_OK if health["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(status_code=status_code, content=health)
```

### Liveness vs Readiness

**Liveness probe** (is the app alive?):
```python
@router.get("/health/live")
async def liveness():
    """
    Liveness probe for Kubernetes
    
    Returns 200 if process is running
    """
    return {"status": "alive"}
```

**Readiness probe** (is the app ready to serve traffic?):
```python
@router.get("/health/ready")
async def readiness(db: Session = Depends(get_db)):
    """
    Readiness probe for Kubernetes
    
    Returns 200 only if dependencies are ready
    """
    try:
        # Check database
        db.execute("SELECT 1")
        
        # Check Redis
        cache.redis.ping()
        
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "reason": str(e)}
        )
```

---

## 💾 Database Backups

### Backup Strategy

**What to backup:**
- Database (PostgreSQL)
- Uploaded models (files)
- Redis data (if persistent)
- Configuration files

### Automated PostgreSQL Backups

**Backup script (`scripts/backup_db.sh`):**
```bash
#!/bin/bash
# Automated database backup script

# Configuration
DB_NAME="mlplatform"
DB_USER="postgres"
BACKUP_DIR="/backups/postgres"
RETENTION_DAYS=7

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Create backup
echo "Starting backup: $BACKUP_FILE"
pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_FILE"
    
    # Delete old backups
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Old backups cleaned up (older than $RETENTION_DAYS days)"
else
    echo "Backup failed!"
    exit 1
fi
```

**Make executable and schedule:**
```bash
chmod +x scripts/backup_db.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /path/to/scripts/backup_db.sh
```

### File Backup

**Backup uploaded models:**
```bash
#!/bin/bash
# Backup uploaded files

MODELS_DIR="/app/models"
BACKUP_DIR="/backups/models"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create tarball
tar -czf "$BACKUP_DIR/models_${TIMESTAMP}.tar.gz" "$MODELS_DIR"

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/models_${TIMESTAMP}.tar.gz" s3://your-bucket/backups/
```

### Restore Procedure

**Restore database:**
```bash
# Extract and restore
gunzip -c backup.sql.gz | psql -U postgres mlplatform

# Or with docker
gunzip -c backup.sql.gz | docker exec -i postgres_container psql -U postgres mlplatform
```

**Restore files:**
```bash
tar -xzf models_backup.tar.gz -C /app/models
```

---

## 🐳 Docker Production Optimization

### Multi-Stage Build

**Optimized Dockerfile:**
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy only installed packages
COPY --from=builder /root/.local /root/.local

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run with Gunicorn
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120"]
```

### Production Docker Compose

**`docker-compose.prod.yml`:**
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/mlplatform
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    volumes:
      - models-data:/app/models
      - logs:/app/logs
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.api.tls=true"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"

  db:
    image: postgres:15-alpine
    restart: always
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=mlplatform
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static-files:/var/www/static:ro
    depends_on:
      - api
    networks:
      - app-network

volumes:
  postgres-data:
  redis-data:
  models-data:
  logs:
  static-files:

networks:
  app-network:
    driver: bridge
```

---

## 📚 Key Takeaways

### Concepts Learned
1. **Environment Configuration**: Different settings for dev/prod
2. **Security Hardening**: Headers, CORS, input validation
3. **Performance Optimization**: Connection pooling, caching, indexing
4. **Health Checks**: Liveness and readiness probes
5. **Database Backups**: Automated backup and restore
6. **Docker Optimization**: Multi-stage builds, health checks
7. **Production Deployment**: Proper configuration for scale

### Best Practices
✅ Use environment variables
✅ Enable security headers
✅ Configure CORS properly
✅ Optimize database connections
✅ Add indexes to frequently queried columns
✅ Implement health checks
✅ Automate backups
✅ Use multi-stage Docker builds
✅ Run as non-root user
✅ Set up monitoring

### Common Mistakes to Avoid
❌ Same config for dev and prod → Insecure
❌ Debug mode in production → Exposes stack traces
❌ No security headers → Vulnerable to attacks
❌ No connection pooling → Database bottleneck
❌ No indexes → Slow queries
❌ No backups → Data loss risk
❌ Running as root in Docker → Security risk
❌ No health checks → Can't detect failures

---

## 🔗 Related Documentation

- See `app/core/config.py` for configuration
- See Docker docs: https://docs.docker.com/
- See PostgreSQL backup docs: https://www.postgresql.org/docs/current/backup.html

**Next:** [Phase 9: Deployment →](PHASE_9_DEPLOYMENT_GUIDE.md)
