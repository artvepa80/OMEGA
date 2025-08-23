#!/usr/bin/env python3
"""
Unified Interface for OMEGA AI Models
Provides standardized interface for all prediction models
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Types of prediction models"""
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"
    PROBABILISTIC = "probabilistic"
    EVOLUTIONARY = "evolutionary"
    CLUSTERING = "clustering"
    TRANSFORMER = "transformer"
    SEQUENTIAL = "sequential"

@dataclass
class ModelConfig:
    """Configuration for prediction models"""
    model_name: str
    model_type: ModelType
    parameters: Dict[str, Any]
    training_required: bool = False
    min_data_size: int = 50
    max_combinations: int = 500
    timeout_seconds: int = 300

@dataclass
class PredictionResult:
    """Standardized prediction result"""
    combination: List[int]
    score: float
    confidence: float
    source: str
    metrics: Dict[str, Any]
    execution_time: float
    normalized_score: float = 0.0

class BasePredictorInterface(ABC):
    """Base interface for all OMEGA prediction models"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.is_trained = False
        self.is_initialized = False
        self.logger = logging.getLogger(f"{__name__}.{config.model_name}")
        
    @abstractmethod
    def initialize(self, historical_data: Union[pd.DataFrame, np.ndarray, List[List[int]]]) -> bool:
        """Initialize the model with historical data"""
        pass
    
    @abstractmethod
    def train(self, training_data: Union[pd.DataFrame, np.ndarray, List[List[int]]], 
              labels: Optional[List[Any]] = None) -> bool:
        """Train the model if training is required"""
        pass
    
    @abstractmethod
    def predict(self, quantity: int = 30, context: Optional[Dict[str, Any]] = None) -> List[PredictionResult]:
        """Generate predictions"""
        pass
    
    @abstractmethod
    def validate_input(self, data: Union[pd.DataFrame, np.ndarray, List[List[int]]]) -> bool:
        """Validate input data format and quality"""
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "name": self.config.model_name,
            "type": self.config.model_type.value,
            "is_trained": self.is_trained,
            "is_initialized": self.is_initialized,
            "training_required": self.config.training_required,
            "min_data_size": self.config.min_data_size,
            "parameters": self.config.parameters
        }
    
    def reset(self) -> bool:
        """Reset model state"""
        self.is_trained = False
        self.is_initialized = False
        return True
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the model"""
        return {
            "status": "healthy" if self.is_initialized else "not_initialized",
            "model_name": self.config.model_name,
            "ready_for_prediction": self.is_initialized and (not self.config.training_required or self.is_trained),
            "last_check": pd.Timestamp.now().isoformat()
        }

class ModelFactory:
    """Factory for creating prediction models"""
    
    _registered_models = {}
    
    @classmethod
    def register_model(cls, model_class: type, config: ModelConfig):
        """Register a model class with configuration"""
        cls._registered_models[config.model_name] = {
            'class': model_class,
            'config': config
        }
        logger.info(f"✅ Registered model: {config.model_name}")
    
    @classmethod
    def create_model(cls, model_name: str, custom_params: Optional[Dict[str, Any]] = None) -> BasePredictorInterface:
        """Create a model instance"""
        if model_name not in cls._registered_models:
            raise ValueError(f"Model '{model_name}' not registered")
        
        model_info = cls._registered_models[model_name]
        config = model_info['config']
        
        # Override parameters if provided
        if custom_params:
            config.parameters.update(custom_params)
        
        return model_info['class'](config)
    
    @classmethod
    def list_models(cls) -> Dict[str, Dict[str, Any]]:
        """List all registered models"""
        return {name: info['config'].__dict__ for name, info in cls._registered_models.items()}

