#!/usr/bin/env python3
"""
📚 CONTINUOUS LEARNING SYSTEM - Fase 4 del Sistema Agéntico
Sistema de aprendizaje continuo online que actualiza conocimiento en tiempo real
Implementa incremental learning, concept drift detection y knowledge retention
"""

import json
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from sklearn.linear_model import SGDRegressor, SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, accuracy_score
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

@dataclass
class LearningExample:
    """Ejemplo de aprendizaje con features y target"""
    features: Dict[str, float]
    target: float
    timestamp: str
    context: Dict[str, Any]
    weight: float = 1.0
    
    def to_feature_vector(self, feature_order: List[str]) -> np.ndarray:
        """Convierte a vector de features ordenado"""
        return np.array([self.features.get(f, 0.0) for f in feature_order])

@dataclass
class ConceptDrift:
    """Detección de cambio conceptual"""
    detected_at: str
    drift_type: str  # "gradual", "sudden", "recurring"
    affected_features: List[str]
    confidence: float
    magnitude: float

class IncrementalLearner:
    """Learner incremental para aprendizaje online"""
    
    def __init__(self, learning_rate: float = 0.01):
        self.learning_rate = learning_rate
        self.model = SGDRegressor(learning_rate='adaptive', eta0=learning_rate)
        self.scaler = StandardScaler()
        
        self.feature_names = []
        self.is_fitted = False
        self.samples_seen = 0
        self.performance_history = deque(maxlen=100)
        
        logger.info(f"📚 IncrementalLearner inicializado (lr={learning_rate})")
    
    def partial_fit(self, X: np.ndarray, y: np.ndarray, feature_names: List[str] = None):
        """Entrenamiento incremental"""
        
        if feature_names:
            self.feature_names = feature_names
        
        # Escalar features
        if not self.is_fitted:
            X_scaled = self.scaler.fit_transform(X)
            self.model.partial_fit(X_scaled, y)
            self.is_fitted = True
        else:
            X_scaled = self.scaler.partial_fit_transform(X, y)
            self.model.partial_fit(X_scaled, y)
        
        self.samples_seen += len(X)
        
        # Evaluar performance si tenemos suficientes datos
        if self.samples_seen >= 10:
            predictions = self.model.predict(X_scaled)
            mse = mean_squared_error(y, predictions)
            self.performance_history.append(mse)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predicción"""
        if not self.is_fitted:
            return np.zeros(len(X))
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Obtiene importancia de features"""
        if not self.is_fitted or not hasattr(self.model, 'coef_'):
            return {}
        
        importances = np.abs(self.model.coef_)
        
        if len(self.feature_names) == len(importances):
            return dict(zip(self.feature_names, importances))
        else:
            return {f"feature_{i}": imp for i, imp in enumerate(importances)}

