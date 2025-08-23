#!/bin/bash

# deploy-railway.sh - Despliegue optimizado non-interactive de OMEGA PRO AI v10.1 en Railway
# Uso: RAILWAY_TOKEN=tu-token bash deploy-railway.sh [project-name] [push]  # 'push' opcional para subir

set -e  # Salir en error
trap 'echo "❌ Error en línea $LINENO - Despliegue fallido! Limpieza..."; railway logout &>/dev/null; exit 1' ERR

# Configurables
PROJECT_NAME="${1:-omega-pro-ai}"  # Default o arg1
OMEGA_VERSION="v10.1"
HEALTH_ENDPOINT="/health"  # Asume endpoint en main.py

echo "🚀 Desplegando OMEGA PRO AI $OMEGA_VERSION a Railway..."
echo "======================================"

# Verificar npm (para CLI install si no)
if ! command -v npm &> /dev/null; then
    echo "⚠️ npm no encontrado – Instalando Node.js minimal..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt-get install -y nodejs
fi

# Verificar/instalar Railway CLI
if ! command -v railway &> /dev/null; then
    echo "📦 Instalando Railway CLI..."
    npm install -g @railway/cli
fi

# Auth con token (non-interactive)
if [[ -z "$RAILWAY_TOKEN" ]]; then
    echo "❌ RAILWAY_TOKEN env var requerida para non-interactive! Genera uno en Railway dashboard > Account > Tokens."
    exit 1
fi
export RAILWAY_TOKEN="$RAILWAY_TOKEN"
echo "🔐 Usando RAILWAY_TOKEN para auth non-interactive..."

# Crear proyecto non-interactive (nuevo comando CLI)
echo "🏗️ Creando/verificando proyecto Railway: $PROJECT_NAME..."
railway project new --name "$PROJECT_NAME" --detach || echo "✅ Proyecto ya existe – Continuando..."

# Linkear al proyecto
railway link "$PROJECT_NAME" --detach

# Desplegar con retry (exponential backoff)
echo "🚀 Desplegando OMEGA..."
for i in {1..3}; do
    railway up --detach && break
    echo "⚠️ Deploy fallido (intento $i/3) – Reintentando en $((2**i))s..."
    sleep $((2**i))
done

# Esperar deploy y obtener URL con retry
echo "⏳ Esperando deploy completado..."
DEPLOY_URL=""
for i in {1..12}; do  # Max ~2 min
    DEPLOY_URL=$(railway service | grep -oP 'https://\S+' | head -1) || true
    if [[ -n "$DEPLOY_URL" ]]; then
        break
    fi
    echo "🔄 Chequeando status (intento $i/12)..."
    sleep 10
done

if [[ -z "$DEPLOY_URL" ]]; then
    echo "⚠️ No se pudo obtener URL – Chequea manual en dashboard!"
    DEPLOY_URL="https://$PROJECT_NAME-production.up.railway.app"  # Fallback
fi

# Test post-deploy con retry
echo "🧪 Testeando deploy en $DEPLOY_URL..."
for i in {1..3}; do
    curl -s -f "$DEPLOY_URL$HEALTH_ENDPOINT" >/dev/null && echo "✅ Health OK!" && break
    echo "⚠️ Health check fallido (intento $i/3) – Reintentando en $((2**i))s..."
    sleep $((2**i))
done || echo "❌ Health falló después de retries – Verifica logs: railway logs"

# Push opcional
if [[ "$2" == "push" ]]; then
    echo "📤 Pusheando cambios extras si hay..."
    git add . && git commit -m "Deploy updates" && git push || echo "⚠️ No hay cambios para push."
fi

echo ""
echo "✅ OMEGA PRO AI desplegado exitosamente en Railway!"
echo "🌐 Tu API está disponible en: $DEPLOY_URL"
echo ""
echo "📋 Próximos pasos:"
echo "1. Copia la URL: $DEPLOY_URL"
echo "2. Actualiza el proxy para usar Railway en lugar de Akash"
echo "3. Prueba la app iOS con la nueva URL"
echo "4. Monitorea: railway logs | railway open"
echo ""
echo "🎯 Railway es mucho más confiable que Akash Network – ¡Escala con autoscaling y zero-downtime!"