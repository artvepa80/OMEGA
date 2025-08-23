#!/usr/bin/env python3
"""
Meta-Learning Controller for OMEGA PRO AI
Controlador inteligente que aprende qué modelos predicen mejor en qué contextos
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class ContextRegime(Enum):
    """Regímenes de contexto identificados"""
    REGIME_A = "high_frequency_low_variance"  # Alta frecuencia, baja varianza
    REGIME_B = "moderate_balanced"           # Moderado balanceado
    REGIME_C = "low_frequency_high_variance" # Baja frecuencia, alta varianza
    REGIME_UNKNOWN = "unknown"

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

@dataclass
class PredictionContext:
    """Contexto actual para predicción"""
    entropy: float
    variance: float
    trend_strength: float
    cycle_phase: float
    recent_volatility: float
    seasonal_factor: float
    regime: ContextRegime

class MetaLearningController:
    """Controlador de meta-aprendizaje para selección inteligente de modelos"""
    
    def __init__(self, memory_size: int = 1000):
        self.memory_size = memory_size
        self.performance_history: List[ModelPerformance] = []
        self.context_classifier = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model_selector = RandomForestRegressor(n_estimators=50, random_state=42)
        self.scaler = StandardScaler()
        
        # Modelos disponibles y sus pesos dinámicos
        self.available_models = {
            'lstm_v2': {'weight': 1.0, 'specialty': 'temporal_patterns'},
            'transformer': {'weight': 1.0, 'specialty': 'attention_patterns'},
            'clustering': {'weight': 1.0, 'specialty': 'group_patterns'},
            'montecarlo': {'weight': 1.0, 'specialty': 'probabilistic'},
            'genetic': {'weight': 1.0, 'specialty': 'evolutionary'},
            'gboost': {'weight': 1.0, 'specialty': 'gradient_boosting'},
            'ensemble_ai': {'weight': 1.5, 'specialty': 'meta_ensemble'}
        }
        
        # Historia de contextos y regímenes
        self.regime_history: List[Tuple[datetime, ContextRegime]] = []
        self.context_features_history: List[Dict[str, float]] = []
        
        # Métricas de aprendizaje
        self.learning_rate = 0.01
        self.adaptation_threshold = 0.05
        self.is_trained = False
        
        logger.info("🧠 Meta-Learning Controller inicializado")
    
    def analyze_current_context(self, historical_data: List[List[int]]) -> PredictionContext:
        """Analiza el contexto actual de los datos para determinar el régimen"""
        if not historical_data or len(historical_data) < 10:
            return PredictionContext(
                entropy=0.5, variance=0.5, trend_strength=0.0,
                cycle_phase=0.0, recent_volatility=0.5, seasonal_factor=1.0,
                regime=ContextRegime.REGIME_UNKNOWN
            )
        
        try:
            # Convertir a DataFrame para análisis
            df = pd.DataFrame(historical_data)
            
            # 1. Calcular entropía de la distribución de números
            all_numbers = np.concatenate(historical_data)
            entropy = self._calculate_entropy(all_numbers)
            
            # 2. Calcular varianza de las sumas
            sums = [sum(combo) for combo in historical_data]
            variance = np.var(sums) / np.mean(sums) if np.mean(sums) > 0 else 0
            
            # 3. Detectar fuerza de tendencia
            trend_strength = self._calculate_trend_strength(sums)
            
            # 4. Detectar fase del ciclo
            cycle_phase = self._detect_cycle_phase(historical_data)
            
            # 5. Volatilidad reciente (últimas 10 combinaciones)
            recent_data = historical_data[-10:] if len(historical_data) >= 10 else historical_data
            recent_sums = [sum(combo) for combo in recent_data]
            recent_volatility = np.std(recent_sums) / np.mean(recent_sums) if np.mean(recent_sums) > 0 else 0
            
            # 6. Factor estacional (basado en posición en el año)
            seasonal_factor = self._calculate_seasonal_factor()
            
            # 7. Determinar régimen basado en las métricas
            regime = self._classify_regime(entropy, variance, trend_strength, recent_volatility)
            
            context = PredictionContext(
                entropy=entropy,
                variance=variance,
                trend_strength=trend_strength,
                cycle_phase=cycle_phase,
                recent_volatility=recent_volatility,
                seasonal_factor=seasonal_factor,
                regime=regime
            )
            
            # Registrar en historia
            self.regime_history.append((datetime.now(), regime))
            self.context_features_history.append({
                'entropy': entropy,
                'variance': variance,
                'trend_strength': trend_strength,
                'cycle_phase': cycle_phase,
                'recent_volatility': recent_volatility,
                'seasonal_factor': seasonal_factor
            })
            
            # Mantener tamaño de historia
            if len(self.regime_history) > self.memory_size:
                self.regime_history.pop(0)
                self.context_features_history.pop(0)
            
            logger.info(f"📊 Contexto analizado: {regime.value} (entropía: {entropy:.3f}, varianza: {variance:.3f})")
            return context
            
        except Exception as e:
            logger.error(f"❌ Error analizando contexto: {e}")
            return PredictionContext(
                entropy=0.5, variance=0.5, trend_strength=0.0,
                cycle_phase=0.0, recent_volatility=0.5, seasonal_factor=1.0,
                regime=ContextRegime.REGIME_UNKNOWN
            )
    
    def _calculate_entropy(self, numbers: np.ndarray) -> float:
        """Calcula la entropía de Shannon de la distribución de números"""
        unique, counts = np.unique(numbers, return_counts=True)
        probabilities = counts / len(numbers)
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        # Normalizar entre 0 y 1
        max_entropy = np.log2(40)  # Máxima entropía para 40 números
        return entropy / max_entropy
    
    def _calculate_trend_strength(self, values: List[float]) -> float:
        """Calcula la fuerza de la tendencia usando regresión lineal"""
        if len(values) < 3:
            return 0.0
        
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)
        slope = coeffs[0]
        
        # Normalizar slope relativo a la media
        mean_val = np.mean(values)
        normalized_slope = abs(slope) / mean_val if mean_val > 0 else 0
        
        return min(normalized_slope, 1.0)
    
    def _detect_cycle_phase(self, historical_data: List[List[int]]) -> float:
        """Detecta la fase del ciclo usando FFT simplificado"""
        if len(historical_data) < 8:
            return 0.0
        
        try:
            sums = [sum(combo) for combo in historical_data]
            
            # FFT para detectar periodicidades
            fft_values = np.fft.fft(sums)
            frequencies = np.fft.fftfreq(len(sums))
            
            # Encontrar frecuencia dominante (excluyendo DC)
            magnitude = np.abs(fft_values[1:len(fft_values)//2])
            if len(magnitude) > 0:
                dominant_freq_idx = np.argmax(magnitude)
                phase = np.angle(fft_values[dominant_freq_idx + 1])
                
                # Normalizar fase entre 0 y 1
                normalized_phase = (phase + np.pi) / (2 * np.pi)
                return normalized_phase
            
        except Exception as e:
            logger.debug(f"Error en detección de ciclo: {e}")
        
        return 0.0
    
    def _calculate_seasonal_factor(self) -> float:
        """Calcula factor estacional basado en la fecha actual"""
        now = datetime.now()
        day_of_year = now.timetuple().tm_yday
        
        # Factor sinusoidal basado en el día del año
        seasonal_factor = 0.5 * (1 + np.sin(2 * np.pi * day_of_year / 365.25))
        return seasonal_factor
    
    def _classify_regime(self, entropy: float, variance: float, trend_strength: float, volatility: float) -> ContextRegime:
        """Clasifica el régimen actual basado en las métricas"""
        
        # Régimen A: Alta frecuencia, baja varianza (números más predecibles)
        if entropy > 0.7 and variance < 0.3 and volatility < 0.2:
            return ContextRegime.REGIME_A
        
        # Régimen C: Baja frecuencia, alta varianza (números muy aleatorios)
        elif entropy < 0.4 and variance > 0.6 and volatility > 0.4:
            return ContextRegime.REGIME_C
        
        # Régimen B: Moderado balanceado (zona intermedia)
        else:
            return ContextRegime.REGIME_B
    
    def get_optimal_model_weights(self, context: PredictionContext) -> Dict[str, float]:
        """Obtiene los pesos óptimos de modelos para el contexto actual"""
        
        # Si no hay suficiente historia, usar pesos base ajustados por régimen
        if not self.is_trained or len(self.performance_history) < 50:
            return self._get_regime_based_weights(context.regime)
        
        try:
            # Usar modelo entrenado para predecir pesos óptimos
            context_vector = self._context_to_vector(context)
            predicted_weights = self.model_selector.predict([context_vector])[0]
            
            # Normalizar y asegurar pesos positivos
            weights = {}
            total_weight = 0
            
            for i, model_name in enumerate(self.available_models.keys()):
                if i < len(predicted_weights):
                    weight = max(0.1, predicted_weights[i])  # Mínimo 0.1
                    weights[model_name] = weight
                    total_weight += weight
                else:
                    weights[model_name] = 0.5
                    total_weight += 0.5
            
            # Normalizar para que sumen a cantidad deseada
            target_sum = len(self.available_models)
            for model_name in weights:
                weights[model_name] = (weights[model_name] / total_weight) * target_sum
            
            logger.info(f"🎯 Pesos optimizados para {context.regime.value}")
            return weights
            
        except Exception as e:
            logger.error(f"❌ Error calculando pesos: {e}")
            return self._get_regime_based_weights(context.regime)
    
    def _get_regime_based_weights(self, regime: ContextRegime) -> Dict[str, float]:
        """Obtiene pesos basados en reglas por régimen"""
        base_weights = {model: data['weight'] for model, data in self.available_models.items()}
        
        if regime == ContextRegime.REGIME_A:
            # Régimen A: Favorece modelos de patrones secuenciales
            base_weights['lstm_v2'] *= 1.5
            base_weights['transformer'] *= 1.3
            base_weights['clustering'] *= 0.8
            base_weights['montecarlo'] *= 0.7
            
        elif regime == ContextRegime.REGIME_C:
            # Régimen C: Favorece modelos probabilísticos y evolutivos
            base_weights['montecarlo'] *= 1.4
            base_weights['genetic'] *= 1.3
            base_weights['ensemble_ai'] *= 1.2
            base_weights['lstm_v2'] *= 0.8
            
        # Régimen B mantiene pesos balanceados
        
        logger.info(f"📊 Pesos por régimen {regime.value}")
        return base_weights
    
    def record_model_performance(self, model_name: str, context: PredictionContext, 
                                results: Dict[str, float]):
        """Registra el performance de un modelo en un contexto específico"""
        
        performance = ModelPerformance(
            model_name=model_name,
            regime=context.regime,
            accuracy=results.get('accuracy', 0.0),
            precision=results.get('precision', 0.0),
            recall=results.get('recall', 0.0),
            f1_score=results.get('f1_score', 0.0),
            timestamp=datetime.now(),
            context_features=self._context_to_dict(context)
        )
        
        self.performance_history.append(performance)
        
        # Mantener tamaño de memoria
        if len(self.performance_history) > self.memory_size:
            self.performance_history.pop(0)
        
        # Actualizar pesos dinámicamente
        self._update_dynamic_weights(model_name, performance)
        
        logger.info(f"📈 Performance registrado: {model_name} en {context.regime.value} (F1: {results.get('f1_score', 0):.3f})")
        
        # Re-entrenar si hay suficientes datos
        if len(self.performance_history) >= 100 and len(self.performance_history) % 25 == 0:
            self._retrain_meta_models()
    
    def _update_dynamic_weights(self, model_name: str, performance: ModelPerformance):
        """Actualiza los pesos dinámicos basado en performance reciente"""
        if model_name in self.available_models:
            current_weight = self.available_models[model_name]['weight']
            
            # Ajuste basado en F1 score
            f1_adjustment = (performance.f1_score - 0.5) * self.learning_rate
            new_weight = current_weight + f1_adjustment
            
            # Mantener en rango razonable
            new_weight = max(0.1, min(2.0, new_weight))
            
            self.available_models[model_name]['weight'] = new_weight
            
            logger.debug(f"⚖️ Peso actualizado {model_name}: {current_weight:.3f} → {new_weight:.3f}")
    
    def _retrain_meta_models(self):
        """Re-entrena los modelos meta con nueva data"""
        try:
            logger.info("🔄 Re-entrenando modelos meta...")
            
            # Preparar datos de entrenamiento
            X_context = []
            y_weights = []
            
            # Agrupar performance por contexto
            context_groups = {}
            for perf in self.performance_history[-500:]:  # Últimos 500 registros
                context_key = self._context_to_key(perf.context_features)
                if context_key not in context_groups:
                    context_groups[context_key] = {}
                
                if perf.model_name not in context_groups[context_key]:
                    context_groups[context_key][perf.model_name] = []
                
                context_groups[context_key][perf.model_name].append(perf.f1_score)
            
            # Crear vectores de entrenamiento
            for context_key, models_performance in context_groups.items():
                if len(models_performance) >= 3:  # Mínimo 3 modelos
                    context_vector = self._key_to_vector(context_key)
                    
                    # Pesos basados en performance promedio
                    weights_vector = []
                    for model_name in self.available_models.keys():
                        if model_name in models_performance:
                            avg_perf = np.mean(models_performance[model_name])
                            weights_vector.append(max(0.1, avg_perf))
                        else:
                            weights_vector.append(0.5)
                    
                    X_context.append(context_vector)
                    y_weights.append(weights_vector)
            
            if len(X_context) >= 20:  # Mínimo de datos para entrenar
                X_context = np.array(X_context)
                y_weights = np.array(y_weights)
                
                # Entrenar selector de modelos
                self.model_selector.fit(X_context, y_weights)
                self.is_trained = True
                
                logger.info(f"✅ Modelos meta re-entrenados con {len(X_context)} muestras")
            else:
                logger.warning("⚠️ Insuficientes datos para re-entrenamiento")
                
        except Exception as e:
            logger.error(f"❌ Error re-entrenando modelos meta: {e}")
    
    def _context_to_vector(self, context: PredictionContext) -> List[float]:
        """Convierte contexto a vector numérico"""
        return [
            context.entropy,
            context.variance,
            context.trend_strength,
            context.cycle_phase,
            context.recent_volatility,
            context.seasonal_factor,
            float(list(ContextRegime).index(context.regime))
        ]
    
    def _context_to_dict(self, context: PredictionContext) -> Dict[str, float]:
        """Convierte contexto a diccionario"""
        return {
            'entropy': context.entropy,
            'variance': context.variance,
            'trend_strength': context.trend_strength,
            'cycle_phase': context.cycle_phase,
            'recent_volatility': context.recent_volatility,
            'seasonal_factor': context.seasonal_factor,
            'regime_index': float(list(ContextRegime).index(context.regime))
        }
    
    def _context_to_key(self, context_dict: Dict[str, float]) -> str:
        """Convierte contexto a clave única"""
        rounded = {k: round(v, 2) for k, v in context_dict.items()}
        return str(hash(tuple(sorted(rounded.items()))))
    
    def _key_to_vector(self, context_key: str) -> List[float]:
        """Recupera vector desde clave (simplificado)"""
        # En implementación real, mantendríamos mapeo completo
        # Por simplicidad, generamos vector basado en hash
        hash_val = abs(hash(context_key))
        return [(hash_val >> i) % 100 / 100.0 for i in range(7)]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de performance del sistema"""
        if not self.performance_history:
            return {"error": "No hay datos de performance"}
        
        summary = {
            "total_records": len(self.performance_history),
            "regimes_detected": len(set(p.regime for p in self.performance_history)),
            "models_evaluated": len(set(p.model_name for p in self.performance_history)),
            "is_trained": self.is_trained,
            "current_weights": self.available_models
        }
        
        # Performance por régimen
        regime_stats = {}
        for regime in ContextRegime:
            regime_perfs = [p for p in self.performance_history if p.regime == regime]
            if regime_perfs:
                regime_stats[regime.value] = {
                    "count": len(regime_perfs),
                    "avg_f1": np.mean([p.f1_score for p in regime_perfs]),
                    "best_model": max(regime_perfs, key=lambda x: x.f1_score).model_name
                }
        
        summary["regime_statistics"] = regime_stats
        
        # Performance por modelo
        model_stats = {}
        for model_name in self.available_models.keys():
            model_perfs = [p for p in self.performance_history if p.model_name == model_name]
            if model_perfs:
                model_stats[model_name] = {
                    "evaluations": len(model_perfs),
                    "avg_f1": np.mean([p.f1_score for p in model_perfs]),
                    "current_weight": self.available_models[model_name]['weight']
                }
        
        summary["model_statistics"] = model_stats
        
        return summary
    
    def export_learning_state(self, filepath: str):
        """Exporta el estado de aprendizaje a archivo"""
        try:
            state = {
                "timestamp": datetime.now().isoformat(),
                "model_weights": self.available_models,
                "performance_history": [
                    {
                        "model_name": p.model_name,
                        "regime": p.regime.value,
                        "f1_score": p.f1_score,
                        "timestamp": p.timestamp.isoformat(),
                        "context_features": p.context_features
                    }
                    for p in self.performance_history[-100:]  # Últimos 100
                ],
                "regime_history": [
                    {"timestamp": ts.isoformat(), "regime": regime.value}
                    for ts, regime in self.regime_history[-50:]  # Últimos 50
                ],
                "is_trained": self.is_trained,
                "learning_rate": self.learning_rate
            }
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"💾 Estado de meta-learning exportado a {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error exportando estado: {e}")

