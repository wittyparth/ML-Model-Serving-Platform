# API Design Specification

## 🎯 Overview

**Base URL:** `https://api.mlplatform.com/api/v1`  
**Protocol:** HTTPS only  
**Format:** JSON  
**Authentication:** JWT Bearer Token / API Key  
**Documentation:** Auto-generated via FastAPI (`/docs`, `/redoc`)

---

## 📋 API Conventions

### **Response Format**

#### Success Response:
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "timestamp": "2025-10-21T10:30:00Z"
}
```

#### Error Response:
```json
{
  "success": false,
  "error": {
    "code": "MODEL_NOT_FOUND",
    "message": "Model with ID 'abc123' not found",
    "details": { ... }
  },
  "timestamp": "2025-10-21T10:30:00Z"
}
```

### **HTTP Status Codes**

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (resource created) |
| 202 | Accepted | Async operation accepted (batch jobs) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Valid auth but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error (Pydantic) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Server overloaded |

### **Pagination**

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 5,
    "total_items": 100,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## 🔐 Authentication Endpoints

### **1. User Registration**

**Endpoint:** `POST /auth/register`  
**Authentication:** None  
**Rate Limit:** 5 requests/hour per IP

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "full_name": "John Doe",
      "is_active": true,
      "created_at": "2025-10-21T10:30:00Z"
    }
  },
  "message": "User registered successfully"
}
```

**Validation Rules:**
- Email: Valid email format, unique
- Password: Min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
- Full name: 2-100 characters

---

### **2. User Login**

**Endpoint:** `POST /auth/login`  
**Authentication:** None  
**Rate Limit:** 10 requests/minute per IP

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "full_name": "John Doe"
    }
  },
  "message": "Login successful"
}
```

**Token Expiry:**
- Access Token: 30 minutes
- Refresh Token: 7 days

---

### **3. Refresh Token**

**Endpoint:** `POST /auth/refresh`  
**Authentication:** Refresh Token  
**Rate Limit:** 20 requests/hour

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

---

### **4. Get Current User**

**Endpoint:** `GET /auth/me`  
**Authentication:** Required (JWT)  
**Rate Limit:** 100 requests/minute

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_admin": false,
    "created_at": "2025-10-21T10:30:00Z"
  }
}
```

---

## 🤖 Model Management Endpoints

### **5. Upload Model**

**Endpoint:** `POST /models/upload`  
**Authentication:** Required (JWT)  
**Rate Limit:** 10 uploads/hour  
**Max File Size:** 100 MB

**Request (multipart/form-data):**
```
file: <binary data>
name: "iris_classifier"
description: "Iris species classification model"
model_type: "sklearn"
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "model": {
      "id": "model_abc123",
      "name": "iris_classifier",
      "description": "Iris species classification model",
      "model_type": "sklearn",
      "version": 1,
      "status": "active",
      "file_size": 15360,
      "prediction_endpoint": "/api/v1/predict/model_abc123",
      "created_at": "2025-10-21T10:30:00Z"
    }
  },
  "message": "Model uploaded successfully"
}
```

**Supported Model Types:**
- `sklearn` (`.pkl`, `.joblib`)
- Future: `tensorflow`, `pytorch`, `onnx`

---

### **6. List User Models**

**Endpoint:** `GET /models`  
**Authentication:** Required (JWT)  
**Rate Limit:** 100 requests/minute

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `status` (string: "active", "deprecated", "archived")
- `sort_by` (string: "created_at", "name", "version")
- `sort_order` (string: "asc", "desc")

**Example:** `GET /models?page=1&per_page=20&status=active&sort_by=created_at&sort_order=desc`

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "model_abc123",
      "name": "iris_classifier",
      "version": 2,
      "status": "active",
      "model_type": "sklearn",
      "file_size": 15360,
      "prediction_count": 1250,
      "created_at": "2025-10-21T10:30:00Z"
    },
    {
      "id": "model_def456",
      "name": "sentiment_analyzer",
      "version": 1,
      "status": "active",
      "model_type": "sklearn",
      "file_size": 28720,
      "prediction_count": 850,
      "created_at": "2025-10-20T15:20:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 1,
    "total_items": 2
  }
}
```

---

### **7. Get Model Details**

**Endpoint:** `GET /models/{model_id}`  
**Authentication:** Required (JWT)  
**Rate Limit:** 100 requests/minute

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "model_abc123",
    "name": "iris_classifier",
    "description": "Iris species classification model trained on sklearn iris dataset",
    "model_type": "sklearn",
    "version": 2,
    "status": "active",
    "file_size": 15360,
    "file_path": "models/user_123/iris_classifier/v2/model.pkl",
    "input_schema": {
      "type": "object",
      "properties": {
        "sepal_length": {"type": "number"},
        "sepal_width": {"type": "number"},
        "petal_length": {"type": "number"},
        "petal_width": {"type": "number"}
      }
    },
    "output_schema": {
      "type": "object",
      "properties": {
        "prediction": {"type": "integer"},
        "probabilities": {"type": "array"}
      }
    },
    "statistics": {
      "total_predictions": 1250,
      "avg_inference_time_ms": 45,
      "success_rate": 99.2
    },
    "created_at": "2025-10-21T10:30:00Z",
    "updated_at": "2025-10-21T10:30:00Z"
  }
}
```

