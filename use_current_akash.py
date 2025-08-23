#!/usr/bin/env python3
"""
Script para ejecutar main.py en el deployment actual de Akash
"""

import requests
import json
import time

AKASH_URL = "https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win"

def execute_main_via_predict():
    print("🚀 Ejecutando main.py en Akash Network...")
    print(f"🌐 URL: {AKASH_URL}")
    print("=" * 50)
    
    try:
        payload = {
            "numbers": 8,
            "verbose": True,
            "full_execution": True
        }
        
        print("📤 Enviando request...")
        start_time = time.time()
        
        response = requests.post(
            f"{AKASH_URL}/predict",
            json=payload,
            timeout=300
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️  Tiempo: {execution_time:.2f}s")
        print(f"📊 Status: {response.status_code}")
        print("")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ RESPUESTA DE AKASH:")
            print("=" * 50)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🚀 OMEGA PRO AI v10.1 - Akash Client")
    print("=" * 50)
    execute_main_via_predict()
    print("")
    print("💡 Para output completo usa: ./deploy_omega_terminal.sh")

if __name__ == "__main__":
    main()