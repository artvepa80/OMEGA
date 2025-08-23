# OMEGA Infrastructure as Code - Main Configuration
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
  
  # Remote state configuration (uncomment for production)
  # backend "s3" {
  #   bucket = "omega-terraform-state"
  #   key    = "infrastructure/terraform.tfstate"
  #   region = "us-west-2"
  # }
}

# Local variables
locals {
  project_name = "omega-pro-ai"
  environment  = var.environment
  
  common_tags = {
    Project     = local.project_name
    Environment = local.environment
    ManagedBy   = "terraform"
    CreatedAt   = timestamp()
  }
  
  # Network configuration
  network_config = {
    api_port      = 8000
    gpu_api_port  = 8001
    ui_port       = 3000
    redis_port    = 6379
    prometheus_port = 9090
    grafana_port  = 3001
  }
}

# Random password generation for services
resource "random_password" "redis_password" {
  length  = 32
  special = true
}

resource "random_password" "api_secret_key" {
  length  = 64
  special = true
}

# TLS certificates for secure communication
resource "tls_private_key" "omega_ca" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "tls_self_signed_cert" "omega_ca" {
  private_key_pem = tls_private_key.omega_ca.private_key_pem
  
  subject {
    common_name  = "OMEGA CA"
    organization = "OMEGA Pro AI"
  }
  
  validity_period_hours = 8760 # 1 year
  is_ca_certificate     = true
  
  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "cert_signing",
  ]
}

resource "tls_private_key" "omega_server" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "tls_cert_request" "omega_server" {
  private_key_pem = tls_private_key.omega_server.private_key_pem
  
  subject {
    common_name  = var.domain_name
    organization = "OMEGA Pro AI"
  }
  
  dns_names = [
    var.domain_name,
    "*.${var.domain_name}",
    "localhost",
    "omega-api",
    "omega-gpu",
    "omega-ui"
  ]
  
  ip_addresses = [
    "127.0.0.1",
    "0.0.0.0"
  ]
}

resource "tls_locally_signed_cert" "omega_server" {
  cert_request_pem   = tls_cert_request.omega_server.cert_request_pem
  ca_private_key_pem = tls_private_key.omega_ca.private_key_pem
  ca_cert_pem        = tls_self_signed_cert.omega_ca.cert_pem
  
  validity_period_hours = 8760 # 1 year
  
  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
  ]
}

# Docker network for OMEGA services
resource "docker_network" "omega_network" {
  name = "${local.project_name}-network-${local.environment}"
  
  driver = "bridge"
  
  ipam_config {
    subnet  = "172.20.0.0/16"
    gateway = "172.20.0.1"
  }
  
  labels = {
    for k, v in local.common_tags : k => v
  }
}

# Redis service for caching and session management
resource "docker_volume" "redis_data" {
  name = "${local.project_name}-redis-data-${local.environment}"
  
  labels = {
    for k, v in local.common_tags : k => v
  }
}

resource "docker_container" "redis" {
  count = var.enable_redis ? 1 : 0
  
  name  = "${local.project_name}-redis-${local.environment}"
  image = "redis:7-alpine"
  
  restart = "unless-stopped"
  
  ports {
    internal = local.network_config.redis_port
    external = local.network_config.redis_port
  }
  
  networks_advanced {
    name = docker_network.omega_network.name
    aliases = ["redis"]
  }
  
  volumes {
    volume_name    = docker_volume.redis_data[0].name
    container_path = "/data"
  }
  
  command = [
    "redis-server",
    "--requirepass", random_password.redis_password.result,
    "--appendonly", "yes",
    "--maxmemory", "512mb",
    "--maxmemory-policy", "allkeys-lru"
  ]
  
  labels = {
    for k, v in merge(local.common_tags, {
      "omega.service" = "redis"
      "omega.type"    = "cache"
    }) : k => v
  }
  
  healthcheck {
    test     = ["CMD", "redis-cli", "--raw", "incr", "ping"]
    interval = "10s"
    timeout  = "3s"
    retries  = 3
  }
}

# PostgreSQL database for persistent data
resource "docker_volume" "postgres_data" {
  count = var.enable_postgres ? 1 : 0
  
  name = "${local.project_name}-postgres-data-${local.environment}"
  
  labels = {
    for k, v in local.common_tags : k => v
  }
}

