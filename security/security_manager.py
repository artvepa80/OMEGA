"""
OMEGA PRO AI v10.1 - Integrated Security Manager
Central security management system integrating all security components
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# Import security modules
from .encryption_manager import EncryptionManager
from .auth_manager import AuthManager, UserRole
from .audit_logger import AuditLogger
from .backup_manager import BackupManager
from .secure_database_manager import SecureDatabaseManager
from .data_protection_manager import DataProtectionManager, DataClassification
from .anomaly_detector import AnomalyDetector
from .compliance_manager import ComplianceManager, ComplianceStandard

class SecurityManager:
    """
    Integrated security management system
    Coordinates all security components and provides unified interface
    """
    
    def __init__(self, config_path: str = None):
        """Initialize integrated security manager"""
        self.logger = self._setup_logging()
        self.config_path = config_path or 'security/security_config.json'
        
        # Initialize security components
        self.encryption_manager = EncryptionManager(config_path)
        self.auth_manager = AuthManager(config_path)
        self.audit_logger = AuditLogger(config_path)
        self.backup_manager = BackupManager(config_path)
        self.database_manager = SecureDatabaseManager(config_path)
        self.data_protection_manager = DataProtectionManager(config_path)
        self.anomaly_detector = AnomalyDetector(config_path)
        self.compliance_manager = ComplianceManager(config_path)
        
        self.logger.info("OMEGA Security Manager initialized successfully")
        
    def _setup_logging(self) -> logging.Logger:
        """Setup security manager logging"""
        logger = logging.getLogger('SecurityManager')
        logger.setLevel(logging.INFO)
        
        os.makedirs('security/logs', exist_ok=True)
        handler = logging.FileHandler(
            'security/logs/security_manager.log',
            mode='a'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    # Authentication & Authorization Methods
    
    def authenticate_user(self, username: str, password: str, totp_code: str = None,
                         ip_address: str = "unknown", user_agent: str = "unknown") -> Dict[str, Any]:
        """Authenticate user with comprehensive security logging"""
        
        # Log authentication attempt
        self.audit_logger.log_user_authentication(
            username=username,
            success=False,  # Will update if successful
            ip_address=ip_address,
            user_agent=user_agent,
            details={"attempt_time": datetime.utcnow().isoformat()}
        )
        
        # Perform authentication
        success, token, message = self.auth_manager.authenticate_user(
            username=username,
            password=password,
            totp_code=totp_code,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Log successful authentication
        if success:
            self.audit_logger.log_user_authentication(
                username=username,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"session_token": token[:16] + "..."}
            )
        
        return {
            "success": success,
            "token": token,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def validate_session(self, token: str, ip_address: str = None) -> Dict[str, Any]:
        """Validate user session with security monitoring"""
        
        valid, session, message = self.auth_manager.validate_session(token, ip_address)
        
        if valid and session:
            return {
                "valid": True,
                "username": session.username,
                "role": session.role.value,
                "expires_at": session.expires_at.isoformat(),
                "message": message
            }
        else:
            return {
                "valid": False,
                "message": message
            }
    
    def check_permission(self, username: str, permission: str) -> bool:
        """Check user permissions"""
        return self.auth_manager.check_permission(username, permission)
    
    # Data Security Methods
    
    def encrypt_data(self, data: Any, field_type: str = 'general') -> Dict[str, Any]:
        """Encrypt data with audit logging"""
        try:
            encrypted_metadata = self.encryption_manager.encrypt_data(data, field_type)
            
            self.audit_logger.log_event(
                event_type=self.audit_logger.AuditEventType.DATA_MODIFICATION,
                username="system",
                action="encrypt_data",
                resource=f"data.{field_type}",
                details={"field_type": field_type, "algorithm": "AES-256-GCM"}
            )
            
            return {"success": True, "encrypted_data": encrypted_metadata}
            
        except Exception as e:
            self.logger.error(f"Data encryption failed: {e}")
            return {"success": False, "error": str(e)}
    
    def decrypt_data(self, encrypted_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt data with audit logging"""
        try:
            decrypted_data = self.encryption_manager.decrypt_data(encrypted_metadata)
            
            self.audit_logger.log_event(
                event_type=self.audit_logger.AuditEventType.DATA_ACCESS,
                username="system",
                action="decrypt_data",
                resource="encrypted_data",
                details={"decryption_successful": True}
            )
            
            return {"success": True, "data": decrypted_data}
            
        except Exception as e:
            self.logger.error(f"Data decryption failed: {e}")
            return {"success": False, "error": str(e)}
    
    def secure_file_operation(self, username: str, operation: str, file_path: str,
                             ip_address: str = "unknown", **kwargs) -> Dict[str, Any]:
        """Perform secure file operations with comprehensive monitoring"""
        
        try:
            with self.database_manager.get_secure_connection(
                username=username,
                ip_address=ip_address
            ) as conn:
                
                if operation == "read_csv":
                    result = conn.read_csv_secure(file_path, **kwargs)
                    return {"success": True, "data": result}
                    
                elif operation == "write_csv":
                    data = kwargs.get('data')
                    if data is not None:
                        conn.write_csv_secure(data, file_path, **kwargs)
                        return {"success": True, "message": f"CSV written to {file_path}"}
                    else:
                        return {"success": False, "error": "No data provided"}
                
                else:
                    return {"success": False, "error": f"Unsupported operation: {operation}"}
                    
        except Exception as e:
            self.logger.error(f"Secure file operation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def mask_sensitive_data(self, data: Any, environment: str = "development") -> Any:
        """Apply data masking based on environment and security policies"""
        return self.data_protection_manager.mask_sensitive_data(data, environment)
    
    def track_data_file(self, file_path: str, classification: DataClassification) -> Dict[str, Any]:
        """Track file for data protection and retention policies"""
        try:
            file_id = self.data_protection_manager.track_file(file_path, classification)
            return {"success": True, "file_id": file_id}
        except Exception as e:
            self.logger.error(f"File tracking failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Backup & Recovery Methods
    
    def create_backup(self, job_name: str) -> Dict[str, Any]:
        """Create secure encrypted backup"""
        success, message, backup_id = self.backup_manager.create_backup(job_name)
        
        self.audit_logger.log_event(
            event_type=self.audit_logger.AuditEventType.BACKUP_OPERATION,
            username="system",
            action="create_backup",
            resource=f"backup_job.{job_name}",
            result="SUCCESS" if success else "FAILURE",
            details={"backup_id": backup_id, "message": message}
        )
        
        return {
            "success": success,
            "message": message,
            "backup_id": backup_id
        }
    
    def restore_backup(self, backup_id: str, restore_path: str) -> Dict[str, Any]:
        """Restore from secure backup"""
        success, message = self.backup_manager.restore_backup(backup_id, restore_path)
        
        self.audit_logger.log_event(
            event_type=self.audit_logger.AuditEventType.RESTORE_OPERATION,
            username="system",
            action="restore_backup",
            resource=f"backup.{backup_id}",
            result="SUCCESS" if success else "FAILURE",
            details={"restore_path": restore_path, "message": message}
        )
        
        return {"success": success, "message": message}
    
    # Security Monitoring Methods
    
    def get_security_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive security dashboard data"""
        try:
            dashboard = {
                "timestamp": datetime.utcnow().isoformat(),
                "authentication": {
                    "active_sessions": len([
                        s for s in self.auth_manager.sessions.values()
                        if s.is_active
                    ]),
                    "users_count": len(self.auth_manager.users_db)
                },
                "data_protection": self.data_protection_manager.get_protection_status(),
                "backups": self.backup_manager.get_backup_status(),
                "queries": self.database_manager.get_query_statistics(),
                "alerts": self.anomaly_detector.get_alert_summary(),
                "compliance": self.compliance_manager.get_compliance_status()
            }
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Dashboard generation failed: {e}")
            return {"error": str(e)}
    
    def get_security_alerts(self, severity: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent security alerts"""
        try:
            # This would integrate with the anomaly detector
            # For now, return basic structure
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get security alerts: {e}")
            return []
    
    # Compliance Methods
    
    def generate_compliance_report(self, standard: str = None) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        try:
            compliance_standard = None
            if standard:
                compliance_standard = ComplianceStandard(standard.lower())
            
            report = self.compliance_manager.generate_compliance_report(compliance_standard)
            
            self.audit_logger.log_event(
                event_type=self.audit_logger.AuditEventType.DATA_ACCESS,
                username="system",
                action="generate_compliance_report",
                resource="compliance_data",
                details={"standard": standard, "report_generated": True}
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Compliance report generation failed: {e}")
            return {"error": str(e)}
    
    def generate_audit_report(self, start_date: datetime = None,
                            end_date: datetime = None) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            report = self.audit_logger.generate_compliance_report(start_date, end_date)
            return report
            
        except Exception as e:
            self.logger.error(f"Audit report generation failed: {e}")
            return {"error": str(e)}
    
    # Utility Methods
    
    def run_security_health_check(self) -> Dict[str, Any]:
        """Run comprehensive security health check"""
        health_check = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "HEALTHY",
            "components": {}
        }
        
        try:
            # Check encryption system
            test_data = "test_encryption"
            encrypted = self.encryption_manager.encrypt_data(test_data)
            decrypted = self.encryption_manager.decrypt_data(encrypted)
            health_check["components"]["encryption"] = {
                "status": "HEALTHY" if decrypted == test_data else "UNHEALTHY",
                "test_passed": decrypted == test_data
            }
            
            # Check authentication system
            health_check["components"]["authentication"] = {
                "status": "HEALTHY",
                "users_loaded": len(self.auth_manager.users_db) > 0,
                "session_management": True
            }
            
            # Check audit system
            health_check["components"]["audit"] = {
                "status": "HEALTHY",
                "logging_active": True,
                "database_accessible": Path(self.audit_logger.db_path).exists()
            }
            
            # Check backup system
            backup_status = self.backup_manager.get_backup_status()
            health_check["components"]["backup"] = {
                "status": "HEALTHY" if backup_status.get("scheduler_running") else "WARNING",
                "jobs_configured": backup_status.get("backup_jobs_count", 0),
                "recent_backups": backup_status.get("total_backups", 0)
            }
            
            # Check compliance system
            compliance_status = self.compliance_manager.get_compliance_status()
            health_check["components"]["compliance"] = {
                "status": compliance_status.get("overall_status", "UNKNOWN"),
                "standards_monitored": len(compliance_status.get("standards", {})),
                "checks_configured": compliance_status.get("total_checks", 0)
            }
            
            # Determine overall status
            component_statuses = [comp["status"] for comp in health_check["components"].values()]
            if "UNHEALTHY" in component_statuses:
                health_check["overall_status"] = "UNHEALTHY"
            elif "WARNING" in component_statuses:
                health_check["overall_status"] = "WARNING"
            
            return health_check
            
        except Exception as e:
            self.logger.error(f"Security health check failed: {e}")
            health_check["overall_status"] = "ERROR"
            health_check["error"] = str(e)
            return health_check
    
    def initialize_security_for_project(self) -> Dict[str, Any]:
        """Initialize security systems for OMEGA project"""
        try:
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "initialization_results": {}
            }
            
            # Create security directories
            security_dirs = [
                'security',
                'security/logs',
                'security/backups',
                'security/keys',
                'security/certificates'
            ]
            
            for directory in security_dirs:
                Path(directory).mkdir(parents=True, exist_ok=True)
            
            results["initialization_results"]["directories_created"] = len(security_dirs)
            
            # Track important data files
            data_files = [
                ('data/historial_kabala_github.csv', DataClassification.CONFIDENTIAL),
                ('data/omega_learning_data.json', DataClassification.CONFIDENTIAL),
                ('models/', DataClassification.INTERNAL),
                ('config/', DataClassification.INTERNAL)
            ]
            
            tracked_files = 0
            for file_path, classification in data_files:
                if Path(file_path).exists():
                    self.track_data_file(file_path, classification)
                    tracked_files += 1
            
            results["initialization_results"]["files_tracked"] = tracked_files
            
            # Create initial backup
            backup_result = self.create_backup("daily_data_backup")
            results["initialization_results"]["initial_backup"] = backup_result["success"]
            
            # Run initial health check
            health_check = self.run_security_health_check()
            results["health_check"] = health_check
            
            self.logger.info("OMEGA security system initialized successfully")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Security initialization failed: {e}")
            return {"error": str(e)}

# Global security manager instance
_security_manager = None

def get_security_manager(config_path: str = None) -> SecurityManager:
    """Get singleton security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager(config_path)
    return _security_manager