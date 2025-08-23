#!/bin/bash

# Update Current Akash Deployment to Full Terminal Server
# This script updates the existing deployment to use omega_akash_terminal.py

set -e

echo "🔄 OMEGA Terminal Server - Update Current Deployment"
echo "===================================================="
echo "📍 Current URL: https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win"
echo "🎯 Target: Full terminal server with /execute and /predict endpoints"
echo ""

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker not found"
    exit 1
fi

echo "✅ Prerequisites checked"

# Build the terminal server image
echo ""
echo "🔨 Building OMEGA Terminal Server image..."
docker build -f Dockerfile.terminal -t artvepa80/omega-terminal:latest .

echo ""
echo "📤 Pushing updated image to registry..."
docker push artvepa80/omega-terminal:latest

echo ""
echo "✅ Updated Docker image deployed to registry"
echo ""
echo "🔧 NEXT STEPS FOR AKASH DEPLOYMENT:"
echo ""
echo "Option A - Update Existing Deployment (Recommended):"
echo "1. Close current deployment:"
echo "   akash tx deployment close --dseq <CURRENT_DSEQ> --from \$AKASH_ACCOUNT"
echo ""
echo "2. Deploy new terminal server:"
echo "   akash tx deployment create deploy/omega-terminal-server.yaml --from \$AKASH_ACCOUNT"
echo ""
echo "3. Create lease for new deployment:"
echo "   ./create-lease.sh <NEW_DSEQ>"
echo ""
echo "Option B - Manual Provider Update (Advanced):"
echo "1. Contact your provider to update image to: artvepa80/omega-terminal:latest"
echo "2. Request container restart with new entrypoint"
echo ""
echo "Expected Result After Update:"
echo "✅ /health endpoint - health status"
echo "✅ /predict endpoint - optimized predictions"
echo "✅ /execute endpoint - run any OMEGA command"
echo "✅ / endpoint - full web terminal interface"
echo ""
echo "Validation Command:"
echo "python3 validate-omega-terminal.py https://your-new-url.com"

# Create a quick deployment script
echo ""
echo "🤖 Creating quick deployment script..."

cat > quick-redeploy.sh << 'EOF'
#!/bin/bash

echo "🚀 Quick Redeploy OMEGA Terminal Server"

# Close existing deployment (if you know the DSEQ)
read -p "Enter current DSEQ to close (or press enter to skip): " CURRENT_DSEQ
if [ ! -z "$CURRENT_DSEQ" ]; then
    echo "Closing deployment $CURRENT_DSEQ..."
    akash tx deployment close --dseq $CURRENT_DSEQ --from $AKASH_ACCOUNT \
        --node $AKASH_NODE --chain-id $AKASH_CHAIN_ID \
        --gas-prices 0.025uakt --gas-adjustment 1.15 --gas auto -b block -y
    echo "✅ Deployment closed"
    sleep 5
fi

# Create new deployment
echo "Creating new deployment..."
akash tx deployment create deploy/omega-terminal-server.yaml \
    --from $AKASH_ACCOUNT \
    --node $AKASH_NODE \
    --chain-id $AKASH_CHAIN_ID \
    --gas-prices 0.025uakt \
    --gas-adjustment 1.15 \
    --gas auto \
    -b block \
    -y

sleep 10

# Get new DSEQ
NEW_DSEQ=$(akash query deployment list --owner $AKASH_ACCOUNT_ADDRESS \
    --node $AKASH_NODE \
    --chain-id $AKASH_CHAIN_ID \
    --output json | jq -r '.deployments[0].deployment.deployment_id.dseq')

echo "📋 New DSEQ: $NEW_DSEQ"

# Auto-create lease
./create-lease.sh $NEW_DSEQ
EOF

chmod +x quick-redeploy.sh

echo "📄 Created: quick-redeploy.sh - automated redeploy script"
echo ""
echo "🎯 IMMEDIATE ACTIONS:"
echo ""
echo "For fastest deployment, run:"
echo "./quick-redeploy.sh"
echo ""
echo "Then validate with:"
echo "python3 validate-omega-terminal.py <new-url>"
echo ""
echo "✨ After update, you'll have:"
echo "   - Full terminal interface at /"
echo "   - Fast predictions at /predict"
echo "   - Custom commands at /execute"
echo "   - All processing 100% on Akash"