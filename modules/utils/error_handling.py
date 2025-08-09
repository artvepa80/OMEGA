#!/usr/bin/env python3
"""
Módulo de Manejo de Errores Profesional para OMEGA PRO AI
Reemplaza try-except genéricos con manejo específico y logging detallado
"""

import logging
import traceback
import functools
from typing import Any, Callable, Dict, List, Optional, Union, Type
from datetime import datetime
import json
import os
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Niveles de severidad de errores"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Categorías de errores específicas para OMEGA PRO AI"""
    DATA_VALIDATION = "data_validation"
    MODEL_TRAINING = "model_training"
    MODEL_PREDICTION = "model_prediction"
    FILE_IO = "file_io"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    MEMORY = "memory"
    COMPUTATION = "computation"
    MULTIPROCESSING = "multiprocessing"
    DEPENDENCY = "dependency"

class OmegaError(Exception):
    """Excepción base personalizada para OMEGA PRO AI"""
    
    def __init__(self, 
                 message: str,
                 category: ErrorCategory,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 details: Optional[Dict[str, Any]] = None,
                 suggestions: Optional[List[str]] = None):
        
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.suggestions = suggestions or []
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el error a diccionario para logging"""
        return {
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value,
            'details': self.details,
            'suggestions': self.suggestions,
            'timestamp': self.timestamp.isoformat(),
            'traceback': traceback.format_exc()
        }

class DataValidationError(OmegaError):
    """Error específico de validación de datos"""
    def __init__(self, message: str, details: Optional[Dict] = None, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.DATA_VALIDATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            suggestions=suggestions or [
                "Verificar formato de datos de entrada",
                "Revisar tipos de datos esperados",
                "Validar rangos de valores permitidos"
            ]
        )

class ModelTrainingError(OmegaError):
    """Error específico de entrenamiento de modelos"""
    def __init__(self, message: str, model_name: str = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.MODEL_TRAINING,
            severity=ErrorSeverity.HIGH,
            details={**(details or {}), 'model_name': model_name},
            suggestions=[
                "Verificar calidad de datos de entrenamiento",
                "Ajustar hiperparámetros del modelo",
                "Revisar suficiencia de datos",
                "Considerar reducir complejidad del modelo"
            ]
        )

class ModelPredictionError(OmegaError):
    """Error específico de predicción de modelos"""
    def __init__(self, message: str, model_name: str = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.MODEL_PREDICTION,
            severity=ErrorSeverity.MEDIUM,
            details={**(details or {}), 'model_name': model_name},
            suggestions=[
                "Verificar que el modelo esté entrenado",
                "Validar formato de datos de entrada",
                "Revisar compatibilidad de características",
                "Considerar re-entrenar el modelo"
            ]
        )

class ConfigurationError(OmegaError):
    """Error específico de configuración"""
    def __init__(self, message: str, config_file: str = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            details={**(details or {}), 'config_file': config_file},
            suggestions=[
                "Verificar sintaxis del archivo de configuración",
                "Revisar valores de parámetros requeridos",
                "Validar rutas de archivos especificadas",
                "Consultar documentación de configuración"
            ]
        )

class FileIOError(OmegaError):
    """Error específico de entrada/salida de archivos"""
    def __init__(self, message: str, file_path: str = None, operation: str = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.FILE_IO,
            severity=ErrorSeverity.MEDIUM,
            details={**(details or {}), 'file_path': file_path, 'operation': operation},
            suggestions=[
                "Verificar que el archivo existe y es accesible",
                "Revisar permisos de lectura/escritura",
                "Validar formato del archivo",
                "Verificar espacio disponible en disco"
            ]
        )

class MultiprocessingError(OmegaError):
    """Error específico de multiprocesamiento"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.MULTIPROCESSING,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            suggestions=[
                "Agregar freeze_support() al script principal",
                "Usar processing secuencial como fallback",
                "Verificar compatibilidad del sistema operativo",
                "Reducir número de procesos paralelos"
            ]
        )

