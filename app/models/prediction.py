"""
Prediction database model
Logs all prediction requests for analytics and debugging
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Prediction(Base):
    """Prediction log model"""
    
    __tablename__ = "predictions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Prediction data (stored as JSON)
    input_data = Column(JSONB, nullable=False)
    output_data = Column(JSONB, nullable=True)
    
    # Performance metrics
    inference_time_ms = Column(Integer, nullable=True)  # Inference time in milliseconds
    
    # Status
    status = Column(String(20), default="success", index=True)  # 'success', 'failed', 'pending'
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    model = relationship("Model", back_populates="predictions")
    user = relationship("User", back_populates="predictions")
    
    def __repr__(self) -> str:
        return f"<Prediction(id={self.id}, model_id={self.model_id}, status={self.status})>"
