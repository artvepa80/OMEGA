"""
OMEGA ENHANCEMENT HEADER
Archivo original: (nuevo)
Archivo mejorado: omega_config_enhanced.py
Cambios clave:
* Configuración central unificada para todo el proyecto OMEGA
* Sistema de logging estructurado con niveles y rotación
* Manejo de dependencias opcionales con fallbacks
* Validación de configuración y parámetros de entrada
* Soporte para profiles (dev, prod, test)

Dependencias opcionales detectadas: {HAVE_OPTUNA: bool, HAVE_RIVER: bool, HAVE_RAY: bool, HAVE_PYMOO: bool}
"""

import os
import sys
import json
import yaml
import logging
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from datetime import datetime

try:
    import optuna as _optuna
    HAVE_OPTUNA = True
except ImportError:
    HAVE_OPTUNA = False

try:
    import river as _river
    HAVE_RIVER = True
except ImportError:
    HAVE_RIVER = False

try:
    import ray as _ray
    HAVE_RAY = True
except ImportError:
    HAVE_RAY = False

try:
    import pymoo as _pymoo
    HAVE_PYMOO = True
except ImportError:
    HAVE_PYMOO = False

try:
    import psutil as _psutil
    HAVE_PSUTIL = True
except ImportError:
    HAVE_PSUTIL = False


class OmegaConfigError(Exception):
    """Excepción personalizada para errores de configuración OMEGA"""
    pass


class OmegaValidationError(Exception):
    """Excepción personalizada para errores de validación"""
    pass


@dataclass
class ModelConfig:
    """Configuración para un modelo específico"""
    name: str
    enabled: bool = True
    timeout_seconds: int = 300
    max_memory_mb: int = 1024
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceConfig:
    """Configuración de rendimiento"""
    max_workers: int = 4
    batch_size: int = 32
    cache_size: int = 1000
    parallel_backend: str = "threading"
    profiling_enabled: bool = False


