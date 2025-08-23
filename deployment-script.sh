#!/bin/bash

# 🚀 OMEGA AI Production Deployment Script
# Complete orchestration for conversational AI system with monitoring

set -e

echo "🤖 OMEGA AI - Production Deployment Starting..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="./logs/deployment_$(date +%Y%m%d_%H%M%S).log"

# Create directories
mkdir -p logs backups data

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "🔍 Running pre-deployment checks..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose > /dev/null 2>&1; then
        error "docker-compose is not installed. Please install docker-compose."
        exit 1
    fi
    
    # Check required files
    local required_files=(
        "$COMPOSE_FILE"
        "conversational_ai_system.py"
        "api_main.py"
        "omega_integrated_system.py"
        "requirements-conversational.txt"
        "requirements-railway.txt"
        "Dockerfile.api"
        "Dockerfile.chat"
        "config/prometheus.yml"
        "config/nginx.conf"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Required file missing: $file"
            exit 1
        fi
    done
    
    log "✅ Pre-deployment checks passed"
}

# Create backup
create_backup() {
    log "📦 Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup configuration files
    cp -r config/ "$BACKUP_DIR/" 2>/dev/null || true
    cp -r data/ "$BACKUP_DIR/" 2>/dev/null || true
    cp docker-compose*.yml "$BACKUP_DIR/" 2>/dev/null || true
    
    # Backup Redis data if container exists
    if docker ps -a --format 'table {{.Names}}' | grep -q omega_redis; then
        log "Backing up Redis data..."
        docker exec omega_redis redis-cli BGSAVE > /dev/null 2>&1 || true
        docker cp omega_redis:/data/dump.rdb "$BACKUP_DIR/redis_dump.rdb" 2>/dev/null || true
    fi
    
    log "✅ Backup created at $BACKUP_DIR"
}

# Setup environment
setup_environment() {
    log "🔧 Setting up environment..."
    
    # Create data directories
    mkdir -p data/redis data/prometheus data/grafana logs
    
    # Set proper permissions
    chmod -R 755 config/
    chmod -R 755 logs/
    
    # Create .env file if it doesn't exist
    if [[ ! -f .env ]]; then
        cat > .env << EOF
# OMEGA AI Production Environment
REDIS_URL=redis://redis:6379
METRICS_PORT=8081
ENVIRONMENT=production
PYTHONUNBUFFERED=1

# Security (change these in production)
GRAFANA_ADMIN_PASSWORD=omega123

# Monitoring
PROMETHEUS_RETENTION=200h
EOF
        warning "Created default .env file. Please review and update security settings."
    fi
    
    log "✅ Environment setup complete"
}

# Build images
build_images() {
    log "🏗️  Building Docker images..."
    
    # Build with proper context and cache
    docker-compose -f "$COMPOSE_FILE" build --no-cache --parallel
    
    if [[ $? -eq 0 ]]; then
        log "✅ Docker images built successfully"
    else
        error "Failed to build Docker images"
        exit 1
    fi
}

# Deploy services
deploy_services() {
    log "🚀 Deploying services..."
    
    # Stop existing services
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans || true
    
    # Start services with proper order
    info "Starting Redis..."
    docker-compose -f "$COMPOSE_FILE" up -d redis
    sleep 10
    
    info "Starting OMEGA API..."
    docker-compose -f "$COMPOSE_FILE" up -d omega_api
    sleep 15
    
    info "Starting Conversational AI..."
    docker-compose -f "$COMPOSE_FILE" up -d conversational_ai
    sleep 10
    
    info "Starting monitoring services..."
    docker-compose -f "$COMPOSE_FILE" up -d prometheus grafana
    sleep 10
    
    info "Starting reverse proxy..."
    docker-compose -f "$COMPOSE_FILE" up -d nginx
    
    log "✅ All services deployed"
}

