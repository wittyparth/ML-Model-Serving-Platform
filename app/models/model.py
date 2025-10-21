"""
Model database model
Represents ML model metadata and versioning
"""
from sqlalchemy import Column, String, Integer, BigInteger, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Model(Base):
    """ML Model metadata model"""
    
    __tablename__ = "models"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Model information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    model_type = Column(String(50), nullable=False)  # 'sklearn', 'tensorflow', 'pytorch'
    version = Column(Integer, default=1, nullable=False)
    
    # File information
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=True)  # Size in bytes
    
    # Status
    status = Column(String(20), default="active", index=True)  # 'active', 'deprecated', 'archived'
    
    # Schema information (stored as JSON)
    input_schema = Column(JSONB, nullable=True)
    output_schema = Column(JSONB, nullable=True)
    metadata = Column(JSONB, nullable=True)  # Additional flexible metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="models")
    predictions = relationship("Prediction", back_populates="model")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'name', 'version', name='unique_user_model_version'),
    )
    
    def __repr__(self) -> str:
        return f"<Model(id={self.id}, name={self.name}, version={self.version})>"
