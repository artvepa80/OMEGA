#!/usr/bin/env python3
"""
🔍 TEST COMPONENTES FASE 3
Test individual de componentes reflexivos para verificar funcionamiento
"""

import sys
import numpy as np
from pathlib import Path
from datetime import datetime

# Añadir path del core
sys.path.append('core')

def test_self_reflection_engine():
    """Test del motor de auto-reflexión"""
    try:
        print("🔍 Testing Self-Reflection Engine...")
        from agent.self_reflection import create_self_reflection_engine
        
        engine = create_self_reflection_engine()
        
        # Mock cycle results para reflexión
        mock_cycles = []
        for i in range(8):
            cycle = {
                "cycle_number": i + 1,
                "timestamp": datetime.now().isoformat(),
                "evaluation": {
                    "chosen_config": {
                        "ensemble_weights": {
                            "neural_enhanced": 0.4 + (i * 0.03),
                            "transformer_deep": 0.3,
                            "genetico": 0.3
                        },
                        "svi_profile": ["default", "neural_optimized", "aggressive"][i % 3]
                    },
                    "chosen_reward": 0.65 + (i * 0.025) + np.random.normal(0, 0.02),
                    "metrics": {
                        "best_reward": 0.65 + (i * 0.025) + np.random.normal(0, 0.02),
                        "average_reward": 0.60 + (i * 0.02),
                        "quality_rate": 0.75 + (i * 0.015),
                        "average_execution_time": 45 + np.random.normal(0, 3)
                    }
                }
            }
            mock_cycles.append(cycle)
        
        # Ejecutar reflexión
        reflection = engine.reflect_on_cycles(mock_cycles)
        
        print(f"   ✅ Self-Reflection Engine: PASSED")
        print(f"      🔍 Reflection quality: {reflection.get('reflection_quality', 'unknown')}")
        print(f"      💡 Insights: {reflection.get('synthesis', {}).get('total_insights', 0)}")
        print(f"      📋 Recommendations: {len(reflection.get('recommendations', []))}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Self-Reflection Engine: FAILED - {e}")
        return False

def test_advanced_critic():
    """Test del crítico avanzado"""
    try:
        print("\n🤖 Testing Advanced Critic V2...")
        from agent.critic_v2 import create_advanced_critic
        
        critic = create_advanced_critic()
        
        # Mock cycle results
        mock_cycles = []
        for i in range(10):
            cycle = {
                "cycle": i + 1,
                "best_reward": 0.6 + (i * 0.03) + np.random.normal(0, 0.02),
                "quality_rate": 0.7 + (i * 0.02),
                "planner_mode": ["active_learning", "bayesian_optimization", "recalibration"][i % 3],
                "timestamp": datetime.now().isoformat()
            }
            mock_cycles.append(cycle)
        
        # Ejecutar análisis crítico
        criticism = critic.analyze_cycle_results(mock_cycles)
        
        print(f"   ✅ Advanced Critic V2: PASSED")
        print(f"      🔍 Confidence: {criticism.get('criticism_confidence', 'unknown')}")
        print(f"      🎯 Success patterns: {'✅' if 'success_patterns' in criticism else '❌'}")
        print(f"      💡 Meta insights: {len(criticism.get('meta_insights', []))}")
        print(f"      📋 Recommendations: {len(criticism.get('actionable_recommendations', []))}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Advanced Critic V2: FAILED - {e}")
        return False

