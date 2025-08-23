#!/bin/bash

# 🚀 OMEGA PRO AI v10.1 - Build Monitor
# Monitorea el progreso del build multi-arquitectura

REPO_URL="https://github.com/artvepa80/-Users-user-Documents-OMEGA_PRO_AI_v10.1"
REGISTRY_URL="ghcr.io/artvepa80/omega-pro-ai"

echo "🔄 Monitoreando Build Multi-Arquitectura OMEGA..."
echo "================================================"
echo "📅 $(date)"
echo ""

while true; do
    clear
    echo "🚀 OMEGA PRO AI v10.1 - GitHub Pro Build Monitor"
    echo "================================================"
    echo "🕐 $(date '+%H:%M:%S')"
    echo ""
    
    echo "📊 Estado esperado del build:"
    echo "⏱️  Duración estimada: 15-20 minutos"
    echo "🏗️  Etapas:"
    echo "   1. ✅ Checkout código"
    echo "   2. 🔄 Setup Docker Buildx"
    echo "   3. 🔄 Build imagen AMD64"
    echo "   4. 🔄 Build imagen ARM64"
    echo "   5. 🔄 Test multi-arch"
    echo "   6. 🔄 Push a GHCR"
    echo "   7. 🔄 Generar SDL"
    echo "   8. 🔄 Upload artifacts"
    echo ""
    
    echo "🔗 URLs importantes:"
    echo "• Actions: $REPO_URL/actions"
    echo "• Registry: https://github.com/artvepa80/-Users-user-Documents-OMEGA_PRO_AI_v10.1/pkgs/container/omega-pro-ai"
    echo ""
    
    # Test if image is available
    echo "🧪 Probando disponibilidad de imagen..."
    if docker manifest inspect $REGISTRY_URL:latest >/dev/null 2>&1; then
        echo "✅ Imagen multi-arch disponible en registry!"
        echo "📦 Para usar: docker pull $REGISTRY_URL:latest"
        
        echo ""
        echo "🎯 Manifest info:"
        docker manifest inspect $REGISTRY_URL:latest --verbose | head -20
        break
    else
        echo "⏳ Build en progreso... imagen aún no disponible"
    fi
    
    echo ""
    echo "⏯️  Presiona Ctrl+C para salir, monitoreando cada 30 segundos..."
    echo "================================================"
    
    sleep 30
done

echo ""
echo "🎉 ¡BUILD COMPLETADO!"
echo "🚀 Próximos pasos:"
echo "1. Descarga el artifact 'omega-akash-deployment' desde Actions"
echo "2. Deploya en Akash con el SDL generado"
echo "3. ¡Disfruta OMEGA corriendo en Akash Network!"
echo ""