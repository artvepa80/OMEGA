#!/usr/bin/env python3
"""
AI Ensemble System for OMEGA PRO AI
Sistema de múltiples IAs especializadas trabajando en conjunto
"""

import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod
import asyncio
import concurrent.futures
from enum import Enum

logger = logging.getLogger(__name__)

class AISpecialty(Enum):
    """Especialidades de IA"""
    PATTERN_RECOGNITION = "pattern_recognition"
    FREQUENCY_ANALYSIS = "frequency_analysis"
    SEQUENTIAL_MODELING = "sequential_modeling"
    PROBABILITY_ESTIMATION = "probability_estimation"
    TREND_PREDICTION = "trend_prediction"
    ANOMALY_DETECTION = "anomaly_detection"
    OPTIMIZATION = "optimization"
    RISK_ASSESSMENT = "risk_assessment"

@dataclass
class AIPrediction:
    """Resultado de predicción de una IA especializada"""
    ai_id: str
    specialty: AISpecialty
    prediction: List[int]
    confidence: float
    reasoning: str
    metadata: Dict[str, Any]
    timestamp: datetime

class SpecializedAI(ABC):
    """Clase base para IAs especializadas"""
    
    def __init__(self, ai_id: str, specialty: AISpecialty):
        self.ai_id = ai_id
        self.specialty = specialty
        self.performance_history = []
        self.learning_rate = 0.01
        
    @abstractmethod
    def predict(self, data: List[List[int]], context: Dict[str, Any] = None) -> AIPrediction:
        """Método abstracto para predicción"""
        pass
    
    @abstractmethod
    def train(self, training_data: List[List[int]], outcomes: List[bool] = None):
        """Método abstracto para entrenamiento"""
        pass
    
    def update_performance(self, accuracy: float):
        """Actualiza el historial de rendimiento"""
        self.performance_history.append({
            'timestamp': datetime.now(),
            'accuracy': accuracy
        })
        
        # Mantener solo últimos 100 registros
        if len(self.performance_history) > 100:
            self.performance_history.pop(0)
    
    def get_average_performance(self) -> float:
        """Obtiene el rendimiento promedio"""
        if not self.performance_history:
            return 0.5
        
        return np.mean([p['accuracy'] for p in self.performance_history])

