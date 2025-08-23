#!/bin/bash

echo "🚀 Iniciando OMEGA Proxy Server..."
echo "==============================================="

# Matar cualquier proceso en el puerto
echo "🔄 Limpiando puerto 8090..."
lsof -ti:8090 | xargs kill -9 2>/dev/null || true

# Esperar un momento
sleep 1

echo "🌐 Iniciando servidor en puerto 8090..."
echo "📱 iOS puede conectar a: http://localhost:8090"
echo "⏹️  Presiona Ctrl+C para detener"
echo ""

# Ejecutar el proxy
cd "$(dirname "$0")"
python3 simple_proxy.py