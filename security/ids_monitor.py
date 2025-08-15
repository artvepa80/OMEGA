#!/usr/bin/env python3
"""
Intrusion Detection System (IDS) and Security Monitoring for OMEGA PRO AI v10.1
Real-time threat detection, anomaly analysis, and automated response
"""

import asyncio
import json
import logging
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import redis
import geoip2.database
import requests
import psutil
import time
import threading
from pathlib import Path
import ipaddress
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import socket
import ssl
from urllib.parse import urlparse
import sqlite3
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ThreatIndicator:
    """Threat indicator data structure"""
    indicator_id: str
    indicator_type: str  # ip, domain, hash, pattern
    value: str
    threat_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    source: str
    description: str
    created_at: datetime
    expires_at: Optional[datetime]
    confidence: float  # 0.0 to 1.0

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    source_ip: str
    target_resource: str
    description: str
    details: Dict[str, Any]
    timestamp: datetime
    status: str  # OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE
    assigned_to: Optional[str]
    response_actions: List[str]
    risk_score: float

@dataclass
class NetworkConnection:
    """Network connection monitoring"""
    connection_id: str
    source_ip: str
    source_port: int
    destination_ip: str
    destination_port: int
    protocol: str
    status: str
    bytes_sent: int
    bytes_received: int
    duration: float
    first_seen: datetime
    last_seen: datetime

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io_bytes: Dict[str, int]
    active_connections: int
    failed_logins: int
    successful_logins: int
    api_requests_per_minute: int
    error_rate: float

