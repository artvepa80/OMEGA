#!/bin/bash

# =======================================================
# OMEGA PRO AI v10.1 - Production Deployment Script
# Comprehensive deployment automation for multiple platforms
# =======================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_FILE="${PROJECT_DIR}/logs/deployment-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}

info() { log "INFO" "${BLUE}$*${NC}"; }
success() { log "SUCCESS" "${GREEN}$*${NC}"; }
warning() { log "WARNING" "${YELLOW}$*${NC}"; }
error() { log "ERROR" "${RED}$*${NC}"; }

# Create logs directory
mkdir -p "${PROJECT_DIR}/logs"

# Banner
echo "=========================================================="
echo "🚀 OMEGA PRO AI v10.1 - Production Deployment"
echo "=========================================================="
info "Starting deployment at $(date)"
info "Project directory: $PROJECT_DIR"
info "Log file: $LOG_FILE"
echo ""

# Configuration
DEPLOYMENT_TARGET="${1:-auto}"
FORCE_REBUILD="${2:-false}"
SKIP_TESTS="${3:-false}"
DRY_RUN="${4:-false}"

info "Configuration:"
info "  - Deployment Target: $DEPLOYMENT_TARGET"
info "  - Force Rebuild: $FORCE_REBUILD"
info "  - Skip Tests: $SKIP_TESTS"
info "  - Dry Run: $DRY_RUN"
echo ""

# Functions
check_dependencies() {
    info "🔍 Checking dependencies..."
    
    local deps=("docker" "docker-compose" "git")
    local missing_deps=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        error "Missing dependencies: ${missing_deps[*]}"
        exit 1
    fi
    
    success "✅ All dependencies available"
}

validate_environment() {
    info "🔧 Validating environment..."
    
    # Check required files
    local required_files=(
        "Dockerfile"
        "docker-compose.prod.yml"
        ".env.production"
        "requirements-production.txt"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "${PROJECT_DIR}/$file" ]; then
            error "Required file missing: $file"
            exit 1
        fi
    done
    
    # Check environment variables
    if [ ! -f "${PROJECT_DIR}/.env.production" ]; then
        warning "Production environment file not found"
    fi
    
    success "✅ Environment validation passed"
}

run_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        warning "⏭️ Skipping tests (SKIP_TESTS=true)"
        return 0
    fi
    
    info "🧪 Running tests..."
    
    cd "$PROJECT_DIR"
    
    # Create virtual environment for testing
    if [ ! -d "venv_test" ]; then
        python3 -m venv venv_test
    fi
    
    source venv_test/bin/activate
    
    # Install test dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install pytest pytest-asyncio httpx
    
    # Run tests
    if python -m pytest tests/ -v --tb=short; then
        success "✅ All tests passed"
    else
        error "❌ Tests failed"
        deactivate
        exit 1
    fi
    
    deactivate
}

build_docker_images() {
    info "🏗️ Building Docker images..."
    
    cd "$PROJECT_DIR"
    
    # Build main application image
    if [ "$FORCE_REBUILD" = "true" ]; then
        info "Force rebuilding (--no-cache)"
        docker build --no-cache -t omega-pro-ai:latest -t omega-pro-ai:v10.1 .
    else
        docker build -t omega-pro-ai:latest -t omega-pro-ai:v10.1 .
    fi
    
    # Tag for different registries if needed
    if [ -n "${DOCKER_REGISTRY:-}" ]; then
        docker tag omega-pro-ai:latest "${DOCKER_REGISTRY}/omega-pro-ai:latest"
        docker tag omega-pro-ai:v10.1 "${DOCKER_REGISTRY}/omega-pro-ai:v10.1"
    fi
    
    success "✅ Docker images built successfully"
}

deploy_local() {
    info "🏠 Deploying locally with Docker Compose..."
    
    cd "$PROJECT_DIR"
    
    if [ "$DRY_RUN" = "true" ]; then
        info "DRY RUN: Would execute:"
        echo "  docker-compose -f docker-compose.prod.yml up -d"
        return 0
    fi
    
    # Stop existing deployment
    docker-compose -f docker-compose.prod.yml down || true
    
    # Start production deployment
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    info "⏳ Waiting for services to be ready..."
    sleep 30
    
    # Health check
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        success "✅ Local deployment successful and healthy"
    else
        error "❌ Local deployment health check failed"
        exit 1
    fi
}

deploy_railway() {
    info "🚂 Deploying to Railway..."
    
    if [ "$DRY_RUN" = "true" ]; then
        info "DRY RUN: Would deploy to Railway"
        return 0
    fi
    
    # Check if railway CLI is available
    if ! command -v railway &> /dev/null; then
        error "Railway CLI not found. Install with: npm install -g @railway/cli"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # Deploy to Railway
    railway deploy
    
    success "✅ Railway deployment initiated"
}

