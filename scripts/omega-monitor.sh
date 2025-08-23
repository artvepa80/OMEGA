#!/bin/bash
# 🚀 OMEGA PRO AI - Deployment Monitoring & Health Check
# Monitors Akash deployment health and provides rollback capabilities

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
LOG_FILE="$PROJECT_ROOT/logs/monitoring.log"

# Colors and emojis
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

HEART="❤️"
CHART="📊"
CLOCK="🕐"
FIRE="🔥"
SHIELD="🛡️"
WRENCH="🔧"

# Logging
mkdir -p "$(dirname "$LOG_FILE")"

log_with_timestamp() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    case $level in
        "INFO")
            echo -e "${BLUE}${CHART} [$timestamp] $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}${HEART} [$timestamp] $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  [$timestamp] $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}🚨 [$timestamp] $message${NC}"
            ;;
        "CRITICAL")
            echo -e "${RED}${BOLD}${FIRE} [$timestamp] $message${NC}"
            ;;
    esac
}

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                 ${CHART} OMEGA PRO AI - Deployment Monitor                    ║"
    echo "║                      Health Check & Rollback Tool                           ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

load_environment() {
    if [[ -f "$ENV_FILE" ]]; then
        source "$ENV_FILE"
    else
        log_with_timestamp "ERROR" ".env file not found. Please run setup first."
        exit 1
    fi
}

check_deployment_health() {
    log_with_timestamp "INFO" "Starting comprehensive health check..."
    
    local health_score=0
    local max_score=100
    
    # Test 1: Basic connectivity (20 points)
    log_with_timestamp "INFO" "Testing basic connectivity..."
    if curl -f --connect-timeout 10 "$AKASH_URI/health" &> /dev/null; then
        health_score=$((health_score + 20))
        log_with_timestamp "SUCCESS" "Basic connectivity: PASS"
    else
        log_with_timestamp "ERROR" "Basic connectivity: FAIL"
    fi
    
    # Test 2: API response time (15 points)
    log_with_timestamp "INFO" "Testing API response time..."
    local start_time=$(date +%s%N)
    if curl -f --connect-timeout 5 "$AKASH_URI/" &> /dev/null; then
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 ))  # Convert to milliseconds
        
        if [[ $response_time -lt 2000 ]]; then
            health_score=$((health_score + 15))
            log_with_timestamp "SUCCESS" "Response time: ${response_time}ms (EXCELLENT)"
        elif [[ $response_time -lt 5000 ]]; then
            health_score=$((health_score + 10))
            log_with_timestamp "WARNING" "Response time: ${response_time}ms (ACCEPTABLE)"
        else
            health_score=$((health_score + 5))
            log_with_timestamp "WARNING" "Response time: ${response_time}ms (SLOW)"
        fi
    else
        log_with_timestamp "ERROR" "API response test: FAIL"
    fi
    
    # Test 3: Health endpoint detailed check (15 points)
    log_with_timestamp "INFO" "Testing health endpoint details..."
    local health_response=$(curl -s --connect-timeout 10 "$AKASH_URI/health" 2>/dev/null || echo "{}")
    
    if echo "$health_response" | jq -e '.status == "healthy"' &> /dev/null; then
        health_score=$((health_score + 15))
        log_with_timestamp "SUCCESS" "Health status: HEALTHY"
    elif echo "$health_response" | jq -e '.status' &> /dev/null; then
        health_score=$((health_score + 5))
        local status=$(echo "$health_response" | jq -r '.status')
        log_with_timestamp "WARNING" "Health status: $status"
    else
        log_with_timestamp "ERROR" "Health endpoint: INVALID RESPONSE"
    fi
    
    # Test 4: Prediction endpoint functionality (25 points)
    log_with_timestamp "INFO" "Testing prediction endpoint..."
    local pred_response=$(curl -s --connect-timeout 15 -X POST "$AKASH_URI/predict" \
        -H "Content-Type: application/json" \
        -d '{"cantidad": 3, "perfil_svi": "default"}' 2>/dev/null || echo "{}")
    
    if echo "$pred_response" | jq -e '.predictions | length > 0' &> /dev/null; then
        local pred_count=$(echo "$pred_response" | jq -r '.predictions | length')
        health_score=$((health_score + 25))
        log_with_timestamp "SUCCESS" "Prediction endpoint: FUNCTIONAL ($pred_count predictions)"
        
        # Validate prediction format
        local first_pred=$(echo "$pred_response" | jq -r '.predictions[0].combination // empty')
        if [[ -n "$first_pred" && "$first_pred" != "null" ]]; then
            log_with_timestamp "SUCCESS" "Prediction format: VALID"
        else
            log_with_timestamp "WARNING" "Prediction format: QUESTIONABLE"
        fi
    else
        log_with_timestamp "ERROR" "Prediction endpoint: FAIL"
    fi
    
    # Test 5: Resource usage and performance (15 points)
    log_with_timestamp "INFO" "Testing performance metrics..."
    local perf_start=$(date +%s%N)
    
    # Make multiple rapid requests to test load handling
    local success_count=0
    for i in {1..5}; do
        if curl -f --connect-timeout 3 "$AKASH_URI/" &> /dev/null; then
            success_count=$((success_count + 1))
        fi
    done
    
    local perf_end=$(date +%s%N)
    local total_time=$(( (perf_end - perf_start) / 1000000 ))  # Convert to milliseconds
    
    if [[ $success_count -eq 5 && $total_time -lt 10000 ]]; then
        health_score=$((health_score + 15))
        log_with_timestamp "SUCCESS" "Performance test: EXCELLENT (5/5 requests in ${total_time}ms)"
    elif [[ $success_count -ge 3 ]]; then
        health_score=$((health_score + 10))
        log_with_timestamp "WARNING" "Performance test: ACCEPTABLE ($success_count/5 requests)"
    else
        health_score=$((health_score + 5))
        log_with_timestamp "ERROR" "Performance test: POOR ($success_count/5 requests)"
    fi
    
    # Test 6: Memory and stability (10 points)
    log_with_timestamp "INFO" "Testing memory stability..."
    
    # Test with larger prediction request
    local large_pred_response=$(curl -s --connect-timeout 20 -X POST "$AKASH_URI/predict" \
        -H "Content-Type: application/json" \
        -d '{"cantidad": 20, "perfil_svi": "aggressive"}' 2>/dev/null || echo "{}")
    
    if echo "$large_pred_response" | jq -e '.predictions | length >= 15' &> /dev/null; then
        health_score=$((health_score + 10))
        log_with_timestamp "SUCCESS" "Memory stability: EXCELLENT"
    elif echo "$large_pred_response" | jq -e '.predictions | length >= 5' &> /dev/null; then
        health_score=$((health_score + 5))
        log_with_timestamp "WARNING" "Memory stability: ACCEPTABLE"
    else
        log_with_timestamp "ERROR" "Memory stability: POOR"
    fi
    
    # Calculate health percentage
    local health_percentage=$((health_score * 100 / max_score))
    
    log_with_timestamp "INFO" "=== HEALTH CHECK SUMMARY ==="
    log_with_timestamp "INFO" "Overall Health Score: $health_score/$max_score ($health_percentage%)"
    
    if [[ $health_percentage -ge 90 ]]; then
        log_with_timestamp "SUCCESS" "Status: EXCELLENT ${HEART}"
        return 0
    elif [[ $health_percentage -ge 75 ]]; then
        log_with_timestamp "SUCCESS" "Status: GOOD"
        return 0
    elif [[ $health_percentage -ge 50 ]]; then
        log_with_timestamp "WARNING" "Status: DEGRADED"
        return 1
    else
        log_with_timestamp "CRITICAL" "Status: CRITICAL - IMMEDIATE ATTENTION REQUIRED"
        return 2
    fi
}

