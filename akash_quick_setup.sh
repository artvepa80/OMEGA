#!/bin/bash
# 🚀 OMEGA Akash Quick Setup Script
# Configuración rápida para desplegar en Akash Network

set -e

echo "🌐 OMEGA PRO AI - Akash Network Setup"
echo "===================================="

# Instalar Akash CLI si no existe
if ! command -v akash &> /dev/null; then
    echo "📦 Instalando Akash CLI..."
    curl -sSfL https://raw.githubusercontent.com/akash-network/akash/main/install.sh | sh
    export PATH="$PATH:./bin"
    
    # Verificar instalación
    if command -v akash &> /dev/null; then
        echo "✅ Akash CLI instalado correctamente"
        akash version
    else
        echo "❌ Error instalando Akash CLI"
        exit 1
    fi
else
    echo "✅ Akash CLI ya está instalado"
    akash version
fi

# Configurar variables de red
echo "🔧 Configurando Akash Network..."
export AKASH_NET="https://raw.githubusercontent.com/akash-network/net/main/mainnet"
export AKASH_VERSION="$(curl -s https://api.github.com/repos/akash-network/akash/releases/latest | jq -r '.tag_name')"
export AKASH_CHAIN_ID="$(curl -s "$AKASH_NET/chain-id.txt")"
export AKASH_NODE="$(curl -s "$AKASH_NET/rpc-nodes.txt" | head -1)"

echo "📋 Configuración de red:"
echo "  • Chain ID: $AKASH_CHAIN_ID"
echo "  • Node: $AKASH_NODE"
echo "  • Version: $AKASH_VERSION"

# Crear archivo de variables de entorno
cat > akash_env.sh << EOF
#!/bin/bash
# OMEGA Akash Environment Variables
export AKASH_NET="$AKASH_NET"
export AKASH_VERSION="$AKASH_VERSION" 
export AKASH_CHAIN_ID="$AKASH_CHAIN_ID"
export AKASH_NODE="$AKASH_NODE"
EOF

echo "💾 Variables guardadas en akash_env.sh"
echo ""
echo "📝 Próximos pasos:"
echo "1. Crear wallet: akash keys add omega-wallet"
echo "2. Obtener tokens AKT (100-500 AKT recomendados)"
echo "3. Ejecutar: python3 scripts/deploy_akash.py deploy --wallet omega-wallet"
echo ""
echo "🎯 ¡Listo para desplegar OMEGA en Akash!"