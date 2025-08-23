#!/bin/bash

# OMEGA Akash Terminal Setup
# Configura aliases para usar OMEGA desde cualquier lugar

OMEGA_DIR="/Users/user/Documents/OMEGA_PRO_AI_v10.1"
SHELL_RC=""

# Detectar shell
if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    SHELL_RC="$HOME/.bash_profile"
else
    SHELL_RC="$HOME/.profile"
fi

echo "🚀 Configurando OMEGA Terminal para $SHELL"
echo "📁 Directorio: $OMEGA_DIR"
echo "📝 Archivo de configuración: $SHELL_RC"

# Crear aliases
cat >> "$SHELL_RC" << 'EOF'

# ========================================
# OMEGA PRO AI v10.1 - Akash Terminal
# ========================================
export OMEGA_DIR="/Users/user/Documents/OMEGA_PRO_AI_v10.1"

# Aliases para OMEGA
alias omega-info="python3 $OMEGA_DIR/omega_terminal_client.py info"
alias omega-predict="python3 $OMEGA_DIR/omega_terminal_client.py predict"
alias omega-health="python3 $OMEGA_DIR/omega_terminal_client.py health"
alias omega-stress="python3 $OMEGA_DIR/omega_terminal_client.py stress"
alias omega-cd="cd $OMEGA_DIR"

# Función omega con parámetros
omega() {
    case $1 in
        "predict")
            python3 $OMEGA_DIR/omega_terminal_client.py predict ${2:-5}
            ;;
        "stress")
            python3 $OMEGA_DIR/omega_terminal_client.py stress ${2:-10}
            ;;
        "info"|"health")
            python3 $OMEGA_DIR/omega_terminal_client.py $1
            ;;
        "help"|"")
            echo "🌟 OMEGA PRO AI v10.1 - Comandos disponibles:"
            echo "  omega predict [cantidad]  - Generar predicciones (default: 5)"
            echo "  omega stress [iteraciones] - Prueba de estrés (default: 10)"
            echo "  omega info               - Información del sistema"
            echo "  omega health             - Estado de salud"
            echo "  omega help               - Esta ayuda"
            echo ""
            echo "🚀 Aliases rápidos:"
            echo "  omega-predict [cantidad]"
            echo "  omega-stress [iteraciones]"
            echo "  omega-info"
            echo "  omega-health"
            echo "  omega-cd                 - Ir al directorio OMEGA"
            ;;
        *)
            echo "❌ Comando no reconocido: $1"
            echo "💡 Usa 'omega help' para ver comandos disponibles"
            ;;
    esac
}

# Autocompletar para omega
if [[ "$SHELL" == *"zsh"* ]]; then
    compdef '_values "omega commands" predict stress info health help' omega
fi

EOF

echo "✅ Aliases agregados a $SHELL_RC"
echo ""
echo "🔄 Para aplicar los cambios, ejecuta:"
echo "   source $SHELL_RC"
echo ""
echo "🎯 Después podrás usar desde cualquier directorio:"
echo "   omega predict 10"
echo "   omega stress 20"
echo "   omega info"
echo "   omega health"
echo "   omega help"