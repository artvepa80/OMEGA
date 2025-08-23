#!/bin/bash
# 🚀 OMEGA PRO AI - Mac Deployment Automation
# Simplified deployment script for Mac users
# Automatically syncs local changes to Akash via GitHub Actions

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
EXAMPLE_ENV="$PROJECT_ROOT/.env.example"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Emoji for Mac terminal
ROCKET="🚀"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"
PACKAGE="📦"
CLOUD="☁️"
TIMER="⏱"

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                   ${ROCKET} OMEGA PRO AI - Mac Deploy Tool                        ║"
    echo "║                        Auto-Sync to Akash Network                           ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

log_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
}

log_info() {
    echo -e "${PURPLE}${INFO} $1${NC}"
}

log_step() {
    echo -e "${CYAN}${GEAR} $1${NC}"
}

check_mac_prerequisites() {
    log_step "Checking Mac prerequisites..."
    
    # Check if running on macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This script is designed for macOS. Use deploy-to-akash.sh for other systems."
        exit 1
    fi
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        log_warning "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Check and install git
    if ! command -v git &> /dev/null; then
        log_warning "Git not found. Installing via Homebrew..."
        brew install git
    fi
    
    # Check and install Docker Desktop
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found. Please install Docker Desktop:"
        log_info "1. Download from: https://www.docker.com/products/docker-desktop"
        log_info "2. Install and start Docker Desktop"
        log_info "3. Run this script again"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker Desktop is not running. Please start Docker Desktop and try again."
        open -a Docker
        log_info "Waiting for Docker Desktop to start..."
        sleep 10
        exit 1
    fi
    
    # Check and install GitHub CLI (optional but helpful)
    if ! command -v gh &> /dev/null; then
        log_info "GitHub CLI not found. Installing for better GitHub integration..."
        brew install gh
    fi
    
    log_success "Mac prerequisites check completed"
}

setup_environment() {
    log_step "Setting up environment configuration..."
    
    # Create .env file from example if it doesn't exist
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "$EXAMPLE_ENV" ]]; then
            log_info "Creating .env from example..."
            cp "$EXAMPLE_ENV" "$ENV_FILE"
        else
            log_info "Creating new .env file..."
            create_env_file
        fi
        
        log_warning "Please edit .env file with your credentials:"
        log_info "Open with: code .env  (VS Code) or nano .env"
        
        if command -v code &> /dev/null; then
            read -p "Open .env in VS Code now? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                code "$ENV_FILE"
                read -p "Press Enter when you've finished editing .env..."
            fi
        fi
    fi
    
    # Source environment file
    source "$ENV_FILE"
    
    # Validate required variables
    validate_environment
    
    log_success "Environment setup completed"
}

create_env_file() {
    cat > "$ENV_FILE" << 'EOF'
# 🚀 OMEGA PRO AI - Environment Configuration
# Edit these values with your actual credentials

# Docker Hub Configuration (Required)
DOCKERHUB_USERNAME=your_dockerhub_username
DOCKERHUB_TOKEN=your_dockerhub_token

# Akash Network Configuration (Required)
AKASH_KEYRING_BACKEND=test
AKASH_FROM=your_akash_key_name
AKASH_NODE=https://rpc.akashnet.net:443
AKASH_CHAIN_ID=akashnet-2

# Existing Deployment Info (Optional - leave empty for new deployment)
AKASH_DSEQ=
AKASH_GSEQ=
AKASH_OSEQ=
AKASH_PROVIDER=
AKASH_URI=

# GitHub Configuration (Optional - for advanced features)
GITHUB_TOKEN=your_github_token
EOF
}

validate_environment() {
    local missing_vars=()
    
    # Required variables
    [[ -z "$DOCKERHUB_USERNAME" || "$DOCKERHUB_USERNAME" == "your_dockerhub_username" ]] && missing_vars+=("DOCKERHUB_USERNAME")
    [[ -z "$DOCKERHUB_TOKEN" || "$DOCKERHUB_TOKEN" == "your_dockerhub_token" ]] && missing_vars+=("DOCKERHUB_TOKEN")
    [[ -z "$AKASH_FROM" || "$AKASH_FROM" == "your_akash_key_name" ]] && missing_vars+=("AKASH_FROM")
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables:"
        printf "${RED}  - %s${NC}\n" "${missing_vars[@]}"
        log_info "Please edit .env file with your actual credentials"
        exit 1
    fi
}

check_git_status() {
    log_step "Checking git repository status..."
    
    # Check if in git repository
    if ! git rev-parse --git-dir &> /dev/null; then
        log_error "Not in a git repository"
        exit 1
    fi
    
    # Check if there are uncommitted changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
        log_info "Found uncommitted changes"
        git status --short
        
        echo
        read -p "Do you want to commit these changes? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            commit_changes
        else
            log_warning "Deploying with uncommitted changes"
        fi
    fi
    
    # Check if ahead of remote
    local ahead=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "0")
    if [[ $ahead -gt 0 ]]; then
        log_info "Local branch is $ahead commits ahead of remote"
        push_changes
    fi
    
    log_success "Git status check completed"
}

commit_changes() {
    log_step "Committing changes..."
    
    # Add all changes
    git add .
    
    # Get current timestamp
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Create commit message
    local commit_msg="Update OMEGA v10.1 - $timestamp

${ROCKET} Mac deployment sync
- Local changes committed for deployment
- Timestamp: $timestamp
- Auto-sync to Akash Network

${GEAR} Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    # Commit
    git commit -m "$commit_msg"
    
    log_success "Changes committed"
}

