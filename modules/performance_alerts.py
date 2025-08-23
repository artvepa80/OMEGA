# OMEGA_PRO_AI_v10.1/modules/performance_alerts.py
# Advanced Performance Alert System for Real-time Monitoring and Notifications
# Enhanced with Security Improvements and ML-driven Anomaly Detection

import os
import time
import json
import smtplib
import ssl
import threading
import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText as MimeText
from email.mime.multipart import MIMEMultipart as MimeMultipart
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Event

# Async SMTP for secure email (optional)
try:
    import aiosmtplib
    AIOSMTPLIB_AVAILABLE = True
except ImportError:
    AIOSMTPLIB_AVAILABLE = False
    logging.warning("aiosmtplib not available. Async secure email will be limited.")

# ML Libraries for anomaly detection
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available. ML anomaly detection will be limited.")

# Import accuracy framework for ML performance monitoring
try:
    from modules.accuracy_validation_framework import AccuracyValidationFramework
    ACCURACY_FRAMEWORK_AVAILABLE = True
except ImportError:
    ACCURACY_FRAMEWORK_AVAILABLE = False
    logging.warning("Accuracy framework not available. ML accuracy monitoring will be limited.")

# Configurar directorios
os.makedirs('logs/alerts', exist_ok=True)
os.makedirs('config/alerts', exist_ok=True)

@dataclass
class AlertRule:
    """Enhanced alert rule definition with security and ML capabilities"""
    name: str
    condition: str  # 'threshold', 'trend', 'pattern', 'anomaly', 'ml_anomaly', 'accuracy_drop'
    metric: str     # 'execution_time', 'memory_usage', 'success_rate', 'lstm_accuracy', etc.
    threshold_value: float
    comparison: str  # 'gt', 'lt', 'eq', 'gte', 'lte'
    severity: str    # 'info', 'warning', 'critical'
    cooldown_minutes: int = 5  # Tiempo mínimo entre alertas del mismo tipo
    enabled: bool = True
    description: str = ""
    action: Optional[str] = None  # 'email', 'log', 'callback', 'secure_email'
    ml_sensitivity: float = 0.1  # For ML anomaly detection (contamination rate)
    security_level: str = "standard"  # 'standard', 'high', 'critical'
    encrypted: bool = False  # Whether alert content should be encrypted

@dataclass
class PerformanceAlert:
    """Enhanced performance alert with security and ML context"""
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
    anomaly_score: Optional[float] = None  # ML anomaly detection score
    confidence: Optional[float] = None  # Alert confidence level
    security_context: Optional[Dict] = None  # Security-related metadata
    ml_context: Optional[Dict] = None  # ML-specific context (accuracy trends, etc.)

