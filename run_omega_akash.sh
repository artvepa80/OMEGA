#!/bin/bash

# OMEGA AI - Akash Execution Script
# Ejecutar OMEGA desde Akash sin terminal local

echo "🚀 OMEGA PRO AI v10.1 - Akash Execution"
echo "======================================"

# Configuración
AKASH_URL="https://omega-api.akash.network"
JWT_TOKEN="${OMEGA_JWT_TOKEN:-your_token_here}"

# Función para ejecutar predicción
run_prediction() {
    local TOP_N=${1:-8}
    local PROFILE=${2:-aggressive}
    
    echo "🎯 Generando $TOP_N predicciones con perfil $PROFILE..."
    
    curl -X POST "$AKASH_URL/predict" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -d "{
            \"top_n\": $TOP_N,
            \"svi_profile\": \"$PROFILE\",
            \"enable_models\": [\"consensus\", \"lstm\", \"genetic\", \"clustering\"],
            \"enable_performance_monitoring\": true,
            \"export_formats\": [\"json\", \"csv\"],
            \"partial_hits\": false
        }" | jq '.'
}

# Función para ver estado
check_status() {
    echo "🔍 Verificando estado del sistema..."
    curl -s "$AKASH_URL/health" | jq '.'
    echo ""
    curl -s "$AKASH_URL/metrics" -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
}

# Menú interactivo
case "$1" in
    "predict")
        run_prediction $2 $3
        ;;
    "status")
        check_status
        ;;
    "quick")
        echo "⚡ Ejecución rápida (8 combinaciones)..."
        run_prediction 8 aggressive
        ;;
    "conservative")
        echo "🛡️ Ejecución conservadora (5 combinaciones)..."
        run_prediction 5 conservative
        ;;
    *)
        echo "Uso:"
        echo "  $0 quick              # 8 combinaciones aggressive"
        echo "  $0 conservative       # 5 combinaciones conservative"  
        echo "  $0 predict [n] [profile]  # N combinaciones con perfil"
        echo "  $0 status             # Ver estado del sistema"
        echo ""
        echo "Ejemplos:"
        echo "  $0 quick"
        echo "  $0 predict 10 moderate"
        echo "  $0 status"
        ;;
esac