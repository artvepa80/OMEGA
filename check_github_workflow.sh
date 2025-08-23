#!/bin/bash

# 🚀 OMEGA PRO AI v10.1 - GitHub Workflow Checker
# Verifica el estado del workflow de GitHub Pro Multi-Arch

echo "🔍 Verificando GitHub Workflow..."
echo "================================================"

REPO_URL="https://github.com/artvepa80/-Users-user-Documents-OMEGA_PRO_AI_v10.1"
WORKFLOW_FILE="build-omega-multiarch.yml"

echo "📁 Repositorio: $REPO_URL"
echo "⚡ Workflow: $WORKFLOW_FILE"
echo ""

# Check if GitHub CLI is available
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI disponible"
    
    echo ""
    echo "🔄 Listando workflows disponibles..."
    gh workflow list --repo "artvepa80/-Users-user-Documents-OMEGA_PRO_AI_v10.1"
    
    echo ""
    echo "🚀 Para ejecutar el workflow manualmente:"
    echo "gh workflow run build-omega-multiarch.yml --repo artvepa80/-Users-user-Documents-OMEGA_PRO_AI_v10.1"
    
    echo ""
    echo "📊 Para ver el estado del último run:"
    echo "gh run list --workflow=build-omega-multiarch.yml --repo artvepa80/-Users-user-Documents-OMEGA_PRO_AI_v10.1"
    
else
    echo "⚠️ GitHub CLI no disponible"
    echo "Instálalo con: brew install gh"
    echo ""
fi

echo ""
echo "📖 Pasos manuales:"
echo "1. Ve a: $REPO_URL/actions"
echo "2. Busca '🚀 Build OMEGA Multi-Arch (GitHub Pro)'"
echo "3. Click 'Run workflow' si no se ejecutó automáticamente"
echo "4. Espera ~15-20 minutos para el build completo"
echo ""

echo "🎯 Qué esperar:"
echo "- ✅ Build AMD64 + ARM64"
echo "- ✅ Push a GitHub Container Registry"
echo "- ✅ Generar SDL de Akash automáticamente"
echo "- ✅ Artifact con omega-akash-github-pro.yaml"
echo ""

echo "🔗 Enlaces útiles:"
echo "- Actions: $REPO_URL/actions"
echo "- Registry: https://github.com/artvepa80/-Users-user-Documents-OMEGA_PRO_AI_v10.1/pkgs/container/omega-pro-ai"
echo "================================================"