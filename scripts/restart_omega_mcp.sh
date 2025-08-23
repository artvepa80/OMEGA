#!/bin/bash
# OMEGA AI MCP Service Restart Script
# Graceful restart with validation and health checks

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
START_SCRIPT="$SCRIPT_DIR/start_omega_mcp.sh"
STOP_SCRIPT="$SCRIPT_DIR/stop_omega_mcp.sh"
LOG_FILE="$PROJECT_ROOT/logs/omega_mcp_restart.log"

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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --fast            Fast restart (shorter delays between stop/start)"
    echo "  --force           Force restart even if service appears healthy"
    echo "  --validate        Validate configuration before restart"
    echo "  --timeout=N       Graceful shutdown timeout in seconds (default: 30)"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Normal restart"
    echo "  $0 --fast           # Quick restart with minimal delays"
    echo "  $0 --force          # Force restart regardless of current state"
    echo "  $0 --validate       # Validate configuration before restarting"
}

# Function to validate restart conditions
validate_restart_conditions() {
    info "Validating restart conditions..."
    
    # Check if scripts exist
    if [[ ! -x "$START_SCRIPT" ]]; then
        error "Start script not found or not executable: $START_SCRIPT"
        return 1
    fi
    
    if [[ ! -x "$STOP_SCRIPT" ]]; then
        error "Stop script not found or not executable: $STOP_SCRIPT"
        return 1
    fi
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/omega_mcp_integration.py" ]]; then
        error "Not in OMEGA AI project root directory"
        return 1
    fi
    
    success "Restart conditions validated"
    return 0
}

# Function to backup current state
backup_current_state() {
    info "Backing up current state..."
    
    local backup_dir="$PROJECT_ROOT/data/backups/restart_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup configuration files
    for config_file in "config/mcp_config.json" "config/user_preferences.json" "config/credentials.json"; do
        if [[ -f "$PROJECT_ROOT/$config_file" ]]; then
            cp "$PROJECT_ROOT/$config_file" "$backup_dir/" 2>/dev/null || true
        fi
    done
    
    # Backup recent logs
    if [[ -f "$PROJECT_ROOT/logs/omega_mcp_daemon.log" ]]; then
        cp "$PROJECT_ROOT/logs/omega_mcp_daemon.log" "$backup_dir/daemon_log_backup.log" 2>/dev/null || true
    fi
    
    info "State backed up to: $backup_dir"
    echo "$backup_dir" # Return backup directory path
}

# Function to perform health check before restart
pre_restart_health_check() {
    info "Performing pre-restart health check..."
    
    cd "$PROJECT_ROOT"
    if python3 "scripts/omega_mcp_service.py" health --output json > /tmp/omega_mcp_pre_restart_health.json 2>/dev/null; then
        local status=$(python3 -c "import json; print(json.load(open('/tmp/omega_mcp_pre_restart_health.json')).get('status', 'unknown'))" 2>/dev/null)
        info "Current service health: $status"
        rm -f /tmp/omega_mcp_pre_restart_health.json
        return 0
    else
        warning "Could not determine current service health"
        rm -f /tmp/omega_mcp_pre_restart_health.json
        return 1
    fi
}

# Function to perform post-restart validation
post_restart_validation() {
    info "Performing post-restart validation..."
    
    # Wait for service to fully start
    local max_wait=60
    local wait_count=0
    
    while [[ $wait_count -lt $max_wait ]]; do
        if python3 "$PROJECT_ROOT/scripts/omega_mcp_service.py" status --output json >/dev/null 2>&1; then
            break
        fi
        sleep 1
        ((wait_count++))
        if [[ $((wait_count % 10)) -eq 0 ]]; then
            info "Waiting for service to start... (${wait_count}s)"
        fi
    done
    
    if [[ $wait_count -ge $max_wait ]]; then
        error "Service did not start within ${max_wait} seconds"
        return 1
    fi
    
    # Perform health check
    cd "$PROJECT_ROOT"
    if python3 "scripts/omega_mcp_service.py" health --output json > /tmp/omega_mcp_post_restart_health.json 2>/dev/null; then
        local status=$(python3 -c "import json; print(json.load(open('/tmp/omega_mcp_post_restart_health.json')).get('status', 'unknown'))" 2>/dev/null)
        
        if [[ "$status" == "healthy" ]]; then
            success "Post-restart validation passed - service is healthy"
            rm -f /tmp/omega_mcp_post_restart_health.json
            return 0
        else
            warning "Post-restart validation warning - service health: $status"
            rm -f /tmp/omega_mcp_post_restart_health.json
            return 1
        fi
    else
        error "Post-restart validation failed - could not check service health"
        rm -f /tmp/omega_mcp_post_restart_health.json
        return 1
    fi
}