class PerformanceAlertSystem:
    """
    Advanced Performance Alert System with Security and ML Enhancements.
    
    Features:
    - Secure SMTP with SSL/TLS encryption
    - Async email sending with aiosmtplib
    - ML-driven anomaly detection using Isolation Forest
    - LSTM accuracy monitoring with 65% threshold alerts
    - Proper thread management with cleanup
    - Security hardening with environment variables
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/alerts/alert_config.json"
        self.logger = logging.getLogger('PerformanceAlerts')
        
        # Configuration
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.cooldown_tracker: Dict[str, datetime] = {}
        
        # Metrics for trend analysis
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.baseline_metrics: Dict[str, float] = {}
        
        # Enhanced thread management
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = Event()  # Proper thread termination
        self.lock = threading.Lock()
        self.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="AlertWorker")
        
        # ML Components
        self.ml_models: Dict[str, IsolationForest] = {} if SKLEARN_AVAILABLE else {}
        self.scalers: Dict[str, StandardScaler] = {} if SKLEARN_AVAILABLE else {}
        self.ml_training_window = 50  # Minimum samples for ML training
        self.accuracy_validator: Optional[AccuracyValidationFramework] = None
        
        if ACCURACY_FRAMEWORK_AVAILABLE:
            self.accuracy_validator = AccuracyValidationFramework()
        
        # Security enhancements
        self.secure_email_config = self._load_secure_email_config()
        self.encryption_key = os.getenv('OMEGA_ALERT_ENCRYPTION_KEY')
        
        # Custom callbacks
        self.alert_callbacks: List[Callable] = []
        
        # Legacy email config (deprecated - use secure config)
        self.email_config = {}
        
        # Load configuration
        self.load_configuration()
        
        # Enhanced statistics
        self.stats = {
            'total_alerts': 0,
            'alerts_by_severity': defaultdict(int),
            'alerts_by_model': defaultdict(int),
            'false_positive_rate': 0.0,
            'ml_anomalies_detected': 0,
            'accuracy_alerts_sent': 0,
            'security_incidents': 0
        }
        
        self.logger.info("🔒 Enhanced Performance Alert System initialized with security & ML features")
    
    def _load_secure_email_config(self) -> Dict[str, Any]:
        """Load secure email configuration from environment variables"""
        return {
            'enabled': os.getenv('OMEGA_EMAIL_ENABLED', 'false').lower() == 'true',
            'smtp_host': os.getenv('OMEGA_SMTP_HOST'),
            'smtp_port': int(os.getenv('OMEGA_SMTP_PORT', '587')),
            'sender_email': os.getenv('OMEGA_SENDER_EMAIL'),
            'sender_password': os.getenv('OMEGA_SENDER_PASSWORD'),
            'recipients': os.getenv('OMEGA_EMAIL_RECIPIENTS', '').split(','),
            'use_tls': os.getenv('OMEGA_SMTP_TLS', 'true').lower() == 'true',
            'use_ssl': os.getenv('OMEGA_SMTP_SSL', 'false').lower() == 'true',
            'timeout': int(os.getenv('OMEGA_SMTP_TIMEOUT', '30'))
        }
    
    def shutdown(self):
        """Properly shutdown the alert system with thread cleanup"""
        self.logger.info("🔄 Shutting down Performance Alert System...")
        
        # Stop monitoring
        self.stop_event.set()
        self.monitoring = False
        
        # Wait for monitor thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
            if self.monitor_thread.is_alive():
                self.logger.warning("⚠️ Monitor thread did not terminate gracefully")
        
        # Shutdown thread pool
        try:
            self.thread_pool.shutdown(wait=True, timeout=10.0)
        except Exception as e:
            self.logger.error(f"❌ Error shutting down thread pool: {e}")
        
        self.logger.info("✅ Performance Alert System shutdown complete")
    
    def __del__(self):
        """Ensure proper cleanup on object destruction"""
        try:
            self.shutdown()
        except Exception:
            pass  # Avoid errors during garbage collection
    
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
                threshold_value=180.0,  # 3 minutes for critical models like genetic
                comparison="gt",
                severity="critical",
                cooldown_minutes=2,
                description="Modelo excedió 3 minutos de ejecución"
            ),
            AlertRule(
                name="model_timeout_warning",
                condition="threshold",
                metric="execution_time",
                threshold_value=60.0,  # 1 minute warning threshold
                comparison="gt",
                severity="warning",
                cooldown_minutes=3,
                description="Modelo tardó más de 1 minuto"
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
            ),
            # ML-specific alert rules
            AlertRule(
                name="lstm_accuracy_critical",
                condition="threshold",
                metric="lstm_accuracy",
                threshold_value=0.65,  # 65% threshold as per CTO analysis
                comparison="lt",
                severity="critical",
                cooldown_minutes=5,
                description="LSTM accuracy below critical 65% threshold",
                action="secure_email",
                security_level="high"
            ),
            AlertRule(
                name="ml_anomaly_detected",
                condition="ml_anomaly",
                metric="execution_time",
                threshold_value=0.1,  # Contamination rate
                comparison="gt",
                severity="warning",
                cooldown_minutes=10,
                description="ML anomaly detection: unusual pattern detected",
                ml_sensitivity=0.1
            ),
            AlertRule(
                name="model_accuracy_degradation",
                condition="accuracy_drop",
                metric="model_accuracy",
                threshold_value=0.1,  # 10% drop
                comparison="gt",
                severity="warning",
                cooldown_minutes=15,
                description="Model accuracy degradation detected"
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
    
    def check_metric(self, metric_name: str, value: float, model_name: Optional[str] = None, 
                   accuracy_context: Optional[Dict] = None):
        """Enhanced metric checking with ML and security features"""
        current_time = datetime.now()
        
        # Update metric history
        self.metric_history[metric_name].append((current_time, value))
        
        # Special handling for LSTM accuracy monitoring
        if metric_name == 'lstm_accuracy' and value < 0.65:
            self.stats['accuracy_alerts_sent'] += 1
            self.logger.warning(f"⚠️ LSTM Accuracy Alert: {value:.3f} below 65% threshold")
        
        # Check each rule
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled or rule.metric != metric_name:
                continue
            
            # Check cooldown
            if self._is_in_cooldown(rule_name):
                continue
            
            # Enhanced condition checking with anomaly scores
            condition_met, anomaly_score = self._check_rule_condition(rule, value, model_name)
            
            if condition_met:
                self._trigger_enhanced_alert(rule, metric_name, value, model_name, 
                                           anomaly_score, accuracy_context)
    
    def _check_rule_condition(self, rule: AlertRule, value: float, model_name: Optional[str]) -> Tuple[bool, Optional[float]]:
        """Enhanced rule condition checking with ML and security features"""
        anomaly_score = None
        
        if rule.condition == 'threshold':
            result = self._check_threshold(rule, value)
        elif rule.condition == 'trend':
            result = self._check_trend(rule, value)
        elif rule.condition == 'pattern':
            result = self._check_pattern(rule, value)
        elif rule.condition == 'anomaly':
            result = self._check_anomaly(rule, value)
        elif rule.condition == 'ml_anomaly':
            result, anomaly_score = self._check_ml_anomaly(rule, value)
        elif rule.condition == 'accuracy_drop':
            result = self._check_accuracy_drop(rule, value)
        else:
            result = False
        
        return result, anomaly_score
    
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
        """Detectar anomalías usando desviación estándar (legacy method)"""
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
    
    def _check_ml_anomaly(self, rule: AlertRule, value: float) -> Tuple[bool, float]:
        """Advanced ML-based anomaly detection using Isolation Forest"""
        if not SKLEARN_AVAILABLE:
            self.logger.warning("sklearn not available, falling back to statistical anomaly detection")
            return self._check_anomaly(rule, value), 0.0
        
        metric_data = self.metric_history[rule.metric]
        
        # Need sufficient training data
        if len(metric_data) < self.ml_training_window:
            return False, 0.0
        
        # Prepare data
        values = np.array([v for _, v in metric_data]).reshape(-1, 1)
        
        # Train or update model if needed
        model_key = f"{rule.metric}_{rule.name}"
        if model_key not in self.ml_models or len(metric_data) % 10 == 0:  # Retrain every 10 samples
            try:
                # Use contamination rate from rule
                contamination = rule.ml_sensitivity
                self.ml_models[model_key] = IsolationForest(
                    contamination=contamination,
                    random_state=42,
                    n_estimators=100
                )
                
                # Scale data for better performance
                if model_key not in self.scalers:
                    self.scalers[model_key] = StandardScaler()
                
                values_scaled = self.scalers[model_key].fit_transform(values)
                self.ml_models[model_key].fit(values_scaled)
                
                self.logger.debug(f"Trained ML anomaly model for {metric_data}")
                
            except Exception as e:
                self.logger.error(f"Error training ML anomaly model: {e}")
                return False, 0.0
        
        # Predict anomaly
        try:
            current_value_scaled = self.scalers[model_key].transform([[value]])
            prediction = self.ml_models[model_key].predict(current_value_scaled)[0]
            anomaly_score = self.ml_models[model_key].decision_function(current_value_scaled)[0]
            
            is_anomaly = prediction == -1
            
            if is_anomaly:
                self.stats['ml_anomalies_detected'] += 1
                self.logger.info(f"ML Anomaly detected for {rule.metric}: {value} (score: {anomaly_score:.3f})")
            
            return is_anomaly, float(anomaly_score)
            
        except Exception as e:
            self.logger.error(f"Error in ML anomaly prediction: {e}")
            return False, 0.0
    
    def _check_accuracy_drop(self, rule: AlertRule, value: float) -> bool:
        """Check for significant accuracy drops in ML models"""
        if not ACCURACY_FRAMEWORK_AVAILABLE:
            return False
        
        metric_data = self.metric_history[rule.metric]
        
        if len(metric_data) < 10:
            return False
        
        # Get recent accuracy values
        recent_values = [v for _, v in list(metric_data)[-5:]]
        older_values = [v for _, v in list(metric_data)[-10:-5]] if len(metric_data) >= 10 else recent_values
        
        if not older_values:
            return False
        
        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)
        
        # Calculate percentage drop
        if older_avg > 0:
            accuracy_drop = (older_avg - recent_avg) / older_avg
            return accuracy_drop > rule.threshold_value
        
        return False
    
    def _is_in_cooldown(self, rule_name: str) -> bool:
        """Verificar si la regla está en periodo de enfriamiento"""
        if rule_name not in self.cooldown_tracker:
            return False
        
        last_alert = self.cooldown_tracker[rule_name]
        cooldown_period = self.alert_rules[rule_name].cooldown_minutes
        
        return datetime.now() - last_alert < timedelta(minutes=cooldown_period)
    
    def _trigger_enhanced_alert(self, rule: AlertRule, metric_name: str, value: float, 
                              model_name: Optional[str], anomaly_score: Optional[float] = None,
                              accuracy_context: Optional[Dict] = None):
        """Enhanced alert triggering with security and ML context"""
        alert_id = f"{rule.name}_{int(time.time())}"
        
        # Calculate confidence based on anomaly score and rule type
        confidence = self._calculate_alert_confidence(rule, value, anomaly_score)
        
        # Create enhanced alert
        alert = PerformanceAlert(
            id=alert_id,
            rule_name=rule.name,
            timestamp=datetime.now().isoformat(),
            severity=rule.severity,
            message=self._generate_enhanced_alert_message(rule, metric_name, value, 
                                                        model_name, anomaly_score),
            metric_name=metric_name,
            metric_value=value,
            threshold_value=rule.threshold_value,
            model_name=model_name,
            anomaly_score=anomaly_score,
            confidence=confidence,
            details={
                'rule_description': rule.description,
                'comparison': rule.comparison,
                'condition': rule.condition,
                'ml_enhanced': anomaly_score is not None,
                'training_samples': len(self.metric_history[metric_name])
            },
            security_context={
                'security_level': rule.security_level,
                'encrypted': rule.encrypted,
                'timestamp_utc': datetime.utcnow().isoformat()
            },
            ml_context={
                'accuracy_context': accuracy_context,
                'anomaly_score': anomaly_score,
                'model_performance': self._get_model_performance_context(model_name)
            }
        )
        
        # Register alert
        with self.lock:
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            self.cooldown_tracker[rule.name] = datetime.now()
            
            # Update enhanced statistics
            self.stats['total_alerts'] += 1
            self.stats['alerts_by_severity'][rule.severity] += 1
            if model_name:
                self.stats['alerts_by_model'][model_name] += 1
            if rule.security_level in ['high', 'critical']:
                self.stats['security_incidents'] += 1
        
        # Execute enhanced actions
        self._execute_enhanced_alert_actions(alert, rule)
        
        # Enhanced logging
        severity_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(rule.severity, "•")
        ml_info = f" [ML Score: {anomaly_score:.3f}]" if anomaly_score else ""
        security_info = f" [Security: {rule.security_level}]" if rule.security_level != "standard" else ""
        
        self.logger.warning(
            f"{severity_emoji} ENHANCED ALERT [{rule.severity.upper()}]: {alert.message}"
            f"{ml_info}{security_info} [Confidence: {confidence:.1%}]"
        )
    
    def _generate_enhanced_alert_message(self, rule: AlertRule, metric_name: str, value: float, 
                                       model_name: Optional[str], anomaly_score: Optional[float]) -> str:
        """Generate enhanced alert message with ML and security context"""
        base_msg = rule.description or f"{metric_name} out of range"
        
        model_info = f" in model {model_name}" if model_name else ""
        
        if rule.condition == 'threshold':
            comparison_text = {
                'gt': 'above', 'lt': 'below', 'gte': 'at or above', 
                'lte': 'at or below', 'eq': 'equal to'
            }.get(rule.comparison, rule.comparison)
            
            message = f"{base_msg}{model_info}: {value:.3f} is {comparison_text} threshold {rule.threshold_value:.3f}"
            
        elif rule.condition == 'trend':
            message = f"Performance trend alert{model_info}: significant change detected ({value:.3f})"
            
        elif rule.condition == 'ml_anomaly':
            message = f"ML Anomaly detected{model_info}: {metric_name} = {value:.3f}"
            if anomaly_score:
                message += f" (anomaly score: {anomaly_score:.3f})"
                
        elif rule.condition == 'accuracy_drop':
            message = f"Model accuracy degradation{model_info}: {metric_name} dropped to {value:.3f}"
            
        else:
            message = f"{base_msg}{model_info}: current value {value:.3f}"
            
        # Add security context for high-security alerts
        if rule.security_level in ['high', 'critical']:
            message += f" [SECURITY: {rule.security_level.upper()}]"
            
        return message
    
    def _execute_enhanced_alert_actions(self, alert: PerformanceAlert, rule: AlertRule):
        """Execute enhanced alert actions with security and async capabilities"""
        if rule.action == 'email':
            # Legacy email (deprecated)
            self._send_email_alert(alert)
        elif rule.action == 'secure_email':
            # New secure async email
            self.thread_pool.submit(self._send_secure_email_alert, alert, rule)
        elif rule.action == 'log':
            self._log_alert_to_file(alert)
        
        # Execute custom callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert, rule)
            except Exception as e:
                self.logger.error(f"❌ Error in alert callback: {e}")
    
    def _send_email_alert(self, alert: PerformanceAlert):
        """Send alert via legacy email (DEPRECATED - use secure email instead)"""
        self.logger.warning("Using deprecated email method. Please migrate to secure_email action.")
        
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
            
            # Use secure SMTP with SSL/TLS
            context = ssl.create_default_context()
            
            if self.email_config.get('use_ssl', False):
                server = smtplib.SMTP_SSL(self.email_config.get('smtp_host'), 
                                        self.email_config.get('smtp_port', 465),
                                        context=context)
            else:
                server = smtplib.SMTP(self.email_config.get('smtp_host'), 
                                    self.email_config.get('smtp_port', 587))
                if self.email_config.get('use_tls', True):
                    server.starttls(context=context)
            
            server.login(self.email_config.get('sender_email'), self.email_config.get('sender_password'))
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"📧 Legacy email sent for alert {alert.id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error sending legacy email: {e}")
    
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
    
    def _send_secure_email_alert(self, alert: PerformanceAlert, rule: AlertRule):
        """Send secure email alert using aiosmtplib (non-blocking)"""
        if not self.secure_email_config.get('enabled'):
            self.logger.debug("Secure email not enabled")
            return
        
        if not AIOSMTPLIB_AVAILABLE:
            self.logger.warning("aiosmtplib not available, falling back to synchronous secure email")
            self._send_secure_email_sync(alert, rule)
            return
        
        try:
            # Usar async context detection para evitar conflictos de event loop
            try:
                loop = asyncio.get_running_loop()
                if loop and loop.is_running():
                    # Ya estamos en un event loop, crear task
                    task = asyncio.create_task(self._send_secure_email_async(alert, rule))
                    self.logger.info("📷 Email async en background...")
                else:
                    asyncio.run(self._send_secure_email_async(alert, rule))
            except RuntimeError:
                # No hay event loop, usar asyncio.run normalmente
                asyncio.run(self._send_secure_email_async(alert, rule))
        except Exception as e:
            self.logger.error(f"❌ Error in secure email thread: {e}")
            # Fallback to sync method
            self._send_secure_email_sync(alert, rule)
    
    async def _send_secure_email_async(self, alert: PerformanceAlert, rule: AlertRule):
        """Async secure email sending with proper SSL/TLS"""
        if not AIOSMTPLIB_AVAILABLE:
            raise ImportError("aiosmtplib not available for async email")
        
        try:
            # Enhanced email body with security and ML context
            body = self._generate_secure_email_body(alert, rule)
            
            msg = MimeMultipart()
            msg['From'] = self.secure_email_config['sender_email']
            msg['To'] = ', '.join([r.strip() for r in self.secure_email_config['recipients'] if r.strip()])
            msg['Subject'] = f"🔒 OMEGA AI Security Alert - {alert.severity.upper()} - {alert.rule_name}"
            
            # Add security headers
            msg['X-OMEGA-Alert-ID'] = alert.id
            msg['X-OMEGA-Security-Level'] = rule.security_level
            msg['X-OMEGA-Timestamp'] = alert.timestamp
            
            msg.attach(MimeText(body, 'html'))
            
            # Configure secure SMTP
            smtp_config = {
                'hostname': self.secure_email_config['smtp_host'],
                'port': self.secure_email_config['smtp_port'],
                'username': self.secure_email_config['sender_email'],
                'password': self.secure_email_config['sender_password'],
                'timeout': self.secure_email_config['timeout']
            }
            
            # Use SSL or STARTTLS based on configuration
            if self.secure_email_config['use_ssl']:
                smtp_config['use_tls'] = True
            elif self.secure_email_config['use_tls']:
                smtp_config['start_tls'] = True
            
            # Send email asynchronously
            await aiosmtplib.send(msg, **smtp_config)
            
            self.logger.info(f"🔒 Secure async email sent for alert {alert.id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error sending secure async email: {e}")
    
    def _send_secure_email_sync(self, alert: PerformanceAlert, rule: AlertRule):
        """Synchronous fallback for secure email sending"""
        try:
            # Enhanced email body with security and ML context
            body = self._generate_secure_email_body(alert, rule)
            
            msg = MimeMultipart()
            msg['From'] = self.secure_email_config['sender_email']
            msg['To'] = ', '.join([r.strip() for r in self.secure_email_config['recipients'] if r.strip()])
            msg['Subject'] = f"🔒 OMEGA AI Security Alert - {alert.severity.upper()} - {alert.rule_name}"
            
            # Add security headers
            msg['X-OMEGA-Alert-ID'] = alert.id
            msg['X-OMEGA-Security-Level'] = rule.security_level
            msg['X-OMEGA-Timestamp'] = alert.timestamp
            
            msg.attach(MimeText(body, 'html'))
            
            # Use secure SMTP with SSL/TLS
            context = ssl.create_default_context()
            
            if self.secure_email_config['use_ssl']:
                server = smtplib.SMTP_SSL(
                    self.secure_email_config['smtp_host'], 
                    self.secure_email_config['smtp_port'],
                    context=context,
                    timeout=self.secure_email_config['timeout']
                )
            else:
                server = smtplib.SMTP(
                    self.secure_email_config['smtp_host'], 
                    self.secure_email_config['smtp_port'],
                    timeout=self.secure_email_config['timeout']
                )
                if self.secure_email_config['use_tls']:
                    server.starttls(context=context)
            
            server.login(
                self.secure_email_config['sender_email'], 
                self.secure_email_config['sender_password']
            )
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"🔒 Secure sync email sent for alert {alert.id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error sending secure sync email: {e}")
    
    def _generate_secure_email_body(self, alert: PerformanceAlert, rule: AlertRule) -> str:
        """Generate enhanced HTML email body with security and ML context"""
        # Color coding based on severity
        severity_colors = {
            'info': '#17a2b8',
            'warning': '#ffc107', 
            'critical': '#dc3545'
        }
        
        color = severity_colors.get(alert.severity, '#6c757d')
        
        # ML context information
        ml_info = ""
        if alert.anomaly_score is not None:
            ml_info = f"""
            <tr>
                <td><strong>ML Anomaly Score:</strong></td>
                <td>{alert.anomaly_score:.4f}</td>
            </tr>
            <tr>
                <td><strong>Alert Confidence:</strong></td>
                <td>{alert.confidence:.1%}</td>
            </tr>
            """
        
        # Security context information  
        security_info = ""
        if alert.security_context:
            security_info = f"""
            <tr>
                <td><strong>Security Level:</strong></td>
                <td style="color: {color}; font-weight: bold;">{rule.security_level.upper()}</td>
            </tr>
            """
        
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🔒 OMEGA AI Enhanced Performance Alert</h2>
                <p>Security Level: {rule.security_level.upper()} | Severity: {alert.severity.upper()}</p>
            </div>
            
            <div class="content">
                <table>
                    <tr>
                        <td><strong>Alert ID:</strong></td>
                        <td>{alert.id}</td>
                    </tr>
                    <tr>
                        <td><strong>Timestamp:</strong></td>
                        <td>{alert.timestamp}</td>
                    </tr>
                    <tr>
                        <td><strong>Model:</strong></td>
                        <td>{alert.model_name or 'System'}</td>
                    </tr>
                    <tr>
                        <td><strong>Message:</strong></td>
                        <td style="font-weight: bold; color: {color};">{alert.message}</td>
                    </tr>
                    <tr>
                        <td><strong>Metric:</strong></td>
                        <td>{alert.metric_name}</td>
                    </tr>
                    <tr>
                        <td><strong>Current Value:</strong></td>
                        <td>{alert.metric_value:.4f}</td>
                    </tr>
                    <tr>
                        <td><strong>Threshold:</strong></td>
                        <td>{alert.threshold_value:.4f}</td>
                    </tr>
                    {security_info}
                    {ml_info}
                    <tr>
                        <td><strong>Rule:</strong></td>
                        <td>{alert.rule_name}</td>
                    </tr>
                    <tr>
                        <td><strong>Description:</strong></td>
                        <td>{alert.details.get('rule_description', 'N/A')}</td>
                    </tr>
                </table>
            </div>
            
            <div class="footer">
                <p>Generated by OMEGA AI Enhanced Performance Monitor</p>
                <p>Security-hardened with ML-driven anomaly detection</p>
            </div>
        </body>
        </html>
        """
    
    def _calculate_alert_confidence(self, rule: AlertRule, value: float, 
                                  anomaly_score: Optional[float]) -> float:
        """Calculate alert confidence based on rule type and ML context"""
        base_confidence = 0.8  # Base confidence for threshold alerts
        
        if rule.condition == 'ml_anomaly' and anomaly_score is not None:
            # Higher confidence for stronger anomaly scores
            confidence = min(0.95, 0.5 + abs(anomaly_score) * 0.1)
        elif rule.condition == 'accuracy_drop':
            # High confidence for accuracy drops
            confidence = 0.9
        elif rule.condition == 'threshold':
            # Variable confidence based on how far from threshold
            if rule.threshold_value > 0:
                deviation = abs(value - rule.threshold_value) / rule.threshold_value
                confidence = min(0.95, base_confidence + deviation * 0.15)
            else:
                confidence = base_confidence
        else:
            confidence = base_confidence
            
        return max(0.1, min(0.99, confidence))  # Clamp between 10% and 99%
    
    def _get_model_performance_context(self, model_name: Optional[str]) -> Dict[str, Any]:
        """Get performance context for a specific model"""
        if not model_name:
            return {}
            
        context = {
            'recent_alerts': 0,
            'accuracy_trend': 'stable',
            'performance_score': 0.0
        }
        
        # Count recent alerts for this model
        recent_time = datetime.now() - timedelta(hours=1)
        context['recent_alerts'] = sum(
            1 for alert in self.active_alerts.values()
            if alert.model_name == model_name and 
               datetime.fromisoformat(alert.timestamp) > recent_time
        )
        
        # Analyze accuracy trends if available
        accuracy_metrics = [name for name in self.metric_history.keys() 
                          if 'accuracy' in name.lower()]
        
        if accuracy_metrics:
            recent_accuracies = []
            for metric in accuracy_metrics:
                metric_data = self.metric_history[metric]
                if len(metric_data) >= 5:
                    recent_values = [v for _, v in list(metric_data)[-5:]]
                    recent_accuracies.extend(recent_values)
            
            if recent_accuracies:
                context['performance_score'] = np.mean(recent_accuracies) if np else sum(recent_accuracies) / len(recent_accuracies)
                
                # Determine trend
                if len(recent_accuracies) >= 3:
                    if recent_accuracies[-1] > recent_accuracies[0]:
                        context['accuracy_trend'] = 'improving'
                    elif recent_accuracies[-1] < recent_accuracies[0] - 0.05:
                        context['accuracy_trend'] = 'declining'
        
        return context
    
    def monitor_lstm_accuracy(self, accuracy: float, model_name: str = "LSTM"):
        """Specialized method for monitoring LSTM accuracy against 65% threshold"""
        self.check_metric('lstm_accuracy', accuracy, model_name)
        
        # Additional logging for LSTM accuracy tracking
        if accuracy < 0.65:
            self.logger.critical(
                f"🚨 CRITICAL: LSTM accuracy {accuracy:.1%} below 65% threshold! "
                f"Model performance degradation detected."
            )
        elif accuracy < 0.70:
            self.logger.warning(
                f"⚠️ WARNING: LSTM accuracy {accuracy:.1%} below optimal 70% target."
            )
    
    def detect_anomaly(self, metric: str, current_value: float) -> Tuple[bool, float]:
        """Public method for ML anomaly detection (as specified in CTO requirements)"""
        if not SKLEARN_AVAILABLE:
            self.logger.warning("sklearn not available for ML anomaly detection")
            return False, 0.0
        
        history = [v for _, v in self.metric_history[metric]]
        
        if len(history) < 10:
            return False, 0.0
        
        try:
            from sklearn.ensemble import IsolationForest
            
            # Reshape data for sklearn
            history_array = np.array(history).reshape(-1, 1)
            
            # Train isolation forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            iso_forest.fit(history_array)
            
            # Predict anomaly
            prediction = iso_forest.predict([[current_value]])[0]
            anomaly_score = iso_forest.decision_function([[current_value]])[0]
            
            is_anomaly = prediction == -1
            
            if is_anomaly:
                self.logger.info(f"ML Anomaly detected: {metric} = {current_value} (score: {anomaly_score:.3f})")
            
            return is_anomaly, float(anomaly_score)
            
        except Exception as e:
            self.logger.error(f"Error in ML anomaly detection: {e}")
            return False, 0.0

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