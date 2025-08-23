#!/usr/bin/env python3
"""
📊 OMEGA Advanced Monitoring - Sistema de Monitoreo Avanzado
Alertas inteligentes, dashboards automáticos y análisis predictivo
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from pathlib import Path
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from src.utils.logger_factory import LoggerFactory
from src.monitoring.metrics_collector import MetricsCollector
from src.services.cache_service import CacheService

class AlertSeverity(Enum):
    """Severidad de alertas"""
    INFO = "info"
    WARNING = "warning" 
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertStatus(Enum):
    """Estado de alertas"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class AlertRule:
    """Regla de alerta"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # e.g., ">" "<" "==" "!="
    threshold: float
    severity: AlertSeverity
    cooldown_minutes: int = 5
    enabled: bool = True
    tags: List[str] = None

@dataclass
class Alert:
    """Alerta individual"""
    alert_id: str
    rule_id: str
    severity: AlertSeverity
    title: str
    description: str
    current_value: float
    threshold: float
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

@dataclass
class HealthCheck:
    """Check de salud de componente"""
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    last_check: datetime
    response_time: float
    details: Dict[str, Any] = None
    error_message: Optional[str] = None

class AlertManager:
    """Gestor de alertas inteligente"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.logger = LoggerFactory.get_logger("AlertManager")
        
        # Storage
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # Configuration
        self.config = {
            'max_alert_history': 1000,
            'batch_evaluation_interval': 30,  # seconds
            'notification_cooldown': 300,  # seconds
            'auto_resolution_timeout': 3600,  # 1 hour
        }
        
        # Notification channels
        self.notification_channels = {}
        
        # Initialize default rules
        self._create_default_alert_rules()
        
        # Start background tasks
        self._start_alert_evaluation_loop()
    
    def _create_default_alert_rules(self):
        """Crea reglas de alerta por defecto"""
        default_rules = [
            AlertRule(
                rule_id="high_error_rate",
                name="High Error Rate",
                description="Error rate above threshold",
                metric_name="error_rate",
                condition=">",
                threshold=0.05,  # 5%
                severity=AlertSeverity.WARNING,
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="high_response_time",
                name="High Response Time",
                description="API response time above threshold",
                metric_name="api_request_duration_seconds_p95",
                condition=">",
                threshold=3.0,  # 3 seconds
                severity=AlertSeverity.WARNING,
                cooldown_minutes=3
            ),
            AlertRule(
                rule_id="high_memory_usage",
                name="High Memory Usage",
                description="Memory usage above threshold",
                metric_name="system_memory_percent",
                condition=">",
                threshold=85.0,  # 85%
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=2
            ),
            AlertRule(
                rule_id="high_cpu_usage",
                name="High CPU Usage",
                description="CPU usage above threshold",
                metric_name="system_cpu_percent",
                condition=">",
                threshold=90.0,  # 90%
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=2
            ),
            AlertRule(
                rule_id="model_prediction_failure",
                name="Model Prediction Failures",
                description="Model prediction failure rate too high",
                metric_name="model_prediction_failure_rate",
                condition=">",
                threshold=0.1,  # 10%
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=1
            ),
            AlertRule(
                rule_id="cache_miss_rate_high",
                name="High Cache Miss Rate",
                description="Cache effectiveness degraded",
                metric_name="cache_miss_rate",
                condition=">",
                threshold=0.5,  # 50%
                severity=AlertSeverity.WARNING,
                cooldown_minutes=10
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
        
        self.logger.info(f"📋 Created {len(default_rules)} default alert rules")
    
    def add_alert_rule(self, rule: AlertRule):
        """Agrega nueva regla de alerta"""
        self.alert_rules[rule.rule_id] = rule
        self.logger.info(f"📝 Added alert rule: {rule.name}")
    
    def _start_alert_evaluation_loop(self):
        """Inicia loop de evaluación de alertas"""
        async def evaluation_loop():
            while True:
                try:
                    await self._evaluate_alert_rules()
                    await asyncio.sleep(self.config['batch_evaluation_interval'])
                except Exception as e:
                    self.logger.error(f"Error in alert evaluation loop: {e}")
                    await asyncio.sleep(60)  # Longer wait on error
        
        asyncio.create_task(evaluation_loop())
        self.logger.info("🔄 Alert evaluation loop started")
    
    async def _evaluate_alert_rules(self):
        """Evalúa todas las reglas de alerta"""
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue
            
            try:
                await self._evaluate_single_rule(rule)
            except Exception as e:
                self.logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
    
    async def _evaluate_single_rule(self, rule: AlertRule):
        """Evalúa una regla individual"""
        # Obtener valor actual de la métrica
        current_value = self._get_metric_value(rule.metric_name)
        
        if current_value is None:
            return
        
        # Evaluar condición
        condition_met = self._evaluate_condition(
            current_value, rule.condition, rule.threshold
        )
        
        existing_alert = self._find_active_alert_for_rule(rule.rule_id)
        
        if condition_met:
            if not existing_alert:
                # Verificar cooldown
                if not self._is_in_cooldown(rule.rule_id):
                    await self._create_alert(rule, current_value)
            else:
                # Actualizar alerta existente
                existing_alert.current_value = current_value
                existing_alert.timestamp = datetime.now()
        
        else:
            # Condición no se cumple - resolver alerta si existe
            if existing_alert:
                await self._resolve_alert(existing_alert.alert_id, "condition_resolved")
    
    def _get_metric_value(self, metric_name: str) -> Optional[float]:
        """Obtiene valor actual de métrica"""
        try:
            # Mapeo de nombres de métricas especiales
            if metric_name == "error_rate":
                errors = self.metrics.get_counter("prediction_errors") or 0
                total = self.metrics.get_counter("predictions_generated") or 1
                return errors / total
            
            elif metric_name == "cache_miss_rate":
                misses = self.metrics.get_counter("cache_misses") or 0
                hits = self.metrics.get_counter("cache_hits") or 0
                total = misses + hits
                return misses / total if total > 0 else 0
            
            elif metric_name == "model_prediction_failure_rate":
                failures = self.metrics.get_counter("model_prediction_failures") or 0
                total = self.metrics.get_counter("model_predictions_total") or 1
                return failures / total
            
            elif metric_name.endswith("_p95"):
                # Percentile metric
                base_metric = metric_name.replace("_p95", "")
                stats = self.metrics.get_histogram_stats(base_metric)
                return stats.get("p95", 0.0)
            
            else:
                # Gauge metric
                return self.metrics.get_gauge(metric_name)
                
        except Exception as e:
            self.logger.error(f"Error getting metric {metric_name}: {e}")
            return None
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evalúa condición de alerta"""
        if condition == ">":
            return value > threshold
        elif condition == "<":
            return value < threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return abs(value - threshold) < 0.001
        elif condition == "!=":
            return abs(value - threshold) >= 0.001
        else:
            return False
    
    def _find_active_alert_for_rule(self, rule_id: str) -> Optional[Alert]:
        """Encuentra alerta activa para regla específica"""
        for alert in self.active_alerts.values():
            if alert.rule_id == rule_id and alert.status == AlertStatus.ACTIVE:
                return alert
        return None
    
    def _is_in_cooldown(self, rule_id: str) -> bool:
        """Verifica si regla está en cooldown"""
        cooldown_time = self.alert_rules[rule_id].cooldown_minutes * 60
        
        # Buscar última alerta de esta regla
        for alert in reversed(self.alert_history):
            if alert.rule_id == rule_id:
                time_since = (datetime.now() - alert.timestamp).total_seconds()
                return time_since < cooldown_time
        
        return False
    
    async def _create_alert(self, rule: AlertRule, current_value: float):
        """Crea nueva alerta"""
        alert_id = f"alert_{int(time.time())}_{rule.rule_id}"
        
        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            severity=rule.severity,
            title=rule.name,
            description=f"{rule.description}. Current: {current_value}, Threshold: {rule.threshold}",
            current_value=current_value,
            threshold=rule.threshold,
            timestamp=datetime.now(),
            metadata={
                "metric_name": rule.metric_name,
                "condition": rule.condition
            }
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Mantener historial limitado
        if len(self.alert_history) > self.config['max_alert_history']:
            self.alert_history = self.alert_history[-self.config['max_alert_history']:]
        
        self.logger.warning(f"🚨 Alert created: {alert.title} ({alert.severity.value})")
        
        # Enviar notificación
        await self._send_alert_notification(alert)
        
        # Registrar métrica
        self.metrics.increment(
            "alerts_created", 
            labels={"severity": alert.severity.value, "rule": rule.rule_id}
        )
    
    async def _resolve_alert(self, alert_id: str, reason: str):
        """Resuelve alerta"""
        if alert_id not in self.active_alerts:
            return
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()
        
        if alert.metadata is None:
            alert.metadata = {}
        alert.metadata['resolution_reason'] = reason
        
        del self.active_alerts[alert_id]
        
        self.logger.info(f"✅ Alert resolved: {alert.title} (reason: {reason})")
        
        # Enviar notificación de resolución
        await self._send_resolution_notification(alert)
    
    async def _send_alert_notification(self, alert: Alert):
        """Envía notificación de alerta"""
        try:
            # Determinar canales según severidad
            channels = []
            
            if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
                channels.extend(["email", "slack", "webhook"])
            elif alert.severity == AlertSeverity.WARNING:
                channels.extend(["slack", "webhook"])
            else:
                channels.extend(["webhook"])
            
            for channel in channels:
                if channel in self.notification_channels:
                    await self._send_to_channel(channel, alert, "alert")
            
        except Exception as e:
            self.logger.error(f"Error sending alert notification: {e}")
    
    async def _send_resolution_notification(self, alert: Alert):
        """Envía notificación de resolución"""
        try:
            for channel in ["slack", "webhook"]:  # Menos invasivo para resoluciones
                if channel in self.notification_channels:
                    await self._send_to_channel(channel, alert, "resolution")
        
        except Exception as e:
            self.logger.error(f"Error sending resolution notification: {e}")
    
    async def _send_to_channel(self, channel: str, alert: Alert, notification_type: str):
        """Envía notificación a canal específico"""
        # Implementación específica por canal
        if channel == "webhook":
            await self._send_webhook_notification(alert, notification_type)
        elif channel == "email":
            await self._send_email_notification(alert, notification_type)
        elif channel == "slack":
            await self._send_slack_notification(alert, notification_type)
    
    async def _send_webhook_notification(self, alert: Alert, notification_type: str):
        """Envía notificación por webhook"""
        # Placeholder - integrar con sistema de webhooks
        self.logger.info(f"📬 Webhook notification: {alert.title}")
    
    def configure_notification_channel(self, channel_type: str, config: Dict[str, Any]):
        """Configura canal de notificación"""
        self.notification_channels[channel_type] = config
        self.logger.info(f"📧 Configured notification channel: {channel_type}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Obtiene alertas activas"""
        return [asdict(alert) for alert in self.active_alerts.values()]
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de alertas"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_week = now - timedelta(days=7)
        
        alerts_24h = [a for a in self.alert_history if a.timestamp >= last_24h]
        alerts_week = [a for a in self.alert_history if a.timestamp >= last_week]
        
        return {
            "active_alerts": len(self.active_alerts),
            "alerts_last_24h": len(alerts_24h),
            "alerts_last_week": len(alerts_week),
            "alerts_by_severity": {
                severity.value: len([a for a in alerts_24h if a.severity == severity])
                for severity in AlertSeverity
            },
            "top_alert_rules": self._get_top_alert_rules(),
            "average_resolution_time": self._calculate_average_resolution_time()
        }
    
    def _get_top_alert_rules(self) -> List[Dict[str, Any]]:
        """Obtiene reglas de alerta más frecuentes"""
        rule_counts = {}
        
        for alert in self.alert_history[-100:]:  # Últimas 100 alertas
            rule_counts[alert.rule_id] = rule_counts.get(alert.rule_id, 0) + 1
        
        sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                "rule_id": rule_id,
                "rule_name": self.alert_rules.get(rule_id, {}).name if rule_id in self.alert_rules else rule_id,
                "count": count
            }
            for rule_id, count in sorted_rules[:5]
        ]
    
    def _calculate_average_resolution_time(self) -> float:
        """Calcula tiempo promedio de resolución"""
        resolved_alerts = [
            a for a in self.alert_history 
            if a.status == AlertStatus.RESOLVED and a.resolved_at
        ]
        
        if not resolved_alerts:
            return 0.0
        
        resolution_times = [
            (a.resolved_at - a.timestamp).total_seconds()
            for a in resolved_alerts
        ]
        
        return np.mean(resolution_times) / 60  # en minutos

