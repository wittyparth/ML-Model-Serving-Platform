"""
Comprehensive tests for API key management
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.api_key import APIKey
from app.models.user import User


class TestAPIKeyCreation:
    """Test API key creation"""
    
    def test_create_api_key(self, client: TestClient, auth_headers: dict):
        """Test successful API key creation"""
        response = client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={
                "name": "Test API Key",
                "expires_days": 30
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "api_key" in data["data"]
        assert data["data"]["api_key"].startswith("mlp_")
        assert data["data"]["name"] == "Test API Key"
    
    def test_create_api_key_no_expiration(self, client: TestClient, auth_headers: dict):
        """Test creating API key without expiration"""
        response = client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={"name": "Permanent Key"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["expires_at"] is None
    
    def test_create_api_key_no_auth(self, client: TestClient):
        """Test creating API key without authentication"""
        response = client.post(
            "/api/v1/api-keys",
            json={"name": "Test Key"}
        )
        
        assert response.status_code == 401


class TestAPIKeyListing:
    """Test API key listing"""
    
    def test_list_api_keys_empty(self, client: TestClient, auth_headers: dict):
        """Test listing when no keys exist"""
        response = client.get("/api/v1/api-keys", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0
    
    def test_list_api_keys_with_data(self, client: TestClient, auth_headers: dict):
        """Test listing with existing keys"""
        # Create a key first
        client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={"name": "Test Key"}
        )
        
        response = client.get("/api/v1/api-keys", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Test Key"
        assert "prefix" in data["data"][0]


class TestAPIKeyAuthentication:
    """Test authentication using API keys"""
    
    def test_auth_with_api_key(self, client: TestClient, auth_headers: dict):
        """Test authenticating with API key"""
        # Create API key
        create_response = client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={"name": "Auth Test Key"}
        )
        api_key = create_response.json()["data"]["api_key"]
        
        # Use API key to authenticate
        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["email"] == "test@example.com"
    
    def test_auth_with_invalid_api_key(self, client: TestClient):
        """Test authenticating with invalid API key"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "mlp_invalid_key"}
        )
        
        assert response.status_code == 401
    
    def test_auth_with_inactive_api_key(self, client: TestClient, auth_headers: dict):
        """Test authenticating with deactivated API key"""
        # Create API key
        create_response = client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={"name": "Inactive Key"}
        )
        key_id = create_response.json()["data"]["id"]
        api_key = create_response.json()["data"]["api_key"]
        
        # Deactivate it
        client.patch(
            f"/api/v1/api-keys/{key_id}",
            headers=auth_headers,
            json={"is_active": False}
        )
        
        # Try to use it
        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 401


class TestAPIKeyUpdate:
    """Test API key updates"""
    
    def test_update_api_key_name(self, client: TestClient, auth_headers: dict):
        """Test updating API key name"""
        # Create key
        create_response = client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={"name": "Original Name"}
        )
        key_id = create_response.json()["data"]["id"]
        
        # Update name
        response = client.patch(
            f"/api/v1/api-keys/{key_id}",
            headers=auth_headers,
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Updated Name"
    
    def test_update_api_key_status(self, client: TestClient, auth_headers: dict):
        """Test updating API key active status"""
        # Create key
        create_response = client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={"name": "Test Key"}
        )
        key_id = create_response.json()["data"]["id"]
        
        # Deactivate
        response = client.patch(
            f"/api/v1/api-keys/{key_id}",
            headers=auth_headers,
            json={"is_active": False}
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["is_active"] is False


class TestAPIKeyRevocation:
    """Test API key revocation (deletion)"""
    
    def test_revoke_api_key(self, client: TestClient, auth_headers: dict):
        """Test revoking an API key"""
        # Create key
        create_response = client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={"name": "To Be Revoked"}
        )
        key_id = create_response.json()["data"]["id"]
        
        # Revoke it
        response = client.delete(
            f"/api/v1/api-keys/{key_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(
            f"/api/v1/api-keys/{key_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    def test_revoke_nonexistent_key(self, client: TestClient, auth_headers: dict):
        """Test revoking non-existent key"""
        response = client.delete(
            "/api/v1/api-keys/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )
        
        assert response.status_code == 404
