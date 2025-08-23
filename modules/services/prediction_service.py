#!/usr/bin/env python3
"""
Prediction Service Layer for OMEGA PRO AI
Provides centralized prediction management with dependency injection
"""

import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
import pandas as pd
import numpy as np
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os

from modules.interfaces.predictor_interface import (
    BasePredictorInterface, ModelManager, PredictionResult, 
    ModelFactory, validate_combination, clean_combination
)

logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """Configuration for prediction service"""
    max_workers: int = 4
    prediction_timeout: int = 300
    enable_caching: bool = True
    cache_duration: int = 3600  # 1 hour
    fallback_enabled: bool = True
    metrics_enabled: bool = True
    auto_model_selection: bool = True

@dataclass
class PredictionRequest:
    """Request for predictions"""
    quantity: int = 30
    context: Optional[Dict[str, Any]] = None
    models: Optional[List[str]] = None  # Specific models to use
    timeout: Optional[int] = None
    enable_fallback: bool = True
    
@dataclass
class PredictionResponse:
    """Response from prediction service"""
    predictions: List[PredictionResult]
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    models_used: List[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None

class ModelRegistry:
    """Registry for managing model instances and their metadata"""
    
    def __init__(self):
        self._models: Dict[str, BasePredictorInterface] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
    def register_model(self, model: BasePredictorInterface, metadata: Optional[Dict[str, Any]] = None):
        """Register a model with optional metadata"""
        with self._lock:
            model_name = model.config.model_name
            self._models[model_name] = model
            self._metadata[model_name] = metadata or {}
            self._metadata[model_name].update({
                'registered_at': pd.Timestamp.now().isoformat(),
                'model_type': model.config.model_type.value,
                'training_required': model.config.training_required
            })
            logger.info(f"✅ Model registered: {model_name}")
    
    def get_model(self, model_name: str) -> Optional[BasePredictorInterface]:
        """Get a model by name"""
        with self._lock:
            return self._models.get(model_name)
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """List all registered models with metadata"""
        with self._lock:
            return {
                name: {
                    **self._metadata[name],
                    **model.get_model_info()
                }
                for name, model in self._models.items()
            }
    
    def remove_model(self, model_name: str) -> bool:
        """Remove a model from registry"""
        with self._lock:
            if model_name in self._models:
                del self._models[model_name]
                del self._metadata[model_name]
                logger.info(f"🗑️ Model removed: {model_name}")
                return True
            return False
    
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all models"""
        with self._lock:
            return {name: model.health_check() for name, model in self._models.items()}

class PredictionCache:
    """Simple in-memory cache for predictions"""
    
    def __init__(self, duration: int = 3600):
        self.cache: Dict[str, Any] = {}
        self.duration = duration
        self._lock = threading.RLock()
    
    def _generate_key(self, request: PredictionRequest, historical_hash: str) -> str:
        """Generate cache key from request and data"""
        key_data = {
            'quantity': request.quantity,
            'models': sorted(request.models or []),
            'context': request.context,
            'data_hash': historical_hash
        }
        return str(hash(str(sorted(key_data.items()))))
    
    def get(self, key: str) -> Optional[PredictionResponse]:
        """Get cached prediction"""
        with self._lock:
            if key in self.cache:
                cached_data, timestamp = self.cache[key]
                if time.time() - timestamp < self.duration:
                    return cached_data
                else:
                    del self.cache[key]
            return None
    
    def set(self, key: str, response: PredictionResponse):
        """Cache prediction response"""
        with self._lock:
            self.cache[key] = (response, time.time())
    
    def clear(self):
        """Clear cache"""
        with self._lock:
            self.cache.clear()

class PredictionService:
    """Main prediction service with dependency injection"""
    
    def __init__(self, config: ServiceConfig = None):
        self.config = config or ServiceConfig()
        self.registry = ModelRegistry()
        self.cache = PredictionCache(self.config.cache_duration) if self.config.enable_caching else None
        self.historical_data: Optional[np.ndarray] = None
        self.data_hash: Optional[str] = None
        self._lock = threading.RLock()
        self.metrics = {
            'total_requests': 0,
            'successful_predictions': 0,
            'failed_predictions': 0,
            'cache_hits': 0,
            'average_response_time': 0.0
        }
        
        logger.info("🚀 Prediction Service initialized")
    
    def load_historical_data(self, data: Union[pd.DataFrame, np.ndarray, List[List[int]]]) -> bool:
        """Load historical data for all models"""
        try:
            # Convert to numpy array
            if isinstance(data, pd.DataFrame):
                self.historical_data = data.values
            elif isinstance(data, list):
                self.historical_data = np.array(data)
            else:
                self.historical_data = data
            
            # Generate data hash for caching
            self.data_hash = str(hash(self.historical_data.tobytes()))
            
            # Initialize all models
            initialization_results = {}
            for model_name, model in self.registry._models.items():
                try:
                    result = model.initialize(self.historical_data)
                    initialization_results[model_name] = result
                    if result and model.config.training_required:
                        model.train(self.historical_data)
                    logger.info(f"{'✅' if result else '❌'} {model_name}: {result}")
                except Exception as e:
                    initialization_results[model_name] = False
                    logger.error(f"❌ {model_name} failed: {e}")
            
            logger.info(f"📊 Data loaded: {self.historical_data.shape[0]} samples")
            return any(initialization_results.values())
            
        except Exception as e:
            logger.error(f"❌ Failed to load historical data: {e}")
            return False
    
    def register_model_factory(self, model_name: str, custom_params: Optional[Dict[str, Any]] = None):
        """Register model from factory"""
        try:
            model = ModelFactory.create_model(model_name, custom_params)
            self.registry.register_model(model)
            
            # Initialize with existing data if available
            if self.historical_data is not None:
                model.initialize(self.historical_data)
                if model.config.training_required:
                    model.train(self.historical_data)
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to register model {model_name}: {e}")
            return False
    
    def predict(self, request: PredictionRequest) -> PredictionResponse:
        """Main prediction method with service orchestration"""
        start_time = time.time()
        self.metrics['total_requests'] += 1
        
        try:
            # Check cache if enabled
            if self.cache and self.data_hash:
                cache_key = self.cache._generate_key(request, self.data_hash)
                cached_response = self.cache.get(cache_key)
                if cached_response:
                    self.metrics['cache_hits'] += 1
                    logger.info("📦 Cache hit for prediction request")
                    return cached_response
            
            # Determine models to use
            models_to_use = self._select_models(request)
            if not models_to_use:
                return PredictionResponse(
                    predictions=[],
                    success=False,
                    error_message="No suitable models available"
                )
            
            # Execute predictions
            all_predictions = []
            models_used = []
            
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                # Submit prediction tasks
                futures = {}
                for model_name in models_to_use:
                    model = self.registry.get_model(model_name)
                    if model and model.health_check()["ready_for_prediction"]:
                        future = executor.submit(
                            self._safe_predict, 
                            model, 
                            request.quantity // len(models_to_use), 
                            request.context
                        )
                        futures[future] = model_name
                
                # Collect results
                timeout = request.timeout or self.config.prediction_timeout
                for future in as_completed(futures, timeout=timeout):
                    model_name = futures[future]
                    try:
                        predictions = future.result()
                        if predictions:
                            all_predictions.extend(predictions)
                            models_used.append(model_name)
                            logger.info(f"✅ {model_name}: {len(predictions)} predictions")
                    except Exception as e:
                        logger.error(f"❌ {model_name} prediction failed: {e}")
            
            # Handle insufficient predictions
            if len(all_predictions) < request.quantity and request.enable_fallback:
                needed = request.quantity - len(all_predictions)
                fallback_predictions = self._generate_fallback_predictions(needed)
                all_predictions.extend(fallback_predictions)
                models_used.append("fallback")
            
            # Sort by score and take top predictions
            all_predictions.sort(key=lambda x: x.score, reverse=True)
            final_predictions = all_predictions[:request.quantity]
            
            # Create response
            execution_time = time.time() - start_time
            response = PredictionResponse(
                predictions=final_predictions,
                metadata={
                    'total_generated': len(all_predictions),
                    'models_available': len(models_to_use),
                    'cache_enabled': self.config.enable_caching,
                    'request_timestamp': pd.Timestamp.now().isoformat()
                },
                execution_time=execution_time,
                models_used=models_used,
                success=True
            )
            
            # Cache response
            if self.cache and self.data_hash:
                self.cache.set(cache_key, response)
            
            # Update metrics
            self.metrics['successful_predictions'] += 1
            self._update_average_response_time(execution_time)
            
            logger.info(f"✅ Prediction completed: {len(final_predictions)} results in {execution_time:.2f}s")
            return response
            
        except Exception as e:
            self.metrics['failed_predictions'] += 1
            logger.error(f"❌ Prediction service error: {e}")
            return PredictionResponse(
                predictions=[],
                execution_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    def _select_models(self, request: PredictionRequest) -> List[str]:
        """Select appropriate models for the request"""
        if request.models:
            # Use specified models
            available_models = [name for name in request.models 
                             if self.registry.get_model(name) is not None]
            return available_models
        
        # Auto-select based on model health and performance
        healthy_models = []
        for model_name, health in self.registry.health_check_all().items():
            if health["ready_for_prediction"]:
                healthy_models.append(model_name)
        
        return healthy_models
    
    def _safe_predict(self, model: BasePredictorInterface, quantity: int, 
                     context: Optional[Dict[str, Any]]) -> List[PredictionResult]:
        """Safe prediction wrapper with error handling"""
        try:
            return model.predict(quantity, context)
        except Exception as e:
            logger.error(f"❌ Model {model.config.model_name} prediction error: {e}")
            return []
    
    def _generate_fallback_predictions(self, quantity: int) -> List[PredictionResult]:
        """Generate fallback predictions when models fail"""
        import random
        
        predictions = []
        for i in range(quantity):
            combination = sorted(random.sample(range(1, 41), 6))
            prediction = PredictionResult(
                combination=combination,
                score=0.3,
                confidence=0.2,
                source="service_fallback",
                metrics={"type": "fallback"},
                execution_time=0.0
            )
            predictions.append(prediction)
        
        logger.warning(f"⚠️ Generated {quantity} fallback predictions")
        return predictions
    
    def _update_average_response_time(self, execution_time: float):
        """Update average response time metric"""
        total_requests = self.metrics['total_requests']
        current_avg = self.metrics['average_response_time']
        self.metrics['average_response_time'] = (
            (current_avg * (total_requests - 1) + execution_time) / total_requests
        )
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics"""
        return {
            **self.metrics,
            'models_registered': len(self.registry._models),
            'cache_size': len(self.cache.cache) if self.cache else 0,
            'uptime': time.time(),  # Simplified uptime
            'data_loaded': self.historical_data is not None
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive service health check"""
        return {
            'service_status': 'healthy',
            'data_loaded': self.historical_data is not None,
            'models_ready': len([
                name for name, health in self.registry.health_check_all().items()
                if health["ready_for_prediction"]
            ]),
            'models_total': len(self.registry._models),
            'cache_enabled': self.config.enable_caching,
            'metrics': self.get_service_metrics()
        }

# Utility functions for service setup
def create_prediction_service(config: Optional[ServiceConfig] = None) -> PredictionService:
    """Create a new prediction service instance"""
    return PredictionService(config)

def setup_standard_models(service: PredictionService) -> bool:
    """Setup standard OMEGA models in the service"""
    try:
        # Register LSTM adapter
        from modules.adapters.lstm_adapter import register_lstm_model
        register_lstm_model()
        service.register_model_factory("lstm_v2")
        
        # Add more models as they get adapted...
        
        logger.info("✅ Standard models setup completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to setup standard models: {e}")
        return False

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Prediction Service...")
    
    # Create service
    service = create_prediction_service()
    
    # Setup models
    setup_standard_models(service)
    
    # Load sample data
    sample_data = np.random.randint(1, 41, size=(200, 6))
    service.load_historical_data(sample_data)
    
    # Test prediction
    request = PredictionRequest(quantity=10)
    response = service.predict(request)
    
    print(f"✅ Prediction successful: {response.success}")
    print(f"📊 Generated: {len(response.predictions)} predictions")
    print(f"⏱️ Execution time: {response.execution_time:.2f}s")
    print(f"🤖 Models used: {response.models_used}")
    
    # Health check
    health = service.health_check()
    print(f"❤️ Service health: {health['service_status']}")
    
    print("🏁 Prediction Service test completed")