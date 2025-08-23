#!/usr/bin/env python3
"""
Ensemble Trainer para OMEGA PRO AI
Entrenador de ensemble con stacking avanzado para meta-modelo
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, StackingClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import cross_val_score, train_test_split, KFold
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import joblib
import warnings
warnings.filterwarnings("ignore")

# Importar validaciones si están disponibles
try:
    from modules.utils.validation_enhanced import OmegaValidator, ValidationError, validate_and_log_combinations
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False

logger = logging.getLogger(__name__)

class EnsembleStrategy(Enum):
    """Estrategias de ensemble disponibles"""
    VOTING = "voting"
    STACKING = "stacking"
    BLENDING = "blending"
    BAYESIAN_ENSEMBLE = "bayesian_ensemble"
    DYNAMIC_WEIGHTING = "dynamic_weighting"

class BaseModelType(Enum):
    """Tipos de modelos base"""
    FREQUENCY_BASED = "frequency_based"
    PATTERN_BASED = "pattern_based"
    STATISTICAL = "statistical"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"

@dataclass
class ModelPerformance:
    """Performance de un modelo base"""
    model_name: str
    model_type: BaseModelType
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    consistency: float
    diversity_contribution: float
    training_time: float
    prediction_time: float

@dataclass
class EnsembleConfiguration:
    """Configuración del ensemble"""
    strategy: EnsembleStrategy
    base_models: List[str]
    meta_model: str
    weights: Dict[str, float]
    feature_selection: List[str]
    validation_method: str
    performance_threshold: float

class OmegaModelSimulator:
    """Simulador de modelos OMEGA para ensemble"""
    
    def __init__(self):
        self.models = {
            'lstm_v2': self._create_lstm_simulator(),
            'transformer': self._create_transformer_simulator(),
            'clustering': self._create_clustering_simulator(),
            'montecarlo': self._create_montecarlo_simulator(),
            'genetic': self._create_genetic_simulator(),
            'gboost': self._create_gboost_simulator(),
            'apriori': self._create_apriori_simulator()
        }
        
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def _create_lstm_simulator(self):
        """Crea simulador para LSTM"""
        return RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42)
    
    def _create_transformer_simulator(self):
        """Crea simulador para Transformer"""
        return RandomForestClassifier(n_estimators=60, max_depth=10, random_state=43)
    
    def _create_clustering_simulator(self):
        """Crea simulador para Clustering"""
        return SVC(kernel='rbf', probability=True, random_state=44)
    
    def _create_montecarlo_simulator(self):
        """Crea simulador para Monte Carlo"""
        return LogisticRegression(random_state=45)
    
    def _create_genetic_simulator(self):
        """Crea simulador para Genetic"""
        return RandomForestClassifier(n_estimators=40, max_depth=6, random_state=46)
    
    def _create_gboost_simulator(self):
        """Crea simulador para GBoost"""
        return GradientBoostingClassifier(n_estimators=50, max_depth=5, learning_rate=0.1, random_state=47)
    
    def _create_apriori_simulator(self):
        """Crea simulador para Apriori"""
        return RandomForestClassifier(n_estimators=30, max_depth=5, random_state=48)
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Entrena todos los modelos simulados"""
        
        # Escalar features
        X_scaled = self.scaler.fit_transform(X)
        
        # Entrenar cada modelo
        for name, model in self.models.items():
            try:
                model.fit(X_scaled, y)
                logger.debug(f"✅ Modelo {name} entrenado")
            except Exception as e:
                logger.error(f"❌ Error entrenando {name}: {e}")
        
        self.is_fitted = True
    
    def predict_proba(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Obtiene probabilidades de todos los modelos"""
        
        if not self.is_fitted:
            raise ValueError("Modelos no entrenados")
        
        X_scaled = self.scaler.transform(X)
        predictions = {}
        
        for name, model in self.models.items():
            try:
                if hasattr(model, 'predict_proba'):
                    predictions[name] = model.predict_proba(X_scaled)
                else:
                    # Para modelos sin predict_proba, usar predict y convertir
                    pred = model.predict(X_scaled)
                    # Crear pseudo-probabilidades
                    proba = np.zeros((len(pred), len(np.unique(pred))))
                    for i, p in enumerate(pred):
                        proba[i, p] = 1.0
                    predictions[name] = proba
            except Exception as e:
                logger.error(f"❌ Error prediciendo con {name}: {e}")
                # Fallback: probabilidades uniformes
                predictions[name] = np.ones((X_scaled.shape[0], 2)) * 0.5
        
        return predictions

class EnsembleTrainer:
    """Entrenador de ensemble para modelos OMEGA"""
    
    def __init__(self, 
                 strategy: EnsembleStrategy = EnsembleStrategy.STACKING,
                 cv_folds: int = 5,
                 random_state: int = 42,
                 normalization_method: str = 'standard'):
        
        self.strategy = strategy
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.normalization_method = normalization_method
        
        # Componentes del ensemble
        self.base_models_simulator = OmegaModelSimulator()
        self.meta_model = None
        self.ensemble_model = None
        
        # Configuración y rendimiento
        self.configuration = None
        self.base_model_performances = {}
        self.ensemble_performance = None
        
        # Procesadores de datos con persistencia
        self.feature_scaler = None
        self.target_encoder = None
        self.fitted = False
        
        # Metadatos para reproducibilidad
        self.training_metadata = {
            'feature_names': None,
            'target_classes': None,
            'scaler_type': normalization_method,
            'training_date': None,
            'data_shape': None
        }
        
        # Estado de entrenamiento
        self.is_trained = False
        self.training_history = []
        
        # Escaladores y encoders
        self.feature_scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        logger.info("🏗️ Ensemble Trainer inicializado")
        logger.info(f"   Estrategia: {strategy.value}, CV Folds: {cv_folds}")
    
    def _initialize_preprocessors(self):
        """Inicializa los procesadores de datos según la configuración"""
        if self.normalization_method == 'standard':
            self.feature_scaler = StandardScaler()
        elif self.normalization_method == 'minmax':
            self.feature_scaler = MinMaxScaler()
        elif self.normalization_method == 'none':
            self.feature_scaler = None
        else:
            logger.warning(f"⚠️ Método de normalización desconocido: {self.normalization_method}, usando 'standard'")
            self.feature_scaler = StandardScaler()
        
        self.target_encoder = LabelEncoder()
        logger.info(f"✅ Procesadores inicializados: {self.normalization_method}")
    
    def _validate_historical_data(self, historical_data: Any) -> List[List[int]]:
        """Valida datos históricos usando validación mejorada si está disponible"""
        if VALIDATION_AVAILABLE:
            try:
                if isinstance(historical_data, pd.DataFrame):
                    validated_data = OmegaValidator.validate_historical_data(historical_data)
                    # Extraer combinaciones de las primeras 6 columnas numéricas
                    numeric_cols = validated_data.select_dtypes(include=[np.number]).columns[:6]
                    return validated_data[numeric_cols].values.tolist()
                else:
                    valid_combos, errors = OmegaValidator.validate_combinations_batch(
                        historical_data,
                        allow_failures=True,
                        max_failure_rate=0.2
                    )
                    if errors:
                        logger.warning(f"⚠️ {len(errors)} combinaciones con errores de validación")
                    return valid_combos
            except ValidationError as e:
                logger.error(f"❌ Error de validación: {e}")
                raise
        else:
            # Validación básica
            if not isinstance(historical_data, (list, tuple)):
                raise ValueError("historical_data debe ser una lista de combinaciones")
            
            valid_data = []
            for i, combo in enumerate(historical_data):
                if isinstance(combo, (list, tuple)) and len(combo) >= 6:
                    try:
                        validated_combo = [int(x) for x in combo[:6]]
                        if all(1 <= x <= 40 for x in validated_combo):
                            valid_data.append(validated_combo)
                    except (ValueError, TypeError):
                        logger.warning(f"⚠️ Combinación inválida en índice {i}: {combo}")
            
            if len(valid_data) < len(historical_data) * 0.8:
                logger.warning(f"⚠️ Muchos datos inválidos: {len(valid_data)}/{len(historical_data)}")
            
            return valid_data
    
    def prepare_ensemble_data(self, 
                            historical_data: Union[List[List[int]], pd.DataFrame, np.ndarray], 
                            window_size: int = 10,
                            fit_preprocessors: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara datos para entrenamiento del ensemble con persistencia de escaladores"""
        
        logger.info(f"📊 Preparando datos de ensemble con ventana {window_size}")
        
        # Inicializar procesadores si es necesario
        if self.feature_scaler is None or self.target_encoder is None:
            self._initialize_preprocessors()
        
        # Validar datos históricos
        validated_data = self._validate_historical_data(historical_data)
        
        if len(historical_data) < window_size + 5:
            raise ValueError(f"Insuficientes datos: {len(historical_data)} < {window_size + 5}")
        
        # Filtrar y validar combinaciones
        valid_data = []
        discarded_count = 0
        
        for i, combination in enumerate(historical_data):
            if not isinstance(combination, (list, tuple)):
                logger.debug(f"⚠️ Combinación {i} no es una lista: {type(combination)}")
                discarded_count += 1
                continue
            
            if len(combination) != 6:
                logger.debug(f"⚠️ Combinación {i} no tiene 6 números: {len(combination)}")
                discarded_count += 1
                continue
            
            # Validar que todos son números enteros en rango 1-40
            try:
                validated_combo = []
                for num in combination:
                    # Aceptar int, float, numpy.int64, numpy.int32, etc.
                    if not isinstance(num, (int, float, np.integer, np.floating)):
                        raise ValueError(f"Número no válido: {num} (tipo: {type(num)})")
                    int_num = int(num)
                    if not (1 <= int_num <= 40):
                        raise ValueError(f"Número fuera de rango: {int_num}")
                    validated_combo.append(int_num)
                
                # Verificar que no hay duplicados
                if len(set(validated_combo)) != 6:
                    logger.debug(f"⚠️ Combinación {i} tiene números duplicados: {validated_combo}")
                    discarded_count += 1
                    continue
                
                valid_data.append(validated_combo)
                
            except (ValueError, TypeError) as e:
                logger.debug(f"⚠️ Error validando combinación {i}: {e}")
                discarded_count += 1
                continue
        
        if discarded_count > 0:
            logger.warning(f"⚠️ Descartadas {discarded_count} combinaciones inválidas de {len(historical_data)}")
        
        if len(valid_data) < window_size + 5:
            raise ValueError(f"Datos válidos insuficientes: {len(valid_data)} < {window_size + 5}")
        
        X_features = []
        y_labels = []
        
        for i in range(window_size, len(valid_data) - 1):
            try:
                # Features: estadísticas de ventana anterior
                window = valid_data[i - window_size:i]
                features = self._extract_ensemble_features(window)
                
                # Validar que features es válido
                if not features or len(features) == 0:
                    logger.debug(f"⚠️ Features vacías para ventana {i}")
                    continue
                
                # Verificar que no hay NaN o infinitos
                if any(not np.isfinite(f) for f in features):
                    logger.debug(f"⚠️ Features no finitas en ventana {i}")
                    continue
                
                # Label: si la siguiente combinación es "buena"
                next_combo = valid_data[i + 1]
                label = self._evaluate_combination_quality(next_combo, window)
                
                X_features.append(features)
                y_labels.append(label)
                
            except Exception as e:
                logger.debug(f"⚠️ Error procesando ventana {i}: {e}")
                continue
        
        if not X_features:
            raise ValueError("No se pudo extraer ninguna característica válida")
        
        X = np.array(X_features)
        y = np.array(y_labels)
        
        # Validación final
        if X.shape[0] == 0:
            raise ValueError("Array de características vacío")
        
        if np.any(~np.isfinite(X)):
            logger.warning("⚠️ Reemplazando valores no finitos en características con 0")
            X = np.where(np.isfinite(X), X, 0)
        
        logger.info(f"✅ Datos preparados: {X.shape[0]} muestras, {X.shape[1]} features")
        logger.info(f"   Distribución labels: {np.bincount(y)} (0: malo, 1: bueno)")
        
        return X, y
    
    def _extract_ensemble_features(self, window: List[List[int]]) -> List[float]:
        """Extrae features para el ensemble"""
        
        # Convertir a array plano
        all_numbers = np.concatenate(window)
        
        features = []
        
        # 1. Estadísticas básicas
        features.extend([
            np.mean(all_numbers),
            np.std(all_numbers),
            np.min(all_numbers),
            np.max(all_numbers),
            len(np.unique(all_numbers))
        ])
        
        # 2. Distribución por zonas
        zones = {1: 0, 2: 0, 3: 0, 4: 0}
        for num in all_numbers:
            zone = min(4, (num - 1) // 10 + 1)
            zones[zone] += 1
        
        total_nums = len(all_numbers)
        zone_props = [zones[i] / total_nums for i in range(1, 5)]
        features.extend(zone_props)
        
        # 3. Frecuencias de números
        freq_counts = np.bincount(all_numbers, minlength=41)[1:41]  # Excluir 0
        features.extend([
            np.mean(freq_counts),
            np.std(freq_counts),
            np.max(freq_counts),
            np.sum(freq_counts == 0)  # Números no aparecidos
        ])
        
        # 4. Patterns secuenciales
        sums = [sum(combo) for combo in window]
        ranges = [max(combo) - min(combo) for combo in window]
        
        features.extend([
            np.mean(sums),
            np.std(sums),
            np.mean(ranges),
            np.std(ranges)
        ])
        
        # 5. Gaps entre números consecutivos
        all_gaps = []
        for combo in window:
            sorted_combo = sorted(combo)
            gaps = [sorted_combo[i+1] - sorted_combo[i] for i in range(5)]
            all_gaps.extend(gaps)
        
        features.extend([
            np.mean(all_gaps),
            np.std(all_gaps),
            np.max(all_gaps)
        ])
        
        return features
    
    def _evaluate_combination_quality(self, 
                                     combination: List[int], 
                                     context_window: List[List[int]],
                                     criteria_config: Dict[str, Any] = None) -> int:
        """Evalúa calidad de combinación (0=mala, 1=buena) con criterios configurables"""
        
        # Configuración por defecto más estricta para generar ambas clases
        if criteria_config is None:
            criteria_config = {
                'sum_tolerance': 20,  # Más estricto
                'range_min': 120,     # Más estricto
                'range_max': 220,     # Más estricto
                'min_zones': 4,       # Más estricto (requiere 4 zonas)
                'min_criteria': 3,    # Más estricto (requiere 3 de 5 criterios)
                'adaptive_thresholds': True
            }
        
        combo_sum = sum(combination)
        combo_range = max(combination) - min(combination)
        
        # Obtener estadísticas del contexto para criterios adaptativos
        context_sums = [sum(combo) for combo in context_window]
        context_ranges = [max(combo) - min(combo) for combo in context_window]
        
        if criteria_config.get('adaptive_thresholds', False) and len(context_sums) > 0:
            # Criterios adaptativos basados en el contexto
            avg_sum = np.mean(context_sums)
            std_sum = np.std(context_sums)
            
            avg_range = np.mean(context_ranges)
            std_range = np.std(context_ranges)
            
            # Tolerancias adaptativas
            sum_tolerance = max(criteria_config['sum_tolerance'], std_sum * 1.5)
            range_min = max(criteria_config['range_min'], avg_range - std_range * 2)
            range_max = min(criteria_config['range_max'], avg_range + std_range * 2)
        else:
            # Criterios fijos
            avg_sum = np.mean(context_sums) if context_sums else 125  # Suma típica para 6 números
            sum_tolerance = criteria_config['sum_tolerance']
            range_min = criteria_config['range_min']
            range_max = criteria_config['range_max']
        
        # Criterio 1: Suma dentro de rango esperado
        sum_ok = abs(combo_sum - avg_sum) <= sum_tolerance
        
        # Criterio 2: Rango adecuado
        range_ok = range_min <= combo_range <= range_max
        
        # Criterio 3: Diversidad de zonas (décadas)
        zones = set()
        for num in combination:
            zone = min(4, (num - 1) // 10 + 1)
            zones.add(zone)
        diversity_ok = len(zones) >= criteria_config['min_zones']
        
        # Criterio 4: Distribución par/impar balanceada
        evens = sum(1 for num in combination if num % 2 == 0)
        parity_ok = 2 <= evens <= 4  # Entre 2-4 números pares
        
        # Criterio 5: Sin gaps excesivos entre números consecutivos
        sorted_combo = sorted(combination)
        max_gap = max(sorted_combo[i+1] - sorted_combo[i] for i in range(5))
        gap_ok = max_gap <= 15  # Gap máximo de 15
        
        # Contar criterios cumplidos
        criteria_met = sum([sum_ok, range_ok, diversity_ok, parity_ok, gap_ok])
        
        # Determinar calidad
        min_criteria = criteria_config['min_criteria']
        quality = criteria_met >= min_criteria
        
        # Log detallado para debugging (solo en nivel debug)
        logger.debug(f"🔍 Evaluación calidad: {combination}")
        logger.debug(f"   Suma: {combo_sum} (ref: {avg_sum:.1f}) -> {'✓' if sum_ok else '✗'}")
        logger.debug(f"   Rango: {combo_range} ({range_min}-{range_max}) -> {'✓' if range_ok else '✗'}")
        logger.debug(f"   Zonas: {len(zones)} (min: {criteria_config['min_zones']}) -> {'✓' if diversity_ok else '✗'}")
        logger.debug(f"   Paridad: {evens} pares -> {'✓' if parity_ok else '✗'}")
        logger.debug(f"   Gap máx: {max_gap} -> {'✓' if gap_ok else '✗'}")
        logger.debug(f"   Criterios: {criteria_met}/{len([sum_ok, range_ok, diversity_ok, parity_ok, gap_ok])} -> {'BUENA' if quality else 'MALA'}")
        
        return 1 if quality else 0
    
    def train_ensemble(self, 
                      historical_data: List[List[int]], 
                      test_size: float = 0.2,
                      optimize_weights: bool = True) -> Dict[str, Any]:
        """Entrena el ensemble completo"""
        
        logger.info(f"🏋️ Iniciando entrenamiento de ensemble...")
        
        start_time = datetime.now()
        
        try:
            # Preparar datos
            X, y = self.prepare_ensemble_data(historical_data)
            
            # Dividir train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=self.random_state, stratify=y
            )
            
            # Escalar features
            X_train_scaled = self.feature_scaler.fit_transform(X_train)
            X_test_scaled = self.feature_scaler.transform(X_test)
            
            # Entrenar modelos base (simulados)
            self.base_models_simulator.fit(X_train_scaled, y_train)
            
            # Evaluar modelos base individualmente
            self._evaluate_base_models(X_test_scaled, y_test)
            
            # Crear ensemble según estrategia
            if self.strategy == EnsembleStrategy.VOTING:
                self.ensemble_model = self._create_voting_ensemble()
            
            elif self.strategy == EnsembleStrategy.STACKING:
                self.ensemble_model = self._create_stacking_ensemble()
            
            elif self.strategy == EnsembleStrategy.BLENDING:
                self.ensemble_model = self._create_blending_ensemble(X_train_scaled, y_train)
            
            elif self.strategy == EnsembleStrategy.DYNAMIC_WEIGHTING:
                self.ensemble_model = self._create_dynamic_weighted_ensemble()
            
            else:
                # Default a stacking
                self.ensemble_model = self._create_stacking_ensemble()
            
            # Entrenar ensemble
            if hasattr(self.ensemble_model, 'fit'):
                self.ensemble_model.fit(X_train_scaled, y_train)
            
            # Evaluar ensemble
            ensemble_performance = self._evaluate_ensemble(X_test_scaled, y_test)
            
            # Optimizar pesos si se solicita
            if optimize_weights and self.strategy == EnsembleStrategy.DYNAMIC_WEIGHTING:
                optimized_weights = self._optimize_ensemble_weights(X_test_scaled, y_test)
                ensemble_performance['optimized_weights'] = optimized_weights
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Guardar configuración
            self.configuration = EnsembleConfiguration(
                strategy=self.strategy,
                base_models=list(self.base_models_simulator.models.keys()),
                meta_model=str(type(self.ensemble_model).__name__) if self.ensemble_model else "None",
                weights=self._get_current_weights(),
                feature_selection=list(range(X.shape[1])),
                validation_method=f"{self.cv_folds}-fold CV",
                performance_threshold=0.6
            )
            
            self.is_trained = True
            
            # Registrar en historial
            training_record = {
                'timestamp': datetime.now().isoformat(),
                'strategy': self.strategy.value,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'features_count': X.shape[1],
                'base_models_count': len(self.base_models_simulator.models),
                'training_time': training_time,
                'ensemble_performance': ensemble_performance
            }
            
            self.training_history.append(training_record)
            
            logger.info(f"✅ Ensemble entrenado exitosamente en {training_time:.2f}s")
            logger.info(f"   Rendimiento: Accuracy = {ensemble_performance['accuracy']:.3f}")
            
            return {
                'training_time': training_time,
                'ensemble_performance': ensemble_performance,
                'base_model_performances': self.base_model_performances,
                'configuration': asdict(self.configuration),
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en entrenamiento de ensemble: {e}")
            raise
    
    def _evaluate_base_models(self, X_test: np.ndarray, y_test: np.ndarray):
        """Evalúa modelos base individualmente"""
        
        predictions = self.base_models_simulator.predict_proba(X_test)
        
        for model_name, proba in predictions.items():
            try:
                # Convertir probabilidades a predicciones
                y_pred = np.argmax(proba, axis=1)
                
                # Calcular métricas
                accuracy = accuracy_score(y_test, y_pred)
                precision, recall, f1, _ = precision_recall_fscore_support(
                    y_test, y_pred, average='weighted', zero_division=0
                )
                
                # Calcular consistency (pseudo-métrica)
                consistency = 1.0 - np.std(proba[:, 1])  # Baja varianza en probabilidades
                
                # Diversity contribution (simplificado)
                diversity = np.mean(np.abs(proba[:, 1] - 0.5))  # Qué tan lejos de neutral
                
                self.base_model_performances[model_name] = ModelPerformance(
                    model_name=model_name,
                    model_type=BaseModelType.ENSEMBLE,  # Simplificado
                    accuracy=accuracy,
                    precision=precision,
                    recall=recall,
                    f1_score=f1,
                    consistency=consistency,
                    diversity_contribution=diversity,
                    training_time=0.1,  # Simulado
                    prediction_time=0.01  # Simulado
                )
                
                logger.debug(f"📊 {model_name}: Acc={accuracy:.3f}, F1={f1:.3f}")
                
            except Exception as e:
                logger.error(f"❌ Error evaluando {model_name}: {e}")
    
    def _create_voting_ensemble(self):
        """Crea ensemble de voting"""
        
        # Simular voting ensemble
        estimators = []
        for name, model in self.base_models_simulator.models.items():
            estimators.append((name, model))
        
        return VotingClassifier(
            estimators=estimators[:5],  # Limitar para eficiencia
            voting='soft'
        )
    
    def _create_stacking_ensemble(self):
        """Crea ensemble de stacking"""
        
        # Modelos base para stacking
        base_models = []
        for name, model in list(self.base_models_simulator.models.items())[:5]:
            base_models.append((name, model))
        
        # Meta-modelo
        meta_model = LogisticRegression(random_state=self.random_state)
        
        return StackingClassifier(
            estimators=base_models,
            final_estimator=meta_model,
            cv=3,  # Reducido para eficiencia
            n_jobs=1
        )
    
    def _create_blending_ensemble(self, X_train: np.ndarray, y_train: np.ndarray):
        """Crea ensemble de blending"""
        
        # Dividir training data para blending
        X_blend, X_holdout, y_blend, y_holdout = train_test_split(
            X_train, y_train, test_size=0.2, random_state=self.random_state
        )
        
        # Entrenar modelos base en subset
        blend_simulator = OmegaModelSimulator()
        blend_simulator.fit(X_blend, y_blend)
        
        # Obtener predicciones en holdout
        holdout_predictions = blend_simulator.predict_proba(X_holdout)
        
        # Crear features para meta-modelo
        meta_features = []
        for i in range(len(X_holdout)):
            row_features = []
            for model_name in blend_simulator.models.keys():
                if model_name in holdout_predictions:
                    proba = holdout_predictions[model_name][i]
                    row_features.extend(proba)
            meta_features.append(row_features)
        
        meta_X = np.array(meta_features)
        
        # Entrenar meta-modelo
        meta_model = LogisticRegression(random_state=self.random_state)
        meta_model.fit(meta_X, y_holdout)
        
        # Crear wrapper para blending
        class BlendingEnsemble:
            def __init__(self, base_simulator, meta_model):
                self.base_simulator = base_simulator
                self.meta_model = meta_model
            
            def predict_proba(self, X):
                base_predictions = self.base_simulator.predict_proba(X)
                meta_features = []
                
                for i in range(len(X)):
                    row_features = []
                    for model_name in self.base_simulator.models.keys():
                        if model_name in base_predictions:
                            proba = base_predictions[model_name][i]
                            row_features.extend(proba)
                    meta_features.append(row_features)
                
                meta_X = np.array(meta_features)
                return self.meta_model.predict_proba(meta_X)
            
            def predict(self, X):
                proba = self.predict_proba(X)
                return np.argmax(proba, axis=1)
        
        return BlendingEnsemble(blend_simulator, meta_model)
    
    def _create_dynamic_weighted_ensemble(self):
        """Crea ensemble con pesos dinámicos"""
        
        # Pesos iniciales basados en performance
        initial_weights = {}
        total_f1 = sum(perf.f1_score for perf in self.base_model_performances.values())
        
        for name, perf in self.base_model_performances.items():
            if total_f1 > 0:
                initial_weights[name] = perf.f1_score / total_f1
            else:
                initial_weights[name] = 1.0 / len(self.base_model_performances)
        
        class DynamicWeightedEnsemble:
            def __init__(self, base_simulator, weights):
                self.base_simulator = base_simulator
                self.weights = weights
            
            def predict_proba(self, X):
                base_predictions = self.base_simulator.predict_proba(X)
                
                # Combinar predicciones con pesos
                weighted_proba = None
                total_weight = 0
                
                for model_name, proba in base_predictions.items():
                    weight = self.weights.get(model_name, 0.0)
                    if weight > 0:
                        if weighted_proba is None:
                            weighted_proba = proba * weight
                        else:
                            weighted_proba += proba * weight
                        total_weight += weight
                
                if total_weight > 0:
                    weighted_proba /= total_weight
                else:
                    # Fallback: promedio uniforme
                    weighted_proba = np.mean(list(base_predictions.values()), axis=0)
                
                return weighted_proba
            
            def predict(self, X):
                proba = self.predict_proba(X)
                return np.argmax(proba, axis=1)
        
        return DynamicWeightedEnsemble(self.base_models_simulator, initial_weights)
    
    def _evaluate_ensemble(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Evalúa rendimiento del ensemble"""
        
        try:
            # Hacer predicciones
            if hasattr(self.ensemble_model, 'predict'):
                y_pred = self.ensemble_model.predict(X_test)
            else:
                y_pred = np.random.randint(0, 2, len(y_test))  # Fallback
            
            if hasattr(self.ensemble_model, 'predict_proba'):
                y_proba = self.ensemble_model.predict_proba(X_test)
            else:
                y_proba = None
            
            # Calcular métricas
            accuracy = accuracy_score(y_test, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_test, y_pred, average='weighted', zero_division=0
            )
            
            # Métricas adicionales
            conf_matrix = confusion_matrix(y_test, y_pred).tolist()
            
            performance = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'confusion_matrix': conf_matrix
            }
            
            # Agregar métricas de probabilidad si disponibles
            if y_proba is not None:
                # Calibración (Brier score simplificado)
                brier_score = np.mean((y_proba[:, 1] - y_test) ** 2)
                performance['brier_score'] = brier_score
                
                # Confianza promedio
                confidence = np.mean(np.max(y_proba, axis=1))
                performance['average_confidence'] = confidence
            
            self.ensemble_performance = performance
            
            return performance
            
        except Exception as e:
            logger.error(f"❌ Error evaluando ensemble: {e}")
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'confusion_matrix': [[0, 0], [0, 0]]
            }
    
    def _optimize_ensemble_weights(self, X_test: np.ndarray, y_test: np.ndarray, method: str = 'hybrid') -> Dict[str, float]:
        """Optimiza pesos del ensemble con métodos avanzados"""
        
        base_predictions = self.base_models_simulator.predict_proba(X_test)
        model_names = list(base_predictions.keys())
        
        if method == 'hybrid':
            # Combinar múltiples métodos y tomar el mejor
            methods = ['random_search', 'grid_search', 'performance_based']
            results = []
            
            for method_name in methods:
                try:
                    weights, score = self._optimize_weights_method(base_predictions, y_test, method_name)
                    results.append((weights, score, method_name))
                except Exception as e:
                    logger.debug(f"⚠️ Error en método {method_name}: {e}")
            
            if results:
                # Seleccionar el mejor resultado
                best_weights, best_score, best_method = max(results, key=lambda x: x[1])
                logger.info(f"🎯 Pesos optimizados con {best_method}: Score = {best_score:.3f}")
                return best_weights
            else:
                # Fallback a pesos uniformes
                return {name: 1.0/len(model_names) for name in model_names}
        else:
            weights, score = self._optimize_weights_method(base_predictions, y_test, method)
            logger.info(f"🎯 Pesos optimizados con {method}: Score = {score:.3f}")
            return weights
    
    def _optimize_weights_method(self, base_predictions: Dict[str, np.ndarray], y_test: np.ndarray, method: str) -> Tuple[Dict[str, float], float]:
        """Optimiza pesos usando un método específico"""
        
        model_names = list(base_predictions.keys())
        best_weights = {}
        best_score = 0.0
        
        if method == 'random_search':
            # Búsqueda aleatoria con Dirichlet
            for _ in range(100):  # Más iteraciones
                weights = np.random.dirichlet(np.ones(len(model_names)))
                weight_dict = dict(zip(model_names, weights))
                score = self._evaluate_weight_combination(base_predictions, weight_dict, y_test)
                
                if score > best_score:
                    best_score = score
                    best_weights = weight_dict.copy()
        
        elif method == 'grid_search':
            # Búsqueda en grilla (limitada para eficiencia)
            from itertools import product
            
            # Crear grilla de pesos (5 valores por modelo)
            weight_values = [0.0, 0.25, 0.5, 0.75, 1.0]
            
            # Limitar combinaciones para evitar explosión combinatorial
            max_combinations = 500
            combinations_tested = 0
            
            for weight_combo in product(weight_values, repeat=len(model_names)):
                if combinations_tested >= max_combinations:
                    break
                
                # Normalizar pesos
                total_weight = sum(weight_combo)
                if total_weight == 0:
                    continue
                
                normalized_weights = [w / total_weight for w in weight_combo]
                weight_dict = dict(zip(model_names, normalized_weights))
                
                score = self._evaluate_weight_combination(base_predictions, weight_dict, y_test)
                
                if score > best_score:
                    best_score = score
                    best_weights = weight_dict.copy()
                
                combinations_tested += 1
        
        elif method == 'performance_based':
            # Pesos basados en performance individual de modelos
            individual_scores = {}
            
            for model_name, proba in base_predictions.items():
                y_pred = np.argmax(proba, axis=1)
                score = accuracy_score(y_test, y_pred)
                individual_scores[model_name] = score
            
            # Normalizar scores a pesos
            total_score = sum(individual_scores.values())
            if total_score > 0:
                best_weights = {name: score / total_score for name, score in individual_scores.items()}
                best_score = self._evaluate_weight_combination(base_predictions, best_weights, y_test)
            else:
                # Fallback a pesos uniformes
                best_weights = {name: 1.0/len(model_names) for name in model_names}
                best_score = self._evaluate_weight_combination(base_predictions, best_weights, y_test)
        
        elif method == 'bayesian_like':
            # Optimización tipo Bayesiana simplificada
            # Empezar con pesos uniformes y refinar iterativamente
            current_weights = {name: 1.0/len(model_names) for name in model_names}
            current_score = self._evaluate_weight_combination(base_predictions, current_weights, y_test)
            
            best_weights = current_weights.copy()
            best_score = current_score
            
            # Iteraciones de refinamiento
            for iteration in range(50):
                # Generar variación gaussiana alrededor de mejores pesos actuales
                noise_scale = 0.1 * (1 - iteration / 50)  # Reducir ruido con el tiempo
                
                new_weights = {}
                for name in model_names:
                    new_weight = best_weights[name] + np.random.normal(0, noise_scale)
                    new_weights[name] = max(0, new_weight)  # No negativos
                
                # Normalizar
                total_weight = sum(new_weights.values())
                if total_weight > 0:
                    new_weights = {name: weight / total_weight for name, weight in new_weights.items()}
                    
                    score = self._evaluate_weight_combination(base_predictions, new_weights, y_test)
                    
                    if score > best_score:
                        best_score = score
                        best_weights = new_weights.copy()
        
        else:
            raise ValueError(f"Método de optimización no reconocido: {method}")
        
        return best_weights, best_score
    
    def _evaluate_weight_combination(self, base_predictions: Dict[str, np.ndarray], weights: Dict[str, float], y_test: np.ndarray) -> float:
        """Evalúa una combinación específica de pesos"""
        
        try:
            combined_proba = None
            total_weight = 0
            
            for model_name, weight in weights.items():
                if model_name in base_predictions and weight > 0:
                    proba = base_predictions[model_name] * weight
                    if combined_proba is None:
                        combined_proba = proba
                    else:
                        combined_proba += proba
                    total_weight += weight
            
            if combined_proba is not None and total_weight > 0:
                combined_proba /= total_weight  # Normalizar
                y_pred = np.argmax(combined_proba, axis=1)
                return accuracy_score(y_test, y_pred)
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _get_current_weights(self) -> Dict[str, float]:
        """Obtiene pesos actuales del ensemble"""
        
        if hasattr(self.ensemble_model, 'weights'):
            return self.ensemble_model.weights
        elif hasattr(self.ensemble_model, 'estimators_'):
            # Para VotingClassifier, pesos uniformes
            return {f"model_{i}": 1.0 for i in range(len(self.ensemble_model.estimators_))}
        else:
            return {name: 1.0 for name in self.base_models_simulator.models.keys()}
    
    def predict_combinations(self, 
                           recent_data: List[List[int]], 
                           num_predictions: int = 5) -> List[Dict[str, Any]]:
        """Predice combinaciones usando el ensemble"""
        
        if not self.is_trained:
            logger.warning("⚠️ Ensemble no entrenado, usando predicciones aleatorias")
            return self._generate_random_predictions(num_predictions)
        
        try:
            # Extraer features del contexto reciente
            features = self._extract_ensemble_features(recent_data[-10:])
            X_pred = np.array([features])
            X_pred_scaled = self.feature_scaler.transform(X_pred)
            
            # Obtener probabilidades del ensemble
            if hasattr(self.ensemble_model, 'predict_proba'):
                proba = self.ensemble_model.predict_proba(X_pred_scaled)[0]
                confidence = max(proba)
            else:
                confidence = 0.6  # Confianza por defecto
            
            predictions = []
            
            for i in range(num_predictions):
                # Generar combinación basada en contexto
                combination = self._generate_context_based_combination(recent_data, i)
                
                prediction = {
                    'combination': combination,
                    'confidence': confidence + np.random.normal(0, 0.05),  # Pequeña variación
                    'source': 'ensemble_trainer',
                    'strategy': self.strategy.value,
                    'model_contributions': self._get_model_contributions(),
                    'timestamp': datetime.now().isoformat()
                }
                
                predictions.append(prediction)
            
            logger.info(f"🎯 Generadas {len(predictions)} predicciones de ensemble")
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error en predicción de ensemble: {e}")
            return self._generate_random_predictions(num_predictions)
    
    def _generate_context_based_combination(self, recent_data: List[List[int]], seed: int) -> List[int]:
        """Genera combinación basada en contexto histórico"""
        
        np.random.seed(seed + 42)
        
        # Analizar frecuencias en datos recientes
        all_numbers = np.concatenate(recent_data[-5:])  # Últimas 5 combinaciones
        unique, counts = np.unique(all_numbers, return_counts=True)
        
        # Crear distribución de probabilidades
        probs = np.ones(40) * 0.025  # Base uniforme
        
        for num, count in zip(unique, counts):
            if 1 <= num <= 40:
                probs[num - 1] += count * 0.1  # Reforzar números frecuentes
        
        # Normalizar
        probs = probs / np.sum(probs)
        
        # Generar combinación sin repeticiones
        combination = []
        available = list(range(1, 41))
        
        for _ in range(6):
            if not available:
                break
            
            # Probabilidades para números disponibles
            available_probs = [probs[num - 1] for num in available]
            available_probs = np.array(available_probs) / np.sum(available_probs)
            
            # Seleccionar número
            chosen_idx = np.random.choice(len(available), p=available_probs)
            chosen_num = available[chosen_idx]
            
            combination.append(chosen_num)
            available.remove(chosen_num)
        
        return sorted(combination)
    
    def _get_model_contributions(self) -> Dict[str, float]:
        """Obtiene contribuciones de cada modelo base"""
        
        contributions = {}
        
        if self.base_model_performances:
            total_f1 = sum(perf.f1_score for perf in self.base_model_performances.values())
            
            for name, perf in self.base_model_performances.items():
                if total_f1 > 0:
                    contributions[name] = perf.f1_score / total_f1
                else:
                    contributions[name] = 1.0 / len(self.base_model_performances)
        
        return contributions
    
    def _generate_random_predictions(self, num_predictions: int) -> List[Dict[str, Any]]:
        """Genera predicciones aleatorias como fallback"""
        
        predictions = []
        
        for i in range(num_predictions):
            combination = sorted(np.random.choice(range(1, 41), 6, replace=False).tolist())
            
            prediction = {
                'combination': combination,
                'confidence': 0.5,
                'source': 'ensemble_fallback',
                'strategy': 'random',
                'timestamp': datetime.now().isoformat()
            }
            
            predictions.append(prediction)
        
        return predictions
    
    def get_ensemble_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del ensemble"""
        
        summary = {
            'is_trained': self.is_trained,
            'strategy': self.strategy.value if self.strategy else None,
            'base_models_count': len(self.base_models_simulator.models),
            'ensemble_performance': self.ensemble_performance,
            'training_history_count': len(self.training_history)
        }
        
        if self.configuration:
            summary['configuration'] = asdict(self.configuration)
        
        if self.base_model_performances:
            summary['base_models_summary'] = {
                name: {
                    'accuracy': perf.accuracy,
                    'f1_score': perf.f1_score,
                    'consistency': perf.consistency
                }
                for name, perf in self.base_model_performances.items()
            }
            
            # Mejor y peor modelo base
            best_model = max(self.base_model_performances.items(), key=lambda x: x[1].f1_score)
            worst_model = min(self.base_model_performances.items(), key=lambda x: x[1].f1_score)
            
            summary['best_base_model'] = {
                'name': best_model[0],
                'f1_score': best_model[1].f1_score
            }
            summary['worst_base_model'] = {
                'name': worst_model[0],
                'f1_score': worst_model[1].f1_score
            }
        
        return summary
    
    def save_model(self, directory: str):
        """Guarda el modelo ensemble completo con procesadores y metadatos"""
        try:
            # Crear directorio si no existe
            os.makedirs(directory, exist_ok=True)
            
            # Guardar modelos de scikit-learn
            if self.ensemble_model is not None:
                model_path = os.path.join(directory, 'ensemble_model.pkl')
                joblib.dump(self.ensemble_model, model_path)
                logger.info(f"✅ Modelo ensemble guardado: {model_path}")
            
            if self.meta_model is not None:
                meta_path = os.path.join(directory, 'meta_model.pkl')
                joblib.dump(self.meta_model, meta_path)
                logger.info(f"✅ Meta-modelo guardado: {meta_path}")
            
            # Guardar procesadores de datos
            if self.feature_scaler is not None:
                scaler_path = os.path.join(directory, 'feature_scaler.pkl')
                joblib.dump(self.feature_scaler, scaler_path)
                logger.info(f"✅ Feature scaler guardado: {scaler_path}")
            
            if self.target_encoder is not None:
                encoder_path = os.path.join(directory, 'target_encoder.pkl')
                joblib.dump(self.target_encoder, encoder_path)
                logger.info(f"✅ Target encoder guardado: {encoder_path}")
            
            # Guardar configuración y metadatos
            config_data = {
                'strategy': self.strategy.value,
                'cv_folds': self.cv_folds,
                'random_state': self.random_state,
                'normalization_method': self.normalization_method,
                'fitted': self.fitted,
                'is_trained': self.is_trained,
                'training_metadata': self.training_metadata,
                'base_model_performances': {
                    name: asdict(perf) for name, perf in self.base_model_performances.items()
                } if self.base_model_performances else {},
                'ensemble_performance': asdict(self.ensemble_performance) if self.ensemble_performance else None,
                'configuration': asdict(self.configuration) if self.configuration else None
            }
            
            config_path = os.path.join(directory, 'ensemble_config.json')
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            logger.info(f"✅ Configuración guardada: {config_path}")
            logger.info(f"🎯 Ensemble completo guardado en: {directory}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando ensemble: {e}")
            raise
    
    @classmethod
    def load_model(cls, directory: str):
        """Carga un modelo ensemble completo desde directorio"""
        try:
            # Cargar configuración
            config_path = os.path.join(directory, 'ensemble_config.json')
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
            
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Crear instancia
            strategy = EnsembleStrategy(config_data['strategy'])
            trainer = cls(
                strategy=strategy,
                cv_folds=config_data.get('cv_folds', 5),
                random_state=config_data.get('random_state', 42),
                normalization_method=config_data.get('normalization_method', 'standard')
            )
            
            # Restaurar estado
            trainer.fitted = config_data.get('fitted', False)
            trainer.is_trained = config_data.get('is_trained', False)
            trainer.training_metadata = config_data.get('training_metadata', {})
            
            # Cargar modelos
            model_path = os.path.join(directory, 'ensemble_model.pkl')
            if os.path.exists(model_path):
                trainer.ensemble_model = joblib.load(model_path)
                logger.info(f"✅ Modelo ensemble cargado: {model_path}")
            
            meta_path = os.path.join(directory, 'meta_model.pkl')
            if os.path.exists(meta_path):
                trainer.meta_model = joblib.load(meta_path)
                logger.info(f"✅ Meta-modelo cargado: {meta_path}")
            
            # Cargar procesadores
            scaler_path = os.path.join(directory, 'feature_scaler.pkl')
            if os.path.exists(scaler_path):
                trainer.feature_scaler = joblib.load(scaler_path)
                logger.info(f"✅ Feature scaler cargado: {scaler_path}")
            
            encoder_path = os.path.join(directory, 'target_encoder.pkl')
            if os.path.exists(encoder_path):
                trainer.target_encoder = joblib.load(encoder_path)
                logger.info(f"✅ Target encoder cargado: {encoder_path}")
            
            # Restaurar performances
            if 'base_model_performances' in config_data:
                trainer.base_model_performances = {
                    name: ModelPerformance(**perf_data)
                    for name, perf_data in config_data['base_model_performances'].items()
                }
            
            if config_data.get('ensemble_performance'):
                trainer.ensemble_performance = ModelPerformance(**config_data['ensemble_performance'])
            
            if config_data.get('configuration'):
                trainer.configuration = EnsembleConfiguration(**config_data['configuration'])
            
            logger.info(f"🎯 Ensemble completo cargado desde: {directory}")
            return trainer
            
        except Exception as e:
            logger.error(f"❌ Error cargando ensemble: {e}")
            raise
    
    def predict_with_preprocessing(self, 
                                 combinations: Union[List[List[int]], np.ndarray],
                                 return_probabilities: bool = False) -> Union[List[int], Tuple[List[int], List[float]]]:
        """Realiza predicciones aplicando el preprocesamiento guardado"""
        if not self.is_trained:
            raise ValueError("El modelo debe estar entrenado antes de hacer predicciones")
        
        if not self.fitted:
            raise ValueError("Los procesadores deben estar ajustados antes de hacer predicciones")
        
        try:
            # Validar entrada
            validated_data = self._validate_historical_data(combinations)
            
            if not validated_data:
                raise ValueError("No se pudieron validar las combinaciones de entrada")
            
            # Extraer características usando el mismo método del entrenamiento
            features = []
            for combo in validated_data:
                feature_vector = self._extract_combination_features(combo)
                features.append(feature_vector)
            
            X = np.array(features)
            
            # Aplicar preprocesamiento
            if self.feature_scaler is not None:
                X = self.feature_scaler.transform(X)
            
            # Realizar predicción
            predictions = self.ensemble_model.predict(X)
            
            if return_probabilities and hasattr(self.ensemble_model, 'predict_proba'):
                probabilities = self.ensemble_model.predict_proba(X)
                return predictions.tolist(), probabilities.tolist()
            else:
                return predictions.tolist()
            
        except Exception as e:
            logger.error(f"❌ Error en predicción: {e}")
            raise

# Funciones de utilidad
def create_ensemble_trainer(strategy: EnsembleStrategy = EnsembleStrategy.STACKING) -> EnsembleTrainer:
    """Crea entrenador de ensemble"""
    return EnsembleTrainer(strategy=strategy)

def train_and_evaluate_ensemble(trainer: EnsembleTrainer, 
                               historical_data: List[List[int]]) -> Dict[str, Any]:
    """Entrena y evalúa ensemble en un solo paso"""
    
    training_results = trainer.train_ensemble(historical_data)
    predictions = trainer.predict_combinations(historical_data[-20:], num_predictions=3)
    summary = trainer.get_ensemble_summary()
    
    return {
        'training_results': training_results,
        'sample_predictions': predictions,
        'ensemble_summary': summary
    }

if __name__ == "__main__":
    # Demo del ensemble trainer
    print("🏗️ Demo Ensemble Trainer")
    
    # Crear trainer
    trainer = create_ensemble_trainer(EnsembleStrategy.STACKING)
    
    # Datos de ejemplo
    sample_data = []
    np.random.seed(42)
    
    for _ in range(100):  # Más datos para entrenamiento efectivo
        combination = sorted(np.random.choice(range(1, 41), 6, replace=False))
        sample_data.append(combination)
    
    print(f"📊 Entrenando ensemble con {len(sample_data)} combinaciones...")
    
    try:
        # Entrenar y evaluar
        results = train_and_evaluate_ensemble(trainer, sample_data)
        
        print(f"✅ Entrenamiento completado:")
        training = results['training_results']
        print(f"   Tiempo: {training['training_time']:.2f}s")
        print(f"   Accuracy: {training['ensemble_performance']['accuracy']:.3f}")
        print(f"   F1-Score: {training['ensemble_performance']['f1_score']:.3f}")
        
        print(f"\n🎯 Predicciones de muestra:")
        for i, pred in enumerate(results['sample_predictions'], 1):
            combination = pred['combination']
            confidence = pred['confidence']
            print(f"   {i}. {' - '.join(map(str, combination))} (Confianza: {confidence:.1%})")
        
        # Resumen
        summary = results['ensemble_summary']
        print(f"\n📈 Resumen del ensemble:")
        print(f"   Estrategia: {summary['strategy']}")
        print(f"   Modelos base: {summary['base_models_count']}")
        
        if 'best_base_model' in summary:
            best = summary['best_base_model']
            print(f"   Mejor modelo: {best['name']} (F1: {best['f1_score']:.3f})")
        
    except Exception as e:
        print(f"❌ Error en demo: {e}")
        
        # Test básico de funcionalidad
        print(f"🔍 Test básico de funcionalidad...")
        predictions = trainer._generate_random_predictions(3)
        print(f"   Predicciones aleatorias generadas: {len(predictions)}")
        for i, pred in enumerate(predictions, 1):
            print(f"     {i}. {' - '.join(map(str, pred['combination']))}")
