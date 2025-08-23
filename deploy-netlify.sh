#!/bin/bash

echo "🚀 OMEGA Netlify Proxy Deployment"
echo "================================"

# Verificar si Netlify CLI está instalado
if ! command -v netlify &> /dev/null; then
    echo "📦 Instalando Netlify CLI..."
    npm install -g netlify-cli
fi

# Cambiar al directorio de Netlify
cd netlify/

echo "🔐 Iniciando sesión en Netlify..."
netlify login

echo "🚀 Desplegando OMEGA Proxy..."
netlify deploy --prod --dir=.

echo ""
echo "✅ OMEGA Proxy desplegado exitosamente en Netlify!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Copia la URL que te dio Netlify (algo como: https://omega-abc123.netlify.app)"
echo "2. Actualiza SimpleContentView.swift línea 190 con tu nueva URL"
echo "3. Recompila la app iOS"
echo ""
echo "🎯 Arquitectura implementada:"
echo "iOS App → Netlify (SSL válido) → Akash Network OMEGA API"