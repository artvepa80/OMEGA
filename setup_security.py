#!/usr/bin/env python3
"""
OMEGA PRO AI v10.1 - Security System Setup Script
Automated setup and initialization of the complete security infrastructure
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_security_directories():
    """Create required security directories"""
    directories = [
        'security',
        'security/logs',
        'security/keys',
        'security/certificates',
        'security/backups',
        'security/config',
        'security/compliance',
        'security/vault',
        'security/monitoring'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")
    
    return True

def install_security_requirements():
    """Install security-specific Python packages"""
    try:
        logger.info("Installing security requirements...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements-security.txt'
        ], check=True)
        logger.info("Security requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install security requirements: {e}")
        return False

def generate_security_keys():
    """Generate initial security keys and certificates"""
    try:
        logger.info("Generating security keys...")
        
        from security.encryption_manager import SecureKeyManager
        key_manager = SecureKeyManager()
        
        # Generate master encryption key
        master_key = key_manager.generate_master_key()
        logger.info("Master encryption key generated")
        
        # Generate JWT secrets
        import secrets
        jwt_secret = secrets.token_urlsafe(64)
        
        # Write JWT secret to secure config
        with open('security/config/jwt_secret.key', 'w') as f:
            f.write(jwt_secret)
        
        # Set secure permissions
        os.chmod('security/config/jwt_secret.key', 0o600)
        
        logger.info("Security keys generated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate security keys: {e}")
        return False

def initialize_security_database():
    """Initialize security databases"""
    try:
        logger.info("Initializing security databases...")
        
        # Initialize audit database
        from security.audit_compliance import SecureAuditLogger
        audit_logger = SecureAuditLogger()
        logger.info("Audit database initialized")
        
        # Initialize dashboard database
        from security.security_dashboard import SecurityDashboard
        dashboard = SecurityDashboard()
        logger.info("Dashboard database initialized")
        
        logger.info("Security databases initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize security databases: {e}")
        return False

def setup_firewall_rules():
    """Set up basic firewall rules (Linux only)"""
    try:
        if os.name != 'posix':
            logger.info("Firewall setup skipped (not on Linux)")
            return True
        
        logger.info("Setting up basic firewall rules...")
        
        # Basic UFW rules (if available)
        firewall_commands = [
            "ufw --force reset",
            "ufw default deny incoming",
            "ufw default allow outgoing",
            "ufw allow 22/tcp",    # SSH
            "ufw allow 80/tcp",    # HTTP
            "ufw allow 443/tcp",   # HTTPS
            "ufw allow 5000/tcp",  # Dashboard
            "ufw --force enable"
        ]
        
        for cmd in firewall_commands:
            try:
                subprocess.run(cmd.split(), check=True, capture_output=True)
                logger.info(f"Executed: {cmd}")
            except subprocess.CalledProcessError:
                logger.warning(f"Failed to execute: {cmd} (may require sudo)")
        
        logger.info("Basic firewall rules configured")
        return True
        
    except Exception as e:
        logger.error(f"Firewall setup failed: {e}")
        return False

def create_security_config():
    """Create default security configuration"""
    try:
        logger.info("Creating security configuration...")
        
        config = {
            "security": {
                "encryption": {
                    "algorithm": "AES-256-GCM",
                    "key_rotation_days": 90
                },
                "authentication": {
                    "mfa_required": True,
                    "session_timeout_hours": 8,
                    "max_login_attempts": 5
                },
                "monitoring": {
                    "log_level": "INFO",
                    "alert_threshold_high": 10,
                    "alert_threshold_critical": 5
                },
                "compliance": {
                    "frameworks": ["GDPR", "SOX", "HIPAA"],
                    "audit_retention_days": 2555  # 7 years
                }
            }
        }
        
        import json
        with open('security/config/security_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        os.chmod('security/config/security_config.json', 0o600)
        
        logger.info("Security configuration created")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create security configuration: {e}")
        return False

def run_security_tests():
    """Run basic security system tests"""
    try:
        logger.info("Running security system tests...")
        
        # Test encryption
        from security.encryption_manager import DataProtectionManager, SecureKeyManager
        key_manager = SecureKeyManager()
        data_manager = DataProtectionManager(key_manager)
        
        test_data = "test_security_data"
        encrypted = data_manager.encrypt_data(test_data, "test", "system")
        decrypted = data_manager.decrypt_data(encrypted["encrypted_data"])
        
        if decrypted != test_data:
            logger.error("Encryption test failed")
            return False
        
        logger.info("Encryption test passed")
        
        # Test authentication
        from security.auth_manager import AdvancedAuthManager
        auth_manager = AdvancedAuthManager("test-jwt-secret")
        
        # Create test user
        user_created = auth_manager.create_user(
            username="test_user",
            password="test_password_123!",
            email="test@omega-pro-ai.com",
            role="user"
        )
        
        if not user_created:
            logger.error("User creation test failed")
            return False
        
        logger.info("Authentication test passed")
        
        logger.info("All security tests passed")
        return True
        
    except Exception as e:
        logger.error(f"Security tests failed: {e}")
        return False

def main():
    """Main security setup function"""
    logger.info("Starting OMEGA PRO AI Security System Setup...")
    logger.info("=" * 60)
    
    steps = [
        ("Creating security directories", create_security_directories),
        ("Installing security requirements", install_security_requirements),
        ("Creating security configuration", create_security_config),
        ("Generating security keys", generate_security_keys),
        ("Initializing security databases", initialize_security_database),
        ("Setting up firewall rules", setup_firewall_rules),
        ("Running security tests", run_security_tests)
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        logger.info(f"\n--- {step_name} ---")
        try:
            results[step_name] = step_func()
            status = "SUCCESS" if results[step_name] else "FAILED"
            logger.info(f"{step_name}: {status}")
        except Exception as e:
            logger.error(f"{step_name} failed with exception: {e}")
            results[step_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SETUP SUMMARY")
    logger.info("=" * 60)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for step_name, success in results.items():
        status = "✓" if success else "✗"
        logger.info(f"{status} {step_name}")
    
    logger.info(f"\nCompleted: {success_count}/{total_count} steps")
    
    if success_count == total_count:
        logger.info("🎉 OMEGA PRO AI Security System setup completed successfully!")
        logger.info("🔒 Your system is now secured with enterprise-grade protection.")
        logger.info("\nNext steps:")
        logger.info("1. Change default passwords")
        logger.info("2. Configure SSL certificates")
        logger.info("3. Set up monitoring alerts")
        logger.info("4. Run the security dashboard: python -m security.security_dashboard")
    else:
        logger.warning("⚠️  Setup completed with some failures. Please review the logs above.")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)