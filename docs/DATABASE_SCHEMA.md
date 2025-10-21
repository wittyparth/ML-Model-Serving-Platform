# Database Schema Design

## 🎯 Overview

**Database:** PostgreSQL 15+  
**ORM:** SQLAlchemy 2.0+  
**Migrations:** Alembic  
**Design Principles:** Normalized, scalable, ACID-compliant

---

## 📊 Entity Relationship Diagram (ERD)

```
┌─────────────────────┐
│       Users         │
│─────────────────────│
│ PK id (UUID)        │
│    email            │
│    hashed_password  │
│    full_name        │
│    is_active        │
│    is_admin         │
│    created_at       │
│    updated_at       │
└──────────┬──────────┘
           │
           │ 1:N (one user has many models)
           │
           ▼
┌─────────────────────┐
│       Models        │
│─────────────────────│
│ PK id (UUID)        │
│ FK user_id          │◄───────┐
│    name             │        │
│    description      │        │
│    model_type       │        │
│    version          │        │ 1:N (one model has many predictions)
│    file_path        │        │
│    file_size        │        │
│    status           │        │
│    input_schema     │        │
│    output_schema    │        │
│    created_at       │        │
│    updated_at       │        │
└──────────┬──────────┘        │
           │                   │
           │ 1:N                │
           │                   │
           ▼                   │
┌─────────────────────┐        │
│    Predictions      │        │
│─────────────────────│        │
│ PK id (UUID)        │        │
│ FK model_id         │────────┘
│ FK user_id          │
│    input_data       │
│    output_data      │
│    inference_time   │
│    status           │
│    error_message    │
│    created_at       │
└─────────────────────┘


┌─────────────────────┐
│      API Keys       │
│─────────────────────│
│ PK id (UUID)        │
│ FK user_id          │───┐
│    key_hash         │   │ 1:N (one user has many API keys)
│    name             │   │
│    is_active        │   │
│    last_used_at     │   │
│    expires_at       │   │
│    created_at       │   │
└─────────────────────┘   │
           │              │
           │              │
           └──────────────┘
           Links to Users table
```

---

## 📋 Table Definitions

### 1. **users** Table

**Purpose:** Store user account information

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
```

**SQLAlchemy Model:**
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    models = relationship("Model", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
```

**Why UUID?**
- ✅ Globally unique (no collisions)
- ✅ Non-sequential (security)
- ✅ Distributed-friendly
- ✅ Future-proof for scaling

---

### 2. **models** Table

**Purpose:** Store ML model metadata and versioning

```sql
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_type VARCHAR(50) NOT NULL,  -- 'sklearn', 'tensorflow', 'pytorch', etc.
    version INTEGER DEFAULT 1,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,  -- in bytes
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'deprecated', 'archived'
    input_schema JSONB,  -- Store expected input format
    output_schema JSONB,  -- Store output format
    metadata JSONB,  -- Additional flexible metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint: one user can't have same model name + version
    CONSTRAINT unique_user_model_version UNIQUE (user_id, name, version)
);

-- Indexes
CREATE INDEX idx_models_user_id ON models(user_id);
CREATE INDEX idx_models_status ON models(status);
CREATE INDEX idx_models_created_at ON models(created_at DESC);
CREATE INDEX idx_models_metadata ON models USING GIN(metadata);  -- For JSONB queries
```

**SQLAlchemy Model:**
```python
class Model(Base):
    __tablename__ = "models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    model_type = Column(String(50), nullable=False)
    version = Column(Integer, default=1)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger)
    status = Column(String(20), default="active", index=True)
    input_schema = Column(JSONB)
    output_schema = Column(JSONB)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="models")
    predictions = relationship("Prediction", back_populates="model")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'name', 'version', name='unique_user_model_version'),
    )
```

**Design Decisions:**
- **JSONB for schemas:** Flexible, queryable, efficient storage
- **Version as integer:** Simple incrementing (v1, v2, v3...)
- **Status field:** Soft delete pattern (active/deprecated/archived)
- **Metadata JSONB:** Store arbitrary model info (framework version, training date, etc.)

---

### 3. **predictions** Table

**Purpose:** Log all prediction requests for analytics and debugging

```sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    input_data JSONB NOT NULL,
    output_data JSONB,
    inference_time_ms INTEGER,  -- in milliseconds
    status VARCHAR(20) DEFAULT 'success',  -- 'success', 'failed', 'pending'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_predictions_model_id ON predictions(model_id);
CREATE INDEX idx_predictions_user_id ON predictions(user_id);
CREATE INDEX idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX idx_predictions_status ON predictions(status);

-- Partition by date (future optimization for large datasets)
-- CREATE TABLE predictions_2025_10 PARTITION OF predictions
-- FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
```

**SQLAlchemy Model:**
```python
class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    input_data = Column(JSONB, nullable=False)
    output_data = Column(JSONB)
    inference_time_ms = Column(Integer)
    status = Column(String(20), default="success", index=True)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    model = relationship("Model", back_populates="predictions")
    user = relationship("User", back_populates="predictions")
```

**Why Log Predictions?**
- ✅ Analytics and usage tracking
- ✅ Debugging failed predictions
- ✅ Model performance monitoring
- ✅ Billing/usage reports
- ✅ Data drift detection (future)