continuous_monitoring() {
    local duration=${1:-3600}  # Default 1 hour
    local interval=${2:-60}    # Default 60 seconds
    
    log_with_timestamp "INFO" "Starting continuous monitoring for ${duration}s (interval: ${interval}s)"
    
    local start_time=$(date +%s)
    local end_time=$((start_time + duration))
    local check_count=0
    local success_count=0
    local warning_count=0
    local critical_count=0
    
    while [[ $(date +%s) -lt $end_time ]]; do
        check_count=$((check_count + 1))
        log_with_timestamp "INFO" "=== Health Check #$check_count ==="
        
        if check_deployment_health; then
            case $? in
                0) success_count=$((success_count + 1)) ;;
                1) warning_count=$((warning_count + 1)) ;;
                2) critical_count=$((critical_count + 1)) ;;
            esac
        else
            critical_count=$((critical_count + 1))
        fi
        
        # If too many critical failures, suggest rollback
        if [[ $critical_count -gt 0 && $check_count -ge 3 ]]; then
            local failure_rate=$((critical_count * 100 / check_count))
            if [[ $failure_rate -gt 50 ]]; then
                log_with_timestamp "CRITICAL" "High failure rate detected: $failure_rate%"
                log_with_timestamp "CRITICAL" "Consider rolling back deployment!"
                
                read -p "Do you want to initiate rollback? (y/n): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    initiate_rollback
                    return
                fi
            fi
        fi
        
        sleep $interval
    done
    
    # Final summary
    log_with_timestamp "INFO" "=== MONITORING SUMMARY ==="
    log_with_timestamp "INFO" "Total checks: $check_count"
    log_with_timestamp "INFO" "Successful: $success_count"
    log_with_timestamp "INFO" "Warnings: $warning_count"
    log_with_timestamp "INFO" "Critical: $critical_count"
    
    local success_rate=$((success_count * 100 / check_count))
    log_with_timestamp "INFO" "Success rate: $success_rate%"
}

