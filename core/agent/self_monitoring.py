#!/usr/bin/env python3
"""
👁️ SELF-MONITORING & ALERTS SYSTEM - Fase 4 del Sistema Agéntico
Sistema de auto-monitoreo continuo con alertas inteligentes y diagnósticos
Supervisa salud del sistema, performance y eventos críticos en tiempo real
"""

import json
import time
import logging
import threading
try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    # Crear clases dummy para compatibilidad
    class MimeText:
        def __init__(self, *args, **kwargs):
            pass
    class MimeMultipart:
        def __init__(self, *args, **kwargs):
            pass
from typing import Dict, List, Any, Optional, Callable, Protocol, Iterable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import deque, defaultdict
try:
    import psutil
except Exception:
    psutil = None
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)
try:
    # Integración: WhatsApp Notifier opcional
    from notifications.notifier_enhanced import WhatsAppNotifier  # type: ignore
    from integrations.whatsapp_client_enhanced import WhatsAppClient  # type: ignore
    _WA_AVAILABLE = True
except Exception:
    _WA_AVAILABLE = False

class AlertLevel(Enum):
    """Niveles de alerta"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertChannel(Enum):
    """Canales de notificación"""
    LOG = "log"
    EMAIL = "email"
    FILE = "file"
    CONSOLE = "console"
    WEBHOOK = "webhook"

@dataclass
class Alert:
    """Definición de una alerta"""
    alert_id: str
    title: str
    message: str
    level: AlertLevel
    category: str
    timestamp: str
    source_component: str
    context: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[str] = None
    acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    escalation_count: int = 0

@dataclass
class MonitoringMetric:
    """Métrica de monitoreo"""
    name: str
    value: float
    unit: str
    timestamp: str
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    trend: str = "stable"  # "increasing", "decreasing", "stable"

class SystemHealthMonitor:
    """Monitor de salud del sistema"""
    
    def __init__(self):
        self.metrics_history = defaultdict(lambda: deque(maxlen=100))
        self.health_checks = {}
        self.last_check_time = datetime.now()
        
        # Thresholds por defecto
        self.thresholds = {
            "cpu_usage": {"warning": 80.0, "critical": 95.0},
            "memory_usage": {"warning": 85.0, "critical": 95.0},
            "disk_usage": {"warning": 90.0, "critical": 98.0},
            "process_count": {"warning": 300, "critical": 500},
            "network_latency": {"warning": 1000, "critical": 5000},  # ms
            "response_time": {"warning": 5.0, "critical": 15.0},  # seconds
            "error_rate": {"warning": 0.05, "critical": 0.15},  # 5% - 15%
            "queue_size": {"warning": 100, "critical": 500}
        }
        
        logger.info("👁️ SystemHealthMonitor inicializado")
    
    def collect_system_metrics(self) -> List[MonitoringMetric]:
        """Recolecta métricas del sistema"""
        
        metrics = []
        timestamp = datetime.now().isoformat()
        
        try:
            # CPU
            cpu_usage = psutil.cpu_percent(interval=1) if psutil else 0.0
            metrics.append(MonitoringMetric(
                name="cpu_usage",
                value=cpu_usage,
                unit="%",
                timestamp=timestamp,
                threshold_warning=self.thresholds["cpu_usage"]["warning"],
                threshold_critical=self.thresholds["cpu_usage"]["critical"]
            ))
            
            # Memoria
            memory = psutil.virtual_memory() if psutil else type("M", (), {"percent": 0.0, "available": 8*1024**3})()
            metrics.append(MonitoringMetric(
                name="memory_usage",
                value=memory.percent,
                unit="%",
                timestamp=timestamp,
                threshold_warning=self.thresholds["memory_usage"]["warning"],
                threshold_critical=self.thresholds["memory_usage"]["critical"]
            ))
            
            # Disco
            disk = psutil.disk_usage('/') if psutil else type("D", (), {"percent": 0.0})()
            metrics.append(MonitoringMetric(
                name="disk_usage",
                value=disk.percent,
                unit="%",
                timestamp=timestamp,
                threshold_warning=self.thresholds["disk_usage"]["warning"],
                threshold_critical=self.thresholds["disk_usage"]["critical"]
            ))
            
            # Procesos
            process_count = len(psutil.pids()) if psutil else 0
            metrics.append(MonitoringMetric(
                name="process_count",
                value=process_count,
                unit="count",
                timestamp=timestamp,
                threshold_warning=self.thresholds["process_count"]["warning"],
                threshold_critical=self.thresholds["process_count"]["critical"]
            ))
            
            # Memoria disponible
            metrics.append(MonitoringMetric(
                name="available_memory",
                value=memory.available / (1024**3),  # GB
                unit="GB",
                timestamp=timestamp
            ))
            
        except Exception as e:
            logger.error(f"Error recolectando métricas del sistema: {e}")
        
        # Almacenar en historial y calcular tendencias
        for metric in metrics:
            self.metrics_history[metric.name].append(metric.value)
            metric.trend = self._calculate_trend(metric.name)
        
        self.last_check_time = datetime.now()
        
        return metrics
    
    def _calculate_trend(self, metric_name: str) -> str:
        """Calcula tendencia de una métrica"""
        
        history = list(self.metrics_history[metric_name])
        
        if len(history) < 5:
            return "stable"
        
        # Comparar últimos 3 valores con 3 anteriores
        recent = history[-3:]
        previous = history[-6:-3] if len(history) >= 6 else history[:-3]
        
        recent_avg = sum(recent) / len(recent)
        previous_avg = sum(previous) / len(previous)
        
        change_pct = (recent_avg - previous_avg) / previous_avg * 100 if previous_avg != 0 else 0
        
        if change_pct > 5:
            return "increasing"
        elif change_pct < -5:
            return "decreasing"
        else:
            return "stable"
    
    def check_metric_thresholds(self, metrics: List[MonitoringMetric]) -> List[Alert]:
        """Verifica thresholds y genera alertas"""
        
        alerts = []
        
        for metric in metrics:
            alert = self._check_single_metric(metric)
            if alert:
                alerts.append(alert)
        
        return alerts
    
    def _check_single_metric(self, metric: MonitoringMetric) -> Optional[Alert]:
        """Verifica una métrica individual"""
        
        if metric.threshold_critical and metric.value >= metric.threshold_critical:
            return Alert(
                alert_id=f"critical_{metric.name}_{int(time.time())}",
                title=f"Critical: {metric.name} threshold exceeded",
                message=f"{metric.name} is at {metric.value}{metric.unit} (critical threshold: {metric.threshold_critical}{metric.unit})",
                level=AlertLevel.CRITICAL,
                category="system_health",
                timestamp=metric.timestamp,
                source_component="system_health_monitor",
                context={
                    "metric_name": metric.name,
                    "current_value": metric.value,
                    "threshold": metric.threshold_critical,
                    "unit": metric.unit,
                    "trend": metric.trend
                }
            )
        
        elif metric.threshold_warning and metric.value >= metric.threshold_warning:
            return Alert(
                alert_id=f"warning_{metric.name}_{int(time.time())}",
                title=f"Warning: {metric.name} approaching threshold",
                message=f"{metric.name} is at {metric.value}{metric.unit} (warning threshold: {metric.threshold_warning}{metric.unit})",
                level=AlertLevel.WARNING,
                category="system_health",
                timestamp=metric.timestamp,
                source_component="system_health_monitor",
                context={
                    "metric_name": metric.name,
                    "current_value": metric.value,
                    "threshold": metric.threshold_warning,
                    "unit": metric.unit,
                    "trend": metric.trend
                }
            )
        
        return None

class AgentPerformanceMonitor:
    """Monitor de performance del agente"""
    
    def __init__(self):
        self.cycle_metrics = deque(maxlen=50)
        self.performance_baseline = None
        self.degradation_threshold = 0.15  # 15% degradation
        
        logger.info("🤖 AgentPerformanceMonitor inicializado")
    
    def record_cycle_metrics(self, cycle_result: Dict[str, Any]) -> List[Alert]:
        """Registra métricas de un ciclo y genera alertas si es necesario"""
        
        alerts = []
        timestamp = datetime.now().isoformat()
        
        # Extraer métricas del ciclo
        evaluation = cycle_result.get("evaluation", {})
        metrics = evaluation.get("metrics", {})
        
        cycle_metrics = {
            "timestamp": timestamp,
            "best_reward": metrics.get("best_reward", 0),
            "average_reward": metrics.get("average_reward", 0),
            "quality_rate": metrics.get("quality_rate", 0),
            "execution_time": metrics.get("average_execution_time", 0),
            "cycle_duration": cycle_result.get("duration_seconds", 0),
            "success": "error" not in cycle_result
        }
        
        self.cycle_metrics.append(cycle_metrics)
        
        # Establecer baseline si es la primera vez
        if self.performance_baseline is None and len(self.cycle_metrics) >= 5:
            self._establish_baseline()
        
        # Verificar degradación de performance
        if self.performance_baseline:
            alerts.extend(self._check_performance_degradation(cycle_metrics))
        
        # Verificar fallos consecutivos
        alerts.extend(self._check_consecutive_failures())
        
        return alerts
    
    def _establish_baseline(self):
        """Establece baseline de performance"""
        
        recent_cycles = list(self.cycle_metrics)[-5:]
        
        self.performance_baseline = {
            "avg_reward": sum(c["best_reward"] for c in recent_cycles) / len(recent_cycles),
            "avg_quality": sum(c["quality_rate"] for c in recent_cycles) / len(recent_cycles),
            "avg_duration": sum(c["cycle_duration"] for c in recent_cycles) / len(recent_cycles),
            "success_rate": sum(1 for c in recent_cycles if c["success"]) / len(recent_cycles),
            "established_at": datetime.now().isoformat()
        }
        
        logger.info(f"📊 Performance baseline establecido: reward={self.performance_baseline['avg_reward']:.3f}")
    
    def _check_performance_degradation(self, current_metrics: Dict[str, Any]) -> List[Alert]:
        """Verifica degradación de performance"""
        
        alerts = []
        
        # Verificar reward
        reward_degradation = (self.performance_baseline["avg_reward"] - current_metrics["best_reward"]) / self.performance_baseline["avg_reward"]
        
        if reward_degradation > self.degradation_threshold:
            alerts.append(Alert(
                alert_id=f"perf_degradation_reward_{int(time.time())}",
                title="Performance Degradation: Reward",
                message=f"Reward dropped by {reward_degradation:.1%} from baseline ({current_metrics['best_reward']:.3f} vs {self.performance_baseline['avg_reward']:.3f})",
                level=AlertLevel.WARNING,
                category="agent_performance",
                timestamp=current_metrics["timestamp"],
                source_component="agent_performance_monitor",
                context={
                    "current_reward": current_metrics["best_reward"],
                    "baseline_reward": self.performance_baseline["avg_reward"],
                    "degradation_pct": reward_degradation * 100
                }
            ))
        
        # Verificar quality rate
        quality_degradation = (self.performance_baseline["avg_quality"] - current_metrics["quality_rate"]) / self.performance_baseline["avg_quality"]
        
        if quality_degradation > self.degradation_threshold:
            alerts.append(Alert(
                alert_id=f"perf_degradation_quality_{int(time.time())}",
                title="Performance Degradation: Quality",
                message=f"Quality rate dropped by {quality_degradation:.1%} from baseline",
                level=AlertLevel.WARNING,
                category="agent_performance",
                timestamp=current_metrics["timestamp"],
                source_component="agent_performance_monitor",
                context={
                    "current_quality": current_metrics["quality_rate"],
                    "baseline_quality": self.performance_baseline["avg_quality"],
                    "degradation_pct": quality_degradation * 100
                }
            ))
        
        return alerts
    
    def _check_consecutive_failures(self) -> List[Alert]:
        """Verifica fallos consecutivos"""
        
        alerts = []
        
        if len(self.cycle_metrics) >= 3:
            recent_cycles = list(self.cycle_metrics)[-3:]
            consecutive_failures = all(not cycle["success"] for cycle in recent_cycles)
            
            if consecutive_failures:
                alerts.append(Alert(
                    alert_id=f"consecutive_failures_{int(time.time())}",
                    title="Critical: Consecutive Cycle Failures",
                    message="Agent has failed 3 consecutive cycles",
                    level=AlertLevel.CRITICAL,
                    category="agent_reliability",
                    timestamp=datetime.now().isoformat(),
                    source_component="agent_performance_monitor",
                    context={
                        "consecutive_failures": 3,
                        "recent_cycles": recent_cycles
                    }
                ))
        
        return alerts

class AlertManager:
    """Gestor de alertas y notificaciones"""
    
    def __init__(self):
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.notification_channels = {}
        self.escalation_rules = {}
        
        # Configuración de notificaciones
        self.config = {
            "enable_email_notifications": False,
            "email_recipients": [],
            "smtp_server": "localhost",
            "smtp_port": 587,
            "smtp_username": "",
            "smtp_password": "",
            "escalation_delay_minutes": 30,
            "max_escalations": 3,
            "quiet_hours": {"start": "22:00", "end": "08:00"},
            "enable_quiet_hours": False
        }
        
        # Estadísticas
        self.stats = {
            "total_alerts": 0,
            "alerts_by_level": defaultdict(int),
            "alerts_by_category": defaultdict(int),
            "resolution_times": [],
            "average_resolution_time": 0
        }
        
        logger.info("🚨 AlertManager inicializado")
        # Fanout de notifiers externos (p. ej., WhatsApp)
        self._notifiers: List[Notifier] = []
    
    def process_alert(self, alert: Alert) -> Dict[str, Any]:
        """Procesa una nueva alerta"""
        
        # Verificar si es duplicada
        if self._is_duplicate_alert(alert):
            logger.debug(f"Alerta duplicada ignorada: {alert.alert_id}")
            return {"processed": False, "reason": "duplicate"}
        
        # Añadir a alertas activas
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        
        # Actualizar estadísticas
        self.stats["total_alerts"] += 1
        self.stats["alerts_by_level"][alert.level.value] += 1
        self.stats["alerts_by_category"][alert.category] += 1
        
        # Enviar notificaciones internas (log/console/file/email)
        notifications_sent = self._send_notifications(alert)
        # Fanout a notifiers externos
        try:
            self._fanout(alert)
        except Exception:
            pass
        
        # Programar escalation si es necesario
        if alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            self._schedule_escalation(alert)
        
        logger.info(f"🚨 Alerta procesada: {alert.title} ({alert.level.value})")
        
        return {
            "processed": True,
            "alert_id": alert.alert_id,
            "notifications_sent": notifications_sent,
            "escalation_scheduled": alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]
        }

    # === Notifiers externos ===
    def register_notifier(self, notifier: "Notifier") -> None:
        self._notifiers.append(notifier)

    def register_notifiers(self, notifiers: Iterable["Notifier"]) -> None:
        for n in notifiers:
            self.register_notifier(n)

    def _fanout(self, alert: Alert) -> None:
        message = f"🚨 {alert.level.value.upper()} | {alert.title}\n{alert.message}"
        for notifier in list(self._notifiers):
            try:
                notifier.notify(message)
            except Exception:
                # No bloquear por errores del canal externo
                continue
    
    def _is_duplicate_alert(self, alert: Alert) -> bool:
        """Verifica si la alerta es duplicada"""
        
        # Buscar alertas similares en las últimas 5 minutos
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        for existing_alert in self.active_alerts.values():
            if (existing_alert.category == alert.category and
                existing_alert.source_component == alert.source_component and
                existing_alert.level == alert.level and
                not existing_alert.resolved):
                
                # Verificar si la alerta existente es reciente
                existing_time = datetime.fromisoformat(existing_alert.timestamp)
                if existing_time > cutoff_time:
                    return True
        
        return False
    
    def _send_notifications(self, alert: Alert) -> List[str]:
        """Envía notificaciones por los canales configurados"""
        
        notifications_sent = []
        
        # Verificar quiet hours
        if self._is_quiet_hours() and alert.level not in [AlertLevel.CRITICAL]:
            logger.debug("Notificación diferida por quiet hours")
            return notifications_sent
        
        # Log notification (siempre activa)
        self._send_log_notification(alert)
        notifications_sent.append("log")
        
        # Console notification
        self._send_console_notification(alert)
        notifications_sent.append("console")
        
        # File notification
        self._send_file_notification(alert)
        notifications_sent.append("file")
        
        # Email notification (si está configurado)
        if self.config["enable_email_notifications"] and self.config["email_recipients"]:
            if self._send_email_notification(alert):
                notifications_sent.append("email")
        
        return notifications_sent
    
    def _is_quiet_hours(self) -> bool:
        """Verifica si estamos en horario de silencio"""
        
        if not self.config["enable_quiet_hours"]:
            return False
        
        now = datetime.now().time()
        start_time = datetime.strptime(self.config["quiet_hours"]["start"], "%H:%M").time()
        end_time = datetime.strptime(self.config["quiet_hours"]["end"], "%H:%M").time()
        
        if start_time <= end_time:
            return start_time <= now <= end_time
        else:  # Quiet hours cross midnight
            return now >= start_time or now <= end_time
    
    def _send_log_notification(self, alert: Alert):
        """Envía notificación al log"""
        
        log_message = f"[{alert.level.value.upper()}] {alert.title}: {alert.message}"
        
        if alert.level == AlertLevel.CRITICAL:
            logger.critical(log_message)
        elif alert.level == AlertLevel.ERROR:
            logger.error(log_message)
        elif alert.level == AlertLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _send_console_notification(self, alert: Alert):
        """Envía notificación a consola"""
        
        level_icons = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        icon = level_icons.get(alert.level, "📢")
        print(f"\n{icon} ALERT [{alert.level.value.upper()}]: {alert.title}")
        print(f"   📅 {alert.timestamp}")
        print(f"   📝 {alert.message}")
        print(f"   🔧 Source: {alert.source_component}")
    
    def _send_file_notification(self, alert: Alert):
        """Envía notificación a archivo"""
        
        try:
            from pathlib import Path
            
            alerts_dir = Path("results/alerts")
            alerts_dir.mkdir(parents=True, exist_ok=True)
            
            alert_file = alerts_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.jsonl"
            
            with open(alert_file, 'a') as f:
                f.write(json.dumps(asdict(alert), default=str) + '\n')
                
        except Exception as e:
            logger.error(f"Error escribiendo alerta a archivo: {e}")
    
    def _send_email_notification(self, alert: Alert) -> bool:
        """Envía notificación por email"""
        
        if not EMAIL_AVAILABLE:
            logger.warning("Email functionality not available")
            return False
        
        try:
            # Crear mensaje
            msg = MimeMultipart()
            msg['From'] = self.config["smtp_username"]
            msg['To'] = ", ".join(self.config["email_recipients"])
            msg['Subject'] = f"OMEGA Alert: {alert.title}"
            
            # Cuerpo del mensaje
            body = f"""
