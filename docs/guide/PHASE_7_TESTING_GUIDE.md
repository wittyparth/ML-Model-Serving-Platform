# 🧪 Phase 7: Testing & CI/CD - Learning Guide

**What You'll Learn:**
- pytest testing framework
- Writing unit tests
- Integration testing
- Test fixtures and mocking
- Code coverage
- GitHub Actions CI/CD
- Continuous testing

---

## 🎯 What We Built in Phase 7

### Test Suite Overview
```
tests/
├── conftest.py              # Shared fixtures
├── test_auth.py             # Authentication tests (4 tests)
├── test_models.py           # Model management (26 tests)
├── test_api_keys.py         # API key tests (20 tests)
├── test_integration.py      # End-to-end tests (9 tests)
└── README.md                # Testing documentation
```

### Achievements
- ✅ 39 passing tests
- ✅ 77% code coverage
- ✅ 11.24 second execution time
- ✅ Automated CI/CD pipeline
- ✅ Test database isolation

---

## 🐍 pytest Fundamentals

### What is pytest?
pytest is Python's most popular testing framework. It's simple yet powerful.

**Why pytest over unittest?**
- ✅ Less boilerplate code
- ✅ Better assertion messages
- ✅ Powerful fixtures
- ✅ Plugins ecosystem
- ✅ Parametrized tests

### Installation
```bash
pip install pytest pytest-cov pytest-asyncio httpx
```

### Your First Test

**`test_example.py`:**
```python
def add(a, b):
    return a + b

def test_add():
    """Test addition function"""
    result = add(2, 3)
    assert result == 5  # Simple assertion

def test_add_negative():
    """Test with negative numbers"""
    result = add(-1, 1)
    assert result == 0
```

**Run tests:**
```bash
pytest test_example.py -v
```

**Output:**
```
test_example.py::test_add PASSED
test_example.py::test_add_negative PASSED
```

### pytest Conventions

1. **Test files**: Must start with `test_` or end with `_test.py`
2. **Test functions**: Must start with `test_`
3. **Test classes**: Must start with `Test`
4. **Assertions**: Use `assert` statement

**Common Mistakes:**
❌ Not following naming conventions → pytest doesn't find tests
❌ Using `assertEqual` instead of `assert` → Less clear errors
❌ Not using descriptive test names → Hard to debug failures
❌ Testing multiple things in one test → Hard to pinpoint issues

---

## 🔧 Test Fixtures

### What are Fixtures?
Fixtures are **reusable test setup and teardown** functions. Think of them as "test prerequisites."

### Basic Fixture Example

```python
import pytest

@pytest.fixture
def sample_user():
    """Fixture that returns a sample user dict"""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30
    }

def test_user_name(sample_user):
    """Test uses the fixture"""
    assert sample_user["name"] == "John Doe"

def test_user_email(sample_user):
    """Each test gets a fresh copy"""
    assert sample_user["email"] == "john@example.com"
```

### Fixture Scopes

```python
@pytest.fixture(scope="function")  # Default: New for each test
def func_fixture():
    return "function scope"

@pytest.fixture(scope="module")    # One per module (file)
def module_fixture():
    return "module scope"

@pytest.fixture(scope="session")   # One per test session
def session_fixture():
    return "session scope"
```

**When to use each:**
- **function**: Database sessions, user objects (default)
- **module**: Database connections, API clients
- **session**: Expensive setup (loading ML models)

### Setup and Teardown

```python
@pytest.fixture
def database():
    """Setup database before test, cleanup after"""
    # Setup
    db = create_database()
    db.create_tables()
    
    yield db  # Test runs here
    
    # Teardown (runs even if test fails)
    db.drop_tables()
    db.close()

def test_insert_user(database):
    database.insert({"name": "Alice"})
    users = database.get_all_users()
    assert len(users) == 1
```

**Common Mistakes:**
❌ Not using `yield` → Teardown doesn't run
❌ Wrong scope → Tests interfere with each other
❌ Heavy fixtures with function scope → Tests are slow
❌ Not cleaning up → Database fills with test data

---

## 🗄️ Database Testing with FastAPI

### Test Database Setup

**`tests/conftest.py`:**
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.core.security import get_password_hash