# Health checks
health_checks() {
    log "🏥 Running health checks..."
    
    local max_retries=30
    local retry_count=0
    
    # Check Redis
    info "Checking Redis..."
    while [[ $retry_count -lt $max_retries ]]; do
        if docker exec omega_redis redis-cli ping > /dev/null 2>&1; then
            log "✅ Redis is healthy"
            break
        fi
        ((retry_count++))
        sleep 2
    done
    
    if [[ $retry_count -eq $max_retries ]]; then
        error "Redis health check failed"
        return 1
    fi
    
    # Check OMEGA API
    info "Checking OMEGA API..."
    retry_count=0
    while [[ $retry_count -lt $max_retries ]]; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log "✅ OMEGA API is healthy"
            break
        fi
        ((retry_count++))
        sleep 2
    done
    
    if [[ $retry_count -eq $max_retries ]]; then
        error "OMEGA API health check failed"
        return 1
    fi
    
    # Check Conversational AI
    info "Checking Conversational AI..."
    retry_count=0
    while [[ $retry_count -lt $max_retries ]]; do
        if curl -f http://localhost:8080/health > /dev/null 2>&1; then
            log "✅ Conversational AI is healthy"
            break
        fi
        ((retry_count++))
        sleep 2
    done
    
    if [[ $retry_count -eq $max_retries ]]; then
        error "Conversational AI health check failed"
        return 1
    fi
    
    # Check Prometheus
    info "Checking Prometheus..."
    if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
        log "✅ Prometheus is healthy"
    else
        warning "Prometheus health check failed"
    fi
    
    # Check Grafana
    info "Checking Grafana..."
    if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
        log "✅ Grafana is healthy"
    else
        warning "Grafana health check failed"
    fi
    
    log "✅ Health checks completed"
}

# Show deployment summary
show_summary() {
    log "📋 Deployment Summary"
    
    echo ""
    echo "🎯 OMEGA AI System URLs:"
    echo "├── Main API: http://localhost:8000"
    echo "├── API Docs: http://localhost:8000/docs"
    echo "├── Chat API: http://localhost:8080"
    echo "├── Chat Health: http://localhost:8080/health"
    echo "├── Prometheus: http://localhost:9090"
    echo "└── Grafana: http://localhost:3000 (admin/omega123)"
    echo ""
    
    echo "🔍 Service Status:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    
    echo "📊 Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
    echo ""
    
    echo "🚀 Next Steps:"
    echo "1. Test the APIs: curl http://localhost:8000/health"
    echo "2. Monitor with Grafana: http://localhost:3000"
    echo "3. Check logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "4. Scale if needed: docker-compose -f $COMPOSE_FILE up -d --scale conversational_ai=2"
    echo ""
    
    info "Deployment completed successfully! 🎉"
}

# Rollback function
rollback() {
    error "Deployment failed. Starting rollback..."
    
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans || true
    
    if [[ -d "$BACKUP_DIR" ]]; then
        log "Restoring from backup..."
        cp -r "$BACKUP_DIR/config/" ./ 2>/dev/null || true
        cp -r "$BACKUP_DIR/data/" ./ 2>/dev/null || true
    fi
    
    error "Rollback completed. Please check the logs for issues."
    exit 1
}

# Cleanup function
cleanup() {
    log "🧹 Cleaning up unused resources..."
    
    # Remove unused containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful with this)
    # docker volume prune -f
    
    log "✅ Cleanup completed"
}

# Signal handlers
trap 'error "Deployment interrupted"; rollback' INT TERM

# Main deployment flow
main() {
    log "🚀 Starting OMEGA AI Production Deployment"
    
    # Check if running with --rollback flag
    if [[ "$1" == "--rollback" ]]; then
        rollback
        return
    fi
    
    # Check if running with --cleanup flag
    if [[ "$1" == "--cleanup" ]]; then
        cleanup
        return
    fi
    
    # Normal deployment flow
    pre_deployment_checks || rollback
    create_backup || rollback
    setup_environment || rollback
    build_images || rollback
    deploy_services || rollback
    
    # Wait for services to be ready
    sleep 30
    
    health_checks || rollback
    show_summary
    cleanup
    
    log "🎉 OMEGA AI Production Deployment Completed Successfully!"
}

# Run main function
main "$@"