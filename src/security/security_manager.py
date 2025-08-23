#!/usr/bin/env python3
"""
🔒 OMEGA Security Manager - Sistema de Seguridad Avanzado
Autenticación, autorización, validación y auditoría completas
"""

import asyncio
import hashlib
import hmac
import jwt
import time
import re
import ipaddress
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import secrets
import bcrypt
from pathlib import Path
import json

from src.utils.logger_factory import LoggerFactory
from src.monitoring.metrics_collector import MetricsCollector

class SecurityLevel(Enum):
    """Niveles de seguridad"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditEventType(Enum):
    """Tipos de eventos de auditoría"""
    LOGIN = "login"
    LOGOUT = "logout"
    API_ACCESS = "api_access"
    PREDICTION_REQUEST = "prediction_request"
    CONFIG_CHANGE = "config_change"
    MODEL_ACCESS = "model_access"
    DATA_ACCESS = "data_access"
    SECURITY_VIOLATION = "security_violation"
    ADMIN_ACTION = "admin_action"

@dataclass
class SecurityPolicy:
    """Política de seguridad"""
    name: str
    description: str
    enabled: bool
    severity: SecurityLevel
    rules: List[Dict[str, Any]]
    action: str  # "block", "warn", "log"

@dataclass
class AuditEvent:
    """Evento de auditoría"""
    event_id: str
    event_type: AuditEventType
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: str
    user_agent: Optional[str]
    resource: str
    action: str
    result: str  # "success", "failure", "blocked"
    timestamp: datetime
    metadata: Dict[str, Any]
    risk_score: float = 0.0

@dataclass
class SecurityToken:
    """Token de seguridad"""
    token_id: str
    user_id: str
    token_type: str  # "access", "refresh", "api_key"
    permissions: List[str]
    issued_at: datetime
    expires_at: datetime
    last_used: Optional[datetime] = None
    ip_address: Optional[str] = None
    is_revoked: bool = False

class InputValidator:
    """Validador de entrada para prevenir inyecciones"""
    
    def __init__(self):
        self.logger = LoggerFactory.get_logger("InputValidator")
        
        # Patrones peligrosos
        self.sql_injection_patterns = [
            r"('|(\\')|(;)|(\\;))",
            r"(\\b(ALTER|CREATE|DELETE|DROP|EXEC(UTE)?|INSERT|SELECT|UNION|UPDATE)\\b)",
            r"(\\b(AND|OR)\\b.{1,6}?(=|>|<|\\bin\\b|\\blike\\b))",
            r"(\\b(GRANT|REVOKE)\\b)",
            r"(\\bCHAR\\s*\\()",
            r"(\\bCAST\\s*\\()"
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"onmouseover=",
            r"<iframe",
            r"<object",
            r"<embed"
        ]
        
        self.command_injection_patterns = [
            r"[;&|`$()]",
            r"\\b(wget|curl|nc|netcat|telnet|ssh)\\b",
            r"\\b(rm|del|format|shutdown)\\b",
            r"\\.\\.[\\/]",
            r"[<>|&;`$(){}\\[\\]\\\\]"
        ]
    
    def validate_string(self, value: str, field_name: str = "unknown") -> Dict[str, Any]:
        """Valida string contra patrones peligrosos"""
        if not isinstance(value, str):
            return {"valid": True, "sanitized": str(value)}
        
        threats = []
        
        # Verificar SQL injection
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append("sql_injection")
                break
        
        # Verificar XSS
        for pattern in self.xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append("xss")
                break
        
        # Verificar command injection
        for pattern in self.command_injection_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append("command_injection")
                break
        
        # Sanitizar
        sanitized = value
        if threats:
            # Escape caracteres peligrosos
            sanitized = (sanitized
                        .replace("'", "\\'")
                        .replace('"', '\\"')
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace("&", "&amp;"))
            
            self.logger.warning(f"🚨 Security threat detected in field {field_name}: {threats}")
        
        return {
            "valid": len(threats) == 0,
            "threats": threats,
            "sanitized": sanitized,
            "original": value
        }
    
    def validate_prediction_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida request de predicción"""
        validated_data = {}
        threats = []
        
        for key, value in data.items():
            if isinstance(value, str):
                validation = self.validate_string(value, key)
                validated_data[key] = validation["sanitized"]
                if not validation["valid"]:
                    threats.extend(validation["threats"])
            else:
                validated_data[key] = value
        
        return {
            "data": validated_data,
            "valid": len(threats) == 0,
            "threats": threats
        }