# Use same database as dev (cleaned after each test)
SQLALCHEMY_DATABASE_URL = "postgresql://mluser:mlpassword@db:5432/mlplatform"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables before tests, drop after"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db():
    """Create database session for each test"""
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        # Clean up data after each test
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()
```

**Why This Works:**
1. **Session scope setup**: Creates tables once
2. **Function scope db**: New session per test
3. **Cleanup after each test**: Tables are emptied
4. **Handles exceptions**: Rollback on errors

### Test Client Fixture

```python
@pytest.fixture(scope="function")
def client(db):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

**What This Does:**
- Replaces `get_db()` dependency with our test database
- Ensures tests use the same database session
- Cleans up overrides after test

---

## ✍️ Writing Unit Tests

### Test Structure: Arrange-Act-Assert (AAA)

```python
def test_user_registration(client, db):
    # ARRANGE: Set up test data
    user_data = {
        "email": "test@example.com",
        "password": "Password123!",
        "full_name": "Test User"
    }
    
    # ACT: Perform the action
    response = client.post("/api/v1/auth/register", json=user_data)
    
    # ASSERT: Check the results
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "test@example.com"
    
    # Verify in database
    user = db.query(User).filter(User.email == "test@example.com").first()
    assert user is not None
    assert user.full_name == "Test User"
```

### Testing Different Scenarios

**Happy Path:**
```python
def test_successful_login(client, test_user):
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
```

**Error Cases:**
```python
def test_login_invalid_password(client, test_user):
    """Test login with wrong password"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()

def test_login_nonexistent_user(client):
    """Test login with email that doesn't exist"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "password123"}
    )
    
    assert response.status_code == 401
```

**Edge Cases:**
```python
def test_register_invalid_email(client):
    """Test registration with invalid email"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "Password123!",
            "full_name": "Test User"
        }
    )
    
    assert response.status_code == 422  # Validation error

def test_register_duplicate_email(client, test_user):
    """Test registering with existing email"""
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

**Common Mistakes:**
❌ Only testing happy path → Bugs in error handling
❌ Not testing edge cases → Fails with unusual input
❌ Testing too much in one test → Hard to debug
❌ Not checking database state → API lies but DB is wrong
❌ Hardcoding test data → Tests break when data changes

---

## 🧩 Test Fixtures for FastAPI

### User Fixtures

```python
@pytest.fixture
def test_user(db):
    """Create a regular test user"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        is_active=True,
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def admin_user(db):
    """Create an admin test user"""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Admin User",
        is_active=True,
        is_admin=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

### Authentication Headers Fixture

```python
@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client, admin_user):
    """Get authentication headers for admin user"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### Using Auth Fixtures

```python
def test_get_current_user(client, auth_headers):
    """Test getting current user info"""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == "test@example.com"

def test_protected_route_no_auth(client):
    """Test accessing protected route without auth"""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 401
```

### Temporary File Fixture

```python
import tempfile
import os
import joblib
from sklearn.linear_model import LogisticRegression

@pytest.fixture
def temp_model_file():
    """Create a temporary ML model file"""
    # Create a simple model
    model = LogisticRegression()
    
    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(
        mode='wb',
        suffix='.pkl',
        delete=False
    )
    joblib.dump(model, temp_file.name)
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)
```

**Using the Fixture:**
```python
def test_upload_model(client, auth_headers, temp_model_file):
    """Test model upload"""
    with open(temp_model_file, 'rb') as f:
        response = client.post(
            "/api/v1/models/upload",
            headers=auth_headers,
            data={
                "name": "test_model",
                "model_type": "sklearn"
            },
            files={"file": ("model.pkl", f, "application/octet-stream")}
        )
    
    assert response.status_code == 201
```

---

## 🔄 Integration Testing

### What is Integration Testing?
Testing how multiple parts of your system work together.

**Unit Test:**
```python
def test_create_user(db):
    """Test creating a user (database only)"""
    user = User(email="test@example.com", ...)
    db.add(user)
    db.commit()
    assert user.id is not None
```

