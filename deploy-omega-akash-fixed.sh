#!/bin/bash

# OMEGA PRO AI v10.1 - Fixed Akash Network Deployment Script
# ==========================================================

set -euo pipefail

echo "🚀 OMEGA PRO AI v10.1 - Akash Network Deployment (Fixed)"
echo "========================================================"

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_FILE="deploy/omega-akash-working.yaml"
AKASH_CHAIN_ID="akashnet-2"
AKASH_NODE="https://rpc.akashnet.net:443"
AKASH_KEYRING_BACKEND="os"
AKASH_GAS_PRICES="0.025uakt"
AKASH_GAS_ADJUSTMENT="1.5"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Akash CLI
    if ! command -v akash >/dev/null 2>&1; then
        log_error "Akash CLI not found. Please install it first."
        echo "Install with: curl -sSf https://raw.githubusercontent.com/akash-network/node/master/install.sh | sh"
        exit 1
    fi
    
    log_success "Akash CLI found: $(akash version)"
    
    # Check deployment file
    if [ ! -f "$SCRIPT_DIR/$DEPLOYMENT_FILE" ]; then
        log_error "Deployment file not found: $DEPLOYMENT_FILE"
        exit 1
    fi
    
    log_success "Deployment file found: $DEPLOYMENT_FILE"
}

# Setup Akash environment
setup_akash_environment() {
    log_info "Setting up Akash environment..."
    
    export AKASH_NET="https://raw.githubusercontent.com/akash-network/net/main/mainnet"
    export AKASH_VERSION="0.38.4"
    export AKASH_CHAIN_ID="$AKASH_CHAIN_ID"
    export AKASH_NODE="$AKASH_NODE"
    export AKASH_KEYRING_BACKEND="$AKASH_KEYRING_BACKEND"
    export AKASH_GAS_PRICES="$AKASH_GAS_PRICES"
    export AKASH_GAS_ADJUSTMENT="$AKASH_GAS_ADJUSTMENT"
    
    log_success "Akash environment configured"
    log_info "  Chain ID: $AKASH_CHAIN_ID"
    log_info "  Node: $AKASH_NODE"
    log_info "  Gas Prices: $AKASH_GAS_PRICES"
}

# Check or create wallet
setup_wallet() {
    log_info "Setting up Akash wallet..."
    
    # Check if wallet exists
    WALLET_NAME="omega-deployer"
    
    if ! akash keys show "$WALLET_NAME" >/dev/null 2>&1; then
        log_warning "Wallet '$WALLET_NAME' not found. Creating new wallet..."
        
        # Create new wallet
        akash keys add "$WALLET_NAME" --keyring-backend "$AKASH_KEYRING_BACKEND"
        
        WALLET_ADDRESS=$(akash keys show "$WALLET_NAME" -a --keyring-backend "$AKASH_KEYRING_BACKEND")
        
        log_success "Wallet created: $WALLET_ADDRESS"
        log_warning "IMPORTANT: Please fund this wallet with at least 10 AKT tokens"
        log_warning "Fund at: https://faucet.akash.network/ or buy AKT tokens"
        
        echo -e "${YELLOW}"
        echo "=========================================="
        echo "WALLET FUNDING REQUIRED"
        echo "=========================================="
        echo "Address: $WALLET_ADDRESS"
        echo "Minimum: 10 AKT"
        echo "Faucet: https://faucet.akash.network/"
        echo "=========================================="
        echo -e "${NC}"
        
        read -p "Press Enter after funding the wallet to continue..."
    else
        WALLET_ADDRESS=$(akash keys show "$WALLET_NAME" -a --keyring-backend "$AKASH_KEYRING_BACKEND")
        log_success "Using existing wallet: $WALLET_ADDRESS"
    fi
    
    export AKASH_FROM="$WALLET_NAME"
}

# Check wallet balance
check_wallet_balance() {
    log_info "Checking wallet balance..."
    
    local balance_output
    balance_output=$(akash query bank balances "$WALLET_ADDRESS" \
        --chain-id "$AKASH_CHAIN_ID" \
        --node "$AKASH_NODE" 2>/dev/null || echo "")
    
    if [ -n "$balance_output" ]; then
        echo "$balance_output"
        
        # Extract AKT balance (basic parsing)
        local akt_balance
        akt_balance=$(echo "$balance_output" | grep -o '[0-9]*uakt' | head -1 | sed 's/uakt//' || echo "0")
        
        if [ "$akt_balance" -lt 5000000 ]; then  # 5 AKT minimum
            log_warning "Low AKT balance detected. Recommended minimum: 10 AKT"
            log_warning "Current balance: $((akt_balance / 1000000)) AKT"
        else
            log_success "Sufficient AKT balance: $((akt_balance / 1000000)) AKT"
        fi
    else
        log_warning "Could not retrieve balance. Proceeding with deployment..."
    fi
}

