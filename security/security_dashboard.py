#!/usr/bin/env python3
"""
Security Dashboard and Monitoring Interface for OMEGA PRO AI v10.1
Real-time security monitoring, incident management, and executive reporting
"""

import os
import json
import logging
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import redis
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import plotly.graph_objs as go
import plotly.utils
import pandas as pd
from jinja2 import Template
import threading
import time
from collections import defaultdict, deque

# Import our security modules
from auth_manager import AdvancedAuthManager
from ids_monitor import SecurityMonitor
from audit_compliance import SecureAuditLogger, ComplianceManager
from encryption_manager import DataProtectionManager, SecureKeyManager
from vulnerability_scanner import VulnerabilityScanner

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SecurityMetrics:
    """Security metrics data structure"""
    timestamp: datetime
    security_score: float
    active_threats: int
    blocked_ips: int
    failed_logins: int
    successful_logins: int
    api_requests: int
    error_rate: float
    vulnerability_count: int
    compliance_score: float
    encryption_operations: int
    audit_events: int

@dataclass
class ThreatIncident:
    """Security threat incident"""
    incident_id: str
    incident_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    status: str  # OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE
    source_ip: str
    target_resource: str
    description: str
    first_detected: datetime
    last_updated: datetime
    assigned_to: Optional[str]
    mitigation_actions: List[str]
    evidence: Dict[str, Any]
    impact_assessment: str
    remediation_status: str

class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, id, username, email, role):
        self.id = id
        self.username = username
        self.email = email
        self.role = role

