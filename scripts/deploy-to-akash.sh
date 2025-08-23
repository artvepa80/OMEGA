#!/bin/bash
# 🚀 OMEGA PRO AI v10.1 - Akash Network Deployment Script
# One-command deployment to Akash Network with health monitoring

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCKER_IMAGE="omegaproai/omega-ai:latest"
AKASH_DEPLOYMENT_FILE="$PROJECT_DIR/deploy/akash-deployment.yaml"
LOG_FILE="$PROJECT_DIR/logs/akash-deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Emoji for better UX
ROCKET="🚀"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"
CLOUD="☁️"
MONITOR="📊"

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        INFO)  echo -e "${BLUE}${INFO}${NC} ${WHITE}$message${NC}" ;;
        SUCCESS) echo -e "${GREEN}${CHECK}${NC} ${WHITE}$message${NC}" ;;
        ERROR) echo -e "${RED}${CROSS}${NC} ${WHITE}$message${NC}" ;;
        WARNING) echo -e "${YELLOW}${WARNING}${NC} ${WHITE}$message${NC}" ;;
        GEAR) echo -e "${CYAN}${GEAR}${NC} ${WHITE}$message${NC}" ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log INFO "Checking prerequisites..."
    
    # Check if required commands exist
    local required_commands=("docker" "akash" "curl" "jq")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log ERROR "$cmd is required but not installed"
            exit 1
        fi
    done
    
    # Check if Akash CLI is configured
    if [ -z "${AKASH_NODE:-}" ] || [ -z "${AKASH_CHAIN_ID:-}" ]; then
        log WARNING "Akash environment variables not set. Loading from .env file..."
        if [ -f "$PROJECT_DIR/.env" ]; then
            source "$PROJECT_DIR/.env"
        else
            log ERROR "No .env file found. Please configure Akash environment variables."
            exit 1
        fi
    fi
    
    log SUCCESS "Prerequisites check completed"
}

# Build and push Docker image
build_and_push_image() {
    log INFO "Building and pushing Docker image..."
    
    cd "$PROJECT_DIR"
    
    # Build the image
    log GEAR "Building Docker image: $DOCKER_IMAGE"
    docker build -f Dockerfile.production -t "$DOCKER_IMAGE" .
    
    # Push to registry
    log GEAR "Pushing image to Docker Hub..."
    docker push "$DOCKER_IMAGE"
    
    log SUCCESS "Docker image built and pushed successfully"
}

# Create Akash deployment manifest
create_deployment_manifest() {
    log INFO "Creating Akash deployment manifest..."
    
    mkdir -p "$(dirname "$AKASH_DEPLOYMENT_FILE")"
    
    cat > "$AKASH_DEPLOYMENT_FILE" << EOF
version: "2.0"

services:
  omega-ai:
    image: $DOCKER_IMAGE
    expose:
      - port: 8000
        as: 80
        to:
          - global: true
    env:
      - "APP_ENV=production"
      - "PORT=8000"
      - "PYTHONUNBUFFERED=1"
    resources:
      cpu:
        units: "2.0"
      memory:
        size: "4Gi"
      storage:
        size: "10Gi"

profiles:
  compute:
    omega-ai:
      resources:
        cpu:
          units: "2.0"
        memory:
          size: "4Gi"
        storage:
          size: "10Gi"
  
  placement:
    akash:
      attributes:
        host: akash
      signedBy:
        anyOf:
          - "akash1365yvmc4s7awdyj3n2sav7xfx76adc6dnmlx63"
      pricing:
        omega-ai:
          denom: uakt
          amount: 1000

deployment:
  omega-ai:
    akash:
      profile: omega-ai
      count: 1
EOF

    log SUCCESS "Deployment manifest created at $AKASH_DEPLOYMENT_FILE"
}

# Deploy to Akash Network
deploy_to_akash() {
    log INFO "Deploying to Akash Network..."
    
    export AKASH_KEYRING_BACKEND=test
    
    # Check if this is an update or new deployment
    if [ -n "${AKASH_DSEQ:-}" ]; then
        log GEAR "Updating existing deployment (DSEQ: $AKASH_DSEQ)..."
        akash tx deployment update "$AKASH_DEPLOYMENT_FILE" \
            --from main \
            --gas-prices="0.025uakt" \
            --gas="auto" \
            --gas-adjustment=1.15 \
            --broadcast-mode=block \
            --yes
    else
        log GEAR "Creating new deployment..."
        akash tx deployment create "$AKASH_DEPLOYMENT_FILE" \
            --from main \
            --gas-prices="0.025uakt" \
            --gas="auto" \
            --gas-adjustment=1.15 \
            --broadcast-mode=block \
            --yes
        
        # Get the new DSEQ
        AKASH_DSEQ=$(akash query deployment list --owner "$AKASH_ACCOUNT_ADDRESS" --output json | jq -r '.deployments[0].deployment.deployment_id.dseq')
        echo "export AKASH_DSEQ=$AKASH_DSEQ" >> "$PROJECT_DIR/.env"
        log INFO "New deployment created with DSEQ: $AKASH_DSEQ"
    fi
    
    log SUCCESS "Deployment command sent successfully"
}