---

### 4. **api_keys** Table

**Purpose:** Alternative authentication method for programmatic access

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,  -- Hashed API key
    name VARCHAR(255),  -- User-friendly name ("Production API", "Testing")
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);
```

**SQLAlchemy Model:**
```python
class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    last_used_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
```

---

## 🔍 Query Patterns

### **Common Queries:**

#### 1. Get User's Active Models
```sql
SELECT id, name, version, status, created_at
FROM models
WHERE user_id = :user_id AND status = 'active'
ORDER BY created_at DESC;
```

#### 2. Get Latest Model Version
```sql
SELECT *
FROM models
WHERE user_id = :user_id AND name = :model_name
ORDER BY version DESC
LIMIT 1;
```

#### 3. Model Prediction Statistics
```sql
SELECT 
    m.name,
    m.version,
    COUNT(p.id) as total_predictions,
    AVG(p.inference_time_ms) as avg_inference_time,
    COUNT(CASE WHEN p.status = 'failed' THEN 1 END) as failed_predictions
FROM models m
LEFT JOIN predictions p ON m.id = p.model_id
WHERE m.user_id = :user_id
GROUP BY m.id, m.name, m.version;
```

#### 4. User Usage Analytics (Last 30 Days)
```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as prediction_count,
    AVG(inference_time_ms) as avg_time
FROM predictions
WHERE user_id = :user_id 
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

---

## 🚀 Performance Optimizations

### **Indexing Strategy:**

1. **Primary Keys:** Automatic indexes on UUID primary keys
2. **Foreign Keys:** Indexes on all foreign key columns
3. **Frequent Filters:** Status, is_active, created_at
4. **JSONB Columns:** GIN indexes for JSONB queries
5. **Composite Indexes:** (user_id, created_at) for user-specific queries

### **Connection Pooling:**

```python
# config.py
DATABASE_URL = "postgresql://user:pass@localhost:5432/mlplatform"
engine = create_engine(
    DATABASE_URL,
    pool_size=20,              # Max 20 connections
    max_overflow=10,           # +10 overflow connections
    pool_pre_ping=True,        # Test connections before use
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False                 # Disable SQL logging in production
)
```

### **Query Optimization:**

1. **Use Eager Loading:** Avoid N+1 queries
   ```python
   # Good: Single query with join
   users = db.query(User).options(joinedload(User.models)).all()
   
   # Bad: N+1 queries
   users = db.query(User).all()
   for user in users:
       models = user.models  # Separate query for each user
   ```

2. **Pagination:** Always paginate large result sets
   ```python
   models = db.query(Model)\
       .filter(Model.user_id == user_id)\
       .offset(skip)\
       .limit(limit)\
       .all()
   ```

3. **Selective Column Loading:** Only load needed columns
   ```python
   # Only load specific columns
   models = db.query(Model.id, Model.name, Model.version).all()
   ```

---

## 🔄 Migration Strategy

### **Alembic Setup:**

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Create initial tables"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### **Migration Best Practices:**

1. **Always Review Auto-generated Migrations:** Alembic isn't perfect
2. **Test Migrations:** Run on dev/staging before production
3. **Backward Compatible:** Don't break existing code
4. **Data Migrations:** Use separate scripts for data changes
5. **Rollback Plan:** Always test downgrade migrations

---

## 🧪 Seed Data (for Development)

```python
# scripts/seed_data.py
from app.models import User, Model
from app.core.security import get_password_hash

# Create test user
test_user = User(
    email="test@example.com",
    hashed_password=get_password_hash("testpassword123"),
    full_name="Test User",
    is_active=True
)
db.add(test_user)
db.commit()

# Create test model
test_model = Model(
    user_id=test_user.id,
    name="iris_classifier",
    description="Iris species classification model",
    model_type="sklearn",
    version=1,
    file_path="models/test_user/iris_classifier/v1/model.pkl",
    status="active"
)
db.add(test_model)
db.commit()
```

---

## 📊 Database Monitoring

### **Key Metrics to Track:**

1. **Connection Pool Usage:**
   - Active connections
   - Idle connections
   - Connection wait time

2. **Query Performance:**
   - Slow queries (> 100ms)
   - Most frequent queries
   - Query execution plans

3. **Table Statistics:**
   - Table sizes
   - Index usage
   - Dead tuples (vacuum needed)

### **PostgreSQL Monitoring Queries:**

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Slow queries
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🎓 Interview Talking Points

### **Schema Design:**
- **Why UUID over INT?** Security, distributed systems, no collisions
- **Why JSONB?** Flexible schema, queryable, efficient storage
- **Why soft delete (status)?** Data retention, analytics, undo capability

### **Performance:**
- **Indexing strategy?** All FKs, frequent filters, JSONB columns
- **N+1 queries?** Use eager loading with joinedload/selectinload
- **Scaling?** Connection pooling, read replicas, caching layer

### **Data Integrity:**
- **Foreign keys?** CASCADE deletes, referential integrity
- **Transactions?** ACID compliance, rollback on errors
- **Migrations?** Alembic for version control, backward compatible

---

**Last Updated:** October 21, 2025  
**Status:** ✅ Database Schema Design Complete  
**Next:** API Endpoint Design
