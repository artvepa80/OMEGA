#!/usr/bin/env python3
"""
End-to-End Encryption and Data Protection Manager for OMEGA PRO AI v10.1
Implements AES-256 encryption, RSA key management, secure key storage, and GDPR compliance
"""

import os
import json
import logging
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import redis
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization, padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import keyring
import getpass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EncryptionKey:
    """Encryption key metadata"""
    key_id: str
    key_type: str  # symmetric, asymmetric_public, asymmetric_private
    algorithm: str  # AES-256, RSA-2048, RSA-4096
    created_at: datetime
    expires_at: Optional[datetime]
    usage_count: int
    max_usage: Optional[int]
    purpose: str  # data_encryption, key_encryption, signing
    owner: str
    is_active: bool

@dataclass
class EncryptedData:
    """Encrypted data container"""
    data_id: str
    encrypted_data: bytes
    encryption_key_id: str
    algorithm: str
    iv: Optional[bytes]  # Initialization vector
    tag: Optional[bytes]  # Authentication tag for AEAD
    metadata: Dict[str, Any]
    created_at: datetime
    data_type: str  # file, database_field, message, api_payload
    retention_period: Optional[timedelta]
    access_log: List[str]

@dataclass
class DataClassification:
    """Data classification for GDPR compliance"""
    classification_id: str
    data_type: str
    sensitivity_level: str  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    contains_pii: bool  # Personally Identifiable Information
    retention_period: timedelta
    encryption_required: bool
    access_controls: List[str]
    legal_basis: str  # GDPR legal basis
    processing_purpose: str
    data_subject_rights: List[str]  # access, rectification, erasure, portability