**Integration Test:**
```python
def test_full_user_workflow(client, temp_model_file):
    """Test complete user journey"""
    # 1. Register
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "journey@example.com",
            "password": "password123",
            "full_name": "Journey User"
        }
    )
    assert register_response.status_code == 201
    
    # 2. Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "journey@example.com", "password": "password123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Upload model
    with open(temp_model_file, 'rb') as f:
        upload_response = client.post(
            "/api/v1/models/upload",
            headers=headers,
            data={"name": "my_model", "model_type": "sklearn"},
            files={"file": ("model.pkl", f, "application/octet-stream")}
        )
    assert upload_response.status_code == 201
    model_id = upload_response.json()["data"]["model"]["id"]
    
    # 4. Get model
    get_response = client.get(f"/api/v1/models/{model_id}", headers=headers)
    assert get_response.status_code == 200
    
    # 5. List models
    list_response = client.get("/api/v1/models", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1
```

### Testing Multi-User Isolation

```python
def test_user_cannot_see_other_users_models(client, temp_model_file):
    """Test that users can only see their own models"""
    # User 1: Register and upload
    client.post("/api/v1/auth/register", json={
        "email": "user1@example.com",
        "password": "password123",
        "full_name": "User One"
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
    
    # User 2: Register
    client.post("/api/v1/auth/register", json={
        "email": "user2@example.com",
        "password": "password123",
        "full_name": "User Two"
    })
    login2 = client.post("/api/v1/auth/login", json={
        "email": "user2@example.com",
        "password": "password123"
    })
    headers2 = {"Authorization": f"Bearer {login2.json()['data']['access_token']}"}
    
    # User 2 tries to access User 1's model
    response = client.get(f"/api/v1/models/{model1_id}", headers=headers2)
    assert response.status_code == 404  # Not found (or 403 Forbidden)
    
    # User 2 lists models (should be empty)
    list_response = client.get("/api/v1/models", headers=headers2)
    assert len(list_response.json()["data"]) == 0
```

---

## 📊 Code Coverage

### What is Code Coverage?
Percentage of your code that is executed during tests.

**Install:**
```bash
pip install pytest-cov
```

**Run with coverage:**
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

**Output:**
```
Name                        Stmts   Miss  Cover
-----------------------------------------------
app/__init__.py                 1      0   100%
app/api/v1/auth.py             41      7    83%
app/api/v1/models.py          105      9    91%
app/core/security.py           35      5    86%
-----------------------------------------------
TOTAL                         965    226    77%

Coverage HTML written to dir htmlcov
```

**View HTML Report:**
```bash
open htmlcov/index.html  # Mac
start htmlcov/index.html # Windows
```

### Understanding Coverage

**77% Coverage Means:**
- 77% of code lines are executed during tests
- 23% of code is never run by tests

**What's a Good Coverage Number?**
- ✅ 80%+ Excellent
- ✅ 70-80%: Good
- ⚠️ 60-70%: Acceptable
- ❌ <60%: Needs improvement

**But Remember:**
- **100% coverage ≠ Bug-free code**
- **Quality > Quantity**: Test logic, not lines
- Focus on critical paths first

**Common Mistakes:**
❌ Chasing 100% coverage → Waste of time
❌ Testing trivial code → Low value
❌ Not testing error handling → Bugs in production
❌ Gaming the system → Coverage without assertions

---

## 🚀 Continuous Integration with GitHub Actions

### What is CI/CD?
**CI (Continuous Integration)**: Automatically test code on every commit
**CD (Continuous Deployment)**: Automatically deploy passing code

**Benefits:**
- ✅ Catch bugs early
- ✅ Ensure code quality
- ✅ Team collaboration
- ✅ Confidence in changes

### GitHub Actions Workflow

**`.github/workflows/ci.yml`:**
```yaml
name: CI/CD Pipeline

# Run on push and pull request
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: mluser
          POSTGRES_PASSWORD: mlpassword
          POSTGRES_DB: mlplatform
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql://mluser:mlpassword@localhost:5432/mlplatform
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key
        run: |
          pytest tests/ -v --cov=app --cov-report=xml --cov-report=term
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  lint:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install linting tools
        run: |
          pip install flake8 black mypy
      
      - name: Run flake8
        run: flake8 app/ --max-line-length=100
      
      - name: Run black
        run: black --check app/
      
      - name: Run mypy
        run: mypy app/

  security:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install safety
        run: pip install safety
      
      - name: Run security check
        run: safety check
```

### Understanding the Workflow

**1. Triggers:**
```yaml
on:
  push:
    branches: [ main, develop ]  # Run on push to these branches
  pull_request:
    branches: [ main ]            # Run on PR to main
```

**2. Services:**
```yaml
services:
  postgres:  # Spin up PostgreSQL
  redis:     # Spin up Redis
```

