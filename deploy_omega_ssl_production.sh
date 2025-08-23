#!/bin/bash
# OMEGA Production SSL Deployment Master Script
# Orchestrates complete SSL certificate deployment with enterprise security

set -e  # Exit on any error

# Configuration
DOMAIN="omega-api.akash.network"
EMAIL="admin@omega-pro-ai.com"
LOG_FILE="./logs/ssl_deployment_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
    
    case $level in
        "INFO")  echo -e "${CYAN}ℹ️  $message${NC}" ;;
        "SUCCESS") echo -e "${GREEN}✅ $message${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "ERROR") echo -e "${RED}❌ $message${NC}" ;;
        "STEP") echo -e "${PURPLE}🚀 $message${NC}" ;;
    esac
}

# Create log directory
mkdir -p ./logs

# Header
echo -e "${BLUE}"
echo "============================================================================"
echo "🔐 OMEGA PRODUCTION SSL CERTIFICATE DEPLOYMENT"
echo "============================================================================"
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo "Timestamp: $(date)"
echo "Log File: $LOG_FILE"
echo "============================================================================"
echo -e "${NC}"

log "INFO" "Starting OMEGA Production SSL Certificate Deployment"

# Step 1: Prerequisites Check
log "STEP" "Step 1: Checking Prerequisites"
echo "----------------------------------------------------------------------------"

# Check if running as root (required for Let's Encrypt)
if [[ $EUID -ne 0 ]]; then
    log "WARNING" "Not running as root. Some operations may fail."
    echo "Consider running with: sudo $0"
fi

# Check Python dependencies
log "INFO" "Checking Python dependencies..."
python3 -c "import click, cryptography, requests" 2>/dev/null || {
    log "ERROR" "Missing Python dependencies. Installing..."
    pip3 install click cryptography requests
}

# Check system tools
for tool in openssl curl nginx python3; do
    if ! command -v $tool &> /dev/null; then
        log "ERROR" "$tool is not installed"
        exit 1
    else
        log "SUCCESS" "$tool is available"
    fi
done

# Step 2: Stop conflicting services
log "STEP" "Step 2: Preparing Services"
echo "----------------------------------------------------------------------------"

log "INFO" "Stopping services that might conflict with port 80..."
systemctl stop nginx 2>/dev/null || log "WARNING" "Could not stop nginx"
systemctl stop apache2 2>/dev/null || log "WARNING" "Could not stop apache2"

# Step 3: Generate DH Parameters (if not exists)
log "STEP" "Step 3: Generating Diffie-Hellman Parameters"
echo "----------------------------------------------------------------------------"

if [[ ! -f "./ssl/dhparam.pem" ]]; then
    log "INFO" "Generating 2048-bit DH parameters (this may take several minutes)..."
    python3 ./scripts/generate_dhparam.py --bits 2048 --output ./ssl/dhparam.pem
    
    if [[ $? -eq 0 ]]; then
        log "SUCCESS" "DH parameters generated successfully"
    else
        log "ERROR" "Failed to generate DH parameters"
        exit 1
    fi
else
    log "INFO" "DH parameters already exist, skipping generation"
fi

# Step 4: Deploy Let's Encrypt Production Certificate
log "STEP" "Step 4: Deploying Let's Encrypt Production Certificate"
echo "----------------------------------------------------------------------------"

log "INFO" "Generating production Let's Encrypt certificate for $DOMAIN..."
python3 ./scripts/ssl_cert_manager.py generate \
    --domain "$DOMAIN" \
    --email "$EMAIL" \
    --type letsencrypt \
    --production

if [[ $? -eq 0 ]]; then
    log "SUCCESS" "Let's Encrypt certificate deployed successfully"
else
    log "ERROR" "Failed to deploy Let's Encrypt certificate"
    exit 1
fi

# Step 5: Update iOS Certificate Pinning
log "STEP" "Step 5: Updating iOS Certificate Pinning"
echo "----------------------------------------------------------------------------"

log "INFO" "Updating iOS certificate pinning configuration..."
python3 ./scripts/update_ios_pinning.py --domain "$DOMAIN"

if [[ $? -eq 0 ]]; then
    log "SUCCESS" "iOS certificate pinning updated"
else
    log "WARNING" "iOS certificate pinning update failed (non-critical)"
fi