class ConceptDriftDetector:
    """Detector de concept drift usando ADWIN adaptativo"""
    
    def __init__(self, window_size: int = 50, sensitivity: float = 0.002):
        self.window_size = window_size
        self.sensitivity = sensitivity
        self.performance_window = deque(maxlen=window_size)
        self.feature_windows = defaultdict(lambda: deque(maxlen=window_size))
        
        self.drift_history = []
        self.baseline_performance = None
        self.baseline_features = {}
        
        logger.info(f"🔍 ConceptDriftDetector inicializado (window={window_size})")
    
    def add_sample(self, performance: float, features: Dict[str, float]) -> Optional[ConceptDrift]:
        """Añade muestra y detecta drift"""
        
        self.performance_window.append(performance)
        
        for feature_name, value in features.items():
            self.feature_windows[feature_name].append(value)
        
        # Establecer baseline si es la primera vez
        if self.baseline_performance is None and len(self.performance_window) >= 20:
            self.baseline_performance = np.mean(list(self.performance_window)[:20])
            
            for feature_name, window in self.feature_windows.items():
                if len(window) >= 20:
                    self.baseline_features[feature_name] = np.mean(list(window)[:20])
        
        # Detectar drift si tenemos suficientes datos
        if len(self.performance_window) >= self.window_size:
            return self._detect_drift()
        
        return None
    
    def _detect_drift(self) -> Optional[ConceptDrift]:
        """Detecta concept drift usando estadísticas"""
        
        if self.baseline_performance is None:
            return None
        
        # Dividir ventana en dos mitades
        mid_point = len(self.performance_window) // 2
        recent_performance = list(self.performance_window)[mid_point:]
        
        # Test estadístico para performance
        recent_mean = np.mean(recent_performance)
        performance_change = abs(recent_mean - self.baseline_performance) / self.baseline_performance
        
        drift_detected = performance_change > self.sensitivity
        
        if drift_detected:
            # Analizar qué features han cambiado más
            affected_features = []
            
            for feature_name, window in self.feature_windows.items():
                if len(window) >= self.window_size and feature_name in self.baseline_features:
                    recent_feature = np.mean(list(window)[mid_point:])
                    baseline_feature = self.baseline_features[feature_name]
                    
                    if baseline_feature != 0:
                        feature_change = abs(recent_feature - baseline_feature) / abs(baseline_feature)
                        if feature_change > self.sensitivity:
                            affected_features.append(feature_name)
            
            # Determinar tipo de drift
            if performance_change > 0.1:
                drift_type = "sudden"
            elif len(affected_features) > len(self.baseline_features) * 0.5:
                drift_type = "gradual"
            else:
                drift_type = "recurring"
            
            drift = ConceptDrift(
                detected_at=datetime.now().isoformat(),
                drift_type=drift_type,
                affected_features=affected_features,
                confidence=min(performance_change * 10, 1.0),
                magnitude=performance_change
            )
            
            self.drift_history.append(drift)
            
            # Actualizar baseline
            self.baseline_performance = recent_mean
            
            logger.warning(f"🚨 Concept drift detectado: {drift_type} (magnitude: {performance_change:.3f})")
            
            return drift
        
        return None

class KnowledgeRetentionManager:
    """Gestor de retención de conocimiento"""
    
    def __init__(self, max_knowledge_items: int = 1000):
        self.max_knowledge_items = max_knowledge_items
        self.knowledge_base = deque(maxlen=max_knowledge_items)
        self.concept_summaries = {}
        self.importance_scores = {}
        
        logger.info(f"🧠 KnowledgeRetentionManager inicializado (max_items={max_knowledge_items})")
    
    def store_knowledge(self, example: LearningExample, importance: float = 1.0):
        """Almacena conocimiento con puntuación de importancia"""
        
        knowledge_item = {
            "example": example,
            "importance": importance,
            "stored_at": datetime.now().isoformat(),
            "access_count": 0,
            "last_accessed": datetime.now().isoformat()
        }
        
        self.knowledge_base.append(knowledge_item)
        
        # Actualizar puntuaciones de importancia
        example_id = len(self.knowledge_base) - 1
        self.importance_scores[example_id] = importance
    
    def retrieve_relevant_knowledge(self, current_context: Dict[str, Any], 
                                  top_k: int = 10) -> List[LearningExample]:
        """Recupera conocimiento relevante para el contexto actual"""
        
        if not self.knowledge_base:
            return []
        
        # Calcular relevancia basada en similitud de contexto
        relevance_scores = []
        
        for i, item in enumerate(self.knowledge_base):
            example = item["example"]
            
            # Similitud de contexto simple
            context_similarity = self._calculate_context_similarity(
                current_context, example.context
            )
            
            # Combinar con importancia y frecuencia de acceso
            importance = self.importance_scores.get(i, 1.0)
            access_bonus = min(item["access_count"] * 0.1, 0.5)
            
            relevance = context_similarity * importance + access_bonus
            relevance_scores.append((relevance, i, example))
        
        # Ordenar por relevancia y retornar top-k
        relevance_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Actualizar contadores de acceso
        for _, idx, _ in relevance_scores[:top_k]:
            if idx < len(self.knowledge_base):
                self.knowledge_base[idx]["access_count"] += 1
                self.knowledge_base[idx]["last_accessed"] = datetime.now().isoformat()
        
        return [example for _, _, example in relevance_scores[:top_k]]
    
    def _calculate_context_similarity(self, context1: Dict[str, Any], 
                                    context2: Dict[str, Any]) -> float:
        """Calcula similitud entre contextos"""
        
        if not context1 or not context2:
            return 0.0
        
        common_keys = set(context1.keys()) & set(context2.keys())
        
        if not common_keys:
            return 0.0
        
        similarities = []
        
        for key in common_keys:
            val1, val2 = context1[key], context2[key]
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Similitud numérica
                if val1 == 0 and val2 == 0:
                    sim = 1.0
                elif val1 == 0 or val2 == 0:
                    sim = 0.0
                else:
                    sim = 1.0 - abs(val1 - val2) / max(abs(val1), abs(val2))
                similarities.append(sim)
            
            elif isinstance(val1, str) and isinstance(val2, str):
                # Similitud de strings
                sim = 1.0 if val1 == val2 else 0.0
                similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0
    
    def consolidate_knowledge(self):
        """Consolida conocimiento eliminando duplicados y ejemplos poco útiles"""
        
        if len(self.knowledge_base) < self.max_knowledge_items * 0.9:
            return  # No necesita consolidación aún
        
        logger.info("🧹 Iniciando consolidación de conocimiento...")
        
        # Ordenar por importancia y uso
        items_with_scores = []
        
        for i, item in enumerate(self.knowledge_base):
            importance = self.importance_scores.get(i, 1.0)
            usage_score = item["access_count"] * 0.1
            age_penalty = (datetime.now() - datetime.fromisoformat(item["stored_at"])).days * 0.01
            
            final_score = importance + usage_score - age_penalty
            items_with_scores.append((final_score, item))
        
        # Mantener top items
        items_with_scores.sort(key=lambda x: x[0], reverse=True)
        keep_count = int(self.max_knowledge_items * 0.7)
        
        self.knowledge_base = deque(
            [item for _, item in items_with_scores[:keep_count]],
            maxlen=self.max_knowledge_items
        )
        
        # Actualizar índices de importancia
        self.importance_scores = {
            i: score for i, (score, _) in enumerate(items_with_scores[:keep_count])
        }
        
        logger.info(f"✅ Consolidación completada: {keep_count} items retenidos")

