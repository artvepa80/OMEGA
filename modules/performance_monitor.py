# OMEGA_PRO_AI_v10.1/modules/performance_monitor.py
# Comprehensive Performance Monitoring System for OMEGA AI Unified Architecture

import os
import time
import json
import psutil
import threading
import logging
from datetime import datetime, timedelta
from collections import deque, defaultdict, Counter
from typing import Dict, List, Optional, Any, Tuple, Callable
from contextlib import contextmanager
from dataclasses import dataclass, asdict
import gc
import traceback
import warnings
import numpy as np

# Configurar directorios necesarios
os.makedirs('logs/performance', exist_ok=True)
os.makedirs('reports/performance', exist_ok=True)

# Importar sistema de alertas
try:
    from modules.performance_alerts import get_alert_system, PerformanceAlertSystem
    ALERTS_AVAILABLE = True
except ImportError:
    ALERTS_AVAILABLE = False

@dataclass
class ModelPerformance:
    """Métricas de rendimiento por modelo"""
    name: str
    execution_count: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    last_execution_time: float = 0.0
    peak_memory_usage: float = 0.0
    avg_memory_usage: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    fallback_count: int = 0
    timeout_count: int = 0
    error_types: Dict[str, int] = None
    last_error: Optional[str] = None
    last_execution: Optional[str] = None
    
    def __post_init__(self):
        if self.error_types is None:
            self.error_types = defaultdict(int)