# Create deployment
create_deployment() {
    log_info "Creating Akash deployment..."
    
    local deployment_file="$SCRIPT_DIR/$DEPLOYMENT_FILE"
    
    # Validate deployment file
    log_info "Validating deployment configuration..."
    if ! grep -q "version:" "$deployment_file"; then
        log_error "Invalid deployment file format"
        exit 1
    fi
    
    log_success "Deployment file validated"
    
    # Create deployment
    log_info "Submitting deployment to Akash Network..."
    
    local tx_result
    tx_result=$(akash tx deployment create "$deployment_file" \
        --from "$AKASH_FROM" \
        --chain-id "$AKASH_CHAIN_ID" \
        --node "$AKASH_NODE" \
        --gas-prices "$AKASH_GAS_PRICES" \
        --gas-adjustment "$AKASH_GAS_ADJUSTMENT" \
        --keyring-backend "$AKASH_KEYRING_BACKEND" \
        --yes \
        --output json 2>/dev/null || echo "")
    
    if [ -n "$tx_result" ] && echo "$tx_result" | grep -q "txhash"; then
        local tx_hash
        tx_hash=$(echo "$tx_result" | grep -o '"txhash":"[^"]*"' | cut -d'"' -f4)
        
        log_success "Deployment transaction submitted!"
        log_info "Transaction Hash: $tx_hash"
        
        # Wait for transaction to be processed
        log_info "Waiting for transaction confirmation..."
        sleep 30
        
        # Try to extract DSEQ from events
        log_info "Retrieving deployment sequence..."
        
        # List deployments to find our deployment
        local deployments
        deployments=$(akash query deployment list \
            --owner "$WALLET_ADDRESS" \
            --chain-id "$AKASH_CHAIN_ID" \
            --node "$AKASH_NODE" 2>/dev/null || echo "")
        
        if [ -n "$deployments" ]; then
            log_success "Deployment created successfully!"
            echo "$deployments"
            
            # Wait for bids
            log_info "Waiting for provider bids (60 seconds)..."
            sleep 60
            
            check_bids
        else
            log_warning "Could not retrieve deployment information"
            log_info "Check your deployment manually with:"
            log_info "akash query deployment list --owner $WALLET_ADDRESS --chain-id $AKASH_CHAIN_ID --node $AKASH_NODE"
        fi
        
    else
        log_error "Deployment creation failed!"
        log_error "Response: $tx_result"
        
        log_info "Troubleshooting steps:"
        log_info "1. Check wallet balance (minimum 10 AKT)"
        log_info "2. Verify network connectivity"
        log_info "3. Check Akash network status"
        exit 1
    fi
}

# Check for bids
check_bids() {
    log_info "Checking for provider bids..."
    
    local bids_output
    bids_output=$(akash query market bid list \
        --owner "$WALLET_ADDRESS" \
        --chain-id "$AKASH_CHAIN_ID" \
        --node "$AKASH_NODE" 2>/dev/null || echo "")
    
    if [ -n "$bids_output" ] && echo "$bids_output" | grep -q "bids:"; then
        log_success "Bids received from providers!"
        echo "$bids_output"
        
        echo ""
        log_info "Next Steps:"
        log_info "1. Review the bids above"
        log_info "2. Select a provider and create a lease"
        log_info "3. Use the following commands:"
        echo ""
        echo -e "${CYAN}# List deployments${NC}"
        echo "akash query deployment list --owner $WALLET_ADDRESS --chain-id $AKASH_CHAIN_ID --node $AKASH_NODE"
        echo ""
        echo -e "${CYAN}# Create lease with selected provider${NC}"
        echo "akash tx market lease create --dseq <DSEQ> --provider <PROVIDER_ADDRESS> --from $AKASH_FROM --chain-id $AKASH_CHAIN_ID --node $AKASH_NODE --yes"
        echo ""
        echo -e "${CYAN}# Get lease status and URI${NC}"
        echo "akash query market lease get --dseq <DSEQ> --provider <PROVIDER_ADDRESS> --from $AKASH_FROM --chain-id $AKASH_CHAIN_ID --node $AKASH_NODE"
        
    else
        log_warning "No bids received yet"
        log_info "This may take a few minutes. You can check manually with:"
        log_info "akash query market bid list --owner $WALLET_ADDRESS --chain-id $AKASH_CHAIN_ID --node $AKASH_NODE"
    fi
}

# Show deployment status
show_deployment_status() {
    log_info "Deployment Status Summary:"
    echo ""
    echo -e "${GREEN}✅ Deployment Created Successfully${NC}"
    echo -e "${BLUE}📋 Wallet Address:${NC} $WALLET_ADDRESS"
    echo -e "${BLUE}🌐 Chain ID:${NC} $AKASH_CHAIN_ID"
    echo -e "${BLUE}🔗 Node:${NC} $AKASH_NODE"
    echo ""
    echo -e "${YELLOW}⏳ Waiting for provider selection and lease creation${NC}"
    echo ""
    echo -e "${PURPLE}📚 Useful Commands:${NC}"
    echo "• List deployments: akash query deployment list --owner $WALLET_ADDRESS --chain-id $AKASH_CHAIN_ID --node $AKASH_NODE"
    echo "• Check bids: akash query market bid list --owner $WALLET_ADDRESS --chain-id $AKASH_CHAIN_ID --node $AKASH_NODE"
    echo "• Monitor logs: akash logs --dseq <DSEQ> --provider <PROVIDER> --from $AKASH_FROM --chain-id $AKASH_CHAIN_ID --node $AKASH_NODE"
    echo ""
}

# Main execution
main() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                    🚀 OMEGA PRO AI v10.1                         ║"
    echo "║                 AKASH NETWORK DEPLOYMENT                         ║"
    echo "║                                                                  ║"
    echo "║  🌐 Decentralized Cloud Deployment                              ║"
    echo "║  🔧 AI-Powered Lottery Predictions                              ║"
    echo "║  📊 Real-time Processing                                        ║"
    echo "║  ⚡ High Performance Computing                                   ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Execute deployment steps
    check_prerequisites
    setup_akash_environment
    setup_wallet
    check_wallet_balance
    create_deployment
    show_deployment_status
    
    log_success "🎉 OMEGA PRO AI Akash deployment process completed!"
    log_info "Monitor the deployment progress and create a lease when ready."
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi