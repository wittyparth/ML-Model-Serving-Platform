# 🔮 Phase 4: Prediction Engine - Learning Guide

**What You'll Learn:**
- Loading ML models into memory
- Model caching for performance
- Real-time predictions API
- Input validation with Pydantic
- Error handling for ML models
- Prediction history tracking
- Performance optimization

---

## 🎯 What We Built in Phase 4

### Prediction Features
```
✅ Load models from disk (joblib/pickle)
✅ Cache models in memory (LRU cache)
✅ Accept input data (JSON)
✅ Validate input schema
✅ Make predictions
✅ Return predictions with confidence
✅ Track prediction history
✅ Performance metrics
```

### Endpoints Created
```
POST   /api/v1/predictions/predict        - Make prediction
GET    /api/v1/predictions                - List prediction history
GET    /api/v1/predictions/{id}           - Get prediction details
GET    /api/v1/predictions/stats          - Get usage statistics
```

---

## 🤖 Loading ML Models

### The Challenge

ML models are files on disk, but we need them in memory to make predictions:
- Loading is slow (can take seconds)
- Models can be large (100MB+)
- Need to handle different formats (sklearn, tensorflow, etc.)
- Can't load every time (performance)

### Solution: Model Loader

**`app/core/model_loader.py`:**
```python
import joblib
import pickle
import os
from functools import lru_cache
from typing import Any, Dict
from fastapi import HTTPException, status

class ModelLoader:
    """Load and cache ML models"""
    
    def __init__(self, cache_size: int = 10):
        """
        Initialize model loader
        
        Args:
            cache_size: Maximum number of models to keep in cache
        """
        self.cache_size = cache_size
        self._cache: Dict[str, Any] = {}
    
    def load_model(self, file_path: str, model_type: str) -> Any:
        """
        Load model from disk
        
        Args:
            file_path: Path to model file
            model_type: Type of model (sklearn, tensorflow, etc.)
        
        Returns:
            Loaded model object
        """
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model file not found: {file_path}"
            )
        
        # Check cache first
        if file_path in self._cache:
            print(f"✅ Model loaded from cache: {file_path}")
            return self._cache[file_path]
        
        print(f"⏳ Loading model from disk: {file_path}")
        
        try:
            # Load based on type
            if model_type in ['sklearn', 'xgboost', 'lightgbm']:
                model = joblib.load(file_path)
            elif model_type == 'pickle':
                with open(file_path, 'rb') as f:
                    model = pickle.load(f)
            elif model_type == 'tensorflow':
                import tensorflow as tf
                model = tf.keras.models.load_model(file_path)
            elif model_type == 'pytorch':
                import torch
                model = torch.load(file_path)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
            
            # Add to cache
            self._cache[file_path] = model
            
            # Manage cache size (simple LRU)
            if len(self._cache) > self.cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                print(f"🗑️  Evicted from cache: {oldest_key}")
            
            print(f"✅ Model loaded successfully: {file_path}")
            return model
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error loading model: {str(e)}"
            )
    
    def clear_cache(self):
        """Clear all cached models"""
        self._cache.clear()
        print("🗑️  Model cache cleared")

# Global instance
model_loader = ModelLoader(cache_size=10)
```

### How Caching Works

**Without Cache:**
```
Request 1 → Load model (2 seconds) → Predict
Request 2 → Load model (2 seconds) → Predict  ❌ Slow!
Request 3 → Load model (2 seconds) → Predict  ❌ Slow!
```

**With Cache:**
```
Request 1 → Load model (2 seconds) → Cache → Predict
Request 2 → Get from cache (instant) → Predict  ✅ Fast!
Request 3 → Get from cache (instant) → Predict  ✅ Fast!
```

### LRU Cache Explained

**LRU = Least Recently Used**

When cache is full, remove the model that hasn't been used for the longest time.

```python
Cache size = 2

1. Load Model A → Cache: [A]
2. Load Model B → Cache: [A, B]
3. Load Model C → Cache: [B, C]  (A removed - least recently used)
4. Use Model B  → Cache: [B, C]  (B is now most recent)
5. Load Model D → Cache: [B, D]  (C removed)
```