# Main restart function
perform_restart() {
    local fast_mode=$1
    local force_restart=$2
    local graceful_timeout=$3
    local validate_config=$4
    
    # Backup current state
    local backup_dir=$(backup_current_state)
    
    # Pre-restart health check (if not forcing)
    if [[ "$force_restart" != true ]]; then
        if ! pre_restart_health_check; then
            warning "Pre-restart health check failed, proceeding anyway..."
        fi
    fi
    
    # Validate configuration if requested
    if [[ "$validate_config" == true ]]; then
        info "Validating configuration..."
        if ! "$START_SCRIPT" --validate-only; then
            error "Configuration validation failed"
            return 1
        fi
        success "Configuration validation passed"
    fi
    
    # Stop the service
    info "Stopping OMEGA AI MCP Service..."
    local stop_args=("--quiet")
    if [[ "$graceful_timeout" -ne 30 ]]; then
        stop_args+=("--timeout=$graceful_timeout")
    fi
    
    if ! "$STOP_SCRIPT" "${stop_args[@]}"; then
        error "Failed to stop service"
        return 1
    fi
    
    success "Service stopped successfully"
    
    # Wait between stop and start (unless fast mode)
    if [[ "$fast_mode" != true ]]; then
        info "Waiting for complete shutdown..."
        sleep 5
    else
        sleep 1
    fi
    
    # Start the service
    info "Starting OMEGA AI MCP Service..."
    if ! "$START_SCRIPT" --no-health; then
        error "Failed to start service"
        return 1
    fi
    
    success "Service started successfully"
    
    # Post-restart validation (unless fast mode)
    if [[ "$fast_mode" != true ]]; then
        if ! post_restart_validation; then
            warning "Post-restart validation had issues, but service appears to be running"
        fi
    fi
    
    # Show restart summary
    echo ""
    echo "🎉 Restart Summary:"
    echo "  ✅ Service stopped gracefully"
    echo "  ✅ Service started successfully"
    echo "  📁 State backed up to: $backup_dir"
    echo "  🕒 Total restart time: $((SECONDS))s"
    echo ""
    echo "Service Status:"
    python3 "$PROJECT_ROOT/scripts/omega_mcp_service.py" status 2>/dev/null || echo "  Status check unavailable"
    
    return 0
}

# Main execution
main() {
    local fast_mode=false
    local force_restart=false
    local graceful_timeout=30
    local validate_config=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --fast)
                fast_mode=true
                shift
                ;;
            --force)
                force_restart=true
                shift
                ;;
            --timeout=*)
                graceful_timeout="${1#*=}"
                shift
                ;;
            --validate)
                validate_config=true
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
    
    info "🔄 OMEGA AI MCP Service Restart Script"
    info "Project Root: $PROJECT_ROOT"
    
    # Track total time
    SECONDS=0
    
    # Validate restart conditions
    if ! validate_restart_conditions; then
        error "Restart validation failed"
        exit 1
    fi
    
    # Perform the restart
    if perform_restart "$fast_mode" "$force_restart" "$graceful_timeout" "$validate_config"; then
        success "🎉 OMEGA AI MCP Service restart completed successfully!"
        
        # Show useful information
        echo ""
        echo "Useful Commands:"
        echo "  Status:    python3 scripts/omega_mcp_service.py status"
        echo "  Health:    python3 scripts/omega_mcp_service.py health"
        echo "  Stop:      $STOP_SCRIPT"
        echo "  Logs:      tail -f logs/omega_mcp_daemon.log"
        
        exit 0
    else
        error "Service restart failed"
        
        # Show recovery instructions
        echo ""
        echo "Recovery Options:"
        echo "  1. Check logs: tail -f logs/omega_mcp_restart.log"
        echo "  2. Manual start: $START_SCRIPT"
        echo "  3. Force start: $START_SCRIPT --force"
        echo "  4. Validate config: $START_SCRIPT --validate-only"
        
        exit 1
    fi
}

# Make scripts executable
chmod +x "$START_SCRIPT" 2>/dev/null || true
chmod +x "$STOP_SCRIPT" 2>/dev/null || true

# Run main function with all arguments
main "$@"