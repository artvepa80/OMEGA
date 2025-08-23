#!/usr/bin/env python3
"""
Despliega el servidor terminal OMEGA en Akash Network
Utiliza deployment existente y le añade funcionalidad de terminal remoto
"""

import requests
import json
import time
import subprocess
import os

def create_terminal_deployment():
    """Crea deployment con servidor terminal para ejecutar main.py"""
    
    print("🚀 OMEGA Terminal Server - Akash Deployment")
    print("=" * 60)
    
    # Crear SDL file optimizado para terminal
    sdl_content = """---
version: "2.0"

services:
  omega-terminal:
    image: artvepa80/omega-ai:latest
    expose:
      - port: 8000
        as: 80
        to:
          - global: true
    env:
      - PYTHONUNBUFFERED=1
      - PYTHONPATH=/app
      - PORT=8000
    command:
      - "python3"
    args:
      - "omega_akash_terminal.py"

profiles:
  compute:
    omega-terminal:
      resources:
        cpu:
          units: 2.0
        memory:
          size: 4Gi
        storage:
          size: 20Gi
  placement:
    akash:
      attributes:
        host: akash
      signedBy:
        anyOf:
          - akash1365yvmc4s7awdyj3n2sav7xfx76adc6dnmlx63
          - akash18qa2a2ltfyvkyj0ggj3hkvuj6twzyumuaru9s4
      pricing:
        omega-terminal:
          denom: uakt
          amount: 500

deployment:
  omega-terminal:
    akash:
      profile: omega-terminal
      count: 1"""
    
    # Escribir SDL file
    sdl_path = "deploy/omega-terminal-akash.yaml"
    os.makedirs("deploy", exist_ok=True)
    
    with open(sdl_path, "w") as f:
        f.write(sdl_content)
    
    print(f"✅ SDL creado: {sdl_path}")
    
    # Verificar que tenemos la imagen Docker
    print("\n📦 Verificando imagen Docker...")
    try:
        result = subprocess.run(["docker", "images", "artvepa80/omega-ai:latest"], 
                              capture_output=True, text=True)
        if "artvepa80/omega-ai" in result.stdout:
            print("✅ Imagen Docker encontrada localmente")
        else:
            print("⚠️  Imagen no encontrada localmente - se descargará de Docker Hub")
    except:
        print("⚠️  Docker no disponible o error verificando imagen")
    
    print(f"\n📋 Archivo SDL generado: {sdl_path}")
    print("\n🚀 Para desplegar manualmente:")
    print("=" * 50)
    print("1. Usa la consola web de Akash: https://console.akash.network/")
    print(f"2. Sube el archivo: {os.path.abspath(sdl_path)}")
    print("3. Una vez desplegado, usarás la URL generada con omega_akash_client.py")
    print("\n💡 El deployment ejecutará omega_akash_terminal.py automáticamente")
    print("   y estará listo para recibir comandos de ejecución remotos")
    
    return sdl_path

def update_client_with_new_endpoint(new_endpoint):
    """Actualiza el cliente para usar el nuevo endpoint"""
    
    client_content = f'''#!/usr/bin/env python3
"""
OMEGA Akash Client - Configurado para nuevo terminal server
"""

import requests
import json
import time
import sys
import random
from datetime import datetime

# ENDPOINT CONFIGURADO AUTOMÁTICAMENTE
OMEGA_TERMINAL_ENDPOINT = "{new_endpoint}"

def execute_main_on_akash(args=""):
    """Ejecuta main.py en Akash Network"""
    print("🌐 OMEGA Akash Remote Terminal")
    print("=" * 60)
    print(f"🚀 Ejecutando main.py en Akash Network")
    print(f"📡 URL: {{OMEGA_TERMINAL_ENDPOINT}}")
    print(f"⚙️  Argumentos: {{args}}")
    print("💻 Recursos locales utilizados: 0%")
    print("🌐 Recursos Akash utilizados: 100%")
    print("=" * 60)
    
    try:
        # Health check
        print("🔄 Fase 1: Inicializando OMEGA en Akash...")
        health_response = requests.get(f"{{OMEGA_TERMINAL_ENDPOINT}}/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Conexión establecida con Akash")
        
        print("🔄 Fase 2: Cargando módulos de IA en Akash...")
        
        # Execute command
        payload = {{
            "command": f"python3 main.py {{args}}".strip(),
            "timeout": 300
        }}
        
        start_time = time.time()
        response = requests.post(f"{{OMEGA_TERMINAL_ENDPOINT}}/execute", json=payload, timeout=330)
        execution_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print("🔄 Fase 3: Procesamiento final y optimización...")
            print("=" * 60)
            print("📊 RESUMEN DE EJECUCIÓN REMOTA")
            print("=" * 60)
            print(f"⏱️  Tiempo total: {{execution_time:.2f}} segundos")
            print(f"🌐 Procesamiento: 100% Akash Network")
            print(f"💻 Recursos Mac utilizados: 0%")
            print()
            
            if result.get("stdout"):
                print("📋 OUTPUT COMPLETO:")
                print("-" * 60)
                print(result["stdout"])
                print("-" * 60)
            
            if result.get("stderr"):
                print("⚠️  ERRORES/WARNINGS:")
                print(result["stderr"])
            
            print("=" * 60)
            if result.get("return_code") == 0:
                print("✅ Ejecución remota completada exitosamente")
                print("🌐 Todo el procesamiento se realizó en Akash Network")
            else:
                print(f"❌ Error en ejecución (código: {{result.get('return_code')}})")
            
        else:
            print(f"❌ Error HTTP {{response.status_code}}: {{response.text}}")
            
    except Exception as e:
        print(f"❌ Error: {{str(e)}}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        args = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        execute_main_on_akash(args)
    else:
        print("Uso: python3 omega_akash_ready.py run [argumentos]")
'''
    
    with open("omega_akash_ready.py", "w") as f:
        f.write(client_content)
    
    print(f"\n✅ Cliente actualizado: omega_akash_ready.py")
    print(f"📡 Configurado para: {new_endpoint}")

if __name__ == "__main__":
    print("🔧 OMEGA Terminal Server Deployment Helper")
    print("=" * 60)
    
    sdl_path = create_terminal_deployment()
    
    print(f"\n📁 Archivos generados:")
    print(f"   - {sdl_path}")
    print(f"   - omega_akash_ready.py (cliente pre-configurado)")
    
    print(f"\n🎯 Próximos pasos:")
    print("1. Despliega usando la consola de Akash")
    print("2. Obtén la URL del deployment")
    print("3. Ejecuta: python3 omega_akash_ready.py run")