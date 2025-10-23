"""
Model Loading and Caching Service
Handles loading ML models from disk and caching them in memory
"""
import joblib
import pickle
from typing import Any, Optional
from functools import lru_cache
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelLoader:
    """Service for loading and caching ML models"""
    
    def __init__(self, cache_size: int = 5):
        """
        Initialize model loader
        
        Args:
            cache_size: Maximum number of models to keep in memory
        """
        self.cache_size = cache_size
        self._cache: dict[str, Any] = {}
    
    def load_model(self, file_path: str, model_id: str) -> Any:
        """
        Load a model from disk (with LRU caching)
        
        Args:
            file_path: Path to model file
            model_id: Unique model identifier for caching
            
        Returns:
            Loaded model object
            
        Raises:
            FileNotFoundError: If model file doesn't exist
            Exception: If model loading fails
        """
        # Check if model is in cache
        if model_id in self._cache:
            logger.info(f"Model {model_id} loaded from cache")
            return self._cache[model_id]
        
        # Load from disk
        try:
            model_path = Path(file_path)
            
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found: {file_path}")
            
            # Try loading with joblib first, then pickle as fallback
            try:
                model = joblib.load(file_path)
                logger.info(f"Model loaded with joblib: {file_path}")
            except Exception as joblib_error:
                logger.warning(f"Joblib load failed, trying pickle: {str(joblib_error)}")
                try:
                    with open(file_path, 'rb') as f:
                        model = pickle.load(f)
                    logger.info(f"Model loaded with pickle: {file_path}")
                except Exception as pickle_error:
                    raise Exception(f"Failed to load model with both joblib and pickle. Joblib: {str(joblib_error)}, Pickle: {str(pickle_error)}")
            
            # Add to cache
            self._add_to_cache(model_id, model)
            
            logger.info(f"Model {model_id} successfully loaded and cached")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {str(e)}")
            raise
    
    def _add_to_cache(self, model_id: str, model: Any):
        """Add model to cache with LRU eviction"""
        # If cache is full, remove oldest entry
        if len(self._cache) >= self.cache_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.info(f"Evicted model {oldest_key} from cache")
        
        self._cache[model_id] = model
    
    def clear_cache(self):
        """Clear all models from cache"""
        self._cache.clear()
        logger.info("Model cache cleared")
    
    def remove_from_cache(self, model_id: str):
        """Remove a specific model from cache"""
        if model_id in self._cache:
            del self._cache[model_id]
            logger.info(f"Model {model_id} removed from cache")
    
    def is_model_cached(self, model_id: str) -> bool:
        """Check if a model is currently in cache"""
        return model_id in self._cache


# Global model loader instance
model_loader = ModelLoader(cache_size=5)


def get_model_loader() -> ModelLoader:
    """Dependency for getting model loader instance"""
    return model_loader
