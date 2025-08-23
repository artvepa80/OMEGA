#!/usr/bin/env python3
"""
🧪 Test Optimal Weights Implementation
Verifica que los pesos óptimos estén correctamente implementados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from omega_integrated_system import OMEGA_OPTIMAL_WEIGHTS, OmegaIntegratedSystem

def test_optimal_weights_implementation():
    """Prueba que los pesos óptimos estén correctamente implementados"""
    
    print("🧪" + "="*50)
    print("   TEST OPTIMAL WEIGHTS IMPLEMENTATION")
    print("   'Verificando implementación de pesos óptimos'")
    print("="*52)
    
    # 1. Verificar que los pesos óptimos están definidos correctamente
    print("\n🔍 VERIFICANDO PESOS ÓPTIMOS DEFINIDOS...")
    
    expected_weights = {
        'partial_hit_score': 0.412,
        'jackpot_score': 0.353, 
        'entropy_fft_score': 0.118,
        'pattern_score': 0.118,
        'positional_score': 0.000
    }
    
    print("✅ Pesos esperados:")
    for component, weight in expected_weights.items():
        print(f"   {component}: {weight} ({weight*100:.1f}%)")
    
    print("\n✅ Pesos implementados:")
    for component, weight in OMEGA_OPTIMAL_WEIGHTS.items():
        print(f"   {component}: {weight} ({weight*100:.1f}%)")
    
    # 2. Verificar que los pesos coinciden
    weights_match = True
    print("\n🔍 COMPARANDO PESOS...")
    
    for component, expected_weight in expected_weights.items():
        actual_weight = OMEGA_OPTIMAL_WEIGHTS.get(component)
        if actual_weight != expected_weight:
            print(f"❌ {component}: esperado {expected_weight}, actual {actual_weight}")
            weights_match = False
        else:
            print(f"✅ {component}: {actual_weight} ✓")
    
    # 3. Verificar que los pesos suman 1.0 (aproximadamente)
    print("\n🔍 VERIFICANDO SUMA DE PESOS...")
    total_weight = sum(OMEGA_OPTIMAL_WEIGHTS.values())
    expected_total = 1.0
    
    print(f"   Suma total: {total_weight}")
    print(f"   Esperado:   {expected_total}")
    
    if abs(total_weight - expected_total) < 0.001:
        print("✅ Suma de pesos correcta")
        sum_correct = True
    else:
        print("❌ Suma de pesos incorrecta")
        sum_correct = False
    
    # 4. Crear muestra de datos para test funcional
    print("\n🔍 TEST FUNCIONAL CON DATOS DUMMY...")
    
    # Crear datos dummy para test
    import pandas as pd
    import numpy as np
    
    dummy_historical = pd.DataFrame({
        'bolilla_1': np.random.randint(1, 41, 100),
        'bolilla_2': np.random.randint(1, 41, 100),
        'bolilla_3': np.random.randint(1, 41, 100),
        'bolilla_4': np.random.randint(1, 41, 100),
        'bolilla_5': np.random.randint(1, 41, 100),
        'bolilla_6': np.random.randint(1, 41, 100)
    })
    
    # Crear datos jackpot dummy
    dummy_jackpots = pd.DataFrame({
        'numeros': ['[1,2,3,4,5,6]', '[7,8,9,10,11,12]']
    })
    
    # Guardar archivos dummy temporalmente
    dummy_historical.to_csv('test_historical.csv', index=False)
    dummy_jackpots.to_csv('test_jackpots.csv', index=False)
    
    try:
        # Crear sistema con datos dummy
        system = OmegaIntegratedSystem('test_historical.csv', 'test_jackpots.csv')
        
        # Crear combinaciones dummy para test
        dummy_combinations = [
            {
                'combination': [1, 2, 3, 4, 5, 6],
                'partial_hit_score': 0.8,
                'jackpot_score': 0.7,
                'entropy_fft_score': 0.6,
                'pattern_score': 0.5,
                'positional_score': 0.4
            }
        ]
        
        # Test de cálculo de ranking
        ranked = system._calculate_final_rankings(dummy_combinations)
        
        if ranked and len(ranked) > 0:
            final_score = ranked[0]['final_score']
            weights_used = ranked[0]['weights_used']
            
            print(f"✅ Test funcional exitoso")
            print(f"   Score final calculado: {final_score:.4f}")
            print(f"   Pesos utilizados: {weights_used}")
            
            # Verificar que se usaron los pesos óptimos
            if weights_used == OMEGA_OPTIMAL_WEIGHTS:
                print("✅ Pesos óptimos aplicados correctamente en cálculo")
                functional_test_passed = True
            else:
                print("❌ Pesos aplicados no coinciden con los óptimos")
                functional_test_passed = False
        else:
            print("❌ Test funcional falló - no se generaron rankings")
            functional_test_passed = False
            
    except Exception as e:
        print(f"❌ Test funcional falló: {e}")
        functional_test_passed = False
    
    finally:
        # Limpiar archivos dummy
        try:
            os.remove('test_historical.csv')
            os.remove('test_jackpots.csv')
        except:
            pass
    
    # 5. Resultado final
    print("\n" + "="*52)
    print("📊 RESULTADO DEL TEST")
    print("="*52)
    
    if weights_match and sum_correct and functional_test_passed:
        print("🎉 ✅ TODOS LOS TESTS PASARON")
        print("   Los pesos óptimos están correctamente implementados")
        print("   Performance esperada: +29.9% (23.6% → 30.7%)")
        return True
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        if not weights_match:
            print("   - Pesos no coinciden con los esperados")
        if not sum_correct:
            print("   - Suma de pesos incorrecta")
        if not functional_test_passed:
            print("   - Test funcional falló")
        return False

if __name__ == "__main__":
    success = test_optimal_weights_implementation()
    if success:
        print("\n🚀 SISTEMA LISTO CON PESOS ÓPTIMOS")
    else:
        print("\n🛠️ REVISAR IMPLEMENTACIÓN")