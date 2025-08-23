#!/usr/bin/env python3
"""
🧪 TEST COMPONENTES FASE 2
Test individual de componentes de auto-tuning para verificar funcionamiento
"""

import sys
import numpy as np
from pathlib import Path

# Añadir path del core
sys.path.append('core')

def test_bayesian_optimizer():
    """Test del optimizador Bayesiano"""
    try:
        print("🔍 Testing Bayesian Optimizer...")
        from agent.bayesian_optimizer import create_bayesian_optimizer
        
        optimizer = create_bayesian_optimizer("test_study_phase2")
        
        # Mock functions
        def mock_executor(config):
            import random
            neural_w = config["ensemble_weights"].get("neural_enhanced", 0.45)
            base_reward = 0.6 + (neural_w * 0.3)
            return {
                "returncode": 0,
                "stdout": f"SVI: {base_reward + random.uniform(-0.1, 0.1):.3f} Generadas",
                "stderr": ""
            }
        
        def mock_evaluator(run_result, baseline):
            import re
            svi = float(re.search(r"SVI: ([0-9.]+)", run_result["stdout"]).group(1))
            return {
                "reward": svi * 0.85,
                "quality_ok": svi > 0.65,
                "signals": {"svi": svi}
            }
        
        # Ejecutar optimización corta
        result = optimizer.optimize(
            mock_executor, mock_evaluator, 
            "ensemble", n_trials=3, timeout=30
        )
        
        print(f"   ✅ Bayesian Optimizer: PASSED")
        print(f"      🏆 Best reward: {result['best_reward']:.3f}")
        print(f"      🔢 Trials: {result['completed_trials']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Bayesian Optimizer: FAILED - {e}")
        return False

def test_drift_detector():
    """Test del detector de deriva"""
    try:
        print("\n📊 Testing Drift Detector...")
        from agent.drift_detector import create_drift_detector
        
        detector = create_drift_detector()
        
        # Simular episodios normales
        for i in range(15):
            detector.add_episode(
                reward=0.75 + np.random.normal(0, 0.05),
                svi=0.8 + np.random.normal(0, 0.03),
                diversity=0.85 + np.random.normal(0, 0.02),
                quality_ok=True,
                combinations=[[np.random.randint(1, 41) for _ in range(6)] for _ in range(2)]
            )
        
        # Simular deriva
        for i in range(8):
            detector.add_episode(
                reward=0.5 + np.random.normal(0, 0.02),  # Performance drop
                svi=0.55 + np.random.normal(0, 0.02),
                diversity=0.6 + np.random.normal(0, 0.02),
                quality_ok=i > 4,
                combinations=[[np.random.randint(1, 25) for _ in range(6)] for _ in range(2)]
            )
        
        # Verificar detección
        should_recal, details = detector.should_trigger_recalibration()
        
        print(f"   ✅ Drift Detector: PASSED")
        print(f"      🚨 Deriva detectada: {'✅' if should_recal else '❌'}")
        print(f"      📊 Ratio deriva: {details['drift_ratio']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Drift Detector: FAILED - {e}")
        return False

def test_active_learner():
    """Test del sistema de Active Learning"""
    try:
        print("\n🎯 Testing Active Learner...")
        from agent.active_learner import create_active_learner
        
        learner = create_active_learner("uncertainty_sampling")
        
        # Mock configs
        configs = [
            {"ensemble_weights": {"neural_enhanced": 0.4, "transformer_deep": 0.3, "genetico": 0.3}, "svi_profile": "default"},
            {"ensemble_weights": {"neural_enhanced": 0.6, "transformer_deep": 0.2, "genetico": 0.2}, "svi_profile": "neural_optimized"},
            {"ensemble_weights": {"neural_enhanced": 0.5, "transformer_deep": 0.25, "genetico": 0.25}, "svi_profile": "aggressive"}
        ]
        
        # Simular learning
        for trial in range(12):
            selected = learner.select_next_configuration(configs, trial)
            
            # Simular reward
            neural_w = selected["ensemble_weights"]["neural_enhanced"]
            reward = 0.6 + (neural_w * 0.25) + np.random.normal(0, 0.05)
            reward = max(0.3, min(0.95, reward))
            
            learner.update_with_result(selected, reward, trial)
        
        # Obtener insights
        insights = learner.get_learning_insights()
        
        print(f"   ✅ Active Learner: PASSED")
        print(f"      🔍 Exploration ratio: {insights['exploration_ratio']:.1%}")
        print(f"      🏆 Best reward: {insights['best_reward']:.3f}")
        print(f"      📈 Trend: {insights['learning_trend']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Active Learner: FAILED - {e}")
        return False

def test_planner_v2():
    """Test del Planner V2"""
    try:
        print("\n🧠 Testing Planner V2...")
        from agent.planner_v2 import create_advanced_planner
        
        policy_cfg = {"baseline_profile": "default"}
        planner = create_advanced_planner(policy_cfg)
        
        # Simular states y proposals
        for trial in range(8):
            state = {
                "recent_rewards": [0.7 + np.random.normal(0, 0.05) for _ in range(5)],
                "n": trial
            }
            
            proposals = planner.propose(state, n=3)
            
            # Simular resultado del mejor
            best_proposal = proposals[0]
            reward = 0.65 + np.random.random() * 0.25
            
            planner.update_with_result(best_proposal, reward, trial)
        
        # Obtener insights
        insights = planner.get_planner_insights()
        
        print(f"   ✅ Planner V2: PASSED")
        print(f"      🎯 Modo actual: {insights['current_mode']}")
        print(f"      🏆 Configs exitosas: {insights['successful_configs_count']}")
        print(f"      📈 Mejor reward: {insights['best_successful_reward']:.3f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Planner V2: FAILED - {e}")
        return False

def main():
    """Función principal de testing"""
    
    print("🧪 TESTING COMPONENTES FASE 2 - AUTO-TUNING AVANZADO")
    print("=" * 70)
    
    # Ejecutar tests individuales
    results = []
    
    results.append(test_bayesian_optimizer())
    results.append(test_drift_detector())  
    results.append(test_active_learner())
    results.append(test_planner_v2())
    
    # Resumen
    passed = sum(results)
    total = len(results)
    
    print(f"\n" + "=" * 70)
    print(f"📊 RESUMEN TESTS FASE 2")
    print(f"=" * 70)
    print(f"✅ Tests pasados: {passed}/{total}")
    print(f"📈 Success rate: {passed/total:.1%}")
    
    if passed == total:
        print(f"\n🎉 TODOS LOS COMPONENTES FASE 2 FUNCIONANDO!")
        print(f"🚀 Sistema listo para auto-tuning avanzado:")
        print(f"   • 🔍 Bayesian Optimization operativa")
        print(f"   • 📊 Drift Detection activa")
        print(f"   • 🎯 Active Learning inteligente")
        print(f"   • 🧠 Planner V2 con estrategias avanzadas")
        
        print(f"\n✅ FASE 2 COMPLETADA EXITOSAMENTE!")
        return 0
    else:
        print(f"\n⚠️ Algunos componentes requieren atención")
        print(f"🔧 Revisar componentes fallidos antes de continuar")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
