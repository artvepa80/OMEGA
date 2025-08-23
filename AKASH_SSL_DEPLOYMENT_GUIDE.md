# OMEGA Pro AI - Secure Akash Deployment Guide

## 🔐 SSL/TLS Infrastructure & Akash Network Deployment

This guide provides complete instructions for deploying OMEGA Pro AI to Akash Network with production-ready SSL/TLS infrastructure, secure container configurations, and comprehensive monitoring.

## 📋 Prerequisites

### Required Tools
```bash
# Akash CLI
curl -sSfL https://raw.githubusercontent.com/akash-network/node/master/install.sh | sh

# Docker
# Follow installation guide: https://docs.docker.com/get-docker/

# Python dependencies
pip install -r requirements.txt
pip install docker click cryptography pyopenssl requests pyyaml
```

### Required Environment Variables
```bash
export GITHUB_TOKEN="your_github_token_here"  # For container registry
export AKASH_WALLET="your_akash_wallet_name"  # Your Akash wallet
export DOMAIN_NAME="your-domain.com"          # Your domain
export EMAIL="your-email@example.com"         # For SSL certificates
export REDIS_PASSWORD="secure_redis_password" # Redis authentication
export JWT_SECRET="secure_jwt_secret"         # API authentication
```

## 🚀 Quick Deployment

### 1. Complete Deployment (Recommended)
```bash
# Deploy with all security features
python scripts/akash_deployment_manager.py deploy \
  --domain your-domain.com \
  --email your-email@example.com \
  --wallet your-wallet-name
```

### 2. Step-by-Step Deployment

#### A. Generate SSL Certificates
```bash
# Self-signed certificate (development)
python scripts/ssl_cert_manager.py generate \
  --domain your-domain.com \
  --email your-email@example.com \
  --type self-signed

# Let's Encrypt certificate (production)
python scripts/ssl_cert_manager.py generate \
  --domain your-domain.com \
  --email your-email@example.com \
  --type letsencrypt
```

#### B. Generate Security Configurations
```bash
# Generate service mesh security configs
python scripts/service_mesh_security.py generate-configs \
  --output-dir ./config
```

#### C. Deploy to Akash
```bash
# Secure deployment with SSL
python scripts/secure_akash_deploy.py deploy \
  --gpu-model rtx4090 \
  --max-price-uakt 1000 \
  --wallet your-wallet-name \
  --domain your-domain.com \
  --email your-email@example.com \
  --github-token $GITHUB_TOKEN
```

## 🔧 Configuration Files Overview

### Created Files Structure
```
├── ssl/
│   ├── cert.pem                    # SSL certificate
│   ├── key.pem                     # Private key
│   ├── bundle.pem                  # Certificate bundle
│   └── ssl_config.json             # SSL configuration
├── config/
│   ├── service_mesh_security.json  # Service security config
│   ├── health_checks.json          # Health monitoring
│   └── secure-akash-deployment.yaml # Akash manifest
├── docker/
│   ├── nginx-ssl.conf              # Nginx SSL configuration
│   ├── supervisord-ssl.conf        # API service supervisor
│   ├── supervisord-gpu-ssl.conf    # GPU service supervisor
│   ├── ssl-handler.sh              # SSL certificate handler
│   └── gpu-ssl-handler.sh          # GPU SSL handler
└── akash_deployments/
    ├── deployment-domain.yaml      # Domain-specific manifest
    ├── metadata-domain.json        # Deployment metadata
    └── active-domain.json          # Active deployment info
```

## 🏗️ Docker Images

### Secure Images Built
- `ghcr.io/omega-pro-ai/omega-api:latest` - API service with SSL
- `ghcr.io/omega-pro-ai/omega-gpu:latest` - GPU service with SSL

### Key Security Features
- Non-root user execution
- SSL/TLS 1.2+ enforcement
- Security headers implementation
- Rate limiting and CORS protection
- GPU memory monitoring
- Health checks and monitoring

## 🔐 SSL/TLS Security Features

### Certificate Management
- Automatic certificate generation
- Certificate rotation support
- Expiration monitoring and alerts
- Self-signed and Let's Encrypt support

### Security Configurations
- TLS 1.2+ enforcement
- Strong cipher suites
- HSTS headers
- Content Security Policy
- Rate limiting
- CORS protection

## 📊 Monitoring & Health Checks

### Service Health Monitoring
```bash
# Check all service health
python scripts/service_mesh_security.py health-check

# Monitor continuously
python scripts/service_mesh_security.py monitor --interval 60
```

### SSL Certificate Monitoring
```bash
# Check certificate status
python scripts/ssl_cert_manager.py status

# Monitor certificate expiration
python scripts/ssl_cert_manager.py monitor
```

### Deployment Status
```bash
# Check deployment status
python scripts/akash_deployment_manager.py status --domain your-domain.com

# List all deployments
python scripts/akash_deployment_manager.py list
```

