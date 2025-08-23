#!/usr/bin/env python3
"""
🧪 OMEGA A/B Testing System - Sistema de Testing A/B para Modelos
Comparación estadística de modelos con split de tráfico inteligente
"""

import asyncio
import time
import random
import uuid
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from scipy import stats
import json
from pathlib import Path

from src.utils.logger_factory import LoggerFactory, performance_monitor
from src.monitoring.metrics_collector import MetricsCollector
from src.services.cache_service import CacheService

class ExperimentStatus(Enum):
    """Estados de experimentos A/B"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class ABTestVariant:
    """Variante de test A/B"""
    variant_id: str
    name: str
    description: str
    model_config: Dict[str, Any]
    traffic_allocation: float  # 0.0 - 1.0
    is_control: bool = False

@dataclass
class ABTestResult:
    """Resultado individual de test A/B"""
    experiment_id: str
    variant_id: str
    user_id: str
    session_id: str
    timestamp: float
    prediction_time: float
    accuracy_score: Optional[float] = None
    user_satisfaction: Optional[float] = None
    conversion: bool = False
    metadata: Dict[str, Any] = None

@dataclass
class ABTestMetrics:
    """Métricas de variante en test A/B"""
    variant_id: str
    sample_size: int
    conversion_rate: float
    average_prediction_time: float
    average_accuracy: float
    confidence_interval: Tuple[float, float]
    statistical_significance: float
    
class ABTestExperiment:
    """Experimento A/B individual"""
    
    def __init__(self,
                 experiment_id: str,
                 name: str,
                 description: str,
                 variants: List[ABTestVariant],
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None,
                 minimum_sample_size: int = 100,
                 confidence_level: float = 0.95):
        
        self.experiment_id = experiment_id
        self.name = name
        self.description = description
        self.variants = {v.variant_id: v for v in variants}
        self.start_date = start_date or datetime.now()
        self.end_date = end_date
        self.minimum_sample_size = minimum_sample_size
        self.confidence_level = confidence_level
        
        self.status = ExperimentStatus.DRAFT
        self.results: List[ABTestResult] = []
        
        self.logger = LoggerFactory.get_logger(f"ABTest_{experiment_id}")
        
        # Validar configuración
        self._validate_experiment()
    
    def _validate_experiment(self):
        """Valida configuración del experimento"""
        if len(self.variants) < 2:
            raise ValueError("Experiment must have at least 2 variants")
        
        total_allocation = sum(v.traffic_allocation for v in self.variants.values())
        if not (0.95 <= total_allocation <= 1.05):  # Allow small floating point errors
            raise ValueError(f"Traffic allocation must sum to 1.0, got {total_allocation}")
        
        control_variants = [v for v in self.variants.values() if v.is_control]
        if len(control_variants) != 1:
            raise ValueError("Experiment must have exactly one control variant")
    
    def get_variant_for_user(self, user_id: str) -> ABTestVariant:
        """Asigna variante a usuario usando hash consistente"""
        if self.status != ExperimentStatus.RUNNING:
            # Si no está corriendo, retornar control
            control_variant = next(v for v in self.variants.values() if v.is_control)
            return control_variant
        
        # Hash consistente basado en user_id y experiment_id
        hash_input = f"{user_id}_{self.experiment_id}"
        user_hash = hash(hash_input) % 10000 / 10000.0  # 0.0-1.0
        
        # Asignar basado en traffic allocation
        cumulative_allocation = 0.0
        for variant in self.variants.values():
            cumulative_allocation += variant.traffic_allocation
            if user_hash <= cumulative_allocation:
                return variant
        
        # Fallback to control
        return next(v for v in self.variants.values() if v.is_control)
    
    def record_result(self, result: ABTestResult):
        """Registra resultado de test"""
        if result.variant_id not in self.variants:
            raise ValueError(f"Unknown variant: {result.variant_id}")
        
        self.results.append(result)
        self.logger.debug(f"Result recorded for variant {result.variant_id}")
    
    def get_metrics(self) -> Dict[str, ABTestMetrics]:
        """Calcula métricas estadísticas por variante"""
        metrics = {}
        
        for variant_id, variant in self.variants.items():
            variant_results = [r for r in self.results if r.variant_id == variant_id]
            
            if not variant_results:
                metrics[variant_id] = ABTestMetrics(
                    variant_id=variant_id,
                    sample_size=0,
                    conversion_rate=0.0,
                    average_prediction_time=0.0,
                    average_accuracy=0.0,
                    confidence_interval=(0.0, 0.0),
                    statistical_significance=0.0
                )
                continue
            
            # Calcular métricas básicas
            sample_size = len(variant_results)
            conversions = sum(1 for r in variant_results if r.conversion)
            conversion_rate = conversions / sample_size
            
            avg_prediction_time = np.mean([r.prediction_time for r in variant_results])
            accuracies = [r.accuracy_score for r in variant_results if r.accuracy_score is not None]
            avg_accuracy = np.mean(accuracies) if accuracies else 0.0
            
            # Intervalo de confianza para conversion rate
            ci_lower, ci_upper = self._calculate_confidence_interval(
                conversions, sample_size, self.confidence_level
            )
            
            # Significancia estadística vs control
            statistical_significance = self._calculate_statistical_significance(variant_id)
            
            metrics[variant_id] = ABTestMetrics(
                variant_id=variant_id,
                sample_size=sample_size,
                conversion_rate=conversion_rate,
                average_prediction_time=avg_prediction_time,
                average_accuracy=avg_accuracy,
                confidence_interval=(ci_lower, ci_upper),
                statistical_significance=statistical_significance
            )
        
        return metrics
    
    def _calculate_confidence_interval(self, conversions: int, sample_size: int, 
                                     confidence_level: float) -> Tuple[float, float]:
        """Calcula intervalo de confianza para tasa de conversión"""
        if sample_size == 0:
            return (0.0, 0.0)
        
        proportion = conversions / sample_size
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        
        # Wilson score interval (más robusto que normal approximation)
        n = sample_size
        p = proportion
        
        center = (p + z_score**2 / (2*n)) / (1 + z_score**2 / n)
        margin = z_score * np.sqrt(p * (1-p) / n + z_score**2 / (4*n**2)) / (1 + z_score**2 / n)
        
        return (max(0, center - margin), min(1, center + margin))
    
    def _calculate_statistical_significance(self, variant_id: str) -> float:
        """Calcula p-value comparado con control"""
        if variant_id == next(v.variant_id for v in self.variants.values() if v.is_control):
            return 1.0  # Control vs itself
        
        control_id = next(v.variant_id for v in self.variants.values() if v.is_control)
        
        variant_results = [r for r in self.results if r.variant_id == variant_id]
        control_results = [r for r in self.results if r.variant_id == control_id]
        
        if len(variant_results) < 10 or len(control_results) < 10:
            return 1.0  # Not enough data
        
        # Chi-square test for conversion rates
        variant_conversions = sum(1 for r in variant_results if r.conversion)
        variant_total = len(variant_results)
        control_conversions = sum(1 for r in control_results if r.conversion)
        control_total = len(control_results)
        
        # Contingency table
        observed = np.array([
            [variant_conversions, variant_total - variant_conversions],
            [control_conversions, control_total - control_conversions]
        ])
        
        try:
            chi2, p_value, _, _ = stats.chi2_contingency(observed)
            return p_value
        except:
            return 1.0
    
    def is_statistically_significant(self, variant_id: str, alpha: float = 0.05) -> bool:
        """Verifica si una variante es estadísticamente significativa"""
        p_value = self._calculate_statistical_significance(variant_id)
        return p_value < alpha
    
    def get_winning_variant(self) -> Optional[str]:
        """Determina variante ganadora basada en métricas"""
        metrics = self.get_metrics()
        
        # Filtrar variantes con suficientes datos
        valid_variants = {
            vid: m for vid, m in metrics.items() 
            if m.sample_size >= self.minimum_sample_size
        }
        
        if len(valid_variants) < 2:
            return None
        
        # Encontrar la mejor variante (mayor conversion rate)
        best_variant = max(valid_variants.items(), key=lambda x: x[1].conversion_rate)
        best_variant_id, best_metrics = best_variant
        
        # Verificar significancia estadística
        if self.is_statistically_significant(best_variant_id):
            return best_variant_id
        
        return None

class ABTestingSystem:
    """
    Sistema completo de A/B Testing para modelos de IA
    """
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        self.logger = LoggerFactory.get_logger("ABTestingSystem")
        self.metrics = MetricsCollector()
        
        # Storage
        self.experiments: Dict[str, ABTestExperiment] = {}
        self.active_experiments: Dict[str, str] = {}  # user_id -> experiment_id
        
        # Configuration
        self.config = {
            'max_concurrent_experiments': 5,
            'default_minimum_sample_size': 100,
            'default_confidence_level': 0.95,
            'experiment_timeout_days': 30,
            'results_cache_ttl': 3600  # 1 hour
        }
        
        self.logger.info("🧪 A/B Testing System initialized")
    
    def create_experiment(self,
                         name: str,
                         description: str,
                         variants: List[Dict[str, Any]],
                         duration_days: Optional[int] = None,
                         **kwargs) -> str:
        """Crea nuevo experimento A/B"""
        
        experiment_id = f"exp_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Convertir dicts a ABTestVariant objects
        variant_objects = []
        for i, variant_dict in enumerate(variants):
            variant_obj = ABTestVariant(
                variant_id=variant_dict.get('variant_id', f'variant_{i}'),
                name=variant_dict['name'],
                description=variant_dict.get('description', ''),
                model_config=variant_dict['model_config'],
                traffic_allocation=variant_dict['traffic_allocation'],
                is_control=variant_dict.get('is_control', i == 0)  # First is control by default
            )
            variant_objects.append(variant_obj)
        
        # Configurar fechas
        start_date = datetime.now()
        end_date = None
        if duration_days:
            end_date = start_date + timedelta(days=duration_days)
        
        # Crear experimento
        experiment = ABTestExperiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            variants=variant_objects,
            start_date=start_date,
            end_date=end_date,
            **kwargs
        )
        
        self.experiments[experiment_id] = experiment
        
        self.logger.info(f"🧪 Created experiment: {experiment_id} ({name})")
        self.metrics.increment("ab_experiments_created")
        
        return experiment_id
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Inicia experimento A/B"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        experiment = self.experiments[experiment_id]
        
        # Verificar límites
        running_experiments = [
            exp for exp in self.experiments.values() 
            if exp.status == ExperimentStatus.RUNNING
        ]
        
        if len(running_experiments) >= self.config['max_concurrent_experiments']:
            self.logger.warning(f"Cannot start experiment: max concurrent limit reached")
            return False
        
        experiment.status = ExperimentStatus.RUNNING
        experiment.start_date = datetime.now()
        
        self.logger.info(f"🚀 Started experiment: {experiment_id}")
        self.metrics.increment("ab_experiments_started")
        
        return True
    
    def stop_experiment(self, experiment_id: str, reason: str = "manual") -> bool:
        """Detiene experimento A/B"""
        if experiment_id not in self.experiments:
            return False
        
        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.COMPLETED
        
        self.logger.info(f"⏹️ Stopped experiment: {experiment_id} (reason: {reason})")
        self.metrics.increment("ab_experiments_stopped")
        
        return True
    
    @performance_monitor()
    async def get_model_config_for_user(self, 
                                       user_id: str, 
                                       default_config: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Obtiene configuración de modelo para usuario según experimentos A/B activos
        
        Returns:
            Tuple[config, experiment_id] donde experiment_id es None si no hay experimento
        """
        
        # Verificar si usuario tiene experimento asignado
        if user_id in self.active_experiments:
            experiment_id = self.active_experiments[user_id]
            
            if experiment_id in self.experiments:
                experiment = self.experiments[experiment_id]
                
                if experiment.status == ExperimentStatus.RUNNING:
                    variant = experiment.get_variant_for_user(user_id)
                    
                    self.metrics.increment(
                        "ab_variant_assignments",
                        labels={
                            "experiment": experiment_id,
                            "variant": variant.variant_id
                        }
                    )
                    
                    return variant.model_config, experiment_id
        
        # Buscar nuevo experimento para usuario
        for experiment in self.experiments.values():
            if experiment.status == ExperimentStatus.RUNNING:
                variant = experiment.get_variant_for_user(user_id)
                self.active_experiments[user_id] = experiment.experiment_id
                
                self.metrics.increment(
                    "ab_variant_assignments",
                    labels={
                        "experiment": experiment.experiment_id,
                        "variant": variant.variant_id
                    }
                )
                
                return variant.model_config, experiment.experiment_id
        
        # No hay experimentos activos
        return default_config, None
    
    async def record_prediction_result(self,
                                     user_id: str,
                                     session_id: str,
                                     prediction_time: float,
                                     accuracy_score: Optional[float] = None,
                                     user_satisfaction: Optional[float] = None,
                                     conversion: bool = False,
                                     metadata: Optional[Dict[str, Any]] = None):
        """Registra resultado de predicción para A/B testing"""
        
        if user_id not in self.active_experiments:
            return  # Usuario no está en ningún experimento
        
        experiment_id = self.active_experiments[user_id]
        
        if experiment_id not in self.experiments:
            return
        
        experiment = self.experiments[experiment_id]
        if experiment.status != ExperimentStatus.RUNNING:
            return
        
        variant = experiment.get_variant_for_user(user_id)
        
        result = ABTestResult(
            experiment_id=experiment_id,
            variant_id=variant.variant_id,
            user_id=user_id,
            session_id=session_id,
            timestamp=time.time(),
            prediction_time=prediction_time,
            accuracy_score=accuracy_score,
            user_satisfaction=user_satisfaction,
            conversion=conversion,
            metadata=metadata or {}
        )
        
        experiment.record_result(result)
        
        self.metrics.increment(
            "ab_results_recorded",
            labels={
                "experiment": experiment_id,
                "variant": variant.variant_id
            }
        )
        
        # Auto-evaluation para stopping rules
        await self._evaluate_experiment_stopping_rules(experiment_id)
    
    async def _evaluate_experiment_stopping_rules(self, experiment_id: str):
        """Evalúa reglas de parada automática para experimento"""
        experiment = self.experiments[experiment_id]
        
        # Rule 1: Timeout
        if experiment.end_date and datetime.now() > experiment.end_date:
            self.stop_experiment(experiment_id, "timeout")
            return
        
        # Rule 2: Minimum sample size reached and significant result
        metrics = experiment.get_metrics()
        
        # Verificar si todas las variantes tienen suficientes datos
        all_variants_ready = all(
            m.sample_size >= experiment.minimum_sample_size 
            for m in metrics.values()
        )
        
        if not all_variants_ready:
            return
        
        # Rule 3: Statistical significance achieved
        winning_variant = experiment.get_winning_variant()
        if winning_variant:
            self.logger.info(
                f"🏆 Experiment {experiment_id} has clear winner: {winning_variant}"
            )
            
            # Optionally auto-stop if very significant (p < 0.001)
            p_value = experiment._calculate_statistical_significance(winning_variant)
            if p_value < 0.001:
                self.stop_experiment(experiment_id, "highly_significant_result")
    
    def get_experiment_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene resultados detallados de experimento"""
        if experiment_id not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_id]
        metrics = experiment.get_metrics()
        winning_variant = experiment.get_winning_variant()
        
        results = {
            'experiment_id': experiment_id,
            'name': experiment.name,
            'description': experiment.description,
            'status': experiment.status.value,
            'start_date': experiment.start_date.isoformat(),
            'end_date': experiment.end_date.isoformat() if experiment.end_date else None,
            'total_results': len(experiment.results),
            'winning_variant': winning_variant,
            'variants': {},
            'summary': {}
        }
        
        # Detalles por variante
        for variant_id, variant in experiment.variants.items():
            variant_metrics = metrics[variant_id]
            
            results['variants'][variant_id] = {
                'name': variant.name,
                'description': variant.description,
                'is_control': variant.is_control,
                'traffic_allocation': variant.traffic_allocation,
                'metrics': asdict(variant_metrics),
                'is_winner': variant_id == winning_variant,
                'is_significant': experiment.is_statistically_significant(variant_id)
            }
        
        # Resumen estadístico
        if len(metrics) >= 2:
            control_metrics = next(
                (m for vid, m in metrics.items() 
                 if experiment.variants[vid].is_control), 
                None
            )
            
            if control_metrics:
                best_variant_metrics = max(metrics.values(), key=lambda m: m.conversion_rate)
                
                if best_variant_metrics != control_metrics:
                    lift = ((best_variant_metrics.conversion_rate - control_metrics.conversion_rate) 
                           / control_metrics.conversion_rate * 100)
                    
                    results['summary'] = {
                        'conversion_lift_percent': lift,
                        'statistical_confidence': (1 - best_variant_metrics.statistical_significance) * 100,
                        'recommendation': 'implement' if winning_variant else 'continue_testing'
                    }
        
        return results
    
    def list_experiments(self, status: Optional[ExperimentStatus] = None) -> List[Dict[str, Any]]:
        """Lista todos los experimentos"""
        experiments = []
        
        for exp_id, experiment in self.experiments.items():
            if status is None or experiment.status == status:
                experiments.append({
                    'experiment_id': exp_id,
                    'name': experiment.name,
                    'status': experiment.status.value,
                    'variants_count': len(experiment.variants),
                    'results_count': len(experiment.results),
                    'start_date': experiment.start_date.isoformat() if experiment.start_date else None,
                    'end_date': experiment.end_date.isoformat() if experiment.end_date else None
                })
        
        return sorted(experiments, key=lambda x: x['start_date'] or '', reverse=True)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema A/B"""
        running_experiments = sum(
            1 for exp in self.experiments.values() 
            if exp.status == ExperimentStatus.RUNNING
        )
        
        total_results = sum(len(exp.results) for exp in self.experiments.values())
        active_users = len(self.active_experiments)
        
        return {
            'total_experiments': len(self.experiments),
            'running_experiments': running_experiments,
            'active_users': active_users,
            'total_results_recorded': total_results,
            'experiments_by_status': {
                status.value: sum(1 for exp in self.experiments.values() if exp.status == status)
                for status in ExperimentStatus
            }
        }

# Decorador para auto A/B testing
def ab_test_model(ab_system: ABTestingSystem):
    """Decorador para aplicar A/B testing automático a modelos"""
    def decorator(model_func):
        async def wrapper(user_id: str, *args, **kwargs):
            # Obtener configuración para usuario
            default_config = kwargs.get('config', {})
            config, experiment_id = await ab_system.get_model_config_for_user(
                user_id, default_config
            )
            
            # Actualizar kwargs con nueva configuración
            kwargs['config'] = config
            
            # Ejecutar modelo
            start_time = time.time()
            result = await model_func(*args, **kwargs)
            prediction_time = time.time() - start_time
            
            # Registrar resultado si hay experimento activo
            if experiment_id:
                await ab_system.record_prediction_result(
                    user_id=user_id,
                    session_id=kwargs.get('session_id', 'unknown'),
                    prediction_time=prediction_time,
                    accuracy_score=result.get('accuracy_score'),
                    conversion=result.get('conversion', False)
                )
            
            return result
        
        return wrapper
    return decorator