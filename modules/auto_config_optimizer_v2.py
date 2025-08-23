#!/usr/bin/env python3
"""
Auto Config Optimizer v2.0 para OMEGA PRO AI
Versión mejorada con heurísticas avanzadas de evaluación y optimización inteligente
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import json
import os
from pathlib import Path
from sklearn.model_selection import ParameterGrid
from sklearn.metrics import silhouette_score
from collections import defaultdict, deque
import math
import warnings
warnings.filterwarnings("ignore")

# Importar dependencias opcionales
try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

try:
    from modules.utils.validation_enhanced import OmegaValidator, ValidationError
    from modules.utils.error_handling import (
        handle_omega_errors, safe_execute, ConfigurationError, ModelTrainingError
    )
    ENHANCED_MODULES_AVAILABLE = True
except ImportError:
    ENHANCED_MODULES_AVAILABLE = False

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """Estrategias de optimización mejoradas"""
    GRID_SEARCH = "grid_search"
    BAYESIAN = "bayesian" 
    RANDOM_SEARCH = "random_search"
    ADAPTIVE_MULTI_OBJECTIVE = "adaptive_multi_objective"
    EVOLUTIONARY = "evolutionary"
    THOMPSON_SAMPLING = "thompson_sampling"
    CONTEXTUAL_BANDIT = "contextual_bandit"

class PerformanceMetric(Enum):
    """Métricas de rendimiento avanzadas"""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    CONSISTENCY = "consistency"
    DIVERSITY = "diversity"
    COVERAGE = "coverage"
    EFFICIENCY = "efficiency"
    ROBUSTNESS = "robustness"
    ADAPTABILITY = "adaptability"
    STABILITY = "stability"
    CONVERGENCE_RATE = "convergence_rate"

class ContextualFactor(Enum):
    """Factores contextuales para optimización adaptativa"""
    TIME_OF_DAY = "time_of_day"
    DAY_OF_WEEK = "day_of_week"
    HISTORICAL_PERFORMANCE = "historical_performance"
    DATA_REGIME = "data_regime"
    PREDICTION_CONFIDENCE = "prediction_confidence"
    SYSTEM_LOAD = "system_load"
    ERROR_RATE = "error_rate"

@dataclass
class EnhancedOptimizationTarget:
    """Objetivo de optimización mejorado con contexto"""
    parameter_name: str
    current_value: Union[int, float, str]
    min_value: Union[int, float]
    max_value: Union[int, float]
    value_type: str  # 'int', 'float', 'categorical'
    category_options: Optional[List[str]] = None
    importance: float = 1.0
    
    # Nuevos campos para heurísticas avanzadas
    sensitivity: float = 0.5  # Sensibilidad del parámetro (0-1)
    interaction_effects: Dict[str, float] = field(default_factory=dict)
    contextual_dependencies: List[ContextualFactor] = field(default_factory=list)
    optimization_history: List[Tuple[float, float]] = field(default_factory=list)  # (value, performance)
    stability_score: float = 1.0  # Qué tan estable es el parámetro
    last_optimized: Optional[datetime] = None
    
@dataclass 
class AdvancedPerformanceMetrics:
    """Métricas de rendimiento avanzadas"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    consistency: float = 0.0
    diversity: float = 0.0
    coverage: float = 0.0
    efficiency: float = 0.0
    robustness: float = 0.0
    adaptability: float = 0.0
    stability: float = 0.0
    convergence_rate: float = 0.0
    
    # Métricas compuestas
    overall_score: float = 0.0
    quality_index: float = 0.0
    risk_adjusted_performance: float = 0.0
    contextual_fitness: float = 0.0
    
    def calculate_composite_scores(self, weights: Optional[Dict[str, float]] = None):
        """Calcula métricas compuestas usando pesos"""
        if weights is None:
            weights = {
                'accuracy': 0.25, 'precision': 0.15, 'recall': 0.15, 'f1_score': 0.20,
                'consistency': 0.10, 'diversity': 0.05, 'robustness': 0.10
            }
        
        # Score general ponderado
        self.overall_score = sum(
            getattr(self, metric, 0) * weight 
            for metric, weight in weights.items()
        )
        
        # Índice de calidad (penaliza desequilibrios)
        scores = [self.accuracy, self.precision, self.recall, self.consistency]
        self.quality_index = np.mean(scores) - np.std(scores) * 0.2
        
        # Performance ajustado por riesgo
        risk_factor = 1.0 - (1.0 - self.stability) * 0.3
        self.risk_adjusted_performance = self.overall_score * risk_factor
        
        # Fitness contextual (adapta según contexto)
        context_bonus = (self.adaptability + self.robustness) * 0.1
        self.contextual_fitness = self.overall_score + context_bonus

