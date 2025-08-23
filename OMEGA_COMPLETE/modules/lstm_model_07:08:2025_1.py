# OMEGA_PRO_AI_v10.1/modules/lstm_model.py Red LSTM para secuencias temporales – OMEGA PRO AI (Versión Final) – Versión Corregida

import logging
import os
import json
import random
import traceback
import datetime
from dataclasses import dataclass, field, asdict, fields
from pathlib import Path
from typing import Optional, List, Dict, Set, Tuple, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed  # No usado, pero mantenido por compatibilidad

# Third-party imports
import numpy as np
import tensorflow as tf
import joblib
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau,
    ModelCheckpoint, TensorBoard
)
from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator

# Local modules
from modules.score_dynamics import score_combinations

# ========== TIPOS DE DATOS ==========
@dataclass
class Combination:
    """Representa una combinación de números con metadatos"""
    numbers: List[int] # Cambiado a List para evitar tuples en scoring
    source: str
    score: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    normalized: float = 0.0

    def __post_init__(self):
        """Valida la combinación después de la inicialización"""
        # Convertir tuples a listas si necesario
        if isinstance(self.numbers, tuple):
            self.numbers = list(self.numbers)
           
        if len(self.numbers) != 6:
            raise ValueError(f"Combinación debe tener 6 números, recibió {len(self.numbers)}")
       
        # Verificar duplicados
        if len(set(self.numbers)) != 6:
            raise ValueError(f"Combinación contiene números duplicados: {self.numbers}")
       
        if not all(1 <= num <= 40 for num in self.numbers):
            invalid = [num for num in self.numbers if not 1 <= num <= 40]
            raise ValueError(f"Números fuera de rango (1-40): {invalid}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "combination": self.numbers, # Siempre list for scoring
            "source": self.source,
            "score": self.score,
            "metrics": self.metrics,
            "normalized": self.normalized
        }

