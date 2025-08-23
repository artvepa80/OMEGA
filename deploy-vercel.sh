#!/bin/bash

echo "🚀 OMEGA Vercel Proxy Deployment"
echo "================================"

# Verificar si Vercel CLI está instalado
if ! command -v vercel &> /dev/null; then
    echo "📦 Instalando Vercel CLI..."
    npm install -g vercel
fi

# Cambiar al directorio de Vercel
cd vercel/

echo "🔐 Iniciando sesión en Vercel..."
vercel login

echo "🚀 Desplegando OMEGA Proxy..."
vercel --prod

echo ""
echo "✅ OMEGA Proxy desplegado exitosamente!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Copia la URL que te dio Vercel"
echo "2. Actualiza SimpleContentView.swift con tu nueva URL"
echo "3. Recompila la app iOS"
echo ""
echo "🎯 Arquitectura implementada:"
echo "iOS App → Vercel (SSL válido) → Akash Network OMEGA API"