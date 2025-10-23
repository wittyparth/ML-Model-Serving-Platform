# 📊 Phase 5: Logging & Monitoring - Learning Guide

**What You'll Learn:**
- Structured logging with Python logging module
- FastAPI middleware for request/response logging
- Performance monitoring
- Error tracking
- Log aggregation
- Analytics and metrics
- Debugging production issues

---

## 🎯 What We Built in Phase 5

### Logging & Monitoring Features
```
✅ Structured JSON logging
✅ Request/response logging middleware
✅ Performance timing
✅ Error tracking with stack traces
✅ User activity monitoring
✅ API endpoint analytics
✅ Slow query detection
✅ Log rotation and management
```

### What Gets Logged
```
- Every API request (method, path, status)
- Response times
- User actions (login, upload, predict)
- Errors and exceptions
- Database queries
- Model loading times
- Prediction metrics
```

---

## 📝 Python Logging Basics

### Why Logging?

**Without logging:**
```python
def process_data(data):
    result = do_something(data)
    return result
```
When something breaks: 🤷 "I don't know what happened"

**With logging:**
```python
import logging

logger = logging.getLogger(__name__)

def process_data(data):
    logger.info(f"Processing data: {len(data)} items")
    try:
        result = do_something(data)
        logger.info("Processing successful")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise
```
When something breaks: 📋 "Here's exactly what happened"

### Logging Levels

```python
import logging

logger = logging.getLogger(__name__)

# From least to most severe:
logger.debug("Detailed info for debugging")      # DEBUG (10)
logger.info("General information")                # INFO (20)
logger.warning("Something unusual happened")      # WARNING (30)
logger.error("An error occurred")                 # ERROR (40)
logger.critical("Critical failure!")              # CRITICAL (50)
```

**When to use each:**
- **DEBUG**: Detailed diagnostic info (rarely in production)
- **INFO**: Confirm things are working as expected
- **WARNING**: Something unexpected but not an error
- **ERROR**: A specific operation failed
- **CRITICAL**: The entire system is failing

### Setting Log Level

```python
# Only show WARNING and above (WARNING, ERROR, CRITICAL)
logging.basicConfig(level=logging.WARNING)

# Development: Show everything
logging.basicConfig(level=logging.DEBUG)

# Production: Show INFO and above
logging.basicConfig(level=logging.INFO)
```

---

## 🏗️ Structured Logging Setup

### Basic Configuration

**`app/core/logging.py`:**
```python
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """
    Custom formatter to output logs as JSON
    
    Why JSON?
    - Easy to parse by log aggregation tools
    - Structured data (not just strings)
    - Can query specific fields
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON
        
        Args:
            record: The log record to format
        
        Returns:
            JSON string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        if hasattr(record, 'duration'):
            log_data["duration"] = record.duration
        
        return json.dumps(log_data)

def setup_logging(log_level: str = "INFO"):
    """
    Configure application logging
    
    Args:
        log_level: Minimum level to log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # Optional: File handler for persistent logs
    file_handler = logging.FileHandler("logs/app.log")
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Silence noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return logger

# Create logger instance
logger = logging.getLogger(__name__)
```

### Using the Logger

```python
from app.core.logging import logger

# Simple messages
logger.info("Application started")
logger.warning("API rate limit approaching")
logger.error("Database connection failed")

# With variables
user_id = "123"
logger.info(f"User {user_id} logged in")

# With extra fields
logger.info(
    "Model prediction completed",
    extra={
        "user_id": user_id,
        "model_id": "abc-123",
        "duration": 0.5
    }
)

# With exception info
try:
    result = risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True)  # Includes stack trace
```

**Example JSON Output:**
```json
{
  "timestamp": "2025-10-23T10:30:45.123456",
  "level": "INFO",
  "logger": "app.api.v1.predictions",
  "message": "Model prediction completed",
  "module": "predictions",
  "function": "make_prediction",
  "line": 42,
  "user_id": "123",
  "model_id": "abc-123",
  "duration": 0.5
}
```

**Common Mistakes:**
❌ Not using structured logging → Hard to query logs
❌ Logging sensitive data (passwords, tokens) → Security breach
❌ Too verbose (DEBUG in production) → Disk fills up
❌ Not enough context → Can't debug issues
❌ No exception info → Can't see stack trace

