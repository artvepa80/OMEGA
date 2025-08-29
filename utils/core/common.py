# utils/common.py - Módulo común centralizado para OMEGA PRO AI v12.4
"""
Módulo común que centraliza funciones y validaciones compartidas
para evitar dependencias circulares entre módulos del sistema.
"""

import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import pandas as pd
import numpy as np
import dotenv  # Nueva: para cargar .env

dotenv.load_dotenv()  # Cargar variables de entorno para config flexible

# ═══════════════════════════════════════════════════════════════════
# VALIDACIONES CENTRALIZADAS
# ═══════════════════════════════════════════════════════════════════

def validate_combination(combination: Union[List[int], Tuple[int, ...], np.ndarray]) -> bool:
    """
    Validación centralizada de combinaciones.
    
    Args:
        combination: Lista, tupla o array de números
        
    Returns:
        bool: True si la combinación es válida
    """
    try:
        if combination is None:
            return False
            
        # Convertir a lista si es necesario
        if isinstance(combination, (np.ndarray, tuple)):
            combination = list(combination)
        elif not isinstance(combination, list):
            return False
            
        # Convertir a enteros
        try:
            nums = [int(n) for n in combination]
        except (ValueError, TypeError):
            return False
            
        # Obtener rangos de configuración
        min_val = config.get("combo_range_min", 1)
        max_val = config.get("combo_range_max", 40)
        combo_length = config.get("combo_length", 6)
            
        # Validaciones específicas
        if len(nums) != combo_length:
            return False
            
        if len(set(nums)) != combo_length:  # No duplicados
            return False
            
        if not all(min_val <= n <= max_val for n in nums):  # Rango válido
            return False
            
        return True
        
    except Exception:
        return False

def clean_combination(combination: Any, logger: Optional[logging.Logger] = None) -> Optional[List[int]]:
    """
    Limpia y valida una combinación, retornando None si es inválida.
    
    Args:
        combination: Combinación a limpiar
        logger: Logger opcional para debug
        
    Returns:
        List[int] | None: Combinación limpia o None si es inválida
    """
    try:
        if combination is None:
            return None
            
        # Manejar diferentes tipos de input
        if isinstance(combination, str):
            # Parsear string JSON o formato "[1,2,3,4,5,6]"
            combination = combination.strip('[]')
            nums = [int(x.strip()) for x in combination.split(',')]
        elif isinstance(combination, (list, tuple, np.ndarray)):
            nums = [int(x) for x in combination]
        else:
            return None
            
        # Ordenar y validar
        clean_nums = sorted(list(set(nums)))
        
        if validate_combination(clean_nums):
            return clean_nums
        else:
            if logger:
                logger.warning(f"⚠️ Combinación inválida descartada: {combination}")
            return None
            
    except Exception as e:
        if logger:
            logger.error(f"🚨 Error limpiando combinación {combination}: {e}")
        return None

