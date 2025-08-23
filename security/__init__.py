"""
OMEGA PRO AI v10.1 - Security Package
Comprehensive security system with encryption, authentication, auditing, and compliance
"""

from .security_manager import SecurityManager, get_security_manager
from .encryption_manager import EncryptionManager
from .auth_manager import AuthManager, UserRole, AuthenticationMethod
from .audit_logger import AuditLogger, AuditEventType, AuditSeverity
from .backup_manager import BackupManager, BackupJob
from .secure_database_manager import SecureDatabaseManager
from .data_protection_manager import DataProtectionManager, DataClassification, MaskingType
from .anomaly_detector import AnomalyDetector, AlertSeverity, AnomalyType
from .compliance_manager import ComplianceManager, ComplianceStandard, ComplianceStatus

__version__ = "10.1.0"
__author__ = "OMEGA PRO AI Security Team"

__all__ = [
    # Main security manager
    'SecurityManager',
    'get_security_manager',
    
    # Core security components
    'EncryptionManager',
    'AuthManager',
    'AuditLogger',
    'BackupManager',
    'SecureDatabaseManager',
    'DataProtectionManager',
    'AnomalyDetector',
    'ComplianceManager',
    
    # Enums and types
    'UserRole',
    'AuthenticationMethod',
    'AuditEventType',
    'AuditSeverity',
    'DataClassification',
    'MaskingType',
    'AlertSeverity',
    'AnomalyType',
    'ComplianceStandard',
    'ComplianceStatus',
    
    # Data classes
    'BackupJob'
]