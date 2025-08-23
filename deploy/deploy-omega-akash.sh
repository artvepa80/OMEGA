#!/bin/bash

# OMEGA PRO AI v10.1 - Akash Network Deployment Script
# =================================================

echo "🚀 OMEGA PRO AI v10.1 - Akash Deployment Script"
echo "================================================="

# Step 1: Set Akash Environment Variables
echo "📝 Setting up Akash environment..."
export AKASH_NET="https://raw.githubusercontent.com/akash-network/net/main/mainnet"
export AKASH_VERSION="0.38.0"
export AKASH_CHAIN_ID="akashnet-2"
export AKASH_NODE="https://rpc.akashnet.net:443"
export AKASH_KEYRING_BACKEND="os"
export AKASH_FROM="omega-wallet"
export AKASH_GAS_PRICES="0.025uakt"
export AKASH_GAS_ADJUSTMENT="1.5"

echo "✅ Environment configured:"
echo "   Chain ID: $AKASH_CHAIN_ID"
echo "   Node: $AKASH_NODE"
echo "   Wallet: $AKASH_FROM"

# Step 2: Check wallet balance
echo "💰 Checking wallet balance..."
BALANCE=$(akash query bank balances akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t --chain-id $AKASH_CHAIN_ID --node $AKASH_NODE)
echo "$BALANCE"

# Step 3: Estimate deployment costs
echo "💸 Deployment cost estimation:"
echo "   - Deployment creation: ~0.05 AKT (50,000 uakt)"
echo "   - Monthly hosting: ~5 AKT/month"
echo "   - Recommended minimum: 10 AKT for safe deployment"

# Step 4: Create deployment
echo "🚀 Creating deployment..."
DEPLOYMENT_TX=$(akash tx deployment create omega-akash-optimized.yaml \
  --from $AKASH_FROM \
  --chain-id $AKASH_CHAIN_ID \
  --node $AKASH_NODE \
  --gas-prices $AKASH_GAS_PRICES \
  --gas-adjustment $AKASH_GAS_ADJUSTMENT \
  --fees 50000uakt \
  --yes)

if [ $? -eq 0 ]; then
    echo "✅ Deployment created successfully!"
    echo "$DEPLOYMENT_TX"
    
    # Extract deployment sequence (DSEQ)
    DSEQ=$(echo "$DEPLOYMENT_TX" | grep -o '"key":"dseq","value":"[0-9]*"' | grep -o '[0-9]*')
    echo "📋 Deployment Sequence (DSEQ): $DSEQ"
    
    # Step 5: Query market for bids
    echo "🏪 Waiting for provider bids..."
    sleep 30
    
    echo "📊 Checking available bids..."
    akash query market bid list --owner=akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t --dseq=$DSEQ --chain-id $AKASH_CHAIN_ID --node $AKASH_NODE
    
    echo "📋 Next steps:"
    echo "1. Review the bids above"
    echo "2. Select a provider (copy the provider address)"
    echo "3. Run: ./create-lease.sh $DSEQ [provider-address]"
    
else
    echo "❌ Deployment creation failed!"
    echo "Please check:"
    echo "1. Wallet has sufficient AKT balance (minimum 10 AKT recommended)"
    echo "2. Network connectivity"
    echo "3. Akash CLI is properly configured"
fi

echo "📚 For more info: https://docs.akash.network/"