#!/usr/bin/env python3
"""
OMEGA AI Security Audit Suite
Security Auditor Specialist Implementation
"""

import requests
import json
import hashlib
import jwt
import re
import ssl
import socket
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import subprocess
import os
import secrets
import base64
from cryptography.fernet import Fernet
from pathlib import Path
import yaml

@dataclass
class SecurityVulnerability:
    """Security vulnerability data structure"""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # Authentication, Authorization, Data Protection, etc.
    description: str
    location: str  # File/endpoint location
    recommendation: str
    cve_reference: Optional[str] = None
    exploitable: bool = False

class OmegaSecurityAuditor:
    """Comprehensive security audit for OMEGA AI system"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url
        self.vulnerabilities: List[SecurityVulnerability] = []
        self.api_endpoints = []
        self.security_headers = {}
        self.auth_mechanisms = []
        
    def audit_api_endpoints(self) -> List[SecurityVulnerability]:
        """Comprehensive API endpoint security audit"""
        print("🔒 Auditing API Endpoints...")
        
        vulnerabilities = []
        
        # Discover API endpoints from code
        api_files = [
            "api_simple.py", "api_interface.py", "api_interface_railway.py",
            "main.py", "minimal_api.py"
        ]
        
        for api_file in api_files:
            if os.path.exists(api_file):
                vulnerabilities.extend(self._audit_api_file(api_file))
        
        # Test deployed endpoints if base_url provided
        if self.base_url:
            vulnerabilities.extend(self._test_live_endpoints())
        
        return vulnerabilities
    
    def _audit_api_file(self, filepath: str) -> List[SecurityVulnerability]:
        """Audit individual API file for security issues"""
        vulnerabilities = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for authentication issues
            if not re.search(r'@auth|@login_required|authenticate|verify_token', content):
                vulnerabilities.append(SecurityVulnerability(
                    severity="HIGH",
                    category="Authentication",
                    description="No authentication mechanisms found in API endpoints",
                    location=f"{filepath}",
                    recommendation="Implement JWT or API key authentication for all endpoints",
                    exploitable=True
                ))
            
            # Check for CORS configuration
            if not re.search(r'CORS|Cross-Origin|cors', content, re.IGNORECASE):
                vulnerabilities.append(SecurityVulnerability(
                    severity="MEDIUM",
                    category="CORS",
                    description="No CORS configuration found",
                    location=f"{filepath}",
                    recommendation="Configure proper CORS headers to prevent unauthorized cross-origin requests"
                ))
            
            # Check for input validation
            if re.search(r'request\.(json|form|args)\[', content) and not re.search(r'validate|sanitize|escape', content):
                vulnerabilities.append(SecurityVulnerability(
                    severity="HIGH",
                    category="Input Validation",
                    description="Direct use of user input without validation detected",
                    location=f"{filepath}",
                    recommendation="Implement input validation and sanitization for all user inputs",
                    exploitable=True
                ))
            
            # Check for SQL injection vulnerabilities
            if re.search(r'execute\(.*%.*\)|query\(.*\+.*\)', content):
                vulnerabilities.append(SecurityVulnerability(
                    severity="CRITICAL",
                    category="SQL Injection",
                    description="Potential SQL injection vulnerability found",
                    location=f"{filepath}",
                    recommendation="Use parameterized queries and prepared statements",
                    cve_reference="CWE-89",
                    exploitable=True
                ))
            
            # Check for hardcoded secrets
            secret_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ]
            
            for pattern in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    vulnerabilities.append(SecurityVulnerability(
                        severity="CRITICAL",
                        category="Credentials",
                        description="Hardcoded credentials found in source code",
                        location=f"{filepath}",
                        recommendation="Move all credentials to environment variables or secure vaults",
                        exploitable=True
                    ))
            
            # Check for debug mode
            if re.search(r'debug\s*=\s*True|DEBUG\s*=\s*True', content, re.IGNORECASE):
                vulnerabilities.append(SecurityVulnerability(
                    severity="HIGH",
                    category="Configuration",
                    description="Debug mode enabled in production code",
                    location=f"{filepath}",
                    recommendation="Disable debug mode in production environments"
                ))
            
            # Check for error information leakage
            if re.search(r'traceback|exception.*print|error.*print', content, re.IGNORECASE):
                vulnerabilities.append(SecurityVulnerability(
                    severity="MEDIUM",
                    category="Information Disclosure",
                    description="Potential error information leakage",
                    location=f"{filepath}",
                    recommendation="Implement proper error handling without exposing stack traces"
                ))
                
        except Exception as e:
            print(f"❌ Error auditing {filepath}: {e}")
        
        return vulnerabilities
    
    def _test_live_endpoints(self) -> List[SecurityVulnerability]:
        """Test live API endpoints for vulnerabilities"""
        vulnerabilities = []
        
        common_endpoints = [
            "/", "/api", "/predict", "/health", "/docs", "/swagger",
            "/admin", "/login", "/auth", "/status"
        ]
        
        for endpoint in common_endpoints:
            url = f"{self.base_url.rstrip('/')}{endpoint}"
            vulnerabilities.extend(self._test_endpoint_security(url))
        
        return vulnerabilities
    
    def _test_endpoint_security(self, url: str) -> List[SecurityVulnerability]:
        """Test individual endpoint for security issues"""
        vulnerabilities = []
        
        try:
            # Test for missing security headers
            response = requests.get(url, timeout=10, verify=True)
            headers = response.headers
            
            required_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Content-Security-Policy': 'default-src \'self\''
            }
            
            for header, expected in required_headers.items():
                if header not in headers:
                    vulnerabilities.append(SecurityVulnerability(
                        severity="MEDIUM",
                        category="Security Headers",
                        description=f"Missing security header: {header}",
                        location=url,
                        recommendation=f"Add {header}: {expected} header"
                    ))
            
            # Test for HTTP instead of HTTPS
            if url.startswith('http://'):
                vulnerabilities.append(SecurityVulnerability(
                    severity="HIGH",
                    category="Encryption",
                    description="Endpoint accessible over unencrypted HTTP",
                    location=url,
                    recommendation="Enforce HTTPS for all endpoints"
                ))
            
            # Test for verbose error messages
            test_payload = {"malicious": "'; DROP TABLE users; --"}
            try:
                error_response = requests.post(url, json=test_payload, timeout=5)
                if "traceback" in error_response.text.lower() or "error" in error_response.text.lower():
                    vulnerabilities.append(SecurityVulnerability(
                        severity="MEDIUM",
                        category="Information Disclosure",
                        description="Verbose error messages exposed",
                        location=url,
                        recommendation="Implement generic error responses"
                    ))
            except:
                pass
            
            # Test for rate limiting
            if not self._test_rate_limiting(url):
                vulnerabilities.append(SecurityVulnerability(
                    severity="MEDIUM",
                    category="Rate Limiting",
                    description="No rate limiting detected",
                    location=url,
                    recommendation="Implement rate limiting to prevent abuse"
                ))
                
        except requests.RequestException as e:
            print(f"⚠️ Could not test {url}: {e}")
        
        return vulnerabilities
    
    def _test_rate_limiting(self, url: str) -> bool:
        """Test if endpoint has rate limiting"""
        try:
            responses = []
            for _ in range(10):
                resp = requests.get(url, timeout=2)
                responses.append(resp.status_code)
                if resp.status_code == 429:  # Too Many Requests
                    return True
            return False
        except:
            return False
    
    def audit_data_protection(self) -> List[SecurityVulnerability]:
        """Audit data protection mechanisms"""
        print("🛡️ Auditing Data Protection...")
        
        vulnerabilities = []
        
        # Check for encryption at rest
        data_files = ["data/historial_kabala_github.csv", "results/", "models/"]
        
        for data_path in data_files:
            if os.path.exists(data_path):
                if not self._is_encrypted(data_path):
                    vulnerabilities.append(SecurityVulnerability(
                        severity="HIGH",
                        category="Data Encryption",
                        description=f"Data stored unencrypted: {data_path}",
                        location=data_path,
                        recommendation="Implement encryption at rest for sensitive data"
                    ))
        
        # Check for secure random number generation
        code_files = [f for f in os.listdir('.') if f.endswith('.py')]
        
        for file_path in code_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if re.search(r'random\.random\(\)|random\.choice\(\)', content):
                    vulnerabilities.append(SecurityVulnerability(
                        severity="MEDIUM",
                        category="Cryptographic Security",
                        description=f"Insecure random number generation in {file_path}",
                        location=file_path,
                        recommendation="Use secrets module for cryptographically secure randomness"
                    ))
            except:
                continue
        
        return vulnerabilities
    
    def _is_encrypted(self, file_path: str) -> bool:
        """Check if file/directory is encrypted"""
        try:
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    header = f.read(100)
                # Simple check for common encrypted file signatures
                return header.startswith(b'\x89PNG') or header.startswith(b'PK\x03\x04') or len(set(header)) > 20
            return False
        except:
            return False
    
    def audit_dependencies(self) -> List[SecurityVulnerability]:
        """Audit third-party dependencies for known vulnerabilities"""
        print("📦 Auditing Dependencies...")
        
        vulnerabilities = []
        
        # Check requirements files
        req_files = ["requirements.txt", "requirements-dev.txt", "requirements-gpu.txt"]
        
        for req_file in req_files:
            if os.path.exists(req_file):
                vulnerabilities.extend(self._scan_requirements(req_file))
        
        return vulnerabilities
    
    def _scan_requirements(self, req_file: str) -> List[SecurityVulnerability]:
        """Scan requirements file for vulnerable packages"""
        vulnerabilities = []
        
        try:
            with open(req_file, 'r') as f:
                requirements = f.readlines()
            
            # Known vulnerable patterns (simplified - in production use safety or snyk)
            vulnerable_patterns = {
                'django<3.2': 'Django versions before 3.2 have known security issues',
                'flask<1.1': 'Flask versions before 1.1 have security vulnerabilities',
                'tensorflow<2.8': 'TensorFlow versions before 2.8 have security issues',
                'requests<2.25': 'Requests versions before 2.25 have security vulnerabilities'
            }
            
            for req in requirements:
                req = req.strip().lower()
                for pattern, description in vulnerable_patterns.items():
                    if pattern.split('<')[0] in req:
                        # Simple version check
                        vulnerabilities.append(SecurityVulnerability(
                            severity="HIGH",
                            category="Dependency",
                            description=f"Potentially vulnerable dependency: {req}",
                            location=req_file,
                            recommendation=f"Update dependency: {description}"
                        ))
                        
        except Exception as e:
            print(f"❌ Error scanning {req_file}: {e}")
        
        return vulnerabilities
    
    def audit_configuration(self) -> List[SecurityVulnerability]:
        """Audit configuration security"""
        print("⚙️ Auditing Configuration...")
        
        vulnerabilities = []
        
        # Check for insecure configurations
        config_files = ["config/", ".env", ".env.example", "railway.toml", "vercel.json"]
        
        for config_path in config_files:
            if os.path.exists(config_path):
                vulnerabilities.extend(self._audit_config_file(config_path))
        
        return vulnerabilities
    
    def _audit_config_file(self, config_path: str) -> List[SecurityVulnerability]:
        """Audit individual configuration file"""
        vulnerabilities = []
        
        try:
            if os.path.isdir(config_path):
                for file_name in os.listdir(config_path):
                    file_path = os.path.join(config_path, file_name)
                    if os.path.isfile(file_path):
                        vulnerabilities.extend(self._check_config_content(file_path))
            else:
                vulnerabilities.extend(self._check_config_content(config_path))
                
        except Exception as e:
            print(f"❌ Error auditing config {config_path}: {e}")
        
        return vulnerabilities
    
    def _check_config_content(self, file_path: str) -> List[SecurityVulnerability]:
        """Check configuration file content for security issues"""
        vulnerabilities = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for default passwords
            if re.search(r'password.*=.*(admin|password|123456|default)', content, re.IGNORECASE):
                vulnerabilities.append(SecurityVulnerability(
                    severity="CRITICAL",
                    category="Credentials",
                    description="Default or weak passwords found in configuration",
                    location=file_path,
                    recommendation="Use strong, unique passwords and store in environment variables"
                ))
            
            # Check for debug settings
            if re.search(r'debug.*=.*true|DEBUG.*=.*1', content, re.IGNORECASE):
                vulnerabilities.append(SecurityVulnerability(
                    severity="MEDIUM",
                    category="Configuration",
                    description="Debug mode enabled in configuration",
                    location=file_path,
                    recommendation="Disable debug mode in production"
                ))
                
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
        
        return vulnerabilities
    
    def generate_security_report(self, output_path: str = "omega_security_report.json") -> Dict[str, Any]:
        """Generate comprehensive security report"""
        print("📋 Generating Security Report...")
        
        # Run all audits
        api_vulns = self.audit_api_endpoints()
        data_vulns = self.audit_data_protection()
        dep_vulns = self.audit_dependencies()
        config_vulns = self.audit_configuration()
        
        all_vulnerabilities = api_vulns + data_vulns + dep_vulns + config_vulns
        
        # Categorize by severity
        critical = [v for v in all_vulnerabilities if v.severity == "CRITICAL"]
        high = [v for v in all_vulnerabilities if v.severity == "HIGH"]
        medium = [v for v in all_vulnerabilities if v.severity == "MEDIUM"]
        low = [v for v in all_vulnerabilities if v.severity == "LOW"]
        
        # Generate security score (0-100)
        total_vulns = len(all_vulnerabilities)
        critical_weight = len(critical) * 10
        high_weight = len(high) * 5
        medium_weight = len(medium) * 2
        low_weight = len(low) * 1
        
        total_weight = critical_weight + high_weight + medium_weight + low_weight
        security_score = max(0, 100 - total_weight)
        
        report = {
            "audit_timestamp": datetime.now().isoformat(),
            "security_score": security_score,
            "total_vulnerabilities": total_vulns,
            "severity_breakdown": {
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium),
                "low": len(low)
            },
            "category_breakdown": self._categorize_vulnerabilities(all_vulnerabilities),
            "vulnerabilities": [
                {
                    "severity": v.severity,
                    "category": v.category,
                    "description": v.description,
                    "location": v.location,
                    "recommendation": v.recommendation,
                    "exploitable": v.exploitable,
                    "cve_reference": v.cve_reference
                }
                for v in all_vulnerabilities
            ],
            "priority_fixes": [
                {
                    "description": v.description,
                    "location": v.location,
                    "recommendation": v.recommendation
                }
                for v in sorted(all_vulnerabilities, key=lambda x: {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}[x.severity], reverse=True)[:10]
            ]
        }
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Security report saved to {output_path}")
        return report
    
    def _categorize_vulnerabilities(self, vulnerabilities: List[SecurityVulnerability]) -> Dict[str, int]:
        """Categorize vulnerabilities by type"""
        categories = {}
        for vuln in vulnerabilities:
            categories[vuln.category] = categories.get(vuln.category, 0) + 1
        return categories
    
    def generate_security_fixes(self, output_path: str = "security_fixes.py"):
        """Generate automated security fixes"""
        print("🔧 Generating Security Fixes...")
        
        fixes_content = '''#!/usr/bin/env python3
"""
OMEGA AI Automated Security Fixes
Generated by Security Auditor
"""

import os
import secrets
import hashlib
from cryptography.fernet import Fernet

class OmegaSecurityFixes:
    """Automated security fixes for OMEGA AI system"""
    
    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
    
    def generate_secure_api_key(self) -> str:
        """Generate cryptographically secure API key"""
        return secrets.token_urlsafe(32)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def secure_hash_password(self, password: str, salt: str = None) -> tuple:
        """Create secure password hash with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)  # 100k iterations
        return password_hash.hex(), salt
    
    def validate_input(self, user_input: str, input_type: str = "general") -> str:
        """Validate and sanitize user input"""
        if input_type == "lottery_numbers":
            # Validate lottery number input
            numbers = user_input.split(',')
            validated = []
            for num in numbers:
                try:
                    n = int(num.strip())
                    if 1 <= n <= 40:  # Kabala range
                        validated.append(str(n))
                except ValueError:
                    continue
            return ','.join(validated)
        
        # General input sanitization
        import html
        import re
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\\'%;()&+]', '', user_input)
        # HTML escape
        sanitized = html.escape(sanitized)
        return sanitized
    
    def setup_security_headers(self) -> dict:
        """Generate security headers for API responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    def create_env_template(self):
        """Create secure environment template"""
        template = f\"\"\"
# OMEGA AI Secure Environment Variables
# Generated: {datetime.now().isoformat()}

# API Configuration
API_KEY={self.generate_secure_api_key()}
JWT_SECRET_KEY={self.generate_secure_api_key()}

# Database Configuration
DB_PASSWORD={self.generate_secure_api_key()}
DB_ENCRYPTION_KEY={Fernet.generate_key().decode()}

# External Services
RAILWAY_TOKEN=your_railway_token_here
VERCEL_TOKEN=your_vercel_token_here

# Security Settings
RATE_LIMIT_PER_MINUTE=60
MAX_PREDICTION_REQUESTS_PER_DAY=1000
ENABLE_HTTPS_ONLY=true
SESSION_TIMEOUT_MINUTES=30
\"\"\"
        
        with open('.env.secure', 'w') as f:
            f.write(template)
        
        print("✅ Secure environment template created: .env.secure")

if __name__ == "__main__":
    security_fixes = OmegaSecurityFixes()
    
    # Generate secure API key
    api_key = security_fixes.generate_secure_api_key()
    print(f"🔑 Generated API Key: {api_key}")
    
    # Create secure environment template
    security_fixes.create_env_template()
    
    # Generate security headers
    headers = security_fixes.setup_security_headers()
    print("🛡️ Security Headers:", headers)
'''
        
        with open(output_path, 'w') as f:
            f.write(fixes_content)
        
        print(f"✅ Security fixes generated: {output_path}")

# Example usage
if __name__ == "__main__":
    # Initialize security auditor
    auditor = OmegaSecurityAuditor(base_url="https://your-omega-api.railway.app")
    
    # Run comprehensive security audit
    print("🔍 Starting OMEGA AI Security Audit...")
    print("=" * 50)
    
    # Generate security report
    report = auditor.generate_security_report()
    
    # Generate security fixes
    auditor.generate_security_fixes()
    
    # Print summary
    print(f"\n📊 Security Audit Summary:")
    print(f"   Security Score: {report['security_score']}/100")
    print(f"   Total Vulnerabilities: {report['total_vulnerabilities']}")
    print(f"   Critical: {report['severity_breakdown']['critical']}")
    print(f"   High: {report['severity_breakdown']['high']}")  
    print(f"   Medium: {report['severity_breakdown']['medium']}")
    print(f"   Low: {report['severity_breakdown']['low']}")
    
    if report['security_score'] < 70:
        print("\n⚠️  SECURITY ALERT: Score below 70 - Immediate action required!")
    elif report['security_score'] < 85:
        print("\n🔶 Security improvements recommended")
    else:
        print("\n✅ Good security posture")