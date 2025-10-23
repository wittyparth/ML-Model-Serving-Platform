"""Database models"""

# Import all models here to avoid circular import issues
# and to make them available when importing from app.models
from app.models.user import User
from app.models.model import Model
from app.models.prediction import Prediction
from app.models.api_key import APIKey

__all__ = ["User", "Model", "Prediction", "APIKey"]
