# ML Model Serving Platform - System Architecture

## 🎯 Project Overview

**Name:** ML Model Serving Platform  
**Purpose:** Production-ready platform for deploying, versioning, and serving machine learning models via REST API  
**Target:** Resume project demonstrating enterprise-level backend architecture skills  
**Timeline:** 6-8 weeks (October 2025 - December 2025)

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  (Web UI / Mobile App / External Services / API Consumers)       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI Application Server                              │   │
│  │  - Authentication & Authorization (JWT)                  │   │
│  │  - Request Validation (Pydantic)                         │   │
│  │  - Rate Limiting                                         │   │
│  │  - API Documentation (/docs, /redoc)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   BUSINESS   │  │    CACHING   │  │   STORAGE    │
│     LOGIC    │  │     LAYER    │  │     LAYER    │
│    LAYER     │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        │                │                │
┌───────▼────────┐  ┌────▼──────┐  ┌─────▼────────┐
│ Model Manager  │  │   Redis   │  │  PostgreSQL  │
│ - Upload       │  │ - Sessions│  │  - Users     │
│ - Version      │  │ - Cache   │  │  - Models    │
│ - Validate     │  │ - Queues  │  │  - Logs      │
└───────┬────────┘  └───────────┘  └──────────────┘
        │
        │
┌───────▼────────────────────────────┐
│     INFERENCE ENGINE               │
│  ┌──────────────────────────────┐  │
│  │  Model Loading & Caching     │  │
│  │  - Lazy Loading              │  │
│  │  - Memory Management         │  │
│  │  - Version Selection         │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Prediction Service          │  │
│  │  - Real-time Prediction      │  │
│  │  - Batch Prediction          │  │
│  │  - Input Validation          │  │
│  │  - Output Formatting         │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘
        │
        │
┌───────▼────────────────────────────┐
│   MONITORING & LOGGING LAYER       │
│  - Request/Response Logging        │
│  - Performance Metrics             │
│  - Model Performance Tracking      │
│  - Health Checks                   │
└────────────────────────────────────┘
```

---

## 🧩 Core Components

### 1. **API Gateway Layer (FastAPI)**

**Responsibility:** Handle all incoming HTTP requests, authentication, and routing

**Key Features:**
- RESTful API endpoints
- JWT-based authentication
- Request validation using Pydantic models
- Automatic OpenAPI documentation
- CORS handling
- Rate limiting per user/IP
- Error handling and standardized responses

**Why FastAPI?**
- ✅ High performance (async/await support)
- ✅ Automatic API documentation
- ✅ Built-in data validation
- ✅ Type hints and editor support
- ✅ Easy to learn coming from React/JavaScript background
- ✅ Production-ready with uvicorn/gunicorn

### 2. **Business Logic Layer**

**Responsibility:** Core application logic and orchestration

**Components:**

#### **User Management Service**
- User registration and authentication
- Profile management
- API key generation and management
- Permission and role-based access control (RBAC)

#### **Model Management Service**
- Model upload and storage
- Model versioning (v1, v2, v3...)
- Model metadata management
- Model validation (format, size, compatibility)
- Model lifecycle (active, deprecated, archived)

#### **Prediction Service**
- Real-time single predictions
- Batch predictions (async processing)
- Input preprocessing
- Output postprocessing
- Error handling for failed predictions

### 3. **Caching Layer (Redis)**

**Responsibility:** Fast data retrieval and temporary storage

**Use Cases:**
- **Session Storage:** JWT token blacklisting, user sessions
- **Response Caching:** Cache frequent prediction results
- **Rate Limiting:** Track API usage per user
- **Queue Management:** Async job queue for batch predictions
- **Model Metadata Cache:** Quick access to model info

**Why Redis?**
- ✅ In-memory performance (sub-millisecond latency)
- ✅ Support for complex data structures
- ✅ TTL (Time To Live) support
- ✅ Pub/Sub for real-time features
- ✅ Persistence options

### 4. **Storage Layer (PostgreSQL)**

**Responsibility:** Persistent data storage

**Data Models:**
- **Users:** User accounts, credentials, API keys
- **Models:** Model metadata, versions, owner, status
- **Predictions:** Prediction history, inputs, outputs, timestamps
- **Logs:** System logs, audit trails
- **Analytics:** Usage statistics, performance metrics

**Why PostgreSQL?**
- ✅ ACID compliance (data integrity)
- ✅ Rich query capabilities (joins, aggregations)
- ✅ JSON support for flexible schema
- ✅ Excellent performance for complex queries
- ✅ Strong ecosystem and tools

### 5. **Model Storage (File System / S3)**

**Responsibility:** Store actual model files

**Structure:**
```
models/
├── user_123/
│   ├── model_abc/
│   │   ├── v1/
│   │   │   ├── model.pkl
│   │   │   └── metadata.json
│   │   ├── v2/
│   │   │   ├── model.pkl
│   │   │   └── metadata.json
```

**Why File System (initially)?**
- ✅ Simple to implement locally
- ✅ Easy debugging
- ✅ Can migrate to S3 later
- ✅ Good for MVP

### 6. **Inference Engine**

**Responsibility:** Load and execute ML models

**Features:**
- **Lazy Loading:** Load models only when needed
- **Model Caching:** Keep frequently used models in memory
- **Version Selection:** Route to correct model version
- **Input Validation:** Ensure inputs match model expectations
- **Error Handling:** Graceful failures with meaningful errors
- **Performance Monitoring:** Track inference time

**Supported Model Types (Initially):**
- Scikit-learn models (.pkl, .joblib)
- Future: TensorFlow, PyTorch, ONNX

---

## 🔄 Key Workflows

### **Workflow 1: User Registration & Authentication**

```
1. User submits registration (POST /api/auth/register)
   ↓
