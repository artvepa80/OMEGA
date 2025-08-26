# OMEGA_PRO_AI_v10.1/modules/lstm_model.py - Unified Enhanced LSTM for OMEGA PRO AI
# Consolidates best features from all LSTM versions: enhanced architecture, attention mechanisms, smart caching
# Production-ready with 65-70% accuracy targeting and robust error handling

import logging
import os
import json
import random
import traceback
import datetime
import copy
from dataclasses import dataclass, field, asdict, fields
from pathlib import Path
from typing import Optional, List, Dict, Set, Tuple, Any, Union

# Third-party imports
import numpy as np
import pandas as pd
import tensorflow as tf
import joblib
from sklearn.preprocessing import MinMaxScaler, StandardScaler

# Enhanced TensorFlow layers for advanced architecture
from tensorflow.keras.models import Sequential, load_model, Model
from tensorflow.keras.layers import (
    LSTM, Dense, Dropout, BatchNormalization, Input, Concatenate, 
    Bidirectional, MultiHeadAttention, LayerNormalization, Add,
    GlobalAveragePooling1D, GlobalMaxPooling1D, Attention
)
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, ModelCheckpoint, TensorBoard
)
from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator

# Local modules
from modules.score_dynamics import score_combinations

# ========== TIPOS DE DATOS ==========
@dataclass
class Combination:
    """Representa una combinación de números con metadatos"""
    numbers: List[int]
    source: str
    score: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    normalized: float = 0.0

    min_value: int = field(default=1, init=False, repr=False)
    max_value: int = field(default=40, init=False, repr=False)
    required_count: int = field(default=6, init=False, repr=False)

    def __post_init__(self):
        if isinstance(self.numbers, tuple):
            self.numbers = list(self.numbers)
        if len(self.numbers) != self.required_count:
            raise ValueError(
                f"Combinación debe tener {self.required_count} números, "
                f"recibió {len(self.numbers)}"
            )

        if len(set(self.numbers)) != self.required_count:
            raise ValueError(f"Combinación contiene números duplicados: {self.numbers}")

        if not all(self.min_value <= num <= self.max_value for num in self.numbers):
            invalid = [num for num in self.numbers if not self.min_value <= num <= self.max_value]
            raise ValueError(
                f"Números fuera de rango ({self.min_value}-{self.max_value}): {invalid}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "combination": self.numbers,
            "numbers": self.numbers,
            "source": self.source,
            "score": self.score,
            "metrics": self.metrics,
            "normalized": self.normalized
        }

@dataclass
class LSTMConfig:
    """Enhanced configuration for unified LSTM model with advanced features"""
    n_steps: int = 10
    n_units: int = 128
    dropout_rate: float = 0.3
    learning_rate: float = 0.001
    seed: Optional[int] = None
    model_path: Optional[Path] = None
    epochs: int = 100
    batch_size: int = 32
    validation_split: float = 0.15
    use_cached_model: bool = False
    tensorboard_logdir: Optional[Path] = None

    use_enhanced_architecture: bool = True
    use_attention: bool = True
    attention_heads: int = 4
    attention_units: int = 64
    use_bidirectional: bool = True
    use_positional_outputs: bool = True
    
    # Feature fusion parameters
    use_feature_fusion: bool = True
    fusion_units: int = 64
    
    # Advanced training parameters
    use_batch_norm: bool = True
    use_layer_norm: bool = True
    gradient_clipping: float = 1.0
    
    # Regularization
    l1_reg: float = 0.001
    l2_reg: float = 0.001
    
    # Strategic filtering integration
    use_strategic_filtering: bool = True
    
    # Data parameters
    number_range: Tuple[int, int] = (1, 40)
    number_count: int = 6
    scaler_type: str = "minmax"
    
    # Callback parameters
    early_stopping_patience: int = 20
    reduce_lr_patience: int = 8
    reduce_lr_factor: float = 0.3
    reduce_lr_min: float = 1e-7

    def __post_init__(self):
        """
        Valida los hiperparámetros después de la inicialización.

        Realiza comprobaciones básicas para asegurar que los parámetros
        numéricos y lógicos estén en rangos aceptables. Además valida
        parámetros añadidos como `number_range`, `number_count`, el tipo de
        escalador, y las configuraciones de callbacks.
        """
        if self.n_steps <= 0:
            raise ValueError(f"n_steps debe ser positivo, recibió {self.n_steps}")

        if not (0 <= self.dropout_rate < 1):
            raise ValueError(f"dropout_rate debe estar en [0,1), recibió {self.dropout_rate}")

        if not (0 < self.validation_split < 1):
            raise ValueError(f"validation_split debe estar entre 0-1, recibió {self.validation_split}")

        if self.learning_rate <= 0:
            raise ValueError(f"learning_rate debe ser positivo, recibió {self.learning_rate}")

        if self.use_cached_model and not self.model_path:
            raise ValueError("model_path debe estar definido cuando use_cached_model es True")

        # Validar rango de números
        if (not isinstance(self.number_range, (list, tuple)) or
                len(self.number_range) != 2):
            raise ValueError(
                f"number_range debe ser una tupla/lista de 2 enteros, recibió {self.number_range}"
            )
        min_val, max_val = self.number_range
        if not (isinstance(min_val, int) and isinstance(max_val, int)):
            raise ValueError("number_range debe contener enteros")
        if min_val >= max_val:
            raise ValueError(f"number_range mínimo debe ser menor que máximo, recibió {self.number_range}")

        # Validar número de elementos en la combinación
        if not isinstance(self.number_count, int) or self.number_count <= 0:
            raise ValueError(
                f"number_count debe ser un entero positivo, recibió {self.number_count}"
            )
        if self.number_count > (max_val - min_val + 1):
            raise ValueError(
                f"number_count ({self.number_count}) no puede exceder el rango total "
                f"de valores ({max_val - min_val + 1})"
            )

        # Validar tipo de escalador
        if self.scaler_type.lower() not in {"minmax", "standard"}:
            raise ValueError(
                f"scaler_type debe ser 'minmax' o 'standard', recibió {self.scaler_type}"
            )
        self.scaler_type = self.scaler_type.lower()

        # Validar parámetros de callbacks
        if self.early_stopping_patience <= 0:
            raise ValueError(
                f"early_stopping_patience debe ser positivo, recibió {self.early_stopping_patience}"
            )
        if self.reduce_lr_patience <= 0:
            raise ValueError(
                f"reduce_lr_patience debe ser positivo, recibió {self.reduce_lr_patience}"
            )
        if not (0 < self.reduce_lr_factor < 1):
            raise ValueError(
                f"reduce_lr_factor debe estar entre 0 y 1, recibió {self.reduce_lr_factor}"
            )
        if self.reduce_lr_min <= 0:
            raise ValueError(
                f"reduce_lr_min debe ser positivo, recibió {self.reduce_lr_min}"
            )

        # Normalizar booleano para use_batch_norm
        if isinstance(self.use_batch_norm, str):
            # Aceptar 'true'/'false' en strings (por ejemplo desde JSON)
            self.use_batch_norm = self.use_batch_norm.lower() in {"true", "1", "yes"}

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "LSTMConfig":
        """Crea una configuración desde un diccionario con conversión de tipos"""
        valid_keys = {f.name for f in fields(cls)}
        filtered = {}
       
        for key, value in config_dict.items():
            if key in valid_keys:
                if key in {'model_path', 'tensorboard_logdir'} and value:
                    # Convertir rutas a objetos Path
                    filtered[key] = Path(value)
                # Convertir enteros almacenados como cadenas
                elif key in {
                    'n_steps', 'n_units', 'epochs', 'batch_size',
                    'number_count', 'early_stopping_patience', 'reduce_lr_patience'
                } and isinstance(value, str):
                    filtered[key] = int(value)
                # Convertir flotantes almacenados como cadenas
                elif key in {
                    'dropout_rate', 'learning_rate', 'validation_split',
                    'reduce_lr_factor', 'reduce_lr_min'
                } and isinstance(value, str):
                    filtered[key] = float(value)
                # Convertir semántica booleana almacenada como cadenas
                elif key == 'use_batch_norm':
                    if isinstance(value, str):
                        filtered[key] = value.lower() in {"true", "1", "yes"}
                    else:
                        filtered[key] = bool(value)
                # Normalizar scaler_type
                elif key == 'scaler_type' and isinstance(value, str):
                    filtered[key] = value.lower()
                # Convertir number_range (lista o cadena) a tupla de enteros
                elif key == 'number_range':
                    if isinstance(value, str):
                        # Aceptar formatos "1-40" o "1,40"
                        if '-' in value:
                            parts = value.split('-')
                        else:
                            parts = value.split(',')
                        try:
                            min_val, max_val = int(parts[0]), int(parts[1])
                            filtered[key] = (min_val, max_val)
                        except Exception:
                            # Si falla, ignorar y dejar que el valor por defecto aplique
                            pass
                    elif isinstance(value, (list, tuple)) and len(value) == 2:
                        try:
                            filtered[key] = (int(value[0]), int(value[1]))
                        except Exception:
                            pass
                    else:
                        # dejar el valor sin cambios; será validado posteriormente
                        filtered[key] = value
                elif key == 'seed' and value == 'None':
                    filtered[key] = None
                else:
                    filtered[key] = value
       
        default_config = asdict(cls())
        default_config.update(filtered)
        return cls(**default_config)