@dataclass
class SystemResources:
    """Recursos del sistema en un momento dado"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    memory_used_mb: float
    disk_usage_percent: float
    process_memory_mb: float
    process_cpu_percent: float
    active_threads: int
    open_files: int

@dataclass
class PerformanceAlert:
    """Alerta de rendimiento"""
    timestamp: str
    severity: str  # 'warning', 'critical', 'info'
    category: str  # 'timeout', 'memory', 'cpu', 'error_rate', 'degradation'
    message: str
    model_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    recommendation: Optional[str] = None

class PerformanceMonitor:
    """
    Sistema integral de monitoreo de rendimiento para OMEGA AI.
    
    Características:
    - Seguimiento de tiempo de ejecución por modelo
    - Monitoreo de uso de memoria y CPU
    - Detección de cuellos de botella
    - Sistema de alertas configurables
    - Análisis de patrones de degradación
    - Recomendaciones de optimización automáticas
    """
    
    def __init__(self, 
                 monitor_interval: float = 1.0,
                 alert_thresholds: Optional[Dict] = None,
                 history_size: int = 1000):
        
        self.monitor_interval = monitor_interval
        self.history_size = history_size
        self.start_time = time.time()
        
        # Métricas por modelo
        self.model_performances: Dict[str, ModelPerformance] = {}
        
        # Historial de recursos del sistema
        self.resource_history: deque = deque(maxlen=history_size)
        self.cpu_history: deque = deque(maxlen=100)
        self.memory_history: deque = deque(maxlen=100)
        
        # Sistema de alertas
        self.alerts: List[PerformanceAlert] = []
        self.alert_thresholds = alert_thresholds or self._get_default_thresholds()
        
        # Control de monitoreo
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Mediciones de sesión actual
        self.current_executions: Dict[str, Dict] = {}
        self.session_stats = {
            'total_models_executed': 0,
            'total_execution_time': 0.0,
            'total_timeouts': 0,
            'total_fallbacks': 0,
            'session_start': datetime.now().isoformat()
        }
        
        # Configurar logging
        self.logger = self._setup_logger()
        
        # Inicializar sistema de alertas
        self.alert_system = None
        if ALERTS_AVAILABLE:
            try:
                self.alert_system = get_alert_system()
                self.logger.info("🚨 Sistema de alertas integrado")
            except Exception as e:
                self.logger.warning(f"⚠️ No se pudo integrar sistema de alertas: {e}")
        
        # Inicializar proceso actual para monitoreo
        try:
            self.process = psutil.Process()
        except psutil.NoSuchProcess:
            self.process = None
            self.logger.warning("No se pudo inicializar monitoreo de proceso")
        
        self.logger.info("✅ Performance Monitor inicializado correctamente")
    
    def _get_default_thresholds(self) -> Dict:
        """Umbrales por defecto para alertas"""
        return {
            'max_execution_time': 30.0,  # segundos
            'max_memory_percent': 80.0,  # porcentaje
            'max_cpu_percent': 90.0,     # porcentaje
            'min_success_rate': 0.85,    # 85%
            'max_timeout_rate': 0.10,    # 10%
            'memory_growth_rate': 50.0,  # MB por minuto
            'cpu_sustained_time': 30.0,  # segundos de CPU alto
            'max_consecutive_failures': 3
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Configurar logger específico para performance"""
        logger = logging.getLogger('PerformanceMonitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Handler para archivo
            file_handler = logging.FileHandler('logs/performance/monitor.log')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Handler para consola (solo warnings y errores)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            console_formatter = logging.Formatter('%(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def start_monitoring(self):
        """Iniciar monitoreo en background"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("🔍 Monitoreo de rendimiento iniciado")
    
    def stop_monitoring(self):
        """Detener monitoreo"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        self.logger.info("⏹️ Monitoreo de rendimiento detenido")
    
    def _monitoring_loop(self):
        """Loop principal de monitoreo"""
        while self.monitoring:
            try:
                self._collect_system_metrics()
                self._check_performance_alerts()
                time.sleep(self.monitor_interval)
            except Exception as e:
                self.logger.error(f"Error en loop de monitoreo: {e}")
    
    def _collect_system_metrics(self):
        """Recolectar métricas del sistema"""
        if not self.process:
            return
        
        try:
            # Métricas del sistema
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Métricas del proceso
            process_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            process_cpu = self.process.cpu_percent()
            
            # Información del proceso
            active_threads = self.process.num_threads()
            try:
                open_files = len(self.process.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = 0
            
            resources = SystemResources(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / 1024 / 1024,
                memory_used_mb=memory.used / 1024 / 1024,
                disk_usage_percent=disk.percent,
                process_memory_mb=process_memory,
                process_cpu_percent=process_cpu,
                active_threads=active_threads,
                open_files=open_files
            )
            
            with self.lock:
                self.resource_history.append(resources)
                self.cpu_history.append(cpu_percent)
                self.memory_history.append(memory.percent)
                
        except Exception as e:
            self.logger.error(f"Error recolectando métricas: {e}")
    
    @contextmanager
    def track_model_execution(self, model_name: str, expected_duration: Optional[float] = None):
        """
        Context manager para rastrear ejecución de modelos
        
        Args:
            model_name: Nombre del modelo
            expected_duration: Duración esperada en segundos (para alertas)
        """
        start_time = time.time()
        start_memory = self._get_current_memory_usage()
        execution_id = f"{model_name}_{int(start_time)}"
        
        # Registrar inicio de ejecución
        self.current_executions[execution_id] = {
            'model_name': model_name,
            'start_time': start_time,
            'start_memory': start_memory,
            'expected_duration': expected_duration
        }
        
        # Inicializar métricas del modelo si no existen
        if model_name not in self.model_performances:
            self.model_performances[model_name] = ModelPerformance(name=model_name)
        
        try:
            yield execution_id
            # Ejecución exitosa
            self._record_successful_execution(execution_id, start_time, start_memory)
        except TimeoutError as e:
            self._record_timeout(execution_id, start_time, start_memory, str(e))
            raise
        except Exception as e:
            self._record_execution_error(execution_id, start_time, start_memory, e)
            raise
        finally:
            # Limpiar ejecución actual
            self.current_executions.pop(execution_id, None)
    
    def _record_successful_execution(self, execution_id: str, start_time: float, start_memory: float):
        """Registrar ejecución exitosa"""
        execution_time = time.time() - start_time
        current_memory = self._get_current_memory_usage()
        memory_used = max(0, current_memory - start_memory)
        
        exec_info = self.current_executions.get(execution_id)
        if not exec_info:
            return
        
        model_name = exec_info['model_name']
        
        with self.lock:
            perf = self.model_performances[model_name]
            perf.execution_count += 1
            perf.total_execution_time += execution_time
            perf.avg_execution_time = perf.total_execution_time / perf.execution_count
            perf.last_execution_time = execution_time
            perf.success_count += 1
            perf.last_execution = datetime.now().isoformat()
            
            # Actualizar uso de memoria
            if memory_used > perf.peak_memory_usage:
                perf.peak_memory_usage = memory_used
            
            if perf.execution_count > 0:
                perf.success_rate = perf.success_count / perf.execution_count
            
            # Actualizar estadísticas de sesión
            self.session_stats['total_models_executed'] += 1
            self.session_stats['total_execution_time'] += execution_time
        
        # Enviar métricas al sistema de alertas
        if self.alert_system:
            self.alert_system.check_metric('execution_time', execution_time, model_name)
            self.alert_system.check_metric('memory_usage', memory_used, model_name)
        
        self.logger.info(f"✅ {model_name} ejecutado en {execution_time:.2f}s "
                        f"(memoria: {memory_used:.1f}MB)")
    
    def _record_timeout(self, execution_id: str, start_time: float, start_memory: float, error_msg: str):
        """Registrar timeout de ejecución"""
        execution_time = time.time() - start_time
        
        exec_info = self.current_executions.get(execution_id)
        if not exec_info:
            return
        
        model_name = exec_info['model_name']
        
        with self.lock:
            perf = self.model_performances[model_name]
            perf.execution_count += 1
            perf.timeout_count += 1
            perf.total_execution_time += execution_time
            perf.avg_execution_time = perf.total_execution_time / perf.execution_count
            perf.last_execution_time = execution_time
            perf.last_error = f"TIMEOUT: {error_msg}"
            perf.last_execution = datetime.now().isoformat()
            perf.error_types['timeout'] += 1
            
            if perf.execution_count > 0:
                perf.success_rate = perf.success_count / perf.execution_count
            
            self.session_stats['total_timeouts'] += 1
        
        # Enviar métricas al sistema de alertas
        if self.alert_system:
            self.alert_system.check_metric('execution_time', execution_time, model_name)
        
        # Generar alerta de timeout
        self._add_alert(
            severity='warning',
            category='timeout',
            message=f"Modelo {model_name} excedió tiempo límite ({execution_time:.1f}s)",
            model_name=model_name,
            metric_value=execution_time,
            recommendation="Considerar optimización del modelo o incrementar timeout"
        )
        
        self.logger.warning(f"⏰ TIMEOUT: {model_name} ({execution_time:.1f}s) - {error_msg}")
    
    def _record_execution_error(self, execution_id: str, start_time: float, start_memory: float, error: Exception):
        """Registrar error de ejecución"""
        execution_time = time.time() - start_time
        
        exec_info = self.current_executions.get(execution_id)
        if not exec_info:
            return
        
        model_name = exec_info['model_name']
        error_type = type(error).__name__
        
        with self.lock:
            perf = self.model_performances[model_name]
            perf.execution_count += 1
            perf.failure_count += 1
            perf.total_execution_time += execution_time
            perf.avg_execution_time = perf.total_execution_time / perf.execution_count
            perf.last_execution_time = execution_time
            perf.last_error = f"{error_type}: {str(error)}"
            perf.last_execution = datetime.now().isoformat()
            perf.error_types[error_type] += 1
            
            if perf.execution_count > 0:
                perf.success_rate = perf.success_count / perf.execution_count
        
        # Generar alerta si hay muchos errores consecutivos
        if perf.failure_count >= self.alert_thresholds['max_consecutive_failures']:
            self._add_alert(
                severity='critical',
                category='error_rate',
                message=f"Modelo {model_name} tiene {perf.failure_count} errores consecutivos",
                model_name=model_name,
                metric_value=perf.failure_count,
                threshold_value=self.alert_thresholds['max_consecutive_failures'],
                recommendation="Revisar configuración del modelo y logs de error"
            )
        
        self.logger.error(f"❌ ERROR: {model_name} ({execution_time:.1f}s) - {error_type}: {error}")
    
    def record_fallback_usage(self, model_name: str, reason: str):
        """Registrar uso de fallback"""
        if model_name not in self.model_performances:
            self.model_performances[model_name] = ModelPerformance(name=model_name)
        
        with self.lock:
            self.model_performances[model_name].fallback_count += 1
            self.session_stats['total_fallbacks'] += 1
            fallback_count = self.model_performances[model_name].fallback_count
        
        # Enviar métricas al sistema de alertas
        if self.alert_system:
            self.alert_system.check_metric('fallback_count', fallback_count, model_name)
        
        self.logger.warning(f"🔄 FALLBACK: {model_name} - {reason}")
        
        # Alerta si hay demasiados fallbacks
        if fallback_count >= 3:
            self._add_alert(
                severity='warning',
                category='fallback',
                message=f"Modelo {model_name} ha usado fallback {fallback_count} veces",
                model_name=model_name,
                metric_value=fallback_count,
                recommendation="Investigar causa de fallos repetidos"
            )
    
    def _check_performance_alerts(self):
        """Verificar condiciones de alerta"""
        if not self.resource_history:
            return
        
        latest_resources = self.resource_history[-1]
        
        # Enviar métricas de recursos al sistema de alertas
        if self.alert_system:
            self.alert_system.check_metric('cpu_percent', latest_resources.cpu_percent)
            self.alert_system.check_metric('memory_percent', latest_resources.memory_percent)
        
        # Alertas de CPU
        if latest_resources.cpu_percent > self.alert_thresholds['max_cpu_percent']:
            self._add_alert(
                severity='warning',
                category='cpu',
                message=f"Alto uso de CPU: {latest_resources.cpu_percent:.1f}%",
                metric_value=latest_resources.cpu_percent,
                threshold_value=self.alert_thresholds['max_cpu_percent'],
                recommendation="Considerar reducir modelos concurrentes o optimizar algoritmos"
            )
        
        # Alertas de memoria
        if latest_resources.memory_percent > self.alert_thresholds['max_memory_percent']:
            self._add_alert(
                severity='critical' if latest_resources.memory_percent > 90 else 'warning',
                category='memory',
                message=f"Alto uso de memoria: {latest_resources.memory_percent:.1f}%",
                metric_value=latest_resources.memory_percent,
                threshold_value=self.alert_thresholds['max_memory_percent'],
                recommendation="Liberar memoria o reducir tamaño de datasets"
            )
        
        # Verificar crecimiento de memoria del proceso
        if len(self.resource_history) >= 10:
            memory_growth = self._calculate_memory_growth_rate()
            if memory_growth > self.alert_thresholds['memory_growth_rate']:
                self._add_alert(
                    severity='warning',
                    category='memory',
                    message=f"Crecimiento rápido de memoria: {memory_growth:.1f} MB/min",
                    metric_value=memory_growth,
                    threshold_value=self.alert_thresholds['memory_growth_rate'],
                    recommendation="Posible memory leak - revisar gestión de memoria"
                )
        
        # Verificar modelos con bajo rendimiento
        for model_name, perf in self.model_performances.items():
            if perf.execution_count >= 5 and perf.success_rate < self.alert_thresholds['min_success_rate']:
                # Enviar métrica al sistema de alertas
                if self.alert_system:
                    self.alert_system.check_metric('success_rate', perf.success_rate, model_name)
                
                self._add_alert(
                    severity='warning',
                    category='error_rate',
                    message=f"Baja tasa de éxito para {model_name}: {perf.success_rate:.1%}",
                    model_name=model_name,
                    metric_value=perf.success_rate,
                    threshold_value=self.alert_thresholds['min_success_rate'],
                    recommendation="Revisar configuración y logs del modelo"
                )
    
    def _calculate_memory_growth_rate(self) -> float:
        """Calcular tasa de crecimiento de memoria en MB/min"""
        if len(self.resource_history) < 2:
            return 0.0
        
        recent_samples = list(self.resource_history)[-10:]  # Últimas 10 muestras
        if len(recent_samples) < 2:
            return 0.0
        
        start_memory = recent_samples[0].process_memory_mb
        end_memory = recent_samples[-1].process_memory_mb
        
        start_time = datetime.fromisoformat(recent_samples[0].timestamp)
        end_time = datetime.fromisoformat(recent_samples[-1].timestamp)
        
        time_diff_minutes = (end_time - start_time).total_seconds() / 60.0
        
        if time_diff_minutes <= 0:
            return 0.0
        
        return (end_memory - start_memory) / time_diff_minutes
    
    def _add_alert(self, severity: str, category: str, message: str, 
                   model_name: Optional[str] = None, metric_value: Optional[float] = None,
                   threshold_value: Optional[float] = None, recommendation: Optional[str] = None):
        """Agregar nueva alerta"""
        alert = PerformanceAlert(
            timestamp=datetime.now().isoformat(),
            severity=severity,
            category=category,
            message=message,
            model_name=model_name,
            metric_value=metric_value,
            threshold_value=threshold_value,
            recommendation=recommendation
        )
        
        with self.lock:
            self.alerts.append(alert)
            # Mantener solo las últimas 100 alertas
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
    
    def _get_current_memory_usage(self) -> float:
        """Obtener uso actual de memoria en MB"""
        if not self.process:
            return 0.0
        try:
            return self.process.memory_info().rss / 1024 / 1024
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtener resumen completo de rendimiento"""
        with self.lock:
            # Métricas de modelos
            model_metrics = {}
            for name, perf in self.model_performances.items():
                model_metrics[name] = {
                    'execution_count': perf.execution_count,
                    'avg_execution_time': perf.avg_execution_time,
                    'last_execution_time': perf.last_execution_time,
                    'success_rate': perf.success_rate,
                    'fallback_count': perf.fallback_count,
                    'timeout_count': perf.timeout_count,
                    'peak_memory_usage': perf.peak_memory_usage,
                    'last_error': perf.last_error,
                    'error_types': dict(perf.error_types)
                }
            
            # Recursos del sistema
            current_resources = None
            if self.resource_history:
                current_resources = asdict(self.resource_history[-1])
            
            # Alertas recientes
            recent_alerts = [asdict(alert) for alert in self.alerts[-10:]]
            
            # Estadísticas de sesión
            session_duration = time.time() - self.start_time
            
            return {
                'session_info': {
                    'duration_seconds': session_duration,
                    'duration_formatted': str(timedelta(seconds=int(session_duration))),
                    **self.session_stats
                },
                'model_performance': model_metrics,
                'current_resources': current_resources,
                'recent_alerts': recent_alerts,
                'bottleneck_analysis': self._analyze_bottlenecks(),
                'optimization_recommendations': self._get_optimization_recommendations()
            }
    
    def _analyze_bottlenecks(self) -> Dict[str, Any]:
        """Analizar cuellos de botella del sistema"""
        bottlenecks = {
            'identified_bottlenecks': [],
            'slowest_models': [],
            'resource_constraints': [],
            'timeout_models': []
        }
        
        # Modelos más lentos
        slow_models = sorted(
            [(name, perf) for name, perf in self.model_performances.items() if perf.execution_count > 0],
            key=lambda x: x[1].avg_execution_time,
            reverse=True
        )[:3]
        
        for name, perf in slow_models:
            if perf.avg_execution_time > 10.0:  # Más de 10 segundos
                bottlenecks['slowest_models'].append({
                    'model': name,
                    'avg_time': perf.avg_execution_time,
                    'executions': perf.execution_count
                })
        
        # Modelos con timeouts
        for name, perf in self.model_performances.items():
            if perf.timeout_count > 0:
                bottlenecks['timeout_models'].append({
                    'model': name,
                    'timeout_count': perf.timeout_count,
                    'total_executions': perf.execution_count,
                    'timeout_rate': perf.timeout_count / perf.execution_count if perf.execution_count > 0 else 0
                })
        
        # Restricciones de recursos
        if self.resource_history:
            avg_cpu = np.mean([r.cpu_percent for r in self.resource_history[-10:]])
            avg_memory = np.mean([r.memory_percent for r in self.resource_history[-10:]])
            
            if avg_cpu > 70:
                bottlenecks['resource_constraints'].append({
                    'resource': 'CPU',
                    'avg_usage': avg_cpu,
                    'impact': 'Alto uso de CPU puede causar slowdowns'
                })
            
            if avg_memory > 75:
                bottlenecks['resource_constraints'].append({
                    'resource': 'Memory',
                    'avg_usage': avg_memory,
                    'impact': 'Alto uso de memoria puede causar swapping'
                })
        
        return bottlenecks
    
    def _get_optimization_recommendations(self) -> List[Dict[str, str]]:
        """Generar recomendaciones de optimización"""
        recommendations = []
        
        # Analizar modelos problemáticos
        for name, perf in self.model_performances.items():
            if perf.execution_count == 0:
                continue
            
            # Modelos lentos
            if perf.avg_execution_time > 20.0:
                recommendations.append({
                    'type': 'model_optimization',
                    'model': name,
                    'issue': 'Ejecución lenta',
                    'recommendation': f'Optimizar {name}: tiempo promedio {perf.avg_execution_time:.1f}s',
                    'priority': 'high' if perf.avg_execution_time > 30 else 'medium'
                })
            
            # Modelos con baja tasa de éxito
            if perf.success_rate < 0.8 and perf.execution_count >= 3:
                recommendations.append({
                    'type': 'reliability',
                    'model': name,
                    'issue': 'Baja confiabilidad',
                    'recommendation': f'Revisar configuración de {name}: tasa éxito {perf.success_rate:.1%}',
                    'priority': 'high'
                })
            
            # Modelos con timeouts frecuentes
            timeout_rate = perf.timeout_count / perf.execution_count if perf.execution_count > 0 else 0
            if timeout_rate > 0.2:  # Más del 20% de timeouts
                recommendations.append({
                    'type': 'timeout',
                    'model': name,
                    'issue': 'Timeouts frecuentes',
                    'recommendation': f'Incrementar timeout o optimizar {name}: {timeout_rate:.1%} timeouts',
                    'priority': 'medium'
                })
        
        # Recomendaciones de recursos
        if self.resource_history:
            latest = self.resource_history[-1]
            
            if latest.memory_percent > 85:
                recommendations.append({
                    'type': 'resource',
                    'issue': 'Alto uso de memoria',
                    'recommendation': 'Considerar incrementar RAM o reducir datasets simultáneos',
                    'priority': 'high'
                })
            
            if latest.cpu_percent > 90:
                recommendations.append({
                    'type': 'resource',
                    'issue': 'Alto uso de CPU',
                    'recommendation': 'Reducir modelos concurrentes o usar CPU con más núcleos',
                    'priority': 'medium'
                })
        
        return sorted(recommendations, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x.get('priority', 'low')])
    
    def export_performance_report(self, filepath: Optional[str] = None) -> str:
        """Exportar reporte completo de rendimiento"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"reports/performance/performance_report_{timestamp}.json"
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        report = {
            'report_info': {
                'generated_at': datetime.now().isoformat(),
                'monitor_duration_seconds': time.time() - self.start_time,
                'version': 'OMEGA_AI_v10.1'
            },
            'performance_summary': self.get_performance_summary(),
            'detailed_metrics': {
                'model_performances': {
                    name: asdict(perf) for name, perf in self.model_performances.items()
                },
                'resource_history': [asdict(r) for r in list(self.resource_history)[-50:]],  # Últimos 50 registros
                'all_alerts': [asdict(alert) for alert in self.alerts]
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"📊 Reporte de rendimiento exportado: {filepath}")
        return filepath
    
    def print_performance_summary(self):
        """Imprimir resumen de rendimiento en consola"""
        summary = self.get_performance_summary()
        
        print("\n" + "="*80)
        print("🔍 OMEGA AI - RESUMEN DE RENDIMIENTO")
        print("="*80)
        
        # Información de sesión
        session = summary['session_info']
        print(f"⏱️  Duración de sesión: {session['duration_formatted']}")
        print(f"🎯 Modelos ejecutados: {session['total_models_executed']}")
        print(f"⏰ Tiempo total ejecución: {session['total_execution_time']:.1f}s")
        print(f"⚠️  Timeouts totales: {session['total_timeouts']}")
        print(f"🔄 Fallbacks totales: {session['total_fallbacks']}")
        
        # Rendimiento por modelo
        print("\n📊 RENDIMIENTO POR MODELO:")
        print("-" * 80)
        model_perf = summary['model_performance']
        
        if model_perf:
            print(f"{'Modelo':<20} {'Ejec.':<6} {'Tiempo Prom.':<12} {'Éxito':<8} {'Timeouts':<9} {'Fallbacks':<10}")
            print("-" * 80)
            
            for model_name, metrics in model_perf.items():
                exec_count = metrics['execution_count']
                avg_time = metrics['avg_execution_time']
                success_rate = metrics['success_rate']
                timeouts = metrics['timeout_count']
                fallbacks = metrics['fallback_count']
                
                print(f"{model_name:<20} {exec_count:<6} {avg_time:<12.1f} "
                      f"{success_rate:<8.1%} {timeouts:<9} {fallbacks:<10}")
        else:
            print("No hay datos de modelos ejecutados")
        
        # Recursos actuales
        print("\n💻 RECURSOS DEL SISTEMA:")
        print("-" * 40)
        if summary['current_resources']:
            resources = summary['current_resources']
            print(f"CPU: {resources['cpu_percent']:.1f}%")
            print(f"Memoria: {resources['memory_percent']:.1f}% ({resources['process_memory_mb']:.1f}MB proceso)")
            print(f"Hilos activos: {resources['active_threads']}")
            print(f"Archivos abiertos: {resources['open_files']}")
        
        # Alertas recientes
        recent_alerts = summary['recent_alerts']
        if recent_alerts:
            print("\n⚠️  ALERTAS RECIENTES:")
            print("-" * 60)
            for alert in recent_alerts[-5:]:  # Últimas 5 alertas
                severity_emoji = {"warning": "⚠️", "critical": "🚨", "info": "ℹ️"}.get(alert['severity'], "•")
                print(f"{severity_emoji} [{alert['severity'].upper()}] {alert['message']}")
                if alert.get('recommendation'):
                    print(f"   💡 {alert['recommendation']}")
        
        # Cuellos de botella
        bottlenecks = summary['bottleneck_analysis']
        if any(bottlenecks.values()):
            print("\n🚧 CUELLOS DE BOTELLA IDENTIFICADOS:")
            print("-" * 50)
            
            if bottlenecks['slowest_models']:
                print("⏳ Modelos más lentos:")
                for model_info in bottlenecks['slowest_models']:
                    print(f"   • {model_info['model']}: {model_info['avg_time']:.1f}s promedio")
            
            if bottlenecks['timeout_models']:
                print("⏰ Modelos con timeouts:")
                for model_info in bottlenecks['timeout_models']:
                    print(f"   • {model_info['model']}: {model_info['timeout_count']} timeouts "
                          f"({model_info['timeout_rate']:.1%})")
            
            if bottlenecks['resource_constraints']:
                print("💻 Restricciones de recursos:")
                for constraint in bottlenecks['resource_constraints']:
                    print(f"   • {constraint['resource']}: {constraint['avg_usage']:.1f}% - "
                          f"{constraint['impact']}")
        
        # Recomendaciones de optimización
        recommendations = summary['optimization_recommendations']
        if recommendations:
            print("\n💡 RECOMENDACIONES DE OPTIMIZACIÓN:")
            print("-" * 60)
            for rec in recommendations[:5]:  # Top 5 recomendaciones
                priority_emoji = {"high": "🔥", "medium": "⚠️", "low": "ℹ️"}.get(rec.get('priority', 'low'), "•")
                print(f"{priority_emoji} {rec['recommendation']}")
        
        print("\n" + "="*80)

# Instancia global del monitor
_performance_monitor: Optional[PerformanceMonitor] = None

def get_performance_monitor() -> PerformanceMonitor:
    """Obtener instancia global del monitor de rendimiento"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
        _performance_monitor.start_monitoring()
    return _performance_monitor

def initialize_performance_monitoring(config: Optional[Dict] = None) -> PerformanceMonitor:
    """Inicializar sistema de monitoreo con configuración personalizada"""
    global _performance_monitor
    
    if config is None:
        config = {}
    
    _performance_monitor = PerformanceMonitor(
        monitor_interval=config.get('monitor_interval', 1.0),
        alert_thresholds=config.get('alert_thresholds'),
        history_size=config.get('history_size', 1000)
    )
    
    _performance_monitor.start_monitoring()
    return _performance_monitor

def shutdown_performance_monitoring():
    """Cerrar sistema de monitoreo"""
    global _performance_monitor
    if _performance_monitor:
        _performance_monitor.stop_monitoring()
        _performance_monitor = None