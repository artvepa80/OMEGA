# OMEGA_PRO_AI_v10.1/modules/performance_alerts.py
# Advanced Performance Alert System for Real-time Monitoring and Notifications

import os
import time
import json
import smtplib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import logging

# Configurar directorios
os.makedirs('logs/alerts', exist_ok=True)
os.makedirs('config/alerts', exist_ok=True)

@dataclass
class AlertRule:
    """Definición de una regla de alerta"""
    name: str
    condition: str  # 'threshold', 'trend', 'pattern', 'anomaly'
    metric: str     # 'execution_time', 'memory_usage', 'success_rate', etc.
    threshold_value: float
    comparison: str  # 'gt', 'lt', 'eq', 'gte', 'lte'
    severity: str    # 'info', 'warning', 'critical'
    cooldown_minutes: int = 5  # Tiempo mínimo entre alertas del mismo tipo
    enabled: bool = True
    description: str = ""
    action: Optional[str] = None  # 'email', 'log', 'callback'

@dataclass
class PerformanceAlert:
    """Alerta de rendimiento generada"""
    id: str
    rule_name: str
    timestamp: str
    severity: str
    message: str
    metric_name: str
    metric_value: float
    threshold_value: float
    model_name: Optional[str] = None
    details: Optional[Dict] = None
    acknowledged: bool = False
    resolved: bool = False

