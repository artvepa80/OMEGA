#!/usr/bin/env python3
"""
Perfilador Dinámico para OMEGA PRO AI
Predictor dinámico de perfiles jackpot en tiempo real
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix
from scipy import stats
from scipy.fft import fft, fftfreq
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class JackpotProfile(Enum):
    """Perfiles de jackpot identificados"""
    PROFILE_A = "high_frequency_stable"     # Alta frecuencia, patrones estables
    PROFILE_B = "moderate_mixed"           # Moderado, patrones mixtos
    PROFILE_C = "low_frequency_chaotic"    # Baja frecuencia, patrones caóticos
    PROFILE_UNKNOWN = "unknown"

@dataclass
class ProfileFeatures:
    """Features para clasificación de perfiles"""
    # Features de entropía
    entropy_shannon: float
    entropy_relative: float
    entropy_conditional: float
    
    # Features de frecuencia
    frequency_variance: float
    frequency_skewness: float
    frequency_kurtosis: float
    
    # Features de FFT
    dominant_frequency: float
    spectral_density: float
    harmonic_ratio: float
    
    # Features temporales
    trend_strength: float
    seasonality_score: float
    volatility_index: float
    
    # Features de distribución
    range_ratio: float
    gap_analysis: float
    clustering_coefficient: float
    
    # Features de secuencias
    sequence_entropy: float
    transition_matrix_entropy: float
    repetition_score: float

@dataclass
class ProfilePrediction:
    """Predicción de perfil"""
    profile: JackpotProfile
    confidence: float
    probability_distribution: Dict[str, float]
    features_importance: Dict[str, float]
    timestamp: datetime

class DynamicProfiler:
    """Perfilador dinámico de jackpots"""
    
    def __init__(self, 
                 window_size: int = 50,
                 min_samples: int = 20,
                 ensemble_size: int = 3):
        
        self.window_size = window_size
        self.min_samples = min_samples
        self.ensemble_size = ensemble_size
        
        # Modelos de clasificación
        self.models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=42
            ),
            'svm': SVC(
                kernel='rbf',
                probability=True,
                random_state=42,
                class_weight='balanced'
            )
        }
        
        # Scaler para normalización
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Estado del modelo
        self.is_trained = False
        self.feature_names = []
        self.training_history = []
        self.profile_transitions = []
        
        # Cache de features
        self.features_cache = {}
        
        logger.info("🎯 Perfilador Dinámico inicializado")
        logger.info(f"   Ventana: {window_size}, Mínimo: {min_samples}, Ensemble: {ensemble_size}")
    
    def extract_features(self, data: List[List[int]], window_data: List[List[int]] = None) -> ProfileFeatures:
        """Extrae features completas para clasificación de perfil"""
        
        if len(data) < self.min_samples:
            logger.warning(f"⚠️ Pocos datos para análisis ({len(data)})")
            return self._get_default_features()
        
        try:
            # Usar ventana si se proporciona, sino usar todos los datos
            analysis_data = window_data if window_data else data[-self.window_size:]
            
            # Cache key
            cache_key = self._get_cache_key(analysis_data)
            if cache_key in self.features_cache:
                return self.features_cache[cache_key]
            
            # Convertir a arrays para análisis
            all_numbers = np.concatenate(analysis_data)
            sums = np.array([sum(combo) for combo in analysis_data])
            ranges = np.array([max(combo) - min(combo) for combo in analysis_data])
            
            # 1. Features de Entropía
            entropy_features = self._calculate_entropy_features(all_numbers, analysis_data)
            
            # 2. Features de Frecuencia
            frequency_features = self._calculate_frequency_features(all_numbers)
            
            # 3. Features de FFT
            fft_features = self._calculate_fft_features(sums)
            
            # 4. Features Temporales
            temporal_features = self._calculate_temporal_features(sums, ranges)
            
            # 5. Features de Distribución
            distribution_features = self._calculate_distribution_features(analysis_data, ranges)
            
            # 6. Features de Secuencias
            sequence_features = self._calculate_sequence_features(analysis_data)
            
            features = ProfileFeatures(
                # Entropía
                entropy_shannon=entropy_features['shannon'],
                entropy_relative=entropy_features['relative'],
                entropy_conditional=entropy_features['conditional'],
                
                # Frecuencia
                frequency_variance=frequency_features['variance'],
                frequency_skewness=frequency_features['skewness'],
                frequency_kurtosis=frequency_features['kurtosis'],
                
                # FFT
                dominant_frequency=fft_features['dominant'],
                spectral_density=fft_features['density'],
                harmonic_ratio=fft_features['harmonic'],
                
                # Temporal
                trend_strength=temporal_features['trend'],
                seasonality_score=temporal_features['seasonality'],
                volatility_index=temporal_features['volatility'],
                
                # Distribución
                range_ratio=distribution_features['range_ratio'],
                gap_analysis=distribution_features['gap_analysis'],
                clustering_coefficient=distribution_features['clustering'],
                
                # Secuencias
                sequence_entropy=sequence_features['entropy'],
                transition_matrix_entropy=sequence_features['transition'],
                repetition_score=sequence_features['repetition']
            )
            
            # Guardar en cache
            self.features_cache[cache_key] = features
            
            # Limpiar cache si crece mucho
            if len(self.features_cache) > 100:
                oldest_key = next(iter(self.features_cache))
                del self.features_cache[oldest_key]
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo features: {e}")
            return self._get_default_features()
    
    def _calculate_entropy_features(self, all_numbers: np.ndarray, combinations: List[List[int]]) -> Dict[str, float]:
        """Calcula features de entropía"""
        
        # Entropía de Shannon
        unique, counts = np.unique(all_numbers, return_counts=True)
        probabilities = counts / len(all_numbers)
        shannon_entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        shannon_entropy_norm = shannon_entropy / np.log2(40)  # Normalizar
        
        # Entropía relativa (KL divergence respecto a uniforme)
        uniform_prob = np.ones(40) / 40
        prob_dist = np.zeros(40)
        for num in range(1, 41):
            prob_dist[num-1] = np.sum(all_numbers == num) / len(all_numbers)
        
        relative_entropy = stats.entropy(prob_dist + 1e-10, uniform_prob + 1e-10)
        
        # Entropía condicional (entropía de posiciones)
        position_entropies = []
        for pos in range(6):
            pos_numbers = [combo[pos] for combo in combinations]
            pos_unique, pos_counts = np.unique(pos_numbers, return_counts=True)
            pos_probs = pos_counts / len(pos_numbers)
            pos_entropy = -np.sum(pos_probs * np.log2(pos_probs + 1e-10))
            position_entropies.append(pos_entropy)
        
        conditional_entropy = np.mean(position_entropies) / np.log2(40)
        
        return {
            'shannon': shannon_entropy_norm,
            'relative': relative_entropy,
            'conditional': conditional_entropy
        }
    
    def _calculate_frequency_features(self, all_numbers: np.ndarray) -> Dict[str, float]:
        """Calcula features de frecuencia"""
        
        # Frecuencias de cada número
        frequencies = np.zeros(40)
        for num in range(1, 41):
            frequencies[num-1] = np.sum(all_numbers == num)
        
        # Estadísticas de frecuencias
        freq_variance = np.var(frequencies) / np.mean(frequencies) if np.mean(frequencies) > 0 else 0
        freq_skewness = stats.skew(frequencies)
        freq_kurtosis = stats.kurtosis(frequencies)
        
        return {
            'variance': freq_variance,
            'skewness': freq_skewness,
            'kurtosis': freq_kurtosis
        }
    
    def _calculate_fft_features(self, sums: np.ndarray) -> Dict[str, float]:
        """Calcula features de FFT para análisis espectral"""
        
        if len(sums) < 8:
            return {'dominant': 0.0, 'density': 0.0, 'harmonic': 0.0}
        
        try:
            # FFT de las sumas
            fft_values = fft(sums)
            freqs = fftfreq(len(sums))
            
            # Magnitudes (excluyendo DC)
            magnitudes = np.abs(fft_values[1:len(fft_values)//2])
            
            if len(magnitudes) == 0:
                return {'dominant': 0.0, 'density': 0.0, 'harmonic': 0.0}
            
            # Frecuencia dominante
            dominant_idx = np.argmax(magnitudes)
            dominant_frequency = abs(freqs[dominant_idx + 1])
            
            # Densidad espectral
            spectral_density = np.sum(magnitudes ** 2) / len(magnitudes)
            
            # Ratio armónico (energía en múltiplos de frecuencia fundamental)
            harmonic_ratio = 0.0
            if dominant_frequency > 0:
                fundamental_energy = magnitudes[dominant_idx] ** 2
                total_energy = np.sum(magnitudes ** 2)
                harmonic_ratio = fundamental_energy / total_energy if total_energy > 0 else 0
            
            return {
                'dominant': dominant_frequency,
                'density': spectral_density,
                'harmonic': harmonic_ratio
            }
            
        except Exception as e:
            logger.debug(f"Error en FFT: {e}")
            return {'dominant': 0.0, 'density': 0.0, 'harmonic': 0.0}
    
    def _calculate_temporal_features(self, sums: np.ndarray, ranges: np.ndarray) -> Dict[str, float]:
        """Calcula features temporales"""
        
        if len(sums) < 3:
            return {'trend': 0.0, 'seasonality': 0.0, 'volatility': 0.0}
        
        # Fuerza de tendencia
        x = np.arange(len(sums))
        slope, _, r_value, _, _ = stats.linregress(x, sums)
        trend_strength = abs(r_value)  # Correlación absoluta
        
        # Score de estacionalidad (autocorrelación)
        if len(sums) >= 7:
            autocorr = np.corrcoef(sums[:-1], sums[1:])[0, 1]
            seasonality_score = abs(autocorr) if not np.isnan(autocorr) else 0.0
        else:
            seasonality_score = 0.0
        
        # Índice de volatilidad
        volatility_index = np.std(sums) / np.mean(sums) if np.mean(sums) > 0 else 0
        
        return {
            'trend': trend_strength,
            'seasonality': seasonality_score,
            'volatility': volatility_index
        }
    
    def _calculate_distribution_features(self, combinations: List[List[int]], ranges: np.ndarray) -> Dict[str, float]:
        """Calcula features de distribución"""
        
        # Ratio de rangos
        range_ratio = np.std(ranges) / np.mean(ranges) if np.mean(ranges) > 0 else 0
        
        # Análisis de gaps (espacios entre números)
        all_gaps = []
        for combo in combinations:
            sorted_combo = sorted(combo)
            gaps = [sorted_combo[i+1] - sorted_combo[i] for i in range(5)]
            all_gaps.extend(gaps)
        
        gap_analysis = np.std(all_gaps) / np.mean(all_gaps) if all_gaps and np.mean(all_gaps) > 0 else 0
        
        # Coeficiente de clustering (números que aparecen juntos)
        clustering_score = 0.0
        if len(combinations) >= 5:
            adjacency_count = 0
            total_pairs = 0
            
            for combo in combinations:
                sorted_combo = sorted(combo)
                for i in range(len(sorted_combo) - 1):
                    total_pairs += 1
                    if sorted_combo[i+1] - sorted_combo[i] <= 3:  # Números "cercanos"
                        adjacency_count += 1
            
            clustering_score = adjacency_count / total_pairs if total_pairs > 0 else 0
        
        return {
            'range_ratio': range_ratio,
            'gap_analysis': gap_analysis,
            'clustering': clustering_score
        }
    
    def _calculate_sequence_features(self, combinations: List[List[int]]) -> Dict[str, float]:
        """Calcula features de secuencias"""
        
        # Entropía de secuencias (patrones en el orden)
        sequence_patterns = []
        for combo in combinations:
            # Patrón de incrementos
            increments = tuple(combo[i+1] - combo[i] for i in range(5))
            sequence_patterns.append(increments)
        
        unique_patterns = set(sequence_patterns)
        pattern_counts = {pattern: sequence_patterns.count(pattern) for pattern in unique_patterns}
        
        if pattern_counts:
            pattern_probs = np.array(list(pattern_counts.values())) / len(sequence_patterns)
            sequence_entropy = -np.sum(pattern_probs * np.log2(pattern_probs + 1e-10))
            sequence_entropy_norm = sequence_entropy / np.log2(len(unique_patterns)) if len(unique_patterns) > 1 else 0
        else:
            sequence_entropy_norm = 0.0
        
        # Entropía de matriz de transición
        transition_matrix = np.zeros((40, 40))
        for combo in combinations:
            for i in range(len(combo) - 1):
                from_num = combo[i] - 1
                to_num = combo[i + 1] - 1
                transition_matrix[from_num][to_num] += 1
        
        # Normalizar matriz
        row_sums = transition_matrix.sum(axis=1)
        transition_matrix = np.divide(transition_matrix, row_sums[:, np.newaxis], 
                                    out=np.zeros_like(transition_matrix), where=row_sums[:, np.newaxis]!=0)
        
        # Calcular entropía de transición
        non_zero_probs = transition_matrix[transition_matrix > 0]
        if len(non_zero_probs) > 0:
            transition_entropy = -np.sum(non_zero_probs * np.log2(non_zero_probs))
            transition_entropy_norm = transition_entropy / np.log2(len(non_zero_probs))
        else:
            transition_entropy_norm = 0.0
        
        # Score de repetición
        all_numbers = [num for combo in combinations for num in combo]
        number_counts = {num: all_numbers.count(num) for num in set(all_numbers)}
        max_count = max(number_counts.values()) if number_counts else 1
        avg_count = np.mean(list(number_counts.values())) if number_counts else 1
        repetition_score = max_count / avg_count if avg_count > 0 else 1
        
        return {
            'entropy': sequence_entropy_norm,
            'transition': transition_entropy_norm,
            'repetition': repetition_score
        }
    
    def _get_default_features(self) -> ProfileFeatures:
        """Retorna features por defecto"""
        return ProfileFeatures(
            entropy_shannon=0.5, entropy_relative=0.5, entropy_conditional=0.5,
            frequency_variance=0.5, frequency_skewness=0.0, frequency_kurtosis=0.0,
            dominant_frequency=0.0, spectral_density=0.5, harmonic_ratio=0.5,
            trend_strength=0.0, seasonality_score=0.0, volatility_index=0.5,
            range_ratio=0.5, gap_analysis=0.5, clustering_coefficient=0.5,
            sequence_entropy=0.5, transition_matrix_entropy=0.5, repetition_score=1.0
        )
    
    def _get_cache_key(self, data: List[List[int]]) -> str:
        """Genera clave de cache para los datos"""
        data_str = str(sorted([tuple(sorted(combo)) for combo in data]))
        return str(hash(data_str))
    
    def train(self, historical_data: List[List[int]], labels: Optional[List[JackpotProfile]] = None) -> Dict[str, Any]:
        """Entrena el perfilador con datos históricos"""
        
        logger.info(f"🏋️ Entrenando perfilador con {len(historical_data)} muestras...")
        
        if len(historical_data) < self.min_samples * 3:
            logger.warning("⚠️ Pocos datos para entrenamiento efectivo")
        
        try:
            # Si no hay labels, generar automáticamente basado en features
            if labels is None:
                labels = self._auto_generate_labels(historical_data)
            
            # Extraer features de ventanas deslizantes
            X_features = []
            y_labels = []
            
            for i in range(self.window_size, len(historical_data)):
                window_data = historical_data[i - self.window_size:i]
                features = self.extract_features(window_data)
                feature_vector = self._features_to_vector(features)
                
                X_features.append(feature_vector)
                y_labels.append(labels[i])
            
            if len(X_features) < self.min_samples:
                raise ValueError(f"Insuficientes muestras después del windowing: {len(X_features)}")
            
            X = np.array(X_features)
            y = np.array([label.value for label in y_labels])
            
            # Normalizar features
            X_scaled = self.scaler.fit_transform(X)
            
            # Codificar labels
            y_encoded = self.label_encoder.fit_transform(y)
            
            # Entrenar cada modelo
            training_scores = {}
            
            for name, model in self.models.items():
                logger.info(f"   Entrenando {name}...")
                
                # Cross-validation
                cv_scores = cross_val_score(model, X_scaled, y_encoded, cv=3, scoring='accuracy')
                training_scores[name] = {
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std()
                }
                
                # Entrenar en todos los datos
                model.fit(X_scaled, y_encoded)
                
                logger.info(f"     CV Score: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
            
            self.is_trained = True
            self.feature_names = self._get_feature_names()
            
            # Guardar en historial
            training_record = {
                'timestamp': datetime.now(),
                'samples': len(X_features),
                'features': len(X[0]),
                'classes': len(np.unique(y_encoded)),
                'scores': training_scores
            }
            
            self.training_history.append(training_record)
            
            logger.info(f"✅ Entrenamiento completado: {len(X_features)} muestras, {len(np.unique(y_encoded))} clases")
            
            return {
                'samples_trained': len(X_features),
                'features_count': len(X[0]),
                'classes_count': len(np.unique(y_encoded)),
                'model_scores': training_scores,
                'feature_names': self.feature_names
            }
            
        except Exception as e:
            logger.error(f"❌ Error en entrenamiento: {e}")
            raise
    
    def _auto_generate_labels(self, historical_data: List[List[int]]) -> List[JackpotProfile]:
        """Genera labels automáticamente basado en análisis de features"""
        labels = []
        
        for i in range(len(historical_data)):
            if i < self.window_size:
                labels.append(JackpotProfile.PROFILE_UNKNOWN)
                continue
            
            window_data = historical_data[max(0, i - self.window_size):i]
            features = self.extract_features(window_data)
            
            # Clasificación basada en reglas
            if (features.entropy_shannon > 0.7 and 
                features.frequency_variance < 0.3 and 
                features.volatility_index < 0.3):
                profile = JackpotProfile.PROFILE_A
                
            elif (features.entropy_shannon < 0.4 and 
                  features.frequency_variance > 0.6 and 
                  features.volatility_index > 0.5):
                profile = JackpotProfile.PROFILE_C
                
            else:
                profile = JackpotProfile.PROFILE_B
            
            labels.append(profile)
        
        logger.info(f"📊 Labels generados automáticamente: "
                   f"A={labels.count(JackpotProfile.PROFILE_A)}, "
                   f"B={labels.count(JackpotProfile.PROFILE_B)}, "
                   f"C={labels.count(JackpotProfile.PROFILE_C)}")
        
        return labels
    
    def predict_profile(self, recent_data: List[List[int]]) -> ProfilePrediction:
        """Predice el perfil actual"""
        
        if not self.is_trained:
            logger.warning("⚠️ Modelo no entrenado, usando clasificación por reglas")
            return self._rule_based_prediction(recent_data)
        
        if len(recent_data) < self.min_samples:
            logger.warning(f"⚠️ Pocos datos para predicción ({len(recent_data)})")
            return self._rule_based_prediction(recent_data)
        
        try:
            # Usar últimos datos para predicción
            window_data = recent_data[-self.window_size:] if len(recent_data) >= self.window_size else recent_data
            
            # Extraer features
            features = self.extract_features(window_data)
            feature_vector = self._features_to_vector(features).reshape(1, -1)
            
            # Normalizar
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Predicciones de ensemble
            predictions = {}
            probabilities = {}
            
            for name, model in self.models.items():
                pred = model.predict(feature_vector_scaled)[0]
                pred_proba = model.predict_proba(feature_vector_scaled)[0]
                
                predictions[name] = self.label_encoder.inverse_transform([pred])[0]
                probabilities[name] = dict(zip(
                    [self.label_encoder.inverse_transform([i])[0] for i in range(len(pred_proba))],
                    pred_proba
                ))
            
            # Combinar predicciones (voting)
            profile_votes = {}
            for pred in predictions.values():
                profile_votes[pred] = profile_votes.get(pred, 0) + 1
            
            # Perfil más votado
            predicted_profile_str = max(profile_votes.items(), key=lambda x: x[1])[0]
            predicted_profile = JackpotProfile(predicted_profile_str)
            
            # Confianza promedio
            avg_probabilities = {}
            for profile_str in probabilities[list(self.models.keys())[0]].keys():
                avg_prob = np.mean([probs[profile_str] for probs in probabilities.values()])
                avg_probabilities[profile_str] = avg_prob
            
            confidence = avg_probabilities[predicted_profile_str]
            
            # Importancia de features (usando Random Forest)
            if hasattr(self.models['random_forest'], 'feature_importances_'):
                feature_importance = dict(zip(
                    self.feature_names,
                    self.models['random_forest'].feature_importances_
                ))
            else:
                feature_importance = {}
            
            prediction = ProfilePrediction(
                profile=predicted_profile,
                confidence=confidence,
                probability_distribution=avg_probabilities,
                features_importance=feature_importance,
                timestamp=datetime.now()
            )
            
            # Registrar transición si es diferente al anterior
            if (self.profile_transitions and 
                self.profile_transitions[-1][1] != predicted_profile):
                self.profile_transitions.append((datetime.now(), predicted_profile))
            elif not self.profile_transitions:
                self.profile_transitions.append((datetime.now(), predicted_profile))
            
            logger.info(f"🎯 Perfil predicho: {predicted_profile.value} (confianza: {confidence:.1%})")
            
            return prediction
            
        except Exception as e:
            logger.error(f"❌ Error en predicción: {e}")
            return self._rule_based_prediction(recent_data)
    
    def _rule_based_prediction(self, data: List[List[int]]) -> ProfilePrediction:
        """Predicción basada en reglas como fallback"""
        
        features = self.extract_features(data)
        
        # Clasificación simple por reglas
        if (features.entropy_shannon > 0.7 and 
            features.frequency_variance < 0.3):
            profile = JackpotProfile.PROFILE_A
            confidence = 0.6
            
        elif (features.entropy_shannon < 0.4 and 
              features.frequency_variance > 0.6):
            profile = JackpotProfile.PROFILE_C
            confidence = 0.6
            
        else:
            profile = JackpotProfile.PROFILE_B
            confidence = 0.5
        
        return ProfilePrediction(
            profile=profile,
            confidence=confidence,
            probability_distribution={
                profile.value: confidence,
                JackpotProfile.PROFILE_B.value: 1 - confidence
            },
            features_importance={},
            timestamp=datetime.now()
        )
    
    def _features_to_vector(self, features: ProfileFeatures) -> np.ndarray:
        """Convierte features a vector numérico"""
        return np.array([
            features.entropy_shannon,
            features.entropy_relative,
            features.entropy_conditional,
            features.frequency_variance,
            features.frequency_skewness,
            features.frequency_kurtosis,
            features.dominant_frequency,
            features.spectral_density,
            features.harmonic_ratio,
            features.trend_strength,
            features.seasonality_score,
            features.volatility_index,
            features.range_ratio,
            features.gap_analysis,
            features.clustering_coefficient,
            features.sequence_entropy,
            features.transition_matrix_entropy,
            features.repetition_score
        ])
    
    def _get_feature_names(self) -> List[str]:
        """Obtiene nombres de features"""
        return [
            'entropy_shannon', 'entropy_relative', 'entropy_conditional',
            'frequency_variance', 'frequency_skewness', 'frequency_kurtosis',
            'dominant_frequency', 'spectral_density', 'harmonic_ratio',
            'trend_strength', 'seasonality_score', 'volatility_index',
            'range_ratio', 'gap_analysis', 'clustering_coefficient',
            'sequence_entropy', 'transition_matrix_entropy', 'repetition_score'
        ]
    
    def get_profiling_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del perfilado"""
        
        summary = {
            'is_trained': self.is_trained,
            'window_size': self.window_size,
            'min_samples': self.min_samples,
            'models_count': len(self.models),
            'feature_count': len(self._get_feature_names()),
            'cache_size': len(self.features_cache)
        }
        
        if self.training_history:
            last_training = self.training_history[-1]
            summary['last_training'] = {
                'timestamp': last_training['timestamp'].isoformat(),
                'samples': last_training['samples'],
                'classes': last_training['classes'],
                'best_score': max([scores['cv_mean'] for scores in last_training['scores'].values()])
            }
        
        if self.profile_transitions:
            summary['recent_transitions'] = [
                {
                    'timestamp': ts.isoformat(),
                    'profile': profile.value
                }
                for ts, profile in self.profile_transitions[-5:]
            ]
        
        return summary

