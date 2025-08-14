#!/usr/bin/env python3
"""
🛡️ Network Security Implementation for OMEGA Pro AI
Implements TLS 1.2+, security headers, rate limiting, and DDoS protection
"""

import click
import subprocess
import os
import json
from pathlib import Path
from datetime import datetime

@click.group()
def security_cli():
    """Network Security Deployment CLI"""
    pass

@security_cli.command()
def implement_tls_security():
    """Implement TLS 1.2+ enforcement and security configurations"""
    
    click.echo("🛡️ Implementing TLS security configurations...")
    
    # Create enhanced nginx configuration with security
    nginx_security_config = """# Enhanced Nginx Security Configuration for OMEGA Pro AI
# Production-ready SSL/TLS setup with maximum security

user nginx;
worker_processes auto;
worker_cpu_affinity auto;
worker_rlimit_nofile 65535;
pid /var/run/nginx.pid;

# Load dynamic modules
include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
    accept_mutex off;
}

http {
    # Basic Settings
    sendfile on;
    sendfile_max_chunk 1m;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    types_hash_max_size 2048;
    client_max_body_size 64M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    large_client_header_buffers 4 32k;
    
    # Hide server information
    server_tokens off;
    more_clear_headers Server;
    more_set_headers "Server: OMEGA-Secure";

    # MIME Types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging Configuration with Security Context
    log_format security_log '$remote_addr - $remote_user [$time_local] '
                           '"$request" $status $body_bytes_sent '
                           '"$http_referer" "$http_user_agent" '
                           '$request_time $upstream_response_time '
                           '"$http_x_forwarded_for" "$ssl_protocol" '
                           '"$ssl_cipher" "$ssl_client_fingerprint"';

    access_log /var/log/nginx/access.log security_log buffer=32k flush=5s;
    error_log /var/log/nginx/error.log warn;

    # SSL/TLS Configuration - Maximum Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_ecdh_curve secp384r1;
    
    # SSL Session Configuration
    ssl_session_cache shared:SSL:50m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    ssl_buffer_size 4k;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /app/ssl/chain.pem;
    resolver 8.8.8.8 8.8.4.4 1.1.1.1 valid=300s;
    resolver_timeout 5s;

    # Security Headers - Maximum Protection
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval'; frame-ancestors 'self'; form-action 'self'; base-uri 'self';" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=(), vibrate=(), fullscreen=(self), sync-xhr=()" always;
    add_header Cross-Origin-Embedder-Policy "require-corp" always;
    add_header Cross-Origin-Opener-Policy "same-origin" always;
    add_header Cross-Origin-Resource-Policy "cross-origin" always;

    # Rate Limiting - DDoS Protection
    limit_req_zone $binary_remote_addr zone=api_limit:50m rate=20r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;
    limit_req_zone $binary_remote_addr zone=general_limit:100m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=static_limit:50m rate=200r/s;
    
    # Connection limiting
    limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
    limit_conn_zone $server_name zone=conn_limit_per_server:10m;

    # Request size limits
    client_body_buffer_size 128k;
    client_header_buffer_size 3m;

    # Gzip Configuration with Security
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Proxy Settings for Security
    proxy_hide_header X-Powered-By;
    proxy_hide_header Server;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Port $server_port;

    # Map for blocking common attack patterns
    map $request_uri $blocked {
        default 0;
        "~*\\.(asp|aspx|php|jsp)$" 1;
        "~*/\\..*" 1;
        "~*/(wp-admin|wp-login|phpMyAdmin|admin)" 1;
    }

    # Map for user agent filtering
    map $http_user_agent $blocked_agent {
        default 0;
        "~*bot" 0;  # Allow legitimate bots
        "~*crawler" 0;
        "" 1;  # Block empty user agents
        "~*scanner" 1;
        "~*sqlmap" 1;
        "~*nikto" 1;
        "~*nmap" 1;
    }

    # HTTP to HTTPS Redirect Server
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;
        
        # Security headers even for HTTP
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        
        # Health check endpoint (allow HTTP)
        location = /health {
            access_log off;
            proxy_pass http://omega-api:8000/health;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        # Block common attack patterns
        if ($blocked) {
            return 444;
        }
        
        if ($blocked_agent) {
            return 444;
        }
        
        # Redirect all other HTTP requests to HTTPS
        location / {
            return 301 https://$host$request_uri;
        }
    }

    # Main HTTPS Server - Maximum Security
    server {
        listen 443 ssl http2 default_server;
        listen [::]:443 ssl http2 default_server;
        server_name omega-api.akash.network *.omega-pro.ai;

        # SSL Certificate Configuration
        ssl_certificate /app/ssl/cert.pem;
        ssl_certificate_key /app/ssl/key.pem;
        ssl_dhparam /app/ssl/dhparam.pem;

        # Connection limits
        limit_conn conn_limit_per_ip 50;
        limit_conn conn_limit_per_server 1000;

        # Root and security
        root /app/static;
        index index.html;

        # Block malicious requests
        if ($blocked) {
            return 444;
        }
        
        if ($blocked_agent) {
            return 444;
        }

        # Block requests with suspicious headers
        if ($http_x_forwarded_host) {
            return 444;
        }

        # API Endpoints - Strict Rate Limiting
        location /api/ {
            limit_req zone=api_limit burst=100 nodelay;
            
            # Additional security for API
            if ($request_method !~ ^(GET|POST|PUT|DELETE|OPTIONS)$ ) {
                return 405;
            }
            
            proxy_pass http://omega-api:8000/api/;
            include /etc/nginx/proxy_params;
            
            # Timeout Configuration
            proxy_connect_timeout 30s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # Buffer Configuration
            proxy_buffering on;
            proxy_buffer_size 128k;
            proxy_buffers 4 256k;
            proxy_busy_buffers_size 256k;
            
            # Security headers for API responses
            add_header X-API-Version "1.0" always;
        }

        # Authentication Endpoints - Extra Strict Limiting
        location ~ ^/api/(auth|login|register|password|oauth) {
            limit_req zone=auth_limit burst=10 nodelay;
            
            # Only allow POST for auth endpoints
            if ($request_method !~ ^(POST|OPTIONS)$ ) {
                return 405;
            }
            
            proxy_pass http://omega-api:8000;
            include /etc/nginx/proxy_params;
            
            # Shorter timeouts for auth
            proxy_connect_timeout 15s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # GPU Service Internal Communication (Block external access)
        location /gpu/ {
            # Only allow internal communication
            allow 127.0.0.0/8;
            allow 10.0.0.0/8;
            allow 172.16.0.0/12;
            allow 192.168.0.0/16;
            deny all;
            
            proxy_pass http://omega-gpu:8001/;
            include /etc/nginx/proxy_params;
            
            # Extended timeouts for GPU processing
            proxy_connect_timeout 60s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }

        # WebSocket Support with Security
        location /ws/ {
            # Rate limit WebSocket connections
            limit_req zone=general_limit burst=20 nodelay;
            limit_conn conn_limit_per_ip 10;
            
            proxy_pass http://omega-api:8000/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            include /etc/nginx/proxy_params;
            
            # WebSocket timeout
            proxy_read_timeout 86400s;
            proxy_send_timeout 86400s;
        }

        # Health Check Endpoints - No rate limiting but logging
        location ~ ^/(health|metrics|status)$ {
            access_log /var/log/nginx/health.log;
            
            proxy_pass http://omega-api:8000$request_uri;
            include /etc/nginx/proxy_params;
            
            # Quick health check timeouts
            proxy_connect_timeout 5s;
            proxy_send_timeout 5s;
            proxy_read_timeout 5s;
        }

        # Static Files with Aggressive Caching
        location /static/ {
            limit_req zone=static_limit burst=1000 nodelay;
            
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Content-Type-Options "nosniff";
            
            # Security for static files
            location ~* \\.(js|css)$ {
                add_header Content-Security-Policy "default-src 'self'";
            }
            
            try_files $uri $uri/ =404;
        }

        # Favicon with caching
        location = /favicon.ico {
            expires 1y;
            add_header Cache-Control "public, immutable";
            try_files /favicon.ico =404;
        }

        # Robots.txt
        location = /robots.txt {
            add_header Content-Type text/plain;
            return 200 "User-agent: *\\nDisallow: /api/\\nDisallow: /admin/\\n";
        }

        # Security.txt for responsible disclosure
        location = /.well-known/security.txt {
            add_header Content-Type text/plain;
            return 200 "Contact: security@omega-pro.ai\\nExpires: 2025-12-31T23:59:59.000Z\\n";
        }

        # Block access to sensitive files and directories
        location ~ /\\.(ht|env|git|svn|hg) {
            deny all;
            return 404;
        }

        location ~ \\.(log|conf|ini|sql|bak|backup)$ {
            deny all;
            return 404;
        }

        location ~ ^/(config|scripts|logs|tmp)/ {
            deny all;
            return 404;
        }

        # Default location with comprehensive security
        location / {
            limit_req zone=general_limit burst=200 nodelay;
            
            # Try static files first, then API
            try_files $uri $uri/ @api;
        }

        # Fallback to API with security
        location @api {
            proxy_pass http://omega-api:8000;
            include /etc/nginx/proxy_params;
            
            # Standard timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Custom Error Pages
        error_page 400 /error/400.html;
        error_page 401 /error/401.html;
        error_page 403 /error/403.html;
        error_page 404 /error/404.html;
        error_page 429 /error/429.html;
        error_page 500 502 503 504 /error/50x.html;
        
        location ^~ /error/ {
            internal;
            root /usr/share/nginx/html;
        }
    }

    # Additional security server for monitoring and metrics
    server {
        listen 9090;
        server_name localhost;
        
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
        
        location /nginx_status {
            stub_status on;
            access_log off;
        }
        
        location /metrics {
            proxy_pass http://omega-api:8000/metrics;
        }
    }
}

# Stream configuration for TCP/UDP proxying
stream {
    # Logging
    error_log /var/log/nginx/stream.log;
    
    # Security for non-HTTP protocols
    map $remote_addr $allowed_ips {
        ~^127\\.0\\.0\\.1$ 1;
        ~^10\\. 1;
        ~^172\\.(1[6-9]|2[0-9]|3[01])\\. 1;
        ~^192\\.168\\. 1;
        default 0;
    }
}
"""

    # Write enhanced nginx configuration
    nginx_config_path = Path("docker/nginx-security-enhanced.conf")
    with open(nginx_config_path, 'w') as f:
        f.write(nginx_security_config)
    
    click.echo(f"✅ Enhanced nginx security configuration created: {nginx_config_path}")
    
    # Create proxy parameters file
    proxy_params = """proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Port $server_port;
proxy_set_header X-Original-URI $request_uri;
proxy_set_header X-Original-Method $request_method;

# Security headers for proxied requests
proxy_hide_header X-Powered-By;
proxy_hide_header Server;

# Buffer settings
proxy_buffering on;
proxy_buffer_size 128k;
proxy_buffers 4 256k;
proxy_busy_buffers_size 256k;

# Connection settings
proxy_connect_timeout 30s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
"""

    proxy_params_path = Path("docker/proxy_params")
    with open(proxy_params_path, 'w') as f:
        f.write(proxy_params)
    
    click.echo(f"✅ Proxy parameters configuration created: {proxy_params_path}")

