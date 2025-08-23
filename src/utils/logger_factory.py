#!/usr/bin/env python3
"""
📝 OMEGA Logger Factory - Sistema de Logging Estructurado Avanzado
Logging centralizado con niveles, formateo y rotación optimizada
"""

import logging
import logging.handlers
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import traceback
from functools import wraps

class StructuredFormatter(logging.Formatter):
    """Formateador de logging estructurado con JSON"""
    
    def __init__(self, service_name: str = "OMEGA", include_trace: bool = True):
        super().__init__()
        self.service_name = service_name
        self.include_trace = include_trace
    
    def format(self, record: logging.LogRecord) -> str:
        # Crear estructura base
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "module": record.name,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Agregar contexto adicional si existe
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
            
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        # Agregar stack trace para errores
        if record.exc_info and self.include_trace:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Agregar métricas de performance si existen
        if hasattr(record, 'duration'):
            log_entry['performance'] = {
                'duration_ms': record.duration,
                'memory_usage': getattr(record, 'memory_usage', None),
                'cpu_usage': getattr(record, 'cpu_usage', None)
            }
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)

class ColoredConsoleFormatter(logging.Formatter):
    """Formateador con colores para consola"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Formato: TIMESTAMP [LEVEL] MODULE: MESSAGE
        formatted_time = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        base_message = f"{formatted_time} [{color}{record.levelname:8}{reset}] {record.name}: {record.getMessage()}"
        
        # Agregar contexto si existe
        if hasattr(record, 'context'):
            context_str = json.dumps(record.context, ensure_ascii=False, default=str)
            base_message += f" | Context: {context_str}"
        
        # Agregar excepción si existe
        if record.exc_info:
            base_message += f"\n{self.formatException(record.exc_info)}"
        
        return base_message

class PerformanceLogger:
    """Logger especializado en métricas de performance"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_execution_time(self, func_name: str, duration: float, **kwargs):
        """Log tiempo de ejecución de función"""
        extra = {
            'duration': duration,
            'context': {
                'function': func_name,
                'performance_type': 'execution_time',
                **kwargs
            }
        }
        self.logger.info(f"⏱️ {func_name} ejecutado en {duration:.3f}ms", extra=extra)
    
    def log_memory_usage(self, component: str, memory_mb: float, **kwargs):
        """Log uso de memoria"""
        extra = {
            'memory_usage': memory_mb,
            'context': {
                'component': component,
                'performance_type': 'memory_usage',
                **kwargs
            }
        }
        self.logger.info(f"💾 {component} usando {memory_mb:.1f}MB", extra=extra)
    
    def log_throughput(self, component: str, items_per_second: float, **kwargs):
        """Log throughput"""
        extra = {
            'context': {
                'component': component,
                'throughput': items_per_second,
                'performance_type': 'throughput',
                **kwargs
            }
        }
        self.logger.info(f"🚀 {component} throughput: {items_per_second:.1f} items/s", extra=extra)

