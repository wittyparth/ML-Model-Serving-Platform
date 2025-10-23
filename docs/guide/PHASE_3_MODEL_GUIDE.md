# 📦 Phase 3: Model Management - Learning Guide

**What You'll Learn:**
- File upload handling in FastAPI
- Model versioning system
- CRUD operations with SQLAlchemy
- Multi-user data isolation
- Soft delete patterns
- UUID-based identification

---

## 🎯 What We Built in Phase 3

### Model Management Features
```
✅ Upload ML models (joblib/pickle files)
✅ Automatic versioning (v1, v2, v3...)
✅ List models with pagination
✅ Get model details
✅ Update model metadata
✅ Soft delete (mark inactive, don't actually delete)
✅ Multi-user isolation (users can't see each other's models)
```

### Endpoints Created
```
POST   /api/v1/models/upload        - Upload new model
GET    /api/v1/models               - List all models (paginated)
GET    /api/v1/models/{id}          - Get model details
PUT    /api/v1/models/{id}          - Update model
DELETE /api/v1/models/{id}          - Soft delete model
POST   /api/v1/models/{id}/versions - Create new version
GET    /api/v1/models/{id}/versions - List all versions
PUT    /api/v1/models/{id}/activate - Activate specific version
```

---

## 📤 File Upload in FastAPI

### Why File Upload is Tricky
File uploads are different from JSON data:
- Can be very large (100MB+ models)
- Need validation (file type, size)
- Must be saved to disk
- Security risks (malicious files)

### Basic File Upload

**Endpoint Definition:**
```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import os

router = APIRouter(prefix="/models", tags=["Models"])

@router.post("/upload")
async def upload_model(
    file: UploadFile = File(...),  # The uploaded file
    name: str,                      # Model name (form data)
    model_type: str,                # sklearn, tensorflow, etc
    description: str = None,        # Optional description
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a machine learning model"""
    
    # 1. Validate file
    # 2. Save to disk
    # 3. Create database record
    # 4. Return model info
```

### Understanding `UploadFile`

**What is UploadFile?**
A special FastAPI class that handles uploaded files efficiently.

**Properties:**
```python
file.filename          # Original filename: "model.pkl"
file.content_type      # MIME type: "application/octet-stream"
file.file              # File-like object for reading
file.size              # File size in bytes (if available)
```

**Methods:**
```python
await file.read()      # Read entire file into memory
await file.seek(0)     # Move to beginning of file
await file.close()     # Close the file
```

### Step 1: Validate File

```python
# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pkl', '.joblib', '.h5', '.pt', '.pth', '.onnx'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file
    
    Checks:
    1. File extension is allowed
    2. File size is within limit
    3. File is not empty
    """
    # Check extension
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {ALLOWED_EXTENSIONS}"
        )
    
    # Check size (if available)
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {MAX_FILE_SIZE} bytes"
        )
    
    # Check not empty
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
```

**Common Mistakes:**
❌ Not validating file type → Users upload malicious files
❌ No size limit → Server runs out of disk space
❌ Trusting client-provided MIME type → Can be spoofed
❌ Not sanitizing filename → Path traversal attacks

### Step 2: Save File to Disk

```python
import aiofiles
from pathlib import Path

async def save_upload_file(
    upload_file: UploadFile,
    destination_dir: str,
    filename: str = None
) -> str:
    """
    Save uploaded file to disk
    
    Args:
        upload_file: The uploaded file
        destination_dir: Where to save
        filename: Optional custom filename
    
    Returns:
        Full path to saved file
    """
    # Use custom filename or generate unique one
    if not filename:
        filename = f"{uuid.uuid4()}{os.path.splitext(upload_file.filename)[1]}"
    
    # Create destination directory if doesn't exist
    Path(destination_dir).mkdir(parents=True, exist_ok=True)
    
    # Full path
    file_path = os.path.join(destination_dir, filename)
    
    # Save file (async for better performance)
    async with aiofiles.open(file_path, 'wb') as f:
        # Read in chunks to handle large files
        while chunk := await upload_file.read(1024 * 1024):  # 1MB chunks
            await f.write(chunk)
    
    return file_path
```

