"""
OMEGA PRO AI v10.1 - Secure Backup Manager
Automated encrypted backup system with integrity verification
"""

import os
import json
import shutil
import zipfile
import hashlib
import schedule
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import threading
import logging
import sqlite3
from dataclasses import dataclass
from cryptography.fernet import Fernet
import boto3
from botocore.exceptions import ClientError

@dataclass
class BackupJob:
    """Backup job configuration"""
    name: str
    source_paths: List[str]
    destination_path: str
    frequency: str  # daily, hourly, weekly, monthly
    retention_days: int
    encrypt: bool = True
    compress: bool = True
    verify_integrity: bool = True
    cloud_sync: bool = False
    cloud_provider: Optional[str] = None
    
class BackupManager:
    """Manages automated encrypted backups"""
    
    def __init__(self, config_path: str = None):
        """Initialize backup manager"""
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        self.encryption_key = self._load_encryption_key()
        self.backup_jobs = self._load_backup_jobs()
        self.backup_db_path = 'security/backups.db'
        self._setup_backup_database()
        self._schedule_backups()
        self.cloud_clients = self._setup_cloud_clients()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup backup logging"""
        logger = logging.getLogger('BackupManager')
        logger.setLevel(logging.INFO)
        
        os.makedirs('security/logs', exist_ok=True)
        handler = logging.FileHandler(
            'security/logs/backup_audit.log',
            mode='a'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load backup configuration"""
        default_path = 'security/security_config.json'
        path = config_path or default_path
        
        try:
            with open(path, 'r') as f:
                config = json.load(f)
            return config.get('backup', {})
        except Exception as e:
            self.logger.error(f"Failed to load backup config: {e}")
            return self._get_default_backup_config()
    
    def _get_default_backup_config(self) -> Dict[str, Any]:
        """Default backup configuration"""
        return {
            "encryption": {
                "enabled": True,
                "algorithm": "AES-256-GCM"
            },
            "schedule": {
                "full_backup_frequency": "daily",
                "incremental_frequency": "hourly",
                "backup_window": "02:00-06:00"
            },
            "retention": {
                "daily_retention_days": 30,
                "weekly_retention_weeks": 12,
                "monthly_retention_months": 12,
                "yearly_retention_years": 7
            },
            "verification": {
                "integrity_check": True,
                "test_restore_frequency": "weekly"
            },
            "cloud_sync": {
                "enabled": False,
                "provider": "s3",
                "bucket": "omega-backups",
                "region": "us-east-1"
            }
        }
    
    def _load_encryption_key(self) -> bytes:
        """Load or generate backup encryption key"""
        key_file = 'security/backup_key.key'
        
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    key = f.read()
                self.logger.info("Backup encryption key loaded")
                return key
            except Exception as e:
                self.logger.error(f"Failed to load backup key: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        
        try:
            os.makedirs('security', exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            self.logger.info("New backup encryption key generated")
        except Exception as e:
            self.logger.error(f"Failed to store backup key: {e}")
        
        return key
    
    def _load_backup_jobs(self) -> List[BackupJob]:
        """Load backup job configurations"""
        jobs_file = 'security/backup_jobs.json'
        
        if os.path.exists(jobs_file):
            try:
                with open(jobs_file, 'r') as f:
                    jobs_data = json.load(f)
                
                jobs = []
                for job_data in jobs_data:
                    jobs.append(BackupJob(**job_data))
                
                return jobs
            except Exception as e:
                self.logger.error(f"Failed to load backup jobs: {e}")
        
        return self._create_default_backup_jobs()
    
    def _create_default_backup_jobs(self) -> List[BackupJob]:
        """Create default backup jobs"""
        default_jobs = [
            BackupJob(
                name="daily_data_backup",
                source_paths=[
                    "data/",
                    "models/",
                    "results/",
                    "config/"
                ],
                destination_path="backups/daily",
                frequency="daily",
                retention_days=30,
                encrypt=True,
                compress=True,
                verify_integrity=True,
                cloud_sync=self.config.get('cloud_sync', {}).get('enabled', False)
            ),
            BackupJob(
                name="security_backup",
                source_paths=[
                    "security/",
                    "ssl/"
                ],
                destination_path="backups/security",
                frequency="daily",
                retention_days=90,
                encrypt=True,
                compress=True,
                verify_integrity=True,
                cloud_sync=False  # Security data stays local
            ),
            BackupJob(
                name="incremental_backup",
                source_paths=[
                    "data/",
                    "results/"
                ],
                destination_path="backups/incremental",
                frequency="hourly",
                retention_days=7,
                encrypt=True,
                compress=True,
                verify_integrity=True,
                cloud_sync=False
            )
        ]
        
        # Save default jobs
        self._save_backup_jobs(default_jobs)
        return default_jobs
    
    def _save_backup_jobs(self, jobs: List[BackupJob]) -> None:
        """Save backup jobs configuration"""
        try:
            jobs_data = [
                {
                    'name': job.name,
                    'source_paths': job.source_paths,
                    'destination_path': job.destination_path,
                    'frequency': job.frequency,
                    'retention_days': job.retention_days,
                    'encrypt': job.encrypt,
                    'compress': job.compress,
                    'verify_integrity': job.verify_integrity,
                    'cloud_sync': job.cloud_sync,
                    'cloud_provider': job.cloud_provider
                }
                for job in jobs
            ]
            
            os.makedirs('security', exist_ok=True)
            with open('security/backup_jobs.json', 'w') as f:
                json.dump(jobs_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save backup jobs: {e}")
    
    def _setup_backup_database(self):
        """Setup backup tracking database"""
        os.makedirs('security', exist_ok=True)
        
        with sqlite3.connect(self.backup_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS backup_history (
                    backup_id TEXT PRIMARY KEY,
                    job_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    backup_path TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    file_count INTEGER NOT NULL,
                    duration_seconds REAL NOT NULL,
                    status TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    encrypted BOOLEAN NOT NULL,
                    compressed BOOLEAN NOT NULL,
                    cloud_synced BOOLEAN NOT NULL,
                    error_message TEXT,
                    retention_expires TEXT
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON backup_history(timestamp)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_name 
                ON backup_history(job_name)
            ''')
            
            conn.commit()
    
    def _setup_cloud_clients(self) -> Dict[str, Any]:
        """Setup cloud storage clients"""
        clients = {}
        
        cloud_config = self.config.get('cloud_sync', {})
        if not cloud_config.get('enabled', False):
            return clients
        
        provider = cloud_config.get('provider', 's3')
        
        if provider == 's3':
            try:
                clients['s3'] = boto3.client(
                    's3',
                    region_name=cloud_config.get('region', 'us-east-1')
                )
                self.logger.info("S3 client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize S3 client: {e}")
        
        return clients
    
    def create_backup(self, job_name: str) -> Tuple[bool, str, Optional[str]]:
        """Create backup for specified job"""
        start_time = datetime.utcnow()
        backup_id = hashlib.sha256(
            f"{job_name}_{start_time.isoformat()}".encode()
        ).hexdigest()[:16]
        
        try:
            # Find backup job
            job = next((j for j in self.backup_jobs if j.name == job_name), None)
            if not job:
                return False, f"Backup job '{job_name}' not found", None
            
            # Create destination directory
            timestamp = start_time.strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(job.destination_path) / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Collect files
            files_to_backup = []
            total_size = 0
            
            for source_path in job.source_paths:
                source = Path(source_path)
                if source.exists():
                    if source.is_file():
                        files_to_backup.append(source)
                        total_size += source.stat().st_size
                    elif source.is_dir():
                        for file_path in source.rglob('*'):
                            if file_path.is_file():
                                files_to_backup.append(file_path)
                                total_size += file_path.stat().st_size
            
            if not files_to_backup:
                return False, "No files to backup", None
            
            # Create backup archive
            backup_file = backup_dir / f"{job_name}_{timestamp}.zip"
            
            with zipfile.ZipFile(backup_file, 'w', 
                               zipfile.ZIP_DEFLATED if job.compress else zipfile.ZIP_STORED) as zf:
                
                for file_path in files_to_backup:
                    try:
                        # Calculate relative path
                        rel_path = file_path.relative_to(Path.cwd())
                        zf.write(file_path, rel_path)
                    except Exception as e:
                        self.logger.warning(f"Failed to add file to backup: {file_path}: {e}")
            
            # Calculate checksum
            checksum = self._calculate_file_checksum(backup_file)
            
            # Encrypt if required
            if job.encrypt:
                encrypted_file = backup_file.with_suffix('.zip.encrypted')
                self._encrypt_file(backup_file, encrypted_file)
                backup_file.unlink()  # Remove unencrypted file
                backup_file = encrypted_file
            
            # Calculate backup duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Calculate retention expiry
            retention_expires = start_time + timedelta(days=job.retention_days)
            
            # Record backup in database
            self._record_backup(
                backup_id=backup_id,
                job_name=job_name,
                timestamp=start_time,
                backup_path=str(backup_file),
                size_bytes=backup_file.stat().st_size,
                file_count=len(files_to_backup),
                duration_seconds=duration,
                status="SUCCESS",
                checksum=checksum,
                encrypted=job.encrypt,
                compressed=job.compress,
                cloud_synced=False,  # Will be updated if cloud sync succeeds
                retention_expires=retention_expires
            )
            
            # Cloud sync if enabled
            if job.cloud_sync and 's3' in self.cloud_clients:
                try:
                    self._sync_to_cloud(backup_file, job_name, timestamp)
                    # Update cloud sync status
                    self._update_backup_cloud_status(backup_id, True)
                except Exception as e:
                    self.logger.error(f"Cloud sync failed: {e}")
            
            # Verify integrity if required
            if job.verify_integrity:
                if not self._verify_backup_integrity(backup_file, checksum):
                    return False, "Backup integrity verification failed", backup_id
            
            self.logger.info(f"Backup completed: {job_name} - {backup_file} - {duration:.2f}s")
            return True, f"Backup created successfully: {backup_file}", backup_id
            
        except Exception as e:
            self.logger.error(f"Backup failed: {job_name}: {e}")
            
            # Record failed backup
            self._record_backup(
                backup_id=backup_id,
                job_name=job_name,
                timestamp=start_time,
                backup_path="",
                size_bytes=0,
                file_count=0,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                status="FAILED",
                checksum="",
                encrypted=False,
                compressed=False,
                cloud_synced=False,
                error_message=str(e),
                retention_expires=start_time + timedelta(days=1)
            )
            
            return False, str(e), backup_id
    
    def _encrypt_file(self, source_file: Path, encrypted_file: Path) -> None:
        """Encrypt backup file"""
        fernet = Fernet(self.encryption_key)
        
        with open(source_file, 'rb') as f:
            file_data = f.read()
        
        encrypted_data = fernet.encrypt(file_data)
        
        with open(encrypted_file, 'wb') as f:
            f.write(encrypted_data)
    
    def _decrypt_file(self, encrypted_file: Path, output_file: Path) -> None:
        """Decrypt backup file"""
        fernet = Fernet(self.encryption_key)
        
        with open(encrypted_file, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = fernet.decrypt(encrypted_data)
        
        with open(output_file, 'wb') as f:
            f.write(decrypted_data)
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _verify_backup_integrity(self, backup_file: Path, expected_checksum: str) -> bool:
        """Verify backup file integrity"""
        try:
            actual_checksum = self._calculate_file_checksum(backup_file)
            return actual_checksum == expected_checksum
        except Exception as e:
            self.logger.error(f"Integrity verification failed: {e}")
            return False
    
    def _sync_to_cloud(self, backup_file: Path, job_name: str, timestamp: str) -> None:
        """Sync backup to cloud storage"""
        if 's3' not in self.cloud_clients:
            raise ValueError("S3 client not available")
        
        s3_client = self.cloud_clients['s3']
        cloud_config = self.config.get('cloud_sync', {})
        bucket = cloud_config.get('bucket', 'omega-backups')
        
        # Create S3 key
        s3_key = f"backups/{job_name}/{timestamp}/{backup_file.name}"
        
        try:
            # Upload to S3
            s3_client.upload_file(
                str(backup_file),
                bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'  # Infrequent Access for cost optimization
                }
            )
            
            self.logger.info(f"Backup synced to S3: {s3_key}")
            
        except ClientError as e:
            self.logger.error(f"S3 upload failed: {e}")
            raise
    
    def _record_backup(self, backup_id: str, job_name: str, timestamp: datetime,
                      backup_path: str, size_bytes: int, file_count: int,
                      duration_seconds: float, status: str, checksum: str,
                      encrypted: bool, compressed: bool, cloud_synced: bool,
                      error_message: str = None, retention_expires: datetime = None):
        """Record backup in database"""
        try:
            with sqlite3.connect(self.backup_db_path) as conn:
                conn.execute('''
                    INSERT INTO backup_history (
                        backup_id, job_name, timestamp, backup_path, size_bytes,
                        file_count, duration_seconds, status, checksum,
                        encrypted, compressed, cloud_synced, error_message,
                        retention_expires
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    backup_id, job_name, timestamp.isoformat(), backup_path,
                    size_bytes, file_count, duration_seconds, status, checksum,
                    encrypted, compressed, cloud_synced, error_message,
                    retention_expires.isoformat() if retention_expires else None
                ))
                
        except Exception as e:
            self.logger.error(f"Failed to record backup: {e}")
    
    def _update_backup_cloud_status(self, backup_id: str, cloud_synced: bool) -> None:
        """Update cloud sync status for backup"""
        try:
            with sqlite3.connect(self.backup_db_path) as conn:
                conn.execute('''
                    UPDATE backup_history 
                    SET cloud_synced = ? 
                    WHERE backup_id = ?
                ''', (cloud_synced, backup_id))
                
        except Exception as e:
            self.logger.error(f"Failed to update cloud sync status: {e}")
    
    def restore_backup(self, backup_id: str, restore_path: str) -> Tuple[bool, str]:
        """Restore backup by ID"""
        try:
            # Get backup info from database
            with sqlite3.connect(self.backup_db_path) as conn:
                cursor = conn.execute('''
                    SELECT * FROM backup_history WHERE backup_id = ?
                ''', (backup_id,))
                
                backup_info = cursor.fetchone()
                if not backup_info:
                    return False, f"Backup {backup_id} not found"
            
            backup_path = Path(backup_info[3])  # backup_path column
            encrypted = backup_info[9]  # encrypted column
            
            if not backup_path.exists():
                return False, f"Backup file not found: {backup_path}"
            
            # Create restore directory
            restore_dir = Path(restore_path)
            restore_dir.mkdir(parents=True, exist_ok=True)
            
            # Decrypt if necessary
            if encrypted:
                decrypted_file = restore_dir / f"temp_{backup_path.stem}.zip"
                self._decrypt_file(backup_path, decrypted_file)
                backup_path = decrypted_file
            
            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as zf:
                zf.extractall(restore_dir)
            
            # Clean up temporary files
            if encrypted and decrypted_file.exists():
                decrypted_file.unlink()
            
            self.logger.info(f"Backup restored: {backup_id} to {restore_path}")
            return True, f"Backup restored successfully to {restore_path}"
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False, str(e)
    
    def _schedule_backups(self):
        """Schedule automatic backups"""
        for job in self.backup_jobs:
            if job.frequency == 'hourly':
                schedule.every().hour.do(self._run_scheduled_backup, job.name)
            elif job.frequency == 'daily':
                schedule.every().day.at("02:00").do(self._run_scheduled_backup, job.name)
            elif job.frequency == 'weekly':
                schedule.every().sunday.at("01:00").do(self._run_scheduled_backup, job.name)
            elif job.frequency == 'monthly':
                schedule.every().month.do(self._run_scheduled_backup, job.name)
        
        # Start scheduler in separate thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        self.logger.info(f"Backup scheduler started with {len(self.backup_jobs)} jobs")
    
    def _run_scheduled_backup(self, job_name: str):
        """Run scheduled backup"""
        try:
            success, message, backup_id = self.create_backup(job_name)
            if success:
                self.logger.info(f"Scheduled backup completed: {job_name}")
            else:
                self.logger.error(f"Scheduled backup failed: {job_name}: {message}")
        except Exception as e:
            self.logger.error(f"Scheduled backup error: {job_name}: {e}")
    
    def cleanup_expired_backups(self) -> int:
        """Clean up expired backups"""
        cleaned_count = 0
        current_time = datetime.utcnow()
        
        try:
            with sqlite3.connect(self.backup_db_path) as conn:
                # Find expired backups
                cursor = conn.execute('''
                    SELECT backup_id, backup_path FROM backup_history
                    WHERE retention_expires < ? AND status = 'SUCCESS'
                ''', (current_time.isoformat(),))
                
                expired_backups = cursor.fetchall()
                
                for backup_id, backup_path in expired_backups:
                    try:
                        # Delete backup file
                        if backup_path and Path(backup_path).exists():
                            Path(backup_path).unlink()
                        
                        # Update database record
                        conn.execute('''
                            UPDATE backup_history 
                            SET status = 'EXPIRED' 
                            WHERE backup_id = ?
                        ''', (backup_id,))
                        
                        cleaned_count += 1
                        
                    except Exception as e:
                        self.logger.error(f"Failed to clean backup {backup_id}: {e}")
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} expired backups")
        
        return cleaned_count
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get overall backup status"""
        try:
            with sqlite3.connect(self.backup_db_path) as conn:
                # Get recent backup statistics
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_backups,
                        SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_backups,
                        SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_backups,
                        SUM(size_bytes) as total_size_bytes,
                        MAX(timestamp) as last_backup
                    FROM backup_history
                    WHERE timestamp >= ?
                ''', ((datetime.utcnow() - timedelta(days=30)).isoformat(),))
                
                stats = cursor.fetchone()
                
                return {
                    "total_backups": stats[0] or 0,
                    "successful_backups": stats[1] or 0,
                    "failed_backups": stats[2] or 0,
                    "total_size_gb": round((stats[3] or 0) / (1024**3), 2),
                    "last_backup": stats[4],
                    "backup_jobs_count": len(self.backup_jobs),
                    "scheduler_running": True
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get backup status: {e}")
            return {"error": str(e)}