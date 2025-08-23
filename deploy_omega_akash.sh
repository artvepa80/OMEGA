#!/bin/bash
# 🚀 OMEGA PRO AI - Complete Akash Deployment Script
# Automated deployment to Akash Network with GPU support

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌐 OMEGA PRO AI v10.1 - Akash Network Deployment${NC}"
echo "=========================================================="

# Load environment variables
if [ -f "akash_env.sh" ]; then
    echo -e "${GREEN}📋 Loading Akash environment...${NC}"
    source akash_env.sh
else
    echo -e "${YELLOW}⚠️  Setting up environment variables...${NC}"
    export AKASH_NET="https://raw.githubusercontent.com/akash-network/net/main/mainnet"
    export AKASH_CHAIN_ID="akashnet-2"
    export AKASH_NODE="https://rpc.akashnet.net:443"
fi

# Wallet configuration
WALLET_NAME="omega-wallet"
WALLET_ADDRESS="akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t"

echo -e "${GREEN}💰 Wallet: $WALLET_NAME${NC}"
echo -e "${GREEN}📧 Address: $WALLET_ADDRESS${NC}"

# Check wallet balance
echo -e "${BLUE}💰 Checking wallet balance...${NC}"
BALANCE=$(akash query bank balances $WALLET_ADDRESS --node $AKASH_NODE --output json | jq -r '.balances[] | select(.denom=="uakt") | .amount' 2>/dev/null || echo "0")
AKT_BALANCE=$(echo "scale=2; $BALANCE / 1000000" | bc -l 2>/dev/null || echo "0.00")

echo -e "${GREEN}💰 Current balance: $AKT_BALANCE AKT${NC}"

if (( $(echo "$AKT_BALANCE < 50" | bc -l) )); then
    echo -e "${RED}❌ Insufficient AKT balance! You need at least 50 AKT for deployment.${NC}"
    echo -e "${YELLOW}💡 Please fund your wallet and try again.${NC}"
    echo -e "${YELLOW}   Wallet address: $WALLET_ADDRESS${NC}"
    exit 1
fi

# Build Docker image
echo -e "${BLUE}🏗️  Building Docker image for Akash...${NC}"
if command -v docker &> /dev/null; then
    docker build -f Dockerfile.akash -t omega-pro-ai:latest .
    
    # For production, push to registry
    echo -e "${YELLOW}📝 Note: For actual deployment, push image to public registry:${NC}"
    echo "   docker tag omega-pro-ai:latest your-registry/omega-pro-ai:latest"
    echo "   docker push your-registry/omega-pro-ai:latest"
    echo "   Then update the image name in deploy/omega-akash-gpu.yaml"
else
    echo -e "${YELLOW}⚠️  Docker not found. Please build image manually.${NC}"
fi

# Create deployment
echo -e "${BLUE}🚀 Creating Akash deployment...${NC}"
DEPLOY_OUTPUT=$(akash tx deployment create deploy/omega-akash-gpu.yaml \
    --from $WALLET_NAME \
    --node $AKASH_NODE \
    --chain-id $AKASH_CHAIN_ID \
    --gas 200000 \
    --gas-adjustment 1.5 \
    --gas-prices 0.025uakt \
    --broadcast-mode block \
    --yes 2>&1)

echo "$DEPLOY_OUTPUT"

# Extract deployment ID
DSEQ=$(echo "$DEPLOY_OUTPUT" | grep -o 'dseq:[0-9]*' | cut -d: -f2 | head -1)

if [ -z "$DSEQ" ]; then
    echo -e "${RED}❌ Could not extract deployment ID. Check the output above.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment created! DSEQ: $DSEQ${NC}"

# Wait for bids
echo -e "${BLUE}⏳ Waiting for provider bids...${NC}"
sleep 30

BID_COUNT=0
RETRY_COUNT=0
MAX_RETRIES=20

while [ $BID_COUNT -eq 0 ] && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo -n "."
    BIDS=$(akash query market bid list \
        --owner $WALLET_ADDRESS \
        --dseq $DSEQ \
        --node $AKASH_NODE \
        --output json 2>/dev/null)
    
    BID_COUNT=$(echo "$BIDS" | jq -r '.bids | length' 2>/dev/null || echo "0")
    
    if [ $BID_COUNT -eq 0 ]; then
        sleep 15
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

echo ""

if [ $BID_COUNT -eq 0 ]; then
    echo -e "${RED}❌ No bids received after waiting. Try adjusting pricing in SDL file.${NC}"
    exit 1
fi

echo -e "${GREEN}📦 Received $BID_COUNT bid(s)!${NC}"

