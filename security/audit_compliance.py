#!/usr/bin/env python3
"""
Audit and Compliance System for OMEGA PRO AI v10.1
Implements comprehensive audit logging, compliance frameworks (GDPR, SOX, HIPAA),
automated compliance reporting, and security audit trails
"""

import os
import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import redis
from enum import Enum
import pandas as pd
import schedule
import threading
import time
from jinja2 import Template
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.application import MimeApplication
import zipfile
import io
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    GDPR = "GDPR"  # General Data Protection Regulation
    SOX = "SOX"    # Sarbanes-Oxley Act
    HIPAA = "HIPAA"  # Health Insurance Portability and Accountability Act
    PCI_DSS = "PCI_DSS"  # Payment Card Industry Data Security Standard
    ISO_27001 = "ISO_27001"  # Information Security Management
    NIST = "NIST"  # NIST Cybersecurity Framework

class AuditEventType(Enum):
    """Types of audit events"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    DATA_EXPORT = "data_export"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_CHECK = "compliance_check"
    POLICY_VIOLATION = "policy_violation"
    SYSTEM_ACCESS = "system_access"
    ADMIN_ACTION = "admin_action"
    API_ACCESS = "api_access"
    FILE_ACCESS = "file_access"
    DATABASE_ACCESS = "database_access"
    ENCRYPTION_OPERATION = "encryption_operation"
    KEY_MANAGEMENT = "key_management"
    BACKUP_OPERATION = "backup_operation"
    RESTORE_OPERATION = "restore_operation"
    INCIDENT_RESPONSE = "incident_response"

class RiskLevel(Enum):
    """Risk levels for audit events"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class AuditEvent:
    """Comprehensive audit event structure"""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: Optional[str]
    user_name: Optional[str]
    user_role: Optional[str]
    session_id: Optional[str]
    ip_address: str
    user_agent: str
    resource_id: Optional[str]
    resource_type: Optional[str]
    resource_name: Optional[str]
    action: str
    outcome: str  # SUCCESS, FAILURE, PARTIAL
    risk_level: RiskLevel
    details: Dict[str, Any]
    before_state: Optional[Dict[str, Any]]
    after_state: Optional[Dict[str, Any]]
    compliance_tags: List[str]  # Which compliance frameworks this relates to
    data_classification: Optional[str]
    retention_period: timedelta
    tamper_proof_hash: str

@dataclass
class ComplianceRule:
    """Compliance rule definition"""
    rule_id: str
    framework: ComplianceFramework
    rule_name: str
    description: str
    requirement: str
    control_objective: str
    test_procedure: str
    frequency: str  # daily, weekly, monthly, quarterly, annually
    automated: bool
    risk_level: RiskLevel
    remediation_actions: List[str]
    responsible_party: str
    evidence_requirements: List[str]
    tags: List[str]

@dataclass
class ComplianceCheck:
    """Compliance check result"""
    check_id: str
    rule_id: str
    timestamp: datetime
    status: str  # PASS, FAIL, WARNING, NOT_APPLICABLE
    score: float  # 0.0 to 1.0
    evidence: Dict[str, Any]
    findings: List[str]
    recommendations: List[str]
    remediation_required: bool
    next_check_due: datetime

@dataclass
class ComplianceReport:
    """Compliance report structure"""
    report_id: str
    framework: ComplianceFramework
    report_type: str  # summary, detailed, executive
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    overall_score: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    critical_findings: List[str]
    recommendations: List[str]
    report_data: Dict[str, Any]
    report_html: str
    report_pdf_path: Optional[str]

