#!/usr/bin/env python3
"""
Sistema de Aprendizaje Adaptativo Completo para OMEGA PRO AI
Integrador que une todos los módulos de aprendizaje adaptativo
"""

import asyncio
import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# Importar validaciones mejoradas
try:
    from modules.utils.validation_enhanced import OmegaValidator, ValidationError, validate_and_log_combinations
    ENHANCED_VALIDATION_AVAILABLE = True
except ImportError:
    ENHANCED_VALIDATION_AVAILABLE = False
    logging.warning("⚠️ Validaciones mejoradas no disponibles, usando validación básica")

# Importar todos los módulos de aprendizaje
try:
    from modules.aprendizaje_omega import create_omega_learning_system, OmegaLearningSystem
    from modules.auto_config_optimizer import create_auto_optimizer, AutoConfigOptimizer, OptimizationStrategy
    from modules.ensemble_trainer import create_ensemble_trainer, EnsembleTrainer, EnsembleStrategy
    from modules.meta_learning_controller import create_meta_controller, MetaLearningController
    from modules.perfilador_dinamico import create_dynamic_profiler, DynamicProfiler
    ADAPTIVE_MODULES_AVAILABLE = True
except ImportError as e:
    ADAPTIVE_MODULES_AVAILABLE = False
    logging.warning(f"⚠️ Módulos adaptativos no disponibles: {e}")

logger = logging.getLogger(__name__)

