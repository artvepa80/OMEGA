#!/bin/bash
# OMEGA AI MCP Service Shutdown Script
# Graceful shutdown with proper cleanup

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICE_SCRIPT="$SCRIPT_DIR/omega_mcp_service.py"
LOG_FILE="$PROJECT_ROOT/logs/omega_mcp_shutdown.log"
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

# Function to check if service is running
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

# Function to stop service gracefully
stop_service_gracefully() {
    local pid=$1
    local timeout=${2:-30}  # Default 30 seconds timeout
    
    info "Sending SIGTERM to process $pid..."
    kill -TERM "$pid" 2>/dev/null || {
        warning "Could not send SIGTERM to process $pid"
        return 1
    }
    
    # Wait for graceful shutdown
    local count=0
    while kill -0 "$pid" 2>/dev/null; do
        if [[ $count -ge $timeout ]]; then
            warning "Graceful shutdown timeout after ${timeout}s"
            return 1
        fi
        sleep 1
        ((count++))
        if [[ $((count % 5)) -eq 0 ]]; then
            info "Waiting for graceful shutdown... (${count}s)"
        fi
    done
    
    success "Process stopped gracefully in ${count}s"
    return 0
}

# Function to force stop service
force_stop_service() {
    local pid=$1
    
    warning "Force stopping process $pid with SIGKILL..."
    if kill -KILL "$pid" 2>/dev/null; then
        success "Process force stopped"
        return 0
    else
        error "Could not force stop process $pid"
        return 1
    fi
}

# Function to cleanup related processes
cleanup_related_processes() {
    info "Checking for related processes..."
    
    # Find processes related to omega_mcp
    local related_pids=$(pgrep -f "omega_mcp" 2>/dev/null || true)
    
    if [[ -n "$related_pids" ]]; then
        warning "Found related processes: $related_pids"
        for pid in $related_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                info "Stopping related process $pid..."
                kill -TERM "$pid" 2>/dev/null || true
                sleep 2
                if kill -0 "$pid" 2>/dev/null; then
                    warning "Force stopping stubborn process $pid"
                    kill -KILL "$pid" 2>/dev/null || true
                fi
            fi
        done
    fi
}

# Function to cleanup files and resources
cleanup_resources() {
    info "Cleaning up resources..."
    
    # Remove PID file
    if [[ -f "$PID_FILE" ]]; then
        rm -f "$PID_FILE"
        info "Removed PID file: $PID_FILE"
    fi
    
    # Clean up temporary files
    local temp_files=(
        "/tmp/omega_mcp_*.json"
        "/tmp/omega_mcp_*.log"
        "$PROJECT_ROOT/temp/omega_mcp_*"
    )
    
    for pattern in "${temp_files[@]}"; do
        for file in $pattern 2>/dev/null; do
            if [[ -f "$file" ]]; then
                rm -f "$file"
                info "Cleaned up temporary file: $file"
            fi
        done
    done
    
    # Ensure log directories exist for next startup
    mkdir -p "$PROJECT_ROOT/logs"
}

# Function to show final status
show_final_status() {
    info "Verifying shutdown completion..."
    
    # Check if any omega_mcp processes are still running
    local remaining_processes=$(pgrep -f "omega_mcp" 2>/dev/null | wc -l || echo "0")
    
    if [[ "$remaining_processes" -eq 0 ]]; then
        success "All OMEGA MCP processes have been stopped"
    else
        warning "$remaining_processes related processes may still be running"
    fi
    
    # Check if PID file still exists
    if [[ -f "$PID_FILE" ]]; then
        warning "PID file still exists: $PID_FILE"
    fi
    
    # Show summary
    echo ""
    echo "Shutdown Summary:"
    echo "  Service stopped: ✅"
    echo "  Resources cleaned: ✅"  
    echo "  Related processes: $([ "$remaining_processes" -eq 0 ] && echo "✅ None remaining" || echo "⚠️ $remaining_processes may remain")"
    echo ""
    echo "To restart the service:"
    echo "  $SCRIPT_DIR/start_omega_mcp.sh"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --force           Force stop without graceful shutdown"
    echo "  --timeout=N       Graceful shutdown timeout in seconds (default: 30)"
    echo "  --quiet           Reduce output verbosity"
    echo "  --cleanup-only    Only cleanup resources, don't stop processes"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Stop service gracefully"
    echo "  $0 --force           # Force stop immediately"
    echo "  $0 --timeout=60      # Wait up to 60s for graceful shutdown"
    echo "  $0 --cleanup-only    # Just cleanup leftover resources"
}

# Main execution
main() {
    local force_stop=false
    local graceful_timeout=30
    local quiet_mode=false
    local cleanup_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force_stop=true
                shift
                ;;
            --timeout=*)
                graceful_timeout="${1#*=}"
                shift
                ;;
            --quiet)
                quiet_mode=true
                shift
                ;;
            --cleanup-only)
                cleanup_only=true
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
    
    # Redirect output if quiet mode
    if [[ "$quiet_mode" == true ]]; then
        exec 1>/dev/null
    fi
    
    # Create log file directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    info "🛑 OMEGA AI MCP Service Shutdown Script"
    info "Project Root: $PROJECT_ROOT"
    
    # If cleanup-only mode, just cleanup and exit
    if [[ "$cleanup_only" == true ]]; then
        cleanup_resources
        success "Resource cleanup completed"
        exit 0
    fi
    
    # Check if service is running
    if ! check_if_running; then
        warning "OMEGA AI MCP Service is not running"
        
        # Still perform cleanup in case of leftover resources
        cleanup_resources
        success "Cleanup completed - service was not running"
        exit 0
    fi
    
    # Get PID
    local service_pid=$(cat "$PID_FILE" 2>/dev/null)
    info "Found running service with PID: $service_pid"
    
    # Stop the service
    local stop_successful=false
    
    if [[ "$force_stop" == true ]]; then
        # Force stop immediately
        if force_stop_service "$service_pid"; then
            stop_successful=true
        fi
    else
        # Try graceful shutdown first
        if stop_service_gracefully "$service_pid" "$graceful_timeout"; then
            stop_successful=true
        else
            warning "Graceful shutdown failed, trying force stop..."
            if force_stop_service "$service_pid"; then
                stop_successful=true
            fi
        fi
    fi
    
    # Cleanup related processes regardless of main service stop result
    cleanup_related_processes
    
    # Cleanup resources
    cleanup_resources
    
    # Show final status
    if [[ "$quiet_mode" != true ]]; then
        show_final_status
    fi
    
    if [[ "$stop_successful" == true ]]; then
        success "🎉 OMEGA AI MCP Service shutdown completed successfully!"
        exit 0
    else
        error "Service shutdown encountered issues"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"