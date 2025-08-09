# OMEGA_PRO_AI_v10.1/utils/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime
from logging import getLogger  # Added for direct logger access

class OmegaLogger:
    def __init__(self):
        self.logger = logging.getLogger("OmegaLogger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        
        # Create timestamped log directory
        self.log_dir = f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.log_dir, exist_ok=True)
        
        self._setup_handlers()
        
    def _setup_handlers(self):
        # Common formatter
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] [%(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # System log handler
        system_handler = RotatingFileHandler(
            f"{self.log_dir}/omega_system.log",
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        system_handler.setLevel(logging.DEBUG)
        system_handler.setFormatter(formatter)
        system_handler.name = "system_handler"  # Add identifier
        
        # Error log handler
        error_handler = RotatingFileHandler(
            f"{self.log_dir}/omega_errors.log",
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=3,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        error_handler.name = "error_handler"  # Add identifier
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        console_handler.name = "console_handler"  # Add identifier
        
        # Add handlers
        self.logger.addHandler(system_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        # Initial log
        self.logger.info("Logger inicializado - Sistema OMEGA PRO AI v10.1")
    
    def debug(self, message):
        self.logger.debug(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message, exc_info=False):
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message):
        self.logger.critical(message, exc_info=True)
    
    def rotate_handlers(self):
        """Reinitialize file handlers after manual rotation"""
        self.logger.info("Iniciando rotación de handlers de logging")
        
        # Close and remove only file handlers
        for handler in self.logger.handlers[:]:
            if isinstance(handler, RotatingFileHandler):
                handler.close()
                self.logger.removeHandler(handler)
        
        # Recreate file handlers with same configuration
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] [%(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Recreate system handler
        system_handler = RotatingFileHandler(
            f"{self.log_dir}/omega_system.log",
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding="utf-8"
        )
        system_handler.setLevel(logging.DEBUG)
        system_handler.setFormatter(formatter)
        
        # Recreate error handler
        error_handler = RotatingFileHandler(
            f"{self.log_dir}/omega_errors.log",
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Add handlers back
        self.logger.addHandler(system_handler)
        self.logger.addHandler(error_handler)
        self.logger.info("Handlers de logging rotados exitosamente")

# Singleton logger instance
logger = OmegaLogger()

# Fast access functions
def log_debug(message):
    logger.debug(message)

def log_info(message):
    logger.info(message)

def log_warning(message):
    logger.warning(message)

def log_error(message, exc_info=False):
    logger.error(message, exc_info=exc_info)

def log_critical(message):
    logger.critical(message)

# Rotation interface function - UPDATED IMPLEMENTATION
def rotate_logs():
    """Public interface for log rotation"""
    # Get the logger instance directly
    omega_logger = getLogger("OmegaLogger")
    omega_logger.info("Iniciando rotación manual de logs")
    
    # Close and remove all handlers
    for handler in omega_logger.handlers[:]:
        handler.close()
        omega_logger.removeHandler(handler)
    
    # Create new timestamped log directory
    new_log_dir = f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(new_log_dir, exist_ok=True)
    
    # Recreate formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Recreate system handler
    system_handler = RotatingFileHandler(
        f"{new_log_dir}/omega_system.log",
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding="utf-8"
    )
    system_handler.setLevel(logging.DEBUG)
    system_handler.setFormatter(formatter)
    
    # Recreate error handler
    error_handler = RotatingFileHandler(
        f"{new_log_dir}/omega_errors.log",
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Recreate console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    
    # Add all handlers back
    omega_logger.addHandler(system_handler)
    omega_logger.addHandler(error_handler)
    omega_logger.addHandler(console_handler)
    
    omega_logger.info("Rotación manual de logs completada exitosamente")