---

## 🌐 Request/Response Logging Middleware

### What is Middleware?

**Middleware** wraps around every request/response:

```
Client Request
    ↓
[Middleware: Log request]
    ↓
[Your endpoint handler]
    ↓
[Middleware: Log response]
    ↓
Client Response
```

### Logging Middleware Implementation

**`app/middleware/logging.py`:**
```python
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests and responses
    
    Logs:
    - Request method, path, headers
    - Response status, time taken
    - User info (if authenticated)
    - Errors (if any)
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and response
        
        Args:
            request: Incoming HTTP request
            call_next: Function to call next handler
        
        Returns:
            HTTP response
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else None
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": f"{duration:.3f}s"
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration": f"{duration:.3f}s",
                    "error": str(e)
                },
                exc_info=True
            )
            
            # Re-raise to let FastAPI handle it
            raise
```

### Adding Middleware to FastAPI

**`app/main.py`:**
```python
from fastapi import FastAPI
from app.middleware.logging import LoggingMiddleware

app = FastAPI()

# Add middleware
app.add_middleware(LoggingMiddleware)

# Your routes...
@app.get("/")
async def root():
    return {"message": "Hello World"}
```

### What Gets Logged

**Example request log:**
```json
{
  "timestamp": "2025-10-23T10:30:45.123456",
  "level": "INFO",
  "message": "Request started",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "method": "POST",
  "path": "/api/v1/predictions/predict",
  "query_params": {},
  "client_ip": "192.168.1.100"
}
```

**Example response log:**
```json
{
  "timestamp": "2025-10-23T10:30:45.623456",
  "level": "INFO",
  "message": "Request completed",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "method": "POST",
  "path": "/api/v1/predictions/predict",
  "status_code": 200,
  "duration": "0.500s"
}
```

**Common Mistakes:**
❌ Logging request body → May contain sensitive data
❌ Not timing requests → Can't identify slow endpoints
❌ No request ID → Can't correlate logs
❌ Not catching exceptions → Middleware crashes

---

## ⏱️ Performance Monitoring

### Tracking Slow Operations

**Decorator for timing:**
```python
import time
from functools import wraps
from app.core.logging import logger

def log_performance(operation_name: str):
    """
    Decorator to log operation performance
    
    Usage:
        @log_performance("database_query")
        def get_user(user_id):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                
                # Log if slow
                if duration > 1.0:  # More than 1 second
                    logger.warning(
                        f"Slow {operation_name}",
                        extra={
                            "operation": operation_name,
                            "duration": f"{duration:.3f}s",
                            "function": func.__name__
                        }
                    )
                else:
                    logger.debug(
                        f"{operation_name} completed",
                        extra={
                            "operation": operation_name,
                            "duration": f"{duration:.3f}s"
                        }
                    )
                
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    f"{operation_name} failed",
                    extra={
                        "operation": operation_name,
                        "duration": f"{duration:.3f}s",
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                
                if duration > 1.0:
                    logger.warning(
                        f"Slow {operation_name}",
                        extra={
                            "operation": operation_name,
                            "duration": f"{duration:.3f}s",
                            "function": func.__name__
                        }
                    )
                
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    f"{operation_name} failed",
                    extra={
                        "operation": operation_name,
                        "duration": f"{duration:.3f}s",
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
```

**Using the decorator:**
```python
@log_performance("model_loading")
def load_model(file_path: str):
    """Load model from disk"""
    return joblib.load(file_path)

@log_performance("prediction")
async def make_prediction(model_id: str, input_data: list):
    """Make ML prediction"""
    model = load_model(model_id)
    return model.predict(input_data)
```

### Database Query Logging

**SQLAlchemy event listener:**
```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time"""
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries"""
    total = time.time() - conn.info['query_start_time'].pop()
    
    if total > 0.5:  # Slower than 500ms
        logger.warning(
            "Slow database query",
            extra={
                "duration": f"{total:.3f}s",
                "query": statement[:200]  # First 200 chars
            }
        )
```

### Endpoint Performance Tracking

