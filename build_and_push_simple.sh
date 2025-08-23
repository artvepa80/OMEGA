#!/bin/bash

# 🚀 OMEGA PRO AI v10.1 - Build & Push Simple
# Build directo sin complicaciones

set -e

IMAGE_NAME="artvepa80/omega-ai"
TAG="github-pro-v10.1"

echo "🚀 OMEGA PRO AI v10.1 - Build Directo"
echo "================================================"
echo "📅 $(date)"
echo ""

echo "🏗️ Building imagen Docker..."
echo "📦 Imagen: $IMAGE_NAME:$TAG"
echo ""

# Build simple con Dockerfile existente
docker build \
  -f Dockerfile.github \
  -t $IMAGE_NAME:$TAG \
  -t $IMAGE_NAME:latest \
  .

echo ""
echo "✅ Build completado!"
echo ""

echo "🧪 Probando imagen..."
docker run --rm $IMAGE_NAME:$TAG /app/entrypoint.sh echo "Test OK"

echo ""
echo "📤 Pushing to Docker Hub..."
echo "⚠️  Necesitas estar logueado: docker login"
echo ""

read -p "¿Push a Docker Hub ahora? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker push $IMAGE_NAME:$TAG
    docker push $IMAGE_NAME:latest
    
    echo ""
    echo "🎉 ¡ÉXITO! Imagen disponible:"
    echo "docker pull $IMAGE_NAME:$TAG"
    echo "docker pull $IMAGE_NAME:latest"
    
    # Crear SDL inmediatamente
    echo ""
    echo "📝 Creando SDL de Akash..."
    
    cat > omega-akash-simple.yaml << EOF
version: "2.0"

services:
  omegaproaiv101:
    image: $IMAGE_NAME:latest
    command:
      - "bash"
      - "-c"
      - "cd /app && python3 main.py --server-mode --port 8000"
    expose:
      - port: 8000
        as: 80
        to:
          - global: true
    env:
      - OMEGA_ENV=production
      - REAL_ALGORITHMS=true
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

    echo "✅ SDL creado: omega-akash-simple.yaml"
    echo ""
    echo "🚀 Para deployar en Akash:"
    echo "akash tx deployment create omega-akash-simple.yaml --from \$AKASH_FROM --node \$AKASH_NODE --chain-id \$AKASH_CHAIN_ID --gas-prices \$AKASH_GAS_PRICES -y"
    
else
    echo "📦 Imagen construida localmente:"
    echo "docker run -p 8000:8000 $IMAGE_NAME:$TAG"
fi

echo ""
echo "================================================"
echo "✅ OMEGA PRO AI v10.1 listo!"
echo "🐳 Imagen: $IMAGE_NAME:$TAG"
echo "🌍 Deploy: omega-akash-simple.yaml"
echo "================================================"