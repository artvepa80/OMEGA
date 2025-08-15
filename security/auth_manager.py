"""
OMEGA PRO AI v10.1 - Authentication & Access Control Manager
Multi-factor authentication and role-based access control system
"""

import os
import json
import hashlib
import secrets
import pyotp
import qrcode
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import bcrypt
import jwt
import logging
import time

class UserRole(Enum):
    """User roles with different permission levels"""
    READ_ONLY = "read_only"
    ANALYST = "analyst"
    ADMIN = "admin"
    SYSTEM = "system"

class AuthenticationMethod(Enum):
    """Authentication methods"""
    PASSWORD = "password"
    TOTP = "totp"
    HARDWARE_TOKEN = "hardware_token"
    BIOMETRIC = "biometric"

@dataclass
class User:
    """User data structure"""
    username: str
    email: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    mfa_enabled: bool = True
    mfa_methods: List[AuthenticationMethod] = None
    totp_secret: Optional[str] = None
    session_tokens: List[str] = None
    
    def __post_init__(self):
        if self.mfa_methods is None:
            self.mfa_methods = [AuthenticationMethod.PASSWORD, AuthenticationMethod.TOTP]
        if self.session_tokens is None:
            self.session_tokens = []

@dataclass
class Session:
    """User session data structure"""
    token: str
    username: str
    role: UserRole
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True