**Better LRU with Python:**
```python
from functools import lru_cache

@lru_cache(maxsize=10)
def load_model_cached(file_path: str, model_type: str):
    """Load model with automatic LRU caching"""
    if model_type == 'sklearn':
        return joblib.load(file_path)
    elif model_type == 'tensorflow':
        import tensorflow as tf
        return tf.keras.models.load_model(file_path)
    # etc...
```

**Common Mistakes:**
❌ No caching → Every request loads model (slow)
❌ Unlimited cache → Out of memory
❌ Not handling load errors → Server crashes
❌ Wrong file format → Crashes
❌ Not checking file exists → FileNotFoundError

---

## 🎯 Making Predictions

### Prediction Endpoint

**`app/api/v1/predictions.py`:**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import numpy as np
from typing import List, Dict, Any
import time

from app.api.dependencies import get_current_user, get_db
from app.core.model_loader import model_loader
from app.models.model import Model
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionRequest, PredictionResponse

router = APIRouter(prefix="/predictions", tags=["Predictions"])

@router.post("/predict")
async def make_prediction(
    request: PredictionRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Make a prediction using a model
    
    Steps:
    1. Validate model exists and user has access
    2. Load model from disk/cache
    3. Validate input data
    4. Make prediction
    5. Save prediction history
    6. Return result
    """
    
    # 1. Get model from database
    model = db.query(Model).filter(
        Model.id == request.model_id,
        Model.user_id == current_user.id,  # Security check
        Model.status == "active"
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found or inactive"
        )
    
    # 2. Load model
    try:
        ml_model = model_loader.load_model(
            file_path=model.file_path,
            model_type=model.model_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading model: {str(e)}"
        )
    
    # 3. Prepare input data
    try:
        # Convert input to numpy array
        input_data = np.array(request.input_data)
        
        # Reshape if needed (sklearn expects 2D array)
        if input_data.ndim == 1:
            input_data = input_data.reshape(1, -1)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input data: {str(e)}"
        )
    
    # 4. Make prediction
    start_time = time.time()
    
    try:
        # Prediction
        prediction = ml_model.predict(input_data)
        
        # Confidence (if available)
        confidence = None
        if hasattr(ml_model, 'predict_proba'):
            proba = ml_model.predict_proba(input_data)
            confidence = float(np.max(proba))
        
        # Convert to Python types
        prediction = prediction.tolist()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )
    
    prediction_time = time.time() - start_time
    
    # 5. Save to database
    db_prediction = Prediction(
        user_id=current_user.id,
        model_id=model.id,
        input_data=request.input_data,
        prediction=prediction,
        confidence=confidence,
        prediction_time=prediction_time
    )
    
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    
    # 6. Return result
    return {
        "success": True,
        "data": {
            "prediction_id": str(db_prediction.id),
            "prediction": prediction,
            "confidence": confidence,
            "prediction_time": f"{prediction_time:.3f}s"
        },
        "message": "Prediction successful"
    }
```

### Understanding the Flow

```
User Request
    ↓
[1. Validate Model]
    ↓
[2. Load Model from Cache/Disk]
    ↓
[3. Prepare Input Data]
    ↓
[4. Make Prediction]
    ↓
[5. Save to Database]
    ↓
[6. Return Result]
    ↓
User Response
```

### Input Data Validation

**Why validate?**
- ML models expect specific input shapes
- Wrong shape → crash
- Wrong type → crash
- Missing features → wrong predictions

**Example:**
```python
# Model trained on 4 features
model.fit(X_train)  # X_train.shape = (1000, 4)

# Valid input
predict([1.2, 3.4, 5.6, 7.8])  # ✅ Shape: (1, 4)

# Invalid inputs
predict([1.2, 3.4])             # ❌ Shape: (1, 2) - Too few features
predict([1.2, 3.4, 5.6, 7.8, 9.0])  # ❌ Shape: (1, 5) - Too many
predict("hello")                # ❌ Not a number
```

**Validation with Pydantic:**
```python
from pydantic import BaseModel, Field, validator
from typing import List, Union
from uuid import UUID

class PredictionRequest(BaseModel):
    """Schema for prediction request"""
    model_id: UUID
    input_data: List[Union[float, int, str]]  # Flexible input
    
    @validator('input_data')
    def validate_input(cls, v):
        """Validate input data"""
        if len(v) == 0:
            raise ValueError("Input data cannot be empty")
        if len(v) > 1000:
            raise ValueError("Too many features (max 1000)")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": "123e4567-e89b-12d3-a456-426614174000",
                "input_data": [5.1, 3.5, 1.4, 0.2]
            }
        }
```

**Common Mistakes:**
❌ Not reshaping 1D to 2D → sklearn error
❌ Wrong number of features → wrong predictions
❌ String instead of number → type error
❌ Not validating input → model crashes
❌ Not handling errors → server crashes

---

## 🗄️ Prediction Database Model

**`app/models/prediction.py`:**
```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class Prediction(Base):
    __tablename__ = "predictions"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False)
    
    # Prediction Data
    input_data = Column(JSON, nullable=False)  # Store as JSON
    prediction = Column(JSON, nullable=False)  # Store as JSON
    confidence = Column(Float, nullable=True)  # Optional confidence score
    
    # Performance
    prediction_time = Column(Float, nullable=False)  # Time in seconds
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="predictions")
    model = relationship("Model", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction {self.id}>"
```

**Key Design Decisions:**

1. **JSON Columns**
   ```python
   input_data = Column(JSON, nullable=False)
   prediction = Column(JSON, nullable=False)
   ```
   - Store arrays/objects as JSON
   - Flexible schema
   - Can query JSON fields in PostgreSQL

2. **Performance Tracking**
   ```python
   prediction_time = Column(Float, nullable=False)
   ```
   - Measure how long prediction took
   - Identify slow models
   - Optimize performance

3. **Optional Confidence**
   ```python
   confidence = Column(Float, nullable=True)
   ```
   - Not all models provide confidence
   - Classification: yes
   - Regression: no

---

## 📊 Prediction History

### List Predictions

```python
@router.get("/")
async def list_predictions(
    skip: int = 0,
    limit: int = 20,
    model_id: str = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List prediction history for current user"""
    
    # Base query
    query = db.query(Prediction).filter(
        Prediction.user_id == current_user.id
    )
    
    # Optional filter by model
    if model_id:
        query = query.filter(Prediction.model_id == model_id)
    
    # Order by newest first
    query = query.order_by(Prediction.created_at.desc())
    
    # Count total
    total = query.count()
    
    # Paginate
    predictions = query.offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "data": [PredictionResponse.model_validate(p) for p in predictions],
        "pagination": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    }
