"""
OMEGA PRO AI v10.1 - Secure Database Manager
Connection pooling, query monitoring, and database security management
"""

import os
import json
import time
import sqlite3
import threading
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
from contextlib import contextmanager
from dataclasses import dataclass
import logging
import hashlib
import re
from queue import Queue, Empty
import pandas as pd
from pathlib import Path

@dataclass
class QueryInfo:
    """Query execution information"""
    query_id: str
    sql: str
    username: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    rows_affected: Optional[int] = None
    result_count: Optional[int] = None
    status: str = "EXECUTING"
    error_message: Optional[str] = None
    ip_address: str = "unknown"
    session_id: Optional[str] = None

@dataclass
class ConnectionInfo:
    """Database connection information"""
    connection_id: str
    username: str
    created_at: datetime
    last_used: datetime
    query_count: int = 0
    is_active: bool = True
    ip_address: str = "unknown"
    session_id: Optional[str] = None

class SecureDatabaseManager:
    """Secure database connection and query management"""
    
    def __init__(self, config_path: str = None):
        """Initialize secure database manager"""
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        self.connection_pool = {}
        self.active_queries = {}
        self.query_history = []
        self.suspicious_patterns = self._load_suspicious_patterns()
        self.monitoring_db_path = 'security/query_monitoring.db'
        self._setup_monitoring_database()
        self._start_monitoring_thread()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup database security logging"""
        logger = logging.getLogger('SecureDatabaseManager')
        logger.setLevel(logging.INFO)
        
        os.makedirs('security/logs', exist_ok=True)
        handler = logging.FileHandler(
            'security/logs/database_security.log',
            mode='a'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load database security configuration"""
        default_path = 'security/security_config.json'
        path = config_path or default_path
        
        try:
            with open(path, 'r') as f:
                config = json.load(f)
            return config.get('monitoring', {})
        except Exception as e:
            self.logger.error(f"Failed to load database config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default database security configuration"""
        return {
            "connection_pool": {
                "max_connections": 10,
                "max_idle_time_seconds": 300,
                "max_lifetime_seconds": 3600
            },
            "query_monitoring": {
                "enabled": True,
                "slow_query_threshold_ms": 1000,
                "log_all_queries": True,
                "detect_injection_attempts": True
            },
            "resource_limits": {
                "max_query_duration_ms": 30000,
                "max_result_rows": 10000,
                "max_concurrent_queries_per_user": 3
            }
        }
    
    def _load_suspicious_patterns(self) -> List[str]:
        """Load SQL injection and suspicious query patterns"""
        return [
            r"(?i)(union\s+select)",
            r"(?i)(drop\s+table)",
            r"(?i)(delete\s+from.*where\s+1=1)",
            r"(?i)(insert\s+into.*values.*\(\s*select)",
            r"(?i)(or\s+1=1)",
            r"(?i)(and\s+1=1)",
            r"(?i)(';\s*drop)",
            r"(?i)(exec\s*\()",
            r"(?i)(script\s*>)",
            r"(?i)(javascript:)",
            r"(?i)(vbscript:)",
            r"(?i)(onload\s*=)",
            r"(?i)(onerror\s*=)",
            r"(?i)(eval\s*\()",
            r"(?i)(expression\s*\()",
            r"(?i)(url\s*\(.*javascript)",
            r"(?i)(import\s+.*system)",
            r"(?i)(__import__)",
            r"(?i)(os\.system)",
            r"(?i)(subprocess)",
            r"(?i)(exec\s+open)"
        ]
    
    def _setup_monitoring_database(self):
        """Setup query monitoring database"""
        os.makedirs('security', exist_ok=True)
        
        with sqlite3.connect(self.monitoring_db_path) as conn:
            # Query execution history
            conn.execute('''
                CREATE TABLE IF NOT EXISTS query_history (
                    query_id TEXT PRIMARY KEY,
                    sql_hash TEXT NOT NULL,
                    sanitized_sql TEXT NOT NULL,
                    username TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    duration_ms INTEGER,
                    rows_affected INTEGER,
                    result_count INTEGER,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    ip_address TEXT,
                    session_id TEXT,
                    suspicious_score INTEGER DEFAULT 0,
                    blocked BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Connection pool monitoring
            conn.execute('''
                CREATE TABLE IF NOT EXISTS connection_history (
                    connection_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    query_count INTEGER DEFAULT 0,
                    ip_address TEXT,
                    session_id TEXT,
                    max_concurrent_queries INTEGER DEFAULT 0
                )
            ''')
            
            # Security events
            conn.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    username TEXT NOT NULL,
                    description TEXT NOT NULL,
                    query_id TEXT,
                    connection_id TEXT,
                    ip_address TEXT,
                    severity TEXT NOT NULL,
                    action_taken TEXT
                )
            ''')
            
            # Create indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_query_username ON query_history(username)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_query_time ON query_history(start_time)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_suspicious ON query_history(suspicious_score)')
            
            conn.commit()
    
    def _start_monitoring_thread(self):
        """Start background monitoring thread"""
        def monitor_connections():
            while True:
                try:
                    self._cleanup_idle_connections()
                    self._detect_anomalies()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    self.logger.error(f"Monitoring thread error: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor_connections, daemon=True)
        monitor_thread.start()
        self.logger.info("Database monitoring thread started")
    
    @contextmanager
    def get_secure_connection(self, username: str, ip_address: str = "unknown",
                            session_id: str = None):
        """Get secure database connection from pool"""
        connection_id = self._create_connection(username, ip_address, session_id)
        
        try:
            # For file-based operations, we'll use a simple connection wrapper
            connection = SecureConnection(
                connection_id=connection_id,
                username=username,
                manager=self,
                ip_address=ip_address,
                session_id=session_id
            )
            
            yield connection
            
        finally:
            self._release_connection(connection_id)
    
    def _create_connection(self, username: str, ip_address: str, session_id: str) -> str:
        """Create new database connection"""
        connection_id = hashlib.sha256(
            f"{username}_{datetime.utcnow().isoformat()}_{ip_address}".encode()
        ).hexdigest()[:16]
        
        # Check connection limits
        user_connections = sum(
            1 for conn in self.connection_pool.values()
            if conn.username == username and conn.is_active
        )
        
        max_connections = self.config.get('connection_pool', {}).get('max_connections', 10)
        if user_connections >= max_connections:
            raise Exception(f"Maximum connections ({max_connections}) exceeded for user {username}")
        
        # Create connection info
        connection_info = ConnectionInfo(
            connection_id=connection_id,
            username=username,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
            ip_address=ip_address,
            session_id=session_id
        )
        
        self.connection_pool[connection_id] = connection_info
        
        # Log connection creation
        self._log_security_event(
            event_type="CONNECTION_CREATED",
            username=username,
            description=f"Database connection created",
            connection_id=connection_id,
            ip_address=ip_address,
            severity="LOW"
        )
        
        self.logger.info(f"Database connection created: {connection_id} for {username}")
        return connection_id
    
    def _release_connection(self, connection_id: str):
        """Release connection back to pool"""
        if connection_id in self.connection_pool:
            connection_info = self.connection_pool[connection_id]
            connection_info.is_active = False
            
            # Record connection closure
            with sqlite3.connect(self.monitoring_db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO connection_history (
                        connection_id, username, created_at, closed_at,
                        query_count, ip_address, session_id, max_concurrent_queries
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    connection_id,
                    connection_info.username,
                    connection_info.created_at.isoformat(),
                    datetime.utcnow().isoformat(),
                    connection_info.query_count,
                    connection_info.ip_address,
                    connection_info.session_id,
                    0  # TODO: Track max concurrent queries
                ))
            
            self.logger.debug(f"Database connection released: {connection_id}")
    
    def _cleanup_idle_connections(self):
        """Clean up idle and expired connections"""
        current_time = datetime.utcnow()
        max_idle_time = self.config.get('connection_pool', {}).get('max_idle_time_seconds', 300)
        max_lifetime = self.config.get('connection_pool', {}).get('max_lifetime_seconds', 3600)
        
        connections_to_remove = []
        
        for conn_id, conn_info in self.connection_pool.items():
            # Check idle time
            idle_seconds = (current_time - conn_info.last_used).total_seconds()
            lifetime_seconds = (current_time - conn_info.created_at).total_seconds()
            
            if idle_seconds > max_idle_time or lifetime_seconds > max_lifetime:
                connections_to_remove.append(conn_id)
        
        # Remove expired connections
        for conn_id in connections_to_remove:
            if conn_id in self.connection_pool:
                self._release_connection(conn_id)
                del self.connection_pool[conn_id]
        
        if connections_to_remove:
            self.logger.info(f"Cleaned up {len(connections_to_remove)} idle connections")
    
    def execute_secure_query(self, connection_id: str, sql: str, 
                           parameters: Tuple = None) -> Tuple[bool, Any, str]:
        """Execute query with security monitoring"""
        start_time = datetime.utcnow()
        query_id = hashlib.sha256(
            f"{sql}_{start_time.isoformat()}_{connection_id}".encode()
        ).hexdigest()[:16]
        
        connection_info = self.connection_pool.get(connection_id)
        if not connection_info:
            return False, None, "Invalid connection"
        
        # Check concurrent query limits
        user_queries = sum(
            1 for query in self.active_queries.values()
            if query.username == connection_info.username
        )
        
        max_concurrent = self.config.get('resource_limits', {}).get('max_concurrent_queries_per_user', 3)
        if user_queries >= max_concurrent:
            return False, None, f"Maximum concurrent queries ({max_concurrent}) exceeded"
        
        # Create query info
        query_info = QueryInfo(
            query_id=query_id,
            sql=sql,
            username=connection_info.username,
            start_time=start_time,
            ip_address=connection_info.ip_address,
            session_id=connection_info.session_id
        )
        
        # Security checks
        security_result = self._check_query_security(sql, connection_info.username)
        if not security_result[0]:
            query_info.status = "BLOCKED"
            query_info.error_message = security_result[1]
            self._record_query(query_info, blocked=True)
            return False, None, security_result[1]
        
        self.active_queries[query_id] = query_info
        
        try:
            # Execute query based on type (simplified for file operations)
            if sql.strip().upper().startswith('SELECT'):
                result = self._execute_select_query(sql, parameters)
                query_info.result_count = len(result) if isinstance(result, list) else 1
            else:
                result = self._execute_modify_query(sql, parameters)
                query_info.rows_affected = result if isinstance(result, int) else 0
            
            # Calculate duration
            query_info.end_time = datetime.utcnow()
            query_info.duration_ms = int((query_info.end_time - start_time).total_seconds() * 1000)
            query_info.status = "SUCCESS"
            
            # Update connection info
            connection_info.last_used = datetime.utcnow()
            connection_info.query_count += 1
            
            # Log successful query
            self._record_query(query_info)
            
            # Check for slow queries
            slow_threshold = self.config.get('query_monitoring', {}).get('slow_query_threshold_ms', 1000)
            if query_info.duration_ms > slow_threshold:
                self._log_security_event(
                    event_type="SLOW_QUERY",
                    username=connection_info.username,
                    description=f"Slow query detected: {query_info.duration_ms}ms",
                    query_id=query_id,
                    connection_id=connection_id,
                    ip_address=connection_info.ip_address,
                    severity="MEDIUM"
                )
            
            return True, result, "Query executed successfully"
            
        except Exception as e:
            query_info.end_time = datetime.utcnow()
            query_info.duration_ms = int((query_info.end_time - start_time).total_seconds() * 1000)
            query_info.status = "ERROR"
            query_info.error_message = str(e)
            
            self._record_query(query_info)
            
            # Log query error
            self._log_security_event(
                event_type="QUERY_ERROR",
                username=connection_info.username,
                description=f"Query execution failed: {str(e)}",
                query_id=query_id,
                connection_id=connection_id,
                ip_address=connection_info.ip_address,
                severity="HIGH"
            )
            
            return False, None, str(e)
            
        finally:
            if query_id in self.active_queries:
                del self.active_queries[query_id]
    
    def _check_query_security(self, sql: str, username: str) -> Tuple[bool, str]:
        """Check query for security issues"""
        # Check for SQL injection patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                self._log_security_event(
                    event_type="INJECTION_ATTEMPT",
                    username=username,
                    description=f"Suspicious SQL pattern detected: {pattern}",
                    severity="CRITICAL"
                )
                return False, "Query blocked due to security policy violation"
        
        # Check query complexity (basic)
        if len(sql) > 10000:  # Very long queries
            return False, "Query too complex"
        
        # Check for dangerous operations by non-admin users
        dangerous_ops = ['DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'DELETE']
        if any(op in sql.upper() for op in dangerous_ops):
            # TODO: Check user permissions here
            pass
        
        return True, "Query passed security checks"
    
    def _execute_select_query(self, sql: str, parameters: Tuple = None) -> List[Dict[str, Any]]:
        """Execute SELECT query (simplified for file operations)"""
        # This is a simplified implementation for CSV/JSON file operations
        # In a real database, this would execute against the actual DB
        
        # For demonstration, return empty result
        return []
    
    def _execute_modify_query(self, sql: str, parameters: Tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE query (simplified)"""
        # This is a simplified implementation
        # In a real database, this would execute against the actual DB
        
        # For demonstration, return 0 rows affected
        return 0
    
    def _record_query(self, query_info: QueryInfo, blocked: bool = False):
        """Record query execution in monitoring database"""
        try:
            # Calculate suspicious score
            suspicious_score = 0
            for pattern in self.suspicious_patterns:
                if re.search(pattern, query_info.sql, re.IGNORECASE):
                    suspicious_score += 10
            
            # Sanitize SQL for storage
            sanitized_sql = self._sanitize_sql(query_info.sql)
            sql_hash = hashlib.sha256(query_info.sql.encode()).hexdigest()[:16]
            
            with sqlite3.connect(self.monitoring_db_path) as conn:
                conn.execute('''
                    INSERT INTO query_history (
                        query_id, sql_hash, sanitized_sql, username, start_time,
                        duration_ms, rows_affected, result_count, status,
                        error_message, ip_address, session_id, suspicious_score, blocked
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    query_info.query_id,
                    sql_hash,
                    sanitized_sql,
                    query_info.username,
                    query_info.start_time.isoformat(),
                    query_info.duration_ms,
                    query_info.rows_affected,
                    query_info.result_count,
                    query_info.status,
                    query_info.error_message,
                    query_info.ip_address,
                    query_info.session_id,
                    suspicious_score,
                    blocked
                ))
                
        except Exception as e:
            self.logger.error(f"Failed to record query: {e}")
    
    def _sanitize_sql(self, sql: str) -> str:
        """Sanitize SQL for logging"""
        # Remove potential sensitive data
        sanitized = re.sub(r"'[^']*password[^']*'", "'***PASSWORD***'", sql, flags=re.IGNORECASE)
        sanitized = re.sub(r"'[^']*token[^']*'", "'***TOKEN***'", sanitized, flags=re.IGNORECASE)
        
        # Limit length
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000] + "... [TRUNCATED]"
        
        return sanitized
    
    def _log_security_event(self, event_type: str, username: str, description: str,
                          query_id: str = None, connection_id: str = None,
                          ip_address: str = "unknown", severity: str = "MEDIUM"):
        """Log security event"""
        event_id = hashlib.sha256(
            f"{event_type}_{username}_{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        try:
            with sqlite3.connect(self.monitoring_db_path) as conn:
                conn.execute('''
                    INSERT INTO security_events (
                        event_id, event_type, timestamp, username, description,
                        query_id, connection_id, ip_address, severity, action_taken
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_id,
                    event_type,
                    datetime.utcnow().isoformat(),
                    username,
                    description,
                    query_id,
                    connection_id,
                    ip_address,
                    severity,
                    "LOGGED"
                ))
                
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
        
        # Also log to file
        log_level = {
            "LOW": logging.INFO,
            "MEDIUM": logging.WARNING,
            "HIGH": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }.get(severity, logging.WARNING)
        
        self.logger.log(
            log_level,
            f"SECURITY_EVENT: {event_type} - {username} - {description} - IP:{ip_address}"
        )
    
    def _detect_anomalies(self):
        """Detect anomalous database access patterns"""
        try:
            with sqlite3.connect(self.monitoring_db_path) as conn:
                # Check for excessive failed queries
                cursor = conn.execute('''
                    SELECT username, COUNT(*) as failed_count
                    FROM query_history
                    WHERE status = 'ERROR' 
                    AND start_time >= ?
                    GROUP BY username
                    HAVING failed_count > 10
                ''', ((datetime.utcnow() - timedelta(hours=1)).isoformat(),))
                
                for username, failed_count in cursor.fetchall():
                    self._log_security_event(
                        event_type="EXCESSIVE_FAILURES",
                        username=username,
                        description=f"Excessive query failures: {failed_count} in past hour",
                        severity="HIGH"
                    )
                
                # Check for suspicious query patterns
                cursor = conn.execute('''
                    SELECT username, COUNT(*) as suspicious_count
                    FROM query_history
                    WHERE suspicious_score > 0
                    AND start_time >= ?
                    GROUP BY username
                    HAVING suspicious_count > 5
                ''', ((datetime.utcnow() - timedelta(hours=1)).isoformat(),))
                
                for username, suspicious_count in cursor.fetchall():
                    self._log_security_event(
                        event_type="SUSPICIOUS_ACTIVITY",
                        username=username,
                        description=f"Multiple suspicious queries: {suspicious_count} in past hour",
                        severity="CRITICAL"
                    )
                
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
    
    def get_query_statistics(self, username: str = None, 
                           hours: int = 24) -> Dict[str, Any]:
        """Get query execution statistics"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            with sqlite3.connect(self.monitoring_db_path) as conn:
                query = '''
                    SELECT 
                        COUNT(*) as total_queries,
                        AVG(duration_ms) as avg_duration,
                        MAX(duration_ms) as max_duration,
                        SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_queries,
                        SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) as failed_queries,
                        SUM(CASE WHEN blocked THEN 1 ELSE 0 END) as blocked_queries,
                        SUM(CASE WHEN suspicious_score > 0 THEN 1 ELSE 0 END) as suspicious_queries
                    FROM query_history
                    WHERE start_time >= ?
                '''
                
                params = [start_time.isoformat()]
                
                if username:
                    query += " AND username = ?"
                    params.append(username)
                
                cursor = conn.execute(query, params)
                stats = cursor.fetchone()
                
                return {
                    "total_queries": stats[0] or 0,
                    "avg_duration_ms": round(stats[1] or 0, 2),
                    "max_duration_ms": stats[2] or 0,
                    "successful_queries": stats[3] or 0,
                    "failed_queries": stats[4] or 0,
                    "blocked_queries": stats[5] or 0,
                    "suspicious_queries": stats[6] or 0,
                    "period_hours": hours,
                    "username": username
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get query statistics: {e}")
            return {"error": str(e)}

class SecureConnection:
    """Secure database connection wrapper"""
    
    def __init__(self, connection_id: str, username: str, 
                 manager: SecureDatabaseManager, ip_address: str, session_id: str):
        self.connection_id = connection_id
        self.username = username
        self.manager = manager
        self.ip_address = ip_address
        self.session_id = session_id
    
    def execute_query(self, sql: str, parameters: Tuple = None) -> Tuple[bool, Any, str]:
        """Execute query through secure manager"""
        return self.manager.execute_secure_query(self.connection_id, sql, parameters)
    
    def read_csv_secure(self, file_path: str, **kwargs) -> pd.DataFrame:
        """Securely read CSV file with audit logging"""
        # Log data access
        self.manager._log_security_event(
            event_type="DATA_ACCESS",
            username=self.username,
            description=f"CSV file access: {file_path}",
            ip_address=self.ip_address,
            severity="LOW"
        )
        
        try:
            df = pd.read_csv(file_path, **kwargs)
            
            # Log successful access
            self.manager._log_security_event(
                event_type="DATA_ACCESS_SUCCESS",
                username=self.username,
                description=f"CSV file read successfully: {file_path} - {len(df)} rows",
                ip_address=self.ip_address,
                severity="LOW"
            )
            
            return df
            
        except Exception as e:
            self.manager._log_security_event(
                event_type="DATA_ACCESS_ERROR",
                username=self.username,
                description=f"CSV file read failed: {file_path} - {str(e)}",
                ip_address=self.ip_address,
                severity="MEDIUM"
            )
            raise
    
    def write_csv_secure(self, df: pd.DataFrame, file_path: str, **kwargs) -> None:
        """Securely write CSV file with audit logging"""
        # Log data modification
        self.manager._log_security_event(
            event_type="DATA_MODIFICATION",
            username=self.username,
            description=f"CSV file write: {file_path} - {len(df)} rows",
            ip_address=self.ip_address,
            severity="MEDIUM"
        )
        
        try:
            # Create backup before modification
            backup_path = f"{file_path}.backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            if Path(file_path).exists():
                shutil.copy2(file_path, backup_path)
            
            df.to_csv(file_path, **kwargs)
            
            # Log successful modification
            self.manager._log_security_event(
                event_type="DATA_MODIFICATION_SUCCESS",
                username=self.username,
                description=f"CSV file written successfully: {file_path}",
                ip_address=self.ip_address,
                severity="MEDIUM"
            )
            
        except Exception as e:
            self.manager._log_security_event(
                event_type="DATA_MODIFICATION_ERROR",
                username=self.username,
                description=f"CSV file write failed: {file_path} - {str(e)}",
                ip_address=self.ip_address,
                severity="HIGH"
            )
            raise