#!/usr/bin/env python3
"""
LSTM Model Adapter for Unified Interface
Adapts existing LSTM model to the standardized interface
"""

import time
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import numpy as np
import logging

from modules.interfaces.predictor_interface import (
    BasePredictorInterface, ModelConfig, ModelType, PredictionResult,
    validate_combination, clean_combination
)

logger = logging.getLogger(__name__)

class LSTMModelAdapter(BasePredictorInterface):
    """Adapter for LSTM model to unified interface"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.historical_data = None
        self.historial_set = None
        self.lstm_config = {
            'n_steps': config.parameters.get('n_steps', 5),
            'epochs': config.parameters.get('epochs', 20),
            'batch_size': config.parameters.get('batch_size', 16),
            'min_history': config.parameters.get('min_history', 100),
            'seed': config.parameters.get('seed', 42)
        }
    
    def initialize(self, historical_data: Union[pd.DataFrame, np.ndarray, List[List[int]]]) -> bool:
        """Initialize LSTM model with historical data"""
        try:
            # Convert data to appropriate format
            if isinstance(historical_data, pd.DataFrame):
                self.historical_data = historical_data.values
            elif isinstance(historical_data, list):
                self.historical_data = np.array(historical_data)
            else:
                self.historical_data = historical_data
            
            # Validate data
            if not self.validate_input(self.historical_data):
                return False
            
            # Create historial_set for LSTM
            historial = self.historical_data.tolist()
            self.historial_set = {tuple(sorted(map(int, d))) for d in historial}
            
            self.is_initialized = True
            self.logger.info(f"✅ LSTM initialized with {len(self.historical_data)} samples")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ LSTM initialization failed: {e}")
            return False
    
    def train(self, training_data: Union[pd.DataFrame, np.ndarray, List[List[int]]], 
              labels: Optional[List[Any]] = None) -> bool:
        """LSTM doesn't require explicit training - uses data directly"""
        try:
            # LSTM model uses historical data directly for predictions
            # No separate training phase required
            self.is_trained = True
            self.logger.info("✅ LSTM training completed (data-driven model)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ LSTM training failed: {e}")
            return False
    
    def predict(self, quantity: int = 30, context: Optional[Dict[str, Any]] = None) -> List[PredictionResult]:
        """Generate LSTM predictions"""
        if not self.is_initialized:
            self.logger.error("❌ LSTM not initialized")
            return []
        
        start_time = time.time()
        results = []
        
        try:
            # Import LSTM model function
            from modules.lstm_model import generar_combinaciones_lstm
            
            # Check minimum data requirement
            if self.historical_data.shape[0] < self.lstm_config['min_history']:
                self.logger.warning(f"⚠️ Insufficient data for LSTM: {self.historical_data.shape[0]} < {self.lstm_config['min_history']}")
                return self._generate_fallback_predictions(quantity, start_time)
            
            if self.historical_data.shape[0] < self.lstm_config['n_steps'] + 1:
                self.logger.warning(f"⚠️ Insufficient sequence length for LSTM")
                return self._generate_fallback_predictions(quantity, start_time)
            
            # Call original LSTM function
            raw_predictions = generar_combinaciones_lstm(
                data=self.historical_data,
                cantidad=quantity,
                historial_set=self.historial_set,
                logger=self.logger,
                config=self.lstm_config
            )
            
            # Convert to standardized format
            execution_time = time.time() - start_time
            
            for item in raw_predictions:
                combination = clean_combination(item.get("combination", []), self.logger)
                if combination and validate_combination(combination):
                    result = PredictionResult(
                        combination=combination,
                        score=item.get("score", 1.0),
                        confidence=min(item.get("score", 1.0), 1.0),  # Normalize to [0,1]
                        source=f"lstm_v2_{self.config.model_name}",
                        metrics=item.get("metrics", {}),
                        execution_time=execution_time,
                        normalized_score=0.0  # Will be set by scoring system
                    )
                    results.append(result)
            
            self.logger.info(f"✅ LSTM generated {len(results)} valid predictions in {execution_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"❌ LSTM prediction failed: {e}")
            results = self._generate_fallback_predictions(quantity, start_time)
        
        return results[:quantity]  # Ensure we don't exceed requested quantity
    
    def validate_input(self, data: Union[pd.DataFrame, np.ndarray, List[List[int]]]) -> bool:
        """Validate input data for LSTM"""
        try:
            if isinstance(data, pd.DataFrame):
                data_array = data.values
            elif isinstance(data, list):
                data_array = np.array(data)
            else:
                data_array = data
            
            # Check shape
            if len(data_array.shape) != 2:
                return False
            
            if data_array.shape[1] < 6:
                return False
            
            # Check data ranges
            if data_array.min() < 1 or data_array.max() > 40:
                return False
            
            # Check for NaN or infinite values
            if np.isnan(data_array).any() or np.isinf(data_array).any():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Input validation failed: {e}")
            return False
    
    def _generate_fallback_predictions(self, quantity: int, start_time: float) -> List[PredictionResult]:
        """Generate fallback predictions when LSTM fails"""
        import random
        
        results = []
        execution_time = time.time() - start_time
        
        for i in range(min(quantity, 5)):  # Limit fallbacks
            combination = sorted(random.sample(range(1, 41), 6))
            result = PredictionResult(
                combination=combination,
                score=0.5,
                confidence=0.3,  # Low confidence for fallback
                source=f"lstm_fallback_{self.config.model_name}",
                metrics={"fallback_reason": "insufficient_data_or_error"},
                execution_time=execution_time,
                normalized_score=0.0
            )
            results.append(result)
        
        self.logger.warning(f"⚠️ Generated {len(results)} LSTM fallback predictions")
        return results

# Factory registration function
def register_lstm_model():
    """Register LSTM model with the factory"""
    from modules.interfaces.predictor_interface import ModelFactory
    
    config = ModelConfig(
        model_name="lstm_v2",
        model_type=ModelType.SEQUENTIAL,
        parameters={
            'n_steps': 5,
            'epochs': 20,
            'batch_size': 16,
            'min_history': 100,
            'seed': 42
        },
        training_required=False,  # Data-driven, no explicit training
        min_data_size=100,
        max_combinations=500,
        timeout_seconds=300
    )
    
    ModelFactory.register_model(LSTMModelAdapter, config)
    logger.info("✅ LSTM model registered with unified interface")

# Example usage
if __name__ == "__main__":
    # Register the model
    register_lstm_model()
    
    # Create model instance
    from modules.interfaces.predictor_interface import ModelFactory
    lstm_model = ModelFactory.create_model("lstm_v2")
    
    # Example data
    sample_data = np.random.randint(1, 41, size=(150, 6))
    
    # Test model workflow
    print("🧪 Testing LSTM Adapter...")
    
    # Initialize
    if lstm_model.initialize(sample_data):
        print("✅ Initialization successful")
        
        # Train (no-op for LSTM)
        if lstm_model.train(sample_data):
            print("✅ Training successful")
            
            # Predict
            predictions = lstm_model.predict(10)
            print(f"✅ Generated {len(predictions)} predictions")
            
            for i, pred in enumerate(predictions[:3]):
                print(f"   {i+1}: {pred.combination} (score: {pred.score:.3f})")
        
        # Health check
        health = lstm_model.health_check()
        print(f"📊 Health: {health['status']}")
    
    print("🏁 LSTM Adapter test completed")