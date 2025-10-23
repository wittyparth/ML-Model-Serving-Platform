# 🔐 Phase 2: Authentication System - Learning Guide

**What You'll Learn:**
- JWT (JSON Web Tokens) authentication
- Password hashing with Argon2
- FastAPI dependencies for auth
- Protected routes
- Token refresh mechanism

---

## 🎯 What We Built in Phase 2

### Authentication Flow
```
1. User Registration → Hash password → Store in DB
2. User Login → Verify password → Generate JWT token
3. Access Protected Route → Verify JWT → Return data
4. Token Refresh → Verify refresh token → Generate new access token
```

### Endpoints Created
```
POST /api/v1/auth/register  - Create new user
POST /api/v1/auth/login     - Login and get tokens
POST /api/v1/auth/refresh   - Refresh access token
GET  /api/v1/auth/me        - Get current user info
```

---

## 🔑 JWT (JSON Web Tokens)

### What is JWT?
A JWT is a secure way to transmit information between parties as a JSON object.

**Structure:**
```
header.payload.signature
```

**Example:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLWlkIiwiZXhwIjoxNjk5OTk5OTk5fQ.signature
```

### JWT Parts

1. **Header** (Algorithm & Type)
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

2. **Payload** (Claims/Data)
```json
{
  "sub": "user-id-here",
  "exp": 1699999999,
  "type": "access"
}
```

3. **Signature** (Verification)
```
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  secret_key
)
```

### Why Use JWT?
✅ **Stateless**: No server-side session storage
✅ **Scalable**: Works across multiple servers
✅ **Self-contained**: Contains all user info
✅ **Secure**: Cryptographically signed
✅ **Standard**: Widely supported

### Common JWT Mistakes
❌ **Storing sensitive data in payload** → Anyone can decode it
❌ **Not setting expiration** → Tokens never expire
❌ **Using weak secret key** → Easy to forge tokens
❌ **Storing tokens in localStorage** → Vulnerable to XSS attacks
❌ **Not validating expiration** → Accepting expired tokens

---

## 🔒 Password Hashing with Argon2

### Why Hash Passwords?
- Never store passwords in plain text!
- If database is compromised, passwords are safe
- One-way function (can't reverse)

### Why Argon2?
Argon2 is the winner of the 2015 Password Hashing Competition.

**Better than bcrypt/MD5/SHA because:**
- ✅ Memory-hard (resists GPU cracking)
- ✅ Configurable cost
- ✅ Built-in salt
- ✅ Modern and secure

### Implementation

**`app/core/security.py`:**
```python
from passlib.context import CryptContext

# Configure password hashing
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],  # Argon2 preferred, bcrypt fallback
    deprecated="auto"               # Auto-migrate from bcrypt to argon2
)

def get_password_hash(password: str) -> str:
    """Hash a password using Argon2"""
    # Check password length (bcrypt has 72 byte limit)
    if len(password.encode('utf-8')) > 72:
        raise ValueError("Password is too long (max 72 bytes)")
    
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)
```

**How It Works:**
```python
# Registration
password = "mySecretPassword123"
hashed = get_password_hash(password)
# Result: $argon2id$v=19$m=65536,t=3,p=4$random_salt$hashed_value

# Login
user_input = "mySecretPassword123"
is_valid = verify_password(user_input, hashed)  # True