@dataclass
class LSTMConfig:
    """Contenedor de configuración para el modelo LSTM"""
    n_steps: int = 5
    n_units: int = 64
    dropout_rate: float = 0.3
    learning_rate: float = 0.001
    seed: Optional[int] = None
    model_path: Optional[Path] = None
    epochs: int = 100
    batch_size: int = 32
    validation_split: float = 0.1
    use_cached_model: bool = False
    tensorboard_logdir: Optional[Path] = None

    def __post_init__(self):
        """Valida los hiperparámetros después de la inicialización"""
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

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "LSTMConfig":
        """Crea una configuración desde un diccionario con conversión de tipos"""
        valid_keys = {f.name for f in fields(cls)}
        filtered = {}
       
        for key, value in config_dict.items():
            if key in valid_keys:
                if key in {'model_path', 'tensorboard_logdir'} and value:
                    filtered[key] = Path(value)
                elif key in {'n_steps', 'n_units', 'epochs', 'batch_size'} and isinstance(value, str):
                    filtered[key] = int(value)
                elif key in {'dropout_rate', 'learning_rate', 'validation_split'} and isinstance(value, str):
                    filtered[key] = float(value)
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
        getattr(log, level)(formatted_msg)
   
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
    rng: random.Random
) -> List[Combination]:
    results = []
    while len(results) < cantidad:
        # CORRECCIÓN: Paréntesis faltante añadido
        combo = tuple(sorted(rng.sample(range(1, 41), 6)))
        if combo not in historial_set:
            results.append(Combination(
                numbers=list(combo),
                source="lstm_fallback"
            ))
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
    
    def _validate_data(self, data: np.ndarray):
        """Valida los datos antes del entrenamiento"""
        if data.size == 0:
            raise ValueError("Datos de entrenamiento vacíos")
            
        if data.ndim != 2:
            raise ValueError(f"Se esperaba matriz 2D, se recibió {data.ndim}D")
            
        if data.shape[1] != 6:
            logging.warning(
                f"Se esperaban 6 características, se recibieron {data.shape[1]}. "
                "El modelo puede no funcionar correctamente."
            )
            
        if np.isnan(data).any():
            raise ValueError("Los datos contienen valores NaN")
            
        n_samples = data.shape[0]
        if n_samples < self.config.n_steps + 2:  # Actualizado a +2
            raise ValueError(
                f"Insuficientes datos: {n_samples} muestras. "
                f"Se necesitan ≥{self.config.n_steps+2} para n_steps={self.config.n_steps}"
            )
    
    def build_model(self, n_features: int) -> Sequential:
        """Construye el modelo LSTM con los parámetros configurados"""
        model = Sequential([
            LSTM(
                self.config.n_units, 
                return_sequences=True, 
                input_shape=(self.config.n_steps, n_features)
            ),
            Dropout(self.config.dropout_rate),
            LSTM(self.config.n_units),
            Dropout(self.config.dropout_rate),
            Dense(n_features, activation='linear')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.config.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        return model
    
    def train(self, data: np.ndarray, log_func: callable) -> tf.keras.callbacks.History:
        """
        Entrena el modelo LSTM con los datos proporcionados
        
        Args:
            data: Datos de entrenamiento
            log_func: Función para logging
            
        Returns:
            history: Objeto con historial de entrenamiento
        """
        # Validar datos
        self._validate_data(data)
        
        # Preprocesamiento y escalado
        self.scaler = MinMaxScaler()
        data_scaled = self.scaler.fit_transform(data)

        n_samples = len(data_scaled)
        n_steps = self.config.n_steps
        val_split = self.config.validation_split

        # Calcular índice de split considerando ventanas temporales
        split_index = int((n_samples - n_steps) * (1 - val_split)) + n_steps
        split_index = max(split_index, n_steps + 1)  # Garantizar al menos 1 ventana en train
        split_index = min(split_index, n_samples - 1)  # Garantizar al menos 1 ventana en val

        # Crear generadores para entrenamiento y validación
        train_generator = TimeseriesGenerator(
            data_scaled, 
            data_scaled,
            length=n_steps,
            batch_size=self.config.batch_size,
            start_index=0,
            end_index=split_index - 1
        )
        
        val_generator = TimeseriesGenerator(
            data_scaled, 
            data_scaled,
            length=n_steps,
            batch_size=self.config.batch_size,
            start_index=split_index,
            end_index=n_samples - 1
        )
        
        log_func(f"Ventanas entrenamiento: {len(train_generator)}, "
                f"Ventanas validación: {len(val_generator)}", "debug")
        
        n_features = data_scaled.shape[1]
        
        # Construir modelo
        self.model = self.build_model(n_features)
        
        # Callbacks por defecto
        callbacks = [
            EarlyStopping(
                monitor='val_loss', 
                patience=15, 
                restore_best_weights=True, 
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss', 
                factor=0.2, 
                patience=5, 
                min_lr=1e-6, 
                verbose=1
            )
        ]
        
        # Callbacks adicionales
        if self.config.tensorboard_logdir:
            self.config.tensorboard_logdir.mkdir(parents=True, exist_ok=True)
            callbacks.append(TensorBoard(
                log_dir=self.config.tensorboard_logdir, 
                histogram_freq=1
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
        
        # Entrenamiento con generadores (shuffle=False para series temporales)
        self.history = self.model.fit(
            train_generator,
            epochs=self.config.epochs,
            validation_data=val_generator,
            verbose=1,
            callbacks=callbacks,
            shuffle=False  # Deshabilitar shuffle para series temporales
        )
        return self.history
    
    def safe_train_and_predict(
        self, 
        data: np.ndarray,
        historial_set: Set[Tuple[int, ...]],
        steps: int,
        log_func: callable
    ) -> List[Combination]:
        """Entrena y predice con manejo de errores integrado"""
        try:
            # Entrenar y predecir
            self.train(data, log_func) # Pasar log_func a train
            history_list = data.tolist()
            predictions = self.predict_sequence(history_list, steps)
           
            # Procesar y puntuar combinaciones
            combos = [self.clean_combination(pred) for pred in predictions]
            return self.process_combinations(combos, historial_set, data, log_func)
           
        except Exception as e:
            log_func(f"Error en LSTM: {e}\n{traceback.format_exc()}", "error")
            return fallback_combinations(historial_set, steps, self.rng)
   
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
                    key = tuple(scored['numbers'])
                    scored_map[key] = scored
                except KeyError:
                    log_func(f"Elemento de scoring inválido: {scored}", "warning")
           
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
        Limpia y formatea una combinación predicha
        
        Args:
            prediction: Valores brutos de predicción
            
        Returns:
            combo: Combinación limpia de 6 números únicos
        """
        # Clip y redondeo a enteros
        cleaned = np.clip(np.rint(prediction), 1, 40).astype(int)
       
        # Eliminar duplicados manteniendo orden de primera aparición
        _, idx = np.unique(cleaned, return_index=True)
        cleaned = cleaned[np.sort(idx)].tolist()
       
        # Completar si faltan números
        if len(cleaned) < 6:
            disponibles = list(set(range(1, 41)) - set(cleaned))
            cleaned.extend(self.rng.sample(disponibles, 6 - len(cleaned)))
        # Seleccionar los 6 valores más probables si hay exceso
        elif len(cleaned) > 6:
            # Usar valores absolutos como proxy de probabilidad
            probas = np.abs(prediction)
            # Seleccionar los 6 valores con mayor probabilidad
            top_indices = np.argsort(probas)[-6:]
            cleaned = [cleaned[i] for i in sorted(top_indices)]
           
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
def generar_combinaciones_lstm(
    data: np.ndarray,  # Cambiado a np.ndarray para flexibilidad
    historial_set: Set[Tuple[int, ...]],
    cantidad: int,
    logger: Optional[logging.Logger] = None,
    config: Optional[Dict[str, Any]] = None,
    return_history: bool = False
) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], Dict]]:
    """
    Interfaz estándar para el sistema OMEGA
    
    Args:
        data: Array con datos históricos (cada fila es una combinación)
        historial_set: Conjunto de combinaciones históricas (tuplas de 6 enteros ordenados)
        cantidad: Número de combinaciones a generar
        logger: Logger para registro
        config: Configuración de hiperparámetros (opcional)
        return_history: Si True, devuelve también el historial de entrenamiento
        
    Returns:
        Lista de diccionarios con estructura:
        {
            'numbers': Tuple[int, ...],  # 6 números ordenados (1-40)
            'source': str,               # Origen de la combinación
            'score': float,              # Puntuación de calidad
            'metrics': Dict[str, Any],   # Métricas adicionales
            'normalized': float          # Puntuación normalizada
        }
        Y opcionalmente el historial de entrenamiento
    """
    log = wrap_logger(logger, prefix="OMEGA-LSTM")
    
    # Cargar configuración
    base_config = load_config()
    if config:
        base_config = LSTMConfig.from_dict({**asdict(base_config), **config})
    else:
        base_config = LSTMConfig.from_dict(asdict(base_config))
    
    log(f"Iniciando generación LSTM con config: {base_config}", "info")
    
    try:
        # Validar y preparar datos
        if data.size == 0:
            raise ValueError("Array de entrada vacío")
        
        if np.isnan(data).any():
            log("Datos contienen NaN - aplicando imputación", "warning")
            data = np.nan_to_num(data)
        
        # Crear combinador
        combiner = None
        if base_config.use_cached_model and base_config.model_path:
            try:
                combiner = LSTMCombiner.load(base_config)
                log("Modelo cargado desde caché", "info")
            except Exception as e:
                log(f"Error cargando modelo: {e}. Entrenando nuevo", "warning")
                combiner = LSTMCombiner(base_config)
        else:
            combiner = LSTMCombiner(base_config)
        
        # Generar combinaciones
        combinations = combiner.safe_train_and_predict(
            data=data,
            historial_set=historial_set,
            steps=cantidad * 2,  # Generar extras para filtrar
            log_func=log
        )
        
        # Seleccionar las mejores
        top_combinations = sorted(combinations, key=lambda x: x.score, reverse=True)[:cantidad]
        log(f"Generadas {len(top_combinations)} combinaciones válidas", "info")
        
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
            rng=random.Random(base_config.seed) if base_config.seed else random.Random()
        )
        return [c.to_dict() for c in fallback]