class HealthMonitor:
    """Monitor de salud de componentes del sistema"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.logger = LoggerFactory.get_logger("HealthMonitor")
        
        # Storage
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_functions: Dict[str, Callable] = {}
        
        # Configuration
        self.config = {
            'check_interval_seconds': 60,
            'timeout_seconds': 10,
            'max_check_history': 100
        }
        
        # Register default health checks
        self._register_default_checks()
        
        # Start monitoring loop
        self._start_health_monitoring_loop()
    
    def _register_default_checks(self):
        """Registra health checks por defecto"""
        self.register_health_check("api", self._check_api_health)
        self.register_health_check("database", self._check_database_health)
        self.register_health_check("cache", self._check_cache_health)
        self.register_health_check("models", self._check_models_health)
        self.register_health_check("disk_space", self._check_disk_space)
    
    def register_health_check(self, component: str, check_function: Callable):
        """Registra función de health check"""
        self.check_functions[component] = check_function
        self.logger.info(f"🏥 Registered health check: {component}")
    
    def _start_health_monitoring_loop(self):
        """Inicia loop de monitoreo de salud"""
        async def monitoring_loop():
            while True:
                try:
                    await self._run_all_health_checks()
                    await asyncio.sleep(self.config['check_interval_seconds'])
                except Exception as e:
                    self.logger.error(f"Error in health monitoring loop: {e}")
                    await asyncio.sleep(120)  # Longer wait on error
        
        asyncio.create_task(monitoring_loop())
        self.logger.info("🔄 Health monitoring loop started")
    
    async def _run_all_health_checks(self):
        """Ejecuta todos los health checks"""
        tasks = []
        
        for component, check_func in self.check_functions.items():
            task = self._run_single_health_check(component, check_func)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _run_single_health_check(self, component: str, check_function: Callable):
        """Ejecuta health check individual"""
        start_time = time.time()
        
        try:
            # Ejecutar check con timeout
            result = await asyncio.wait_for(
                check_function(),
                timeout=self.config['timeout_seconds']
            )
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            health_check = HealthCheck(
                component=component,
                status=result.get('status', 'healthy'),
                last_check=datetime.now(),
                response_time=response_time,
                details=result.get('details', {}),
                error_message=result.get('error')
            )
            
            self.health_checks[component] = health_check
            
            # Registrar métrica
            self.metrics.set_gauge(
                f"health_check_{component}_status",
                1.0 if health_check.status == 'healthy' else 0.0
            )
            self.metrics.record_histogram(
                f"health_check_{component}_response_time",
                response_time
            )
            
        except asyncio.TimeoutError:
            health_check = HealthCheck(
                component=component,
                status='unhealthy',
                last_check=datetime.now(),
                response_time=(time.time() - start_time) * 1000,
                error_message="Health check timeout"
            )
            
            self.health_checks[component] = health_check
            self.logger.warning(f"🏥 Health check timeout: {component}")
            
        except Exception as e:
            health_check = HealthCheck(
                component=component,
                status='unhealthy',
                last_check=datetime.now(),
                response_time=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
            
            self.health_checks[component] = health_check
            self.logger.error(f"🏥 Health check failed: {component} - {e}")
    
    async def _check_api_health(self) -> Dict[str, Any]:
        """Health check para API"""
        try:
            # Simular check de API
            await asyncio.sleep(0.01)  # Simular latencia
            
            return {
                'status': 'healthy',
                'details': {
                    'endpoints_active': True,
                    'response_time_ok': True
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Health check para base de datos"""
        try:
            # Placeholder - implementar check real
            return {
                'status': 'healthy',
                'details': {
                    'connection_active': True,
                    'query_response_ok': True
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_cache_health(self) -> Dict[str, Any]:
        """Health check para caché"""
        try:
            # Simular test de cache
            cache_hits = self.metrics.get_counter("cache_hits") or 0
            cache_misses = self.metrics.get_counter("cache_misses") or 0
            total = cache_hits + cache_misses
            
            hit_rate = cache_hits / total if total > 0 else 1.0
            
            status = 'healthy' if hit_rate > 0.5 else 'degraded'
            
            return {
                'status': status,
                'details': {
                    'hit_rate': hit_rate,
                    'total_operations': total
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_models_health(self) -> Dict[str, Any]:
        """Health check para modelos"""
        try:
            # Verificar estado de modelos
            model_errors = self.metrics.get_counter("model_prediction_failures") or 0
            model_predictions = self.metrics.get_counter("model_predictions_total") or 1
            
            error_rate = model_errors / model_predictions
            
            if error_rate < 0.05:
                status = 'healthy'
            elif error_rate < 0.15:
                status = 'degraded' 
            else:
                status = 'unhealthy'
            
            return {
                'status': status,
                'details': {
                    'error_rate': error_rate,
                    'total_predictions': model_predictions
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Health check para espacio en disco"""
        try:
            import psutil
            
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            if free_percent > 20:
                status = 'healthy'
            elif free_percent > 10:
                status = 'degraded'
            else:
                status = 'unhealthy'
            
            return {
                'status': status,
                'details': {
                    'free_percent': free_percent,
                    'free_gb': disk_usage.free / (1024**3)
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Obtiene estado de salud general del sistema"""
        if not self.health_checks:
            return {'status': 'unknown', 'components': {}}
        
        component_statuses = [check.status for check in self.health_checks.values()]
        
        if all(status == 'healthy' for status in component_statuses):
            overall_status = 'healthy'
        elif any(status == 'unhealthy' for status in component_statuses):
            overall_status = 'unhealthy'
        else:
            overall_status = 'degraded'
        
        return {
            'status': overall_status,
            'last_check': max(check.last_check for check in self.health_checks.values()).isoformat(),
            'components': {
                name: {
                    'status': check.status,
                    'response_time_ms': check.response_time,
                    'last_check': check.last_check.isoformat(),
                    'error': check.error_message
                }
                for name, check in self.health_checks.items()
            }
        }

class AdvancedMonitoringSystem:
    """Sistema completo de monitoreo avanzado"""
    
    def __init__(self, metrics_collector: MetricsCollector, cache_service: Optional[CacheService] = None):
        self.metrics = metrics_collector
        self.cache_service = cache_service
        self.logger = LoggerFactory.get_logger("AdvancedMonitoring")
        
        # Componentes
        self.alert_manager = AlertManager(metrics_collector)
        self.health_monitor = HealthMonitor(metrics_collector)
        
        # Dashboard data
        self.dashboard_data = {}
        
        # Configuration
        self.config = {
            'dashboard_refresh_interval': 30,  # seconds
            'data_retention_days': 30
        }
        
        # Start background tasks
        self._start_dashboard_update_loop()
        
        self.logger.info("📊 Advanced Monitoring System initialized")
    
    def _start_dashboard_update_loop(self):
        """Inicia loop de actualización de dashboard"""
        async def dashboard_loop():
            while True:
                try:
                    await self._update_dashboard_data()
                    await asyncio.sleep(self.config['dashboard_refresh_interval'])
                except Exception as e:
                    self.logger.error(f"Error updating dashboard: {e}")
                    await asyncio.sleep(60)
        
        asyncio.create_task(dashboard_loop())
    
    async def _update_dashboard_data(self):
        """Actualiza datos del dashboard"""
        try:
            self.dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'system_health': self.health_monitor.get_overall_health(),
                'alerts': {
                    'active_count': len(self.alert_manager.active_alerts),
                    'statistics': self.alert_manager.get_alert_statistics()
                },
                'metrics': {
                    'system_metrics': self._get_system_metrics_summary(),
                    'application_metrics': self._get_application_metrics_summary(),
                    'performance_metrics': self._get_performance_metrics_summary()
                }
            }
            
            # Cache dashboard data
            if self.cache_service:
                await self.cache_service.set(
                    "monitoring:dashboard_data",
                    self.dashboard_data,
                    ttl=60
                )
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard data: {e}")
    
    def _get_system_metrics_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de métricas del sistema"""
        return {
            'cpu_usage_percent': self.metrics.get_gauge('system_cpu_percent') or 0,
            'memory_usage_percent': self.metrics.get_gauge('system_memory_percent') or 0,
            'disk_usage_percent': self.metrics.get_gauge('system_disk_percent') or 0,
            'network_io': {
                'bytes_sent': self.metrics.get_counter('system_network_bytes_sent') or 0,
                'bytes_recv': self.metrics.get_counter('system_network_bytes_recv') or 0
            }
        }
    
    def _get_application_metrics_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de métricas de aplicación"""
        return {
            'predictions_generated': self.metrics.get_counter('predictions_generated') or 0,
            'api_requests_total': self.metrics.get_counter('api_requests_total') or 0,
            'models_loaded': self.metrics.get_gauge('models_loaded') or 0,
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'error_rate': self._calculate_error_rate()
        }
    
    def _get_performance_metrics_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de métricas de performance"""
        prediction_stats = self.metrics.get_histogram_stats('prediction_duration_seconds')
        api_stats = self.metrics.get_histogram_stats('api_request_duration_seconds')
        
        return {
            'prediction_time': {
                'avg_ms': prediction_stats.get('mean', 0) * 1000,
                'p95_ms': prediction_stats.get('p95', 0) * 1000,
                'p99_ms': prediction_stats.get('p99', 0) * 1000
            },
            'api_response_time': {
                'avg_ms': api_stats.get('mean', 0) * 1000,
                'p95_ms': api_stats.get('p95', 0) * 1000,
                'p99_ms': api_stats.get('p99', 0) * 1000
            },
            'throughput_rps': self._calculate_throughput()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calcula tasa de aciertos de cache"""
        hits = self.metrics.get_counter('cache_hits') or 0
        misses = self.metrics.get_counter('cache_misses') or 0
        total = hits + misses
        return hits / total if total > 0 else 0.0
    
    def _calculate_error_rate(self) -> float:
        """Calcula tasa de errores"""
        errors = self.metrics.get_counter('api_errors') or 0
        total = self.metrics.get_counter('api_requests_total') or 1
        return errors / total
    
    def _calculate_throughput(self) -> float:
        """Calcula throughput aproximado"""
        # Implementación simplificada - en producción usar ventanas de tiempo
        requests = self.metrics.get_counter('api_requests_total') or 0
        return requests / 3600  # Aproximación por hora convertida a por segundo
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtiene datos actuales del dashboard"""
        return self.dashboard_data
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Obtiene resumen completo del monitoreo"""
        return {
            'system_status': self.health_monitor.get_overall_health()['status'],
            'active_alerts': len(self.alert_manager.active_alerts),
            'critical_alerts': len([
                a for a in self.alert_manager.active_alerts.values()
                if a.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
            ]),
            'monitoring_health': {
                'alert_manager': 'active',
                'health_monitor': 'active',
                'dashboard_updates': 'active'
            },
            'last_update': self.dashboard_data.get('timestamp', 'never')
        }
    
    # Public interface methods
    def create_alert_rule(self, **kwargs) -> str:
        """Crea nueva regla de alerta"""
        rule = AlertRule(**kwargs)
        self.alert_manager.add_alert_rule(rule)
        return rule.rule_id
    
    def configure_notifications(self, channel_type: str, config: Dict[str, Any]):
        """Configura canal de notificaciones"""
        self.alert_manager.configure_notification_channel(channel_type, config)
    
    def register_health_check(self, component: str, check_function: Callable):
        """Registra función de health check personalizada"""
        self.health_monitor.register_health_check(component, check_function)
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Obtiene alertas activas"""
        return self.alert_manager.get_active_alerts()
    
    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Confirma alerta"""
        if alert_id in self.alert_manager.active_alerts:
            alert = self.alert_manager.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = user
            self.logger.info(f"✅ Alert acknowledged: {alert_id} by {user}")
            return True
        return False