class ErrorHandler:
    """Manejador centralizado de errores para OMEGA PRO AI"""
    
    def __init__(self, 
                 log_to_file: bool = True,
                 log_directory: str = "logs",
                 max_log_files: int = 10):
        
        self.log_to_file = log_to_file
        self.log_directory = log_directory
        self.max_log_files = max_log_files
        self.error_history = []
        
        if log_to_file:
            os.makedirs(log_directory, exist_ok=True)
    
    def handle_error(self, 
                    error: Union[Exception, OmegaError],
                    context: Optional[Dict[str, Any]] = None,
                    reraise: bool = True) -> Optional[Dict[str, Any]]:
        """
        Maneja un error de forma específica y profesional
        
        Args:
            error: La excepción a manejar
            context: Contexto adicional del error
            reraise: Si re-lanzar la excepción después del manejo
            
        Returns:
            Diccionario con información del error si reraise=False
        """
        # Convertir Exception genérica a OmegaError si es necesario
        if not isinstance(error, OmegaError):
            omega_error = self._classify_generic_error(error)
        else:
            omega_error = error
        
        # Agregar contexto
        if context:
            omega_error.details.update(context)
        
        # Registrar en historial
        error_info = omega_error.to_dict()
        self.error_history.append(error_info)
        
        # Logging específico por severidad
        self._log_error(omega_error)
        
        # Guardar en archivo si está habilitado
        if self.log_to_file:
            self._save_error_to_file(error_info)
        
        # Re-lanzar o retornar información
        if reraise:
            raise omega_error
        else:
            return error_info
    
    def _classify_generic_error(self, error: Exception) -> OmegaError:
        """Clasifica una excepción genérica en OmegaError específico"""
        error_type = type(error).__name__
        message = str(error)
        
        # Clasificación basada en tipo de excepción
        if isinstance(error, (FileNotFoundError, PermissionError, IOError)):
            return FileIOError(
                message=f"{error_type}: {message}",
                operation="unknown",
                details={'original_type': error_type}
            )
        
        elif isinstance(error, (ValueError, TypeError)) and any(
            keyword in message.lower() 
            for keyword in ['validation', 'format', 'range', 'type']
        ):
            return DataValidationError(
                message=f"{error_type}: {message}",
                details={'original_type': error_type}
            )
        
        elif isinstance(error, ImportError):
            return OmegaError(
                message=f"Dependencia faltante: {message}",
                category=ErrorCategory.DEPENDENCY,
                severity=ErrorSeverity.HIGH,
                details={'original_type': error_type},
                suggestions=[
                    "Instalar dependencia faltante",
                    "Verificar versión de Python",
                    "Revisar requirements.txt"
                ]
            )
        
        elif 'multiprocessing' in message.lower() or 'freeze_support' in message.lower():
            return MultiprocessingError(
                message=f"Error de multiprocesamiento: {message}",
                details={'original_type': error_type}
            )
        
        elif isinstance(error, MemoryError):
            return OmegaError(
                message=f"Error de memoria: {message}",
                category=ErrorCategory.MEMORY,
                severity=ErrorSeverity.CRITICAL,
                details={'original_type': error_type},
                suggestions=[
                    "Reducir tamaño de datos procesados",
                    "Usar procesamiento por lotes",
                    "Liberar memoria no utilizada",
                    "Considerar aumentar memoria del sistema"
                ]
            )
        
        # Error genérico si no se puede clasificar
        return OmegaError(
            message=f"{error_type}: {message}",
            category=ErrorCategory.COMPUTATION,
            severity=ErrorSeverity.MEDIUM,
            details={'original_type': error_type}
        )
    
    def _log_error(self, error: OmegaError):
        """Registra el error usando logging apropiado"""
        log_message = f"[{error.category.value.upper()}] {error.message}"
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Log detalles y sugerencias si existen
        if error.details:
            logger.info(f"   Detalles: {error.details}")
        
        if error.suggestions:
            logger.info(f"   Sugerencias: {', '.join(error.suggestions[:3])}")
    
    def _save_error_to_file(self, error_info: Dict[str, Any]):
        """Guarda error detallado en archivo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"error_{timestamp}.json"
            filepath = os.path.join(self.log_directory, filename)
            
            with open(filepath, 'w') as f:
                json.dump(error_info, f, indent=2, default=str)
            
            # Limpiar archivos antiguos
            self._cleanup_old_error_files()
            
        except Exception as e:
            logger.warning(f"⚠️ No se pudo guardar error en archivo: {e}")
    
    def _cleanup_old_error_files(self):
        """Limpia archivos de error antiguos"""
        try:
            error_files = [
                f for f in os.listdir(self.log_directory)
                if f.startswith('error_') and f.endswith('.json')
            ]
            
            if len(error_files) > self.max_log_files:
                # Ordenar por fecha y eliminar los más antiguos
                error_files.sort()
                files_to_remove = error_files[:-self.max_log_files]
                
                for file_to_remove in files_to_remove:
                    os.remove(os.path.join(self.log_directory, file_to_remove))
                    
        except Exception as e:
            logger.warning(f"⚠️ Error limpiando archivos antiguos: {e}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de errores recientes"""
        if not self.error_history:
            return {'total_errors': 0, 'categories': {}, 'severities': {}}
        
        categories = {}
        severities = {}
        
        for error in self.error_history[-50:]:  # Últimos 50 errores
            category = error.get('category', 'unknown')
            severity = error.get('severity', 'unknown')
            
            categories[category] = categories.get(category, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors': len(self.error_history[-50:]),
            'categories': categories,
            'severities': severities,
            'most_recent': self.error_history[-1] if self.error_history else None
        }