**Why Async File I/O?**
- Doesn't block other requests
- Better performance with large files
- FastAPI is async-first

**Common Mistakes:**
❌ Reading entire file into memory → Out of memory with large files
❌ Using sync I/O → Blocks other requests
❌ Not creating directories → FileNotFoundError
❌ Predictable filenames → Users can guess/overwrite files
❌ Not handling disk full errors → Server crashes

### Step 3: Create Database Record

```python
from app.models.model import Model

# Calculate file size
file_size = os.path.getsize(file_path)

# Check if model with same name exists (for versioning)
existing_model = db.query(Model).filter(
    Model.user_id == current_user.id,
    Model.name == name
).first()

if existing_model:
    # Create new version
    version = existing_model.version + 1
else:
    # First version
    version = 1

# Create model record
new_model = Model(
    user_id=current_user.id,
    name=name,
    description=description,
    model_type=model_type,
    version=version,
    file_path=file_path,
    file_size=file_size,
    status="active"
)

db.add(new_model)
db.commit()
db.refresh(new_model)

return {
    "success": True,
    "data": {
        "model": ModelResponse.model_validate(new_model)
    },
    "message": f"Model uploaded successfully (v{version})"
}
```

---

## 🗄️ Database Model for Models

### Model Table Schema

**`app/models/model.py`:**
```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class Model(Base):
    __tablename__ = "models"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Model Information
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    model_type = Column(String, nullable=False)  # sklearn, tensorflow, pytorch
    version = Column(Integer, default=1, nullable=False)
    
    # File Information
    file_path = Column(String, nullable=False)  # Path on disk
    file_size = Column(Integer, nullable=False)  # Size in bytes
    
    # Status
    status = Column(String, default="active")  # active, inactive, training
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="models")
    predictions = relationship("Prediction", back_populates="model", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Model {self.name} v{self.version}>"
```

**Key Design Decisions:**

1. **UUID Primary Key**
   ```python
   id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
   ```
   - Non-sequential (security)
   - Globally unique
   - Can generate client-side

2. **User Foreign Key**
   ```python
   user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
   ```
   - Links model to owner
   - Enables multi-user isolation
   - Cascade delete possible

3. **Versioning**
   ```python
   version = Column(Integer, default=1, nullable=False)
   ```
   - Track model evolution
   - Can have multiple versions
   - Version 1, 2, 3, etc.

4. **Soft Delete**
   ```python
   status = Column(String, default="active")
   ```
   - Don't actually delete
   - Just mark as "inactive"
   - Can recover if needed

5. **Timestamps**
   ```python
   created_at = Column(DateTime(timezone=True), server_default=func.now())
   updated_at = Column(DateTime(timezone=True), onupdate=func.now())
   ```
   - Track when created
   - Auto-update on changes
   - Timezone-aware

**Common Mistakes:**
❌ Integer IDs → Sequential, predictable
❌ No user_id → Can't isolate users
❌ Hard delete → Can't recover
❌ No timestamps → Can't track changes
❌ Not timezone-aware → Bugs with different timezones

---

## 🔄 Model Versioning System

### Why Version Models?

Imagine you improve your ML model:
- Old version: 85% accuracy
- New version: 92% accuracy

**Problems without versioning:**
- Can't rollback if new version has bugs
- Can't compare performance
- Lose history of improvements

**With versioning:**
- Keep all versions
- Easy rollback
- Compare versions
- A/B testing

### Versioning Implementation