@security_cli.command()
def create_security_monitoring():
    """Create security monitoring and alerting system"""
    
    click.echo("🔍 Creating security monitoring system...")
    
    security_monitor_script = """#!/usr/bin/env python3
'''
Security Monitoring and Alerting System for OMEGA Pro AI
'''

import time
import subprocess
import json
import requests
import re
import os
from datetime import datetime, timedelta
from collections import defaultdict

class SecurityMonitor:
    def __init__(self):
        self.alert_thresholds = {
            'failed_requests_per_minute': 50,
            'error_rate_percentage': 5.0,
            'blocked_requests_per_minute': 20,
            'concurrent_connections': 1000,
            'bandwidth_mbps': 100
        }
        
        self.log_files = {
            'access': '/var/log/nginx/access.log',
            'error': '/var/log/nginx/error.log'
        }
        
        self.metrics = defaultdict(int)
        self.last_alert_time = defaultdict(lambda: datetime.min)
        
    def analyze_logs(self):
        '''Analyze nginx logs for security threats'''
        
        # Read recent access log entries
        try:
            result = subprocess.run(['tail', '-1000', self.log_files['access']], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.analyze_access_log(result.stdout)
                
        except Exception as e:
            print(f"Error reading access logs: {e}")
        
        # Read recent error log entries
        try:
            result = subprocess.run(['tail', '-100', self.log_files['error']], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.analyze_error_log(result.stdout)
                
        except Exception as e:
            print(f"Error reading error logs: {e}")
    
    def analyze_access_log(self, log_content):
        '''Analyze access log for security patterns'''
        
        lines = log_content.strip().split('\\n')
        recent_time = datetime.now() - timedelta(minutes=1)
        
        for line in lines:
            if not line:
                continue
                
            # Parse log line
            match = re.search(r'(\\d+\\.\\d+\\.\\d+\\.\\d+).*"([A-Z]+)\\s+([^"]+)"\\s+(\\d+)', line)
            if not match:
                continue
                
            ip, method, path, status = match.groups()
            status_code = int(status)
            
            # Count various metrics
            if status_code >= 400:
                self.metrics['failed_requests'] += 1
                
            if status_code == 429:
                self.metrics['rate_limited_requests'] += 1
                
            if status_code == 444:  # Blocked requests
                self.metrics['blocked_requests'] += 1
                
            # Check for common attack patterns
            if self.is_suspicious_request(path, method):
                self.metrics['suspicious_requests'] += 1
                self.alert(f"Suspicious request from {ip}: {method} {path}")
    
    def analyze_error_log(self, log_content):
        '''Analyze error log for security issues'''
        
        lines = log_content.strip().split('\\n')
        
        for line in lines:
            if 'limit_req' in line:
                self.metrics['rate_limit_violations'] += 1
            elif 'limit_conn' in line:
                self.metrics['connection_limit_violations'] += 1
            elif 'SSL' in line and 'error' in line.lower():
                self.metrics['ssl_errors'] += 1
    
    def is_suspicious_request(self, path, method):
        '''Check if request is suspicious'''
        
        suspicious_patterns = [
            r'/\\.\\./.*',  # Directory traversal
            r'/wp-admin.*',  # WordPress attacks
            r'/admin.*',  # Admin panel probing
            r'/phpmyadmin.*',  # Database admin attacks
            r'\\.(php|asp|jsp)$',  # Script file access
            r'/\\.env',  # Environment file access
            r'/config.*',  # Config file access
            r'select.*from.*',  # SQL injection patterns
            r'union.*select.*',  # SQL injection
            r'<script.*>.*',  # XSS patterns
            r'javascript:.*',  # XSS
        ]
        
        path_lower = path.lower()
        
        for pattern in suspicious_patterns:
            if re.search(pattern, path_lower):
                return True
                
        return False
    
    def check_system_health(self):
        '''Check system health metrics'''
        
        try:
            # Check nginx status
            result = subprocess.run(['curl', '-s', 'http://localhost:9090/nginx_status'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.parse_nginx_status(result.stdout)
                
        except Exception as e:
            print(f"Error checking nginx status: {e}")
    
    def parse_nginx_status(self, status_output):
        '''Parse nginx status output'''
        
        lines = status_output.strip().split('\\n')
        
        for line in lines:
            if 'Active connections:' in line:
                connections = int(line.split(':')[1].strip())
                self.metrics['active_connections'] = connections
                
                if connections > self.alert_thresholds['concurrent_connections']:
                    self.alert(f"High connection count: {connections}")
    
    def alert(self, message):
        '''Send security alert'''
        
        alert_type = message.split(':')[0].lower()
        now = datetime.now()
        
        # Rate limit alerts (max 1 per type per 5 minutes)
        if now - self.last_alert_time[alert_type] < timedelta(minutes=5):
            return
            
        self.last_alert_time[alert_type] = now
        
        print(f"SECURITY ALERT: {message}")
        
        # Send webhook alert if configured
        webhook_url = os.getenv('SECURITY_WEBHOOK_URL')
        if webhook_url:
            try:
                requests.post(webhook_url, json={
                    'text': f'OMEGA Security Alert: {message}',
                    'timestamp': now.isoformat(),
                    'severity': 'high' if 'attack' in message.lower() else 'medium'
                }, timeout=10)
            except Exception as e:
                print(f"Failed to send webhook alert: {e}")
    
    def generate_report(self):
        '''Generate security report'''
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': dict(self.metrics),
            'alerts_generated': len(self.last_alert_time),
            'status': 'healthy' if self.metrics['suspicious_requests'] < 10 else 'warning'
        }
        
        # Save report
        with open('/tmp/security_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        return report
    
    def monitor_loop(self):
        '''Main monitoring loop'''
        
        print("Starting OMEGA security monitoring...")
        
        while True:
            try:
                # Reset metrics for this iteration
                self.metrics.clear()
                
                # Analyze logs
                self.analyze_logs()
                
                # Check system health
                self.check_system_health()
                
                # Generate report
                report = self.generate_report()
                print(f"Security scan complete: {report['status']}")
                
                # Sleep for 60 seconds
                time.sleep(60)
                
            except KeyboardInterrupt:
                print("Security monitoring stopped by user")
                break
            except Exception as e:
                print(f"Security monitoring error: {e}")
                time.sleep(30)

if __name__ == '__main__':
    monitor = SecurityMonitor()
    monitor.monitor_loop()
"""

    security_monitor_path = Path("scripts/security_monitor.py")
    with open(security_monitor_path, 'w') as f:
        f.write(security_monitor_script)
    
    os.chmod(security_monitor_path, 0o755)
    
    click.echo(f"✅ Security monitoring script created: {security_monitor_path}")

