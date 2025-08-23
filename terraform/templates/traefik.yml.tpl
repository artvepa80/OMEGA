# Traefik Configuration Template
api:
  dashboard: true
  debug: ${environment == "development" ? "true" : "false"}

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true

  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: omega_network

  file:
    filename: /etc/traefik/dynamic.yml
    watch: true

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@${domain_name}
      storage: /acme.json
      httpChallenge:
        entryPoint: web

# Global configuration
global:
  checkNewVersion: false
  sendAnonymousUsage: false

# Logging
log:
  level: ${environment == "development" ? "DEBUG" : "INFO"}
  format: json

accessLog:
  format: json
  fields:
    defaultMode: keep
    names:
      ClientUsername: drop
    headers:
      defaultMode: keep
      names:
        User-Agent: redact
        Authorization: drop
        Content-Type: keep

# Metrics
metrics:
  prometheus:
    addEntryPointsLabels: true
    addServicesLabels: true
    buckets:
      - 0.1
      - 0.3
      - 1.2
      - 5.0

# Ping endpoint for health checks
ping:
  entryPoint: websecure

# Tracing (optional)
%{ if environment == "production" ~}
tracing:
  jaeger:
    samplingServerURL: http://jaeger:14268/api/sampling
    localAgentHostPort: jaeger:6831
%{ endif ~}