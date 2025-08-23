#!/bin/bash
# 📊 OMEGA PRO AI v10.1 - Akash Network Monitoring Script
# Continuous monitoring of Akash deployment with alerts

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MONITOR_LOG="$PROJECT_DIR/logs/akash-monitor.log"
STATUS_FILE="$PROJECT_DIR/.akash-status"

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
fi

# Default monitoring configuration
AKASH_URL="${AKASH_URL:-https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win}"
MONITOR_INTERVAL="${MONITOR_INTERVAL:-60}"  # seconds
ALERT_THRESHOLD="${ALERT_THRESHOLD:-3}"     # failed checks before alert
RESPONSE_TIME_THRESHOLD="${RESPONSE_TIME_THRESHOLD:-10}" # seconds

# Colors and emoji
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

ROCKET="🚀"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"
MONITOR="📊"
ALERT="🚨"
HEART="💚"

# Global state
CONSECUTIVE_FAILURES=0
LAST_ALERT_TIME=0
MONITORING_START_TIME=$(date +%s)

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
        MONITOR) echo -e "${PURPLE}${MONITOR}${NC} ${WHITE}$message${NC}" ;;
        ALERT) echo -e "${RED}${ALERT}${NC} ${WHITE}$message${NC}" ;;
        HEART) echo -e "${GREEN}${HEART}${NC} ${WHITE}$message${NC}" ;;
    esac
    
    mkdir -p "$(dirname "$MONITOR_LOG")"
    echo "[$timestamp] [$level] $message" >> "$MONITOR_LOG"
}

# Send Slack notification (if configured)
send_slack_alert() {
    local message="$1"
    local level="${2:-WARNING}"
    
    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        local color="warning"
        local emoji="⚠️"
        
        case $level in
            ERROR) color="danger"; emoji="🚨" ;;
            SUCCESS) color="good"; emoji="✅" ;;
        esac
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"$emoji OMEGA PRO AI - Akash Monitoring Alert\",
                    \"text\": \"$message\",
                    \"fields\": [
                        {\"title\": \"Deployment\", \"value\": \"$AKASH_URL\", \"short\": true},
                        {\"title\": \"DSEQ\", \"value\": \"${AKASH_DSEQ:-Unknown}\", \"short\": true},
                        {\"title\": \"Time\", \"value\": \"$(date)\", \"short\": false}
                    ]
                }]
            }" \
            "$SLACK_WEBHOOK" &>/dev/null || true
    fi
}