## 🔄 Certificate Rotation

### Manual Renewal
```bash
# Renew SSL certificate
python scripts/ssl_cert_manager.py renew \
  --domain your-domain.com \
  --email your-email@example.com
```

### Automatic Renewal
The deployment includes automatic certificate monitoring that:
- Checks certificate expiration daily
- Sends alerts when certificates expire within 7 days
- Supports auto-renewal for Let's Encrypt certificates

## 🌐 Network Configuration

### Akash Network Settings
- **Chain ID**: `akashnet-2`
- **RPC Endpoints**: Multiple fallback endpoints for reliability
- **Gas Prices**: `0.025uakt`
- **Provider Selection**: Automatic best-price selection

### Port Configuration
- **80**: HTTP (redirects to HTTPS)
- **443**: HTTPS (main API)
- **8001**: Internal GPU service (SSL-secured)
- **6379**: Redis (internal only)

## 💡 iOS Development Integration

### API Endpoints for iOS
```swift
// Production endpoint
let apiURL = "https://your-domain.com/api/v1"

// Health check
let healthURL = "https://your-domain.com/health"

// WebSocket for real-time updates
let wsURL = "wss://your-domain.com/ws"
```

### SSL Certificate Handling
The deployment is configured to work seamlessly with iOS applications:
- Valid SSL certificates (self-signed or CA-issued)
- CORS headers configured for mobile access
- WebSocket support for real-time features

## 🚨 Troubleshooting

### Common Issues

#### 1. SSL Certificate Issues
```bash
# Test SSL connection
python scripts/ssl_cert_manager.py test --domain your-domain.com

# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout
```

#### 2. Docker Image Issues
```bash
# Check if images are accessible
docker manifest inspect ghcr.io/omega-pro-ai/omega-api:latest

# Build images locally if needed
docker build -f Dockerfile.secure-api -t omega-api:latest .
docker build -f Dockerfile.secure-gpu -t omega-gpu:latest .
```

#### 3. Akash Deployment Issues
```bash
# Check wallet balance
akash query bank balances $(akash keys show wallet -a) --node https://rpc.akashnet.net:443

# Verify certificate
akash query cert list --owner $(akash keys show wallet -a) --node https://rpc.akashnet.net:443

# Check deployment logs
akash provider lease-logs --from wallet --dseq DSEQ --provider PROVIDER --node https://rpc.akashnet.net:443
```

#### 4. GPU Service Issues
```bash
# Check GPU availability
nvidia-smi

# Test CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU service logs
docker logs omega-gpu-container
```

### Performance Optimization

#### GPU Memory Management
- Automatic GPU memory monitoring
- Memory cleanup after processing
- Configurable memory limits

#### API Performance
- Connection pooling
- Request rate limiting
- Response caching
- Load balancing ready

## 🔒 Security Best Practices

### Implemented Security Measures
1. **SSL/TLS Encryption**: End-to-end encryption
2. **Authentication**: JWT-based API authentication
3. **Rate Limiting**: DDoS protection
4. **Input Validation**: SQL injection prevention
5. **Security Headers**: XSS and clickjacking protection
6. **Container Security**: Non-root execution
7. **Network Isolation**: Service mesh security

### Additional Recommendations
1. Regular security updates
2. Log monitoring and analysis
3. Intrusion detection system
4. Regular security audits
5. Backup and disaster recovery

## 📞 Support & Maintenance

### Health Monitoring
- Automated health checks every 30-45 seconds
- SSL certificate expiration monitoring
- GPU performance monitoring
- Service availability alerts

### Maintenance Tasks
- SSL certificate renewal
- Docker image updates
- Security patch deployment
- Performance monitoring
- Log rotation and cleanup

## 💰 Cost Optimization

### Akash Network Pricing
- **RTX 4090**: ~$0.30/hour (vs $4.00 on AWS)
- **Tesla T4**: ~$0.15/hour (vs $0.50 on GCP)
- **24/7 Operation**: ~$100-200/month

### Cost Management
- Automatic provider selection for best prices
- Resource usage monitoring
- Deployment scaling options
- Cost alerting and budgeting

---

## 🎯 Quick Commands Reference

```bash
# Deploy complete system
./scripts/akash_deployment_manager.py deploy --domain example.com --email admin@example.com --wallet mywallet

# Check status
./scripts/akash_deployment_manager.py status --domain example.com

# Monitor health
./scripts/service_mesh_security.py monitor

# Renew SSL
./scripts/ssl_cert_manager.py renew --domain example.com --email admin@example.com

# Close deployment
./scripts/akash_deployment_manager.py close --domain example.com --wallet mywallet
```

This deployment provides enterprise-grade security, monitoring, and reliability for OMEGA Pro AI on the Akash Network, with seamless integration for iOS development workflows.