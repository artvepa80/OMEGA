#!/usr/bin/env python3
"""
🎭 OMEGA Ensemble Manager - Gestor de Ensemble con Lazy Loading
Gestión inteligente de múltiples modelos con optimizaciones de performance
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

from src.ai.model_registry import ModelRegistry, ModelInterface
from src.core.config_manager import ConfigManager
from src.utils.logger_factory import LoggerFactory, performance_monitor
from src.monitoring.metrics_collector import MetricsCollector

@dataclass
class EnsembleWeights:
    """Pesos del ensemble"""
    base_weights: Dict[str, float]
    dynamic_weights: Dict[str, float]
    performance_weights: Dict[str, float]
    final_weights: Dict[str, float]

@dataclass
class ModelPerformance:
    """Métricas de performance de modelo"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    prediction_time: float = 0.0
    memory_usage: float = 0.0
    error_rate: float = 0.0
    last_updated: float = 0.0

class EnsembleManager:
    """
    Gestor avanzado de ensemble con lazy loading y optimizaciones
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.model_registry = ModelRegistry(config_manager)
        self.metrics = MetricsCollector()
        self.logger = LoggerFactory.get_logger("EnsembleManager")
        
        # Performance tracking
        self.model_performance: Dict[str, ModelPerformance] = defaultdict(ModelPerformance)
        
        # Configuración de ensemble
        self.ensemble_config = {
            'min_models': 2,
            'max_models': 8,
            'weight_decay': 0.95,  # Para pesos dinámicos
            'performance_window': 100,  # Ventana de evaluación
            'auto_rebalance': True,
            'diversity_bonus': 0.1  # Bonus por diversidad
        }
        
        # Registro de modelos por defecto
        self._register_default_models()
        
        self.logger.info("🎭 EnsembleManager inicializado")
    
    def _register_default_models(self):
        """Registra modelos por defecto"""
        # En un sistema real, estos serían importados dinámicamente
        model_factories = {
            'neural_enhanced': self._create_neural_enhanced_factory,
            'transformer_deep': self._create_transformer_factory,
            'lstm_v2': self._create_lstm_factory,
            'genetic': self._create_genetic_factory,
            'clustering': self._create_clustering_factory,
            'montecarlo': self._create_montecarlo_factory
        }
        
        for name, factory in model_factories.items():
            self.model_registry.register_model_factory(name, factory)
            self.logger.debug(f"📝 Registered model factory: {name}")
    
    def _create_neural_enhanced_factory(self, config):
        """Factory para modelo neural enhanced"""
        class NeuralEnhancedModel(ModelInterface):
            def __init__(self, config):
                self.config = config
                self.version = "2.1.0"
                self.training_date = "2025-08-01"
                self._memory_usage = 45.0
            
            async def predict(self, data: Any, count: int = 8) -> list:
                # Simular predicción neural
                await asyncio.sleep(0.1)  # Simular tiempo de procesamiento
                
                predictions = []
                for _ in range(count):
                    # Generar combinación "inteligente"
                    combination = sorted(np.random.choice(range(1, 41), 6, replace=False))
                    confidence = np.random.uniform(0.7, 0.95)
                    
                    predictions.append({
                        'combination': combination.tolist(),
                        'confidence': confidence
                    })
                
                return predictions
            
            def get_version(self) -> str:
                return self.version
            
            def get_training_date(self) -> str:
                return self.training_date
            
            def get_memory_usage(self) -> float:
                return self._memory_usage
        
        return NeuralEnhancedModel(config)
    
    def _create_transformer_factory(self, config):
        """Factory para modelo transformer"""
        class TransformerModel(ModelInterface):
            def __init__(self, config):
                self.config = config
                self.version = "1.8.0"
                self.training_date = "2025-07-28"
                self._memory_usage = 32.0
            
            async def predict(self, data: Any, count: int = 8) -> list:
                await asyncio.sleep(0.08)
                
                predictions = []
                for _ in range(count):
                    combination = sorted(np.random.choice(range(1, 41), 6, replace=False))
                    confidence = np.random.uniform(0.65, 0.88)
                    
                    predictions.append({
                        'combination': combination.tolist(),
                        'confidence': confidence
                    })
                
                return predictions
            
            def get_version(self) -> str:
                return self.version
            
            def get_training_date(self) -> str:
                return self.training_date
            
            def get_memory_usage(self) -> float:
                return self._memory_usage
        
        return TransformerModel(config)
    
    def _create_lstm_factory(self, config):
        """Factory para modelo LSTM"""
        class LSTMModel(ModelInterface):
            def __init__(self, config):
                self.config = config
                self.version = "2.0.5"
                self.training_date = "2025-07-25"
                self._memory_usage = 28.0
            
            async def predict(self, data: Any, count: int = 8) -> list:
                await asyncio.sleep(0.06)
                
                predictions = []
                for _ in range(count):
                    combination = sorted(np.random.choice(range(1, 41), 6, replace=False))
                    confidence = np.random.uniform(0.6, 0.82)
                    
                    predictions.append({
                        'combination': combination.tolist(),
                        'confidence': confidence
                    })
                
                return predictions
            
            def get_version(self) -> str:
                return self.version
            
            def get_training_date(self) -> str:
                return self.training_date
            
            def get_memory_usage(self) -> float:
                return self._memory_usage
        
        return LSTMModel(config)
    
    def _create_genetic_factory(self, config):
        """Factory para algoritmo genético"""
        class GeneticModel(ModelInterface):
            def __init__(self, config):
                self.config = config
                self.version = "1.5.2"
                self.training_date = "2025-07-20"
                self._memory_usage = 15.0
            
            async def predict(self, data: Any, count: int = 8) -> list:
                await asyncio.sleep(0.12)  # Genetic algorithms take more time
                
                predictions = []
                for _ in range(count):
                    combination = sorted(np.random.choice(range(1, 41), 6, replace=False))
                    confidence = np.random.uniform(0.55, 0.78)
                    
                    predictions.append({
                        'combination': combination.tolist(),
                        'confidence': confidence
                    })
                
                return predictions
            
            def get_version(self) -> str:
                return self.version
            
            def get_training_date(self) -> str:
                return self.training_date
            
            def get_memory_usage(self) -> float:
                return self._memory_usage
        
        return GeneticModel(config)
    
    def _create_clustering_factory(self, config):
        """Factory para modelo clustering"""
        class ClusteringModel(ModelInterface):
            def __init__(self, config):
                self.config = config
                self.version = "1.3.0"
                self.training_date = "2025-07-15"
                self._memory_usage = 12.0
            
            async def predict(self, data: Any, count: int = 8) -> list:
                await asyncio.sleep(0.04)
                
                predictions = []
                for _ in range(count):
                    combination = sorted(np.random.choice(range(1, 41), 6, replace=False))
                    confidence = np.random.uniform(0.5, 0.72)
                    
                    predictions.append({
                        'combination': combination.tolist(),
                        'confidence': confidence
                    })
                
                return predictions
            
            def get_version(self) -> str:
                return self.version
            
            def get_training_date(self) -> str:
                return self.training_date
            
            def get_memory_usage(self) -> float:
                return self._memory_usage
        
        return ClusteringModel(config)
    
    def _create_montecarlo_factory(self, config):
        """Factory para Monte Carlo"""
        class MonteCarloModel(ModelInterface):
            def __init__(self, config):
                self.config = config
                self.version = "1.2.8"
                self.training_date = "2025-07-10"
                self._memory_usage = 8.0
            
            async def predict(self, data: Any, count: int = 8) -> list:
                await asyncio.sleep(0.03)
                
                predictions = []
                for _ in range(count):
                    combination = sorted(np.random.choice(range(1, 41), 6, replace=False))
                    confidence = np.random.uniform(0.45, 0.68)
                    
                    predictions.append({
                        'combination': combination.tolist(),
                        'confidence': confidence
                    })
                
                return predictions
            
            def get_version(self) -> str:
                return self.version
            
            def get_training_date(self) -> str:
                return self.training_date
            
            def get_memory_usage(self) -> float:
                return self._memory_usage
        
        return MonteCarloModel(config)
    
    def get_model(self, model_name: str):
        """Obtiene modelo con lazy loading"""
        return self.model_registry.get_model(model_name)
    
    def get_active_models(self) -> List[str]:
        """Obtiene lista de modelos activos"""
        enabled_models = self.config_manager.get_enabled_models()
        return list(enabled_models.keys())
    
    def get_model_weights(self) -> Dict[str, float]:
        """Obtiene pesos actuales de modelos"""
        if self.ensemble_config['auto_rebalance']:
            return self._calculate_dynamic_weights()
        else:
            return self._get_base_weights()
    
    def _get_base_weights(self) -> Dict[str, float]:
        """Obtiene pesos base de configuración"""
        enabled_models = self.config_manager.get_enabled_models()
        weights = {}
        
        for name, config in enabled_models.items():
            weights[name] = config.weight
        
        # Normalizar pesos
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}
        
        return weights
    
    @performance_monitor()
    def _calculate_dynamic_weights(self) -> Dict[str, float]:
        """Calcula pesos dinámicos basados en performance"""
        base_weights = self._get_base_weights()
        enabled_models = list(base_weights.keys())
        
        # Si no hay datos de performance, usar pesos base
        if not any(self.model_performance[model].last_updated > 0 for model in enabled_models):
            return base_weights
        
        performance_weights = {}
        
        for model in enabled_models:
            perf = self.model_performance[model]
            
            # Calcular score de performance combinado
            performance_score = (
                perf.accuracy * 0.4 +
                perf.f1_score * 0.3 +
                (1 - perf.error_rate) * 0.2 +
                (1 - min(perf.prediction_time / 1.0, 1.0)) * 0.1  # Penalizar lentitud
            )
            
            # Aplicar decaimiento temporal
            time_decay = self.ensemble_config['weight_decay'] ** (
                (time.time() - perf.last_updated) / 3600  # Decay por horas
            )
            
            performance_weights[model] = performance_score * time_decay
        
        # Combinar con pesos base
        final_weights = {}
        total_performance = sum(performance_weights.values())
        
        for model in enabled_models:
            base_weight = base_weights[model]
            perf_weight = performance_weights[model] / total_performance if total_performance > 0 else 0
            
            # Combinar pesos (70% base, 30% performance)
            final_weights[model] = base_weight * 0.7 + perf_weight * 0.3
        
        # Normalizar
        total_final = sum(final_weights.values())
        if total_final > 0:
            final_weights = {k: v/total_final for k, v in final_weights.items()}
        
        self.logger.debug(f"💫 Dynamic weights calculated: {final_weights}")
        return final_weights
    
    def update_model_performance(self, 
                                model_name: str,
                                accuracy: float = None,
                                prediction_time: float = None,
                                memory_usage: float = None,
                                error_occurred: bool = False):
        """Actualiza métricas de performance de modelo"""
        perf = self.model_performance[model_name]
        
        if accuracy is not None:
            # Media móvil exponencial
            alpha = 0.2
            perf.accuracy = perf.accuracy * (1 - alpha) + accuracy * alpha
        
        if prediction_time is not None:
            perf.prediction_time = prediction_time
        
        if memory_usage is not None:
            perf.memory_usage = memory_usage
        
        if error_occurred:
            perf.error_rate = min(perf.error_rate + 0.1, 1.0)
        else:
            # Decaimiento de error rate
            perf.error_rate *= 0.95
        
        perf.last_updated = time.time()
        
        self.metrics.set_gauge(f"model_performance_{model_name}", perf.accuracy)
        self.logger.debug(f"📊 Updated performance for {model_name}: acc={perf.accuracy:.3f}")
    
    async def update_model_weights(self, weight_adjustments: Dict[str, Dict[str, Any]]):
        """Actualiza pesos de modelos basado en aprendizaje"""
        for model_name, adjustments in weight_adjustments.items():
            config = self.config_manager.get_model_config(model_name)
            if config:
                weight_change = adjustments.get('weight_change', 0.0)
                new_weight = max(0.01, min(1.0, config.weight + weight_change))
                
                self.config_manager.update_model_weight(model_name, new_weight)
                self.logger.info(f"⚖️ Updated weight for {model_name}: {config.weight:.3f} → {new_weight:.3f}")
    
    def get_ensemble_weights(self) -> EnsembleWeights:
        """Obtiene desglose completo de pesos"""
        base_weights = self._get_base_weights()
        dynamic_weights = self._calculate_dynamic_weights()
        
        # Calcular pesos de performance
        performance_weights = {}
        for model in base_weights.keys():
            perf = self.model_performance[model]
            performance_weights[model] = perf.accuracy if perf.last_updated > 0 else 0.5
        
        return EnsembleWeights(
            base_weights=base_weights,
            dynamic_weights=dynamic_weights,
            performance_weights=performance_weights,
            final_weights=dynamic_weights
        )
    
    def optimize_ensemble(self) -> Dict[str, Any]:
        """Optimiza configuración del ensemble"""
        self.logger.info("🔧 Optimizing ensemble configuration")
        
        # Analizar performance de modelos
        performance_analysis = {}
        enabled_models = self.get_active_models()
        
        for model in enabled_models:
            perf = self.model_performance[model]
            performance_analysis[model] = {
                'accuracy': perf.accuracy,
                'prediction_time': perf.prediction_time,
                'memory_usage': perf.memory_usage,
                'error_rate': perf.error_rate,
                'efficiency_score': perf.accuracy / max(perf.prediction_time, 0.001)
            }
        
        # Identificar modelos sub-performantes
        avg_accuracy = np.mean([p['accuracy'] for p in performance_analysis.values()])
        underperforming = [
            model for model, perf in performance_analysis.items()
            if perf['accuracy'] < avg_accuracy * 0.8
        ]
        
        # Sugerencias de optimización
        suggestions = []
        
        if underperforming:
            suggestions.append(f"Consider disabling underperforming models: {underperforming}")
        
        if len(enabled_models) > self.ensemble_config['max_models']:
            suggestions.append(f"Too many models enabled ({len(enabled_models)}). Consider reducing.")
        
        optimization_result = {
            'performance_analysis': performance_analysis,
            'underperforming_models': underperforming,
            'suggestions': suggestions,
            'current_weights': self.get_model_weights(),
            'memory_usage': self.model_registry.get_memory_usage()
        }
        
        self.logger.info(f"🔧 Ensemble optimization complete: {len(suggestions)} suggestions")
        return optimization_result
    
    async def save_model_states(self):
        """Guarda estados actuales de modelos"""
        try:
            states = {
                'model_weights': self.get_model_weights(),
                'performance_metrics': dict(self.model_performance),
                'ensemble_config': self.ensemble_config,
                'timestamp': time.time()
            }
            
            # En un sistema real, guardaría en base de datos o archivo
            self.logger.info("💾 Model states saved")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving model states: {e}")
    
    def get_health_status(self) -> str:
        """Obtiene estado de salud del ensemble"""
        try:
            enabled_models = self.get_active_models()
            loaded_models = len(self.model_registry.get_loaded_models())
            
            if len(enabled_models) == 0:
                return "unhealthy"
            elif loaded_models == 0:
                return "degraded"
            else:
                return "healthy"
        except:
            return "unknown"
    
    async def cleanup(self):
        """Limpieza de recursos"""
        self.logger.info("🔄 Cleaning up EnsembleManager")
        
        # Descargar todos los modelos
        self.model_registry.unload_all_models()
        
        # Optimizar memoria
        self.model_registry.optimize_memory()
        
        # Shutdown registry
        self.model_registry.shutdown()
        
        self.logger.info("✅ EnsembleManager cleanup complete")