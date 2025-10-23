"""
Prediction endpoints
Handles real-time and batch predictions
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
import time
import numpy as np
import logging

from app.db.session import get_db
from app.models.user import User
from app.models.model import Model
from app.models.prediction import Prediction
from app.schemas.prediction import (
    PredictionInput,
    PredictionResponse,
    PredictionResult,
    PredictionMetadata
)
from app.api.dependencies import get_current_user
from app.core.model_loader import get_model_loader, ModelLoader

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predict", tags=["Predictions"])


# Background task to log predictions
def log_prediction_to_db(
    db: Session,
    user_id: UUID,
    model_id: UUID,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    inference_time_ms: int,
    status: str = "success",
    error_message: str = None
):
    """Background task to log prediction to database"""
    try:
        prediction_log = Prediction(
            user_id=user_id,
            model_id=model_id,
            input_data=input_data,
            output_data=output_data,
            inference_time_ms=inference_time_ms,
            status=status,
            error_message=error_message
        )
        db.add(prediction_log)
        db.commit()
        logger.info(f"Logged prediction for model {model_id}, status: {status}")
    except Exception as e:
        logger.error(f"Failed to log prediction: {str(e)}")
        db.rollback()


@router.post("/{model_id}", response_model=dict)
async def predict(
    model_id: str,
    prediction_input: PredictionInput,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    loader: ModelLoader = Depends(get_model_loader)
):
    """
    Make a real-time prediction
    
    - **model_id**: Model UUID
    - **input**: Input data as JSON object
    - **version**: Optional model version (defaults to latest)
    
    Requires authentication
    
    Returns prediction result with metadata
    """
    start_time = time.time()
    
    # Get model
    query = db.query(Model).filter(Model.id == model_id)
    
    # Filter by version if specified
    if prediction_input.version:
        query = query.filter(Model.version == prediction_input.version)
    
    model_record = query.first()
    
    if not model_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found or version not available"
        )
    
    if model_record.status not in ["active", "deprecated"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model is not available for predictions"
        )
    
    try:
        # Load model from disk/cache
        model = loader.load_model(model_record.file_path, str(model_record.id))
        
        # Prepare input data
        input_data = prediction_input.input
        
        # Convert input to numpy array for sklearn models
        if model_record.model_type == "sklearn":
            # Extract features as list (assume dict keys are feature names)
            if isinstance(input_data, dict):
                # Try to get features in order
                feature_values = list(input_data.values())
            elif isinstance(input_data, list):
                feature_values = input_data
            else:
                raise ValueError("Input must be a dict or list")
            
            X = np.array([feature_values])
            
            # Make prediction
            prediction = model.predict(X)
            
            # Get probabilities if available
            probabilities = None
            confidence = None
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(X)
                probabilities = proba[0].tolist()
                confidence = float(max(probabilities))
            
            # Format result
            prediction_result = {
                "prediction": int(prediction[0]) if hasattr(prediction[0], 'item') else prediction[0],
                "confidence": confidence,
                "probabilities": probabilities
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Predictions for {model_record.model_type} models not yet implemented"
            )
        
        # Calculate inference time
        inference_time_ms = int((time.time() - start_time) * 1000)
        
        # Log prediction to database asynchronously (non-blocking)
        background_tasks.add_task(
            log_prediction_to_db,
            db=db,
            user_id=current_user.id,
            model_id=model_record.id,
            input_data=prediction_input.input,
            output_data=prediction_result,
            inference_time_ms=inference_time_ms,
            status="success"
        )
        
        return {
            "success": True,
            "data": {
                "prediction": prediction_result,
                "metadata": {
                    "model_id": str(model_record.id),
                    "model_version": model_record.version,
                    "inference_time_ms": inference_time_ms,
                    "cached": loader.is_model_cached(str(model_record.id))
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model file not found on disk"
        )
    except Exception as e:
        # Log failed prediction asynchronously
        background_tasks.add_task(
            log_prediction_to_db,
            db=db,
            user_id=current_user.id,
            model_id=model_record.id,
            input_data=prediction_input.input,
            output_data=None,
            inference_time_ms=int((time.time() - start_time) * 1000),
            status="failed",
            error_message=str(e)
        )
        
        logger.error(f"Prediction failed for model {model_id}: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/history", response_model=dict)
async def get_prediction_history(
    model_id: str = None,
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get prediction history
    
    - **model_id**: Optional model UUID to filter by
    - **page**: Page number
    - **per_page**: Items per page
    
    Requires authentication
    
    Returns paginated prediction history
    """
    # TODO: Implement prediction history query
    # Query predictions table with filters
    
    return {
        "success": True,
        "data": [],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_pages": 0,
            "total_items": 0
        }
    }
