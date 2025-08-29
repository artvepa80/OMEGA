# OMEGA_PRO_AI_v10.1/utils/unified_logger.py - Sistema de Logging Unificado

import logging
import os
import sys
import glob
import time
import shutil
import gzip
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Union, Optional

class OmegaUnifiedLogger:
    """
    Sistema de logging unificado que combina:
    - Configuración simple y flexible
    - Manejo avanzado de archivos con rotación automática
    - Gestión y limpieza de logs antiguos
    - Múltiples handlers (sistema, errores, consola)
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 name: str = "OmegaUnified",
                 level: Union[int, str] = logging.INFO,
                 base_log_dir: str = "logs",
                 max_system_size_mb: int = 10,
                 max_error_size_mb: int = 5,
                 backup_count: int = 5,
                 create_timestamped_dir: bool = True):
        
        if self._initialized:
            return
            
        self.logger = logging.getLogger(name)
        
        # Normalize level
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(level)
        self.logger.propagate = False
        
        # Setup log directory
        if create_timestamped_dir:
            self.log_dir = os.path.join(base_log_dir, datetime.now().strftime('%Y%m%d_%H%M%S'))
        else:
            self.log_dir = base_log_dir
            
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configuration
        self.max_system_size_mb = max_system_size_mb
        self.max_error_size_mb = max_error_size_mb
        self.backup_count = backup_count
        self.base_log_dir = base_log_dir
        
        self._setup_handlers()
        self._initialized = True
        
        # Initial log
        self.logger.info("Sistema de Logging Unificado OMEGA PRO AI v10.1 inicializado")
    
    def _setup_handlers(self):
        """Configura todos los handlers de logging"""
        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
        
        # Common formatter
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] [%(name)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # System log handler (all levels)
        system_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "omega_system.log"),
            maxBytes=self.max_system_size_mb * 1024 * 1024,
            backupCount=self.backup_count,
            encoding="utf-8"
        )
        system_handler.setLevel(logging.DEBUG)
        system_handler.setFormatter(formatter)
        system_handler.name = "system_handler"
        
        # Error log handler (errors and critical only)
        error_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "omega_errors.log"),
            maxBytes=self.max_error_size_mb * 1024 * 1024,
            backupCount=self.backup_count,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        error_handler.name = "error_handler"
        
        # Console handler (configurable level)
        console_level = os.getenv("CONSOLE_LOG_LEVEL", "ERROR").upper()
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level, logging.ERROR))
        console_handler.setFormatter(formatter)
        console_handler.name = "console_handler"
        
        # Add all handlers
        self.logger.addHandler(system_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = True):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info)
    
    def rotate_logs(self):
        """Manually rotate logs by creating new timestamped directory"""
        self.logger.info("Iniciando rotación manual de logs")
        
        # Create new timestamped directory
        new_log_dir = os.path.join(self.base_log_dir, datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(new_log_dir, exist_ok=True)
        
        # Update log directory
        old_log_dir = self.log_dir
        self.log_dir = new_log_dir
        
        # Recreate handlers with new directory
        self._setup_handlers()
        
        self.logger.info(f"Rotación completada: {old_log_dir} -> {new_log_dir}")
    
    def clean_old_logs(self, days: int = 7, dry_run: bool = False) -> int:
        """
        Elimina logs antiguos con verificación de seguridad
        Returns: número de directorios eliminados
        """
        abs_base_dir = os.path.abspath(self.base_log_dir)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Security check
        if not abs_base_dir.startswith(project_root):
            self.warning(f"Directorio de logs fuera del proyecto: {abs_base_dir}")
            if not dry_run:
                self.error("Operación cancelada por seguridad")
                return 0
        
        # Disk space check
        disk_threshold = float(os.getenv("MIN_DISK_SPACE_RATIO", "0.1"))
        try:
            stat = shutil.disk_usage(self.base_log_dir)
            if stat.free / stat.total < disk_threshold:
                self.warning(f"Espacio en disco bajo ({stat.free / (1024**3):.2f}GB libre)")
        except Exception as e:
            self.error(f"Error verificando espacio en disco: {str(e)}", exc_info=True)
        
        current_time = time.time()
        threshold = current_time - (days * 86400)
        deleted_count = 0
        
        try:
            log_dirs = glob.glob(os.path.join(self.base_log_dir, "*"))
            for log_dir in log_dirs:
                if os.path.isdir(log_dir):
                    dir_time = os.path.getmtime(log_dir)
                    if dir_time < threshold:
                        if not dry_run and not os.access(log_dir, os.W_OK):
                            self.error(f"Sin permisos de escritura para {log_dir}")
                            continue
                        
                        if dry_run:
                            self.info(f"Simulación: eliminaría {log_dir} (>{days} días)")
                        else:
                            shutil.rmtree(log_dir)
                            self.info(f"Directorio eliminado: {log_dir} (>{days} días)")
                        deleted_count += 1
            
            if dry_run:
                self.info(f"Simulación: {deleted_count} directorios serían eliminados")
            else:
                self.info(f"Limpieza completada: {deleted_count} directorios eliminados")
                
        except Exception as e:
            self.error(f"Error en clean_old_logs: {str(e)}", exc_info=True)
        
        return deleted_count
    
    def get_log_stats(self) -> dict:
        """Obtiene estadísticas de los archivos de log actuales"""
        stats = {
            "log_dir": self.log_dir,
            "system_log_size_mb": 0,
            "error_log_size_mb": 0,
            "total_log_dirs": 0
        }
        
        try:
            # Current log sizes
            system_log = os.path.join(self.log_dir, "omega_system.log")
            if os.path.exists(system_log):
                stats["system_log_size_mb"] = os.path.getsize(system_log) / (1024 * 1024)
            
            error_log = os.path.join(self.log_dir, "omega_errors.log")
            if os.path.exists(error_log):
                stats["error_log_size_mb"] = os.path.getsize(error_log) / (1024 * 1024)
            
            # Total log directories
            log_dirs = glob.glob(os.path.join(self.base_log_dir, "*"))
            stats["total_log_dirs"] = len([d for d in log_dirs if os.path.isdir(d)])
            
        except Exception as e:
            self.error(f"Error obteniendo estadísticas: {str(e)}", exc_info=True)
        
        return stats

# Singleton instance
_unified_logger = None

def get_unified_logger(**kwargs) -> OmegaUnifiedLogger:
    """Get or create the unified logger singleton"""
    global _unified_logger
    if _unified_logger is None:
        _unified_logger = OmegaUnifiedLogger(**kwargs)
    return _unified_logger

# Convenience functions for backward compatibility
def log_debug(message: str):
    get_unified_logger().debug(message)

def log_info(message: str):
    get_unified_logger().info(message)

def log_warning(message: str):
    get_unified_logger().warning(message)

def log_error(message: str, exc_info: bool = False):
    get_unified_logger().error(message, exc_info=exc_info)

def log_critical(message: str, exc_info: bool = True):
    get_unified_logger().critical(message, exc_info=exc_info)

def rotate_logs():
    """Manually rotate logs"""
    get_unified_logger().rotate_logs()

def clean_old_logs(days: int = 7, dry_run: bool = False) -> int:
    """Clean old log directories"""
    return get_unified_logger().clean_old_logs(days=days, dry_run=dry_run)

def get_log_stats() -> dict:
    """Get current log statistics"""
    return get_unified_logger().get_log_stats()

# Legacy compatibility function
def get_logger(name: str = "OmegaUnified", **kwargs) -> logging.Logger:
    """Get logger instance for backward compatibility"""
    unified = get_unified_logger(**kwargs)
    return unified.logger