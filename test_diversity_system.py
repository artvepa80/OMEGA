#!/usr/bin/env python3
"""
🧪 Test del Sistema de Diversidad y Anti-Sesgo OMEGA
Valida que todas las soluciones funcionen correctamente
"""

import sys
import os
import logging
from typing import List, Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_diversity_enhancer():
    """Test del Diversity Enhancer"""
    try:
        from modules.diversity_enhancer import enhance_prediction_diversity, validate_prediction_diversity
        
        # Crear predicciones de prueba con sesgos
        test_predictions = [
            {'combination': [1, 2, 3, 4, 5, 6], 'source': 'test1'},
            {'combination': [7, 8, 9, 10, 11, 12], 'source': 'test2'},
            {'combination': [13, 14, 15, 16, 17, 18], 'source': 'test3'},
            {'combination': [1, 3, 5, 7, 9, 11], 'source': 'test4'},  # Solo impares bajos
            {'combination': [2, 4, 6, 8, 10, 12], 'source': 'test5'}, # Solo pares bajos
        ]
        
        print("🧪 Testing Diversity Enhancer...")
        print(f"   📊 Predicciones originales: {len(test_predictions)}")
        
        # Validar diversidad antes
        diversity_before = validate_prediction_diversity(test_predictions)
        print(f"   📉 Cobertura antes: {diversity_before['coverage_score']:.1f}%")
        print(f"   ❌ Números omitidos: {len(diversity_before['missing_numbers'])}")
        
        # Aplicar mejora de diversidad
        enhanced_predictions = enhance_prediction_diversity(test_predictions)
        
        # Validar diversidad después
        diversity_after = validate_prediction_diversity(enhanced_predictions)
        print(f"   📈 Cobertura después: {diversity_after['coverage_score']:.1f}%")
        print(f"   ✅ Números omitidos: {len(diversity_after['missing_numbers'])}")
        
        success = diversity_after['coverage_score'] > diversity_before['coverage_score']
        print(f"   {'✅ PASS' if success else '❌ FAIL'}: Diversity Enhancer")
        
        return success
        
    except Exception as e:
        print(f"   ❌ FAIL: Diversity Enhancer - {e}")
        return False

def test_bias_detector():
    """Test del Bias Detector"""
    try:
        from modules.bias_detector import detect_prediction_biases, correct_prediction_biases
        
        # Crear predicciones con sesgos evidentes
        biased_predictions = [
            {'combination': [1, 2, 3, 4, 5, 6], 'source': 'biased_model'},
            {'combination': [1, 2, 3, 7, 8, 9], 'source': 'biased_model'},
            {'combination': [1, 2, 4, 5, 6, 10], 'source': 'biased_model'},
            {'combination': [32, 33, 34, 35, 36, 37], 'source': 'high_bias_model'}, # Sesgo alto
            {'combination': [38, 39, 40, 32, 33, 34], 'source': 'high_bias_model'}, # Sesgo alto
        ] * 10  # Repetir para crear patrones
        
        print("🔍 Testing Bias Detector...")
        print(f"   📊 Predicciones sesgadas: {len(biased_predictions)}")
        
        # Detectar sesgos
        bias_analysis = detect_prediction_biases(biased_predictions)
        biases_detected = len(bias_analysis.get('biases_detected', []))
        
        print(f"   🔍 Sesgos detectados: {biases_detected}")
        for bias in bias_analysis.get('biases_detected', []):
            print(f"      - {bias['type']}: {bias['description']}")
        
        # Corregir sesgos
        corrected_predictions = correct_prediction_biases(biased_predictions, bias_analysis)
        
        # Validar corrección
        bias_analysis_after = detect_prediction_biases(corrected_predictions)
        biases_after = len(bias_analysis_after.get('biases_detected', []))
        
        print(f"   🔧 Sesgos después corrección: {biases_after}")
        
        success = biases_detected > 0 and biases_after < biases_detected
        print(f"   {'✅ PASS' if success else '❌ FAIL'}: Bias Detector")
        
        return success
        
    except Exception as e:
        print(f"   ❌ FAIL: Bias Detector - {e}")
        return False

