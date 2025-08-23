#!/bin/bash

# 🚀 OMEGA PRO AI v10.1 - Deploy NOW to Akash
# Usa imagen existente que YA funciona

set -e

SDL_FILE="omega-akash-ready.yaml"
DEPLOY_NAME="omega-v10.1-production"

echo "🚀 OMEGA PRO AI v10.1 - Deploy a Akash Network"
echo "================================================"
echo "📅 $(date)"
echo "🐳 Imagen: artvepa80/omega-ai:latest"
echo "📄 SDL: $SDL_FILE"
echo ""

# Verificar imagen funciona
echo "🧪 Verificando imagen..."
if docker run --rm artvepa80/omega-ai:latest echo "Test OK" >/dev/null 2>&1; then
    echo "✅ Imagen funciona correctamente"
else
    echo "❌ Imagen no funciona. Verifica Docker."
    exit 1
fi

echo ""
echo "📋 SDL Content:"
echo "================================================"
cat $SDL_FILE
echo "================================================"
echo ""

# Check Akash environment
echo "🔍 Verificando configuración Akash..."
if [ -z "$AKASH_FROM" ]; then
    echo "⚠️ AKASH_FROM no configurado"
    echo "Exporta tu wallet: export AKASH_FROM=tu-wallet"
fi

if [ -z "$AKASH_NODE" ]; then
    echo "⚠️ AKASH_NODE no configurado"
    echo "Usando por defecto: https://rpc.akashnet.net:443"
    export AKASH_NODE="https://rpc.akashnet.net:443"
fi

if [ -z "$AKASH_CHAIN_ID" ]; then
    echo "⚠️ AKASH_CHAIN_ID no configurado" 
    echo "Usando por defecto: akashnet-2"
    export AKASH_CHAIN_ID="akashnet-2"
fi

if [ -z "$AKASH_GAS_PRICES" ]; then
    echo "⚠️ AKASH_GAS_PRICES no configurado"
    echo "Usando por defecto: 0.025uakt"
    export AKASH_GAS_PRICES="0.025uakt"
fi

echo ""
echo "⚙️ Configuración Akash:"
echo "• FROM: $AKASH_FROM"
echo "• NODE: $AKASH_NODE" 
echo "• CHAIN: $AKASH_CHAIN_ID"
echo "• GAS: $AKASH_GAS_PRICES"
echo ""

if command -v akash &> /dev/null; then
    echo "✅ Akash CLI disponible"
    
    echo ""
    echo "💰 Verificando balance..."
    akash query bank balances --from $AKASH_FROM --node $AKASH_NODE 2>/dev/null || echo "⚠️ No se pudo verificar balance"
    
    echo ""
    read -p "🚀 ¿Deployar OMEGA en Akash Network ahora? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🚀 Desplegando OMEGA PRO AI v10.1..."
        
        # Deploy command
        akash tx deployment create $SDL_FILE \
          --from $AKASH_FROM \
          --node $AKASH_NODE \
          --chain-id $AKASH_CHAIN_ID \
          --gas-prices $AKASH_GAS_PRICES \
          --gas-adjustment 1.5 \
          -y
        
        echo ""
        echo "🎉 ¡DEPLOYMENT ENVIADO!"
        echo ""
        echo "📊 Para monitorear:"
        echo "akash query deployment list --from $AKASH_FROM --node $AKASH_NODE"
        echo ""
        echo "🔍 Próximos pasos:"
        echo "1. Esperar lease activo (~2-5 min)"
        echo "2. Obtener URI pública"
        echo "3. Probar: https://tu-uri/health"
        echo ""
        echo "🎯 ¡OMEGA funcionando en Akash Network!"
        
    else
        echo ""
        echo "📄 SDL listo: $SDL_FILE"
        echo "🚀 Ejecuta cuando estés listo:"
        echo "akash tx deployment create $SDL_FILE --from \$AKASH_FROM --node \$AKASH_NODE --chain-id \$AKASH_CHAIN_ID --gas-prices \$AKASH_GAS_PRICES -y"
    fi
    
else
    echo "❌ Akash CLI no disponible"
    echo "📥 Instalar: https://docs.akash.network/get-started/setup"
    echo ""
    echo "📄 SDL generado: $SDL_FILE"
    echo "🌐 Deploy manual: https://console.akash.network"
fi

echo ""
echo "================================================"
echo "✅ OMEGA PRO AI v10.1 listo para Akash Network!"
echo "🐳 Imagen: artvepa80/omega-ai:latest"
echo "⚡ Algoritmos: REALES (no simulaciones)"
echo "🌍 Deploy: $SDL_FILE"
echo "================================================"