```python
@router.post("/{model_id}/versions")
async def create_new_version(
    model_id: str,
    file: UploadFile = File(...),
    description: str = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new version of an existing model"""
    
    # 1. Get original model
    original_model = db.query(Model).filter(
        Model.id == model_id,
        Model.user_id == current_user.id  # Security: Only owner
    ).first()
    
    if not original_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # 2. Find highest version
    max_version = db.query(func.max(Model.version)).filter(
        Model.name == original_model.name,
        Model.user_id == current_user.id
    ).scalar() or 0
    
    new_version = max_version + 1
    
    # 3. Save new file
    validate_file(file)
    file_path = await save_upload_file(
        file,
        f"models/{current_user.id}/{original_model.name}",
        f"v{new_version}.pkl"
    )
    
    # 4. Create new model record
    new_model = Model(
        user_id=current_user.id,
        name=original_model.name,          # Same name
        description=description,
        model_type=original_model.model_type,
        version=new_version,                # New version!
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        status="active"
    )
    
    # 5. Optional: Deactivate old versions
    db.query(Model).filter(
        Model.name == original_model.name,
        Model.user_id == current_user.id,
        Model.id != new_model.id
    ).update({"status": "inactive"})
    
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    
    return {
        "success": True,
        "data": {"model": ModelResponse.model_validate(new_model)},
        "message": f"Version {new_version} created"
    }
```

### List All Versions

```python
@router.get("/{model_id}/versions")
async def list_model_versions(
    model_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all versions of a model"""
    
    # Get model to get its name
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.user_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Get all versions with same name
    versions = db.query(Model).filter(
        Model.name == model.name,
        Model.user_id == current_user.id
    ).order_by(Model.version.desc()).all()
    
    return {
        "success": True,
        "data": [ModelResponse.model_validate(v) for v in versions],
        "message": f"Found {len(versions)} versions"
    }
```

**Common Mistakes:**
❌ Not checking ownership → Users access others' models
❌ Not tracking max version → Version conflicts
❌ Deleting old versions → Can't rollback
❌ No version in filename → Files overwrite each other

---

## 📋 CRUD Operations

### C - Create (Upload)
Already covered above ✅

### R - Read (Get/List)

**Get Single Model:**
```python
@router.get("/{model_id}")
async def get_model(
    model_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get model details by ID"""
    
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.user_id == current_user.id  # Only owner can see
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    return {
        "success": True,
        "data": ModelResponse.model_validate(model),
        "message": "Model retrieved successfully"
    }
```

**List All Models (with Pagination):**
```python
@router.get("/")
async def list_models(
    skip: int = 0,              # Offset
    limit: int = 10,            # Page size
    status: str = None,         # Filter by status
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all models for current user"""
    
    # Base query
    query = db.query(Model).filter(Model.user_id == current_user.id)
    
    # Optional status filter
    if status:
        query = query.filter(Model.status == status)
    
    # Count total (for pagination info)
    total = query.count()
    
    # Apply pagination
    models = query.offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "data": [ModelResponse.model_validate(m) for m in models],
        "pagination": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "pages": (total + limit - 1) // limit  # Ceiling division
        },
        "message": f"Found {len(models)} models"
    }
```

**Pagination Explained:**
```
Total: 25 models
Limit: 10 per page

Page 1: skip=0,  limit=10  → Models 1-10
Page 2: skip=10, limit=10  → Models 11-20
Page 3: skip=20, limit=10  → Models 21-25
```

### U - Update

```python
@router.put("/{model_id}")
async def update_model(
    model_id: str,
    update_data: ModelUpdate,  # Pydantic schema
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update model metadata (not the file itself)"""
    
    # Get model
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.user_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Update only provided fields
    update_dict = update_data.dict(exclude_unset=True)
    
    for field, value in update_dict.items():
        setattr(model, field, value)
    
    db.commit()
    db.refresh(model)
    
    return {
        "success": True,
        "data": ModelResponse.model_validate(model),
        "message": "Model updated successfully"
    }
```

**Pydantic Schema for Update:**
```python
from pydantic import BaseModel
from typing import Optional

class ModelUpdate(BaseModel):
    """Schema for updating model metadata"""
    description: Optional[str] = None
    status: Optional[str] = None  # active, inactive, training
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Updated description",
                "status": "active"
            }
        }
```

### D - Delete (Soft Delete)

```python
@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete model (mark as inactive)"""
    
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.user_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Soft delete - just mark as inactive
    model.status = "inactive"
    
    # Optional: Delete file from disk
    # if os.path.exists(model.file_path):
    #     os.remove(model.file_path)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Model deleted successfully"
    }
```

