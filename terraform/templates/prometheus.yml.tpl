# Prometheus Configuration Template
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093

scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s
    metrics_path: /metrics

  # OMEGA API Service
  - job_name: 'omega-api'
    static_configs:
      - targets: ['omega-api:${api_port}']
    scrape_interval: 15s
    metrics_path: /metrics
    scrape_timeout: 10s
    honor_labels: true
    params:
      format: ['prometheus']

  # OMEGA GPU Service
  - job_name: 'omega-gpu'
    static_configs:
      - targets: ['omega-gpu:${gpu_port}']
    scrape_interval: 15s
    metrics_path: /metrics
    scrape_timeout: 10s
    honor_labels: true
    params:
      format: ['prometheus']

  # Redis metrics (if available)
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s
    metrics_path: /metrics

  # PostgreSQL metrics (if available with exporter)
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']
    scrape_interval: 30s
    metrics_path: /metrics

  # Docker container metrics
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 30s
    metrics_path: /metrics

  # Node exporter for system metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s
    metrics_path: /metrics

# Storage configuration
storage:
  tsdb:
    path: /prometheus
    retention.time: 30d
    retention.size: 10GB