# Funciones de utilidad
def create_dynamic_profiler(window_size: int = 50) -> DynamicProfiler:
    """Crea un perfilador dinámico"""
    return DynamicProfiler(window_size=window_size)

def train_and_predict(profiler: DynamicProfiler, 
                     historical_data: List[List[int]],
                     recent_data: List[List[int]] = None) -> Tuple[Dict[str, Any], ProfilePrediction]:
    """Entrena y predice en un solo paso"""
    
    # Dividir datos para entrenamiento
    train_data = historical_data[:-10] if len(historical_data) > 20 else historical_data
    test_data = recent_data if recent_data else historical_data[-10:]
    
    # Entrenar
    training_results = profiler.train(train_data)
    
    # Predecir
    prediction = profiler.predict_profile(test_data)
    
    return training_results, prediction

if __name__ == "__main__":
    # Demo del perfilador dinámico
    print("🎯 Demo Perfilador Dinámico")
    
    # Crear perfilador
    profiler = create_dynamic_profiler()
    
    # Datos de ejemplo con diferentes patrones
    stable_pattern = [
        [1, 15, 23, 31, 35, 40], [2, 16, 24, 32, 36, 40],
        [3, 17, 25, 33, 37, 40], [4, 18, 26, 34, 38, 40]
    ] * 15  # Patrón estable
    
    chaotic_pattern = []
    np.random.seed(42)
    for _ in range(30):
        combo = sorted(np.random.choice(range(1, 41), 6, replace=False))
        chaotic_pattern.append(combo)
    
    mixed_data = stable_pattern + chaotic_pattern
    
    print(f"📊 Entrenando con {len(mixed_data)} combinaciones...")
    
    try:
        # Entrenar y predecir
        training_results, prediction = train_and_predict(profiler, mixed_data)
        
        print(f"✅ Entrenamiento completado:")
        print(f"   Muestras: {training_results['samples_trained']}")
        print(f"   Features: {training_results['features_count']}")
        print(f"   Clases: {training_results['classes_count']}")
        
        print(f"\n🎯 Predicción de perfil:")
        print(f"   Perfil: {prediction.profile.value}")
        print(f"   Confianza: {prediction.confidence:.1%}")
        print(f"   Distribución:")
        for profile, prob in prediction.probability_distribution.items():
            print(f"     {profile}: {prob:.1%}")
        
        # Resumen
        summary = profiler.get_profiling_summary()
        print(f"\n📈 Resumen del sistema:")
        print(f"   Entrenado: {summary['is_trained']}")
        print(f"   Modelos: {summary['models_count']}")
        print(f"   Features: {summary['feature_count']}")
        
    except Exception as e:
        print(f"❌ Error en demo: {e}")
        
        # Test de features básico
        features = profiler.extract_features(mixed_data[-20:])
        print(f"🔍 Features extraídas:")
        print(f"   Entropía Shannon: {features.entropy_shannon:.3f}")
        print(f"   Varianza de frecuencia: {features.frequency_variance:.3f}")
        print(f"   Índice de volatilidad: {features.volatility_index:.3f}")