class PatternRecognitionAI(SpecializedAI):
    """IA especializada en reconocimiento de patrones"""
    
    def __init__(self):
        super().__init__("pattern_ai", AISpecialty.PATTERN_RECOGNITION)
        self.pattern_memory = {}
        self.sequence_weights = np.random.random(10)
        
    def predict(self, data: List[List[int]], context: Dict[str, Any] = None) -> AIPrediction:
        """Predicción basada en reconocimiento de patrones"""
        logger.info(f"🔍 {self.ai_id}: Analizando patrones...")
        
        if not data:
            return self._generate_fallback_prediction()
        
        # Validar entrada
        try:
            for i, sequence in enumerate(data):
                if not isinstance(sequence, (list, tuple)) or len(sequence) != 6:
                    logger.warning(f"⚠️ Secuencia {i} inválida: esperado 6 números, recibido {len(sequence) if sequence else 0}")
                    continue
                if not all(isinstance(n, int) and 1 <= n <= 40 for n in sequence):
                    logger.warning(f"⚠️ Secuencia {i} contiene números fuera del rango 1-40")
                    continue
        except Exception as e:
            logger.error(f"❌ Error validando datos: {e}")
            return self._generate_fallback_prediction()
        
        # Análisis de patrones secuenciales
        patterns = self._extract_patterns(data)
        
        # Identificar el patrón más fuerte
        strongest_pattern = max(patterns.items(), key=lambda x: x[1]) if patterns else (None, 0)
        
        # Generar predicción basada en patrones
        prediction = self._generate_from_pattern(strongest_pattern[0], data)
        confidence = min(strongest_pattern[1], 0.95)
        
        reasoning = f"Patrón dominante identificado con fuerza {strongest_pattern[1]:.3f}. "
        reasoning += f"Secuencias analizadas: {len(data)}. "
        reasoning += f"Patrones únicos encontrados: {len(patterns)}."
        
        return AIPrediction(
            ai_id=self.ai_id,
            specialty=self.specialty,
            prediction=prediction,
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                'patterns_found': len(patterns),
                'strongest_pattern_strength': strongest_pattern[1],
                'pattern_type': strongest_pattern[0]
            },
            timestamp=datetime.now()
        )
    
    def _extract_patterns(self, data: List[List[int]]) -> Dict[str, float]:
        """Extrae patrones de los datos"""
        patterns = {}
        
        for sequence in data:
            # Patrones de diferencias
            diffs = [sequence[i+1] - sequence[i] for i in range(len(sequence)-1)]
            diff_pattern = tuple(diffs)
            patterns[f"diff_{hash(diff_pattern)}"] = patterns.get(f"diff_{hash(diff_pattern)}", 0) + 0.1
            
            # Patrones de suma
            total = sum(sequence)
            sum_range = total // 20  # Agrupar por rangos de suma
            patterns[f"sum_range_{sum_range}"] = patterns.get(f"sum_range_{sum_range}", 0) + 0.15
            
            # Patrones de paridad
            evens = len([n for n in sequence if n % 2 == 0])
            odds = len(sequence) - evens
            patterns[f"parity_{evens}_{odds}"] = patterns.get(f"parity_{evens}_{odds}", 0) + 0.1
        
        # Normalizar por frecuencia
        max_freq = max(patterns.values()) if patterns else 1
        return {k: v/max_freq for k, v in patterns.items()}
    
    def _generate_from_pattern(self, pattern_key: str, data: List[List[int]]) -> List[int]:
        """Genera combinación basada en patrón identificado"""
        if not pattern_key or not data:
            return sorted(np.random.choice(range(1, 41), 6, replace=False))
        
        last_sequence = data[-1]
        
        if "diff_" in pattern_key:
            # Continuar patrón de diferencias
            return self._continue_diff_pattern(last_sequence)
        elif "sum_range_" in pattern_key:
            # Mantener rango de suma
            return self._maintain_sum_range(last_sequence)
        elif "parity_" in pattern_key:
            # Mantener distribución de paridad
            return self._maintain_parity(pattern_key)
        
        return sorted(np.random.choice(range(1, 41), 6, replace=False))
    
    def _continue_diff_pattern(self, sequence: List[int]) -> List[int]:
        """Continúa patrón de diferencias"""
        diffs = [sequence[i+1] - sequence[i] for i in range(len(sequence)-1)]
        avg_diff = np.mean(diffs)
        
        new_sequence = [sequence[-1]]
        for _ in range(5):
            next_num = new_sequence[-1] + int(avg_diff) + np.random.randint(-2, 3)
            next_num = max(1, min(40, next_num))
            if next_num not in new_sequence:
                new_sequence.append(next_num)
            else:
                new_sequence.append(np.random.randint(1, 41))
        
        return sorted(new_sequence)
    
    def _maintain_sum_range(self, sequence: List[int]) -> List[int]:
        """Mantiene rango de suma"""
        target_sum = sum(sequence)
        new_sequence = []
        
        while len(new_sequence) < 6:
            remaining = 6 - len(new_sequence)
            avg_needed = (target_sum - sum(new_sequence)) // remaining if remaining > 0 else 20
            
            candidate = max(1, min(40, avg_needed + np.random.randint(-5, 6)))
            if candidate not in new_sequence:
                new_sequence.append(candidate)
        
        return sorted(new_sequence)
    
    def _maintain_parity(self, pattern_key: str) -> List[int]:
        """Mantiene distribución de paridad"""
        parts = pattern_key.split('_')
        target_evens = int(parts[1]) if len(parts) > 1 else 3
        
        new_sequence = []
        evens_added = 0
        
        while len(new_sequence) < 6:
            need_even = evens_added < target_evens and (6 - len(new_sequence)) > (target_evens - evens_added)
            
            if need_even:
                candidate = np.random.choice([n for n in range(2, 41, 2) if n not in new_sequence])
                evens_added += 1
            else:
                candidate = np.random.choice([n for n in range(1, 41, 2) if n not in new_sequence])
            
            new_sequence.append(candidate)
        
        return sorted(new_sequence)
    
    def _generate_fallback_prediction(self) -> AIPrediction:
        """Genera predicción de respaldo"""
        prediction = sorted(np.random.choice(range(1, 41), 6, replace=False))
        
        return AIPrediction(
            ai_id=self.ai_id,
            specialty=self.specialty,
            prediction=prediction,
            confidence=0.3,
            reasoning="Predicción de respaldo - datos insuficientes",
            metadata={'fallback': True},
            timestamp=datetime.now()
        )
    
    def train(self, training_data: List[List[int]], outcomes: List[bool] = None):
        """Entrena el reconocedor de patrones"""
        logger.info(f"📚 {self.ai_id}: Entrenando con {len(training_data)} secuencias...")
        
        # Validar datos de entrenamiento
        if not training_data:
            logger.warning("⚠️ No hay datos de entrenamiento")
            return
        
        valid_sequences = []
        for i, sequence in enumerate(training_data):
            if len(sequence) == 6 and all(1 <= n <= 40 for n in sequence):
                valid_sequences.append(sequence)
            else:
                logger.warning(f"⚠️ Secuencia de entrenamiento {i} inválida: {sequence}")
        
        if not valid_sequences:
            logger.error("❌ No hay secuencias válidas para entrenamiento")
            return
        
        # Actualizar patrones con pesos basados en outcomes
        for i, sequence in enumerate(valid_sequences):
            patterns = self._extract_patterns([sequence])
            outcome_weight = 1.0
            
            if outcomes and i < len(outcomes):
                outcome_weight = 1.5 if outcomes[i] else 0.5  # Reforzar patrones exitosos
            
            for pattern, strength in patterns.items():
                if pattern not in self.pattern_memory:
                    self.pattern_memory[pattern] = {'strengths': [], 'success_rate': 0.5}
                
                self.pattern_memory[pattern]['strengths'].append(strength * outcome_weight)
                
                # Mantener solo últimos 50 registros para evitar memoria excesiva
                if len(self.pattern_memory[pattern]['strengths']) > 50:
                    self.pattern_memory[pattern]['strengths'].pop(0)
                
                # Actualizar tasa de éxito
                if outcomes and i < len(outcomes):
                    current_success = self.pattern_memory[pattern]['success_rate']
                    new_success = outcomes[i]
                    # Promedio móvil con factor de decaimiento
                    self.pattern_memory[pattern]['success_rate'] = 0.9 * current_success + 0.1 * new_success

