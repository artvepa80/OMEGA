#!/bin/bash

# Auto-lease creation for OMEGA Terminal deployment
# Usage: ./create-lease.sh <DSEQ>

set -e

DSEQ=$1

if [ -z "$DSEQ" ]; then
    echo "❌ Usage: $0 <DSEQ>"
    exit 1
fi

echo "🔍 Auto-selecting best provider for DSEQ: $DSEQ"

# Get the first available bid (usually the cheapest)
PROVIDER=$(akash query market bid list \
  --owner ${AKASH_ACCOUNT_ADDRESS} \
  --node ${AKASH_NODE} \
  --chain-id ${AKASH_CHAIN_ID} \
  --dseq ${DSEQ} \
  --output json | jq -r '.bids[0].bid.bid_id.provider')

if [ "$PROVIDER" = "null" ] || [ -z "$PROVIDER" ]; then
    echo "❌ No providers found for deployment $DSEQ"
    echo "💡 Wait a few more seconds and try again"
    exit 1
fi

echo "✅ Selected provider: $PROVIDER"

# Create lease
echo "🤝 Creating lease..."
akash tx market lease create \
  --dseq ${DSEQ} \
  --provider ${PROVIDER} \
  --from ${AKASH_ACCOUNT} \
  --node ${AKASH_NODE} \
  --chain-id ${AKASH_CHAIN_ID} \
  --gas-prices 0.025uakt \
  --gas-adjustment 1.15 \
  --gas auto \
  -b block \
  -y

echo ""
echo "⏳ Waiting for lease activation..."
sleep 15

# Get lease status and URL
echo "📊 Checking lease status..."
LEASE_STATUS=$(akash lease-status \
  --dseq ${DSEQ} \
  --provider ${PROVIDER} \
  --from ${AKASH_ACCOUNT} \
  --node ${AKASH_NODE} \
  --chain-id ${AKASH_CHAIN_ID})

echo "$LEASE_STATUS"

# Extract URL from lease status
URL=$(echo "$LEASE_STATUS" | grep -o 'https://[^[:space:]]*' | head -1)

if [ ! -z "$URL" ]; then
    echo ""
    echo "🌐 OMEGA Terminal Server deployed successfully!"
    echo "🔗 URL: $URL"
    echo "📡 Test endpoints:"
    echo "   Health: curl $URL/health"
    echo "   Predict: curl -X POST $URL/predict"
    echo "   Execute: curl -X POST $URL/execute"
    echo ""
    echo "🎯 Quick prediction test:"
    echo "curl -X POST $URL/predict -H 'Content-Type: application/json' -d '{\"predictions\": 5}'"
else
    echo "⚠️  Lease created but URL not found yet. Check status in a few minutes:"
    echo "akash lease-status --dseq $DSEQ --provider $PROVIDER"
fi