push_changes() {
    log_step "Pushing changes to GitHub..."
    
    # Get current branch
    local current_branch=$(git branch --show-current)
    
    # Push to remote
    git push origin "$current_branch"
    
    log_success "Changes pushed to GitHub"
    log_info "GitHub Actions will now trigger automatic deployment"
}

build_local_docker() {
    log_step "Building Docker image locally..."
    
    # Build Docker image for testing
    local image_tag="omega-local:$(date +%s)"
    
    docker build -f Dockerfile.cicd -t "$image_tag" .
    
    log_success "Docker image built: $image_tag"
    
    # Quick local test
    log_info "Testing image locally..."
    local container_id=$(docker run -d -p 8080:8000 "$image_tag")
    
    # Wait for container to start
    sleep 10
    
    # Test health endpoint
    if curl -f http://localhost:8080/health &> /dev/null; then
        log_success "Local Docker test passed"
    else
        log_warning "Local Docker test failed"
    fi
    
    # Cleanup
    docker stop "$container_id" &> /dev/null
    docker rm "$container_id" &> /dev/null
    
    # Clean up test image
    docker rmi "$image_tag" &> /dev/null
}

monitor_github_actions() {
    log_step "Monitoring GitHub Actions deployment..."
    
    # Check if GitHub CLI is available and authenticated
    if command -v gh &> /dev/null && gh auth status &> /dev/null; then
        log_info "Opening GitHub Actions in browser..."
        gh run list --limit 1
        gh run watch
    else
        log_info "GitHub CLI not available or not authenticated"
        log_info "Monitor deployment at: https://github.com/$(git remote get-url origin | sed 's/.*github.com[\/:]//g' | sed 's/.git$//')/actions"
    fi
}

wait_for_deployment() {
    log_step "Waiting for Akash deployment..."
    
    if [[ -n "$AKASH_URI" ]]; then
        log_info "Checking deployment at: $AKASH_URI"
        
        local max_attempts=20
        local attempt=1
        
        while [[ $attempt -le $max_attempts ]]; do
            log_info "Health check attempt $attempt/$max_attempts..."
            
            if curl -f "$AKASH_URI/health" &> /dev/null; then
                log_success "Deployment is healthy!"
                
                # Test prediction endpoint
                if curl -f -X POST "$AKASH_URI/predict" \
                    -H "Content-Type: application/json" \
                    -d '{"cantidad": 3, "perfil_svi": "default"}' &> /dev/null; then
                    log_success "Prediction endpoint is working!"
                else
                    log_warning "Prediction endpoint not responding"
                fi
                
                return 0
            fi
            
            sleep 30
            ((attempt++))
        done
        
        log_warning "Deployment health check timeout"
    else
        log_info "AKASH_URI not set in .env, skipping health check"
    fi
}

show_deployment_info() {
    echo
    echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║                        ${ROCKET} DEPLOYMENT SUMMARY                                ║${NC}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    
    log_success "OMEGA PRO AI v10.1 deployment initiated"
    
    if [[ -n "$AKASH_URI" ]]; then
        log_info "Akash Deployment: $AKASH_URI"
    fi
    
    log_info "GitHub Repository: $(git remote get-url origin)"
    log_info "GitHub Actions: https://github.com/$(git remote get-url origin | sed 's/.*github.com[\/:]//g' | sed 's/.git$//')/actions"
    
    echo
    echo -e "${CYAN}${BOLD}Next Steps:${NC}"
    echo -e "${BLUE}1.${NC} Monitor GitHub Actions for deployment progress"
    echo -e "${BLUE}2.${NC} Check Akash deployment health once completed"
    echo -e "${BLUE}3.${NC} Test the API endpoints"
    echo -e "${BLUE}4.${NC} Make more changes and run this script again to auto-deploy"
    echo
}

show_help() {
    cat << EOF
${ROCKET} OMEGA PRO AI - Mac Deploy Tool

Usage: $0 [options]

This tool automates the deployment of OMEGA PRO AI from your Mac to Akash Network
via GitHub Actions. It handles:
- Git commit and push
- Docker build and registry push  
- Akash deployment via GitHub Actions
- Health monitoring

Options:
  --help, -h         Show this help message
  --setup           Set up environment configuration only
  --check           Check prerequisites and configuration
  --local-test      Build and test Docker image locally only
  --monitor         Monitor existing GitHub Actions run
  --quick           Skip local Docker testing (faster)

Files created/used:
  .env              Environment configuration
  .env.example      Environment template
  
Required Setup:
1. Docker Hub account and access token
2. Akash Network wallet and key
3. GitHub repository access

For detailed setup instructions, see README.md
EOF
}

main() {
    print_header
    
    log_info "Starting Mac deployment automation..."
    
    # Check Mac prerequisites
    check_mac_prerequisites
    
    # Setup environment
    setup_environment
    
    # Check git status and commit/push if needed
    check_git_status
    
    # Build and test Docker locally (unless --quick)
    if [[ "${1:-}" != "--quick" ]]; then
        build_local_docker
    fi
    
    # Monitor GitHub Actions
    monitor_github_actions
    
    # Wait for deployment and health check
    wait_for_deployment
    
    # Show deployment summary
    show_deployment_info
    
    log_success "Deployment automation completed!"
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --setup)
        print_header
        setup_environment
        log_success "Environment setup completed. Edit .env file as needed."
        exit 0
        ;;
    --check)
        print_header
        check_mac_prerequisites
        setup_environment
        log_success "All checks passed. Ready for deployment."
        exit 0
        ;;
    --local-test)
        print_header
        check_mac_prerequisites
        setup_environment
        build_local_docker
        exit 0
        ;;
    --monitor)
        print_header
        monitor_github_actions
        exit 0
        ;;
    --quick)
        main --quick
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown option: $1"
        log_info "Use --help for usage information"
        exit 1
        ;;
esac
EOF