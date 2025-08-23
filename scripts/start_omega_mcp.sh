#!/bin/bash
# OMEGA AI MCP Service Startup Script
# Production-ready startup with error handling and validation

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICE_SCRIPT="$SCRIPT_DIR/omega_mcp_service.py"
LOG_FILE="$PROJECT_ROOT/logs/omega_mcp_startup.log"
PID_FILE="$PROJECT_ROOT/logs/omega_mcp.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ ERROR: $1${NC}" >&2
    log "ERROR: $1"
}

info() {
    echo -e "${BLUE}ℹ️  INFO: $1${NC}"
    log "INFO: $1"
}

success() {
    echo -e "${GREEN}✅ SUCCESS: $1${NC}"
    log "SUCCESS: $1"
}

warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    log "WARNING: $1"
}

# Function to check if service is already running
check_if_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            return 0  # Service is running
        else
            # Stale PID file
            rm -f "$PID_FILE"
            return 1  # Service not running
        fi
    fi
    return 1  # Service not running
}

# Function to validate environment
validate_environment() {
    info "Validating environment..."
    
    # Check if we're in the project root
    if [[ ! -f "$PROJECT_ROOT/omega_mcp_integration.py" ]]; then
        error "Not in OMEGA AI project root. Please run from the project directory."
        return 1
    fi
    
    # Check Python version
    if ! python3 --version >/dev/null 2>&1; then
        error "Python 3 is required but not installed."
        return 1
    fi
    
    # Check required directories
    local dirs=("logs" "data" "config" "mcps")
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$PROJECT_ROOT/$dir" ]]; then
            info "Creating missing directory: $dir"
            mkdir -p "$PROJECT_ROOT/$dir"
        fi
    done
    
    # Check if MCP dependencies are installed
    if ! python3 -c "import apscheduler, twilio, bs4" >/dev/null 2>&1; then
        warning "Some MCP dependencies may be missing. Run: pip install -r requirements.txt"
    fi
    
    success "Environment validation completed"
    return 0
}

# Function to check configuration
check_configuration() {
    info "Checking configuration..."
    
    local config_ok=true
    
    # Check if MCP config exists
    if [[ ! -f "$PROJECT_ROOT/config/mcp_config.json" ]]; then
        warning "MCP configuration file not found. Using defaults."
    fi
    
    # Check if credentials are configured
    if [[ ! -f "$PROJECT_ROOT/config/credentials.json" ]] && [[ -z "${TWILIO_ACCOUNT_SID:-}" ]]; then
        warning "No credentials found. MCP services will run in limited mode."
        warning "Set up credentials.json or environment variables for full functionality."
        config_ok=false
    fi
    
    # Check if user preferences exist
    if [[ ! -f "$PROJECT_ROOT/config/user_preferences.json" ]]; then
        info "User preferences not found. Will create default preferences."
    fi
    
    if [[ "$config_ok" == true ]]; then
        success "Configuration check completed"
    else
        warning "Configuration check completed with warnings"
    fi
    
    return 0
}

# Function to perform health check
health_check() {
    info "Performing health check..."
    
    cd "$PROJECT_ROOT"
    if python3 "$SERVICE_SCRIPT" health --output json > /tmp/omega_mcp_health.json 2>/dev/null; then
        local status=$(python3 -c "import json; print(json.load(open('/tmp/omega_mcp_health.json')).get('status', 'unknown'))" 2>/dev/null)
        if [[ "$status" == "healthy" ]]; then
            success "Health check passed - all systems healthy"
        else
            warning "Health check passed but some issues detected: $status"
        fi
    else
        warning "Health check could not be performed"
    fi
    
    # Cleanup temp file
    rm -f /tmp/omega_mcp_health.json
}

# Function to start the service
start_service() {
    info "Starting OMEGA AI MCP Service..."
    
    cd "$PROJECT_ROOT"
    
    # Start service in background with nohup
    nohup python3 "$SERVICE_SCRIPT" start --daemon \
        > "$PROJECT_ROOT/logs/omega_mcp_daemon.log" 2>&1 &
    
    local service_pid=$!
    echo "$service_pid" > "$PID_FILE"
    
    # Wait a bit and check if service started successfully
    sleep 3
    
    if kill -0 "$service_pid" 2>/dev/null; then
        success "OMEGA AI MCP Service started successfully (PID: $service_pid)"
        
        # Perform health check after startup
        sleep 5
        health_check
        
        info "Service logs: $PROJECT_ROOT/logs/omega_mcp_daemon.log"
        info "To stop the service, run: $SCRIPT_DIR/stop_omega_mcp.sh"
        info "To check status, run: python3 $SERVICE_SCRIPT status"
        
        return 0
    else
        error "Service failed to start or exited immediately"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --force           Force start even if service appears to be running"
    echo "  --no-health       Skip health check after startup"
    echo "  --validate-only   Only validate environment, don't start service"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start service normally"
    echo "  $0 --force           # Force restart if already running"
    echo "  $0 --validate-only   # Just check if everything is configured"
}

# Main execution
main() {
    local force_start=false
    local skip_health=false
    local validate_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force_start=true
                shift
                ;;
            --no-health)
                skip_health=true
                shift
                ;;
            --validate-only)
                validate_only=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Create log file directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    info "🚀 OMEGA AI MCP Service Startup Script"
    info "Project Root: $PROJECT_ROOT"
    
    # Validate environment first
    if ! validate_environment; then
        error "Environment validation failed. Cannot start service."
        exit 1
    fi
    
    # Check configuration
    check_configuration
    
    # If validate-only flag is set, exit here
    if [[ "$validate_only" == true ]]; then
        success "Environment and configuration validation completed"
        exit 0
    fi
    
    # Check if service is already running
    if check_if_running; then
        if [[ "$force_start" == false ]]; then
            warning "OMEGA AI MCP Service is already running (PID: $(cat "$PID_FILE"))"
            warning "Use --force to restart the service"
            exit 1
        else
            info "Force starting - stopping existing service first"
            "$SCRIPT_DIR/stop_omega_mcp.sh" --quiet
            sleep 2
        fi
    fi
    
    # Start the service
    if start_service; then
        success "🎉 OMEGA AI MCP Service startup completed successfully!"
        
        # Show service information
        echo ""
        echo "Service Information:"
        echo "  PID File: $PID_FILE"
        echo "  Log File: $PROJECT_ROOT/logs/omega_mcp_daemon.log"
        echo "  Config: $PROJECT_ROOT/config/mcp_config.json"
        echo ""
        echo "Useful Commands:"
        echo "  Status:    python3 $SERVICE_SCRIPT status"
        echo "  Health:    python3 $SERVICE_SCRIPT health"
        echo "  Stop:      $SCRIPT_DIR/stop_omega_mcp.sh"
        echo "  Restart:   $SCRIPT_DIR/restart_omega_mcp.sh"
        
    else
        error "Failed to start OMEGA AI MCP Service"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"