class FrequencyAnalysisAI(SpecializedAI):
    """IA especializada en análisis de frecuencias"""
    
    def __init__(self):
        super().__init__("frequency_ai", AISpecialty.FREQUENCY_ANALYSIS)
        self.number_frequencies = np.zeros(40)  # Frecuencias de números 1-40
        self.position_frequencies = np.zeros((6, 40))  # Frecuencias por posición
        
    def predict(self, data: List[List[int]], context: Dict[str, Any] = None) -> AIPrediction:
        """Predicción basada en análisis de frecuencias"""
        logger.info(f"📊 {self.ai_id}: Analizando frecuencias...")
        
        if not data:
            return self._generate_fallback_prediction()
        
        # Actualizar frecuencias
        self._update_frequencies(data)
        
        # Generar predicción basada en frecuencias
        prediction = self._generate_frequency_based_prediction()
        
        # Calcular confianza basada en consistencia de frecuencias
        confidence = self._calculate_frequency_confidence()
        
        reasoning = f"Análisis de {len(data)} secuencias. "
        reasoning += f"Números más frecuentes: {self._get_top_frequent_numbers(3)}. "
        reasoning += f"Distribución de frecuencias estable: {confidence > 0.6}."
        
        return AIPrediction(
            ai_id=self.ai_id,
            specialty=self.specialty,
            prediction=prediction,
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                'total_sequences': len(data),
                'top_frequent': self._get_top_frequent_numbers(5),
                'frequency_variance': np.var(self.number_frequencies)
            },
            timestamp=datetime.now()
        )
    
    def _update_frequencies(self, data: List[List[int]]):
        """Actualiza las frecuencias basadas en nuevos datos"""
        for sequence in data:
            for i, number in enumerate(sequence):
                if 1 <= number <= 40:
                    self.number_frequencies[number-1] += 1
                    if i < 6:
                        self.position_frequencies[i][number-1] += 1
    
    def _generate_frequency_based_prediction(self) -> List[int]:
        """Genera predicción basada en frecuencias"""
        # Normalizar frecuencias con suavizado para evitar sesgo extremo
        total_freq = np.sum(self.number_frequencies)
        if total_freq == 0:
            # Si no hay frecuencias, usar distribución uniforme
            normalized_freq = np.ones(40) / 40
        else:
            # Suavizado laplaciano para evitar probabilidades cero
            smoothed_freq = self.number_frequencies + 1.0
            normalized_freq = smoothed_freq / np.sum(smoothed_freq)
        
        # Limitar frecuencias máximas para evitar sesgo hacia números muy frecuentes
        max_allowed_freq = 0.15  # No más del 15% de probabilidad para un número
        normalized_freq = np.minimum(normalized_freq, max_allowed_freq)
        normalized_freq = normalized_freq / np.sum(normalized_freq)  # Re-normalizar
        
        # Añadir ruido controlado para diversidad
        noise_factor = 0.1  # Menor ruido para más estabilidad
        freq_with_noise = normalized_freq + np.random.normal(0, noise_factor * normalized_freq, 40)
        freq_with_noise = np.maximum(freq_with_noise, 0.001)  # Mínimo positivo
        
        # Seleccionar números basados en probabilidades
        prediction = []
        available_numbers = list(range(1, 41))
        
        for _ in range(6):
            if not available_numbers:
                break
            
            # Crear probabilidades solo para números disponibles
            available_indices = [n-1 for n in available_numbers]
            probs = freq_with_noise[available_indices]
            probs = probs / np.sum(probs) if np.sum(probs) > 0 else np.ones(len(probs)) / len(probs)
            
            # Seleccionar número
            chosen_idx = np.random.choice(len(available_numbers), p=probs)
            chosen_number = available_numbers[chosen_idx]
            
            prediction.append(chosen_number)
            available_numbers.remove(chosen_number)
        
        return sorted(prediction)
    
    def _calculate_frequency_confidence(self) -> float:
        """Calcula confianza basada en estabilidad de frecuencias"""
        if np.sum(self.number_frequencies) == 0:
            return 0.3
        
        # Confianza basada en la uniformidad de la distribución
        normalized = self.number_frequencies / np.sum(self.number_frequencies)
        entropy = -np.sum(normalized * np.log(normalized + 1e-10))
        max_entropy = np.log(40)  # Máxima entropía para 40 números
        
        # Convertir entropía a confianza (mayor entropía = menor confianza en frecuencias específicas)
        confidence = 0.3 + 0.5 * (1 - entropy / max_entropy)
        
        return min(confidence, 0.9)
    
    def _get_top_frequent_numbers(self, top_n: int) -> List[int]:
        """Obtiene los números más frecuentes"""
        indices = np.argsort(self.number_frequencies)[::-1][:top_n]
        return [i + 1 for i in indices]
    
    def _generate_fallback_prediction(self) -> AIPrediction:
        """Genera predicción de respaldo"""
        prediction = sorted(np.random.choice(range(1, 41), 6, replace=False))
        
        return AIPrediction(
            ai_id=self.ai_id,
            specialty=self.specialty,
            prediction=prediction,
            confidence=0.3,
            reasoning="Predicción de respaldo - sin datos de frecuencia",
            metadata={'fallback': True},
            timestamp=datetime.now()
        )
    
    def train(self, training_data: List[List[int]], outcomes: List[bool] = None):
        """Entrena el analizador de frecuencias"""
        logger.info(f"📚 {self.ai_id}: Entrenando con {len(training_data)} secuencias...")
        
        # Validar datos de entrenamiento
        if not training_data:
            logger.warning("⚠️ No hay datos de entrenamiento")
            return
        
        # Reiniciar frecuencias para entrenamiento fresco
        self.number_frequencies = np.zeros(40)
        self.position_frequencies = np.zeros((6, 40))
        
        # Validar y procesar solo secuencias válidas
        valid_sequences = []
        for i, sequence in enumerate(training_data):
            if len(sequence) == 6 and all(isinstance(n, int) and 1 <= n <= 40 for n in sequence):
                valid_sequences.append(sequence)
            else:
                logger.warning(f"⚠️ Secuencia de entrenamiento {i} inválida: {sequence}")
        
        if not valid_sequences:
            logger.error("❌ No hay secuencias válidas para entrenamiento")
            return
        
        # Actualizar frecuencias con ponderación por outcomes
        for i, sequence in enumerate(valid_sequences):
            weight = 1.0
            if outcomes and i < len(outcomes):
                weight = 2.0 if outcomes[i] else 0.5  # Ponderar secuencias exitosas
            
            for j, number in enumerate(sequence):
                self.number_frequencies[number-1] += weight
                if j < 6:
                    self.position_frequencies[j][number-1] += weight
        
        logger.info(f"✅ Entrenamiento completado con {len(valid_sequences)} secuencias válidas")

