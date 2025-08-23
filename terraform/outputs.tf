# OMEGA Infrastructure Outputs

output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "domain_name" {
  description = "Domain name for OMEGA services"
  value       = var.domain_name
}

# Network information
output "network_id" {
  description = "Docker network ID"
  value       = docker_network.omega_network.id
}

output "network_name" {
  description = "Docker network name"
  value       = docker_network.omega_network.name
}

# Service endpoints
output "api_endpoint" {
  description = "OMEGA API endpoint"
  value       = "http://localhost:8000"
}

output "api_health_endpoint" {
  description = "OMEGA API health check endpoint"
  value       = "http://localhost:8000/health"
}

output "gpu_endpoint" {
  description = "OMEGA GPU service endpoint"
  value       = var.enable_gpu_service ? "http://localhost:8001" : null
}

output "ui_endpoint" {
  description = "OMEGA UI endpoint"
  value       = var.enable_ui ? "http://localhost:3000" : null
}

output "traefik_dashboard" {
  description = "Traefik dashboard endpoint"
  value       = var.enable_traefik ? "http://localhost:8888" : null
  sensitive   = false
}

# Database information
output "database_host" {
  description = "Database host"
  value       = var.enable_postgres ? "localhost" : null
}

output "database_port" {
  description = "Database port"
  value       = var.enable_postgres ? 5432 : null
}

output "database_name" {
  description = "Database name"
  value       = var.enable_postgres ? var.database_name : null
}

# Redis information
output "redis_host" {
  description = "Redis host"
  value       = var.enable_redis ? "localhost" : null
}

output "redis_port" {
  description = "Redis port"
  value       = var.enable_redis ? 6379 : null
}

# Monitoring endpoints
output "prometheus_endpoint" {
  description = "Prometheus endpoint"
  value       = var.enable_monitoring ? "http://localhost:9090" : null
}

output "grafana_endpoint" {
  description = "Grafana endpoint"
  value       = var.enable_monitoring ? "http://localhost:3001" : null
}

output "grafana_admin_user" {
  description = "Grafana admin username"
  value       = var.enable_monitoring ? "admin" : null
}

# SSL/TLS information
output "ssl_enabled" {
  description = "Whether SSL/TLS is enabled"
  value       = var.enable_ssl
}

output "ssl_certificate_path" {
  description = "SSL certificate file path"
  value       = var.enable_ssl ? var.ssl_cert_path : null
}

# Container information
output "api_container_id" {
  description = "API container ID"
  value       = docker_container.omega_api.id
  sensitive   = false
}

output "api_container_name" {
  description = "API container name"
  value       = docker_container.omega_api.name
}

output "gpu_container_id" {
  description = "GPU service container ID"
  value       = var.enable_gpu_service ? docker_container.omega_gpu[0].id : null
  sensitive   = false
}

output "ui_container_id" {
  description = "UI container ID"
  value       = var.enable_ui ? docker_container.omega_ui[0].id : null
  sensitive   = false
}

output "redis_container_id" {
  description = "Redis container ID"
  value       = var.enable_redis ? docker_container.redis[0].id : null
  sensitive   = false
}

output "postgres_container_id" {
  description = "PostgreSQL container ID"
  value       = var.enable_postgres ? docker_container.postgres[0].id : null
  sensitive   = false
}

# Volume information
output "redis_volume_name" {
  description = "Redis data volume name"
  value       = var.enable_redis ? docker_volume.redis_data[0].name : null
}

output "postgres_volume_name" {
  description = "PostgreSQL data volume name"
  value       = var.enable_postgres ? docker_volume.postgres_data[0].name : null
}

output "prometheus_volume_name" {
  description = "Prometheus data volume name"
  value       = var.enable_monitoring ? docker_volume.prometheus_data[0].name : null
}

output "grafana_volume_name" {
  description = "Grafana data volume name"
  value       = var.enable_monitoring ? docker_volume.grafana_data[0].name : null
}

# Security information
output "api_secret_key" {
  description = "API secret key (first 8 characters)"
  value       = "${substr(random_password.api_secret_key.result, 0, 8)}..."
  sensitive   = false
}

