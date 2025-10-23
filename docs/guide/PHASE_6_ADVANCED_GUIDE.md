# 🚀 Phase 6: Advanced Features - Learning Guide

**What You'll Learn:**
- API Key authentication
- Rate limiting
- Redis caching
- WebSockets for real-time updates
- Background tasks with Celery
- Advanced security features
- API versioning
- CORS configuration

---

## 🎯 What We Built in Phase 6

### Advanced Features
```
✅ API Keys for programmatic access
✅ Rate limiting per user/endpoint
✅ Redis caching for performance
✅ WebSocket connections for real-time
✅ Background task processing
✅ API key rotation
✅ Request throttling
✅ CORS for frontend integration
```

### New Capabilities
```
- Generate/revoke API keys
- Cache predictions in Redis
- Real-time prediction status updates
- Async model training jobs
- Multiple authentication methods
- Rate limit by tier (free/pro/enterprise)
- Cross-origin resource sharing
```

---

## 🔑 API Key Authentication

### Why API Keys?

**JWT tokens** are great for users in browsers, but not ideal for:
- Scripts and automation
- Server-to-server communication
- Third-party integrations
- Mobile apps

**API Keys** are better because:
- ✅ Long-lived (don't expire)
- ✅ Can be revoked anytime
- ✅ Easier for developers
- ✅ No login flow needed

### API Key Model

**`app/models/api_key.py`:**
```python
import uuid
import secrets
from datetime import datetime
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class APIKey(Base):
    __tablename__ = "api_keys"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # API Key (hashed)
    key_hash = Column(String, unique=True, nullable=False, index=True)
    
    # Metadata
    name = Column(String, nullable=False)  # User-friendly name
    prefix = Column(String, nullable=False)  # First 8 chars for identification
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey {self.prefix}... ({self.name})>"
```

**Key Design Decisions:**

1. **Hash the key** (like passwords)
   ```python
   # NEVER store plain key in database
   key_hash = hash_api_key(plain_key)
   ```

2. **Store prefix** for identification
   ```python
   # User can identify key: "mlp_abc123..."
   prefix = plain_key[:8]
   ```

3. **Track usage**
   ```python
   last_used = Column(DateTime)  # When last used
   ```

4. **Optional expiration**
   ```python
   expires_at = Column(DateTime, nullable=True)
   ```

### Generating API Keys

**`app/api/v1/api_keys.py`:**
```python
import secrets
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyResponse

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

def generate_api_key() -> str:
    """
    Generate a secure random API key
    
    Format: mlp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
    
    Returns:
        32-character random string with prefix
    """
    # Generate 24 random bytes (32 chars base64)
    random_part = secrets.token_urlsafe(24)
    
    # Add prefix for identification
    api_key = f"mlp_{random_part}"
    
    return api_key

def hash_api_key(api_key: str) -> str:
    """
    Hash API key for storage
    
    Uses SHA-256 (one-way hash)
    
    Args:
        api_key: Plain API key
    
    Returns:
        Hashed key (hex string)
    """
    return hashlib.sha256(api_key.encode()).hexdigest()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key
    
    Returns the plain key ONCE (can't retrieve later!)
    """
    # Check user doesn't have too many keys
    existing_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).count()
    
    if existing_keys >= 5:  # Limit per user
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 active API keys per user"
        )
    
    # Generate key
    plain_key = generate_api_key()
    key_hash = hash_api_key(plain_key)
    prefix = plain_key[:8]  # "mlp_xxx"
    
    # Create database record
    api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        prefix=prefix,
        name=key_data.name,
        expires_at=key_data.expires_at
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    # Return plain key (ONLY TIME IT'S VISIBLE!)
    return {
        "success": True,
        "data": {
            "api_key": plain_key,  # 👈 Save this!
            "key_id": str(api_key.id),
            "prefix": prefix,
            "name": api_key.name,
            "created_at": api_key.created_at
        },
        "message": "API key created. Save it now - you won't see it again!"
    }
```

**Important:** The plain key is only shown once! Users must save it.

### Authenticating with API Keys

**Dependency:**
```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from datetime import datetime

# Define header where API key should be
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_user_from_api_key(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """
    Authenticate user via API key
    
    Checks:
    1. API key provided
    2. Key exists in database
    3. Key is active
    4. Key not expired
    
    Returns:
        User object
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Hash provided key
    key_hash = hash_api_key(api_key)
    
    # Look up in database
    db_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()
    
    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Check expiration
    if db_key.expires_at and db_key.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expired"
        )
    
    # Update last used
    db_key.last_used = datetime.utcnow()
    db.commit()
    
    # Return user
    return db_key.user
```

**Using API key authentication:**
```python
@router.post("/predictions/predict")
async def predict(
    request: PredictionRequest,
    current_user = Depends(get_current_user_from_api_key),  # 👈 API key
    db: Session = Depends(get_db)
):
    """Make prediction using API key"""
    # Same as JWT authentication
    # ...
```

### Dual Authentication

**Support both JWT and API keys:**
```python
from fastapi import Depends

async def get_current_user_flexible(
    jwt_user = Depends(get_current_user),  # Try JWT first
    api_user = Depends(get_current_user_from_api_key)  # Then API key
):
    """Accept either JWT token or API key"""
    return jwt_user or api_user  # Use whichever works
```

**Common Mistakes:**
❌ Storing plain keys → Anyone with database access can steal
❌ Not hashing keys → Same as storing passwords in plain text
❌ No key rotation → Compromised keys can't be replaced
❌ No expiration → Keys work forever
❌ Not limiting keys per user → Abuse

---

## 🚦 Rate Limiting

### Why Rate Limiting?

**Without rate limiting:**
```
User makes 10,000 requests/second → Server crashes
```

**With rate limiting:**
```
User makes 100 requests/minute → Extra requests rejected
```

**Benefits:**
- Prevent abuse
- Fair resource allocation
- Cost control
- DDoS protection

### Rate Limit Tiers

```python
RATE_LIMITS = {
    "free": {
        "requests_per_minute": 10,
        "requests_per_day": 1000
    },
    "pro": {
        "requests_per_minute": 100,
        "requests_per_day": 50000
    },
    "enterprise": {
        "requests_per_minute": 1000,
        "requests_per_day": 1000000
    }
}
```

### Simple Rate Limiter (In-Memory)

```python
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException, status

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        # Track requests per user per minute
        self.requests = defaultdict(list)
    
    def check_rate_limit(
        self,
        user_id: str,
        limit: int = 60,
        window: int = 60  # seconds
    ):
        """
        Check if user is within rate limit
        
        Args:
            user_id: User identifier
            limit: Max requests per window
            window: Time window in seconds
        
        Raises:
            HTTPException if rate limit exceeded
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window)
        
        # Get user's recent requests
        user_requests = self.requests[user_id]
        
        # Remove old requests (outside window)
        user_requests[:] = [
            req_time for req_time in user_requests
            if req_time > cutoff
        ]
        
        # Check limit
        if len(user_requests) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {limit} requests per {window}s",
                headers={"Retry-After": str(window)}
            )
        
        # Record this request
        user_requests.append(now)

# Global rate limiter
rate_limiter = RateLimiter()
```

**Using rate limiter:**
```python
@router.post("/predictions/predict")
async def predict(
    request: PredictionRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check rate limit
    rate_limiter.check_rate_limit(
        user_id=str(current_user.id),
        limit=RATE_LIMITS[current_user.tier]["requests_per_minute"],
        window=60
    )
    
    # Make prediction
    # ...
```

### Redis-Based Rate Limiter

**Why Redis?**
- ✅ Distributed (works across multiple servers)
- ✅ Fast (in-memory)
- ✅ Persistent (survives restarts)
- ✅ Built-in expiration

**Implementation:**
```python
import redis
from datetime import timedelta

class RedisRateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    def check_rate_limit(
        self,
        user_id: str,
        limit: int = 60,
        window: int = 60
    ):
        """
        Check rate limit using Redis
        
        Uses Redis sorted set with timestamps
        """
        key = f"rate_limit:{user_id}"
        now = datetime.utcnow().timestamp()
        cutoff = now - window
        
        # Remove old entries
        self.redis.zremrangebyscore(key, 0, cutoff)
        
        # Count recent requests
        count = self.redis.zcard(key)
        
        if count >= limit:
            # Get oldest request to calculate retry time
            oldest = self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window - now)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Max {limit} requests per {window}s",
                    headers={"Retry-After": str(retry_after)}
                )
        
        # Add this request
        self.redis.zadd(key, {str(now): now})
        
        # Set expiration on key
        self.redis.expire(key, window)
```

**Common Mistakes:**
❌ No rate limiting → Abuse and DDoS
❌ Same limit for all users → Unfair
❌ No retry-after header → Clients don't know when to retry
❌ In-memory limiter with multiple servers → Inconsistent limits
❌ Not cleaning up old entries → Memory leak

---

## 🗄️ Redis Caching

### Why Cache?

**Without caching:**
```
Request → Load model (2s) → Predict (0.1s) → Response (2.1s total)
Request → Load model (2s) → Predict (0.1s) → Response (2.1s total)
Request → Load model (2s) → Predict (0.1s) → Response (2.1s total)
```

**With caching:**
```
Request → Cache miss → Load model (2s) → Predict → Cache (2.1s)
Request → Cache hit → Return cached result (0.01s) ⚡
Request → Cache hit → Return cached result (0.01s) ⚡
```

### Setting up Redis

**Docker Compose:**
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

**Python client:**
```python
import redis
from typing import Optional, Any
import json

class RedisCache:
    """Redis caching client"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Returns:
            Cached value or None if not found
        """
        value = self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600  # Time to live in seconds
    ):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time to live in seconds (default 1 hour)
        """
        self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )
    
    def delete(self, key: str):
        """Delete key from cache"""
        self.redis.delete(key)
    
    def clear(self):
        """Clear all cache"""
        self.redis.flushdb()

# Global cache instance
cache = RedisCache()
```

### Caching Predictions

**Cache key strategy:**
```python
def get_cache_key(model_id: str, input_data: list) -> str:
    """
    Generate cache key for prediction
    
    Format: prediction:{model_id}:{input_hash}
    """
    import hashlib
    
    # Hash input data for consistent key
    input_str = json.dumps(input_data, sort_keys=True)
    input_hash = hashlib.md5(input_str.encode()).hexdigest()
    
    return f"prediction:{model_id}:{input_hash}"
```

**Using cache:**
```python
@router.post("/predictions/predict")
async def predict(
    request: PredictionRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Generate cache key
    cache_key = get_cache_key(
        model_id=str(request.model_id),
        input_data=request.input_data
    )
    
    # Check cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"Cache hit for {cache_key}")
        return {
            "success": True,
            "data": cached_result,
            "cached": True
        }
    
    # Cache miss - make prediction
    logger.info(f"Cache miss for {cache_key}")
    
    # Load model and predict
    model = load_model(request.model_id)
    prediction = model.predict(request.input_data)
    
    result = {
        "prediction": prediction.tolist(),
        "model_id": str(request.model_id),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Cache result (TTL: 1 hour)
    cache.set(cache_key, result, ttl=3600)
    
    return {
        "success": True,
        "data": result,
        "cached": False
    }
```

### Cache Invalidation

**When to invalidate:**
- Model is updated
- Model is deleted
- New version uploaded

```python
@router.put("/models/{model_id}")
async def update_model(model_id: str, ...):
    # Update model
    # ...
    
    # Invalidate all predictions for this model
    pattern = f"prediction:{model_id}:*"
    for key in cache.redis.scan_iter(match=pattern):
        cache.delete(key)
    
    return {"success": True}

@router.post("/models/{model_id}/versions")
async def create_version(model_id: str, ...):
    # Create new version
    # ...
    
    # Clear cache for old version
    pattern = f"prediction:{model_id}:*"
    for key in cache.redis.scan_iter(match=pattern):
        cache.delete(key)
    
    return {"success": True}
```

**Common Mistakes:**
❌ Not setting TTL → Cache never expires
❌ Caching user-specific data globally → Data leaks
❌ Not invalidating on updates → Stale data
❌ Cache key not unique → Wrong data returned
❌ Caching errors → Users see cached errors

---

## 🔌 WebSockets for Real-Time Updates

### What are WebSockets?

**HTTP (Request/Response):**
```
Client: "Give me data"
Server: "Here's the data"
[Connection closes]

Client: "Any updates?"
Server: "No"
[Connection closes]

Client: "Any updates now?"
Server: "No"
[Connection closes]
```

**WebSocket (Persistent Connection):**
```
Client: "Connect"
Server: "Connected"
[Connection stays open]

Server: "Update: Model trained!"
Server: "Update: Prediction complete!"
Server: "Update: New version available!"
[Connection stays open]
```

### Setting up WebSocket

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        # Active connections per user
        self.active_connections: dict[str, List[WebSocket]] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        """Accept new connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        print(f"User {user_id} connected. Total: {len(self.active_connections[user_id])}")
    
    def disconnect(self, user_id: str, websocket: WebSocket):
        """Remove connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            print(f"User {user_id} disconnected")
    
    async def send_personal_message(self, user_id: str, message: dict):
        """Send message to specific user's connections"""
        if user_id in self.active_connections:
            # Send to all user's connections
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    # Connection closed
                    self.disconnect(user_id, connection)
    
    async def broadcast(self, message: dict):
        """Send message to all connections"""
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except:
                    self.disconnect(user_id, connection)

# Global manager
manager = ConnectionManager()
```

### WebSocket Endpoint

```python
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str
):
    """
    WebSocket endpoint for real-time updates
    
    Usage:
        const ws = new WebSocket('ws://localhost:8000/api/v1/ws/user123');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Update:', data);
        };
    """
    await manager.connect(user_id, websocket)
    
    try:
        while True:
            # Wait for messages from client (keep-alive)
            data = await websocket.receive_text()
            
            # Echo back (or handle commands)
            await websocket.send_json({
                "type": "echo",
                "message": data
            })
    
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
```

### Sending Real-Time Updates

**When prediction completes:**
```python
@router.post("/predictions/predict")
async def predict(
    request: PredictionRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Make prediction
    result = await make_prediction(request)
    
    # Send real-time update
    await manager.send_personal_message(
        user_id=str(current_user.id),
        message={
            "type": "prediction_complete",
            "data": {
                "prediction_id": str(result.id),
                "prediction": result.prediction,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
    
    return result
```

**When model training completes:**
```python
async def train_model_background(model_id: str, user_id: str):
    """Background task to train model"""
    try:
        # Training logic
        train_model(model_id)
        
        # Notify user via WebSocket
        await manager.send_personal_message(
            user_id=user_id,
            message={
                "type": "model_training_complete",
                "data": {
                    "model_id": model_id,
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )
    except Exception as e:
        # Notify error
        await manager.send_personal_message(
            user_id=user_id,
            message={
                "type": "model_training_failed",
                "data": {
                    "model_id": model_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )
```

**Common Mistakes:**
❌ Not handling disconnections → Memory leak
❌ Sending too many messages → Client overwhelmed
❌ No authentication → Anyone can connect
❌ Not testing reconnection → Poor user experience

---

## 📚 Key Takeaways

### Concepts Learned
1. **API Keys**: Alternative to JWT for programmatic access
2. **Rate Limiting**: Prevent abuse and ensure fair usage
3. **Redis Caching**: Speed up responses with in-memory cache
4. **WebSockets**: Real-time bidirectional communication
5. **Dual Authentication**: Support both JWT and API keys
6. **Cache Invalidation**: Keep cached data fresh
7. **Connection Management**: Handle multiple WebSocket clients

### Best Practices
✅ Hash API keys (never store plain)
✅ Rate limit by user tier
✅ Cache frequently accessed data
✅ Set TTL on cached items
✅ Invalidate cache on updates
✅ Handle WebSocket disconnections
✅ Use Redis for distributed systems
✅ Provide retry-after headers

### Common Mistakes to Avoid
❌ Storing plain API keys → Security breach
❌ No rate limiting → Server abuse
❌ No cache TTL → Stale data forever
❌ Not invalidating cache → Outdated results
❌ Memory-based rate limiter with multiple servers → Inconsistent
❌ Not handling WebSocket errors → Crashes
❌ Caching user-specific data globally → Data leaks

---

## 🔗 Related Documentation

- See `app/models/api_key.py` for API key model
- See `app/api/v1/api_keys.py` for endpoints
- Redis docs: https://redis.io/documentation
- FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/

**Next:** [Phase 8: Production Preparation →](PHASE_8_PRODUCTION_GUIDE.md)
