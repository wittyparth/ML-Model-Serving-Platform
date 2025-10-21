# Pydantic & SQLAlchemy Production Mastery

> **Philosophy**: Understand how data flows from API → validation → database → response. This is the backbone of every production API.

---

## Table of Contents
1. [Pydantic Basics](#pydantic-basics)
2. [Advanced Validation](#advanced-validation)
3. [SQLAlchemy Models](#sqlalchemy-models)
4. [Relationships](#relationships)
5. [Querying Database](#querying-database)
6. [The Complete Flow](#the-complete-flow)
7. [Production Patterns](#production-patterns)

---

## Pydantic Basics

**What is Pydantic?** Data validation using Python type hints. Converts messy JSON → clean Python objects.

### 1. Basic Schema

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    email: str

# This works
user = User(name="John", age=30, email="john@test.com")
print(user.name)  # "John"

# This fails validation (age is string, not int)
user = User(name="John", age="thirty", email="john@test.com")
# ValidationError: age must be an integer
```

### 2. Optional Fields

```python
from typing import Optional

class User(BaseModel):
    name: str              # Required
    age: int               # Required
    email: Optional[str] = None  # Optional, defaults to None
    bio: str = "No bio"    # Optional, defaults to "No bio"

# Both valid
user1 = User(name="John", age=30)  # email=None, bio="No bio"
user2 = User(name="Jane", age=25, email="jane@test.com", bio="Hello")
```

### 3. Field Validation

```python
from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)  # ... means required
    age: int = Field(..., ge=18, le=120)  # ge = greater/equal, le = less/equal
    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=8)

# Valid
user = UserCreate(
    name="John",
    age=25,
    email="john@test.com",
    password="secure123"
)

# Invalid (age < 18)
user = UserCreate(name="John", age=15, email="john@test.com", password="secure123")
# ValidationError: age must be >= 18
```

**Common Field validators**:
- `min_length`, `max_length` - String length
- `ge`, `le`, `gt`, `lt` - Numbers (greater/less than)
- `regex` - Pattern matching
- `EmailStr` - Email validation (needs `pip install pydantic[email]`)

### 4. Type Conversion

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    quantity: int

# Pydantic auto-converts types
item = Item(name="Book", price="19.99", quantity="5")
# price becomes 19.99 (float), quantity becomes 5 (int)

print(type(item.price))  # <class 'float'>
print(type(item.quantity))  # <class 'int'>
```

---

## Advanced Validation

### 1. Custom Validators

```python
from pydantic import BaseModel, validator

class User(BaseModel):
    username: str
    password: str
    
    @validator('username')
    def username_must_be_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('must be alphanumeric')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('must contain a number')
        return v

# Valid
user = User(username="john123", password="secure123")

# Invalid
user = User(username="john@123", password="weak")  # username has @, password no number
```

### 2. Root Validators (Validate multiple fields together)

```python
from pydantic import BaseModel, root_validator

class PasswordChange(BaseModel):
    password: str
    password_confirm: str
    
    @root_validator
    def passwords_match(cls, values):
        password = values.get('password')
        password_confirm = values.get('password_confirm')
        
        if password != password_confirm:
            raise ValueError('passwords do not match')
        
        return values

# Valid
data = PasswordChange(password="test123", password_confirm="test123")

# Invalid
data = PasswordChange(password="test123", password_confirm="different")
# ValidationError: passwords do not match
```

### 3. Computed Fields

```python
from pydantic import BaseModel, computed_field

class User(BaseModel):
    first_name: str
    last_name: str
    
    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

user = User(first_name="John", last_name="Doe")
print(user.full_name)  # "John Doe"
```

### 4. Model Config

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    _internal: str = "secret"  # Underscore fields are private
    
    class Config:
        # Allow SQLAlchemy models → Pydantic
        from_attributes = True  # Old name: orm_mode = True
        
        # Validate on assignment (not just initialization)
        validate_assignment = True
        
        # Custom JSON encoding
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

---

## SQLAlchemy Models

**What is SQLAlchemy?** ORM (Object-Relational Mapping) - Write Python, get SQL automatically.

### 1. Basic Model

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"  # Table name in database
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer)

# SQLAlchemy generates SQL:
# CREATE TABLE users (
#     id INTEGER PRIMARY KEY,
#     email VARCHAR UNIQUE NOT NULL,
#     name VARCHAR NOT NULL,
#     age INTEGER
# );
```

### 2. Column Types

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, JSON
from datetime import datetime
import uuid

class Model(Base):
    __tablename__ = "models"
    
    # UUID primary key (better for distributed systems)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Common types
    name = Column(String(255))  # VARCHAR(255)
    description = Column(Text)  # Unlimited text
    version = Column(Integer)
    is_active = Column(Boolean, default=True)
    accuracy = Column(Float)
    
    # JSON data (PostgreSQL JSONB)
    metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Common types**:
- `Integer` - Whole numbers
- `String(n)` - Fixed-length text
- `Text` - Unlimited text
- `Boolean` - True/False
- `Float` - Decimal numbers
- `DateTime` - Timestamps
- `JSON` - JSON data (PostgreSQL JSONB)

### 3. Default Values

```python
from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"
    
    # Python function (runs when creating object)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Static value
    is_active = Column(Boolean, default=True)
    
    # Database default (runs in SQL)
    created_at = Column(DateTime, server_default="now()")
    
    # Update on modification
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### 4. Constraints

```python
from sqlalchemy import Column, String, Integer, UniqueConstraint, Index

class Model(Base):
    __tablename__ = "models"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    
    # Composite unique constraint (user can't have duplicate model name+version)
    __table_args__ = (
        UniqueConstraint('user_id', 'name', 'version', name='unique_user_model_version'),
        Index('idx_user_id', 'user_id'),  # Index for faster queries
    )
```

---

## Relationships

**This is where ORMs shine - connecting tables without writing JOIN queries.**

### 1. One-to-Many (Most Common)

```python
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

# One user → Many models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    
    # Relationship (not a column, just Python convenience)
    models = relationship("Model", back_populates="user", cascade="all, delete-orphan")

class Model(Base):
    __tablename__ = "models"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String)
    
    # Relationship back to user
    user = relationship("User", back_populates="models")

# Usage
user = session.query(User).first()
print(user.models)  # List of all models for this user (automatic JOIN!)

model = session.query(Model).first()
print(model.user.email)  # The user who owns this model
```

**How it works**:
- `ForeignKey("users.id")` - SQL constraint (enforces user must exist)
- `relationship()` - Python convenience (no SQL column, just makes `.models` work)
- `back_populates` - Keeps both sides in sync
- `cascade="all, delete-orphan"` - Delete models when user is deleted

### 2. Many-to-Many (Less Common)

```python
from sqlalchemy import Table, Column, String, ForeignKey
from sqlalchemy.orm import relationship

# Association table (junction table)
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id')),
    Column('role_id', String, ForeignKey('roles.id'))
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String)
    
    # Many-to-many
    roles = relationship("Role", secondary=user_roles, back_populates="users")

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    
    users = relationship("User", secondary=user_roles, back_populates="roles")

# Usage
user = session.query(User).first()
print([role.name for role in user.roles])  # ['admin', 'editor']
```

### 3. Cascade Options

```python
# Delete user → delete all their models
models = relationship("Model", cascade="all, delete-orphan")

# Delete user → set model.user_id = NULL (keep models)
models = relationship("Model", cascade="save-update, merge")

# Delete user → prevent if they have models (raise error)
models = relationship("Model", cascade="save-update, merge", passive_deletes=False)
```

**Common cascades**:
- `"all, delete-orphan"` - Delete children when parent deleted
- `"save-update"` - Only save/update children, don't delete
- `"delete"` - Delete children when parent deleted (but not orphans)

---

## Querying Database

### 1. Basic Queries

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Get all users
async def get_users(db: AsyncSession):
    result = await db.execute(select(User))
    users = result.scalars().all()  # Convert to list of User objects
    return users

# Get one user by ID
async def get_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()  # Returns User or None
    return user

# Get first user
async def get_first_user(db: AsyncSession):
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    return user
```

### 2. Filtering

```python
from sqlalchemy import select, and_, or_

# WHERE email = 'test@test.com'
result = await db.execute(
    select(User).where(User.email == "test@test.com")
)

# WHERE age > 18
result = await db.execute(
    select(User).where(User.age > 18)
)

# WHERE age > 18 AND is_active = True
result = await db.execute(
    select(User).where(
        and_(User.age > 18, User.is_active == True)
    )
)

# WHERE age < 18 OR age > 65
result = await db.execute(
    select(User).where(
        or_(User.age < 18, User.age > 65)
    )
)

# WHERE email LIKE '%@gmail.com'
result = await db.execute(
    select(User).where(User.email.like("%@gmail.com"))
)

# WHERE email IN ('a@test.com', 'b@test.com')
result = await db.execute(
    select(User).where(User.email.in_(["a@test.com", "b@test.com"]))
)
```

### 3. Ordering & Pagination

```python
from sqlalchemy import select, desc

# ORDER BY created_at DESC
result = await db.execute(
    select(User).order_by(desc(User.created_at))
)

# ORDER BY name ASC
result = await db.execute(
    select(User).order_by(User.name)
)

# LIMIT 10 OFFSET 20 (pagination)
result = await db.execute(
    select(User)
    .order_by(User.created_at)
    .limit(10)
    .offset(20)
)

# Production pagination pattern
async def get_users_paginated(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(
        select(User)
        .order_by(User.created_at)
        .limit(limit)
        .offset(skip)
    )
    return result.scalars().all()
```

### 4. Creating Records

```python
# Create one
async def create_user(db: AsyncSession, email: str, name: str):
    user = User(email=email, name=name)
    db.add(user)
    await db.commit()  # Save to database
    await db.refresh(user)  # Reload from DB to get defaults/auto-generated fields
    return user

# Create many
async def create_users(db: AsyncSession, users_data: list):
    users = [User(**data) for data in users_data]
    db.add_all(users)
    await db.commit()
    return users
```

### 5. Updating Records

```python
# Update one field
async def update_user_name(db: AsyncSession, user_id: str, new_name: str):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    user.name = new_name
    await db.commit()
    await db.refresh(user)
    return user

# Update multiple fields
async def update_user(db: AsyncSession, user_id: str, updates: dict):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    for key, value in updates.items():
        setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    return user
```

### 6. Deleting Records

```python
# Delete one
async def delete_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return False
    
    await db.delete(user)
    await db.commit()
    return True

# Delete many
async def delete_inactive_users(db: AsyncSession):
    result = await db.execute(select(User).where(User.is_active == False))
    users = result.scalars().all()
    
    for user in users:
        await db.delete(user)
    
    await db.commit()
    return len(users)
```

### 7. Joins (Relationships)

```python
from sqlalchemy.orm import selectinload

# Eager loading (avoid N+1 query problem)
async def get_users_with_models(db: AsyncSession):
    result = await db.execute(
        select(User).options(selectinload(User.models))
    )
    users = result.scalars().all()
    
    # Now you can access user.models without extra queries
    for user in users:
        print(user.email, len(user.models))
    
    return users

# Filter by related table
async def get_users_with_sklearn_models(db: AsyncSession):
    result = await db.execute(
        select(User)
        .join(Model)
        .where(Model.framework == "sklearn")
    )
    return result.scalars().all()
```

---

## The Complete Flow

**This is how data moves through your API. Master this pattern.**

### 1. The Three Schema Pattern

```python
# database.py - Database model (SQLAlchemy)
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # Hashed
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# schemas.py - API schemas (Pydantic)

# For creating user (request)
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1)

# For updating user (request)
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

# For returning user (response)
class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime
    # Notice: NO password field!
    
    class Config:
        from_attributes = True  # Allow SQLAlchemy → Pydantic
```

### 2. Complete CRUD Example

```python
# routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# CREATE
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,  # Pydantic validates JSON
    db: AsyncSession = Depends(get_db)
):
    # Check if email exists
    existing = await db.execute(select(User).where(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create SQLAlchemy model
    db_user = User(
        email=user_data.email,
        password=hashed_password,
        name=user_data.name
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # FastAPI converts SQLAlchemy → UserResponse (removes password)
    return db_user

# READ (list)
@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()

# READ (one)
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# UPDATE
@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,  # Pydantic validates JSON
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update only provided fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user

# DELETE
@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    return
```

### 3. Data Flow Diagram

```
Request JSON                     Pydantic Schema           SQLAlchemy Model         Database
------------                     ---------------           ----------------         --------
{                                UserCreate                User                     users table
  "email": "a@b.com",      -->   - Validates email   -->   - Maps to SQL      -->  INSERT
  "password": "pass123",         - Checks length           - Hashes password
  "name": "John"                 - Type conversion         - Generates UUID
}

Database                         SQLAlchemy Model          Pydantic Schema          Response JSON
--------                         ----------------          ---------------          -------------
users table                      User                      UserResponse             {
SELECT *                   -->   - Load from DB      -->   - Remove password  -->     "id": "uuid",
                                 - With password           - Keep safe fields         "email": "a@b.com",
                                                                                       "name": "John"
                                                                                     }
```

---

## Production Patterns

### 1. Base Schema (DRY - Don't Repeat Yourself)

```python
from pydantic import BaseModel
from datetime import datetime

# Base for all responses
class BaseResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Extend for specific models
class UserResponse(BaseResponse):
    email: str
    name: str

class ModelResponse(BaseResponse):
    name: str
    version: int
    user_id: str
```

### 2. Exclude Fields Pattern

```python
class UserInDB(BaseModel):
    id: str
    email: str
    password: str  # Has password
    
    class Config:
        from_attributes = True

# For API response (exclude password)
class UserResponse(UserInDB):
    class Config:
        fields = {'password': {'exclude': True}}  # Remove password

# Or use separate model (cleaner)
class UserResponse(BaseModel):
    id: str
    email: str
    # No password field at all
```

### 3. Nested Models

```python
# Response with nested relationship
class ModelResponse(BaseModel):
    id: str
    name: str
    user: UserResponse  # Nested user
    
    class Config:
        from_attributes = True

# API returns
{
  "id": "model-uuid",
  "name": "My Model",
  "user": {
    "id": "user-uuid",
    "email": "user@test.com"
  }
}
```

### 4. Partial Updates

```python
# All fields optional for PATCH
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None

# In route
update_data = user_data.dict(exclude_unset=True)  # Only get provided fields
for field, value in update_data.items():
    setattr(user, field, value)
```

### 5. Database Session Management

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Engine (one per application)
engine = create_async_engine(DATABASE_URL)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency for routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Auto-commit on success
        except Exception:
            await session.rollback()  # Auto-rollback on error
            raise
        finally:
            await session.close()
```

### 6. Soft Delete Pattern

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

# Instead of deleting
async def soft_delete_user(db: AsyncSession, user_id: str):
    user = await get_user(db, user_id)
    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    await db.commit()

# Filter out deleted in queries
async def get_active_users(db: AsyncSession):
    result = await db.execute(
        select(User).where(User.is_deleted == False)
    )
    return result.scalars().all()
```

---

## Common Mistakes to Avoid

### ❌ Don't expose database models directly

```python
# BAD
@app.get("/users", response_model=User)  # SQLAlchemy model
async def get_users():
    return db.query(User).all()

# GOOD
@app.get("/users", response_model=list[UserResponse])  # Pydantic schema
async def get_users():
    users = db.query(User).all()
    return users  # FastAPI converts using UserResponse
```

### ❌ Don't forget to commit

```python
# BAD
user = User(email="test@test.com")
db.add(user)
# Forgot db.commit() - changes not saved!

# GOOD
user = User(email="test@test.com")
db.add(user)
await db.commit()
await db.refresh(user)
```

### ❌ Don't use synchronous SQLAlchemy with async FastAPI

```python
# BAD (blocks event loop)
@app.get("/users")
def get_users():  # Sync function
    return db.query(User).all()  # Sync query

# GOOD
@app.get("/users")
async def get_users():  # Async function
    result = await db.execute(select(User))  # Async query
    return result.scalars().all()
```

### ❌ Don't return passwords in responses

```python
# BAD
class UserResponse(BaseModel):
    email: str
    password: str  # NEVER DO THIS!

# GOOD
class UserResponse(BaseModel):
    email: str
    # No password field
```

---

## The 20% You'll Use 80% of the Time

**Pydantic**:
1. ✅ `BaseModel` for schemas
2. ✅ `Field()` for validation
3. ✅ `EmailStr` for emails
4. ✅ `from_attributes = True` in Config
5. ✅ `@validator` for custom validation

**SQLAlchemy**:
1. ✅ `Column()` with types (String, Integer, DateTime)
2. ✅ `ForeignKey()` for relationships
3. ✅ `relationship()` with `back_populates`
4. ✅ `select()` for queries
5. ✅ `where()` for filtering
6. ✅ `add()`, `commit()`, `refresh()` for CRUD

**Everything else is bonus.**

---

## Your Project Examples

Check these files:
- `app/models/user.py` - SQLAlchemy models
- `app/schemas/user.py` - Pydantic schemas
- `app/api/v1/auth.py` - Complete CRUD examples
- `app/db/session.py` - Database session setup

**Next**: Read `FASTAPI_MASTERY.md` to see how these pieces connect in routes.
