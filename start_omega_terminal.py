#!/usr/bin/env python3
"""
Script para iniciar el servidor terminal en tu deployment existente de Akash
"""

import requests
import json
import time

def start_terminal_server(deployment_url):
    """Inicia el servidor terminal en el deployment existente"""
    
    print("🚀 Iniciando OMEGA Terminal Server en Akash")
    print("=" * 60)
    print(f"📡 Deployment: {deployment_url}")
    
    # Comando para ejecutar en el deployment remoto
    start_server_command = {
        "command": "cd /app && python3 omega_akash_terminal.py &",
        "timeout": 10
    }
    
    try:
        # Intentar ejecutar el servidor en background
        response = requests.post(
            f"{deployment_url}/execute",
            json=start_server_command,
            timeout=15
        )
        
        if response.status_code == 200:
            print("✅ Comando de inicio enviado")
            
            # Esperar un momento para que arranque
            print("⏳ Esperando que el servidor inicie...")
            time.sleep(5)
            
            # Verificar si el servidor está corriendo
            health_check = requests.get(f"{deployment_url}/health", timeout=10)
            
            if health_check.status_code == 200:
                print("✅ Servidor terminal iniciado correctamente")
                print(f"🌐 Disponible en: {deployment_url}")
                print("\n🎯 Ahora puedes ejecutar:")
                print("   python3 run_omega_akash.py run")
                return True
            else:
                print("⚠️  Servidor iniciado pero health check no disponible")
                return True
                
        else:
            print(f"❌ Error enviando comando: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Solución manual:")
        print("1. Accede al shell de tu deployment de Akash")
        print("2. Ejecuta: cd /app && python3 omega_akash_terminal.py")
        print("3. El servidor quedará disponible en puerto 8000")
        return False

def check_server_status(deployment_url):
    """Verifica si el servidor terminal ya está ejecutándose"""
    
    print(f"🔍 Verificando estado del servidor en {deployment_url}")
    
    try:
        # Verificar health endpoint
        response = requests.get(f"{deployment_url}/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Servidor terminal YA está ejecutándose")
            return True
        else:
            print("⚠️  Servidor no responde en /health")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar - servidor no está ejecutándose")
        return False
    except Exception as e:
        print(f"❌ Error verificando: {str(e)}")
        return False

if __name__ == "__main__":
    # Tu deployment existente
    deployment_url = "https://a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online"
    
    print("🔧 OMEGA Terminal Server Starter")
    print("=" * 50)
    
    # Verificar estado actual
    if check_server_status(deployment_url):
        print("\n🎯 El servidor ya está corriendo. Puedes ejecutar:")
        print("   python3 run_omega_akash.py run")
    else:
        print("\n🚀 Intentando iniciar servidor...")
        if start_terminal_server(deployment_url):
            print("\n🎯 Servidor iniciado. Ejecuta:")
            print("   python3 run_omega_akash.py run")
        else:
            print("\n❌ No se pudo iniciar automáticamente")
            print("   Sigue las instrucciones manuales arriba")