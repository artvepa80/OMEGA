"""
Logging utilities for OMEGA system
"""

import logging
import sys
from typing import Any

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_logger(name: str) -> logging.Logger:
    """Get logger for specific module"""
    return logging.getLogger(name)

def log_info(message: str, *args: Any):
    """Log info message"""
    logger = logging.getLogger("OMEGA")
    logger.info(message, *args)

def log_warning(message: str, *args: Any):
    """Log warning message"""
    logger = logging.getLogger("OMEGA")
    logger.warning(message, *args)

def log_error(message: str, *args: Any):
    """Log error message"""
    logger = logging.getLogger("OMEGA")
    logger.error(message, *args)

def log_debug(message: str, *args: Any):
    """Log debug message"""
    logger = logging.getLogger("OMEGA")
    logger.debug(message, *args)