resource "docker_container" "postgres" {
  count = var.enable_postgres ? 1 : 0
  
  name  = "${local.project_name}-postgres-${local.environment}"
  image = "postgres:15-alpine"
  
  restart = "unless-stopped"
  
  ports {
    internal = 5432
    external = 5432
  }
  
  networks_advanced {
    name = docker_network.omega_network.name
    aliases = ["postgres", "database"]
  }
  
  volumes {
    volume_name    = docker_volume.postgres_data[0].name
    container_path = "/var/lib/postgresql/data"
  }
  
  env = [
    "POSTGRES_DB=${var.database_name}",
    "POSTGRES_USER=${var.database_user}",
    "POSTGRES_PASSWORD=${var.database_password}",
    "PGDATA=/var/lib/postgresql/data/pgdata"
  ]
  
  labels = {
    for k, v in merge(local.common_tags, {
      "omega.service" = "postgres"
      "omega.type"    = "database"
    }) : k => v
  }
  
  healthcheck {
    test     = ["CMD-SHELL", "pg_isready -U ${var.database_user} -d ${var.database_name}"]
    interval = "10s"
    timeout  = "5s"
    retries  = 5
  }
}

# Monitoring stack - Prometheus
resource "docker_volume" "prometheus_data" {
  count = var.enable_monitoring ? 1 : 0
  
  name = "${local.project_name}-prometheus-data-${local.environment}"
  
  labels = {
    for k, v in local.common_tags : k => v
  }
}

resource "local_file" "prometheus_config" {
  count = var.enable_monitoring ? 1 : 0
  
  filename = "${path.module}/config/prometheus.yml"
  content = templatefile("${path.module}/templates/prometheus.yml.tpl", {
    environment = local.environment
    api_port    = local.network_config.api_port
    gpu_port    = local.network_config.gpu_api_port
  })
}

resource "docker_container" "prometheus" {
  count = var.enable_monitoring ? 1 : 0
  
  name  = "${local.project_name}-prometheus-${local.environment}"
  image = "prom/prometheus:v2.47.0"
  
  restart = "unless-stopped"
  
  ports {
    internal = local.network_config.prometheus_port
    external = local.network_config.prometheus_port
  }
  
  networks_advanced {
    name = docker_network.omega_network.name
    aliases = ["prometheus"]
  }
  
  volumes {
    volume_name    = docker_volume.prometheus_data[0].name
    container_path = "/prometheus"
  }
  
  volumes {
    host_path      = abspath(local_file.prometheus_config[0].filename)
    container_path = "/etc/prometheus/prometheus.yml"
    read_only      = true
  }
  
  command = [
    "--config.file=/etc/prometheus/prometheus.yml",
    "--storage.tsdb.path=/prometheus",
    "--web.console.libraries=/etc/prometheus/console_libraries",
    "--web.console.templates=/etc/prometheus/consoles",
    "--storage.tsdb.retention.time=30d",
    "--web.enable-lifecycle"
  ]
  
  labels = {
    for k, v in merge(local.common_tags, {
      "omega.service" = "prometheus"
      "omega.type"    = "monitoring"
    }) : k => v
  }
  
  depends_on = [local_file.prometheus_config]
}

# Monitoring stack - Grafana
resource "docker_volume" "grafana_data" {
  count = var.enable_monitoring ? 1 : 0
  
  name = "${local.project_name}-grafana-data-${local.environment}"
  
  labels = {
    for k, v in local.common_tags : k => v
  }
}

resource "docker_container" "grafana" {
  count = var.enable_monitoring ? 1 : 0
  
  name  = "${local.project_name}-grafana-${local.environment}"
  image = "grafana/grafana:10.2.0"
  
  restart = "unless-stopped"
  
  ports {
    internal = local.network_config.grafana_port
    external = local.network_config.grafana_port
  }
  
  networks_advanced {
    name = docker_network.omega_network.name
    aliases = ["grafana"]
  }
  
  volumes {
    volume_name    = docker_volume.grafana_data[0].name
    container_path = "/var/lib/grafana"
  }
  
  env = [
    "GF_SECURITY_ADMIN_PASSWORD=${var.grafana_admin_password}",
    "GF_USERS_ALLOW_SIGN_UP=false",
    "GF_INSTALL_PLUGINS=redis-datasource,postgres-datasource"
  ]
  
  labels = {
    for k, v in merge(local.common_tags, {
      "omega.service" = "grafana"
      "omega.type"    = "monitoring"
    }) : k => v
  }
  
  depends_on = [docker_container.prometheus]
}