class RateLimiter:
    """Sistema de rate limiting"""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        self.blocked_ips: Dict[str, float] = {}  # IP -> block_until_timestamp
        
        # Configuración
        self.limits = {
            "api_requests": {"count": 100, "window": 3600},  # 100/hour
            "predictions": {"count": 50, "window": 3600},    # 50/hour
            "auth_attempts": {"count": 5, "window": 900}     # 5/15min
        }
    
    def is_allowed(self, identifier: str, limit_type: str = "api_requests") -> bool:
        """Verifica si request está permitido"""
        now = time.time()
        
        # Verificar si IP está bloqueada
        if identifier in self.blocked_ips:
            if now < self.blocked_ips[identifier]:
                return False
            else:
                del self.blocked_ips[identifier]
        
        # Obtener límite
        if limit_type not in self.limits:
            return True
        
        limit_config = self.limits[limit_type]
        window_size = limit_config["window"]
        max_requests = limit_config["count"]
        
        # Limpiar requests antiguos
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < window_size
        ]
        
        # Verificar límite
        if len(self.requests[identifier]) >= max_requests:
            # Bloquear IP temporalmente si excede límite crítico
            if limit_type == "auth_attempts":
                self.blocked_ips[identifier] = now + 3600  # 1 hour block
            return False
        
        # Registrar request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining_requests(self, identifier: str, limit_type: str = "api_requests") -> int:
        """Obtiene requests restantes"""
        if limit_type not in self.limits:
            return float('inf')
        
        now = time.time()
        window_size = self.limits[limit_type]["window"]
        max_requests = self.limits[limit_type]["count"]
        
        if identifier not in self.requests:
            return max_requests
        
        # Limpiar requests antiguos
        recent_requests = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < window_size
        ]
        
        return max(0, max_requests - len(recent_requests))

