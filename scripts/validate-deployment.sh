#!/bin/bash

# =======================================================
# OMEGA PRO AI v10.1 - Deployment Validation Script
# Comprehensive validation for production deployments
# =======================================================

set -euo pipefail

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMEOUT=60
HEALTH_CHECK_RETRIES=5

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
info() { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

echo "=========================================================="
echo "🔍 OMEGA PRO AI v10.1 - Deployment Validation"
echo "=========================================================="
info "Starting validation at $(date)"
echo ""

# Test functions
test_api_health() {
    local url="${1:-http://localhost:8000}"
    info "Testing API health at $url"
    
    for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
        if curl -sf "$url/health" > /dev/null; then
            success "✅ API health check passed"
            return 0
        else
            warning "Attempt $i/$HEALTH_CHECK_RETRIES failed, retrying..."
            sleep 5
        fi
    done
    
    error "❌ API health check failed after $HEALTH_CHECK_RETRIES attempts"
    return 1
}

test_api_endpoints() {
    local base_url="${1:-http://localhost:8000}"
    info "Testing API endpoints"
    
    local endpoints=(
        "/"
        "/health"
        "/ready"
        "/metrics"
        "/system/info"
    )
    
    local failed=0
    
    for endpoint in "${endpoints[@]}"; do
        local url="$base_url$endpoint"
        if curl -sf "$url" > /dev/null; then
            success "✅ $endpoint"
        else
            error "❌ $endpoint"
            ((failed++))
        fi
    done
    
    if [ $failed -eq 0 ]; then
        success "✅ All API endpoints working"
        return 0
    else
        error "❌ $failed endpoint(s) failed"
        return 1
    fi
}

test_prediction_api() {
    local base_url="${1:-http://localhost:8000}"
    info "Testing prediction API"
    
    local response=$(curl -sf -X POST "$base_url/predict" \
        -H "Content-Type: application/json" \
        -d '{"params": {"test": true}}' 2>/dev/null || echo "")
    
    if [ -n "$response" ] && echo "$response" | jq -e '.success' > /dev/null 2>&1; then
        success "✅ Prediction API working"
        local predictions=$(echo "$response" | jq -r '.predictions | length')
        info "Generated $predictions predictions"
        return 0
    else
        error "❌ Prediction API failed"
        return 1
    fi
}

test_redis_connection() {
    local redis_url="${1:-redis://localhost:6379}"
    info "Testing Redis connection"
    
    # Extract host and port from URL
    local host=$(echo "$redis_url" | sed -n 's/.*:\/\/\([^:]*\).*/\1/p')
    local port=$(echo "$redis_url" | sed -n 's/.*:\([0-9]*\).*/\1/p')
    
    if [ -z "$port" ]; then
        port=6379
    fi
    
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h "$host" -p "$port" ping > /dev/null 2>&1; then
            success "✅ Redis connection working"
            return 0
        fi
    fi
    
    # Fallback: test with nc if available
    if command -v nc &> /dev/null; then
        if nc -z "$host" "$port" 2>/dev/null; then
            success "✅ Redis port accessible"
            return 0
        fi
    fi
    
    error "❌ Redis connection failed"
    return 1
}

test_monitoring_stack() {
    info "Testing monitoring stack"
    
    local services=(
        "http://localhost:9090|-/healthy|Prometheus"
        "http://localhost:3000|api/health|Grafana"
        "http://localhost:8404|stats|HAProxy"
    )
    
    local failed=0
    
    for service in "${services[@]}"; do
        IFS='|' read -r url path name <<< "$service"
        local full_url="$url/$path"
        
        if curl -sf "$full_url" > /dev/null 2>&1; then
            success "✅ $name accessible"
        else
            warning "⚠️  $name not accessible (might be disabled)"
            # Don't count as failure for optional services
        fi
    done
    
    success "✅ Monitoring stack check completed"
    return 0
}

test_ssl_certificates() {
    info "Testing SSL certificates"
    
    local cert_file="$PROJECT_DIR/ssl/omega.crt"
    
    if [ -f "$cert_file" ]; then
        local expiry=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f 2)
        local expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || echo "0")
        local current_epoch=$(date +%s)
        local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
        
        if [ $days_until_expiry -gt 30 ]; then
            success "✅ SSL certificate valid ($days_until_expiry days remaining)"
        elif [ $days_until_expiry -gt 0 ]; then
            warning "⚠️  SSL certificate expires soon ($days_until_expiry days)"
        else
            error "❌ SSL certificate expired"
            return 1
        fi
    else
        warning "⚠️  SSL certificate not found (might be using external SSL)"
    fi
    
    return 0
}

