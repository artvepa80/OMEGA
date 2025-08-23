#!/bin/bash
# GPU SSL Certificate Handler for OMEGA Pro AI GPU Service

set -e

SSL_DIR="/app/ssl"
LOG_FILE="/app/logs/gpu-ssl-handler.log"
GPU_LOG_FILE="/app/logs/gpu-service.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] GPU-SSL: $1" | tee -a "$LOG_FILE"
}

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

log "Starting GPU SSL handler for OMEGA GPU service"

# GPU availability check
check_gpu() {
    if command -v nvidia-smi >/dev/null 2>&1; then
        GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
        log "Found $GPU_COUNT GPU(s)"
        nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits | while read line; do
            log "GPU: $line"
        done
        return 0
    else
        log "WARNING: nvidia-smi not found - GPU may not be available"
        return 1
    fi
}

# Initialize GPU environment
init_gpu_env() {
    log "Initializing GPU environment"
    
    # Set CUDA environment variables
    export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
    export NVIDIA_VISIBLE_DEVICES="${NVIDIA_VISIBLE_DEVICES:-all}"
    
    # Create CUDA cache directories
    mkdir -p /app/cache/cuda /app/cache/torch /app/cache/transformers
    
    # Check GPU availability
    if check_gpu; then
        log "GPU environment initialized successfully"
        
        # Test CUDA availability with Python
        python3 -c "
import torch
import sys
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
else:
    print('WARNING: CUDA not available')
    sys.exit(1)
" 2>&1 | tee -a "$LOG_FILE"
        
    else
        log "ERROR: GPU initialization failed"
        exit 1
    fi
}

# SSL certificate setup for GPU service
setup_ssl_for_gpu() {
    log "Setting up SSL for GPU service"
    
    # Check if SSL certificates exist
    if [[ -f "$SSL_DIR/cert.pem" && -f "$SSL_DIR/key.pem" ]]; then
        log "SSL certificates found - configuring GPU service SSL"
        
        # Verify certificate validity
        if openssl x509 -in "$SSL_DIR/cert.pem" -checkend 86400 -noout >/dev/null 2>&1; then
            log "SSL certificate is valid for GPU service"
        else
            log "WARNING: SSL certificate expires soon for GPU service"
        fi
        
        # Set proper permissions for GPU service
        chmod 644 "$SSL_DIR/cert.pem"
        chmod 600 "$SSL_DIR/key.pem"
        
        # Create GPU service SSL configuration
        cat > "$SSL_DIR/gpu_ssl_config.py" << 'EOF'
# GPU Service SSL Configuration
import ssl
import os

SSL_DIR = "/app/ssl"

def get_ssl_context():
    """Create SSL context for GPU service"""
    if os.path.exists(f"{SSL_DIR}/cert.pem") and os.path.exists(f"{SSL_DIR}/key.pem"):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(f"{SSL_DIR}/cert.pem", f"{SSL_DIR}/key.pem")
        
        # Security settings
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # Internal service communication
        
        return context
    return None

SSL_CONTEXT = get_ssl_context()
SSL_ENABLED = SSL_CONTEXT is not None
EOF
        
        log "GPU service SSL configuration created"
        
    else
        log "SSL certificates not found - GPU service will run without SSL"
        
        # Create dummy SSL config
        cat > "$SSL_DIR/gpu_ssl_config.py" << 'EOF'
# GPU Service SSL Configuration (Disabled)
SSL_CONTEXT = None
SSL_ENABLED = False
EOF
    fi
}

