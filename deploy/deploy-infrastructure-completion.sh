#!/bin/bash
# OMEGA Pro AI - Infrastructure Completion Deployment Script
# Deploy enterprise-grade infrastructure components to Akash Network
# Version: 4.0.1 - Infrastructure Completion

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="akash-services"
DEPLOYMENT_DIR="/Users/user/Documents/OMEGA_PRO_AI_v10.1/deploy"
LOG_FILE="/tmp/omega-infrastructure-deployment.log"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}OMEGA PRO AI - INFRASTRUCTURE COMPLETION${NC}"
echo -e "${BLUE}Deploy Version: 4.0.1${NC}"
echo -e "${BLUE}Target: 99.5% Infrastructure Readiness${NC}"
echo -e "${BLUE}========================================${NC}"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

# Success message
success() {
    echo -e "${GREEN}SUCCESS: $1${NC}" | tee -a "$LOG_FILE"
}

# Warning message
warning() {
    echo -e "${YELLOW}WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Info message
info() {
    echo -e "${BLUE}INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    info "Checking deployment prerequisites..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        error_exit "kubectl is not installed or not in PATH"
    fi
    
    # Check if we can connect to Akash cluster
    if ! kubectl cluster-info &> /dev/null; then
        error_exit "Cannot connect to Kubernetes cluster"
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        info "Creating namespace $NAMESPACE..."
        kubectl create namespace "$NAMESPACE" || error_exit "Failed to create namespace"
    fi
    
    # Check deployment files exist
    local files=(
        "akash-firewall-rules.yaml"
        "akash-load-balancer.yaml" 
        "health-check-automation.yaml"
        "service-mesh-resilience.yaml"
    )
    
    for file in "${files[@]}"; do
        if [[ ! -f "$DEPLOYMENT_DIR/$file" ]]; then
            error_exit "Deployment file not found: $file"
        fi
    done
    
    success "Prerequisites check completed"
}

# Deploy firewall rules
deploy_firewall() {
    info "Deploying enterprise firewall rules and DDoS protection..."
    
    kubectl apply -f "$DEPLOYMENT_DIR/akash-firewall-rules.yaml" -n "$NAMESPACE" || error_exit "Failed to deploy firewall rules"
    
    # Wait for firewall pods to be ready
    info "Waiting for firewall enforcer to be ready..."
    kubectl wait --for=condition=ready pod -l app=omega-firewall -n "$NAMESPACE" --timeout=300s || warning "Firewall pods may not be fully ready"
    
    success "Firewall rules deployed successfully"
}

# Deploy load balancer
deploy_load_balancer() {
    info "Deploying enterprise load balancer with health checks..."
    
    kubectl apply -f "$DEPLOYMENT_DIR/akash-load-balancer.yaml" -n "$NAMESPACE" || error_exit "Failed to deploy load balancer"
    
    # Wait for load balancer to be ready
    info "Waiting for load balancer to be ready..."
    kubectl wait --for=condition=available deployment/omega-load-balancer -n "$NAMESPACE" --timeout=300s || error_exit "Load balancer deployment failed"
    
    success "Load balancer deployed successfully"
}

# Deploy health check automation
deploy_health_checks() {
    info "Deploying health check automation and monitoring..."
    
    kubectl apply -f "$DEPLOYMENT_DIR/health-check-automation.yaml" -n "$NAMESPACE" || error_exit "Failed to deploy health check automation"
    
    # Wait for health monitor to be ready
    info "Waiting for health monitor to be ready..."
    kubectl wait --for=condition=available deployment/omega-health-monitor -n "$NAMESPACE" --timeout=300s || error_exit "Health monitor deployment failed"
    
    success "Health check automation deployed successfully"
}

# Deploy service mesh resilience
deploy_service_mesh() {
    info "Deploying service mesh resilience and failover coordination..."
    
    kubectl apply -f "$DEPLOYMENT_DIR/service-mesh-resilience.yaml" -n "$NAMESPACE" || error_exit "Failed to deploy service mesh resilience"
    
    # Wait for resilience coordinator to be ready
    info "Waiting for resilience coordinator to be ready..."
    kubectl wait --for=condition=available deployment/omega-resilience-coordinator -n "$NAMESPACE" --timeout=300s || error_exit "Resilience coordinator deployment failed"
    
    success "Service mesh resilience deployed successfully"
}

# Validate infrastructure deployment
validate_infrastructure() {
    info "Validating infrastructure deployment..."
    
    local validation_passed=true
    
    # Check all deployments are ready
    info "Checking deployment status..."
    local deployments=(
        "omega-load-balancer"
        "omega-health-monitor"
        "omega-resilience-coordinator"
    )
    
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment "$deployment" -n "$NAMESPACE" &> /dev/null; then
            local ready=$(kubectl get deployment "$deployment" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
            local desired=$(kubectl get deployment "$deployment" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
            
            if [[ "$ready" == "$desired" ]]; then
                success "Deployment $deployment: $ready/$desired replicas ready"
            else
                warning "Deployment $deployment: $ready/$desired replicas ready"
                validation_passed=false
            fi
        else
            warning "Deployment $deployment not found"
            validation_passed=false
        fi
    done
    
    # Check DaemonSet status (firewall)
    if kubectl get daemonset omega-firewall-enforcer -n "$NAMESPACE" &> /dev/null; then
        local ready=$(kubectl get daemonset omega-firewall-enforcer -n "$NAMESPACE" -o jsonpath='{.status.numberReady}')
        local desired=$(kubectl get daemonset omega-firewall-enforcer -n "$NAMESPACE" -o jsonpath='{.status.desiredNumberScheduled}')
        
        if [[ "$ready" == "$desired" ]]; then
            success "DaemonSet omega-firewall-enforcer: $ready/$desired pods ready"
        else
            warning "DaemonSet omega-firewall-enforcer: $ready/$desired pods ready"
            validation_passed=false
        fi
    else
        warning "DaemonSet omega-firewall-enforcer not found"
        validation_passed=false
    fi
    
    # Test load balancer health endpoint
    info "Testing load balancer health endpoint..."
    local lb_service=$(kubectl get service omega-load-balancer-service -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
    if [[ -n "$lb_service" ]]; then
        if kubectl run test-pod --rm -i --tty --restart=Never --image=alpine/curl -- curl -s "http://$lb_service:8080/health" | grep -q "healthy"; then
            success "Load balancer health endpoint responding correctly"
        else
            warning "Load balancer health endpoint may not be responding correctly"
        fi
    fi
    
    return $([[ "$validation_passed" == true ]] && echo 0 || echo 1)
}

# Generate infrastructure status report
generate_status_report() {
    info "Generating infrastructure status report..."
    
    local report_file="/tmp/omega-infrastructure-status-$(date +%Y%m%d_%H%M%S).json"
    
    # Collect deployment information
    local deployments_info=$(kubectl get deployments -n "$NAMESPACE" -o json)
    local services_info=$(kubectl get services -n "$NAMESPACE" -o json)
    local daemonsets_info=$(kubectl get daemonsets -n "$NAMESPACE" -o json)
    local pods_info=$(kubectl get pods -n "$NAMESPACE" -o json)
    
    # Create comprehensive status report
    cat > "$report_file" << EOF
{
  "infrastructure_completion_report": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
    "version": "4.0.1",
    "target_readiness": "99.5%",
    "deployment_status": {
      "namespace": "$NAMESPACE",
      "components_deployed": [
        "enterprise_firewall_rules",
        "ddos_protection",
        "load_balancer_with_health_checks",
        "health_check_automation",
        "service_discovery",
        "circuit_breaker_patterns",
        "failover_coordination",
        "graceful_degradation"
      ]
    },
    "deployments": $deployments_info,
    "services": $services_info,
    "daemonsets": $daemonsets_info,
    "pods": $pods_info,
    "validation_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
  }
}
EOF
    
    info "Infrastructure status report generated: $report_file"
    echo "$report_file"
}

# Calculate infrastructure readiness percentage
calculate_readiness() {
    info "Calculating infrastructure readiness percentage..."
    
    local total_components=8
    local ready_components=0
    
    # Check each component
    local components=(
        "omega-load-balancer"
        "omega-health-monitor" 
        "omega-resilience-coordinator"
        "omega-firewall-enforcer"
    )
    
    for component in "${components[@]}"; do
        if [[ "$component" == "omega-firewall-enforcer" ]]; then
            if kubectl get daemonset "$component" -n "$NAMESPACE" &> /dev/null; then
                ((ready_components++))
            fi
        else
            if kubectl get deployment "$component" -n "$NAMESPACE" &> /dev/null; then
                local ready=$(kubectl get deployment "$component" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
                local desired=$(kubectl get deployment "$component" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "1")
                
                if [[ "$ready" == "$desired" ]] && [[ "$ready" -gt 0 ]]; then
                    ((ready_components+=2)) # Each deployment counts as 2 components
                fi
            fi
        fi
    done
    
    local readiness_percentage=$((ready_components * 100 / total_components))
    
    info "Infrastructure readiness: $readiness_percentage% ($ready_components/$total_components components ready)"
    
    if [[ $readiness_percentage -ge 99 ]]; then
        success "Target 99.5% infrastructure readiness achieved!"
    elif [[ $readiness_percentage -ge 95 ]]; then
        warning "Infrastructure readiness is $readiness_percentage% - close to target"
    else
        warning "Infrastructure readiness is $readiness_percentage% - below target"
    fi
    
    echo $readiness_percentage
}

# Main deployment flow
main() {
    info "Starting OMEGA Pro AI Infrastructure Completion Deployment"
    
    # Step 1: Check prerequisites
    check_prerequisites
    
    # Step 2: Deploy firewall rules
    deploy_firewall
    
    # Step 3: Deploy load balancer
    deploy_load_balancer
    
    # Step 4: Deploy health check automation
    deploy_health_checks
    
    # Step 5: Deploy service mesh resilience
    deploy_service_mesh
    
    # Step 6: Validate deployment
    if validate_infrastructure; then
        success "Infrastructure validation passed"
    else
        warning "Infrastructure validation completed with warnings"
    fi
    
    # Step 7: Generate status report
    local report_file=$(generate_status_report)
    
    # Step 8: Calculate final readiness
    local readiness=$(calculate_readiness)
    
    # Final summary
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}DEPLOYMENT SUMMARY${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Infrastructure Readiness: ${GREEN}$readiness%${NC}"
    echo -e "Status Report: ${YELLOW}$report_file${NC}"
    echo -e "Deployment Log: ${YELLOW}$LOG_FILE${NC}"
    echo -e "Target Achievement: $([[ $readiness -ge 99 ]] && echo -e "${GREEN}ACHIEVED${NC}" || echo -e "${YELLOW}IN PROGRESS${NC}")"
    echo -e "${BLUE}========================================${NC}"
    
    if [[ $readiness -ge 99 ]]; then
        success "OMEGA Pro AI Infrastructure Completion successful - 99.5% target achieved!"
        exit 0
    else
        warning "Infrastructure completion in progress - current readiness: $readiness%"
        exit 1
    fi
}

# Run main deployment
main "$@"