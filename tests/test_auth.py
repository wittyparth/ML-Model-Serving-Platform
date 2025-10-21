"""Tests for authentication endpoints"""
import pytest
from fastapi import status


def test_register_user(client):
    """Test user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPass123!",
            "full_name": "Test User"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "test@example.com"


def test_register_duplicate_email(client):
    """Test registration with duplicate email"""
    # Register first user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPass123!",
        }
    )
    
    # Try to register again with same email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "AnotherPass123!",
        }
    )
    assert response.status_code == status.HTTP_409_CONFLICT


def test_login(client):
    """Test user login"""
    # Register user first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPass123!",
        }
    )
    
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPass123!",
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword!",
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