user_input = "wrongPassword"
is_valid = verify_password(user_input, hashed)  # False
```

**Common Mistakes:**
❌ Using MD5/SHA-256 directly → Not designed for passwords
❌ Not using a salt → Rainbow table attacks
❌ Implementing your own hashing → Likely has vulnerabilities
❌ Storing password length → Information leakage
❌ Comparing hashes with `==` → Timing attacks

---

## 🎟️ Creating JWT Tokens

### Access Token (Short-lived)
Used for API requests. Expires quickly (15-30 minutes).

```python
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: User data to encode (usually {"sub": user_id})
        expires_delta: Custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Add claims
    to_encode.update({
        "exp": expire,      # Expiration time
        "type": "access"    # Token type
    })
    
    # Encode and sign
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt
```

### Refresh Token (Long-lived)
Used to get new access tokens. Expires after days/weeks.

```python
def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token (longer expiration)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    to_encode.update({
        "exp": expire,
        "type": "refresh"  # Different type!
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt
```

### Verifying Tokens

```python
from jose import JWTError, jwt
from fastapi import HTTPException, status

def verify_token(token: str, token_type: str = "access") -> dict:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

**Why Two Token Types?**
- **Access token** (short): Used frequently, short expiration = more secure
- **Refresh token** (long): Used rarely, can get new access tokens

**Common Mistakes:**
❌ Access tokens expire too late → Security risk
❌ No token type verification → Can use refresh token as access token
❌ Same secret for all environments → Prod tokens work in dev
❌ Tokens don't expire → Infinite validity
❌ Not using UTC time → Timezone issues

---

## 🛡️ Protected Routes with Dependencies

### FastAPI Dependency Injection

**What is a Dependency?**
A function that runs before your endpoint and provides data.

**Simple Example:**
```python
from fastapi import Depends

def get_current_time():
    return datetime.now()

@app.get("/time")
def show_time(current_time: datetime = Depends(get_current_time)):
    return {"time": current_time}
```

### Authentication Dependency

**`app/api/dependencies.py`:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import verify_token
from app.models.user import User

# Create security scheme
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token
    
    How it works:
    1. Extract token from Authorization header
    2. Verify and decode token
    3. Get user from database
    4. Return user object
    """
    # Extract token
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token, token_type="access")
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user
```

### Using Protected Routes

```python
from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Protected route - requires authentication"""
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_admin": current_user.is_admin
    }

@router.get("/public")
def public_route():
    """Public route - no authentication required"""
    return {"message": "This is public"}
```

**How to Call Protected Route:**
```bash
# Get token first
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Response:
# {"data":{"access_token":"eyJhbGc..."}}

# Use token
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGc..."
```

**Common Mistakes:**
❌ Not checking `is_active` → Disabled users can access
❌ Querying database on every request → Slow (use caching)
❌ Not handling token expiration → 401 errors everywhere
❌ Missing `WWW-Authenticate` header → Poor UX
❌ Not using FastAPI security schemes → No OpenAPI docs

---

## 📝 Pydantic Schemas for Auth

### Why Schemas?
- **Validation**: Automatic data validation
- **Documentation**: Auto-generated API docs
- **Type Safety**: IDE autocomplete and type checking
- **Serialization**: Convert DB models to JSON

### Request Schemas

**`app/schemas/user.py`:**
```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr                           # Validates email format
    password: str = Field(
        ...,                                  # Required
        min_length=8,                         # Min 8 characters
        max_length=100,
        description="User password"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="User's full name"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securePass123",
                "full_name": "John Doe"
            }
        }

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securePass123"
            }
        }
```

### Response Schemas

```python
from uuid import UUID
from datetime import datetime

class UserResponse(BaseModel):
    """Schema for user data in responses (no password!)"""
    id: UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  # Enable ORM mode (SQLAlchemy)

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until expiration
```

**Common Mistakes:**
❌ Including password in response schema → Security leak
❌ Not using `EmailStr` → Invalid emails accepted
❌ No field validation → Bad data in database
❌ Not using `from_attributes=True` → Can't convert ORM objects
❌ No example in docs → Hard for users to understand

---

## 🔌 Complete Authentication Endpoints

### 1. Register Endpoint

**`app/api/v1/auth.py`:**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.security import get_password_hash

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    - Validates email format
    - Checks if email already exists
    - Hashes password
    - Creates user in database
    """
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "success": True,
        "data": {
            "user": UserResponse.model_validate(new_user)
        },
        "message": "User registered successfully"
    }
```

### 2. Login Endpoint

```python
from datetime import timedelta
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.schemas.user import UserLogin, TokenResponse

@router.post("/login", response_model=dict)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    
    Returns:
    - access_token: Short-lived token for API requests
    - refresh_token: Long-lived token to get new access tokens
    """
    # Find user
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        },
        "message": "Login successful"
    }
```