# Wait for deployment to be active
wait_for_deployment() {
    log INFO "Waiting for deployment to become active..."
    
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        local status=$(akash query deployment get \
            --owner "$AKASH_ACCOUNT_ADDRESS" \
            --dseq "$AKASH_DSEQ" \
            --output json 2>/dev/null | jq -r '.deployment.state' || echo "unknown")
        
        case $status in
            "active")
                log SUCCESS "Deployment is active!"
                return 0
                ;;
            "closed")
                log ERROR "Deployment was closed"
                return 1
                ;;
            *)
                log GEAR "Deployment status: $status (attempt $attempt/$max_attempts)"
                sleep 10
                ;;
        esac
        
        ((attempt++))
    done
    
    log ERROR "Deployment did not become active within expected time"
    return 1
}

# Get deployment URI
get_deployment_uri() {
    log INFO "Getting deployment URI..."
    
    local uri=$(akash provider lease-status \
        --node "$AKASH_NODE" \
        --owner "$AKASH_ACCOUNT_ADDRESS" \
        --dseq "$AKASH_DSEQ" \
        --oseq 1 \
        --gseq 1 \
        --provider "$AKASH_PROVIDER" \
        --output json | jq -r '.services."omega-ai".uris[0]' 2>/dev/null || echo "")
    
    if [ -n "$uri" ] && [ "$uri" != "null" ]; then
        echo "$uri" > "$PROJECT_DIR/.akash-uri"
        log SUCCESS "Deployment URI: $uri"
        return 0
    else
        log WARNING "Could not retrieve deployment URI. Will retry..."
        return 1
    fi
}

# Health check deployment
health_check_deployment() {
    local uri_file="$PROJECT_DIR/.akash-uri"
    
    if [ ! -f "$uri_file" ]; then
        log ERROR "No deployment URI found. Skipping health check."
        return 1
    fi
    
    local uri=$(cat "$uri_file")
    log INFO "Performing health check on: $uri"
    
    # Wait for service to fully start
    sleep 60
    
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        local health_url="$uri/health"
        
        log GEAR "Health check attempt $attempt/$max_attempts..."
        
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            log SUCCESS "Health check passed!"
            
            # Additional API check
            if curl -f -s "$uri/" > /dev/null 2>&1; then
                log SUCCESS "API endpoint is responding!"
                return 0
            else
                log WARNING "Health endpoint OK, but API endpoint not responding"
            fi
        else
            log WARNING "Health check failed, retrying..."
        fi
        
        sleep 30
        ((attempt++))
    done
    
    log ERROR "Health check failed after $max_attempts attempts"
    return 1
}

# Display deployment information
display_deployment_info() {
    log INFO "Deployment completed successfully!"
    
    local uri_file="$PROJECT_DIR/.akash-uri"
    local uri="Unknown"
    
    if [ -f "$uri_file" ]; then
        uri=$(cat "$uri_file")
    fi
    
    echo
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}                  ${WHITE}🚀 OMEGA PRO AI DEPLOYMENT${NC}                   ${PURPLE}║${NC}"
    echo -e "${PURPLE}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}🌐 URL:${NC}        ${WHITE}$uri${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}📊 DSEQ:${NC}       ${WHITE}${AKASH_DSEQ:-Unknown}${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}🏢 Provider:${NC}   ${WHITE}${AKASH_PROVIDER:-Unknown}${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}🐳 Image:${NC}      ${WHITE}$DOCKER_IMAGE${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}⏰ Time:${NC}       ${WHITE}$(date)${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    # Save deployment info
    cat > "$PROJECT_DIR/deployment-info.json" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "deployment": {
    "uri": "$uri",
    "dseq": "${AKASH_DSEQ:-}",
    "provider": "${AKASH_PROVIDER:-}",
    "image": "$DOCKER_IMAGE"
  },
  "status": "deployed"
}
EOF
}

# Cleanup function
cleanup() {
    log INFO "Cleaning up temporary files..."
    # Add any cleanup operations here
}

# Main deployment function
main() {
    echo -e "${PURPLE}${ROCKET}${NC} ${WHITE}OMEGA PRO AI v10.1 - Akash Deployment${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Execute deployment steps
    check_prerequisites
    build_and_push_image
    create_deployment_manifest
    deploy_to_akash
    wait_for_deployment
    
    # Try to get URI and perform health check
    local uri_attempts=3
    local attempt=1
    while [ $attempt -le $uri_attempts ]; do
        if get_deployment_uri; then
            break
        fi
        log WARNING "Failed to get deployment URI (attempt $attempt/$uri_attempts)"
        sleep 30
        ((attempt++))
    done
    
    health_check_deployment || log WARNING "Health check failed, but deployment may still be starting"
    display_deployment_info
    
    log SUCCESS "OMEGA PRO AI deployment completed!"
    echo -e "${GREEN}${CHECK}${NC} ${WHITE}Your AI system is now running on Akash Network!${NC}"
}

# Execute main function
main "$@"