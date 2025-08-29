# utils/meta_learning_error_handler.py
"""
Meta-Learning Systems Error Handler
Comprehensive error handling and logging for meta-learning components
"""

import logging
import traceback
import time
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
import json
import os
from datetime import datetime

class MetaLearningError(Exception):
    """Base exception for meta-learning system errors"""
    pass

class MetaControllerError(MetaLearningError):
    """Exception for Meta-Learning Controller errors"""
    pass

class AdaptiveLearningError(MetaLearningError):
    """Exception for Adaptive Learning System errors"""
    pass

class NeuralEnhancerError(MetaLearningError):
    """Exception for Neural Enhancer errors"""
    pass

class AIEnsembleError(MetaLearningError):
    """Exception for AI Ensemble System errors"""
    pass

class MetaLearningErrorHandler:
    """Comprehensive error handler for meta-learning systems"""
    
    def __init__(self, logger: Optional[logging.Logger] = None, log_file: str = "logs/meta_learning_errors.log"):
        self.logger = logger or self._setup_logger(log_file)
        self.error_stats = {
            'meta_controller': {'total': 0, 'success': 0, 'errors': 0, 'fallbacks': 0},
            'adaptive_learning': {'total': 0, 'success': 0, 'errors': 0, 'fallbacks': 0},
            'neural_enhancer': {'total': 0, 'success': 0, 'errors': 0, 'fallbacks': 0},
            'ai_ensemble': {'total': 0, 'success': 0, 'errors': 0, 'fallbacks': 0}
        }
        self.error_log = []
        self.max_error_log_size = 1000
        
    def _setup_logger(self, log_file: str) -> logging.Logger:
        """Setup logger para manejo de errores de meta-learning"""
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logger = logging.getLogger('MetaLearningErrorHandler')
        logger.setLevel(logging.DEBUG)
        
        # Evitar duplicar handlers
        if logger.handlers:
            return logger
            
        # File handler
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def log_error(self, component: str, error_type: str, error: Exception, 
                  context: Dict[str, Any] = None, fallback_used: bool = False):
        """Log comprehensive error information"""
        
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'error_type': error_type,
            'error_message': str(error),
            'error_class': error.__class__.__name__,
            'traceback': traceback.format_exc(),
            'context': context or {},
            'fallback_used': fallback_used
        }
        
        # Add to error log
        self.error_log.append(error_info)
        
        # Maintain log size
        if len(self.error_log) > self.max_error_log_size:
            self.error_log = self.error_log[-self.max_error_log_size:]
        
        # Update statistics
        if component in self.error_stats:
            self.error_stats[component]['total'] += 1
            self.error_stats[component]['errors'] += 1
            if fallback_used:
                self.error_stats[component]['fallbacks'] += 1
        
        # Log to file
        self.logger.error(
            f"🚨 {component.upper()} ERROR - {error_type}: {str(error)}"
        )
        self.logger.debug(f"Error context: {json.dumps(context, indent=2, default=str)}")
        self.logger.debug(f"Traceback:\n{traceback.format_exc()}")
        
        if fallback_used:
            self.logger.warning(f"💡 Fallback mechanism activated for {component}")
    
    def log_success(self, component: str, operation: str, metrics: Dict[str, Any] = None):
        """Log successful operations"""
        
        if component in self.error_stats:
            self.error_stats[component]['total'] += 1
            self.error_stats[component]['success'] += 1
        
        self.logger.info(f"✅ {component.upper()} SUCCESS - {operation}")
        if metrics:
            self.logger.debug(f"Success metrics: {json.dumps(metrics, indent=2, default=str)}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        stats = {
            'components': self.error_stats.copy(),
            'total_errors': sum(comp['errors'] for comp in self.error_stats.values()),
            'total_operations': sum(comp['total'] for comp in self.error_stats.values()),
            'total_fallbacks': sum(comp['fallbacks'] for comp in self.error_stats.values()),
            'error_log_size': len(self.error_log)
        }
        
        # Calculate success rates
        for component, data in stats['components'].items():
            if data['total'] > 0:
                data['success_rate'] = data['success'] / data['total']
                data['error_rate'] = data['errors'] / data['total']
                data['fallback_rate'] = data['fallbacks'] / data['total']
            else:
                data['success_rate'] = 0.0
                data['error_rate'] = 0.0
                data['fallback_rate'] = 0.0
        
        return stats
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error entries"""
        return self.error_log[-limit:] if self.error_log else []
    
    def export_error_report(self, filename: str = None) -> str:
        """Export comprehensive error report"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/meta_learning_error_report_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_error_statistics(),
            'recent_errors': self.get_recent_errors(50),
            'system_info': {
                'error_handler_version': '1.0.0',
                'total_error_log_entries': len(self.error_log)
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
        
        self.logger.info(f"📄 Error report exported to: {filename}")
        return filename

def with_meta_learning_error_handling(component: str, operation: str = None, 
                                     fallback: Callable = None):
    """Decorator for meta-learning error handling"""
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = getattr(args[0], '_meta_error_handler', None)
            if not error_handler:
                error_handler = MetaLearningErrorHandler()
                setattr(args[0], '_meta_error_handler', error_handler)
            
            operation_name = operation or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Log success
                execution_time = time.time() - start_time
                metrics = {
                    'execution_time': execution_time,
                    'result_type': type(result).__name__,
                    'result_size': len(result) if hasattr(result, '__len__') else 'N/A'
                }
                
                error_handler.log_success(component, operation_name, metrics)
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Prepare error context
                context = {
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys()),
                    'execution_time': execution_time
                }
                
                # Determine error type based on exception
                if isinstance(e, MetaControllerError):
                    error_type = "meta_controller_error"
                elif isinstance(e, AdaptiveLearningError):
                    error_type = "adaptive_learning_error"
                elif isinstance(e, NeuralEnhancerError):
                    error_type = "neural_enhancer_error"
                elif isinstance(e, AIEnsembleError):
                    error_type = "ai_ensemble_error"
                elif isinstance(e, ImportError):
                    error_type = "module_import_error"
                elif isinstance(e, ValueError):
                    error_type = "validation_error"
                elif isinstance(e, TypeError):
                    error_type = "type_error"
                elif isinstance(e, RuntimeError):
                    error_type = "runtime_error"
                else:
                    error_type = "unknown_error"
                
                # Try fallback if available
                fallback_used = False
                if fallback:
                    try:
                        result = fallback(*args, **kwargs)
                        fallback_used = True
                        context['fallback_result_type'] = type(result).__name__
                    except Exception as fallback_error:
                        context['fallback_error'] = str(fallback_error)
                        result = []  # Default empty result
                        fallback_used = True
                else:
                    result = []  # Default empty result
                
                # Log error
                error_handler.log_error(
                    component=component,
                    error_type=error_type,
                    error=e,
                    context=context,
                    fallback_used=fallback_used
                )
                
                return result
                
        return wrapper
    return decorator

