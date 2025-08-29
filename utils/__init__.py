# OMEGA_PRO_AI_v10.1/utils/__init__.py - Paquete de utilidades reorganizado

"""
Paquete de utilidades OMEGA PRO AI v10.1 - Reorganizado

Estructura:
- core/: Funcionalidades básicas (errores, validación, compatibilidad)
- logging/: Sistema de logging unificado
- data/: Utilidades de procesamiento de datos
- async/: Utilidades asíncronas
- ml/: Utilidades de machine learning
"""

# Importaciones principales para compatibilidad hacia atrás
from .logging.unified_logger import (
    get_unified_logger,
    log_debug, log_info, log_warning, log_error, log_critical,
    rotate_logs, clean_old_logs, get_log_stats, get_logger
)

from .core.errors import OmegaError, DataLoadError, ModelLoadError, ValidationError
from .core.validation import validate_combination, clean_historial_df, safe_convert_to_int
from .core.numpy_compat import patch_numpy_deprecated_aliases
from .core.random_control import maybe_seed_from_env

__version__ = "10.1.0"
__all__ = [
    # Logging
    "get_unified_logger", "log_debug", "log_info", "log_warning", 
    "log_error", "log_critical", "rotate_logs", "clean_old_logs", 
    "get_log_stats", "get_logger",
    
    # Core
    "OmegaError", "DataLoadError", "ModelLoadError", "ValidationError",
    "validate_combination", "clean_historial_df", "safe_convert_to_int", "patch_numpy_deprecated_aliases",
    "maybe_seed_from_env"
]