---

### **8. Update Model**

**Endpoint:** `PATCH /models/{model_id}`  
**Authentication:** Required (JWT, owner only)  
**Rate Limit:** 50 requests/minute

**Request:**
```json
{
  "description": "Updated model description",
  "status": "deprecated"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "model_abc123",
    "description": "Updated model description",
    "status": "deprecated",
    "updated_at": "2025-10-21T11:00:00Z"
  },
  "message": "Model updated successfully"
}
```

**Updatable Fields:**
- `description`
- `status` ("active", "deprecated", "archived")

---

### **9. Delete Model**

**Endpoint:** `DELETE /models/{model_id}`  
**Authentication:** Required (JWT, owner only)  
**Rate Limit:** 20 requests/minute

**Response (204):**
```
No content (successful deletion)
```

**Behavior:** Soft delete (sets status to "archived")

---

### **10. Upload New Model Version**

**Endpoint:** `POST /models/{model_id}/versions`  
**Authentication:** Required (JWT, owner only)  
**Rate Limit:** 10 uploads/hour

**Request (multipart/form-data):**
```
file: <binary data>
description: "Improved model with 95% accuracy"
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "model_abc124",
    "name": "iris_classifier",
    "version": 3,
    "description": "Improved model with 95% accuracy",
    "status": "active",
    "previous_version": 2,
    "created_at": "2025-10-21T12:00:00Z"
  },
  "message": "New model version uploaded successfully"
}
```

---

## 🔮 Prediction Endpoints

### **11. Real-time Prediction**

**Endpoint:** `POST /predict/{model_id}`  
**Authentication:** Required (JWT or API Key)  
**Rate Limit:** 100 requests/minute  
**Timeout:** 30 seconds

**Request:**
```json
{
  "input": {
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  },
  "version": 2  // Optional: specify version, defaults to latest
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "prediction": {
      "class": 0,
      "class_name": "setosa",
      "probabilities": [0.98, 0.01, 0.01],
      "confidence": 0.98
    },
    "metadata": {
      "model_id": "model_abc123",
      "model_version": 2,
      "inference_time_ms": 45,
      "cached": false
    }
  },
  "timestamp": "2025-10-21T10:30:00Z"
}
```

**Caching:** Results cached in Redis for 1 hour (same input + model)

---

### **12. Batch Prediction**

**Endpoint:** `POST /predict/batch/{model_id}`  
**Authentication:** Required (JWT or API Key)  
**Rate Limit:** 10 requests/hour  
**Max Batch Size:** 1000 items

**Request:**
```json
{
  "inputs": [
    {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
    {"sepal_length": 6.2, "sepal_width": 2.9, "petal_length": 4.3, "petal_width": 1.3},
    {"sepal_length": 7.3, "sepal_width": 3.0, "petal_length": 6.3, "petal_width": 1.8}
  ],
  "version": 2
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_xyz789",
    "status": "pending",
    "total_items": 3,
    "estimated_completion": "2025-10-21T10:35:00Z",
    "status_endpoint": "/api/v1/jobs/job_xyz789"
  },
  "message": "Batch prediction job created"
}
```

---

### **13. Get Batch Job Status**

**Endpoint:** `GET /jobs/{job_id}`  
**Authentication:** Required (JWT or API Key)  
**Rate Limit:** 200 requests/minute

**Response (200) - Processing:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_xyz789",
    "status": "processing",
    "progress": {
      "completed": 500,
      "total": 1000,
      "percentage": 50
    },
    "created_at": "2025-10-21T10:30:00Z",
    "started_at": "2025-10-21T10:30:05Z"
  }
}
```

**Response (200) - Completed:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_xyz789",
    "status": "completed",
    "results": [
      {"input_index": 0, "prediction": {"class": 0, "confidence": 0.98}},
      {"input_index": 1, "prediction": {"class": 1, "confidence": 0.87}},
      {"input_index": 2, "prediction": {"class": 2, "confidence": 0.95}}
    ],
    "statistics": {
      "total_items": 3,
      "successful": 3,
      "failed": 0,
      "avg_inference_time_ms": 42
    },
    "created_at": "2025-10-21T10:30:00Z",
    "completed_at": "2025-10-21T10:35:00Z"
  }
}
```

---

### **14. Get Prediction History**

**Endpoint:** `GET /predictions`  
**Authentication:** Required (JWT)  
**Rate Limit:** 100 requests/minute

**Query Parameters:**
- `model_id` (string, optional)
- `page` (int, default: 1)
- `per_page` (int, default: 20)
- `start_date` (ISO 8601)
- `end_date` (ISO 8601)