# Comprehensive health check
perform_health_check() {
    local health_url="$AKASH_URL/health"
    local api_url="$AKASH_URL/"
    local metrics_url="$AKASH_URL/metrics"
    
    # Initialize check results
    local health_status=0
    local api_status=0
    local metrics_status=0
    local response_time=0
    local health_body=""
    
    # Health endpoint check
    local start_time=$(date +%s.%3N)
    if health_body=$(curl -s -f --max-time 30 "$health_url" 2>/dev/null); then
        health_status=200
        local end_time=$(date +%s.%3N)
        response_time=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "0")
    else
        health_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$health_url" 2>/dev/null || echo "000")
    fi
    
    # API endpoint check
    api_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$api_url" 2>/dev/null || echo "000")
    
    # Metrics endpoint check
    metrics_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$metrics_url" 2>/dev/null || echo "000")
    
    # Analyze results
    local overall_healthy=true
    local issues=()
    
    if [ "$health_status" != "200" ]; then
        overall_healthy=false
        issues+=("Health endpoint failed (HTTP $health_status)")
    fi
    
    if [ "$api_status" != "200" ]; then
        overall_healthy=false
        issues+=("API endpoint failed (HTTP $api_status)")
    fi
    
    if [ "$metrics_status" != "200" ]; then
        issues+=("Metrics endpoint failed (HTTP $metrics_status)")
    fi
    
    # Check response time
    if (( $(echo "$response_time > $RESPONSE_TIME_THRESHOLD" | bc -l 2>/dev/null || echo "0") )); then
        issues+=("Slow response time (${response_time}s > ${RESPONSE_TIME_THRESHOLD}s)")
    fi
    
    # Update status file
    cat > "$STATUS_FILE" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "healthy": $overall_healthy,
    "checks": {
        "health_endpoint": {"status": $health_status, "healthy": $([ "$health_status" = "200" ] && echo "true" || echo "false")},
        "api_endpoint": {"status": $api_status, "healthy": $([ "$api_status" = "200" ] && echo "true" || echo "false")},
        "metrics_endpoint": {"status": $metrics_status, "healthy": $([ "$metrics_status" = "200" ] && echo "true" || echo "false")},
        "response_time": {"value": $response_time, "threshold": $RESPONSE_TIME_THRESHOLD, "healthy": $([ $(echo "$response_time <= $RESPONSE_TIME_THRESHOLD" | bc -l 2>/dev/null || echo "1") = "1" ] && echo "true" || echo "false")}
    },
    "issues": $(printf '%s\n' "${issues[@]}" | jq -R . | jq -s .)
}
EOF
    
    # Log results
    if [ "$overall_healthy" = true ]; then
        CONSECUTIVE_FAILURES=0
        log HEART "System healthy - Response time: ${response_time}s"
        
        # Parse health response if available
        if [ -n "$health_body" ]; then
            local status_from_body=$(echo "$health_body" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
            if [ "$status_from_body" = "healthy" ]; then
                log MONITOR "Service reports: $status_from_body"
            fi
        fi
    else
        ((CONSECUTIVE_FAILURES++))
        log ERROR "Health check failed (consecutive failures: $CONSECUTIVE_FAILURES)"
        
        for issue in "${issues[@]}"; do
            log WARNING "$issue"
        done
        
        # Send alert if threshold reached
        if [ $CONSECUTIVE_FAILURES -ge $ALERT_THRESHOLD ]; then
            local current_time=$(date +%s)
            local alert_cooldown=1800  # 30 minutes between alerts
            
            if [ $((current_time - LAST_ALERT_TIME)) -ge $alert_cooldown ]; then
                local alert_message="OMEGA PRO AI deployment is experiencing issues after $CONSECUTIVE_FAILURES consecutive failed health checks. Issues: $(IFS='; '; echo "${issues[*]}")"
                log ALERT "$alert_message"
                send_slack_alert "$alert_message" "ERROR"
                LAST_ALERT_TIME=$current_time
            fi
        fi
    fi
    
    return $([ "$overall_healthy" = true ] && echo 0 || echo 1)
}

# Get deployment statistics
get_deployment_stats() {
    if command -v akash &> /dev/null && [ -n "${AKASH_ACCOUNT_ADDRESS:-}" ]; then
        log GEAR "Fetching Akash deployment statistics..."
        
        # Get deployment info
        local deployment_info=""
        if deployment_info=$(akash query deployment get \
            --owner "$AKASH_ACCOUNT_ADDRESS" \
            --dseq "${AKASH_DSEQ:-}" \
            --output json 2>/dev/null); then
            
            local state=$(echo "$deployment_info" | jq -r '.deployment.state')
            local created_at=$(echo "$deployment_info" | jq -r '.deployment.created_at')
            
            log MONITOR "Akash deployment state: $state (created: $created_at)"
        fi
        
        # Get lease information
        if [ -n "${AKASH_PROVIDER:-}" ]; then
            local lease_info=""
            if lease_info=$(akash provider lease-status \
                --node "${AKASH_NODE:-}" \
                --owner "$AKASH_ACCOUNT_ADDRESS" \
                --dseq "${AKASH_DSEQ:-}" \
                --oseq 1 \
                --gseq 1 \
                --provider "$AKASH_PROVIDER" \
                --output json 2>/dev/null); then
                
                local services=$(echo "$lease_info" | jq -r '.services | keys[]' | wc -l)
                log MONITOR "Active services: $services"
            fi
        fi
    fi
}

