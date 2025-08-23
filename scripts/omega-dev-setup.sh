#!/bin/bash
# 🛠️ OMEGA PRO AI v10.1 - Development Environment Setup Script
# One-command setup for local development

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Emoji
ROCKET="🚀"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    
    case $level in
        INFO)  echo -e "${BLUE}${INFO}${NC} ${WHITE}$message${NC}" ;;
        SUCCESS) echo -e "${GREEN}${CHECK}${NC} ${WHITE}$message${NC}" ;;
        ERROR) echo -e "${RED}${CROSS}${NC} ${WHITE}$message${NC}" ;;
        WARNING) echo -e "${YELLOW}${WARNING}${NC} ${WHITE}$message${NC}" ;;
        GEAR) echo -e "${CYAN}${GEAR}${NC} ${WHITE}$message${NC}" ;;
    esac
}

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log ERROR "This script is optimized for macOS. For other platforms, please refer to the manual setup guide."
        exit 1
    fi
    log SUCCESS "macOS detected"
}

# Install Homebrew if not present
install_homebrew() {
    if ! command -v brew &> /dev/null; then
        log INFO "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        log SUCCESS "Homebrew installed successfully"
    else
        log SUCCESS "Homebrew already installed"
    fi
}

# Install required system dependencies
install_system_dependencies() {
    log INFO "Installing system dependencies with Homebrew..."
    
    # Update Homebrew
    brew update
    
    # Install required packages
    local packages=("python@3.11" "docker" "git" "curl" "jq" "node" "yarn")
    
    for package in "${packages[@]}"; do
        if brew list "$package" &> /dev/null; then
            log SUCCESS "$package already installed"
        else
            log GEAR "Installing $package..."
            brew install "$package"
        fi
    done
    
    # Install Docker Desktop if not running
    if ! docker info &> /dev/null; then
        log WARNING "Docker is not running. Please start Docker Desktop."
        open -a Docker
        log INFO "Waiting for Docker to start..."
        sleep 30
    fi
    
    log SUCCESS "System dependencies installed"
}

# Set up Python environment
setup_python_environment() {
    log INFO "Setting up Python environment..."
    
    cd "$PROJECT_DIR"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log GEAR "Creating Python virtual environment..."
        python3.11 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install Python dependencies
    log GEAR "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Install development dependencies
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    fi
    
    log SUCCESS "Python environment setup complete"
}

# Set up pre-commit hooks
setup_pre_commit_hooks() {
    log INFO "Setting up pre-commit hooks..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Install pre-commit
    pip install pre-commit
    
    # Create pre-commit configuration
    cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements
      - id: check-json

  - repo: https://github.com/psf/black
    rev: 22.12.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/PyCQA/bandit
    rev: '1.7.4'
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]
EOF

    # Install the git hook scripts
    pre-commit install
    
    log SUCCESS "Pre-commit hooks installed"
}

# Create development configuration
setup_dev_config() {
    log INFO "Setting up development configuration..."
    
    cd "$PROJECT_DIR"
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log SUCCESS "Created .env file from template"
        else
            cat > .env << EOF
# OMEGA PRO AI Development Configuration
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Akash Network Configuration (for deployment)
AKASH_NODE=https://rpc.akashnet.net:443
AKASH_CHAIN_ID=akashnet-2
AKASH_ACCOUNT_ADDRESS=your_akash_address_here
AKASH_DSEQ=your_deployment_sequence_here
AKASH_PROVIDER=your_provider_address_here

# Docker Configuration
DOCKER_REGISTRY=docker.io
DOCKER_IMAGE_NAME=omegaproai/omega-ai

# GitHub Configuration (for CI/CD)
GITHUB_TOKEN=your_github_token_here
DOCKERHUB_USERNAME=your_dockerhub_username
DOCKERHUB_TOKEN=your_dockerhub_token

# Optional: Slack notifications
SLACK_WEBHOOK=your_slack_webhook_url
EOF
            log SUCCESS "Created .env file with defaults"
            log WARNING "Please update .env file with your actual configuration values"
        fi
    else
        log SUCCESS ".env file already exists"
    fi
    
    # Create necessary directories
    local dirs=("data" "models" "results" "logs" "temp" "core" "modules")
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
    
    log SUCCESS "Development configuration complete"
}