2. Validate input (Pydantic model)
   ↓
3. Hash password (bcrypt)
   ↓
4. Store in PostgreSQL
   ↓
5. Return success response

Login Flow:
1. User submits credentials (POST /api/auth/login)
   ↓
2. Validate credentials
   ↓
3. Generate JWT token (access + refresh)
   ↓
4. Store session in Redis (optional)
   ↓
5. Return tokens
```

### **Workflow 2: Model Upload**

```
1. User uploads model file (POST /api/models/upload)
   ↓
2. Authenticate user (JWT validation)
   ↓
3. Validate file (type, size, format)
   ↓
4. Generate unique model_id
   ↓
5. Save file to storage (models/user_id/model_id/v1/)
   ↓
6. Extract metadata (input shape, output shape, type)
   ↓
7. Store metadata in PostgreSQL
   ↓
8. Cache metadata in Redis
   ↓
9. Return model info and prediction endpoint
```

### **Workflow 3: Real-time Prediction**

```
1. Client sends prediction request (POST /api/predict/{model_id})
   ↓
2. Authenticate request (JWT or API key)
   ↓
3. Check cache for same input (Redis)
   │
   ├─ Cache Hit → Return cached result
   │
   └─ Cache Miss:
      ↓
      4. Load model (from memory or disk)
         ↓
      5. Validate input format
         ↓
      6. Run inference
         ↓
      7. Format output
         ↓
      8. Cache result (Redis, TTL: 1 hour)
         ↓
      9. Log prediction (PostgreSQL - async)
         ↓
      10. Return prediction
```

### **Workflow 4: Batch Prediction**

```
1. Client submits batch job (POST /api/predict/batch/{model_id})
   ↓
2. Authenticate request
   ↓
3. Validate input data
   ↓
4. Create job_id
   ↓
5. Queue job in Redis (background task)
   ↓
6. Return job_id immediately (202 Accepted)
   ↓
7. Background worker processes job
   ↓
8. Store results in PostgreSQL
   ↓
9. Update job status
   ↓
10. Client polls status (GET /api/jobs/{job_id})
```

---

## 📊 Data Flow Diagram

### **Read-Heavy Operations (Predictions)**

```
Client Request
    ↓
FastAPI Endpoint
    ↓
Check Redis Cache ──→ [CACHE HIT] ──→ Return Result
    │
    │ [CACHE MISS]
    ↓
Load Model (Memory/Disk)
    ↓
Run Inference
    ↓
Store in Redis Cache
    ↓
Return Result
    ↓
Log to PostgreSQL (async)
```

### **Write-Heavy Operations (Model Upload)**

```
Client Upload
    ↓
FastAPI Endpoint
    ↓
Validate File
    ↓
Save to File System
    ↓
Write Metadata to PostgreSQL
    ↓
Cache Metadata in Redis
    ↓
