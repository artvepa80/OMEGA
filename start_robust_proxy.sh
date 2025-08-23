#!/bin/bash

echo "🚀 Iniciando OMEGA Robust Proxy v2.0..."
echo "======================================="

# Matar procesos anteriores
echo "🔄 Limpiando procesos anteriores..."
pkill -f "python.*proxy" 2>/dev/null || true
lsof -ti:8090 | xargs kill -9 2>/dev/null || true

sleep 2

echo "🚀 Iniciando servidor robusto..."
echo "📱 Con auto-restart, retry logic y logging detallado"
echo "⏹️  Presiona Ctrl+C para detener"
echo ""

# Ejecutar el proxy robusto
cd "$(dirname "$0")"
python3 robust_proxy.py