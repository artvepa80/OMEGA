# OMEGA PRO AI v10.1 - Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying OMEGA PRO AI v10.1 to production environments. The system is designed for high availability, scalability, and robust monitoring across multiple deployment platforms.

## Quick Start

```bash
# Deploy locally with monitoring
./scripts/deploy-production.sh local

# Deploy to Railway
./scripts/deploy-production.sh railway

# Deploy to all platforms (dry run)
./scripts/deploy-production.sh all false false true
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   OMEGA API     │────│     Redis       │
│    (HAProxy)    │    │   (Primary)     │    │    (Cache)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │              ┌─────────────────┐                │
         └──────────────│   OMEGA API     │────────────────┘
                        │  (Secondary)    │
                        └─────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │────│   Monitoring    │────│    Grafana      │
│   (Metrics)     │    │     Stack       │    │  (Dashboards)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Deployment Platforms

### 1. Docker Compose (Recommended for Self-Hosting)

**Features:**
- High availability with primary/secondary API instances
- Load balancing with HAProxy
- Comprehensive monitoring (Prometheus, Grafana, ELK Stack)
- Automated backups
- SSL/TLS termination

**Requirements:**
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum, 8GB recommended
- 20GB disk space

**Deployment:**
```bash
# Copy production environment
cp .env.production .env

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Monitor deployment
docker-compose -f docker-compose.prod.yml logs -f
```

**Access Points:**
- API: https://localhost/api/
- Grafana: http://localhost:3000 (admin/omega123)
- Prometheus: http://localhost:9090
- HAProxy Stats: http://localhost:8404/stats

### 2. Railway Platform

**Features:**
- Managed infrastructure
- Auto-scaling
- Git-based deployments
- Built-in monitoring

**Setup:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway link

# Deploy
railway deploy
```

**Configuration:**
- Uses `railway.toml` for configuration
- Auto-detects from `Dockerfile`
- Environment variables managed through Railway dashboard

### 3. Akash Network (Decentralized Cloud)

**Features:**
- Decentralized infrastructure
- Cost-effective
- Global distribution
- Kubernetes-based

**Prerequisites:**
```bash
# Install Akash CLI
curl -sSfL https://raw.githubusercontent.com/akash-network/akash/master/godownloader.sh | sh

# Setup wallet and certificates (see Akash documentation)
```

**Deployment Files:**
- `deploy/production-akash-secure.yaml` - Main deployment
- `deploy/akash-load-balancer.yaml` - Load balancer
- `deploy/akash-firewall-rules.yaml` - Security rules

### 4. Vercel (Serverless)

**Features:**
- Serverless deployment
- Global edge network
- Zero-config deployments

**Limitations:**
- Function timeout limits
- No persistent storage
- Limited to HTTP/REST API

**Setup:**
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

## Environment Configuration

### Production Environment Variables

Create `.env.production` with the following key configurations:

```env
# Application
ENVIRONMENT=production
DEBUG=false
WORKERS=3

# Security
JWT_SECRET=your-secure-jwt-secret
VERIFY_SIGNATURE=true
CORS_ORIGINS=https://yourdomain.com

# Database & Cache
REDIS_URL=redis://redis:6379

# Monitoring
PROMETHEUS_METRICS=true
GRAFANA_ADMIN_PASSWORD=secure-password

# API Keys (configure as needed)
TWILIO_ACCOUNT_SID=your_sid
WHATSAPP_TOKEN=your_token
```

### Security Considerations

1. **Secrets Management:**
   ```bash
   # Use Docker secrets for sensitive data
   echo "your-jwt-secret" | docker secret create jwt_secret -
   ```

2. **SSL/TLS:**
   ```bash
   # Generate SSL certificates
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout ssl/omega.key -out ssl/omega.crt
   ```

3. **Firewall Rules:**
   - Only allow necessary ports (80, 443)
   - Restrict admin interfaces to authorized IPs
   - Use VPN for internal monitoring tools

## Health Checks & Monitoring

### Health Endpoints

- `/health` - Basic health check
- `/ready` - Kubernetes readiness probe
- `/metrics` - Prometheus metrics
- `/system/status` - Detailed system status

### Monitoring Stack

1. **Prometheus Metrics:**
   - API response times
   - Request rates
   - Error rates
   - Resource utilization

2. **Grafana Dashboards:**
   - System overview
   - API performance
   - ML model metrics
   - Alert management

