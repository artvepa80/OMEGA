"""
OMEGA PRO AI v10.1 - Comprehensive Security Audit Logger
Complete auditing system for all database and system operations
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import logging.handlers
from pathlib import Path
import threading
import queue
import sqlite3
from contextlib import contextmanager

class AuditEventType(Enum):
    """Types of audit events"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATION = "user_creation"
    USER_MODIFICATION = "user_modification"
    USER_DELETION = "user_deletion"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    DATA_EXPORT = "data_export"
    QUERY_EXECUTION = "query_execution"
    SCHEMA_CHANGE = "schema_change"
    PERMISSION_CHANGE = "permission_change"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_INCIDENT = "security_incident"
    SYSTEM_ERROR = "system_error"
    BACKUP_OPERATION = "backup_operation"
    RESTORE_OPERATION = "restore_operation"

class AuditSeverity(Enum):
    """Severity levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    username: str
    ip_address: str
    user_agent: str
    resource: str
    action: str
    details: Dict[str, Any]
    result: str  # SUCCESS, FAILURE, ERROR
    session_id: Optional[str] = None
    duration_ms: Optional[int] = None
    data_classification: Optional[str] = None
    compliance_tags: List[str] = None
    
    def __post_init__(self):
        if self.compliance_tags is None:
            self.compliance_tags = []

class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(self, config_path: str = None):
        """Initialize audit logger"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.db_path = 'security/audit.db'
        self.event_queue = queue.Queue()
        self._setup_database()
        self._start_async_processor()
        self.tamper_protection = True
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load audit configuration"""
        default_path = 'security/security_config.json'
        path = config_path or default_path
        
        try:
            with open(path, 'r') as f:
                config = json.load(f)
            return config.get('compliance', {}).get('audit_logging', {})
        except Exception as e:
            return self._get_default_audit_config()
    
    def _get_default_audit_config(self) -> Dict[str, Any]:
        """Default audit configuration"""
        return {
            "enabled": True,
            "log_all_access": True,
            "log_schema_changes": True,
            "log_permission_changes": True,
            "tamper_protection": True,
            "retention_days": 2555,
            "real_time_alerts": True
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup secure audit logging"""
        logger = logging.getLogger('AuditLogger')
        logger.setLevel(logging.DEBUG)
        
        # Ensure audit logs directory exists
        os.makedirs('security/audit_logs', exist_ok=True)
        
        # Setup rotating file handler for audit logs
        handler = logging.handlers.RotatingFileHandler(
            'security/audit_logs/security_audit.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=50,  # Keep 50 backup files
            encoding='utf-8'
        )
        
        # Custom formatter with tamper protection
        formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d|%(levelname)s|%(message)s|HASH:%(hash)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add custom filter for tamper protection
        handler.addFilter(self._add_hash_filter)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Setup separate handler for critical events
        critical_handler = logging.FileHandler(
            'security/audit_logs/critical_events.log',
            encoding='utf-8'
        )
        critical_handler.setLevel(logging.CRITICAL)
        critical_handler.setFormatter(formatter)
        logger.addHandler(critical_handler)
        
        return logger
    
    def _add_hash_filter(self, record):
        """Add tamper protection hash to log records"""
        if self.tamper_protection:
            # Create hash of log message for integrity verification
            message_hash = hashlib.sha256(
                f"{record.asctime}{record.levelname}{record.getMessage()}".encode()
            ).hexdigest()[:16]
            record.hash = message_hash
        else:
            record.hash = "DISABLED"
        return True
    
    def _setup_database(self):
        """Setup SQLite database for structured audit logs"""
        os.makedirs('security', exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    username TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT,
                    resource TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    result TEXT NOT NULL,
                    session_id TEXT,
                    duration_ms INTEGER,
                    data_classification TEXT,
                    compliance_tags TEXT,
                    integrity_hash TEXT NOT NULL
                )
            ''')
            
            # Create indexes for efficient querying
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON audit_events(timestamp)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_event_type 
                ON audit_events(event_type)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_username 
                ON audit_events(username)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_severity 
                ON audit_events(severity)
            ''')
            
            conn.commit()
    
    def _start_async_processor(self):
        """Start async event processor thread"""
        def process_events():
            while True:
                try:
                    event = self.event_queue.get(timeout=1)
                    if event is None:  # Shutdown signal
                        break
                    self._write_event_to_db(event)
                    self.event_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    self.logger.error(f"Event processing error: {e}")
        
        processor_thread = threading.Thread(target=process_events, daemon=True)
        processor_thread.start()
    
    def _write_event_to_db(self, event: AuditEvent):
        """Write audit event to database"""
        try:
            # Create integrity hash
            event_data = f"{event.event_id}{event.timestamp}{event.username}{event.action}"
            integrity_hash = hashlib.sha256(event_data.encode()).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO audit_events (
                        event_id, timestamp, event_type, severity, username,
                        ip_address, user_agent, resource, action, details,
                        result, session_id, duration_ms, data_classification,
                        compliance_tags, integrity_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.event_type.value,
                    event.severity.value,
                    event.username,
                    event.ip_address,
                    event.user_agent,
                    event.resource,
                    event.action,
                    json.dumps(event.details),
                    event.result,
                    event.session_id,
                    event.duration_ms,
                    event.data_classification,
                    json.dumps(event.compliance_tags),
                    integrity_hash
                ))
                
        except Exception as e:
            self.logger.error(f"Database write error: {e}")
    
    def log_event(self, event_type: AuditEventType, username: str,
                  action: str, resource: str, result: str = "SUCCESS",
                  details: Dict[str, Any] = None, severity: AuditSeverity = AuditSeverity.MEDIUM,
                  ip_address: str = "unknown", user_agent: str = "unknown",
                  session_id: str = None, duration_ms: int = None,
                  data_classification: str = None, compliance_tags: List[str] = None):
        """Log audit event"""
        
        if not self.config.get('enabled', True):
            return
        
        # Generate unique event ID
        event_id = hashlib.sha256(
            f"{datetime.utcnow().isoformat()}{username}{action}".encode()
        ).hexdigest()[:16]
        
        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            severity=severity,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            details=details or {},
            result=result,
            session_id=session_id,
            duration_ms=duration_ms,
            data_classification=data_classification,
            compliance_tags=compliance_tags or []
        )
        
        # Add to processing queue
        self.event_queue.put(event)
        
        # Log to file immediately for critical events
        log_message = (
            f"EVENT_ID:{event_id}|TYPE:{event_type.value}|USER:{username}|"
            f"ACTION:{action}|RESOURCE:{resource}|RESULT:{result}|"
            f"IP:{ip_address}|DETAILS:{json.dumps(details or {})}"
        )
        
        if severity == AuditSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif severity == AuditSeverity.HIGH:
            self.logger.error(log_message)
        elif severity == AuditSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def log_user_authentication(self, username: str, success: bool,
                              ip_address: str, user_agent: str,
                              details: Dict[str, Any] = None):
        """Log user authentication event"""
        self.log_event(
            event_type=AuditEventType.USER_LOGIN,
            username=username,
            action="authenticate",
            resource="authentication_system",
            result="SUCCESS" if success else "FAILURE",
            details=details,
            severity=AuditSeverity.MEDIUM if success else AuditSeverity.HIGH,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_data_access(self, username: str, resource: str, action: str,
                       details: Dict[str, Any] = None, session_id: str = None,
                       ip_address: str = "unknown", duration_ms: int = None):
        """Log data access event"""
        self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            username=username,
            action=action,
            resource=resource,
            details=details,
            severity=AuditSeverity.LOW,
            session_id=session_id,
            ip_address=ip_address,
            duration_ms=duration_ms,
            data_classification="sensitive"
        )
    
    def log_data_modification(self, username: str, resource: str,
                            before_data: Any = None, after_data: Any = None,
                            session_id: str = None, ip_address: str = "unknown"):
        """Log data modification event"""
        details = {}
        if before_data is not None:
            details['before'] = str(before_data)[:1000]  # Limit size
        if after_data is not None:
            details['after'] = str(after_data)[:1000]  # Limit size
        
        self.log_event(
            event_type=AuditEventType.DATA_MODIFICATION,
            username=username,
            action="modify",
            resource=resource,
            details=details,
            severity=AuditSeverity.MEDIUM,
            session_id=session_id,
            ip_address=ip_address,
            data_classification="sensitive",
            compliance_tags=["data_modification", "gdpr"]
        )
    
    def log_query_execution(self, username: str, query: str, 
                          execution_time_ms: int, result_count: int = None,
                          session_id: str = None, ip_address: str = "unknown"):
        """Log database query execution"""
        # Sanitize query for logging (remove potential sensitive data)
        sanitized_query = self._sanitize_query(query)
        
        details = {
            "query": sanitized_query,
            "execution_time_ms": execution_time_ms,
            "result_count": result_count
        }
        
        # Detect potentially suspicious queries
        severity = AuditSeverity.LOW
        if any(keyword in query.upper() for keyword in ['DROP', 'DELETE', 'TRUNCATE']):
            severity = AuditSeverity.HIGH
        elif execution_time_ms > 5000:  # Slow query
            severity = AuditSeverity.MEDIUM
        
        self.log_event(
            event_type=AuditEventType.QUERY_EXECUTION,
            username=username,
            action="execute_query",
            resource="database",
            details=details,
            severity=severity,
            session_id=session_id,
            ip_address=ip_address,
            duration_ms=execution_time_ms
        )
    
    def log_security_incident(self, incident_type: str, username: str,
                            description: str, details: Dict[str, Any] = None,
                            ip_address: str = "unknown"):
        """Log security incident"""
        incident_details = {
            "incident_type": incident_type,
            "description": description
        }
        if details:
            incident_details.update(details)
        
        self.log_event(
            event_type=AuditEventType.SECURITY_INCIDENT,
            username=username,
            action=incident_type,
            resource="security_system",
            details=incident_details,
            severity=AuditSeverity.CRITICAL,
            ip_address=ip_address,
            compliance_tags=["security_incident", "immediate_review"]
        )
    
    def log_configuration_change(self, username: str, config_section: str,
                               old_value: Any, new_value: Any,
                               session_id: str = None, ip_address: str = "unknown"):
        """Log configuration changes"""
        details = {
            "section": config_section,
            "old_value": str(old_value),
            "new_value": str(new_value)
        }
        
        self.log_event(
            event_type=AuditEventType.CONFIGURATION_CHANGE,
            username=username,
            action="modify_configuration",
            resource=f"config.{config_section}",
            details=details,
            severity=AuditSeverity.HIGH,
            session_id=session_id,
            ip_address=ip_address,
            compliance_tags=["configuration_change", "admin_action"]
        )
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize query for logging (remove sensitive data patterns)"""
        import re
        
        # Remove potential password/token patterns
        sanitized = re.sub(r"'[^']*password[^']*'", "'***PASSWORD***'", query, flags=re.IGNORECASE)
        sanitized = re.sub(r"'[^']*token[^']*'", "'***TOKEN***'", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"'[^']*key[^']*'", "'***KEY***'", sanitized, flags=re.IGNORECASE)
        
        # Limit query length
        if len(sanitized) > 500:
            sanitized = sanitized[:500] + "... [TRUNCATED]"
        
        return sanitized
    
    @contextmanager
    def audit_context(self, username: str, action: str, resource: str,
                     session_id: str = None, ip_address: str = "unknown"):
        """Context manager for auditing operations with timing"""
        start_time = datetime.utcnow()
        try:
            yield
            # Log successful operation
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                username=username,
                action=action,
                resource=resource,
                result="SUCCESS",
                session_id=session_id,
                ip_address=ip_address,
                duration_ms=int(duration)
            )
        except Exception as e:
            # Log failed operation
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.log_event(
                event_type=AuditEventType.SYSTEM_ERROR,
                username=username,
                action=action,
                resource=resource,
                result="ERROR",
                details={"error": str(e)},
                severity=AuditSeverity.HIGH,
                session_id=session_id,
                ip_address=ip_address,
                duration_ms=int(duration)
            )
            raise
    
    def query_audit_events(self, start_date: datetime = None,
                          end_date: datetime = None,
                          username: str = None,
                          event_type: AuditEventType = None,
                          severity: AuditSeverity = None,
                          limit: int = 1000) -> List[Dict[str, Any]]:
        """Query audit events with filters"""
        try:
            query = "SELECT * FROM audit_events WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            if username:
                query += " AND username = ?"
                params.append(username)
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type.value)
            
            if severity:
                query += " AND severity = ?"
                params.append(severity.value)
            
            query += f" ORDER BY timestamp DESC LIMIT {limit}"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Return rows as dictionaries
                cursor = conn.execute(query, params)
                results = []
                
                for row in cursor.fetchall():
                    event_dict = dict(row)
                    # Parse JSON fields
                    if event_dict['details']:
                        event_dict['details'] = json.loads(event_dict['details'])
                    if event_dict['compliance_tags']:
                        event_dict['compliance_tags'] = json.loads(event_dict['compliance_tags'])
                    results.append(event_dict)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Query audit events failed: {e}")
            return []
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime,
                                 report_type: str = "comprehensive") -> Dict[str, Any]:
        """Generate compliance report"""
        try:
            events = self.query_audit_events(start_date=start_date, end_date=end_date)
            
            report = {
                "report_type": report_type,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "summary": {
                    "total_events": len(events),
                    "by_type": {},
                    "by_severity": {},
                    "by_user": {}
                },
                "security_incidents": [],
                "configuration_changes": [],
                "data_access_patterns": {},
                "compliance_violations": []
            }
            
            # Analyze events
            for event in events:
                event_type = event['event_type']
                severity = event['severity']
                username = event['username']
                
                # Count by type
                report["summary"]["by_type"][event_type] = report["summary"]["by_type"].get(event_type, 0) + 1
                
                # Count by severity
                report["summary"]["by_severity"][severity] = report["summary"]["by_severity"].get(severity, 0) + 1
                
                # Count by user
                report["summary"]["by_user"][username] = report["summary"]["by_user"].get(username, 0) + 1
                
                # Collect security incidents
                if event_type == "security_incident":
                    report["security_incidents"].append({
                        "timestamp": event['timestamp'],
                        "username": username,
                        "details": event['details']
                    })
                
                # Collect configuration changes
                if event_type == "configuration_change":
                    report["configuration_changes"].append({
                        "timestamp": event['timestamp'],
                        "username": username,
                        "resource": event['resource'],
                        "details": event['details']
                    })
            
            return report
            
        except Exception as e:
            self.logger.error(f"Compliance report generation failed: {e}")
            return {"error": str(e)}
    
    def verify_log_integrity(self) -> Dict[str, Any]:
        """Verify audit log integrity"""
        verification_result = {
            "status": "VERIFIED",
            "total_events": 0,
            "corrupted_events": 0,
            "details": []
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM audit_events")
                
                for row in cursor.fetchall():
                    verification_result["total_events"] += 1
                    
                    # Verify integrity hash
                    event_data = f"{row[0]}{row[1]}{row[4]}{row[8]}"  # event_id, timestamp, username, action
                    expected_hash = hashlib.sha256(event_data.encode()).hexdigest()
                    
                    if row[15] != expected_hash:  # integrity_hash column
                        verification_result["corrupted_events"] += 1
                        verification_result["details"].append({
                            "event_id": row[0],
                            "timestamp": row[1],
                            "issue": "Integrity hash mismatch"
                        })
                
                if verification_result["corrupted_events"] > 0:
                    verification_result["status"] = "COMPROMISED"
                
        except Exception as e:
            verification_result["status"] = "ERROR"
            verification_result["error"] = str(e)
        
        return verification_result