"""
Model management endpoints
Handles model upload, versioning, listing, and deletion
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import os
import uuid as uuid_lib

from app.db.session import get_db
from app.models.user import User
from app.models.model import Model
from app.models.prediction import Prediction
from app.schemas.model import (
    ModelResponse,
    ModelListResponse,
    ModelUpdate,
    ModelUploadResponse
)
from app.api.dependencies import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/models", tags=["Models"])


@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    model_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a new ML model
    
    - **file**: Model file (.pkl, .joblib for sklearn)
    - **name**: Model name
    - **description**: Optional model description
    - **model_type**: Type of model (sklearn, tensorflow, pytorch)
    
    Requires authentication
    
    Returns model metadata and prediction endpoint
    """
    # Validate model type
    if model_type not in settings.ALLOWED_MODEL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model type must be one of: {', '.join(settings.ALLOWED_MODEL_TYPES)}"
        )
    
    # Check file size
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    # Get next version number for this model name
    latest_model = db.query(Model).filter(
        Model.user_id == current_user.id,
        Model.name == name
    ).order_by(desc(Model.version)).first()
    
    version = 1 if not latest_model else latest_model.version + 1
    
    # Create file path
    model_id = str(uuid_lib.uuid4())
    file_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id), name, f"v{version}")
    os.makedirs(file_dir, exist_ok=True)
    
    file_path = os.path.join(file_dir, file.filename or "model.pkl")
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create model record
    new_model = Model(
        id=model_id,
        user_id=current_user.id,
        name=name,
        description=description,
        model_type=model_type,
        version=version,
        file_path=file_path,
        file_size=file_size,
        status="active"
    )
    
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    
    return {
        "success": True,
        "data": {
            "model": ModelResponse.model_validate(new_model),
            "prediction_endpoint": f"{settings.API_V1_PREFIX}/predict/{model_id}",
            "message": "Model uploaded successfully"
        }
    }