class ContinuousLearningSystem:
    """Sistema principal de aprendizaje continuo"""
    
    def __init__(self):
        self.learners = {}  # Múltiples learners especializados
        self.drift_detector = ConceptDriftDetector()
        self.knowledge_manager = KnowledgeRetentionManager()
        
        self.learning_history = []
        self.adaptation_count = 0
        
        # Configuración del sistema
        self.config = {
            "enable_drift_detection": True,
            "enable_knowledge_retention": True,
            "adaptation_threshold": 0.05,
            "learning_rate_decay": 0.99,
            "min_samples_for_adaptation": 10,
            "max_learners": 5
        }
        
        # Métricas del sistema
        self.metrics = {
            "total_samples_processed": 0,
            "drift_events": 0,
            "adaptations_made": 0,
            "knowledge_items_stored": 0,
            "average_prediction_accuracy": 0.0,
            "last_adaptation_time": None
        }
        
        logger.info("📚 ContinuousLearningSystem inicializado")
    
    def create_learner(self, learner_id: str, specialization: str = "general"):
        """Crea un nuevo learner especializado"""
        
        learning_rate = 0.01 if specialization == "general" else 0.005
        learner = IncrementalLearner(learning_rate)
        
        self.learners[learner_id] = {
            "learner": learner,
            "specialization": specialization,
            "created_at": datetime.now().isoformat(),
            "samples_seen": 0,
            "performance_trend": []
        }
        
        logger.info(f"📚 Learner creado: {learner_id} ({specialization})")
    
    def process_learning_example(self, example: LearningExample, 
                                learner_id: str = "default") -> Dict[str, Any]:
        """Procesa un ejemplo de aprendizaje"""
        
        # Crear learner por defecto si no existe
        if learner_id not in self.learners:
            self.create_learner(learner_id)
        
        learner_info = self.learners[learner_id]
        learner = learner_info["learner"]
        
        # Extraer features y target
        feature_names = list(example.features.keys())
        X = example.to_feature_vector(feature_names).reshape(1, -1)
        y = np.array([example.target])
        
        # Predicción antes del aprendizaje (para medir performance)
        prediction = learner.predict(X)[0] if learner.is_fitted else example.target
        prediction_error = abs(prediction - example.target)
        
        # Entrenamiento incremental
        learner.partial_fit(X, y, feature_names)
        
        # Actualizar métricas del learner
        learner_info["samples_seen"] += 1
        learner_info["performance_trend"].append(prediction_error)
        
        # Mantener solo últimas 100 mediciones
        if len(learner_info["performance_trend"]) > 100:
            learner_info["performance_trend"] = learner_info["performance_trend"][-100:]
        
        # Detectar concept drift
        drift = None
        if self.config["enable_drift_detection"]:
            drift = self.drift_detector.add_sample(prediction_error, example.features)
        
        # Almacenar conocimiento
        if self.config["enable_knowledge_retention"]:
            importance = self._calculate_example_importance(example, prediction_error)
            self.knowledge_manager.store_knowledge(example, importance)
        
        # Adaptar si es necesario
        adaptation_result = self._consider_adaptation(drift, prediction_error)
        
        # Actualizar métricas globales
        self.metrics["total_samples_processed"] += 1
        self.metrics["knowledge_items_stored"] = len(self.knowledge_manager.knowledge_base)
        
        # Actualizar accuracy promedio
        current_acc = 1.0 / (1.0 + prediction_error)  # Convertir error a accuracy
        total_samples = self.metrics["total_samples_processed"]
        prev_acc = self.metrics["average_prediction_accuracy"]
        
        self.metrics["average_prediction_accuracy"] = (
            (prev_acc * (total_samples - 1) + current_acc) / total_samples
        )
        
        # Compilar resultado
        processing_result = {
            "learner_id": learner_id,
            "prediction": prediction,
            "actual": example.target,
            "error": prediction_error,
            "drift_detected": drift is not None,
            "drift_info": asdict(drift) if drift else None,
            "adaptation_triggered": adaptation_result["adapted"],
            "adaptation_info": adaptation_result,
            "feature_importance": learner.get_feature_importance(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Guardar en historial
        self.learning_history.append(processing_result)
        
        # Mantener historial limitado
        if len(self.learning_history) > 1000:
            self.learning_history = self.learning_history[-1000:]
        
        return processing_result
    
    def _calculate_example_importance(self, example: LearningExample, 
                                    prediction_error: float) -> float:
        """Calcula importancia de un ejemplo para almacenamiento"""
        
        # Ejemplos con mayor error son más importantes para aprender
        error_importance = min(prediction_error * 2, 1.0)
        
        # Ejemplos con contexto único son más importantes
        context_uniqueness = self._calculate_context_uniqueness(example.context)
        
        # Peso del ejemplo
        weight_importance = example.weight
        
        # Combinar factores
        total_importance = (error_importance * 0.5 + 
                          context_uniqueness * 0.3 + 
                          weight_importance * 0.2)
        
        return min(total_importance, 1.0)
    
    def _calculate_context_uniqueness(self, context: Dict[str, Any]) -> float:
        """Calcula qué tan único es un contexto"""
        
        if not self.knowledge_manager.knowledge_base:
            return 1.0  # Primer ejemplo es único
        
        # Muestrear algunos ejemplos recientes para comparar
        recent_examples = list(self.knowledge_manager.knowledge_base)[-20:]
        
        similarities = []
        for item in recent_examples:
            sim = self.knowledge_manager._calculate_context_similarity(
                context, item["example"].context
            )
            similarities.append(sim)
        
        # Uniqueness = 1 - max_similarity
        max_similarity = max(similarities) if similarities else 0
        return 1.0 - max_similarity
    
    def _consider_adaptation(self, drift: Optional[ConceptDrift], 
                           prediction_error: float) -> Dict[str, Any]:
        """Considera si hacer adaptación del sistema"""
        
        adaptation_result = {"adapted": False, "reason": "no_trigger"}
        
        # Trigger 1: Concept drift detectado
        if drift and drift.confidence > 0.5:
            self._perform_drift_adaptation(drift)
            adaptation_result = {
                "adapted": True,
                "reason": "concept_drift",
                "drift_type": drift.drift_type,
                "confidence": drift.confidence
            }
        
        # Trigger 2: Performance degradation
        elif prediction_error > self.config["adaptation_threshold"]:
            if self._check_performance_degradation():
                self._perform_performance_adaptation()
                adaptation_result = {
                    "adapted": True,
                    "reason": "performance_degradation",
                    "error": prediction_error
                }
        
        return adaptation_result
    
    def _perform_drift_adaptation(self, drift: ConceptDrift):
        """Realiza adaptación por concept drift"""
        
        logger.info(f"🔄 Adaptando por concept drift: {drift.drift_type}")
        
        # Estrategias de adaptación según tipo de drift
        if drift.drift_type == "sudden":
            # Reset parcial de learners
            for learner_info in self.learners.values():
                learner = learner_info["learner"]
                learner.learning_rate = min(learner.learning_rate * 1.5, 0.1)
        
        elif drift.drift_type == "gradual":
            # Ajuste gradual de learning rate
            for learner_info in self.learners.values():
                learner = learner_info["learner"]
                learner.learning_rate = min(learner.learning_rate * 1.2, 0.05)
        
        # Recuperar conocimiento relevante
        relevant_knowledge = self.knowledge_manager.retrieve_relevant_knowledge(
            {"drift_type": drift.drift_type}, top_k=20
        )
        
        # Re-entrenar con conocimiento relevante
        self._retrain_with_knowledge(relevant_knowledge)
        
        self.adaptation_count += 1
        self.metrics["adaptations_made"] += 1
        self.metrics["drift_events"] += 1
        self.metrics["last_adaptation_time"] = datetime.now().isoformat()
    
    def _check_performance_degradation(self) -> bool:
        """Verifica si hay degradación de performance"""
        
        if not self.learners:
            return False
        
        # Verificar tendencia en performance de learners
        for learner_info in self.learners.values():
            trend = learner_info["performance_trend"]
            
            if len(trend) >= 10:
                recent_errors = trend[-5:]
                older_errors = trend[-10:-5]
                
                recent_avg = np.mean(recent_errors)
                older_avg = np.mean(older_errors)
                
                # Si el error reciente es significativamente mayor
                if recent_avg > older_avg * 1.2:
                    return True
        
        return False
    
    def _perform_performance_adaptation(self):
        """Realiza adaptación por degradación de performance"""
        
        logger.info("🔄 Adaptando por degradación de performance")
        
        # Aumentar learning rate temporalmente
        for learner_info in self.learners.values():
            learner = learner_info["learner"]
            learner.learning_rate = min(learner.learning_rate * 1.3, 0.08)
        
        self.adaptation_count += 1
        self.metrics["adaptations_made"] += 1
        self.metrics["last_adaptation_time"] = datetime.now().isoformat()
    
    def _retrain_with_knowledge(self, knowledge_examples: List[LearningExample]):
        """Re-entrena con ejemplos de conocimiento relevante"""
        
        if not knowledge_examples:
            return
        
        logger.info(f"🧠 Re-entrenando con {len(knowledge_examples)} ejemplos de conocimiento")
        
        for learner_id, learner_info in self.learners.items():
            learner = learner_info["learner"]
            
            # Preparar datos de conocimiento
            feature_names = learner.feature_names
            if not feature_names:
                continue
            
            X_knowledge = []
            y_knowledge = []
            
            for example in knowledge_examples:
                features_vector = example.to_feature_vector(feature_names)
                X_knowledge.append(features_vector)
                y_knowledge.append(example.target)
            
            if X_knowledge:
                X_knowledge = np.array(X_knowledge)
                y_knowledge = np.array(y_knowledge)
                
                # Re-entrenamiento incremental
                learner.partial_fit(X_knowledge, y_knowledge, feature_names)
    
    def predict_with_ensemble(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Hace predicción usando ensemble de learners"""
        
        if not self.learners:
            return {"prediction": 0.0, "confidence": 0.0, "learners_used": 0}
        
        predictions = []
        learner_contributions = {}
        
        for learner_id, learner_info in self.learners.items():
            learner = learner_info["learner"]
            
            if learner.is_fitted:
                feature_names = learner.feature_names
                X = np.array([features.get(f, 0.0) for f in feature_names]).reshape(1, -1)
                
                pred = learner.predict(X)[0]
                predictions.append(pred)
                learner_contributions[learner_id] = pred
        
        if not predictions:
            return {"prediction": 0.0, "confidence": 0.0, "learners_used": 0}
        
        # Ensemble simple (promedio)
        ensemble_prediction = np.mean(predictions)
        confidence = 1.0 - (np.std(predictions) / max(abs(ensemble_prediction), 1.0))
        
        return {
            "prediction": ensemble_prediction,
            "confidence": confidence,
            "learners_used": len(predictions),
            "individual_predictions": learner_contributions
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del sistema de aprendizaje"""
        
        learner_status = {}
        for learner_id, learner_info in self.learners.items():
            learner = learner_info["learner"]
            
            recent_errors = learner_info["performance_trend"][-10:] if learner_info["performance_trend"] else []
            
            learner_status[learner_id] = {
                "specialization": learner_info["specialization"],
                "samples_seen": learner_info["samples_seen"],
                "is_fitted": learner.is_fitted,
                "recent_avg_error": np.mean(recent_errors) if recent_errors else 0.0,
                "feature_count": len(learner.feature_names),
                "learning_rate": learner.learning_rate
            }
        
        return {
            "system_metrics": self.metrics,
            "learners": learner_status,
            "drift_detection": {
                "enabled": self.config["enable_drift_detection"],
                "sensitivity": self.drift_detector.sensitivity,
                "recent_drifts": len(self.drift_detector.drift_history)
            },
            "knowledge_management": {
                "enabled": self.config["enable_knowledge_retention"],
                "items_stored": len(self.knowledge_manager.knowledge_base),
                "max_capacity": self.knowledge_manager.max_knowledge_items
            },
            "recent_learning_activity": self.learning_history[-5:],
            "config": self.config
        }

# Función de conveniencia
def create_continuous_learning_system() -> ContinuousLearningSystem:
    """Crea sistema de aprendizaje continuo configurado"""
    
    system = ContinuousLearningSystem()
    
    # Crear learners especializados por defecto
    system.create_learner("performance_predictor", "performance")
    system.create_learner("stability_analyzer", "stability")
    system.create_learner("efficiency_optimizer", "efficiency")
    
    return system

if __name__ == '__main__':
    # Test básico del sistema
    print("📚 Testing Continuous Learning System...")
    
    system = create_continuous_learning_system()
    
    # Simular ejemplos de aprendizaje
    for i in range(20):
        # Features simuladas
        features = {
            "neural_weight": 0.4 + (i * 0.02),
            "svi_score": 0.7 + np.random.normal(0, 0.05),
            "diversity": 0.8 + np.random.normal(0, 0.03)
        }
        
        # Target simulado (reward)
        target = 0.6 + features["neural_weight"] * 0.3 + np.random.normal(0, 0.02)
        
        # Contexto
        context = {
            "cycle": i,
            "strategy": ["active_learning", "bayesian", "conservative"][i % 3]
        }
        
        # Crear ejemplo
        example = LearningExample(
            features=features,
            target=target,
            timestamp=datetime.now().isoformat(),
            context=context
        )
        
        # Procesar
        result = system.process_learning_example(example, "performance_predictor")
        
        if i % 5 == 0:
            print(f"   📊 Sample {i}: Error = {result['error']:.3f}, Drift = {'✅' if result['drift_detected'] else '❌'}")
    
    # Test de predicción ensemble
    test_features = {"neural_weight": 0.6, "svi_score": 0.8, "diversity": 0.85}
    prediction_result = system.predict_with_ensemble(test_features)
    
    print(f"\n✅ Test completado:")
    print(f"   📊 Samples procesados: {system.metrics['total_samples_processed']}")
    print(f"   🎯 Accuracy promedio: {system.metrics['average_prediction_accuracy']:.3f}")
    print(f"   🔄 Adaptaciones: {system.metrics['adaptations_made']}")
    print(f"   🧠 Conocimiento almacenado: {system.metrics['knowledge_items_stored']}")
    print(f"   🔮 Predicción ensemble: {prediction_result['prediction']:.3f} (confidence: {prediction_result['confidence']:.3f})")
    
    # Mostrar estado del sistema
    status = system.get_system_status()
    print(f"   📚 Learners activos: {len(status['learners'])}")
    print(f"   📈 Drift detection: {'✅' if status['drift_detection']['enabled'] else '❌'}")