def test_integrated_system():
    """Test del sistema integrado"""
    try:
        from core.predictor import HybridOmegaPredictor
        
        print("🚀 Testing Sistema Integrado...")
        
        # Crear predictor con cantidad pequeña para test
        predictor = HybridOmegaPredictor(
            data_path="data/historial_kabala_github.csv",
            cantidad_final=20,  # Cantidad pequeña para test rápido
            perfil_svi="default"
        )
        
        # Ejecutar predicción con nuevo sistema
        predictions = predictor.run_all_models()
        
        print(f"   📊 Predicciones generadas: {len(predictions)}")
        
        if predictions:
            # Extraer números únicos
            all_numbers = []
            for pred in predictions:
                combination = pred.get('combination', [])
                if combination:
                    all_numbers.extend(combination)
            
            unique_numbers = len(set(all_numbers))
            coverage = unique_numbers / 40 * 100
            
            print(f"   🎯 Números únicos: {unique_numbers}/40")
            print(f"   📈 Cobertura: {coverage:.1f}%")
            
            # Verificar que no hay números completamente omitidos críticos
            present_numbers = set(all_numbers)
            missing_numbers = set(range(1, 41)) - present_numbers
            
            if missing_numbers:
                print(f"   ⚠️ Números omitidos: {sorted(list(missing_numbers))}")
            
            success = coverage >= 70 and len(missing_numbers) <= 5  # Criterios de éxito
            print(f"   {'✅ PASS' if success else '❌ FAIL'}: Sistema Integrado")
            
            return success
        else:
            print("   ❌ FAIL: No se generaron predicciones")
            return False
            
    except Exception as e:
        print(f"   ❌ FAIL: Sistema Integrado - {e}")
        return False

def test_number_coverage():
    """Test específico de cobertura de números críticos"""
    try:
        print("🎯 Testing Cobertura de Números Críticos...")
        
        # Simular resultado oficial problemático
        resultado_oficial = [12, 27, 1, 10, 13, 22]
        
        # Crear predicciones que omiten estos números
        problematic_predictions = [
            {'combination': [5, 15, 25, 30, 35, 40], 'source': 'model1'},
            {'combination': [2, 14, 16, 28, 32, 38], 'source': 'model2'},
            {'combination': [3, 7, 18, 24, 31, 39], 'source': 'model3'},
            {'combination': [4, 8, 19, 26, 33, 37], 'source': 'model4'},
            {'combination': [6, 9, 20, 29, 34, 36], 'source': 'model5'},
        ] * 5  # 25 predicciones total
        
        # Verificar que números críticos están omitidos
        all_numbers = []
        for pred in problematic_predictions:
            all_numbers.extend(pred.get('combination', []))
        
        present_numbers = set(all_numbers)
        missing_critical = [num for num in resultado_oficial if num not in present_numbers]
        
        print(f"   📊 Resultado oficial: {resultado_oficial}")
        print(f"   ❌ Números críticos omitidos inicialmente: {missing_critical}")
        
        # Aplicar corrección
        from modules.diversity_enhancer import enhance_prediction_diversity
        enhanced_predictions = enhance_prediction_diversity(problematic_predictions)
        
        # Verificar mejora
        all_enhanced_numbers = []
        for pred in enhanced_predictions:
            all_enhanced_numbers.extend(pred.get('combination', []))
        
        enhanced_present = set(all_enhanced_numbers)
        missing_after = [num for num in resultado_oficial if num not in enhanced_present]
        
        print(f"   ✅ Números críticos omitidos después: {missing_after}")
        
        success = len(missing_after) < len(missing_critical)
        print(f"   {'✅ PASS' if success else '❌ FAIL'}: Cobertura Números Críticos")
        
        return success
        
    except Exception as e:
        print(f"   ❌ FAIL: Cobertura Números Críticos - {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("🧪 OMEGA Diversity & Anti-Bias System Tests")
    print("=" * 60)
    
    tests = [
        ("Diversity Enhancer", test_diversity_enhancer),
        ("Bias Detector", test_bias_detector),
        ("Number Coverage", test_number_coverage),
        ("Integrated System", test_integrated_system),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ FAIL: {test_name} - {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print(f"\nRESULTADO FINAL: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡TODOS LOS TESTS PASARON! Sistema listo para uso.")
        return 0
    else:
        print("⚠️ Algunos tests fallaron. Revisar implementación.")
        return 1

if __name__ == "__main__":
    exit(main())