@router.get("", response_model=dict)
async def list_models(
    page: int = 1,
    per_page: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's models
    
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **status**: Filter by status (active, deprecated, archived)
    
    Requires authentication
    
    Returns paginated list of models
    """
    # Build query
    query = db.query(Model).filter(Model.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Model.status == status_filter)
    
    # Get total count
    total = query.count()
    
    # Paginate
    skip = (page - 1) * per_page
    models = query.order_by(desc(Model.created_at)).offset(skip).limit(per_page).all()
    
    # TODO: Add prediction count from predictions table
    model_list = [
        {
            **ModelListResponse.model_validate(model).model_dump(),
            "prediction_count": 0  # Placeholder
        }
        for model in models
    ]
    
    return {
        "success": True,
        "data": model_list,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "total_items": total
        }
    }


@router.get("/{model_id}", response_model=dict)
async def get_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get model details
    
    - **model_id**: Model UUID
    
    Requires authentication and ownership
    
    Returns detailed model information
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    if model.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this model"
        )
    
    # TODO: Add statistics from predictions table
    response_data = ModelResponse.model_validate(model).model_dump()
    response_data["statistics"] = {
        "total_predictions": 0,
        "avg_inference_time_ms": 0,
        "success_rate": 100.0
    }
    
    return {
        "success": True,
        "data": response_data
    }


@router.patch("/{model_id}", response_model=dict)
async def update_model(
    model_id: str,
    model_update: ModelUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update model metadata
    
    - **model_id**: Model UUID
    - **description**: New description (optional)
    - **status**: New status (optional): active, deprecated, archived
    
    Requires authentication and ownership
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    if model.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this model"
        )
    
    # Update fields
    if model_update.description is not None:
        model.description = model_update.description
    if model_update.status is not None:
        model.status = model_update.status
    
    db.commit()
    db.refresh(model)
    
    return {
        "success": True,
        "data": ModelResponse.model_validate(model),
        "message": "Model updated successfully"
    }


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete (archive) a model
    
    - **model_id**: Model UUID
    
    Requires authentication and ownership
    
    Performs soft delete (sets status to 'archived')
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    if model.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this model"
        )
    
    # Soft delete
    model.status = "archived"
    db.commit()
    
    return None


@router.get("/{model_id}/analytics", response_model=dict)
async def get_model_analytics(
    model_id: str,
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get model analytics and usage statistics
    
    - **model_id**: Model UUID
    - **days**: Number of days to analyze (default: 7, max: 90)
    
    Requires authentication and ownership
    
    Returns prediction count, avg inference time, success rate, and usage trends
    """
    # Validate model exists and user has access
    model = db.query(Model).filter(Model.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    if model.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this model's analytics"
        )
    
    # Limit days to reasonable range
    if days > 90:
        days = 90
    
    # Query predictions for this model
    predictions_query = db.query(Prediction).filter(Prediction.model_id == model_id)
    
    # Overall statistics
    total_predictions = predictions_query.count()
    successful_predictions = predictions_query.filter(Prediction.status == "success").count()
    failed_predictions = predictions_query.filter(Prediction.status == "failed").count()
    
    # Calculate success rate
    success_rate = (successful_predictions / total_predictions * 100) if total_predictions > 0 else 0
    
    # Average inference time (only for successful predictions)
    avg_inference_time = db.query(func.avg(Prediction.inference_time_ms)).filter(
        Prediction.model_id == model_id,
        Prediction.status == "success",
        Prediction.inference_time_ms.isnot(None)
    ).scalar()
    
    # Min and max inference time
    min_inference_time = db.query(func.min(Prediction.inference_time_ms)).filter(
        Prediction.model_id == model_id,
        Prediction.status == "success",
        Prediction.inference_time_ms.isnot(None)
    ).scalar()
    
    max_inference_time = db.query(func.max(Prediction.inference_time_ms)).filter(
        Prediction.model_id == model_id,
        Prediction.status == "success",
        Prediction.inference_time_ms.isnot(None)
    ).scalar()
    
    # Daily usage trends (last N days)
    from datetime import datetime, timedelta
    from sqlalchemy import cast, Date
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    daily_stats = db.query(
        cast(Prediction.created_at, Date).label('date'),
        func.count(Prediction.id).label('count'),
        func.avg(Prediction.inference_time_ms).label('avg_time')
    ).filter(
        Prediction.model_id == model_id,
        Prediction.created_at >= cutoff_date
    ).group_by(
        cast(Prediction.created_at, Date)
    ).order_by(
        cast(Prediction.created_at, Date)
    ).all()
    
    usage_trends = [
        {
            "date": str(stat.date),
            "prediction_count": stat.count,
            "avg_inference_time_ms": round(float(stat.avg_time), 2) if stat.avg_time else None
        }
        for stat in daily_stats
    ]
    
    # Recent errors (last 10)
    recent_errors = db.query(Prediction).filter(
        Prediction.model_id == model_id,
        Prediction.status == "failed"
    ).order_by(
        desc(Prediction.created_at)
    ).limit(10).all()
    
    error_list = [
        {
            "timestamp": error.created_at.isoformat(),
            "error_message": error.error_message,
            "input_data": error.input_data
        }
        for error in recent_errors
    ]
    
    return {
        "success": True,
        "data": {
            "model_id": str(model_id),
            "model_name": model.name,
            "model_version": model.version,
            "statistics": {
                "total_predictions": total_predictions,
                "successful_predictions": successful_predictions,
                "failed_predictions": failed_predictions,
                "success_rate": round(success_rate, 2),
                "avg_inference_time_ms": round(float(avg_inference_time), 2) if avg_inference_time else None,
                "min_inference_time_ms": min_inference_time,
                "max_inference_time_ms": max_inference_time
            },
            "usage_trends": usage_trends,
            "recent_errors": error_list,
            "analysis_period_days": days
        }
    }