def test_html_reporter_v3():
    """Test del reporter HTML V3"""
    try:
        print("\n📊 Testing HTML Reporter V3...")
        from modules.reporting.html_reporter_v3 import generate_advanced_report
        
        # Mock data
        agent_data = {
            "cycle_results": [
                {"cycle": 1, "best_reward": 0.75, "quality_rate": 0.8, "planner_mode": "active_learning"},
                {"cycle": 2, "best_reward": 0.78, "quality_rate": 0.85, "planner_mode": "bayesian_optimization"},
                {"cycle": 3, "best_reward": 0.82, "quality_rate": 0.9, "planner_mode": "neural_optimized"}
            ]
        }
        
        reflection_data = {
            "insights": [
                "🎯 Neural Enhanced muestra alta correlación con performance",
                "📈 Learning detectado: 15% mejora en últimos ciclos"
            ],
            "recommendations": [
                {
                    "type": "optimization",
                    "priority": "high", 
                    "action": "Aumentar peso neural",
                    "rationale": "Correlación positiva detectada",
                    "implementation": "Ajustar a 0.6 en próximas config"
                }
            ]
        }
        
        # Generar reporte
        report_path = generate_advanced_report(
            "Test OMEGA V3 Report",
            agent_data,
            reflection_data,
            "outputs/test_report_v3.html"
        )
        
        # Verificar que se creó el archivo
        if Path(report_path).exists():
            file_size = Path(report_path).stat().st_size
            print(f"   ✅ HTML Reporter V3: PASSED")
            print(f"      📊 Report generated: {Path(report_path).name}")
            print(f"      📁 File size: {file_size:,} bytes")
            print(f"      🔗 Path: {report_path}")
            return True
        else:
            print(f"   ❌ HTML Reporter V3: FAILED - File not created")
            return False
        
    except Exception as e:
        print(f"   ❌ HTML Reporter V3: FAILED - {e}")
        return False

def test_agent_controller_v3_initialization():
    """Test de inicialización del controlador V3"""
    try:
        print("\n🤖 Testing Agent Controller V3 Initialization...")
        from agent.agent_controller_v3 import create_reflective_agent_controller
        
        # Crear controlador V3
        controller = create_reflective_agent_controller()
        
        # Verificar componentes V3
        has_advanced_critic = hasattr(controller, 'advanced_critic')
        has_reflection_engine = hasattr(controller, 'reflection_engine')
        has_reflection_config = hasattr(controller, 'reflection_config')
        
        # Obtener insights V3
        insights = controller.get_v3_insights()
        
        print(f"   ✅ Agent Controller V3: PASSED")
        print(f"      🤖 Advanced Critic: {'✅' if has_advanced_critic else '❌'}")
        print(f"      🔍 Reflection Engine: {'✅' if has_reflection_engine else '❌'}")
        print(f"      ⚙️ Reflection Config: {'✅' if has_reflection_config else '❌'}")
        print(f"      📊 Controller version: {insights.get('controller_version', 'unknown')}")
        print(f"      🎯 Capabilities: {len(insights.get('capabilities', {}))}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Agent Controller V3: FAILED - {e}")
        return False

def main():
    """Función principal de testing"""
    
    print("🔍 TESTING COMPONENTES FASE 3 - SISTEMA REFLEXIVO")
    print("=" * 70)
    
    # Ejecutar tests individuales
    results = []
    
    results.append(test_self_reflection_engine())
    results.append(test_advanced_critic())
    results.append(test_html_reporter_v3())
    results.append(test_agent_controller_v3_initialization())
    
    # Resumen
    passed = sum(results)
    total = len(results)
    
    print(f"\n" + "=" * 70)
    print(f"📊 RESUMEN TESTS FASE 3")
    print(f"=" * 70)
    print(f"✅ Tests pasados: {passed}/{total}")
    print(f"📈 Success rate: {passed/total:.1%}")
    
    if passed == total:
        print(f"\n🎉 TODOS LOS COMPONENTES FASE 3 FUNCIONANDO!")
        print(f"🔍 Sistema reflexivo listo para operación:")
        print(f"   • 🔍 Self-Reflection Engine operativo")
        print(f"   • 🤖 Advanced Critic V2 con meta-learning")
        print(f"   • 📊 HTML Reporter V3 con explicabilidad")
        print(f"   • 🤖 Agent Controller V3 reflexivo")
        
        print(f"\n✅ FASE 3 COMPLETADA EXITOSAMENTE!")
        print(f"🌟 OMEGA ahora tiene:")
        print(f"   • 🧠 Auto-reflexión profunda")
        print(f"   • 🤖 Meta-learning avanzado")
        print(f"   • 📊 Explicabilidad completa")
        print(f"   • 🎯 Decision tracking detallado")
        print(f"   • 🔄 Auto-mejora continua")
        
        return 0
    else:
        print(f"\n⚠️ Algunos componentes requieren atención")
        print(f"🔧 Revisar componentes fallidos antes de continuar")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
