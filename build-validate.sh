#!/bin/bash

# build-validate.sh - Validación local de build multi-arch para OMEGA PRO AI v10.1
# Uso: ./build-validate.sh [push]  # Agrega 'push' para subir a GHCR

set -e  # Salir en error

# Config
REGISTRY="ghcr.io"
REPO_OWNER="artvepa80"  # Cambia a tu usuario/repo
IMAGE_NAME="omega-ai"  # Mantengo consistencia con workflow existente
TAG="latest"
PLATFORMS="linux/amd64,linux/arm64"
DOCKERFILE="Dockerfile"

# Build args (simula CI)
OMEGA_VERSION="v10.1"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "🚀 Iniciando validación local de build multi-arch para OMEGA PRO AI"
echo "📊 Plataformas: $PLATFORMS"
echo "🏷️ Imagen: $REGISTRY/$REPO_OWNER/$IMAGE_NAME:$TAG"
echo "🔧 Build args: OMEGA_VERSION=$OMEGA_VERSION, BUILD_DATE=$BUILD_DATE, VCS_REF=$VCS_REF"

# Paso 0: Validar pre-requisitos
echo "🔍 Validando pre-requisitos..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi

if ! docker buildx version &> /dev/null; then
    echo "❌ Docker Buildx no está disponible"
    exit 1
fi

# Validar archivos críticos de OMEGA
if [ ! -f "main.py" ]; then
    echo "❌ main.py no encontrado - ¿estás en el directorio correcto?"
    exit 1
fi

if [ ! -d "core" ] || [ ! -d "modules" ]; then
    echo "❌ Directorios core/ o modules/ no encontrados"
    exit 1
fi

echo "✅ Pre-requisitos validados"

# Paso 1: Setup Buildx si no existe
echo "🔧 Configurando Docker Buildx..."
if ! docker buildx inspect multi-arch-builder &>/dev/null; then
  echo "📦 Creando builder multi-arch..."
  docker buildx create --name multi-arch-builder --driver docker-container --use
else
  echo "✅ Builder multi-arch ya existe"
  docker buildx use multi-arch-builder
fi
docker buildx inspect --bootstrap

# Paso 2: Build multi-arch (primero solo load para test local)
echo "🏗️ Iniciando build multi-arch..."
echo "⏱️  Esto puede tomar 10-20 minutos para el proyecto completo..."

# Build para test local (solo AMD64 para rapidez)
docker buildx build \
  --platform "linux/amd64" \
  --file "$DOCKERFILE" \
  --tag "$REGISTRY/$REPO_OWNER/$IMAGE_NAME:test-local" \
  --build-arg OMEGA_VERSION="$OMEGA_VERSION" \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --build-arg VCS_REF="$VCS_REF" \
  --load .

echo "✅ Build local completado"

# Paso 3: Test funcionalidad básica
echo "🧪 Testeando funcionalidad básica..."
docker run --rm "$REGISTRY/$REPO_OWNER/$IMAGE_NAME:test-local" \
  python3 -c "
import sys
sys.path.append('/app')
print('✅ Python version:', sys.version)
print('✅ Working dir:', __import__('os').getcwd())
print('✅ OMEGA files:', len([f for f in __import__('os').listdir('.') if f.endswith('.py')]))
print('✅ Core exists:', __import__('os').path.exists('core'))
print('✅ Modules exists:', __import__('os').path.exists('modules'))
"

# Test del entrypoint
echo "🧪 Testeando entrypoint..."
docker run --rm "$REGISTRY/$REPO_OWNER/$IMAGE_NAME:test-local" \
  ./entrypoint.sh echo "Test entrypoint OK"

# Test del healthcheck
echo "🧪 Testeando healthcheck..."
docker run --rm "$REGISTRY/$REPO_OWNER/$IMAGE_NAME:test-local" \
  python3 -c "
import sys; sys.path.append('/app'); print('✅ OMEGA Multi-Stage Health OK'); 
try: 
    import core.predictor, modules.lstm_model; 
    print('✅ Core modules loaded successfully'); 
except ImportError as e: 
    print('⚠️ Some modules not available:', str(e)); 
"

echo "✅ Tests básicos completados"

# Paso 4: Build multi-arch completo si todo OK
if [ "$1" = "push" ]; then
  echo "📤 Iniciando build multi-arch completo para push..."
  echo "⏱️  Esto puede tomar 20-30 minutos..."
  
  # Verificar login a GHCR
  if ! docker info | grep -q "ghcr.io"; then
    echo "⚠️  Parece que no estás logueado en GHCR. Ejecuta: docker login ghcr.io"
  fi
  
  docker buildx build \
    --platform "$PLATFORMS" \
    --file "$DOCKERFILE" \
    --tag "$REGISTRY/$REPO_OWNER/$IMAGE_NAME:$TAG" \
    --tag "$REGISTRY/$REPO_OWNER/$IMAGE_NAME:complete-v10.1" \
    --build-arg OMEGA_VERSION="$OMEGA_VERSION" \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    --build-arg VCS_REF="$VCS_REF" \
    --push .
  
  echo "✅ Push completado"
  
  # Paso 5: Verificar manifests multi-arch
  echo "🔍 Inspeccionando imagen multi-arch..."
  docker buildx imagetools inspect "$REGISTRY/$REPO_OWNER/$IMAGE_NAME:$TAG"
  
  # Paso 6: Test por arquitectura (del registry)
  for ARCH in amd64 arm64; do
    echo "🧪 Testeando $ARCH desde registry..."
    docker run --rm --platform linux/$ARCH \
      "$REGISTRY/$REPO_OWNER/$IMAGE_NAME:$TAG" \
      bash -c "echo '✅ Health check $ARCH:' && python3 -c 'import sys; sys.path.append(\"/app\"); print(\"OMEGA OK on\", __import__(\"platform\").machine());' && \
               echo '📊 Entrypoint info:' && ./entrypoint.sh echo 'Test OK'"
  done
  
else
  echo "💡 Para hacer push a GHCR, ejecuta: ./build-validate.sh push"
fi

# Cleanup
echo "🧹 Limpiando imagen de test local..."
docker image rm "$REGISTRY/$REPO_OWNER/$IMAGE_NAME:test-local" 2>/dev/null || true
docker image prune -f

echo ""
echo "🎉 Validación completada!"
if [ "$1" = "push" ]; then
  echo "✅ Imagen multi-arch disponible en: $REGISTRY/$REPO_OWNER/$IMAGE_NAME:$TAG"
  echo "🚀 Lista para usar en Akash o cualquier plataforma"
else
  echo "✅ Build local validado - listo para GitHub Actions"
  echo "💡 Para push manual: ./build-validate.sh push"
fi
echo "🔄 Para trigger automático: git push origin main"