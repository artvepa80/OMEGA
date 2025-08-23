#!/usr/bin/env python3
"""
🧪 Test Akash Execution - Prueba rápida del endpoint
"""

import requests
import json

# Configuración
AKASH_URL = "https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win"
API_KEY = "ac.sk.production.a16cbf***c4cad7"

def test_environment():
    """Prueba la verificación del entorno"""
    
    print("🧪 PROBANDO VERIFICACIÓN DE ENTORNO EN AKASH")
    print("=" * 60)
    
    url = f"{AKASH_URL}/execute"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "command": "python3 verify_akash_environment.py",
        "args": []
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Respuesta exitosa:")
            print(json.dumps(result, indent=2))
            
            # Verificar si está en Akash
            env_info = result.get("environment", {})
            environment = env_info.get("environment", "")
            
            if "AKASH" in environment:
                print("\n🚀 ¡CONFIRMADO! Se está ejecutando en AKASH")
            else:
                print(f"\n🏠 Se está ejecutando localmente: {environment}")
                
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_omega_command():
    """Prueba un comando OMEGA simple"""
    
    print("\n🎯 PROBANDO COMANDO OMEGA SIMPLE")
    print("=" * 60)
    
    url = f"{AKASH_URL}/execute"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "command": "python3 run_main_full_output.py",
        "args": ["--top_n", "3"]  # Solo 3 números para prueba rápida
    }
    
    try:
        print("⏳ Ejecutando comando OMEGA (esto puede tomar unos minutos)...")
        response = requests.post(url, headers=headers, json=payload, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Comando ejecutado exitosamente!")
            print(f"⏱️  Tiempo: {result.get('execution_time', 0):.2f}s")
            print(f"🎯 Output (primeras líneas):")
            
            output = result.get("output", "")
            lines = output.split('\n')[:10]  # Primeras 10 líneas
            for line in lines:
                print(f"   {line}")
                
            if len(output.split('\n')) > 10:
                print("   ... (output truncado)")
                
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 OMEGA AKASH EXECUTION TEST")
    print("=" * 60)
    
    # Test 1: Verificar entorno
    test_environment()
    
    # Test 2: Comando OMEGA
    test_omega_command()
    
    print("\n✅ Pruebas completadas!")
    print("\nPara usar el executor completo, ejecuta:")
    print("python3 execute_on_akash.py")