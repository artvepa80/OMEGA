# OMEGA Infrastructure Variables

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "domain_name" {
  description = "Domain name for OMEGA services"
  type        = string
  default     = "omega.local"
}

# Service configurations
variable "api_image_tag" {
  description = "Docker image tag for OMEGA API service"
  type        = string
  default     = "omega-api:latest"
}

variable "gpu_image_tag" {
  description = "Docker image tag for OMEGA GPU service"
  type        = string
  default     = "omega-gpu:latest"
}

variable "ui_image_tag" {
  description = "Docker image tag for OMEGA UI service"
  type        = string
  default     = "omega-ui:latest"
}

# Feature flags
variable "enable_redis" {
  description = "Enable Redis service for caching"
  type        = bool
  default     = true
}

variable "enable_postgres" {
  description = "Enable PostgreSQL database service"
  type        = bool
  default     = false
}

variable "enable_gpu_service" {
  description = "Enable GPU-accelerated service"
  type        = bool
  default     = false
}

variable "enable_ui" {
  description = "Enable web UI service"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable monitoring stack (Prometheus, Grafana)"
  type        = bool
  default     = true
}

variable "enable_traefik" {
  description = "Enable Traefik reverse proxy"
  type        = bool
  default     = true
}

# Database configuration
variable "database_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "omega_ai"
}

variable "database_user" {
  description = "PostgreSQL database user"
  type        = string
  default     = "omega_user"
}

variable "database_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
  default     = ""
  
  validation {
    condition     = length(var.database_password) >= 8 || var.database_password == ""
    error_message = "Database password must be at least 8 characters long."
  }
}

# Monitoring configuration
variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
  default     = "admin123"
  
  validation {
    condition     = length(var.grafana_admin_password) >= 6
    error_message = "Grafana admin password must be at least 6 characters long."
  }
}

# Resource limits
variable "api_memory_limit" {
  description = "Memory limit for API service (MB)"
  type        = number
  default     = 2048
}

variable "api_cpu_limit" {
  description = "CPU limit for API service (cores)"
  type        = number
  default     = 2
}

variable "gpu_memory_limit" {
  description = "Memory limit for GPU service (MB)"
  type        = number
  default     = 8192
}

variable "gpu_cpu_limit" {
  description = "CPU limit for GPU service (cores)"
  type        = number
  default     = 4
}

# Security configuration
variable "enable_ssl" {
  description = "Enable SSL/TLS encryption"
  type        = bool
  default     = true
}

variable "ssl_cert_path" {
  description = "Path to SSL certificate file"
  type        = string
  default     = "../ssl/cert.pem"
}

variable "ssl_key_path" {
  description = "Path to SSL private key file"
  type        = string
  default     = "../ssl/key.pem"
}

# Backup configuration
variable "enable_backups" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_schedule" {
  description = "Backup schedule in cron format"
  type        = string
  default     = "0 2 * * *"  # Daily at 2 AM
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

# Logging configuration
variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
  
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
  }
}

variable "enable_log_aggregation" {
  description = "Enable centralized log aggregation"
  type        = bool
  default     = false
}

# Scaling configuration
variable "api_replicas" {
  description = "Number of API service replicas"
  type        = number
  default     = 1
  
  validation {
    condition     = var.api_replicas >= 1 && var.api_replicas <= 10
    error_message = "API replicas must be between 1 and 10."
  }
}

variable "enable_autoscaling" {
  description = "Enable automatic scaling based on metrics"
  type        = bool
  default     = false
}

variable "autoscaling_min_replicas" {
  description = "Minimum number of replicas for autoscaling"
  type        = number
  default     = 1
}

variable "autoscaling_max_replicas" {
  description = "Maximum number of replicas for autoscaling"
  type        = number
  default     = 5
}

variable "autoscaling_cpu_threshold" {
  description = "CPU threshold percentage for scaling up"
  type        = number
  default     = 70
}

# Network configuration
variable "custom_network_cidr" {
  description = "Custom CIDR block for Docker network"
  type        = string
  default     = "172.20.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.custom_network_cidr, 0))
    error_message = "Custom network CIDR must be a valid CIDR block."
  }
}

# Development configuration
variable "enable_debug_mode" {
  description = "Enable debug mode for development"
  type        = bool
  default     = false
}

variable "enable_hot_reload" {
  description = "Enable hot reload for development"
  type        = bool
  default     = false
}

variable "mount_source_code" {
  description = "Mount source code as volume for development"
  type        = bool
  default     = false
}