# GPU memory monitoring
monitor_gpu_memory() {
    while true; do
        sleep 60  # Check every minute
        
        if command -v nvidia-smi >/dev/null 2>&1; then
            # Get GPU memory usage
            MEMORY_INFO=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits)
            
            while IFS=',' read -r used total; do
                used=$(echo "$used" | tr -d ' ')
                total=$(echo "$total" | tr -d ' ')
                
                if [[ -n "$used" && -n "$total" ]]; then
                    usage_percent=$((used * 100 / total))
                    
                    if [[ $usage_percent -gt 90 ]]; then
                        log "WARNING: GPU memory usage at ${usage_percent}% (${used}/${total} MB)"
                        
                        # Alert if webhook configured
                        if [[ -n "$WEBHOOK_URL" ]]; then
                            curl -X POST "$WEBHOOK_URL" \
                                -H "Content-Type: application/json" \
                                -d "{\"text\":\"GPU memory usage high: ${usage_percent}%\"}" \
                                >/dev/null 2>&1 || true
                        fi
                    elif [[ $usage_percent -gt 80 ]]; then
                        log "INFO: GPU memory usage at ${usage_percent}% (${used}/${total} MB)"
                    fi
                fi
            done <<< "$MEMORY_INFO"
        fi
    done
}

# Model preloading function
preload_models() {
    log "Starting model preloading for GPU service"
    
    python3 -c "
import sys
import os
sys.path.append('/app')

try:
    # Import OMEGA modules
    from modules import lstm_model, transformer_model
    from core import predictor
    
    print('Preloading LSTM model...')
    # Preload LSTM model
    lstm = lstm_model.LSTMModel()
    if hasattr(lstm, 'load_model'):
        lstm.load_model()
        print('LSTM model preloaded successfully')
    
    print('Preloading Transformer model...')
    # Preload Transformer model
    transformer = transformer_model.EnhancedLotteryTransformer()
    if hasattr(transformer, 'load_pretrained'):
        transformer.load_pretrained()
        print('Transformer model preloaded successfully')
    
    print('Initializing predictor...')
    # Initialize predictor
    pred = predictor.OmegaPredictor()
    print('Predictor initialized successfully')
    
    print('Model preloading completed')
    
except Exception as e:
    print(f'Model preloading failed: {e}')
    sys.exit(1)
" 2>&1 | tee -a "$LOG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log "Model preloading completed successfully"
    else
        log "WARNING: Model preloading failed - service will load models on demand"
    fi
}

# Health check for GPU service
gpu_health_check() {
    while true; do
        sleep 30  # Check every 30 seconds
        
        # Check if GPU service is responding
        if curl -f -s -k https://localhost:8001/health >/dev/null 2>&1 || \
           curl -f -s http://localhost:8001/health >/dev/null 2>&1; then
            # Service is healthy
            continue
        else
            log "WARNING: GPU service health check failed"
            
            # Check if GPU is still available
            if ! check_gpu >/dev/null 2>&1; then
                log "ERROR: GPU no longer available"
                exit 1
            fi
        fi
    done
}

# Initialize GPU environment
init_gpu_env

# Setup SSL for GPU service
setup_ssl_for_gpu

# Preload models in background
preload_models &
PRELOAD_PID=$!

# Start GPU memory monitoring in background
monitor_gpu_memory &
MONITOR_PID=$!

# Start GPU health monitoring in background
gpu_health_check &
HEALTH_PID=$!

log "GPU SSL handler initialized successfully"
log "Model preloading started (PID: $PRELOAD_PID)"
log "GPU memory monitoring started (PID: $MONITOR_PID)"
log "GPU health monitoring started (PID: $HEALTH_PID)"

# Keep the script running
trap "
    log 'Stopping GPU SSL handler'
    kill $PRELOAD_PID $MONITOR_PID $HEALTH_PID 2>/dev/null || true
    exit 0
" SIGTERM SIGINT

# Wait for signals
while true; do
    sleep 30
    
    # Check if SSL configuration still exists
    if [[ ! -f "$SSL_DIR/gpu_ssl_config.py" ]]; then
        log "ERROR: GPU SSL configuration missing!"
        setup_ssl_for_gpu
    fi
    
    # Log GPU status periodically
    if (( $(date +%s) % 300 == 0 )); then  # Every 5 minutes
        if command -v nvidia-smi >/dev/null 2>&1; then
            TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits)
            POWER=$(nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits)
            UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)
            
            log "GPU Status - Temperature: ${TEMP}°C, Power: ${POWER}W, Utilization: ${UTIL}%"
        fi
    fi
done