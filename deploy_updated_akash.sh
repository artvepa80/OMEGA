#!/bin/bash

# OMEGA PRO AI v10.1 - Deploy Updated Version with Execute Endpoint
# ================================================================

set -euo pipefail

echo "🚀 Deploying OMEGA PRO AI v10.1 with Execute Endpoint to Akash"
echo "=============================================================="

# Configuration
AKASH_CHAIN_ID="akashnet-2"
AKASH_NODE="https://rpc.akashnet.net:443"
AKASH_KEYRING_BACKEND="os"
AKASH_GAS_PRICES="0.025uakt"
AKASH_GAS_ADJUSTMENT="1.5"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if wallet exists
if ! akash keys show omega-wallet >/dev/null 2>&1; then
    log_error "Wallet 'omega-wallet' not found. Please create it first."
    exit 1
fi

# Create updated deployment file
cat > omega-updated-akash.yaml << 'EOF'
version: "2.0"

services:
  omega-api:
    image: python:3.11-slim
    expose:
      - port: 8000
        as: 80
        to:
          - global: true
        accept:
          - "*.akash.network"
        http_options:
          max_body_size: 67108864
    env:
      - OMEGA_ENV=production
      - OMEGA_VERSION=v10.1-execute
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
      - PORT=8000
    command:
      - "/bin/bash"
    args:
      - "-c"
      - |
        # Install system dependencies
        apt-get update && apt-get install -y \
          git \
          curl \
          build-essential \
          && rm -rf /var/lib/apt/lists/*
        
        # Clone/update repository
        if [ ! -d "/app" ]; then
          git clone https://github.com/tu-usuario/OMEGA_PRO_AI_v10.1.git /app || \
          (mkdir -p /app && echo "Using local files")
        fi
        
        cd /app
        
        # Copy updated api_main.py with execute endpoint
        cat > api_main.py << 'APIEOF'
EOF

# Add the updated api_main.py content
cat api_main.py >> omega-updated-akash.yaml

cat >> omega-updated-akash.yaml << 'EOF'
APIEOF
        
        # Install Python dependencies
        pip install --no-cache-dir \
          fastapi \
          uvicorn[standard] \
          pandas \
          numpy \
          scikit-learn \
          requests \
          pydantic
        
        # Start the API server
        exec uvicorn api_main:app --host 0.0.0.0 --port 8000

profiles:
  compute:
    omega-api:
      resources:
        cpu:
          units: 2.0
        memory:
          size: 4Gi
        storage:
          size: 10Gi
  placement:
    dcloud:
      pricing:
        omega-api:
          denom: uakt
          amount: 12000

deployment:
  omega-api:
    dcloud:
      profile: omega-api
      count: 1
EOF

log_info "Created updated deployment configuration"

# Deploy to Akash
log_info "Creating deployment..."
DEPLOY_TX=$(akash tx deployment create omega-updated-akash.yaml \
  --from omega-wallet \
  --node $AKASH_NODE \
  --chain-id $AKASH_CHAIN_ID \
  --gas-prices $AKASH_GAS_PRICES \
  --gas-adjustment $AKASH_GAS_ADJUSTMENT \
  --broadcast-mode block \
  --yes \
  --output json)

if [ $? -eq 0 ]; then
    log_success "Deployment transaction submitted!"
    
    # Extract deployment sequence
    DSEQ=$(echo $DEPLOY_TX | jq -r '.logs[0].events[] | select(.type=="akash.v1beta3.EventDeploymentCreated") | .attributes[] | select(.key=="dseq") | .value')
    
    if [ "$DSEQ" != "null" ] && [ -n "$DSEQ" ]; then
        log_success "Deployment Sequence (DSEQ): $DSEQ"
        
        echo ""
        echo "Next steps:"
        echo "1. Wait for bids: akash query market bid list --owner \$(akash keys show omega-wallet -a) --dseq $DSEQ"
        echo "2. Create lease with chosen provider"
        echo "3. Test the updated API with /execute endpoint"
        
    else
        log_error "Could not extract deployment sequence"
    fi
else
    log_error "Deployment failed"
    exit 1
fi