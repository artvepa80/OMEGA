"""
OMEGA PRO AI v10.1 - Data Protection Manager
Data masking, retention policies, and secure deletion system
"""

import os
import json
import re
import hashlib
import shutil
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import logging
from dataclasses import dataclass
import sqlite3
from enum import Enum
import schedule
import time
import threading

class DataClassification(Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class MaskingType(Enum):
    """Types of data masking"""
    FULL = "full"
    PARTIAL = "partial"
    RANDOM = "random"
    HASH = "hash"
    TOKENIZE = "tokenize"

@dataclass
class RetentionRule:
    """Data retention rule"""
    name: str
    pattern: str  # File pattern or data type
    retention_days: int
    archive_days: int
    classification: DataClassification
    auto_delete: bool = True
    requires_approval: bool = False

@dataclass
class MaskingRule:
    """Data masking rule"""
    field_name: str
    masking_type: MaskingType
    classification: DataClassification
    preserve_format: bool = True
    mask_character: str = "*"
    preserve_length: bool = True

class DataProtectionManager:
    """Manages data masking and retention policies"""
    
    def __init__(self, config_path: str = None):
        """Initialize data protection manager"""
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        self.masking_rules = self._load_masking_rules()
        self.retention_rules = self._load_retention_rules()
        self.protection_db_path = 'security/data_protection.db'
        self._setup_protection_database()
        self._schedule_retention_cleanup()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup data protection logging"""
        logger = logging.getLogger('DataProtectionManager')
        logger.setLevel(logging.INFO)
        
        os.makedirs('security/logs', exist_ok=True)
        handler = logging.FileHandler(
            'security/logs/data_protection.log',
            mode='a'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load data protection configuration"""
        default_path = 'security/security_config.json'
        path = config_path or default_path
        
        try:
            with open(path, 'r') as f:
                config = json.load(f)
            return config.get('data_protection', {})
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default data protection configuration"""
        return {
            "data_masking": {
                "enabled": True,
                "environments": ["development", "testing", "staging"],
                "masking_rules": {
                    "email": "partial",
                    "phone": "full",
                    "credit_card": "full",
                    "ssn": "full"
                }
            },
            "retention_policy": {
                "enabled": True,
                "default_retention_days": 2555,
                "categories": {
                    "logs": {
                        "retention_days": 365,
                        "archive_after_days": 90
                    },
                    "user_data": {
                        "retention_days": 2555,
                        "archive_after_days": 1825
                    },
                    "audit_logs": {
                        "retention_days": 2555,
                        "archive_after_days": 365
                    }
                }
            },
            "secure_deletion": {
                "overwrite_passes": 3,
                "verify_deletion": True
            }
        }
    
    def _load_masking_rules(self) -> List[MaskingRule]:
        """Load data masking rules"""
        rules_file = 'security/masking_rules.json'
        
        if os.path.exists(rules_file):
            try:
                with open(rules_file, 'r') as f:
                    rules_data = json.load(f)
                
                rules = []
                for rule_data in rules_data:
                    rule_data['masking_type'] = MaskingType(rule_data['masking_type'])
                    rule_data['classification'] = DataClassification(rule_data['classification'])
                    rules.append(MaskingRule(**rule_data))
                
                return rules
                
            except Exception as e:
                self.logger.error(f"Failed to load masking rules: {e}")
        
        return self._create_default_masking_rules()
    
    def _create_default_masking_rules(self) -> List[MaskingRule]:
        """Create default masking rules"""
        default_rules = [
            MaskingRule(
                field_name="email",
                masking_type=MaskingType.PARTIAL,
                classification=DataClassification.CONFIDENTIAL,
                preserve_format=True
            ),
            MaskingRule(
                field_name="phone",
                masking_type=MaskingType.FULL,
                classification=DataClassification.CONFIDENTIAL,
                preserve_format=False
            ),
            MaskingRule(
                field_name="credit_card",
                masking_type=MaskingType.PARTIAL,
                classification=DataClassification.RESTRICTED,
                preserve_format=True
            ),
            MaskingRule(
                field_name="ssn",
                masking_type=MaskingType.FULL,
                classification=DataClassification.RESTRICTED,
                preserve_format=False
            ),
            MaskingRule(
                field_name="password",
                masking_type=MaskingType.HASH,
                classification=DataClassification.RESTRICTED,
                preserve_format=False
            ),
            MaskingRule(
                field_name="api_key",
                masking_type=MaskingType.TOKENIZE,
                classification=DataClassification.RESTRICTED,
                preserve_format=False
            )
        ]
        
        self._save_masking_rules(default_rules)
        return default_rules
    
    def _save_masking_rules(self, rules: List[MaskingRule]) -> None:
        """Save masking rules"""
        try:
            rules_data = []
            for rule in rules:
                rule_dict = {
                    'field_name': rule.field_name,
                    'masking_type': rule.masking_type.value,
                    'classification': rule.classification.value,
                    'preserve_format': rule.preserve_format,
                    'mask_character': rule.mask_character,
                    'preserve_length': rule.preserve_length
                }
                rules_data.append(rule_dict)
            
            os.makedirs('security', exist_ok=True)
            with open('security/masking_rules.json', 'w') as f:
                json.dump(rules_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save masking rules: {e}")
    
    def _load_retention_rules(self) -> List[RetentionRule]:
        """Load retention rules"""
        rules_file = 'security/retention_rules.json'
        
        if os.path.exists(rules_file):
            try:
                with open(rules_file, 'r') as f:
                    rules_data = json.load(f)
                
                rules = []
                for rule_data in rules_data:
                    rule_data['classification'] = DataClassification(rule_data['classification'])
                    rules.append(RetentionRule(**rule_data))
                
                return rules
                
            except Exception as e:
                self.logger.error(f"Failed to load retention rules: {e}")
        
        return self._create_default_retention_rules()
    
    def _create_default_retention_rules(self) -> List[RetentionRule]:
        """Create default retention rules"""
        default_rules = [
            RetentionRule(
                name="log_files",
                pattern="*.log",
                retention_days=365,
                archive_days=90,
                classification=DataClassification.INTERNAL
            ),
            RetentionRule(
                name="csv_data",
                pattern="*.csv",
                retention_days=2555,
                archive_days=1825,
                classification=DataClassification.CONFIDENTIAL
            ),
            RetentionRule(
                name="json_data",
                pattern="*.json",
                retention_days=2555,
                archive_days=1825,
                classification=DataClassification.CONFIDENTIAL
            ),
            RetentionRule(
                name="model_files",
                pattern="*.pkl",
                retention_days=1095,
                archive_days=365,
                classification=DataClassification.INTERNAL
            ),
            RetentionRule(
                name="backup_files",
                pattern="*.backup",
                retention_days=90,
                archive_days=30,
                classification=DataClassification.CONFIDENTIAL
            ),
            RetentionRule(
                name="temp_files",
                pattern="temp/*",
                retention_days=7,
                archive_days=0,
                classification=DataClassification.PUBLIC
            )
        ]
        
        self._save_retention_rules(default_rules)
        return default_rules
    
    def _save_retention_rules(self, rules: List[RetentionRule]) -> None:
        """Save retention rules"""
        try:
            rules_data = []
            for rule in rules:
                rule_dict = {
                    'name': rule.name,
                    'pattern': rule.pattern,
                    'retention_days': rule.retention_days,
                    'archive_days': rule.archive_days,
                    'classification': rule.classification.value,
                    'auto_delete': rule.auto_delete,
                    'requires_approval': rule.requires_approval
                }
                rules_data.append(rule_dict)
            
            os.makedirs('security', exist_ok=True)
            with open('security/retention_rules.json', 'w') as f:
                json.dump(rules_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save retention rules: {e}")
    
    def _setup_protection_database(self):
        """Setup data protection tracking database"""
        os.makedirs('security', exist_ok=True)
        
        with sqlite3.connect(self.protection_db_path) as conn:
            # File tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS file_tracking (
                    file_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    retention_rule TEXT,
                    archive_date TEXT,
                    deletion_date TEXT,
                    is_archived BOOLEAN DEFAULT FALSE,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    checksum TEXT
                )
            ''')
            
            # Masking operations table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS masking_operations (
                    operation_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    masking_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    original_checksum TEXT,
                    masked_checksum TEXT,
                    reversible BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Data deletion audit
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deletion_audit (
                    deletion_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    deletion_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    reason TEXT,
                    approved_by TEXT,
                    verification_status TEXT,
                    secure_deletion BOOLEAN DEFAULT TRUE
                )
            ''')
            
            conn.commit()
    
    def mask_sensitive_data(self, data: Union[pd.DataFrame, dict, str], 
                          environment: str = "development") -> Union[pd.DataFrame, dict, str]:
        """Apply data masking based on environment and rules"""
        masking_enabled = self.config.get('data_masking', {}).get('enabled', True)
        masked_environments = self.config.get('data_masking', {}).get('environments', [])
        
        if not masking_enabled or environment not in masked_environments:
            return data
        
        if isinstance(data, pd.DataFrame):
            return self._mask_dataframe(data)
        elif isinstance(data, dict):
            return self._mask_dictionary(data)
        elif isinstance(data, str):
            return self._mask_string(data)
        
        return data
    
    def _mask_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mask sensitive fields in DataFrame"""
        masked_df = df.copy()
        
        for rule in self.masking_rules:
            if rule.field_name in masked_df.columns:
                masked_df[rule.field_name] = masked_df[rule.field_name].apply(
                    lambda x: self._apply_masking(str(x), rule) if pd.notna(x) else x
                )
                
                self.logger.info(f"Applied {rule.masking_type.value} masking to column: {rule.field_name}")
        
        return masked_df
    
    def _mask_dictionary(self, data: dict) -> dict:
        """Mask sensitive fields in dictionary"""
        masked_data = data.copy()
        
        for rule in self.masking_rules:
            if rule.field_name in masked_data:
                original_value = masked_data[rule.field_name]
                masked_data[rule.field_name] = self._apply_masking(str(original_value), rule)
                
                self.logger.info(f"Applied {rule.masking_type.value} masking to field: {rule.field_name}")
        
        return masked_data
    
    def _mask_string(self, text: str) -> str:
        """Mask sensitive patterns in text"""
        masked_text = text
        
        # Email masking
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        masked_text = re.sub(email_pattern, lambda m: self._mask_email(m.group()), masked_text)
        
        # Phone masking
        phone_pattern = r'\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s*\d{3}-\d{4}\b'
        masked_text = re.sub(phone_pattern, 'XXX-XXX-XXXX', masked_text)
        
        # SSN masking
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        masked_text = re.sub(ssn_pattern, 'XXX-XX-XXXX', masked_text)
        
        return masked_text
    
    def _apply_masking(self, value: str, rule: MaskingRule) -> str:
        """Apply specific masking rule to value"""
        if not value or value.lower() in ['nan', 'none', 'null']:
            return value
        
        if rule.masking_type == MaskingType.FULL:
            return rule.mask_character * (len(value) if rule.preserve_length else 8)
        
        elif rule.masking_type == MaskingType.PARTIAL:
            if rule.field_name == 'email':
                return self._mask_email(value)
            elif rule.field_name == 'credit_card':
                return self._mask_credit_card(value)
            else:
                # Generic partial masking - show first and last 2 characters
                if len(value) > 4:
                    return value[:2] + rule.mask_character * (len(value) - 4) + value[-2:]
                else:
                    return rule.mask_character * len(value)
        
        elif rule.masking_type == MaskingType.RANDOM:
            import random
            import string
            if rule.preserve_format:
                result = ""
                for char in value:
                    if char.isalpha():
                        result += random.choice(string.ascii_letters)
                    elif char.isdigit():
                        result += random.choice(string.digits)
                    else:
                        result += char
                return result
            else:
                return ''.join(random.choices(string.ascii_letters + string.digits, k=len(value)))
        
        elif rule.masking_type == MaskingType.HASH:
            return hashlib.sha256(value.encode()).hexdigest()[:16]
        
        elif rule.masking_type == MaskingType.TOKENIZE:
            # Simple tokenization - in production, use a proper tokenization system
            token_map = getattr(self, '_token_map', {})
            if value not in token_map:
                token_map[value] = f"TOKEN_{len(token_map):06d}"
            self._token_map = token_map
            return token_map[value]
        
        return value
    
    def _mask_email(self, email: str) -> str:
        """Mask email address"""
        try:
            local, domain = email.split('@')
            if len(local) <= 2:
                masked_local = '*' * len(local)
            else:
                masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
            
            domain_parts = domain.split('.')
            if len(domain_parts[0]) <= 2:
                masked_domain = '*' * len(domain_parts[0]) + '.' + '.'.join(domain_parts[1:])
            else:
                masked_domain = domain_parts[0][:2] + '*' * (len(domain_parts[0]) - 2) + '.' + '.'.join(domain_parts[1:])
            
            return f"{masked_local}@{masked_domain}"
        except:
            return "***@***.***"
    
    def _mask_credit_card(self, cc: str) -> str:
        """Mask credit card number"""
        # Remove spaces and dashes
        cc_clean = re.sub(r'[\s-]', '', cc)
        if len(cc_clean) >= 13:  # Valid credit card length
            return '*' * (len(cc_clean) - 4) + cc_clean[-4:]
        return '*' * len(cc)
    
    def track_file(self, file_path: str, classification: DataClassification) -> str:
        """Track file for retention and protection policies"""
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_id = hashlib.sha256(
            f"{file_path}_{file_path_obj.stat().st_mtime}".encode()
        ).hexdigest()[:16]
        
        # Calculate checksum
        checksum = self._calculate_file_checksum(file_path_obj)
        
        # Find applicable retention rule
        retention_rule = self._find_retention_rule(file_path)
        
        # Calculate dates
        created_at = datetime.fromtimestamp(file_path_obj.stat().st_ctime)
        archive_date = None
        deletion_date = None
        
        if retention_rule:
            if retention_rule.archive_days > 0:
                archive_date = created_at + timedelta(days=retention_rule.archive_days)
            deletion_date = created_at + timedelta(days=retention_rule.retention_days)
        
        # Record in database
        try:
            with sqlite3.connect(self.protection_db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO file_tracking (
                        file_id, file_path, file_size, created_at, last_accessed,
                        classification, retention_rule, archive_date, deletion_date,
                        is_archived, is_deleted, checksum
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_id,
                    str(file_path),
                    file_path_obj.stat().st_size,
                    created_at.isoformat(),
                    datetime.now().isoformat(),
                    classification.value,
                    retention_rule.name if retention_rule else None,
                    archive_date.isoformat() if archive_date else None,
                    deletion_date.isoformat() if deletion_date else None,
                    False,
                    False,
                    checksum
                ))
                
        except Exception as e:
            self.logger.error(f"Failed to track file: {e}")
            
        self.logger.info(f"File tracked: {file_path} - Classification: {classification.value}")
        return file_id
    
    def _find_retention_rule(self, file_path: str) -> Optional[RetentionRule]:
        """Find applicable retention rule for file"""
        import fnmatch
        
        for rule in self.retention_rules:
            if fnmatch.fnmatch(file_path, rule.pattern):
                return rule
        
        return None
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    def _schedule_retention_cleanup(self):
        """Schedule automatic retention cleanup"""
        schedule.every().day.at("03:00").do(self._run_retention_cleanup)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(3600)  # Check every hour
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        self.logger.info("Retention cleanup scheduler started")
    
    def _run_retention_cleanup(self):
        """Run retention cleanup process"""
        try:
            current_time = datetime.utcnow()
            archived_count = 0
            deleted_count = 0
            
            with sqlite3.connect(self.protection_db_path) as conn:
                # Find files that need archiving
                cursor = conn.execute('''
                    SELECT file_id, file_path, archive_date
                    FROM file_tracking
                    WHERE archive_date <= ? AND is_archived = FALSE AND is_deleted = FALSE
                ''', (current_time.isoformat(),))
                
                for file_id, file_path, archive_date in cursor.fetchall():
                    if self._archive_file(file_path):
                        conn.execute('''
                            UPDATE file_tracking 
                            SET is_archived = TRUE 
                            WHERE file_id = ?
                        ''', (file_id,))
                        archived_count += 1
                
                # Find files that need deletion
                cursor = conn.execute('''
                    SELECT file_id, file_path, deletion_date, retention_rule
                    FROM file_tracking
                    WHERE deletion_date <= ? AND is_deleted = FALSE
                ''', (current_time.isoformat(),))
                
                for file_id, file_path, deletion_date, retention_rule_name in cursor.fetchall():
                    rule = next((r for r in self.retention_rules if r.name == retention_rule_name), None)
                    
                    if rule and rule.auto_delete:
                        if not rule.requires_approval or self._has_deletion_approval(file_id):
                            if self._secure_delete_file(file_path):
                                conn.execute('''
                                    UPDATE file_tracking 
                                    SET is_deleted = TRUE 
                                    WHERE file_id = ?
                                ''', (file_id,))
                                deleted_count += 1
                
                conn.commit()
            
            if archived_count > 0 or deleted_count > 0:
                self.logger.info(f"Retention cleanup completed: {archived_count} archived, {deleted_count} deleted")
            
        except Exception as e:
            self.logger.error(f"Retention cleanup failed: {e}")
    
    def _archive_file(self, file_path: str) -> bool:
        """Archive file to long-term storage"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                self.logger.warning(f"File not found for archiving: {file_path}")
                return False
            
            # Create archive directory structure
            archive_dir = Path("archives") / datetime.now().strftime("%Y/%m")
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Archive file
            archive_path = archive_dir / source_path.name
            shutil.move(str(source_path), str(archive_path))
            
            self.logger.info(f"File archived: {file_path} -> {archive_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"File archiving failed: {file_path}: {e}")
            return False
    
    def _has_deletion_approval(self, file_id: str) -> bool:
        """Check if file has deletion approval"""
        # In a real implementation, this would check an approval system
        return True
    
    def _secure_delete_file(self, file_path: str) -> bool:
        """Securely delete file with overwriting"""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                self.logger.warning(f"File not found for deletion: {file_path}")
                return True  # Already deleted
            
            # Get file size
            file_size = file_path_obj.stat().st_size
            
            # Overwrite file multiple times
            overwrite_passes = self.config.get('secure_deletion', {}).get('overwrite_passes', 3)
            
            for pass_num in range(overwrite_passes):
                with open(file_path, 'r+b') as f:
                    # Overwrite with random data
                    import os
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
            
            # Finally delete the file
            file_path_obj.unlink()
            
            # Record deletion
            deletion_id = hashlib.sha256(
                f"{file_path}_{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:16]
            
            with sqlite3.connect(self.protection_db_path) as conn:
                conn.execute('''
                    INSERT INTO deletion_audit (
                        deletion_id, file_path, deletion_type, timestamp,
                        reason, approved_by, verification_status, secure_deletion
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    deletion_id,
                    file_path,
                    "RETENTION_POLICY",
                    datetime.utcnow().isoformat(),
                    "Automatic deletion per retention policy",
                    "SYSTEM",
                    "VERIFIED" if self._verify_deletion(file_path) else "FAILED",
                    True
                ))
            
            self.logger.info(f"File securely deleted: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Secure deletion failed: {file_path}: {e}")
            return False
    
    def _verify_deletion(self, file_path: str) -> bool:
        """Verify file has been securely deleted"""
        return not Path(file_path).exists()
    
    def get_protection_status(self) -> Dict[str, Any]:
        """Get data protection status"""
        try:
            with sqlite3.connect(self.protection_db_path) as conn:
                # File statistics
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_files,
                        SUM(CASE WHEN is_archived THEN 1 ELSE 0 END) as archived_files,
                        SUM(CASE WHEN is_deleted THEN 1 ELSE 0 END) as deleted_files,
                        SUM(file_size) as total_size_bytes
                    FROM file_tracking
                ''')
                
                stats = cursor.fetchone()
                
                # Upcoming actions
                current_time = datetime.utcnow()
                
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM file_tracking
                    WHERE archive_date <= ? AND is_archived = FALSE AND is_deleted = FALSE
                ''', (current_time.isoformat(),))
                
                pending_archives = cursor.fetchone()[0]
                
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM file_tracking
                    WHERE deletion_date <= ? AND is_deleted = FALSE
                ''', (current_time.isoformat(),))
                
                pending_deletions = cursor.fetchone()[0]
                
                return {
                    "total_tracked_files": stats[0] or 0,
                    "archived_files": stats[1] or 0,
                    "deleted_files": stats[2] or 0,
                    "total_size_gb": round((stats[3] or 0) / (1024**3), 2),
                    "pending_archives": pending_archives,
                    "pending_deletions": pending_deletions,
                    "masking_rules": len(self.masking_rules),
                    "retention_rules": len(self.retention_rules)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get protection status: {e}")
            return {"error": str(e)}