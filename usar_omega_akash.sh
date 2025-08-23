#!/bin/bash

# OMEGA PRO AI v10.1 - Sistema Completo en Akash
# ==============================================

URL="https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win"

show_header() {
    clear
    echo "🚀 OMEGA PRO AI v10.1 - Menú Interactivo"
    echo "========================================"
    echo "🌐 URL: $URL"
    echo "⚡ Estado: Activo en Akash Network"
    echo "💻 Recursos Mac: 0% | 🌐 Recursos Akash: 100%"
    echo "========================================"
}

# Función para generar predicciones
generate_predictions() {
    echo ""
    echo "🎯 ¿Cuántas predicciones quieres generar?"
    echo "1) 5 predicciones rápidas"
    echo "2) 10 predicciones estándar" 
    echo "3) 25 predicciones completas"
    echo "4) Cantidad personalizada"
    echo ""
    read -p "Selecciona (1-4): " pred_choice
    
    case $pred_choice in
        1) python3 omega_akash_client.py predict 5 ;;
        2) python3 omega_akash_client.py predict 10 ;;
        3) python3 omega_akash_client.py predict 25 ;;
        4) 
            read -p "Ingresa cantidad (1-50): " custom_num
            python3 omega_akash_client.py predict $custom_num
            ;;
        *) echo "❌ Opción inválida" ;;
    esac
    
    echo ""
    read -p "Presiona ENTER para continuar..."
}

# Función para multijugadas
generate_multijugada() {
    echo ""
    echo "🎲 MULTIJUGADAS OMEGA"
    echo "===================="
    echo "Selecciona el tipo de multijugada:"
    echo "1) 7 números (7 combinaciones)"
    echo "2) 9 números (84 combinaciones)"
    echo "3) 10 números (210 combinaciones)"
    echo ""
    read -p "Tipo de multijugada (1-3): " multi_choice
    
    case $multi_choice in
        1) numeros=7 ;;
        2) numeros=9 ;;
        3) numeros=10 ;;
        *) echo "❌ Opción inválida"; return ;;
    esac
    
    echo ""
    echo "📈 ¿Cuántas series deseas?"
    echo "1) 1 serie"
    echo "2) 2 series"
    echo "3) 3 series"
    echo "4) 4 series"
    echo ""
    read -p "Cantidad de series (1-4): " series_choice
    
    case $series_choice in
        1) series=1 ;;
        2) series=2 ;;
        3) series=3 ;;
        4) series=4 ;;
        *) echo "❌ Opción inválida"; return ;;
    esac
    
    echo ""
    echo "🚀 Generando multijugada de $numeros números con $series series..."
    python3 omega_akash_client.py multijugada $numeros $series
    
    echo ""
    read -p "Presiona ENTER para continuar..."
}

# Función para verificar estado
check_system() {
    echo ""
    echo "🔍 VERIFICANDO ESTADO DEL SISTEMA..."
    echo "======================================"
    python3 omega_akash_client.py health
    echo ""
    echo "📊 PRUEBA DE CONECTIVIDAD..."
    echo "=============================="
    curl -s "$URL/health" | python3 -m json.tool
    echo ""
    read -p "Presiona ENTER para continuar..."
}

# Función para ejecutar comandos avanzados
advanced_commands() {
    echo ""
    echo "🛠️  COMANDOS AVANZADOS"
    echo "===================="
    echo "1) Ejecutar omega_remote_executor.py"
    echo "2) Ejecutar omega_terminal_client.py"
    echo "3) Ejecutar main.py local"
    echo "4) Volver al menú principal"
    echo ""
    read -p "Selecciona (1-4): " adv_choice
    
    case $adv_choice in
        1) 
            echo "🚀 Ejecutando Remote Executor..."
            python3 omega_remote_executor.py run --ai-combinations 5 --advanced-ai
            ;;
        2) 
            read -p "¿Cuántas predicciones? (default 8): " num_pred
            num_pred=${num_pred:-8}
            echo "🔮 Ejecutando Terminal Client..."
            python3 omega_terminal_client.py predict $num_pred
            ;;
        3)
            echo "💻 Ejecutando main.py localmente..."
            python3 main.py
            ;;
        4) return ;;
        *) echo "❌ Opción inválida" ;;
    esac
    
    echo ""
    read -p "Presiona ENTER para continuar..."
}

# Función principal del menú
main_menu() {
    while true; do
        show_header
        echo ""
        echo "SELECCIONA UNA OPCIÓN:"
        echo "====================="
        echo "1) 🎲 Generar Predicciones OMEGA"
        echo "2) 🎰 Multijugadas (7, 9, 10 números)"
        echo "3) ⚡ Verificar Estado del Sistema"
        echo "4) 🛠️  Comandos Avanzados"
        echo "5) 📋 Mostrar URLs y Endpoints"
        echo "6) 🏃 Prueba Rápida (5 predicciones)"
        echo "7) 🚪 Salir"
        echo ""
        read -p "👉 Tu opción (1-7): " choice
        
        case $choice in
            1) generate_predictions ;;
            2) generate_multijugada ;;
            3) check_system ;;
            4) advanced_commands ;;
            5) show_endpoints ;;
            6) 
                echo "🏃 PRUEBA RÁPIDA..."
                python3 omega_akash_client.py predict 5
                read -p "Presiona ENTER para continuar..."
                ;;
            7) 
                echo "👋 Saliendo del sistema OMEGA..."
                echo "✅ Hasta luego!"
                exit 0
                ;;
            *) 
                echo "❌ Opción inválida. Usa 1-7."
                sleep 2
                ;;
        esac
    done
}

# Función para mostrar endpoints
show_endpoints() {
    echo ""
    echo "📋 INFORMACIÓN DEL SISTEMA"
    echo "=========================="
    echo "🌐 URL Principal: $URL"
    echo "🔗 Health Check: $URL/health"
    echo "🎯 Predicciones: $URL/predict"
    echo ""
    echo "COMANDOS DISPONIBLES:"
    echo "===================="
    echo "• python3 omega_akash_client.py predict [cantidad]"
    echo "• python3 omega_akash_client.py health"
    echo "• python3 omega_remote_executor.py run"
    echo "• python3 omega_terminal_client.py predict [cantidad]"
    echo ""
    read -p "Presiona ENTER para continuar..."
}

# Verificar archivos necesarios
if [ ! -f "omega_akash_client.py" ]; then
    echo "❌ Error: No se encuentra omega_akash_client.py"
    echo "💡 Asegúrate de estar en el directorio correcto"
    exit 1
fi

# Iniciar menú principal
main_menu