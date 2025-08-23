# OMEGA Infrastructure as Code

This directory contains Terraform configurations for deploying the OMEGA AI system infrastructure using Infrastructure as Code (IaC) principles.

## Overview

The infrastructure deployment includes:

- **OMEGA API Service**: Main prediction API with ML models
- **OMEGA GPU Service**: GPU-accelerated inference service (optional)
- **OMEGA UI**: Web interface for user interactions
- **Redis**: Caching and session management
- **PostgreSQL**: Persistent data storage (optional)
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Visualization and alerting dashboard
- **Traefik**: Reverse proxy and load balancer
- **SSL/TLS**: Automated certificate management

## Prerequisites

1. **Terraform**: Install Terraform >= 1.0
   ```bash
   # macOS
   brew install terraform
   
   # Ubuntu/Debian
   sudo apt-get update && sudo apt-get install terraform
   ```

2. **Docker**: Ensure Docker is running
   ```bash
   docker --version
   docker-compose --version
   ```

3. **Docker Images**: Build or pull the required OMEGA images
   ```bash
   # Build images
   docker build -t omega-api:latest -f ../Dockerfile ../
   docker build -t omega-gpu:latest -f ../Dockerfile.gpu ../
   docker build -t omega-ui:latest -f ../ui/Dockerfile.ui ../ui/
   ```

## Quick Start

1. **Copy configuration template**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit configuration**:
   ```bash
   nano terraform.tfvars
   ```
   Update variables according to your requirements.

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Plan deployment**:
   ```bash
   terraform plan
   ```

5. **Deploy infrastructure**:
   ```bash
   terraform apply
   ```

6. **Access services**:
   - API: http://localhost:8000
   - GPU API: http://localhost:8001 (if enabled)
   - UI: http://localhost:3000 (if enabled)
   - Grafana: http://localhost:3001
   - Prometheus: http://localhost:9090
   - Traefik Dashboard: http://localhost:8888

## Configuration Options

### Environment Configurations

#### Development
```hcl
environment = "development"
enable_debug_mode = true
enable_hot_reload = true
mount_source_code = true
log_level = "DEBUG"
```

#### Staging
```hcl
environment = "staging"
enable_monitoring = true
enable_ssl = true
api_replicas = 2
```

#### Production
```hcl
environment = "production"
enable_ssl = true
enable_monitoring = true
enable_backups = true
enable_autoscaling = true
api_replicas = 3
autoscaling_max_replicas = 10
```

### Service Options

```hcl
# Core services
enable_redis = true
enable_postgres = true
enable_gpu_service = true
enable_ui = true

# Monitoring stack
enable_monitoring = true
enable_traefik = true

# Security
enable_ssl = true
ssl_cert_path = "../ssl/cert.pem"
ssl_key_path = "../ssl/key.pem"
```

### Resource Limits

```hcl
# API service resources
api_memory_limit = 4096  # MB
api_cpu_limit = 4        # cores

# GPU service resources
gpu_memory_limit = 8192  # MB
gpu_cpu_limit = 8        # cores
```

## File Structure

```
terraform/
├── main.tf                    # Main infrastructure configuration
├── variables.tf               # Variable definitions
├── outputs.tf                 # Output definitions
├── terraform.tfvars.example  # Configuration template
├── templates/                 # Configuration templates
│   ├── prometheus.yml.tpl     # Prometheus configuration
│   ├── api.env.tpl           # API environment template
│   ├── traefik.yml.tpl       # Traefik static configuration
│   └── traefik-dynamic.yml.tpl # Traefik dynamic configuration
├── config/                   # Generated configurations
└── README.md                 # This file
```

## Advanced Usage

### Custom Network Configuration

```hcl
custom_network_cidr = "192.168.100.0/24"
```

### GPU Support

```hcl
enable_gpu_service = true
gpu_image_tag = "omega-gpu:cuda-11.8"
```

### High Availability Setup

```hcl
api_replicas = 3
enable_autoscaling = true
autoscaling_min_replicas = 2
autoscaling_max_replicas = 10
autoscaling_cpu_threshold = 70
```