**Example:** `GET /predictions?model_id=model_abc123&page=1&per_page=20`

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "pred_123",
      "model_id": "model_abc123",
      "model_name": "iris_classifier",
      "input": {"sepal_length": 5.1, "sepal_width": 3.5, ...},
      "output": {"class": 0, "confidence": 0.98},
      "inference_time_ms": 45,
      "status": "success",
      "created_at": "2025-10-21T10:30:00Z"
    }
  ],
  "pagination": {...}
}
```

---

## 📊 Analytics Endpoints

### **15. Get User Statistics**

**Endpoint:** `GET /analytics/overview`  
**Authentication:** Required (JWT)  
**Rate Limit:** 50 requests/minute

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_models": 5,
    "active_models": 3,
    "total_predictions": 15420,
    "predictions_today": 245,
    "predictions_this_month": 8350,
    "avg_inference_time_ms": 52,
    "most_used_model": {
      "id": "model_abc123",
      "name": "iris_classifier",
      "prediction_count": 8500
    },
    "api_usage": {
      "requests_today": 312,
      "rate_limit": 10000,
      "remaining": 9688
    }
  }
}
```

---

### **16. Get Model Analytics**

**Endpoint:** `GET /analytics/models/{model_id}`  
**Authentication:** Required (JWT, owner only)  
**Rate Limit:** 50 requests/minute

**Query Parameters:**
- `period` (string: "day", "week", "month", default: "week")

**Response (200):**
```json
{
  "success": true,
  "data": {
    "model_id": "model_abc123",
    "model_name": "iris_classifier",
    "period": "week",
    "statistics": {
      "total_predictions": 1250,
      "successful_predictions": 1240,
      "failed_predictions": 10,
      "success_rate": 99.2,
      "avg_inference_time_ms": 45,
      "p95_inference_time_ms": 78,
      "p99_inference_time_ms": 120
    },
    "daily_breakdown": [
      {"date": "2025-10-15", "predictions": 180, "avg_time_ms": 43},
      {"date": "2025-10-16", "predictions": 195, "avg_time_ms": 46},
      ...
    ],
    "prediction_distribution": {
      "class_0": 450,
      "class_1": 420,
      "class_2": 380
    }
  }
}
```

---

## 🔑 API Key Management

### **17. Create API Key**

**Endpoint:** `POST /api-keys`  
**Authentication:** Required (JWT)  
**Rate Limit:** 10 requests/hour

**Request:**
```json
{
  "name": "Production API Key",
  "expires_in_days": 365  // Optional, default: never expires
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "api_key": "mlp_live_abc123xyz789...",  // ⚠️ Only shown once!
    "key_id": "key_123",
    "name": "Production API Key",
    "expires_at": "2026-10-21T10:30:00Z",
    "created_at": "2025-10-21T10:30:00Z"
  },
  "message": "API key created successfully. Store it securely - it won't be shown again."
}
```

---

### **18. List API Keys**

**Endpoint:** `GET /api-keys`  
**Authentication:** Required (JWT)  
**Rate Limit:** 100 requests/minute

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "key_123",
      "name": "Production API Key",
      "key_preview": "mlp_live_abc123...",  // Only first 15 chars
      "is_active": true,
      "last_used_at": "2025-10-21T09:15:00Z",
      "expires_at": "2026-10-21T10:30:00Z",
      "created_at": "2025-10-21T10:30:00Z"
    }
  ]
}
```

---

### **19. Revoke API Key**

**Endpoint:** `DELETE /api-keys/{key_id}`  
**Authentication:** Required (JWT)  
**Rate Limit:** 50 requests/minute

**Response (204):**
```
No content (successful revocation)
```

---

## 🏥 System Endpoints

### **20. Health Check**

**Endpoint:** `GET /health`  
**Authentication:** None  
**Rate Limit:** None

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "storage": "healthy"
  },
  "uptime_seconds": 345600
}
```

---

### **21. API Documentation**

**Endpoint:** `GET /docs`  
**Authentication:** None  
**Description:** Interactive Swagger UI documentation

**Endpoint:** `GET /redoc`  
**Authentication:** None  
**Description:** ReDoc alternative documentation

---

## 🔒 Authentication Methods

### **Method 1: JWT Bearer Token**

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### **Method 2: API Key**

```http
X-API-Key: mlp_live_abc123xyz789...
```

---

## ⚠️ Rate Limiting

**Headers in Response:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1697884800
```

**Rate Limit Exceeded (429):**
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 45 seconds.",
    "details": {
      "limit": 100,
      "window": "1 minute",
      "retry_after": 45
    }
  }
}
```

---

## 🎓 Interview Talking Points

### **API Design Principles:**
- **RESTful:** Resource-based URLs, standard HTTP methods
- **Versioning:** `/api/v1` for backward compatibility
- **Consistency:** Standardized response format across all endpoints
- **Error Handling:** Meaningful error codes and messages

### **Performance:**
- **Caching:** Redis for prediction results (1-hour TTL)
- **Pagination:** Limit result sets to prevent overload
- **Async:** Batch predictions run in background
- **Rate Limiting:** Prevent abuse, ensure fair usage

### **Security:**
- **Authentication:** JWT + API keys for flexibility
- **Authorization:** Resource ownership checks
- **Input Validation:** Pydantic models catch bad data early
- **Rate Limiting:** Per-user limits

---

**Last Updated:** October 21, 2025  
**Status:** ✅ API Design Complete  
**Next:** Technology Decision Documentation
