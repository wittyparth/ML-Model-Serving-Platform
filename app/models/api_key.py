"""
API Key database model
Alternative authentication method for programmatic access
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class APIKey(Base):
    """API Key model for programmatic access"""
    
    __tablename__ = "api_keys"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Key information
    key_hash = Column(String(255), unique=True, nullable=False, index=True)  # Hashed API key
    name = Column(String(255), nullable=True)  # User-friendly name
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name={self.name})>"
