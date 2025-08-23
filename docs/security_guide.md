# 🔒 OMEGA Security Guide

## Overview

The OMEGA Pro AI system includes a comprehensive security framework designed to protect against common vulnerabilities and provide enterprise-grade security features.

## Security Components

### 1. Security Manager (`src/security/security_manager.py`)

The Security Manager is the core component that provides:

- **Authentication & Authorization**: JWT token management with role-based access
- **Input Validation**: Protection against SQL injection, XSS, and command injection
- **Rate Limiting**: Configurable rate limiting to prevent abuse
- **Audit Logging**: Comprehensive logging of security events
- **Password Management**: Secure hashing and strength validation

#### Key Features:

```python
from src.security.security_manager import SecurityManager

# Initialize security manager
security_manager = SecurityManager()

# Validate user input
result = await security_manager.validate_request(
    request_data={"user_input": "some data"},
    user_id="user123",
    ip_address="192.168.1.1"
)

# Create JWT token
tokens = security_manager.create_jwt_token(
    user_id="user123",
    permissions=["read:predictions", "write:config"]
)
```

### 2. Vulnerability Scanner (`src/security/vulnerability_scanner.py`)

Automated vulnerability scanning for:

- **Code Analysis**: Static analysis for common vulnerabilities
- **Dependency Scanning**: Known vulnerability database checks
- **Configuration Review**: Security misconfigurations detection

#### Usage:

```python
from src.security.vulnerability_scanner import VulnerabilityScanner

scanner = VulnerabilityScanner()
results = await scanner.scan_project("/path/to/project")
```

## Security Policies

The system implements several security policies:

### Input Validation Policy
- **Purpose**: Prevent injection attacks
- **Action**: Block malicious input and sanitize
- **Severity**: High

### Rate Limiting Policy  
- **Purpose**: Prevent abuse and DoS attacks
- **Limits**: 
  - API requests: 100/hour per IP
  - Predictions: 50/hour per IP
  - Auth attempts: 5/15min per IP
- **Action**: Block exceeding requests

### Authentication Policy
- **Purpose**: Ensure secure authentication
- **Requirements**:
  - Valid JWT tokens required
  - Token IP binding (optional)
  - Automatic token revocation

### Audit Logging Policy
- **Purpose**: Security event tracking
- **Logs**: All security events, failed attempts, violations
- **Retention**: Configurable (default: 10,000 events)

## Security CLI Tool

Use the security CLI for management tasks:

```bash
# Scan for vulnerabilities
python scripts/security_cli.py scan vulnerabilities /path/to/project

# Create user token
python scripts/security_cli.py auth create-token user123 --permissions read:predictions

# View audit events
python scripts/security_cli.py audit events --hours 24

# Security health check
python scripts/security_cli.py health-check
```

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET=your-secret-key-32-chars-minimum
JWT_EXPIRY_HOURS=24

# Security Settings  
SECURITY_LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
AUDIT_RETENTION_DAYS=30

# Password Policy
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_SPECIAL=true
```

### Security Manager Configuration

```python
security_config = {
    'jwt_secret': 'your-secret-key',
    'jwt_algorithm': 'HS256', 
    'token_expiry_hours': 24,
    'max_audit_events': 10000,
    'password_min_length': 8,
    'password_require_special': True
}
```

## Best Practices

### 1. Authentication

- **Use strong JWT secrets** (32+ characters)
- **Implement token rotation** for long-lived sessions
- **Bind tokens to IP addresses** when possible
- **Use HTTPS only** in production

### 2. Input Validation

- **Validate all user inputs** before processing
- **Use parameterized queries** for database access
- **Sanitize output** to prevent XSS
- **Implement CSRF protection** for web interfaces

### 3. Rate Limiting

- **Configure appropriate limits** based on use case
- **Monitor rate limiting metrics** for abuse patterns
- **Implement progressive delays** for repeated violations
- **Use distributed rate limiting** for scaled deployments

### 4. Audit & Monitoring

- **Log all security events** with sufficient detail
- **Monitor for suspicious patterns** in real-time
- **Set up alerts** for critical security events
- **Regular review** of audit logs

### 5. Vulnerability Management

- **Run regular security scans** (weekly/monthly)
- **Keep dependencies updated** and monitor for vulnerabilities
- **Implement security testing** in CI/CD pipeline
- **Conduct periodic security reviews**

## API Security Integration

### FastAPI Integration

```python
from fastapi import Depends, HTTPException
from src.security.security_manager import SecurityManager