# Install Akash CLI
install_akash_cli() {
    log INFO "Installing Akash CLI..."
    
    if command -v akash &> /dev/null; then
        log SUCCESS "Akash CLI already installed"
        akash version
        return
    fi
    
    # Download and install Akash CLI
    curl -sSfL https://raw.githubusercontent.com/akash-network/node/master/install.sh | sh
    
    # Move to a location in PATH
    if [ -d "./bin" ]; then
        sudo mv ./bin/akash /usr/local/bin/
        rm -rf ./bin
    fi
    
    # Verify installation
    if command -v akash &> /dev/null; then
        log SUCCESS "Akash CLI installed successfully"
        akash version
    else
        log ERROR "Failed to install Akash CLI"
        return 1
    fi
}

# Create development scripts
create_dev_scripts() {
    log INFO "Creating development helper scripts..."
    
    cd "$PROJECT_DIR"
    
    # Create local run script
    cat > run-local.sh << 'EOF'
#!/bin/bash
# Start OMEGA PRO AI locally

cd "$(dirname "$0")"
source venv/bin/activate

echo "🚀 Starting OMEGA PRO AI locally..."
python main.py --top_n=8 --svi_profile=default
EOF
    chmod +x run-local.sh
    
    # Create test script
    cat > run-tests.sh << 'EOF'
#!/bin/bash
# Run all tests

cd "$(dirname "$0")"
source venv/bin/activate

echo "🧪 Running tests..."
pytest tests/ -v --cov=. --cov-report=html
echo "📊 Coverage report generated in htmlcov/"
EOF
    chmod +x run-tests.sh
    
    # Create Docker development script
    cat > run-docker-dev.sh << 'EOF'
#!/bin/bash
# Run OMEGA PRO AI in Docker for development

cd "$(dirname "$0")"

echo "🐳 Building and running Docker container for development..."
docker build -f Dockerfile.production -t omega-ai-dev .
docker run --rm -it -p 8000:8000 -v "$(pwd)":/app/dev omega-ai-dev
EOF
    chmod +x run-docker-dev.sh
    
    log SUCCESS "Development scripts created"
}

# Display setup summary
display_setup_summary() {
    echo
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}              ${WHITE}🛠️ OMEGA PRO AI - Development Setup${NC}              ${PURPLE}║${NC}"
    echo -e "${PURPLE}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║${NC} ${GREEN}${CHECK}${NC} Python 3.11 virtual environment ready            ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC} ${GREEN}${CHECK}${NC} All dependencies installed                       ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC} ${GREEN}${CHECK}${NC} Pre-commit hooks configured                      ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC} ${GREEN}${CHECK}${NC} Development configuration created                ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC} ${GREEN}${CHECK}${NC} Akash CLI installed                             ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC} ${GREEN}${CHECK}${NC} Helper scripts ready                            ${PURPLE}║${NC}"
    echo -e "${PURPLE}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}Quick Start Commands:${NC}                               ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}   ${WHITE}./run-local.sh${NC}        - Run OMEGA PRO AI locally     ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}   ${WHITE}./run-tests.sh${NC}        - Run test suite               ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}   ${WHITE}./run-docker-dev.sh${NC}   - Run in Docker                ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}   ${WHITE}./scripts/deploy-to-akash.sh${NC} - Deploy to Akash       ${PURPLE}║${NC}"
    echo -e "${PURPLE}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║${NC} ${YELLOW}${WARNING}${NC} Remember to:                                     ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}   1. Update .env file with your configuration          ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}   2. Configure Akash wallet for deployments           ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}   3. Set up Docker Hub credentials for CI/CD          ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Main setup function
main() {
    echo -e "${PURPLE}${ROCKET}${NC} ${WHITE}OMEGA PRO AI v10.1 - Development Environment Setup${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    
    check_macos
    install_homebrew
    install_system_dependencies
    setup_python_environment
    setup_pre_commit_hooks
    setup_dev_config
    install_akash_cli
    create_dev_scripts
    
    display_setup_summary
    
    log SUCCESS "Development environment setup completed!"
    echo -e "${GREEN}${CHECK}${NC} ${WHITE}You're ready to develop and deploy OMEGA PRO AI!${NC}"
}

# Execute main function
main "$@"