class TrendPredictionAI(SpecializedAI):
    """IA especializada en predicción de tendencias"""
    
    def __init__(self):
        super().__init__("trend_ai", AISpecialty.TREND_PREDICTION)
        self.trend_window = 10  # Ventana para análisis de tendencias
        self.momentum_weights = np.exp(np.linspace(-1, 0, self.trend_window))  # Pesos exponenciales
        
    def predict(self, data: List[List[int]], context: Dict[str, Any] = None) -> AIPrediction:
        """Predicción basada en análisis de tendencias"""
        logger.info(f"📈 {self.ai_id}: Analizando tendencias...")
        
        # Validar datos suficientes para análisis de tendencias
        if not data or len(data) < 3:
            logger.warning(f"⚠️ Datos insuficientes para análisis de tendencias: {len(data) if data else 0} secuencias")
            return self._generate_fallback_prediction()
        
        # Validar calidad de los datos
        valid_data = []
        for i, sequence in enumerate(data):
            if len(sequence) == 6 and all(isinstance(n, int) and 1 <= n <= 40 for n in sequence):
                valid_data.append(sequence)
            else:
                logger.warning(f"⚠️ Secuencia {i} inválida para análisis de tendencias: {sequence}")
        
        if len(valid_data) < 3:
            logger.warning(f"⚠️ Muy pocas secuencias válidas para tendencias: {len(valid_data)}")
            return self._generate_fallback_prediction()
        
        # Analizar tendencias en múltiples métricas
        trends = self._analyze_trends(data)
        
        # Generar predicción basada en tendencias
        prediction = self._generate_trend_prediction(data, trends)
        
        # Calcular confianza basada en consistencia de tendencias
        confidence = self._calculate_trend_confidence(trends)
        
        reasoning = f"Análisis de tendencias en {len(data)} secuencias. "
        reasoning += f"Tendencia de suma: {trends.get('sum_trend', 0):.2f}. "
        reasoning += f"Tendencia de rango: {trends.get('range_trend', 0):.2f}. "
        reasoning += f"Momentum detectado: {abs(trends.get('momentum', 0)) > 0.1}."
        
        return AIPrediction(
            ai_id=self.ai_id,
            specialty=self.specialty,
            prediction=prediction,
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                'trends_analyzed': list(trends.keys()),
                'strongest_trend': max(trends.items(), key=lambda x: abs(x[1])),
                'trend_consistency': confidence
            },
            timestamp=datetime.now()
        )
    
    def _analyze_trends(self, data: List[List[int]]) -> Dict[str, float]:
        """Analiza múltiples tipos de tendencias"""
        trends = {}
        
        # Tendencia de suma total
        sums = [sum(seq) for seq in data[-self.trend_window:]]
        if len(sums) > 1:
            trends['sum_trend'] = self._calculate_linear_trend(sums)
        
        # Tendencia de rango (max - min)
        ranges = [max(seq) - min(seq) for seq in data[-self.trend_window:]]
        if len(ranges) > 1:
            trends['range_trend'] = self._calculate_linear_trend(ranges)
        
        # Tendencia de números altos vs bajos
        high_counts = [len([n for n in seq if n > 20]) for seq in data[-self.trend_window:]]
        if len(high_counts) > 1:
            trends['high_low_trend'] = self._calculate_linear_trend(high_counts)
        
        # Momentum (aceleración de cambios)
        if len(data) >= 5:
            recent_changes = [abs(sum(data[i]) - sum(data[i-1])) for i in range(-4, 0)]
            trends['momentum'] = np.mean(recent_changes[-2:]) - np.mean(recent_changes[:2])
        
        return trends
    
    def _calculate_linear_trend(self, values: List[float]) -> float:
        """Calcula tendencia lineal de una serie de valores"""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)
        return coeffs[0]  # Pendiente
    
    def _generate_trend_prediction(self, data: List[List[int]], trends: Dict[str, float]) -> List[int]:
        """Genera predicción basada en tendencias"""
        last_sequence = data[-1]
        
        # Predecir suma objetivo basada en tendencia
        current_sum = sum(last_sequence)
        sum_trend = trends.get('sum_trend', 0)
        target_sum = current_sum + sum_trend
        target_sum = max(21, min(240, target_sum))  # Límites razonables
        
        # Predecir rango objetivo
        current_range = max(last_sequence) - min(last_sequence)
        range_trend = trends.get('range_trend', 0)
        target_range = current_range + range_trend
        target_range = max(5, min(39, target_range))
        
        # Generar números para alcanzar objetivos
        prediction = self._generate_numbers_for_targets(target_sum, target_range, trends)
        
        return sorted(prediction)
    
    def _generate_numbers_for_targets(self, target_sum: float, target_range: float, trends: Dict[str, float]) -> List[int]:
        """Genera números para alcanzar objetivos de suma y rango"""
        prediction = []
        
        # Determinar números mínimo y máximo para el rango objetivo
        mid_point = target_sum / 6
        half_range = target_range / 2
        
        min_num = max(1, int(mid_point - half_range))
        max_num = min(40, int(mid_point + half_range))
        
        # Ajustar según tendencia high/low
        high_low_trend = trends.get('high_low_trend', 0)
        if high_low_trend > 0:  # Tendencia hacia números altos
            min_num += 2
            max_num += 2
        elif high_low_trend < 0:  # Tendencia hacia números bajos
            min_num -= 2
            max_num -= 2
        
        # Generar números en el rango ajustado
        available_range = list(range(max(1, min_num), min(41, max_num + 1)))
        
        if len(available_range) < 6:
            available_range = list(range(1, 41))
        
        # Seleccionar 6 números intentando aproximar la suma objetivo
        attempts = 0
        while len(prediction) < 6 and attempts < 100:
            candidate = np.random.choice(available_range)
            if candidate not in prediction:
                prediction.append(candidate)
            attempts += 1
        
        # Completar si no se llenó
        while len(prediction) < 6:
            candidate = np.random.randint(1, 41)
            if candidate not in prediction:
                prediction.append(candidate)
        
        return prediction
    
    def _calculate_trend_confidence(self, trends: Dict[str, float]) -> float:
        """Calcula confianza basada en consistencia de tendencias"""
        if not trends:
            return 0.3
        
        # Confianza basada en la magnitud de las tendencias
        trend_magnitudes = [abs(trend) for trend in trends.values()]
        avg_magnitude = np.mean(trend_magnitudes)
        
        # Normalizar a rango 0.3-0.8
        confidence = 0.3 + min(0.5, avg_magnitude * 0.1)
        
        return confidence
    
    def _generate_fallback_prediction(self) -> AIPrediction:
        """Genera predicción de respaldo"""
        prediction = sorted(np.random.choice(range(1, 41), 6, replace=False))
        
        return AIPrediction(
            ai_id=self.ai_id,
            specialty=self.specialty,
            prediction=prediction,
            confidence=0.3,
            reasoning="Predicción de respaldo - datos insuficientes para análisis de tendencias",
            metadata={'fallback': True},
            timestamp=datetime.now()
        )
    
    def train(self, training_data: List[List[int]], outcomes: List[bool] = None):
        """Entrena el predictor de tendencias"""
        logger.info(f"📚 {self.ai_id}: Entrenando con {len(training_data)} secuencias...")
        # El entrenamiento se hace implícitamente a través del análisis de tendencias

