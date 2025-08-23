#!/usr/bin/env python3
"""
OMEGA Akash Client - Universal
Compatible con deployment actual y terminal server completo
"""

import requests
import json
import sys
import time
from datetime import datetime

CURRENT_ENDPOINT = "http://3n7g0Gpdlpdkndfijdg6enauofo.ingress.bdl.computer"

def detect_server_type(endpoint_url):
    """Detect which type of server is running"""
    try:
        health_response = requests.get(f"{endpoint_url}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            service = health_data.get('service', '')
            endpoints = health_data.get('endpoints', [])
            
            if '/execute' in endpoints:
                return "terminal_server"
            elif 'OMEGA PRO AI' in service:
                return "api_server"
            else:
                return "unknown"
    except:
        pass
    
    # Try to access /execute to determine type
    try:
        response = requests.post(f"{endpoint_url}/execute", 
                               json={"command": "echo test"}, timeout=5)
        if response.status_code in [200, 500]:  # Server responds to /execute
            return "terminal_server"
    except:
        pass
    
    return "api_server"  # Default to API server

def use_api_server(endpoint_url, predictions=10):
    """Use current API server for predictions"""
    print("🌐 Usando API Server actual de Akash")
    print("=" * 50)
    print(f"📡 URL: {endpoint_url}")
    print(f"🎯 Predicciones solicitadas: {predictions}")
    print("=" * 50)
    
    try:
        payload = {
            "predictions": predictions,
            "ai_combinations": 25,
            "timeout": 120
        }
        
        start_time = time.time()
        response = requests.post(f"{endpoint_url}/predict", json=payload, timeout=150)
        execution_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Predicciones generadas en {execution_time:.2f}s")
            print(f"🤖 Modelo: {result.get('model', 'N/A')}")
            print(f"🌐 Plataforma: {result.get('platform', 'N/A')}")
            print(f"📊 Precisión baseline: {result.get('accuracy_baseline', 'N/A')}")
            print()
            
            predictions_list = result.get('predictions', [])
            
            # Si pedimos más predicciones de las que devuelve el servidor, hacer más llamadas
            if len(predictions_list) < predictions and predictions > 5:
                print(f"🔄 Servidor devolvió {len(predictions_list)}, generando {predictions - len(predictions_list)} adicionales...")
                
                remaining_needed = predictions - len(predictions_list)
                calls_needed = (remaining_needed + 4) // 5  # Redondear hacia arriba
                
                for call in range(calls_needed):
                    try:
                        additional_response = requests.post(f"{endpoint_url}/predict", json=payload, timeout=150)
                        if additional_response.status_code == 200:
                            additional_result = additional_response.json()
                            additional_preds = additional_result.get('predictions', [])
                            predictions_list.extend(additional_preds)
                            
                            # Limitar al número solicitado
                            if len(predictions_list) >= predictions:
                                predictions_list = predictions_list[:predictions]
                                break
                    except:
                        break
            
            if predictions_list:
                print("🏆 TOP PREDICCIONES DESDE AKASH:")
                print("-" * 50)
                
                for i, pred in enumerate(predictions_list[:predictions], 1):
                    numbers = pred.get('combination', pred.get('numbers', []))
                    score = pred.get('score', 0)
                    svi = pred.get('svi', 0)
                    
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
                    if i < len(predictions_list):
                        print()
                
                print("-" * 50)
                print("✅ Predicciones generadas exitosamente")
                print("🌐 100% procesamiento en Akash Network")
                return True
            else:
                print("⚠️  No se encontraron predicciones en la respuesta")
                return False
        else:
            print(f"❌ Error HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def use_terminal_server(endpoint_url, predictions=10, command=None):
    """Use terminal server for predictions or custom commands"""
    print("🖥️  Usando Terminal Server de Akash")
    print("=" * 50)
    print(f"📡 URL: {endpoint_url}")
    print("=" * 50)
    
    try:
        if command:
            # Execute custom command
            print(f"🔧 Ejecutando comando: {command}")
            payload = {
                "command": command,
                "timeout": 300
            }
            
            start_time = time.time()
            response = requests.post(f"{endpoint_url}/execute", json=payload, timeout=330)
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Comando ejecutado en {execution_time:.2f}s")
                print(f"🔄 Código de retorno: {result.get('return_code', 'N/A')}")
                
                stdout = result.get('stdout', '')
                if stdout:
                    print("📋 OUTPUT:")
                    print("-" * 30)
                    print(stdout)
                    print("-" * 30)
                
                stderr = result.get('stderr', '')
                if stderr:
                    print("⚠️  STDERR:")
                    print("-" * 30)
                    print(stderr)
                    print("-" * 30)
                
                return result.get('return_code', 1) == 0
            else:
                print(f"❌ Error HTTP {response.status_code}")
                return False
        else:
            # Generate predictions
            print(f"🎯 Generando {predictions} predicciones optimizadas...")
            payload = {
                "predictions": predictions,
                "ai_combinations": 25,
                "timeout": 180
            }
            
            start_time = time.time()
            response = requests.post(f"{endpoint_url}/predict", json=payload, timeout=210)
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Predicciones generadas en {execution_time:.2f}s")
                
                predictions_list = result.get('predictions', [])
                if predictions_list:
                    print()
                    print("🏆 TOP PREDICCIONES OMEGA TERMINAL:")
                    print("-" * 50)
                    
                    for i, pred in enumerate(predictions_list, 1):
                        numbers = pred.get('numbers', [])
                        confidence = pred.get('confidence', 0)
                        source = pred.get('source', 'unknown')
                        
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
                        print(f"    Confianza: {confidence:.3f} | Fuente: {source}")
                        if i < len(predictions_list):
                            print()
                    
                    print("-" * 50)
                    parameters = result.get('parameters', {})
                    print(f"⚙️  Configuración: {parameters.get('ai_combinations', 'N/A')} combinaciones AI")
                    print(f"🧠 IA Avanzada: {'✅' if parameters.get('advanced_ai') else '❌'}")
                    print(f"🎯 Meta-Learning: {'✅' if parameters.get('meta_learning') else '❌'}")
                    print("🌐 100% procesamiento en Akash Network")
                    return True
                else:
                    print("⚠️  No se encontraron predicciones")
                    return False
            else:
                print(f"❌ Error HTTP {response.status_code}")
                return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def generate_multijugada(endpoint_url, numeros, series, server_type):
    """Generate multijugada combinations with specified numbers and series"""
    import itertools
    import random
    
    try:
        num_count = int(numeros)
        if num_count not in [7, 9, 10]:
            print("❌ Error: Solo se permiten multijugadas de 7, 9 o 10 números")
            return
    except:
        print("❌ Error: Formato de números inválido")
        return
    
    print("🎲 MULTIJUGADA OMEGA - Akash Network")
    print("=" * 60)
    print(f"📊 Tipo: Multijugada de {num_count} números")
    print(f"📈 Series: {series}")
    print(f"🌐 Servidor: {endpoint_url}")
    print("=" * 60)
    print()
    
    # Calculate total combinations for each type
    total_combinations = {
        7: 7,      # C(7,6) = 7 combinations
        9: 84,     # C(9,6) = 84 combinations  
        10: 210    # C(10,6) = 210 combinations
    }
    
    combinations_per_series = total_combinations[num_count]
    total_predictions_needed = combinations_per_series * series
    
    print(f"📋 Generando {combinations_per_series} combinaciones por serie")
    print(f"🎯 Total de predicciones necesarias: {total_predictions_needed}")
    print()
    
    # Get base predictions from Akash
    print("🔄 Obteniendo predicciones base desde Akash...")
    
    try:
        if server_type == "terminal_server":
            # Use terminal server if available
            payload = {
                "predictions": min(50, total_predictions_needed),
                "ai_combinations": 50,
                "multijugada_mode": True,
                "numbers_count": num_count
            }
            response = requests.post(f"{endpoint_url}/predict", json=payload, timeout=180)
        else:
            # Use API server
            payload = {
                "predictions": min(50, total_predictions_needed),
                "ai_combinations": 30,
                "timeout": 120
            }
            response = requests.post(f"{endpoint_url}/predict", json=payload, timeout=150)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}")
            return
            
        result = response.json()
        base_predictions = result.get('predictions', [])
        
        if not base_predictions:
            print("❌ No se obtuvieron predicciones base")
            return
            
        print(f"✅ Obtenidas {len(base_predictions)} predicciones base")
        print()
        
        # Generate multijugada combinations for each series
        all_multijugadas = []
        
        for serie_num in range(1, series + 1):
            print(f"🔄 Generando Serie {serie_num}...")
            
            # Get a base prediction and extend it to required numbers
            base_idx = (serie_num - 1) % len(base_predictions)
            base_combo = base_predictions[base_idx].get('combination', 
                                                       base_predictions[base_idx].get('numbers', []))
            
            # Extend base combination to required number count
            multijugada_numbers = extend_to_multijugada(base_combo, num_count)
            
            # Generate all 6-number combinations from the multijugada numbers
            combinations = list(itertools.combinations(sorted(multijugada_numbers), 6))
            
            serie_data = {
                'serie': serie_num,
                'numeros_base': sorted(multijugada_numbers),
                'combinaciones': combinations,
                'total_combinaciones': len(combinations)
            }
            
            all_multijugadas.append(serie_data)
            
            print(f"✅ Serie {serie_num}: {len(combinations)} combinaciones generadas")
            print(f"🎯 Números base: {' - '.join([f'{n:2d}' for n in sorted(multijugada_numbers)])}")
            print()
        
        # Display results
        print("🏆 MULTIJUGADAS GENERADAS")
        print("=" * 60)
        
        total_combos = 0
        for serie_data in all_multijugadas:
            serie_num = serie_data['serie']
            numeros_base = serie_data['numeros_base']
            combinaciones = serie_data['combinaciones']
            
            print(f"📊 SERIE {serie_num}")
            print(f"🎯 Números base ({num_count}): {' - '.join([f'{n:2d}' for n in numeros_base])}")
            print(f"🎲 Combinaciones de 6: {len(combinaciones)}")
            print()
            
            # Show first few combinations as preview
            print("   Primeras combinaciones:")
            for i, combo in enumerate(combinaciones[:5]):
                combo_str = " - ".join([f"{n:2d}" for n in combo])
                print(f"   {i+1:3d}. [{combo_str}]")
            
            if len(combinaciones) > 5:
                print(f"   ... y {len(combinaciones) - 5} combinaciones más")
            print()
            
            total_combos += len(combinaciones)
        
        print("=" * 60)
        print(f"✅ MULTIJUGADA COMPLETADA")
        print(f"📊 Series generadas: {series}")
        print(f"🎯 Tipo: {num_count} números por serie")
        print(f"🎲 Total combinaciones: {total_combos}")
        print(f"💰 Costo estimado: ${total_combos * 1.5:.2f} USD")
        print("🌐 100% procesamiento en Akash Network")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def extend_to_multijugada(base_combo, target_count):
    """Extend a 6-number combination to target_count numbers"""
    import random
    
    # Start with base combination
    result = list(base_combo[:6])  # Ensure we start with 6 numbers
    
    # Add random numbers to reach target count
    available_numbers = [n for n in range(1, 40) if n not in result]
    
    needed = target_count - len(result)
    if needed > 0:
        additional = random.sample(available_numbers, min(needed, len(available_numbers)))
        result.extend(additional)
    
    return sorted(result[:target_count])

def main():
    if len(sys.argv) < 2:
        print("🌐 OMEGA Akash Client - Universal")
        print("=" * 40)
        print("Uso:")
        print(f"  python3 {sys.argv[0]} predict [cantidad]")
        print(f"  python3 {sys.argv[0]} multijugada [7|9|10] [series]")
        print(f"  python3 {sys.argv[0]} execute \"comando\"")
        print(f"  python3 {sys.argv[0]} health")
        print()
        print("Ejemplos:")
        print(f"  {sys.argv[0]} predict 5")
        print(f"  {sys.argv[0]} multijugada 7 2")
        print(f"  {sys.argv[0]} multijugada 9 1") 
        print(f"  {sys.argv[0]} multijugada 10 4")
        print(f"  {sys.argv[0]} execute \"python3 main.py --data-info\"")
        print(f"  {sys.argv[0]} health")
        sys.exit(1)
    
    action = sys.argv[1]
    
    # Detect server type
    print("🔍 Detectando tipo de servidor...")
    server_type = detect_server_type(CURRENT_ENDPOINT)
    print(f"📡 Servidor detectado: {server_type}")
    print()
    
    if action == "health":
        try:
            response = requests.get(f"{CURRENT_ENDPOINT}/health", timeout=10)
            if response.status_code == 200:
                health = response.json()
                print("✅ Health Check OK")
                print(json.dumps(health, indent=2))
            else:
                print(f"❌ Health check failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
    
    elif action == "predict":
        predictions = 10
        if len(sys.argv) > 2:
            try:
                predictions = int(sys.argv[2])
            except:
                predictions = 10
        
        if server_type == "terminal_server":
            use_terminal_server(CURRENT_ENDPOINT, predictions)
        else:
            use_api_server(CURRENT_ENDPOINT, predictions)
    
    elif action == "multijugada":
        if len(sys.argv) < 3:
            print("❌ Error: Especifica el tipo de multijugada")
            print("Opciones: 7, 9, 10")
            sys.exit(1)
        
        numeros = sys.argv[2]
        series = 1
        if len(sys.argv) > 3:
            try:
                series = int(sys.argv[3])
                if series < 1 or series > 4:
                    series = 1
            except:
                series = 1
        
        generate_multijugada(CURRENT_ENDPOINT, numeros, series, server_type)
    
    elif action == "execute":
        if len(sys.argv) < 3:
            print("❌ Error: Especifica el comando a ejecutar")
            sys.exit(1)
        
        command = sys.argv[2]
        
        if server_type == "terminal_server":
            use_terminal_server(CURRENT_ENDPOINT, command=command)
        else:
            print("❌ Error: Comando execute no disponible en API server")
            print("💡 Actualiza a terminal server para usar /execute")
            print("   Ejecuta: ./update-to-terminal-server.sh")
            sys.exit(1)
    
    else:
        print(f"❌ Acción desconocida: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()