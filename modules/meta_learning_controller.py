# modules/meta_learning_controller.py
"""
Meta-Learning Controller - High-level intelligent orchestration system
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class LotteryRegime(Enum):
    HIGH_FREQUENCY_LOW_VARIANCE = "high_frequency_low_variance"
    LOW_FREQUENCY_HIGH_VARIANCE = "low_frequency_high_variance"
    BALANCED = "balanced"
    EXPLORATORY = "exploratory"

class ContextRegime(Enum):
    """Regímenes de contexto identificados"""
    REGIME_A = "high_frequency_low_variance"  # Alta frecuencia, baja varianza
    REGIME_B = "moderate_balanced"           # Moderado balanceado
    REGIME_C = "low_frequency_high_variance" # Baja frecuencia, alta varianza
    REGIME_UNKNOWN = "unknown"

@dataclass
class LotteryContext:
    regime: LotteryRegime
    entropy: float
    variance: float
    trend_strength: float
    confidence: float

@dataclass
class ModelPerformance:
    """Registro de performance de un modelo"""
    model_name: str
    regime: ContextRegime
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    timestamp: datetime
    context_features: Dict[str, float]

class MetaLearningController:
    """Meta-Learning Controller for intelligent model orchestration"""
    
    def __init__(self, memory_size: int = 1000):
        self.memory_size = memory_size
        self.historical_contexts = []
        self.performance_history = []
        self.logger = logging.getLogger(__name__)
        
        # Available models and their dynamic weights
        self.available_models = {
            'lstm_v2': {'weight': 1.0, 'specialty': 'temporal_patterns'},
            'transformer': {'weight': 1.0, 'specialty': 'attention_patterns'},
            'clustering': {'weight': 1.0, 'specialty': 'group_patterns'},
            'montecarlo': {'weight': 1.0, 'specialty': 'probabilistic'},
            'genetic': {'weight': 1.0, 'specialty': 'evolutionary'},
            'gboost': {'weight': 1.0, 'specialty': 'gradient_boosting'},
            'ensemble_ai': {'weight': 1.5, 'specialty': 'meta_ensemble'}
        }
    
    def analyze_context(self, historical_data: List[List[int]]) -> LotteryContext:
        """Analyze lottery data context"""
        try:
            # Flatten historical data
            all_numbers = [num for combo in historical_data for num in combo]
            
            # Calculate entropy
            from collections import Counter
            freq = Counter(all_numbers)
            probs = np.array(list(freq.values())) / len(all_numbers)
            entropy = -np.sum(probs * np.log2(probs + 1e-10))
            
            # Calculate variance
            variance = np.var(all_numbers)
            
            # Calculate trend strength (simplified)
            recent_numbers = all_numbers[-30:] if len(all_numbers) >= 30 else all_numbers
            trend_strength = len(set(recent_numbers)) / len(recent_numbers) if recent_numbers else 0.5
            
            # Determine regime
            if entropy > 3.5 and variance < 100:
                regime = LotteryRegime.HIGH_FREQUENCY_LOW_VARIANCE
            elif entropy < 3.0 and variance > 150:
                regime = LotteryRegime.LOW_FREQUENCY_HIGH_VARIANCE
            elif trend_strength > 0.8:
                regime = LotteryRegime.EXPLORATORY
            else:
                regime = LotteryRegime.BALANCED
            
            # Calculate confidence
            confidence = min(0.95, 0.5 + (entropy / 10) + (trend_strength * 0.3))
            
            return LotteryContext(
                regime=regime,
                entropy=entropy,
                variance=variance,
                trend_strength=trend_strength,
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.warning(f"Context analysis failed: {e}")
            return LotteryContext(
                regime=LotteryRegime.BALANCED,
                entropy=3.0,
                variance=100.0,
                trend_strength=0.5,
                confidence=0.5
            )
    
    def optimize_weights(self, context: LotteryContext) -> Dict[str, float]:
        """Optimize model weights based on context"""
        
        # Base weights
        base_weights = {
            'lstm': 1.0,
            'transformer': 1.0,
            'ensemble': 1.0,
            'clustering': 1.0,
            'genetic': 1.0
        }
        
        # Adjust based on regime
        if context.regime == LotteryRegime.HIGH_FREQUENCY_LOW_VARIANCE:
            base_weights['lstm'] = 1.2
            base_weights['clustering'] = 1.1
        elif context.regime == LotteryRegime.LOW_FREQUENCY_HIGH_VARIANCE:
            base_weights['genetic'] = 1.3
            base_weights['ensemble'] = 1.2
        elif context.regime == LotteryRegime.EXPLORATORY:
            base_weights['transformer'] = 1.3
            base_weights['ensemble'] = 1.4
        
        # Normalize weights
        total_weight = sum(base_weights.values())
        normalized_weights = {k: v/total_weight for k, v in base_weights.items()}
        
        return normalized_weights
    
    def _get_regime_based_weights(self, regime, entropy=None, trend_strength=None) -> Dict[str, float]:
        """Obtiene pesos basados en reglas por régimen - compatible con ContextRegime y LotteryRegime"""
        base_weights = {model: data['weight'] for model, data in self.available_models.items()}
        
        # Handle both LotteryRegime and ContextRegime enums
        regime_value = regime.value if hasattr(regime, 'value') else str(regime)
        
        if regime_value in ["high_frequency_low_variance", "REGIME_A"]:
            # Régimen A: Favorece modelos de patrones secuenciales
            base_weights['lstm_v2'] *= 1.5
            base_weights['transformer'] *= 1.3
            base_weights['clustering'] *= 0.8
            base_weights['montecarlo'] *= 0.7
            
        elif regime_value in ["low_frequency_high_variance", "REGIME_C"]:
            # Régimen C: Favorece modelos probabilísticos y evolutivos
            base_weights['montecarlo'] *= 1.4
            base_weights['genetic'] *= 1.3
            base_weights['ensemble_ai'] *= 1.2
            base_weights['lstm_v2'] *= 0.8
            
        elif regime_value == "exploratory":
            # Exploratory regime: favor transformer and ensemble
            base_weights['transformer'] *= 1.3
            base_weights['ensemble_ai'] *= 1.4
        
        # Apply entropy and trend adjustments if provided
        if entropy is not None and trend_strength is not None:
            if entropy > 0.7:
                base_weights['transformer'] *= 1.1
            if trend_strength > 0.5:
                base_weights['lstm_v2'] *= 1.2
                
        self.logger.info(f"📊 Pesos por régimen {regime_value}")
        return base_weights
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de performance del sistema"""
        if not self.performance_history:
            return {
                "error": "No hay datos de performance",
                "total_records": 0,
                "regimes_detected": 0,
                "models_evaluated": 0,
                "is_trained": False,
                "current_weights": self.available_models
            }
        
        summary = {
            "total_records": len(self.performance_history),
            "regimes_detected": len(set(getattr(p, 'regime', 'unknown') for p in self.performance_history)),
            "models_evaluated": len(set(getattr(p, 'model_name', 'unknown') for p in self.performance_history)),
            "is_trained": False,
            "current_weights": self.available_models
        }
        
        # Model statistics
        model_stats = {}
        for model_name in self.available_models.keys():
            model_stats[model_name] = {
                "evaluations": 0,
                "avg_f1": 0.5,
                "current_weight": self.available_models[model_name]['weight']
            }
        
        summary["model_statistics"] = model_stats
        summary["regime_statistics"] = {}
        
        return summary

def create_meta_controller(memory_size: int = 1000) -> MetaLearningController:
    """Create and configure meta-learning controller"""
    return MetaLearningController(memory_size=memory_size)

def analyze_and_optimize(controller: MetaLearningController, 
                        historical_data: List[List[int]]) -> Tuple[LotteryContext, Dict[str, float]]:
    """Analyze context and optimize model weights"""
    context = controller.analyze_context(historical_data)
    optimal_weights = controller.optimize_weights(context)
    return context, optimal_weights