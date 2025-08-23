"""
Enhanced logging utilities for OMEGA system
"""

import logging
import sys
from typing import Any, Optional

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get configured logger for specific module"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    
    return logger