```python
from collections import defaultdict
from typing import Dict

class PerformanceMonitor:
    """Track endpoint performance metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, list] = defaultdict(list)
    
    def record(self, endpoint: str, duration: float):
        """Record endpoint duration"""
        self.metrics[endpoint].append(duration)
        
        # Keep only last 1000 requests per endpoint
        if len(self.metrics[endpoint]) > 1000:
            self.metrics[endpoint] = self.metrics[endpoint][-1000:]
    
    def get_stats(self, endpoint: str = None):
        """Get performance statistics"""
        if endpoint:
            durations = self.metrics[endpoint]
            if not durations:
                return None
            
            return {
                "endpoint": endpoint,
                "count": len(durations),
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "p95": sorted(durations)[int(len(durations) * 0.95)]
            }
        else:
            return {
                endpoint: self.get_stats(endpoint)
                for endpoint in self.metrics.keys()
            }

# Global instance
perf_monitor = PerformanceMonitor()

# Use in middleware
class PerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        
        # Record metric
        perf_monitor.record(
            endpoint=f"{request.method} {request.url.path}",
            duration=duration
        )
        
        return response
```

**Viewing stats:**
```python
@router.get("/admin/performance")
async def get_performance_stats(current_user = Depends(require_admin)):
    """Get performance statistics (admin only)"""
    stats = perf_monitor.get_stats()
    return {"success": True, "data": stats}
```

---

## 🚨 Error Tracking

### Exception Logging

**Global exception handler:**
```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch all unhandled exceptions
    
    Logs:
    - Exception type and message
    - Stack trace
    - Request info
    - User info (if available)
    """
    # Log exception with full context
    logger.error(
        "Unhandled exception",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else None
        },
        exc_info=True  # Include stack trace
    )
    
    # Return generic error (don't expose internals)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )
```

### Custom Exception Classes

```python
class AppException(Exception):
    """Base exception for application errors"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ModelNotFoundError(AppException):
    """Model not found in database"""
    pass

class ModelLoadError(AppException):
    """Error loading model from disk"""
    pass

class PredictionError(AppException):
    """Error making prediction"""
    pass

# Handler for custom exceptions
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.error(
        f"{type(exc).__name__}: {exc.message}",
        extra={
            "exception_type": type(exc).__name__,
            "details": exc.details,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": type(exc).__name__,
            "message": exc.message,
            "details": exc.details
        }
    )
```

**Using custom exceptions:**
```python
@router.post("/predict")
async def predict(request: PredictionRequest, ...):
    # Get model
    model = db.query(Model).filter(Model.id == request.model_id).first()
    if not model:
        raise ModelNotFoundError(
            f"Model {request.model_id} not found",
            details={"model_id": str(request.model_id)}
        )
    
    # Load model
    try:
        ml_model = joblib.load(model.file_path)
    except Exception as e:
        raise ModelLoadError(
            f"Failed to load model: {str(e)}",
            details={"file_path": model.file_path}
        )
    
    # Make prediction
    try:
        prediction = ml_model.predict(input_data)
    except Exception as e:
        raise PredictionError(
            f"Prediction failed: {str(e)}",
            details={"model_id": str(model.id)}
        )
```

---

## 📈 Analytics and Metrics

### Tracking User Activity

```python
from app.core.logging import logger

def log_user_action(user_id: str, action: str, details: dict = None):
    """
    Log user action for analytics
    
    Actions: login, logout, upload_model, make_prediction, etc.
    """
    logger.info(
        f"User action: {action}",
        extra={
            "event_type": "user_action",
            "user_id": user_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Usage in endpoints
@router.post("/auth/login")
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(credentials.email, credentials.password, db)
    
    # Log successful login
    log_user_action(
        user_id=str(user.id),
        action="login",
        details={"email": credentials.email}
    )
    
    return {"access_token": token}

@router.post("/models/upload")
async def upload_model(...):
    # Upload model
    model = save_model(...)
    
    # Log upload
    log_user_action(
        user_id=str(current_user.id),
        action="upload_model",
        details={
            "model_id": str(model.id),
            "model_name": model.name,
            "file_size": model.file_size
        }
    )
    
    return model
```

### API Endpoint Usage

