#!/bin/bash

# OMEGA Terminal Server - Complete Akash Deployment Script
# Configures OMEGA AI to run predictions directly on Akash Network

set -e

echo "🚀 OMEGA Terminal Server - Akash Deployment"
echo "============================================"

# Check if akash CLI is available
if ! command -v akash &> /dev/null; then
    echo "❌ Error: Akash CLI not found"
    echo "💡 Install: https://docs.akash.network/guides/cli"
    exit 1
fi

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker not found"
    echo "💡 Install Docker first"
    exit 1
fi

echo "✅ Prerequisites checked"

# Build and push Docker image
echo ""
echo "🔨 Building Docker image..."
docker build -f Dockerfile.terminal -t artvepa80/omega-terminal:latest .

echo ""
echo "📤 Pushing Docker image to registry..."
docker push artvepa80/omega-terminal:latest

echo ""
echo "🌐 Deploying to Akash Network..."

# Set environment variables if not set
export AKASH_NET=${AKASH_NET:-mainnet}
export AKASH_VERSION=${AKASH_VERSION:-v0.34.2}
export AKASH_CHAIN_ID=${AKASH_CHAIN_ID:-akashnet-2}
export AKASH_NODE=${AKASH_NODE:-https://rpc.akash.network:443}

# Deploy using SDL file
echo "📝 Creating deployment..."
akash tx deployment create deploy/omega-terminal-server.yaml \
  --from ${AKASH_ACCOUNT} \
  --node ${AKASH_NODE} \
  --chain-id ${AKASH_CHAIN_ID} \
  --gas-prices 0.025uakt \
  --gas-adjustment 1.15 \
  --gas auto \
  -b block \
  -y

echo ""
echo "⏳ Waiting for deployment creation..."
sleep 10

# Get deployment sequence
DSEQ=$(akash query deployment list --owner ${AKASH_ACCOUNT_ADDRESS} \
  --node ${AKASH_NODE} \
  --chain-id ${AKASH_CHAIN_ID} \
  --output json | jq -r '.deployments[0].deployment.deployment_id.dseq')

echo "📋 Deployment DSEQ: ${DSEQ}"

# Query market for bids
echo "🏪 Querying marketplace for bids..."
sleep 5

akash query market bid list \
  --owner ${AKASH_ACCOUNT_ADDRESS} \
  --node ${AKASH_NODE} \
  --chain-id ${AKASH_CHAIN_ID} \
  --dseq ${DSEQ}

echo ""
echo "💡 Manual steps needed:"
echo "1. Choose a provider from the bids above"
echo "2. Create lease: akash tx market lease create --dseq ${DSEQ} --provider <PROVIDER> --from ${AKASH_ACCOUNT}"
echo "3. Get lease status: akash lease-status --dseq ${DSEQ} --provider <PROVIDER>"
echo ""
echo "Or use the automated lease creation script:"
echo "./create-lease.sh ${DSEQ}"

echo ""
echo "✅ Deployment configuration completed!"
echo "🔗 SDL File: deploy/omega-terminal-server.yaml"
echo "🐳 Docker Image: artvepa80/omega-terminal:latest"
echo "📡 Expected Endpoints: /execute /predict /health"