Return Success
```

---

## 🔐 Security Architecture

### **Authentication Layers**

1. **User Authentication:**
   - JWT tokens (access token: 30 min, refresh token: 7 days)
   - Password hashing with bcrypt (12 rounds)
   - Secure token storage (httpOnly cookies)

2. **API Key Authentication:**
   - Alternative to JWT for service-to-service
   - API keys stored hashed in database
   - Rate limiting per API key

3. **Authorization:**
   - Role-based access control (RBAC)
   - Resource ownership (users can only access their models)
   - Admin vs regular user permissions

### **Security Measures**

- ✅ HTTPS only in production
- ✅ CORS configuration
- ✅ Rate limiting (100 requests/minute per user)
- ✅ Input validation (Pydantic models)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ File upload restrictions (size, type)
- ✅ Environment variable management (.env files)
- ✅ Secret rotation strategy

---

## 📈 Scalability Considerations

### **Current Architecture (MVP - Single Server)**

```
[Single EC2/Render Instance]
├── FastAPI App
├── PostgreSQL (local)
├── Redis (local)
└── File Storage (local disk)

Capacity: ~100 concurrent users, ~1000 req/min
```

### **Future Scalability Path**

#### **Phase 1: Horizontal Scaling**
```
Load Balancer
    ├── App Server 1
    ├── App Server 2
    └── App Server 3
         ↓
    PostgreSQL (RDS)
    Redis (ElastiCache)
    S3 (Model Storage)

Capacity: ~1000 concurrent users, ~10,000 req/min
```

#### **Phase 2: Microservices**
```
API Gateway
    ├── Auth Service
    ├── Model Management Service
    ├── Prediction Service (Auto-scaling)
    └── Analytics Service
         ↓
    Message Queue (RabbitMQ/SQS)
    Database Cluster
    Distributed Cache (Redis Cluster)

