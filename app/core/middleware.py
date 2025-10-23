"""
Custom middleware for request logging, error tracking, and performance monitoring
"""
import time
import logging
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import traceback

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class RateLimitHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add rate limit headers to responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add rate limit headers if metadata exists
        if hasattr(request.state, "rate_limit_metadata"):
            metadata = request.state.rate_limit_metadata
            response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
            response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
            response.headers["X-RateLimit-Reset"] = str(metadata["reset"])
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests with timing information
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()
        
        # Get request details
        request_id = str(time.time())
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(json.dumps({
            "event": "request_started",
            "request_id": request_id,
            "method": method,
            "path": path,
            "client": client_host,
            "timestamp": time.time()
        }))
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(json.dumps({
                "event": "request_completed",
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "timestamp": time.time()
            }))
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{round(duration_ms, 2)}ms"
            
            return response
            
        except Exception as e:
            # Calculate duration even for errors
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(json.dumps({
                "event": "request_failed",
                "request_id": request_id,
                "method": method,
                "path": path,
                "error": str(e),
                "duration_ms": round(duration_ms, 2),
                "timestamp": time.time()
            }))
            
            # Re-raise the exception
            raise


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch and log all unhandled exceptions
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            # Get full traceback
            tb = traceback.format_exc()
            
            # Log detailed error
            logger.error(json.dumps({
                "event": "unhandled_exception",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "path": request.url.path,
                "method": request.method,
                "traceback": tb,
                "timestamp": time.time()
            }))
            
            # Re-raise to let FastAPI handle it
            raise


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track endpoint performance and log slow requests
    """
    
    def __init__(self, app: ASGIApp, slow_threshold_ms: float = 1000):
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Log slow requests
        if duration_ms > self.slow_threshold_ms:
            logger.warning(json.dumps({
                "event": "slow_request",
                "path": request.url.path,
                "method": request.method,
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": self.slow_threshold_ms,
                "timestamp": time.time()
            }))
        
        return response
