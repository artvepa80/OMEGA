#!/bin/bash

# 🚀 OMEGA Build Monitor
# Monitorea el progreso del build completo

BUILD_START="Thu Aug 21 12:28:35 -05 2025"
IMAGE_NAME="artvepa80/omega-ai:complete-v10.1"

echo "🔄 Monitor Build OMEGA COMPLETO"
echo "================================================"
echo "🕐 Inicio: $BUILD_START"
echo "🎯 Imagen: $IMAGE_NAME"
echo "⏰ Timeout: 4 horas"
echo ""

while true; do
    clear
    echo "🚀 OMEGA PRO AI v10.1 - Build Monitor"
    echo "================================================"
    echo "🕐 Hora actual: $(date)"
    echo "⏱️  Tiempo transcurrido: Calculando..."
    echo ""
    
    # Check if build is still running
    if docker ps -q -f ancestor=python:3.11-slim >/dev/null 2>&1; then
        echo "🔄 Build en progreso..."
        echo "📊 Contenedores activos: $(docker ps -q | wc -l)"
    else
        echo "⏸️  No hay builds activos detectados"
    fi
    
    echo ""
    echo "🧪 Estado de imagen:"
    if docker images | grep -q "artvepa80/omega-ai.*complete-v10.1"; then
        echo "✅ Imagen complete-v10.1 encontrada!"
        
        echo ""
        echo "🎉 ¡BUILD COMPLETADO!"
        echo ""
        echo "📊 Verificando contenido..."
        docker run --rm $IMAGE_NAME find /app -name "*.py" | wc -l
        
        echo ""
        echo "🚀 Próximos pasos:"
        echo "1. Push a Docker Hub"
        echo "2. Actualizar deployment Akash"
        echo "3. Probar OMEGA funcionando"
        
        break
    else
        echo "⏳ Build aún en progreso..."
        echo "🔍 Imágenes disponibles:"
        docker images | grep artvepa80/omega-ai | head -3
    fi
    
    echo ""
    echo "💾 Espacio en disco:"
    df -h / | tail -1
    
    echo ""
    echo "📊 Uso de CPU/RAM:"
    top -l 1 | head -4 | tail -1
    
    echo ""
    echo "⏯️  Presiona Ctrl+C para salir"
    echo "🔄 Actualizando en 30 segundos..."
    echo "================================================"
    
    sleep 30
done

echo ""
echo "✅ Monitor finalizado"