class AIEnsembleSystem:
    """Sistema de ensemble de múltiples IAs especializadas"""
    
    def __init__(self):
        self.specialists = [
            PatternRecognitionAI(),
            FrequencyAnalysisAI(),
            TrendPredictionAI()
        ]
        
        self.ensemble_weights = np.ones(len(self.specialists)) / len(self.specialists)
        self.performance_tracker = {}
        self.meta_learner_enabled = True
        
    async def generate_ensemble_predictions(self, data: List[List[int]], num_predictions: int = 5) -> List[Dict[str, Any]]:
        """Genera predicciones usando todo el ensemble de IAs"""
        logger.info(f"🤖 Generando {num_predictions} predicciones con ensemble de {len(self.specialists)} IAs...")
        
        # Obtener predicciones de todas las IAs en paralelo
        individual_predictions = await self._get_all_predictions(data)
        
        # Generar predicciones ensemble
        ensemble_predictions = []
        
        for i in range(num_predictions):
            # Combinar predicciones usando diferentes estrategias
            if i % 3 == 0:  # Votación ponderada
                prediction = self._weighted_voting(individual_predictions)
            elif i % 3 == 1:  # Consenso
                prediction = self._consensus_method(individual_predictions)
            else:  # Hibridación
                prediction = self._hybrid_method(individual_predictions)
            
            # Calcular confianza ensemble
            confidence = self._calculate_ensemble_confidence(individual_predictions, prediction)
            
            ensemble_predictions.append({
                'combination': prediction,
                'confidence': confidence,
                'source': 'ai_ensemble',
                'individual_predictions': individual_predictions,
                'method': ['weighted_voting', 'consensus', 'hybrid'][i % 3],
                'specialists_used': len(self.specialists),
                'timestamp': datetime.now().isoformat()
            })
        
        logger.info(f"✅ Generadas {len(ensemble_predictions)} predicciones ensemble")
        return ensemble_predictions
    
    async def _get_all_predictions(self, data: List[List[int]]) -> List[AIPrediction]:
        """Obtiene predicciones de todas las IAs en paralelo"""
        predictions = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.specialists)) as executor:
            # Crear futures con manejo de excepciones
            futures = {}
            for ai in self.specialists:
                future = executor.submit(self._safe_predict, ai, data)
                futures[future] = ai
            
            # Recopilar resultados manejando excepciones
            for future in concurrent.futures.as_completed(futures):
                ai = futures[future]
                try:
                    prediction = future.result(timeout=30)  # Timeout de 30 segundos
                    if prediction:
                        predictions.append(prediction)
                    else:
                        logger.warning(f"⚠️ {ai.ai_id} devolvió predicción nula")
                except concurrent.futures.TimeoutError:
                    logger.error(f"❌ Timeout en {ai.ai_id}: predicción tomó más de 30 segundos")
                except Exception as e:
                    logger.error(f"❌ Error en predicción de {ai.ai_id}: {e}")
                    # Generar predicción de fallback para esta IA
                    try:
                        fallback = ai._generate_fallback_prediction()
                        predictions.append(fallback)
                    except:
                        logger.error(f"❌ Error crítico en fallback de {ai.ai_id}")
        
        return predictions
    
    def _safe_predict(self, ai: SpecializedAI, data: List[List[int]]) -> Optional[AIPrediction]:
        """Predicción segura con manejo de excepciones"""
        try:
            return ai.predict(data)
        except Exception as e:
            logger.error(f"❌ Error en {ai.ai_id}.predict(): {e}")
            try:
                return ai._generate_fallback_prediction()
            except:
                logger.error(f"❌ Error crítico en fallback de {ai.ai_id}")
                return None
    
    def _weighted_voting(self, predictions: List[AIPrediction]) -> List[int]:
        """Combina predicciones usando votación ponderada"""
        if not predictions:
            return sorted(np.random.choice(range(1, 41), 6, replace=False))
        
        number_votes = np.zeros(40)
        total_weight = 0
        
        for i, prediction in enumerate(predictions):
            if i < len(self.ensemble_weights):
                weight = self.ensemble_weights[i] * prediction.confidence
                total_weight += weight
                
                # Penalizar repeticiones en la misma predicción
                unique_numbers = list(set(prediction.prediction))
                repetition_penalty = len(prediction.prediction) / len(unique_numbers) if unique_numbers else 1
                adjusted_weight = weight / repetition_penalty
                
                for number in unique_numbers:
                    if 1 <= number <= 40:
                        number_votes[number - 1] += adjusted_weight
        
        # Normalizar votos si hay peso total
        if total_weight > 0:
            number_votes = number_votes / total_weight
        
        # Añadir pequeña aleatoriedad para empates
        number_votes += np.random.normal(0, 0.001, 40)
        
        # Seleccionar los 6 números con mayor votación
        top_indices = np.argsort(number_votes)[-6:]
        result = sorted([int(idx + 1) for idx in top_indices])  # Convertir a int estándar
        
        # Verificar que no hay duplicados (redundante pero seguro)
        if len(set(result)) != 6:
            logger.warning("⚠️ Duplicados detectados en weighted voting, regenerando...")
            return sorted([int(x) for x in np.random.choice(range(1, 41), 6, replace=False)])
        
        return result
    
    def _consensus_method(self, predictions: List[AIPrediction]) -> List[int]:
        """Combina predicciones buscando consenso"""
        if not predictions:
            return sorted(np.random.choice(range(1, 41), 6, replace=False))
        
        # Encontrar números que aparecen en múltiples predicciones con ponderación por confianza
        number_frequency = {}
        number_confidence = {}
        
        for prediction in predictions:
            unique_numbers = list(set(prediction.prediction))  # Evitar duplicados en una predicción
            for number in unique_numbers:
                if 1 <= number <= 40:
                    number_frequency[number] = number_frequency.get(number, 0) + 1
                    # Acumular confianza ponderada
                    current_conf = number_confidence.get(number, 0)
                    number_confidence[number] = current_conf + prediction.confidence
        
        # Priorizar números con alta frecuencia Y alta confianza
        consensus_score = {}
        for number in number_frequency:
            freq = number_frequency[number]
            avg_confidence = number_confidence[number] / freq  # Confianza promedio
            # Score híbrido: frecuencia * confianza
            consensus_score[number] = freq * avg_confidence
        
        # Ordenar por score de consenso
        sorted_numbers = sorted(consensus_score.items(), key=lambda x: x[1], reverse=True)
        consensus_numbers = [num for num, score in sorted_numbers[:6]]
        
        # Completar si es necesario con números de alta confianza
        while len(consensus_numbers) < 6:
            best_prediction = max(predictions, key=lambda p: p.confidence)
            for number in best_prediction.prediction:
                if number not in consensus_numbers and 1 <= number <= 40:
                    consensus_numbers.append(number)
                    break
            
            # Prevenir bucle infinito
            if len(consensus_numbers) >= len(set().union(*[p.prediction for p in predictions])):
                break
        
        # Rellenar con números aleatorios únicos si es necesario
        while len(consensus_numbers) < 6:
            candidate = np.random.randint(1, 41)
            if candidate not in consensus_numbers:
                consensus_numbers.append(candidate)
        
        # Asegurar no duplicados
        unique_result = list(dict.fromkeys(consensus_numbers))[:6]
        
        # Si aún faltan números, completar con aleatorios
        while len(unique_result) < 6:
            candidate = np.random.randint(1, 41)
            if candidate not in unique_result:
                unique_result.append(candidate)
        
        return sorted([int(x) for x in unique_result[:6]])
    
    def _hybrid_method(self, predictions: List[AIPrediction]) -> List[int]:
        """Combina predicciones usando método híbrido"""
        # Tomar elementos de cada predicción basado en su especialidad
        hybrid_prediction = []
        
        # Distribuir números según especialidad de cada IA
        numbers_per_ai = 6 // len(predictions)
        extra_numbers = 6 % len(predictions)
        
        for i, prediction in enumerate(predictions):
            take_count = numbers_per_ai + (1 if i < extra_numbers else 0)
            
            # Tomar los números más "representativos" de esta IA
            available_numbers = [n for n in prediction.prediction if n not in hybrid_prediction]
            
            for j in range(min(take_count, len(available_numbers))):
                hybrid_prediction.append(available_numbers[j])
        
        # Completar si es necesario
        while len(hybrid_prediction) < 6:
            candidate = np.random.randint(1, 41)
            if candidate not in hybrid_prediction:
                hybrid_prediction.append(candidate)
        
        return sorted([int(x) for x in hybrid_prediction[:6]])
    
    def _calculate_ensemble_confidence(self, individual_predictions: List[AIPrediction], ensemble_prediction: List[int]) -> float:
        """Calcula la confianza del ensemble"""
        # Confianza promedio ponderada de las predicciones individuales
        weighted_confidence = sum(pred.confidence * weight for pred, weight in zip(individual_predictions, self.ensemble_weights))
        
        # Bonus por consenso
        consensus_bonus = 0
        for number in ensemble_prediction:
            appearances = sum(1 for pred in individual_predictions if number in pred.prediction)
            consensus_bonus += appearances / len(individual_predictions)
        
        consensus_bonus /= 6  # Normalizar por número de números
        
        # Combinar confianzas
        ensemble_confidence = 0.7 * weighted_confidence + 0.3 * consensus_bonus
        
        return min(ensemble_confidence, 0.95)
    
    def train_ensemble(self, training_data: List[List[int]], outcomes: List[bool] = None):
        """Entrena todo el ensemble"""
        logger.info(f"🎓 Entrenando ensemble con {len(training_data)} ejemplos...")
        
        # Entrenar cada IA especializada
        for ai in self.specialists:
            ai.train(training_data, outcomes)
        
        # Actualizar pesos del ensemble si hay resultados
        if outcomes and len(outcomes) == len(training_data):
            self._update_ensemble_weights(training_data, outcomes)
        
        logger.info("✅ Entrenamiento del ensemble completado")
    
    def _update_ensemble_weights(self, training_data: List[List[int]], outcomes: List[bool]):
        """Actualiza los pesos del ensemble basado en rendimiento"""
        if not self.meta_learner_enabled:
            return
        
        # Evaluar cada IA individualmente
        individual_accuracies = []
        
        for ai in self.specialists:
            correct_predictions = 0
            
            for data_point, outcome in zip(training_data, outcomes):
                prediction = ai.predict([data_point])
                # Simplificación: considerar "correcto" si la predicción está cerca del outcome esperado
                if outcome:  # Si el outcome fue positivo, premiamos confianza alta
                    if prediction.confidence > 0.5:
                        correct_predictions += 1
                else:  # Si fue negativo, premiamos confianza baja
                    if prediction.confidence <= 0.5:
                        correct_predictions += 1
            
            accuracy = correct_predictions / len(outcomes) if outcomes else 0.5
            individual_accuracies.append(accuracy)
            ai.update_performance(accuracy)
        
        # Actualizar pesos basado en rendimiento
        total_accuracy = sum(individual_accuracies)
        if total_accuracy > 0:
            self.ensemble_weights = np.array(individual_accuracies) / total_accuracy
        
        logger.info(f"📊 Pesos del ensemble actualizados: {self.ensemble_weights}")
    
    def get_ensemble_analysis(self) -> Dict[str, Any]:
        """Obtiene análisis del estado del ensemble"""
        analysis = {
            'total_specialists': len(self.specialists),
            'ensemble_weights': self.ensemble_weights.tolist(),
            'specialists_info': [],
            'meta_learning_enabled': self.meta_learner_enabled
        }
        
        for i, ai in enumerate(self.specialists):
            specialist_info = {
                'ai_id': ai.ai_id,
                'specialty': ai.specialty.value,
                'weight': self.ensemble_weights[i],
                'average_performance': ai.get_average_performance(),
                'total_predictions': len(ai.performance_history)
            }
            analysis['specialists_info'].append(specialist_info)
        
        return analysis

