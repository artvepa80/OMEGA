#!/bin/bash

echo "🔗 OMEGA GPU Shell Connector"
echo "============================"

# Akash environment
export AKASH_NODE="https://rpc.akashnet.net:443"
export AKASH_CHAIN_ID="akashnet-2"
export AKASH_FROM="omega-wallet"

# Check if required tools are installed
if ! command -v provider-services >/dev/null 2>&1; then
    echo "❌ provider-services not found. Install with:"
    echo "   go install github.com/akash-network/provider/cmd/provider-services@latest"
    exit 1
fi

# Get wallet address
OWNER=$(akash keys show $AKASH_FROM -a 2>/dev/null || echo "")
if [[ -z "$OWNER" ]]; then
    echo "❌ Could not get wallet address. Check your Akash configuration."
    exit 1
fi

echo "👤 Wallet: $OWNER"
echo ""

# List deployments
echo "📋 Your active deployments:"
akash query deployment list \
    --owner $OWNER \
    --node $AKASH_NODE \
    --chain-id $AKASH_CHAIN_ID

echo ""
echo "🔍 Finding GPU deployment..."

# Try to auto-detect OMEGA deployment
DEPLOYMENTS=$(akash query deployment list --owner $OWNER --node $AKASH_NODE --chain-id $AKASH_CHAIN_ID --output json 2>/dev/null)

if [[ -n "$DEPLOYMENTS" ]]; then
    # Extract DSEQ if available
    DSEQ=$(echo "$DEPLOYMENTS" | grep -o '"dseq":"[0-9]*"' | head -1 | cut -d'"' -f4)
    
    if [[ -n "$DSEQ" ]]; then
        echo "✅ Found deployment DSEQ: $DSEQ"
        
        # Get lease info
        echo "🔍 Getting lease information..."
        LEASE_INFO=$(akash query market lease list \
            --owner $OWNER \
            --node $AKASH_NODE \
            --chain-id $AKASH_CHAIN_ID \
            --output json 2>/dev/null)
        
        if [[ -n "$LEASE_INFO" ]]; then
            PROVIDER=$(echo "$LEASE_INFO" | grep -o '"provider":"[^"]*"' | head -1 | cut -d'"' -f4)
            
            if [[ -n "$PROVIDER" ]]; then
                echo "✅ Found provider: $PROVIDER"
                echo ""
                echo "🚀 Connecting to OMEGA GPU container..."
                echo "======================================="
                
                # Connect to shell
                provider-services lease-shell \
                    --from $AKASH_FROM \
                    --dseq $DSEQ \
                    --provider $PROVIDER \
                    --service omega-cpu \
                    --tty \
                    --node $AKASH_NODE \
                    /bin/bash
                    
                echo ""
                echo "🎯 Once connected, you can run:"
                echo "   python3 main.py                 # Execute OMEGA main system"
                echo "   python3 omega_unified_main.py   # Execute unified system"
                echo "   htop                            # Check CPU/memory usage"
                echo "   free -h                         # Check memory status"
                
            else
                echo "❌ Could not find provider address"
                manual_connection
            fi
        else
            echo "❌ Could not get lease information"
            manual_connection
        fi
    else
        echo "❌ Could not extract DSEQ"
        manual_connection
    fi
else
    echo "❌ No deployments found or query failed"
    manual_connection
fi

manual_connection() {
    echo ""
    echo "🔧 Manual connection required"
    echo "============================="
    echo ""
    echo "1. Get your deployment info:"
    echo "   akash query deployment list --owner $OWNER --node $AKASH_NODE --chain-id $AKASH_CHAIN_ID"
    echo ""
    echo "2. Get lease info:"
    echo "   akash query market lease list --owner $OWNER --node $AKASH_NODE --chain-id $AKASH_CHAIN_ID"
    echo ""
    echo "3. Connect manually:"
    echo "   provider-services lease-shell \\"
    echo "     --from $AKASH_FROM \\"
    echo "     --dseq <YOUR_DSEQ> \\"
    echo "     --provider <YOUR_PROVIDER> \\"
    echo "     --service omega-cpu \\"
    echo "     --tty \\"
    echo "     --node $AKASH_NODE \\"
    echo "     /bin/bash"
    echo ""
    echo "4. Run OMEGA:"
    echo "   python3 main.py"
}

echo ""
echo "💡 Tip: Once in the container, all GPU resources are available to main.py"
echo "   Output will stream to your Mac terminal in real-time!"