@dataclass
class LoggingConfig:
    """Configuración de logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 50
    backup_count: int = 5
    json_format: bool = False


@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    max_input_size: int = 10_000_000
    timeout_seconds: int = 3600
    allowed_file_extensions: List[str] = field(default_factory=lambda: ['.csv', '.json', '.yaml'])
    sanitize_inputs: bool = True


@dataclass
class OmegaConfig:
    """Configuración central del sistema OMEGA"""
    # Información del proyecto
    project_name: str = "OMEGA PRO AI"
    version: str = "v10.1-enhanced"
    environment: str = "production"
    
    # Rutas
    data_dir: Path = field(default_factory=lambda: Path("data"))
    output_dir: Path = field(default_factory=lambda: Path("outputs"))
    log_dir: Path = field(default_factory=lambda: Path("logs"))
    model_dir: Path = field(default_factory=lambda: Path("models"))
    config_dir: Path = field(default_factory=lambda: Path("config"))
    
    # Configuraciones específicas
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Modelos habilitados
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    
    # Features opcionales
    features: Dict[str, bool] = field(default_factory=lambda: {
        "optuna_optimization": HAVE_OPTUNA,
        "river_streaming": HAVE_RIVER,
        "ray_distributed": HAVE_RAY,
        "pymoo_multiobjective": HAVE_PYMOO,
        "psutil_monitoring": HAVE_PSUTIL,
        "neural_networks": True,
        "ensemble_learning": True,
        "adaptive_learning": True,
        "autonomous_agent": True
    })

    def __post_init__(self):
        """Validar configuración después de inicialización"""
        self._create_directories()
        self._validate_config()
    
    def _create_directories(self):
        """Crear directorios necesarios"""
        for path_attr in ['data_dir', 'output_dir', 'log_dir', 'model_dir', 'config_dir']:
            path = getattr(self, path_attr)
            path.mkdir(parents=True, exist_ok=True)
    
    def _validate_config(self):
        """Validar configuración"""
        if self.performance.max_workers <= 0:
            raise OmegaConfigError("max_workers debe ser > 0")
        
        if self.performance.batch_size <= 0:
            raise OmegaConfigError("batch_size debe ser > 0")
        
        if self.logging.level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise OmegaConfigError(f"Logging level inválido: {self.logging.level}")
        
        if self.environment not in ['dev', 'test', 'production']:
            raise OmegaConfigError(f"Environment inválido: {self.environment}")

    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> 'OmegaConfig':
        """Cargar configuración desde archivo YAML o JSON"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise OmegaConfigError(f"Archivo de configuración no encontrado: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    raise OmegaConfigError(f"Formato de archivo no soportado: {config_path.suffix}")
            
            return cls.from_dict(data)
        
        except Exception as e:
            raise OmegaConfigError(f"Error cargando configuración: {e}") from e
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OmegaConfig':
        """Crear configuración desde diccionario"""
        # Convertir paths a Path objects
        for key in ['data_dir', 'output_dir', 'log_dir', 'model_dir', 'config_dir']:
            if key in data:
                data[key] = Path(data[key])
        
        # Crear sub-configuraciones
        if 'logging' in data:
            data['logging'] = LoggingConfig(**data['logging'])
        
        if 'performance' in data:
            data['performance'] = PerformanceConfig(**data['performance'])
        
        if 'security' in data:
            data['security'] = SecurityConfig(**data['security'])
        
        if 'models' in data:
            models = {}
            for name, model_data in data['models'].items():
                models[name] = ModelConfig(name=name, **model_data)
            data['models'] = models
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir configuración a diccionario"""
        result = {}
        
        for key, value in self.__dict__.items():
            if isinstance(value, Path):
                result[key] = str(value)
            elif isinstance(value, (LoggingConfig, PerformanceConfig, SecurityConfig)):
                result[key] = value.__dict__
            elif isinstance(value, dict) and key == 'models':
                result[key] = {name: model.__dict__ for name, model in value.items()}
            else:
                result[key] = value
        
        return result
    
    def save_to_file(self, config_path: Union[str, Path]):
        """Guardar configuración a archivo"""
        config_path = Path(config_path)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
            elif config_path.suffix.lower() == '.json':
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            else:
                raise OmegaConfigError(f"Formato de archivo no soportado: {config_path.suffix}")


class OmegaLogger:
    """Logger centralizado para OMEGA con soporte para múltiples formatos"""
    
    def __init__(self, config: LoggingConfig, name: str = "OMEGA"):
        self.config = config
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configurar logger"""
        self.logger.setLevel(getattr(logging, self.config.level))
        
        # Remover handlers existentes
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Formatter
        if self.config.json_format:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(self.config.format)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler si especificado
        if self.config.file_path:
            from logging.handlers import RotatingFileHandler
            
            file_handler = RotatingFileHandler(
                self.config.file_path,
                maxBytes=self.config.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """Obtener logger configurado"""
        return self.logger


class JsonFormatter(logging.Formatter):
    """Formatter para logs en formato JSON"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


def validate_combinations(combinations: List[List[int]], 
                         min_numbers: int = 6, 
                         max_numbers: int = 6,
                         min_value: int = 1, 
                         max_value: int = 40) -> List[List[int]]:
    """
    Validar combinaciones de números
    
    Args:
        combinations: Lista de combinaciones a validar
        min_numbers: Mínimo número de elementos por combinación
        max_numbers: Máximo número de elementos por combinación
        min_value: Valor mínimo permitido
        max_value: Valor máximo permitido
    
    Returns:
        Lista de combinaciones válidas
    
    Raises:
        OmegaValidationError: Si hay errores de validación
    """
    if not combinations:
        raise OmegaValidationError("Lista de combinaciones vacía")
    
    valid_combinations = []
    
    for i, combo in enumerate(combinations):
        try:
            # Validar tipo
            if not isinstance(combo, (list, tuple)):
                continue
            
            # Convertir a lista de enteros
            combo = [int(x) for x in combo]
            
            # Validar longitud
            if not (min_numbers <= len(combo) <= max_numbers):
                continue
            
            # Validar rango de valores
            if not all(min_value <= x <= max_value for x in combo):
                continue
            
            # Validar duplicados
            if len(combo) != len(set(combo)):
                continue
            
            # Ordenar combinación
            valid_combinations.append(sorted(combo))
            
        except (ValueError, TypeError):
            continue
    
    if not valid_combinations:
        raise OmegaValidationError("No hay combinaciones válidas después de la validación")
    
    return valid_combinations


def sanitize_file_path(file_path: Union[str, Path], 
                      allowed_extensions: List[str] = None) -> Path:
    """
    Sanitizar path de archivo para seguridad
    
    Args:
        file_path: Path del archivo
        allowed_extensions: Extensiones permitidas
    
    Returns:
        Path sanitizado
    
    Raises:
        OmegaValidationError: Si el path no es válido
    """
    if allowed_extensions is None:
        allowed_extensions = ['.csv', '.json', '.yaml', '.txt']
    
    path = Path(file_path).resolve()
    
    # Validar extensión
    if path.suffix.lower() not in allowed_extensions:
        raise OmegaValidationError(f"Extensión no permitida: {path.suffix}")
    
    # Validar que no sea path absoluto peligroso
    cwd = Path.cwd()
    try:
        path.relative_to(cwd)
    except ValueError:
        # Si no es relativo al directorio actual, verificar que esté en paths seguros
        safe_dirs = ['/tmp', '/var/tmp', str(cwd)]
        if not any(str(path).startswith(safe_dir) for safe_dir in safe_dirs):
            raise OmegaValidationError(f"Path no seguro: {path}")
    
    return path


# Configuración global por defecto
_global_config: Optional[OmegaConfig] = None
_global_logger: Optional[OmegaLogger] = None


def get_config() -> OmegaConfig:
    """Obtener configuración global"""
    global _global_config
    if _global_config is None:
        _global_config = OmegaConfig()
    return _global_config


def set_config(config: OmegaConfig):
    """Establecer configuración global"""
    global _global_config, _global_logger
    _global_config = config
    _global_logger = None  # Reset logger para que use nueva config


def get_logger(name: str = "OMEGA") -> logging.Logger:
    """Obtener logger configurado"""
    global _global_logger
    if _global_logger is None:
        config = get_config()
        _global_logger = OmegaLogger(config.logging, name)
    return _global_logger.get_logger()


def load_config_from_env() -> OmegaConfig:
    """Cargar configuración desde variables de entorno"""
    config_file = os.getenv('OMEGA_CONFIG_FILE', 'config/omega_config.yaml')
    environment = os.getenv('OMEGA_ENVIRONMENT', 'production')
    
    if os.path.exists(config_file):
        config = OmegaConfig.from_file(config_file)
    else:
        config = OmegaConfig()
    
    config.environment = environment
    
    # Override con variables de entorno
    if 'OMEGA_LOG_LEVEL' in os.environ:
        config.logging.level = os.environ['OMEGA_LOG_LEVEL']
    
    if 'OMEGA_MAX_WORKERS' in os.environ:
        config.performance.max_workers = int(os.environ['OMEGA_MAX_WORKERS'])
    
    return config


# Inicializar configuración al importar
if __name__ != "__main__":
    try:
        set_config(load_config_from_env())
    except Exception:
        # Fallback a configuración por defecto
        set_config(OmegaConfig())


if __name__ == "__main__":
    # Demo de configuración
    config = OmegaConfig()
    print("Configuración OMEGA cargada:")
    print(f"- Versión: {config.version}")
    print(f"- Environment: {config.environment}")
    print(f"- Features disponibles:")
    for feature, available in config.features.items():
        status = "✅" if available else "❌"
        print(f"  {status} {feature}")
    
    # Test de logger
    logger = get_logger("TEST")
    logger.info("Logger configurado correctamente")
    logger.debug("Mensaje de debug")
    logger.warning("Mensaje de warning")