**Why Soft Delete?**
- ✅ Can recover if mistake
- ✅ Keep history/audit trail
- ✅ Don't break relationships
- ✅ Safer than hard delete

**When to Hard Delete:**
- User explicitly requests it
- Compliance requirements (GDPR)
- Disk space constraints

**Common Mistakes:**
❌ Hard delete by default → Can't recover
❌ Not deleting files → Disk fills up
❌ Breaking foreign key relationships → Database errors
❌ Not checking ownership → Users delete others' models

---

## 🔒 Multi-User Isolation

### The Problem

Without isolation:
```python
# BAD: Returns ALL models from ALL users
models = db.query(Model).all()
```

User A can see User B's models! 😱

### The Solution

Always filter by current user:
```python
# GOOD: Returns only current user's models
models = db.query(Model).filter(
    Model.user_id == current_user.id
).all()
```

### Implementing Isolation

**Every query must check ownership:**

```python
# Get model
model = db.query(Model).filter(
    Model.id == model_id,
    Model.user_id == current_user.id  # 👈 Critical!
).first()

# List models
models = db.query(Model).filter(
    Model.user_id == current_user.id  # 👈 Critical!
).all()

# Update model
db.query(Model).filter(
    Model.id == model_id,
    Model.user_id == current_user.id  # 👈 Critical!
).update({"status": "inactive"})

# Delete model
db.query(Model).filter(
    Model.id == model_id,
    Model.user_id == current_user.id  # 👈 Critical!
).delete()
```

### Testing Isolation

```python
def test_user_cannot_see_other_users_models(client, temp_model_file):
    """Test that User B can't access User A's model"""
    
    # User A uploads a model
    register_user_a(client)
    headers_a = login_user_a(client)
    
    upload_response = client.post(
        "/api/v1/models/upload",
        headers=headers_a,
        data={"name": "user_a_model", "model_type": "sklearn"},
        files={"file": ("model.pkl", temp_model_file, "application/octet-stream")}
    )
    model_a_id = upload_response.json()["data"]["model"]["id"]
    
    # User B tries to access User A's model
    register_user_b(client)
    headers_b = login_user_b(client)
    
    response = client.get(f"/api/v1/models/{model_a_id}", headers=headers_b)
    
    # Should be 404 (or 403)
    assert response.status_code == 404
```

**Common Mistakes:**
❌ Forgetting user_id filter → Security breach
❌ Trusting client-provided user_id → Users can impersonate
❌ Not testing isolation → Bug found in production
❌ Inconsistent filtering → Some endpoints leak data

---

## 📊 Pydantic Schemas

### Request Schema

```python
from pydantic import BaseModel, Field
from typing import Optional

class ModelUpload(BaseModel):
    """Schema for model upload form data"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    model_type: str = Field(..., pattern="^(sklearn|tensorflow|pytorch|onnx)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "my_classifier",
                "description": "A Random Forest classifier",
                "model_type": "sklearn"
            }
        }
```

### Response Schema

```python
from datetime import datetime
from uuid import UUID

class ModelResponse(BaseModel):
    """Schema for model in responses"""
    id: UUID
    name: str
    description: Optional[str]
    model_type: str
    version: int
    file_size: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True  # For SQLAlchemy models
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "my_classifier",
                "description": "A Random Forest classifier",
                "model_type": "sklearn",
                "version": 1,
                "file_size": 1024000,
                "status": "active",
                "created_at": "2025-10-23T10:00:00Z",
                "updated_at": None
            }
        }
```

**Note:** Never include `file_path` in response → Security risk!

---

## 🧪 Testing Model Management

### Test Upload