# Instancia global del manejador de errores
error_handler = ErrorHandler()

def handle_omega_errors(context: str = "", 
                       fallback_return: Any = None,
                       specific_exceptions: Optional[Dict[Type[Exception], Callable]] = None):
    """
    Decorador para manejo específico de errores en funciones de OMEGA PRO AI
    
    Args:
        context: Contexto descriptivo de la función
        fallback_return: Valor a retornar en caso de error
        specific_exceptions: Mapeo de excepciones específicas a manejadores
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                # Manejo específico si está definido
                if specific_exceptions and type(e) in specific_exceptions:
                    handler_func = specific_exceptions[type(e)]
                    return handler_func(e, *args, **kwargs)
                
                # Contexto de la función
                func_context = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'context': context,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                }
                
                # Manejar error
                error_handler.handle_error(
                    error=e,
                    context=func_context,
                    reraise=False
                )
                
                # Retornar fallback
                logger.warning(f"⚠️ Función {func.__name__} falló, usando fallback: {fallback_return}")
                return fallback_return
                
        return wrapper
    return decorator

def safe_execute(func: Callable, 
                *args,
                context: str = "",
                fallback: Any = None,
                log_success: bool = False,
                **kwargs) -> Any:
    """
    Ejecuta una función de forma segura con manejo específico de errores
    
    Args:
        func: Función a ejecutar
        *args: Argumentos posicionales
        context: Contexto descriptivo
        fallback: Valor fallback en caso de error
        log_success: Si registrar ejecuciones exitosas
        **kwargs: Argumentos con nombre
        
    Returns:
        Resultado de la función o valor fallback
    """
    try:
        result = func(*args, **kwargs)
        
        if log_success:
            logger.info(f"✅ Ejecución exitosa: {func.__name__} en contexto {context}")
        
        return result
        
    except Exception as e:
        func_context = {
            'function': func.__name__,
            'module': getattr(func, '__module__', 'unknown'),
            'context': context,
            'has_fallback': fallback is not None
        }
        
        error_handler.handle_error(
            error=e,
            context=func_context,
            reraise=False
        )
        
        return fallback

# Funciones de utilidad específicas para OMEGA PRO AI
def validate_and_execute(validation_func: Callable,
                        execution_func: Callable,
                        data: Any,
                        *args,
                        **kwargs) -> Any:
    """
    Valida datos antes de ejecutar función principal
    
    Args:
        validation_func: Función de validación
        execution_func: Función principal a ejecutar
        data: Datos a validar
        
    Returns:
        Resultado de execution_func o None si validación falla
    """
    try:
        # Validar datos
        validation_result = validation_func(data)
        
        if not validation_result:
            raise DataValidationError(
                f"Validación falló para {execution_func.__name__}",
                details={'data_type': type(data).__name__}
            )
        
        # Ejecutar función principal
        return execution_func(data, *args, **kwargs)
        
    except Exception as e:
        error_handler.handle_error(
            error=e,
            context={
                'validation_function': validation_func.__name__,
                'execution_function': execution_func.__name__
            },
            reraise=False
        )
        return None

def log_error_statistics():
    """Registra estadísticas de errores en el log"""
    summary = error_handler.get_error_summary()
    
    if summary['total_errors'] > 0:
        logger.info("📊 ESTADÍSTICAS DE ERRORES:")
        logger.info(f"   Total errores: {summary['total_errors']}")
        logger.info(f"   Errores recientes: {summary['recent_errors']}")
        
        if summary['categories']:
            logger.info("   Por categoría:")
            for category, count in summary['categories'].items():
                logger.info(f"     - {category}: {count}")
        
        if summary['severities']:
            logger.info("   Por severidad:")
            for severity, count in summary['severities'].items():
                logger.info(f"     - {severity}: {count}")
    else:
        logger.info("✅ No se han registrado errores")
