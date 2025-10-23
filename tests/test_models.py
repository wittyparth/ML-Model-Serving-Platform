"""
Comprehensive tests for model management endpoints
"""
import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.model import Model
from app.models.user import User


class TestModelUpload:
    """Test model upload functionality"""
    
    def test_upload_model_success(self, client: TestClient, auth_headers: dict, temp_model_file: str):
        """Test successful model upload"""
        with open(temp_model_file, 'rb') as f:
            response = client.post(
                "/api/v1/models/upload",
                headers=auth_headers,
                data={
                    "name": "test_classifier",
                    "description": "Test model",
                    "model_type": "sklearn"
                },
                files={"file": ("model.pkl", f, "application/octet-stream")}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["model"]["name"] == "test_classifier"
        assert data["data"]["model"]["model_type"] == "sklearn"
        assert data["data"]["model"]["version"] == 1
    
    def test_upload_model_versioning(self, client: TestClient, auth_headers: dict, temp_model_file: str):
        """Test automatic versioning on model upload"""
        # Upload first version
        with open(temp_model_file, 'rb') as f:
            response1 = client.post(
                "/api/v1/models/upload",
                headers=auth_headers,
                data={
                    "name": "versioned_model",
                    "model_type": "sklearn"
                },
                files={"file": ("model.pkl", f, "application/octet-stream")}
            )
        
        assert response1.json()["data"]["model"]["version"] == 1
        
        # Upload second version
        with open(temp_model_file, 'rb') as f:
            response2 = client.post(
                "/api/v1/models/upload",
                headers=auth_headers,
                data={
                    "name": "versioned_model",
                    "model_type": "sklearn"
                },
                files={"file": ("model.pkl", f, "application/octet-stream")}
            )
        
        assert response2.json()["data"]["model"]["version"] == 2
    
    def test_upload_model_no_auth(self, client: TestClient, temp_model_file: str):
        """Test model upload without authentication"""
        with open(temp_model_file, 'rb') as f:
            response = client.post(
                "/api/v1/models/upload",
                data={
                    "name": "test_model",
                    "model_type": "sklearn"
                },
                files={"file": ("model.pkl", f, "application/octet-stream")}
            )
        
        assert response.status_code == 401


class TestModelListing:
    """Test model listing functionality"""
    
    def test_list_models_empty(self, client: TestClient, auth_headers: dict):
        """Test listing models when none exist"""
        response = client.get("/api/v1/models", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0
    
    def test_list_models_with_data(self, client: TestClient, auth_headers: dict, test_model: Model):
        """Test listing models with existing models"""
        response = client.get("/api/v1/models", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "test_model"
    
    def test_list_models_pagination(self, client: TestClient, auth_headers: dict):
        """Test model listing with pagination"""
        response = client.get(
            "/api/v1/models?page=1&per_page=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "pagination" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 10


class TestModelDetails:
    """Test getting model details"""
    
    def test_get_model_success(self, client: TestClient, auth_headers: dict, test_model: Model):
        """Test getting model details"""
        response = client.get(
            f"/api/v1/models/{test_model.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "test_model"
        assert "statistics" in data["data"]
    
    def test_get_model_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent model"""
        response = client.get(
            "/api/v1/models/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_model_unauthorized(self, client: TestClient, test_model: Model):
        """Test getting model without authentication"""
        response = client.get(f"/api/v1/models/{test_model.id}")
        
        assert response.status_code == 401


class TestModelUpdate:
    """Test model update functionality"""
    
    def test_update_model_description(self, client: TestClient, auth_headers: dict, test_model: Model):
        """Test updating model description"""
        response = client.patch(
            f"/api/v1/models/{test_model.id}",
            headers=auth_headers,
            json={"description": "Updated description"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["description"] == "Updated description"
    
    def test_update_model_status(self, client: TestClient, auth_headers: dict, test_model: Model):
        """Test updating model status"""
        response = client.patch(
            f"/api/v1/models/{test_model.id}",
            headers=auth_headers,
            json={"status": "deprecated"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "deprecated"


class TestModelDeletion:
    """Test model deletion (soft delete)"""
    
    def test_delete_model(self, client: TestClient, auth_headers: dict, test_model: Model):
        """Test soft deleting a model"""
        response = client.delete(
            f"/api/v1/models/{test_model.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
    
    def test_delete_model_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent model"""
        response = client.delete(
            "/api/v1/models/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestModelAnalytics:
    """Test model analytics endpoint"""
    
    def test_get_analytics(self, client: TestClient, auth_headers: dict, test_model: Model):
        """Test getting model analytics"""
        response = client.get(
            f"/api/v1/models/{test_model.id}/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data["data"]
        assert "usage_trends" in data["data"]
        assert "recent_errors" in data["data"]
    
    def test_get_analytics_custom_period(self, client: TestClient, auth_headers: dict, test_model: Model):
        """Test getting analytics with custom period"""
        response = client.get(
            f"/api/v1/models/{test_model.id}/analytics?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["analysis_period_days"] == 30
