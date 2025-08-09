#!/usr/bin/env python3
"""
Auto Config Optimizer para OMEGA PRO AI
Optimizador automático de hiperparámetros y filtros basado en rendimiento
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os
from pathlib import Path
from sklearn.model_selection import ParameterGrid
try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """Estrategias de optimización disponibles"""
    GRID_SEARCH = "grid_search"
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    RANDOM_SEARCH = "random_search"
    ADAPTIVE = "adaptive"

class PerformanceMetric(Enum):
    """Métricas de rendimiento para optimización"""
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    DIVERSITY = "diversity"
    COVERAGE = "coverage"
    EFFICIENCY = "efficiency"

@dataclass
class OptimizationTarget:
    """Objetivo de optimización"""
    parameter_name: str
    current_value: Union[int, float, str]
    min_value: Union[int, float]
    max_value: Union[int, float]
    value_type: str  # 'int', 'float', 'categorical'
    category_options: Optional[List[str]] = None
    importance: float = 1.0
    
@dataclass
class OptimizationResult:
    """Resultado de optimización"""
    parameter_name: str
    old_value: Union[int, float, str]
    new_value: Union[int, float, str]
    improvement: float
    confidence: float
    trials_count: int
    best_score: float

@dataclass
class PerformanceHistory:
    """Historial de rendimiento"""
    timestamp: datetime
    parameters: Dict[str, Any]
    accuracy_score: float
    consistency_score: float
    diversity_score: float
    coverage_score: float
    efficiency_score: float
    combined_score: float
    notes: str

class AutoConfigOptimizer:
    """Optimizador automático de configuraciones"""
    
    def __init__(self, 
                 optimization_strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE,
                 performance_window: int = 20,
                 optimization_threshold: float = 0.1,
                 max_trials: int = 100):
        
        self.optimization_strategy = optimization_strategy
        self.performance_window = performance_window
        self.optimization_threshold = optimization_threshold
        self.max_trials = max_trials
        
        # Historia de rendimiento
        self.performance_history: List[PerformanceHistory] = []
        
        # Objetivos de optimización
        self.optimization_targets = self._initialize_optimization_targets()
        
        # Configuración actual
        self.current_config = self._initialize_default_config()
        
        # Optimizadores especializados
        self.bayesian_optimizer = None
        self.optuna_study = None
        
        # Métricas de optimización
        self.optimization_metrics = {
            'total_optimizations': 0,
            'successful_improvements': 0,
            'average_improvement': 0.0,
            'best_configuration': None,
            'last_optimization': None
        }
        
        logger.info("⚙️ Auto Config Optimizer inicializado")
        logger.info(f"   Estrategia: {optimization_strategy.value}")
        logger.info(f"   Ventana: {performance_window}, Umbral: {optimization_threshold}")
    
    def _initialize_optimization_targets(self) -> Dict[str, OptimizationTarget]:
        """Inicializa objetivos de optimización"""
        
        return {
            # Parámetros de generación
            'num_combinations': OptimizationTarget(
                parameter_name='num_combinations',
                current_value=30,
                min_value=10,
                max_value=100,
                value_type='int',
                importance=0.8
            ),
            
            'exploration_factor': OptimizationTarget(
                parameter_name='exploration_factor',
                current_value=0.3,
                min_value=0.0,
                max_value=0.8,
                value_type='float',
                importance=0.9
            ),
            
            'diversity_weight': OptimizationTarget(
                parameter_name='diversity_weight',
                current_value=0.5,
                min_value=0.1,
                max_value=1.0,
                value_type='float',
                importance=0.7
            ),
            
            # Parámetros de filtros
            'range_filter_min': OptimizationTarget(
                parameter_name='range_filter_min',
                current_value=100,
                min_value=80,
                max_value=150,
                value_type='int',
                importance=0.6
            ),
            
            'range_filter_max': OptimizationTarget(
                parameter_name='range_filter_max',
                current_value=200,
                min_value=150,
                max_value=300,
                value_type='int',
                importance=0.6
            ),
            
            'sum_filter_tolerance': OptimizationTarget(
                parameter_name='sum_filter_tolerance',
                current_value=30,
                min_value=10,
                max_value=60,
                value_type='int',
                importance=0.5
            ),
            
            'gap_filter_max': OptimizationTarget(
                parameter_name='gap_filter_max',
                current_value=15,
                min_value=8,
                max_value=25,
                value_type='int',
                importance=0.4
            ),
            
            # Pesos de modelos
            'lstm_weight': OptimizationTarget(
                parameter_name='lstm_weight',
                current_value=1.0,
                min_value=0.5,
                max_value=2.0,
                value_type='float',
                importance=0.8
            ),
            
            'transformer_weight': OptimizationTarget(
                parameter_name='transformer_weight',
                current_value=1.0,
                min_value=0.5,
                max_value=2.0,
                value_type='float',
                importance=0.8
            ),
            
            'clustering_weight': OptimizationTarget(
                parameter_name='clustering_weight',
                current_value=1.0,
                min_value=0.5,
                max_value=2.0,
                value_type='float',
                importance=0.7
            ),
            
            # Parámetros SVI
            'svi_profile': OptimizationTarget(
                parameter_name='svi_profile',
                current_value='default',
                min_value=0,  # No usado para categórico
                max_value=0,  # No usado para categórico
                value_type='categorical',
                category_options=['conservative', 'default', 'aggressive'],
                importance=0.6
            ),
            
            # Parámetros de meta-learning
            'meta_learning_rate': OptimizationTarget(
                parameter_name='meta_learning_rate',
                current_value=0.1,
                min_value=0.01,
                max_value=0.5,
                value_type='float',
                importance=0.5
            )
        }
    
    def _initialize_default_config(self) -> Dict[str, Any]:
        """Inicializa configuración por defecto"""
        
        config = {}
        for target_name, target in self.optimization_targets.items():
            config[target_name] = target.current_value
        
        return config
    
    def record_performance(self, 
                         parameters: Dict[str, Any],
                         sorteo_results: List[Dict[str, Any]],
                         notes: str = "") -> PerformanceHistory:
        """Registra rendimiento de una configuración"""
        
        # Calcular métricas de rendimiento
        accuracy_score = self._calculate_accuracy_score(sorteo_results)
        consistency_score = self._calculate_consistency_score(sorteo_results)
        diversity_score = self._calculate_diversity_score(sorteo_results)
        coverage_score = self._calculate_coverage_score(sorteo_results)
        efficiency_score = self._calculate_efficiency_score(sorteo_results, parameters)
        
        # Combinar métricas con pesos
        combined_score = (
            accuracy_score * 0.4 +
            consistency_score * 0.2 +
            diversity_score * 0.2 +
            coverage_score * 0.1 +
            efficiency_score * 0.1
        )
        
        # Crear registro
        performance = PerformanceHistory(
            timestamp=datetime.now(),
            parameters=parameters.copy(),
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            diversity_score=diversity_score,
            coverage_score=coverage_score,
            efficiency_score=efficiency_score,
            combined_score=combined_score,
            notes=notes
        )
        
        # Agregar a historial
        self.performance_history.append(performance)
        
        # Mantener ventana de rendimiento
        if len(self.performance_history) > self.performance_window * 2:
            self.performance_history = self.performance_history[-self.performance_window * 2:]
        
        logger.info(f"📊 Rendimiento registrado: Score combinado = {combined_score:.3f}")
        logger.debug(f"   Accuracy: {accuracy_score:.3f}, Consistency: {consistency_score:.3f}")
        logger.debug(f"   Diversity: {diversity_score:.3f}, Coverage: {coverage_score:.3f}")
        
        return performance
    
    def _calculate_accuracy_score(self, sorteo_results: List[Dict[str, Any]]) -> float:
        """Calcula score de precisión"""
        
        if not sorteo_results:
            return 0.0
        
        valid_results = []
        
        for result in sorteo_results:
            # Validar que existen los datos necesarios
            if not isinstance(result, dict):
                logger.warning("⚠️ Resultado de sorteo no es un diccionario válido")
                continue
                
            if 'aciertos_por_combinacion' not in result:
                logger.debug("⚠️ 'aciertos_por_combinacion' faltante en resultado")
                continue
                
            aciertos = result['aciertos_por_combinacion']
            if not isinstance(aciertos, (list, tuple)) or not aciertos:
                logger.debug("⚠️ 'aciertos_por_combinacion' vacío o no válido")
                continue
            
            # Validar que los aciertos son números válidos
            try:
                max_aciertos = max([int(a) for a in aciertos if isinstance(a, (int, float)) and 0 <= a <= 6])
                accuracy = max_aciertos / 6.0
                valid_results.append(accuracy)
            except (ValueError, TypeError) as e:
                logger.debug(f"⚠️ Error procesando aciertos: {e}")
                continue
        
        if not valid_results:
            logger.warning("⚠️ No hay resultados válidos para calcular accuracy")
            return 0.0
        
        return sum(valid_results) / len(valid_results)
    
    def _calculate_consistency_score(self, sorteo_results: List[Dict[str, Any]]) -> float:
        """Calcula score de consistencia (baja varianza en rendimiento)"""
        
        if len(sorteo_results) < 2:
            return 0.5  # Score neutro
        
        accuracies = []
        for result in sorteo_results:
            if 'aciertos_por_combinacion' in result:
                max_aciertos = max(result['aciertos_por_combinacion']) if result['aciertos_por_combinacion'] else 0
                accuracies.append(max_aciertos)
        
        if not accuracies:
            return 0.0
        
        # Consistencia = 1 - (desviación estándar normalizada)
        mean_accuracy = np.mean(accuracies)
        std_accuracy = np.std(accuracies)
        
        if mean_accuracy == 0:
            return 0.0
        
        consistency = 1.0 - (std_accuracy / (mean_accuracy + 1e-10))
        return max(0.0, min(1.0, consistency))
    
    def _calculate_diversity_score(self, sorteo_results: List[Dict[str, Any]]) -> float:
        """Calcula score de diversidad en predicciones"""
        
        if not sorteo_results:
            return 0.0
        
        all_numbers_predicted = set()
        total_combinations = 0
        
        for result in sorteo_results:
            if not isinstance(result, dict):
                continue
                
            if 'combinaciones_predichas' not in result:
                logger.debug("⚠️ 'combinaciones_predichas' faltante en resultado")
                continue
            
            combinaciones = result['combinaciones_predichas']
            if not isinstance(combinaciones, (list, tuple)):
                logger.debug("⚠️ 'combinaciones_predichas' no es una lista válida")
                continue
            
            for combo in combinaciones:
                if not isinstance(combo, (list, tuple)) or len(combo) != 6:
                    logger.debug(f"⚠️ Combinación inválida: {combo}")
                    continue
                
                # Validar que todos son números en rango 1-40
                try:
                    valid_combo = [int(n) for n in combo if isinstance(n, (int, float)) and 1 <= n <= 40]
                    if len(valid_combo) == 6:
                        all_numbers_predicted.update(valid_combo)
                        total_combinations += 1
                except (ValueError, TypeError):
                    logger.debug(f"⚠️ Error procesando combinación: {combo}")
                    continue
        
        if total_combinations == 0:
            logger.warning("⚠️ No hay combinaciones válidas para calcular diversidad")
            return 0.0
        
        # Diversidad = números únicos predichos / total posible (40)
        diversity = len(all_numbers_predicted) / 40.0
        
        return min(1.0, diversity)
    
    def _calculate_coverage_score(self, sorteo_results: List[Dict[str, Any]]) -> float:
        """Calcula score de cobertura (qué tan bien cubren el espacio de números)"""
        
        if not sorteo_results:
            return 0.0
        
        # Analizar distribución por zonas
        zone_counts = {1: 0, 2: 0, 3: 0, 4: 0}  # Zonas 1-10, 11-20, 21-30, 31-40
        total_numbers = 0
        
        def get_zone(num):
            return min(4, (num - 1) // 10 + 1)
        
        for result in sorteo_results:
            if 'combinaciones_predichas' in result:
                for combo in result['combinaciones_predichas']:
                    for num in combo:
                        zone = get_zone(num)
                        zone_counts[zone] += 1
                        total_numbers += 1
        
        if total_numbers == 0:
            return 0.0
        
        # Calcular balance entre zonas (ideal = 25% cada zona)
        zone_proportions = [count / total_numbers for count in zone_counts.values()]
        ideal_proportion = 0.25
        
        # Coverage = 1 - desviación del balance ideal
        deviation = sum(abs(prop - ideal_proportion) for prop in zone_proportions) / 4
        coverage = 1.0 - deviation
        
        return max(0.0, min(1.0, coverage))
    
    def _calculate_efficiency_score(self, sorteo_results: List[Dict[str, Any]], parameters: Dict[str, Any]) -> float:
        """Calcula score de eficiencia (rendimiento vs recursos)"""
        
        # Eficiencia basada en número de combinaciones generadas vs resultados
        num_combinations = parameters.get('num_combinations', 30)
        
        if not sorteo_results:
            return 0.0
        
        # Calcular accuracy promedio
        total_accuracy = 0.0
        total_sorteos = len(sorteo_results)
        
        for result in sorteo_results:
            if 'aciertos_por_combinacion' in result:
                max_aciertos = max(result['aciertos_por_combinacion']) if result['aciertos_por_combinacion'] else 0
                total_accuracy += max_aciertos / 6.0
        
        avg_accuracy = total_accuracy / total_sorteos if total_sorteos > 0 else 0.0
        
        # Eficiencia = accuracy / (num_combinations / 30) 
        # Normalizado para que 30 combinaciones sea el baseline
        efficiency_factor = 30 / max(num_combinations, 1)
        efficiency = avg_accuracy * efficiency_factor
        
        return min(1.0, efficiency)
    
    def should_optimize(self) -> bool:
        """Determina si es momento de optimizar"""
        
        if len(self.performance_history) < self.performance_window:
            return False
        
        # Analizar tendencia reciente
        recent_scores = [p.combined_score for p in self.performance_history[-self.performance_window:]]
        
        # Si hay tendencia decreciente o estancamiento, optimizar
        if len(recent_scores) >= 5:
            # Calcular tendencia (regresión lineal simple)
            x = np.arange(len(recent_scores))
            slope = np.polyfit(x, recent_scores, 1)[0]
            
            # Si la tendencia es negativa o muy plana, optimizar
            if slope < -self.optimization_threshold or abs(slope) < self.optimization_threshold / 2:
                logger.info(f"🔍 Optimización necesaria: tendencia = {slope:.4f}")
                return True
        
        # Si el rendimiento está por debajo del promedio histórico
        if len(self.performance_history) > self.performance_window:
            historical_avg = np.mean([p.combined_score for p in self.performance_history[:-self.performance_window]])
            recent_avg = np.mean(recent_scores)
            
            if recent_avg < historical_avg - self.optimization_threshold:
                logger.info(f"🔍 Optimización necesaria: rendimiento por debajo del promedio histórico")
                return True
        
        return False
    
    def optimize_configuration(self, 
                             target_parameters: Optional[List[str]] = None,
                             custom_objective: Optional[callable] = None) -> Dict[str, OptimizationResult]:
        """Ejecuta optimización de configuración"""
        
        logger.info(f"🚀 Iniciando optimización con estrategia {self.optimization_strategy.value}")
        
        # Seleccionar parámetros a optimizar
        if target_parameters is None:
            # Optimizar parámetros más importantes
            target_parameters = [
                name for name, target in self.optimization_targets.items() 
                if target.importance >= 0.7
            ]
        
        optimization_results = {}
        
        # Ejecutar optimización según estrategia
        if self.optimization_strategy == OptimizationStrategy.BAYESIAN:
            optimization_results = self._bayesian_optimization(target_parameters, custom_objective)
        
        elif self.optimization_strategy == OptimizationStrategy.GRID_SEARCH:
            optimization_results = self._grid_search_optimization(target_parameters, custom_objective)
        
        elif self.optimization_strategy == OptimizationStrategy.RANDOM_SEARCH:
            optimization_results = self._random_search_optimization(target_parameters, custom_objective)
        
        elif self.optimization_strategy == OptimizationStrategy.ADAPTIVE:
            optimization_results = self._adaptive_optimization(target_parameters, custom_objective)
        
        else:
            logger.warning(f"⚠️ Estrategia no implementada: {self.optimization_strategy.value}")
            return {}
        
        # Actualizar métricas
        self.optimization_metrics['total_optimizations'] += 1
        successful_improvements = sum(1 for result in optimization_results.values() if result.improvement > 0)
        self.optimization_metrics['successful_improvements'] += successful_improvements
        
        if optimization_results:
            avg_improvement = np.mean([result.improvement for result in optimization_results.values()])
            self.optimization_metrics['average_improvement'] = avg_improvement
            self.optimization_metrics['last_optimization'] = datetime.now().isoformat()
        
        logger.info(f"✅ Optimización completada: {len(optimization_results)} parámetros optimizados")
        logger.info(f"   Mejoras exitosas: {successful_improvements}/{len(optimization_results)}")
        
        return optimization_results
    
    def _bayesian_optimization(self, target_parameters: List[str], custom_objective: Optional[callable]) -> Dict[str, OptimizationResult]:
        """Optimización Bayesiana usando Optuna"""
        
        results = {}
        
        if not OPTUNA_AVAILABLE:
            logger.warning("⚠️ Optuna no disponible, usando random search")
            return self._random_search_optimization(target_parameters, custom_objective)
        
        try:
            # Crear estudio Optuna
            study_name = f"omega_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.optuna_study = optuna.create_study(
                direction='maximize',
                study_name=study_name,
                sampler=optuna.samplers.TPESampler(seed=42)
            )
            
            # Definir función objetivo
            def objective(trial):
                # Sugerir valores para parámetros
                suggested_params = {}
                for param_name in target_parameters:
                    target = self.optimization_targets[param_name]
                    
                    if target.value_type == 'int':
                        suggested_params[param_name] = trial.suggest_int(
                            param_name, int(target.min_value), int(target.max_value)
                        )
                    elif target.value_type == 'float':
                        suggested_params[param_name] = trial.suggest_float(
                            param_name, float(target.min_value), float(target.max_value)
                        )
                    elif target.value_type == 'categorical':
                        suggested_params[param_name] = trial.suggest_categorical(
                            param_name, target.category_options
                        )
                
                # Evaluar configuración
                if custom_objective:
                    return custom_objective(suggested_params)
                else:
                    return self._evaluate_configuration(suggested_params)
            
            # Ejecutar optimización
            self.optuna_study.optimize(objective, n_trials=min(self.max_trials, 50))
            
            # Procesar resultados
            best_params = self.optuna_study.best_params
            best_score = self.optuna_study.best_value
            
            for param_name in target_parameters:
                if param_name in best_params:
                    target = self.optimization_targets[param_name]
                    old_value = target.current_value
                    new_value = best_params[param_name]
                    
                    # Calcular mejora
                    improvement = self._calculate_improvement(param_name, old_value, new_value, best_score)
                    
                    results[param_name] = OptimizationResult(
                        parameter_name=param_name,
                        old_value=old_value,
                        new_value=new_value,
                        improvement=improvement,
                        confidence=0.8,  # Confianza alta para Bayesiana
                        trials_count=len(self.optuna_study.trials),
                        best_score=best_score
                    )
                    
                    # Actualizar objetivo
                    target.current_value = new_value
                    self.current_config[param_name] = new_value
            
        except Exception as e:
            logger.error(f"❌ Error en optimización Bayesiana: {e}")
        
        return results
    
    def _grid_search_optimization(self, target_parameters: List[str], custom_objective: Optional[callable]) -> Dict[str, OptimizationResult]:
        """Optimización por búsqueda en rejilla"""
        
        results = {}
        
        try:
            # Crear rejilla de parámetros (limitada para eficiencia)
            param_grid = {}
            
            for param_name in target_parameters:
                target = self.optimization_targets[param_name]
                
                if target.value_type == 'int':
                    # 5 valores distribuidos uniformemente
                    values = np.linspace(target.min_value, target.max_value, 5, dtype=int)
                    param_grid[param_name] = list(set(values))  # Eliminar duplicados
                
                elif target.value_type == 'float':
                    # 5 valores distribuidos uniformemente
                    values = np.linspace(target.min_value, target.max_value, 5)
                    param_grid[param_name] = values.tolist()
                
                elif target.value_type == 'categorical':
                    param_grid[param_name] = target.category_options
            
            # Generar combinaciones (limitadas)
            grid = ParameterGrid(param_grid)
            max_combinations = min(self.max_trials, 100)
            
            best_score = -np.inf
            best_params = {}
            
            # Evaluar combinaciones
            for i, params in enumerate(grid):
                if i >= max_combinations:
                    break
                
                if custom_objective:
                    score = custom_objective(params)
                else:
                    score = self._evaluate_configuration(params)
                
                if score > best_score:
                    best_score = score
                    best_params = params.copy()
            
            # Procesar resultados
            for param_name in target_parameters:
                if param_name in best_params:
                    target = self.optimization_targets[param_name]
                    old_value = target.current_value
                    new_value = best_params[param_name]
                    
                    improvement = self._calculate_improvement(param_name, old_value, new_value, best_score)
                    
                    results[param_name] = OptimizationResult(
                        parameter_name=param_name,
                        old_value=old_value,
                        new_value=new_value,
                        improvement=improvement,
                        confidence=0.7,  # Confianza moderada para grid search
                        trials_count=min(i + 1, max_combinations),
                        best_score=best_score
                    )
                    
                    # Actualizar objetivo
                    target.current_value = new_value
                    self.current_config[param_name] = new_value
            
        except Exception as e:
            logger.error(f"❌ Error en grid search: {e}")
        
        return results
    
    def _random_search_optimization(self, target_parameters: List[str], custom_objective: Optional[callable]) -> Dict[str, OptimizationResult]:
        """Optimización por búsqueda aleatoria"""
        
        results = {}
        
        try:
            best_score = -np.inf
            best_params = {}
            trials = min(self.max_trials, 50)
            
            # Ejecutar búsqueda aleatoria
            for trial in range(trials):
                # Generar configuración aleatoria
                random_params = {}
                
                for param_name in target_parameters:
                    target = self.optimization_targets[param_name]
                    
                    if target.value_type == 'int':
                        random_params[param_name] = np.random.randint(
                            int(target.min_value), int(target.max_value) + 1
                        )
                    elif target.value_type == 'float':
                        random_params[param_name] = np.random.uniform(
                            target.min_value, target.max_value
                        )
                    elif target.value_type == 'categorical':
                        random_params[param_name] = np.random.choice(target.category_options)
                
                # Evaluar configuración
                if custom_objective:
                    score = custom_objective(random_params)
                else:
                    score = self._evaluate_configuration(random_params)
                
                if score > best_score:
                    best_score = score
                    best_params = random_params.copy()
            
            # Procesar resultados
            for param_name in target_parameters:
                if param_name in best_params:
                    target = self.optimization_targets[param_name]
                    old_value = target.current_value
                    new_value = best_params[param_name]
                    
                    improvement = self._calculate_improvement(param_name, old_value, new_value, best_score)
                    
                    results[param_name] = OptimizationResult(
                        parameter_name=param_name,
                        old_value=old_value,
                        new_value=new_value,
                        improvement=improvement,
                        confidence=0.6,  # Confianza moderada-baja para random search
                        trials_count=trials,
                        best_score=best_score
                    )
                    
                    # Actualizar objetivo
                    target.current_value = new_value
                    self.current_config[param_name] = new_value
            
        except Exception as e:
            logger.error(f"❌ Error en random search: {e}")
        
        return results
    
    def _adaptive_optimization(self, target_parameters: List[str], custom_objective: Optional[callable]) -> Dict[str, OptimizationResult]:
        """Optimización adaptativa (combina múltiples estrategias)"""
        
        results = {}
        
        # Estrategia adaptativa: usar diferentes métodos según situación
        recent_performance = self.performance_history[-self.performance_window:]
        
        if len(recent_performance) < 10:
            # Pocos datos: usar random search
            logger.info("🎲 Usando random search (pocos datos)")
            return self._random_search_optimization(target_parameters, custom_objective)
        
        elif len(self.performance_history) < 50:
            # Datos moderados: usar grid search
            logger.info("🔍 Usando grid search (datos moderados)")
            return self._grid_search_optimization(target_parameters, custom_objective)
        
        else:
            # Muchos datos: usar optimización Bayesiana
            logger.info("🧠 Usando optimización Bayesiana (muchos datos)")
            return self._bayesian_optimization(target_parameters, custom_objective)
    
    def _evaluate_configuration(self, params: Dict[str, Any]) -> float:
        """Evalúa configuración basada en historial de rendimiento"""
        
        # Simular evaluación basada en similitud con configuraciones históricas exitosas
        if not self.performance_history:
            return 0.5  # Score neutro
        
        # Encontrar configuraciones históricas similares
        similar_scores = []
        
        for hist in self.performance_history:
            similarity = self._calculate_configuration_similarity(params, hist.parameters)
            
            if similarity > 0.7:  # Alta similitud
                # Ponderar score por similitud
                weighted_score = hist.combined_score * similarity
                similar_scores.append(weighted_score)
        
        if similar_scores:
            # Promedio ponderado de configuraciones similares
            return np.mean(similar_scores)
        else:
            # Sin configuraciones similares: score basado en heurísticas
            return self._heuristic_evaluation(params)
    
    def _calculate_configuration_similarity(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> float:
        """Calcula similitud entre dos configuraciones"""
        
        common_params = set(params1.keys()) & set(params2.keys())
        
        if not common_params:
            return 0.0
        
        similarities = []
        
        for param in common_params:
            target = self.optimization_targets.get(param)
            if not target:
                continue
            
            val1 = params1[param]
            val2 = params2[param]
            
            if target.value_type in ['int', 'float']:
                # Similitud numérica normalizada
                range_size = target.max_value - target.min_value
                diff = abs(val1 - val2) / range_size if range_size > 0 else 0
                similarity = 1.0 - diff
            
            elif target.value_type == 'categorical':
                # Similitud categórica
                similarity = 1.0 if val1 == val2 else 0.0
            
            else:
                similarity = 0.5  # Score neutro
            
            # Ponderar por importancia del parámetro
            weighted_similarity = similarity * target.importance
            similarities.append(weighted_similarity)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _heuristic_evaluation(self, params: Dict[str, Any]) -> float:
        """Evaluación heurística de configuración con pesos adaptativos"""
        
        score = 0.5  # Base score
        
        # Obtener pesos adaptativos basados en rendimiento histórico
        weights = self._get_adaptive_heuristic_weights()
        
        # 1. Balance exploración-explotación
        exploration = params.get('exploration_factor', 0.3)
        if 0.2 <= exploration <= 0.5:  # Rango óptimo
            score += weights['exploration'] * 0.2
        elif 0.1 <= exploration <= 0.6:  # Rango aceptable
            score += weights['exploration'] * 0.1
        
        # 2. Número de combinaciones razonable
        num_combinations = params.get('num_combinations', 30)
        if 20 <= num_combinations <= 50:  # Rango eficiente
            score += weights['efficiency'] * 0.2
        elif 15 <= num_combinations <= 70:  # Rango aceptable
            score += weights['efficiency'] * 0.1
        
        # 3. Diversidad adecuada
        diversity_weight = params.get('diversity_weight', 0.5)
        if 0.3 <= diversity_weight <= 0.7:  # Balance adecuado
            score += weights['diversity'] * 0.15
        elif 0.2 <= diversity_weight <= 0.8:  # Rango aceptable
            score += weights['diversity'] * 0.075
        
        # 4. Filtros no muy restrictivos
        range_max = params.get('range_filter_max', 200)
        if range_max >= 180:  # No muy restrictivo
            score += weights['coverage'] * 0.1
        elif range_max >= 160:  # Moderadamente restrictivo
            score += weights['coverage'] * 0.05
        
        # 5. Pesos de modelos balanceados
        model_weights = [
            params.get('lstm_weight', 1.0),
            params.get('transformer_weight', 1.0),
            params.get('clustering_weight', 1.0)
        ]
        
        weight_variance = np.var(model_weights)
        if weight_variance < 0.2:  # Pesos relativamente balanceados
            score += weights['balance'] * 0.1
        elif weight_variance < 0.4:  # Moderadamente balanceados
            score += weights['balance'] * 0.05
        
        # 6. Configuración SVI apropiada
        svi_profile = params.get('svi_profile', 'default')
        if svi_profile in ['default', 'conservative']:  # Perfiles más seguros
            score += weights['stability'] * 0.08
        
        return min(1.0, score)
    
    def _get_adaptive_heuristic_weights(self) -> Dict[str, float]:
        """Obtiene pesos adaptativos para heurísticas basados en rendimiento histórico"""
        
        default_weights = {
            'exploration': 1.0,
            'efficiency': 1.0,
            'diversity': 1.0,
            'coverage': 1.0,
            'balance': 1.0,
            'stability': 1.0
        }
        
        if len(self.performance_history) < 5:
            return default_weights
        
        # Analizar qué métricas han sido más importantes en el rendimiento histórico
        recent_performance = self.performance_history[-10:]
        
        # Correlación simple entre métricas y rendimiento combinado
        accuracy_scores = [p.accuracy_score for p in recent_performance]
        diversity_scores = [p.diversity_score for p in recent_performance]
        coverage_scores = [p.coverage_score for p in recent_performance]
        efficiency_scores = [p.efficiency_score for p in recent_performance]
        consistency_scores = [p.consistency_score for p in recent_performance]
        combined_scores = [p.combined_score for p in recent_performance]
        
        # Calcular importancia relativa (correlación simple)
        weights = default_weights.copy()
        
        try:
            if np.var(combined_scores) > 0:
                # Usar correlación como proxy de importancia
                accuracy_corr = abs(np.corrcoef(accuracy_scores, combined_scores)[0, 1]) if len(accuracy_scores) > 1 else 1.0
                diversity_corr = abs(np.corrcoef(diversity_scores, combined_scores)[0, 1]) if len(diversity_scores) > 1 else 1.0
                coverage_corr = abs(np.corrcoef(coverage_scores, combined_scores)[0, 1]) if len(coverage_scores) > 1 else 1.0
                efficiency_corr = abs(np.corrcoef(efficiency_scores, combined_scores)[0, 1]) if len(efficiency_scores) > 1 else 1.0
                consistency_corr = abs(np.corrcoef(consistency_scores, combined_scores)[0, 1]) if len(consistency_scores) > 1 else 1.0
                
                # Actualizar pesos con suavizado
                alpha = 0.3  # Factor de suavizado
                weights['exploration'] = (1 - alpha) * weights['exploration'] + alpha * (accuracy_corr + efficiency_corr) / 2
                weights['efficiency'] = (1 - alpha) * weights['efficiency'] + alpha * efficiency_corr
                weights['diversity'] = (1 - alpha) * weights['diversity'] + alpha * diversity_corr
                weights['coverage'] = (1 - alpha) * weights['coverage'] + alpha * coverage_corr
                weights['balance'] = (1 - alpha) * weights['balance'] + alpha * (accuracy_corr + consistency_corr) / 2
                weights['stability'] = (1 - alpha) * weights['stability'] + alpha * consistency_corr
                
        except (ValueError, np.linalg.LinAlgError):
            # En caso de error, usar pesos por defecto
            pass
        
        return weights
    
    def _calculate_improvement(self, param_name: str, old_value: Any, new_value: Any, new_score: float) -> float:
        """Calcula mejora estimada para un parámetro"""
        
        if not self.performance_history:
            return 0.0
        
        # Comparar con rendimiento promedio histórico
        historical_avg = np.mean([p.combined_score for p in self.performance_history[-20:]])
        
        # Mejora = (nuevo_score - promedio_histórico) / promedio_histórico
        if historical_avg > 0:
            improvement = (new_score - historical_avg) / historical_avg
        else:
            improvement = 0.0
        
        return improvement
    
    def apply_optimized_configuration(self, omega_system) -> Dict[str, Any]:
        """Aplica configuración optimizada al sistema OMEGA"""
        
        applied_changes = []
        
        try:
            # Aplicar parámetros de generación
            if hasattr(omega_system, 'generation_config'):
                gen_params = {
                    'num_combinations': self.current_config.get('num_combinations'),
                    'exploration_factor': self.current_config.get('exploration_factor'),
                    'diversity_weight': self.current_config.get('diversity_weight')
                }
                omega_system.generation_config.update({k: v for k, v in gen_params.items() if v is not None})
                applied_changes.extend([k for k, v in gen_params.items() if v is not None])
            
            # Aplicar parámetros de filtros
            if hasattr(omega_system, 'filter_config'):
                filter_params = {
                    'range_filter_min': self.current_config.get('range_filter_min'),
                    'range_filter_max': self.current_config.get('range_filter_max'),
                    'sum_filter_tolerance': self.current_config.get('sum_filter_tolerance'),
                    'gap_filter_max': self.current_config.get('gap_filter_max')
                }
                omega_system.filter_config.update({k: v for k, v in filter_params.items() if v is not None})
                applied_changes.extend([k for k, v in filter_params.items() if v is not None])
            
            # Aplicar pesos de modelos
            if hasattr(omega_system, 'model_weights'):
                weight_params = {
                    'lstm_v2': self.current_config.get('lstm_weight'),
                    'transformer': self.current_config.get('transformer_weight'),
                    'clustering': self.current_config.get('clustering_weight')
                }
                omega_system.model_weights.update({k: v for k, v in weight_params.items() if v is not None})
                applied_changes.extend([k for k, v in weight_params.items() if v is not None])
            
            # Aplicar configuración SVI
            svi_profile = self.current_config.get('svi_profile')
            if svi_profile and hasattr(omega_system, 'set_svi_profile'):
                omega_system.set_svi_profile(svi_profile)
                applied_changes.append('svi_profile')
            
            logger.info(f"✅ Configuración optimizada aplicada: {len(applied_changes)} parámetros")
            
        except Exception as e:
            logger.error(f"❌ Error aplicando configuración optimizada: {e}")
        
        return {
            'applied_changes': applied_changes,
            'configuration': self.current_config.copy(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de optimización"""
        
        summary = {
            'strategy': self.optimization_strategy.value,
            'total_optimizations': self.optimization_metrics['total_optimizations'],
            'successful_improvements': self.optimization_metrics['successful_improvements'],
            'success_rate': 0.0,
            'average_improvement': self.optimization_metrics['average_improvement'],
            'performance_history_size': len(self.performance_history),
            'current_configuration': self.current_config.copy(),
            'optimization_targets_count': len(self.optimization_targets),
            'last_optimization': self.optimization_metrics['last_optimization']
        }
        
        if self.optimization_metrics['total_optimizations'] > 0:
            summary['success_rate'] = (
                self.optimization_metrics['successful_improvements'] / 
                self.optimization_metrics['total_optimizations']
            )
        
        # Estadísticas de rendimiento reciente
        if self.performance_history:
            recent_scores = [p.combined_score for p in self.performance_history[-10:]]
            summary['recent_performance'] = {
                'average_score': np.mean(recent_scores),
                'best_score': max(recent_scores),
                'worst_score': min(recent_scores),
                'trend': 'improving' if len(recent_scores) >= 2 and recent_scores[-1] > recent_scores[0] else 'stable'
            }
        
        return summary