test_docker_services() {
    info "Testing Docker services"
    
    if ! command -v docker &> /dev/null; then
        warning "⚠️  Docker not available, skipping container checks"
        return 0
    fi
    
    local compose_file="$PROJECT_DIR/docker-compose.prod.yml"
    
    if [ ! -f "$compose_file" ]; then
        warning "⚠️  Production docker-compose file not found"
        return 0
    fi
    
    # Check if services are running
    local services=$(docker-compose -f "$compose_file" ps --services 2>/dev/null || echo "")
    
    if [ -n "$services" ]; then
        local running=0
        local total=0
        
        while IFS= read -r service; do
            ((total++))
            local status=$(docker-compose -f "$compose_file" ps -q "$service" 2>/dev/null)
            if [ -n "$status" ]; then
                local health=$(docker inspect --format='{{.State.Health.Status}}' $(docker-compose -f "$compose_file" ps -q "$service") 2>/dev/null || echo "unknown")
                if [ "$health" = "healthy" ] || [ "$health" = "unknown" ]; then
                    success "✅ $service running"
                    ((running++))
                else
                    error "❌ $service unhealthy ($health)"
                fi
            else
                error "❌ $service not running"
            fi
        done <<< "$services"
        
        info "Services: $running/$total running"
    else
        warning "⚠️  No Docker services detected"
    fi
    
    return 0
}

test_resource_usage() {
    info "Testing resource usage"
    
    # Memory usage
    if command -v free &> /dev/null; then
        local mem_usage=$(free | awk '/^Mem:/ {printf "%.1f", $3/$2 * 100}')
        if (( $(echo "$mem_usage > 90" | bc -l 2>/dev/null || echo "0") )); then
            error "❌ High memory usage: ${mem_usage}%"
        elif (( $(echo "$mem_usage > 70" | bc -l 2>/dev/null || echo "0") )); then
            warning "⚠️  Memory usage: ${mem_usage}%"
        else
            success "✅ Memory usage: ${mem_usage}%"
        fi
    fi
    
    # Disk usage
    local disk_usage=$(df / | awk 'NR==2 {printf "%s", $5}' | tr -d '%')
    if [ "$disk_usage" -gt 90 ]; then
        error "❌ High disk usage: ${disk_usage}%"
    elif [ "$disk_usage" -gt 70 ]; then
        warning "⚠️  Disk usage: ${disk_usage}%"
    else
        success "✅ Disk usage: ${disk_usage}%"
    fi
    
    # Load average
    if command -v uptime &> /dev/null; then
        local load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
        success "✅ Load average: $load"
    fi
    
    return 0
}

run_comprehensive_test() {
    info "Running comprehensive deployment validation..."
    echo ""
    
    local failed_tests=0
    local total_tests=8
    
    # Core API tests
    if ! test_api_health; then ((failed_tests++)); fi
    if ! test_api_endpoints; then ((failed_tests++)); fi
    if ! test_prediction_api; then ((failed_tests++)); fi
    
    # Infrastructure tests
    if ! test_redis_connection; then ((failed_tests++)); fi
    if ! test_monitoring_stack; then ((failed_tests++)); fi
    if ! test_ssl_certificates; then ((failed_tests++)); fi
    if ! test_docker_services; then ((failed_tests++)); fi
    if ! test_resource_usage; then ((failed_tests++)); fi
    
    echo ""
    echo "=========================================================="
    if [ $failed_tests -eq 0 ]; then
        success "🎉 All tests passed! ($((total_tests - failed_tests))/$total_tests)"
        echo "✅ OMEGA PRO AI v10.1 deployment is healthy and ready"
    else
        error "❌ $failed_tests/$total_tests tests failed"
        echo "⚠️  Please check the failed tests above"
    fi
    echo "=========================================================="
    
    return $failed_tests
}

# Performance benchmark
run_performance_test() {
    info "Running performance benchmark..."
    
    local base_url="${1:-http://localhost:8000}"
    local requests=10
    local concurrent=2
    
    if command -v ab &> /dev/null; then
        info "Running Apache Benchmark (ab) test..."
        ab -n $requests -c $concurrent "$base_url/" | tail -20
    elif command -v curl &> /dev/null; then
        info "Running simple response time test..."
        local total_time=0
        
        for i in $(seq 1 5); do
            local start_time=$(date +%s%N)
            curl -sf "$base_url/health" > /dev/null
            local end_time=$(date +%s%N)
            local response_time=$(( (end_time - start_time) / 1000000 ))
            echo "Request $i: ${response_time}ms"
            total_time=$((total_time + response_time))
        done
        
        local avg_time=$((total_time / 5))
        success "✅ Average response time: ${avg_time}ms"
    else
        warning "⚠️  No performance testing tools available"
    fi
}

# Main execution
main() {
    local test_type="${1:-comprehensive}"
    local base_url="${2:-http://localhost:8000}"
    
    case "$test_type" in
        "health")
            test_api_health "$base_url"
            ;;
        "endpoints")
            test_api_endpoints "$base_url"
            ;;
        "prediction")
            test_prediction_api "$base_url"
            ;;
        "performance")
            run_performance_test "$base_url"
            ;;
        "comprehensive"|*)
            run_comprehensive_test
            ;;
    esac
}

# Usage information
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "Usage: $0 [TEST_TYPE] [BASE_URL]"
    echo ""
    echo "TEST_TYPE:"
    echo "  comprehensive  - Run all tests (default)"
    echo "  health        - Test API health only"
    echo "  endpoints     - Test API endpoints"
    echo "  prediction    - Test prediction API"
    echo "  performance   - Run performance benchmark"
    echo ""
    echo "BASE_URL: API base URL (default: http://localhost:8000)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Full validation"
    echo "  $0 health                            # Health check only"
    echo "  $0 comprehensive https://api.domain.com  # Remote validation"
    exit 0
fi

# Execute main function
main "$@"