def clean_historial_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpieza robusta y centralizada del DataFrame histórico.
    Ahora usa rangos configurables y mejora manejo de datos faltantes.
    """
    # Obtener valores de configuración
    min_val = config.get("combo_range_min", 1)
    max_val = config.get("combo_range_max", 40)
    combo_length = config.get("combo_length", 6)
    
    if df is None or df.empty:
        # Retornar DataFrame dummy usando rangos configurados
        return pd.DataFrame({
            f'B{i}': np.random.randint(min_val, max_val + 1, size=100)
            for i in range(1, combo_length + 1)
        })
    
    try:
        # 1. Eliminar duplicados completos
        df = df.drop_duplicates().reset_index(drop=True)
        
        # 2. Identificar columnas de bolillas
        ball_cols = []
        for col in df.columns:
            if any(pattern in col.lower() for pattern in ['bolilla', 'ball', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6']):
                ball_cols.append(col)
        
        # Si no hay columnas identificables, usar las primeras 6 numéricas
        if len(ball_cols) < combo_length:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            ball_cols = numeric_cols[:combo_length] if len(numeric_cols) >= combo_length else ball_cols
        
        if len(ball_cols) < combo_length:
            raise ValueError("No hay suficientes columnas de bolillas")
        
        # 3. Tomar solo las columnas de bolillas necesarias
        df = df[ball_cols[:combo_length]].copy()
        
        # 4. Renombrar columnas de forma estándar
        df.columns = [f'B{i}' for i in range(1, combo_length + 1)]
        
        # 5. Conversión a numérico con manejo de errores
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 6. Eliminar filas con demasiados NaN
        df = df.dropna(thresh=combo_length-2)  # Al menos N-2 valores válidos por fila
        
        # 7. Imputar NaN restantes con valores aleatorios válidos
        for col in df.columns:
            mask = df[col].isna()
            if mask.any():
                # Generar valores aleatorios únicos para cada fila
                for idx in df[mask].index:
                    existing = df.loc[idx].dropna().astype(int).values
                    available = [x for x in range(min_val, max_val + 1) if x not in existing]
                    if available:
                        df.loc[idx, col] = np.random.choice(available)
                    else:
                        df.loc[idx, col] = np.random.randint(min_val, max_val + 1)
        
        # 8. Asegurar valores en rango configurado
        df = df.clip(min_val, max_val)
        
        # 9. Convertir a enteros
        df = df.round().astype(int)
        
        # 10. Eliminar filas con duplicados internos
        def has_duplicates(row):
            return len(set(row)) != len(row)
        
        mask = ~df.apply(has_duplicates, axis=1)
        df = df[mask].reset_index(drop=True)
        
        # 11. Si quedó muy pequeño, duplicar algunas filas con variación
        if len(df) < 10:
            while len(df) < 50:
                # Duplicar una fila aleatoria con pequeña variación
                idx = np.random.randint(0, len(df))
                row = df.iloc[idx].copy()
                # Cambiar 1-2 números aleatoriamente
                for _ in range(np.random.randint(1, 3)):
                    col = np.random.choice(df.columns)
                    row[col] = np.random.randint(min_val, max_val + 1)
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        return df
        
    except Exception as e:
        logging.error(f"🚨 Error en limpieza de historial: {e}")
        # Fallback: DataFrame dummy con rangos configurados
        return pd.DataFrame({
            f'B{i}': np.random.randint(min_val, max_val + 1, size=100) 
            for i in range(1, combo_length + 1)
        })

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN CENTRALIZADA
# ═══════════════════════════════════════════════════════════════════

class OmegaConfig:
    """Gestión centralizada de configuración con soporte para .env"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OmegaConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.reload_config()
    
    def reload_config(self):
        """Recarga la configuración desde archivos JSON y variables de entorno."""
        self._config = {}
        
        # Configuración base
        base_config = {
            "app_name": "OMEGA PRO AI",
            "app_version": "v12.4",
            "combo_length": 6,
            "combo_range_min": 1,
            "combo_range_max": 40,
            "max_combinations": 500,
            "memory_limit_mb": 1000,
            "default_data_paths": [
                "data/historial_kabala_github.csv",
                "backup/historial_kabala_github.csv"
            ],
            "svi_profiles": {
                "default": {"prediction_weight": 0.7, "svi_weight": 0.3},
                "conservative": {"prediction_weight": 0.8, "svi_weight": 0.2},
                "aggressive": {"prediction_weight": 0.6, "svi_weight": 0.4}
            },
            "model_weights": {
                "consensus": 1.0,
                "lstm_v2": 1.0,
                "montecarlo": 1.0,
                "apriori": 1.0,
                "transformer_deep": 1.0,
                "clustering": 1.0,
                "genetico": 1.0,
                "ghost_rng": 1.2,
                "inverse_mining": 1.0
            },
            "security": {
                "max_file_size_mb": 100,
                "allowed_extensions": [".csv", ".json"],
                "sanitize_paths": True
            },
            "performance": {
                "enable_multiprocessing": True,
                "max_workers": 4,
                "chunk_size": 1000,
                "memory_threshold": 0.8
            }
        }
        
        # Cargar desde archivos si existen
        config_files = [
            "config/omega_config.json",
            "config/viabilidad.json",
            "config/pesos_modelos.json"
        ]
        
        for config_file in config_files:
            try:
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        file_config = json.load(f)
                    self._merge_config(base_config, file_config)
            except Exception as e:
                logging.warning(f"⚠️ Error cargando {config_file}: {e}")
        
        # Sobrescribir con variables de entorno (OMEGA_*)
        for key in os.environ:
            if key.startswith('OMEGA_'):
                config_key = key[6:].lower()  # Remover prefijo OMEGA_
                self.set(config_key, self._convert_env_value(os.environ[key]))
        
        self._config = base_config
    
    def _convert_env_value(self, value: str) -> Any:
        """Convierte valores de entorno a tipos de Python apropiados."""
        try:
            # Intenta convertir a número
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Manejo de booleanos
        if value.lower() in ('true', 'yes', 'on'):
            return True
        if value.lower() in ('false', 'no', 'off'):
            return False
        
        # Manejo de listas/diccionarios
        if value.startswith(('{', '[')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        return value
    
    def _merge_config(self, base: dict, override: dict):
        """Fusiona configuraciones recursivamente."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración usando notación de punto."""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Establece un valor de configuración usando notación de punto."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self, filepath: str = "config/omega_config.json"):
        """Guarda la configuración actual a un archivo."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"🚨 Error guardando configuración: {e}")

# Instancia global singleton
config = OmegaConfig()

# ═══════════════════════════════════════════════════════════════════
# LOGGING CENTRALIZADO
# ═══════════════════════════════════════════════════════════════════

def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5
) -> logging.Logger:
    """
    Configuración estandarizada de logging para todos los módulos.
    
    Args:
        name: Nombre del logger
        level: Nivel de logging
        log_file: Archivo de log (opcional)
        max_bytes: Tamaño máximo del archivo
        backup_count: Número de backups a mantener
        
    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
    
    # Configurar nivel
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Formato estándar
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo (opcional)
    if log_file:
        try:
            from logging.handlers import RotatingFileHandler
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo configurar archivo de log: {e}")
    
    return logger

# ═══════════════════════════════════════════════════════════════════
# UTILIDADES DE SEGURIDAD
# ═══════════════════════════════════════════════════════════════════

def sanitize_path(path: str, base_dir: str = ".") -> Optional[str]:
    """
    Sanitiza y valida rutas de archivos para evitar path traversal.
    
    Args:
        path: Ruta a sanitizar
        base_dir: Directorio base permitido
        
    Returns:
        str | None: Ruta sanitizada o None si es insegura
    """
    try:
        # Resolver path absoluto
        abs_base = os.path.abspath(base_dir)
        abs_path = os.path.abspath(os.path.join(abs_base, path))
        
        # Verificar que está dentro del directorio base
        if not abs_path.startswith(abs_base):
            return None
        
        # Verificar extensión si está configurado
        allowed_ext = config.get("security.allowed_extensions", [])
        if allowed_ext:
            _, ext = os.path.splitext(abs_path)
            if ext.lower() not in allowed_ext:
                return None
        
        return abs_path
        
    except Exception:
        return None

def validate_file_size(filepath: str) -> bool:
    """
    Valida que el tamaño del archivo esté dentro de límites seguros.
    
    Args:
        filepath: Ruta del archivo
        
    Returns:
        bool: True si el tamaño es válido
    """
    try:
        max_size_mb = config.get("security.max_file_size_mb", 100)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            return size <= max_size_bytes
        
        return True  # Si no existe, asumimos que es válido
        
    except Exception:
        return False

# ═══════════════════════════════════════════════════════════════════
# GESTIÓN DE MEMORIA OPTIMIZADA
# ═══════════════════════════════════════════════════════════════════

def get_optimal_batch_size(data_size: int, available_memory_mb: Optional[int] = None) -> int:
    """
    Calcula el tamaño de lote óptimo basado en memoria disponible.
    
    Args:
        data_size: Tamaño de los datos
        available_memory_mb: Memoria disponible en MB
        
    Returns:
        int: Tamaño de lote óptimo
    """
    try:
        # Intentar obtener memoria disponible
        if available_memory_mb is None:
            try:
                import psutil
                available_memory_mb = psutil.virtual_memory().available / (1024 * 1024)
            except ImportError:
                available_memory_mb = config.get("memory_limit_mb", 1000)
        
        # Calcular batch size conservador
        memory_per_item = 1  # MB por ítem (estimación conservadora)
        max_batch = int(available_memory_mb * config.get("performance.memory_threshold", 0.8) / memory_per_item)
        
        # Limitar a valores razonables
        min_batch = 10
        default_batch = config.get("performance.chunk_size", 1000)
        
        optimal_batch = min(max(min_batch, max_batch), default_batch, data_size)
        
        return optimal_batch
        
    except Exception:
        return config.get("performance.chunk_size", 1000)

def process_in_chunks(data: List[Any], chunk_size: Optional[int] = None):
    """
    Generador que procesa datos en chunks para optimizar memoria.
    
    Args:
        data: Lista de datos a procesar
        chunk_size: Tamaño del chunk (auto-calculado si es None)
        
    Yields:
        List: Chunk de datos
    """
    if chunk_size is None:
        chunk_size = get_optimal_batch_size(len(data))
    
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

# ═══════════════════════════════════════════════════════════════════
# UTILIDADES DE FALLBACK
# ═══════════════════════════════════════════════════════════════════

def get_fallback_combination() -> Dict[str, Any]:
    """Retorna una combinación de fallback consistente."""
    return {
        "combination": [1, 2, 3, 4, 5, 6],
        "score": 0.5,
        "svi_score": 0.5,
        "source": "fallback",
        "original_score": 0.5,
        "metrics": {},
        "normalized": 0.0
    }

def safe_execute(func, *args, fallback=None, logger=None, **kwargs):
    """
    Ejecuta una función de forma segura con fallback.
    
    Args:
        func: Función a ejecutar
        *args: Argumentos posicionales
        fallback: Valor de fallback si falla
        logger: Logger opcional
        **kwargs: Argumentos con nombre
        
    Returns:
        Any: Resultado de la función o fallback
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if logger:
            logger.error(f"🚨 Error en {func.__name__}: {e}")
        return fallback

# ═══════════════════════════════════════════════════════════════════
# NUEVAS UTILIDADES
# ═══════════════════════════════════════════════════════════════════

def normalize_scores(scores: List[float]) -> List[float]:
    """
    Normaliza una lista de scores entre 0 y 1.
    
    Args:
        scores: Lista de valores a normalizar
        
    Returns:
        List[float]: Scores normalizados
    """
    if not scores:
        return []
    
    min_score = min(scores)
    max_score = max(scores)
    
    # Evitar división por cero
    if max_score == min_score:
        return [0.5] * len(scores)
    
    return [(s - min_score) / (max_score - min_score) for s in scores]

# ═══════════════════════════════════════════════════════════════════
# EXPORTAR FUNCIONES PRINCIPALES
# ═══════════════════════════════════════════════════════════════════

__all__ = [
    "validate_combination",
    "clean_combination", 
    "clean_historial_df",
    "OmegaConfig",
    "config",
    "setup_logger",
    "sanitize_path",
    "validate_file_size",
    "get_optimal_batch_size",
    "process_in_chunks",
    "get_fallback_combination",
    "safe_execute",
    "normalize_scores"  # Nueva función añadida
]