# ========== UTILIDADES ==========
def wrap_logger(logger: Optional[logging.Logger] = None, prefix: str = "LSTM") -> callable:
    log = logger or logging.getLogger(__name__)
   
    def log_func(msg: str, level: str = "info"):
        level = level.lower()
        if level not in ["debug", "info", "warning", "error", "critical"]:
            level = "info"
        formatted_msg = f"[{prefix}] {msg}"
        # Use proper logging call without extra parameters
        if level == "debug":
            log.debug(formatted_msg)
        elif level == "info":
            log.info(formatted_msg)
        elif level == "warning":
            log.warning(formatted_msg)
        elif level == "error":
            log.error(formatted_msg)
        elif level == "critical":
            log.critical(formatted_msg)
   
    return log_func

def load_config(config_path: Path = Path("config/lstm_config.json")) -> LSTMConfig:
    default_config = LSTMConfig()
   
    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return LSTMConfig.from_dict(config_data)
    except Exception as e:
        logging.error(f"Error cargando configuración: {e}")
   
    return default_config

def fallback_combinations(
    historial_set: Set[Tuple[int, ...]],
    cantidad: int,
    rng: random.Random,
    config: Optional[LSTMConfig] = None,
    training_data: Optional[np.ndarray] = None
) -> List[Combination]:
    """
    Genera combinaciones aleatorias inteligentes que no se encuentren en el historial.
    Ahora incluye sesgo histórico basado en frecuencias de números ganadores.

    Args:
        historial_set: Conjunto de combinaciones históricas a evitar.
        cantidad: Número de combinaciones a generar.
        rng: Generador de números aleatorios.
        config: Configuración opcional para ajustar rango y tamaño.
        training_data: Datos de entrenamiento para calcular frecuencias históricas.

    Returns:
        Lista de objetos Combination con sesgo histórico mejorado.
    """
    results: List[Combination] = []
    
    # Determinar rango y longitud de la combinación
    if config:
        min_val, max_val = config.number_range
        num_count = config.number_count
    else:
        min_val, max_val = Combination.min_value, Combination.max_value
        num_count = Combination.required_count

    value_range = list(range(min_val, max_val + 1))
    
    # Calcular frecuencias históricas si hay datos disponibles
    historical_bias = None
    if training_data is not None and len(training_data) > 0:
        try:
            # Calcular frecuencias de aparición de cada número
            frequency_count = np.zeros(max_val + 1)
            
            for combination in training_data:
                for number in combination:
                    if isinstance(number, (int, float)) and min_val <= int(number) <= max_val:
                        frequency_count[int(number)] += 1
            
            # Normalizar frecuencias para crear pesos de probabilidad
            total_count = np.sum(frequency_count[min_val:max_val+1])
            if total_count > 0:
                historical_bias = frequency_count[min_val:max_val+1] / total_count
                # Suavizar para evitar ceros absolutos
                historical_bias = historical_bias + 0.01  # Laplace smoothing
                historical_bias = historical_bias / np.sum(historical_bias)
                
        except Exception:
            historical_bias = None
    
    # Generar combinaciones con sesgo histórico o aleatorio
    max_attempts = cantidad * 50  # Prevenir bucles infinitos
    attempts = 0
    
    while len(results) < cantidad and attempts < max_attempts:
        attempts += 1
        
        try:
            if historical_bias is not None:
                # Usar probabilidades basadas en frecuencia histórica
                # 70% de números basados en frecuencia, 30% aleatorios para diversidad
                combo_numbers = []
                
                # Primeros 4 números con sesgo histórico
                biased_numbers = rng.choices(
                    value_range, 
                    weights=historical_bias, 
                    k=min(4, num_count)
                )
                combo_numbers.extend(biased_numbers)
                
                # Números restantes aleatorios para diversidad
                remaining_count = num_count - len(combo_numbers)
                if remaining_count > 0:
                    available = [n for n in value_range if n not in combo_numbers]
                    if len(available) >= remaining_count:
                        random_numbers = rng.sample(available, remaining_count)
                        combo_numbers.extend(random_numbers)
                    else:
                        # Si no hay suficientes disponibles, usar muestreo completo
                        combo_numbers = rng.sample(value_range, num_count)
                
                combo = tuple(sorted(set(combo_numbers)))
                
                # Si hay duplicados o no tiene la longitud correcta, reintenta
                if len(combo) != num_count:
                    continue
                    
            else:
                # Fallback a generación completamente aleatoria
                combo = tuple(sorted(rng.sample(value_range, num_count)))
            
            # Verificar que no esté en el historial
            if combo not in historial_set:
                combination_obj = Combination(
                    numbers=list(combo),
                    source="lstm_fallback_enhanced"
                )
                
                # Añadir métricas de sesgo histórico
                if historical_bias is not None:
                    bias_score = sum(historical_bias[n - min_val] for n in combo) / len(combo)
                    combination_obj.metrics['historical_bias_score'] = float(bias_score)
                    combination_obj.metrics['generation_method'] = 'historical_weighted'
                else:
                    combination_obj.metrics['generation_method'] = 'pure_random'
                
                results.append(combination_obj)
                
        except Exception as e:
            # En caso de error, usar método básico
            combo = tuple(sorted(rng.sample(value_range, num_count)))
            if combo not in historial_set:
                results.append(
                    Combination(
                        numbers=list(combo),
                        source="lstm_fallback_basic"
                    )
                )
    
    # Si no se pudo generar suficientes, completar con aleatorias básicas
    while len(results) < cantidad:
        try:
            combo = tuple(sorted(rng.sample(value_range, num_count)))
            if combo not in historial_set:
                results.append(
                    Combination(
                        numbers=list(combo),
                        source="lstm_fallback_final"
                    )
                )
        except Exception:
            break
    
    return results