security_manager = SecurityManager()

async def verify_token(authorization: str = Header(...)):
    """Dependency for JWT token verification"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")
    
    token = authorization.split(" ")[1]
    result = security_manager.verify_jwt_token(token)
    
    if not result["valid"]:
        raise HTTPException(401, result["error"])
    
    return result

@app.post("/api/v1/predictions")
async def create_prediction(
    request: PredictionRequest,
    user_info = Depends(verify_token)
):
    # Validate input
    validation = await security_manager.validate_request(
        request.dict(),
        user_id=user_info["user_id"]
    )
    
    if not validation["valid"]:
        raise HTTPException(400, "Invalid input detected")
    
    # Process with sanitized data
    return process_prediction(validation["sanitized_data"])
```

## Security Monitoring

### Metrics

The security system provides metrics for monitoring:

- `security_validations_total`: Total input validations
- `security_threats_detected`: Threats detected by type  
- `security_events_total`: Security events by type
- `high_risk_events_total`: High-risk security events
- `alerts_created`: Security alerts created

### Health Checks

```python
# Get security status
summary = security_manager.get_security_summary()

# Run security health check
health_results = await security_manager.perform_security_scan()
```

## Incident Response

### Automated Response

The system automatically:

1. **Blocks malicious requests** based on input validation
2. **Rate limits** abusive clients
3. **Logs security events** for investigation  
4. **Revokes tokens** when necessary

### Manual Response

For security incidents:

1. **Review audit logs** for the incident timeframe
2. **Revoke affected user tokens** immediately
3. **Block suspicious IP addresses** temporarily
4. **Update security policies** if needed
5. **Conduct post-incident review**

### Example Incident Commands

```bash
# View recent security events
python scripts/security_cli.py audit events --hours 24 --event-type security_violation

# Revoke user tokens
python scripts/security_cli.py auth revoke-token compromised_user

# Run emergency security scan
python scripts/security_cli.py scan vulnerabilities . --severity high

# Check system security health
python scripts/security_cli.py health-check
```

## Testing Security

### Running Security Tests

```bash
# Run security-specific tests
pytest tests/test_security.py -v

# Run with coverage
pytest tests/test_security.py --cov=src/security

# Run integration tests
pytest tests/test_security.py::TestSecurityIntegration -v
```

### Security Test Categories

1. **Input Validation Tests**: SQL injection, XSS, command injection
2. **Authentication Tests**: JWT token creation, validation, revocation
3. **Rate Limiting Tests**: Various rate limit scenarios
4. **Vulnerability Scanner Tests**: Code analysis, dependency scanning
5. **Integration Tests**: End-to-end security workflows

## Compliance

The OMEGA security framework helps with:

- **OWASP Top 10** compliance
- **Data protection** requirements
- **Audit trail** maintenance
- **Access control** implementation
- **Vulnerability management** processes

## Security Updates

### Regular Tasks

- **Weekly**: Review audit logs and security events
- **Monthly**: Run comprehensive vulnerability scans
- **Quarterly**: Review and update security policies
- **Annually**: Full security assessment and penetration testing

### Keeping Current

- Monitor security advisories for dependencies
- Update security tools and scanners regularly
- Stay informed about new threat vectors
- Participate in security communities and training

## Troubleshooting

### Common Issues

#### 1. JWT Token Issues
```bash
# Verify token manually
python scripts/security_cli.py auth verify-token <token>

# Check token configuration
python -c "from src.security.security_manager import SecurityManager; sm=SecurityManager(); print(sm.config)"
```

#### 2. Rate Limiting Problems
```bash
# Check rate limit status
python -c "from src.security.security_manager import RateLimiter; rl=RateLimiter(); print(rl.requests)"

# Reset rate limits
python -c "from src.security.security_manager import RateLimiter; rl=RateLimiter(); rl.requests.clear()"
```

#### 3. Validation Failures
```bash
# Test input validation
python scripts/security_cli.py validate input "test input"

# Check validation policies
python scripts/security_cli.py config list-policies
```

## Support

For security-related questions or incident reporting:

1. Review this documentation
2. Check the audit logs for clues
3. Run the security health check
4. Use the security CLI tools for diagnosis
5. Review test cases for examples

---

**Remember**: Security is an ongoing process, not a one-time setup. Regular monitoring, updates, and reviews are essential for maintaining a secure system.