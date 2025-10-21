# Interview Preparation Guide

## 🎯 Overview

This guide helps you confidently discuss the ML Model Serving Platform in technical interviews. Practice these answers until you can explain them naturally.

---

## 📋 Table of Contents

1. [Project Overview Questions](#project-overview)
2. [Architecture & Design Questions](#architecture--design)
3. [Technology Stack Questions](#technology-stack)
4. [Database & Performance Questions](#database--performance)
5. [Security Questions](#security)
6. [Scalability Questions](#scalability)
7. [ML-Specific Questions](#ml-specific-questions)
8. [Problem-Solving Scenarios](#problem-solving-scenarios)
9. [Code Walkthrough Questions](#code-walkthrough)
10. [Behavioral Questions](#behavioral-questions)

---

## 🎬 Project Overview

### **Q1: Tell me about your ML Model Serving Platform.**

**Answer Structure (2 minutes):**
> "I built a production-ready platform for deploying and serving machine learning models via REST API. Think of it as Heroku for ML models - users upload their trained models, and the platform provides prediction endpoints.
>
> **Key Features:**
> - User authentication with JWT
> - Model upload and version management
> - Real-time and batch prediction APIs
> - Caching with Redis for performance
> - Analytics dashboard for usage tracking
>
> **Tech Stack:**
> - Backend: FastAPI (Python async framework)
> - Database: PostgreSQL with SQLAlchemy ORM
> - Cache: Redis for prediction caching and rate limiting
> - Deployment: Docker containers on Render
>
> **Scale:** Handles 100+ concurrent users with sub-200ms API response times. It demonstrates my understanding of backend architecture, async programming, database design, and production deployment."

**Follow-up Points:**
- "I chose this project to learn production backend while applying my Python and algorithm skills from LeetCode."
- "It solves the problem of data scientists not knowing how to deploy models - they just upload a `.pkl` file and get a REST API."

---

### **Q2: Why did you build this project?**

**Answer:**
> "I wanted to transition from frontend (React/React Native) to full-stack/backend roles. I already knew Python from college and LeetCode, but needed production backend experience.
>
> I chose an ML serving platform because:
> 1. It's complex enough to showcase backend skills (auth, databases, caching, file handling)
> 2. It combines my Python knowledge with ML (my electrical engineering background)
> 3. It's a real-world problem - many data scientists struggle with model deployment
> 4. It demonstrates system design thinking, not just CRUD operations
>
> Building this taught me async programming, database optimization, API design, and production deployment - all interview-worthy skills."

---

### **Q3: What was the biggest technical challenge?**

**Answer:**
> "The biggest challenge was **model loading and caching strategy**. ML models can be large (50-100 MB), and loading from disk for every prediction is slow (200-500ms).
>
> **Problem:** If I loaded all models into memory, the server would crash. If I loaded on-demand, predictions were slow.
>
> **Solution:** Implemented a **lazy loading + LRU cache** strategy:
> 1. Models load only when first requested (lazy loading)
> 2. Keep 5 most recently used models in memory (LRU cache)
> 3. Prediction results cached in Redis for 1 hour (repeated inputs)
>
> **Result:** 
> - First prediction: ~300ms (load model + infer)
> - Cached predictions: ~5ms (Redis lookup)
> - Repeated model usage: ~50ms (memory inference)
>
> This taught me the importance of profiling (I used `cProfile`) and understanding memory/performance tradeoffs."

---

## 🏗️ Architecture & Design

### **Q4: Walk me through your system architecture.**

**Answer (Use whiteboard/screen share if possible):**

> "I'll draw the architecture:
>
> ```
> Client → API Gateway (FastAPI) → Business Logic Layer
>                                         ↓
>                          ┌──────────────┼──────────────┐
>                          ↓              ↓              ↓
>                      PostgreSQL      Redis        File Storage
>                      (metadata)      (cache)       (models)
> ```
>
> **Request Flow for Prediction:**
> 1. Client sends POST /predict with JWT token
> 2. FastAPI validates token (auth middleware)
> 3. Check Redis cache for same input + model
>    - Cache hit? Return immediately (5ms)
>    - Cache miss? Continue...
> 4. Load model from memory or disk (lazy loading)
> 5. Run inference (50-300ms depending on model)
> 6. Cache result in Redis (1-hour TTL)
> 7. Log prediction to PostgreSQL (async)
> 8. Return response
>
> **Why this architecture?**
> - Caching reduces inference costs (70%+ cache hit rate)
> - Async logging doesn't slow down responses
> - Separation of concerns (metadata in DB, cache in Redis, files on disk)
> - Stateless API for horizontal scaling"

---

### **Q5: Why did you choose a monolithic architecture instead of microservices?**

**Answer:**
> "I chose monolith for the MVP because:
>
> **Pros of Monolith:**
> 1. **Faster development** - one codebase, one deployment
> 2. **Easier debugging** - all logs in one place
> 3. **No network overhead** - function calls vs HTTP requests
> 4. **Simpler deployment** - one Docker container
>
> **When to go Microservices:**
> If I saw these patterns, I'd extract services:
> 1. **Inference engine** needs independent scaling (CPU-heavy)
> 2. **Different teams** working on different features
> 3. **Different tech stacks** needed (e.g., Go for inference, Python for API)
>
> **Current Scale:** Monolith handles 100+ concurrent users easily. Microservices would add complexity without benefits at this scale.
>
> **Future Plan:** If prediction load increases 10x, I'd extract the inference engine into a separate service with auto-scaling."

---

### **Q6: How did you design your database schema?**

**Answer:**
> "I followed normalization principles with these key tables:
>
> **Users (1) → Models (N) → Predictions (N)**
>
> ```
> users: id, email, hashed_password, created_at
> models: id, user_id, name, version, file_path, status
> predictions: id, model_id, user_id, input_data (JSONB), output_data
> api_keys: id, user_id, key_hash, expires_at
> ```
>
> **Key Decisions:**
> 1. **UUID primary keys** - globally unique, non-sequential (security)
> 2. **JSONB for flexible data** - input/output schemas vary by model
> 3. **Status field for soft deletes** - 'active', 'deprecated', 'archived'
> 4. **Version as integer** - simple incrementing (v1, v2, v3)
>
> **Indexing Strategy:**
> - All foreign keys indexed
> - `(user_id, created_at)` for user queries
> - `status` for filtering active models
> - GIN index on JSONB for efficient queries
>
> **Normalization:** 3NF to avoid data duplication, with JSONB for truly flexible data."

---

## 🛠️ Technology Stack

### **Q7: Why FastAPI over Flask or Django?**

**Answer:**
> "I chose FastAPI for three main reasons:
>
> **1. Performance (Async Support):**
> - ML inference is I/O-bound (loading models, DB queries)
> - FastAPI's async/await handles concurrent requests efficiently
> - Flask is synchronous, blocking on I/O operations
>
> **2. Automatic Documentation:**
> - `/docs` endpoint auto-generated from code
> - No need to maintain separate API docs
> - Interactive testing built-in
>
> **3. Data Validation:**
> - Pydantic models validate requests automatically
> - Type hints improve IDE support
> - Clear error messages for clients
>
> **Code Example:**
> ```python
> @app.post('/predict')
> async def predict(input: PredictionInput):  # Auto-validated!
>     result = await model.predict(input.dict())
>     return result
> ```
>
> **Django REST?** Too heavy - we don't need admin panel, ORM-specific features. FastAPI is lean and modern.
>
> **Flask?** Great for simple apps, but lacks async and auto-validation. Would need Flask-RESTX, Marshmallow, etc."

---

### **Q8: Why PostgreSQL over MongoDB?**

**Answer:**
> "PostgreSQL fits our use case better:
>
> **Our Data is Relational:**
> - Users have many models
> - Models have many predictions
> - Need joins for analytics
>
> **PostgreSQL Advantages:**
> 1. **ACID Compliance** - user data integrity is critical
> 2. **JSONB support** - flexible schema where needed (input/output)
> 3. **Rich queries** - aggregations, window functions for analytics
> 4. **Mature ecosystem** - 30+ years, excellent tooling
>
> **MongoDB Trade-offs:**
> - Schema flexibility not needed (our data is structured)
> - Joins are inefficient in MongoDB
> - Eventual consistency is risky for user data
>
> **When I'd use MongoDB:**
> - Truly unstructured data (logs, events)
> - Write-heavy workloads
> - Need horizontal sharding from day 1
>
> **Best of Both:** PostgreSQL JSONB gives us structure + flexibility."

---

### **Q9: Explain your caching strategy with Redis.**

**Answer:**
> "I use Redis for three caching patterns:
>
> **1. Prediction Caching (Cache-Aside):**
> ```python
> # Check cache first
> cached = redis.get(f'pred:{model_id}:{input_hash}')
> if cached:
>     return cached  # 5ms
> 
> # Cache miss - compute and store
> result = model.predict(input)
> redis.setex(f'pred:{model_id}:{input_hash}', 3600, result)
> return result
> ```
> - **TTL:** 1 hour (models might change)
> - **Hit Rate:** 70%+ for production APIs
> - **Savings:** Avoid 50-300ms inference time
>
> **2. Rate Limiting:**
> ```python
> key = f'rate:{user_id}:{minute}'
> if redis.incr(key) > 100:  # 100 req/min
>     raise RateLimitError
> redis.expire(key, 60)
> ```
>
> **3. Session Storage:**
> - JWT token blacklist (logout)
> - Active user sessions
>
> **Why Redis?**
> - Sub-millisecond latency
> - TTL handles expiration automatically
> - Rich data structures (strings, hashes, sets)
>
> **Alternative Considered:** Local cache (not shared across instances), Memcached (less features)."

---

## 🗄️ Database & Performance

### **Q10: How do you handle database performance?**

**Answer:**
> "I use multiple strategies:
>
> **1. Connection Pooling:**
> ```python
> engine = create_engine(
>     DATABASE_URL,
>     pool_size=20,        # Max 20 connections
>     max_overflow=10,     # +10 burst
>     pool_recycle=3600    # Recycle hourly
> )
> ```
> - Reuse connections (avoid overhead)
> - Limit concurrent connections
>
> **2. Indexing Strategy:**
> ```sql
> CREATE INDEX idx_models_user_id ON models(user_id);
> CREATE INDEX idx_predictions_created_at ON predictions(created_at DESC);
> CREATE INDEX idx_models_metadata ON models USING GIN(metadata);
> ```
> - Index all foreign keys
> - Index common filters (status, created_at)
> - GIN index for JSONB queries
>
> **3. Query Optimization:**
> - **Avoid N+1 queries** with eager loading:
>   ```python
>   users = db.query(User).options(joinedload(User.models)).all()
>   ```
> - **Pagination** for large results:
>   ```python
>   models = query.offset(skip).limit(page_size).all()
>   ```
> - **Select only needed columns:**
>   ```python
>   db.query(Model.id, Model.name).all()  # Not SELECT *
>   ```
>
> **4. Async Operations:**
> - Logging happens asynchronously (doesn't block response)
> - Background tasks for analytics
>
> **Result:** p95 query time < 50ms, p95 API response < 200ms."

---

### **Q11: How would you handle 1 million predictions per day?**

**Answer:**
> "I'd optimize in stages:
>
> **Stage 1: Optimize Current Architecture (0-100K/day)**
> - Increase Redis cache size (more memory)
> - Database read replica for analytics queries
> - CDN for static assets
> - **Cost:** ~$50/month
>
> **Stage 2: Horizontal Scaling (100K-1M/day)**
> ```
> Load Balancer
>     ├── API Server 1
>     ├── API Server 2
>     ├── API Server 3
>     └── API Server 4
>           ↓
>     PostgreSQL (RDS with read replicas)
>     Redis Cluster
> ```
> - 4-8 API servers (auto-scaling)
> - Managed PostgreSQL with 2 read replicas
> - Redis Cluster for distributed cache
> - **Cost:** ~$300-500/month
>
> **Stage 3: Microservices (1M+/day)**
> - Extract inference engine (separate service)
> - Message queue (SQS) for async predictions
> - S3 for model storage
> - CloudFront CDN
> - **Cost:** ~$1000+/month
>
> **Bottlenecks to Monitor:**
> 1. **Database connections** - add read replicas
> 2. **Model loading** - separate inference service
> 3. **Network I/O** - CDN and better instance types
>
> **Key Metric:** Cost per prediction should decrease with scale."

---

## 🔐 Security

### **Q12: How do you handle authentication and authorization?**

**Answer:**
> "I implement defense-in-depth with multiple layers:
>
> **Authentication (Who are you?):**
> 1. **Password Storage:**
>    ```python
>    hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
>    ```
>    - bcrypt with 12 rounds (computationally expensive)
>    - Prevents rainbow table attacks
>
> 2. **JWT Tokens:**
>    ```python
>    access_token = jwt.encode({
>        'user_id': user.id,
>        'exp': datetime.utcnow() + timedelta(minutes=30)
>    }, SECRET_KEY, algorithm='HS256')
>    ```
>    - Access token: 30 min (short-lived)
>    - Refresh token: 7 days (rotate regularly)
>    - Stateless (no server-side session)
>
> 3. **API Keys (Alternative):**
>    - For service-to-service auth
>    - Hashed in database
>    - Per-key rate limits
>
> **Authorization (What can you do?):**
> ```python
> @app.get('/models/{model_id}')
> async def get_model(model_id: str, current_user: User = Depends(get_current_user)):
>     model = db.query(Model).filter(Model.id == model_id).first()
>     if model.user_id != current_user.id:
>         raise HTTPException(403, 'Not authorized')
>     return model
> ```
> - **Resource ownership** check
> - **Role-based** (admin vs user)
>
> **Other Security Measures:**
> - HTTPS only in production
> - CORS configuration
> - Rate limiting (prevent DoS)
> - Input validation (Pydantic)
> - SQL injection prevention (SQLAlchemy ORM)"

---

### **Q13: How do you prevent common security vulnerabilities?**

**Answer:**
> "I address OWASP Top 10:
>
> **1. Injection (SQL, NoSQL):**
> - SQLAlchemy ORM with parameterized queries
> - Never concatenate user input into queries
>
> **2. Broken Authentication:**
> - JWT with short expiration
> - Password complexity requirements
> - Rate limit login attempts
>
> **3. Sensitive Data Exposure:**
> - Passwords hashed with bcrypt
> - Secrets in environment variables
> - API keys hashed in database
> - HTTPS for all production traffic
>
> **4. XML External Entities (XXE):**
> - Not accepting XML (JSON only)
>
> **5. Broken Access Control:**
> - Resource ownership checks
> - Role-based authorization
> - JWT validation on every protected route
>
> **6. Security Misconfiguration:**
> - Separate dev/staging/prod configs
> - Debug mode off in production
> - Dependency scanning (Dependabot)
>
> **7. Cross-Site Scripting (XSS):**
> - JSON responses (not HTML)
> - Content-Type headers set correctly
>
> **8. Insecure Deserialization:**
> - Using pickle carefully (only for models)
> - Validating model files before loading
>
> **9. Using Components with Known Vulnerabilities:**
> - Regular `pip audit` runs
> - Dependabot alerts
> - Keep dependencies updated
>
> **10. Insufficient Logging & Monitoring:**
> - Structured JSON logging
> - Failed login attempts logged
> - Unusual API usage alerts"

---

## 📈 Scalability

### **Q14: How would you scale this platform to handle 10,000 concurrent users?**

**Answer:**
> "I'd scale in three dimensions:
>
> **Horizontal Scaling (Add More Servers):**
> ```
> AWS Application Load Balancer
>     ├── ECS Task 1 (API)
>     ├── ECS Task 2 (API)
>     ├── ECS Task 3 (API)
>     └── ECS Task 4 (API) [Auto-scaling]
>           ↓
>     RDS PostgreSQL (Multi-AZ)
>         ├── Primary (writes)
>         ├── Read Replica 1
>         └── Read Replica 2
>           ↓
>     ElastiCache Redis (Cluster Mode)
>           ↓
>     S3 (Model Storage)
> ```
>
> **Vertical Scaling (Bigger Servers):**
> - Current: 2 vCPU, 4GB RAM
> - Scale to: 8 vCPU, 16GB RAM
> - Use case: CPU-intensive inference
>
> **Database Scaling:**
> 1. **Read Replicas** - analytics queries don't slow writes
> 2. **Connection Pooling** - PgBouncer between API and DB
> 3. **Partitioning** - predictions table by month
> 4. **Caching** - Redis caching layer (70%+ hit rate)
>
> **Asynchronous Processing:**
> ```
> API Server → SQS Queue → Worker Pool → S3 Results
> ```
> - Batch predictions in background
> - Workers scale independently
> - Clients poll for results
>
> **Content Delivery:**
> - CloudFront CDN for static assets
> - S3 for model downloads
> - Regional endpoints (future)
>
> **Monitoring:**
> - Prometheus metrics
> - Auto-scaling triggers (CPU > 70%)
> - Alerting (PagerDuty)
>
> **Cost:** ~$500-1000/month for 10K concurrent users."

---

## 🤖 ML-Specific Questions

### **Q15: How do you handle different types of ML models?**

**Answer:**
> "I designed a pluggable architecture:
>
> **Current: Scikit-learn Support**
> ```python
> class SklearnModelHandler:
>     def load(self, file_path):
>         return joblib.load(file_path)
>     
>     def predict(self, model, input_data):
>         return model.predict(input_data)
>     
>     def validate(self, model):
>         return hasattr(model, 'predict')
> ```
>
> **Future: Multiple Frameworks**
> ```python
> class ModelHandlerFactory:
>     handlers = {
>         'sklearn': SklearnHandler(),
>         'tensorflow': TensorFlowHandler(),
>         'pytorch': PyTorchHandler(),
>         'onnx': ONNXHandler()
>     }
>     
>     def get_handler(self, model_type):
>         return self.handlers[model_type]
> ```
>
> **Upload Flow:**
> 1. User specifies model type (`model_type='sklearn'`)
> 2. System validates file format (`.pkl`, `.joblib`)
> 3. Loads model to verify it's valid
> 4. Extracts metadata (input shape, output shape)
> 5. Stores with appropriate handler
>
> **Prediction Flow:**
> 1. Lookup model type from database
> 2. Get appropriate handler
> 3. Load model using handler
> 4. Predict using handler
>
> **Why This Design?**
> - **Extensible:** Add new frameworks easily
> - **Isolated:** Framework-specific code contained
> - **Testable:** Mock handlers for testing
>
> **Future:** ONNX for cross-framework compatibility."

---

### **Q16: How do you handle model versioning?**

**Answer:**
> "I implement semantic versioning for models:
>
> **Storage Structure:**
> ```
> models/
>     user_123/
>         iris_classifier/
>             v1/
>                 model.pkl
>                 metadata.json
>             v2/
>                 model.pkl
>                 metadata.json
>             v3/  ← Latest
>                 model.pkl
>                 metadata.json
> ```
>
> **Database Schema:**
> ```sql
> models:
>     - (user_id, name, version) UNIQUE
>     - version: INTEGER (1, 2, 3...)
>     - status: 'active', 'deprecated', 'archived'
> ```
>
> **Version Resolution:**
> 1. **Explicit version:**
>    ```
>    POST /predict/model_abc?version=2
>    ```
>
> 2. **Latest version (default):**
>    ```sql
>    SELECT * FROM models
>    WHERE name='iris_classifier' AND status='active'
>    ORDER BY version DESC LIMIT 1
>    ```
>
> 3. **Pinned version:** Users can specify default version in settings
>
> **Version Lifecycle:**
> 1. **Upload v1** → status='active'
> 2. **Upload v2** → v2 active, v1 stays active
> 3. **Deprecate v1** → status='deprecated' (still accessible)
> 4. **Archive v1** → status='archived' (read-only)
>
> **Why This Matters:**
> - **Backward compatibility** - clients don't break
> - **A/B testing** - compare v1 vs v2 performance
> - **Rollback** - reactivate old version if new one fails
> - **Gradual migration** - clients update at their pace
>
> **Database records which version was used for each prediction** for debugging."

---

## 🔧 Problem-Solving Scenarios

### **Q17: A user reports predictions are slow. How do you debug?**

**Answer:**
> "I follow a systematic debugging approach:
>
> **Step 1: Gather Data (5 minutes)**
> - Which model? (some models are slower)
> - Input size? (large inputs take longer)
> - Consistent slowness or spike? (transient issue?)
> - User location? (network latency?)
>
> **Step 2: Check Logs (10 minutes)**
> ```python
> # Structured logging shows breakdown
> {
>   'model_id': 'abc123',
>   'inference_time_ms': 2500,  # ← SLOW!
>   'load_time_ms': 2000,       # ← Model loading slow
>   'predict_time_ms': 500
> }
> ```
>
> **Step 3: Identify Bottleneck**
> - **Model loading slow** → Model not cached, increase cache size
> - **Inference slow** → Model complexity, optimize or use GPU
> - **Database slow** → Query optimization, add indexes
> - **Network slow** → Add CDN, regional endpoints
>
> **Step 4: Reproduce Locally**
> ```bash
> curl -X POST http://localhost:8000/predict/abc123 \
>      -H "Authorization: Bearer ..." \
>      -d '{"input": ...}' \
>      -w "\nTime: %{time_total}s\n"
> ```
>
> **Step 5: Profile**
> ```python
> import cProfile
> cProfile.run('model.predict(input)')
> ```
>
> **Common Fixes:**
> 1. **Cache miss** → Warm up cache, increase cache size
> 2. **Large model** → Load once, keep in memory
> 3. **Inefficient model** → Suggest user optimize (pruning, quantization)
> 4. **Cold start** → Keep models warm with periodic pings
>
> **Long-term Solution:**
> - Add performance monitoring (Prometheus)
> - Set SLA targets (p95 < 200ms)
> - Alert when exceeded"

---

### **Q18: Database is running out of space. What do you do?**

**Answer:**
> "I'd triage and implement a data retention strategy:
>
> **Immediate Action (1 hour):**
> 1. **Identify space hogs:**
>    ```sql
>    SELECT 
>        tablename,
>        pg_size_pretty(pg_total_relation_size(tablename::text)) as size
>    FROM pg_tables
>    ORDER BY pg_total_relation_size(tablename::text) DESC;
>    ```
>    - Likely culprit: `predictions` table (grows fastest)
>
> 2. **Quick wins:**
>    ```sql
>    -- Archive predictions > 90 days
>    DELETE FROM predictions WHERE created_at < NOW() - INTERVAL '90 days';
>    
>    -- Vacuum to reclaim space
>    VACUUM FULL predictions;
>    ```
>
> **Short-term Solution (1 day):**
> 1. **Implement data retention policy:**
>    ```python
>    # Cron job runs daily
>    @scheduler.scheduled_job('cron', hour=3)
>    def archive_old_predictions():
>        cutoff = datetime.now() - timedelta(days=90)
>        
>        # Export to S3
>        old_predictions = db.query(Prediction).filter(
>            Prediction.created_at < cutoff
>        ).all()
>        export_to_s3(old_predictions, 'archived-predictions/')
>        
>        # Delete from DB
>        db.query(Prediction).filter(
>            Prediction.created_at < cutoff
>        ).delete()
>    ```
>
> 2. **Aggregate old data:**
>    ```sql
>    -- Keep only daily stats, not individual predictions
>    INSERT INTO prediction_stats_daily (date, model_id, count, avg_time)
>    SELECT DATE(created_at), model_id, COUNT(*), AVG(inference_time_ms)
>    FROM predictions
>    WHERE created_at < NOW() - INTERVAL '30 days'
>    GROUP BY DATE(created_at), model_id;
>    ```
>
> **Long-term Solution:**
> 1. **Table Partitioning:**
>    ```sql
>    -- Partition by month
>    CREATE TABLE predictions_2025_10 PARTITION OF predictions
>    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
>    
>    -- Drop old partitions easily
>    DROP TABLE predictions_2024_01;
>    ```
>
> 2. **Monitoring:**
>    - Alert when disk > 80% full
>    - Track table growth rate
>    - Estimate when next cleanup needed
>
> **Alternative:** Move to TimescaleDB for automatic data retention."

---

## 💻 Code Walkthrough

### **Q19: Show me how you implemented JWT authentication.**

**Answer:**
> "I'll walk through the code:
>
> **1. User Login (Generate JWT):**
> ```python
> # app/api/v1/auth.py
> from datetime import datetime, timedelta
> import jwt
> from app.core.config import settings
> from app.core.security import verify_password
>
> @router.post('/login')
> async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
>     # Find user
>     user = db.query(User).filter(User.email == credentials.email).first()
>     if not user or not verify_password(credentials.password, user.hashed_password):
>         raise HTTPException(401, 'Invalid credentials')
>     
>     # Generate tokens
>     access_token = create_access_token(user.id)
>     refresh_token = create_refresh_token(user.id)
>     
>     return {
>         'access_token': access_token,
>         'refresh_token': refresh_token,
>         'token_type': 'bearer'
>     }
>
> def create_access_token(user_id: str) -> str:
>     expires = datetime.utcnow() + timedelta(minutes=30)
>     payload = {
>         'user_id': str(user_id),
>         'exp': expires,
>         'type': 'access'
>     }
>     return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
> ```
>
> **2. Protected Endpoint (Validate JWT):**
> ```python
> # app/api/dependencies.py
> from fastapi import Depends, HTTPException
> from fastapi.security import HTTPBearer
> import jwt
>
> security = HTTPBearer()
>
> async def get_current_user(
>     token: str = Depends(security),
>     db: Session = Depends(get_db)
> ) -> User:
>     try:
>         # Decode token
>         payload = jwt.decode(
>             token.credentials,
>             settings.SECRET_KEY,
>             algorithms=['HS256']
>         )
>         user_id = payload.get('user_id')
>         
>         # Check token type
>         if payload.get('type') != 'access':
>             raise HTTPException(401, 'Invalid token type')
>         
>     except jwt.ExpiredSignatureError:
>         raise HTTPException(401, 'Token expired')
>     except jwt.InvalidTokenError:
>         raise HTTPException(401, 'Invalid token')
>     
>     # Get user from DB
>     user = db.query(User).filter(User.id == user_id).first()
>     if not user or not user.is_active:
>         raise HTTPException(401, 'User not found or inactive')
>     
>     return user
>
> # Use in endpoint
> @router.get('/models')
> async def list_models(
>     current_user: User = Depends(get_current_user),  # ← Dependency injection
>     db: Session = Depends(get_db)
> ):
>     models = db.query(Model).filter(Model.user_id == current_user.id).all()
>     return models
> ```
>
> **Key Points:**
> - **Stateless:** No server-side session storage
> - **Dependency Injection:** FastAPI's `Depends()` is elegant
> - **Error Handling:** Specific errors for debugging
> - **Refresh Tokens:** Longer-lived for token rotation
>
> **Security:**
> - Secret key from environment variable
> - HS256 algorithm (symmetric)
> - Short expiration (30 min)
> - User existence check"

---

## 🎤 Behavioral Questions

### **Q20: How did you learn all these technologies?**

**Answer:**
> "I followed a structured learning approach:
>
> **Week 1-2: Fundamentals**
> - Read FastAPI documentation (official docs are excellent)
> - Built simple CRUD API (Todo app)
> - Understood async/await concepts
>
> **Week 3-4: Database & Authentication**
> - Learned SQL (refresher from college)
> - SQLAlchemy tutorials
> - Implemented JWT auth from scratch
>
> **Week 5-6: Advanced Features**
> - Redis tutorial (try.redis.io)
> - Caching patterns (cache-aside, write-through)
> - Docker basics
>
> **Week 7-8: ML Integration & Polish**
> - Model serialization (joblib)
> - Production deployment
> - Performance optimization
>
> **Learning Resources:**
> - Official documentation (best resource)
> - FastAPI course on YouTube
> - PostgreSQL tutorial
> - Stack Overflow for specific issues
>
> **What Helped:**
> 1. **Hands-on learning:** Built features immediately after learning
> 2. **Documentation:** Explained design decisions in docs (taught myself)
> 3. **Incremental complexity:** Started simple, added features gradually
>
> **My Advantage:**
> - Python from college + LeetCode
> - React/async concepts transferred
> - Strong debugging skills from LeetCode
>
> **Total Time:** ~200 hours over 8 weeks (25 hours/week)"

---

### **Q21: What would you do differently if you built this again?**

**Answer (show self-awareness):**
> "Great question! Here's what I'd change:
>
> **1. Start with API Design First:**
> - I refactored endpoints twice
> - Next time: Design API spec before coding
> - Use OpenAPI spec as contract
>
> **2. Write Tests Earlier:**
> - I added tests after features
> - Should have done TDD (test-driven development)
> - Tests catch regressions early
>
> **3. Better Error Handling from Day 1:**
> - Initially: Generic 500 errors
> - Improved: Specific error codes with context
> - Should have had error taxonomy upfront
>
> **4. Monitoring Built-in:**
> - Added logging/metrics later
> - Should instrument from start
> - Hard to debug without good logs
>
> **5. Consider Asynchronous from Start:**
> - Some operations (email, analytics) could be async
> - Retrofit async is harder than building async-first
>
> **What I Did Right:**
> ✅ **Documentation-first approach**
> ✅ **Modular code structure**
> ✅ **Environment-based configuration**
> ✅ **Git commits with clear messages**
>
> **Biggest Lesson:**
> Production systems need non-functional requirements (logging, monitoring, error handling) from day 1, not bolted on later."

---

## 🎯 Closing

### **Q22: Why should we hire you for this backend role?**

**Answer:**
> "I bring three key strengths:
>
> **1. Fast Learner with Proven Results:**
> - Built production ML platform in 8 weeks
> - Self-taught FastAPI, PostgreSQL, Redis
> - LeetCode Knight shows algorithmic thinking
>
> **2. Full-Stack Perspective:**
> - Frontend experience (React/React Native)
> - Understand API design from consumer perspective
> - Can communicate with frontend teams effectively
>
> **3. Production-Ready Mindset:**
> - Not just features, but auth, caching, monitoring, tests
> - Understand tradeoffs (complexity vs simplicity)
> - Documentation and design decisions matter
>
> **Why Backend?**
> I realized through this project that I enjoy:
> - System design and architecture
> - Performance optimization
> - Scalability challenges
> - Building reliable infrastructure
>
> **What I Bring:**
> - Electrical engineering rigor
> - Strong Python & algorithms
> - Quick ramp-up time
> - Passion for learning backend systems
>
> I'm excited to bring these skills to your team and grow as a backend engineer."

---

## 📝 Practice Tips

### **Before Interview:**
1. ✅ Run your project locally - be ready to demo
2. ✅ Practice explaining architecture on whiteboard
3. ✅ Review your code - be ready for deep dives
4. ✅ Prepare metrics (response times, cache hit rate)
5. ✅ Have a few "I learned..." stories ready

### **During Interview:**
1. 🎯 Start with high-level, drill down if asked
2. 🎯 Use examples from your project
3. 🎯 Mention tradeoffs you considered
4. 🎯 Be honest about what you'd improve
5. 🎯 Show enthusiasm for learning

### **Topics to Review:**
- [ ] FastAPI async/await
- [ ] PostgreSQL indexes and query optimization
- [ ] Redis caching patterns
- [ ] JWT authentication flow
- [ ] Docker and containerization
- [ ] System design principles
- [ ] API design best practices

---

**Last Updated:** October 21, 2025  
**Status:** ✅ Interview Prep Complete  
**Next:** Start Building! 🚀