3. **Log Aggregation:**
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Structured JSON logging
   - Log retention policies

### Alerting Rules

Create `config/prometheus/alerts/omega-alerts.yml`:

```yaml
groups:
  - name: omega.rules
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~\"5..\"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High error rate detected

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Service is down
```

## Performance Optimization

### Resource Allocation

```yaml
# Docker Compose resource limits
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2.0'
    reservations:
      memory: 1G
      cpus: '1.0'
```

### Caching Strategy

1. **Redis Configuration:**
   - Memory limit: 512MB
   - Eviction policy: allkeys-lru
   - Persistence: AOF + RDB snapshots

2. **Application Caching:**
   - API response caching
   - Model prediction caching
   - Static asset caching

### Database Optimization

```bash
# Redis performance tuning
echo 'vm.overcommit_memory = 1' >> /etc/sysctl.conf
echo 'net.core.somaxconn = 65535' >> /etc/sysctl.conf
sysctl -p
```

## Backup & Recovery

### Automated Backups

The production deployment includes automated backup service:

```yaml
backup:
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention: 30 days
  destinations:
    - redis_data
    - application_data
    - model_files
```

### Recovery Procedures

1. **Data Recovery:**
   ```bash
   # Restore Redis data
   docker run --rm -v redis_data:/data -v ./backups:/backup \
     redis:7-alpine sh -c "cp /backup/latest.rdb /data/dump.rdb"
   ```

2. **Service Recovery:**
   ```bash
   # Rolling restart
   docker-compose -f docker-compose.prod.yml restart omega_api_primary
   # Wait for health check, then restart secondary
   docker-compose -f docker-compose.prod.yml restart omega_api_secondary
   ```

## Troubleshooting

### Common Issues

1. **Service Won't Start:**
   ```bash
   # Check logs
   docker-compose -f docker-compose.prod.yml logs omega_api_primary
   
   # Check health
   curl -f http://localhost:8000/health
   ```

2. **High Memory Usage:**
   ```bash
   # Monitor resources
   docker stats
   
   # Adjust memory limits in docker-compose.prod.yml
   ```

3. **SSL Certificate Issues:**
   ```bash
   # Verify certificate
   openssl x509 -in ssl/omega.crt -text -noout
   
   # Test SSL
   openssl s_client -connect localhost:443
   ```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Temporary debug deployment
ENVIRONMENT=debug docker-compose -f docker-compose.prod.yml up
```

## Maintenance

### Regular Maintenance Tasks

1. **Weekly:**
   - Review monitoring alerts
   - Check disk usage
   - Verify backup integrity

2. **Monthly:**
   - Update dependencies
   - Security patches
   - Performance review

3. **Quarterly:**
   - Disaster recovery testing
   - Capacity planning
   - Security audit

### Update Procedures

```bash
# Rolling update
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d --no-deps omega_api_secondary
# Wait for health check
docker-compose -f docker-compose.prod.yml up -d --no-deps omega_api_primary
```

## Security Best Practices

1. **Container Security:**
   - Non-root user
   - Read-only root filesystem
   - Minimal base images
   - Regular security scanning

2. **Network Security:**
   - Network segmentation
   - TLS encryption
   - Rate limiting
   - DDoS protection

3. **Access Control:**
   - API key authentication
   - JWT token validation
   - Role-based access control
   - Audit logging

## Support & Documentation

### Additional Resources

- [Akash Network Documentation](https://docs.akash.network/)
- [Railway Documentation](https://docs.railway.app/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Prometheus Documentation](https://prometheus.io/docs/)

### Getting Help

1. Check monitoring dashboards for system status
2. Review application logs for errors
3. Run health checks to identify issues
4. Consult troubleshooting section above

## Deployment Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] SSL certificates generated
- [ ] Dependencies installed
- [ ] Tests passing
- [ ] Security scan completed

### Deployment

- [ ] Deploy with zero downtime
- [ ] Health checks passing
- [ ] Monitoring active
- [ ] Backups configured
- [ ] Load balancer healthy

### Post-Deployment

- [ ] Performance metrics normal
- [ ] Error rates acceptable
- [ ] SSL certificate valid
- [ ] Monitoring alerts configured
- [ ] Documentation updated

---

**Last Updated:** August 15, 2025  
**Version:** 10.1  
**Status:** Production Ready