# OMEGA API Service
resource "local_file" "api_env" {
  filename = "${path.module}/config/.env.api"
  content = templatefile("${path.module}/templates/api.env.tpl", {
    environment     = local.environment
    redis_host      = var.enable_redis ? "redis" : "localhost"
    redis_port      = local.network_config.redis_port
    redis_password  = random_password.redis_password.result
    database_url    = var.enable_postgres ? "postgresql://${var.database_user}:${var.database_password}@postgres:5432/${var.database_name}" : ""
    secret_key      = random_password.api_secret_key.result
    api_port        = local.network_config.api_port
  })
  
  depends_on = [
    random_password.redis_password,
    random_password.api_secret_key
  ]
}

resource "docker_container" "omega_api" {
  name  = "${local.project_name}-api-${local.environment}"
  image = var.api_image_tag
  
  restart = "unless-stopped"
  
  ports {
    internal = local.network_config.api_port
    external = local.network_config.api_port
  }
  
  networks_advanced {
    name = docker_network.omega_network.name
    aliases = ["omega-api", "api"]
  }
  
  volumes {
    host_path      = abspath("${path.module}/../data")
    container_path = "/app/data"
    read_only      = true
  }
  
  volumes {
    host_path      = abspath("${path.module}/../models")
    container_path = "/app/models"
    read_only      = true
  }
  
  volumes {
    host_path      = abspath("${path.module}/../ssl")
    container_path = "/app/ssl"
    read_only      = true
  }
  
  volumes {
    host_path      = abspath(local_file.api_env.filename)
    container_path = "/app/.env"
    read_only      = true
  }
  
  env = [
    "OMEGA_ENV=${local.environment}",
    "PYTHONPATH=/app",
    "PORT=${local.network_config.api_port}"
  ]
  
  labels = {
    for k, v in merge(local.common_tags, {
      "omega.service" = "api"
      "omega.type"    = "application"
      "traefik.enable" = "true"
      "traefik.http.routers.omega-api.rule" = "Host(`${var.domain_name}`) && PathPrefix(`/api`)"
      "traefik.http.routers.omega-api.tls" = "true"
    }) : k => v
  }
  
  healthcheck {
    test     = ["CMD", "curl", "-f", "http://localhost:${local.network_config.api_port}/health"]
    interval = "30s"
    timeout  = "10s"
    retries  = 3
  }
  
  depends_on = [
    docker_container.redis,
    docker_container.postgres,
    local_file.api_env
  ]
}

# OMEGA GPU Service (if GPU support enabled)
resource "docker_container" "omega_gpu" {
  count = var.enable_gpu_service ? 1 : 0
  
  name  = "${local.project_name}-gpu-${local.environment}"
  image = var.gpu_image_tag
  
  restart = "unless-stopped"
  
  ports {
    internal = local.network_config.gpu_api_port
    external = local.network_config.gpu_api_port
  }
  
  networks_advanced {
    name = docker_network.omega_network.name
    aliases = ["omega-gpu", "gpu"]
  }
  
  volumes {
    host_path      = abspath("${path.module}/../data")
    container_path = "/app/data"
    read_only      = true
  }
  
  volumes {
    host_path      = abspath("${path.module}/../models")
    container_path = "/app/models"
  }
  
  volumes {
    host_path      = abspath(local_file.api_env.filename)
    container_path = "/app/.env"
    read_only      = true
  }
  
  env = [
    "OMEGA_ENV=${local.environment}",
    "PYTHONPATH=/app",
    "PORT=${local.network_config.gpu_api_port}",
    "CUDA_VISIBLE_DEVICES=0",
    "NVIDIA_VISIBLE_DEVICES=all"
  ]
  
  # GPU runtime configuration
  runtime = "nvidia"
  
  labels = {
    for k, v in merge(local.common_tags, {
      "omega.service" = "gpu"
      "omega.type"    = "application"
      "traefik.enable" = "true"
      "traefik.http.routers.omega-gpu.rule" = "Host(`${var.domain_name}`) && PathPrefix(`/gpu`)"
      "traefik.http.routers.omega-gpu.tls" = "true"
    }) : k => v
  }
  
  healthcheck {
    test     = ["CMD", "curl", "-f", "http://localhost:${local.network_config.gpu_api_port}/health"]
    interval = "30s"
    timeout  = "10s"
    retries  = 3
  }
  
  depends_on = [
    docker_container.redis,
    docker_container.postgres,
    local_file.api_env
  ]
}

