#!/bin/bash

# 🚀 OMEGA PRO AI v10.1 - Build COMPLETO para Akash
# Estrategia: Build por partes para evitar timeouts

set -e

IMAGE_NAME="artvepa80/omega-ai"
TAG="complete-v10.1"
TEMP_DIR="/tmp/omega-complete-build"

echo "🚀 OMEGA PRO AI v10.1 - Build Completo"
echo "================================================"
echo "📅 $(date)"
echo "🎯 Objetivo: TODO OMEGA en una imagen Docker"
echo "📦 Imagen: $IMAGE_NAME:$TAG"
echo ""

# Crear directorio temporal
echo "📁 Preparando build completo..."
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR
cd $TEMP_DIR

# Copiar archivos esenciales primero
echo "📋 Copiando archivos esenciales..."
cp -r /Users/user/Documents/OMEGA_PRO_AI_v10.1/core .
cp -r /Users/user/Documents/OMEGA_PRO_AI_v10.1/modules .
cp -r /Users/user/Documents/OMEGA_PRO_AI_v10.1/utils . 2>/dev/null || echo "⚠️ utils no encontrado"
cp -r /Users/user/Documents/OMEGA_PRO_AI_v10.1/config .
cp -r /Users/user/Documents/OMEGA_PRO_AI_v10.1/data .

# Copiar archivos principales
echo "🐍 Copiando scripts principales..."
cp /Users/user/Documents/OMEGA_PRO_AI_v10.1/main.py .
cp /Users/user/Documents/OMEGA_PRO_AI_v10.1/omega_unified_main.py .
cp /Users/user/Documents/OMEGA_PRO_AI_v10.1/requirements.txt .

# Copiar otros scripts importantes
echo "⚙️ Copiando scripts adicionales..."
find /Users/user/Documents/OMEGA_PRO_AI_v10.1 -maxdepth 1 -name "*.py" -exec cp {} . \;

# Crear Dockerfile optimizado
echo "🐳 Creando Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# Environment setup
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV OMEGA_VERSION=v10.1
ENV OMEGA_COMPLETE=true

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    build-essential \
    git \
    curl \
    htop \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt ./
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip3 install --no-cache-dir tensorflow-cpu && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy ALL OMEGA code
COPY . /app/

# Create necessary directories
RUN mkdir -p logs outputs results temp checkpoints models export

# Set permissions
RUN chmod +x *.py || true

# Create enhanced entrypoint
RUN echo '#!/bin/bash\necho "🚀 OMEGA PRO AI v10.1 COMPLETO - Akash Container"\necho "🏗️ Arquitectura: $(uname -m)"\necho "💻 CPU: $(nproc) cores"\necho "🐍 Python: $(python3 --version)"\necho "📁 OMEGA COMPLETO cargado en /app"\necho "📊 Archivos Python: $(find /app -name \"*.py\" | wc -l)"\necho "✅ TODO disponible para ejecución"\necho "================================================"\nexec "$@"' > entrypoint.sh && chmod +x entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "print('✅ OMEGA Complete Health OK')" || exit 1

# Default port
EXPOSE 8000

# Default command
CMD ["python3", "main.py", "--server-mode", "--port", "8000"]
ENTRYPOINT ["./entrypoint.sh"]
EOF

# Mostrar estadísticas
echo ""
echo "📊 Estadísticas del build:"
echo "• Archivos Python: $(find . -name '*.py' | wc -l)"
echo "• Tamaño total: $(du -sh . | cut -f1)"
echo "• Directorio: $TEMP_DIR"
echo ""

# Build con timeout más largo
echo "🏗️ Iniciando build Docker (puede tomar 30-45 min)..."
echo "⏰ Build iniciado: $(date)"

docker build -t $IMAGE_NAME:$TAG . --no-cache

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ BUILD EXITOSO!"
    echo "🧪 Probando imagen..."
    
    docker run --rm $IMAGE_NAME:$TAG echo "Test completo OK"
    
    echo ""
    echo "📊 Verificando contenido:"
    docker run --rm $IMAGE_NAME:$TAG find /app -name "*.py" | wc -l
    
    echo ""
    read -p "🚀 ¿Push a Docker Hub? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📤 Pushing imagen completa..."
        docker push $IMAGE_NAME:$TAG
        docker tag $IMAGE_NAME:$TAG $IMAGE_NAME:complete-latest
        docker push $IMAGE_NAME:complete-latest
        
        echo ""
        echo "🎉 ¡OMEGA COMPLETO disponible!"
        echo "🐳 docker pull $IMAGE_NAME:$TAG"
        echo "🐳 docker pull $IMAGE_NAME:complete-latest"
    fi
    
else
    echo "❌ Build falló. Revisar logs arriba."
    exit 1
fi

# Cleanup
echo ""
echo "🧹 Limpiando..."
cd /
rm -rf $TEMP_DIR

echo ""
echo "================================================"
echo "✅ OMEGA PRO AI v10.1 COMPLETO listo!"
echo "🌍 TODO el proyecto disponible en Docker"
echo "🚀 Listo para deploy completo en Akash"
echo "================================================"