```

### Get Single Prediction

```python
@router.get("/{prediction_id}")
async def get_prediction(
    prediction_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get prediction details"""
    
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == current_user.id
    ).first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    
    return {
        "success": True,
        "data": PredictionResponse.model_validate(prediction)
    }
```

### Usage Statistics

```python
from sqlalchemy import func

@router.get("/stats")
async def get_prediction_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get prediction statistics for current user"""
    
    # Total predictions
    total = db.query(Prediction).filter(
        Prediction.user_id == current_user.id
    ).count()
    
    # Average prediction time
    avg_time = db.query(func.avg(Prediction.prediction_time)).filter(
        Prediction.user_id == current_user.id
    ).scalar() or 0.0
    
    # Predictions by model
    by_model = db.query(
        Model.name,
        func.count(Prediction.id).label('count')
    ).join(
        Prediction, Prediction.model_id == Model.id
    ).filter(
        Prediction.user_id == current_user.id
    ).group_by(Model.name).all()
    
    # Recent predictions (last 24 hours)
    from datetime import timedelta
    recent_count = db.query(Prediction).filter(
        Prediction.user_id == current_user.id,
        Prediction.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    return {
        "success": True,
        "data": {
            "total_predictions": total,
            "average_prediction_time": f"{avg_time:.3f}s",
            "predictions_24h": recent_count,
            "by_model": [
                {"model": name, "count": count}
                for name, count in by_model
            ]
        }
    }
```

---

## ⚡ Performance Optimization

### 1. Model Caching

**Problem:** Loading model every time is slow
```python
# BAD: Load every time
def predict(model_id):
    model = joblib.load(f"models/{model_id}.pkl")  # 2 seconds
    return model.predict(data)
```

**Solution:** Cache loaded models
```python
# GOOD: Load once, cache
model_cache = {}

def predict(model_id):
    if model_id not in model_cache:
        model_cache[model_id] = joblib.load(f"models/{model_id}.pkl")
    return model_cache[model_id].predict(data)
```

### 2. Batch Predictions

**Problem:** Making 100 requests = 100 predictions
```python
# BAD: One at a time
for data in batch:
    response = requests.post("/predict", json={"input_data": data})
```

**Solution:** Batch endpoint
```python
@router.post("/predict/batch")
async def batch_predict(
    requests: List[PredictionRequest],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Make multiple predictions at once"""
    
    results = []
    
    for req in requests:
        # Load model (from cache if possible)
        model = model_loader.load_model(req.model_id)
        
        # Predict
        prediction = model.predict([req.input_data])
        results.append(prediction)
    
    return {
        "success": True,
        "data": results
    }
```

### 3. Async Operations

**Problem:** Blocking operations slow down other requests
```python
# BAD: Blocking file I/O
def load_model(path):
    return joblib.load(path)  # Blocks other requests
```

**Solution:** Use async
```python
# GOOD: Non-blocking
async def load_model(path):
    async with aiofiles.open(path, 'rb') as f:
        content = await f.read()
        return pickle.loads(content)
```

### 4. Database Connection Pooling

**Already configured in SQLAlchemy:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # 20 connections in pool
    max_overflow=0,        # No extra connections
    pool_pre_ping=True     # Check connection before use
)
```

### 5. Monitoring Slow Predictions

```python
import time
from app.core.logging import logger

@router.post("/predict")
async def predict(request: PredictionRequest, ...):
    start = time.time()
    
    # Make prediction
    result = model.predict(data)
    
    elapsed = time.time() - start
    
    # Log slow predictions
    if elapsed > 1.0:  # More than 1 second
        logger.warning(
            f"Slow prediction: {elapsed:.2f}s",
            extra={
                "model_id": model.id,
                "elapsed": elapsed,
                "user_id": current_user.id
            }
        )
    
    return result
```

**Common Mistakes:**
❌ No caching → Every request is slow
❌ Loading model in sync code → Blocks server
❌ Not using connection pooling → Database bottleneck
❌ Not monitoring performance → Don't know what's slow
❌ No batch endpoints → Inefficient for bulk predictions

---

## 🧪 Testing Predictions

### Test Prediction Endpoint

```python
import pytest
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

@pytest.fixture
def trained_model(tmp_path):
    """Create a simple trained model for testing"""
    # Create simple dataset
    X = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
    y = np.array([0, 1, 1, 0])
    
    # Train model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)
    
    # Save to temp file
    model_path = tmp_path / "test_model.pkl"
    joblib.dump(model, model_path)
    
    return model_path

def test_make_prediction(client, auth_headers, trained_model, db_session):
    """Test successful prediction"""
    # Upload model first
    with open(trained_model, 'rb') as f:
        upload_response = client.post(
            "/api/v1/models/upload",
            headers=auth_headers,
            data={"name": "test_model", "model_type": "sklearn"},
            files={"file": ("model.pkl", f, "application/octet-stream")}
        )
    
    model_id = upload_response.json()["data"]["model"]["id"]
    
    # Make prediction
    response = client.post(
        "/api/v1/predictions/predict",
        headers=auth_headers,
        json={
            "model_id": model_id,
            "input_data": [0.5, 0.5]
        }
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert "prediction" in data
    assert "confidence" in data
    assert "prediction_time" in data
    assert isinstance(data["prediction"], list)

def test_invalid_input(client, auth_headers, test_model):
    """Test prediction with invalid input"""
    response = client.post(
        "/api/v1/predictions/predict",
        headers=auth_headers,
        json={
            "model_id": str(test_model.id),
            "input_data": []  # Empty input
        }
    )
    
    assert response.status_code == 422  # Validation error

def test_model_not_found(client, auth_headers):
    """Test prediction with non-existent model"""
    response = client.post(
        "/api/v1/predictions/predict",
        headers=auth_headers,
        json={
            "model_id": "00000000-0000-0000-0000-000000000000",
            "input_data": [1, 2, 3, 4]
        }
    )
    
    assert response.status_code == 404

def test_prediction_history(client, auth_headers, test_prediction):
    """Test retrieving prediction history"""
    response = client.get(
        "/api/v1/predictions",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) > 0
    assert "input_data" in data[0]
    assert "prediction" in data[0]
```

### Test Model Caching

```python
def test_model_caching(client, auth_headers, trained_model, db_session):
    """Test that models are cached for performance"""
    import time
    
    # Upload model
    with open(trained_model, 'rb') as f:
        upload_response = client.post(
            "/api/v1/models/upload",
            headers=auth_headers,
            data={"name": "test_model", "model_type": "sklearn"},
            files={"file": ("model.pkl", f, "application/octet-stream")}
        )
    
    model_id = upload_response.json()["data"]["model"]["id"]
    
    # First prediction (should load model)
    start = time.time()
    response1 = client.post(
        "/api/v1/predictions/predict",
        headers=auth_headers,
        json={"model_id": model_id, "input_data": [0.5, 0.5]}
    )
    first_time = time.time() - start
    
    # Second prediction (should use cache)
    start = time.time()
    response2 = client.post(
        "/api/v1/predictions/predict",
        headers=auth_headers,
        json={"model_id": model_id, "input_data": [0.5, 0.5]}
    )
    second_time = time.time() - start
    
    # Second should be faster (cached)
    assert second_time < first_time
    assert response1.status_code == 200
    assert response2.status_code == 200
```

---

## 🔍 Error Handling

### Common Errors

1. **Model Not Found**
```python
try:
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(404, "Model not found")
except Exception as e:
    logger.error(f"Error finding model: {e}")
    raise
```

2. **Model Loading Error**
```python
try:
    ml_model = joblib.load(model.file_path)
except FileNotFoundError:
    raise HTTPException(404, "Model file not found on disk")
except Exception as e:
    raise HTTPException(500, f"Error loading model: {str(e)}")
```

3. **Invalid Input**
```python
try:
    input_array = np.array(input_data)
    if input_array.shape[1] != expected_features:
        raise HTTPException(
            400,
            f"Expected {expected_features} features, got {input_array.shape[1]}"
        )
except ValueError as e:
    raise HTTPException(400, f"Invalid input data: {str(e)}")
```

4. **Prediction Error**
```python
try:
    prediction = model.predict(input_data)
except Exception as e:
    logger.error(f"Prediction failed: {e}")
    raise HTTPException(500, f"Prediction error: {str(e)}")
```

### Graceful Degradation

```python
@router.post("/predict")
async def predict(request: PredictionRequest, ...):
    try:
        # Try to make prediction
        result = await make_prediction_internal(request)
        return result
    except ModelLoadError as e:
        # Model loading failed - retry or use backup
        logger.error(f"Model load failed: {e}")
        return {"error": "Model temporarily unavailable", "status": 503}
    except ValidationError as e:
        # Input validation failed
        return {"error": f"Invalid input: {e}", "status": 400}
    except Exception as e:
        # Unknown error - log and return generic message
        logger.exception(f"Unexpected error: {e}")
        return {"error": "Internal server error", "status": 500}
```

---

## 📚 Key Takeaways

### Concepts Learned
1. **Model Loading**: Load ML models from disk
2. **Caching**: Keep models in memory for performance
3. **Input Validation**: Ensure correct data format
4. **Error Handling**: Graceful failures
5. **Performance Tracking**: Measure prediction time
6. **History Tracking**: Save all predictions
7. **Batch Processing**: Efficient bulk predictions

### Best Practices
✅ Cache loaded models (LRU)
✅ Validate input data shape
✅ Handle all error cases
✅ Track prediction metrics
✅ Use async operations
✅ Implement batch endpoints
✅ Monitor slow predictions
✅ Save prediction history

### Common Mistakes to Avoid
❌ No caching → Slow predictions
❌ Not validating input → Crashes
❌ Not handling errors → Server crashes
❌ Blocking operations → Performance issues
❌ No monitoring → Can't optimize
❌ Not tracking history → No analytics
❌ Synchronous file I/O → Slow

---

## 🔗 Related Documentation

- See `docs/PHASE_3_MODEL_GUIDE.md` for model upload
- See `app/core/model_loader.py` for implementation
- See `tests/test_predictions.py` for test examples

**Next:** [Phase 5: Logging & Monitoring →](PHASE_5_LOGGING_GUIDE.md)