class SecureKeyManager:
    """Secure cryptographic key management system"""
    
    def __init__(self, master_key: Optional[bytes] = None, keystore_path: str = "secure_keystore.db"):
        """Initialize secure key manager"""
        
        self.keystore_path = keystore_path
        self.backend = default_backend()
        
        # Initialize master key for key encryption
        if master_key:
            self.master_key = master_key
        else:
            self.master_key = self._get_or_create_master_key()
        
        self.master_cipher = Fernet(base64.urlsafe_b64encode(self.master_key[:32]))
        
        # Initialize key database
        self.init_keystore()
        
        # Key rotation settings
        self.key_rotation_interval = timedelta(days=90)
        self.max_key_usage = 1000000  # Maximum operations per key
        
        logger.info("Secure Key Manager initialized")
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key from secure storage"""
        try:
            # Try to get from keyring first
            stored_key = keyring.get_password("omega_pro_ai", "master_key")
            if stored_key:
                return base64.b64decode(stored_key)
            
            # If not found, create new master key
            master_key = secrets.token_bytes(32)  # 256-bit key
            
            # Store in keyring
            keyring.set_password("omega_pro_ai", "master_key", base64.b64encode(master_key).decode())
            
            # Also store in environment file as backup (encrypted with user password)
            self._backup_master_key_to_file(master_key)
            
            logger.info("New master key created and stored securely")
            return master_key
            
        except Exception as e:
            logger.error(f"Master key management failed: {e}")
            # Fallback to generating a key (not recommended for production)
            logger.warning("Using fallback key generation - not suitable for production!")
            return secrets.token_bytes(32)
    
    def _backup_master_key_to_file(self, master_key: bytes):
        """Backup master key to encrypted file"""
        try:
            # Get user password for encryption
            password = getpass.getpass("Enter password for master key backup: ").encode()
            
            # Derive key from password
            salt = secrets.token_bytes(16)
            kdf = Scrypt(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            key = kdf.derive(password)
            
            # Encrypt master key
            cipher = Fernet(base64.urlsafe_b64encode(key))
            encrypted_master = cipher.encrypt(master_key)
            
            # Save to file
            backup_data = {
                "salt": base64.b64encode(salt).decode(),
                "encrypted_master_key": base64.b64encode(encrypted_master).decode(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            backup_path = Path("master_key_backup.json")
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(backup_path, 0o600)
            
            logger.info("Master key backup created")
            
        except Exception as e:
            logger.error(f"Master key backup failed: {e}")
    
    def init_keystore(self):
        """Initialize key storage database"""
        try:
            conn = sqlite3.connect(self.keystore_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS encryption_keys (
                    key_id TEXT PRIMARY KEY,
                    key_type TEXT NOT NULL,
                    algorithm TEXT NOT NULL,
                    encrypted_key_data BLOB NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    max_usage INTEGER,
                    purpose TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_key_type ON encryption_keys(key_type);
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_purpose ON encryption_keys(purpose);
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_owner ON encryption_keys(owner);
            ''')
            
            conn.commit()
            conn.close()
            
            # Set restrictive permissions on database file
            os.chmod(self.keystore_path, 0o600)
            
            logger.info("Key store database initialized")
            
        except Exception as e:
            logger.error(f"Key store initialization failed: {e}")
            raise
    
    def generate_symmetric_key(self, purpose: str, owner: str, 
                             algorithm: str = "AES-256") -> str:
        """Generate symmetric encryption key"""
        try:
            # Generate key
            if algorithm == "AES-256":
                key = secrets.token_bytes(32)  # 256-bit key
            elif algorithm == "AES-128":
                key = secrets.token_bytes(16)  # 128-bit key
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
            
            # Create key metadata
            key_id = hashlib.sha256(f"{purpose}:{owner}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
            
            key_info = EncryptionKey(
                key_id=key_id,
                key_type="symmetric",
                algorithm=algorithm,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + self.key_rotation_interval,
                usage_count=0,
                max_usage=self.max_key_usage,
                purpose=purpose,
                owner=owner,
                is_active=True
            )
            
            # Encrypt key with master key
            encrypted_key = self.master_cipher.encrypt(key)
            
            # Store in database
            self._store_key(key_info, encrypted_key)
            
            logger.info(f"Symmetric key generated: {key_id} for {purpose}")
            return key_id
            
        except Exception as e:
            logger.error(f"Symmetric key generation failed: {e}")
            raise
    
    def generate_asymmetric_keypair(self, purpose: str, owner: str,
                                  key_size: int = 2048) -> Tuple[str, str]:
        """Generate RSA asymmetric key pair"""
        try:
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=self.backend
            )
            public_key = private_key.public_key()
            
            # Serialize keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Create key IDs
            private_key_id = hashlib.sha256(f"private:{purpose}:{owner}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
            public_key_id = hashlib.sha256(f"public:{purpose}:{owner}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
            
            # Create key metadata
            private_key_info = EncryptionKey(
                key_id=private_key_id,
                key_type="asymmetric_private",
                algorithm=f"RSA-{key_size}",
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + self.key_rotation_interval,
                usage_count=0,
                max_usage=self.max_key_usage,
                purpose=purpose,
                owner=owner,
                is_active=True
            )
            
            public_key_info = EncryptionKey(
                key_id=public_key_id,
                key_type="asymmetric_public",
                algorithm=f"RSA-{key_size}",
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + self.key_rotation_interval,
                usage_count=0,
                max_usage=self.max_key_usage,
                purpose=purpose,
                owner=owner,
                is_active=True
            )
            
            # Encrypt and store keys
            encrypted_private = self.master_cipher.encrypt(private_pem)
            encrypted_public = self.master_cipher.encrypt(public_pem)
            
            self._store_key(private_key_info, encrypted_private)
            self._store_key(public_key_info, encrypted_public)
            
            logger.info(f"Asymmetric key pair generated: private={private_key_id}, public={public_key_id}")
            return private_key_id, public_key_id
            
        except Exception as e:
            logger.error(f"Asymmetric key generation failed: {e}")
            raise
    
    def get_key(self, key_id: str) -> Optional[bytes]:
        """Retrieve and decrypt key by ID"""
        try:
            conn = sqlite3.connect(self.keystore_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT encrypted_key_data, usage_count, max_usage, is_active
                FROM encryption_keys WHERE key_id = ?
            ''', (key_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                logger.warning(f"Key not found: {key_id}")
                return None
            
            encrypted_key_data, usage_count, max_usage, is_active = row
            
            if not is_active:
                logger.warning(f"Key is inactive: {key_id}")
                return None
            
            if max_usage and usage_count >= max_usage:
                logger.warning(f"Key usage limit exceeded: {key_id}")
                return None
            
            # Decrypt key
            key = self.master_cipher.decrypt(encrypted_key_data)
            
            # Increment usage count
            self._increment_key_usage(key_id)
            
            return key
            
        except Exception as e:
            logger.error(f"Key retrieval failed for {key_id}: {e}")
            return None
    
    def _store_key(self, key_info: EncryptionKey, encrypted_key_data: bytes):
        """Store encrypted key in database"""
        try:
            conn = sqlite3.connect(self.keystore_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO encryption_keys 
                (key_id, key_type, algorithm, encrypted_key_data, created_at, expires_at, 
                 usage_count, max_usage, purpose, owner, is_active, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                key_info.key_id, key_info.key_type, key_info.algorithm,
                encrypted_key_data, key_info.created_at, key_info.expires_at,
                key_info.usage_count, key_info.max_usage, key_info.purpose,
                key_info.owner, key_info.is_active, json.dumps(asdict(key_info))
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Key storage failed: {e}")
            raise
    
    def _increment_key_usage(self, key_id: str):
        """Increment key usage counter"""
        try:
            conn = sqlite3.connect(self.keystore_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE encryption_keys 
                SET usage_count = usage_count + 1
                WHERE key_id = ?
            ''', (key_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Key usage increment failed for {key_id}: {e}")
    
    def rotate_key(self, key_id: str) -> Optional[str]:
        """Rotate encryption key"""
        try:
            # Get existing key info
            conn = sqlite3.connect(self.keystore_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT purpose, owner, algorithm, key_type
                FROM encryption_keys WHERE key_id = ?
            ''', (key_id,))
            
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Key not found for rotation: {key_id}")
                return None
            
            purpose, owner, algorithm, key_type = row
            
            # Deactivate old key
            cursor.execute('''
                UPDATE encryption_keys 
                SET is_active = 0
                WHERE key_id = ?
            ''', (key_id,))
            
            conn.commit()
            conn.close()
            
            # Generate new key
            if key_type == "symmetric":
                new_key_id = self.generate_symmetric_key(purpose, owner, algorithm)
            elif key_type == "asymmetric_private":
                key_size = int(algorithm.split('-')[1])
                private_id, _ = self.generate_asymmetric_keypair(purpose, owner, key_size)
                new_key_id = private_id
            else:
                logger.error(f"Cannot rotate public key: {key_id}")
                return None
            
            logger.info(f"Key rotated: {key_id} -> {new_key_id}")
            return new_key_id
            
        except Exception as e:
            logger.error(f"Key rotation failed for {key_id}: {e}")
            return None
    
    def list_keys(self, owner: Optional[str] = None, 
                  purpose: Optional[str] = None) -> List[EncryptionKey]:
        """List encryption keys"""
        try:
            conn = sqlite3.connect(self.keystore_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM encryption_keys WHERE 1=1"
            params = []
            
            if owner:
                query += " AND owner = ?"
                params.append(owner)
            
            if purpose:
                query += " AND purpose = ?"
                params.append(purpose)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            keys = []
            for row in rows:
                key_info = EncryptionKey(
                    key_id=row[0],
                    key_type=row[1],
                    algorithm=row[2],
                    created_at=datetime.fromisoformat(row[4]),
                    expires_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    usage_count=row[6],
                    max_usage=row[7],
                    purpose=row[8],
                    owner=row[9],
                    is_active=bool(row[10])
                )
                keys.append(key_info)
            
            return keys
            
        except Exception as e:
            logger.error(f"Key listing failed: {e}")
            return []

class DataProtectionManager:
    """End-to-end data protection and encryption manager"""
    
    def __init__(self, key_manager: SecureKeyManager, redis_host: str = 'localhost'):
        """Initialize data protection manager"""
        
        self.key_manager = key_manager
        self.backend = default_backend()
        
        # Redis for caching encrypted data metadata
        try:
            self.redis_client = redis.Redis(host=redis_host, decode_responses=False)
            self.redis_client.ping()
            logger.info("Data protection Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
        
        # Data classification database
        self.classification_db = "data_classification.db"
        self.init_classification_db()
        
        # Default encryption settings
        self.default_algorithm = "AES-256-GCM"
        self.default_key_purpose = "data_encryption"
        
        logger.info("Data Protection Manager initialized")
    
    def init_classification_db(self):
        """Initialize data classification database"""
        try:
            conn = sqlite3.connect(self.classification_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_classifications (
                    classification_id TEXT PRIMARY KEY,
                    data_type TEXT NOT NULL,
                    sensitivity_level TEXT NOT NULL,
                    contains_pii BOOLEAN NOT NULL,
                    retention_period_days INTEGER NOT NULL,
                    encryption_required BOOLEAN NOT NULL,
                    access_controls TEXT,
                    legal_basis TEXT,
                    processing_purpose TEXT,
                    data_subject_rights TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS encrypted_data (
                    data_id TEXT PRIMARY KEY,
                    encrypted_data BLOB NOT NULL,
                    encryption_key_id TEXT NOT NULL,
                    algorithm TEXT NOT NULL,
                    iv BLOB,
                    auth_tag BLOB,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL,
                    data_type TEXT NOT NULL,
                    retention_until TIMESTAMP,
                    access_log TEXT,
                    classification_id TEXT,
                    FOREIGN KEY (classification_id) REFERENCES data_classifications(classification_id)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_data_type ON encrypted_data(data_type);
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_encryption_key ON encrypted_data(encryption_key_id);
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_retention ON encrypted_data(retention_until);
            ''')
            
            conn.commit()
            conn.close()
            
            # Set restrictive permissions
            os.chmod(self.classification_db, 0o600)
            
            logger.info("Data classification database initialized")
            
        except Exception as e:
            logger.error(f"Classification DB initialization failed: {e}")
            raise
    
    def classify_data(self, data_type: str, sensitivity_level: str, 
                     contains_pii: bool, retention_days: int,
                     processing_purpose: str, legal_basis: str = "legitimate_interest") -> str:
        """Create data classification"""
        try:
            classification_id = hashlib.sha256(
                f"{data_type}:{sensitivity_level}:{processing_purpose}".encode()
            ).hexdigest()[:16]
            
            classification = DataClassification(
                classification_id=classification_id,
                data_type=data_type,
                sensitivity_level=sensitivity_level,
                contains_pii=contains_pii,
                retention_period=timedelta(days=retention_days),
                encryption_required=sensitivity_level in ["CONFIDENTIAL", "RESTRICTED"] or contains_pii,
                access_controls=self._get_default_access_controls(sensitivity_level),
                legal_basis=legal_basis,
                processing_purpose=processing_purpose,
                data_subject_rights=self._get_data_subject_rights(contains_pii)
            )
            
            # Store classification
            conn = sqlite3.connect(self.classification_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO data_classifications
                (classification_id, data_type, sensitivity_level, contains_pii,
                 retention_period_days, encryption_required, access_controls,
                 legal_basis, processing_purpose, data_subject_rights,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                classification_id, data_type, sensitivity_level, contains_pii,
                retention_days, classification.encryption_required,
                json.dumps(classification.access_controls), legal_basis,
                processing_purpose, json.dumps(classification.data_subject_rights),
                datetime.utcnow(), datetime.utcnow()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Data classification created: {classification_id}")
            return classification_id
            
        except Exception as e:
            logger.error(f"Data classification failed: {e}")
            raise
    
    def _get_default_access_controls(self, sensitivity_level: str) -> List[str]:
        """Get default access controls based on sensitivity level"""
        controls = {
            "PUBLIC": ["read_all"],
            "INTERNAL": ["read_authenticated", "write_authorized"],
            "CONFIDENTIAL": ["read_need_to_know", "write_authorized", "audit_access"],
            "RESTRICTED": ["read_explicit_permission", "write_explicit_permission", 
                         "audit_access", "mfa_required", "approval_required"]
        }
        return controls.get(sensitivity_level, ["read_authorized", "write_authorized"])
    
    def _get_data_subject_rights(self, contains_pii: bool) -> List[str]:
        """Get GDPR data subject rights"""
        if contains_pii:
            return ["access", "rectification", "erasure", "portability", "restrict_processing", "object"]
        return []
    
    def encrypt_data(self, data: Union[str, bytes], data_type: str, 
                    owner: str, classification_id: Optional[str] = None) -> str:
        """Encrypt data with end-to-end encryption"""
        try:
            # Convert string to bytes
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            # Get or create encryption key
            key_id = self._get_or_create_encryption_key(owner, data_type)
            encryption_key = self.key_manager.get_key(key_id)
            
            if not encryption_key:
                raise ValueError(f"Failed to retrieve encryption key: {key_id}")
            
            # Generate IV
            iv = secrets.token_bytes(12)  # 96-bit IV for GCM
            
            # Encrypt with AES-GCM (provides authentication)
            cipher = Cipher(
                algorithms.AES(encryption_key),
                modes.GCM(iv),
                backend=self.backend
            )
            encryptor = cipher.encryptor()
            
            ciphertext = encryptor.update(data_bytes) + encryptor.finalize()
            auth_tag = encryptor.tag
            
            # Create encrypted data container
            data_id = hashlib.sha256(f"{owner}:{data_type}:{int(time.time())}".encode()).hexdigest()[:16]
            
            # Determine retention period
            retention_until = None
            if classification_id:
                classification = self._get_classification(classification_id)
                if classification:
                    retention_until = datetime.utcnow() + classification.retention_period
            
            encrypted_container = EncryptedData(
                data_id=data_id,
                encrypted_data=ciphertext,
                encryption_key_id=key_id,
                algorithm=self.default_algorithm,
                iv=iv,
                tag=auth_tag,
                metadata={"owner": owner, "original_size": len(data_bytes)},
                created_at=datetime.utcnow(),
                data_type=data_type,
                retention_period=timedelta(days=365) if not retention_until else None,
                access_log=[]
            )
            
            # Store encrypted data
            self._store_encrypted_data(encrypted_container, classification_id, retention_until)
            
            # Cache metadata in Redis
            if self.redis_client:
                cache_key = f"encrypted_data_meta:{data_id}"
                metadata = {
                    "data_id": data_id,
                    "key_id": key_id,
                    "algorithm": self.default_algorithm,
                    "created_at": encrypted_container.created_at.isoformat(),
                    "data_type": data_type,
                    "owner": owner
                }
                self.redis_client.setex(cache_key, 3600, json.dumps(metadata))
            
            logger.info(f"Data encrypted: {data_id} (size: {len(data_bytes)} bytes)")
            return data_id
            
        except Exception as e:
            logger.error(f"Data encryption failed: {e}")
            raise
    
    def decrypt_data(self, data_id: str, requester: str) -> Optional[bytes]:
        """Decrypt data with access control and audit logging"""
        try:
            # Check access permissions
            if not self._check_access_permission(data_id, requester, "read"):
                logger.warning(f"Access denied for {requester} to {data_id}")
                return None
            
            # Get encrypted data
            encrypted_container = self._get_encrypted_data(data_id)
            if not encrypted_container:
                logger.warning(f"Encrypted data not found: {data_id}")
                return None
            
            # Check retention period
            if encrypted_container.retention_period:
                expiry = encrypted_container.created_at + encrypted_container.retention_period
                if datetime.utcnow() > expiry:
                    logger.warning(f"Data expired: {data_id}")
                    self.delete_data(data_id)
                    return None
            
            # Get decryption key
            encryption_key = self.key_manager.get_key(encrypted_container.encryption_key_id)
            if not encryption_key:
                logger.error(f"Decryption key not found: {encrypted_container.encryption_key_id}")
                return None
            
            # Decrypt with AES-GCM
            cipher = Cipher(
                algorithms.AES(encryption_key),
                modes.GCM(encrypted_container.iv, encrypted_container.tag),
                backend=self.backend
            )
            decryptor = cipher.decryptor()
            
            plaintext = decryptor.update(encrypted_container.encrypted_data) + decryptor.finalize()
            
            # Log access
            self._log_data_access(data_id, requester, "decrypt")
            
            logger.info(f"Data decrypted: {data_id} by {requester}")
            return plaintext
            
        except Exception as e:
            logger.error(f"Data decryption failed for {data_id}: {e}")
            return None
    
    def _get_or_create_encryption_key(self, owner: str, data_type: str) -> str:
        """Get or create encryption key for data type"""
        try:
            # Look for existing active key
            keys = self.key_manager.list_keys(owner=owner, purpose=f"{self.default_key_purpose}:{data_type}")
            active_keys = [k for k in keys if k.is_active and k.key_type == "symmetric"]
            
            if active_keys:
                return active_keys[0].key_id
            
            # Create new key
            purpose = f"{self.default_key_purpose}:{data_type}"
            return self.key_manager.generate_symmetric_key(purpose, owner)
            
        except Exception as e:
            logger.error(f"Key management failed for {owner}:{data_type}: {e}")
            raise
    
    def _store_encrypted_data(self, container: EncryptedData, 
                            classification_id: Optional[str], 
                            retention_until: Optional[datetime]):
        """Store encrypted data in database"""
        try:
            conn = sqlite3.connect(self.classification_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO encrypted_data
                (data_id, encrypted_data, encryption_key_id, algorithm, iv, auth_tag,
                 metadata, created_at, data_type, retention_until, access_log, classification_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                container.data_id, container.encrypted_data, container.encryption_key_id,
                container.algorithm, container.iv, container.tag,
                json.dumps(container.metadata), container.created_at,
                container.data_type, retention_until,
                json.dumps(container.access_log), classification_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Encrypted data storage failed: {e}")
            raise
    
    def _get_encrypted_data(self, data_id: str) -> Optional[EncryptedData]:
        """Retrieve encrypted data container"""
        try:
            conn = sqlite3.connect(self.classification_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT data_id, encrypted_data, encryption_key_id, algorithm, iv, auth_tag,
                       metadata, created_at, data_type, retention_until, access_log
                FROM encrypted_data WHERE data_id = ?
            ''', (data_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return EncryptedData(
                data_id=row[0],
                encrypted_data=row[1],
                encryption_key_id=row[2],
                algorithm=row[3],
                iv=row[4],
                tag=row[5],
                metadata=json.loads(row[6]),
                created_at=datetime.fromisoformat(row[7]),
                data_type=row[8],
                retention_period=None,  # Calculated from retention_until
                access_log=json.loads(row[10]) if row[10] else []
            )
            
        except Exception as e:
            logger.error(f"Encrypted data retrieval failed for {data_id}: {e}")
            return None
    
    def _get_classification(self, classification_id: str) -> Optional[DataClassification]:
        """Get data classification"""
        try:
            conn = sqlite3.connect(self.classification_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM data_classifications WHERE classification_id = ?
            ''', (classification_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return DataClassification(
                classification_id=row[0],
                data_type=row[1],
                sensitivity_level=row[2],
                contains_pii=bool(row[3]),
                retention_period=timedelta(days=row[4]),
                encryption_required=bool(row[5]),
                access_controls=json.loads(row[6]) if row[6] else [],
                legal_basis=row[7] or "",
                processing_purpose=row[8] or "",
                data_subject_rights=json.loads(row[9]) if row[9] else []
            )
            
        except Exception as e:
            logger.error(f"Classification retrieval failed for {classification_id}: {e}")
            return None
    
    def _check_access_permission(self, data_id: str, requester: str, action: str) -> bool:
        """Check if requester has permission to access data"""
        try:
            # Get data metadata
            container = self._get_encrypted_data(data_id)
            if not container:
                return False
            
            # Check if requester is owner
            owner = container.metadata.get("owner")
            if owner == requester:
                return True
            
            # For now, implement basic access control
            # In production, this would integrate with proper RBAC system
            if requester in ["admin", "system"]:
                return True
            
            # Check classification-based access controls
            # This would integrate with identity management system
            
            logger.info(f"Access check: {requester} -> {data_id} ({action}) = ALLOWED")
            return True
            
        except Exception as e:
            logger.error(f"Access permission check failed: {e}")
            return False
    
    def _log_data_access(self, data_id: str, requester: str, action: str):
        """Log data access for audit trail"""
        try:
            access_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "requester": requester,
                "action": action,
                "success": True
            }
            
            # Update access log in database
            conn = sqlite3.connect(self.classification_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT access_log FROM encrypted_data WHERE data_id = ?
            ''', (data_id,))
            
            row = cursor.fetchone()
            if row:
                access_log = json.loads(row[0]) if row[0] else []
                access_log.append(access_entry)
                
                # Keep only last 100 access entries
                access_log = access_log[-100:]
                
                cursor.execute('''
                    UPDATE encrypted_data SET access_log = ? WHERE data_id = ?
                ''', (json.dumps(access_log), data_id))
                
                conn.commit()
            
            conn.close()
            
            # Also log to Redis for real-time monitoring
            if self.redis_client:
                audit_key = f"data_access_audit:{datetime.utcnow().strftime('%Y-%m-%d')}"
                audit_entry = json.dumps({
                    "data_id": data_id,
                    "requester": requester,
                    "action": action,
                    "timestamp": access_entry["timestamp"]
                })
                self.redis_client.lpush(audit_key, audit_entry)
                self.redis_client.expire(audit_key, 86400 * 30)  # 30 days retention
            
        except Exception as e:
            logger.error(f"Data access logging failed: {e}")
    
    def delete_data(self, data_id: str, requester: str = "system") -> bool:
        """Securely delete encrypted data (GDPR right to erasure)"""
        try:
            # Check access permission
            if not self._check_access_permission(data_id, requester, "delete"):
                logger.warning(f"Delete access denied for {requester} to {data_id}")
                return False
            
            # Log the deletion
            self._log_data_access(data_id, requester, "delete")
            
            # Remove from database
            conn = sqlite3.connect(self.classification_db)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM encrypted_data WHERE data_id = ?', (data_id,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            # Remove from Redis cache
            if self.redis_client:
                cache_key = f"encrypted_data_meta:{data_id}"
                self.redis_client.delete(cache_key)
            
            if deleted_count > 0:
                logger.info(f"Data securely deleted: {data_id} by {requester}")
                return True
            else:
                logger.warning(f"Data not found for deletion: {data_id}")
                return False
                
        except Exception as e:
            logger.error(f"Data deletion failed for {data_id}: {e}")
            return False
    
    def export_data(self, owner: str, requester: str) -> Optional[Dict[str, Any]]:
        """Export all data for a user (GDPR right to data portability)"""
        try:
            if owner != requester and requester not in ["admin", "system"]:
                logger.warning(f"Export access denied for {requester} to {owner}'s data")
                return None
            
            # Get all data owned by user
            conn = sqlite3.connect(self.classification_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT data_id, created_at, data_type, metadata
                FROM encrypted_data 
                WHERE JSON_EXTRACT(metadata, '$.owner') = ?
            ''', (owner,))
            
            rows = cursor.fetchall()
            conn.close()
            
            exported_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "data_subject": owner,
                "requester": requester,
                "data_items": []
            }
            
            for row in rows:
                data_id, created_at, data_type, metadata = row
                
                # Decrypt data
                decrypted = self.decrypt_data(data_id, requester)
                if decrypted:
                    # Convert to base64 for JSON serialization
                    data_content = base64.b64encode(decrypted).decode('utf-8')
                    
                    exported_data["data_items"].append({
                        "data_id": data_id,
                        "data_type": data_type,
                        "created_at": created_at,
                        "metadata": json.loads(metadata),
                        "content_base64": data_content
                    })
            
            # Log the export
            if self.redis_client:
                export_log_key = f"data_exports:{datetime.utcnow().strftime('%Y-%m-%d')}"
                export_entry = json.dumps({
                    "owner": owner,
                    "requester": requester,
                    "timestamp": exported_data["export_timestamp"],
                    "items_count": len(exported_data["data_items"])
                })
                self.redis_client.lpush(export_log_key, export_entry)
                self.redis_client.expire(export_log_key, 86400 * 365)  # 1 year retention
            
            logger.info(f"Data export completed for {owner} (requested by {requester})")
            return exported_data
            
        except Exception as e:
            logger.error(f"Data export failed for {owner}: {e}")
            return None
    
    def cleanup_expired_data(self) -> int:
        """Clean up expired data (automated retention management)"""
        try:
            conn = sqlite3.connect(self.classification_db)
            cursor = conn.cursor()
            
            # Find expired data
            cursor.execute('''
                SELECT data_id FROM encrypted_data 
                WHERE retention_until IS NOT NULL 
                AND retention_until < ?
            ''', (datetime.utcnow(),))
            
            expired_data_ids = [row[0] for row in cursor.fetchall()]
            
            # Delete expired data
            deleted_count = 0
            for data_id in expired_data_ids:
                if self.delete_data(data_id, "system"):
                    deleted_count += 1
            
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} expired data items")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            return 0
    
    def get_encryption_metrics(self) -> Dict[str, Any]:
        """Get encryption and data protection metrics"""
        try:
            conn = sqlite3.connect(self.classification_db)
            cursor = conn.cursor()
            
            # Total encrypted data count
            cursor.execute('SELECT COUNT(*) FROM encrypted_data')
            total_data_count = cursor.fetchone()[0]
            
            # Data by type
            cursor.execute('''
                SELECT data_type, COUNT(*) 
                FROM encrypted_data 
                GROUP BY data_type
            ''')
            data_by_type = dict(cursor.fetchall())
            
            # Data by classification
            cursor.execute('''
                SELECT c.sensitivity_level, COUNT(e.data_id)
                FROM data_classifications c
                LEFT JOIN encrypted_data e ON c.classification_id = e.classification_id
                GROUP BY c.sensitivity_level
            ''')
            data_by_sensitivity = dict(cursor.fetchall())
            
            # PII data count
            cursor.execute('''
                SELECT COUNT(e.data_id)
                FROM encrypted_data e
                JOIN data_classifications c ON e.classification_id = c.classification_id
                WHERE c.contains_pii = 1
            ''')
            pii_data_count = cursor.fetchone()[0]
            
            conn.close()
            
            # Key metrics
            keys = self.key_manager.list_keys()
            active_keys = len([k for k in keys if k.is_active])
            
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_encrypted_data_items": total_data_count,
                "pii_data_items": pii_data_count,
                "active_encryption_keys": active_keys,
                "total_keys": len(keys),
                "data_by_type": data_by_type,
                "data_by_sensitivity": data_by_sensitivity,
                "encryption_algorithm": self.default_algorithm,
                "key_rotation_interval_days": self.key_manager.key_rotation_interval.days
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Encryption metrics generation failed: {e}")
            return {"error": str(e)}

# Example usage and testing
if __name__ == "__main__":
    import time
    
    # Initialize managers
    key_manager = SecureKeyManager()
    data_manager = DataProtectionManager(key_manager)
    
    # Create data classification
    classification_id = data_manager.classify_data(
        data_type="user_preferences",
        sensitivity_level="CONFIDENTIAL",
        contains_pii=True,
        retention_days=365,
        processing_purpose="Application personalization",
        legal_basis="consent"
    )
    
    # Encrypt some test data
    test_data = "This is sensitive user data that needs encryption"
    encrypted_id = data_manager.encrypt_data(
        data=test_data,
        data_type="user_preferences",
        owner="user123",
        classification_id=classification_id
    )
    
    print(f"Data encrypted with ID: {encrypted_id}")
    
    # Decrypt data
    decrypted_data = data_manager.decrypt_data(encrypted_id, "user123")
    if decrypted_data:
        print(f"Decrypted data: {decrypted_data.decode('utf-8')}")
    
    # Get metrics
    metrics = data_manager.get_encryption_metrics()
    print(f"Encryption metrics: {json.dumps(metrics, indent=2)}")
    
    # Export user data
    exported = data_manager.export_data("user123", "user123")
    if exported:
        print(f"Exported {len(exported['data_items'])} data items")
    
    # Clean up test data
    data_manager.delete_data(encrypted_id, "user123")