class SecurityDashboard:
    """Main security dashboard application"""
    
    def __init__(self):
        """Initialize security dashboard"""
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.secret_key = os.environ.get('DASHBOARD_SECRET_KEY', secrets.token_urlsafe(32))
        
        # Initialize SocketIO for real-time updates
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize Flask-Login
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = 'login'
        
        # Initialize security modules
        try:
            self.auth_manager = AdvancedAuthManager(
                jwt_secret=os.environ.get('JWT_SECRET', 'default-jwt-secret-change-me')
            )
            self.security_monitor = SecurityMonitor()
            self.audit_logger = SecureAuditLogger()
            self.compliance_manager = ComplianceManager(self.audit_logger)
            self.key_manager = SecureKeyManager()
            self.data_manager = DataProtectionManager(self.key_manager)
            self.vuln_scanner = VulnerabilityScanner()
            
            logger.info("Security modules initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize security modules: {e}")
            # Initialize with None to handle gracefully
            self.auth_manager = None
            self.security_monitor = None
            self.audit_logger = None
            self.compliance_manager = None
            self.key_manager = None
            self.data_manager = None
            self.vuln_scanner = None
        
        # Dashboard state
        self.active_incidents: Dict[str, ThreatIncident] = {}
        self.metrics_history = deque(maxlen=1440)  # 24 hours of minute data
        self.connected_clients = set()
        
        # Initialize database
        self.init_dashboard_database()
        
        # Set up routes
        self.setup_routes()
        
        # Start background tasks
        self.start_background_tasks()
        
        logger.info("Security Dashboard initialized")
    
    def init_dashboard_database(self):
        """Initialize dashboard database"""
        try:
            conn = sqlite3.connect('security_dashboard.db')
            cursor = conn.cursor()
            
            # Dashboard users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dashboard_users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    mfa_enabled BOOLEAN DEFAULT 0,
                    mfa_secret TEXT
                )
            ''')
            
            # Security incidents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_incidents (
                    incident_id TEXT PRIMARY KEY,
                    incident_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source_ip TEXT,
                    target_resource TEXT,
                    description TEXT,
                    first_detected TIMESTAMP NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    assigned_to TEXT,
                    mitigation_actions TEXT,
                    evidence TEXT,
                    impact_assessment TEXT,
                    remediation_status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Security metrics history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_metrics_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    security_score REAL,
                    active_threats INTEGER,
                    blocked_ips INTEGER,
                    failed_logins INTEGER,
                    successful_logins INTEGER,
                    api_requests INTEGER,
                    error_rate REAL,
                    vulnerability_count INTEGER,
                    compliance_score REAL,
                    encryption_operations INTEGER,
                    audit_events INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create default admin user if not exists
            cursor.execute('SELECT COUNT(*) FROM dashboard_users')
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                admin_id = secrets.token_urlsafe(16)
                admin_password = generate_password_hash('admin123!')  # Change this!
                cursor.execute('''
                    INSERT INTO dashboard_users 
                    (id, username, email, password_hash, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', (admin_id, 'admin', 'admin@omega-pro-ai.com', admin_password, 'admin'))
                
                logger.warning("Created default admin user - change password immediately!")
            
            conn.commit()
            conn.close()
            
            os.chmod('security_dashboard.db', 0o600)
            
            logger.info("Dashboard database initialized")
            
        except Exception as e:
            logger.error(f"Dashboard database initialization failed: {e}")
            raise
    
    def setup_routes(self):
        """Set up Flask routes"""
        
        @self.login_manager.user_loader
        def load_user(user_id):
            return self.get_user_by_id(user_id)
        
        @self.app.route('/')
        @login_required
        def dashboard():
            """Main dashboard page"""
            try:
                # Get current security metrics
                metrics = self.get_current_metrics()
                
                # Get recent incidents
                recent_incidents = self.get_recent_incidents(limit=10)
                
                # Get vulnerability summary
                vuln_summary = {}
                if self.vuln_scanner:
                    vuln_summary = self.vuln_scanner.get_vulnerability_summary(days_back=7)
                
                # Get compliance status
                compliance_status = self.get_compliance_status()
                
                # Generate charts data
                charts_data = self.generate_charts_data()
                
                return render_template_string(DASHBOARD_TEMPLATE, 
                    metrics=metrics,
                    incidents=recent_incidents,
                    vuln_summary=vuln_summary,
                    compliance_status=compliance_status,
                    charts_data=charts_data,
                    user=current_user
                )
                
            except Exception as e:
                logger.error(f"Dashboard rendering failed: {e}")
                return f"Dashboard error: {str(e)}", 500
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Login page"""
            if request.method == 'POST':
                username = request.form['username']
                password = request.form['password']
                mfa_token = request.form.get('mfa_token', '')
                
                user = self.authenticate_user(username, password, mfa_token)
                if user:
                    login_user(user)
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid credentials')
            
            return render_template_string(LOGIN_TEMPLATE)
        
        @self.app.route('/logout')
        @login_required
        def logout():
            """Logout"""
            logout_user()
            return redirect(url_for('login'))
        
        @self.app.route('/api/metrics')
        @login_required
        def api_metrics():
            """API endpoint for current metrics"""
            return jsonify(self.get_current_metrics())
        
        @self.app.route('/api/incidents')
        @login_required
        def api_incidents():
            """API endpoint for incidents"""
            limit = request.args.get('limit', 50, type=int)
            return jsonify(self.get_recent_incidents(limit))
        
        @self.app.route('/api/incident/<incident_id>', methods=['POST'])
        @login_required
        def api_update_incident(incident_id):
            """API endpoint to update incident"""
            if current_user.role not in ['admin', 'security_analyst']:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            data = request.get_json()
            success = self.update_incident(incident_id, data, current_user.username)
            
            if success:
                return jsonify({'status': 'success'})
            else:
                return jsonify({'error': 'Failed to update incident'}), 500
        
        @self.app.route('/api/compliance')
        @login_required
        def api_compliance():
            """API endpoint for compliance status"""
            return jsonify(self.get_compliance_status())
        
        @self.app.route('/api/vulnerabilities')
        @login_required
        def api_vulnerabilities():
            """API endpoint for vulnerability summary"""
            days_back = request.args.get('days', 30, type=int)
            if self.vuln_scanner:
                return jsonify(self.vuln_scanner.get_vulnerability_summary(days_back))
            return jsonify({'error': 'Vulnerability scanner not available'})
        
        @self.app.route('/api/audit_events')
        @login_required
        def api_audit_events():
            """API endpoint for recent audit events"""
            limit = request.args.get('limit', 100, type=int)
            if self.audit_logger:
                events = self.audit_logger.search_events(limit=limit)
                return jsonify([asdict(event) for event in events])
            return jsonify([])
        
        # WebSocket events
        @self.socketio.on('connect')
        @login_required
        def handle_connect():
            """Handle client connection"""
            self.connected_clients.add(request.sid)
            join_room('security_dashboard')
            emit('status', {'msg': f'Connected to security dashboard'})
            logger.info(f"Client connected: {request.sid}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            self.connected_clients.discard(request.sid)
            leave_room('security_dashboard')
            logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('request_update')
        @login_required
        def handle_request_update():
            """Handle real-time update request"""
            try:
                metrics = self.get_current_metrics()
                emit('metrics_update', metrics)
                
                incidents = self.get_recent_incidents(limit=5)
                emit('incidents_update', incidents)
                
            except Exception as e:
                logger.error(f"Real-time update failed: {e}")
                emit('error', {'msg': str(e)})
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID for Flask-Login"""
        try:
            conn = sqlite3.connect('security_dashboard.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, role 
                FROM dashboard_users 
                WHERE id = ? AND is_active = 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return User(row[0], row[1], row[2], row[3])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str, mfa_token: str) -> Optional[User]:
        """Authenticate dashboard user"""
        try:
            conn = sqlite3.connect('security_dashboard.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, role, mfa_enabled, mfa_secret
                FROM dashboard_users 
                WHERE username = ? AND is_active = 1
            ''', (username,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            user_id, username, email, password_hash, role, mfa_enabled, mfa_secret = row
            
            # Verify password
            if not check_password_hash(password_hash, password):
                return None
            
            # Verify MFA if enabled
            if mfa_enabled and mfa_secret:
                if not self.auth_manager or not self.auth_manager.verify_mfa_token(mfa_secret, mfa_token):
                    return None
            
            # Update last login
            cursor.execute('''
                UPDATE dashboard_users 
                SET last_login = ? 
                WHERE id = ?
            ''', (datetime.utcnow(), user_id))
            
            conn.commit()
            conn.close()
            
            return User(user_id, username, email, role)
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current security metrics"""
        try:
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'security_score': 85.0,  # Default fallback
                'active_threats': len(self.active_incidents),
                'blocked_ips': 0,
                'failed_logins': 0,
                'successful_logins': 0,
                'api_requests': 0,
                'error_rate': 0.0,
                'vulnerability_count': 0,
                'compliance_score': 90.0,
                'encryption_operations': 0,
                'audit_events': 0
            }
            
            # Get metrics from security monitor
            if self.security_monitor:
                monitor_data = self.security_monitor.get_security_dashboard_data()
                if monitor_data and 'error' not in monitor_data:
                    metrics.update({
                        'security_score': monitor_data.get('security_score', 85.0),
                        'blocked_ips': monitor_data.get('blocked_ips_count', 0),
                        'active_connections': monitor_data.get('active_connections', 0)
                    })
            
            # Get vulnerability metrics
            if self.vuln_scanner:
                vuln_summary = self.vuln_scanner.get_vulnerability_summary(days_back=1)
                if vuln_summary and 'error' not in vuln_summary:
                    metrics['vulnerability_count'] = vuln_summary.get('total_open_vulnerabilities', 0)
            
            # Get encryption metrics
            if self.data_manager:
                encryption_metrics = self.data_manager.get_encryption_metrics()
                if encryption_metrics and 'error' not in encryption_metrics:
                    metrics['encryption_operations'] = encryption_metrics.get('total_encrypted_data_items', 0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get current metrics: {e}")
            return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    
    def get_recent_incidents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent security incidents"""
        try:
            conn = sqlite3.connect('security_dashboard.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM security_incidents 
                ORDER BY first_detected DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            incidents = []
            for row in rows:
                incident = {
                    'incident_id': row[0],
                    'incident_type': row[1],
                    'severity': row[2],
                    'status': row[3],
                    'source_ip': row[4],
                    'target_resource': row[5],
                    'description': row[6],
                    'first_detected': row[7],
                    'last_updated': row[8],
                    'assigned_to': row[9],
                    'mitigation_actions': json.loads(row[10]) if row[10] else [],
                    'evidence': json.loads(row[11]) if row[11] else {},
                    'impact_assessment': row[12],
                    'remediation_status': row[13]
                }
                incidents.append(incident)
            
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get recent incidents: {e}")
            return []
    
    def update_incident(self, incident_id: str, data: Dict[str, Any], username: str) -> bool:
        """Update security incident"""
        try:
            conn = sqlite3.connect('security_dashboard.db')
            cursor = conn.cursor()
            
            # Build update query dynamically
            update_fields = []
            update_values = []
            
            allowed_fields = ['status', 'assigned_to', 'impact_assessment', 'remediation_status']
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    update_values.append(data[field])
            
            if 'mitigation_actions' in data:
                update_fields.append("mitigation_actions = ?")
                update_values.append(json.dumps(data['mitigation_actions']))
            
            if update_fields:
                update_fields.append("last_updated = ?")
                update_values.append(datetime.utcnow())
                update_values.append(incident_id)
                
                query = f"UPDATE security_incidents SET {', '.join(update_fields)} WHERE incident_id = ?"
                cursor.execute(query, update_values)
                
                conn.commit()
            
            conn.close()
            
            # Emit real-time update
            self.socketio.emit('incident_updated', {
                'incident_id': incident_id,
                'updated_by': username,
                'timestamp': datetime.utcnow().isoformat()
            }, room='security_dashboard')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update incident {incident_id}: {e}")
            return False
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """Get compliance framework status"""
        try:
            if not self.compliance_manager:
                return {'error': 'Compliance manager not available'}
            
            # Get recent compliance checks
            from audit_compliance import ComplianceFramework
            
            status = {}
            for framework in ComplianceFramework:
                try:
                    # In a real implementation, you'd get actual compliance scores
                    status[framework.value] = {
                        'score': 85.0,  # Mock score
                        'status': 'COMPLIANT',
                        'last_check': datetime.utcnow().isoformat(),
                        'issues': 2,
                        'resolved': 15
                    }
                except Exception as e:
                    logger.error(f"Failed to get {framework.value} status: {e}")
                    status[framework.value] = {'error': str(e)}
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get compliance status: {e}")
            return {'error': str(e)}
    
    def generate_charts_data(self) -> Dict[str, Any]:
        """Generate data for dashboard charts"""
        try:
            # Security score trend (last 24 hours)
            security_scores = []
            timestamps = []
            
            # Generate mock data - in production this would come from metrics_history
            now = datetime.utcnow()
            for i in range(24):
                timestamps.append((now - timedelta(hours=23-i)).strftime('%H:%M'))
                # Mock data with some variation
                base_score = 85.0
                variation = (i % 5) * 2 - 4  # -4 to +6 variation
                security_scores.append(min(100, max(0, base_score + variation)))
            
            # Threat types distribution
            threat_types = {
                'Malicious IP': 5,
                'Failed Login': 12,
                'Suspicious Pattern': 3,
                'Rate Limit Exceeded': 8,
                'Unauthorized Access': 2
            }
            
            # Vulnerability severity distribution
            vuln_severity = {
                'Critical': 2,
                'High': 8,
                'Medium': 15,
                'Low': 25
            }
            
            charts_data = {
                'security_trend': {
                    'timestamps': timestamps,
                    'scores': security_scores
                },
                'threat_distribution': threat_types,
                'vulnerability_severity': vuln_severity
            }
            
            return charts_data
            
        except Exception as e:
            logger.error(f"Failed to generate charts data: {e}")
            return {}
    
    def start_background_tasks(self):
        """Start background monitoring tasks"""
        try:
            # Start metrics collection thread
            metrics_thread = threading.Thread(target=self._collect_metrics_loop, daemon=True)
            metrics_thread.start()
            
            # Start incident monitoring thread
            incident_thread = threading.Thread(target=self._monitor_incidents_loop, daemon=True)
            incident_thread.start()
            
            # Start real-time update thread
            update_thread = threading.Thread(target=self._real_time_updates_loop, daemon=True)
            update_thread.start()
            
            logger.info("Background tasks started")
            
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
    
    def _collect_metrics_loop(self):
        """Background metrics collection loop"""
        while True:
            try:
                metrics = self.get_current_metrics()
                
                # Store in history
                self.metrics_history.append(metrics)
                
                # Store in database
                self._store_metrics_history(metrics)
                
                time.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                time.sleep(60)
    
    def _monitor_incidents_loop(self):
        """Background incident monitoring loop"""
        while True:
            try:
                # Check for new security alerts from monitors
                if self.security_monitor:
                    dashboard_data = self.security_monitor.get_security_dashboard_data()
                    if dashboard_data and 'recent_alerts' in dashboard_data:
                        for alert_data in dashboard_data['recent_alerts']:
                            self._process_security_alert(alert_data)
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Incident monitoring error: {e}")
                time.sleep(30)
    
    def _real_time_updates_loop(self):
        """Background real-time updates loop"""
        while True:
            try:
                if self.connected_clients:
                    # Send periodic updates to connected clients
                    metrics = self.get_current_metrics()
                    self.socketio.emit('metrics_update', metrics, room='security_dashboard')
                
                time.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Real-time updates error: {e}")
                time.sleep(10)
    
    def _store_metrics_history(self, metrics: Dict[str, Any]):
        """Store metrics in database"""
        try:
            conn = sqlite3.connect('security_dashboard.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO security_metrics_history
                (timestamp, security_score, active_threats, blocked_ips, failed_logins,
                 successful_logins, api_requests, error_rate, vulnerability_count,
                 compliance_score, encryption_operations, audit_events)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.utcnow(),
                metrics.get('security_score', 0),
                metrics.get('active_threats', 0),
                metrics.get('blocked_ips', 0),
                metrics.get('failed_logins', 0),
                metrics.get('successful_logins', 0),
                metrics.get('api_requests', 0),
                metrics.get('error_rate', 0),
                metrics.get('vulnerability_count', 0),
                metrics.get('compliance_score', 0),
                metrics.get('encryption_operations', 0),
                metrics.get('audit_events', 0)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store metrics history: {e}")
    
    def _process_security_alert(self, alert_data: Dict[str, Any]):
        """Process security alert and create incident if necessary"""
        try:
            # Check if this alert should create an incident
            if alert_data.get('severity') in ['HIGH', 'CRITICAL']:
                incident_id = secrets.token_urlsafe(16)
                
                incident = ThreatIncident(
                    incident_id=incident_id,
                    incident_type=alert_data.get('alert_type', 'UNKNOWN'),
                    severity=alert_data.get('severity', 'MEDIUM'),
                    status='OPEN',
                    source_ip=alert_data.get('source_ip', 'unknown'),
                    target_resource=alert_data.get('target_resource', 'unknown'),
                    description=alert_data.get('description', ''),
                    first_detected=datetime.utcnow(),
                    last_updated=datetime.utcnow(),
                    assigned_to=None,
                    mitigation_actions=[],
                    evidence=alert_data,
                    impact_assessment='',
                    remediation_status='PENDING'
                )
                
                # Store incident
                self._store_incident(incident)
                
                # Add to active incidents
                self.active_incidents[incident_id] = incident
                
                # Emit real-time alert
                self.socketio.emit('new_incident', asdict(incident), room='security_dashboard')
                
                logger.warning(f"New security incident created: {incident_id}")
            
        except Exception as e:
            logger.error(f"Failed to process security alert: {e}")
    
    def _store_incident(self, incident: ThreatIncident):
        """Store incident in database"""
        try:
            conn = sqlite3.connect('security_dashboard.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO security_incidents
                (incident_id, incident_type, severity, status, source_ip, target_resource,
                 description, first_detected, last_updated, assigned_to, mitigation_actions,
                 evidence, impact_assessment, remediation_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                incident.incident_id, incident.incident_type, incident.severity,
                incident.status, incident.source_ip, incident.target_resource,
                incident.description, incident.first_detected, incident.last_updated,
                incident.assigned_to, json.dumps(incident.mitigation_actions),
                json.dumps(incident.evidence), incident.impact_assessment,
                incident.remediation_status
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store incident: {e}")
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the security dashboard"""
        logger.info(f"Starting security dashboard on {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)

# HTML Templates
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>OMEGA PRO AI Security Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <style>
        .security-score { font-size: 2rem; font-weight: bold; }
        .critical { color: #dc3545; }
        .high { color: #fd7e14; }
        .medium { color: #ffc107; }
        .low { color: #28a745; }
        .info { color: #17a2b8; }
        .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .threat-card { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        .vuln-card { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
        .compliance-card { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
        .incident-row:hover { background-color: #f8f9fa; }
        .chart-container { position: relative; height: 400px; }
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#"><i class="fas fa-shield-alt"></i> OMEGA Security Dashboard</a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">Welcome, {{ user.username }}</span>
                <a class="nav-link" href="{{ url_for('logout') }}"><i class="fas fa-sign-out-alt"></i> Logout</a>
            </div>
        </div>
    </nav>

    <div class="container-fluid py-4">
        <!-- Status Banner -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="alert alert-info d-flex align-items-center" role="alert">
                    <i class="fas fa-info-circle me-2"></i>
                    <div>
                        <strong>System Status:</strong> Operational | 
                        <strong>Last Updated:</strong> <span id="lastUpdate">{{ metrics.timestamp }}</span> |
                        <span class="status-indicator bg-success me-1"></span> All systems monitoring
                    </div>
                </div>
            </div>
        </div>

        <!-- Metrics Cards -->
        <div class="row mb-4">
            <div class="col-md-3 mb-3">
                <div class="card text-white metric-card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h5 class="card-title">Security Score</h5>
                                <div class="security-score">{{ "%.1f"|format(metrics.security_score) }}%</div>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-shield-alt fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card text-white threat-card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h5 class="card-title">Active Threats</h5>
                                <div class="security-score">{{ metrics.active_threats }}</div>
                                <small>{{ metrics.blocked_ips }} IPs blocked</small>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-exclamation-triangle fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card text-white vuln-card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h5 class="card-title">Vulnerabilities</h5>
                                <div class="security-score">{{ metrics.vulnerability_count }}</div>
                                <small>Open vulnerabilities</small>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-bug fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card text-white compliance-card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h5 class="card-title">Compliance</h5>
                                <div class="security-score">{{ "%.1f"|format(metrics.compliance_score) }}%</div>
                                <small>Overall compliance</small>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-clipboard-check fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts and Incidents -->
        <div class="row">
            <div class="col-lg-8">
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0"><i class="fas fa-chart-line"></i> Security Trends (24h)</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="securityTrendChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="card-title mb-0"><i class="fas fa-exclamation-circle"></i> Recent Security Incidents</h5>
                        <span class="badge bg-danger">{{ incidents|length }}</span>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Type</th>
                                        <th>Severity</th>
                                        <th>Source</th>
                                        <th>Status</th>
                                        <th>Detected</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for incident in incidents %}
                                    <tr class="incident-row">
                                        <td>{{ incident.incident_type }}</td>
                                        <td>
                                            <span class="badge bg-{{ 'danger' if incident.severity == 'CRITICAL' else ('warning' if incident.severity == 'HIGH' else 'info') }}">
                                                {{ incident.severity }}
                                            </span>
                                        </td>
                                        <td>{{ incident.source_ip }}</td>
                                        <td>
                                            <span class="badge bg-{{ 'success' if incident.status == 'RESOLVED' else 'warning' }}">
                                                {{ incident.status }}
                                            </span>
                                        </td>
                                        <td>{{ incident.first_detected }}</td>
                                        <td>
                                            <button class="btn btn-sm btn-outline-primary" onclick="viewIncident('{{ incident.incident_id }}')">
                                                <i class="fas fa-eye"></i>
                                            </button>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                    {% if not incidents %}
                                    <tr>
                                        <td colspan="6" class="text-center text-muted py-4">No recent incidents</td>
                                    </tr>
                                    {% endif %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4">
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0"><i class="fas fa-shield-virus"></i> Threat Distribution</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="threatDistributionChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0"><i class="fas fa-clipboard-check"></i> Compliance Status</h5>
                    </div>
                    <div class="card-body">
                        {% for framework, status in compliance_status.items() %}
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span>{{ framework }}</span>
                            <span class="badge bg-{{ 'success' if status.status == 'COMPLIANT' else 'warning' }}">
                                {{ status.score }}%
                            </span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0"><i class="fas fa-tachometer-alt"></i> System Health</h5>
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-6 mb-3">
                                <div class="border rounded p-3">
                                    <i class="fas fa-lock fa-2x text-success mb-2"></i>
                                    <div><small>Encryption</small></div>
                                    <div><strong>Active</strong></div>
                                </div>
                            </div>
                            <div class="col-6 mb-3">
                                <div class="border rounded p-3">
                                    <i class="fas fa-eye fa-2x text-info mb-2"></i>
                                    <div><small>Monitoring</small></div>
                                    <div><strong>Online</strong></div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="border rounded p-3">
                                    <i class="fas fa-history fa-2x text-primary mb-2"></i>
                                    <div><small>Audit</small></div>
                                    <div><strong>{{ metrics.audit_events }}</strong></div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="border rounded p-3">
                                    <i class="fas fa-users fa-2x text-warning mb-2"></i>
                                    <div><small>Sessions</small></div>
                                    <div><strong>{{ metrics.successful_logins }}</strong></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Initialize Socket.IO
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to security dashboard');
        });
        
        socket.on('metrics_update', function(data) {
            updateMetrics(data);
        });
        
        socket.on('new_incident', function(data) {
            showNewIncidentAlert(data);
        });
        
        // Initialize Charts
        const securityTrendCtx = document.getElementById('securityTrendChart').getContext('2d');
        const securityTrendChart = new Chart(securityTrendCtx, {
            type: 'line',
            data: {
                labels: {{ charts_data.security_trend.timestamps | tojsonfilter }},
                datasets: [{
                    label: 'Security Score',
                    data: {{ charts_data.security_trend.scores | tojsonfilter }},
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        const threatDistCtx = document.getElementById('threatDistributionChart').getContext('2d');
        const threatDistChart = new Chart(threatDistCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys({{ charts_data.threat_distribution | tojsonfilter }}),
                datasets: [{
                    data: Object.values({{ charts_data.threat_distribution | tojsonfilter }}),
                    backgroundColor: ['#dc3545', '#fd7e14', '#ffc107', '#28a745', '#17a2b8']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
        
        function updateMetrics(metrics) {
            // Update metric displays
            document.querySelector('.security-score').textContent = metrics.security_score.toFixed(1) + '%';
            document.getElementById('lastUpdate').textContent = new Date(metrics.timestamp).toLocaleString();
        }
        
        function showNewIncidentAlert(incident) {
            // Show toast notification for new incident
            const toast = `
                <div class="toast" role="alert">
                    <div class="toast-header">
                        <strong class="me-auto text-danger">New Security Incident</strong>
                        <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                    </div>
                    <div class="toast-body">
                        ${incident.incident_type}: ${incident.description}
                    </div>
                </div>
            `;
            // Add toast to page and show (implementation depends on your toast container)
        }
        
        function viewIncident(incidentId) {
            // Open incident details modal
            alert('View incident: ' + incidentId);
        }
        
        // Request periodic updates
        setInterval(() => {
            socket.emit('request_update');
        }, 30000); // Every 30 seconds
    </script>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>OMEGA Security Dashboard - Login</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .login-card { max-width: 400px; margin: 10vh auto; }
        .card { border: none; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
    </style>
</head>
<body class="d-flex align-items-center">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="card login-card">
                    <div class="card-body p-5">
                        <div class="text-center mb-4">
                            <i class="fas fa-shield-alt fa-3x text-primary mb-3"></i>
                            <h3>OMEGA Security</h3>
                            <p class="text-muted">Dashboard Login</p>
                        </div>
                        
                        {% with messages = get_flashed_messages() %}
                        {% if messages %}
                        <div class="alert alert-danger">
                            {{ messages[0] }}
                        </div>
                        {% endif %}
                        {% endwith %}
                        
                        <form method="post">
                            <div class="mb-3">
                                <label for="username" class="form-label">Username</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="fas fa-user"></i></span>
                                    <input type="text" class="form-control" id="username" name="username" required>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="fas fa-lock"></i></span>
                                    <input type="password" class="form-control" id="password" name="password" required>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="mfa_token" class="form-label">MFA Token (if enabled)</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="fas fa-key"></i></span>
                                    <input type="text" class="form-control" id="mfa_token" name="mfa_token" placeholder="6-digit code">
                                </div>
                            </div>
                            
                            <button type="submit" class="btn btn-primary w-100 mb-3">
                                <i class="fas fa-sign-in-alt"></i> Login
                            </button>
                        </form>
                        
                        <div class="text-center">
                            <small class="text-muted">
                                OMEGA PRO AI v10.1 Security Dashboard<br>
                                Secured with enterprise-grade encryption
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

# Main execution
if __name__ == "__main__":
    dashboard = SecurityDashboard()
    dashboard.run(host='0.0.0.0', port=5000, debug=False)