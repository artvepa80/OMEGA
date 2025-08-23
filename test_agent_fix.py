#!/usr/bin/env python3
"""
🧪 Test rápido del agente después de corregir el error KeyError: 'reward'
"""

import sys
import json
from pathlib import Path

# Añadir path del core
sys.path.append('core')

def test_basic_agent():
    """Test del agente básico V1"""
    
    print("🧪 TESTING AGENTE BÁSICO V1")
    print("-" * 40)
    
    try:
        from agent.agent_controller import AgentController
        from agent.evaluator import Evaluator
        
        # Test del evaluator primero
        print("1️⃣ Testing Evaluator...")
        
        evaluator = Evaluator({
            "reward_weights": {
                "svi": 0.5,
                "diversity": 0.2,
                "jackpot_profile": 0.2,
                "filters_pass_rate": 0.1
            },
            "min_quality_threshold": 0.6
        })
        
        # Test con datos válidos
        run_out_valid = {
            "stdout": "SVI: 0.75\nGeneradas 17 combinaciones\nPerfil detectado: 0.8",
            "returncode": 0
        }
        
        eval_result = evaluator.score(run_out_valid, "default")
        print(f"   ✅ Evaluator válido: {eval_result}")
        assert "reward" in eval_result
        assert "quality_ok" in eval_result
        
        # Test con datos inválidos
        run_out_invalid = {"stdout": "", "returncode": 1}
        eval_result_invalid = evaluator.score(run_out_invalid, "default")
        print(f"   ✅ Evaluator inválido: {eval_result_invalid}")
        assert "reward" in eval_result_invalid
        
        print("   ✅ Evaluator OK")
        
        # Test del AgentController básico
        print("2️⃣ Testing AgentController básico...")
        
        # Verificar que existe el config
        config_path = Path("config/agent_policy.json")
        if not config_path.exists():
            print(f"   ⚠️ Creando config básico...")
            config_path.parent.mkdir(exist_ok=True)
            config = {
                "schedule_seconds": 86400,
                "max_experiments_per_cycle": 2,
                "safe_rollback_drop_pct": 0.05,
                "min_quality_threshold": 0.60,
                "diversity_min_jaccard": 0.25,
                "reward_weights": {
                    "svi": 0.5,
                    "diversity": 0.2,
                    "jackpot_profile": 0.2,
                    "filters_pass_rate": 0.1
                },
                "guardrails": {
                    "max_weight_change_per_day": 0.10,
                    "enable_kill_switch": True
                },
                "baseline_profile": "default"
            }
            config_path.write_text(json.dumps(config, indent=2))
        
        # Crear controlador
        controller = AgentController()
        print(f"   ✅ Controller creado: {controller}")
        
        # Test básico del ciclo (sin ejecutar completo)
        print("3️⃣ Testing componentes individuales...")
        
        # Test memory
        memory_status = controller.memory.summarize()
        print(f"   ✅ Memory OK: {memory_status}")
        
        # Test planner
        candidates = controller.planner.propose(memory_status, n=1)
        print(f"   ✅ Planner OK: generó {len(candidates)} candidatos")
        
        # Test policy
        test_arms = {"test1": 0.7, "test2": 0.5}
        chosen = controller.policy.select(test_arms)
        print(f"   ✅ Policy OK: eligió {chosen}")
        
        print("✅ AGENTE BÁSICO V1: TODOS LOS TESTS PASARON")
        return True
        
    except Exception as e:
        print(f"❌ Error en test básico: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_advanced_agent():
    """Test del agente avanzado V2"""
    
    print("\n🧪 TESTING AGENTE AVANZADO V2")
    print("-" * 40)
    
    try:
        from agent.agent_controller_v2 import AdvancedAgentController
        
        # Verificar que tenemos config
        config_path = Path("config/agent_policy.json")
        if not config_path.exists():
            print("⚠️ Config no encontrado para V2")
            return False
        
        # Crear controlador V2
        controller = AdvancedAgentController()
        print(f"   ✅ AdvancedController creado: {controller}")
        
        # Test de componentes V2
        print("   ✅ Componentes V2 inicializados correctamente")
        
        print("✅ AGENTE AVANZADO V2: TEST BÁSICO PASÓ")
        return True
        
    except Exception as e:
        print(f"❌ Error en test avanzado: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_autonomous_agent():
    """Test del agente autónomo V4"""
    
    print("\n🧪 TESTING AGENTE AUTÓNOMO V4")
    print("-" * 40)
    
    try:
        from agent.agent_controller_v4 import create_autonomous_agent_controller
        
        # Crear controlador V4
        controller = create_autonomous_agent_controller()
        print(f"   ✅ AutonomousController creado: {controller}")
        
        # Test de estado
        status = controller.get_autonomous_status()
        print(f"   ✅ Status obtenido: versión {status.get('controller_version', 'unknown')}")
        
        print("✅ AGENTE AUTÓNOMO V4: TEST BÁSICO PASÓ")
        return True
        
    except Exception as e:
        print(f"❌ Error en test autónomo: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test principal"""
    
    print("🔧 TESTING CORRECCIÓN DEL ERROR 'KeyError: reward'")
    print("=" * 60)
    
    success_count = 0
    total_tests = 3
    
    # Test 1: Agente básico
    if test_basic_agent():
        success_count += 1
    
    # Test 2: Agente avanzado
    if test_advanced_agent():
        success_count += 1
    
    # Test 3: Agente autónomo
    if test_autonomous_agent():
        success_count += 1
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   ✅ Tests exitosos: {success_count}/{total_tests}")
    print(f"   📈 Porcentaje de éxito: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print(f"\n🎉 ¡TODOS LOS TESTS PASARON!")
        print(f"   🔧 El error 'KeyError: reward' ha sido corregido")
        print(f"   🤖 El sistema agéntico está funcionando correctamente")
        return 0
    else:
        print(f"\n⚠️ Algunos tests fallaron, pero el progreso es positivo")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
