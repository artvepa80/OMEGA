#!/usr/bin/env python3
"""
🚀 Test directo de Akash - Sin menú interactivo
"""

import requests
import json
import time

AKASH_URL = "https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win"

def test_health():
    """Test health endpoint"""
    print("🔍 VERIFICANDO ESTADO DE AKASH")
    print("=" * 50)
    
    try:
        response = requests.get(f"{AKASH_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Deployment activo y saludable")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"⚠️ Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_predictions():
    """Test predictions endpoint"""
    print("\n🎯 EJECUTANDO PREDICCIONES OMEGA EN AKASH")
    print("=" * 50)
    
    try:
        start_time = time.time()
        
        payload = {"numbers": 8}
        response = requests.post(
            f"{AKASH_URL}/predict",
            json=payload,
            timeout=60
        )
        
        execution_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ PREDICCIONES GENERADAS EXITOSAMENTE")
            print(f"⏱️ Tiempo de ejecución: {execution_time:.2f}s")
            print(f"🎲 Predicciones generadas: {len(data.get('predictions', []))}")
            print(f"🏆 Precisión baseline: {data.get('accuracy_baseline', 'N/A')}")
            print(f"🚀 Plataforma: {data.get('platform', 'Akash Network')}")
            print(f"🤖 Modelo: {data.get('model', 'N/A')}")
            
            print("\n📊 PRIMERAS 5 PREDICCIONES:")
            predictions = data.get('predictions', [])
            for i, pred in enumerate(predictions[:5], 1):
                combination = pred.get('combination', [])
                score = pred.get('score', 0)
                svi = pred.get('svi', 0)
                print(f"{i:2}. {combination} (Score: {score:.3f}, SVI: {svi:.3f})")
            
            print(f"\n🌍 ¡CONFIRMADO! EJECUTÁNDOSE EN AKASH NETWORK")
            print(f"🎯 Source: {predictions[0].get('source', 'unknown') if predictions else 'N/A'}")
            return True
            
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 OMEGA AKASH DIRECT TEST")
    print("=" * 60)
    
    # Test 1: Health check
    health_ok = test_health()
    
    # Test 2: Predictions
    if health_ok:
        predictions_ok = test_predictions()
        
        if predictions_ok:
            print("\n✅ TODAS LAS PRUEBAS EXITOSAS!")
            print("🌍 Tu OMEGA está corriendo perfectamente en Akash Network")
            
            print("\n📋 COMANDOS EQUIVALENTES:")
            print("- Pipeline completo (8 números): ✅ Funcionando")
            print("- IA avanzada: curl con números: 10")  
            print("- Meta-learning: curl con números: 15")
            
        else:
            print("\n⚠️ Health OK pero predictions falló")
    else:
        print("\n❌ No se pudo conectar al deployment")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()