#!/usr/bin/env python3
"""
🧪 TEST AGENTE BÁSICO - Plan-Act-Learn
Prueba el sistema agéntico básico sin ejecutar el ciclo completo
"""

import sys
import json
from pathlib import Path

# Añadir path del core
sys.path.append('core')

def test_agent_components():
    """Test de componentes individuales del agente"""
    
    print("🧪 TESTING AGENTE BÁSICO - FASE 1")
    print("=" * 50)
    
    try:
        # Test 1: Planner
        print("\n🔹 Testing Planner...")
        from agent.planner import Planner
        
        policy_cfg = {
            "baseline_profile": "default",
            "max_experiments_per_cycle": 3
        }
        
        planner = Planner(policy_cfg)
        state = {"recent_rewards": [0.7, 0.8, 0.6], "n": 3}
        proposals = planner.propose(state, n=2)
        
        assert len(proposals) == 2, f"Expected 2 proposals, got {len(proposals)}"
        assert all("ensemble_weights" in p for p in proposals), "Proposals missing ensemble_weights"
        
        print("✅ Planner: PASSED")
        
    except Exception as e:
        print(f"❌ Planner: FAILED - {e}")
        return False
    
    try:
        # Test 2: Memory
        print("\n🔹 Testing Memory...")
        from agent.memory import Memory
        
        test_memory_path = Path("test_memory.parquet")
        memory = Memory(test_memory_path)
        
        # Test logging
        test_cfg = {"test": "config"}
        test_run = {"returncode": 0, "stdout": "test"}
        test_eval = {"reward": 0.8, "quality_ok": True, "signals": {"svi": 0.8}}
        
        memory.log("test_sig", test_cfg, test_run, test_eval)
        
        # Test summarize
        summary = memory.summarize(last_k=10)
        assert "recent_rewards" in summary, "Summary missing recent_rewards"
        assert summary["n"] >= 1, "Summary should show at least 1 record"
        
        # Cleanup
        if test_memory_path.exists():
            test_memory_path.unlink()
        
        print("✅ Memory: PASSED")
        
    except Exception as e:
        print(f"❌ Memory: FAILED - {e}")
        return False
    
    try:
        # Test 3: Evaluator
        print("\n🔹 Testing Evaluator...")
        from agent.evaluator import Evaluator
        
        policy_cfg = {
            "reward_weights": {
                "svi": 0.5,
                "diversity": 0.2,
                "jackpot_profile": 0.2,
                "filters_pass_rate": 0.1
            },
            "min_quality_threshold": 0.6
        }
        
        evaluator = Evaluator(policy_cfg)
        
        # Test con stdout simulado
        test_run = {
            "returncode": 0,
            "stdout": "SVI: 0.75 Generadas Perfil detectado: 0.6 ✅ 17 combinaciones"
        }
        
        result = evaluator.score(test_run, "default")
        
        assert "reward" in result, "Result missing reward"
        assert "quality_ok" in result, "Result missing quality_ok"
        assert result["reward"] > 0, "Reward should be positive"
        
        print("✅ Evaluator: PASSED")
        
    except Exception as e:
        print(f"❌ Evaluator: FAILED - {e}")
        return False
    
    try:
        # Test 4: UCB1 Policy
        print("\n🔹 Testing UCB1 Policy...")
        from agent.policies.bandit import UCB1Policy
        
        policy = UCB1Policy()
        
        # Test con arms simulados
        arms = {
            "config_a": 0.8,
            "config_b": 0.6,
            "config_c": 0.9
        }
        
        # Primeras selecciones deben explorar
        selections = []
        for _ in range(3):
            selected = policy.select(arms)
            selections.append(selected)
        
        assert len(set(selections)) == 3, "Should explore all arms initially"
        
        # Siguiente selección debe explotar
        selected = policy.select(arms)
        assert selected in arms, "Selected arm should be valid"
        
        print("✅ UCB1 Policy: PASSED")
        
    except Exception as e:
        print(f"❌ UCB1 Policy: FAILED - {e}")
        return False
    
    try:
        # Test 5: Critic
        print("\n🔹 Testing Critic...")
        from agent.critic import Critic
        
        critic = Critic()
        
        # Test reflection
        state = {"recent_rewards": [0.7, 0.8]}
        results = [
            ("sig_a", {}, {}, {"reward": 0.8}),
            ("sig_b", {}, {}, {"reward": 0.6})
        ]
        
        test_log_path = Path("test_decisions.jsonl")
        critic.reflect(state, results, "sig_a", test_log_path)
        
        assert test_log_path.exists(), "Critic should create log file"
        
        # Verificar contenido
        with open(test_log_path, 'r') as f:
            log_content = f.read()
            assert "sig_a" in log_content, "Log should contain chosen sig"
        
        # Cleanup
        test_log_path.unlink()
        
        print("✅ Critic: PASSED")
        
    except Exception as e:
        print(f"❌ Critic: FAILED - {e}")
        return False
    
    return True

def test_agent_controller_init():
    """Test de inicialización del controlador de agente"""
    
    try:
        print("\n🔹 Testing AgentController initialization...")
        from agent.agent_controller import AgentController
        
        # Verificar que config existe
        config_path = Path("config/agent_policy.json")
        assert config_path.exists(), "Agent policy config should exist"
        
        # Inicializar controller
        controller = AgentController()
        
        assert hasattr(controller, 'planner'), "Controller should have planner"
        assert hasattr(controller, 'executor'), "Controller should have executor"
        assert hasattr(controller, 'evaluator'), "Controller should have evaluator"
        assert hasattr(controller, 'memory'), "Controller should have memory"
        assert hasattr(controller, 'policy'), "Controller should have policy"
        assert hasattr(controller, 'critic'), "Controller should have critic"
        
        print("✅ AgentController: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ AgentController: FAILED - {e}")
        return False

def main():
    """Función principal de testing"""
    
    print("🚀 STARTING AGENT TESTS")
    print("Testing individual components before full agent cycle")
    
    # Test componentes individuales
    components_ok = test_agent_components()
    
    # Test inicialización del controller
    controller_ok = test_agent_controller_init()
    
    print("\n" + "=" * 50)
    if components_ok and controller_ok:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Sistema agéntico básico funcionando correctamente")
        print("\n📋 Componentes verificados:")
        print("   • 🧠 Planner: Genera configuraciones experimentales")
        print("   • 💾 Memory: Almacena episodios de aprendizaje")
        print("   • ⚖️ Evaluator: Calcula rewards de configuraciones")
        print("   • 🎯 UCB1 Policy: Selecciona mejores configuraciones")
        print("   • 🔍 Critic: Reflexiona sobre decisiones")
        print("   • 🤖 AgentController: Orquesta el ciclo completo")
        print("\n🚀 LISTO PARA IMPLEMENTAR CICLO AGÉNTICO COMPLETO!")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️ Revisar componentes antes de continuar")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