deploy_akash() {
    info "☁️ Deploying to Akash Network..."
    
    if [ "$DRY_RUN" = "true" ]; then
        info "DRY RUN: Would deploy to Akash Network"
        return 0
    fi
    
    # Check if akash CLI is available
    if ! command -v akash &> /dev/null; then
        error "Akash CLI not found. Please install Akash CLI"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # Use the production deployment configuration
    local deployment_file="deploy/production-akash-secure.yaml"
    
    if [ ! -f "$deployment_file" ]; then
        error "Akash deployment file not found: $deployment_file"
        exit 1
    fi
    
    # Deploy to Akash (this would need proper wallet and configuration)
    info "Using deployment file: $deployment_file"
    warning "Manual Akash deployment required - automated deployment needs wallet setup"
    
    success "✅ Akash deployment configuration ready"
}

deploy_vercel() {
    info "▲ Deploying to Vercel..."
    
    if [ "$DRY_RUN" = "true" ]; then
        info "DRY RUN: Would deploy to Vercel"
        return 0
    fi
    
    # Check if vercel CLI is available
    if ! command -v vercel &> /dev/null; then
        error "Vercel CLI not found. Install with: npm install -g vercel"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # Deploy to Vercel
    vercel --prod
    
    success "✅ Vercel deployment successful"
}

run_health_checks() {
    info "🔍 Running post-deployment health checks..."
    
    # Run comprehensive health checks
    if [ -f "${PROJECT_DIR}/config/health_checks_production.py" ]; then
        cd "$PROJECT_DIR"
        python config/health_checks_production.py
    else
        warning "Health check script not found, running basic checks..."
        
        # Basic health checks
        local endpoints=(
            "http://localhost:8000/health"
            "http://localhost:8000/"
        )
        
        for endpoint in "${endpoints[@]}"; do
            if curl -f "$endpoint" > /dev/null 2>&1; then
                success "✅ $endpoint is healthy"
            else
                error "❌ $endpoint health check failed"
            fi
        done
    fi
}

cleanup() {
    info "🧹 Cleaning up..."
    
    # Remove test virtual environment
    [ -d "${PROJECT_DIR}/venv_test" ] && rm -rf "${PROJECT_DIR}/venv_test"
    
    # Clean up temporary files
    find "$PROJECT_DIR" -name "*.pyc" -delete 2>/dev/null || true
    find "$PROJECT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    success "✅ Cleanup completed"
}

generate_deployment_report() {
    info "📊 Generating deployment report..."
    
    local report_file="${PROJECT_DIR}/logs/deployment-report-$(date +%Y%m%d-%H%M%S).json"
    
    cat > "$report_file" << EOF
{
    "deployment": {
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "target": "$DEPLOYMENT_TARGET",
        "version": "10.1",
        "force_rebuild": "$FORCE_REBUILD",
        "skip_tests": "$SKIP_TESTS",
        "dry_run": "$DRY_RUN"
    },
    "git": {
        "commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
        "branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')"
    },
    "system": {
        "os": "$(uname -s)",
        "arch": "$(uname -m)",
        "docker_version": "$(docker --version 2>/dev/null || echo 'not available')"
    }
}
EOF
    
    success "✅ Deployment report saved: $report_file"
}

# Main deployment logic
main() {
    cd "$PROJECT_DIR"
    
    # Pre-deployment checks
    check_dependencies
    validate_environment
    
    # Run tests unless skipped
    run_tests
    
    # Build Docker images
    build_docker_images
    
    # Deploy based on target
    case "$DEPLOYMENT_TARGET" in
        "local")
            deploy_local
            ;;
        "railway")
            deploy_railway
            ;;
        "akash")
            deploy_akash
            ;;
        "vercel")
            deploy_vercel
            ;;
        "all")
            info "🌐 Deploying to all platforms..."
            deploy_local
            deploy_railway
            deploy_akash
            deploy_vercel
            ;;
        "auto")
            info "🤖 Auto-detecting deployment target..."
            if [ -f "railway.toml" ]; then
                deploy_railway
            elif [ -f "vercel.json" ]; then
                deploy_vercel
            else
                deploy_local
            fi
            ;;
        *)
            error "Unknown deployment target: $DEPLOYMENT_TARGET"
            error "Valid targets: local, railway, akash, vercel, all, auto"
            exit 1
            ;;
    esac
    
    # Post-deployment checks
    run_health_checks
    
    # Cleanup and reporting
    cleanup
    generate_deployment_report
    
    success "🎉 Deployment completed successfully!"
    info "📄 Check logs at: $LOG_FILE"
}

# Error handling
trap 'error "Deployment failed at line $LINENO"; exit 1' ERR

# Usage information
if [ "$#" -gt 4 ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "Usage: $0 [TARGET] [FORCE_REBUILD] [SKIP_TESTS] [DRY_RUN]"
    echo ""
    echo "Arguments:"
    echo "  TARGET        : local, railway, akash, vercel, all, auto (default: auto)"
    echo "  FORCE_REBUILD : true/false (default: false)"
    echo "  SKIP_TESTS    : true/false (default: false)"
    echo "  DRY_RUN       : true/false (default: false)"
    echo ""
    echo "Examples:"
    echo "  $0                          # Auto-detect target"
    echo "  $0 local                    # Deploy locally"
    echo "  $0 railway true             # Deploy to Railway with rebuild"
    echo "  $0 all false false true     # Dry run deployment to all platforms"
    exit 0
fi

# Execute main function
main "$@"