**3. Steps:**
1. **Checkout code**: Get your code from GitHub
2. **Setup Python**: Install Python 3.11
3. **Cache dependencies**: Speed up builds
4. **Install dependencies**: `pip install -r requirements.txt`
5. **Run tests**: Execute pytest with coverage
6. **Upload coverage**: Send to Codecov

**4. Environment Variables:**
```yaml
env:
  DATABASE_URL: postgresql://...
  REDIS_URL: redis://...
  SECRET_KEY: test-secret-key
```

### Viewing CI Results

**In GitHub:**
1. Go to your repository
2. Click "Actions" tab
3. See all workflow runs
4. Click on a run to see details
5. View logs for each step

**Badge in README:**
```markdown
![CI](https://github.com/yourusername/yourrepo/workflows/CI%2FCD%20Pipeline/badge.svg)
```

---

## 🎯 Testing Best Practices

### 1. Test Organization

**Good:**
```python
class TestUserRegistration:
    """Group related tests in a class"""
    
    def test_successful_registration(self, client):
        """Test happy path"""
        ...
    
    def test_duplicate_email(self, client, test_user):
        """Test error case"""
        ...
    
    def test_invalid_email(self, client):
        """Test validation"""
        ...
```

**Bad:**
```python
def test_everything():
    """Test that does too much"""
    ...
```

### 2. Test Naming

**Good:**
```python
def test_user_can_login_with_valid_credentials(client, test_user):
    """Clear what is being tested"""
    ...

def test_login_fails_with_invalid_password(client, test_user):
    """Clear what is expected"""
    ...
```

**Bad:**
```python
def test_login(client):  # Too vague
    ...

def test_1(client):      # What does this test?
    ...
```

### 3. Use Assertions Wisely

**Good:**
```python
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert "email" in data, "Response missing email field"
assert user.is_active is True, "User should be active"
```

**Bad:**
```python
assert True  # Useless test
assert response  # What are you checking?
```

### 4. Don't Test Framework Code

**Don't Test:**
```python
def test_pydantic_validation():
    """Testing Pydantic, not your code"""
    model = UserCreate(email="test@example.com", password="pass")
    assert model.email == "test@example.com"
```

**Do Test:**
```python
def test_invalid_email_rejected(client):
    """Test YOUR endpoint's validation"""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "invalid", "password": "pass"}
    )
    assert response.status_code == 422
```

### 5. Keep Tests Independent

**Good:**
```python
def test_create_user(client):
    # Creates its own user
    response = client.post("/users", json={...})
    assert response.status_code == 201

def test_delete_user(client):
    # Creates its own user
    response = client.post("/users", json={...})
    user_id = response.json()["id"]
    
    # Then deletes it
    delete_response = client.delete(f"/users/{user_id}")
    assert delete_response.status_code == 204
```

**Bad:**
```python
created_user_id = None

def test_create_user(client):
    global created_user_id
    response = client.post("/users", json={...})
    created_user_id = response.json()["id"]

def test_delete_user(client):
    # Depends on test_create_user running first!
    response = client.delete(f"/users/{created_user_id}")
```

---

## 📚 Key Takeaways

### Concepts Learned
1. **pytest**: Modern Python testing framework
2. **Fixtures**: Reusable test setup/teardown
3. **Unit Tests**: Testing individual functions
4. **Integration Tests**: Testing system interactions
5. **Code Coverage**: Measuring test completeness
6. **CI/CD**: Automated testing pipelines

### Testing Principles
✅ Test behavior, not implementation
✅ One assertion per test (when possible)
✅ Tests should be independent
✅ Use descriptive test names
✅ Test happy path and error cases
✅ Keep tests fast
✅ Don't test framework code

### Common Mistakes to Avoid
❌ Testing everything → Waste of time
❌ Not testing error cases → Bugs in production
❌ Tests depend on each other → Brittle test suite
❌ Slow tests → Developers skip them
❌ No CI/CD → Manual testing required
❌ Chasing 100% coverage → Wrong goal

---

## 🔗 Related Documentation

- See `tests/README.md` for running tests
- See `TEST_SUMMARY.md` for test results
- See `.github/workflows/ci.yml` for CI/CD config

**Next:** [Phase 8: Production Prep →](PHASE_8_PRODUCTION_GUIDE.md)
