#!/usr/bin/env python3
"""
Setup Twilio + ngrok
--------------------
Script para configurar automáticamente el webhook de Twilio con ngrok
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

def check_ngrok_installed():
    """Verifica si ngrok está instalado"""
    try:
        result = subprocess.run(["ngrok", "version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def start_ngrok(port=8000):
    """Inicia ngrok en el puerto especificado"""
    try:
        print(f"🚀 Iniciando ngrok en puerto {port}...")
        proc = subprocess.Popen(
            ["ngrok", "http", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Esperar un poco para que ngrok se inicie
        time.sleep(3)
        
        # Obtener la URL pública de ngrok
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            tunnels = response.json()["tunnels"]
            
            for tunnel in tunnels:
                if tunnel["proto"] == "https":
                    public_url = tunnel["public_url"]
                    print(f"✅ ngrok URL: {public_url}")
                    return public_url, proc
                    
        except Exception as e:
            print(f"❌ Error obteniendo URL de ngrok: {e}")
            proc.terminate()
            return None, None
            
    except Exception as e:
        print(f"❌ Error iniciando ngrok: {e}")
        return None, None

def create_env_file():
    """Crea archivo .env con plantilla de configuración"""
    env_path = Path(".env")
    if env_path.exists():
        print("📄 Archivo .env ya existe")
        return
    
    template_path = Path("config/environment_template.txt")
    if template_path.exists():
        with open(template_path, "r") as f:
            template = f.read()
        
        with open(env_path, "w") as f:
            f.write(template)
        
        print("✅ Archivo .env creado desde template")
        print("🔧 Edita .env con tus credenciales de Twilio")
    else:
        print("❌ Template no encontrado en config/environment_template.txt")

def show_twilio_config(webhook_url):
    """Muestra las configuraciones necesarias para Twilio Console"""
    print("\n" + "="*60)
    print("🔧 CONFIGURACIÓN TWILIO CONSOLE")
    print("="*60)
    print("\n1. Ve a tu Twilio Console > Phone Numbers > Manage > Active numbers")
    print("2. Selecciona tu número de Twilio")
    print("3. En la sección 'Messaging', configura:")
    print(f"   📱 Webhook URL: {webhook_url}/webhooks/twilio/sms")
    print("   📝 HTTP Method: POST")
    print("\n4. Para WhatsApp Sandbox (si usas):")
    print("   - Ve a Messaging > Try it out > WhatsApp Sandbox")
    print(f"   - Configura 'When a message comes in': {webhook_url}/webhooks/twilio/sms")
    print("   - Method: POST")
    print("\n5. Credenciales necesarias en tu .env:")
    print("   - TWILIO_ACCOUNT_SID (desde Console > Account Dashboard)")
    print("   - TWILIO_AUTH_TOKEN (desde Console > Account Dashboard)")
    print("   - TWILIO_FROM_NUMBER (tu número de Twilio)")
    print("   - TWILIO_TO_NUMBER (+51972514235)")
    print("\n6. Comandos disponibles por SMS/WhatsApp:")
    print("   • 'predice' - Nueva predicción")
    print("   • 'estado' - Estado del sistema")
    print("   • 'help' - Lista de comandos")
    print("\n" + "="*60)

def main():
    print("🤖 OMEGA AI - Setup Twilio + ngrok")
    print("="*40)
    
    # Verificar ngrok
    if not check_ngrok_installed():
        print("❌ ngrok no está instalado")
        print("📥 Instala desde: https://ngrok.com/download")
        print("💻 macOS: brew install ngrok")
        sys.exit(1)
    
    # Crear .env si no existe
    create_env_file()
    
    # Iniciar ngrok
    public_url, ngrok_proc = start_ngrok(8000)
    
    if not public_url:
        print("❌ No se pudo iniciar ngrok")
        sys.exit(1)
    
    # Mostrar configuración
    show_twilio_config(public_url)
    
    print(f"\n🚀 Inicia tu API con: uvicorn api_interface:app --reload")
    print(f"🔗 Tu webhook: {public_url}/webhooks/twilio/sms")
    print("\n📱 Envía un mensaje a tu número Twilio para probar!")
    print("⌨️  Presiona Ctrl+C para detener ngrok...")
    
    try:
        # Mantener ngrok corriendo
        ngrok_proc.wait()
    except KeyboardInterrupt:
        print("\n👋 Deteniendo ngrok...")
        ngrok_proc.terminate()
        print("✅ ngrok detenido")

if __name__ == "__main__":
    main()

