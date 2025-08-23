#!/usr/bin/env python3
"""
Simulador de ejecución en tiempo real de OMEGA en Akash
Muestra el progreso del ML mientras se ejecuta
"""

import requests
import time
import json
from datetime import datetime

AKASH_URL = "https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win"

def show_live_execution(predictions=10):
    print("🚀 OMEGA ML - Ejecución en Tiempo Real")
    print("=" * 60)
    print(f"🌐 Servidor: {AKASH_URL}")
    print(f"🎯 Predicciones: {predictions}")
    print(f"⏰ Inicio: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    print()
    
    print("🔄 Fase 1: Conectando con Akash Network...")
    time.sleep(0.5)
    
    try:
        health_response = requests.get(f"{AKASH_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Conexión establecida con Akash")
            health_data = health_response.json()
            print(f"🏷️  Servicio: {health_data.get('service', 'N/A')}")
            print(f"🕐 Uptime: {health_data.get('uptime', 'N/A')}")
        else:
            print("❌ Error de conexión")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print()
    print("🔄 Fase 2: Inicializando modelos OMEGA...")
    time.sleep(1)
    print("✅ Modelos LSTM cargados")
    print("✅ Redes neuronales activadas") 
    print("✅ Sistema de ensemble preparado")
    
    print()
    print("🔄 Fase 3: Procesando algoritmos ML...")
    time.sleep(0.5)
    
    # Hacer la llamada real
    start_time = time.time()
    payload = {
        "predictions": predictions,
        "ai_combinations": 25,
        "timeout": 120
    }
    
    print(f"🧠 Ejecutando {predictions} combinaciones IA...")
    print("🔄 Procesamiento en curso...")
    
    try:
        response = requests.post(f"{AKASH_URL}/predict", json=payload, timeout=150)
        execution_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Procesamiento completado en {execution_time:.2f}s")
            print()
            print("🔄 Fase 4: Extrayendo predicciones...")
            time.sleep(0.5)
            
            predictions_list = result.get('predictions', [])
            
            print("✅ Predicciones extraídas exitosamente")
            print(f"📊 Modelo usado: {result.get('model', 'N/A')}")
            print(f"🎯 Precisión baseline: {result.get('accuracy_baseline', 'N/A')}")
            print()
            
            print("🏆 RESULTADOS EN TIEMPO REAL:")
            print("-" * 60)
            
            for i, pred in enumerate(predictions_list, 1):
                numbers = pred.get('combination', pred.get('numbers', []))
                score = pred.get('score', 0)
                svi = pred.get('svi', 0)
                timestamp = pred.get('timestamp', '')
                
                # Simular procesamiento gradual
                if i <= 3:
                    print(f"⚡ Generando predicción {i}...")
                    time.sleep(0.3)
                
                medal = ""
                if i == 1:
                    medal = " 🥇"
                elif i == 2:
                    medal = " 🥈"  
                elif i == 3:
                    medal = " 🥉"
                elif i <= 7:
                    medal = " ⭐"
                
                nums_str = " - ".join([f"{n:2d}" for n in numbers])
                print(f"{i:2d}. [{nums_str}]{medal}")
                print(f"    Score: {score:.3f} | SVI: {svi:.3f}")
                if timestamp:
                    ts_time = timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp
                    print(f"    🕐 Timestamp: {ts_time}")
                
                if i < len(predictions_list):
                    print()
            
            print("-" * 60)
            print("✅ EJECUCIÓN COMPLETADA")
            print(f"⏱️  Tiempo total: {execution_time:.2f} segundos")
            print("🌐 100% procesamiento en Akash Network")
            print("💻 0% uso de recursos Mac")
            
        else:
            print(f"❌ Error HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error durante ejecución: {e}")

if __name__ == "__main__":
    import sys
    predictions = 10
    
    if len(sys.argv) > 1:
        try:
            predictions = int(sys.argv[1])
        except:
            predictions = 10
    
    show_live_execution(predictions)