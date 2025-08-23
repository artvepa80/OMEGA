#!/bin/bash

echo "🚀 OMEGA PRO AI v10.1 - GPU Deployment to Akash Network"
echo "======================================================="

# Set Akash environment
export AKASH_NET="https://raw.githubusercontent.com/akash-network/net/main/mainnet"
export AKASH_VERSION="0.38.0"
export AKASH_CHAIN_ID="akashnet-2"
export AKASH_NODE="https://rpc.akashnet.net:443"
export AKASH_KEYRING_BACKEND="os"
export AKASH_FROM="omega-wallet"
export AKASH_GAS_PRICES="0.025uakt"
export AKASH_GAS_ADJUSTMENT="1.5"

echo "📦 Step 1: Build and push Docker image"
echo "======================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build the image
echo "🔨 Building OMEGA Docker image..."
docker build -f Dockerfile.simple -t omega-ai:latest .

echo "📋 Image built. Next steps:"
echo "1. Tag and push to Docker Hub:"
echo "   docker tag omega-ai:latest YOUR-DOCKERHUB-USERNAME/omega-ai:latest"
echo "   docker push YOUR-DOCKERHUB-USERNAME/omega-ai:latest"
echo ""
echo "2. Update deploy/omega-gpu-akash.yaml with your Docker Hub username"
echo ""
echo "3. Deploy to Akash:"
echo "   ./deploy_omega_gpu.sh deploy"
echo ""

if [[ "$1" == "deploy" ]]; then
    echo "🚀 Step 2: Deploy to Akash Network"
    echo "=================================="
    
    # Check if deployment file exists
    if [[ ! -f "deploy/omega-gpu-akash.yaml" ]]; then
        echo "❌ Deployment file not found: deploy/omega-gpu-akash.yaml"
        exit 1
    fi
    
    # Create deployment
    echo "📤 Creating GPU deployment..."
    akash tx deployment create deploy/omega-gpu-akash.yaml \
        --from $AKASH_FROM \
        --node $AKASH_NODE \
        --chain-id $AKASH_CHAIN_ID \
        --gas-prices $AKASH_GAS_PRICES \
        --gas-adjustment $AKASH_GAS_ADJUSTMENT \
        --yes
    
    echo "⏳ Waiting for deployment to process..."
    sleep 30
    
    # Check deployment status
    echo "📊 Checking deployment status..."
    OWNER=$(akash keys show $AKASH_FROM -a 2>/dev/null || echo "")
    
    if [[ -n "$OWNER" ]]; then
        echo "👤 Owner: $OWNER"
        
        akash query deployment list \
            --owner $OWNER \
            --node $AKASH_NODE \
            --chain-id $AKASH_CHAIN_ID
        
        echo ""
        echo "🔍 Checking for bids..."
        akash query market bid list \
            --owner $OWNER \
            --node $AKASH_NODE \
            --chain-id $AKASH_CHAIN_ID
        
        echo ""
        echo "📋 Next steps:"
        echo "1. Wait for bids from GPU providers"
        echo "2. Create lease: ./connect_gpu_shell.sh"
        echo "3. Access shell: provider-services lease-shell ..."
    else
        echo "❌ Could not retrieve wallet address. Check your Akash wallet configuration."
    fi
    
elif [[ "$1" == "connect" ]]; then
    echo "🔗 Step 3: Connect to GPU container shell"
    echo "========================================"
    
    # This will be filled in after deployment
    echo "⚠️  You need to run this after successful deployment:"
    echo ""
    echo "# Get your DSEQ from deployment list"
    echo "export DSEQ=YOUR_DEPLOYMENT_SEQUENCE"
    echo "export PROVIDER=YOUR_PROVIDER_ADDRESS"
    echo ""
    echo "# Connect to container shell"
    echo "provider-services lease-shell \\"
    echo "  --from $AKASH_FROM \\"
    echo "  --dseq \$DSEQ \\"
    echo "  --provider \$PROVIDER \\"
    echo "  --service omega-gpu \\"
    echo "  --tty \\"
    echo "  --node $AKASH_NODE \\"
    echo "  /bin/bash"
    echo ""
    echo "# Once connected, run OMEGA:"
    echo "python3 main.py"
    
else
    echo "🎯 Usage:"
    echo "  ./deploy_omega_gpu.sh         # Build Docker image"
    echo "  ./deploy_omega_gpu.sh deploy  # Deploy to Akash"
    echo "  ./deploy_omega_gpu.sh connect # Show connection instructions"
fi

echo ""
echo "💡 Remember:"
echo "   - GPU resources cost more AKT tokens"
echo "   - Make sure your Docker image is pushed to Docker Hub"
echo "   - Check GPU availability on Akash providers"