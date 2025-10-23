"""
Rate limiting using Redis
Implements token bucket algorithm for API rate limiting
"""
import time
import redis
from typing import Optional
from fastapi import HTTPException, status, Request
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-based rate limiter using token bucket algorithm
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit
        
        Args:
            key: Unique identifier (user_id, ip_address, etc.)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (allowed: bool, metadata: dict)
        """
        try:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # Redis key for this rate limit
            redis_key = f"rate_limit:{key}"
            
            # Remove old entries outside the window
            self.redis.zremrangebyscore(redis_key, 0, window_start)
            
            # Count requests in current window
            request_count = self.redis.zcard(redis_key)
            
            if request_count < max_requests:
                # Add current request
                self.redis.zadd(redis_key, {str(current_time): current_time})
                self.redis.expire(redis_key, window_seconds)
                
                return True, {
                    "limit": max_requests,
                    "remaining": max_requests - request_count - 1,
                    "reset": int(current_time + window_seconds)
                }
            else:
                # Get oldest request time to calculate reset
                oldest = self.redis.zrange(redis_key, 0, 0, withscores=True)
                reset_time = int(oldest[0][1] + window_seconds) if oldest else int(current_time + window_seconds)
                
                return False, {
                    "limit": max_requests,
                    "remaining": 0,
                    "reset": reset_time
                }
        
        except Exception as e:
            logger.error(f"Rate limiter error: {str(e)}")
            # Fail open - allow request if Redis is down
            return True, {
                "limit": max_requests,
                "remaining": max_requests,
                "reset": int(time.time() + window_seconds)
            }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance"""
    global _rate_limiter
    
    if _rate_limiter is None:
        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=False
            )
            _rate_limiter = RateLimiter(redis_client)
            logger.info("Rate limiter initialized with Redis")
        except Exception as e:
            logger.warning(f"Failed to initialize rate limiter: {str(e)}")
            # Create a dummy limiter that always allows
            _rate_limiter = RateLimiter(None)
    
    return _rate_limiter


async def rate_limit_dependency(
    request: Request,
    max_requests: int = 100,
    window_seconds: int = 60
):
    """
    FastAPI dependency for rate limiting
    
    Usage:
        @app.get("/endpoint", dependencies=[Depends(rate_limit_dependency)])
    """
    limiter = get_rate_limiter()
    
    # Use user ID if authenticated, otherwise IP address
    if hasattr(request.state, "user_id"):
        key = f"user:{request.state.user_id}"
    else:
        key = f"ip:{request.client.host}"
    
    allowed, metadata = await limiter.check_rate_limit(
        key=key,
        max_requests=max_requests,
        window_seconds=window_seconds
    )
    
    # Add rate limit headers to response (we'll do this in middleware)
    request.state.rate_limit_metadata = metadata
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "limit": metadata["limit"],
                "reset": metadata["reset"],
                "retry_after": metadata["reset"] - int(time.time())
            }
        )
