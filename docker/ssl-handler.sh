#!/bin/bash
# SSL Certificate Handler for OMEGA Pro AI API Service

set -e

SSL_DIR="/app/ssl"
LOG_FILE="/app/logs/ssl-handler.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

log "Starting SSL handler for OMEGA API service"

# Check if SSL certificates exist
if [[ -f "$SSL_DIR/cert.pem" && -f "$SSL_DIR/key.pem" ]]; then
    log "SSL certificates found - verifying validity"
    
    # Check certificate validity
    if openssl x509 -in "$SSL_DIR/cert.pem" -checkend 86400 -noout >/dev/null 2>&1; then
        log "SSL certificate is valid for at least 24 hours"
    else
        log "WARNING: SSL certificate expires within 24 hours"
        
        # Try to renew certificate if possible
        if [[ -f "$SSL_DIR/ssl_config.json" ]]; then
            log "Attempting automatic certificate renewal"
            python3 /app/scripts/ssl_cert_manager.py renew \
                --domain "$(jq -r '.domain' $SSL_DIR/ssl_config.json)" \
                --email "$(jq -r '.email' $SSL_DIR/ssl_config.json)" 2>&1 | tee -a "$LOG_FILE"
        fi
    fi
    
    # Verify certificate and key match
    cert_hash=$(openssl x509 -in "$SSL_DIR/cert.pem" -noout -modulus | openssl md5)
    key_hash=$(openssl rsa -in "$SSL_DIR/key.pem" -noout -modulus | openssl md5)
    
    if [[ "$cert_hash" == "$key_hash" ]]; then
        log "SSL certificate and private key match"
    else
        log "ERROR: SSL certificate and private key do not match"
        exit 1
    fi
    
    # Set proper permissions
    chmod 644 "$SSL_DIR/cert.pem"
    chmod 600 "$SSL_DIR/key.pem"
    
    if [[ -f "$SSL_DIR/bundle.pem" ]]; then
        chmod 600 "$SSL_DIR/bundle.pem"
    fi
    
else
    log "SSL certificates not found - generating self-signed certificate"
    
    # Generate self-signed certificate for local development
    DOMAIN="${DOMAIN:-localhost}"
    
    openssl req -x509 -newkey rsa:2048 -keyout "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.pem" \
        -days 365 -nodes -subj "/C=US/ST=CA/L=SF/O=OMEGA/CN=$DOMAIN" \
        2>&1 | tee -a "$LOG_FILE"
    
    # Create bundle
    cat "$SSL_DIR/cert.pem" "$SSL_DIR/key.pem" > "$SSL_DIR/bundle.pem"
    
    # Set permissions
    chmod 644 "$SSL_DIR/cert.pem"
    chmod 600 "$SSL_DIR/key.pem"
    chmod 600 "$SSL_DIR/bundle.pem"
    
    log "Self-signed SSL certificate generated for $DOMAIN"
fi

# Create DH parameters for enhanced security (if not exists)
if [[ ! -f "$SSL_DIR/dhparam.pem" ]]; then
    log "Generating DH parameters for enhanced SSL security"
    openssl dhparam -out "$SSL_DIR/dhparam.pem" 2048 2>&1 | tee -a "$LOG_FILE"
    chmod 644 "$SSL_DIR/dhparam.pem"
    log "DH parameters generated"
fi

# Update nginx configuration if needed
NGINX_CONF="/etc/nginx/nginx.conf"
if [[ -f "$NGINX_CONF" ]]; then
    # Add DH parameters to nginx config if not already present
    if ! grep -q "ssl_dhparam" "$NGINX_CONF"; then
        sed -i '/ssl_session_timeout/a \    ssl_dhparam /app/ssl/dhparam.pem;' "$NGINX_CONF"
        log "Added DH parameters to nginx configuration"
    fi
fi

# Certificate monitoring function
monitor_certificates() {
    while true; do
        sleep 3600  # Check every hour
        
        if [[ -f "$SSL_DIR/cert.pem" ]]; then
            # Check if certificate expires in 7 days
            if ! openssl x509 -in "$SSL_DIR/cert.pem" -checkend 604800 -noout >/dev/null 2>&1; then
                log "ALERT: SSL certificate expires within 7 days!"
                
                # Send alert (could integrate with notification system)
                if command -v curl >/dev/null 2>&1 && [[ -n "$WEBHOOK_URL" ]]; then
                    curl -X POST "$WEBHOOK_URL" \
                        -H "Content-Type: application/json" \
                        -d '{"text":"SSL certificate for OMEGA API expires within 7 days!"}' \
                        2>&1 | tee -a "$LOG_FILE"
                fi
            fi
        fi
    done
}

# Start certificate monitoring in background
monitor_certificates &
MONITOR_PID=$!

log "SSL handler initialized successfully"
log "Certificate monitoring started (PID: $MONITOR_PID)"

# Keep the script running
trap "log 'Stopping SSL handler'; kill $MONITOR_PID 2>/dev/null || true; exit 0" SIGTERM SIGINT

# Wait for signals
while true; do
    sleep 30
    
    # Check if certificates still exist and are valid
    if [[ ! -f "$SSL_DIR/cert.pem" || ! -f "$SSL_DIR/key.pem" ]]; then
        log "ERROR: SSL certificates missing!"
        exit 1
    fi
    
    # Reload nginx if configuration changed
    if [[ -f "/tmp/nginx-reload-needed" ]]; then
        log "Reloading nginx configuration"
        nginx -s reload 2>&1 | tee -a "$LOG_FILE"
        rm -f "/tmp/nginx-reload-needed"
        log "Nginx configuration reloaded"
    fi
done