class SecurityManager:
    """Gestor principal de seguridad"""
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        self.metrics = metrics_collector or MetricsCollector()
        self.logger = LoggerFactory.get_logger("SecurityManager")
        
        # Componentes
        self.input_validator = InputValidator()
        self.rate_limiter = RateLimiter()
        
        # Storage
        self.audit_events: List[AuditEvent] = []
        self.security_tokens: Dict[str, SecurityToken] = {}
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.config = {
            'jwt_secret': secrets.token_urlsafe(32),
            'jwt_algorithm': 'HS256',
            'token_expiry_hours': 24,
            'refresh_token_expiry_days': 30,
            'max_audit_events': 10000,
            'password_min_length': 8,
            'password_require_special': True,
            'session_timeout_minutes': 60,
            'max_failed_logins': 5,
            'lockout_duration_minutes': 15
        }
        
        # Inicializar políticas por defecto
        self._create_default_policies()
        
        self.logger.info("🔒 Security Manager initialized")
    
    def _create_default_policies(self):
        """Crea políticas de seguridad por defecto"""
        default_policies = [
            SecurityPolicy(
                name="input_validation",
                description="Validación de entrada para prevenir inyecciones",
                enabled=True,
                severity=SecurityLevel.HIGH,
                rules=[
                    {"type": "sql_injection", "action": "block"},
                    {"type": "xss", "action": "block"},
                    {"type": "command_injection", "action": "block"}
                ],
                action="block"
            ),
            SecurityPolicy(
                name="rate_limiting",
                description="Límites de velocidad para prevenir abuso",
                enabled=True,
                severity=SecurityLevel.MEDIUM,
                rules=[
                    {"endpoint": "/api/v1/predictions", "limit": "50/hour"},
                    {"endpoint": "/api/v1/auth", "limit": "10/hour"}
                ],
                action="block"
            ),
            SecurityPolicy(
                name="authentication",
                description="Autenticación y autorización requerida",
                enabled=True,
                severity=SecurityLevel.CRITICAL,
                rules=[
                    {"require_jwt": True},
                    {"require_https": True}
                ],
                action="block"
            ),
            SecurityPolicy(
                name="audit_logging",
                description="Registro de eventos críticos",
                enabled=True,
                severity=SecurityLevel.HIGH,
                rules=[
                    {"log_all_requests": True},
                    {"log_failures": True}
                ],
                action="log"
            )
        ]
        
        for policy in default_policies:
            self.security_policies[policy.name] = policy
    
    async def validate_request(self, 
                             request_data: Dict[str, Any], 
                             user_id: Optional[str] = None,
                             ip_address: str = "unknown",
                             endpoint: str = "/") -> Dict[str, Any]:
        """Valida request completo"""
        
        validation_result = {
            "valid": True,
            "threats": [],
            "sanitized_data": request_data.copy(),
            "security_score": 100.0,
            "blocked": False
        }
        
        # 1. Rate limiting
        if not self.rate_limiter.is_allowed(ip_address, "api_requests"):
            validation_result["valid"] = False
            validation_result["blocked"] = True
            validation_result["threats"].append("rate_limit_exceeded")
            validation_result["security_score"] = 0.0
            
            await self._log_security_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                user_id=user_id,
                ip_address=ip_address,
                resource=endpoint,
                action="request_blocked",
                result="blocked",
                metadata={"reason": "rate_limit_exceeded"}
            )
            
            return validation_result
        
        # 2. Input validation
        input_validation = self.input_validator.validate_prediction_request(request_data)
        if not input_validation["valid"]:
            validation_result["valid"] = False
            validation_result["threats"].extend(input_validation["threats"])
            validation_result["security_score"] -= 30.0
        
        validation_result["sanitized_data"] = input_validation["data"]
        
        # 3. Verificar políticas de seguridad
        for policy_name, policy in self.security_policies.items():
            if not policy.enabled:
                continue
            
            if policy.name == "input_validation" and input_validation["threats"]:
                if policy.action == "block":
                    validation_result["blocked"] = True
                validation_result["security_score"] -= 20.0
        
        # 4. Calcular score de riesgo
        risk_score = 100.0 - validation_result["security_score"]
        
        # 5. Log del evento
        await self._log_security_event(
            event_type=AuditEventType.API_ACCESS,
            user_id=user_id,
            ip_address=ip_address,
            resource=endpoint,
            action="request_validation",
            result="success" if validation_result["valid"] else "blocked",
            metadata={
                "threats": validation_result["threats"],
                "risk_score": risk_score
            }
        )
        
        # Métricas
        self.metrics.increment("security_validations_total")
        if validation_result["threats"]:
            self.metrics.increment(
                "security_threats_detected",
                labels={"threats": ",".join(validation_result["threats"])}
            )
        
        return validation_result
    
    def create_jwt_token(self, user_id: str, permissions: List[str] = None, 
                        ip_address: Optional[str] = None) -> Dict[str, str]:
        """Crea token JWT"""
        now = datetime.now()
        
        # Access token
        access_payload = {
            'user_id': user_id,
            'permissions': permissions or [],
            'token_type': 'access',
            'iat': now,
            'exp': now + timedelta(hours=self.config['token_expiry_hours']),
            'ip': ip_address
        }
        
        access_token = jwt.encode(
            access_payload,
            self.config['jwt_secret'],
            algorithm=self.config['jwt_algorithm']
        )
        
        # Refresh token
        refresh_payload = {
            'user_id': user_id,
            'token_type': 'refresh',
            'iat': now,
            'exp': now + timedelta(days=self.config['refresh_token_expiry_days'])
        }
        
        refresh_token = jwt.encode(
            refresh_payload,
            self.config['jwt_secret'],
            algorithm=self.config['jwt_algorithm']
        )
        
        # Guardar token info
        token_id = secrets.token_urlsafe(16)
        self.security_tokens[token_id] = SecurityToken(
            token_id=token_id,
            user_id=user_id,
            token_type='access',
            permissions=permissions or [],
            issued_at=now,
            expires_at=now + timedelta(hours=self.config['token_expiry_hours']),
            ip_address=ip_address
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': self.config['token_expiry_hours'] * 3600
        }
    
    def verify_jwt_token(self, token: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Verifica token JWT"""
        try:
            payload = jwt.decode(
                token,
                self.config['jwt_secret'],
                algorithms=[self.config['jwt_algorithm']]
            )
            
            # Verificar IP si se especificó en el token
            if payload.get('ip') and ip_address and payload['ip'] != ip_address:
                return {"valid": False, "error": "IP mismatch"}
            
            # Verificar si token está revocado
            user_id = payload['user_id']
            for token_info in self.security_tokens.values():
                if (token_info.user_id == user_id and 
                    token_info.token_type == payload['token_type'] and
                    token_info.is_revoked):
                    return {"valid": False, "error": "Token revoked"}
            
            return {
                "valid": True,
                "user_id": payload['user_id'],
                "permissions": payload.get('permissions', []),
                "token_type": payload.get('token_type', 'access')
            }
            
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError as e:
            return {"valid": False, "error": f"Invalid token: {str(e)}"}
    
    def revoke_token(self, user_id: str, token_type: str = "all") -> bool:
        """Revoca tokens de usuario"""
        revoked_count = 0
        
        for token_info in self.security_tokens.values():
            if (token_info.user_id == user_id and 
                (token_type == "all" or token_info.token_type == token_type)):
                token_info.is_revoked = True
                revoked_count += 1
        
        self.logger.info(f"🔒 Revoked {revoked_count} tokens for user {user_id}")
        return revoked_count > 0
    
    def hash_password(self, password: str) -> str:
        """Hash de password con bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verifica password"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Valida fortaleza de password"""
        issues = []
        score = 0
        
        # Longitud
        if len(password) < self.config['password_min_length']:
            issues.append(f"Must be at least {self.config['password_min_length']} characters")
        else:
            score += 20
        
        # Mayúsculas
        if not re.search(r'[A-Z]', password):
            issues.append("Must contain uppercase letter")
        else:
            score += 15
        
        # Minúsculas
        if not re.search(r'[a-z]', password):
            issues.append("Must contain lowercase letter")
        else:
            score += 15
        
        # Números
        if not re.search(r'\d', password):
            issues.append("Must contain number")
        else:
            score += 15
        
        # Caracteres especiales
        if self.config['password_require_special']:
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                issues.append("Must contain special character")
            else:
                score += 20
        
        # Longitud adicional
        if len(password) > 12:
            score += 15
        
        return {
            "valid": len(issues) == 0,
            "score": min(100, score),
            "issues": issues,
            "strength": (
                "Very Weak" if score < 30 else
                "Weak" if score < 50 else
                "Medium" if score < 70 else
                "Strong" if score < 90 else
                "Very Strong"
            )
        }
    
    async def _log_security_event(self,
                                 event_type: AuditEventType,
                                 user_id: Optional[str] = None,
                                 session_id: Optional[str] = None,
                                 ip_address: str = "unknown",
                                 user_agent: Optional[str] = None,
                                 resource: str = "",
                                 action: str = "",
                                 result: str = "",
                                 metadata: Dict[str, Any] = None,
                                 risk_score: float = 0.0):
        """Log evento de auditoría"""
        
        event = AuditEvent(
            event_id=secrets.token_urlsafe(16),
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            result=result,
            timestamp=datetime.now(),
            metadata=metadata or {},
            risk_score=risk_score
        )
        
        self.audit_events.append(event)
        
        # Mantener límite de eventos
        if len(self.audit_events) > self.config['max_audit_events']:
            self.audit_events = self.audit_events[-self.config['max_audit_events']:]
        
        # Log estructurado
        self.logger.info(
            f"🔍 Security Event: {event_type.value}",
            extra={
                "security_event": asdict(event),
                "risk_score": risk_score
            }
        )
        
        # Métricas
        self.metrics.increment(
            "security_events_total",
            labels={
                "event_type": event_type.value,
                "result": result
            }
        )
        
        if risk_score > 50:
            self.metrics.increment("high_risk_events_total")
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de seguridad"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        recent_events = [
            event for event in self.audit_events
            if event.timestamp >= last_24h
        ]
        
        # Análisis de eventos
        event_types = {}
        high_risk_events = 0
        failed_events = 0
        
        for event in recent_events:
            event_types[event.event_type.value] = event_types.get(event.event_type.value, 0) + 1
            if event.risk_score > 50:
                high_risk_events += 1
            if event.result in ["failure", "blocked"]:
                failed_events += 1
        
        # Estado de tokens
        active_tokens = len([
            token for token in self.security_tokens.values()
            if not token.is_revoked and token.expires_at > now
        ])
        
        # Rate limiting stats
        blocked_ips = len(self.rate_limiter.blocked_ips)
        
        return {
            "security_status": "healthy" if high_risk_events < 10 else "attention_required",
            "events_last_24h": len(recent_events),
            "high_risk_events": high_risk_events,
            "failed_events": failed_events,
            "event_breakdown": event_types,
            "active_tokens": active_tokens,
            "blocked_ips": blocked_ips,
            "policies_enabled": len([p for p in self.security_policies.values() if p.enabled]),
            "last_update": now.isoformat()
        }
    
    def get_audit_events(self, 
                        limit: int = 100,
                        event_type: Optional[AuditEventType] = None,
                        user_id: Optional[str] = None,
                        hours_back: int = 24) -> List[Dict[str, Any]]:
        """Obtiene eventos de auditoría"""
        cutoff = datetime.now() - timedelta(hours=hours_back)
        
        filtered_events = []
        for event in reversed(self.audit_events):  # Más recientes primero
            if event.timestamp < cutoff:
                continue
            if event_type and event.event_type != event_type:
                continue
            if user_id and event.user_id != user_id:
                continue
            
            filtered_events.append(asdict(event))
            
            if len(filtered_events) >= limit:
                break
        
        return filtered_events
    
    async def perform_security_scan(self) -> Dict[str, Any]:
        """Realiza escaneo de seguridad"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": 100.0,
            "issues": [],
            "recommendations": [],
            "policies": {}
        }
        
        # 1. Verificar políticas
        for policy_name, policy in self.security_policies.items():
            policy_status = {
                "enabled": policy.enabled,
                "severity": policy.severity.value,
                "issues": []
            }
            
            if not policy.enabled and policy.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                policy_status["issues"].append("Critical policy disabled")
                results["overall_score"] -= 15
                results["issues"].append(f"Critical security policy '{policy_name}' is disabled")
            
            results["policies"][policy_name] = policy_status
        
        # 2. Verificar tokens expirados
        now = datetime.now()
        expired_tokens = [
            token for token in self.security_tokens.values()
            if token.expires_at < now and not token.is_revoked
        ]
        
        if expired_tokens:
            results["issues"].append(f"{len(expired_tokens)} expired tokens not cleaned up")
            results["recommendations"].append("Implement automatic token cleanup")
        
        # 3. Verificar eventos de alto riesgo
        recent_high_risk = [
            event for event in self.audit_events
            if event.risk_score > 70 and 
            event.timestamp > now - timedelta(hours=24)
        ]
        
        if len(recent_high_risk) > 5:
            results["overall_score"] -= 20
            results["issues"].append(f"{len(recent_high_risk)} high-risk events in last 24h")
            results["recommendations"].append("Review and investigate high-risk security events")
        
        # 4. Verificar configuración
        if len(self.config['jwt_secret']) < 32:
            results["overall_score"] -= 25
            results["issues"].append("JWT secret is too short")
            results["recommendations"].append("Use longer JWT secret (32+ characters)")
        
        return results

    def enable_policy(self, policy_name: str) -> bool:
        """Habilita política de seguridad"""
        if policy_name in self.security_policies:
            self.security_policies[policy_name].enabled = True
            self.logger.info(f"🔒 Enabled security policy: {policy_name}")
            return True
        return False
    
    def disable_policy(self, policy_name: str) -> bool:
        """Deshabilita política de seguridad"""
        if policy_name in self.security_policies:
            self.security_policies[policy_name].enabled = False
            self.logger.warning(f"⚠️ Disabled security policy: {policy_name}")
            return True
        return False