class ModelManager:
    """Manages multiple prediction models"""
    
    def __init__(self):
        self.models: Dict[str, BasePredictorInterface] = {}
        self.logger = logging.getLogger(f"{__name__}.ModelManager")
    
    def add_model(self, model: BasePredictorInterface) -> bool:
        """Add a model to the manager"""
        try:
            self.models[model.config.model_name] = model
            self.logger.info(f"✅ Added model: {model.config.model_name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to add model: {e}")
            return False
    
    def initialize_all(self, historical_data: Union[pd.DataFrame, np.ndarray, List[List[int]]]) -> Dict[str, bool]:
        """Initialize all models with historical data"""
        results = {}
        for name, model in self.models.items():
            try:
                results[name] = model.initialize(historical_data)
                self.logger.info(f"{'✅' if results[name] else '❌'} Initialize {name}: {results[name]}")
            except Exception as e:
                results[name] = False
                self.logger.error(f"❌ Failed to initialize {name}: {e}")
        return results
    
    def train_all(self, training_data: Union[pd.DataFrame, np.ndarray, List[List[int]]]) -> Dict[str, bool]:
        """Train all models that require training"""
        results = {}
        for name, model in self.models.items():
            try:
                if model.config.training_required:
                    results[name] = model.train(training_data)
                    self.logger.info(f"{'✅' if results[name] else '❌'} Train {name}: {results[name]}")
                else:
                    results[name] = True  # No training required
            except Exception as e:
                results[name] = False
                self.logger.error(f"❌ Failed to train {name}: {e}")
        return results
    
    def predict_all(self, quantity: int = 30, context: Optional[Dict[str, Any]] = None) -> Dict[str, List[PredictionResult]]:
        """Generate predictions from all models"""
        results = {}
        for name, model in self.models.items():
            try:
                if model.health_check()["ready_for_prediction"]:
                    results[name] = model.predict(quantity, context)
                    self.logger.info(f"✅ {name} generated {len(results[name])} predictions")
                else:
                    self.logger.warning(f"⚠️ {name} not ready for prediction")
                    results[name] = []
            except Exception as e:
                self.logger.error(f"❌ Failed to predict with {name}: {e}")
                results[name] = []
        return results
    
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all models"""
        return {name: model.health_check() for name, model in self.models.items()}
    
    def get_ready_models(self) -> List[str]:
        """Get list of models ready for prediction"""
        return [name for name, model in self.models.items() 
                if model.health_check()["ready_for_prediction"]]

# Utility functions for model integration
def validate_combination(combination: List[int]) -> bool:
    """Validate a lottery combination"""
    try:
        if not isinstance(combination, list) or len(combination) != 6:
            return False
        
        nums = [int(n) for n in combination]
        return (
            len(set(nums)) == 6 and
            all(1 <= n <= 40 for n in nums)
        )
    except (ValueError, TypeError):
        return False

def clean_combination(combination: List[int], logger: Optional[logging.Logger] = None) -> Optional[List[int]]:
    """Clean and validate a combination"""
    try:
        if not combination:
            return None
        
        # Convert to integers and remove duplicates while preserving order
        seen = set()
        clean = []
        for n in combination:
            try:
                num = int(n)
                if 1 <= num <= 40 and num not in seen:
                    clean.append(num)
                    seen.add(num)
            except (ValueError, TypeError):
                continue
        
        # Ensure we have exactly 6 numbers
        if len(clean) == 6:
            return sorted(clean)
        elif len(clean) > 6:
            return sorted(clean[:6])
        else:
            # Pad with random numbers if needed
            remaining = [i for i in range(1, 41) if i not in seen]
            while len(clean) < 6 and remaining:
                import random
                num = random.choice(remaining)
                clean.append(num)
                remaining.remove(num)
            
            if len(clean) == 6:
                return sorted(clean)
        
        return None
        
    except Exception as e:
        if logger:
            logger.debug(f"Error cleaning combination {combination}: {e}")
        return None

# Export main classes and functions
__all__ = [
    'BasePredictorInterface',
    'ModelConfig',
    'ModelType',
    'PredictionResult',
    'ModelFactory',
    'ModelManager',
    'validate_combination',
    'clean_combination'
]