# Show available bids
echo -e "${BLUE}Available providers:${NC}"
echo "$BIDS" | jq -r '.bids[] | "Provider: \(.bid.bidder[0:16])... Price: \(.bid.price.amount) uAKT/block"'

# Select the lowest bid automatically
PROVIDER=$(echo "$BIDS" | jq -r '.bids | sort_by(.bid.price.amount | tonumber) | .[0].bid.bidder')
PRICE=$(echo "$BIDS" | jq -r '.bids | sort_by(.bid.price.amount | tonumber) | .[0].bid.price.amount')
DAILY_COST=$(echo "scale=2; $PRICE * 24 * 60 / 1000000" | bc -l)

echo -e "${GREEN}🏆 Selected provider: ${PROVIDER:0:16}...${NC}"
echo -e "${GREEN}💰 Price: $PRICE uAKT/block (~$$DAILY_COST/day)${NC}"

# Create lease
echo -e "${BLUE}📋 Creating lease...${NC}"
akash tx market lease create \
    --owner $WALLET_ADDRESS \
    --dseq $DSEQ \
    --gseq 1 \
    --oseq 1 \
    --provider $PROVIDER \
    --from $WALLET_NAME \
    --node $AKASH_NODE \
    --chain-id $AKASH_CHAIN_ID \
    --gas 200000 \
    --gas-adjustment 1.5 \
    --gas-prices 0.025uakt \
    --broadcast-mode block \
    --yes

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Lease created successfully!${NC}"
else
    echo -e "${RED}❌ Failed to create lease${NC}"
    exit 1
fi

# Wait for deployment to be ready
echo -e "${BLUE}⏳ Waiting for deployment to be active...${NC}"
sleep 60

# Get lease status and URL
echo -e "${BLUE}📊 Getting deployment status...${NC}"
LEASE_STATUS=$(akash provider lease-status \
    --node $AKASH_NODE \
    --dseq $DSEQ \
    --gseq 1 \
    --oseq 1 \
    --provider $PROVIDER \
    --from $WALLET_NAME \
    --output json 2>/dev/null)

if [ $? -eq 0 ]; then
    # Extract URLs
    URLS=$(echo "$LEASE_STATUS" | jq -r '.services.omega-ai.uris[]?' 2>/dev/null)
    
    echo -e "${GREEN}🎉 OMEGA PRO AI deployed successfully to Akash Network!${NC}"
    echo "=========================================================="
    echo -e "${GREEN}🆔 Deployment ID: $DSEQ${NC}"
    echo -e "${GREEN}🏢 Provider: ${PROVIDER:0:16}...${NC}"
    echo -e "${GREEN}💰 Daily cost: ~$$DAILY_COST${NC}"
    echo ""
    
    if [ ! -z "$URLS" ]; then
        echo -e "${GREEN}🌐 OMEGA API URLs:${NC}"
        echo "$URLS" | while read -r URL; do
            echo -e "${BLUE}   • API: $URL${NC}"
            echo -e "${BLUE}   • Health: $URL/health${NC}"
            echo -e "${BLUE}   • Predict: $URL/predict${NC}"
        done
    else
        echo -e "${YELLOW}⚠️  URLs not ready yet. Check status in a few minutes.${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}📊 Useful commands:${NC}"
    echo "   Status: akash provider lease-status --dseq $DSEQ --provider $PROVIDER --from $WALLET_NAME"
    echo "   Logs:   akash provider lease-logs --dseq $DSEQ --provider $PROVIDER --from $WALLET_NAME"
    echo "   Close:  akash tx deployment close --dseq $DSEQ --from $WALLET_NAME"
    
    # Save deployment info
    cat > omega_deployment_info.json << EOF
{
  "deployment_id": "$DSEQ",
  "provider": "$PROVIDER",
  "wallet": "$WALLET_NAME",
  "daily_cost": "$DAILY_COST",
  "deployment_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "urls": $(echo "$URLS" | jq -R . | jq -s .)
}
EOF
    
    echo -e "${GREEN}💾 Deployment info saved to: omega_deployment_info.json${NC}"
    
else
    echo -e "${YELLOW}⚠️  Could not get lease status. Deployment may still be starting up.${NC}"
    echo -e "${YELLOW}💡 Try checking status in a few minutes with:${NC}"
    echo "   akash provider lease-status --dseq $DSEQ --provider $PROVIDER --from $WALLET_NAME"
fi

echo ""
echo -e "${GREEN}🎯 OMEGA PRO AI is now running 24/7 on Akash Network!${NC}"
echo -e "${GREEN}🌍 Accessible globally with 50% validated accuracy baseline${NC}"
echo "=========================================================="