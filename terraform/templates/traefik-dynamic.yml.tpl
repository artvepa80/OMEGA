# Traefik Dynamic Configuration Template
tls:
  certificates:
    - certFile: ${cert_file}
      keyFile: ${key_file}

# HTTP middlewares
http:
  middlewares:
    # Security headers
    security-headers:
      headers:
        customRequestHeaders:
          X-Forwarded-Proto: https
        customResponseHeaders:
          X-Robots-Tag: noindex
          X-Frame-Options: DENY
          X-Content-Type-Options: nosniff
          Referrer-Policy: strict-origin-when-cross-origin
          Strict-Transport-Security: max-age=31536000; includeSubDomains
          Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'

    # Rate limiting
    rate-limit:
      rateLimit:
        burst: 100
        average: 50

    # Authentication (basic auth for development)
    auth:
      basicAuth:
        users:
          - "admin:$2y$10$2b2cu/b9vVpZxOr5/VrFVOW1g6FQ3F.3KvJR.Q7Q/K5q1/K1/Q/7Q"

    # Compression
    compression:
      compress: {}

    # CORS for API
    api-cors:
      headers:
        accessControlAllowMethods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
        accessControlAllowOriginList:
          - "*"
        accessControlAllowHeaders:
          - "*"
        accessControlMaxAge: 86400

  # Services configuration
  services:
    omega-api:
      loadBalancer:
        servers:
          - url: "http://omega-api:8000"
        healthCheck:
          path: /health
          interval: 10s
          timeout: 5s

    omega-gpu:
      loadBalancer:
        servers:
          - url: "http://omega-gpu:8001"
        healthCheck:
          path: /health
          interval: 10s
          timeout: 5s

    omega-ui:
      loadBalancer:
        servers:
          - url: "http://omega-ui:3000"
        healthCheck:
          path: /
          interval: 30s
          timeout: 10s

  # Routers configuration
  routers:
    api:
      rule: "Host(`api.omega.local`) || (Host(`omega.local`) && PathPrefix(`/api`))"
      service: omega-api
      tls: {}
      middlewares:
        - security-headers
        - compression
        - api-cors
        - rate-limit

    gpu:
      rule: "Host(`gpu.omega.local`) || (Host(`omega.local`) && PathPrefix(`/gpu`))"
      service: omega-gpu
      tls: {}
      middlewares:
        - security-headers
        - compression
        - api-cors
        - rate-limit

    ui:
      rule: "Host(`omega.local`)"
      service: omega-ui
      tls: {}
      middlewares:
        - security-headers
        - compression

    dashboard:
      rule: "Host(`traefik.omega.local`)"
      service: api@internal
      tls: {}
      middlewares:
        - security-headers
        - auth

# TCP configuration (if needed)
tcp:
  routers: {}
  services: {}