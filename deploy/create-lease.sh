#!/bin/bash

# OMEGA PRO AI - Create Akash Lease Script
# ========================================

if [ $# -ne 2 ]; then
    echo "Usage: $0 <DSEQ> <PROVIDER_ADDRESS>"
    echo "Example: $0 8012345 akash1provider_address_here"
    exit 1
fi

DSEQ=$1
PROVIDER=$2

echo "🤝 Creating lease with provider..."
echo "   DSEQ: $DSEQ"
echo "   Provider: $PROVIDER"

# Set environment
export AKASH_CHAIN_ID="akashnet-2"
export AKASH_NODE="https://rpc.akashnet.net:443"
export AKASH_KEYRING_BACKEND="os"
export AKASH_FROM="omega-wallet"
export AKASH_GAS_PRICES="0.025uakt"
export AKASH_GAS_ADJUSTMENT="1.5"

# Create lease
LEASE_TX=$(akash tx market lease create \
  --owner=akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t \
  --dseq=$DSEQ \
  --gseq=1 \
  --oseq=1 \
  --provider=$PROVIDER \
  --from $AKASH_FROM \
  --chain-id $AKASH_CHAIN_ID \
  --node $AKASH_NODE \
  --gas-prices $AKASH_GAS_PRICES \
  --gas-adjustment $AKASH_GAS_ADJUSTMENT \
  --fees 50000uakt \
  --yes)

if [ $? -eq 0 ]; then
    echo "✅ Lease created successfully!"
    echo "$LEASE_TX"
    
    echo "⏳ Waiting for deployment to start..."
    sleep 60
    
    # Send manifest
    echo "📄 Sending manifest to provider..."
    provider-services send-manifest omega-akash-optimized.yaml \
      --owner=akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t \
      --dseq=$DSEQ \
      --provider=$PROVIDER
    
    if [ $? -eq 0 ]; then
        echo "✅ Manifest sent successfully!"
        
        # Get lease status and URL
        echo "🔍 Getting deployment URL..."
        sleep 30
        
        LEASE_STATUS=$(akash query market lease get \
          --owner=akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t \
          --dseq=$DSEQ \
          --gseq=1 \
          --oseq=1 \
          --provider=$PROVIDER \
          --chain-id $AKASH_CHAIN_ID \
          --node $AKASH_NODE)
        
        echo "📊 Lease Status:"
        echo "$LEASE_STATUS"
        
        # Get service URL from provider
        echo "🌐 Getting service URL..."
        SERVICE_URL=$(provider-services lease-status \
          --owner=akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t \
          --dseq=$DSEQ \
          --provider=$PROVIDER | grep -o 'https://[^"]*')
        
        if [ ! -z "$SERVICE_URL" ]; then
            echo "🎉 OMEGA PRO AI is now running on Akash!"
            echo "🔗 URL: $SERVICE_URL"
            echo ""
            echo "📋 Available endpoints:"
            echo "   • Health check: $SERVICE_URL/health"
            echo "   • Predictions: $SERVICE_URL/predict (POST)"
            echo "   • Status: $SERVICE_URL/status"
            echo "   • API docs: $SERVICE_URL/docs"
            echo ""
            echo "🧪 Test the API:"
            echo "   curl $SERVICE_URL/health"
            echo "   curl -X POST $SERVICE_URL/predict -H 'Content-Type: application/json' -d '{\"quantity\": 3}'"
        else
            echo "⚠️ Could not retrieve service URL. Check provider logs."
        fi
    else
        echo "❌ Failed to send manifest!"
    fi
else
    echo "❌ Lease creation failed!"
fi