### Database Configuration

```hcl
enable_postgres = true
database_name = "omega_production"
database_user = "omega_user"
database_password = "secure_random_password"
```

### SSL/TLS Configuration

```hcl
enable_ssl = true
ssl_cert_path = "/path/to/certificate.pem"
ssl_key_path = "/path/to/private_key.pem"
```

## Monitoring and Observability

### Prometheus Metrics

Access Prometheus at http://localhost:9090 to view:

- API response times
- Prediction accuracy metrics
- System resource usage
- Error rates and alerts

### Grafana Dashboards

Access Grafana at http://localhost:3001 with:
- Username: `admin`
- Password: (set in `grafana_admin_password`)

Pre-configured dashboards:
- OMEGA API Performance
- System Resource Usage
- Prediction Analytics
- Error Tracking

### Health Checks

All services include health check endpoints:

```bash
# Check API health
curl http://localhost:8000/health

# Check GPU service health
curl http://localhost:8001/health

# Check overall system health
terraform output health_check_urls
```

## Backup and Recovery

### Automated Backups

```hcl
enable_backups = true
backup_schedule = "0 2 * * *"  # Daily at 2 AM
backup_retention_days = 30
```

### Manual Backup

```bash
# Backup Redis data
docker exec omega-redis-production redis-cli BGSAVE

# Backup PostgreSQL data
docker exec omega-postgres-production pg_dump -U omega_user omega_ai > backup.sql

# Backup Docker volumes
docker run --rm -v omega-prometheus-data-production:/data -v $(pwd):/backup ubuntu tar czf /backup/prometheus-backup.tar.gz -C /data .
```

## Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Check port usage
   netstat -tulpn | grep :8000
   
   # Stop conflicting services
   sudo systemctl stop apache2
   ```

2. **Docker permission issues**:
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **SSL certificate issues**:
   ```bash
   # Generate self-signed certificates
   mkdir -p ../ssl
   openssl req -x509 -newkey rsa:4096 -keyout ../ssl/key.pem -out ../ssl/cert.pem -days 365 -nodes
   ```

### Debug Commands

```bash
# View Terraform state
terraform show

# Debug specific resource
terraform show docker_container.omega_api

# View container logs
docker logs $(terraform output -raw api_container_name)

# Execute commands in containers
docker exec -it $(terraform output -raw api_container_name) /bin/bash
```

### Performance Tuning

```hcl
# Increase API workers
api_replicas = 5

# Optimize memory usage
api_memory_limit = 8192

# Enable GPU acceleration
enable_gpu_service = true
```

## Security Considerations

1. **Change default passwords**:
   - Update `grafana_admin_password`
   - Set strong `database_password`

2. **Use proper SSL certificates**:
   - Replace self-signed certificates with CA-signed ones
   - Configure proper domain names

3. **Network security**:
   - Use custom network CIDR
   - Implement proper firewall rules

4. **Access control**:
   - Enable authentication on sensitive endpoints
   - Use Traefik middleware for rate limiting

## Maintenance

### Updates

```bash
# Update Terraform configuration
terraform plan
terraform apply

# Update Docker images
docker pull omega-api:latest
terraform apply -replace="docker_container.omega_api"
```

### Scaling

```bash
# Scale API service
terraform apply -var="api_replicas=5"

# Enable autoscaling
terraform apply -var="enable_autoscaling=true"
```

### Cleanup

```bash
# Destroy specific resources
terraform destroy -target="docker_container.omega_ui"

# Destroy all infrastructure
terraform destroy
```

## Integration with CI/CD

This Terraform configuration integrates with the GitHub Actions workflows:

- **Development**: Automatic deployment on feature branches
- **Staging**: Deployment on PR merge to main
- **Production**: Manual approval required

### Environment Variables for CI/CD

```yaml
env:
  TF_VAR_environment: ${{ matrix.environment }}
  TF_VAR_api_image_tag: ${{ github.sha }}
  TF_VAR_enable_monitoring: true
```

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review Terraform and Docker logs
3. Consult the main project documentation
4. Submit issues to the project repository