# Funciones de utilidad
def create_meta_controller(memory_size: int = 1000) -> MetaLearningController:
    """Crea un controlador de meta-aprendizaje"""
    return MetaLearningController(memory_size)

def analyze_and_optimize(controller: MetaLearningController, 
                        historical_data: List[List[int]]) -> Tuple[PredictionContext, Dict[str, float]]:
    """Analiza contexto y obtiene pesos optimizados"""
    context = controller.analyze_current_context(historical_data)
    weights = controller.get_optimal_model_weights(context)
    return context, weights

if __name__ == "__main__":
    # Demo del controlador
    print("🧠 Demo Meta-Learning Controller")
    
    # Crear controlador
    controller = create_meta_controller()
    
    # Datos de ejemplo
    sample_data = [
        [1, 15, 23, 31, 35, 40],
        [3, 12, 18, 27, 33, 39],
        [5, 14, 22, 28, 34, 38],
        [2, 11, 19, 25, 32, 37],
        [7, 16, 24, 29, 36, 38],
        [4, 13, 21, 26, 34, 39],
        [6, 17, 25, 30, 37, 40],
        [8, 10, 20, 24, 31, 35]
    ]
    
    # Analizar contexto
    context, weights = analyze_and_optimize(controller, sample_data)
    
    print(f"\n📊 Contexto detectado: {context.regime.value}")
    print(f"🎯 Pesos optimizados:")
    for model, weight in weights.items():
        print(f"   {model}: {weight:.3f}")
    
    # Simular performance
    for model in weights.keys():
        results = {
            'accuracy': np.random.uniform(0.6, 0.9),
            'precision': np.random.uniform(0.5, 0.8),
            'recall': np.random.uniform(0.5, 0.8),
            'f1_score': np.random.uniform(0.5, 0.8)
        }
        controller.record_model_performance(model, context, results)
    
    # Mostrar resumen
    summary = controller.get_performance_summary()
    print(f"\n📈 Resumen de performance:")
    print(f"   Registros totales: {summary['total_records']}")
    print(f"   Modelos evaluados: {summary['models_evaluated']}")
    print(f"   Sistema entrenado: {summary['is_trained']}")
