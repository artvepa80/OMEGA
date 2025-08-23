#!/bin/bash

echo "🚀 Deploying OMEGA Terminal to Akash Network"
echo "============================================="

# Set Akash environment
export AKASH_NET="https://raw.githubusercontent.com/akash-network/net/main/mainnet"
export AKASH_VERSION="0.38.0"
export AKASH_CHAIN_ID="akashnet-2"
export AKASH_NODE="https://rpc.akashnet.net:443"
export AKASH_KEYRING_BACKEND="os"
export AKASH_FROM="omega-wallet"
export AKASH_GAS_PRICES="0.025uakt"
export AKASH_GAS_ADJUSTMENT="1.5"

echo "📋 Creating deployment with terminal server..."

# Create the deployment
akash tx deployment create deploy/omega-terminal-akash.yaml \
  --from $AKASH_FROM \
  --node $AKASH_NODE \
  --chain-id $AKASH_CHAIN_ID \
  --gas-prices $AKASH_GAS_PRICES \
  --gas-adjustment $AKASH_GAS_ADJUSTMENT \
  --yes

echo ""
echo "⏳ Waiting for deployment to process..."
sleep 30

echo ""
echo "📋 Checking deployment status..."
akash query deployment list \
  --owner $(akash keys show $AKASH_FROM -a) \
  --node $AKASH_NODE \
  --chain-id $AKASH_CHAIN_ID

echo ""
echo "🔍 Checking for bids..."
akash query market bid list \
  --owner $(akash keys show $AKASH_FROM -a) \
  --node $AKASH_NODE \
  --chain-id $AKASH_CHAIN_ID

echo ""
echo "✅ Deployment created! Next steps:"
echo "1. Wait for bids from providers"
echo "2. Create lease with selected provider"
echo "3. Access terminal at the provided URI"