Capacity: ~10,000+ concurrent users
```

### **Performance Targets (MVP)**

- **API Response Time:** < 200ms (p95)
- **Prediction Latency:** < 500ms (simple models)
- **Concurrent Users:** 100+
- **Database Queries:** < 50ms (p95)
- **Cache Hit Rate:** > 70%
- **Uptime:** 99%+ (hobby tier acceptable)

---

## 🛠️ Technology Stack Summary

| Layer | Technology | Purpose | Why? |
|-------|-----------|---------|------|
| **API Framework** | FastAPI | REST API | High performance, async, great docs |
| **Web Server** | Uvicorn | ASGI server | Production-ready, async support |
| **Database** | PostgreSQL 15+ | Relational data | ACID, powerful queries, JSON support |
| **Cache** | Redis 7.0+ | In-memory cache | Speed, versatility, pub/sub |
| **ORM** | SQLAlchemy | Database abstraction | Type-safe, migration support |
| **Validation** | Pydantic | Data validation | Type hints, auto-validation |
| **Auth** | JWT + bcrypt | Security | Industry standard, stateless |
| **Testing** | pytest | Unit/integration tests | Best Python testing framework |
| **ML** | scikit-learn, joblib | Model training/loading | Simple, well-documented |
| **Container** | Docker | Containerization | Reproducible environments |
| **Deployment** | Render/Railway | Hosting | Free tier, easy deployment |

---

## 📁 Project Structure

```
ml-platform/
├── app/                          # Application code
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── api/                      # API endpoints
│   │   ├── __init__.py
│   │   ├── v1/                   # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # Authentication endpoints
│   │   │   ├── models.py         # Model management endpoints
│   │   │   ├── predictions.py    # Prediction endpoints
│   │   │   └── users.py          # User management endpoints
│   │   └── dependencies.py       # Shared dependencies
│   ├── core/                     # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py             # App configuration
│   │   ├── security.py           # Security utilities
│   │   └── logging.py            # Logging configuration
│   ├── models/                   # Database models
│   │   ├── __init__.py
│   │   ├── user.py               # User model
│   │   ├── model.py              # ML Model metadata
│   │   └── prediction.py         # Prediction log model
│   ├── schemas/                  # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py               # User schemas
│   │   ├── model.py              # Model schemas
│   │   └── prediction.py         # Prediction schemas
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py       # Authentication logic
│   │   ├── model_service.py      # Model management logic
│   │   ├── prediction_service.py # Prediction logic
│   │   └── cache_service.py      # Redis caching logic
│   ├── db/                       # Database
│   │   ├── __init__.py
│   │   ├── session.py            # DB session management
│   │   └── base.py               # Base model
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── file_handler.py       # File operations
│       └── validators.py         # Custom validators
├── tests/                        # Test files
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration
│   ├── test_auth.py
│   ├── test_models.py
│   └── test_predictions.py
├── alembic/                      # Database migrations
│   ├── versions/
│   └── env.py
├── models/                       # Stored ML models (gitignored)
│   └── .gitkeep
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md           # This file
│   ├── API_DESIGN.md
│   ├── DATABASE_SCHEMA.md
│   ├── TECH_DECISIONS.md
│   └── INTERVIEW_PREP.md
├── scripts/                      # Utility scripts
│   ├── seed_data.py
│   └── test_model.py
├── .env.example                  # Environment variables template
├── .gitignore
├── docker-compose.yml            # Multi-container setup
├── Dockerfile                    # Container definition
├── requirements.txt              # Python dependencies
├── README.md                     # Project overview
└── pyproject.toml               # Project metadata
```

---

## 🚀 Deployment Architecture

### **Development Environment**

```
Local Machine
├── FastAPI (localhost:8000)
├── PostgreSQL (localhost:5432)
├── Redis (localhost:6379)
└── Hot Reload Enabled
```

### **Production Environment (Render/Railway)**

```
Cloud Platform
├── Web Service (FastAPI + Uvicorn)
│   ├── Auto-scaling enabled
│   ├── Health checks: /health
│   └── SSL certificate (automatic)
├── PostgreSQL (Managed Database)
│   ├── Automated backups
│   └── Connection pooling
├── Redis (Managed Cache)
│   └── Persistence enabled
└── Environment Variables (Secrets)
```

---

## 🎯 MVP Feature Checklist

### **Phase 1: Core Features (Weeks 1-4)**
- [ ] User authentication (register, login, JWT)
- [ ] Model upload endpoint
- [ ] Model listing (user's models)
- [ ] Real-time prediction API
- [ ] Basic error handling
- [ ] API documentation (/docs)

### **Phase 2: Production Features (Weeks 5-6)**
- [ ] Model versioning
- [ ] Prediction caching (Redis)
- [ ] Rate limiting
- [ ] Batch predictions
- [ ] Logging and monitoring
- [ ] Health check endpoints

### **Phase 3: Advanced Features (Weeks 7-8)**
- [ ] Model performance tracking
- [ ] User analytics dashboard
- [ ] API key management
- [ ] Model soft delete
- [ ] Comprehensive testing (80%+ coverage)
- [ ] Production deployment

---

## 📊 Monitoring & Observability

### **Key Metrics to Track**

1. **Application Metrics:**
   - Request rate (req/sec)
   - Response time (p50, p95, p99)
   - Error rate (4xx, 5xx)
   - Active users

2. **Model Metrics:**
   - Predictions per model
   - Average inference time
   - Cache hit rate
   - Model load time

3. **System Metrics:**
   - CPU usage
   - Memory usage
   - Database connections
   - Redis memory

### **Logging Strategy**

```python
# Structured JSON logging
{
  "timestamp": "2025-10-21T10:30:00Z",
  "level": "INFO",
  "user_id": "user_123",
  "endpoint": "/api/predict/model_abc",
  "method": "POST",
  "status_code": 200,
  "response_time_ms": 156,
  "model_id": "model_abc",
  "model_version": "v2"
}
```

---

## 🎓 Interview Talking Points

### **Architecture Decisions:**
1. **Why FastAPI?** Performance + async support + automatic validation
2. **Why PostgreSQL?** Complex queries, relationships, ACID compliance
3. **Why Redis?** Sub-millisecond latency for caching + session storage
4. **Monolith vs Microservices?** Monolith for MVP (faster development, easier debugging)

### **Scalability:**
1. **How to scale?** Horizontal scaling behind load balancer
2. **Database bottleneck?** Read replicas, connection pooling, caching
3. **Model loading?** Lazy loading + in-memory cache with LRU eviction

### **Security:**
1. **How do you secure APIs?** JWT auth + rate limiting + input validation
2. **How to prevent model theft?** API keys + usage tracking + watermarking (future)

---

## 📝 Next Steps

1. ✅ **Architecture documented** (this file)
2. 🔄 **Database schema design** → `DATABASE_SCHEMA.md`
3. 🔄 **API endpoint specifications** → `API_DESIGN.md`
4. 🔄 **Technology decision rationale** → `TECH_DECISIONS.md`
5. 🔄 **Set up development environment**
6. 🔄 **Generate project structure**
7. 🔄 **Build Week 1 features**

---

**Last Updated:** October 21, 2025  
**Status:** ✅ Architecture Design Complete  
**Next:** Database Schema Design