OMEGA Agent Alert

Level: {alert.level.value.upper()}
Category: {alert.category}
Source: {alert.source_component}
Timestamp: {alert.timestamp}

Message:
{alert.message}

Context:
{json.dumps(alert.context, indent=2)}

Alert ID: {alert.alert_id}
"""
            
            msg.attach(MimeText(body, 'plain'))
            
            # Enviar email
            server = smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"])
            if self.config["smtp_username"]:
                server.starttls()
                server.login(self.config["smtp_username"], self.config["smtp_password"])
            
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
            return False
    
    def _schedule_escalation(self, alert: Alert):
        """Programa escalation de una alerta"""
        
        def escalate():
            time.sleep(self.config["escalation_delay_minutes"] * 60)
            
            if alert.alert_id in self.active_alerts and not self.active_alerts[alert.alert_id].resolved:
                alert.escalation_count += 1
                
                if alert.escalation_count <= self.config["max_escalations"]:
                    escalated_alert = Alert(
                        alert_id=f"{alert.alert_id}_escalation_{alert.escalation_count}",
                        title=f"ESCALATED: {alert.title}",
                        message=f"Unresolved alert (escalation #{alert.escalation_count}): {alert.message}",
                        level=AlertLevel.CRITICAL,
                        category=alert.category,
                        timestamp=datetime.now().isoformat(),
                        source_component=alert.source_component,
                        context={**alert.context, "original_alert_id": alert.alert_id, "escalation_count": alert.escalation_count}
                    )
                    
                    self.process_alert(escalated_alert)
        
        # Ejecutar escalation en thread separado
        escalation_thread = threading.Thread(target=escalate, daemon=True)
        escalation_thread.start()
    
    def resolve_alert(self, alert_id: str, resolution_note: str = "") -> bool:
        """Resuelve una alerta"""
        
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.now().isoformat()
        
        # Calcular tiempo de resolución
        alert_time = datetime.fromisoformat(alert.timestamp)
        resolution_time = datetime.now()
        resolution_duration = (resolution_time - alert_time).total_seconds()
        
        self.stats["resolution_times"].append(resolution_duration)
        
        # Actualizar tiempo promedio de resolución
        if self.stats["resolution_times"]:
            self.stats["average_resolution_time"] = sum(self.stats["resolution_times"]) / len(self.stats["resolution_times"])
        
        # Remover de alertas activas
        del self.active_alerts[alert_id]
        
        logger.info(f"✅ Alerta resuelta: {alert.title} (duración: {resolution_duration:.1f}s)")
        
        return True
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de alertas"""
        
        active_by_level = defaultdict(int)
        for alert in self.active_alerts.values():
            active_by_level[alert.level.value] += 1
        
        return {
            "active_alerts": len(self.active_alerts),
            "active_by_level": dict(active_by_level),
            "total_alerts_processed": self.stats["total_alerts"],
            "alerts_by_level": dict(self.stats["alerts_by_level"]),
            "alerts_by_category": dict(self.stats["alerts_by_category"]),
            "average_resolution_time_seconds": self.stats["average_resolution_time"],
            "recent_alerts": list(self.alert_history)[-5:]
        }