class PerformanceAlertSystem:
    """
    Sistema avanzado de alertas de rendimiento.
    
    Monitorea métricas en tiempo real y genera alertas configurables
    basadas en umbrales, tendencias y patrones anómalos.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/alerts/alert_config.json"
        self.logger = logging.getLogger('PerformanceAlerts')
        
        # Configuración
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.cooldown_tracker: Dict[str, datetime] = {}
        
        # Métricas para análisis de tendencias
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.baseline_metrics: Dict[str, float] = {}
        
        # Control de threading
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Callbacks personalizados
        self.alert_callbacks: List[Callable] = []
        
        # Configuración de email (opcional)
        self.email_config = {}
        
        # Cargar configuración
        self.load_configuration()
        
        # Estadísticas
        self.stats = {
            'total_alerts': 0,
            'alerts_by_severity': defaultdict(int),
            'alerts_by_model': defaultdict(int),
            'false_positive_rate': 0.0
        }
        
        self.logger.info("🚨 Sistema de alertas de rendimiento inicializado")
    
    def load_configuration(self):
        """Cargar configuración de alertas"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                # Cargar reglas de alerta
                for rule_data in config.get('alert_rules', []):
                    rule = AlertRule(**rule_data)
                    self.alert_rules[rule.name] = rule
                
                # Cargar configuración de email
                self.email_config = config.get('email_config', {})
                
                self.logger.info(f"✅ Configuración cargada: {len(self.alert_rules)} reglas")
            else:
                # Crear configuración por defecto
                self.create_default_configuration()
                
        except Exception as e:
            self.logger.error(f"❌ Error cargando configuración: {e}")
            self.create_default_configuration()
    
    def create_default_configuration(self):
        """Crear configuración por defecto"""
        default_rules = [
            AlertRule(
                name="model_timeout_critical",
                condition="threshold",
                metric="execution_time",
                threshold_value=30.0,
                comparison="gt",
                severity="critical",
                cooldown_minutes=2,
                description="Modelo excedió 30 segundos de ejecución"
            ),
            AlertRule(
                name="model_timeout_warning",
                condition="threshold",
                metric="execution_time",
                threshold_value=20.0,
                comparison="gt",
                severity="warning",
                cooldown_minutes=3,
                description="Modelo tardó más de 20 segundos"
            ),
            AlertRule(
                name="low_success_rate",
                condition="threshold",
                metric="success_rate",
                threshold_value=0.7,
                comparison="lt",
                severity="warning",
                cooldown_minutes=5,
                description="Tasa de éxito del modelo por debajo del 70%"
            ),
            AlertRule(
                name="high_memory_usage",
                condition="threshold",
                metric="memory_percent",
                threshold_value=85.0,
                comparison="gt",
                severity="warning",
                cooldown_minutes=1,
                description="Uso de memoria superior al 85%"
            ),
            AlertRule(
                name="critical_memory_usage",
                condition="threshold",
                metric="memory_percent",
                threshold_value=95.0,
                comparison="gt",
                severity="critical",
                cooldown_minutes=1,
                description="Uso crítico de memoria superior al 95%"
            ),
            AlertRule(
                name="high_cpu_usage",
                condition="threshold",
                metric="cpu_percent",
                threshold_value=90.0,
                comparison="gt",
                severity="warning",
                cooldown_minutes=2,
                description="Uso de CPU superior al 90%"
            ),
            AlertRule(
                name="frequent_fallbacks",
                condition="threshold",
                metric="fallback_count",
                threshold_value=3.0,
                comparison="gte",
                severity="warning",
                cooldown_minutes=10,
                description="Modelo usando fallbacks frecuentemente"
            ),
            AlertRule(
                name="performance_degradation",
                condition="trend",
                metric="execution_time",
                threshold_value=0.3,  # 30% de aumento
                comparison="gt",
                severity="warning",
                cooldown_minutes=15,
                description="Degradación de rendimiento detectada"
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.name] = rule
        
        # Guardar configuración por defecto
        self.save_configuration()
        
        self.logger.info("✅ Configuración por defecto creada")
    
    def save_configuration(self):
        """Guardar configuración actual"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            config = {
                'alert_rules': [asdict(rule) for rule in self.alert_rules.values()],
                'email_config': self.email_config
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            
            self.logger.info("✅ Configuración guardada")
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando configuración: {e}")
    
    def add_alert_rule(self, rule: AlertRule):
        """Agregar nueva regla de alerta"""
        with self.lock:
            self.alert_rules[rule.name] = rule
        self.save_configuration()
        self.logger.info(f"➕ Regla de alerta agregada: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Eliminar regla de alerta"""
        with self.lock:
            if rule_name in self.alert_rules:
                del self.alert_rules[rule_name]
                self.save_configuration()
                self.logger.info(f"➖ Regla de alerta eliminada: {rule_name}")
    
    def enable_rule(self, rule_name: str):
        """Habilitar regla de alerta"""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].enabled = True
            self.save_configuration()
            self.logger.info(f"✅ Regla habilitada: {rule_name}")
    
    def disable_rule(self, rule_name: str):
        """Deshabilitar regla de alerta"""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].enabled = False
            self.save_configuration()
            self.logger.info(f"❌ Regla deshabilitada: {rule_name}")
    
    def check_metric(self, metric_name: str, value: float, model_name: Optional[str] = None):
        """Verificar métrica contra reglas de alerta"""
        current_time = datetime.now()
        
        # Actualizar historial de métricas
        self.metric_history[metric_name].append((current_time, value))
        
        # Verificar cada regla
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled or rule.metric != metric_name:
                continue
            
            # Verificar cooldown
            if self._is_in_cooldown(rule_name):
                continue
            
            # Verificar condición
            if self._check_rule_condition(rule, value, model_name):
                self._trigger_alert(rule, metric_name, value, model_name)
    
    def _check_rule_condition(self, rule: AlertRule, value: float, model_name: Optional[str]) -> bool:
        """Verificar si se cumple la condición de la regla"""
        if rule.condition == 'threshold':
            return self._check_threshold(rule, value)
        elif rule.condition == 'trend':
            return self._check_trend(rule, value)
        elif rule.condition == 'pattern':
            return self._check_pattern(rule, value)
        elif rule.condition == 'anomaly':
            return self._check_anomaly(rule, value)
        
        return False
    
    def _check_threshold(self, rule: AlertRule, value: float) -> bool:
        """Verificar umbral simple"""
        if rule.comparison == 'gt':
            return value > rule.threshold_value
        elif rule.comparison == 'lt':
            return value < rule.threshold_value
        elif rule.comparison == 'gte':
            return value >= rule.threshold_value
        elif rule.comparison == 'lte':
            return value <= rule.threshold_value
        elif rule.comparison == 'eq':
            return abs(value - rule.threshold_value) < 0.001
        
        return False
    
    def _check_trend(self, rule: AlertRule, current_value: float) -> bool:
        """Verificar tendencia de degradación"""
        metric_data = self.metric_history[rule.metric]
        
        if len(metric_data) < 10:  # Necesitamos suficiente historial
            return False
        
        # Calcular promedio de últimas 10 mediciones vs promedio anterior
        recent_values = [v for _, v in list(metric_data)[-10:]]
        older_values = [v for _, v in list(metric_data)[-20:-10]] if len(metric_data) >= 20 else recent_values
        
        if not older_values:
            return False
        
        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)
        
        # Calcular porcentaje de cambio
        if older_avg > 0:
            change_percent = (recent_avg - older_avg) / older_avg
            return abs(change_percent) > rule.threshold_value
        
        return False
    
    def _check_pattern(self, rule: AlertRule, value: float) -> bool:
        """Verificar patrones específicos (implementación básica)"""
        # Implementación futura para patrones complejos
        return False
    
    def _check_anomaly(self, rule: AlertRule, value: float) -> bool:
        """Detectar anomalías usando desviación estándar"""
        metric_data = self.metric_history[rule.metric]
        
        if len(metric_data) < 20:  # Necesitamos suficiente historial
            return False
        
        values = [v for _, v in metric_data]
        mean = sum(values) / len(values)
        
        # Calcular desviación estándar
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        
        # Verificar si el valor actual es una anomalía (> 2 desviaciones estándar)
        if std_dev > 0:
            z_score = abs(value - mean) / std_dev
            return z_score > rule.threshold_value
        
        return False
    
    def _is_in_cooldown(self, rule_name: str) -> bool:
        """Verificar si la regla está en periodo de enfriamiento"""
        if rule_name not in self.cooldown_tracker:
            return False
        
        last_alert = self.cooldown_tracker[rule_name]
        cooldown_period = self.alert_rules[rule_name].cooldown_minutes
        
        return datetime.now() - last_alert < timedelta(minutes=cooldown_period)
    
    def _trigger_alert(self, rule: AlertRule, metric_name: str, value: float, model_name: Optional[str]):
        """Disparar alerta"""
        alert_id = f"{rule.name}_{int(time.time())}"
        
        # Crear alerta
        alert = PerformanceAlert(
            id=alert_id,
            rule_name=rule.name,
            timestamp=datetime.now().isoformat(),
            severity=rule.severity,
            message=self._generate_alert_message(rule, metric_name, value, model_name),
            metric_name=metric_name,
            metric_value=value,
            threshold_value=rule.threshold_value,
            model_name=model_name,
            details={
                'rule_description': rule.description,
                'comparison': rule.comparison,
                'condition': rule.condition
            }
        )
        
        # Registrar alerta
        with self.lock:
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            self.cooldown_tracker[rule.name] = datetime.now()
            
            # Actualizar estadísticas
            self.stats['total_alerts'] += 1
            self.stats['alerts_by_severity'][rule.severity] += 1
            if model_name:
                self.stats['alerts_by_model'][model_name] += 1
        
        # Ejecutar acciones
        self._execute_alert_actions(alert, rule)
        
        # Log de la alerta
        severity_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(rule.severity, "•")
        self.logger.warning(f"{severity_emoji} ALERTA [{rule.severity.upper()}]: {alert.message}")
    
    def _generate_alert_message(self, rule: AlertRule, metric_name: str, value: float, model_name: Optional[str]) -> str:
        """Generar mensaje de alerta personalizado"""
        base_msg = rule.description or f"{metric_name} fuera de rango"
        
        if model_name:
            model_info = f" en modelo {model_name}"
        else:
            model_info = ""
        
        if rule.condition == 'threshold':
            return f"{base_msg}{model_info}: {value:.2f} {rule.comparison} {rule.threshold_value:.2f}"
        elif rule.condition == 'trend':
            return f"Tendencia de {metric_name}{model_info}: cambio significativo detectado ({value:.2f})"
        else:
            return f"{base_msg}{model_info}: valor actual {value:.2f}"
    
    def _execute_alert_actions(self, alert: PerformanceAlert, rule: AlertRule):
        """Ejecutar acciones definidas para la alerta"""
        if rule.action == 'email':
            self._send_email_alert(alert)
        elif rule.action == 'log':
            self._log_alert_to_file(alert)
        
        # Ejecutar callbacks personalizados
        for callback in self.alert_callbacks:
            try:
                callback(alert, rule)
            except Exception as e:
                self.logger.error(f"❌ Error en callback de alerta: {e}")
    
    def _send_email_alert(self, alert: PerformanceAlert):
        """Enviar alerta por email"""
        if not self.email_config or not self.email_config.get('enabled'):
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_config.get('sender_email')
            msg['To'] = ', '.join(self.email_config.get('recipients', []))
            msg['Subject'] = f"🚨 OMEGA AI Alert - {alert.severity.upper()}"
            
            body = f"""
            OMEGA AI Performance Alert
            
            Severity: {alert.severity.upper()}
            Time: {alert.timestamp}
            Model: {alert.model_name or 'System'}
            
            Message: {alert.message}
            
            Metric: {alert.metric_name}
            Value: {alert.metric_value:.2f}
            Threshold: {alert.threshold_value:.2f}
            
            Rule: {alert.rule_name}
            Description: {alert.details.get('rule_description', 'N/A')}
            
            ---
            Generated by OMEGA AI Performance Monitor
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config.get('smtp_host'), self.email_config.get('smtp_port'))
            server.starttls()
            server.login(self.email_config.get('sender_email'), self.email_config.get('sender_password'))
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"📧 Email enviado para alerta {alert.id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error enviando email: {e}")
    
    def _log_alert_to_file(self, alert: PerformanceAlert):
        """Guardar alerta en archivo de log"""
        log_file = f"logs/alerts/alerts_{datetime.now().strftime('%Y%m%d')}.log"
        
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{alert.timestamp} [{alert.severity.upper()}] {alert.message}\n")
                f.write(f"    Model: {alert.model_name or 'System'}\n")
                f.write(f"    Metric: {alert.metric_name} = {alert.metric_value:.2f}\n")
                f.write(f"    Threshold: {alert.threshold_value:.2f}\n")
                f.write(f"    Rule: {alert.rule_name}\n")
                f.write("---\n")
            
        except Exception as e:
            self.logger.error(f"❌ Error escribiendo log de alerta: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """Agregar callback personalizado para alertas"""
        self.alert_callbacks.append(callback)
        self.logger.info("✅ Callback de alerta agregado")
    
    def acknowledge_alert(self, alert_id: str):
        """Marcar alerta como reconocida"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.logger.info(f"✅ Alerta reconocida: {alert_id}")
    
    def resolve_alert(self, alert_id: str):
        """Marcar alerta como resuelta"""
        with self.lock:
            if alert_id in self.active_alerts:
                self.active_alerts[alert_id].resolved = True
                self.logger.info(f"✅ Alerta resuelta: {alert_id}")
    
    def get_active_alerts(self, severity: Optional[str] = None) -> List[PerformanceAlert]:
        """Obtener alertas activas"""
        alerts = [alert for alert in self.active_alerts.values() if not alert.resolved]
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de alertas"""
        active_count = len([a for a in self.active_alerts.values() if not a.resolved])
        
        return {
            'total_alerts': self.stats['total_alerts'],
            'active_alerts': active_count,
            'alerts_by_severity': dict(self.stats['alerts_by_severity']),
            'alerts_by_model': dict(self.stats['alerts_by_model']),
            'alert_rules_count': len(self.alert_rules),
            'enabled_rules': len([r for r in self.alert_rules.values() if r.enabled])
        }
    
    def clear_resolved_alerts(self):
        """Limpiar alertas resueltas"""
        with self.lock:
            resolved_ids = [aid for aid, alert in self.active_alerts.items() if alert.resolved]
            for aid in resolved_ids:
                del self.active_alerts[aid]
        
        self.logger.info(f"🧹 {len(resolved_ids)} alertas resueltas eliminadas")
    
    def export_alerts_report(self, output_path: Optional[str] = None) -> str:
        """Exportar reporte de alertas"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/performance/alerts_report_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_alert_statistics(),
            'active_alerts': [asdict(alert) for alert in self.get_active_alerts()],
            'recent_history': [asdict(alert) for alert in list(self.alert_history)[-50:]],
            'alert_rules': {name: asdict(rule) for name, rule in self.alert_rules.items()}
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"📊 Reporte de alertas exportado: {output_path}")
        return output_path

# Instancia global del sistema de alertas
_alert_system: Optional[PerformanceAlertSystem] = None

def get_alert_system() -> PerformanceAlertSystem:
    """Obtener instancia global del sistema de alertas"""
    global _alert_system
    if _alert_system is None:
        _alert_system = PerformanceAlertSystem()
    return _alert_system

def initialize_alert_system(config_path: Optional[str] = None) -> PerformanceAlertSystem:
    """Inicializar sistema de alertas con configuración personalizada"""
    global _alert_system
    _alert_system = PerformanceAlertSystem(config_path)
    return _alert_system