# Funciones de utilidad
def create_ai_ensemble() -> AIEnsembleSystem:
    """Crea el sistema de ensemble de IA"""
    logger.info("🤖 Inicializando ensemble de IAs especializadas...")
    return AIEnsembleSystem()

async def generate_intelligent_predictions(ensemble: AIEnsembleSystem, historical_data: List[List[int]], count: int = 5) -> List[Dict[str, Any]]:
    """Genera predicciones inteligentes usando el ensemble"""
    return await ensemble.generate_ensemble_predictions(historical_data, count)

if __name__ == "__main__":
    # Ejemplo de uso
    async def main():
        ensemble = create_ai_ensemble()
        
        # Datos de ejemplo
        sample_data = [
            [1, 15, 23, 31, 35, 40],
            [3, 12, 18, 27, 33, 39],
            [5, 14, 22, 28, 34, 38],
            [2, 11, 19, 25, 32, 37]
        ]
        
        # Entrenar ensemble
        ensemble.train_ensemble(sample_data)
        
        # Generar predicciones
        predictions = await generate_intelligent_predictions(ensemble, sample_data, 3)
        
        print("🤖 Predicciones del Ensemble AI:")
        for i, pred in enumerate(predictions, 1):
            print(f"{i}. {pred['combination']} (Confianza: {pred['confidence']:.1%})")
        
        # Análisis del ensemble
        analysis = ensemble.get_ensemble_analysis()
        print(f"\n📊 Análisis del Ensemble: {analysis['total_specialists']} especialistas activos")
    
    # Ejecutar ejemplo
    asyncio.run(main())
