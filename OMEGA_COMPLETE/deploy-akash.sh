#!/bin/bash

# OMEGA Akash Network Deployment Script
set -e

echo "🚀 Deploying OMEGA to Akash Network..."

# Configuration
DEPLOYMENT_FILE="deploy/akash-deployment.yaml"
CERT_PATH="$HOME/.akash"
WALLET_NAME="omega-wallet"

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v akash &> /dev/null; then
    echo "❌ Akash CLI not found. Installing..."
    curl -sSfL https://raw.githubusercontent.com/akash-network/provider/main/install.sh | sh
    export PATH="$PATH:./bin"
fi

# Check wallet
if ! akash keys list | grep -q "$WALLET_NAME"; then
    echo "❌ Wallet '$WALLET_NAME' not found."
    echo "Please create wallet with: akash keys add $WALLET_NAME"
    exit 1
fi

# Get wallet address
AKASH_ACCOUNT_ADDRESS=$(akash keys show $WALLET_NAME -a)
echo "📍 Using wallet: $AKASH_ACCOUNT_ADDRESS"

# Check balance
BALANCE=$(akash query bank balances $AKASH_ACCOUNT_ADDRESS --node https://rpc.akash.forbole.com:443)
echo "💰 Account balance: $BALANCE"

# Create certificate if not exists
if [ ! -f "$CERT_PATH/cert.pem" ]; then
    echo "📜 Creating certificate..."
    akash tx cert create client --from $WALLET_NAME --node https://rpc.akash.forbole.com:443 --chain-id akashnet-2 --gas-prices 0.025uakt --gas auto --gas-adjustment 1.15
fi

# Build and push Docker image
echo "🏗️ Building Docker image..."
docker build -f Dockerfile.api -t omega-pro-ai:latest .

# Tag for registry (if using external registry)
# docker tag omega-pro-ai:latest ghcr.io/username/omega-pro-ai:latest
# docker push ghcr.io/username/omega-pro-ai:latest

# Validate deployment file
echo "✅ Validating deployment manifest..."
if [ ! -f "$DEPLOYMENT_FILE" ]; then
    echo "❌ Deployment file not found: $DEPLOYMENT_FILE"
    exit 1
fi

# Create deployment
echo "📋 Creating deployment..."
DEPLOYMENT_TX=$(akash tx deployment create $DEPLOYMENT_FILE \
    --from $WALLET_NAME \
    --node https://rpc.akash.forbole.com:443 \
    --chain-id akashnet-2 \
    --gas-prices 0.025uakt \
    --gas auto \
    --gas-adjustment 1.15 \
    --broadcast-mode block \
    -y)

echo "📦 Deployment transaction: $DEPLOYMENT_TX"

# Extract DSEQ
DSEQ=$(echo "$DEPLOYMENT_TX" | jq -r '.logs[0].events[] | select(.type=="akash.v1beta2.EventDeploymentCreated") | .attributes[] | select(.key=="dseq") | .value' | tr -d '"')

if [ -z "$DSEQ" ] || [ "$DSEQ" == "null" ]; then
    echo "❌ Failed to extract DSEQ from transaction"
    exit 1
fi

echo "🆔 Deployment Sequence (DSEQ): $DSEQ"

# Wait for bids
echo "⏳ Waiting for provider bids (30 seconds)..."
sleep 30

# Query bids
echo "📝 Querying available bids..."
BIDS=$(akash query market bid list --owner $AKASH_ACCOUNT_ADDRESS --dseq $DSEQ --node https://rpc.akash.forbole.com:443)

if echo "$BIDS" | grep -q "No bids found"; then
    echo "❌ No bids received. Please check:"
    echo "   - Deployment requirements are reasonable"
    echo "   - Account has sufficient balance"
    echo "   - Network connectivity"
    exit 1
fi

echo "📊 Available bids:"
echo "$BIDS"

# Select first available bid (you might want to make this interactive)
PROVIDER=$(echo "$BIDS" | jq -r '.bids[0].bid.bid_id.provider' 2>/dev/null || echo "")

if [ -z "$PROVIDER" ] || [ "$PROVIDER" == "null" ]; then
    echo "❌ No valid provider found in bids"
    exit 1
fi

echo "🎯 Selected provider: $PROVIDER"

# Create lease
echo "📝 Creating lease with provider..."
LEASE_TX=$(akash tx market lease create \
    --dseq $DSEQ \
    --provider $PROVIDER \
    --from $WALLET_NAME \
    --node https://rpc.akash.forbole.com:443 \
    --chain-id akashnet-2 \
    --gas-prices 0.025uakt \
    --gas auto \
    --gas-adjustment 1.15 \
    --broadcast-mode block \
    -y)

echo "🤝 Lease created: $LEASE_TX"

# Send manifest
echo "📋 Sending manifest to provider..."
akash provider send-manifest $DEPLOYMENT_FILE \
    --dseq $DSEQ \
    --provider $PROVIDER \
    --from $WALLET_NAME \
    --node https://rpc.akash.forbole.com:443

# Get lease status and service URIs
echo "📊 Getting deployment status..."
sleep 10

LEASE_STATUS=$(akash provider lease-status \
    --dseq $DSEQ \
    --provider $PROVIDER \
    --from $WALLET_NAME \
    --node https://rpc.akash.forbole.com:443)

echo "$LEASE_STATUS"

# Extract service URIs
OMEGA_API_URL=$(echo "$LEASE_STATUS" | jq -r '.services."omega-gpu".uris[0]' 2>/dev/null)
METRICS_URL=$(echo "$LEASE_STATUS" | jq -r '.services."omega-gpu".uris[1]' 2>/dev/null)

echo ""
echo "🎉 OMEGA Successfully Deployed to Akash Network!"
echo "==============================================="
echo "🆔 DSEQ: $DSEQ"
echo "🏢 Provider: $PROVIDER"
echo "🌐 OMEGA API: ${OMEGA_API_URL:-'Pending...'}"
echo "📊 Metrics: ${METRICS_URL:-'Pending...'}"
echo ""
echo "🔗 Useful commands:"
echo "   Check status: akash provider lease-status --dseq $DSEQ --provider $PROVIDER --from $WALLET_NAME --node https://rpc.akash.forbole.com:443"
echo "   View logs: akash provider service-logs --dseq $DSEQ --provider $PROVIDER --service omega-gpu --from $WALLET_NAME --node https://rpc.akash.forbole.com:443"
echo "   Close lease: akash tx market lease close --dseq $DSEQ --provider $PROVIDER --from $WALLET_NAME --node https://rpc.akash.forbole.com:443 --gas-prices 0.025uakt --gas auto --gas-adjustment 1.15"
echo ""
echo "💡 Test the deployment:"
if [ "$OMEGA_API_URL" != "null" ] && [ -n "$OMEGA_API_URL" ]; then
    echo "   curl $OMEGA_API_URL/health"
    echo "   curl $OMEGA_API_URL/api/v1/predictions -X POST -H 'Content-Type: application/json' -d '{\"count\":5}'"
fi