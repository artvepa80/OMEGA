#!/bin/bash
# 🧪 OMEGA PRO AI v10.1 - Complete Pipeline Testing Script
# Validates the entire CI/CD pipeline from local to Akash deployment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_LOG="$PROJECT_DIR/logs/pipeline-test.log"

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
TEST="🧪"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TEST_RESULTS=()

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
        TEST) echo -e "${PURPLE}${TEST}${NC} ${WHITE}$message${NC}" ;;
    esac
    
    mkdir -p "$(dirname "$TEST_LOG")"
    echo "[$timestamp] [$level] $message" >> "$TEST_LOG"
}

# Test function wrapper
run_test() {
    local test_name="$1"
    local test_function="$2"
    local is_critical="${3:-false}"
    
    log TEST "Running test: $test_name"
    
    if $test_function; then
        ((TESTS_PASSED++))
        TEST_RESULTS+=("✅ $test_name: PASSED")
        log SUCCESS "$test_name: PASSED"
        return 0
    else
        ((TESTS_FAILED++))
        TEST_RESULTS+=("❌ $test_name: FAILED")
        log ERROR "$test_name: FAILED"
        
        if [ "$is_critical" = "true" ]; then
            log ERROR "Critical test failed. Stopping pipeline test."
            display_test_results
            exit 1
        fi
        return 1
    fi
}

# Test 1: Environment and prerequisites
test_environment() {
    local required_commands=("python3" "docker" "git" "curl" "jq")
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log ERROR "Required command not found: $cmd"
            return 1
        fi
    done
    
    # Check Python version
    local python_version=$(python3 --version | awk '{print $2}')
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
        log ERROR "Python 3.10+ required, found: $python_version"
        return 1
    fi
    
    # Check if .env.example exists
    if [ ! -f "$PROJECT_DIR/.env.example" ]; then
        log ERROR ".env.example file not found"
        return 1
    fi
    
    return 0
}

# Test 2: Python code quality and syntax
test_code_quality() {
    cd "$PROJECT_DIR"
    
    # Check for syntax errors in main Python files
    local python_files=("main.py" "api_server.py")
    
    for file in "${python_files[@]}"; do
        if [ -f "$file" ]; then
            if ! python3 -m py_compile "$file"; then
                log ERROR "Syntax error in $file"
                return 1
            fi
        fi
    done
    
    # Check core modules
    if [ -d "core" ]; then
        find core -name "*.py" -exec python3 -m py_compile {} \; || return 1
    fi
    
    # Check modules directory
    if [ -d "modules" ]; then
        find modules -name "*.py" -exec python3 -m py_compile {} \; 2>/dev/null || true
    fi
    
    return 0
}

# Test 3: Docker build
test_docker_build() {
    cd "$PROJECT_DIR"
    
    log GEAR "Testing Docker build..."
    
    # Build the production Docker image
    if ! docker build -f Dockerfile.production -t omega-ai-test . >> "$TEST_LOG" 2>&1; then
        log ERROR "Docker build failed"
        return 1
    fi
    
    # Test if the container can start
    local container_id=$(docker run -d -p 8001:8000 omega-ai-test)
    sleep 10
    
    # Check if container is running
    if ! docker ps | grep -q "$container_id"; then
        docker logs "$container_id" >> "$TEST_LOG" 2>&1
        docker rm -f "$container_id" >/dev/null 2>&1 || true
        log ERROR "Docker container failed to start"
        return 1
    fi
    
    # Cleanup
    docker rm -f "$container_id" >/dev/null 2>&1 || true
    docker rmi omega-ai-test >/dev/null 2>&1 || true
    
    return 0
}

# Test 4: API endpoints (if running)
test_api_endpoints() {
    local test_url="${1:-http://localhost:8000}"
    
    # Test health endpoint
    if ! curl -f -s --max-time 10 "$test_url/health" > /dev/null; then
        log WARNING "Health endpoint not accessible at $test_url/health"
        return 1
    fi
    
    # Test root endpoint
    if ! curl -f -s --max-time 10 "$test_url/" > /dev/null; then
        log WARNING "Root endpoint not accessible at $test_url/"
        return 1
    fi
    
    return 0
}

# Test 5: Akash deployment configuration
test_akash_config() {
    # Check if Akash CLI is available
    if ! command -v akash &> /dev/null; then
        log WARNING "Akash CLI not found - deployment tests will be skipped"
        return 1
    fi
    
    # Check environment variables
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
    fi
    
    local required_vars=("AKASH_NODE" "AKASH_CHAIN_ID")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            log WARNING "Required Akash environment variable not set: $var"
            return 1
        fi
    done
    
    # Test Akash connectivity
    if ! akash status >> "$TEST_LOG" 2>&1; then
        log WARNING "Cannot connect to Akash network"
        return 1
    fi
    
    return 0
}

# Test 6: GitHub Actions workflow syntax
test_github_actions() {
    local workflow_file="$PROJECT_DIR/.github/workflows/cicd-pipeline.yml"
    
    if [ ! -f "$workflow_file" ]; then
        log ERROR "GitHub Actions workflow file not found"
        return 1
    fi
    
    # Basic YAML syntax check
    if ! python3 -c "import yaml; yaml.safe_load(open('$workflow_file'))" 2>/dev/null; then
        log ERROR "GitHub Actions workflow has invalid YAML syntax"
        return 1
    fi
    
    return 0
}

# Test 7: Security configuration
test_security_config() {
    # Check .gitignore
    if [ ! -f "$PROJECT_DIR/.gitignore" ]; then
        log ERROR ".gitignore file not found"
        return 1
    fi
    
    # Check that sensitive files are ignored
    local sensitive_patterns=(".env" "*.key" "*.pem" "secrets.json")
    for pattern in "${sensitive_patterns[@]}"; do
        if ! grep -q "$pattern" "$PROJECT_DIR/.gitignore"; then
            log WARNING "Sensitive pattern '$pattern' not found in .gitignore"
        fi
    done
    
    # Check for accidentally committed secrets
    if [ -f "$PROJECT_DIR/.env" ]; then
        if git ls-files --error-unmatch "$PROJECT_DIR/.env" &>/dev/null; then
            log ERROR ".env file is tracked by git - this is a security risk!"
            return 1
        fi
    fi
    
    return 0
}

# Test 8: Deployment scripts
test_deployment_scripts() {
    local scripts=("deploy-to-akash.sh" "monitor-akash.sh" "omega-dev-setup.sh")
    
    for script in "${scripts[@]}"; do
        local script_path="$PROJECT_DIR/scripts/$script"
        
        if [ ! -f "$script_path" ]; then
            log ERROR "Deployment script not found: $script"
            return 1
        fi
        
        if [ ! -x "$script_path" ]; then
            log ERROR "Deployment script not executable: $script"
            return 1
        fi
        
        # Basic syntax check for bash scripts
        if ! bash -n "$script_path"; then
            log ERROR "Syntax error in deployment script: $script"
            return 1
        fi
    done
    
    return 0
}

# Test 9: Live Akash deployment (if configured)
test_live_deployment() {
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
    fi
    
    local akash_url="${AKASH_URL:-https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win}"
    
    log GEAR "Testing live Akash deployment at: $akash_url"
    
    # Test health endpoint
    if ! curl -f -s --max-time 30 "$akash_url/health" | jq -e '.status == "healthy"' &>/dev/null; then
        log WARNING "Live deployment health check failed"
        return 1
    fi
    
    # Test API functionality
    if ! curl -f -s --max-time 30 "$akash_url/" | jq -e '.system == "OMEGA PRO AI"' &>/dev/null; then
        log WARNING "Live deployment API check failed"
        return 1
    fi
    
    return 0
}