# OMEGA UI Service
resource "docker_container" "omega_ui" {
  count = var.enable_ui ? 1 : 0
  
  name  = "${local.project_name}-ui-${local.environment}"
  image = var.ui_image_tag
  
  restart = "unless-stopped"
  
  ports {
    internal = local.network_config.ui_port
    external = local.network_config.ui_port
  }
  
  networks_advanced {
    name = docker_network.omega_network.name
    aliases = ["omega-ui", "ui"]
  }
  
  env = [
    "NODE_ENV=${local.environment}",
    "API_URL=http://omega-api:${local.network_config.api_port}",
    "GPU_API_URL=http://omega-gpu:${local.network_config.gpu_api_port}"
  ]
  
  labels = {
    for k, v in merge(local.common_tags, {
      "omega.service" = "ui"
      "omega.type"    = "frontend"
      "traefik.enable" = "true"
      "traefik.http.routers.omega-ui.rule" = "Host(`${var.domain_name}`)"
      "traefik.http.routers.omega-ui.tls" = "true"
    }) : k => v
  }
  
  healthcheck {
    test     = ["CMD", "curl", "-f", "http://localhost:${local.network_config.ui_port}/"]
    interval = "30s"
    timeout  = "10s"
    retries  = 3
  }
  
  depends_on = [docker_container.omega_api]
}

# Reverse Proxy / Load Balancer - Traefik
resource "local_file" "traefik_config" {
  count = var.enable_traefik ? 1 : 0
  
  filename = "${path.module}/config/traefik.yml"
  content = templatefile("${path.module}/templates/traefik.yml.tpl", {
    environment = local.environment
    domain_name = var.domain_name
  })
}

resource "local_file" "traefik_dynamic_config" {
  count = var.enable_traefik ? 1 : 0
  
  filename = "${path.module}/config/dynamic.yml"
  content = templatefile("${path.module}/templates/traefik-dynamic.yml.tpl", {
    cert_file = "/certs/server.crt"
    key_file  = "/certs/server.key"
  })
}

resource "docker_container" "traefik" {
  count = var.enable_traefik ? 1 : 0
  
  name  = "${local.project_name}-traefik-${local.environment}"
  image = "traefik:v3.0"
  
  restart = "unless-stopped"
  
  ports {
    internal = 80
    external = 80
  }
  
  ports {
    internal = 443
    external = 443
  }
  
  ports {
    internal = 8080
    external = 8888  # Traefik dashboard
  }
  
  networks_advanced {
    name = docker_network.omega_network.name
    aliases = ["traefik", "proxy"]
  }
  
  volumes {
    host_path      = "/var/run/docker.sock"
    container_path = "/var/run/docker.sock"
    read_only      = true
  }
  
  volumes {
    host_path      = abspath(local_file.traefik_config[0].filename)
    container_path = "/etc/traefik/traefik.yml"
    read_only      = true
  }
  
  volumes {
    host_path      = abspath(local_file.traefik_dynamic_config[0].filename)
    container_path = "/etc/traefik/dynamic.yml"
    read_only      = true
  }
  
  volumes {
    host_path      = abspath("${path.module}/../ssl")
    container_path = "/certs"
    read_only      = true
  }
  
  labels = {
    for k, v in merge(local.common_tags, {
      "omega.service" = "traefik"
      "omega.type"    = "proxy"
      "traefik.enable" = "true"
      "traefik.http.routers.dashboard.rule" = "Host(`traefik.${var.domain_name}`)"
      "traefik.http.routers.dashboard.tls" = "true"
      "traefik.http.routers.dashboard.service" = "api@internal"
    }) : k => v
  }
  
  depends_on = [
    docker_container.omega_api,
    docker_container.omega_gpu,
    docker_container.omega_ui,
    local_file.traefik_config,
    local_file.traefik_dynamic_config
  ]
}