```python
from collections import Counter

class UsageTracker:
    """Track API endpoint usage"""
    
    def __init__(self):
        self.endpoint_counts = Counter()
        self.user_counts = Counter()
    
    def track(self, endpoint: str, user_id: str = None):
        """Track endpoint usage"""
        self.endpoint_counts[endpoint] += 1
        if user_id:
            self.user_counts[user_id] += 1
    
    def get_top_endpoints(self, limit: int = 10):
        """Get most used endpoints"""
        return self.endpoint_counts.most_common(limit)
    
    def get_top_users(self, limit: int = 10):
        """Get most active users"""
        return self.user_counts.most_common(limit)

# Global tracker
usage_tracker = UsageTracker()

# Track in middleware
class UsageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get user_id if authenticated
        user_id = getattr(request.state, 'user_id', None)
        
        # Track usage
        usage_tracker.track(
            endpoint=f"{request.method} {request.url.path}",
            user_id=user_id
        )
        
        response = await call_next(request)
        return response
```

### Metrics Endpoint

```python
@router.get("/admin/metrics")
async def get_metrics(current_user = Depends(require_admin)):
    """Get application metrics (admin only)"""
    return {
        "success": True,
        "data": {
            "top_endpoints": usage_tracker.get_top_endpoints(),
            "top_users": usage_tracker.get_top_users(),
            "performance": perf_monitor.get_stats(),
            "total_requests": sum(usage_tracker.endpoint_counts.values()),
            "total_users": len(usage_tracker.user_counts)
        }
    }
```

---

## 🔍 Debugging Production Issues

### Reading Logs

**Filter by level:**
```bash
# Show only errors
grep '"level":"ERROR"' logs/app.log

# Show errors and warnings
grep -E '"level":"(ERROR|WARNING)"' logs/app.log
```

**Filter by user:**
```bash
# All logs for specific user
grep '"user_id":"abc-123"' logs/app.log
```

**Filter by request:**
```bash
# Follow a request through the system
grep '"request_id":"xyz-789"' logs/app.log
```

**Time range:**
```bash
# Logs from specific time
grep '"timestamp":"2025-10-23T10:' logs/app.log
```

### Using jq for JSON Logs

**Install jq:**
```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq

# Windows (via Chocolatey)
choco install jq
```

**Query logs:**
```bash
# Pretty print
cat logs/app.log | jq '.'

# Filter by level
cat logs/app.log | jq 'select(.level == "ERROR")'

# Show only message and timestamp
cat logs/app.log | jq '{timestamp, message}'

# Count by level
cat logs/app.log | jq -r '.level' | sort | uniq -c

# Find slow requests
cat logs/app.log | jq 'select(.duration > 1.0)'
```

### Common Issues

**Issue: Slow endpoint**
```bash
# Find slowest requests
cat logs/app.log | jq 'select(.duration != null) | {path, duration}' | jq -s 'sort_by(.duration) | reverse | .[0:10]'
```

**Issue: User can't login**
```bash
# Find user's login attempts
grep '"action":"login"' logs/app.log | grep '"email":"user@example.com"'
```

**Issue: Prediction failing**
```bash
# Find prediction errors
cat logs/app.log | jq 'select(.message | contains("Prediction"))'
```

---

## 📚 Key Takeaways

### Concepts Learned
1. **Structured Logging**: JSON format for easy querying
2. **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
3. **Middleware**: Intercept all requests/responses
4. **Performance Tracking**: Time operations, find bottlenecks
5. **Error Tracking**: Catch and log exceptions
6. **Analytics**: Track user behavior and API usage
7. **Debugging**: Use logs to diagnose issues

### Best Practices
✅ Use JSON logging for structure
✅ Include request IDs for correlation
✅ Log performance metrics
✅ Track user actions
✅ Catch all exceptions
✅ Don't log sensitive data
✅ Rotate logs to prevent disk fill
✅ Use appropriate log levels

### Common Mistakes to Avoid
❌ Logging passwords/tokens → Security breach
❌ Too verbose logging → Disk fills up
❌ No context in logs → Can't debug
❌ Not logging exceptions → Lost errors
❌ No performance tracking → Can't optimize
❌ Logs not rotating → Disk full
❌ Plain text logs → Hard to query

---

## 🔗 Related Documentation

- See `app/core/logging.py` for logger implementation
- See `app/middleware/logging.py` for middleware
- See Python logging docs: https://docs.python.org/3/library/logging.html

**Next:** [Phase 6: Advanced Features →](PHASE_6_ADVANCED_GUIDE.md)