class SelfMonitoringSystem:
    """Sistema principal de auto-monitoreo"""
    
    def __init__(self):
        self.system_monitor = SystemHealthMonitor()
        self.performance_monitor = AgentPerformanceMonitor()
        self.alert_manager = AlertManager()
        # Registrar notificador de WhatsApp si hay credenciales
        if _WA_AVAILABLE:
            try:
                import os
                token = os.getenv("WHATSAPP_TOKEN", "")
                phone_id = os.getenv("WHATSAPP_PHONE_ID", "")
                admins = [x.strip() for x in os.getenv("WHATSAPP_ADMIN", "").split(",") if x.strip()]
                if token and phone_id and admins:
                    wa_client = WhatsAppClient(token=token, phone_number_id=phone_id, dry_run=False)
                    self.alert_manager.register_notifier(WhatsAppNotifier(wa_client, admins))
            except Exception:
                pass
        
        self.is_monitoring = False
        self.monitoring_thread = None
        self.monitoring_interval = 60  # seconds
        
        logger.info("👁️ SelfMonitoringSystem inicializado")
    
    def start_monitoring(self):
        """Inicia monitoreo continuo"""
        
        if self.is_monitoring:
            logger.warning("⚠️ Monitoreo ya está activo")
            return
        
        self.is_monitoring = True
        
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="SelfMonitoring",
            daemon=True
        )
        self.monitoring_thread.start()
        
        logger.info("👁️ Monitoreo continuo iniciado")
    
    def stop_monitoring(self):
        """Detiene monitoreo continuo"""
        
        self.is_monitoring = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)
        
        logger.info("🛑 Monitoreo continuo detenido")
    
    def _monitoring_loop(self):
        """Loop principal de monitoreo"""
        
        while self.is_monitoring:
            try:
                # Recolectar métricas del sistema
                system_metrics = self.system_monitor.collect_system_metrics()
                
                # Verificar thresholds
                system_alerts = self.system_monitor.check_metric_thresholds(system_metrics)
                
                # Procesar alertas del sistema
                for alert in system_alerts:
                    self.alert_manager.process_alert(alert)
                
                # Esperar hasta próximo ciclo
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error en loop de monitoreo: {e}")
                time.sleep(10)  # Esperar antes de continuar
    
    def process_agent_cycle(self, cycle_result: Dict[str, Any]):
        """Procesa resultado de ciclo del agente"""
        
        # Monitor de performance del agente
        performance_alerts = self.performance_monitor.record_cycle_metrics(cycle_result)
        
        # Procesar alertas de performance
        for alert in performance_alerts:
            self.alert_manager.process_alert(alert)
    
    def trigger_custom_alert(self, title: str, message: str, level: AlertLevel, 
                           category: str, context: Dict[str, Any] = None):
        """Trigger una alerta personalizada"""
        
        alert = Alert(
            alert_id=f"custom_{int(time.time())}",
            title=title,
            message=message,
            level=level,
            category=category,
            timestamp=datetime.now().isoformat(),
            source_component="custom",
            context=context or {}
        )
        
        self.alert_manager.process_alert(alert)
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del monitoreo"""
        
        system_metrics = self.system_monitor.collect_system_metrics()
        alert_summary = self.alert_manager.get_alert_summary()
        
        return {
            "monitoring_active": self.is_monitoring,
            "monitoring_interval": self.monitoring_interval,
            "system_health": {
                "last_check": self.system_monitor.last_check_time.isoformat(),
                "current_metrics": [asdict(m) for m in system_metrics],
                "overall_health": self._calculate_overall_health(system_metrics)
            },
            "agent_performance": {
                "baseline_established": self.performance_monitor.performance_baseline is not None,
                "recent_cycles": len(self.performance_monitor.cycle_metrics),
                "baseline_info": self.performance_monitor.performance_baseline
            },
            "alerts": alert_summary,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_overall_health(self, metrics: List[MonitoringMetric]) -> str:
        """Calcula salud general del sistema"""
        
        critical_issues = 0
        warning_issues = 0
        
        for metric in metrics:
            if metric.threshold_critical and metric.value >= metric.threshold_critical:
                critical_issues += 1
            elif metric.threshold_warning and metric.value >= metric.threshold_warning:
                warning_issues += 1
        
        if critical_issues > 0:
            return "critical"
        elif warning_issues > 0:
            return "warning"
        else:
            return "healthy"

# Función de conveniencia
def create_self_monitoring_system() -> SelfMonitoringSystem:
    """Crea sistema de auto-monitoreo configurado"""
    return SelfMonitoringSystem()

if __name__ == '__main__':
    # Test básico del sistema
    print("👁️ Testing Self-Monitoring System...")
    
    monitoring = create_self_monitoring_system()
    
    # Iniciar monitoreo
    monitoring.start_monitoring()
    
    try:
        # Simular algunos ciclos del agente
        for i in range(3):
            mock_cycle_result = {
                "evaluation": {
                    "metrics": {
                        "best_reward": 0.75 - (i * 0.1),  # Degradación simulada
                        "average_reward": 0.70 - (i * 0.08),
                        "quality_rate": 0.85 - (i * 0.05),
                        "average_execution_time": 45 + (i * 5)
                    }
                },
                "duration_seconds": 120 + (i * 10)
            }
            
            monitoring.process_agent_cycle(mock_cycle_result)
            time.sleep(2)
        
        # Trigger alerta personalizada
        monitoring.trigger_custom_alert(
            "Test Alert",
            "This is a test alert from the monitoring system",
            AlertLevel.WARNING,
            "testing",
            {"test_parameter": "test_value"}
        )
        
        # Esperar un poco para que se procesen las alertas
        time.sleep(5)
        
        # Obtener estado
        status = monitoring.get_monitoring_status()
        
        print(f"✅ Test completado:")
        print(f"   👁️ Monitoreo activo: {'✅' if status['monitoring_active'] else '❌'}")
        print(f"   💚 Salud general: {status['system_health']['overall_health']}")
        print(f"   🚨 Alertas activas: {status['alerts']['active_alerts']}")
        print(f"   📊 Total alertas procesadas: {status['alerts']['total_alerts_processed']}")
        print(f"   🤖 Baseline performance: {'✅' if status['agent_performance']['baseline_established'] else '❌'}")
        
    except KeyboardInterrupt:
        print("\n   🛑 Stopping monitoring...")
    finally:
        monitoring.stop_monitoring()
        print("   ✅ Monitoreo detenido")
