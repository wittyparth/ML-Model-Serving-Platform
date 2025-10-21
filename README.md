# ML Model Serving Platform

> A production-ready platform for deploying and serving machine learning models via REST API

**Status:** 🚧 In Development  
**Timeline:** October 2025 - December 2025  
**Tech Stack:** FastAPI, PostgreSQL, Redis, Docker

---

## 🎯 Project Overview

This platform allows data scientists and ML engineers to deploy their trained models without writing deployment code. Upload a model file, get a REST API endpoint instantly.

**Think of it as:** Heroku for ML Models

### **Key Features**

- 🔐 **User Authentication** - JWT-based auth with secure password hashing
- 📦 **Model Management** - Upload, version, and manage ML models
- 🚀 **Real-time Predictions** - Fast inference with Redis caching
- 📊 **Batch Processing** - Handle large prediction jobs asynchronously  
- 📈 **Analytics** - Track model usage and performance
- 🔑 **API Keys** - Alternative authentication for programmatic access
- ⚡ **High Performance** - Async API with sub-200ms response times

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              Client Layer                        │
│  (Web UI / Mobile / External Services)          │
└────────────────┬────────────────────────────────┘
                 │ HTTPS/REST
                 ▼
┌─────────────────────────────────────────────────┐
│         FastAPI Application Server               │
│  • Authentication (JWT)                          │
│  • Request Validation                            │
│  • Rate Limiting                                 │
│  • Auto Documentation                            │
└────────────┬──────────┬──────────┬──────────────┘
             │          │          │
       ┌─────▼───┐ ┌────▼────┐ ┌──▼──────┐
       │PostgreSQL│ │  Redis  │ │  File   │
       │(metadata)│ │ (cache) │ │ Storage │
       └──────────┘ └─────────┘ └─────────┘
```

[**→ View Detailed Architecture**](./docs/ARCHITECTURE.md)

---

## 🛠️ Technology Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| **API Framework** | FastAPI | High performance, async, auto-docs |
| **Database** | PostgreSQL 15+ | ACID compliance, JSONB support |
| **Cache** | Redis 7.0+ | Sub-millisecond latency, versatility |
| **ORM** | SQLAlchemy | Type-safe, migration support |
| **Web Server** | Uvicorn | ASGI, async support |
| **Validation** | Pydantic | Auto-validation, type hints |
| **Testing** | pytest | Rich ecosystem, fixtures |
| **Containerization** | Docker | Reproducible environments |
| **Deployment** | Render/Railway | Easy deployment, free tier |

[**→ See Technology Decisions**](./docs/TECH_DECISIONS.md)

---

## 📚 Documentation

Comprehensive documentation for understanding and explaining this project:

- **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - System design and component breakdown
- **[DATABASE_SCHEMA.md](./docs/DATABASE_SCHEMA.md)** - Database design and ERD
- **[API_DESIGN.md](./docs/API_DESIGN.md)** - Complete API specifications
- **[TECH_DECISIONS.md](./docs/TECH_DECISIONS.md)** - Technology choice justifications
- **[INTERVIEW_PREP.md](./docs/INTERVIEW_PREP.md)** - Interview Q&A guide
- **[docs/README.md](./docs/README.md)** - Documentation navigation guide

---

## 🚀 Quick Start

### **Prerequisites**

```bash
# Required software
Python 3.11+
PostgreSQL 15+
Redis 7.0+
Docker (optional)
```

### **Local Development Setup**

```bash
# Clone repository
git clone https://github.com/wittyparth/ML-Model-Serving-Platform.git
cd ML-Model-Serving-Platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload

# API runs at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

### **Docker Setup**

```bash
# Start all services (API, PostgreSQL, Redis)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

---

## 📖 API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### **Quick API Examples**

**Register User:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecureP@ss123",
    "full_name": "John Doe"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecureP@ss123"
  }'
```

**Upload Model:**
```bash
curl -X POST http://localhost:8000/api/v1/models/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@model.pkl" \
  -F "name=iris_classifier" \
  -F "model_type=sklearn"
```

**Make Prediction:**
```bash
curl -X POST http://localhost:8000/api/v1/predict/MODEL_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "sepal_length": 5.1,
      "sepal_width": 3.5,
      "petal_length": 1.4,
      "petal_width": 0.2
    }
  }'
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

**Test Coverage Target:** 80%+

---

## 📊 Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time (p95) | < 200ms | TBD |
| Prediction Latency | < 500ms | TBD |
| Cache Hit Rate | > 70% | TBD |
| Database Query Time (p95) | < 50ms | TBD |
| Concurrent Users | 100+ | TBD |
| Uptime | 99%+ | TBD |

---

## 🔒 Security Features

- ✅ JWT authentication with token rotation
- ✅ Password hashing with bcrypt (12 rounds)
- ✅ Rate limiting per user/IP
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ HTTPS only in production
- ✅ CORS configuration
- ✅ API key authentication option
- ✅ Environment variable management

---

## 📈 Roadmap

### **Phase 1: MVP (Weeks 1-4)** ✅ *In Progress*
- [ ] User authentication (JWT)
- [ ] Model upload and storage
- [ ] Real-time prediction API
- [ ] Basic caching with Redis
- [ ] API documentation

### **Phase 2: Production Features (Weeks 5-6)**
- [ ] Model versioning
- [ ] Batch predictions
- [ ] Rate limiting
- [ ] Analytics dashboard
- [ ] Comprehensive testing

### **Phase 3: Advanced Features (Weeks 7-8)**
- [ ] API key management
- [ ] Model performance tracking
- [ ] Background job processing
- [ ] Monitoring and logging
- [ ] Production deployment

### **Future Enhancements**
- [ ] Support for TensorFlow/PyTorch models
- [ ] Model A/B testing
- [ ] Data drift detection
- [ ] Real-time monitoring dashboard
- [ ] Multi-region deployment

---

## 🎓 Learning Resources

This project demonstrates understanding of:

- **Backend Development:** FastAPI, REST APIs, async programming
- **Database Design:** PostgreSQL, SQLAlchemy, migrations, indexing
- **Caching Strategies:** Redis, cache-aside pattern, TTL management
- **Authentication:** JWT tokens, password hashing, authorization
- **System Design:** Monolithic architecture, component separation
- **DevOps:** Docker, containerization, deployment
- **Testing:** Unit tests, integration tests, test coverage
- **Performance:** Query optimization, caching, async operations

---

## 🤝 Contributing

This is a personal portfolio project, but feedback is welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Partha Saradh Munakala**  
IIT Dhanbad - Electrical Engineering  
Software Engineer @ Pursuit Software

- GitHub: [@wittyparth](https://github.com/wittyparth)
- LinkedIn: [Your LinkedIn]
- LeetCode: Knight (1887 rating)

---

## 🙏 Acknowledgments

- FastAPI documentation and community
- PostgreSQL and SQLAlchemy teams
- Redis labs for excellent caching solution
- The ML community for inspiration

---

## 📞 Contact

For questions or discussions about this project:
- Open an issue on GitHub
- Reach out via LinkedIn

---

**Built with ❤️ to learn backend engineering and ML systems design**