@security_cli.command()
def deploy_security_infrastructure():
    """Deploy complete security infrastructure"""
    
    click.echo("🛡️ Deploying complete security infrastructure...")
    
    # Implement TLS security
    implement_tls_security()
    
    # Create security monitoring
    create_security_monitoring()
    
    # Create firewall rules script
    firewall_script = """#!/bin/bash
# OMEGA Pro AI - Firewall Rules for Enhanced Security

set -e

# Enable UFW if available
if command -v ufw >/dev/null 2>&1; then
    echo "Configuring UFW firewall..."
    
    # Reset to defaults
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH (adjust port as needed)
    ufw allow 22/tcp
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow internal monitoring
    ufw allow from 127.0.0.1 to any port 9090
    ufw allow from 10.0.0.0/8 to any port 9090
    ufw allow from 172.16.0.0/12 to any port 9090
    ufw allow from 192.168.0.0/16 to any port 9090
    
    # Rate limiting for SSH
    ufw limit ssh
    
    # Enable firewall
    ufw --force enable
    
    echo "UFW firewall configured successfully"
else
    echo "UFW not available, skipping firewall configuration"
fi

# Configure fail2ban if available
if command -v fail2ban-client >/dev/null 2>&1; then
    echo "Configuring Fail2ban..."
    
    # Create nginx jail
    cat > /etc/fail2ban/jail.d/nginx.conf << 'EOF'
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
bantime = 600

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 3600
EOF

    # Restart fail2ban
    systemctl restart fail2ban
    
    echo "Fail2ban configured successfully"
else
    echo "Fail2ban not available, skipping intrusion prevention setup"
fi

echo "Security infrastructure deployment completed"
"""

    firewall_script_path = Path("scripts/setup_firewall.sh")
    with open(firewall_script_path, 'w') as f:
        f.write(firewall_script)
    
    os.chmod(firewall_script_path, 0o755)
    
    click.echo("✅ Complete security infrastructure deployed!")
    click.echo("")
    click.echo("Security Components:")
    click.echo("   - Enhanced Nginx configuration with TLS 1.2+")
    click.echo("   - Security headers and HSTS")
    click.echo("   - Rate limiting and DDoS protection")
    click.echo("   - Security monitoring system")
    click.echo("   - Firewall configuration script")
    click.echo("")
    click.echo("To complete setup:")
    click.echo(f"   sudo {firewall_script_path}")
    click.echo(f"   python3 scripts/security_monitor.py")

if __name__ == '__main__':
    security_cli()