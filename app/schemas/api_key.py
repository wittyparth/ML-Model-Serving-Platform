"""
API Key schemas for request and response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


# Request Schemas

class APIKeyCreate(BaseModel):
    """Schema for creating a new API key"""
    name: str = Field(..., description="User-friendly name for the API key", max_length=255)
    expires_days: Optional[int] = Field(None, description="Number of days until expiration (None = never expires)", ge=1, le=365)


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key"""
    name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


# Response Schemas

class APIKeyResponse(BaseModel):
    """Schema for API key response (without the actual key)"""
    id: UUID
    user_id: UUID
    name: Optional[str]
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class APIKeyCreateResponse(BaseModel):
    """Schema for API key creation response (includes the key once)"""
    id: UUID
    user_id: UUID
    name: Optional[str]
    api_key: str = Field(..., description="The actual API key - save this, it won't be shown again!")
    expires_at: Optional[datetime]
    created_at: datetime
    message: str = "API key created successfully. Save the key - it won't be shown again!"


class APIKeyListResponse(BaseModel):
    """Schema for listing API keys"""
    id: UUID
    name: Optional[str]
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    prefix: str = Field(..., description="First 8 characters of the key for identification")
    
    model_config = ConfigDict(from_attributes=True)
