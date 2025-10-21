"""
Prediction schemas for request and response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID


# Request Schemas

class PredictionInput(BaseModel):
    """Schema for single prediction request"""
    input: Dict[str, Any] = Field(..., description="Input data for prediction")
    version: Optional[int] = Field(None, description="Model version (defaults to latest)")


class BatchPredictionInput(BaseModel):
    """Schema for batch prediction request"""
    inputs: List[Dict[str, Any]] = Field(..., description="List of input data for batch prediction")
    version: Optional[int] = None


# Response Schemas

class PredictionResult(BaseModel):
    """Schema for prediction result"""
    prediction: Any = Field(..., description="Model prediction output")
    confidence: Optional[float] = Field(None, description="Prediction confidence score")
    probabilities: Optional[List[float]] = Field(None, description="Class probabilities")


class PredictionMetadata(BaseModel):
    """Schema for prediction metadata"""
    model_id: UUID
    model_version: int
    inference_time_ms: int
    cached: bool = False


class PredictionResponse(BaseModel):
    """Schema for prediction response"""
    prediction: PredictionResult
    metadata: PredictionMetadata
    timestamp: datetime


class BatchJobResponse(BaseModel):
    """Schema for batch prediction job response"""
    job_id: UUID
    status: str
    total_items: int
    estimated_completion: Optional[datetime]
    status_endpoint: str
    message: str = "Batch prediction job created"


class BatchJobStatusResponse(BaseModel):
    """Schema for batch job status"""
    job_id: UUID
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: Optional[Dict[str, Any]]
    results: Optional[List[Dict[str, Any]]]
    statistics: Optional[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]


class PredictionHistoryResponse(BaseModel):
    """Schema for prediction history item"""
    id: UUID
    model_id: UUID
    model_name: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    inference_time_ms: Optional[int]
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