class LoggerFactory:
    """Factory para crear loggers configurados"""
    
    _loggers: Dict[str, logging.Logger] = {}
    _performance_loggers: Dict[str, PerformanceLogger] = {}
    _config: Dict[str, Any] = {
        'level': 'INFO',
        'format': 'structured',  # 'structured' o 'colored'
        'log_dir': 'logs',
        'max_bytes': 50 * 1024 * 1024,  # 50MB
        'backup_count': 10,
        'service_name': 'OMEGA_PRO_AI'
    }
    
    @classmethod
    def configure(cls, **config):
        """Configura el factory globalmente"""
        cls._config.update(config)
        
        # Crear directorio de logs
        Path(cls._config['log_dir']).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_logger(cls, name: str, 
                   level: Optional[str] = None,
                   session_id: Optional[str] = None,
                   user_id: Optional[str] = None) -> logging.Logger:
        """
        Obtiene logger configurado
        
        Args:
            name: Nombre del logger
            level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            session_id: ID de sesión para contexto
            user_id: ID de usuario para contexto
        """
        
        if name in cls._loggers:
            logger = cls._loggers[name]
        else:
            logger = logging.getLogger(name)
            logger.setLevel(getattr(logging, level or cls._config['level']))
            
            # Limpiar handlers existentes
            logger.handlers.clear()
            
            # Handler para archivos (structured JSON)
            log_file = Path(cls._config['log_dir']) / f"{name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=cls._config['max_bytes'],
                backupCount=cls._config['backup_count'],
                encoding='utf-8'
            )
            
            structured_formatter = StructuredFormatter(
                service_name=cls._config['service_name']
            )
            file_handler.setFormatter(structured_formatter)
            logger.addHandler(file_handler)
            
            # Handler para consola (colored)
            console_handler = logging.StreamHandler(sys.stdout)
            if cls._config['format'] == 'structured':
                console_handler.setFormatter(structured_formatter)
            else:
                console_handler.setFormatter(ColoredConsoleFormatter())
            
            logger.addHandler(console_handler)
            
            # Evitar propagación duplicada
            logger.propagate = False
            
            cls._loggers[name] = logger
        
        # Agregar contexto persistente si se proporciona
        if session_id or user_id:
            # Crear un adaptador para agregar contexto automáticamente
            adapter = ContextLoggerAdapter(logger, {
                'session_id': session_id,
                'user_id': user_id
            })
            return adapter
        
        return logger
    
    @classmethod
    def get_performance_logger(cls, name: str) -> PerformanceLogger:
        """Obtiene logger especializado en performance"""
        if name not in cls._performance_loggers:
            base_logger = cls.get_logger(f"{name}_performance")
            cls._performance_loggers[name] = PerformanceLogger(base_logger)
        
        return cls._performance_loggers[name]
    
    @classmethod
    def create_request_logger(cls, request_id: str, endpoint: str) -> logging.Logger:
        """Crea logger específico para una request HTTP"""
        logger_name = f"request_{request_id[:8]}"
        return cls.get_logger(
            logger_name,
            session_id=request_id,
            user_id=endpoint
        )

class ContextLoggerAdapter(logging.LoggerAdapter):
    """Adaptador que agrega contexto automáticamente"""
    
    def process(self, msg, kwargs):
        # Agregar contexto persistente
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs

def performance_monitor(logger: Optional[logging.Logger] = None):
    """Decorator para monitorear performance de funciones"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Usar logger específico o crear uno
            perf_logger = logger or LoggerFactory.get_logger(f"perf_{func.__module__}")
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000  # ms
                
                extra = {
                    'duration': duration,
                    'context': {
                        'function': func.__name__,
                        'module': func.__module__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs),
                        'success': True
                    }
                }
                
                perf_logger.info(f"✅ {func.__name__} completado", extra=extra)
                return result
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000  # ms
                
                extra = {
                    'duration': duration,
                    'context': {
                        'function': func.__name__,
                        'module': func.__module__,
                        'error': str(e),
                        'success': False
                    }
                }
                
                perf_logger.error(f"❌ {func.__name__} falló", extra=extra, exc_info=True)
                raise
        
        return wrapper
    return decorator

def log_function_call(logger: Optional[logging.Logger] = None, level: str = "DEBUG"):
    """Decorator para loggear llamadas a funciones"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logger or LoggerFactory.get_logger(func.__module__)
            
            extra = {
                'context': {
                    'function': func.__name__,
                    'args': [str(arg)[:100] for arg in args],  # Limitar longitud
                    'kwargs': {k: str(v)[:100] for k, v in kwargs.items()}
                }
            }
            
            getattr(func_logger, level.lower())(f"🔧 Llamando {func.__name__}", extra=extra)
            
            try:
                result = func(*args, **kwargs)
                getattr(func_logger, level.lower())(f"✅ {func.__name__} completado", extra=extra)
                return result
            except Exception as e:
                extra['context']['error'] = str(e)
                func_logger.error(f"❌ {func.__name__} falló", extra=extra, exc_info=True)
                raise
        
        return wrapper
    return decorator

# Configuración por defecto
LoggerFactory.configure(
    level='INFO',
    format='colored',  # Para desarrollo local
    service_name='OMEGA_PRO_AI_v10.1'
)