# Display monitoring dashboard
display_dashboard() {
    clear
    local current_time=$(date)
    local uptime_seconds=$(($(date +%s) - MONITORING_START_TIME))
    local uptime_formatted=$(printf '%02d:%02d:%02d' $((uptime_seconds/3600)) $(((uptime_seconds%3600)/60)) $((uptime_seconds%60)))
    
    echo -e "${PURPLE}╔═══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}                      ${WHITE}📊 OMEGA PRO AI - Akash Network Monitor${NC}                      ${PURPLE}║${NC}"
    echo -e "${PURPLE}╠═══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}🌐 URL:${NC}           ${WHITE}$AKASH_URL${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}📊 DSEQ:${NC}          ${WHITE}${AKASH_DSEQ:-Unknown}${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}🏢 Provider:${NC}      ${WHITE}${AKASH_PROVIDER:-Unknown}${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}⏰ Current Time:${NC}  ${WHITE}$current_time${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}📈 Monitor Uptime:${NC} ${WHITE}$uptime_formatted${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}🔄 Check Interval:${NC} ${WHITE}${MONITOR_INTERVAL}s${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}❌ Consecutive Failures:${NC} ${WHITE}$CONSECUTIVE_FAILURES${NC}"
    echo -e "${PURPLE}╠═══════════════════════════════════════════════════════════════════════════════╣${NC}"
    
    if [ -f "$STATUS_FILE" ]; then
        local last_check=$(jq -r '.timestamp' "$STATUS_FILE" 2>/dev/null || echo "Unknown")
        local is_healthy=$(jq -r '.healthy' "$STATUS_FILE" 2>/dev/null || echo "false")
        local health_status=$(jq -r '.checks.health_endpoint.status' "$STATUS_FILE" 2>/dev/null || echo "unknown")
        local api_status=$(jq -r '.checks.api_endpoint.status' "$STATUS_FILE" 2>/dev/null || echo "unknown")
        local response_time=$(jq -r '.checks.response_time.value' "$STATUS_FILE" 2>/dev/null || echo "unknown")
        
        local status_emoji=$CROSS
        local status_color=$RED
        
        if [ "$is_healthy" = "true" ]; then
            status_emoji=$HEART
            status_color=$GREEN
        fi
        
        echo -e "${PURPLE}║${NC} ${CYAN}📋 Last Check:${NC}     ${WHITE}$last_check${NC}"
        echo -e "${PURPLE}║${NC} ${CYAN}💚 Overall Status:${NC}  ${status_color}$status_emoji $([ "$is_healthy" = "true" ] && echo "HEALTHY" || echo "UNHEALTHY")${NC}"
        echo -e "${PURPLE}║${NC} ${CYAN}🏥 Health Endpoint:${NC} ${WHITE}HTTP $health_status${NC}"
        echo -e "${PURPLE}║${NC} ${CYAN}🌐 API Endpoint:${NC}   ${WHITE}HTTP $api_status${NC}"
        echo -e "${PURPLE}║${NC} ${CYAN}⚡ Response Time:${NC}  ${WHITE}${response_time}s${NC}"
        
        # Show issues if any
        local issues_count=$(jq -r '.issues | length' "$STATUS_FILE" 2>/dev/null || echo "0")
        if [ "$issues_count" -gt 0 ]; then
            echo -e "${PURPLE}║${NC} ${RED}⚠️ Issues (${issues_count}):${NC}"
            jq -r '.issues[]' "$STATUS_FILE" 2>/dev/null | while IFS= read -r issue; do
                echo -e "${PURPLE}║${NC}   ${RED}• $issue${NC}"
            done
        fi
    else
        echo -e "${PURPLE}║${NC} ${YELLOW}⏳ Performing initial health check...${NC}"
    fi
    
    echo -e "${PURPLE}╠═══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}Press Ctrl+C to stop monitoring${NC}"
    echo -e "${PURPLE}╚═══════════════════════════════════════════════════════════════════════════════╝${NC}"
}

# Signal handler for graceful shutdown
cleanup() {
    log INFO "Monitoring stopped by user"
    echo -e "\n${GREEN}${CHECK}${NC} ${WHITE}Monitoring session ended${NC}"
    exit 0
}

# Main monitoring loop
main() {
    echo -e "${PURPLE}${ROCKET}${NC} ${WHITE}OMEGA PRO AI v10.1 - Akash Network Monitoring${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════${NC}"
    
    # Set up signal handling
    trap cleanup SIGINT SIGTERM
    
    # Create necessary directories
    mkdir -p "$(dirname "$MONITOR_LOG")"
    
    log INFO "Starting Akash Network monitoring..."
    log INFO "Monitoring URL: $AKASH_URL"
    log INFO "Check interval: ${MONITOR_INTERVAL}s"
    log INFO "Alert threshold: $ALERT_THRESHOLD consecutive failures"
    
    # Initial deployment stats
    get_deployment_stats
    
    # Main monitoring loop
    while true; do
        display_dashboard
        perform_health_check
        
        # Wait for next check
        sleep "$MONITOR_INTERVAL"
    done
}

# Execute main function
main "$@"