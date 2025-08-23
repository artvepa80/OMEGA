#!/usr/bin/env python3
"""
🚀 OMEGA Akash Remote Executor
Ejecuta comandos en tu deployment de Akash vía API
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# Configuración de tu deployment de Akash
AKASH_URL = "https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win"
API_KEY = "ac.sk.production.a16cbf***c4cad7"  # Tu API key

# Comandos disponibles
AVAILABLE_COMMANDS = {
    "1": {
        "name": "Pipeline completo (8 números)",
        "command": "python3 run_main_full_output.py",
        "args": ["--top_n", "8"]
    },
    "2": {
        "name": "IA avanzada (10 combinaciones)", 
        "command": "python3 run_main_full_output.py",
        "args": ["--ai-combinations", "10", "--advanced-ai"]
    },
    "3": {
        "name": "Meta-learning activo",
        "command": "python3 run_main_full_output.py", 
        "args": ["--meta-learning", "--enable-adaptive-learning"]
    },
    "4": {
        "name": "Debug completo con monitoreo",
        "command": "python3 run_main_full_output.py",
        "args": ["--enable-performance-monitoring", "--top_n", "8"]
    },
    "5": {
        "name": "Verificar entorno Akash",
        "command": "python3 verify_akash_environment.py",
        "args": []
    },
    "6": {
        "name": "Información del sistema",
        "command": "hostname && whoami && pwd",
        "args": []
    }
}

def execute_on_akash(command: str, args: list = None) -> Dict[Any, Any]:
    """Ejecuta un comando en Akash vía API"""
    
    url = f"{AKASH_URL}/execute"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "command": command,
        "args": args or []
    }
    
    print(f"🚀 Ejecutando en Akash: {command} {' '.join(args or [])}")
    print(f"🌐 URL: {url}")
    print("=" * 80)
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=600)
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout - El comando tomó más de 10 minutos")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None

def display_result(result: Dict[Any, Any]):
    """Muestra el resultado de la ejecución"""
    
    if not result:
        return
    
    print("\n" + "=" * 80)
    print("📊 RESULTADO DE LA EJECUCIÓN")
    print("=" * 80)
    
    # Información del entorno
    env_info = result.get("environment", {})
    print(f"🏠 Host: {env_info.get('hostname', 'unknown')}")
    print(f"👤 Usuario: {env_info.get('user', 'unknown')}")
    print(f"📁 Directorio: {env_info.get('cwd', 'unknown')}")
    print(f"🌍 Entorno: {env_info.get('environment', 'unknown')}")
    print(f"⏱️  Tiempo de ejecución: {result.get('execution_time', 0):.2f}s")
    print(f"✅ Éxito: {'Sí' if result.get('success') else 'No'}")
    
    print("\n" + "-" * 80)
    print("📄 OUTPUT:")
    print("-" * 80)
    print(result.get("output", "Sin output"))
    print("=" * 80)

def show_menu():
    """Muestra el menú de comandos disponibles"""
    
    print("🚀 OMEGA AKASH REMOTE EXECUTOR")
    print("=" * 50)
    print("Selecciona el comando a ejecutar:")
    print()
    
    for key, cmd in AVAILABLE_COMMANDS.items():
        print(f"{key}. {cmd['name']}")
        print(f"   {cmd['command']} {' '.join(cmd['args'])}")
        print()
    
    print("0. Salir")
    print("=" * 50)

def main():
    """Función principal"""
    
    while True:
        show_menu()
        
        try:
            choice = input("Ingresa tu opción (0-6): ").strip()
            
            if choice == "0":
                print("👋 ¡Hasta luego!")
                break
                
            if choice not in AVAILABLE_COMMANDS:
                print("❌ Opción inválida")
                continue
                
            # Obtener comando
            cmd_info = AVAILABLE_COMMANDS[choice]
            command = cmd_info["command"]
            args = cmd_info["args"]
            
            print(f"\n🔄 Ejecutando: {cmd_info['name']}")
            
            # Ejecutar en Akash
            start_time = time.time()
            result = execute_on_akash(command, args)
            total_time = time.time() - start_time
            
            if result:
                display_result(result)
            else:
                print("❌ No se pudo ejecutar el comando")
                
            print(f"\n⏱️  Tiempo total (incluyendo red): {total_time:.2f}s")
            print("\n" + "🔄" * 20)
            input("Presiona Enter para continuar...")
            
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            continue

if __name__ == "__main__":
    main()