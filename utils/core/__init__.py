# OMEGA_PRO_AI_v10.1/utils/core/__init__.py

"""
Módulo core - Funcionalidades básicas del sistema OMEGA PRO AI

Contiene:
- errors.py: Clases de excepción personalizadas
- validation.py: Funciones de validación de datos
- common.py: Utilidades comunes y validaciones
- numpy_compat.py: Parches de compatibilidad con NumPy
- random_control.py: Control de semillas aleatorias
- viabilidad.py: Análisis de viabilidad
"""

from .errors import OmegaError, DataLoadError, ModelLoadError, ValidationError
from .validation import validate_combination, clean_historial_df, safe_convert_to_int
from .numpy_compat import patch_numpy_deprecated_aliases
from .random_control import maybe_seed_from_env

__all__ = [
    "OmegaError", "DataLoadError", "ModelLoadError", "ValidationError",
    "validate_combination", "clean_historial_df", "safe_convert_to_int", "patch_numpy_deprecated_aliases",
    "maybe_seed_from_env"
]