### 3. Refresh Token Endpoint

```python
@router.post("/refresh", response_model=dict)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Get new access token using refresh token
    
    This avoids logging in again when access token expires
    """
    # Verify refresh token
    payload = verify_token(refresh_token, token_type="refresh")
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify user still exists and is active
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    new_access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "success": True,
        "data": {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        },
        "message": "Token refreshed successfully"
    }
```

### 4. Get Current User Endpoint

```python
from app.api.dependencies import get_current_user

@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    
    Protected route - requires valid JWT token
    """
    return {
        "success": True,
        "data": UserResponse.model_validate(current_user),
        "message": "User retrieved successfully"
    }
```

**Common Mistakes:**
❌ Returning different errors for "user not found" vs "wrong password" → User enumeration
❌ Not checking `is_active` → Banned users can login
❌ Logging passwords → Security violation
❌ Not rate limiting login → Brute force attacks
❌ Accepting tokens in URL query → Logged in server logs

---

## 🔐 Security Best Practices

### 1. Password Requirements

```python
import re

def validate_password_strength(password: str) -> bool:
    """
    Validate password strength
    
    Requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains digit
    - Contains special character
    """
    if len(password) < 8:
        return False
    
    if not re.search(r'[A-Z]', password):
        return False
    
    if not re.search(r'[a-z]', password):
        return False
    
    if not re.search(r'\d', password):
        return False
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True
```

### 2. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login(...):
    ...
```

### 3. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourfrontend.com"],  # Specific origins in prod
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 4. HTTPS Only (Production)

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if not settings.DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)
```

### 5. Token Rotation

```python
# On refresh, also return new refresh token
new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

# Invalidate old refresh token (store in database with used=True)
```

---

## 🧪 Testing Authentication

### Test Registration

```python
def test_register_user(client):
    """Test user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password123!",
            "full_name": "Test User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "test@example.com"
    assert "hashed_password" not in data  # Never return password!

def test_register_duplicate_email(client, test_user):
    """Test duplicate email rejection"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "Password123!",
            "full_name": "Another User"
        }
    )
    
    assert response.status_code == 409  # Conflict
```

### Test Login

```python
def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"

def test_login_invalid_password(client, test_user):
    """Test login with wrong password"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
```

### Test Protected Route

```python
def test_protected_route_with_token(client, auth_headers):
    """Test accessing protected route with valid token"""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "email" in data["data"]

def test_protected_route_without_token(client):
    """Test accessing protected route without token"""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 403  # Forbidden
```

---

## 📚 Key Takeaways

### Concepts Learned
1. **JWT Tokens**: Stateless authentication mechanism
2. **Password Hashing**: Argon2 for secure password storage
3. **Dependencies**: FastAPI's dependency injection for auth
4. **Protected Routes**: Requiring authentication for endpoints
5. **Token Refresh**: Long-lived tokens for better UX
6. **Pydantic Validation**: Request/response validation

### Security Principles
✅ Never store passwords in plain text
✅ Use strong hashing algorithms (Argon2)
✅ Implement token expiration
✅ Use HTTPS in production
✅ Rate limit sensitive endpoints
✅ Validate all user input
✅ Don't leak information in error messages
✅ Check user is active before granting access

### Common Mistakes to Avoid
❌ Storing JWT in localStorage (XSS vulnerable)
❌ Not setting token expiration
❌ Using weak secret keys
❌ Including sensitive data in JWT payload
❌ Not rate limiting login endpoint
❌ Returning different errors for enumeration
❌ Not checking `is_active` flag
❌ Logging sensitive information

---

## 🔗 Related Documentation

- See `FASTAPI_MASTERY.md` for FastAPI advanced concepts
- See `PHASE_1_SETUP_GUIDE.md` for database setup
- See `docs/ARCHITECTURE.md` for system design

**Next:** [Phase 3: Model Management →](PHASE_3_MODEL_GUIDE.md)
