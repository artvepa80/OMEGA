#!/usr/bin/env python3
"""
🔄 OMEGA Prediction Pipeline - Pipeline Optimizado de Predicción
Maneja el flujo completo de generación de predicciones
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.services.prediction_service import PredictionService
from src.services.data_service import DataService
from src.ai.ensemble_manager import EnsembleManager
from src.ai.learning_engine import LearningEngine
from src.monitoring.metrics_collector import MetricsCollector
from src.utils.logger_factory import LoggerFactory

@dataclass
class PredictionResult:
    """Resultado de predicción estructurado"""
    combination: List[int]
    confidence: float
    source_model: str
    svi_score: float
    metadata: Dict[str, Any]

class PredictionPipeline:
    """
    Pipeline optimizado para generación de predicciones
    """
    
    def __init__(self, 
                 data_service: DataService,
                 prediction_service: PredictionService,
                 ensemble_manager: EnsembleManager,
                 learning_engine: LearningEngine,
                 metrics: MetricsCollector):
        
        self.data_service = data_service
        self.prediction_service = prediction_service
        self.ensemble_manager = ensemble_manager
        self.learning_engine = learning_engine
        self.metrics = metrics
        self.logger = LoggerFactory.get_logger("PredictionPipeline")
    
    async def generate_predictions(self, 
                                 historical_data: List[Dict],
                                 target_count: int = 8) -> List[PredictionResult]:
        """
        Genera predicciones usando todos los modelos disponibles
        
        Args:
            historical_data: Datos históricos procesados
            target_count: Número objetivo de predicciones
            
        Returns:
            Lista de predicciones optimizadas
        """
        self.logger.info(f"🎯 Generando {target_count} predicciones con pipeline optimizado")
        
        try:
            # Fase 1: Obtener modelos activos
            active_models = self.ensemble_manager.get_active_models()
            self.logger.info(f"🤖 Modelos activos: {len(active_models)}")
            
            # Fase 2: Generar predicciones en paralelo
            prediction_tasks = []
            for model_name in active_models:
                task = self._generate_model_predictions(
                    model_name, historical_data, target_count
                )
                prediction_tasks.append(task)
            
            # Ejecutar predicciones en paralelo
            model_results = await asyncio.gather(*prediction_tasks, return_exceptions=True)
            
            # Fase 3: Procesar resultados
            all_predictions = []
            for model_name, result in zip(active_models, model_results):
                if isinstance(result, Exception):
                    self.logger.warning(f"⚠️ Error en modelo {model_name}: {result}")
                    continue
                
                all_predictions.extend(result)
            
            # Fase 4: Aplicar ensemble y filtros
            ensemble_predictions = await self._apply_ensemble_logic(all_predictions)
            
            # Fase 5: Calcular SVI y scoring
            scored_predictions = await self._calculate_svi_scores(ensemble_predictions)
            
            # Fase 6: Seleccionar mejores predicciones
            final_predictions = await self._select_best_predictions(
                scored_predictions, target_count
            )
            
            # Métricas
            self.metrics.record("predictions_generated", len(final_predictions))
            self.metrics.record("models_successful", len([r for r in model_results if not isinstance(r, Exception)]))
            
            self.logger.info(f"✅ Pipeline completado - {len(final_predictions)} predicciones finales")
            return final_predictions
            
        except Exception as e:
            self.logger.error(f"❌ Error en pipeline: {e}")
            self.metrics.record_error("pipeline_error", str(e))
            raise
    
    async def _generate_model_predictions(self, 
                                        model_name: str,
                                        historical_data: List[Dict],
                                        count: int) -> List[PredictionResult]:
        """Genera predicciones de un modelo específico"""
        try:
            self.logger.debug(f"🔮 Generando predicciones con {model_name}")
            
            # Obtener modelo lazy-loaded
            model = self.ensemble_manager.get_model(model_name)
            
            # Generar predicciones
            raw_predictions = await model.predict(historical_data, count)
            
            # Convertir a formato estructurado
            predictions = []
            for pred in raw_predictions:
                prediction_result = PredictionResult(
                    combination=pred.get('combination', []),
                    confidence=pred.get('confidence', 0.5),
                    source_model=model_name,
                    svi_score=0.0,  # Se calcula después
                    metadata={
                        'generation_time': time.time(),
                        'model_version': model.get_version(),
                        'training_date': model.get_training_date()
                    }
                )
                predictions.append(prediction_result)
            
            self.logger.debug(f"✅ {model_name}: {len(predictions)} predicciones generadas")
            return predictions
            
        except Exception as e:
            self.logger.error(f"❌ Error en modelo {model_name}: {e}")
            raise
    
    async def _apply_ensemble_logic(self, 
                                  all_predictions: List[PredictionResult]) -> List[PredictionResult]:
        """Aplica lógica de ensemble para combinar predicciones"""
        self.logger.debug("🤝 Aplicando lógica de ensemble")
        
        # Obtener pesos de modelos
        model_weights = self.ensemble_manager.get_model_weights()
        
        # Agrupar por combinación
        combination_groups = {}
        for pred in all_predictions:
            combo_key = tuple(sorted(pred.combination))
            if combo_key not in combination_groups:
                combination_groups[combo_key] = []
            combination_groups[combo_key].append(pred)
        
        # Calcular scores ensemble
        ensemble_predictions = []
        for combo_key, predictions in combination_groups.items():
            # Calcular confianza weighted
            weighted_confidence = 0.0
            total_weight = 0.0
            
            for pred in predictions:
                weight = model_weights.get(pred.source_model, 1.0)
                weighted_confidence += pred.confidence * weight
                total_weight += weight
            
            if total_weight > 0:
                weighted_confidence /= total_weight
            
            # Crear predicción ensemble
            ensemble_pred = PredictionResult(
                combination=list(combo_key),
                confidence=weighted_confidence,
                source_model="ensemble",
                svi_score=0.0,
                metadata={
                    'contributing_models': [p.source_model for p in predictions],
                    'model_count': len(predictions),
                    'ensemble_time': time.time()
                }
            )
            ensemble_predictions.append(ensemble_pred)
        
        # Ordenar por confianza
        ensemble_predictions.sort(key=lambda x: x.confidence, reverse=True)
        
        self.logger.debug(f"🤝 Ensemble: {len(ensemble_predictions)} combinaciones únicas")
        return ensemble_predictions
    
    async def _calculate_svi_scores(self, 
                                  predictions: List[PredictionResult]) -> List[PredictionResult]:
        """Calcula scores SVI para todas las predicciones"""
        self.logger.debug("📊 Calculando scores SVI")
        
        try:
            # Preparar datos para cálculo SVI en lote
            combinations = [pred.combination for pred in predictions]
            
            # Calcular SVI en paralelo
            svi_scores = await self.data_service.calculate_svi_batch(combinations)
            
            # Actualizar predicciones con scores SVI
            for pred, svi_score in zip(predictions, svi_scores):
                pred.svi_score = svi_score
                
                # Calcular score final (combinación de confianza y SVI)
                pred.final_score = (pred.confidence * 0.7) + (svi_score * 0.3)
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"❌ Error calculando SVI: {e}")
            # Fallback: usar solo confianza del modelo
            for pred in predictions:
                pred.svi_score = pred.confidence
                pred.final_score = pred.confidence
            return predictions
    
    async def _select_best_predictions(self, 
                                     predictions: List[PredictionResult],
                                     target_count: int) -> List[PredictionResult]:
        """Selecciona las mejores predicciones aplicando filtros avanzados"""
        self.logger.debug(f"🎯 Seleccionando mejores {target_count} predicciones")
        
        # Ordenar por score final
        predictions.sort(key=lambda x: x.final_score, reverse=True)
        
        # Aplicar filtros de diversidad
        selected = []
        used_numbers = set()
        
        for pred in predictions:
            if len(selected) >= target_count:
                break
            
            # Filtro de diversidad: evitar demasiada repetición de números
            combo_set = set(pred.combination)
            overlap = len(combo_set.intersection(used_numbers))
            
            # Permitir cierta superposición pero no total
            if overlap < 4 or len(selected) == 0:
                selected.append(pred)
                used_numbers.update(combo_set)
        
        # Si no tenemos suficientes, completar con las siguientes mejores
        if len(selected) < target_count:
            remaining = target_count - len(selected)
            additional = predictions[len(selected):len(selected) + remaining]
            selected.extend(additional)
        
        self.logger.info(f"🎯 Seleccionadas {len(selected)} predicciones finales")
        return selected[:target_count]
    
    async def validate_predictions(self, 
                                 predictions: List[PredictionResult]) -> List[PredictionResult]:
        """Valida predicciones antes de devolverlas"""
        valid_predictions = []
        
        for pred in predictions:
            # Validaciones básicas
            if (len(pred.combination) == 6 and 
                all(1 <= n <= 40 for n in pred.combination) and
                len(set(pred.combination)) == 6):
                valid_predictions.append(pred)
            else:
                self.logger.warning(f"⚠️ Predicción inválida descartada: {pred.combination}")
        
        return valid_predictions