class SecureAuditLogger:
    """Tamper-proof audit logging system"""
    
    def __init__(self, db_path: str = "audit_log.db", redis_host: str = 'localhost'):
        """Initialize secure audit logger"""
        
        self.db_path = db_path
        self.init_database()
        
        # Redis for real-time audit streaming
        try:
            self.redis_client = redis.Redis(host=redis_host, decode_responses=True)
            self.redis_client.ping()
            logger.info("Audit Redis connection established")
        except Exception as e:
            logger.error(f"Audit Redis connection failed: {e}")
            self.redis_client = None
        
        # Chain hashing for tamper detection
        self.previous_hash = self._get_last_event_hash()
        
        # Audit settings
        self.default_retention = timedelta(days=2555)  # 7 years default
        self.high_risk_retention = timedelta(days=3652)  # 10 years for high-risk events
        
        logger.info("Secure Audit Logger initialized")
    
    def init_database(self):
        """Initialize audit database with security constraints"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Main audit events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    user_name TEXT,
                    user_role TEXT,
                    session_id TEXT,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT,
                    resource_id TEXT,
                    resource_type TEXT,
                    resource_name TEXT,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    details TEXT,
                    before_state TEXT,
                    after_state TEXT,
                    compliance_tags TEXT,
                    data_classification TEXT,
                    retention_until TIMESTAMP NOT NULL,
                    tamper_proof_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Audit chain integrity table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_chain (
                    chain_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    previous_hash TEXT,
                    current_hash TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES audit_events(event_id)
                )
            ''')
            
            # Compliance rules table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compliance_rules (
                    rule_id TEXT PRIMARY KEY,
                    framework TEXT NOT NULL,
                    rule_name TEXT NOT NULL,
                    description TEXT,
                    requirement TEXT,
                    control_objective TEXT,
                    test_procedure TEXT,
                    frequency TEXT NOT NULL,
                    automated BOOLEAN DEFAULT 0,
                    risk_level TEXT NOT NULL,
                    remediation_actions TEXT,
                    responsible_party TEXT,
                    evidence_requirements TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Compliance check results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compliance_checks (
                    check_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    score REAL NOT NULL,
                    evidence TEXT,
                    findings TEXT,
                    recommendations TEXT,
                    remediation_required BOOLEAN DEFAULT 0,
                    next_check_due TIMESTAMP,
                    FOREIGN KEY (rule_id) REFERENCES compliance_rules(rule_id)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_events(event_type);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_events(resource_id);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_compliance ON audit_events(compliance_tags);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_compliance_rule ON compliance_checks(rule_id);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_compliance_timestamp ON compliance_checks(timestamp);')
            
            conn.commit()
            conn.close()
            
            # Set restrictive permissions
            os.chmod(self.db_path, 0o600)
            
            logger.info("Audit database initialized")
            
        except Exception as e:
            logger.error(f"Audit database initialization failed: {e}")
            raise
    
    def _get_last_event_hash(self) -> str:
        """Get the hash of the last audit event for chain integrity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT current_hash FROM audit_chain
                ORDER BY chain_id DESC LIMIT 1
            ''')
            
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else "genesis_hash"
            
        except Exception as e:
            logger.error(f"Failed to get last event hash: {e}")
            return "genesis_hash"
    
    def _calculate_tamper_proof_hash(self, event: AuditEvent, previous_hash: str) -> str:
        """Calculate tamper-proof hash for audit event"""
        try:
            # Create hash input from critical event data
            hash_input = f"{event.event_id}:{event.timestamp.isoformat()}:" \
                        f"{event.event_type.value}:{event.user_id}:{event.action}:" \
                        f"{event.outcome}:{previous_hash}"
            
            return hashlib.sha256(hash_input.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Hash calculation failed: {e}")
            return hashlib.sha256(f"error:{datetime.utcnow().isoformat()}".encode()).hexdigest()
    
    def log_event(self, event: AuditEvent) -> bool:
        """Log audit event with tamper-proof chaining"""
        try:
            # Calculate tamper-proof hash
            event.tamper_proof_hash = self._calculate_tamper_proof_hash(event, self.previous_hash)
            
            # Determine retention period
            if event.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                retention_until = datetime.utcnow() + self.high_risk_retention
            else:
                retention_until = datetime.utcnow() + self.default_retention
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_events
                (event_id, timestamp, event_type, user_id, user_name, user_role,
                 session_id, ip_address, user_agent, resource_id, resource_type,
                 resource_name, action, outcome, risk_level, details, before_state,
                 after_state, compliance_tags, data_classification, retention_until,
                 tamper_proof_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id, event.timestamp, event.event_type.value,
                event.user_id, event.user_name, event.user_role, event.session_id,
                event.ip_address, event.user_agent, event.resource_id,
                event.resource_type, event.resource_name, event.action,
                event.outcome, event.risk_level.value,
                json.dumps(event.details) if event.details else None,
                json.dumps(event.before_state) if event.before_state else None,
                json.dumps(event.after_state) if event.after_state else None,
                json.dumps(event.compliance_tags) if event.compliance_tags else None,
                event.data_classification, retention_until, event.tamper_proof_hash
            ))
            
            # Update audit chain
            cursor.execute('''
                INSERT INTO audit_chain (event_id, previous_hash, current_hash, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (event.event_id, self.previous_hash, event.tamper_proof_hash, event.timestamp))
            
            conn.commit()
            conn.close()
            
            # Update previous hash for next event
            self.previous_hash = event.tamper_proof_hash
            
            # Stream to Redis for real-time processing
            if self.redis_client:
                try:
                    audit_stream_key = f"audit_stream:{datetime.utcnow().strftime('%Y-%m-%d')}"
                    event_data = {
                        "event_id": event.event_id,
                        "timestamp": event.timestamp.isoformat(),
                        "event_type": event.event_type.value,
                        "user_id": event.user_id or "",
                        "action": event.action,
                        "outcome": event.outcome,
                        "risk_level": event.risk_level.value
                    }
                    self.redis_client.lpush(audit_stream_key, json.dumps(event_data))
                    self.redis_client.expire(audit_stream_key, 86400)  # 24 hours
                except Exception as e:
                    logger.error(f"Audit streaming failed: {e}")
            
            logger.debug(f"Audit event logged: {event.event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")
            return False
    
    def verify_audit_integrity(self, start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Tuple[bool, List[str]]:
        """Verify audit trail integrity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get audit events in chronological order
            query = '''
                SELECT e.event_id, e.timestamp, e.event_type, e.user_id, e.action,
                       e.outcome, e.tamper_proof_hash, c.previous_hash
                FROM audit_events e
                JOIN audit_chain c ON e.event_id = c.event_id
                ORDER BY e.timestamp
            '''
            params = []
            
            if start_date:
                query = query.replace('ORDER BY', 'WHERE e.timestamp >= ? ORDER BY')
                params.append(start_date)
                
            if end_date:
                if start_date:
                    query = query.replace('ORDER BY', 'AND e.timestamp <= ? ORDER BY')
                else:
                    query = query.replace('ORDER BY', 'WHERE e.timestamp <= ? ORDER BY')
                params.append(end_date)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return True, []
            
            integrity_violations = []
            previous_hash = "genesis_hash"
            
            for row in rows:
                event_id, timestamp, event_type, user_id, action, outcome, stored_hash, chain_previous_hash = row
                
                # Verify chain integrity
                if chain_previous_hash != previous_hash:
                    integrity_violations.append(f"Chain integrity violation at event {event_id}")
                
                # Verify hash integrity
                hash_input = f"{event_id}:{timestamp}:{event_type}:{user_id}:{action}:{outcome}:{previous_hash}"
                calculated_hash = hashlib.sha256(hash_input.encode()).hexdigest()
                
                if calculated_hash != stored_hash:
                    integrity_violations.append(f"Hash integrity violation at event {event_id}")
                
                previous_hash = stored_hash
            
            is_valid = len(integrity_violations) == 0
            
            if is_valid:
                logger.info(f"Audit integrity verification passed for {len(rows)} events")
            else:
                logger.error(f"Audit integrity violations found: {len(integrity_violations)}")
            
            return is_valid, integrity_violations
            
        except Exception as e:
            logger.error(f"Audit integrity verification failed: {e}")
            return False, [f"Verification error: {str(e)}"]
    
    def search_events(self, user_id: Optional[str] = None,
                     event_type: Optional[AuditEventType] = None,
                     resource_id: Optional[str] = None,
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     risk_level: Optional[RiskLevel] = None,
                     limit: int = 1000) -> List[AuditEvent]:
        """Search audit events with filters"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM audit_events WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type.value)
            
            if resource_id:
                query += " AND resource_id = ?"
                params.append(resource_id)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            if risk_level:
                query += " AND risk_level = ?"
                params.append(risk_level.value)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                event = AuditEvent(
                    event_id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    event_type=AuditEventType(row[2]),
                    user_id=row[3],
                    user_name=row[4],
                    user_role=row[5],
                    session_id=row[6],
                    ip_address=row[7],
                    user_agent=row[8] or "",
                    resource_id=row[9],
                    resource_type=row[10],
                    resource_name=row[11],
                    action=row[12],
                    outcome=row[13],
                    risk_level=RiskLevel(row[14]),
                    details=json.loads(row[15]) if row[15] else {},
                    before_state=json.loads(row[16]) if row[16] else None,
                    after_state=json.loads(row[17]) if row[17] else None,
                    compliance_tags=json.loads(row[18]) if row[18] else [],
                    data_classification=row[19],
                    retention_period=timedelta(seconds=0),  # Calculated from retention_until
                    tamper_proof_hash=row[21]
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Audit search failed: {e}")
            return []

class ComplianceManager:
    """Comprehensive compliance management system"""
    
    def __init__(self, audit_logger: SecureAuditLogger):
        """Initialize compliance manager"""
        
        self.audit_logger = audit_logger
        self.db_path = audit_logger.db_path
        
        # Initialize compliance rules
        self.init_compliance_rules()
        
        # Compliance settings
        self.report_output_dir = Path("compliance_reports")
        self.report_output_dir.mkdir(exist_ok=True)
        
        # Schedule compliance checks
        self.schedule_compliance_checks()
        
        logger.info("Compliance Manager initialized")
    
    def init_compliance_rules(self):
        """Initialize default compliance rules for different frameworks"""
        try:
            # GDPR Rules
            gdpr_rules = [
                ComplianceRule(
                    rule_id="GDPR_ART_32",
                    framework=ComplianceFramework.GDPR,
                    rule_name="Security of Processing",
                    description="Implement appropriate technical and organizational measures",
                    requirement="Article 32 - Security of processing",
                    control_objective="Ensure security of personal data processing",
                    test_procedure="Verify encryption, access controls, and security monitoring",
                    frequency="monthly",
                    automated=True,
                    risk_level=RiskLevel.HIGH,
                    remediation_actions=["Enable encryption", "Implement access controls", "Deploy monitoring"],
                    responsible_party="Data Protection Officer",
                    evidence_requirements=["Encryption status", "Access control logs", "Security monitoring reports"],
                    tags=["encryption", "access_control", "monitoring"]
                ),
                ComplianceRule(
                    rule_id="GDPR_ART_30",
                    framework=ComplianceFramework.GDPR,
                    rule_name="Records of Processing Activities",
                    description="Maintain records of all processing activities",
                    requirement="Article 30 - Records of processing activities",
                    control_objective="Document all data processing activities",
                    test_procedure="Review audit logs and processing records",
                    frequency="monthly",
                    automated=True,
                    risk_level=RiskLevel.MEDIUM,
                    remediation_actions=["Implement audit logging", "Document processes", "Regular reviews"],
                    responsible_party="Data Protection Officer",
                    evidence_requirements=["Audit logs", "Process documentation", "Regular review reports"],
                    tags=["audit", "documentation", "processing"]
                )
            ]
            
            # SOX Rules
            sox_rules = [
                ComplianceRule(
                    rule_id="SOX_404",
                    framework=ComplianceFramework.SOX,
                    rule_name="Management Assessment of Internal Controls",
                    description="Assess effectiveness of internal controls over financial reporting",
                    requirement="Section 404 - Management assessment",
                    control_objective="Ensure reliable financial reporting",
                    test_procedure="Review access controls and change management for financial systems",
                    frequency="quarterly",
                    automated=False,
                    risk_level=RiskLevel.HIGH,
                    remediation_actions=["Strengthen access controls", "Improve change management", "Regular assessments"],
                    responsible_party="Chief Financial Officer",
                    evidence_requirements=["Access control reports", "Change logs", "Control assessments"],
                    tags=["financial", "access_control", "change_management"]
                )
            ]
            
            # ISO 27001 Rules
            iso_rules = [
                ComplianceRule(
                    rule_id="ISO_A9_1_1",
                    framework=ComplianceFramework.ISO_27001,
                    rule_name="Access Control Policy",
                    description="Establish access control policy and procedures",
                    requirement="A.9.1.1 Access control policy",
                    control_objective="Control access to information and information processing facilities",
                    test_procedure="Review access control policies and implementation",
                    frequency="monthly",
                    automated=True,
                    risk_level=RiskLevel.HIGH,
                    remediation_actions=["Update access policies", "Review permissions", "Implement controls"],
                    responsible_party="Information Security Manager",
                    evidence_requirements=["Access control policy", "Permission reports", "Control evidence"],
                    tags=["access_control", "policy", "permissions"]
                )
            ]
            
            # Store rules in database
            all_rules = gdpr_rules + sox_rules + iso_rules
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for rule in all_rules:
                cursor.execute('''
                    INSERT OR REPLACE INTO compliance_rules
                    (rule_id, framework, rule_name, description, requirement,
                     control_objective, test_procedure, frequency, automated,
                     risk_level, remediation_actions, responsible_party,
                     evidence_requirements, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rule.rule_id, rule.framework.value, rule.rule_name,
                    rule.description, rule.requirement, rule.control_objective,
                    rule.test_procedure, rule.frequency, rule.automated,
                    rule.risk_level.value, json.dumps(rule.remediation_actions),
                    rule.responsible_party, json.dumps(rule.evidence_requirements),
                    json.dumps(rule.tags)
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Initialized {len(all_rules)} compliance rules")
            
        except Exception as e:
            logger.error(f"Compliance rules initialization failed: {e}")
    
    def run_compliance_check(self, rule_id: str) -> ComplianceCheck:
        """Run automated compliance check"""
        try:
            # Get rule details
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM compliance_rules WHERE rule_id = ?', (rule_id,))
            rule_row = cursor.fetchone()
            
            if not rule_row:
                raise ValueError(f"Compliance rule not found: {rule_id}")
            
            rule = ComplianceRule(
                rule_id=rule_row[0],
                framework=ComplianceFramework(rule_row[1]),
                rule_name=rule_row[2],
                description=rule_row[3],
                requirement=rule_row[4],
                control_objective=rule_row[5],
                test_procedure=rule_row[6],
                frequency=rule_row[7],
                automated=bool(rule_row[8]),
                risk_level=RiskLevel(rule_row[9]),
                remediation_actions=json.loads(rule_row[10]) if rule_row[10] else [],
                responsible_party=rule_row[11],
                evidence_requirements=json.loads(rule_row[12]) if rule_row[12] else [],
                tags=json.loads(rule_row[13]) if rule_row[13] else []
            )
            
            # Run specific compliance test
            check_result = self._execute_compliance_test(rule)
            
            # Store check result
            cursor.execute('''
                INSERT OR REPLACE INTO compliance_checks
                (check_id, rule_id, timestamp, status, score, evidence,
                 findings, recommendations, remediation_required, next_check_due)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                check_result.check_id, check_result.rule_id, check_result.timestamp,
                check_result.status, check_result.score, json.dumps(check_result.evidence),
                json.dumps(check_result.findings), json.dumps(check_result.recommendations),
                check_result.remediation_required, check_result.next_check_due
            ))
            
            conn.commit()
            conn.close()
            
            # Log compliance check
            audit_event = AuditEvent(
                event_id=secrets.token_urlsafe(16),
                timestamp=datetime.utcnow(),
                event_type=AuditEventType.COMPLIANCE_CHECK,
                user_id="system",
                user_name="Compliance System",
                user_role="system",
                session_id=None,
                ip_address="127.0.0.1",
                user_agent="Compliance Manager",
                resource_id=rule_id,
                resource_type="compliance_rule",
                resource_name=rule.rule_name,
                action="compliance_check",
                outcome=check_result.status,
                risk_level=RiskLevel.INFO if check_result.status == "PASS" else RiskLevel.HIGH,
                details={
                    "framework": rule.framework.value,
                    "score": check_result.score,
                    "findings_count": len(check_result.findings)
                },
                before_state=None,
                after_state=None,
                compliance_tags=[rule.framework.value],
                data_classification="INTERNAL",
                retention_period=timedelta(days=2555),
                tamper_proof_hash=""
            )
            
            self.audit_logger.log_event(audit_event)
            
            logger.info(f"Compliance check completed: {rule_id} - {check_result.status}")
            return check_result
            
        except Exception as e:
            logger.error(f"Compliance check failed for {rule_id}: {e}")
            
            # Create failed check result
            return ComplianceCheck(
                check_id=secrets.token_urlsafe(16),
                rule_id=rule_id,
                timestamp=datetime.utcnow(),
                status="FAIL",
                score=0.0,
                evidence={"error": str(e)},
                findings=[f"Compliance check failed: {str(e)}"],
                recommendations=["Contact system administrator"],
                remediation_required=True,
                next_check_due=datetime.utcnow() + timedelta(days=1)
            )
    
    def _execute_compliance_test(self, rule: ComplianceRule) -> ComplianceCheck:
        """Execute specific compliance test based on rule"""
        try:
            check_id = secrets.token_urlsafe(16)
            timestamp = datetime.utcnow()
            evidence = {}
            findings = []
            recommendations = []
            score = 0.0
            status = "FAIL"
            
            # GDPR Article 32 - Security of Processing
            if rule.rule_id == "GDPR_ART_32":
                # Check encryption implementation
                encryption_score = self._check_encryption_compliance()
                evidence["encryption_status"] = encryption_score
                
                # Check access controls
                access_control_score = self._check_access_control_compliance()
                evidence["access_control_status"] = access_control_score
                
                # Check security monitoring
                monitoring_score = self._check_security_monitoring_compliance()
                evidence["monitoring_status"] = monitoring_score
                
                # Calculate overall score
                score = (encryption_score + access_control_score + monitoring_score) / 3
                
                if score >= 0.8:
                    status = "PASS"
                elif score >= 0.6:
                    status = "WARNING"
                    findings.append("Security measures partially implemented")
                    recommendations.append("Strengthen security implementations")
                else:
                    status = "FAIL"
                    findings.append("Insufficient security measures")
                    recommendations.extend(rule.remediation_actions)
            
            # GDPR Article 30 - Records of Processing
            elif rule.rule_id == "GDPR_ART_30":
                # Check audit logging
                audit_coverage = self._check_audit_coverage()
                evidence["audit_coverage"] = audit_coverage
                
                # Check documentation
                documentation_score = self._check_process_documentation()
                evidence["documentation_status"] = documentation_score
                
                score = (audit_coverage + documentation_score) / 2
                
                if score >= 0.9:
                    status = "PASS"
                elif score >= 0.7:
                    status = "WARNING"
                    findings.append("Audit coverage or documentation gaps identified")
                    recommendations.append("Improve audit logging and documentation")
                else:
                    status = "FAIL"
                    findings.append("Insufficient audit trails or documentation")
                    recommendations.extend(rule.remediation_actions)
            
            # SOX 404 - Internal Controls
            elif rule.rule_id == "SOX_404":
                # Check financial system access controls
                financial_access_score = self._check_financial_access_controls()
                evidence["financial_access_controls"] = financial_access_score
                
                # Check change management
                change_mgmt_score = self._check_change_management()
                evidence["change_management"] = change_mgmt_score
                
                score = (financial_access_score + change_mgmt_score) / 2
                
                if score >= 0.85:
                    status = "PASS"
                else:
                    status = "FAIL"
                    findings.append("Internal controls deficiencies identified")
                    recommendations.extend(rule.remediation_actions)
            
            # ISO 27001 A.9.1.1 - Access Control Policy
            elif rule.rule_id == "ISO_A9_1_1":
                # Check access control policies
                policy_score = self._check_access_control_policies()
                evidence["access_control_policies"] = policy_score
                
                # Check policy implementation
                implementation_score = self._check_policy_implementation()
                evidence["policy_implementation"] = implementation_score
                
                score = (policy_score + implementation_score) / 2
                
                if score >= 0.8:
                    status = "PASS"
                elif score >= 0.6:
                    status = "WARNING"
                    findings.append("Access control policy gaps identified")
                    recommendations.append("Review and update access control policies")
                else:
                    status = "FAIL"
                    findings.append("Inadequate access control policies")
                    recommendations.extend(rule.remediation_actions)
            
            # Default case
            else:
                score = 0.5  # Neutral score for unknown rules
                status = "NOT_APPLICABLE"
                findings.append("Automated check not implemented for this rule")
                recommendations.append("Implement manual review process")
            
            # Determine next check date
            frequency_days = {
                "daily": 1,
                "weekly": 7,
                "monthly": 30,
                "quarterly": 90,
                "annually": 365
            }
            
            next_check_due = timestamp + timedelta(days=frequency_days.get(rule.frequency, 30))
            
            return ComplianceCheck(
                check_id=check_id,
                rule_id=rule.rule_id,
                timestamp=timestamp,
                status=status,
                score=score,
                evidence=evidence,
                findings=findings,
                recommendations=recommendations,
                remediation_required=(status in ["FAIL", "WARNING"]),
                next_check_due=next_check_due
            )
            
        except Exception as e:
            logger.error(f"Compliance test execution failed: {e}")
            
            return ComplianceCheck(
                check_id=secrets.token_urlsafe(16),
                rule_id=rule.rule_id,
                timestamp=datetime.utcnow(),
                status="FAIL",
                score=0.0,
                evidence={"error": str(e)},
                findings=[f"Test execution failed: {str(e)}"],
                recommendations=["Contact system administrator"],
                remediation_required=True,
                next_check_due=datetime.utcnow() + timedelta(days=1)
            )
    
    # Compliance test helper methods
    def _check_encryption_compliance(self) -> float:
        """Check encryption implementation compliance"""
        try:
            # Check for encryption key usage
            recent_events = self.audit_logger.search_events(
                event_type=AuditEventType.ENCRYPTION_OPERATION,
                start_time=datetime.utcnow() - timedelta(days=30),
                limit=100
            )
            
            if len(recent_events) > 0:
                return 1.0  # Encryption is being used
            else:
                return 0.3  # Limited encryption usage
                
        except Exception as e:
            logger.error(f"Encryption compliance check failed: {e}")
            return 0.0
    
    def _check_access_control_compliance(self) -> float:
        """Check access control implementation compliance"""
        try:
            # Check for authentication and authorization events
            auth_events = self.audit_logger.search_events(
                event_type=AuditEventType.AUTHENTICATION,
                start_time=datetime.utcnow() - timedelta(days=7),
                limit=100
            )
            
            authz_events = self.audit_logger.search_events(
                event_type=AuditEventType.AUTHORIZATION,
                start_time=datetime.utcnow() - timedelta(days=7),
                limit=100
            )
            
            if len(auth_events) > 0 and len(authz_events) > 0:
                return 0.9  # Good access control activity
            elif len(auth_events) > 0:
                return 0.6  # Some access control
            else:
                return 0.2  # Limited access control
                
        except Exception as e:
            logger.error(f"Access control compliance check failed: {e}")
            return 0.0
    
    def _check_security_monitoring_compliance(self) -> float:
        """Check security monitoring implementation compliance"""
        try:
            # Check for security events in recent period
            security_events = self.audit_logger.search_events(
                event_type=AuditEventType.SECURITY_EVENT,
                start_time=datetime.utcnow() - timedelta(days=7),
                limit=100
            )
            
            # Check for various event types indicating monitoring
            event_types = [
                AuditEventType.SYSTEM_ACCESS,
                AuditEventType.API_ACCESS,
                AuditEventType.DATA_ACCESS,
                AuditEventType.ADMIN_ACTION
            ]
            
            total_monitoring_events = 0
            for event_type in event_types:
                events = self.audit_logger.search_events(
                    event_type=event_type,
                    start_time=datetime.utcnow() - timedelta(days=7),
                    limit=50
                )
                total_monitoring_events += len(events)
            
            if total_monitoring_events > 100:
                return 1.0  # Extensive monitoring
            elif total_monitoring_events > 50:
                return 0.8  # Good monitoring
            elif total_monitoring_events > 10:
                return 0.5  # Basic monitoring
            else:
                return 0.1  # Limited monitoring
                
        except Exception as e:
            logger.error(f"Security monitoring compliance check failed: {e}")
            return 0.0
    
    def _check_audit_coverage(self) -> float:
        """Check audit logging coverage"""
        try:
            # Check for audit events across different categories
            event_types = [
                AuditEventType.AUTHENTICATION,
                AuditEventType.DATA_ACCESS,
                AuditEventType.CONFIGURATION_CHANGE,
                AuditEventType.ADMIN_ACTION
            ]
            
            coverage_score = 0.0
            for event_type in event_types:
                events = self.audit_logger.search_events(
                    event_type=event_type,
                    start_time=datetime.utcnow() - timedelta(days=30),
                    limit=10
                )
                if len(events) > 0:
                    coverage_score += 0.25
            
            return coverage_score
            
        except Exception as e:
            logger.error(f"Audit coverage check failed: {e}")
            return 0.0
    
    def _check_process_documentation(self) -> float:
        """Check process documentation compliance"""
        try:
            # In a real implementation, this would check for:
            # - Data processing registers
            # - Privacy policies
            # - Procedure documents
            # - Training records
            
            # For now, return a baseline score
            return 0.7
            
        except Exception as e:
            logger.error(f"Process documentation check failed: {e}")
            return 0.0
    
    def _check_financial_access_controls(self) -> float:
        """Check financial system access controls"""
        try:
            # Check for financial system access events
            financial_events = self.audit_logger.search_events(
                start_time=datetime.utcnow() - timedelta(days=30),
                limit=100
            )
            
            # Look for events with financial tags or resources
            financial_access_events = [
                e for e in financial_events
                if any(tag in str(e.details).lower() for tag in ["financial", "accounting", "billing", "payment"])
            ]
            
            if len(financial_access_events) > 0:
                # Check for proper authorization
                authorized_events = [
                    e for e in financial_access_events
                    if e.outcome == "SUCCESS" and e.user_role in ["admin", "financial_admin", "accountant"]
                ]
                
                if len(authorized_events) == len(financial_access_events):
                    return 1.0  # All financial access properly authorized
                else:
                    return 0.5  # Some unauthorized access detected
            else:
                return 0.8  # No financial access events (could be good or concerning)
                
        except Exception as e:
            logger.error(f"Financial access controls check failed: {e}")
            return 0.0
    
    def _check_change_management(self) -> float:
        """Check change management compliance"""
        try:
            # Check for configuration change events
            config_events = self.audit_logger.search_events(
                event_type=AuditEventType.CONFIGURATION_CHANGE,
                start_time=datetime.utcnow() - timedelta(days=30),
                limit=100
            )
            
            if len(config_events) > 0:
                # Check if changes were properly authorized
                authorized_changes = [
                    e for e in config_events
                    if e.user_role in ["admin", "system_admin"] and e.outcome == "SUCCESS"
                ]
                
                change_authorization_rate = len(authorized_changes) / len(config_events)
                return change_authorization_rate
            else:
                return 0.9  # No changes (stable system)
                
        except Exception as e:
            logger.error(f"Change management check failed: {e}")
            return 0.0
    
    def _check_access_control_policies(self) -> float:
        """Check access control policy compliance"""
        try:
            # Check for recent access control events
            access_events = self.audit_logger.search_events(
                event_type=AuditEventType.AUTHORIZATION,
                start_time=datetime.utcnow() - timedelta(days=7),
                limit=100
            )
            
            if len(access_events) > 0:
                successful_events = [e for e in access_events if e.outcome == "SUCCESS"]
                failed_events = [e for e in access_events if e.outcome == "FAILURE"]
                
                # Good ratio of successful to failed indicates proper controls
                if len(failed_events) > 0:
                    success_rate = len(successful_events) / len(access_events)
                    if 0.7 <= success_rate <= 0.95:  # Some failures are expected (security working)
                        return 0.9
                    elif success_rate > 0.95:
                        return 0.7  # Too few failures might indicate weak controls
                    else:
                        return 0.3  # Too many failures
                else:
                    return 0.8  # All successful (could be good or concerning)
            else:
                return 0.5  # No access control events
                
        except Exception as e:
            logger.error(f"Access control policies check failed: {e}")
            return 0.0
    
    def _check_policy_implementation(self) -> float:
        """Check policy implementation compliance"""
        try:
            # Check for evidence of policy enforcement
            policy_events = self.audit_logger.search_events(
                start_time=datetime.utcnow() - timedelta(days=30),
                limit=200
            )
            
            # Look for events indicating policy enforcement
            enforcement_indicators = [
                "access_denied",
                "permission_denied",
                "policy_violation",
                "unauthorized",
                "blocked"
            ]
            
            enforcement_events = []
            for event in policy_events:
                event_text = f"{event.action} {event.details}".lower()
                if any(indicator in event_text for indicator in enforcement_indicators):
                    enforcement_events.append(event)
            
            if len(enforcement_events) > 0:
                return 0.8  # Policy enforcement active
            else:
                return 0.4  # Limited evidence of policy enforcement
                
        except Exception as e:
            logger.error(f"Policy implementation check failed: {e}")
            return 0.0
    
    def generate_compliance_report(self, framework: ComplianceFramework,
                                 report_type: str = "summary",
                                 period_days: int = 30) -> ComplianceReport:
        """Generate comprehensive compliance report"""
        try:
            report_id = secrets.token_urlsafe(16)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=period_days)
            
            # Get all compliance checks for framework
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT c.*, r.rule_name, r.requirement, r.risk_level
                FROM compliance_checks c
                JOIN compliance_rules r ON c.rule_id = r.rule_id
                WHERE r.framework = ? AND c.timestamp >= ? AND c.timestamp <= ?
                ORDER BY c.timestamp DESC
            ''', (framework.value, start_time, end_time))
            
            check_rows = cursor.fetchall()
            conn.close()
            
            # Calculate overall metrics
            total_checks = len(check_rows)
            passed_checks = len([r for r in check_rows if r[3] == "PASS"])
            failed_checks = len([r for r in check_rows if r[3] == "FAIL"])
            warning_checks = len([r for r in check_rows if r[3] == "WARNING"])
            
            overall_score = 0.0
            if total_checks > 0:
                total_score = sum([r[4] for r in check_rows])  # r[4] is score
                overall_score = total_score / total_checks
            
            # Collect critical findings
            critical_findings = []
            recommendations = []
            
            for row in check_rows:
                if row[3] == "FAIL" and row[13] == "HIGH":  # status = FAIL and risk_level = HIGH
                    findings = json.loads(row[7]) if row[7] else []
                    critical_findings.extend(findings)
                    
                    recs = json.loads(row[8]) if row[8] else []
                    recommendations.extend(recs)
            
            # Remove duplicates
            critical_findings = list(set(critical_findings))
            recommendations = list(set(recommendations))
            
            # Generate report data
            report_data = {
                "framework": framework.value,
                "period": f"{start_time.date()} to {end_time.date()}",
                "summary": {
                    "total_checks": total_checks,
                    "passed": passed_checks,
                    "failed": failed_checks,
                    "warnings": warning_checks,
                    "overall_score": round(overall_score, 2),
                    "compliance_percentage": round((passed_checks / max(total_checks, 1)) * 100, 1)
                },
                "checks": []
            }
            
            # Add detailed check information
            for row in check_rows:
                check_data = {
                    "check_id": row[0],
                    "rule_id": row[1],
                    "rule_name": row[11],
                    "requirement": row[12],
                    "timestamp": row[2],
                    "status": row[3],
                    "score": row[4],
                    "risk_level": row[13],
                    "findings": json.loads(row[7]) if row[7] else [],
                    "recommendations": json.loads(row[8]) if row[8] else []
                }
                report_data["checks"].append(check_data)
            
            # Generate HTML report
            report_html = self._generate_html_report(framework, report_data, report_type)
            
            # Create compliance report object
            compliance_report = ComplianceReport(
                report_id=report_id,
                framework=framework,
                report_type=report_type,
                period_start=start_time,
                period_end=end_time,
                generated_at=datetime.utcnow(),
                overall_score=overall_score,
                total_checks=total_checks,
                passed_checks=passed_checks,
                failed_checks=failed_checks,
                warning_checks=warning_checks,
                critical_findings=critical_findings,
                recommendations=recommendations,
                report_data=report_data,
                report_html=report_html,
                report_pdf_path=None
            )
            
            # Save report to file
            report_filename = f"compliance_report_{framework.value}_{report_id}.html"
            report_path = self.report_output_dir / report_filename
            
            with open(report_path, 'w') as f:
                f.write(report_html)
            
            logger.info(f"Compliance report generated: {report_filename}")
            return compliance_report
            
        except Exception as e:
            logger.error(f"Compliance report generation failed: {e}")
            raise
    
    def _generate_html_report(self, framework: ComplianceFramework,
                            report_data: Dict[str, Any], report_type: str) -> str:
        """Generate HTML compliance report"""
        try:
            template_str = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ framework }} Compliance Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .summary { background: #e8f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .critical { background: #ffe6e6; padding: 10px; border-left: 4px solid #ff0000; margin: 10px 0; }
        .warning { background: #fff3cd; padding: 10px; border-left: 4px solid #ffa500; margin: 10px 0; }
        .pass { background: #d4edda; padding: 10px; border-left: 4px solid #28a745; margin: 10px 0; }
        .metric { display: inline-block; margin: 10px; padding: 15px; background: white; border: 1px solid #ddd; border-radius: 5px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .score-high { color: #28a745; font-weight: bold; }
        .score-medium { color: #ffa500; font-weight: bold; }
        .score-low { color: #dc3545; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ framework }} Compliance Report</h1>
        <p><strong>Report Period:</strong> {{ report_data.period }}</p>
        <p><strong>Generated:</strong> {{ generated_at }}</p>
        <p><strong>Report Type:</strong> {{ report_type|title }}</p>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <div class="metric">
            <h3>{{ report_data.summary.compliance_percentage }}%</h3>
            <p>Overall Compliance</p>
        </div>
        <div class="metric">
            <h3>{{ report_data.summary.total_checks }}</h3>
            <p>Total Checks</p>
        </div>
        <div class="metric">
            <h3 class="score-high">{{ report_data.summary.passed }}</h3>
            <p>Passed</p>
        </div>
        <div class="metric">
            <h3 class="score-medium">{{ report_data.summary.warnings }}</h3>
            <p>Warnings</p>
        </div>
        <div class="metric">
            <h3 class="score-low">{{ report_data.summary.failed }}</h3>
            <p>Failed</p>
        </div>
    </div>
    
    {% if critical_findings %}
    <div class="critical">
        <h3>Critical Findings</h3>
        <ul>
        {% for finding in critical_findings %}
            <li>{{ finding }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    {% if recommendations %}
    <div class="warning">
        <h3>Recommendations</h3>
        <ul>
        {% for rec in recommendations %}
            <li>{{ rec }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    <h2>Detailed Compliance Checks</h2>
    <table>
        <thead>
            <tr>
                <th>Rule</th>
                <th>Status</th>
                <th>Score</th>
                <th>Risk Level</th>
                <th>Last Checked</th>
                <th>Findings</th>
            </tr>
        </thead>
        <tbody>
        {% for check in report_data.checks %}
            <tr class="{% if check.status == 'PASS' %}pass{% elif check.status == 'FAIL' %}critical{% else %}warning{% endif %}">
                <td>
                    <strong>{{ check.rule_name }}</strong><br>
                    <small>{{ check.requirement }}</small>
                </td>
                <td>{{ check.status }}</td>
                <td>
                    <span class="{% if check.score >= 0.8 %}score-high{% elif check.score >= 0.6 %}score-medium{% else %}score-low{% endif %}">
                        {{ "%.1f"|format(check.score * 100) }}%
                    </span>
                </td>
                <td>{{ check.risk_level }}</td>
                <td>{{ check.timestamp }}</td>
                <td>
                    {% if check.findings %}
                        <ul>
                        {% for finding in check.findings %}
                            <li>{{ finding }}</li>
                        {% endfor %}
                        </ul>
                    {% else %}
                        No issues found
                    {% endif %}
                </td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
    
    <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 5px;">
        <p><small>This report was automatically generated by the OMEGA PRO AI Compliance Management System.</small></p>
        <p><small>Report ID: {{ report_id }}</small></p>
    </div>
</body>
</html>
'''
            
            template = Template(template_str)
            return template.render(
                framework=framework.value,
                report_data=report_data,
                report_type=report_type,
                generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                critical_findings=report_data.get("critical_findings", []),
                recommendations=report_data.get("recommendations", []),
                report_id=secrets.token_urlsafe(8)
            )
            
        except Exception as e:
            logger.error(f"HTML report generation failed: {e}")
            return f"<html><body><h1>Report Generation Error</h1><p>{str(e)}</p></body></html>"
    
    def schedule_compliance_checks(self):
        """Schedule automated compliance checks"""
        try:
            # Schedule daily checks
            schedule.every().day.at("02:00").do(self._run_daily_compliance_checks)
            
            # Schedule weekly checks
            schedule.every().monday.at("03:00").do(self._run_weekly_compliance_checks)
            
            # Schedule monthly checks
            schedule.every().month.do(self._run_monthly_compliance_checks)
            
            # Start scheduler thread
            scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            scheduler_thread.start()
            
            logger.info("Compliance check scheduling initialized")
            
        except Exception as e:
            logger.error(f"Compliance scheduling failed: {e}")
    
    def _run_scheduler(self):
        """Run the compliance check scheduler"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _run_daily_compliance_checks(self):
        """Run daily compliance checks"""
        try:
            # Get rules with daily frequency
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT rule_id FROM compliance_rules WHERE frequency = ? AND automated = 1', ('daily',))
            rule_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            for rule_id in rule_ids:
                try:
                    self.run_compliance_check(rule_id)
                except Exception as e:
                    logger.error(f"Daily compliance check failed for {rule_id}: {e}")
            
            logger.info(f"Completed daily compliance checks for {len(rule_ids)} rules")
            
        except Exception as e:
            logger.error(f"Daily compliance checks failed: {e}")
    
    def _run_weekly_compliance_checks(self):
        """Run weekly compliance checks"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT rule_id FROM compliance_rules WHERE frequency = ? AND automated = 1', ('weekly',))
            rule_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            for rule_id in rule_ids:
                try:
                    self.run_compliance_check(rule_id)
                except Exception as e:
                    logger.error(f"Weekly compliance check failed for {rule_id}: {e}")
            
            logger.info(f"Completed weekly compliance checks for {len(rule_ids)} rules")
            
        except Exception as e:
            logger.error(f"Weekly compliance checks failed: {e}")
    
    def _run_monthly_compliance_checks(self):
        """Run monthly compliance checks and generate reports"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT rule_id FROM compliance_rules WHERE frequency = ? AND automated = 1', ('monthly',))
            rule_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            for rule_id in rule_ids:
                try:
                    self.run_compliance_check(rule_id)
                except Exception as e:
                    logger.error(f"Monthly compliance check failed for {rule_id}: {e}")
            
            # Generate monthly reports for all frameworks
            for framework in ComplianceFramework:
                try:
                    report = self.generate_compliance_report(framework, "summary", 30)
                    logger.info(f"Generated monthly compliance report for {framework.value}")
                except Exception as e:
                    logger.error(f"Monthly report generation failed for {framework.value}: {e}")
            
            logger.info(f"Completed monthly compliance checks for {len(rule_ids)} rules")
            
        except Exception as e:
            logger.error(f"Monthly compliance checks failed: {e}")

# Convenience functions for creating audit events
def create_auth_event(user_id: str, action: str, outcome: str, 
                     ip_address: str, session_id: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None) -> AuditEvent:
    """Create authentication audit event"""
    return AuditEvent(
        event_id=secrets.token_urlsafe(16),
        timestamp=datetime.utcnow(),
        event_type=AuditEventType.AUTHENTICATION,
        user_id=user_id,
        user_name=None,
        user_role=None,
        session_id=session_id,
        ip_address=ip_address,
        user_agent="",
        resource_id=None,
        resource_type="authentication_system",
        resource_name="Authentication Service",
        action=action,
        outcome=outcome,
        risk_level=RiskLevel.MEDIUM if outcome == "SUCCESS" else RiskLevel.HIGH,
        details=details or {},
        before_state=None,
        after_state=None,
        compliance_tags=["GDPR", "SOX"],
        data_classification="CONFIDENTIAL",
        retention_period=timedelta(days=2555),
        tamper_proof_hash=""
    )

def create_data_access_event(user_id: str, resource_id: str, action: str,
                           outcome: str, ip_address: str,
                           data_classification: str = "INTERNAL",
                           details: Optional[Dict[str, Any]] = None) -> AuditEvent:
    """Create data access audit event"""
    return AuditEvent(
        event_id=secrets.token_urlsafe(16),
        timestamp=datetime.utcnow(),
        event_type=AuditEventType.DATA_ACCESS,
        user_id=user_id,
        user_name=None,
        user_role=None,
        session_id=None,
        ip_address=ip_address,
        user_agent="",
        resource_id=resource_id,
        resource_type="data",
        resource_name=f"Data Resource {resource_id}",
        action=action,
        outcome=outcome,
        risk_level=RiskLevel.HIGH if data_classification in ["CONFIDENTIAL", "RESTRICTED"] else RiskLevel.MEDIUM,
        details=details or {},
        before_state=None,
        after_state=None,
        compliance_tags=["GDPR", "HIPAA"] if data_classification == "RESTRICTED" else ["GDPR"],
        data_classification=data_classification,
        retention_period=timedelta(days=2555),
        tamper_proof_hash=""
    )

# Example usage and testing
if __name__ == "__main__":
    # Initialize audit and compliance system
    audit_logger = SecureAuditLogger()
    compliance_manager = ComplianceManager(audit_logger)
    
    # Test audit logging
    auth_event = create_auth_event("user123", "login", "SUCCESS", "192.168.1.100")
    audit_logger.log_event(auth_event)
    
    data_event = create_data_access_event("user123", "data_001", "read", "SUCCESS", "192.168.1.100")
    audit_logger.log_event(data_event)
    
    print("Audit events logged successfully")
    
    # Test compliance checks
    check_result = compliance_manager.run_compliance_check("GDPR_ART_32")
    print(f"Compliance check result: {check_result.status} (Score: {check_result.score})")
    
    # Generate compliance report
    report = compliance_manager.generate_compliance_report(ComplianceFramework.GDPR)
    print(f"Generated compliance report with {report.total_checks} checks")
    
    # Verify audit integrity
    is_valid, violations = audit_logger.verify_audit_integrity()
    print(f"Audit integrity check: {'PASSED' if is_valid else 'FAILED'}")
    if violations:
        print(f"Violations: {violations}")