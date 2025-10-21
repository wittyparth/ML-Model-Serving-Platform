# FastAPI Production Mastery

> **Philosophy**: Learn what you'll actually use in production. No fluff, no niche features. This is what senior developers know.

---

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [Request Handling](#request-handling)
3. [Response Handling](#response-handling)
4. [Dependency Injection](#dependency-injection)
5. [Authentication & Security](#authentication--security)
6. [Error Handling](#error-handling)
7. [Background Tasks](#background-tasks)
8. [Production Patterns](#production-patterns)

---

## Core Concepts

### 1. The FastAPI App

```python
from fastapi import FastAPI

# Basic app
app = FastAPI()

# Production app (what we use)
app = FastAPI(
    title="My API",                    # Shows in docs
    version="1.0.0",                   # API version
    docs_url="/api/v1/docs",           # Swagger UI URL
    redoc_url="/api/v1/redoc",         # ReDoc URL
    openapi_url="/api/v1/openapi.json" # OpenAPI schema
)
```

**Why this matters**: Auto-generated documentation is FastAPI's superpower. Configure it properly.

### 2. Path Operations (Routes)

```python
# The 5 HTTP methods you'll use 99% of the time
@app.get("/items")           # Get list
@app.get("/items/{id}")      # Get one
@app.post("/items")          # Create
@app.patch("/items/{id}")    # Update (partial)
@app.delete("/items/{id}")   # Delete

# PUT exists but use PATCH (industry standard for updates)
```

### 3. Async vs Sync

```python
# Use async when doing I/O (database, HTTP calls, file operations)
@app.get("/users")
async def get_users():
    users = await db.fetch_all()  # Database I/O
    return users

# Use sync for CPU-bound work (rare)
@app.post("/calculate")
def heavy_calculation(data: dict):
    result = compute_expensive_thing(data)  # Pure computation
    return result
```

**Rule of thumb**: Use `async def` by default. FastAPI handles it efficiently.

---

## Request Handling

### 1. Path Parameters

```python
# Basic
@app.get("/users/{user_id}")
async def get_user(user_id: int):  # FastAPI validates it's an integer
    return {"user_id": user_id}

# With validation
from pydantic import UUID4

@app.get("/users/{user_id}")
async def get_user(user_id: UUID4):  # Must be valid UUID
    return {"user_id": str(user_id)}

# Enum validation (limits allowed values)
from enum import Enum

class ModelType(str, Enum):
    SKLEARN = "sklearn"
    PYTORCH = "pytorch"
    
@app.get("/models/{model_type}")
async def get_model(model_type: ModelType):
    return {"type": model_type}
```

### 2. Query Parameters

```python
from typing import Optional

# Optional with default
@app.get("/items")
async def list_items(
    skip: int = 0,           # Default value
    limit: int = 10,         # Default value
    search: Optional[str] = None  # Can be omitted
):
    return {"skip": skip, "limit": limit, "search": search}

# With validation
from pydantic import Field

@app.get("/items")
async def list_items(
    skip: int = Field(0, ge=0),              # >= 0
    limit: int = Field(10, ge=1, le=100),    # Between 1-100
    search: str = Field(None, min_length=3)  # Min 3 chars if provided
):
    return {}
```

**URL example**: `/items?skip=20&limit=50&search=fastapi`

### 3. Request Body (POST/PATCH)

```python
from pydantic import BaseModel, EmailStr, Field

# Define schema
class UserCreate(BaseModel):
    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=8)  # Required, min 8 chars
    name: str = Field(..., min_length=1, max_length=100)

# Use in route
@app.post("/users")
async def create_user(user: UserCreate):  # Auto-validates JSON body
    # user.email, user.password, user.name are guaranteed valid
    return {"email": user.email}
```

**Request**:
```json
POST /users
{
  "email": "test@example.com",
  "password": "secure123",
  "name": "John"
}
```

### 4. File Uploads

```python
from fastapi import UploadFile, File

# Single file
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()  # Read file bytes
    filename = file.filename
    content_type = file.content_type
    
    # Save to disk
    with open(f"uploads/{filename}", "wb") as f:
        f.write(contents)
    
    return {"filename": filename, "size": len(contents)}

# Multiple files
@app.post("/upload-multiple")
async def upload_files(files: list[UploadFile] = File(...)):
    return [{"filename": f.filename} for f in files]
```

### 5. Form Data (rarely used, but good to know)

```python
from fastapi import Form

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username}
```

---

## Response Handling

### 1. Response Models (Critical for production)

```python
from pydantic import BaseModel

# What you return to client
class UserResponse(BaseModel):
    id: UUID4
    email: str
    name: str
    # Notice: NO password field (security!)

    class Config:
        from_attributes = True  # Allows SQLAlchemy model → Pydantic

# Use response_model to filter/validate response
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID4):
    user = await db.get_user(user_id)  # Has password field
    return user  # FastAPI removes password automatically!
```

**Why critical**: Prevents accidentally leaking sensitive data (passwords, tokens, etc.)

### 2. Status Codes

```python
from fastapi import status

@app.post("/users", status_code=status.HTTP_201_CREATED)  # 201 for creation
async def create_user(user: UserCreate):
    return {}

@app.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT)  # 204 for delete
async def delete_user(id: UUID4):
    await db.delete_user(id)
    return  # No content
```

**Common codes**:
- `200` - OK (default for GET/PATCH)
- `201` - Created (POST)
- `204` - No Content (DELETE)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

### 3. Response Headers

```python
from fastapi import Response

@app.get("/data")
async def get_data(response: Response):
    response.headers["X-Custom-Header"] = "value"
    response.headers["Cache-Control"] = "max-age=3600"
    return {"data": "something"}
```

### 4. Custom Responses

```python
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse

# Custom JSON with status code
@app.get("/custom")
async def custom():
    return JSONResponse(
        status_code=200,
        content={"message": "Custom response"},
        headers={"X-Custom": "header"}
    )

# File download
@app.get("/download/{filename}")
async def download(filename: str):
    return FileResponse(
        path=f"files/{filename}",
        filename=filename,
        media_type="application/octet-stream"
    )
```

---

## Dependency Injection

**This is FastAPI's killer feature. Master this.**

### 1. Basic Dependency

```python
from fastapi import Depends

# Reusable function
def get_db():
    db = Database()
    try:
        yield db  # Provides db to route
    finally:
        db.close()  # Cleanup after request

# Use in route
@app.get("/users")
async def get_users(db = Depends(get_db)):  # db is injected
    users = await db.fetch_all()
    return users
```

### 2. Authentication Dependency (Production Pattern)

```python
from fastapi import Header, HTTPException

async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.replace("Bearer ", "")
    user = await verify_token(token)  # Your verification logic
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return user

# Protected route
@app.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    return current_user  # Only executes if token is valid
```

### 3. Nested Dependencies

```python
# Dependency that uses another dependency
async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user

# Route uses nested dependency
@app.get("/admin")
async def admin_panel(user = Depends(get_current_active_user)):
    return {"admin": user.name}
```

### 4. Class-Based Dependencies

```python
class Pagination:
    def __init__(
        self,
        skip: int = 0,
        limit: int = 10
    ):
        self.skip = skip
        self.limit = limit

@app.get("/items")
async def list_items(pagination: Pagination = Depends()):
    return {
        "skip": pagination.skip,
        "limit": pagination.limit
    }
```

---

## Authentication & Security

### 1. OAuth2 Password Flow (Industry Standard)

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError

# Setup OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Login endpoint
@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# Protected route
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        user = await get_user_by_email(email)
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return current_user
```

**How it works**:
1. Client sends username/password to `/auth/login`
2. Server returns JWT token
3. Client includes token in header: `Authorization: Bearer <token>`
4. FastAPI validates token automatically via `oauth2_scheme`

### 2. Password Hashing (NEVER store plain passwords)

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Use in registration
@app.post("/register")
async def register(user: UserCreate):
    hashed = hash_password(user.password)
    await db.create_user(email=user.email, password=hashed)
    return {"message": "User created"}
```

### 3. CORS (Cross-Origin Resource Sharing)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
```

**Production**: Specify exact origins, don't use `["*"]`

---

## Error Handling

### 1. HTTPException (99% of your errors)

```python
from fastapi import HTTPException

@app.get("/users/{user_id}")
async def get_user(user_id: UUID4):
    user = await db.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return user
```

### 2. Custom Exception Handlers

```python
from fastapi import Request
from fastapi.responses import JSONResponse

# Custom exception
class DatabaseError(Exception):
    pass

# Handler
@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    return JSONResponse(
        status_code=500,
        content={"message": "Database error occurred"}
    )

# Use in route
@app.get("/data")
async def get_data():
    try:
        data = await db.fetch()
    except SomeDBError:
        raise DatabaseError()
    return data
```

### 3. Validation Errors (Automatic)

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "message": "Validation error",
            "errors": exc.errors()
        }
    )
```

---

## Background Tasks

### Use for non-blocking operations (emails, logging, cleanup)

```python
from fastapi import BackgroundTasks

# Background function
def send_email(email: str, message: str):
    # Simulate email sending
    time.sleep(5)  # This won't block the response
    print(f"Email sent to {email}")

# Route
@app.post("/register")
async def register(
    user: UserCreate,
    background_tasks: BackgroundTasks
):
    # Create user first
    await db.create_user(user)
    
    # Send email in background (doesn't block response)
    background_tasks.add_task(send_email, user.email, "Welcome!")
    
    return {"message": "User created"}  # Returns immediately
```

**When to use**:
- ✅ Sending emails
- ✅ Logging to external service
- ✅ File cleanup
- ✅ Cache invalidation

**When NOT to use**:
- ❌ Long-running tasks (use Celery instead)
- ❌ Tasks that must complete (use transactions)

---

## Production Patterns

### 1. Router Organization (Modular API)

```python
# app/api/v1/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
async def list_users():
    return []

@router.get("/{user_id}")
async def get_user(user_id: UUID4):
    return {}

# app/main.py
from app.api.v1 import users

app.include_router(users.router, prefix="/api/v1")
```

### 2. Startup/Shutdown Events

```python
@app.on_event("startup")
async def startup():
    # Connect to database
    await database.connect()
    # Load ML models
    await load_models()
    print("Application started")

@app.on_event("shutdown")
async def shutdown():
    # Close database connections
    await database.disconnect()
    print("Application shutdown")
```

### 3. Middleware (Request/Response Processing)

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)  # Process request
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

### 4. Configuration (Environment Variables)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()

# Use in app
app = FastAPI(debug=settings.debug)
```

### 5. Health Check (Required for production)

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await db.is_alive(),
        "redis": await redis.ping()
    }
```

---

## The 20% You'll Use 80% of the Time

**Master these first**:
1. ✅ Path operations (`@app.get`, `@app.post`)
2. ✅ Pydantic models for request/response
3. ✅ `Depends()` for database sessions and auth
4. ✅ `HTTPException` for errors
5. ✅ `response_model` to filter responses
6. ✅ OAuth2 + JWT for authentication
7. ✅ Router organization for clean code
8. ✅ `async def` for all routes

**Everything else is bonus.**

---

## Common Patterns in Your Project

### Database Session Dependency
```python
async def get_db():
    async with AsyncSession() as session:
        yield session

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### Authenticated User Dependency
```python
@app.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

### Pagination Pattern
```python
@app.get("/items")
async def list_items(skip: int = 0, limit: int = 10):
    return items[skip : skip + limit]
```

---

## Learn More

**Official docs**: https://fastapi.tiangolo.com/
**Your project**: Check `app/api/v1/` for real examples

**Next**: Read `PYDANTIC_ORM_MASTERY.md` to understand data validation and database models.