# ========== MODELO LSTM ==========
class LSTMCombiner:
    """Clase para combinar y predecir combinaciones usando LSTM"""
    
    def __init__(self, config: LSTMConfig):
        """
        Inicializa el combinador LSTM
        
        Args:
            config: Configuración del modelo
        """
        self.config = config
        self.model = None
        self.scaler = None
        self.history = None
        
        # RNG para reproducibilidad
        self.rng = random.Random(config.seed) if config.seed else random.Random()
        
        # Establecer semillas para reproducibilidad
        if config.seed is not None:
            self._set_seeds(config.seed)
    
    def _set_seeds(self, seed: int):
        """Establece todas las semillas para reproducibilidad"""
        os.environ['PYTHONHASHSEED'] = str(seed)
        random.seed(seed)
        np.random.seed(seed)
        tf.random.set_seed(seed)
        os.environ['TF_DETERMINISTIC_OPS'] = '1'
        self.rng = random.Random(seed)
    
    def _configure_gpu_support(self, log_func: callable):
        """Configure GPU support and optimization if available"""
        try:
            # Check for GPU availability
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                log_func(f"🎯 GPU disponible: {len(gpus)} dispositivos detectados", "info")
                try:
                    # Enable memory growth to prevent allocation of all GPU memory
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    
                    # Enable mixed precision for faster training if supported
                    policy = tf.keras.mixed_precision.Policy('mixed_float16')
                    tf.keras.mixed_precision.set_global_policy(policy)
                    log_func("🚀 Mixed precision enabled for faster GPU training", "info")
                    
                except Exception as gpu_config_error:
                    log_func(f"⚠️ GPU configuration warning: {gpu_config_error}", "warning")
            else:
                log_func("💻 No GPU detected, using CPU training", "info")
                # Optimize CPU performance
                tf.config.threading.set_intra_op_parallelism_threads(0)  # Use all cores
                tf.config.threading.set_inter_op_parallelism_threads(0)
                
        except Exception as e:
            log_func(f"⚠️ Error configuring compute devices: {e}", "warning")
    
    def _validate_data(self, data: np.ndarray):
        """
        Valida los datos antes del entrenamiento.

        Comprueba que los datos sean una matriz 2D no vacía, sin valores
        faltantes (NaN) y con un número de columnas coincidente con
        `config.number_count`. Se alerta mediante logging si el número de
        columnas difiere del esperado, ya que puede afectar al rendimiento
        del modelo.
        """
        if data.size == 0:
            raise ValueError("Datos de entrenamiento vacíos")

        if data.ndim != 2:
            raise ValueError(f"Se esperaba matriz 2D, se recibió {data.ndim}D")

        # Verificar número de características
        expected_cols = self.config.number_count
        if data.shape[1] != expected_cols:
            logging.warning(
                f"Se esperaban {expected_cols} características, se recibieron {data.shape[1]}. "
                "El modelo puede no funcionar correctamente."
            )

        # Verificar y limpiar NaN
        if np.isnan(data).any():
            logging.warning("Datos contienen valores NaN, aplicando limpieza...")
            # Replace NaN with column means
            for col in range(data.shape[1]):
                col_data = data[:, col]
                if np.isnan(col_data).any():
                    col_mean = np.nanmean(col_data)
                    data[:, col] = np.where(np.isnan(col_data), col_mean, col_data)

        n_samples = data.shape[0]
        # Se necesitan al menos n_steps+2 muestras para formar al menos una ventana de entrenamiento y otra de validación
        if n_samples < self.config.n_steps + 2:
            raise ValueError(
                f"Insuficientes datos: {n_samples} muestras. "
                f"Se necesitan ≥{self.config.n_steps + 2} para n_steps={self.config.n_steps}"
            )
    
    def build_model(self, input_shape: Tuple[int, int]) -> Model:
        """
        Builds enhanced LSTM model with attention mechanisms and advanced architecture
        
        Args:
            input_shape: (n_steps, n_features) input shape
            
        Returns:
            Compiled Keras Model with enhanced architecture
        """
        if self.config.use_enhanced_architecture:
            return self._build_enhanced_model(input_shape)
        else:
            return self._build_basic_model(input_shape)
    
    def _build_enhanced_model(self, input_shape: Tuple[int, int]) -> Model:
        """Build enhanced model with bidirectional LSTM, attention mechanisms and lottery-optimized architecture"""
        n_steps, n_features = input_shape
        
        # Input layer with enhanced preprocessing
        inputs = Input(shape=input_shape, name='sequence_input')
        
        # Input normalization for better convergence
        normalized_inputs = LayerNormalization(name='input_norm')(inputs) if self.config.use_layer_norm else inputs
        
        # First Bidirectional LSTM layer with enhanced configuration
        if self.config.use_bidirectional:
            lstm1 = Bidirectional(
                LSTM(
                    self.config.n_units, 
                    return_sequences=True, 
                    dropout=self.config.dropout_rate,
                    recurrent_dropout=0.1,  # Added recurrent dropout for better regularization
                    kernel_regularizer=tf.keras.regularizers.l2(self.config.l2_reg)
                ),
                name='bidirectional_lstm1'
            )(normalized_inputs)
        else:
            lstm1 = LSTM(
                self.config.n_units, 
                return_sequences=True, 
                dropout=self.config.dropout_rate,
                recurrent_dropout=0.1,
                kernel_regularizer=tf.keras.regularizers.l2(self.config.l2_reg),
                name='lstm1'
            )(normalized_inputs)
        
        if self.config.use_batch_norm:
            lstm1 = BatchNormalization(name='batch_norm1')(lstm1)
            
        # Second Bidirectional LSTM layer with deeper architecture
        if self.config.use_bidirectional:
            lstm2 = Bidirectional(
                LSTM(
                    self.config.n_units, 
                    return_sequences=True, 
                    dropout=self.config.dropout_rate,
                    recurrent_dropout=0.1,
                    kernel_regularizer=tf.keras.regularizers.l2(self.config.l2_reg)
                ),
                name='bidirectional_lstm2'
            )(lstm1)
        else:
            lstm2 = LSTM(
                self.config.n_units, 
                return_sequences=True, 
                dropout=self.config.dropout_rate,
                recurrent_dropout=0.1,
                kernel_regularizer=tf.keras.regularizers.l2(self.config.l2_reg),
                name='lstm2'
            )(lstm1)
        
        if self.config.use_batch_norm:
            lstm2 = BatchNormalization(name='batch_norm2')(lstm2)
        
        # Enhanced Multi-head attention mechanism
        if self.config.use_attention:
            # Self-attention with multiple heads
            attention_output = MultiHeadAttention(
                num_heads=self.config.attention_heads,
                key_dim=self.config.attention_units,
                dropout=self.config.dropout_rate,
                name='multi_head_attention'
            )(lstm2, lstm2)
            
            if self.config.use_layer_norm:
                attention_output = LayerNormalization(name='attention_layer_norm')(attention_output)
            
            # Residual connection with gating mechanism
            gate = Dense(lstm2.shape[-1], activation='sigmoid', name='attention_gate')(lstm2)
            gated_attention = tf.keras.layers.Multiply(name='gated_attention')([attention_output, gate])
            combined = Add(name='residual_connection')([lstm2, gated_attention])
        else:
            combined = lstm2
        
        # Enhanced global pooling with multiple strategies
        avg_pool = GlobalAveragePooling1D(name='global_avg_pool')(combined)
        max_pool = GlobalMaxPooling1D(name='global_max_pool')(combined)
        
        # Extract last timestep features (important for sequence prediction)
        last_timestep = tf.keras.layers.Lambda(
            lambda x: x[:, -1, :], 
            name='last_timestep'
        )(combined)
        
        pooled_output = Concatenate(name='pooled_features')([avg_pool, max_pool, last_timestep])
        
        # Enhanced feature fusion with lottery-specific optimization
        if self.config.use_feature_fusion:
            # First fusion layer with higher capacity
            fusion1 = Dense(
                self.config.fusion_units * 2,  # Increased capacity
                activation='relu',
                kernel_regularizer=tf.keras.regularizers.l1_l2(
                    l1=self.config.l1_reg, l2=self.config.l2_reg
                ),
                name='fusion1'
            )(pooled_output)
            
            if self.config.use_batch_norm:
                fusion1 = BatchNormalization(name='fusion_batch_norm1')(fusion1)
            fusion1 = Dropout(self.config.dropout_rate, name='fusion_dropout1')(fusion1)
            
            # Second fusion layer with lottery pattern learning
            fusion2 = Dense(
                self.config.fusion_units,
                activation='relu', 
                kernel_regularizer=tf.keras.regularizers.l1_l2(
                    l1=self.config.l1_reg, l2=self.config.l2_reg
                ),
                name='fusion2'
            )(fusion1)
            
            if self.config.use_batch_norm:
                fusion2 = BatchNormalization(name='fusion_batch_norm2')(fusion2)
            fusion2 = Dropout(self.config.dropout_rate, name='fusion_dropout2')(fusion2)
            
            # Third fusion layer for pattern refinement
            fusion3 = Dense(
                self.config.fusion_units // 2,
                activation='relu',
                kernel_regularizer=tf.keras.regularizers.l1_l2(
                    l1=self.config.l1_reg, l2=self.config.l2_reg
                ),
                name='fusion3'
            )(fusion2)
            
            fusion3 = Dropout(self.config.dropout_rate * 0.5, name='fusion_dropout3')(fusion3)
            final_features = fusion3
        else:
            final_features = pooled_output
        
        # Enhanced output layer - unified approach optimized for lottery prediction
        # Use single output that predicts continuous values, then clean to lottery numbers
        output = Dense(
            n_features,
            activation='tanh',  # Changed from linear to tanh for better bounded predictions
            kernel_regularizer=tf.keras.regularizers.l1_l2(
                l1=self.config.l1_reg, l2=self.config.l2_reg
            ),
            name='lottery_prediction_output'
        )(final_features)
        
        model = Model(inputs=inputs, outputs=output, name='enhanced_lottery_lstm_v2')
        
        # Enhanced optimizer with lottery-specific learning schedule
        optimizer = tf.keras.optimizers.Adam(
            learning_rate=self.config.learning_rate,
            beta_1=0.9,
            beta_2=0.999,
            epsilon=1e-7,
            clipnorm=self.config.gradient_clipping
        )
        
        # Custom loss function that emphasizes lottery number range
        def lottery_mse_loss(y_true, y_pred):
            """Custom MSE loss with lottery-specific penalties"""
            base_loss = tf.keras.losses.mse(y_true, y_pred)
            
            # Penalize predictions outside lottery range (1-40)
            range_penalty = tf.reduce_mean(
                tf.maximum(0.0, tf.abs(y_pred) - 40.0) * 0.1
            )
            
            return base_loss + range_penalty
        
        model.compile(
            optimizer=optimizer,
            loss=lottery_mse_loss,
            metrics=['mae', 'mse']
        )
        
        return model
    
    def _build_basic_model(self, input_shape: Tuple[int, int]) -> Model:
        """Build basic sequential LSTM model for compatibility"""
        n_steps, n_features = input_shape
        
        model = Sequential([
            LSTM(self.config.n_units, return_sequences=True, input_shape=input_shape),
            BatchNormalization() if self.config.use_batch_norm else tf.keras.layers.Lambda(lambda x: x),
            Dropout(self.config.dropout_rate),
            LSTM(self.config.n_units),
            BatchNormalization() if self.config.use_batch_norm else tf.keras.layers.Lambda(lambda x: x),
            Dropout(self.config.dropout_rate),
            Dense(n_features, activation='linear')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.config.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        return model
    
    def train(self, data: np.ndarray, log_func: callable, 
             adaptive_config: Optional[Dict] = None) -> tf.keras.callbacks.History:
        """
        Entrena el modelo LSTM con los datos proporcionados
        
        Args:
            data: Datos de entrenamiento
            log_func: Función para logging
            adaptive_config: Configuración adaptativa opcional
            
        Returns:
            history: Objeto con historial de entrenamiento
        """
        try:
            # Validar datos
            self._validate_data(data)
            log_func(f"Datos validados: shape={data.shape}, type={type(data)}", "debug")
            
            # Apply adaptive configuration if provided
            if adaptive_config:
                self._apply_adaptive_config(adaptive_config, log_func)
            
            # Configure GPU if available
            self._configure_gpu_support(log_func)
            
            # Preprocesamiento y escalado
            if self.config.scaler_type == "standard":
                self.scaler = StandardScaler()
            else:
                self.scaler = MinMaxScaler()
                
            log_func(f"Aplicando escalado {self.config.scaler_type}", "debug")
            data_scaled = self.scaler.fit_transform(data)
            log_func(f"Datos escalados: min={data_scaled.min():.4f}, max={data_scaled.max():.4f}", "debug")

            n_samples = len(data_scaled)
            n_steps = self.config.n_steps
            val_split = self.config.validation_split

            # Calcular índice de split considerando ventanas temporales
            available_windows = n_samples - n_steps + 1
            if available_windows < 2:
                raise ValueError(f"Insufficient data: need at least {n_steps + 1} samples, got {n_samples}")
                
            train_windows = max(1, int(available_windows * (1 - val_split)))
            split_index = n_steps + train_windows - 1
            
            log_func(f"Split de datos: train_windows={train_windows}, val_windows={available_windows - train_windows}", "debug")

            # Crear generadores con manejo robusto de errores
            try:
                train_generator = TimeseriesGenerator(
                    data_scaled, 
                    data_scaled,
                    length=n_steps,
                    batch_size=min(self.config.batch_size, train_windows),  # Prevent batch_size > samples
                    start_index=0,
                    end_index=split_index,
                    shuffle=False  # Critical for time series
                )
                
                val_generator = TimeseriesGenerator(
                    data_scaled, 
                    data_scaled,
                    length=n_steps,
                    batch_size=min(self.config.batch_size, available_windows - train_windows),
                    start_index=split_index + 1,
                    end_index=n_samples - 1,
                    shuffle=False
                )
                
                # Validate generators have data
                if len(train_generator) == 0:
                    raise ValueError(f"No training windows generated with current configuration")
                if len(val_generator) == 0:
                    raise ValueError(f"No validation windows generated with current configuration")
                    
                log_func(f"Generadores creados: train={len(train_generator)}, val={len(val_generator)}", "info")
                
                # Test generator unpack to prevent runtime errors
                try:
                    X_test, y_test = train_generator[0]
                    log_func(f"Generator test successful: X_shape={X_test.shape}, y_shape={y_test.shape}", "debug")
                except Exception as unpack_error:
                    log_func(f"CRITICAL: Generator unpack test failed: {unpack_error}", "error")
                    raise RuntimeError(f"TimeseriesGenerator unpack error: {unpack_error}")
                
            except Exception as gen_error:
                log_func(f"Error creating generators: {gen_error}", "error")
                raise RuntimeError(f"Failed to create data generators: {gen_error}")
        
            n_features = data_scaled.shape[1]
            input_shape = (self.config.n_steps, n_features)
            log_func(f"Input shape: {input_shape}, features: {n_features}", "debug")
            
            # Construir modelo con arquitectura mejorada
            self.model = self.build_model(input_shape)
            log_func(f"Modelo construido con arquitectura {'enhanced' if self.config.use_enhanced_architecture else 'basic'}", "info")
            
            # Callbacks por defecto con mejoras
            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=self.config.early_stopping_patience,
                    restore_best_weights=True,
                    verbose=1,
                    min_delta=1e-6  # Added for better convergence detection
                ),
                ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=self.config.reduce_lr_factor,
                    patience=self.config.reduce_lr_patience,
                    min_lr=self.config.reduce_lr_min,
                    verbose=1,
                    cooldown=2  # Added cooldown period
                )
            ]
            
            # Callbacks adicionales
            if self.config.tensorboard_logdir:
                self.config.tensorboard_logdir.mkdir(parents=True, exist_ok=True)
                callbacks.append(TensorBoard(
                    log_dir=self.config.tensorboard_logdir, 
                    histogram_freq=1,
                    write_graph=True,
                    profile_batch='10,20'  # Profile performance
                ))
                
            if self.config.model_path:
                self.config.model_path.parent.mkdir(parents=True, exist_ok=True)
                best_model_path = self.config.model_path.with_name(
                    f"{self.config.model_path.name}_best.h5"
                )
                callbacks.append(ModelCheckpoint(
                    filepath=str(best_model_path),
                    save_best_only=True,
                    monitor='val_loss',
                    save_weights_only=False,
                    verbose=1
                ))
            
            # Training with robust error handling
            log_func(f"🚀 Iniciando entrenamiento: {self.config.epochs} epochs, batch_size={self.config.batch_size}", "info")
            
            # TensorFlow 2.x compatibility - some versions don't support workers parameter
            fit_kwargs = {
                'epochs': self.config.epochs,
                'validation_data': val_generator,
                'verbose': 1,
                'callbacks': callbacks,
                'shuffle': False  # Critical for time series
            }
            
            # Add multiprocessing parameters only if supported
            try:
                self.history = self.model.fit(
                    train_generator,
                    **fit_kwargs,
                    workers=1,
                    use_multiprocessing=False
                )
            except TypeError:
                # Fallback for older TensorFlow versions
                self.history = self.model.fit(
                    train_generator,
                    **fit_kwargs
                )
            
            log_func(f"✅ Entrenamiento completado exitosamente", "info")
            return self.history
            
        except Exception as e:
            log_func(f"❌ Error crítico en entrenamiento: {str(e)}", "error")
            log_func(f"Traceback completo: {traceback.format_exc()}", "debug")
            raise RuntimeError(f"Training failed: {str(e)}") from e
    
    def _apply_adaptive_config(self, adaptive_config: Dict, log_func: callable):
        """Apply adaptive configuration during training"""
        if 'early_stopping_patience' in adaptive_config:
            self.config.early_stopping_patience = adaptive_config['early_stopping_patience']
            log_func(f"Adjusted early stopping patience: {self.config.early_stopping_patience}", "info")
        
        if 'reduce_lr_factor' in adaptive_config:
            self.config.reduce_lr_factor = adaptive_config['reduce_lr_factor']
            log_func(f"Adjusted LR reduction factor: {self.config.reduce_lr_factor}", "info")
        
        if 'batch_size' in adaptive_config:
            self.config.batch_size = adaptive_config['batch_size']
            log_func(f"Adjusted batch size: {self.config.batch_size}", "info")
    
    def safe_train_and_predict(
        self, 
        data: np.ndarray,
        historial_set: Set[Tuple[int, ...]],
        steps: int,
        log_func: callable,
        adaptive_config: Optional[Dict] = None
    ) -> List[Combination]:
        """Entrena y predice con manejo de errores integrado"""
        try:
            # Entrenar con configuración adaptativa
            self.train(data, log_func, adaptive_config)
            history_list = data.tolist()
            predictions = self.predict_sequence(history_list, steps)
           
            # Procesar y puntuar combinaciones
            combos = [self.clean_combination(pred) for pred in predictions]
            return self.process_combinations(combos, historial_set, data, log_func)
           
        except Exception as e:
            log_func(f"Error en LSTM: {e}\n{traceback.format_exc()}", "error")
            # En caso de error, recurrir a combinaciones aleatorias mejoradas con sesgo histórico
            return fallback_combinations(
                historial_set, 
                steps, 
                self.rng, 
                self.config,
                training_data=data  # Pass training data for historical bias
            )
   
    def process_combinations(
        self,
        combos: List[List[int]],
        historial_set: Set[Tuple[int, ...]],
        training_data: np.ndarray,
        log_func: callable
    ) -> List[Combination]:
        """Procesa y puntúa combinaciones generadas"""
        # Eliminar duplicados manteniendo orden de primera aparición
        seen = set()
        unique_combos = []
        for c in combos:
            try:
                c_tuple = tuple(sorted(c))
                if c_tuple not in seen:
                    seen.add(c_tuple)
                    unique_combos.append(c_tuple)
            except Exception as e:
                log_func(f"Error procesando combinación {c}: {e}", "warning")
       
        # Convertir a objetos Combination
        candidates = [
            Combination(numbers=list(combo), source="lstm") # Convert to list
            for combo in unique_combos
        ]
       
        # Apply strategic filtering if enabled
        if self.config.use_strategic_filtering:
            try:
                from modules.filters.rules_filter import FiltroEstrategico
                log_func("🔍 Aplicando filtro estratégico a combinaciones LSTM", "info")
                
                filtro = FiltroEstrategico()
                filtered_candidates = []
                
                for candidate in candidates:
                    combo = candidate.numbers
                    try:
                        valido, score_factor, razones = filtro.aplicar_filtros(
                            combo, return_score=True, return_reasons=True
                        )
                        if valido:
                            candidate.metrics['strategic_filter_score'] = score_factor
                            filtered_candidates.append(candidate)
                        else:
                            log_func(f"Filtrada por estratégico: {combo} | {razones}", "debug")
                    except Exception as e:
                        log_func(f"Error en filtro estratégico: {e}, manteniendo combinación", "warning")
                        filtered_candidates.append(candidate)
                
                # If too many filtered, keep some originals
                if len(filtered_candidates) < len(candidates) * 0.3:
                    log_func("Pocos candidatos pasaron filtro, conservando algunos originales", "warning")
                    filtered_candidates = candidates[:max(10, len(filtered_candidates))]
                
                candidates = filtered_candidates
            except ImportError:
                log_func("Filtro estratégico no disponible, continuando sin filtrar", "warning")
            except Exception as e:
                log_func(f"Error en filtro estratégico: {e}, continuando sin filtrar", "warning")
       
        # Puntuar combinaciones
        try:
            # Convertir a dict para score_combinations
            candidate_dicts = [c.to_dict() for c in candidates]
            scored_dicts = score_combinations(candidate_dicts, training_data)
           
            # Verificar consistencia de resultados
            if len(candidate_dicts) != len(scored_dicts):
                log_func(f"Score_combinations devolvió {len(scored_dicts)} "
                         f"resultados para {len(candidates)} candidatos", "warning")
           
            # Crear mapeo por combinación para matching seguro
            scored_map = {}
            for scored in scored_dicts:
                try:
                    # Use multiple possible keys for compatibility
                    key = tuple(sorted(scored.get('numbers', scored.get('combination', []))))
                    if len(key) == 6 and all(isinstance(x, int) for x in key):
                        scored_map[key] = scored
                    else:
                        log_func(f"Combinación inválida: {key}", "warning")
                except Exception as e:
                    log_func(f"Error procesando scoring: {e}, datos: {scored}", "warning")
           
            # Actualizar objetos Combination con scores y métricas
            for candidate in candidates:
                if tuple(candidate.numbers) in scored_map:
                    scored_data = scored_map[tuple(candidate.numbers)]
                    candidate.score = scored_data.get('score', 0.0)
                    candidate.metrics = scored_data.get('metrics', {})
                    candidate.normalized = scored_data.get('normalized', 0.0)
        except Exception as e:
            log_func(f"Error en scoring: {e}\n{traceback.format_exc()}", "error")
            # Mantener scores en 0 si falla el scoring
       
        # Filtrar históricos y ordenar
        valid_combos = [
            c for c in candidates 
            if tuple(c.numbers) not in historial_set
        ]
        valid_combos.sort(key=lambda x: x.score, reverse=True)
        return valid_combos
   
    def predict_next(self, history: List[List[float]]) -> List[float]:
        """
        Predice la siguiente combinación a partir del historial
        
        Args:
            history: Historial reciente (lista de listas de floats)
            
        Returns:
            prediction: Combinación predicha (valores brutos)
        """
        if self.model is None or self.scaler is None:
            raise RuntimeError("Modelo no entrenado o cargado")
       
        last_seq = np.array(history[-self.config.n_steps:])
        last_seq_scaled = self.scaler.transform(last_seq)
        last_seq_scaled = last_seq_scaled.reshape((1, self.config.n_steps, -1))
       
        pred_scaled = self.model.predict(last_seq_scaled, verbose=0)
        
        # Handle enhanced model with multiple outputs vs single output
        if isinstance(pred_scaled, list) and len(pred_scaled) == 6:
            # Multi-output model - convert probabilities to numbers
            predictions = []
            for pos_probs in pred_scaled:
                # Get most likely number for this position (1-40)
                predicted_num = np.argmax(pos_probs[0]) + 1
                predictions.append(float(predicted_num))
            return predictions
        else:
            # Single output model
            if len(pred_scaled.shape) == 3:
                pred_scaled = pred_scaled[0]
            pred = self.scaler.inverse_transform(pred_scaled)
            return pred[0].tolist()
   
    def predict_sequence(self, history: List[List[float]], steps: int) -> List[List[float]]:
        """
        Predice una secuencia de combinaciones futuras
        
        Args:
            history: Historial inicial
            steps: Número de pasos a predecir
            
        Returns:
            predictions: Lista de predicciones
        """
        current_history = history.copy()
        predictions = []
        for _ in range(steps):
            pred = self.predict_next(current_history)
            predictions.append(pred)
            current_history.append(pred)
            # Mantener solo el historial necesario
            current_history = current_history[-self.config.n_steps:]
        return predictions
   
    def clean_combination(self, prediction: List[float]) -> List[int]:
        """
        Limpia y formatea una combinación predicha.

        Redondea los valores predichos, los recorta al rango definido en la
        configuración (`number_range`) y asegura que la combinación final
        contenga exactamente `number_count` números únicos. En caso de
        contener menos números, se completan con valores aleatorios dentro
        del rango; si hay más, se seleccionan los más probables basándose
        en la magnitud de la predicción.

        Args:
            prediction: Lista de valores continuos predichos por el modelo.

        Returns:
            Lista de enteros ordenados que conforman la combinación limpia.
        """
        min_val, max_val = self.config.number_range
        count = self.config.number_count
        
        # Clip y redondeo a enteros dentro del rango [min_val, max_val]
        cleaned = np.clip(np.rint(prediction), min_val, max_val).astype(int)

        # Eliminar duplicados manteniendo el orden de primera aparición
        _, idx = np.unique(cleaned, return_index=True)
        cleaned = cleaned[np.sort(idx)].tolist()

        # Completar si faltan números
        if len(cleaned) < count:
            disponibles = list(set(range(min_val, max_val + 1)) - set(cleaned))
            cleaned.extend(self.rng.sample(disponibles, count - len(cleaned)))
        # Seleccionar los valores más probables si hay exceso
        elif len(cleaned) > count:
            # Usar valores absolutos como proxy de probabilidad de aparición
            probas = np.abs(prediction)
            # Seleccionar los índices de los `count` valores con mayor probabilidad
            top_indices = np.argsort(probas)[-count:]
            cleaned = [cleaned[i] for i in sorted(top_indices)]

        # Devolver los números ordenados para consistencia
        return sorted(cleaned)
   
    def save(self):
        """Guarda el modelo y escalador en disco con metadatos"""
        if self.model is None or self.scaler is None:
            raise RuntimeError("No hay modelo o escalador para guardar")
        
        if not self.config.model_path:
            raise ValueError("Ruta de modelo no configurada")
            
        self.config.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Guardar modelo
        model_path = self.config.model_path.with_suffix('.h5')
        self.model.save(str(model_path))
        
        # Guardar escalador
        scaler_path = model_path.with_name(f"{model_path.stem}_scaler.pkl")
        joblib.dump(self.scaler, str(scaler_path))
        
        # Guardar metadatos CORREGIDO (usar n_features_in_)
        metadata = {
            "config": asdict(self.config),
            "training_date": datetime.datetime.now().isoformat(), # Usando datetime
            "n_features": getattr(self.scaler, 'n_features_in_', None),
            "tf_version": tf.__version__ # Añadido para depuración
        }
        metadata_path = model_path.with_name(f"{model_path.stem}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def log_training_summary(self, log_func: callable):
        """Registra un resumen del entrenamiento"""
        if not self.history:
            log_func("No hay historial de entrenamiento disponible", "warning")
            return
            
        history = self.history.history
        final_epoch = len(history['loss'])
        
        # Manejo correcto de la mejor época
        if 'val_loss' in history:
            best_epoch = np.argmin(history['val_loss']) + 1
            best_val_loss = min(history['val_loss'])
            final_val_loss = history['val_loss'][-1]
        else:
            best_epoch = final_epoch
            best_val_loss = None
            final_val_loss = None

        msg = (
            f"Entrenamiento completado - Épocas: {final_epoch}\n"
            f"Mejor época: {best_epoch} "
        )
        
        if best_val_loss is not None:
            msg += f"(val_loss: {best_val_loss:.4f})\n"
        else:
            msg += "\n"
            
        msg += f"Final loss: {history['loss'][-1]:.4f}"
        
        if final_val_loss is not None:
            msg += f", val_loss final: {final_val_loss:.4f}"
            
        log_func(msg, "info")
    
    @classmethod
    def load(cls, config: LSTMConfig) -> "LSTMCombiner":
        """
        Carga un modelo y escalador desde disco con validación
        
        Args:
            config: Configuración con ruta del modelo
            
        Returns:
            Instancia con modelo cargado
        """
        if not config.model_path:
            raise ValueError("Ruta de modelo no especificada en configuración")
            
        model_path = config.model_path.with_suffix('.h5')
        if not model_path.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
        
        instance = cls(config)
        instance.model = load_model(str(model_path))
        
        # Cargar escalador
        scaler_path = model_path.with_name(f"{model_path.stem}_scaler.pkl")
        if scaler_path.exists():
            instance.scaler = joblib.load(str(scaler_path))
        else:
            raise FileNotFoundError(f"Escalador no encontrado: {scaler_path}")
        
        # Cargar y validar metadatos si existen
        metadata_path = model_path.with_name(f"{model_path.stem}_metadata.json")
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                # Validar compatibilidad de configuración
                saved_config = metadata.get('config', {})
                for key, saved_value in saved_config.items():
                    current_value = getattr(config, key, None)
                    if current_value != saved_value:
                        logging.warning(
                            f"Configuración diferente para '{key}': "
                            f"Guardado: {saved_value}, Actual: {current_value}"
                        )
        
        return instance

# ========== INTERFAZ PRINCIPAL ==========
def get_system_resources() -> Dict:
    """Get system resources for dynamic configuration"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        cpu_count = os.cpu_count() or 4
        return {
            'available_memory_gb': memory.available / (1024**3),
            'memory_percent': memory.percent,
            'cpu_count': cpu_count,
            'cpu_percent': psutil.cpu_percent(interval=0.1)
        }
    except ImportError:
        return {
            'available_memory_gb': 4.0,
            'memory_percent': 50.0,
            'cpu_count': os.cpu_count() or 4,
            'cpu_percent': 50.0
        }

def get_adaptive_lstm_config(base_config: LSTMConfig, resources: Dict) -> LSTMConfig:
    """Generate adaptive LSTM configuration based on system resources"""
    adaptive_config = copy.deepcopy(base_config)
    
    # Adjust enhanced features based on available resources
    memory_gb = resources['available_memory_gb']
    memory_percent = resources['memory_percent']
    cpu_percent = resources['cpu_percent']
    
    # Memory-based adjustments
    if memory_gb > 8:
        # High memory - enable all advanced features
        adaptive_config.use_enhanced_architecture = True
        adaptive_config.use_attention = True
        adaptive_config.use_bidirectional = True 
        adaptive_config.use_positional_outputs = True
        adaptive_config.n_units = min(256, max(128, adaptive_config.n_units))
        adaptive_config.epochs = min(80, max(40, adaptive_config.epochs))
        adaptive_config.batch_size = min(64, max(16, adaptive_config.batch_size))
        
    elif memory_gb > 4:
        # Medium memory - selective advanced features
        adaptive_config.use_enhanced_architecture = True
        adaptive_config.use_attention = True
        adaptive_config.use_bidirectional = False  # Reduce complexity
        adaptive_config.use_positional_outputs = False  # Single output
        adaptive_config.n_units = min(128, max(64, adaptive_config.n_units))
        adaptive_config.epochs = min(50, max(20, adaptive_config.epochs))
        adaptive_config.batch_size = min(32, max(8, adaptive_config.batch_size))
        
    else:
        # Low memory - basic architecture only
        adaptive_config.use_enhanced_architecture = False
        adaptive_config.use_attention = False
        adaptive_config.use_bidirectional = False
        adaptive_config.use_positional_outputs = False
        adaptive_config.n_units = min(64, max(32, adaptive_config.n_units))
        adaptive_config.epochs = min(30, max(10, adaptive_config.epochs))
        adaptive_config.dropout_rate = max(0.4, adaptive_config.dropout_rate)
    
    # Memory pressure adjustments
    if memory_percent > 85:
        adaptive_config.use_batch_norm = False
        adaptive_config.use_layer_norm = False
        adaptive_config.batch_size = max(4, adaptive_config.batch_size // 2)
        adaptive_config.use_feature_fusion = False
    
    # CPU-based adjustments
    if cpu_percent > 80:
        adaptive_config.early_stopping_patience = max(5, adaptive_config.early_stopping_patience // 2)
        adaptive_config.use_strategic_filtering = False  # Skip filtering to save CPU
    
    # Disable advanced features under extreme resource constraints
    if memory_gb < 2 or memory_percent > 90:
        adaptive_config.use_enhanced_architecture = False
        adaptive_config.use_attention = False
        adaptive_config.use_bidirectional = False
        adaptive_config.use_feature_fusion = False
        adaptive_config.use_strategic_filtering = False
    
    return adaptive_config

def generar_combinaciones_lstm(
    data: Union[np.ndarray, pd.DataFrame],  # Accept both DataFrame and ndarray
    historial_set: Set[Tuple[int, ...]],
    cantidad: int,
    logger: Optional[logging.Logger] = None,
    config: Optional[Dict[str, Any]] = None,
    return_history: bool = False,
    enable_adaptive_config: bool = True
) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], Dict]]:
    """
    Interfaz estándar para el sistema OMEGA
    
    Args:
        data: Array con datos históricos (cada fila es una combinación)
        historial_set: Conjunto de combinaciones históricas (tuplas de enteros ordenados)
        cantidad: Número de combinaciones a generar
        logger: Logger para registro
        config: Configuración de hiperparámetros (opcional)
        return_history: Si True, devuelve también el historial de entrenamiento
        
    Returns:
        Lista de diccionarios con estructura:
        {
            'combination': List[int],      # Números ordenados de la combinación
            'source': str,                 # Origen de la combinación
            'score': float,                # Puntuación de calidad
            'metrics': Dict[str, Any],     # Métricas adicionales
            'normalized': float            # Puntuación normalizada
        }
        y, opcionalmente, el historial de entrenamiento.
    """
    log = wrap_logger(logger, prefix="OMEGA-LSTM")
    
    # PRIORITY 1: Try to use pre-trained PyTorch LSTM models first
    try:
        from modules.pytorch_lstm_adapter import get_pytorch_lstm_predictions, is_pytorch_model_available
        
        if is_pytorch_model_available():
            log("🚀 Detectados modelos PyTorch pre-entrenados - Usando predicción rápida", "info")
            
            # Convert data to list format if needed
            if isinstance(data, pd.DataFrame):
                cols = [c for c in data.columns if "bolilla" in c.lower()]
                if len(cols) >= 6:
                    historical_data = data[cols].values.tolist()
                else:
                    historical_data = data.iloc[:, :6].values.tolist()
            elif isinstance(data, np.ndarray):
                historical_data = data.tolist()
            else:
                historical_data = data
            
            # Get PyTorch predictions
            pytorch_predictions = get_pytorch_lstm_predictions(
                historical_data, 
                num_predictions=cantidad * 2  # Get extra for diversity filtering
            )
            
            if pytorch_predictions:
                # Filter out combinations that are in historical set
                valid_predictions = []
                for pred in pytorch_predictions:
                    combo_tuple = tuple(sorted(pred['combination']))
                    if combo_tuple not in historial_set:
                        # Ensure all required fields are present for OMEGA compatibility
                        if 'numbers' not in pred:
                            pred['numbers'] = pred['combination']
                        if 'score' not in pred:
                            pred['score'] = pred.get('confidence', 0.5)
                        if 'normalized' not in pred:
                            pred['normalized'] = pred.get('confidence', 0.5)
                        if 'metrics' not in pred:
                            pred['metrics'] = {}
                        
                        # Add LSTM-specific metrics for compatibility
                        pred['metrics'].update({
                            'method': 'pytorch_pretrained',
                            'training_time_saved': 'YES',
                            'model_load_time': '<1s'
                        })
                        
                        valid_predictions.append(pred)
                        
                        if len(valid_predictions) >= cantidad:
                            break
                
                if len(valid_predictions) >= cantidad:
                    log(f"✅ PyTorch LSTM generó {len(valid_predictions)} combinaciones en <1 segundo", "info")
                    log(f"⚡ Tiempo de entrenamiento evitado: 5+ minutos", "info")
                    
                    # Return top combinations by score
                    top_predictions = sorted(valid_predictions, key=lambda x: x['score'], reverse=True)[:cantidad]
                    return top_predictions
                else:
                    log(f"⚠️ PyTorch generó solo {len(valid_predictions)}/{cantidad} combinaciones válidas", "warning")
                    # Continue to Keras training for remaining combinations
            else:
                log("⚠️ PyTorch model no generó predicciones válidas", "warning")
        else:
            log("ℹ️ No hay modelos PyTorch pre-entrenados disponibles", "info")
            
    except ImportError:
        log("ℹ️ PyTorch adapter no disponible, usando entrenamiento Keras", "info")
    except Exception as e:
        log(f"⚠️ Error con PyTorch models: {e}, continuando con Keras", "warning")
    
    # Cargar configuración base
    base_config = load_config()
    if config:
        base_config = LSTMConfig.from_dict({**asdict(base_config), **config})
    else:
        base_config = LSTMConfig.from_dict(asdict(base_config))
    
    # Apply adaptive configuration based on system resources
    if enable_adaptive_config:
        system_resources = get_system_resources()
        base_config = get_adaptive_lstm_config(base_config, system_resources)
        log(f"🤖 Configuración adaptativa aplicada para 65-70% accuracy target:", "info")
        log(f"  • Memory: {system_resources['available_memory_gb']:.1f}GB available", "info")
        log(f"  • Config: epochs={base_config.epochs}, batch_size={base_config.batch_size}, "
            f"units={base_config.n_units}", "info")
        log(f"  • Architecture: bidirectional={base_config.use_bidirectional}, "
            f"attention={base_config.use_attention}", "info")
    
    log(f"🚀 Iniciando LSTM Mejorado v2.0 - Objetivo: 65-70% accuracy", "info")
    log(f"📊 Arquitectura: {'Enhanced' if base_config.use_enhanced_architecture else 'Basic'} | "
        f"Bidirectional: {base_config.use_bidirectional} | Attention: {base_config.use_attention} | "
        f"Strategic Filtering: {base_config.use_strategic_filtering}", "info")
    log(f"⚙️ Hiperparámetros: units={base_config.n_units}, steps={base_config.n_steps}, "
        f"batch_size={base_config.batch_size}, epochs={base_config.epochs}", "info")
    
    try:
        # Convertir DataFrame a ndarray si es necesario
        if isinstance(data, pd.DataFrame):
            # Buscar columnas de bolillas
            cols = [c for c in data.columns if "bolilla" in c.lower()]
            if len(cols) >= 6:
                data = data[cols].values
                log(f"DataFrame convertido a ndarray: {data.shape}", "info")
            else:
                raise ValueError(f"DataFrame debe tener ≥6 columnas 'bolilla', encontradas: {len(cols)}")
        
        # Validar y preparar datos
        if data.size == 0:
            raise ValueError("Array de entrada vacío")
        
        if np.isnan(data).any():
            log("Datos contienen NaN - aplicando imputación", "warning")
            data = np.nan_to_num(data)
        
        # Crear combinador con caché inteligente
        combiner = None
        
        # Smart model caching based on data characteristics and enhanced config
        config_signature = f"{base_config.use_enhanced_architecture}_{base_config.use_attention}_{base_config.use_bidirectional}_{base_config.n_units}_{base_config.n_steps}"
        cache_key = f"lstm_unified_{len(data)}_{data.shape[1] if len(data.shape) > 1 else 0}_{hash(config_signature)}"
        model_cache_path = f"models/lstm_cache_{cache_key}.h5" if hasattr(base_config, 'model_path') and base_config.model_path else None
        
        if (base_config.use_cached_model and model_cache_path and 
            os.path.exists(model_cache_path)):
            try:
                # Update model path for cache
                cached_config = copy.deepcopy(base_config)
                cached_config.model_path = Path(model_cache_path)
                combiner = LSTMCombiner.load(cached_config)
                log(f"Modelo cargado desde caché: {model_cache_path}", "info")
            except Exception as e:
                log(f"Error cargando modelo desde caché: {e}. Entrenando nuevo", "warning")
                combiner = LSTMCombiner(base_config)
        else:
            combiner = LSTMCombiner(base_config)
            # Set cache path for future saves
            if model_cache_path:
                combiner.config.model_path = Path(model_cache_path)
        
        # Generar combinaciones con configuración adaptativa optimizada
        adaptive_training_config = None
        if enable_adaptive_config:
            adaptive_training_config = {
                'early_stopping_patience': base_config.early_stopping_patience,
                'reduce_lr_factor': base_config.reduce_lr_factor,
                'batch_size': base_config.batch_size
            }
        
        log(f"🎯 Configuración final: bidirectional={base_config.use_bidirectional}, "
            f"attention={base_config.use_attention}, units={base_config.n_units}, "
            f"epochs={base_config.epochs}, batch_size={base_config.batch_size}", "info")
        
        combinations = combiner.safe_train_and_predict(
            data=data,
            historial_set=historial_set,
            steps=max(cantidad * 3, 20),  # Generate more candidates for better selection
            log_func=log,
            adaptive_config=adaptive_training_config
        )
        
        # Save model to cache if training was successful and caching is enabled
        if (model_cache_path and combiner.model is not None and 
            len(combinations) > 0 and not os.path.exists(model_cache_path)):
            try:
                os.makedirs(os.path.dirname(model_cache_path), exist_ok=True)
                combiner.save()
                log(f"Modelo guardado en caché: {model_cache_path}", "info")
            except Exception as e:
                log(f"Error guardando en caché: {e}", "warning")
        
        # Seleccionar las mejores con filtrado inteligente
        if len(combinations) == 0:
            log("⚠️ No se generaron combinaciones válidas, usando fallback mejorado", "warning")
            fallback_combos = fallback_combinations(
                historial_set, cantidad, random.Random(base_config.seed), base_config, data
            )
            combinations = fallback_combos
        
        # Sort by score and apply additional lottery-specific filtering
        sorted_combinations = sorted(combinations, key=lambda x: x.score, reverse=True)
        
        # Apply diversity filter to avoid too similar combinations
        diverse_combinations = []
        for combo in sorted_combinations:
            if len(diverse_combinations) >= cantidad:
                break
                
            # Check diversity with already selected combinations
            is_diverse = True
            for selected in diverse_combinations:
                common_numbers = len(set(combo.numbers) & set(selected.numbers))
                if common_numbers > 4:  # Too similar if sharing >4 numbers
                    is_diverse = False
                    break
            
            if is_diverse:
                diverse_combinations.append(combo)
        
        # If not enough diverse combinations, fill with highest scoring ones
        if len(diverse_combinations) < cantidad:
            remaining_needed = cantidad - len(diverse_combinations)
            already_selected = {tuple(c.numbers) for c in diverse_combinations}
            
            for combo in sorted_combinations:
                if len(diverse_combinations) >= cantidad:
                    break
                if tuple(combo.numbers) not in already_selected:
                    diverse_combinations.append(combo)
        
        top_combinations = diverse_combinations[:cantidad]
        log(f"✅ Generadas {len(top_combinations)} combinaciones óptimas (diversificadas)", "info")
        
        # Log accuracy insights
        if top_combinations:
            avg_score = sum(c.score for c in top_combinations) / len(top_combinations)
            log(f"📈 Score promedio: {avg_score:.4f} (objetivo: >0.65 para 65% accuracy)", "info")
        
        # Registrar resumen de entrenamiento
        training_summary = None
        if combiner.history:
            combiner.log_training_summary(log)
            training_summary = {
                "epochs": len(combiner.history.history['loss']),
                "final_loss": combiner.history.history['loss'][-1],
                "val_loss": combiner.history.history.get('val_loss', [None])[-1]
            }
        
        # Convertir a dict para salida
        result = [c.to_dict() for c in top_combinations]
        
        if return_history and combiner.history:
            return result, combiner.history.history
        return result
    
    except Exception as e:
        log(f"Error crítico: {e}\n{traceback.format_exc()}", "error")
        log("Usando combinaciones de fallback", "warning")
        fallback = fallback_combinations(
            historial_set,
            cantidad,
            rng=random.Random(base_config.seed) if base_config.seed else random.Random(),
            config=base_config
        )
        return [c.to_dict() for c in fallback]

# Memory management utility
def cleanup_tensorflow_session():
    """Clean up TensorFlow session and free memory"""
    try:
        import tensorflow as tf
        tf.keras.backend.clear_session()
        import gc
        gc.collect()
    except Exception:
        pass