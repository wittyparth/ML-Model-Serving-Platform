"""
Health check endpoints
Monitors system health and service availability
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
from datetime import datetime
from pathlib import Path

from app.db.session import get_db
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint
    
    Checks:
    - API availability
    - Database connectivity
    - File system accessibility
    - Upload directory
    
    Returns overall health status and component details
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check API
    health_status["components"]["api"] = {
        "status": "healthy",
        "message": "API is running"
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
    
    # Check file system and upload directory
    try:
        upload_dir = Path(settings.UPLOAD_DIR)
        
        # Check if directory exists
        if not upload_dir.exists():
            os.makedirs(upload_dir, exist_ok=True)
        
        # Check if directory is writable
        test_file = upload_dir / ".health_check"
        test_file.touch()
        test_file.unlink()
        
        health_status["components"]["file_system"] = {
            "status": "healthy",
            "message": "File system accessible",
            "upload_dir": str(upload_dir)
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["file_system"] = {
            "status": "unhealthy",
            "message": f"File system error: {str(e)}"
        }
    
    # Return appropriate status code
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint
    
    Quick check if the service is ready to accept traffic
    """
    try:
        # Simple database check
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not ready", "error": str(e)}
        )


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint
    
    Quick check if the service is alive
    """
    return {"status": "alive"}
