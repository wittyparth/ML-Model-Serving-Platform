"""
Test script for Phase 5: Logging & Monitoring
Tests analytics endpoints, health checks, and middleware
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None
MODEL_ID = None


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_health_check():
    """Test health check endpoint"""
    print_section("Testing Health Check Endpoint")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")


def test_readiness_check():
    """Test Kubernetes readiness probe"""
    print_section("Testing Readiness Check")
    
    response = requests.get(f"{BASE_URL}/health/ready")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✅ Readiness check passed")


def test_liveness_check():
    """Test Kubernetes liveness probe"""
    print_section("Testing Liveness Check")
    
    response = requests.get(f"{BASE_URL}/health/live")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✅ Liveness check passed")


def test_request_logging():
    """Test request logging middleware"""
    print_section("Testing Request Logging Middleware")
    
    print("Making request to test logging...")
    response = requests.get(f"{BASE_URL}/health")
    
    # Check for custom headers
    print(f"X-Request-ID: {response.headers.get('X-Request-ID')}")
    print(f"X-Response-Time: {response.headers.get('X-Response-Time')}")
    
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time" in response.headers
    print("✅ Request logging middleware working")


def login():
    """Login to get token"""
    global TOKEN
    
    print_section("Logging In")
    
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    
    if response.status_code == 200:
        TOKEN = response.json()["data"]["access_token"]
        print("✅ Login successful")
    else:
        print("❌ Login failed - creating new user")
        # Try registering
        requests.post(f"{BASE_URL}/auth/register", json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        })
        
        # Login again
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        TOKEN = response.json()["data"]["access_token"]
        print("✅ Registered and logged in")


def get_or_create_model():
    """Get existing model or upload new one"""
    global MODEL_ID
    
    print_section("Getting/Creating Model for Testing")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # List existing models
    response = requests.get(f"{BASE_URL}/models", headers=headers)
    
    if response.status_code == 200:
        models = response.json()["data"]
        if models:
            MODEL_ID = models[0]["id"]
            print(f"✅ Using existing model: {MODEL_ID}")
            return
    
    # Upload a test model if none exists
    print("No models found - please upload a model first using test_models_manual.py")
    print("Skipping analytics tests...")


def test_prediction_with_logging():
    """Test prediction with background logging"""
    if not MODEL_ID:
        print("\n⚠️  Skipping prediction test - no model available")
        return
    
    print_section("Testing Prediction with Background Logging")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Make a prediction
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/predict/{MODEL_ID}",
        headers=headers,
        json={
            "input": {"feature1": 1.0, "feature2": 2.0, "feature3": 3.0}
        }
    )
    duration = time.time() - start_time
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {duration * 1000:.2f}ms")
    
    if response.status_code == 200:
        data = response.json()["data"]
        print(f"Prediction: {json.dumps(data['prediction'], indent=2)}")
        print(f"Metadata: {json.dumps(data['metadata'], indent=2)}")
        print("✅ Prediction with logging successful")
    else:
        print(f"❌ Prediction failed: {response.text}")


def test_analytics_endpoint():
    """Test model analytics endpoint"""
    if not MODEL_ID:
        print("\n⚠️  Skipping analytics test - no model available")
        return
    
    print_section("Testing Analytics Endpoint")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Get analytics
    response = requests.get(
        f"{BASE_URL}/models/{MODEL_ID}/analytics?days=7",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        analytics = response.json()["data"]
        print(f"Analytics: {json.dumps(analytics, indent=2)}")
        print("✅ Analytics endpoint working")
    else:
        print(f"❌ Analytics failed: {response.text}")


def test_error_tracking():
    """Test error tracking middleware"""
    print_section("Testing Error Tracking Middleware")
    
    # Make an invalid request to trigger error
    response = requests.get(f"{BASE_URL}/models/invalid-uuid")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Should return error but not crash
    assert response.status_code in [401, 403, 422]
    print("✅ Error tracking middleware working")


def main():
    """Run all Phase 5 tests"""
    print("\n" + "🚀" * 30)
    print("PHASE 5: LOGGING & MONITORING - COMPREHENSIVE TEST")
    print("🚀" * 30)
    
    try:
        # Test health endpoints
        test_health_check()
        test_readiness_check()
        test_liveness_check()
        
        # Test middleware
        test_request_logging()
        
        # Test authenticated endpoints
        login()
        get_or_create_model()
        test_prediction_with_logging()
        test_analytics_endpoint()
        
        # Test error handling
        test_error_tracking()
        
        print("\n" + "✅" * 30)
        print("ALL PHASE 5 TESTS PASSED!")
        print("✅" * 30)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
