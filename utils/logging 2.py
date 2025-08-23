import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Union


def get_logger(name: str,
               level: Union[int, str] = logging.INFO,
               log_file: str = "logs/omega.log",
               max_bytes: int = 10 * 1024 * 1024,
               backup_count: int = 5) -> logging.Logger:
    """
    Returns a singleton-style configured logger with:
    - RotatingFileHandler (10MB, 5 backups)
    - StreamHandler to stdout
    Handlers are added only once per logger name.
    """
    logger = logging.getLogger(name)

    # Normalize level
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(level)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    stream_handler.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


