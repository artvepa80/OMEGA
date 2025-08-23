#!/bin/bash

# OMEGA PRO AI - Akash Deployment Monitoring Script
# ===============================================

if [ $# -lt 1 ]; then
    echo "Usage: $0 <DSEQ> [PROVIDER_ADDRESS]"
    echo "Example: $0 8012345 [optional-provider-address]"
    exit 1
fi

DSEQ=$1
PROVIDER=${2:-""}

echo "📊 OMEGA PRO AI - Deployment Monitoring"
echo "======================================="
echo "DSEQ: $DSEQ"
echo "Provider: ${PROVIDER:-"Auto-detect"}"
echo ""

# Set environment
export AKASH_CHAIN_ID="akashnet-2"
export AKASH_NODE="https://rpc.akashnet.net:443"
export AKASH_FROM="omega-wallet"

# Function to get deployment status
check_deployment_status() {
    echo "🔍 Checking deployment status..."
    akash query deployment get \
      --owner=akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t \
      --dseq=$DSEQ \
      --chain-id $AKASH_CHAIN_ID \
      --node $AKASH_NODE
}

# Function to check bids
check_bids() {
    echo "💰 Checking provider bids..."
    akash query market bid list \
      --owner=akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t \
      --dseq=$DSEQ \
      --chain-id $AKASH_CHAIN_ID \
      --node $AKASH_NODE
}

# Function to check lease
check_lease() {
    if [ ! -z "$PROVIDER" ]; then
        echo "🤝 Checking lease status..."
        akash query market lease get \
          --owner=akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t \
          --dseq=$DSEQ \
          --gseq=1 \
          --oseq=1 \
          --provider=$PROVIDER \
          --chain-id $AKASH_CHAIN_ID \
          --node $AKASH_NODE
    else
        echo "⚠️ Provider address needed to check lease status"
    fi
}

# Function to get service URL and test endpoints
test_service() {
    if [ ! -z "$PROVIDER" ]; then
        echo "🌐 Getting service URL..."
        SERVICE_URL=$(provider-services lease-status \
          --owner=akash1a7ztnxls3dgzdpm85nthvhdhv8wuttre0ydy8t \
          --dseq=$DSEQ \
          --provider=$PROVIDER 2>/dev/null | grep -o 'https://[^"]*' | head -1)
        
        if [ ! -z "$SERVICE_URL" ]; then
            echo "✅ Service URL found: $SERVICE_URL"
            echo ""
            
            echo "🧪 Testing API endpoints..."
            
            # Test health endpoint
            echo "Testing /health..."
            HEALTH_RESPONSE=$(curl -s --max-time 10 "$SERVICE_URL/health")
            if [ $? -eq 0 ]; then
                echo "✅ Health check passed"
                echo "$HEALTH_RESPONSE" | jq . 2>/dev/null || echo "$HEALTH_RESPONSE"
            else
                echo "❌ Health check failed"
            fi
            echo ""
            
            # Test status endpoint
            echo "Testing /status..."
            STATUS_RESPONSE=$(curl -s --max-time 10 "$SERVICE_URL/status")
            if [ $? -eq 0 ]; then
                echo "✅ Status check passed"
                echo "$STATUS_RESPONSE" | jq . 2>/dev/null || echo "$STATUS_RESPONSE"
            else
                echo "❌ Status check failed"
            fi
            echo ""
            
            # Test prediction endpoint
            echo "Testing /predict..."
            PREDICT_RESPONSE=$(curl -s --max-time 15 -X POST "$SERVICE_URL/predict" \
              -H "Content-Type: application/json" \
              -d '{"quantity": 2}')
            if [ $? -eq 0 ]; then
                echo "✅ Prediction endpoint passed"
                echo "$PREDICT_RESPONSE" | jq . 2>/dev/null || echo "$PREDICT_RESPONSE"
            else
                echo "❌ Prediction endpoint failed"
            fi
            
            echo ""
            echo "📋 Service Summary:"
            echo "   URL: $SERVICE_URL"
            echo "   Health: $SERVICE_URL/health"
            echo "   Status: $SERVICE_URL/status"
            echo "   Predict: $SERVICE_URL/predict (POST)"
            echo "   Docs: $SERVICE_URL/docs"
            
        else
            echo "❌ Could not retrieve service URL"
        fi
    else
        echo "⚠️ Provider address needed to get service URL"
    fi
}

# Main monitoring sequence
echo "Starting monitoring sequence..."
echo ""

check_deployment_status
echo ""

check_bids
echo ""

if [ ! -z "$PROVIDER" ]; then
    check_lease
    echo ""
    test_service
else
    echo "💡 To get full monitoring with service tests, run:"
    echo "   $0 $DSEQ <provider-address>"
fi

echo ""
echo "📚 Monitoring complete!"
echo "Re-run this script anytime to check deployment status."