```python
def test_upload_model(client, auth_headers, temp_model_file):
    """Test successful model upload"""
    with open(temp_model_file, 'rb') as f:
        response = client.post(
            "/api/v1/models/upload",
            headers=auth_headers,
            data={
                "name": "test_model",
                "model_type": "sklearn",
                "description": "Test model"
            },
            files={"file": ("model.pkl", f, "application/octet-stream")}
        )
    
    assert response.status_code == 201
    data = response.json()["data"]["model"]
    assert data["name"] == "test_model"
    assert data["version"] == 1
    assert data["status"] == "active"

def test_upload_invalid_file_type(client, auth_headers):
    """Test upload with invalid file type"""
    response = client.post(
        "/api/v1/models/upload",
        headers=auth_headers,
        data={"name": "test", "model_type": "sklearn"},
        files={"file": ("model.txt", b"fake content", "text/plain")}
    )
    
    assert response.status_code == 400
```

### Test Versioning

```python
def test_create_new_version(client, auth_headers, test_model, temp_model_file):
    """Test creating a new version"""
    with open(temp_model_file, 'rb') as f:
        response = client.post(
            f"/api/v1/models/{test_model.id}/versions",
            headers=auth_headers,
            data={"description": "Version 2"},
            files={"file": ("model.pkl", f, "application/octet-stream")}
        )
    
    assert response.status_code == 201
    data = response.json()["data"]["model"]
    assert data["version"] == 2
    assert data["name"] == test_model.name  # Same name
```

### Test Isolation

```python
def test_user_isolation(client, temp_model_file):
    """Test multi-user isolation"""
    # User 1 uploads model
    client.post("/api/v1/auth/register", json={
        "email": "user1@example.com",
        "password": "password123"
    })
    login1 = client.post("/api/v1/auth/login", json={
        "email": "user1@example.com",
        "password": "password123"
    })
    headers1 = {"Authorization": f"Bearer {login1.json()['data']['access_token']}"}
    
    with open(temp_model_file, 'rb') as f:
        upload1 = client.post(
            "/api/v1/models/upload",
            headers=headers1,
            data={"name": "user1_model", "model_type": "sklearn"},
            files={"file": ("model.pkl", f, "application/octet-stream")}
        )
    model1_id = upload1.json()["data"]["model"]["id"]
    
    # User 2 tries to access User 1's model
    client.post("/api/v1/auth/register", json={
        "email": "user2@example.com",
        "password": "password123"
    })
    login2 = client.post("/api/v1/auth/login", json={
        "email": "user2@example.com",
        "password": "password123"
    })
    headers2 = {"Authorization": f"Bearer {login2.json()['data']['access_token']}"}
    
    response = client.get(f"/api/v1/models/{model1_id}", headers=headers2)
    assert response.status_code == 404  # Can't see it
    
    # User 2 lists models - should be empty
    list_response = client.get("/api/v1/models", headers=headers2)
    assert len(list_response.json()["data"]) == 0
```

---

## 📚 Key Takeaways

### Concepts Learned
1. **File Upload**: Handling multipart form data
2. **File Validation**: Security and size checks
3. **Async File I/O**: Non-blocking file operations
4. **Model Versioning**: Tracking model evolution
5. **CRUD Operations**: Create, Read, Update, Delete
6. **Soft Delete**: Mark inactive instead of delete
7. **Multi-User Isolation**: Security through filtering
8. **Pagination**: Handling large datasets

### Best Practices
✅ Always validate file uploads
✅ Use async I/O for large files
✅ Generate unique filenames (UUID)
✅ Filter by user_id in every query
✅ Implement soft delete
✅ Use pagination for lists
✅ Version your models
✅ Never expose file paths in API

### Common Mistakes to Avoid
❌ No file validation → Security risk
❌ Reading entire file to memory → OOM
❌ Predictable filenames → File overwrites
❌ Missing user_id filter → Data leaks
❌ Hard delete → Can't recover
❌ No pagination → Performance issues
❌ Exposing file paths → Security risk
❌ Not testing multi-user isolation

---

## 🔗 Related Documentation

- See `docs/DATABASE_SCHEMA.md` for Model table details
- See `docs/API_DESIGN.md` for endpoint specifications
- See `tests/test_models.py` for complete test examples

**Next:** [Phase 4: Prediction Engine →](PHASE_4_PREDICTION_GUIDE.md)
