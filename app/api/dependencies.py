"""
Shared API dependencies
Provides common dependencies like authentication and database sessions
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import hashlib

from app.db.session import get_db
from app.core.security import verify_token
from app.models.user import User
from app.models.api_key import APIKey

# Security scheme for JWT Bearer tokens (auto_error=False to allow API key auth)
security = HTTPBearer(auto_error=False)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for lookup"""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_user_from_api_key(
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get user from API key header
    
    Args:
        x_api_key: API key from X-API-Key header
        db: Database session
        
    Returns:
        User object if valid API key, None otherwise
    """
    if not x_api_key:
        return None
    
    # Hash the API key
    key_hash = hash_api_key(x_api_key)
    
    # Look up API key in database
    api_key_record = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()
    
    if not api_key_record:
        return None
    
    # Check if key is expired
    if api_key_record.expires_at:
        now = datetime.now(timezone.utc)
        if api_key_record.expires_at < now:
            return None
    
    # Update last_used_at
    api_key_record.last_used_at = datetime.now(timezone.utc)
    db.commit()
    
    # Get and return user
    user = db.query(User).filter(User.id == api_key_record.user_id).first()
    return user


async def get_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> User:
    """
    Dependency to get the current authenticated user
    
    Supports both JWT tokens and API keys
    
    Args:
        credentials: JWT token from Authorization header
        x_api_key: API key from X-API-Key header
        db: Database session
        
    Returns:
        Authenticated user object
        
    Raises:
        HTTPException: If neither auth method is valid
        
    Usage:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
    """
    # Try API key first
    if x_api_key:
        user = await get_user_from_api_key(x_api_key, db)
        if user:
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key"
            )
    
    # Try JWT token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide either Bearer token or X-API-Key header."
        )
    
    # Verify and decode token
    payload = verify_token(credentials.credentials, token_type="access")
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is an admin
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Admin user object
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
