"""
Integration tests for complete workflows
Tests end-to-end user journeys
"""
import pytest
from fastapi.testclient import TestClient


class TestCompleteUserJourney:
    """Test complete user workflow from registration to prediction"""
    
    def test_full_workflow(self, client: TestClient, temp_model_file: str):
        """
        Test complete workflow:
        1. Register user
        2. Login
        3. Upload model
        4. Create API key
        5. Make prediction (if possible)
        6. Check analytics
        """
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
        
        # 2. Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "journey@example.com",
                "password": "password123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Verify user info
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["data"]["email"] == "journey@example.com"
        
        # 4. Upload model
        with open(temp_model_file, 'rb') as f:
            upload_response = client.post(
                "/api/v1/models/upload",
                headers=headers,
                data={
                    "name": "journey_model",
                    "description": "Test journey model",
                    "model_type": "sklearn"
                },
                files={"file": ("model.pkl", f, "application/octet-stream")}
            )
        assert upload_response.status_code == 201
        model_id = upload_response.json()["data"]["model"]["id"]
        
        # 5. Create API key
        api_key_response = client.post(
            "/api/v1/api-keys",
            headers=headers,
            json={"name": "Journey API Key", "expires_days": 30}
        )
        assert api_key_response.status_code == 201
        api_key = api_key_response.json()["data"]["api_key"]
        
        # 5. Use API key to access models
        models_response = client.get(
            "/api/v1/models",
            headers={"X-API-Key": api_key}
        )
        assert models_response.status_code == 200
        assert len(models_response.json()["data"]) == 1
        
        # 6. Check analytics
        analytics_response = client.get(
            f"/api/v1/models/{model_id}/analytics",
            headers=headers
        )
        assert analytics_response.status_code == 200
        assert "statistics" in analytics_response.json()["data"]


class TestMultiUserInteractions:
    """Test interactions between multiple users"""
    
    def test_user_isolation(self, client: TestClient, temp_model_file: str):
        """Test that users can only see their own models"""
        # User 1 - Register and Login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "user1@example.com",
                "password": "password123",
                "full_name": "User One"
            }
        )
        user1_login = client.post(
            "/api/v1/auth/login",
            json={"email": "user1@example.com", "password": "password123"}
        )
        user1_token = user1_login.json()["data"]["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        
        # User 2 - Register and Login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "user2@example.com",
                "password": "password123",
                "full_name": "User Two"
            }
        )
        user2_login = client.post(
            "/api/v1/auth/login",
            json={"email": "user2@example.com", "password": "password123"}
        )
        user2_token = user2_login.json()["data"]["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        # User 1 uploads model
        with open(temp_model_file, 'rb') as f:
            user1_upload = client.post(
                "/api/v1/models/upload",
                headers=user1_headers,
                data={"name": "user1_model", "model_type": "sklearn"},
                files={"file": ("model.pkl", f, "application/octet-stream")}
            )
        user1_model_id = user1_upload.json()["data"]["model"]["id"]
        
        # User 2 uploads model
        with open(temp_model_file, 'rb') as f:
            user2_upload = client.post(
                "/api/v1/models/upload",
                headers=user2_headers,
                data={"name": "user2_model", "model_type": "sklearn"},
                files={"file": ("model.pkl", f, "application/octet-stream")}
            )
        
        # User 1 should only see their model
        user1_models = client.get("/api/v1/models", headers=user1_headers)
        assert len(user1_models.json()["data"]) == 1
        assert user1_models.json()["data"][0]["name"] == "user1_model"
        
        # User 2 should only see their model
        user2_models = client.get("/api/v1/models", headers=user2_headers)
        assert len(user2_models.json()["data"]) == 1
        assert user2_models.json()["data"][0]["name"] == "user2_model"
        
        # User 2 should not be able to access User 1's model
        user2_access = client.get(
            f"/api/v1/models/{user1_model_id}",
            headers=user2_headers
        )
        assert user2_access.status_code == 403


class TestHealthAndMonitoring:
    """Test health check and monitoring endpoints"""
    
    def test_health_check(self, client: TestClient):
        """Test main health check endpoint"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert data["components"]["api"]["status"] == "healthy"
        assert data["components"]["database"]["status"] == "healthy"
    
    def test_readiness_probe(self, client: TestClient):
        """Test Kubernetes readiness probe"""
        response = client.get("/api/v1/health/ready")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
    
    def test_liveness_probe(self, client: TestClient):
        """Test Kubernetes liveness probe"""
        response = client.get("/api/v1/health/live")
        
        assert response.status_code == 200
        assert response.json()["status"] == "alive"


class TestErrorHandling:
    """Test error handling across the application"""
    
    def test_404_not_found(self, client: TestClient):
        """Test 404 error handling"""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    def test_validation_error(self, client: TestClient):
        """Test validation error handling"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",  # Invalid email format
                "password": "pass"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_unauthorized_access(self, client: TestClient):
        """Test unauthorized access handling"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