class ThreatIntelligence:
    """Threat Intelligence Manager"""
    
    def __init__(self, db_path: str = "threat_intel.db"):
        self.db_path = db_path
        self.init_database()
        self.threat_feeds = [
            "https://feodotracker.abuse.ch/downloads/ipblocklist.txt",
            "https://reputation.alienvault.com/reputation.generic"
        ]
        self.last_update = None
        
    def init_database(self):
        """Initialize threat intelligence database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS threat_indicators (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    threat_level TEXT NOT NULL,
                    source TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    confidence REAL
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_value ON threat_indicators(value);
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_type ON threat_indicators(type);
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Threat intelligence database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize threat database: {e}")
    
    def update_threat_feeds(self) -> bool:
        """Update threat intelligence feeds"""
        try:
            updated_count = 0
            
            for feed_url in self.threat_feeds:
                try:
                    logger.info(f"Updating threat feed: {feed_url}")
                    response = requests.get(feed_url, timeout=30)
                    response.raise_for_status()
                    
                    # Parse IP blocklist
                    if "ipblocklist" in feed_url:
                        ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', response.text)
                        for ip in ips:
                            self.add_threat_indicator(
                                indicator_type="ip",
                                value=ip,
                                threat_level="HIGH",
                                source=feed_url,
                                description="Malicious IP from threat feed",
                                confidence=0.8
                            )
                            updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to update feed {feed_url}: {e}")
            
            self.last_update = datetime.utcnow()
            logger.info(f"Updated {updated_count} threat indicators")
            return True
            
        except Exception as e:
            logger.error(f"Threat feed update failed: {e}")
            return False
    
    def add_threat_indicator(self, indicator_type: str, value: str, 
                           threat_level: str, source: str, 
                           description: str = "", confidence: float = 1.0,
                           expires_at: Optional[datetime] = None) -> str:
        """Add threat indicator to database"""
        try:
            indicator_id = hashlib.sha256(f"{indicator_type}:{value}".encode()).hexdigest()[:16]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO threat_indicators 
                (id, type, value, threat_level, source, description, created_at, expires_at, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (indicator_id, indicator_type, value, threat_level, source, 
                 description, datetime.utcnow(), expires_at, confidence))
            
            conn.commit()
            conn.close()
            
            return indicator_id
            
        except Exception as e:
            logger.error(f"Failed to add threat indicator: {e}")
            return ""
    
    def check_threat_indicator(self, indicator_type: str, value: str) -> Optional[ThreatIndicator]:
        """Check if value is a known threat indicator"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM threat_indicators 
                WHERE type = ? AND value = ? 
                AND (expires_at IS NULL OR expires_at > ?)
            ''', (indicator_type, value, datetime.utcnow()))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return ThreatIndicator(
                    indicator_id=row[0],
                    indicator_type=row[1],
                    value=row[2],
                    threat_level=row[3],
                    source=row[4],
                    description=row[5] or "",
                    created_at=datetime.fromisoformat(row[6]),
                    expires_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    confidence=row[8]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Threat indicator check failed: {e}")
            return None

class AnomalyDetector:
    """Machine Learning-based Anomaly Detection"""
    
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_history = deque(maxlen=1000)
        self.model_path = "anomaly_model.pkl"
        self.scaler_path = "anomaly_scaler.pkl"
        
        # Load existing model if available
        self.load_model()
    
    def extract_features(self, metrics: SystemMetrics) -> List[float]:
        """Extract features from system metrics"""
        return [
            metrics.cpu_percent,
            metrics.memory_percent,
            metrics.disk_usage_percent,
            metrics.active_connections,
            metrics.failed_logins,
            metrics.api_requests_per_minute,
            metrics.error_rate,
            len(str(metrics.network_io_bytes))  # Simplified network activity metric
        ]
    
    def train_model(self, historical_data: List[SystemMetrics]) -> bool:
        """Train anomaly detection model"""
        try:
            if len(historical_data) < 50:  # Need minimum data for training
                logger.warning("Insufficient data for anomaly detection training")
                return False
            
            features = [self.extract_features(metrics) for metrics in historical_data]
            features_scaled = self.scaler.fit_transform(features)
            
            self.model.fit(features_scaled)
            self.is_trained = True
            
            # Save model and scaler
            self.save_model()
            
            logger.info(f"Anomaly detection model trained with {len(historical_data)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Anomaly detection training failed: {e}")
            return False
    
    def detect_anomaly(self, metrics: SystemMetrics) -> Tuple[bool, float]:
        """Detect if current metrics are anomalous"""
        try:
            if not self.is_trained:
                return False, 0.0
            
            features = [self.extract_features(metrics)]
            features_scaled = self.scaler.transform(features)
            
            # Get anomaly score (-1 for outliers, 1 for inliers)
            anomaly_score = self.model.decision_function(features_scaled)[0]
            is_anomaly = self.model.predict(features_scaled)[0] == -1
            
            # Convert to confidence score (0-1, higher = more anomalous)
            confidence = max(0, (0.5 - anomaly_score) * 2)
            
            return is_anomaly, confidence
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return False, 0.0
    
    def update_model(self, metrics: SystemMetrics, is_anomaly: bool = False):
        """Update model with new data point"""
        self.feature_history.append((metrics, is_anomaly))
        
        # Retrain periodically
        if len(self.feature_history) > 100 and len(self.feature_history) % 50 == 0:
            normal_metrics = [m for m, a in self.feature_history if not a]
            if len(normal_metrics) > 50:
                self.train_model(normal_metrics)
    
    def save_model(self):
        """Save trained model and scaler"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
        except Exception as e:
            logger.error(f"Failed to save anomaly model: {e}")
    
    def load_model(self):
        """Load saved model and scaler"""
        try:
            if Path(self.model_path).exists() and Path(self.scaler_path).exists():
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                self.is_trained = True
                logger.info("Anomaly detection model loaded")
        except Exception as e:
            logger.error(f"Failed to load anomaly model: {e}")

class SecurityMonitor:
    """Main Security Monitoring and IDS Engine"""
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        """Initialize Security Monitor"""
        
        # Redis for real-time data
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Security monitor Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
        
        # Initialize components
        self.threat_intel = ThreatIntelligence()
        self.anomaly_detector = AnomalyDetector()
        
        # Monitoring settings
        self.monitoring_enabled = True
        self.alert_thresholds = {
            'failed_logins_per_minute': 10,
            'api_requests_per_minute': 1000,
            'cpu_threshold': 90.0,
            'memory_threshold': 90.0,
            'disk_threshold': 95.0,
            'error_rate_threshold': 0.1
        }
        
        # Rate limiting
        self.connection_limits = {
            'max_connections_per_ip': 100,
            'max_requests_per_minute': 60
        }
        
        # Blocked IPs and patterns
        self.blocked_ips: Set[str] = set()
        self.suspicious_patterns = [
            r'\.\./',  # Directory traversal
            r'<script',  # XSS attempts
            r'union\s+select',  # SQL injection
            r'admin[\'"]?\s*(?:;|--)',  # Admin bypass attempts
            r'\bor\s+1\s*=\s*1\b',  # SQL injection
            r'eval\s*\(',  # Code injection
        ]
        
        # Network monitoring
        self.active_connections: Dict[str, NetworkConnection] = {}
        self.connection_stats: Dict[str, int] = defaultdict(int)
        
        # Alert management
        self.alerts: Dict[str, SecurityAlert] = {}
        self.alert_callbacks: List[Callable[[SecurityAlert], None]] = []
        
        # Metrics history
        self.metrics_history: deque = deque(maxlen=1440)  # 24 hours of minute data
        
        # GeoIP database (optional)
        self.geoip_db = None
        try:
            # Download GeoIP database if not exists
            if not Path("GeoLite2-City.mmdb").exists():
                logger.info("GeoIP database not found - geolocation features disabled")
            else:
                self.geoip_db = geoip2.database.Reader("GeoLite2-City.mmdb")
        except Exception as e:
            logger.warning(f"GeoIP database initialization failed: {e}")
        
        logger.info("Security Monitor initialized")
    
    def start_monitoring(self):
        """Start all monitoring threads"""
        logger.info("Starting security monitoring...")
        
        # Update threat feeds
        threading.Thread(target=self._update_threat_feeds_periodically, daemon=True).start()
        
        # System metrics monitoring
        threading.Thread(target=self._monitor_system_metrics, daemon=True).start()
        
        # Network monitoring
        threading.Thread(target=self._monitor_network_connections, daemon=True).start()
        
        # Log analysis
        threading.Thread(target=self._analyze_logs, daemon=True).start()
        
        logger.info("Security monitoring started")
    
    def _update_threat_feeds_periodically(self):
        """Update threat intelligence feeds periodically"""
        while self.monitoring_enabled:
            try:
                self.threat_intel.update_threat_feeds()
                time.sleep(3600)  # Update every hour
            except Exception as e:
                logger.error(f"Threat feed update error: {e}")
                time.sleep(300)  # Retry in 5 minutes on error
    
    def _monitor_system_metrics(self):
        """Monitor system performance metrics"""
        while self.monitoring_enabled:
            try:
                # Collect system metrics
                metrics = SystemMetrics(
                    timestamp=datetime.utcnow(),
                    cpu_percent=psutil.cpu_percent(),
                    memory_percent=psutil.virtual_memory().percent,
                    disk_usage_percent=psutil.disk_usage('/').percent,
                    network_io_bytes=dict(psutil.net_io_counters()._asdict()),
                    active_connections=len(psutil.net_connections()),
                    failed_logins=self._get_failed_logins_count(),
                    successful_logins=self._get_successful_logins_count(),
                    api_requests_per_minute=self._get_api_requests_count(),
                    error_rate=self._get_error_rate()
                )
                
                # Store metrics
                self.metrics_history.append(metrics)
                
                # Store in Redis
                if self.redis_client:
                    metrics_key = f"system_metrics:{int(time.time())}"
                    self.redis_client.setex(metrics_key, 3600, json.dumps(asdict(metrics), default=str))
                
                # Check for anomalies
                is_anomaly, confidence = self.anomaly_detector.detect_anomaly(metrics)
                if is_anomaly and confidence > 0.7:
                    self._create_alert(
                        alert_type="SYSTEM_ANOMALY",
                        severity="HIGH",
                        source_ip="localhost",
                        target_resource="system",
                        description=f"System anomaly detected (confidence: {confidence:.2f})",
                        details=asdict(metrics),
                        risk_score=confidence * 10
                    )
                
                # Update anomaly model
                self.anomaly_detector.update_model(metrics, is_anomaly)
                
                # Check thresholds
                self._check_metric_thresholds(metrics)
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"System metrics monitoring error: {e}")
                time.sleep(60)
    
    def _monitor_network_connections(self):
        """Monitor network connections for suspicious activity"""
        while self.monitoring_enabled:
            try:
                connections = psutil.net_connections(kind='inet')
                
                for conn in connections:
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        connection_id = f"{conn.laddr.ip}:{conn.laddr.port}-{conn.raddr.ip}:{conn.raddr.port}"
                        
                        # Check if this is a new connection
                        if connection_id not in self.active_connections:
                            # Check threat intelligence
                            threat = self.threat_intel.check_threat_indicator("ip", conn.raddr.ip)
                            if threat:
                                self._create_alert(
                                    alert_type="MALICIOUS_CONNECTION",
                                    severity=threat.threat_level,
                                    source_ip=conn.raddr.ip,
                                    target_resource=f"{conn.laddr.ip}:{conn.laddr.port}",
                                    description=f"Connection from known malicious IP: {threat.description}",
                                    details={"threat_source": threat.source, "confidence": threat.confidence},
                                    risk_score=8.0 if threat.threat_level == "HIGH" else 5.0
                                )
                            
                            # Store connection info
                            self.active_connections[connection_id] = NetworkConnection(
                                connection_id=connection_id,
                                source_ip=conn.raddr.ip,
                                source_port=conn.raddr.port,
                                destination_ip=conn.laddr.ip,
                                destination_port=conn.laddr.port,
                                protocol='tcp',
                                status=conn.status,
                                bytes_sent=0,
                                bytes_received=0,
                                duration=0.0,
                                first_seen=datetime.utcnow(),
                                last_seen=datetime.utcnow()
                            )
                            
                            # Check connection limits
                            self.connection_stats[conn.raddr.ip] += 1
                            if self.connection_stats[conn.raddr.ip] > self.connection_limits['max_connections_per_ip']:
                                self._create_alert(
                                    alert_type="CONNECTION_LIMIT_EXCEEDED",
                                    severity="MEDIUM",
                                    source_ip=conn.raddr.ip,
                                    target_resource="server",
                                    description=f"Too many connections from {conn.raddr.ip}",
                                    details={"connection_count": self.connection_stats[conn.raddr.ip]},
                                    risk_score=6.0
                                )
                                # Auto-block IP
                                self.block_ip(conn.raddr.ip, "Excessive connections", duration=timedelta(hours=1))
                
                # Cleanup old connection stats
                current_time = time.time()
                if hasattr(self, '_last_cleanup') and current_time - self._last_cleanup > 300:  # 5 minutes
                    self.connection_stats.clear()
                    self._last_cleanup = current_time
                elif not hasattr(self, '_last_cleanup'):
                    self._last_cleanup = current_time
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Network monitoring error: {e}")
                time.sleep(30)
    
    def _analyze_logs(self):
        """Analyze log files for security events"""
        log_files = [
            "/var/log/nginx/access.log",
            "/var/log/nginx/error.log",
            "api_server.log",
            "omega_ai.log"
        ]
        
        while self.monitoring_enabled:
            try:
                for log_file in log_files:
                    if Path(log_file).exists():
                        self._analyze_log_file(log_file)
                
                time.sleep(60)  # Analyze every minute
                
            except Exception as e:
                logger.error(f"Log analysis error: {e}")
                time.sleep(60)
    
    def _analyze_log_file(self, log_file: str):
        """Analyze individual log file for security events"""
        try:
            with open(log_file, 'r') as f:
                # Read last 1000 lines
                lines = deque(f, maxlen=1000)
                
                for line in lines:
                    # Check for suspicious patterns
                    for pattern in self.suspicious_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Extract IP if possible
                            ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', line)
                            source_ip = ip_match.group() if ip_match else "unknown"
                            
                            self._create_alert(
                                alert_type="SUSPICIOUS_PATTERN",
                                severity="MEDIUM",
                                source_ip=source_ip,
                                target_resource=log_file,
                                description=f"Suspicious pattern detected: {pattern}",
                                details={"log_line": line.strip(), "pattern": pattern},
                                risk_score=5.0
                            )
                            break
                    
                    # Check for failed login attempts
                    if "failed" in line.lower() and "login" in line.lower():
                        ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', line)
                        if ip_match:
                            source_ip = ip_match.group()
                            self._increment_failed_login(source_ip)
                    
                    # Check for error rates
                    if "error" in line.lower() or "500" in line:
                        self._increment_error_count()
                        
        except Exception as e:
            logger.debug(f"Log file analysis error for {log_file}: {e}")
    
    def _check_metric_thresholds(self, metrics: SystemMetrics):
        """Check system metrics against thresholds"""
        
        # CPU threshold
        if metrics.cpu_percent > self.alert_thresholds['cpu_threshold']:
            self._create_alert(
                alert_type="HIGH_CPU_USAGE",
                severity="HIGH",
                source_ip="localhost",
                target_resource="system",
                description=f"CPU usage: {metrics.cpu_percent}%",
                details={"cpu_percent": metrics.cpu_percent},
                risk_score=7.0
            )
        
        # Memory threshold
        if metrics.memory_percent > self.alert_thresholds['memory_threshold']:
            self._create_alert(
                alert_type="HIGH_MEMORY_USAGE",
                severity="HIGH",
                source_ip="localhost",
                target_resource="system",
                description=f"Memory usage: {metrics.memory_percent}%",
                details={"memory_percent": metrics.memory_percent},
                risk_score=7.0
            )
        
        # Disk threshold
        if metrics.disk_usage_percent > self.alert_thresholds['disk_threshold']:
            self._create_alert(
                alert_type="HIGH_DISK_USAGE",
                severity="CRITICAL",
                source_ip="localhost",
                target_resource="system",
                description=f"Disk usage: {metrics.disk_usage_percent}%",
                details={"disk_percent": metrics.disk_usage_percent},
                risk_score=9.0
            )
        
        # Failed logins
        if metrics.failed_logins > self.alert_thresholds['failed_logins_per_minute']:
            self._create_alert(
                alert_type="EXCESSIVE_FAILED_LOGINS",
                severity="HIGH",
                source_ip="multiple",
                target_resource="authentication",
                description=f"Failed logins: {metrics.failed_logins}/minute",
                details={"failed_logins": metrics.failed_logins},
                risk_score=8.0
            )
        
        # API request rate
        if metrics.api_requests_per_minute > self.alert_thresholds['api_requests_per_minute']:
            self._create_alert(
                alert_type="HIGH_API_TRAFFIC",
                severity="MEDIUM",
                source_ip="multiple",
                target_resource="api",
                description=f"API requests: {metrics.api_requests_per_minute}/minute",
                details={"requests_per_minute": metrics.api_requests_per_minute},
                risk_score=6.0
            )
    
    def _create_alert(self, alert_type: str, severity: str, source_ip: str,
                     target_resource: str, description: str, 
                     details: Dict[str, Any], risk_score: float) -> str:
        """Create security alert"""
        
        alert_id = hashlib.sha256(f"{alert_type}:{source_ip}:{int(time.time())}".encode()).hexdigest()[:16]
        
        alert = SecurityAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            source_ip=source_ip,
            target_resource=target_resource,
            description=description,
            details=details,
            timestamp=datetime.utcnow(),
            status="OPEN",
            assigned_to=None,
            response_actions=[],
            risk_score=risk_score
        )
        
        # Store alert
        self.alerts[alert_id] = alert
        
        # Store in Redis
        if self.redis_client:
            alert_key = f"security_alert:{alert_id}"
            self.redis_client.setex(alert_key, 86400 * 30, json.dumps(asdict(alert), default=str))
            
            # Add to alert index
            alert_index_key = f"alerts_index:{datetime.utcnow().strftime('%Y-%m-%d')}"
            self.redis_client.lpush(alert_index_key, alert_id)
            self.redis_client.expire(alert_index_key, 86400 * 30)
        
        # Execute response actions
        self._execute_automated_response(alert)
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        logger.warning(f"Security alert created: {alert_type} [{severity}] - {description}")
        return alert_id
    
    def _execute_automated_response(self, alert: SecurityAlert):
        """Execute automated response to security alert"""
        try:
            # Auto-block malicious IPs
            if alert.alert_type in ["MALICIOUS_CONNECTION", "CONNECTION_LIMIT_EXCEEDED", "SUSPICIOUS_PATTERN"]:
                if alert.source_ip != "unknown" and alert.source_ip != "localhost":
                    self.block_ip(alert.source_ip, f"Auto-blocked: {alert.alert_type}", duration=timedelta(hours=2))
                    alert.response_actions.append(f"Auto-blocked IP: {alert.source_ip}")
            
            # Scale resources for high load
            if alert.alert_type in ["HIGH_CPU_USAGE", "HIGH_MEMORY_USAGE", "HIGH_API_TRAFFIC"]:
                alert.response_actions.append("Resource scaling recommended")
            
            # Critical disk space - cleanup
            if alert.alert_type == "HIGH_DISK_USAGE":
                alert.response_actions.append("Disk cleanup initiated")
                
        except Exception as e:
            logger.error(f"Automated response failed: {e}")
    
    def block_ip(self, ip: str, reason: str, duration: timedelta = timedelta(hours=24)) -> bool:
        """Block IP address"""
        try:
            self.blocked_ips.add(ip)
            
            # Store in Redis with TTL
            if self.redis_client:
                blocked_key = f"blocked_ip:{ip}"
                block_data = {"reason": reason, "blocked_at": datetime.utcnow().isoformat()}
                self.redis_client.setex(blocked_key, int(duration.total_seconds()), json.dumps(block_data))
            
            logger.warning(f"IP blocked: {ip} - {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to block IP {ip}: {e}")
            return False
    
    def unblock_ip(self, ip: str) -> bool:
        """Unblock IP address"""
        try:
            self.blocked_ips.discard(ip)
            
            if self.redis_client:
                blocked_key = f"blocked_ip:{ip}"
                self.redis_client.delete(blocked_key)
            
            logger.info(f"IP unblocked: {ip}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unblock IP {ip}: {e}")
            return False
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        if ip in self.blocked_ips:
            return True
        
        if self.redis_client:
            blocked_key = f"blocked_ip:{ip}"
            return self.redis_client.exists(blocked_key)
        
        return False
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get security dashboard data"""
        try:
            current_metrics = self.metrics_history[-1] if self.metrics_history else None
            
            # Count alerts by severity
            alert_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for alert in self.alerts.values():
                if alert.status == "OPEN":
                    alert_counts[alert.severity] = alert_counts.get(alert.severity, 0) + 1
            
            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "system_status": "OPERATIONAL" if not alert_counts["CRITICAL"] else "CRITICAL",
                "current_metrics": asdict(current_metrics) if current_metrics else None,
                "alert_counts": alert_counts,
                "blocked_ips_count": len(self.blocked_ips),
                "active_connections": len(self.active_connections),
                "threat_indicators_count": self._get_threat_indicators_count(),
                "security_score": self._calculate_security_score(),
                "recent_alerts": [asdict(alert) for alert in list(self.alerts.values())[-10:]],
                "top_source_ips": self._get_top_source_ips(),
                "anomaly_detection_status": "ENABLED" if self.anomaly_detector.is_trained else "TRAINING"
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Dashboard data generation failed: {e}")
            return {"error": str(e)}
    
    def _calculate_security_score(self) -> float:
        """Calculate overall security score (0-100)"""
        try:
            score = 100.0
            
            # Deduct points for open alerts
            for alert in self.alerts.values():
                if alert.status == "OPEN":
                    if alert.severity == "CRITICAL":
                        score -= 20
                    elif alert.severity == "HIGH":
                        score -= 10
                    elif alert.severity == "MEDIUM":
                        score -= 5
                    else:
                        score -= 1
            
            # Deduct for blocked IPs (indicates ongoing attacks)
            score -= len(self.blocked_ips) * 0.1
            
            # Deduct for high resource usage
            if self.metrics_history:
                latest = self.metrics_history[-1]
                if latest.cpu_percent > 90:
                    score -= 5
                if latest.memory_percent > 90:
                    score -= 5
                if latest.disk_usage_percent > 95:
                    score -= 10
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Security score calculation failed: {e}")
            return 50.0
    
    def _get_threat_indicators_count(self) -> int:
        """Get count of active threat indicators"""
        try:
            conn = sqlite3.connect(self.threat_intel.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM threat_indicators WHERE expires_at IS NULL OR expires_at > ?', 
                         (datetime.utcnow(),))
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Threat indicators count failed: {e}")
            return 0
    
    def _get_top_source_ips(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top source IPs by activity"""
        try:
            ip_counts = defaultdict(int)
            
            # Count from alerts
            for alert in self.alerts.values():
                if alert.source_ip != "unknown" and alert.source_ip != "localhost":
                    ip_counts[alert.source_ip] += 1
            
            # Sort and get top IPs with geolocation
            top_ips = []
            for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:limit]:
                ip_data = {"ip": ip, "count": count}
                
                # Add geolocation if available
                if self.geoip_db:
                    try:
                        response = self.geoip_db.city(ip)
                        ip_data["country"] = response.country.name
                        ip_data["city"] = response.city.name
                    except:
                        pass
                
                # Check if blocked
                ip_data["blocked"] = self.is_ip_blocked(ip)
                
                top_ips.append(ip_data)
            
            return top_ips
            
        except Exception as e:
            logger.error(f"Top source IPs generation failed: {e}")
            return []
    
    # Helper methods for metrics collection
    def _get_failed_logins_count(self) -> int:
        """Get failed login count for last minute"""
        if self.redis_client:
            try:
                return int(self.redis_client.get("failed_logins_count") or 0)
            except:
                pass
        return 0
    
    def _get_successful_logins_count(self) -> int:
        """Get successful login count for last minute"""
        if self.redis_client:
            try:
                return int(self.redis_client.get("successful_logins_count") or 0)
            except:
                pass
        return 0
    
    def _get_api_requests_count(self) -> int:
        """Get API request count for last minute"""
        if self.redis_client:
            try:
                return int(self.redis_client.get("api_requests_count") or 0)
            except:
                pass
        return 0
    
    def _get_error_rate(self) -> float:
        """Get error rate for last minute"""
        if self.redis_client:
            try:
                errors = int(self.redis_client.get("error_count") or 0)
                total = int(self.redis_client.get("total_requests_count") or 1)
                return errors / total if total > 0 else 0.0
            except:
                pass
        return 0.0
    
    def _increment_failed_login(self, ip: str):
        """Increment failed login counter"""
        if self.redis_client:
            self.redis_client.incr("failed_logins_count")
            self.redis_client.expire("failed_logins_count", 60)
    
    def _increment_error_count(self):
        """Increment error counter"""
        if self.redis_client:
            self.redis_client.incr("error_count")
            self.redis_client.expire("error_count", 60)
    
    def add_alert_callback(self, callback: Callable[[SecurityAlert], None]):
        """Add alert notification callback"""
        self.alert_callbacks.append(callback)
    
    def stop_monitoring(self):
        """Stop security monitoring"""
        self.monitoring_enabled = False
        if self.geoip_db:
            self.geoip_db.close()
        logger.info("Security monitoring stopped")

# Alert notification functions
def email_alert_callback(alert: SecurityAlert):
    """Send email alert notification"""
    try:
        # Email configuration (should be from environment variables)
        smtp_server = os.getenv("SMTP_SERVER", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        alert_email = os.getenv("ALERT_EMAIL", "security@omega-pro-ai.com")
        
        if not all([smtp_server, smtp_username, smtp_password, alert_email]):
            logger.warning("Email configuration incomplete - skipping email alert")
            return
        
        # Create message
        msg = MimeMultipart()
        msg['From'] = smtp_username
        msg['To'] = alert_email
        msg['Subject'] = f"OMEGA Security Alert: {alert.alert_type} [{alert.severity}]"
        
        body = f"""
Security Alert Details:
- Alert ID: {alert.alert_id}
- Type: {alert.alert_type}
- Severity: {alert.severity}
- Source IP: {alert.source_ip}
- Target: {alert.target_resource}
- Description: {alert.description}
- Timestamp: {alert.timestamp}
- Risk Score: {alert.risk_score}

Details:
{json.dumps(alert.details, indent=2)}

Response Actions:
{chr(10).join(alert.response_actions) if alert.response_actions else 'None'}

This is an automated alert from OMEGA PRO AI Security Monitoring System.
"""
        
        msg.attach(MimeText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, alert_email, text)
        server.quit()
        
        logger.info(f"Email alert sent for: {alert.alert_id}")
        
    except Exception as e:
        logger.error(f"Email alert failed: {e}")

def slack_alert_callback(alert: SecurityAlert):
    """Send Slack alert notification"""
    try:
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            logger.warning("Slack webhook URL not configured - skipping Slack alert")
            return
        
        # Create Slack message
        color = {
            "CRITICAL": "#ff0000",
            "HIGH": "#ff9900", 
            "MEDIUM": "#ffcc00",
            "LOW": "#00ff00"
        }.get(alert.severity, "#cccccc")
        
        message = {
            "attachments": [
                {
                    "color": color,
                    "title": f"Security Alert: {alert.alert_type}",
                    "fields": [
                        {"title": "Severity", "value": alert.severity, "short": True},
                        {"title": "Source IP", "value": alert.source_ip, "short": True},
                        {"title": "Target", "value": alert.target_resource, "short": True},
                        {"title": "Risk Score", "value": str(alert.risk_score), "short": True},
                        {"title": "Description", "value": alert.description, "short": False}
                    ],
                    "timestamp": int(alert.timestamp.timestamp())
                }
            ]
        }
        
        # Send to Slack
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Slack alert sent for: {alert.alert_id}")
        
    except Exception as e:
        logger.error(f"Slack alert failed: {e}")

# Example usage
if __name__ == "__main__":
    # Initialize security monitor
    monitor = SecurityMonitor()
    
    # Add notification callbacks
    monitor.add_alert_callback(email_alert_callback)
    monitor.add_alert_callback(slack_alert_callback)
    
    # Start monitoring
    monitor.start_monitoring()
    
    try:
        # Keep running
        while True:
            time.sleep(60)
            
            # Print dashboard data every 5 minutes
            if int(time.time()) % 300 == 0:
                dashboard = monitor.get_security_dashboard_data()
                print(f"\nSecurity Dashboard: {json.dumps(dashboard, indent=2, default=str)}")
                
    except KeyboardInterrupt:
        logger.info("Shutting down security monitor...")
        monitor.stop_monitoring()