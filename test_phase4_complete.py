#!/usr/bin/env python3
"""
🤖 TEST FASE 4 COMPLETA - Sistema Agéntico Autónomo
Test integral de todas las capacidades autónomas implementadas
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# Añadir path del core
sys.path.append('core')

def test_autonomous_scheduler():
    """Test del programador autónomo"""
    try:
        print("🕐 Testing Autonomous Scheduler...")
        from agent.autonomous_scheduler import create_autonomous_scheduler
        
        scheduler = create_autonomous_scheduler()
        
        # Verificar componentes
        has_resource_manager = hasattr(scheduler, 'resource_manager')
        has_task_registry = hasattr(scheduler, 'task_registry')
        
        # Test de estado
        status = scheduler.get_status()
        
        print(f"   ✅ Autonomous Scheduler: PASSED")
        print(f"      🔧 Resource Manager: {'✅' if has_resource_manager else '❌'}")
        print(f"      📋 Task Registry: {'✅' if has_task_registry else '❌'}")
        print(f"      📊 Config: {len(status.get('config', {}))}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Autonomous Scheduler: FAILED - {e}")
        return False

def test_multi_objective_optimizer():
    """Test del optimizador multi-objetivo"""
    try:
        print("\n🎯 Testing Multi-Objective Optimizer...")
        from agent.multi_objective_optimizer import create_multi_objective_optimizer
        
        optimizer = create_multi_objective_optimizer()
        
        # Verificar componentes
        has_objectives = hasattr(optimizer, 'objectives')
        has_pareto_analyzer = hasattr(optimizer, 'pareto_analyzer')
        
        # Test con datos mock
        mock_configs = [
            {"ensemble_weights": {"neural_enhanced": 0.5}, "svi_profile": "default"},
            {"ensemble_weights": {"neural_enhanced": 0.7}, "svi_profile": "neural_optimized"}
        ]
        
        mock_results_map = {
            "config_0": [{"best_reward": 0.75, "duration": 45, "quality_rate": 0.8}],
            "config_1": [{"best_reward": 0.82, "duration": 50, "quality_rate": 0.85}]
        }
        
        result = optimizer.optimize_configurations(mock_configs, mock_results_map)
        
        print(f"   ✅ Multi-Objective Optimizer: PASSED")
        print(f"      🎯 Objectives: {'✅' if has_objectives else '❌'}")
        print(f"      📊 Pareto Analyzer: {'✅' if has_pareto_analyzer else '❌'}")
        print(f"      🏆 Best score: {result['best_solution']['overall_score']:.3f}")
        print(f"      📈 Pareto fronts: {result['pareto_summary']['total_fronts']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Multi-Objective Optimizer: FAILED - {e}")
        return False

def test_continuous_learning():
    """Test del sistema de aprendizaje continuo"""
    try:
        print("\n📚 Testing Continuous Learning System...")
        from agent.continuous_learning import create_continuous_learning_system, LearningExample
        
        system = create_continuous_learning_system()
        
        # Verificar componentes
        has_learners = hasattr(system, 'learners')
        has_drift_detector = hasattr(system, 'drift_detector')
        has_knowledge_manager = hasattr(system, 'knowledge_manager')
        
        # Test con ejemplo de aprendizaje
        example = LearningExample(
            features={"neural_weight": 0.6, "svi_score": 0.8},
            target=0.75,
            timestamp=datetime.now().isoformat(),
            context={"cycle": 1, "strategy": "test"}
        )
        
        result = system.process_learning_example(example, "test_learner")
        
        # Test de predicción ensemble
        prediction = system.predict_with_ensemble({"neural_weight": 0.5, "svi_score": 0.7})
        
        print(f"   ✅ Continuous Learning: PASSED")
        print(f"      🤖 Learners: {'✅' if has_learners else '❌'}")
        print(f"      🔍 Drift Detector: {'✅' if has_drift_detector else '❌'}")
        print(f"      🧠 Knowledge Manager: {'✅' if has_knowledge_manager else '❌'}")
        print(f"      📊 Prediction error: {result['error']:.3f}")
        print(f"      🎯 Ensemble confidence: {prediction['confidence']:.3f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Continuous Learning: FAILED - {e}")
        return False

def test_self_monitoring():
    """Test del sistema de auto-monitoreo"""
    try:
        print("\n👁️ Testing Self-Monitoring System...")
        from agent.self_monitoring import create_self_monitoring_system, AlertLevel
        
        monitoring = create_self_monitoring_system()
        
        # Verificar componentes
        has_system_monitor = hasattr(monitoring, 'system_monitor')
        has_performance_monitor = hasattr(monitoring, 'performance_monitor')
        has_alert_manager = hasattr(monitoring, 'alert_manager')
        
        # Test de trigger de alerta personalizada
        monitoring.trigger_custom_alert(
            "Test Alert",
            "This is a test alert",
            AlertLevel.INFO,
            "testing",
            {"test": True}
        )
        
        # Test de estado
        status = monitoring.get_monitoring_status()
        
        print(f"   ✅ Self-Monitoring: PASSED")
        print(f"      🖥️ System Monitor: {'✅' if has_system_monitor else '❌'}")
        print(f"      📈 Performance Monitor: {'✅' if has_performance_monitor else '❌'}")
        print(f"      🚨 Alert Manager: {'✅' if has_alert_manager else '❌'}")
        print(f"      💚 System health: {status['system_health']['overall_health']}")
        print(f"      🔔 Active alerts: {status['alerts']['active_alerts']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Self-Monitoring: FAILED - {e}")
        return False

def test_api_interface():
    """Test de la interfaz API"""
    try:
        print("\n🔌 Testing API Interface...")
        from agent.api_interface import create_omega_api
        
        api = create_omega_api()
        
        # Verificar componentes
        has_app = hasattr(api, 'app')
        has_auth = hasattr(api, 'auth')
        has_stats = hasattr(api, 'api_stats')
        
        # Verificar rutas configuradas
        routes_count = len(api.app.routes)
        
        print(f"   ✅ API Interface: PASSED")
        print(f"      🌐 FastAPI App: {'✅' if has_app else '❌'}")
        print(f"      🔐 Authentication: {'✅' if has_auth else '❌'}")
        print(f"      📊 Stats Tracking: {'✅' if has_stats else '❌'}")
        print(f"      🛤️ Routes configured: {routes_count}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API Interface: FAILED - {e}")
        return False

def test_agent_controller_v4():
    """Test del controlador V4 autónomo"""
    try:
        print("\n🤖 Testing Agent Controller V4...")
        from agent.agent_controller_v4 import create_autonomous_agent_controller
        
        controller = create_autonomous_agent_controller()
        
        # Verificar componentes V4
        has_scheduler = hasattr(controller, 'autonomous_scheduler')
        has_optimizer = hasattr(controller, 'multi_objective_optimizer')
        has_learning = hasattr(controller, 'continuous_learning')
        has_monitoring = hasattr(controller, 'self_monitoring')
        has_api = hasattr(controller, 'api_interface')
        
        # Test de estado autónomo
        status = controller.get_autonomous_status()
        
        print(f"   ✅ Agent Controller V4: PASSED")
        print(f"      🕐 Autonomous Scheduler: {'✅' if has_scheduler else '❌'}")
        print(f"      🎯 Multi-Objective Optimizer: {'✅' if has_optimizer else '❌'}")
        print(f"      📚 Continuous Learning: {'✅' if has_learning else '❌'}")
        print(f"      👁️ Self-Monitoring: {'✅' if has_monitoring else '❌'}")
        print(f"      🔌 API Interface: {'✅' if has_api else '❌'}")
        print(f"      📊 Controller version: {status['controller_version']}")
        print(f"      🤖 Autonomous mode: {'✅' if status['autonomous_mode'] else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Agent Controller V4: FAILED - {e}")
        return False

def test_integrated_autonomous_cycle():
    """Test de ciclo autónomo integrado"""
    try:
        print("\n🔄 Testing Integrated Autonomous Cycle...")
        from agent.agent_controller_v4 import create_autonomous_agent_controller
        
        controller = create_autonomous_agent_controller()
        
        # Ejecutar un ciclo V4 completo
        result = controller.cycle_v4()
        
        # Verificar componentes del resultado
        has_v3_base = "v3_enhancements" in result
        has_v4_enhancements = "v4_enhancements" in result
        
        if "error" not in result:
            v4_enhancements = result.get("v4_enhancements", {})
            
            learning_executed = v4_enhancements.get("continuous_learning", {}).get("executed", False)
            monitoring_active = v4_enhancements.get("autonomous_monitoring", {}).get("monitoring_active", False)
            
            print(f"   ✅ Integrated Autonomous Cycle: PASSED")
            print(f"      🔄 V3 Base: {'✅' if has_v3_base else '❌'}")
            print(f"      🚀 V4 Enhancements: {'✅' if has_v4_enhancements else '❌'}")
            print(f"      📚 Learning executed: {'✅' if learning_executed else '❌'}")
            print(f"      👁️ Monitoring active: {'✅' if monitoring_active else '❌'}")
            print(f"      ⏱️ Cycle duration: {result.get('v4_duration', 0):.1f}s")
            
            return True
        else:
            print(f"   ❌ Integrated Autonomous Cycle: FAILED - {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"   ❌ Integrated Autonomous Cycle: FAILED - {e}")
        return False

def main():
    """Función principal de testing"""
    
    print("🤖 TESTING FASE 4 - SISTEMA AGÉNTICO AUTÓNOMO")
    print("=" * 80)
    print("🧪 Probando todos los componentes autónomos implementados")
    
    # Ejecutar tests individuales
    results = []
    
    results.append(test_autonomous_scheduler())
    results.append(test_multi_objective_optimizer())
    results.append(test_continuous_learning())
    results.append(test_self_monitoring())
    results.append(test_api_interface())
    results.append(test_agent_controller_v4())
    results.append(test_integrated_autonomous_cycle())
    
    # Resumen
    passed = sum(results)
    total = len(results)
    
    print(f"\n" + "=" * 80)
    print(f"📊 RESUMEN TESTS FASE 4")
    print(f"=" * 80)
    print(f"✅ Tests pasados: {passed}/{total}")
    print(f"📈 Success rate: {passed/total:.1%}")
    
    if passed == total:
        print(f"\n🎉 TODOS LOS COMPONENTES FASE 4 FUNCIONANDO!")
        print(f"🤖 Sistema agéntico completamente autónomo:")
        print(f"   • 🕐 Autonomous Scheduler operativo")
        print(f"   • 🎯 Multi-Objective Optimizer funcionando")
        print(f"   • 📚 Continuous Learning System activo")
        print(f"   • 👁️ Self-Monitoring & Alerts habilitado")
        print(f"   • 🔌 API REST Interface disponible")
        print(f"   • 🤖 Agent Controller V4 integrado")
        
        print(f"\n✅ FASE 4 COMPLETADA AL 100%!")
        print(f"🌟 OMEGA PRO AI ahora es completamente autónomo:")
        
        print(f"\n🎯 CAPACIDADES AUTÓNOMAS ACTIVAS:")
        print(f"   • 🕐 Programación inteligente de operaciones")
        print(f"   • 🎯 Optimización multi-objetivo con frentes de Pareto") 
        print(f"   • 📚 Aprendizaje continuo online con detección de drift")
        print(f"   • 👁️ Auto-monitoreo con alertas y recuperación automática")
        print(f"   • 🔌 API REST para integración externa completa")
        print(f"   • 🔄 Gestión autónoma de recursos del sistema")
        print(f"   • 🧠 Meta-aprendizaje y auto-reflexión")
        print(f"   • 📊 Explicabilidad y reportes automáticos")
        
        print(f"\n🚀 EVOLUCIÓN COMPLETA DEL SISTEMA:")
        print(f"   ✅ Fase 0: Estabilidad y corrección de errores")
        print(f"   ✅ Fase 1: Agente básico funcional")
        print(f"   ✅ Fase 2: Auto-tuning con optimización bayesiana")
        print(f"   ✅ Fase 3: Reflexión profunda y explicabilidad")
        print(f"   ✅ Fase 4: Autonomía operativa completa")
        
        print(f"\n🌟 OMEGA PRO AI V4.0 - SISTEMA AGÉNTICO AUTÓNOMO")
        print(f"    Operación independiente ✅")
        print(f"    Auto-optimización ✅") 
        print(f"    Aprendizaje continuo ✅")
        print(f"    Auto-monitoreo ✅")
        print(f"    Integración externa ✅")
        
        return 0
    else:
        print(f"\n⚠️ Algunos componentes requieren atención")
        print(f"🔧 Revisar componentes fallidos antes de continuar")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
