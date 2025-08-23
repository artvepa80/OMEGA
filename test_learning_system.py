#!/usr/bin/env python3
"""
🧪 Test del Sistema de Aprendizaje Automático
Prueba el sistema con los datos reales del 07/08/2025
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.omega_auto_learning import aprender_automaticamente
from modules.balanced_range_predictor import crear_predictor_balanceado
import pandas as pd
import json

def test_learning_system():
    """Prueba el sistema de aprendizaje con datos reales"""
    
    print("🧪 TESTEO DEL SISTEMA DE APRENDIZAJE AUTOMÁTICO")
    print("=" * 60)
    
    # Resultado oficial del 07/08/2025
    resultado_oficial = [29, 22, 7, 37, 23, 33]
    
    # Predicciones que hizo OMEGA (del archivo de predicciones)
    predicciones_070825 = [
        {"combination": [14, 16, 20, 33, 35, 36], "source": "200_analyzer_v2", "score": 1.312},
        {"combination": [14, 19, 20, 23, 31, 37], "source": "200_analyzer_v2", "score": 1.25},
        {"combination": [1, 16, 31, 38, 39, 40], "source": "200_analyzer_v2", "score": 1.25},
        {"combination": [19, 20, 27, 33, 35, 37], "source": "200_analyzer_v2", "score": 1.188},
        {"combination": [16, 19, 23, 30, 31, 39], "source": "200_analyzer_v2", "score": 1.188},
        {"combination": [14, 16, 19, 20, 22, 36], "source": "200_analyzer_v2", "score": 1.188},
        {"combination": [16, 19, 22, 27, 33, 40], "source": "200_analyzer_v2", "score": 1.125}
    ]
    
    print(f"📊 Resultado oficial: {' - '.join(map(str, sorted(resultado_oficial)))}")
    print(f"🤖 Predicciones a analizar: {len(predicciones_070825)}")
    print()
    
    # Ejecutar aprendizaje automático
    print("🧠 Ejecutando aprendizaje automático...")
    try:
        resultado_aprendizaje = aprender_automaticamente(
            resultado_oficial=resultado_oficial,
            predicciones=predicciones_070825,
            fecha="2025-08-07"
        )
        
        # Mostrar resultados
        print("\n✅ RESULTADOS DEL APRENDIZAJE:")
        print("-" * 40)
        
        performance = resultado_aprendizaje['performance_analysis']
        print(f"📈 Precisión general: {performance['precision_general']:.3f} ({performance['precision_general']*100:.1f}%)")
        print(f"📊 Mejora sobre azar: +{performance['mejora_sobre_azar']:.3f}")
        print(f"🎯 Total aciertos: {performance['total_aciertos']}/{performance['total_posibles']}")
        print(f"🧠 Score de aprendizaje: {resultado_aprendizaje['learning_score']:.3f}")
        
        print(f"\n🔍 ANÁLISIS DE NÚMEROS:")
        numeros_omitidos = resultado_aprendizaje['number_analysis']['numeros_omitidos']
        numeros_acertados = resultado_aprendizaje['number_analysis']['numeros_acertados']
        print(f"✅ Números acertados: {numeros_acertados}")
        print(f"❌ Números omitidos: {numeros_omitidos}")
        
        print(f"\n⚖️ ANÁLISIS DE SESGOS:")
        bias_analysis = resultado_aprendizaje['bias_analysis']
        print(f"🔢 Distribución por rangos predicha: {bias_analysis['distribucion_rangos_predichos']}")
        print(f"🎯 Distribución real del resultado: {bias_analysis['distribucion_rangos_resultado']}")
        print(f"📊 Sesgo hacia números altos: {'SÍ' if bias_analysis['sesgo_hacia_altos'] else 'NO'}")
        
        print(f"\n💡 RECOMENDACIONES:")
        for i, rec in enumerate(resultado_aprendizaje['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        # Mostrar ajustes de pesos
        print(f"\n🔧 AJUSTES DE PESOS DE MODELOS:")
        weight_adjustments = resultado_aprendizaje.get('weight_adjustments', {})
        for modelo, ajuste in weight_adjustments.items():
            cambio = "↗️" if ajuste['peso_nuevo'] > ajuste['peso_anterior'] else "↘️"
            print(f"   • {modelo}: {ajuste['peso_anterior']:.3f} → {ajuste['peso_nuevo']:.3f} {cambio}")
        
        return resultado_aprendizaje
        
    except Exception as e:
        print(f"❌ Error en el aprendizaje: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_balanced_predictor():
    """Prueba el predictor balanceado"""
    
    print(f"\n{'⚖️'*20}")
    print("⚖️ TESTEO DEL PREDICTOR BALANCEADO")
    print("⚖️" * 20)
    
    try:
        # Cargar datos históricos
        df = pd.read_csv("data/historial_kabala_github.csv")
        print(f"📊 Datos cargados: {len(df)} registros históricos")
        
        # Crear predictor balanceado
        predictor_balanceado = crear_predictor_balanceado(df)
        
        # Generar combinaciones de prueba
        combinaciones_balanceadas = predictor_balanceado.generar_combinaciones_balanceadas(
            cantidad=5, enforce_distribution=True
        )
        
        print(f"\n✅ Generadas {len(combinaciones_balanceadas)} combinaciones balanceadas:")
        
        for i, combo in enumerate(combinaciones_balanceadas, 1):
            nums = combo['combination']
            balance_info = combo['balance_info']
            distribucion = balance_info['distribucion']
            
            print(f"\n   {i}. {' - '.join(f'{n:02d}' for n in nums)}")
            print(f"      Balance: Bajo={distribucion['bajo']}, Medio={distribucion['medio']}, Alto={distribucion['alto']}")
            print(f"      Score: {combo['score']:.3f}")
        
        # Analizar el resultado real del 07/08/2025 con el predictor balanceado
        resultado_oficial = [29, 22, 7, 37, 23, 33]
        predicciones_originales = [
            {"combination": [14, 16, 20, 33, 35, 36], "source": "original"},
            {"combination": [14, 19, 20, 23, 31, 37], "source": "original"},
            {"combination": [1, 16, 31, 38, 39, 40], "source": "original"},
        ]
        
        print(f"\n📊 ANÁLISIS DE MEJORAS NECESARIAS:")
        analisis = predictor_balanceado.analizar_mejoras_necesarias(predicciones_originales)
        
        print(f"   • Distribución actual: {analisis['distribucion_actual']}")
        print(f"   • Necesita balance: {'SÍ' if analisis['necesita_balance'] else 'NO'}")
        print(f"   • Rango más subestimado: {analisis['rango_subestimado'][0]} ({analisis['rango_subestimado'][1]:.1%})")
        print(f"   • Rango más sobreestimado: {analisis['rango_sobreestimado'][0]} ({analisis['rango_sobreestimado'][1]:.1%})")
        
        return combinaciones_balanceadas
        
    except Exception as e:
        print(f"❌ Error en predictor balanceado: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    
    # Verificar estructura
    if not os.path.exists("data/historial_kabala_github.csv"):
        print("❌ ERROR: No se encontró el archivo de datos históricos")
        print("📁 Asegúrate de ejecutar desde el directorio raíz del proyecto")
        sys.exit(1)
    
    # Test 1: Sistema de aprendizaje automático
    resultado_learning = test_learning_system()
    
    # Test 2: Predictor balanceado  
    resultado_balanced = test_balanced_predictor()
    
    # Resumen final
    print(f"\n{'🎉'*20}")
    print("🎉 TESTEO COMPLETADO")
    print("🎉" * 20)
    
    if resultado_learning:
        print("✅ Sistema de aprendizaje automático: FUNCIONANDO")
        print(f"   • Learning score: {resultado_learning['learning_score']:.3f}")
    else:
        print("❌ Sistema de aprendizaje automático: ERROR")
    
    if resultado_balanced:
        print("✅ Predictor balanceado: FUNCIONANDO")
        print(f"   • Combinaciones generadas: {len(resultado_balanced)}")
    else:
        print("❌ Predictor balanceado: ERROR")
    
    print(f"\n🚀 Los sistemas están listos para mejorar OMEGA PRO AI")