class AdaptiveLearningSystem:
    """Sistema completo de aprendizaje adaptativo"""
    
    def __init__(self, 
                 enable_omega_learning: bool = True,
                 enable_auto_optimizer: bool = True,
                 enable_ensemble: bool = True,
                 enable_meta_controller: bool = True,
                 enable_profiler: bool = True):
        
        self.components_enabled = {
            'omega_learning': enable_omega_learning,
            'auto_optimizer': enable_auto_optimizer,
            'ensemble': enable_ensemble,
            'meta_controller': enable_meta_controller,
            'profiler': enable_profiler
        }
        
        # Inicializar componentes
        self.omega_learning = None
        self.auto_optimizer = None
        self.ensemble_trainer = None
        self.meta_controller = None
        self.profiler = None
        
        if not ADAPTIVE_MODULES_AVAILABLE:
            logger.error("❌ Módulos adaptativos no disponibles")
            return
        
        self._initialize_components()
        
        # Estado del sistema
        self.learning_cycles = []
        self.optimization_history = []
        self.performance_tracking = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Configuración del ciclo de aprendizaje
        self.learning_config = {
            'auto_optimization_frequency': 5,  # Cada 5 sorteos
            'ensemble_retrain_frequency': 10,  # Cada 10 sorteos
            'performance_evaluation_window': 20,  # Últimos 20 sorteos
            'adaptation_threshold': 0.05,  # Umbral de mejora mínima
            'emergency_mode_threshold': 0.3  # Umbral para modo emergencia
        }
        
        logger.info("🌟 Sistema de Aprendizaje Adaptativo inicializado")
        logger.info(f"   Componentes activos: {sum(self.components_enabled.values())}/5")
    
    def _initialize_components(self):
        """Inicializa todos los componentes del sistema"""
        
        if self.components_enabled['omega_learning']:
            try:
                self.omega_learning = create_omega_learning_system(memory_size=200)
                logger.info("✅ Aprendizaje OMEGA inicializado")
            except Exception as e:
                logger.error(f"❌ Error inicializando Aprendizaje OMEGA: {e}")
                self.components_enabled['omega_learning'] = False
        
        if self.components_enabled['auto_optimizer']:
            try:
                self.auto_optimizer = create_auto_optimizer(OptimizationStrategy.ADAPTIVE)
                logger.info("✅ Auto Optimizer inicializado")
            except Exception as e:
                logger.error(f"❌ Error inicializando Auto Optimizer: {e}")
                self.components_enabled['auto_optimizer'] = False
        
        if self.components_enabled['ensemble']:
            try:
                self.ensemble_trainer = create_ensemble_trainer(EnsembleStrategy.STACKING)
                logger.info("✅ Ensemble Trainer inicializado")
            except Exception as e:
                logger.error(f"❌ Error inicializando Ensemble Trainer: {e}")
                self.components_enabled['ensemble'] = False
        
        if self.components_enabled['meta_controller']:
            try:
                self.meta_controller = create_meta_controller()
                logger.info("✅ Meta Controller inicializado")
            except Exception as e:
                logger.error(f"❌ Error inicializando Meta Controller: {e}")
                self.components_enabled['meta_controller'] = False
        
        if self.components_enabled['profiler']:
            try:
                self.profiler = create_dynamic_profiler()
                logger.info("✅ Dynamic Profiler inicializado")
            except Exception as e:
                logger.error(f"❌ Error inicializando Dynamic Profiler: {e}")
                self.components_enabled['profiler'] = False
    
    def _validate_cycle_inputs(self, 
                               sorteo_date: datetime,
                               winning_combination: List[int], 
                               predicted_combinations: List[List[int]],
                               system_config: Dict[str, Any]) -> Tuple[List[int], List[List[int]], Dict[str, Any]]:
        """
        Valida todas las entradas del ciclo de aprendizaje
        
        Args:
            sorteo_date: Fecha del sorteo
            winning_combination: Combinación ganadora oficial
            predicted_combinations: Combinaciones predichas por los modelos
            system_config: Configuración del sistema
            
        Returns:
            Tuple[List[int], List[List[int]], Dict[str, Any]]: Datos validados
        """
        if not ENHANCED_VALIDATION_AVAILABLE:
            # Validación básica fallback
            logger.warning("⚠️ Usando validación básica (módulo mejorado no disponible)")
            return winning_combination, predicted_combinations, system_config
        
        try:
            # 1. Validar fecha
            if not isinstance(sorteo_date, datetime):
                raise ValidationError(f"sorteo_date debe ser datetime, recibido: {type(sorteo_date)}")
            
            # 2. Validar combinación ganadora
            validated_winning = OmegaValidator.validate_sorteo_result(winning_combination)
            
            # 3. Validar combinaciones predichas
            if not predicted_combinations:
                logger.warning("⚠️ Lista de combinaciones predichas vacía")
                validated_predicted = []
            else:
                validated_predicted, errors = OmegaValidator.validate_combinations_batch(
                    predicted_combinations,
                    allow_failures=True,
                    max_failure_rate=0.3  # Permitir hasta 30% de fallas
                )
                
                if errors:
                    logger.warning(f"⚠️ {len(errors)} combinaciones con errores de validación (de {len(predicted_combinations)})")
                    for error in errors[:3]:  # Mostrar solo primeros 3
                        logger.warning(f"  - {error}")
            
            # 4. Validar configuración del sistema
            if not isinstance(system_config, dict):
                logger.warning("⚠️ system_config debe ser diccionario, usando configuración vacía")
                system_config = {}
            
            # Asegurar parámetros mínimos
            default_config = {
                'regime': 'A',
                'profile': 'moderado',
                'model_weights': {},
                'filters': {}
            }
            
            for key, default_value in default_config.items():
                if key not in system_config:
                    system_config[key] = default_value
            
            logger.info(f"✅ Validación exitosa: {len(validated_predicted)}/{len(predicted_combinations) if predicted_combinations else 0} combinaciones válidas")
            return validated_winning, validated_predicted, system_config
            
        except ValidationError as e:
            logger.error(f"❌ Error de validación crítico: {e}")
            # En caso de error crítico, usar valores por defecto
            return winning_combination, [], {'regime': 'A', 'profile': 'moderado'}
        except Exception as e:
            logger.error(f"❌ Error inesperado en validación: {e}")
            # Fallback a datos originales si algo falla
            return winning_combination, predicted_combinations, system_config
    
    async def process_sorteo_cycle(self, 
                                 sorteo_date: datetime,
                                 winning_combination: List[int],
                                 predicted_combinations: List[List[int]],
                                 system_config: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un ciclo completo de sorteo con aprendizaje adaptativo"""
        
        logger.info(f"🔄 Procesando ciclo de sorteo {sorteo_date.strftime('%Y-%m-%d')}")
        
        # VALIDACIÓN ROBUSTA DE ENTRADAS
        try:
            winning_combination, predicted_combinations, system_config = self._validate_cycle_inputs(
                sorteo_date, winning_combination, predicted_combinations, system_config
            )
            logger.info("✅ Validación de entradas completada")
        except Exception as e:
            logger.error(f"❌ Error crítico en validación de entradas: {e}")
            # Retornar resultado básico en caso de falla
            return {
                'sorteo_date': sorteo_date.isoformat(),
                'validation_error': str(e),
                'components_results': {},
                'adaptations_made': [],
                'performance_metrics': {'combined_score': 0.0},
                'processing_time': 0.0
            }
        
        cycle_start = datetime.now()
        cycle_results = {
            'sorteo_date': sorteo_date.isoformat(),
            'winning_combination': winning_combination,
            'predicted_combinations': predicted_combinations,
            'components_results': {},
            'adaptations_made': [],
            'performance_metrics': {},
            'timestamp': cycle_start.isoformat()
        }
        
        try:
            # 1. APRENDIZAJE POST-SORTEO (OMEGA Learning)
            if self.omega_learning:
                logger.info("🧠 Ejecutando aprendizaje post-sorteo...")
                omega_results = self.omega_learning.process_sorteo_result(
                    fecha=sorteo_date,
                    combinacion_ganadora=winning_combination,
                    combinaciones_predichas=predicted_combinations,
                    modelo_config=system_config
                )
                cycle_results['components_results']['omega_learning'] = omega_results
                
                # Aplicar configuración adaptativa si hay cambios significativos
                if len(omega_results['learning_actions']) > 0:
                    adapted_config = self.omega_learning.get_current_config()
                    cycle_results['adaptations_made'].append({
                        'component': 'omega_learning',
                        'type': 'configuration_update',
                        'changes': len(omega_results['learning_actions']),
                        'new_config': adapted_config
                    })
            
            # 2. EVALUACIÓN DE RENDIMIENTO PARA OPTIMIZACIÓN
            if self.auto_optimizer:
                logger.info("⚙️ Evaluando necesidad de optimización...")
                
                # Registrar rendimiento actual
                performance = self.auto_optimizer.record_performance(
                    parameters=system_config,
                    sorteo_results=[{
                        'aciertos_por_combinacion': [
                            len(set(pred) & set(winning_combination)) 
                            for pred in predicted_combinations
                        ],
                        'combinaciones_predichas': predicted_combinations
                    }],
                    notes=f"Sorteo {sorteo_date.strftime('%Y-%m-%d')}"
                )
                
                cycle_results['components_results']['auto_optimizer'] = {
                    'performance_recorded': True,
                    'combined_score': performance.combined_score
                }
                
                # Verificar si necesita optimización
                if self.auto_optimizer.should_optimize():
                    logger.info("🚀 Ejecutando optimización automática...")
                    optimization_results = self.auto_optimizer.optimize_configuration()
                    
                    if optimization_results:
                        cycle_results['adaptations_made'].append({
                            'component': 'auto_optimizer',
                            'type': 'parameter_optimization',
                            'parameters_optimized': len(optimization_results),
                            'optimization_results': {k: {
                                'old_value': v.old_value,
                                'new_value': v.new_value,
                                'improvement': v.improvement
                            } for k, v in optimization_results.items()}
                        })
            
            # 3. ANÁLISIS DE CONTEXTO Y PERFIL
            if self.meta_controller and self.profiler:
                logger.info("🎯 Analizando contexto y perfil...")
                
                # Análizar contexto con meta-controller
                historical_context = predicted_combinations[-50:] if len(predicted_combinations) >= 50 else predicted_combinations
                context, optimal_weights = self.meta_controller.analyze_current_context(historical_context)
                
                # Predecir perfil futuro
                profile_prediction = self.profiler.predict_profile(historical_context)
                
                cycle_results['components_results']['context_analysis'] = {
                    'regime': context.regime.value,
                    'entropy': context.entropy,
                    'optimal_weights': optimal_weights,
                    'predicted_profile': profile_prediction.profile.value,
                    'profile_confidence': profile_prediction.confidence
                }
                
                # Registrar performance en meta-controller
                max_aciertos = max([len(set(pred) & set(winning_combination)) for pred in predicted_combinations]) if predicted_combinations else 0
                for model_name in optimal_weights.keys():
                    model_results = {
                        'accuracy': max_aciertos / 6.0,
                        'precision': np.random.uniform(0.5, 0.8),  # Simulado
                        'recall': np.random.uniform(0.5, 0.8),     # Simulado
                        'f1_score': np.random.uniform(0.5, 0.8)    # Simulado
                    }
                    self.meta_controller.record_model_performance(model_name, context, model_results)
            
            # 4. ENTRENAMIENTO DE ENSEMBLE (PERIÓDICO)
            cycle_number = len(self.learning_cycles) + 1
            if (self.ensemble_trainer and 
                cycle_number % self.learning_config['ensemble_retrain_frequency'] == 0):
                
                logger.info("🏗️ Re-entrenando ensemble...")
                
                # Simular datos históricos para entrenamiento
                historical_data = []
                for i in range(max(100, len(predicted_combinations))):
                    if i < len(predicted_combinations):
                        historical_data.append(predicted_combinations[i])
                    else:
                        # Generar datos sintéticos
                        combo = sorted(np.random.choice(range(1, 41), 6, replace=False).tolist())
                        historical_data.append(combo)
                
                try:
                    ensemble_results = self.ensemble_trainer.train_ensemble(historical_data)
                    cycle_results['components_results']['ensemble_training'] = {
                        'training_completed': True,
                        'accuracy': ensemble_results['ensemble_performance']['accuracy'],
                        'training_time': ensemble_results['training_time']
                    }
                    
                    cycle_results['adaptations_made'].append({
                        'component': 'ensemble_trainer',
                        'type': 'model_retraining',
                        'accuracy_achieved': ensemble_results['ensemble_performance']['accuracy']
                    })
                    
                except Exception as e:
                    logger.error(f"❌ Error en entrenamiento de ensemble: {e}")
                    cycle_results['components_results']['ensemble_training'] = {
                        'training_completed': False,
                        'error': str(e)
                    }
            
            # 5. MÉTRICAS DE PERFORMANCE DEL CICLO
            cycle_performance = self._calculate_cycle_performance(
                winning_combination, predicted_combinations, cycle_results
            )
            cycle_results['performance_metrics'] = cycle_performance
            
            # 6. DETECCIÓN DE MODO EMERGENCIA
            emergency_mode = self._check_emergency_mode(cycle_performance)
            if emergency_mode:
                logger.warning("🚨 Modo emergencia activado")
                emergency_actions = await self._activate_emergency_mode(cycle_results)
                cycle_results['emergency_actions'] = emergency_actions
            
            # 7. GUARDAR ESTADO DEL CICLO
            cycle_results['processing_time'] = (datetime.now() - cycle_start).total_seconds()
            self.learning_cycles.append(cycle_results)
            
            # Mantener historial limitado
            if len(self.learning_cycles) > self.learning_config['performance_evaluation_window'] * 2:
                self.learning_cycles = self.learning_cycles[-self.learning_config['performance_evaluation_window'] * 2:]
            
            logger.info(f"✅ Ciclo de aprendizaje completado en {cycle_results['processing_time']:.2f}s")
            logger.info(f"   Adaptaciones realizadas: {len(cycle_results['adaptations_made'])}")
            logger.info(f"   Score de performance: {cycle_performance.get('combined_score', 0):.3f}")
            
            return cycle_results
            
        except Exception as e:
            logger.error(f"❌ Error en ciclo de aprendizaje: {e}")
            cycle_results['error'] = str(e)
            cycle_results['processing_time'] = (datetime.now() - cycle_start).total_seconds()
            return cycle_results
    
    def _calculate_cycle_performance(self, 
                                   winning_combination: List[int],
                                   predicted_combinations: List[List[int]],
                                   cycle_results: Dict[str, Any]) -> Dict[str, float]:
        """Calcula métricas de performance del ciclo"""
        
        if not predicted_combinations:
            return {'combined_score': 0.0, 'accuracy': 0.0, 'adaptivity': 0.0}
        
        # 1. Accuracy de predicciones
        accuracies = []
        for pred in predicted_combinations:
            accuracy = len(set(pred) & set(winning_combination)) / 6.0
            accuracies.append(accuracy)
        
        max_accuracy = max(accuracies)
        avg_accuracy = np.mean(accuracies)
        
        # 2. Score de adaptividad (cuántas adaptaciones se hicieron)
        adaptations_count = len(cycle_results.get('adaptations_made', []))
        adaptivity_score = min(1.0, adaptations_count / 3.0)  # Máximo esperado: 3 adaptaciones
        
        # 3. Score de diversidad
        all_predicted_numbers = set()
        for pred in predicted_combinations:
            all_predicted_numbers.update(pred)
        diversity_score = len(all_predicted_numbers) / 40.0  # Diversidad sobre 40 números
        
        # 4. Score de consistencia (basado en componentes activos)
        components_active = sum(self.components_enabled.values())
        consistency_score = components_active / 5.0
        
        # 5. Score combinado
        combined_score = (
            max_accuracy * 0.4 +
            avg_accuracy * 0.2 +
            adaptivity_score * 0.2 +
            diversity_score * 0.1 +
            consistency_score * 0.1
        )
        
        return {
            'combined_score': combined_score,
            'max_accuracy': max_accuracy,
            'avg_accuracy': avg_accuracy,
            'adaptivity_score': adaptivity_score,
            'diversity_score': diversity_score,
            'consistency_score': consistency_score,
            'components_active': components_active
        }
    
    def _check_emergency_mode(self, performance: Dict[str, float]) -> bool:
        """Verifica si se debe activar modo emergencia"""
        
        # Activar si performance muy baja
        if performance.get('combined_score', 0) < self.learning_config['emergency_mode_threshold']:
            return True
        
        # Activar si tendencia negativa en últimos ciclos
        if len(self.learning_cycles) >= 3:
            recent_scores = [
                cycle['performance_metrics'].get('combined_score', 0)
                for cycle in self.learning_cycles[-3:]
            ]
            
            if all(recent_scores[i] > recent_scores[i+1] for i in range(len(recent_scores)-1)):
                return True  # Tendencia decreciente
        
        return False
    
    async def _activate_emergency_mode(self, cycle_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Activa modo emergencia con acciones correctivas"""
        
        emergency_actions = []
        
        # 1. Reinicializar configuraciones
        if self.omega_learning:
            # Reset a configuración conservadora
            self.omega_learning.adaptive_config.learning_rate *= 0.5  # Reducir agresividad
            emergency_actions.append({
                'action': 'reduce_learning_rate',
                'component': 'omega_learning',
                'description': 'Reducir tasa de aprendizaje para estabilidad'
            })
        
        # 2. Activar todos los boosts disponibles
        if self.omega_learning:
            for boost_name in self.omega_learning.boost_system:
                if not self.omega_learning.boost_system[boost_name]['active']:
                    self.omega_learning.boost_system[boost_name]['active'] = True
                    self.omega_learning.boost_system[boost_name]['strength'] = 1.5
                    emergency_actions.append({
                        'action': 'activate_boost',
                        'component': 'omega_learning',
                        'boost': boost_name,
                        'description': f'Activar boost {boost_name} en modo emergencia'
                    })
        
        # 3. Forzar optimización completa
        if self.auto_optimizer:
            try:
                optimization_results = self.auto_optimizer.optimize_configuration()
                if optimization_results:
                    emergency_actions.append({
                        'action': 'force_optimization',
                        'component': 'auto_optimizer',
                        'parameters_optimized': len(optimization_results),
                        'description': 'Optimización forzada en modo emergencia'
                    })
            except Exception as e:
                logger.error(f"❌ Error en optimización de emergencia: {e}")
        
        # 4. Cambiar estrategia de ensemble
        if self.ensemble_trainer and self.ensemble_trainer.is_trained:
            # Cambiar a estrategia más conservadora
            original_strategy = self.ensemble_trainer.strategy
            self.ensemble_trainer.strategy = EnsembleStrategy.VOTING  # Más estable
            emergency_actions.append({
                'action': 'change_ensemble_strategy',
                'component': 'ensemble_trainer',
                'old_strategy': original_strategy.value,
                'new_strategy': EnsembleStrategy.VOTING.value,
                'description': 'Cambiar a ensemble voting para estabilidad'
            })
        
        logger.warning(f"🚨 Modo emergencia: {len(emergency_actions)} acciones ejecutadas")
        
        return emergency_actions
    
    async def generate_adaptive_predictions(self, 
                                          historical_data: List[List[int]],
                                          num_predictions: int = 5) -> Dict[str, Any]:
        """Genera predicciones usando todo el sistema adaptativo"""
        
        logger.info(f"🎯 Generando predicciones adaptativas...")
        
        prediction_start = datetime.now()
        results = {
            'predictions': [],
            'component_contributions': {},
            'adaptation_info': {},
            'confidence_metrics': {},
            'timestamp': prediction_start.isoformat()
        }
        
        try:
            all_predictions = []
            
            # 1. Predicciones del Ensemble (si está entrenado)
            if self.ensemble_trainer and self.ensemble_trainer.is_trained:
                ensemble_preds = self.ensemble_trainer.predict_combinations(
                    historical_data[-20:], num_predictions
                )
                all_predictions.extend(ensemble_preds)
                results['component_contributions']['ensemble'] = len(ensemble_preds)
            
            # 2. Predicciones basadas en configuración adaptativa
            if self.omega_learning:
                adaptive_config = self.omega_learning.get_current_config()
                
                # Generar predicciones usando configuración adaptativa
                for i in range(num_predictions):
                    pred = self._generate_adaptive_prediction(historical_data, adaptive_config, i)
                    all_predictions.append(pred)
                
                results['component_contributions']['omega_learning'] = num_predictions
                results['adaptation_info']['current_config'] = adaptive_config
            
            # 3. Análisis de contexto para refinamiento
            if self.meta_controller:
                context, optimal_weights = self.meta_controller.analyze_current_context(historical_data)
                
                # Aplicar pesos de contexto a predicciones
                for pred in all_predictions:
                    if 'confidence' in pred:
                        model_source = pred.get('source', 'unknown')
                        weight_boost = optimal_weights.get(model_source, 1.0)
                        pred['confidence'] = min(1.0, pred['confidence'] * weight_boost)
                        pred['context_boost'] = weight_boost
                
                results['adaptation_info']['context'] = {
                    'regime': context.regime.value,
                    'optimal_weights': optimal_weights
                }
            
            # 4. Predicción de perfil para filtrado
            if self.profiler:
                profile_prediction = self.profiler.predict_profile(historical_data)
                
                # Filtrar predicciones según perfil predicho
                filtered_predictions = self._filter_by_profile(all_predictions, profile_prediction)
                all_predictions = filtered_predictions
                
                results['adaptation_info']['profile'] = {
                    'predicted_profile': profile_prediction.profile.value,
                    'confidence': profile_prediction.confidence
                }
            
            # 5. Seleccionar mejores predicciones
            # Ordenar por confianza y diversidad
            scored_predictions = []
            for pred in all_predictions:
                confidence = pred.get('confidence', 0.5)
                diversity_bonus = self._calculate_diversity_bonus(pred['combination'], all_predictions)
                total_score = confidence + diversity_bonus * 0.1
                
                scored_predictions.append((total_score, pred))
            
            # Ordenar y seleccionar top predicciones
            scored_predictions.sort(key=lambda x: x[0], reverse=True)
            final_predictions = [pred for score, pred in scored_predictions[:num_predictions]]
            
            # 6. Calcular métricas de confianza
            confidences = [pred.get('confidence', 0.5) for pred in final_predictions]
            results['confidence_metrics'] = {
                'average_confidence': np.mean(confidences),
                'min_confidence': min(confidences),
                'max_confidence': max(confidences),
                'confidence_variance': np.var(confidences)
            }
            
            # 7. Agregar metadata a predicciones finales
            for i, pred in enumerate(final_predictions):
                pred['rank'] = i + 1
                pred['total_score'] = scored_predictions[i][0]
                pred['adaptive_system_id'] = self.session_id
                pred['components_used'] = [
                    comp for comp, enabled in self.components_enabled.items() if enabled
                ]
            
            results['predictions'] = final_predictions
            results['processing_time'] = (datetime.now() - prediction_start).total_seconds()
            
            logger.info(f"✅ Predicciones adaptativas generadas en {results['processing_time']:.2f}s")
            logger.info(f"   Predicciones finales: {len(final_predictions)}")
            logger.info(f"   Confianza promedio: {results['confidence_metrics']['average_confidence']:.1%}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error generando predicciones adaptativas: {e}")
            return self._generate_fallback_predictions(historical_data, num_predictions)
    
    def _generate_adaptive_prediction(self, 
                                    historical_data: List[List[int]], 
                                    adaptive_config: Dict[str, Any],
                                    seed: int) -> Dict[str, Any]:
        """Genera predicción usando configuración adaptativa"""
        
        np.random.seed(seed + 100)
        
        # Usar parámetros de generación adaptativos
        gen_params = adaptive_config.get('generation_params', {})
        exploration_factor = gen_params.get('exploration_factor', 0.3)
        diversity_weight = gen_params.get('diversity_weight', 0.5)
        
        # Analizar datos recientes
        recent_data = historical_data[-10:] if len(historical_data) >= 10 else historical_data
        all_recent_numbers = np.concatenate(recent_data) if recent_data else []
        
        # Crear distribución de probabilidades
        probs = np.ones(40) * (exploration_factor / 40)  # Base exploratoria
        
        if len(all_recent_numbers) > 0:
            # Añadir información histórica
            unique_numbers, counts = np.unique(all_recent_numbers, return_counts=True)
            
            for num, count in zip(unique_numbers, counts):
                if 1 <= num <= 40:
                    # Balance entre frecuencia histórica y exploración
                    freq_weight = (1 - exploration_factor) * count / len(all_recent_numbers)
                    probs[num - 1] += freq_weight
        
        # Normalizar
        probs = probs / np.sum(probs)
        
        # Generar combinación
        combination = []
        available = list(range(1, 41))
        
        for position in range(6):
            if not available:
                break
            
            # Probabilidades para números disponibles
            available_probs = [probs[num - 1] for num in available]
            available_probs = np.array(available_probs) / np.sum(available_probs)
            
            # Añadir factor de diversidad
            if position > 0:
                for i, num in enumerate(available):
                    # Penalizar números muy cercanos a los ya seleccionados
                    min_distance = min(abs(num - selected) for selected in combination)
                    if min_distance < 3:
                        available_probs[i] *= (1 - diversity_weight)
                
                # Re-normalizar
                available_probs = available_probs / np.sum(available_probs)
            
            # Seleccionar número
            chosen_idx = np.random.choice(len(available), p=available_probs)
            chosen_num = available[chosen_idx]
            
            combination.append(chosen_num)
            available.remove(chosen_num)
        
        # Calcular confianza basada en configuración
        model_weights = adaptive_config.get('model_weights', {})
        avg_weight = np.mean(list(model_weights.values())) if model_weights else 1.0
        confidence = min(1.0, avg_weight / 1.5 + 0.3)  # Normalizar confianza
        
        return {
            'combination': sorted(combination),
            'confidence': confidence,
            'source': 'adaptive_system',
            'exploration_factor': exploration_factor,
            'diversity_weight': diversity_weight,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_diversity_bonus(self, combination: List[int], all_predictions: List[Dict[str, Any]]) -> float:
        """Calcula bonus por diversidad de la combinación"""
        
        if len(all_predictions) <= 1:
            return 0.0
        
        # Calcular similitud promedio con otras predicciones
        similarities = []
        
        for pred in all_predictions:
            other_combo = pred.get('combination', [])
            if other_combo != combination:
                # Similitud = números en común / 6
                similarity = len(set(combination) & set(other_combo)) / 6.0
                similarities.append(similarity)
        
        if similarities:
            avg_similarity = np.mean(similarities)
            diversity_bonus = 1.0 - avg_similarity  # Más diverso = mayor bonus
            return diversity_bonus
        
        return 0.0
    
    def _filter_by_profile(self, predictions: List[Dict[str, Any]], profile_prediction) -> List[Dict[str, Any]]:
        """Filtra predicciones según perfil predicho"""
        
        # Por simplicidad, solo ajustar confianza según perfil
        profile_confidence = profile_prediction.confidence
        
        filtered_predictions = []
        for pred in predictions:
            adjusted_pred = pred.copy()
            
            # Ajustar confianza según perfil
            profile_boost = profile_confidence * 0.2  # Boost máximo 20%
            adjusted_pred['confidence'] = min(1.0, pred.get('confidence', 0.5) + profile_boost)
            adjusted_pred['profile_boost'] = profile_boost
            
            filtered_predictions.append(adjusted_pred)
        
        return filtered_predictions
    
    def _generate_fallback_predictions(self, historical_data: List[List[int]], num_predictions: int) -> Dict[str, Any]:
        """Genera predicciones de fallback"""
        
        predictions = []
        
        for i in range(num_predictions):
            combination = sorted(np.random.choice(range(1, 41), 6, replace=False).tolist())
            
            prediction = {
                'combination': combination,
                'confidence': 0.4,
                'source': 'adaptive_fallback',
                'rank': i + 1,
                'timestamp': datetime.now().isoformat()
            }
            
            predictions.append(prediction)
        
        return {
            'predictions': predictions,
            'component_contributions': {},
            'adaptation_info': {'error': 'Fallback mode activated'},
            'confidence_metrics': {
                'average_confidence': 0.4,
                'min_confidence': 0.4,
                'max_confidence': 0.4,
                'confidence_variance': 0.0
            },
            'processing_time': 0.1,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del sistema adaptativo"""
        
        status = {
            'session_id': self.session_id,
            'components_status': self.components_enabled,
            'learning_cycles_processed': len(self.learning_cycles),
            'configuration': self.learning_config,
            'timestamp': datetime.now().isoformat()
        }
        
        # Estado de componentes individuales
        if self.omega_learning:
            status['omega_learning_summary'] = self.omega_learning.get_learning_summary()
        
        if self.auto_optimizer:
            status['optimizer_summary'] = self.auto_optimizer.get_optimization_summary()
        
        if self.ensemble_trainer:
            status['ensemble_summary'] = self.ensemble_trainer.get_ensemble_summary()
        
        if self.meta_controller:
            status['meta_controller_summary'] = self.meta_controller.get_performance_summary()
        
        if self.profiler:
            status['profiler_summary'] = self.profiler.get_profiling_summary()
        
        # Estadísticas de rendimiento
        if self.learning_cycles:
            recent_cycles = self.learning_cycles[-10:]
            performance_scores = [
                cycle['performance_metrics'].get('combined_score', 0)
                for cycle in recent_cycles
            ]
            
            status['performance_statistics'] = {
                'recent_cycles': len(recent_cycles),
                'average_performance': np.mean(performance_scores),
                'best_performance': max(performance_scores) if performance_scores else 0,
                'performance_trend': self._calculate_trend(performance_scores),
                'total_adaptations': sum(
                    len(cycle.get('adaptations_made', [])) for cycle in recent_cycles
                )
            }
        
        return status
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calcula tendencia de una serie de valores"""
        
        if len(values) < 3:
            return 'insufficient_data'
        
        # Regresión lineal simple
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.01:
            return 'improving'
        elif slope < -0.01:
            return 'declining'
        else:
            return 'stable'
    
    def export_system_state(self, filepath: str):
        """Exporta estado completo del sistema"""
        
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'session_id': self.session_id,
                'system_status': self.get_system_status(),
                'learning_cycles': self.learning_cycles[-50:],  # Últimos 50 ciclos
                'configuration': self.learning_config
            }
            
            # Serializar datos
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return str(obj)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=json_serializer, ensure_ascii=False)
            
            logger.info(f"💾 Estado del sistema exportado a {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error exportando estado: {e}")

# Funciones de utilidad
def create_adaptive_learning_system(enable_all: bool = True) -> AdaptiveLearningSystem:
    """Crea sistema completo de aprendizaje adaptativo"""
    return AdaptiveLearningSystem(
        enable_omega_learning=enable_all,
        enable_auto_optimizer=enable_all,
        enable_ensemble=enable_all,
        enable_meta_controller=enable_all,
        enable_profiler=enable_all
    )

async def simulate_adaptive_cycle(system: AdaptiveLearningSystem, 
                                cycles: int = 5) -> List[Dict[str, Any]]:
    """Simula múltiples ciclos de aprendizaje adaptativo"""
    
    results = []
    
    for cycle in range(cycles):
        # Simular sorteo
        sorteo_date = datetime.now() - timedelta(days=cycles - cycle)
        winning_combination = sorted(np.random.choice(range(1, 41), 6, replace=False).tolist())
        
        # Simular predicciones del sistema
        predicted_combinations = []
        for _ in range(5):
            pred = sorted(np.random.choice(range(1, 41), 6, replace=False).tolist())
            predicted_combinations.append(pred)
        
        # Configuración simulada
        system_config = {
            'num_combinations': 30,
            'exploration_factor': 0.3,
            'model_weights': {
                'lstm_v2': 1.0,
                'transformer': 1.1,
                'clustering': 0.9
            }
        }
        
        # Procesar ciclo
        cycle_result = await system.process_sorteo_cycle(
            sorteo_date, winning_combination, predicted_combinations, system_config
        )
        
        results.append(cycle_result)
    
    return results

if __name__ == "__main__":
    # Demo del sistema adaptativo completo
    async def main():
        print("🌟 Demo Sistema de Aprendizaje Adaptativo Completo")
        
        if not ADAPTIVE_MODULES_AVAILABLE:
            print("❌ Módulos adaptativos no disponibles")
            return
        
        # Crear sistema
        system = create_adaptive_learning_system()
        
        print(f"📊 Sistema inicializado con {sum(system.components_enabled.values())}/5 componentes")
        
        # Simular ciclos de aprendizaje
        print(f"\n🔄 Simulando 3 ciclos de aprendizaje adaptativo...")
        results = await simulate_adaptive_cycle(system, cycles=3)
        
        for i, result in enumerate(results, 1):
            print(f"\nCiclo {i}:")
            print(f"   Ganadora: {' - '.join(map(str, result['winning_combination']))}")
            print(f"   Adaptaciones: {len(result['adaptations_made'])}")
            print(f"   Score: {result['performance_metrics'].get('combined_score', 0):.3f}")
            
            if result['adaptations_made']:
                print(f"   Ajustes realizados:")
                for adaptation in result['adaptations_made'][:2]:  # Mostrar primeros 2
                    print(f"     • {adaptation['component']}: {adaptation['type']}")
        
        # Generar predicciones adaptativas
        print(f"\n🎯 Generando predicciones adaptativas...")
        historical_data = [result['winning_combination'] for result in results]
        
        prediction_results = await system.generate_adaptive_predictions(historical_data, 3)
        
        print(f"✅ Predicciones generadas:")
        for pred in prediction_results['predictions']:
            combo = pred['combination']
            confidence = pred['confidence']
            components = ', '.join(pred.get('components_used', []))
            print(f"   {' - '.join(map(str, combo))} (Confianza: {confidence:.1%})")
            print(f"     Componentes: {components}")
        
        # Estado del sistema
        status = system.get_system_status()
        print(f"\n📈 Estado del sistema:")
        print(f"   Ciclos procesados: {status['learning_cycles_processed']}")
        
        if 'performance_statistics' in status:
            perf = status['performance_statistics']
            print(f"   Performance promedio: {perf['average_performance']:.3f}")
            print(f"   Tendencia: {perf['performance_trend']}")
            print(f"   Adaptaciones totales: {perf['total_adaptations']}")
    
    # Ejecutar demo
    if ADAPTIVE_MODULES_AVAILABLE:
        asyncio.run(main())
    else:
        print("❌ Sistema adaptativo no disponible para demo")
