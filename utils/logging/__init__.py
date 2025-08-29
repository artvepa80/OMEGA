# OMEGA_PRO_AI_v10.1/utils/logging/__init__.py

"""
Módulo logging - Sistema de logging unificado OMEGA PRO AI

Contiene:
- unified_logger.py: Sistema de logging unificado principal
- logging.py: Sistema de logging simple (legacy)
- logger.py: Logger avanzado con timestamping (legacy)
- log_manager.py: Gestión y limpieza de logs (legacy)
"""

from .unified_logger import (
    OmegaUnifiedLogger,
    get_unified_logger,
    log_debug, log_info, log_warning, log_error, log_critical,
    rotate_logs, clean_old_logs, get_log_stats, get_logger
)

__all__ = [
    "OmegaUnifiedLogger",
    "get_unified_logger",
    "log_debug", "log_info", "log_warning", "log_error", "log_critical",
    "rotate_logs", "clean_old_logs", "get_log_stats", "get_logger"
]