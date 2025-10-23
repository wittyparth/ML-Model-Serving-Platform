"""
API Key management endpoints
Handles creation, listing, and revocation of API keys
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import hashlib

from app.db.session import get_db
from app.models.user import User
from app.models.api_key import APIKey
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKeyListResponse,
    APIKeyUpdate
)
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


def generate_api_key() -> str:
    """Generate a secure random API key"""
    return f"mlp_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key
    
    - **name**: User-friendly name for the key
    - **expires_days**: Optional expiration in days (default: never)
    
    Requires authentication
    
    **Important:** The API key is only shown once! Save it securely.
    """
    # Generate API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    
    # Calculate expiration
    expires_at = None
    if key_data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_days)
    
    # Create database record
    db_api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        name=key_data.name,
        expires_at=expires_at
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return {
        "success": True,
        "data": {
            "id": str(db_api_key.id),
            "user_id": str(db_api_key.user_id),
            "name": db_api_key.name,
            "api_key": api_key,  # Only shown once!
            "expires_at": db_api_key.expires_at.isoformat() if db_api_key.expires_at else None,
            "created_at": db_api_key.created_at.isoformat(),
            "message": "API key created successfully. Save the key - it won't be shown again!"
        }
    }


@router.get("", response_model=dict)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all API keys for the current user
    
    Requires authentication
    
    Returns list of API keys (without the actual keys)
    """
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    
    keys_list = []
    for key in api_keys:
        keys_list.append({
            "id": str(key.id),
            "name": key.name,
            "is_active": key.is_active,
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "created_at": key.created_at.isoformat(),
            "prefix": "mlp_" + "*" * 8  # Show prefix only
        })
    
    return {
        "success": True,
        "data": keys_list
    }


@router.get("/{key_id}", response_model=dict)
async def get_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get API key details
    
    - **key_id**: API key UUID
    
    Requires authentication and ownership
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this API key"
        )
    
    return {
        "success": True,
        "data": APIKeyResponse.model_validate(api_key).model_dump()
    }


@router.patch("/{key_id}", response_model=dict)
async def update_api_key(
    key_id: str,
    key_update: APIKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update API key (name or active status)
    
    - **key_id**: API key UUID
    - **name**: New name (optional)
    - **is_active**: Enable/disable key (optional)
    
    Requires authentication and ownership
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this API key"
        )
    
    # Update fields
    if key_update.name is not None:
        api_key.name = key_update.name
    if key_update.is_active is not None:
        api_key.is_active = key_update.is_active
    
    db.commit()
    db.refresh(api_key)
    
    return {
        "success": True,
        "data": APIKeyResponse.model_validate(api_key).model_dump(),
        "message": "API key updated successfully"
    }


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke (delete) an API key
    
    - **key_id**: API key UUID
    
    Requires authentication and ownership
    
    This permanently deletes the API key
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this API key"
        )
    
    db.delete(api_key)
    db.commit()
    
    return None