output "ssl_ca_cert_pem" {
  description = "Generated CA certificate in PEM format"
  value       = tls_self_signed_cert.omega_ca.cert_pem
  sensitive   = true
}

output "ssl_server_cert_pem" {
  description = "Generated server certificate in PEM format"
  value       = tls_locally_signed_cert.omega_server.cert_pem
  sensitive   = true
}

# Configuration files
output "configuration_files" {
  description = "Generated configuration files"
  value = {
    api_env_file        = local_file.api_env.filename
    prometheus_config   = var.enable_monitoring ? local_file.prometheus_config[0].filename : null
    traefik_config      = var.enable_traefik ? local_file.traefik_config[0].filename : null
    traefik_dynamic     = var.enable_traefik ? local_file.traefik_dynamic_config[0].filename : null
  }
}

# Deployment information
output "deployment_summary" {
  description = "Deployment summary"
  value = {
    environment         = var.environment
    services_deployed   = {
      api               = true
      gpu               = var.enable_gpu_service
      ui                = var.enable_ui
      redis             = var.enable_redis
      postgres          = var.enable_postgres
      prometheus        = var.enable_monitoring
      grafana           = var.enable_monitoring
      traefik           = var.enable_traefik
    }
    total_containers    = 1 + (var.enable_gpu_service ? 1 : 0) + (var.enable_ui ? 1 : 0) + (var.enable_redis ? 1 : 0) + (var.enable_postgres ? 1 : 0) + (var.enable_monitoring ? 2 : 0) + (var.enable_traefik ? 1 : 0)
    deployment_time     = timestamp()
  }
}

# Health check URLs
output "health_check_urls" {
  description = "Health check URLs for all services"
  value = {
    api         = "http://localhost:8000/health"
    gpu         = var.enable_gpu_service ? "http://localhost:8001/health" : null
    ui          = var.enable_ui ? "http://localhost:3000/" : null
    redis       = var.enable_redis ? "redis://localhost:6379" : null
    postgres    = var.enable_postgres ? "postgresql://localhost:5432/${var.database_name}" : null
    prometheus  = var.enable_monitoring ? "http://localhost:9090/-/healthy" : null
    grafana     = var.enable_monitoring ? "http://localhost:3001/api/health" : null
  }
}

# Docker commands for management
output "management_commands" {
  description = "Useful Docker commands for managing the deployment"
  value = {
    view_logs = {
      api       = "docker logs ${docker_container.omega_api.name}"
      gpu       = var.enable_gpu_service ? "docker logs ${docker_container.omega_gpu[0].name}" : null
      ui        = var.enable_ui ? "docker logs ${docker_container.omega_ui[0].name}" : null
      redis     = var.enable_redis ? "docker logs ${docker_container.redis[0].name}" : null
      postgres  = var.enable_postgres ? "docker logs ${docker_container.postgres[0].name}" : null
    }
    exec_into = {
      api       = "docker exec -it ${docker_container.omega_api.name} /bin/bash"
      gpu       = var.enable_gpu_service ? "docker exec -it ${docker_container.omega_gpu[0].name} /bin/bash" : null
      ui        = var.enable_ui ? "docker exec -it ${docker_container.omega_ui[0].name} /bin/sh" : null
      redis     = var.enable_redis ? "docker exec -it ${docker_container.redis[0].name} redis-cli" : null
      postgres  = var.enable_postgres ? "docker exec -it ${docker_container.postgres[0].name} psql -U ${var.database_user} -d ${var.database_name}" : null
    }
    restart = {
      api       = "docker restart ${docker_container.omega_api.name}"
      gpu       = var.enable_gpu_service ? "docker restart ${docker_container.omega_gpu[0].name}" : null
      ui        = var.enable_ui ? "docker restart ${docker_container.omega_ui[0].name}" : null
      redis     = var.enable_redis ? "docker restart ${docker_container.redis[0].name}" : null
      postgres  = var.enable_postgres ? "docker restart ${docker_container.postgres[0].name}" : null
    }
  }
}