# Test 10: End-to-end pipeline simulation
test_e2e_pipeline() {
    log GEAR "Simulating end-to-end pipeline..."
    
    # Simulate code changes
    local test_branch="test-pipeline-$(date +%s)"
    
    cd "$PROJECT_DIR"
    
    # Create a test branch
    if ! git checkout -b "$test_branch" >> "$TEST_LOG" 2>&1; then
        log ERROR "Failed to create test branch"
        return 1
    fi
    
    # Make a trivial change
    echo "# Pipeline test $(date)" >> README.md
    
    # Test git operations
    if ! git add README.md >> "$TEST_LOG" 2>&1; then
        log ERROR "Failed to stage changes"
        git checkout main >/dev/null 2>&1 || true
        git branch -D "$test_branch" >/dev/null 2>&1 || true
        return 1
    fi
    
    if ! git commit -m "Test pipeline commit" >> "$TEST_LOG" 2>&1; then
        log ERROR "Failed to commit changes"
        git checkout main >/dev/null 2>&1 || true
        git branch -D "$test_branch" >/dev/null 2>&1 || true
        return 1
    fi
    
    # Cleanup
    git checkout main >/dev/null 2>&1 || true
    git branch -D "$test_branch" >/dev/null 2>&1 || true
    
    # Reset README.md
    git checkout HEAD~1 -- README.md >/dev/null 2>&1 || true
    
    return 0
}

# Display test results
display_test_results() {
    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    local success_rate=0
    
    if [ $total_tests -gt 0 ]; then
        success_rate=$(( (TESTS_PASSED * 100) / total_tests ))
    fi
    
    echo
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}                    ${WHITE}🧪 OMEGA PRO AI - Pipeline Test Results${NC}                    ${PURPLE}║${NC}"
    echo -e "${PURPLE}╠══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}📊 Total Tests:${NC}      ${WHITE}$total_tests${NC}"
    echo -e "${PURPLE}║${NC} ${GREEN}✅ Passed:${NC}          ${WHITE}$TESTS_PASSED${NC}"
    echo -e "${PURPLE}║${NC} ${RED}❌ Failed:${NC}          ${WHITE}$TESTS_FAILED${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}📈 Success Rate:${NC}    ${WHITE}$success_rate%${NC}"
    echo -e "${PURPLE}╠══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}📋 Test Results:${NC}"
    
    for result in "${TEST_RESULTS[@]}"; do
        echo -e "${PURPLE}║${NC}   $result"
    done
    
    echo -e "${PURPLE}╠══════════════════════════════════════════════════════════════════════════════╣${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${PURPLE}║${NC} ${GREEN}🎉 All tests passed! Pipeline is ready for production.${NC}"
        echo -e "${PURPLE}║${NC} ${GREEN}✅ Your OMEGA PRO AI deployment pipeline is fully operational.${NC}"
    else
        echo -e "${PURPLE}║${NC} ${YELLOW}⚠️ Some tests failed. Please review and fix issues before deploying.${NC}"
        echo -e "${PURPLE}║${NC} ${YELLOW}📝 Check the log file: $TEST_LOG${NC}"
    fi
    
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Main test execution
main() {
    echo -e "${PURPLE}${ROCKET}${NC} ${WHITE}OMEGA PRO AI v10.1 - Complete Pipeline Testing${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
    
    log INFO "Starting complete pipeline test suite..."
    log INFO "Test log: $TEST_LOG"
    
    # Run all tests
    run_test "Environment and Prerequisites" test_environment true
    run_test "Python Code Quality and Syntax" test_code_quality true
    run_test "Docker Build Process" test_docker_build false
    run_test "GitHub Actions Workflow Syntax" test_github_actions false
    run_test "Security Configuration" test_security_config false
    run_test "Deployment Scripts" test_deployment_scripts false
    run_test "Akash Network Configuration" test_akash_config false
    run_test "Live Deployment Health Check" test_live_deployment false
    run_test "End-to-End Pipeline Simulation" test_e2e_pipeline false
    
    # Display results
    display_test_results
    
    # Return appropriate exit code
    if [ $TESTS_FAILED -eq 0 ]; then
        log SUCCESS "All critical tests passed! 🎉"
        return 0
    else
        log ERROR "Some tests failed. Please review and fix issues."
        return 1
    fi
}

# Execute main function
main "$@"