class AuthManager:
    """Manages authentication and access control"""
    
    def __init__(self, config_path: str = None):
        """Initialize authentication manager"""
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        self.users_db = self._load_users_database()
        self.sessions = {}
        self.jwt_secret = self._load_jwt_secret()
        self.failed_attempts = {}
        self.role_permissions = self._setup_role_permissions()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup secure logging for authentication"""
        logger = logging.getLogger('AuthManager')
        logger.setLevel(logging.INFO)
        
        os.makedirs('security/logs', exist_ok=True)
        handler = logging.FileHandler(
            'security/logs/auth_audit.log',
            mode='a'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s - User:%(username)s - IP:%(ip)s',
            defaults={'username': 'unknown', 'ip': 'unknown'}
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load authentication configuration"""
        default_path = 'security/security_config.json'
        path = config_path or default_path
        
        try:
            with open(path, 'r') as f:
                config = json.load(f)
            return config.get('database_security', {}).get('authentication', {})
        except Exception as e:
            self.logger.error(f"Failed to load auth config: {e}")
            return self._get_default_auth_config()
    
    def _get_default_auth_config(self) -> Dict[str, Any]:
        """Default authentication configuration"""
        return {
            "multi_factor": {
                "enabled": True,
                "required_factors": 2
            },
            "session_management": {
                "max_session_duration": 3600,
                "idle_timeout": 900,
                "concurrent_sessions_limit": 3
            }
        }
    
    def _load_users_database(self) -> Dict[str, User]:
        """Load users database"""
        db_path = 'security/users.json'
        
        if os.path.exists(db_path):
            try:
                with open(db_path, 'r') as f:
                    users_data = json.load(f)
                
                users = {}
                for username, data in users_data.items():
                    # Convert string dates back to datetime
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                    if data.get('last_login'):
                        data['last_login'] = datetime.fromisoformat(data['last_login'])
                    if data.get('locked_until'):
                        data['locked_until'] = datetime.fromisoformat(data['locked_until'])
                    
                    # Convert role string to enum
                    data['role'] = UserRole(data['role'])
                    
                    # Convert mfa_methods strings to enums
                    data['mfa_methods'] = [AuthenticationMethod(method) for method in data.get('mfa_methods', [])]
                    
                    users[username] = User(**data)
                
                return users
                
            except Exception as e:
                self.logger.error(f"Failed to load users database: {e}")
                return self._create_default_admin()
        else:
            return self._create_default_admin()
    
    def _create_default_admin(self) -> Dict[str, User]:
        """Create default admin user"""
        admin_user = User(
            username="admin",
            email="admin@omega.ai",
            role=UserRole.SYSTEM,
            created_at=datetime.utcnow(),
            mfa_enabled=True,
            totp_secret=pyotp.random_base32()
        )
        
        users = {"admin": admin_user}
        self._save_users_database(users)
        
        self.logger.info("Default admin user created")
        return users
    
    def _save_users_database(self, users: Dict[str, User] = None) -> None:
        """Save users database"""
        if users is None:
            users = self.users_db
        
        try:
            # Convert users to serializable format
            users_data = {}
            for username, user in users.items():
                user_dict = asdict(user)
                # Convert datetime objects to ISO strings
                user_dict['created_at'] = user.created_at.isoformat()
                if user.last_login:
                    user_dict['last_login'] = user.last_login.isoformat()
                if user.locked_until:
                    user_dict['locked_until'] = user.locked_until.isoformat()
                
                # Convert enums to strings
                user_dict['role'] = user.role.value
                user_dict['mfa_methods'] = [method.value for method in user.mfa_methods]
                
                users_data[username] = user_dict
            
            os.makedirs('security', exist_ok=True)
            with open('security/users.json', 'w') as f:
                json.dump(users_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save users database: {e}")
    
    def _load_jwt_secret(self) -> str:
        """Load or generate JWT secret"""
        secret_file = 'security/jwt_secret.key'
        
        if os.path.exists(secret_file):
            try:
                with open(secret_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                self.logger.error(f"Failed to load JWT secret: {e}")
        
        # Generate new secret
        secret = secrets.token_urlsafe(64)
        
        try:
            os.makedirs('security', exist_ok=True)
            with open(secret_file, 'w') as f:
                f.write(secret)
            os.chmod(secret_file, 0o600)
            
            self.logger.info("New JWT secret generated")
        except Exception as e:
            self.logger.error(f"Failed to save JWT secret: {e}")
        
        return secret
    
    def _setup_role_permissions(self) -> Dict[UserRole, List[str]]:
        """Setup role-based permissions"""
        return {
            UserRole.READ_ONLY: [
                "read_data",
                "view_predictions",
                "view_reports"
            ],
            UserRole.ANALYST: [
                "read_data",
                "write_data",
                "view_predictions",
                "create_predictions",
                "view_reports",
                "create_reports"
            ],
            UserRole.ADMIN: [
                "read_data",
                "write_data",
                "delete_data",
                "view_predictions",
                "create_predictions",
                "view_reports",
                "create_reports",
                "manage_users",
                "view_logs"
            ],
            UserRole.SYSTEM: [
                "all_permissions"
            ]
        }
    
    def create_user(self, username: str, email: str, role: UserRole,
                   password: str) -> Tuple[bool, str]:
        """Create new user account"""
        try:
            if username in self.users_db:
                return False, "User already exists"
            
            # Generate TOTP secret
            totp_secret = pyotp.random_base32()
            
            # Create user
            user = User(
                username=username,
                email=email,
                role=role,
                created_at=datetime.utcnow(),
                totp_secret=totp_secret
            )
            
            # Hash and store password separately (not in user object)
            self._store_password(username, password)
            
            # Add to database
            self.users_db[username] = user
            self._save_users_database()
            
            self.logger.info(f"User created: {username}", 
                           extra={'username': username, 'ip': 'system'})
            
            return True, f"User created successfully. TOTP secret: {totp_secret}"
            
        except Exception as e:
            self.logger.error(f"User creation failed: {e}")
            return False, str(e)
    
    def authenticate_user(self, username: str, password: str,
                         totp_code: str = None, ip_address: str = "unknown",
                         user_agent: str = "unknown") -> Tuple[bool, Optional[str], str]:
        """Authenticate user with multi-factor authentication"""
        try:
            # Check if user exists
            if username not in self.users_db:
                self.logger.warning(f"Authentication failed: User not found: {username}",
                                  extra={'username': username, 'ip': ip_address})
                return False, None, "Invalid credentials"
            
            user = self.users_db[username]
            
            # Check if account is locked
            if self._is_account_locked(username):
                self.logger.warning(f"Authentication failed: Account locked: {username}",
                                  extra={'username': username, 'ip': ip_address})
                return False, None, "Account temporarily locked"
            
            # First factor: Password
            if not self._verify_password(username, password):
                self._record_failed_attempt(username)
                self.logger.warning(f"Authentication failed: Invalid password: {username}",
                                  extra={'username': username, 'ip': ip_address})
                return False, None, "Invalid credentials"
            
            # Second factor: TOTP (if enabled)
            if user.mfa_enabled and AuthenticationMethod.TOTP in user.mfa_methods:
                if not totp_code:
                    return False, None, "TOTP code required"
                
                if not self._verify_totp(username, totp_code):
                    self._record_failed_attempt(username)
                    self.logger.warning(f"Authentication failed: Invalid TOTP: {username}",
                                      extra={'username': username, 'ip': ip_address})
                    return False, None, "Invalid TOTP code"
            
            # Authentication successful
            self._reset_failed_attempts(username)
            user.last_login = datetime.utcnow()
            self._save_users_database()
            
            # Create session
            session_token = self._create_session(user, ip_address, user_agent)
            
            self.logger.info(f"Authentication successful: {username}",
                           extra={'username': username, 'ip': ip_address})
            
            return True, session_token, "Authentication successful"
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False, None, "Authentication error"
    
    def _verify_password(self, username: str, password: str) -> bool:
        """Verify user password"""
        try:
            password_file = f'security/passwords/{username}.hash'
            
            if not os.path.exists(password_file):
                return False
            
            with open(password_file, 'rb') as f:
                stored_hash = f.read()
            
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
            
        except Exception as e:
            self.logger.error(f"Password verification failed: {e}")
            return False
    
    def _store_password(self, username: str, password: str) -> None:
        """Store hashed password"""
        try:
            os.makedirs('security/passwords', exist_ok=True)
            
            # Hash password with bcrypt
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            password_file = f'security/passwords/{username}.hash'
            with open(password_file, 'wb') as f:
                f.write(hashed)
            
            os.chmod(password_file, 0o600)
            
        except Exception as e:
            self.logger.error(f"Password storage failed: {e}")
            raise
    
    def _verify_totp(self, username: str, totp_code: str) -> bool:
        """Verify TOTP code"""
        try:
            user = self.users_db[username]
            if not user.totp_secret:
                return False
            
            totp = pyotp.TOTP(user.totp_secret)
            return totp.verify(totp_code, valid_window=1)
            
        except Exception as e:
            self.logger.error(f"TOTP verification failed: {e}")
            return False
    
    def generate_totp_qr(self, username: str) -> Optional[str]:
        """Generate QR code for TOTP setup"""
        try:
            user = self.users_db[username]
            if not user.totp_secret:
                return None
            
            # Create TOTP URI
            totp = pyotp.TOTP(user.totp_secret)
            provisioning_uri = totp.provisioning_uri(
                user.email,
                issuer_name="OMEGA PRO AI"
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # Save QR code image
            os.makedirs('security/qr_codes', exist_ok=True)
            qr_path = f'security/qr_codes/{username}_totp.png'
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(qr_path)
            
            return qr_path
            
        except Exception as e:
            self.logger.error(f"QR generation failed: {e}")
            return None
    
    def _create_session(self, user: User, ip_address: str, user_agent: str) -> str:
        """Create user session with JWT token"""
        try:
            # Check concurrent session limit
            active_sessions = [s for s in self.sessions.values() 
                             if s.username == user.username and s.is_active]
            
            session_limit = self.config.get('session_management', {}).get('concurrent_sessions_limit', 3)
            
            if len(active_sessions) >= session_limit:
                # Deactivate oldest session
                oldest_session = min(active_sessions, key=lambda s: s.created_at)
                oldest_session.is_active = False
            
            # Create session token
            session_duration = self.config.get('session_management', {}).get('max_session_duration', 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=session_duration)
            
            payload = {
                'username': user.username,
                'role': user.role.value,
                'exp': expires_at.timestamp(),
                'iat': datetime.utcnow().timestamp(),
                'ip': ip_address
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            
            # Store session
            session = Session(
                token=token,
                username=user.username,
                role=user.role,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.sessions[token] = session
            user.session_tokens.append(token)
            
            return token
            
        except Exception as e:
            self.logger.error(f"Session creation failed: {e}")
            raise
    
    def validate_session(self, token: str, ip_address: str = None) -> Tuple[bool, Optional[Session], str]:
        """Validate session token"""
        try:
            if token not in self.sessions:
                return False, None, "Invalid session"
            
            session = self.sessions[token]
            
            # Check if session is active
            if not session.is_active:
                return False, None, "Session deactivated"
            
            # Check if session expired
            if datetime.utcnow() > session.expires_at:
                session.is_active = False
                return False, None, "Session expired"
            
            # Check idle timeout
            idle_timeout = self.config.get('session_management', {}).get('idle_timeout', 900)
            if (datetime.utcnow() - session.last_activity).total_seconds() > idle_timeout:
                session.is_active = False
                return False, None, "Session timed out due to inactivity"
            
            # Verify JWT token
            try:
                jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                session.is_active = False
                return False, None, "Token expired"
            except jwt.InvalidTokenError:
                session.is_active = False
                return False, None, "Invalid token"
            
            # Check IP consistency (if provided)
            if ip_address and session.ip_address != ip_address:
                self.logger.warning(f"IP mismatch for session: {session.username}")
                # Optionally invalidate session on IP mismatch
                # session.is_active = False
                # return False, None, "IP address mismatch"
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            
            return True, session, "Valid session"
            
        except Exception as e:
            self.logger.error(f"Session validation failed: {e}")
            return False, None, "Session validation error"
    
    def check_permission(self, username: str, permission: str) -> bool:
        """Check if user has specific permission"""
        try:
            if username not in self.users_db:
                return False
            
            user = self.users_db[username]
            user_permissions = self.role_permissions.get(user.role, [])
            
            return "all_permissions" in user_permissions or permission in user_permissions
            
        except Exception as e:
            self.logger.error(f"Permission check failed: {e}")
            return False
    
    def _is_account_locked(self, username: str) -> bool:
        """Check if account is temporarily locked"""
        user = self.users_db.get(username)
        if not user:
            return False
        
        if user.locked_until and datetime.utcnow() < user.locked_until:
            return True
        
        return False
    
    def _record_failed_attempt(self, username: str) -> None:
        """Record failed authentication attempt"""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []
        
        self.failed_attempts[username].append(datetime.utcnow())
        
        # Lock account after 5 failed attempts
        recent_failures = [
            attempt for attempt in self.failed_attempts[username]
            if (datetime.utcnow() - attempt).total_seconds() < 900  # 15 minutes
        ]
        
        if len(recent_failures) >= 5:
            user = self.users_db[username]
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            self._save_users_database()
            
            self.logger.warning(f"Account locked due to failed attempts: {username}")
    
    def _reset_failed_attempts(self, username: str) -> None:
        """Reset failed attempts counter"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]
        
        user = self.users_db[username]
        user.locked_until = None
        user.failed_attempts = 0
    
    def logout_user(self, token: str) -> bool:
        """Logout user and invalidate session"""
        try:
            if token in self.sessions:
                session = self.sessions[token]
                session.is_active = False
                
                # Remove from user's session list
                user = self.users_db.get(session.username)
                if user and token in user.session_tokens:
                    user.session_tokens.remove(token)
                
                self.logger.info(f"User logged out: {session.username}",
                               extra={'username': session.username, 'ip': session.ip_address})
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Logout failed: {e}")
            return False
    
    def get_user_sessions(self, username: str) -> List[Session]:
        """Get all active sessions for user"""
        return [
            session for session in self.sessions.values()
            if session.username == username and session.is_active
        ]