# Funciones de utilidad
def create_auto_optimizer(strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE) -> AutoConfigOptimizer:
    """Crea optimizador automático"""
    return AutoConfigOptimizer(optimization_strategy=strategy)

def simulate_optimization_cycle(optimizer: AutoConfigOptimizer, cycles: int = 5) -> List[Dict[str, Any]]:
    """Simula múltiples ciclos de optimización"""
    
    results = []
    
    for cycle in range(cycles):
        # Simular datos de rendimiento
        fake_sorteo_results = []
        for _ in range(5):
            fake_result = {
                'aciertos_por_combinacion': [
                    np.random.randint(0, 4) for _ in range(5)  # 5 combinaciones
                ],
                'combinaciones_predichas': [
                    sorted(np.random.choice(range(1, 41), 6, replace=False).tolist())
                    for _ in range(5)
                ]
            }
            fake_sorteo_results.append(fake_result)
        
        # Registrar rendimiento
        performance = optimizer.record_performance(
            parameters=optimizer.current_config.copy(),
            sorteo_results=fake_sorteo_results,
            notes=f"Simulación ciclo {cycle + 1}"
        )
        
        # Verificar si necesita optimización
        if optimizer.should_optimize():
            # Ejecutar optimización
            optimization_results = optimizer.optimize_configuration()
            
            results.append({
                'cycle': cycle + 1,
                'performance_score': performance.combined_score,
                'optimization_executed': True,
                'parameters_optimized': len(optimization_results),
                'optimization_results': {k: asdict(v) for k, v in optimization_results.items()}
            })
        else:
            results.append({
                'cycle': cycle + 1,
                'performance_score': performance.combined_score,
                'optimization_executed': False,
                'parameters_optimized': 0,
                'optimization_results': {}
            })
    
    return results

