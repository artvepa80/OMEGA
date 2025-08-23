#!/bin/bash

# 🚀 OMEGA PRO AI v10.1 - Auto Deploy to Akash Network
# Deploys OMEGA using GitHub Pro built multi-arch image

set -e

REGISTRY_IMAGE="ghcr.io/artvepa80/omega-pro-ai:latest"
DEPLOYMENT_NAME="omega-github-pro"
SDL_FILE="omega-akash-github-pro.yaml"

echo "🚀 OMEGA PRO AI v10.1 - Akash Auto Deploy"
echo "================================================"
echo "📅 $(date)"
echo ""

# Check if image exists
echo "🔍 Verificando imagen multi-arch..."
if ! docker manifest inspect $REGISTRY_IMAGE >/dev/null 2>&1; then
    echo "❌ Imagen no disponible aún. Espera a que termine el build."
    echo "🔄 Ejecuta: ./monitor_build.sh para monitorear"
    exit 1
fi

echo "✅ Imagen multi-arch encontrada!"
echo ""

# Create optimized SDL for GitHub Pro image
echo "📝 Generando SDL optimizado..."
cat > $SDL_FILE << 'EOF'
version: "2.0"

services:
  omegaproaiv101:
    image: ghcr.io/artvepa80/omega-pro-ai:latest
    command:
      - "bash"
      - "-c" 
      - "cd /app && python3 main.py --server-mode --port 8000 --real-algorithms --github-pro"
    expose:
      - port: 8000
        as: 80
        to:
          - global: true
    env:
      - OMEGA_ENV=production
      - REAL_ALGORITHMS=true  
      - GITHUB_PRO=true
      - OMEGA_VERSION=v10.1
      - PYTHONUNBUFFERED=1
    resources:
      cpu:
        units: "8.0"
      memory:
        size: 17Gi
      storage:
        - size: 107Gi
          
profiles:
  compute:
    omegaproaiv101:
      resources:
        cpu:
          units: "8.0"
        memory:
          size: 17Gi
        storage:
          - size: 107Gi
  placement:
    dcloud:
      pricing:
        omegaproaiv101:
          denom: uakt
          amount: 2500

deployment:
  omegaproaiv101:
    dcloud:
      profile: omegaproaiv101
      count: 1
EOF

echo "✅ SDL creado: $SDL_FILE"
echo ""

# Display SDL contents
echo "📋 Contenido del SDL:"
echo "================================================"
cat $SDL_FILE
echo "================================================"
echo ""

# Check Akash CLI
if command -v akash &> /dev/null; then
    echo "✅ Akash CLI disponible"
    echo ""
    
    echo "🔄 Desplegando en Akash Network..."
    echo "⚠️  Asegúrate de tener fondos en tu wallet!"
    echo ""
    
    # Deploy command
    echo "🚀 Comando de deploy:"
    echo "akash tx deployment create $SDL_FILE \\"
    echo "  --from \$AKASH_FROM \\"
    echo "  --node \$AKASH_NODE \\"
    echo "  --chain-id \$AKASH_CHAIN_ID \\"
    echo "  --gas-prices \$AKASH_GAS_PRICES \\"
    echo "  --gas-adjustment \$AKASH_GAS_ADJUSTMENT \\"
    echo "  -y"
    echo ""
    
    read -p "¿Ejecutar deployment ahora? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        akash tx deployment create $SDL_FILE \
          --from $AKASH_FROM \
          --node $AKASH_NODE \
          --chain-id $AKASH_CHAIN_ID \
          --gas-prices $AKASH_GAS_PRICES \
          --gas-adjustment $AKASH_GAS_ADJUSTMENT \
          -y
        
        echo ""
        echo "🎉 ¡Deployment enviado!"
        echo "🔍 Consulta el estado con:"
        echo "akash query deployment list --from $AKASH_FROM"
    else
        echo "📄 SDL guardado como: $SDL_FILE"
        echo "🚀 Despliega manualmente cuando estés listo"
    fi
    
else
    echo "⚠️ Akash CLI no disponible"
    echo "📄 SDL guardado como: $SDL_FILE" 
    echo "🚀 Instala Akash CLI y despliega manualmente"
fi

echo ""
echo "🎯 Próximos pasos después del deployment:"
echo "1. Esperar lease activo (~2-5 minutos)"
echo "2. Obtener URI pública del deployment"
echo "3. Probar endpoint: https://uri-publica/health"
echo "4. ¡OMEGA funcionando en Akash Network!"
echo ""
echo "💡 Tips:"
echo "• Imagen optimizada para GitHub Pro (multi-arch)"
echo "• Algoritmos OMEGA reales (no simulaciones)"
echo "• SSL automático en Akash"
echo "• Escalado horizontal disponible"
echo "================================================"