get_deployment_status() {
    log_with_timestamp "INFO" "Querying Akash deployment status..."
    
    if [[ -z "$AKASH_DSEQ" ]]; then
        log_with_timestamp "WARNING" "AKASH_DSEQ not set, cannot query deployment status"
        return
    fi
    
    # Query deployment status
    local deployment_status=$(akash query deployment get \
        --owner "$AKASH_FROM" \
        --node "$AKASH_NODE" \
        --chain-id "$AKASH_CHAIN_ID" \
        --dseq "$AKASH_DSEQ" \
        --output json 2>/dev/null || echo "{}")
    
    if echo "$deployment_status" | jq -e '.deployment.state == 1' &> /dev/null; then
        log_with_timestamp "SUCCESS" "Deployment state: ACTIVE"
    else
        local state=$(echo "$deployment_status" | jq -r '.deployment.state // "unknown"')
        log_with_timestamp "WARNING" "Deployment state: $state"
    fi
    
    # Query lease status
    if [[ -n "$AKASH_PROVIDER" ]]; then
        local lease_status=$(akash query market lease get \
            --owner "$AKASH_FROM" \
            --node "$AKASH_NODE" \
            --chain-id "$AKASH_CHAIN_ID" \
            --dseq "$AKASH_DSEQ" \
            --gseq "$AKASH_GSEQ" \
            --oseq "$AKASH_OSEQ" \
            --provider "$AKASH_PROVIDER" \
            --output json 2>/dev/null || echo "{}")
        
        if echo "$lease_status" | jq -e '.lease.state == 1' &> /dev/null; then
            log_with_timestamp "SUCCESS" "Lease state: ACTIVE"
        else
            local lease_state=$(echo "$lease_status" | jq -r '.lease.state // "unknown"')
            log_with_timestamp "WARNING" "Lease state: $lease_state"
        fi
    fi
}

initiate_rollback() {
    log_with_timestamp "CRITICAL" "Initiating deployment rollback..."
    
    # Check if we have GitHub CLI for automated rollback
    if command -v gh &> /dev/null && gh auth status &> /dev/null; then
        log_with_timestamp "INFO" "Attempting automated rollback via GitHub Actions..."
        
        # Trigger rollback workflow
        if gh workflow run "OMEGA PRO AI - Akash CI/CD Pipeline" --field rollback=true; then
            log_with_timestamp "SUCCESS" "Rollback workflow triggered"
            
            # Monitor rollback progress
            log_with_timestamp "INFO" "Monitoring rollback progress..."
            gh run watch
        else
            log_with_timestamp "ERROR" "Failed to trigger rollback workflow"
            manual_rollback_instructions
        fi
    else
        manual_rollback_instructions
    fi
}

manual_rollback_instructions() {
    echo -e "${YELLOW}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                      🔄 MANUAL ROLLBACK INSTRUCTIONS                        ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    log_with_timestamp "INFO" "Manual rollback options:"
    log_with_timestamp "INFO" "1. Revert to previous Docker image:"
    echo "   docker pull omegaproai/omega-pro-ai:<previous-tag>"
    echo "   # Update deployment manifest and redeploy"
    
    log_with_timestamp "INFO" "2. Revert git commit and redeploy:"
    echo "   git revert HEAD"
    echo "   git push origin main"
    
    log_with_timestamp "INFO" "3. Emergency deployment closure:"
    echo "   akash tx deployment close --dseq $AKASH_DSEQ --from $AKASH_FROM"
    
    log_with_timestamp "INFO" "4. Check GitHub Actions and manually retry"
}

show_logs() {
    local lines=${1:-50}
    
    echo -e "${CYAN}${BOLD}=== RECENT MONITORING LOGS (last $lines lines) ===${NC}"
    if [[ -f "$LOG_FILE" ]]; then
        tail -n "$lines" "$LOG_FILE"
    else
        log_with_timestamp "WARNING" "No log file found"
    fi
}

show_help() {
    cat << EOF
${CHART} OMEGA PRO AI - Deployment Monitor

Usage: $0 [command] [options]

Commands:
  health              Perform single health check
  monitor [duration]  Continuous monitoring (default: 1 hour)
  status              Show Akash deployment status
  rollback            Initiate deployment rollback
  logs [lines]        Show recent logs (default: 50 lines)
  help                Show this help message

Options:
  --interval N        Monitoring interval in seconds (default: 60)
  --duration N        Monitoring duration in seconds (default: 3600)
  --json              Output health check in JSON format
  --quiet             Suppress non-essential output

Examples:
  $0 health                    # Single health check
  $0 monitor 1800             # Monitor for 30 minutes
  $0 monitor --interval 30    # Monitor with 30s intervals
  $0 status                   # Show deployment status
  $0 logs 100                 # Show last 100 log entries

Environment Variables (from .env):
  AKASH_URI          Deployment URL for health checks
  AKASH_DSEQ         Deployment sequence for status queries
  AKASH_PROVIDER     Provider address for detailed status
EOF
}

main() {
    print_header
    load_environment
    
    case "${1:-health}" in
        "health")
            check_deployment_health
            ;;
        "monitor")
            local duration=${2:-3600}
            local interval=${INTERVAL:-60}
            continuous_monitoring "$duration" "$interval"
            ;;
        "status")
            get_deployment_status
            ;;
        "rollback")
            initiate_rollback
            ;;
        "logs")
            show_logs "${2:-50}"
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_with_timestamp "ERROR" "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --quiet)
            QUIET=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

main "$@"