if __name__ == "__main__":
    # Demo del optimizador automático
    print("⚙️ Demo Auto Config Optimizer")
    
    # Crear optimizador
    optimizer = create_auto_optimizer(OptimizationStrategy.ADAPTIVE)
    
    print(f"🎯 Optimizador inicializado con {len(optimizer.optimization_targets)} parámetros objetivo")
    
    # Simular ciclos de optimización
    print(f"\n🔄 Simulando 5 ciclos de optimización...")
    results = simulate_optimization_cycle(optimizer, cycles=5)
    
    for result in results:
        print(f"\nCiclo {result['cycle']}:")
        print(f"   Score: {result['performance_score']:.3f}")
        print(f"   Optimización: {'Sí' if result['optimization_executed'] else 'No'}")
        if result['optimization_executed']:
            print(f"   Parámetros optimizados: {result['parameters_optimized']}")
    
    # Resumen final
    summary = optimizer.get_optimization_summary()
    print(f"\n📊 Resumen de optimización:")
    print(f"   Estrategia: {summary['strategy']}")
    print(f"   Optimizaciones totales: {summary['total_optimizations']}")
    print(f"   Tasa de éxito: {summary['success_rate']:.1%}")
    print(f"   Mejora promedio: {summary['average_improvement']:.3f}")
    
    if 'recent_performance' in summary:
        perf = summary['recent_performance']
        print(f"   Score promedio reciente: {perf['average_score']:.3f}")
        print(f"   Tendencia: {perf['trend']}")
