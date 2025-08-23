#!/usr/bin/env python3
"""
📊 OMEGA Metrics Collector - Sistema de Métricas y Monitoreo
Recolección centralizada de métricas de performance y sistema
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from src.utils.logger_factory import LoggerFactory

@dataclass
class MetricPoint:
    """Punto de métrica individual"""
    timestamp: float
    value: float
    labels: Dict[str, str]

@dataclass
class TimingMetric:
    """Métrica de tiempo"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    labels: Dict[str, str] = None

class MetricsCollector:
    """
    Recolector centralizado de métricas
    Thread-safe y optimizado para alta frecuencia
    """
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.cutoff_time = time.time() - (retention_hours * 3600)
        
        # Storage thread-safe
        self._lock = threading.RLock()
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._timers: Dict[str, TimingMetric] = {}
        self._errors: Dict[str, int] = defaultdict(int)
        
        # Sistema metrics
        self._system_metrics_enabled = True
        self._last_system_check = 0
        self._system_check_interval = 60  # seconds
        
        # Performance tracking
        self._performance_stats: Dict[str, Dict] = defaultdict(dict)
        
        # Logger
        self.logger = LoggerFactory.get_logger("MetricsCollector")
        
        # Iniciar recolección de métricas del sistema
        self._start_system_metrics()
    
    def increment(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Incrementa contador"""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
            
            self.logger.debug(f"📈 Counter incremented: {name} +{value}")
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Establece valor de gauge"""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
            
            self.logger.debug(f"📊 Gauge set: {name} = {value}")
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Registra valor en histograma"""
        with self._lock:
            key = self._make_key(name, labels)
            metric_point = MetricPoint(
                timestamp=time.time(),
                value=value,
                labels=labels or {}
            )
            self._histograms[key].append(metric_point)
            
            self.logger.debug(f"📉 Histogram recorded: {name} = {value}")
    
    def start_timing(self, name: str, labels: Dict[str, str] = None) -> str:
        """Inicia medición de tiempo"""
        timing_id = f"{name}_{time.time()}_{threading.current_thread().ident}"
        
        with self._lock:
            self._timers[timing_id] = TimingMetric(
                name=name,
                start_time=time.time(),
                labels=labels or {}
            )
        
        self.logger.debug(f"⏱️ Timer started: {name}")
        return timing_id
    
    def end_timing(self, timing_id: str) -> float:
        """Finaliza medición de tiempo"""
        end_time = time.time()
        
        with self._lock:
            if timing_id in self._timers:
                timer = self._timers[timing_id]
                timer.end_time = end_time
                timer.duration = end_time - timer.start_time
                
                # Registrar en histograma
                self.record_histogram(
                    f"{timer.name}_duration", 
                    timer.duration * 1000,  # En milliseconds
                    timer.labels
                )
                
                duration = timer.duration
                del self._timers[timing_id]
                
                self.logger.debug(f"⏱️ Timer ended: {timer.name} = {duration*1000:.2f}ms")
                return duration
        
        return 0.0
    
    def record(self, name: str, value: float, labels: Dict[str, str] = None):
        """Registra métrica genérica"""
        self.record_histogram(name, value, labels)
    
    def record_error(self, error_type: str, message: str = "", labels: Dict[str, str] = None):
        """Registra error"""
        with self._lock:
            key = self._make_key(f"error_{error_type}", labels)
            self._errors[key] += 1
        
        self.logger.warning(f"🚨 Error recorded: {error_type} - {message}")
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Crea clave única para métrica con labels"""
        if not labels:
            return name
        
        label_str = ",".join([f"{k}={v}" for k, v in sorted(labels.items())])
        return f"{name}{{{label_str}}}"
    
    def _start_system_metrics(self):
        """Inicia recolección de métricas del sistema"""
        def collect_system_metrics():
            while self._system_metrics_enabled:
                try:
                    now = time.time()
                    if now - self._last_system_check >= self._system_check_interval:
                        self._collect_system_metrics()
                        self._last_system_check = now
                    
                    time.sleep(10)  # Check every 10 seconds
                except Exception as e:
                    self.logger.error(f"Error collecting system metrics: {e}")
                    time.sleep(30)  # Longer wait on error
        
        thread = threading.Thread(target=collect_system_metrics, daemon=True)
        thread.start()
    
    def _collect_system_metrics(self):
        """Recolecta métricas del sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.set_gauge("system_cpu_percent", cpu_percent)
            
            # Memoria
            memory = psutil.virtual_memory()
            self.set_gauge("system_memory_percent", memory.percent)
            self.set_gauge("system_memory_used_bytes", memory.used)
            self.set_gauge("system_memory_available_bytes", memory.available)
            
            # Disco
            disk = psutil.disk_usage('/')
            self.set_gauge("system_disk_percent", (disk.used / disk.total) * 100)
            self.set_gauge("system_disk_used_bytes", disk.used)
            self.set_gauge("system_disk_free_bytes", disk.free)
            
            # Network (si está disponible)
            try:
                network = psutil.net_io_counters()
                self.increment("system_network_bytes_sent", network.bytes_sent)
                self.increment("system_network_bytes_recv", network.bytes_recv)
            except:
                pass  # Network stats might not be available
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def get_counter(self, name: str, labels: Dict[str, str] = None) -> float:
        """Obtiene valor de contador"""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)
    
    def get_gauge(self, name: str, labels: Dict[str, str] = None) -> Optional[float]:
        """Obtiene valor de gauge"""
        key = self._make_key(name, labels)
        return self._gauges.get(key)
    
    def get_histogram_stats(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Obtiene estadísticas de histograma"""
        key = self._make_key(name, labels)
        
        if key not in self._histograms:
            return {}
        
        values = [point.value for point in self._histograms[key]]
        
        if not values:
            return {}
        
        values.sort()
        n = len(values)
        
        return {
            "count": n,
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / n,
            "p50": values[n // 2],
            "p90": values[int(n * 0.9)] if n > 1 else values[0],
            "p95": values[int(n * 0.95)] if n > 1 else values[0],
            "p99": values[int(n * 0.99)] if n > 1 else values[0]
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene resumen completo de métricas"""
        with self._lock:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "errors": dict(self._errors),
                "active_timers": len(self._timers),
                "system_metrics": self._get_system_summary()
            }
        
        return summary
    
    def _get_system_summary(self) -> Dict[str, Any]:
        """Resumen de métricas del sistema"""
        return {
            "cpu_percent": self.get_gauge("system_cpu_percent"),
            "memory_percent": self.get_gauge("system_memory_percent"),
            "memory_used_mb": (self.get_gauge("system_memory_used_bytes") or 0) / (1024 * 1024),
            "disk_percent": self.get_gauge("system_disk_percent"),
            "disk_free_gb": (self.get_gauge("system_disk_free_bytes") or 0) / (1024 * 1024 * 1024)
        }
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Obtiene uso de memoria detallado"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "rss_mb": memory_info.rss / (1024 * 1024),
                "vms_mb": memory_info.vms / (1024 * 1024),
                "percent": process.memory_percent(),
                "available_mb": psutil.virtual_memory().available / (1024 * 1024)
            }
        except:
            return {}
    
    def cleanup_old_metrics(self):
        """Limpia métricas antiguas"""
        cutoff_time = time.time() - (self.retention_hours * 3600)
        
        with self._lock:
            for key in list(self._histograms.keys()):
                histogram = self._histograms[key]
                # Filtrar puntos antiguos
                while histogram and histogram[0].timestamp < cutoff_time:
                    histogram.popleft()
                
                # Eliminar histogramas vacíos
                if not histogram:
                    del self._histograms[key]
        
        self.logger.debug("🧹 Old metrics cleaned up")
    
    def export_metrics(self, format: str = "json") -> str:
        """Exporta métricas en formato especificado"""
        if format.lower() == "prometheus":
            return self._export_prometheus()
        else:
            return json.dumps(self.get_summary(), indent=2, default=str)
    
    def _export_prometheus(self) -> str:
        """Exporta métricas en formato Prometheus"""
        lines = []
        
        # Counters
        for key, value in self._counters.items():
            lines.append(f"omega_counter_{key} {value}")
        
        # Gauges
        for key, value in self._gauges.items():
            lines.append(f"omega_gauge_{key} {value}")
        
        # Errores
        for key, value in self._errors.items():
            lines.append(f"omega_error_{key} {value}")
        
        return "\n".join(lines)
    
    def save_metrics_to_file(self, file_path: str):
        """Guarda métricas a archivo"""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(self.get_summary(), f, indent=2, default=str)
            
            self.logger.info(f"💾 Métricas guardadas en: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving metrics: {e}")
    
    async def export_session_metrics(self, session_id: str):
        """Exporta métricas de sesión"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = f"logs/session_metrics_{session_id}_{timestamp}.json"
        
        session_summary = {
            "session_id": session_id,
            "export_time": datetime.now().isoformat(),
            "metrics": self.get_summary()
        }
        
        try:
            with open(metrics_file, 'w') as f:
                json.dump(session_summary, f, indent=2, default=str)
            
            self.logger.info(f"📊 Métricas de sesión exportadas: {metrics_file}")
            
        except Exception as e:
            self.logger.error(f"Error exporting session metrics: {e}")
    
    def stop(self):
        """Detiene recolección de métricas"""
        self._system_metrics_enabled = False
        self.logger.info("🛑 Metrics collector stopped")

# Decorador para métricas automáticas
def track_metrics(metrics_collector: MetricsCollector, metric_name: str = None):
    """Decorador para tracking automático de métricas"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            name = metric_name or f"{func.__module__}.{func.__name__}"
            
            # Incrementar contador de llamadas
            metrics_collector.increment(f"{name}_calls")
            
            # Medir tiempo de ejecución
            timer_id = metrics_collector.start_timing(f"{name}_duration")
            
            try:
                result = func(*args, **kwargs)
                metrics_collector.increment(f"{name}_success")
                return result
            except Exception as e:
                metrics_collector.record_error(f"{name}_error", str(e))
                metrics_collector.increment(f"{name}_failures")
                raise
            finally:
                metrics_collector.end_timing(timer_id)
        
        return wrapper
    return decorator