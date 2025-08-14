#!/bin/bash
# 🚀 OMEGA PRO AI - CI/CD Setup Script
# Automates the complete setup process for automatic deployment

set -e

# Colors and emojis
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ROCKET="🚀"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
EXAMPLE_ENV="$PROJECT_ROOT/.env.example"

print_banner() {
    echo -e "${CYAN}${BOLD}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🚀 OMEGA PRO AI CI/CD SETUP                              ║
║                   Automatic Deployment to Akash Network                     ║
║                                                                              ║
║   This script will set up complete CI/CD automation for OMEGA PRO AI        ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

log() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

log_success() {
    echo -e "${GREEN}${CHECK}${NC} $1"
}

log_error() {
    echo -e "${RED}${CROSS}${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}${WARNING}${NC} $1"
}

log_info() {
    echo -e "${PURPLE}${INFO}${NC} $1"
}

step_1_prerequisites() {
    echo -e "${CYAN}${BOLD}STEP 1: Prerequisites Check${NC}"
    echo "Checking required tools and accounts..."
    echo

    # Check OS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This setup is optimized for macOS"
        log_info "For other systems, use: ./scripts/deploy-to-akash.sh"
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found"
        echo "Please install Docker Desktop:"
        echo "1. Download from: https://www.docker.com/products/docker-desktop"
        echo "2. Install and start Docker Desktop"
        echo "3. Run this script again"
        echo
        read -p "Press Enter when Docker is installed..."
        
        # Recheck
        if ! command -v docker &> /dev/null; then
            log_error "Docker still not found. Please install Docker Desktop first."
            exit 1
        fi
    fi

    # Check Docker running
    if ! docker info &> /dev/null; then
        log_warning "Docker is not running"
        log_info "Starting Docker Desktop..."
        open -a Docker
        echo "Waiting for Docker to start..."
        sleep 15
        
        if ! docker info &> /dev/null; then
            log_error "Docker is still not running. Please start Docker Desktop manually."
            exit 1
        fi
    fi

    log_success "Docker is running"

    # Check git
    if ! command -v git &> /dev/null; then
        log_error "Git not found. Please install Git first."
        exit 1
    fi

    log_success "Git is available"

    # Check if in git repository
    if ! git rev-parse --git-dir &> /dev/null; then
        log_error "Not in a Git repository"
        exit 1
    fi

    log_success "In Git repository"

    # Check GitHub remote
    if ! git remote get-url origin &> /dev/null; then
        log_error "No GitHub remote found"
        exit 1
    fi

    local github_url=$(git remote get-url origin)
    log_success "GitHub remote: $github_url"

    echo
    log_success "Prerequisites check passed"
    echo
}

step_2_accounts() {
    echo -e "${CYAN}${BOLD}STEP 2: Account Setup${NC}"
    echo "Setting up required accounts and credentials..."
    echo

    echo "Required accounts:"
    echo "1. ${BOLD}Docker Hub${NC} - Container registry"
    echo "   Sign up: https://hub.docker.com"
    echo "   Create access token: Settings → Security → New Access Token"
    echo
    echo "2. ${BOLD}Akash Network${NC} - Deployment platform" 
    echo "   Install wallet: https://akash.network/docs/getting-started/install/"
    echo "   Fund wallet with AKT tokens"
    echo
    echo "3. ${BOLD}GitHub${NC} - Already configured ✅"
    echo "   Repository: $(git remote get-url origin)"
    echo

    read -p "Do you have Docker Hub and Akash accounts ready? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please set up the required accounts and run this script again."
        echo
        echo "Setup guides:"
        echo "- Docker Hub: https://docs.docker.com/docker-hub/quickstart/"
        echo "- Akash Network: https://akash.network/docs/getting-started/"
        exit 0
    fi

    log_success "Accounts confirmed"
    echo
}

step_3_environment() {
    echo -e "${CYAN}${BOLD}STEP 3: Environment Configuration${NC}"
    echo "Setting up environment variables..."
    echo

    # Create .env from example if needed
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "$EXAMPLE_ENV" ]]; then
            cp "$EXAMPLE_ENV" "$ENV_FILE"
            log_success ".env file created from template"
        else
            log_error ".env.example not found"
            exit 1
        fi
    else
        log_info ".env file already exists"
    fi

    echo "Please fill in your credentials in the .env file:"
    echo
    echo "Required variables:"
    echo "- DOCKERHUB_USERNAME: Your Docker Hub username"
    echo "- DOCKERHUB_TOKEN: Your Docker Hub access token"
    echo "- AKASH_FROM: Your Akash wallet key name"
    echo
    echo "Optional (for existing deployments):"
    echo "- AKASH_DSEQ, AKASH_GSEQ, AKASH_OSEQ, AKASH_PROVIDER, AKASH_URI"
    echo

    # Open .env file for editing
    if command -v code &> /dev/null; then
        echo "Opening .env file in VS Code..."
        code "$ENV_FILE"
    else
        echo "Edit the .env file manually:"
        echo "nano $ENV_FILE"
    fi

    echo
    read -p "Press Enter when you've finished editing .env..."

    # Validate environment
    if [[ -f "$ENV_FILE" ]]; then
        source "$ENV_FILE"
        
        local missing=()
        [[ -z "$DOCKERHUB_USERNAME" || "$DOCKERHUB_USERNAME" == "your_dockerhub_username" ]] && missing+=("DOCKERHUB_USERNAME")
        [[ -z "$DOCKERHUB_TOKEN" || "$DOCKERHUB_TOKEN" == "your_dockerhub_access_token" ]] && missing+=("DOCKERHUB_TOKEN")
        [[ -z "$AKASH_FROM" || "$AKASH_FROM" == "your_akash_key_name" ]] && missing+=("AKASH_FROM")

        if [[ ${#missing[@]} -gt 0 ]]; then
            log_error "Missing required variables: ${missing[*]}"
            echo "Please edit .env file and fill in the required values"
            exit 1
        fi

        log_success "Environment configuration validated"
    else
        log_error ".env file not found"
        exit 1
    fi

    echo
}

step_4_github_secrets() {
    echo -e "${CYAN}${BOLD}STEP 4: GitHub Secrets Configuration${NC}"
    echo "Setting up GitHub repository secrets for CI/CD..."
    echo

    local github_url=$(git remote get-url origin)
    local repo_path=$(echo "$github_url" | sed 's/.*github.com[\/:]//g' | sed 's/.git$//')
    local secrets_url="https://github.com/${repo_path}/settings/secrets/actions"

    echo "You need to add these secrets to your GitHub repository:"
    echo "URL: $secrets_url"
    echo

    echo "Required secrets:"
    echo "1. DOCKERHUB_USERNAME = $DOCKERHUB_USERNAME"
    echo "2. DOCKERHUB_TOKEN = [your Docker Hub access token]"
    echo "3. AKASH_KEY_SECRET = [base64 encoded Akash wallet key]"
    echo "4. AKASH_NODE = https://rpc.akashnet.net:443"
    echo "5. AKASH_CHAIN_ID = akashnet-2"
    echo

    if [[ -n "$AKASH_DSEQ" ]]; then
        echo "Optional secrets (for existing deployment):"
        echo "6. AKASH_DSEQ = $AKASH_DSEQ"
        echo "7. AKASH_GSEQ = $AKASH_GSEQ"
        echo "8. AKASH_OSEQ = $AKASH_OSEQ"
        echo "9. AKASH_PROVIDER = $AKASH_PROVIDER"
        echo "10. AKASH_URI = $AKASH_URI"
        echo
    fi

    echo "To get your base64 encoded Akash key:"
    echo "akash keys export $AKASH_FROM --keyring-backend test | base64"
    echo

    # Open GitHub secrets page
    if command -v open &> /dev/null; then
        echo "Opening GitHub secrets page..."
        open "$secrets_url"
    fi

    echo
    read -p "Press Enter when you've added the GitHub secrets..."

    log_success "GitHub secrets configuration completed"
    echo
}

step_5_test_setup() {
    echo -e "${CYAN}${BOLD}STEP 5: Testing Setup${NC}"
    echo "Testing the complete CI/CD pipeline..."
    echo

    # Test local Docker build
    echo "Testing local Docker build..."
    if docker build -f Dockerfile.cicd -t omega-cicd-test . &> /dev/null; then
        log_success "Local Docker build successful"
        docker rmi omega-cicd-test &> /dev/null || true
    else
        log_error "Local Docker build failed"
        echo "Check the Dockerfile.cicd and requirements.txt"
        exit 1
    fi

    # Test GitHub connectivity
    echo "Testing GitHub connectivity..."
    if git ls-remote origin &> /dev/null; then
        log_success "GitHub connectivity confirmed"
    else
        log_error "GitHub connectivity failed"
        exit 1
    fi

    # Test deployment script
    echo "Testing deployment script..."
    if [[ -x "$PROJECT_ROOT/scripts/omega-deploy-mac.sh" ]]; then
        if "$PROJECT_ROOT/scripts/omega-deploy-mac.sh" --check &> /dev/null; then
            log_success "Deployment script test passed"
        else
            log_warning "Deployment script check failed (may need environment setup)"
        fi
    else
        log_error "Deployment script not found or not executable"
        exit 1
    fi

    echo
    log_success "Setup testing completed"
    echo
}

step_6_first_deployment() {
    echo -e "${CYAN}${BOLD}STEP 6: First Deployment${NC}"
    echo "Ready to perform your first automated deployment!"
    echo

    echo "This will:"
    echo "1. Commit any pending changes"
    echo "2. Push to GitHub"
    echo "3. Trigger GitHub Actions CI/CD"
    echo "4. Build and push Docker image"
    echo "5. Deploy to Akash Network"
    echo "6. Run health checks"
    echo

    read -p "Perform first deployment now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting first deployment..."
        
        # Add setup completion marker
        echo "# CI/CD Setup completed on $(date)" >> "$PROJECT_ROOT/CICD_SETUP_COMPLETE.md"
        
        # Run deployment
        if "$PROJECT_ROOT/scripts/omega-deploy-mac.sh"; then
            log_success "First deployment completed successfully!"
        else
            log_error "First deployment failed"
            echo "Check the logs and try again"
            exit 1
        fi
    else
        echo "Skipping first deployment."
        echo "You can deploy later with:"
        echo "./scripts/omega-deploy-mac.sh"
    fi

    echo
}

show_completion() {
    echo -e "${GREEN}${BOLD}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                        🎉 SETUP COMPLETE! 🎉                               ║
║                                                                              ║
║   Your OMEGA PRO AI CI/CD pipeline is now ready!                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    echo "What you can do now:"
    echo
    echo "${BOLD}Deploy changes:${NC}"
    echo "  ./scripts/omega-deploy-mac.sh"
    echo
    echo "${BOLD}Monitor deployment:${NC}"
    echo "  ./scripts/omega-monitor.sh health"
    echo "  ./scripts/omega-monitor.sh monitor"
    echo
    echo "${BOLD}Check status:${NC}"
    echo "  ./scripts/omega-deploy-mac.sh --check"
    echo "  ./scripts/omega-monitor.sh status"
    echo
    echo "${BOLD}View documentation:${NC}"
    echo "  cat OMEGA_CICD_DEPLOYMENT_GUIDE.md"
    echo
    echo "GitHub Actions URL:"
    local github_url=$(git remote get-url origin)
    local repo_path=$(echo "$github_url" | sed 's/.*github.com[\/:]//g' | sed 's/.git$//')
    echo "  https://github.com/${repo_path}/actions"
    echo

    if [[ -n "$AKASH_URI" ]]; then
        echo "Your OMEGA API:"
        echo "  $AKASH_URI"
        echo
    fi

    echo "${BOLD}Next steps:${NC}"
    echo "1. Make changes to your code"
    echo "2. Run: ./scripts/omega-deploy-mac.sh"
    echo "3. Your changes will automatically deploy to Akash!"
    echo
    
    log_success "OMEGA PRO AI CI/CD setup is complete and ready to use!"
}

main() {
    print_banner
    
    step_1_prerequisites
    step_2_accounts
    step_3_environment
    step_4_github_secrets
    step_5_test_setup
    step_6_first_deployment
    
    show_completion
}

# Handle arguments
case "${1:-}" in
    --help|-h)
        echo "OMEGA PRO AI CI/CD Setup Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "This script sets up complete CI/CD automation for OMEGA PRO AI"
        echo "deployment from Mac to Akash Network via GitHub Actions."
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo ""
        echo "What this script does:"
        echo "1. Checks prerequisites (Docker, Git, etc.)"
        echo "2. Guides through account setup"
        echo "3. Configures environment variables"
        echo "4. Sets up GitHub repository secrets"
        echo "5. Tests the complete pipeline"
        echo "6. Performs first deployment"
        echo ""
        echo "After setup, you can deploy changes with:"
        echo "  ./scripts/omega-deploy-mac.sh"
        exit 0
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