# Step 6: Deploy Production Nginx Configuration
log "STEP" "Step 6: Deploying Production Nginx Configuration"
echo "----------------------------------------------------------------------------"

# Backup existing nginx config
if [[ -f "./docker/nginx.conf" ]]; then
    cp ./docker/nginx.conf "./docker/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)"
    log "INFO" "Backed up existing nginx configuration"
fi

# Deploy production nginx config
cp ./docker/nginx-production-ssl.conf ./docker/nginx.conf
log "SUCCESS" "Production nginx configuration deployed"

# Test nginx configuration
nginx -t -c "$(pwd)/docker/nginx.conf"
if [[ $? -eq 0 ]]; then
    log "SUCCESS" "Nginx configuration test passed"
else
    log "ERROR" "Nginx configuration test failed"
    exit 1
fi

# Step 7: Start Services
log "STEP" "Step 7: Starting Services"
echo "----------------------------------------------------------------------------"

# Start nginx with new configuration
systemctl start nginx
if [[ $? -eq 0 ]]; then
    log "SUCCESS" "Nginx started successfully"
else
    log "ERROR" "Failed to start nginx"
    exit 1
fi

# Wait for nginx to fully start
sleep 5

# Check nginx status
systemctl is-active --quiet nginx
if [[ $? -eq 0 ]]; then
    log "SUCCESS" "Nginx is running"
else
    log "ERROR" "Nginx is not running"
    exit 1
fi

# Step 8: Setup SSL Monitoring
log "STEP" "Step 8: Setting Up SSL Certificate Monitoring"
echo "----------------------------------------------------------------------------"

# Create monitoring configuration
python3 ./scripts/ssl_health_monitor.py config-template

# Create systemd service for monitoring
cat > /etc/systemd/system/omega-ssl-monitor.service << EOF
[Unit]
Description=OMEGA SSL Certificate Health Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/scripts/ssl_health_monitor.py monitor --interval 3600
Restart=always
RestartSec=60
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start monitoring service
systemctl daemon-reload
systemctl enable omega-ssl-monitor.service
systemctl start omega-ssl-monitor.service

if systemctl is-active --quiet omega-ssl-monitor.service; then
    log "SUCCESS" "SSL monitoring service started"
else
    log "WARNING" "SSL monitoring service failed to start"
fi

# Step 9: Validation
log "STEP" "Step 9: Validating SSL Deployment"
echo "----------------------------------------------------------------------------"

log "INFO" "Running comprehensive SSL deployment validation..."
python3 ./scripts/validate_ssl_deployment.py \
    --domain "$DOMAIN" \
    --output "./logs/ssl_validation_$(date +%Y%m%d_%H%M%S).json"

VALIDATION_RESULT=$?

# Step 10: Final Status and Next Steps
log "STEP" "Step 10: Deployment Summary"
echo "============================================================================"

if [[ $VALIDATION_RESULT -eq 0 ]]; then
    log "SUCCESS" "🎉 OMEGA Production SSL Deployment COMPLETED SUCCESSFULLY!"
else
    log "WARNING" "⚠️ SSL deployment completed with validation warnings"
fi

# Display certificate information
log "INFO" "Certificate Status:"
python3 ./scripts/ssl_cert_manager.py status

# Show next steps
echo ""
log "INFO" "🎯 Next Steps:"
echo "   1. Test API endpoints: https://$DOMAIN/health"
echo "   2. Update DNS records if necessary"
echo "   3. Test iOS app with new certificate pinning"
echo "   4. Monitor certificate auto-renewal"
echo "   5. Update deployment documentation"
echo ""
echo "🔗 Key URLs to test:"
echo "   - https://$DOMAIN/health"
echo "   - https://$DOMAIN/api/status" 
echo "   - https://$DOMAIN/ssl/info"
echo ""
echo "📋 Monitoring:"
echo "   - SSL Health Monitor: systemctl status omega-ssl-monitor.service"
echo "   - Certificate Status: python3 ./scripts/ssl_cert_manager.py status"
echo "   - Manual Health Check: python3 ./scripts/ssl_health_monitor.py check"
echo ""

log "INFO" "Deployment log saved to: $LOG_FILE"

echo "============================================================================"
log "SUCCESS" "OMEGA Production SSL Deployment Complete!"
echo "============================================================================"