"""
Model schemas for request and response validation
"""
from pydantic_test import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# Request Schemas

class ModelCreate(BaseModel):
    """Schema for creating a new model (used with file upload)"""
    name: str = Field(..., min_length=1, max_length=255, description="Model name")
    description: Optional[str] = Field(None, description="Model description")
    model_type: str = Field(..., description="Model type (sklearn, tensorflow, pytorch)")


class ModelUpdate(BaseModel):
    """Schema for updating model metadata"""
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|deprecated|archived)$")


# Response Schemas

class ModelResponse(BaseModel):
    """Schema for model response"""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    model_type: str
    version: int
    status: str
    file_size: Optional[int]
    input_schema: Optional[Dict[str, Any]]
    output_schema: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class ModelListResponse(BaseModel):
    """Schema for model list item (summary)"""
    id: UUID
    name: str
    version: int
    status: str
    model_type: str
    file_size: Optional[int]
    prediction_count: int = 0
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ModelUploadResponse(BaseModel):
    """Schema for model upload response"""
    model: ModelResponse
    prediction_endpoint: str
    message: str = "Model uploaded successfully"