def safe_meta_learning_execution(component: str, operation: Callable, 
                                fallback_result = None, context: Dict = None) -> Any:
    """Safe execution wrapper for meta-learning operations"""
    
    error_handler = MetaLearningErrorHandler()
    
    try:
        result = operation()
        
        # Log success
        metrics = {
            'operation_type': operation.__name__ if hasattr(operation, '__name__') else 'lambda',
            'result_type': type(result).__name__,
            'context': context or {}
        }
        
        error_handler.log_success(component, 'safe_execution', metrics)
        return result
        
    except Exception as e:
        # Log error
        error_context = {
            'operation': operation.__name__ if hasattr(operation, '__name__') else 'lambda',
            'original_context': context or {}
        }
        
        error_handler.log_error(
            component=component,
            error_type='safe_execution_error',
            error=e,
            context=error_context,
            fallback_used=fallback_result is not None
        )
        
        return fallback_result if fallback_result is not None else []

# Global error handler instance
_global_meta_error_handler = None

def get_meta_learning_error_handler() -> MetaLearningErrorHandler:
    """Get global meta-learning error handler instance"""
    global _global_meta_error_handler
    if _global_meta_error_handler is None:
        _global_meta_error_handler = MetaLearningErrorHandler()
    return _global_meta_error_handler