class AdvancedHeuristicEvaluator:
    """Evaluador heurístico avanzado para métricas de rendimiento"""
    
    def __init__(self):
        self.performance_history = deque(maxlen=100)
        self.contextual_cache = {}
        self.adaptation_memory = defaultdict(list)
        
    def evaluate_lottery_performance(self, 
                                   predicted_combinations: List[List[int]],
                                   winning_combination: Optional[List[int]] = None,
                                   historical_results: Optional[List[List[int]]] = None,
                                   context: Optional[Dict[str, Any]] = None) -> AdvancedPerformanceMetrics:
        """
        Evaluación heurística avanzada específica para predicciones de lotería
        
        Args:
            predicted_combinations: Combinaciones predichas por el sistema
            winning_combination: Combinación ganadora real (si disponible)
            historical_results: Resultados históricos para contexto
            context: Información contextual adicional
        """
        metrics = AdvancedPerformanceMetrics()
        
        try:
            # Validar entrada si está disponible
            if ENHANCED_MODULES_AVAILABLE:
                validated_predictions = []
                for combo in predicted_combinations:
                    try:
                        validated = OmegaValidator.validate_combination(combo)
                        validated_predictions.append(validated)
                    except ValidationError:
                        continue
                predicted_combinations = validated_predictions
                
                if winning_combination:
                    winning_combination = OmegaValidator.validate_combination(winning_combination)
            
            # 1. ACCURACY - Exactitud de predicción
            metrics.accuracy = self._calculate_accuracy(predicted_combinations, winning_combination)
            
            # 2. PRECISION - Precisión de números individuales
            metrics.precision = self._calculate_precision(predicted_combinations, winning_combination)
            
            # 3. RECALL - Cobertura de números ganadores
            metrics.recall = self._calculate_recall(predicted_combinations, winning_combination)
            
            # 4. F1 SCORE - Balance entre precision y recall
            if metrics.precision + metrics.recall > 0:
                metrics.f1_score = 2 * (metrics.precision * metrics.recall) / (metrics.precision + metrics.recall)
            
            # 5. CONSISTENCY - Consistencia de las predicciones
            metrics.consistency = self._calculate_consistency(predicted_combinations, historical_results)
            
            # 6. DIVERSITY - Diversidad de las combinaciones
            metrics.diversity = self._calculate_diversity(predicted_combinations)
            
            # 7. COVERAGE - Cobertura del espacio de números
            metrics.coverage = self._calculate_coverage(predicted_combinations)
            
            # 8. EFFICIENCY - Eficiencia computacional/predictiva
            metrics.efficiency = self._calculate_efficiency(predicted_combinations, context)
            
            # 9. ROBUSTNESS - Robustez ante variaciones
            metrics.robustness = self._calculate_robustness(predicted_combinations, historical_results)
            
            # 10. ADAPTABILITY - Capacidad de adaptación
            metrics.adaptability = self._calculate_adaptability(predicted_combinations, context)
            
            # 11. STABILITY - Estabilidad temporal
            metrics.stability = self._calculate_stability(predicted_combinations)
            
            # 12. CONVERGENCE RATE - Velocidad de convergencia
            metrics.convergence_rate = self._calculate_convergence_rate(predicted_combinations)
            
            # Calcular métricas compuestas
            metrics.calculate_composite_scores()
            
            # Guardar en historial
            self.performance_history.append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error en evaluación heurística: {e}")
            return AdvancedPerformanceMetrics()  # Retornar métricas vacías
    
    def _calculate_accuracy(self, predictions: List[List[int]], winning: Optional[List[int]]) -> float:
        """Calcula accuracidad exacta de combinaciones"""
        if not winning or not predictions:
            return 0.0
        
        winning_set = set(winning)
        best_match = 0
        
        for pred in predictions:
            matches = len(set(pred) & winning_set)
            best_match = max(best_match, matches)
        
        return best_match / 6.0  # Normalizar a 0-1
    
    def _calculate_precision(self, predictions: List[List[int]], winning: Optional[List[int]]) -> float:
        """Calcula precisión de números individuales"""
        if not winning or not predictions:
            # Heurística: evaluar distribución de números
            all_numbers = [num for pred in predictions for num in pred]
            if not all_numbers:
                return 0.0
            
            # Evaluar balance de distribución (1-40)
            distribution = np.bincount(all_numbers, minlength=41)[1:41]  # Ignorar 0
            ideal_freq = len(all_numbers) / 40
            distribution_score = 1.0 - np.std(distribution) / (ideal_freq + 1e-6)
            return max(0.0, min(1.0, distribution_score))
        
        winning_set = set(winning)
        total_predicted = sum(len(pred) for pred in predictions)
        correct_predicted = sum(len(set(pred) & winning_set) for pred in predictions)
        
        return correct_predicted / max(total_predicted, 1)
    
    def _calculate_recall(self, predictions: List[List[int]], winning: Optional[List[int]]) -> float:
        """Calcula recall (cobertura de números ganadores)"""
        if not winning or not predictions:
            # Heurística: evaluar cobertura del espacio numérico
            all_numbers = set(num for pred in predictions for num in pred)
            coverage = len(all_numbers) / 40.0  # Cobertura de 1-40
            return coverage
        
        winning_set = set(winning)
        covered_winning = set()
        
        for pred in predictions:
            covered_winning.update(set(pred) & winning_set)
        
        return len(covered_winning) / len(winning_set)
    
    def _calculate_consistency(self, predictions: List[List[int]], historical: Optional[List[List[int]]]) -> float:
        """Calcula consistencia temporal y estadística"""
        if len(predictions) < 2:
            return 1.0
        
        # Consistencia interna entre predicciones
        consistencies = []
        for i in range(len(predictions)):
            for j in range(i + 1, len(predictions)):
                overlap = len(set(predictions[i]) & set(predictions[j]))
                consistency = overlap / 6.0
                consistencies.append(consistency)
        
        internal_consistency = np.mean(consistencies) if consistencies else 0.0
        
        # Consistencia con patrones históricos si están disponibles
        historical_consistency = 0.5  # Valor neutro por defecto
        if historical and len(historical) > 0:
            # Evaluar qué tan bien las predicciones siguen patrones históricos
            historical_patterns = self._extract_patterns(historical[-20:])  # Últimos 20
            prediction_patterns = self._extract_patterns(predictions)
            
            pattern_similarity = self._compare_patterns(historical_patterns, prediction_patterns)
            historical_consistency = pattern_similarity
        
        return (internal_consistency + historical_consistency) / 2.0
    
    def _calculate_diversity(self, predictions: List[List[int]]) -> float:
        """Calcula diversidad entre predicciones"""
        if len(predictions) < 2:
            return 1.0
        
        # Diversidad basada en distancia Jaccard
        total_pairs = 0
        total_diversity = 0.0
        
        for i in range(len(predictions)):
            for j in range(i + 1, len(predictions)):
                set1, set2 = set(predictions[i]), set(predictions[j])
                intersection = len(set1 & set2)
                union = len(set1 | set2)
                jaccard_similarity = intersection / union if union > 0 else 0
                diversity = 1.0 - jaccard_similarity
                
                total_diversity += diversity
                total_pairs += 1
        
        return total_diversity / max(total_pairs, 1)
    
    def _calculate_coverage(self, predictions: List[List[int]]) -> float:
        """Calcula cobertura del espacio de números"""
        if not predictions:
            return 0.0
        
        # Números únicos cubiertos
        all_numbers = set(num for pred in predictions for num in pred)
        basic_coverage = len(all_numbers) / 40.0
        
        # Cobertura por zonas (1-10, 11-20, 21-30, 31-40)
        zones = [set(range(1, 11)), set(range(11, 21)), set(range(21, 31)), set(range(31, 41))]
        zone_coverage = []
        
        for zone in zones:
            zone_numbers = all_numbers & zone
            zone_coverage.append(len(zone_numbers) / 10.0)
        
        balanced_coverage = np.mean(zone_coverage)
        
        return (basic_coverage + balanced_coverage) / 2.0
    
    def _calculate_efficiency(self, predictions: List[List[int]], context: Optional[Dict[str, Any]]) -> float:
        """Calcula eficiencia predictiva y computacional"""
        # Eficiencia predictiva: relación calidad/cantidad
        prediction_quality = len(predictions) / max(len(set(tuple(p) for p in predictions)), 1)
        
        # Eficiencia temporal (si disponible en contexto)
        temporal_efficiency = 1.0
        if context and 'processing_time' in context:
            processing_time = context['processing_time']
            # Penalizar tiempos muy largos (>60s)
            temporal_efficiency = max(0.1, 1.0 - (processing_time - 10) / 50) if processing_time > 10 else 1.0
        
        # Eficiencia de recursos
        resource_efficiency = 1.0
        if context and 'memory_usage' in context:
            memory_mb = context['memory_usage']
            # Penalizar uso excesivo de memoria (>1GB)
            resource_efficiency = max(0.1, 1.0 - (memory_mb - 512) / 512) if memory_mb > 512 else 1.0
        
        return (prediction_quality + temporal_efficiency + resource_efficiency) / 3.0
    
    def _calculate_robustness(self, predictions: List[List[int]], historical: Optional[List[List[int]]]) -> float:
        """Calcula robustez ante variaciones"""
        if not predictions:
            return 0.0
        
        # Robustez estadística: qué tan consistentes son las estadísticas
        stats_robustness = self._evaluate_statistical_robustness(predictions)
        
        # Robustez temporal: si funciona en diferentes períodos
        temporal_robustness = 0.5  # Valor neutro
        if historical and len(historical) > 10:
            # Simular robustez comparando con diferentes ventanas históricas
            temporal_robustness = self._evaluate_temporal_robustness(predictions, historical)
        
        return (stats_robustness + temporal_robustness) / 2.0
    
    def _calculate_adaptability(self, predictions: List[List[int]], context: Optional[Dict[str, Any]]) -> float:
        """Calcula capacidad de adaptación"""
        # Adaptabilidad basada en variedad de estrategias
        strategy_diversity = 0.5  # Valor base
        
        if context and 'models_used' in context:
            models = context['models_used']
            strategy_diversity = min(1.0, len(set(models)) / 8.0)  # Normalizar por 8 modelos típicos
        
        # Adaptabilidad numérica: uso equilibrado de rangos
        number_adaptability = self._evaluate_number_adaptability(predictions)
        
        return (strategy_diversity + number_adaptability) / 2.0
    
    def _calculate_stability(self, predictions: List[List[int]]) -> float:
        """Calcula estabilidad de las predicciones"""
        if len(predictions) < 3:
            return 1.0
        
        # Estabilidad de distribución de números
        all_distributions = []
        for pred in predictions:
            distribution = np.bincount(pred, minlength=41)[1:41]  # 1-40
            all_distributions.append(distribution / 6.0)  # Normalizar
        
        # Calcular varianza promedio de las distribuciones
        distribution_matrix = np.array(all_distributions)
        stability_scores = []
        
        for i in range(40):  # Para cada número
            variance = np.var(distribution_matrix[:, i])
            stability = 1.0 - min(variance, 1.0)  # Invertir varianza
            stability_scores.append(stability)
        
        return np.mean(stability_scores)
    
    def _calculate_convergence_rate(self, predictions: List[List[int]]) -> float:
        """Calcula velocidad de convergencia de patrones"""
        if len(predictions) < 3:
            return 1.0
        
        # Analizar convergencia de patrones estadísticos
        pattern_evolution = []
        for i in range(1, len(predictions)):
            current_patterns = self._extract_simple_patterns(predictions[:i+1])
            if i == 1:
                pattern_evolution.append(1.0)  # Inicial
            else:
                previous_patterns = self._extract_simple_patterns(predictions[:i])
                similarity = self._pattern_similarity(current_patterns, previous_patterns)
                pattern_evolution.append(similarity)
        
        # Convergencia = qué tan rápido se estabilizan los patrones
        if len(pattern_evolution) > 1:
            convergence = 1.0 - np.std(pattern_evolution[-3:])  # Últimos 3 puntos
            return max(0.0, convergence)
        
        return 0.5
    
    # Métodos auxiliares
    def _extract_patterns(self, combinations: List[List[int]]) -> Dict[str, float]:
        """Extrae patrones estadísticos de las combinaciones"""
        if not combinations:
            return {}
        
        patterns = {}
        all_numbers = [num for combo in combinations for num in combo]
        
        # Patrones básicos
        patterns['mean'] = np.mean(all_numbers)
        patterns['std'] = np.std(all_numbers)
        patterns['sum_avg'] = np.mean([sum(combo) for combo in combinations])
        
        # Patrones de distribución
        distribution = np.bincount(all_numbers, minlength=41)[1:41]
        patterns['entropy'] = -np.sum(distribution * np.log(distribution + 1e-6)) / np.log(40)
        
        return patterns
    
    def _extract_simple_patterns(self, combinations: List[List[int]]) -> Dict[str, float]:
        """Extrae patrones simples para análisis de convergencia"""
        if not combinations:
            return {}
        
        all_numbers = [num for combo in combinations for num in combo]
        return {
            'mean': np.mean(all_numbers),
            'sum_avg': np.mean([sum(combo) for combo in combinations])
        }
    
    def _compare_patterns(self, patterns1: Dict[str, float], patterns2: Dict[str, float]) -> float:
        """Compara similitud entre patrones"""
        if not patterns1 or not patterns2:
            return 0.0
        
        common_keys = set(patterns1.keys()) & set(patterns2.keys())
        if not common_keys:
            return 0.0
        
        similarities = []
        for key in common_keys:
            val1, val2 = patterns1[key], patterns2[key]
            if val1 == 0 and val2 == 0:
                similarity = 1.0
            else:
                similarity = 1.0 - abs(val1 - val2) / (abs(val1) + abs(val2) + 1e-6)
            similarities.append(similarity)
        
        return np.mean(similarities)
    
    def _pattern_similarity(self, patterns1: Dict[str, float], patterns2: Dict[str, float]) -> float:
        """Calcula similitud entre patrones (alias para compatibilidad)"""
        return self._compare_patterns(patterns1, patterns2)
    
    def _evaluate_statistical_robustness(self, predictions: List[List[int]]) -> float:
        """Evalúa robustez estadística"""
        if not predictions:
            return 0.0
        
        # Evaluar consistencia de estadísticas básicas
        sums = [sum(pred) for pred in predictions]
        sum_consistency = 1.0 - (np.std(sums) / (np.mean(sums) + 1e-6))
        
        # Evaluar consistencia de rangos
        ranges = [max(pred) - min(pred) for pred in predictions]
        range_consistency = 1.0 - (np.std(ranges) / (np.mean(ranges) + 1e-6))
        
        return (max(0.0, sum_consistency) + max(0.0, range_consistency)) / 2.0
    
    def _evaluate_temporal_robustness(self, predictions: List[List[int]], historical: List[List[int]]) -> float:
        """Evalúa robustez temporal"""
        # Comparar predicciones con diferentes ventanas históricas
        window_scores = []
        window_size = min(10, len(historical) // 2)
        
        for start in range(0, len(historical) - window_size, window_size):
            window = historical[start:start + window_size]
            window_patterns = self._extract_patterns(window)
            pred_patterns = self._extract_patterns(predictions)
            similarity = self._compare_patterns(window_patterns, pred_patterns)
            window_scores.append(similarity)
        
        if window_scores:
            return np.mean(window_scores)
        return 0.5
    
    def _evaluate_number_adaptability(self, predictions: List[List[int]]) -> float:
        """Evalúa adaptabilidad en uso de números"""
        if not predictions:
            return 0.0
        
        all_numbers = [num for pred in predictions for num in pred]
        
        # Evaluar uso equilibrado de rangos
        low_nums = sum(1 for n in all_numbers if 1 <= n <= 10)
        mid_low_nums = sum(1 for n in all_numbers if 11 <= n <= 20)
        mid_high_nums = sum(1 for n in all_numbers if 21 <= n <= 30)
        high_nums = sum(1 for n in all_numbers if 31 <= n <= 40)
        
        range_counts = [low_nums, mid_low_nums, mid_high_nums, high_nums]
        ideal_count = len(all_numbers) / 4
        
        adaptability = 1.0 - np.std(range_counts) / (ideal_count + 1e-6)
        return max(0.0, adaptability)

class EnhancedAutoConfigOptimizer:
    """Optimizador de configuración mejorado con heurísticas avanzadas"""
    
    def __init__(self,
                 strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE_MULTI_OBJECTIVE,
                 performance_window: int = 20,
                 optimization_frequency: int = 5):
        
        self.strategy = strategy
        self.performance_window = performance_window
        self.optimization_frequency = optimization_frequency
        
        # Componentes mejorados
        self.heuristic_evaluator = AdvancedHeuristicEvaluator()
        self.optimization_targets = {}
        self.performance_history = deque(maxlen=performance_window)
        self.optimization_history = []
        
        # Estado del optimizador
        self.cycles_since_optimization = 0
        self.best_configuration = {}
        self.current_configuration = {}
        
        logger.info(f"🎯 Enhanced Auto Config Optimizer inicializado")
        logger.info(f"   Estrategia: {strategy.value}")
        logger.info(f"   Ventana de performance: {performance_window}")
    
    @handle_omega_errors(
        context="Registro de performance en Auto Config Optimizer",
        fallback_return=False
    )
    def record_performance(self,
                          predicted_combinations: List[List[int]],
                          winning_combination: Optional[List[int]] = None,
                          system_config: Optional[Dict[str, Any]] = None,
                          context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Registra performance con evaluación heurística avanzada
        """
        try:
            # Evaluar performance usando heurísticas avanzadas
            metrics = self.heuristic_evaluator.evaluate_lottery_performance(
                predicted_combinations=predicted_combinations,
                winning_combination=winning_combination,
                historical_results=context.get('historical_results') if context else None,
                context=context
            )
            
            # Agregar información del sistema
            performance_record = {
                'timestamp': datetime.now(),
                'metrics': metrics,
                'system_config': system_config or {},
                'context': context or {},
                'num_predictions': len(predicted_combinations),
                'has_winning_data': winning_combination is not None
            }
            
            self.performance_history.append(performance_record)
            self.cycles_since_optimization += 1
            
            logger.info(f"📊 Performance registrada - Score: {metrics.overall_score:.3f}")
            logger.info(f"   Accuracy: {metrics.accuracy:.3f}, Consistency: {metrics.consistency:.3f}")
            logger.info(f"   Diversity: {metrics.diversity:.3f}, Coverage: {metrics.coverage:.3f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error registrando performance: {e}")
            return False
    
    def should_optimize(self) -> bool:
        """
        Decide si debe realizar optimización usando criterios avanzados
        """
        # Criterio básico: frecuencia
        if self.cycles_since_optimization < self.optimization_frequency:
            return False
        
        # Criterio avanzado: tendencia de performance
        if len(self.performance_history) < 5:
            return False
        
        recent_scores = [record['metrics'].overall_score for record in self.performance_history[-5:]]
        earlier_scores = [record['metrics'].overall_score for record in self.performance_history[-10:-5]] if len(self.performance_history) >= 10 else []
        
        # Optimizar si hay degradación de performance
        if earlier_scores:
            recent_avg = np.mean(recent_scores)
            earlier_avg = np.mean(earlier_scores)
            performance_degradation = (earlier_avg - recent_avg) / (earlier_avg + 1e-6)
            
            if performance_degradation > 0.1:  # 10% degradación
                logger.info(f"🎯 Optimización activada por degradación: {performance_degradation:.2%}")
                return True
        
        # Optimizar si hay alta variabilidad
        score_variance = np.var(recent_scores)
        if score_variance > 0.05:  # Alta variabilidad
            logger.info(f"🎯 Optimización activada por alta variabilidad: {score_variance:.3f}")
            return True
        
        # Optimización regular
        return True
    
    def optimize_configuration(self,
                             current_config: Dict[str, Any],
                             optimization_targets: Optional[List[EnhancedOptimizationTarget]] = None) -> Dict[str, Any]:
        """
        Optimiza configuración usando estrategia avanzada
        """
        logger.info(f"🔧 Iniciando optimización de configuración...")
        
        if optimization_targets is None:
            optimization_targets = self._create_default_targets(current_config)
        
        optimization_start = datetime.now()
        
        try:
            # Seleccionar estrategia según contexto
            if self.strategy == OptimizationStrategy.ADAPTIVE_MULTI_OBJECTIVE:
                optimized_config = self._adaptive_multi_objective_optimization(
                    current_config, optimization_targets
                )
            elif self.strategy == OptimizationStrategy.BAYESIAN and OPTUNA_AVAILABLE:
                optimized_config = self._bayesian_optimization(
                    current_config, optimization_targets
                )
            elif self.strategy == OptimizationStrategy.EVOLUTIONARY:
                optimized_config = self._evolutionary_optimization(
                    current_config, optimization_targets
                )
            else:
                # Fallback a búsqueda adaptativa
                optimized_config = self._adaptive_search_optimization(
                    current_config, optimization_targets
                )
            
            optimization_time = (datetime.now() - optimization_start).total_seconds()
            
            # Registrar optimización
            optimization_record = {
                'timestamp': datetime.now(),
                'strategy': self.strategy.value,
                'optimization_time': optimization_time,
                'old_config': current_config.copy(),
                'new_config': optimized_config.copy(),
                'improvements': self._calculate_improvements(current_config, optimized_config)
            }
            
            self.optimization_history.append(optimization_record)
            self.cycles_since_optimization = 0
            self.current_configuration = optimized_config
            
            logger.info(f"✅ Optimización completada en {optimization_time:.2f}s")
            logger.info(f"   Mejoras detectadas: {len(optimization_record['improvements'])}")
            
            return optimized_config
            
        except Exception as e:
            logger.error(f"❌ Error en optimización: {e}")
            return current_config  # Retornar configuración original
    
    def _adaptive_multi_objective_optimization(self,
                                             current_config: Dict[str, Any],
                                             targets: List[EnhancedOptimizationTarget]) -> Dict[str, Any]:
        """
        Optimización multi-objetivo adaptativa (método principal)
        """
        optimized_config = current_config.copy()
        
        # Evaluar performance actual
        current_performance = self._evaluate_config_performance(current_config)
        
        # Optimizar cada target según su importancia y sensibilidad
        for target in sorted(targets, key=lambda t: t.importance * t.sensitivity, reverse=True):
            best_value = target.current_value
            best_score = current_performance
            
            # Explorar valores candidatos según el tipo
            candidates = self._generate_candidates(target, adaptive=True)
            
            for candidate_value in candidates:
                test_config = optimized_config.copy()
                test_config[target.parameter_name] = candidate_value
                
                # Evaluar configuración candidata
                candidate_score = self._evaluate_config_performance(test_config)
                
                # Considerar factores contextuales
                adjusted_score = self._apply_contextual_adjustments(
                    candidate_score, target, candidate_value
                )
                
                if adjusted_score > best_score:
                    best_value = candidate_value
                    best_score = adjusted_score
                    
                    logger.debug(f"   Mejora en {target.parameter_name}: {candidate_value} (score: {adjusted_score:.3f})")
            
            optimized_config[target.parameter_name] = best_value
            target.optimization_history.append((best_value, best_score))
        
        return optimized_config
    
    def _evaluate_config_performance(self, config: Dict[str, Any]) -> float:
        """
        Evalúa performance de una configuración usando historial
        """
        if not self.performance_history:
            return 0.5  # Score neutro
        
        # Buscar configuraciones similares en el historial
        similar_configs = []
        for record in self.performance_history:
            similarity = self._calculate_config_similarity(config, record['system_config'])
            if similarity > 0.7:  # Configuraciones similares
                weight = similarity  # Peso por similitud
                score = record['metrics'].overall_score
                similar_configs.append((score, weight))
        
        if similar_configs:
            # Score ponderado por similitud
            weighted_scores = [score * weight for score, weight in similar_configs]
            total_weight = sum(weight for _, weight in similar_configs)
            return sum(weighted_scores) / total_weight
        
        # Si no hay configuraciones similares, usar promedio general
        all_scores = [record['metrics'].overall_score for record in self.performance_history]
        return np.mean(all_scores)
    
    def _generate_candidates(self, target: EnhancedOptimizationTarget, adaptive: bool = False) -> List[Union[int, float, str]]:
        """
        Genera valores candidatos para optimización
        """
        if target.value_type == 'categorical':
            return target.category_options or []
        
        # Para valores numéricos
        candidates = []
        current = target.current_value
        min_val, max_val = target.min_value, target.max_value
        
        if adaptive:
            # Exploración adaptativa basada en sensibilidad
            step_size = (max_val - min_val) * target.sensitivity * 0.1
            num_steps = max(3, int(10 * target.sensitivity))
        else:
            # Exploración uniforme
            step_size = (max_val - min_val) / 10
            num_steps = 10
        
        # Generar candidatos alrededor del valor actual
        for i in range(-num_steps//2, num_steps//2 + 1):
            candidate = current + i * step_size
            candidate = max(min_val, min(max_val, candidate))
            
            if target.value_type == 'int':
                candidate = int(round(candidate))
            
            candidates.append(candidate)
        
        return list(set(candidates))  # Eliminar duplicados
    
    def _apply_contextual_adjustments(self,
                                    base_score: float,
                                    target: EnhancedOptimizationTarget,
                                    candidate_value: Union[int, float, str]) -> float:
        """
        Aplica ajustes contextuales al score
        """
        adjusted_score = base_score
        
        # Ajuste por estabilidad del parámetro
        stability_bonus = target.stability_score * 0.1
        adjusted_score += stability_bonus
        
        # Penalización por cambios drásticos
        if isinstance(candidate_value, (int, float)) and isinstance(target.current_value, (int, float)):
            change_magnitude = abs(candidate_value - target.current_value) / (abs(target.current_value) + 1e-6)
            if change_magnitude > 0.5:  # Cambio > 50%
                adjusted_score -= 0.05  # Penalización leve
        
        # Bonus por tendencias positivas en historial
        if len(target.optimization_history) >= 2:
            recent_trend = target.optimization_history[-1][1] - target.optimization_history[-2][1]
            if recent_trend > 0:
                adjusted_score += 0.02
        
        return max(0.0, min(1.0, adjusted_score))
    
    def _calculate_config_similarity(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> float:
        """
        Calcula similitud entre configuraciones
        """
        if not config1 or not config2:
            return 0.0
        
        common_keys = set(config1.keys()) & set(config2.keys())
        if not common_keys:
            return 0.0
        
        similarities = []
        for key in common_keys:
            val1, val2 = config1[key], config2[key]
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                if val1 == 0 and val2 == 0:
                    similarity = 1.0
                else:
                    similarity = 1.0 - abs(val1 - val2) / (abs(val1) + abs(val2) + 1e-6)
            elif val1 == val2:
                similarity = 1.0
            else:
                similarity = 0.0
            
            similarities.append(similarity)
        
        return np.mean(similarities)
    
    def _create_default_targets(self, config: Dict[str, Any]) -> List[EnhancedOptimizationTarget]:
        """
        Crea targets de optimización por defecto para OMEGA PRO AI
        """
        targets = []
        
        # Targets típicos para sistema de lotería
        default_targets = [
            {
                'name': 'num_combinations',
                'min_val': 5, 'max_val': 50, 'type': 'int',
                'importance': 0.8, 'sensitivity': 0.6
            },
            {
                'name': 'exploration_factor',
                'min_val': 0.1, 'max_val': 1.0, 'type': 'float',
                'importance': 0.7, 'sensitivity': 0.7
            },
            {
                'name': 'prediction_weight',
                'min_val': 0.3, 'max_val': 0.9, 'type': 'float',
                'importance': 0.9, 'sensitivity': 0.8
            },
            {
                'name': 'svi_weight',
                'min_val': 0.1, 'max_val': 0.7, 'type': 'float',
                'importance': 0.9, 'sensitivity': 0.8
            }
        ]
        
        for target_def in default_targets:
            name = target_def['name']
            current_value = config.get(name, (target_def['min_val'] + target_def['max_val']) / 2)
            
            target = EnhancedOptimizationTarget(
                parameter_name=name,
                current_value=current_value,
                min_value=target_def['min_val'],
                max_value=target_def['max_val'],
                value_type=target_def['type'],
                importance=target_def['importance'],
                sensitivity=target_def['sensitivity']
            )
            
            targets.append(target)
        
        return targets
    
    def _calculate_improvements(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calcula mejoras entre configuraciones
        """
        improvements = []
        
        for key in set(old_config.keys()) | set(new_config.keys()):
            old_val = old_config.get(key)
            new_val = new_config.get(key)
            
            if old_val != new_val:
                improvement = {
                    'parameter': key,
                    'old_value': old_val,
                    'new_value': new_val,
                    'change_type': 'modified' if key in old_config else 'added'
                }
                
                # Calcular magnitud del cambio para valores numéricos
                if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                    change_magnitude = abs(new_val - old_val) / (abs(old_val) + 1e-6)
                    improvement['change_magnitude'] = change_magnitude
                
                improvements.append(improvement)
        
        return improvements
    
    # Métodos de optimización alternativos
    def _bayesian_optimization(self, current_config: Dict[str, Any], targets: List[EnhancedOptimizationTarget]) -> Dict[str, Any]:
        """Optimización Bayesiana usando Optuna (si está disponible)"""
        logger.info("🔬 Ejecutando optimización Bayesiana")
        # Implementación simplificada - en la práctica usaría Optuna
        return self._adaptive_search_optimization(current_config, targets)
    
    def _evolutionary_optimization(self, current_config: Dict[str, Any], targets: List[EnhancedOptimizationTarget]) -> Dict[str, Any]:
        """Optimización evolutiva"""
        logger.info("🧬 Ejecutando optimización evolutiva")
        # Implementación simplificada
        return self._adaptive_search_optimization(current_config, targets)
    
    def _adaptive_search_optimization(self, current_config: Dict[str, Any], targets: List[EnhancedOptimizationTarget]) -> Dict[str, Any]:
        """Búsqueda adaptativa (fallback)"""
        optimized_config = current_config.copy()
        
        for target in targets:
            candidates = self._generate_candidates(target, adaptive=True)
            best_value = target.current_value
            
            # Seleccionar el mejor candidato (simplificado)
            if candidates:
                # En una implementación real, evaluaríamos cada candidato
                # Por ahora, seleccionamos uno cercano al óptimo teórico
                mid_index = len(candidates) // 2
                best_value = candidates[mid_index]
            
            optimized_config[target.parameter_name] = best_value
        
        return optimized_config
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen de optimizaciones realizadas
        """
        if not self.optimization_history:
            return {'total_optimizations': 0}
        
        recent_optimizations = self.optimization_history[-5:]
        
        return {
            'total_optimizations': len(self.optimization_history),
            'recent_optimizations': len(recent_optimizations),
            'avg_optimization_time': np.mean([opt['optimization_time'] for opt in recent_optimizations]),
            'strategies_used': list(set(opt['strategy'] for opt in self.optimization_history)),
            'performance_trend': self._calculate_performance_trend(),
            'most_optimized_parameters': self._get_most_optimized_parameters()
        }
    
    def _calculate_performance_trend(self) -> str:
        """Calcula tendencia de performance"""
        if len(self.performance_history) < 10:
            return "insufficient_data"
        
        recent_scores = [record['metrics'].overall_score for record in self.performance_history[-5:]]
        earlier_scores = [record['metrics'].overall_score for record in self.performance_history[-10:-5]]
        
        recent_avg = np.mean(recent_scores)
        earlier_avg = np.mean(earlier_scores)
        
        if recent_avg > earlier_avg * 1.05:
            return "improving"
        elif recent_avg < earlier_avg * 0.95:
            return "declining"
        else:
            return "stable"
    
    def _get_most_optimized_parameters(self) -> List[str]:
        """Obtiene parámetros más frecuentemente optimizados"""
        parameter_counts = defaultdict(int)
        
        for optimization in self.optimization_history:
            for improvement in optimization['improvements']:
                parameter_counts[improvement['parameter']] += 1
        
        return sorted(parameter_counts.keys(), key=parameter_counts.get, reverse=True)[:5]

# Funciones de utilidad
def create_enhanced_optimizer(strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE_MULTI_OBJECTIVE) -> EnhancedAutoConfigOptimizer:
    """Crea optimizador mejorado"""
    return EnhancedAutoConfigOptimizer(strategy=strategy)

def optimize_omega_config(current_config: Dict[str, Any],
                         performance_data: List[Dict[str, Any]],
                         strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE_MULTI_OBJECTIVE) -> Dict[str, Any]:
    """
    Función de conveniencia para optimizar configuración de OMEGA PRO AI
    """
    optimizer = create_enhanced_optimizer(strategy)
    
    # Registrar datos de performance históricos
    for data in performance_data:
        optimizer.record_performance(
            predicted_combinations=data.get('predictions', []),
            winning_combination=data.get('winning'),
            system_config=data.get('config', {}),
            context=data.get('context', {})
        )
    
    # Optimizar si es necesario
    if optimizer.should_optimize():
        return optimizer.optimize_configuration(current_config)
    
    return current_config
