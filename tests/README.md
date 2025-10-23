# Testing Guide

## Overview

The ML Model Serving Platform has comprehensive test coverage across all endpoints and functionality.

## Test Structure

```
tests/
├── conftest.py           # Test fixtures and configuration
├── test_auth.py          # Authentication tests (existing)
├── test_models.py        # Model management tests (50+ tests)
├── test_api_keys.py      # API key management tests (20+ tests)
└── test_integration.py   # End-to-end integration tests
```

## Running Tests

### Local Testing

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_models.py -v

# Run specific test class
pytest tests/test_models.py::TestModelUpload -v

# Run specific test
pytest tests/test_models.py::TestModelUpload::test_upload_model_success -v
```

### Docker Testing

```bash
# Run tests in Docker
docker-compose exec api pytest tests/ -v

# With coverage
docker-compose exec api pytest tests/ --cov=app --cov-report=term
```

## Test Fixtures

### Database Fixtures

- `db`: Fresh test database for each test
- `client`: FastAPI TestClient with database override
- `test_user`: Regular user account
- `admin_user`: Admin user account

### Authentication Fixtures

- `auth_headers`: Bearer token headers for test_user
- `admin_headers`: Bearer token headers for admin_user

### Model Fixtures

- `temp_model_file`: Temporary sklearn model file
- `test_model`: Model record in database

## Test Coverage

### Authentication Tests (`test_auth.py`)
- ✅ User registration (success, duplicate, invalid)
- ✅ User login (success, wrong password, non-existent)
- ✅ Protected endpoints (with/without auth)
- ✅ Token refresh (valid/invalid)

### Model Management Tests (`test_models.py`)
- ✅ Model upload (success, versioning, no auth)
- ✅ Model listing (empty, with data, pagination)
- ✅ Model details (success, not found, unauthorized)
- ✅ Model updates (description, status)
- ✅ Model deletion (soft delete)
- ✅ Model analytics (statistics, custom period)

### API Key Tests (`test_api_keys.py`)
- ✅ API key creation (with/without expiration)
- ✅ API key listing (empty, with data)
- ✅ API key authentication (valid, invalid, inactive)
- ✅ API key updates (name, status)
- ✅ API key revocation (success, non-existent)

### Integration Tests (`test_integration.py`)
- ✅ Complete user journey (register → upload → predict → analytics)
- ✅ Multi-user isolation (users can't see each other's models)
- ✅ Health checks (main, readiness, liveness)
- ✅ Error handling (404, validation, unauthorized)

## Coverage Goals

- **Target:** 80%+ code coverage
- **Current:** Run `pytest --cov=app` to check
- **Focus Areas:**
  - All API endpoints
  - Authentication and authorization
  - Business logic
  - Error handling

## CI/CD Integration

Tests run automatically on:
- Every push to main/develop branches
- Every pull request
- GitHub Actions workflow: `.github/workflows/ci.yml`

The CI pipeline includes:
1. **Test Job**: Runs all tests with PostgreSQL and Redis services
2. **Lint Job**: Code quality checks (flake8, black, mypy)
3. **Security Job**: Dependency vulnerability scanning

## Writing New Tests

### Example Test

```python
def test_new_feature(client: TestClient, auth_headers: dict):
    """Test description"""
    response = client.post(
        "/api/v1/endpoint",
        headers=auth_headers,
        json={"data": "value"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

### Best Practices

1. **Use descriptive test names**: `test_upload_model_with_invalid_file`
2. **Test one thing per test**: Keep tests focused
3. **Use fixtures**: Leverage existing fixtures for setup
4. **Test error cases**: Don't just test happy paths
5. **Clean up**: Fixtures handle cleanup automatically
6. **Mock external services**: Don't make real API calls

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure dependencies are installed
pip install -r requirements.txt
```

**Database Errors**
```bash
# Tests use SQLite by default (no PostgreSQL needed locally)
# Check conftest.py for database configuration
```

**Fixture Not Found**
```bash
# Make sure conftest.py is in the tests/ directory
# Check that fixture names match
```

## Test Metrics

- Total Tests: 50+
- Test Files: 4
- Coverage: Target 80%+
- Execution Time: < 30 seconds

## Next Steps

- [ ] Add prediction endpoint tests
- [ ] Add webhook tests (when implemented)
- [ ] Add performance tests
- [ ] Add load tests
