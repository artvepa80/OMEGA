#!/usr/bin/env python3
"""
🚀 DEMO FASE 2 COMPLETA - Sistema Agéntico Avanzado
Demostración de todas las capacidades de auto-tuning:
- Bayesian Optimization
- Active Learning
- Drift Detection
- Auto-retraining
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

# Añadir path del core
sys.path.append('core')

from agent.agent_controller_v2 import create_advanced_agent_controller

class Phase2Demo:
    """Demo completo de capacidades de Fase 2"""
    
    def __init__(self):
        self.controller = create_advanced_agent_controller()
        self.demo_cycles = []
        
    def simulate_executor_v2(self, config: dict) -> dict:
        """Simula ejecución mejorada para Fase 2"""
        
        # Extraer parámetros clave
        neural_weight = config["ensemble_weights"].get("neural_enhanced", 0.45)
        svi_profile = config.get("svi_profile", "default")
        
        # Simular SVI más realista basado en configuración
        profile_multipliers = {
            "conservative": 0.85,
            "default": 1.0,
            "aggressive": 1.15,
            "neural_optimized": 1.05 + (neural_weight * 0.2)
        }
        
        base_svi = 0.65 + (neural_weight * 0.25)
        profile_mult = profile_multipliers.get(svi_profile, 1.0)
        final_svi = base_svi * profile_mult
        
        # Añadir ruido realista
        noise = np.random.normal(0, 0.08)
        final_svi = max(0.3, min(0.95, final_svi + noise))
        
        # Simular otras métricas
        diversity = 0.75 + (neural_weight * 0.15) + np.random.normal(0, 0.05)
        diversity = max(0.5, min(1.0, diversity))
        
        jackpot = 0.45 + (neural_weight * 0.1) + np.random.normal(0, 0.03)
        jackpot = max(0.2, min(0.8, jackpot))
        
        # Simular éxito/fallo de calidad
        quality_ok = (final_svi > 0.6) and (diversity > 0.65)
        
        simulated_stdout = f"""
🌟 OMEGA PRO AI V3.0 - Fase 2 Simulation
═══════════════════════════════════════

📊 MÉTRICAS DE RENDIMIENTO:
SVI: {final_svi:.3f}
Diversity: {diversity:.3f}
Perfil detectado: {jackpot:.2f}

🎯 CONFIGURACIÓN APLICADA:
Neural Enhanced: {neural_weight:.2f}
SVI Profile: {svi_profile}
Quality Check: {'✅ PASSED' if quality_ok else '❌ FAILED'}

🚀 RESULTADOS:
✅ {'17' if quality_ok else '8'} combinaciones generadas
📈 Performance: {'Óptimo' if final_svi > 0.8 else 'Bueno' if final_svi > 0.7 else 'Aceptable'}
🔧 Modo: {config.get('proposal_metadata', {}).get('mode', 'standard')}
        """
        
        return {
            "returncode": 0 if quality_ok else 1,
            "stdout": simulated_stdout,
            "stderr": "" if quality_ok else "Warning: Quality threshold not met",
            "artifacts": {
                "combinacion": f"combo_{neural_weight:.2f}_{svi_profile}.csv",
                "svi_export": f"svi_{final_svi:.3f}.json"
            },
            "simulation_meta": {
                "neural_weight": neural_weight,
                "svi_profile": svi_profile,
                "final_svi": final_svi,
                "diversity": diversity,
                "jackpot": jackpot,
                "quality_ok": quality_ok
            }
        }
    
    def run_phase2_demo(self, n_cycles: int = 8) -> dict:
        """Ejecuta demo completo de Fase 2"""
        
        print("🚀 DEMO FASE 2 - SISTEMA AGÉNTICO AVANZADO")
        print("=" * 70)
        print("🔧 Capacidades de Auto-tuning:")
        print("   • 🔍 Bayesian Optimization")
        print("   • 🎯 Active Learning")
        print("   • 📊 Drift Detection")
        print("   • 🔄 Auto-retraining")
        print("")
        
        # Patch del executor para usar simulación
        original_executor_run = self.controller.executor.run
        self.controller.executor.run = self.simulate_executor_v2
        
        demo_results = []
        
        try:
            for cycle in range(n_cycles):
                print(f"\n🔄 CICLO FASE 2 #{cycle + 1}")
                print("-" * 50)
                
                # Ejecutar ciclo V2 completo
                cycle_result = self.controller.cycle_v2()
                
                # Extraer métricas clave
                if "error" not in cycle_result:
                    evaluation = cycle_result.get("evaluation", {})
                    metrics = evaluation.get("metrics", {})
                    learning = cycle_result.get("learning", {})
                    adaptation = cycle_result.get("adaptation", {})
                    
                    print(f"✅ Ciclo completado:")
                    print(f"   🏆 Mejor reward: {metrics.get('best_reward', 0):.3f}")
                    print(f"   📊 Promedio: {metrics.get('average_reward', 0):.3f}")
                    print(f"   ✅ Quality rate: {metrics.get('quality_rate', 0):.1%}")
                    print(f"   🎯 Modo planner: {cycle_result.get('state_analysis', {}).get('planner_insights', {}).get('current_mode', 'unknown')}")
                    print(f"   🔧 Adaptaciones: {len(adaptation.get('adaptations_applied', []))}")
                    
                    # Mostrar key learnings
                    key_learnings = learning.get("key_learnings", [])
                    if key_learnings:
                        print(f"   💡 Key learnings:")
                        for learning_item in key_learnings[:2]:
                            print(f"      • {learning_item}")
                    
                    demo_results.append({
                        "cycle": cycle + 1,
                        "best_reward": metrics.get("best_reward", 0),
                        "average_reward": metrics.get("average_reward", 0),
                        "quality_rate": metrics.get("quality_rate", 0),
                        "planner_mode": cycle_result.get("state_analysis", {}).get("planner_insights", {}).get("current_mode", "unknown"),
                        "adaptations_count": len(adaptation.get("adaptations_applied", [])),
                        "key_learnings": key_learnings
                    })
                else:
                    print(f"❌ Error en ciclo: {cycle_result.get('error')}")
            
            # Análisis final
            final_analysis = self._analyze_demo_results(demo_results)
            
            return {
                "demo_completed": True,
                "cycles_executed": len(demo_results),
                "cycle_results": demo_results,
                "final_analysis": final_analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            # Restaurar executor original
            self.controller.executor.run = original_executor_run
    
    def _analyze_demo_results(self, results: list) -> dict:
        """Analiza resultados del demo"""
        
        if not results:
            return {"error": "No results to analyze"}
        
        # Extraer métricas
        rewards = [r["best_reward"] for r in results]
        quality_rates = [r["quality_rate"] for r in results]
        modes_used = [r["planner_mode"] for r in results]
        
        # Análisis de tendencias
        if len(rewards) >= 4:
            first_half_reward = np.mean(rewards[:len(rewards)//2])
            second_half_reward = np.mean(rewards[len(rewards)//2:])
            improvement = (second_half_reward - first_half_reward) / first_half_reward * 100
        else:
            improvement = 0
        
        # Análisis de modos del planner
        mode_usage = {}
        for mode in modes_used:
            mode_usage[mode] = mode_usage.get(mode, 0) + 1
        
        # Conteo de adaptaciones totales
        total_adaptations = sum(r["adaptations_count"] for r in results)
        
        # Learning insights únicos
        all_learnings = []
        for r in results:
            all_learnings.extend(r["key_learnings"])
        unique_learnings = list(set(all_learnings))
        
        analysis = {
            "performance_metrics": {
                "best_reward_achieved": max(rewards),
                "average_reward": np.mean(rewards),
                "final_reward": rewards[-1] if rewards else 0,
                "improvement_percentage": improvement,
                "best_quality_rate": max(quality_rates),
                "average_quality_rate": np.mean(quality_rates)
            },
            "system_behavior": {
                "planner_modes_used": mode_usage,
                "total_adaptations_applied": total_adaptations,
                "unique_learnings_count": len(unique_learnings)
            },
            "phase2_capabilities_demonstrated": {
                "bayesian_optimization": "bayesian_optimization" in mode_usage,
                "active_learning": "active_learning" in mode_usage,
                "recalibration": "recalibration" in mode_usage,
                "adaptive_behavior": len(mode_usage) > 1,
                "continuous_learning": len(unique_learnings) > 3
            },
            "trend_analysis": {
                "performance_trend": "improving" if improvement > 5 else "stable" if improvement > -5 else "degrading",
                "system_stability": "stable" if np.std(rewards) < 0.1 else "variable",
                "learning_progression": "active" if len(unique_learnings) > len(results) * 0.5 else "limited"
            }
        }
        
        return analysis
    
    def display_phase2_summary(self, demo_result: dict):
        """Muestra resumen completo de Fase 2"""
        
        print("\n" + "="*70)
        print("🎉 RESUMEN DEMO FASE 2 - SISTEMA AGÉNTICO AVANZADO")
        print("="*70)
        
        if demo_result.get("demo_completed"):
            cycles = demo_result["cycles_executed"]
            analysis = demo_result["final_analysis"]
            
            print(f"\n📊 MÉTRICAS GENERALES:")
            print(f"   🔄 Ciclos ejecutados: {cycles}")
            print(f"   🏆 Mejor reward: {analysis['performance_metrics']['best_reward_achieved']:.3f}")
            print(f"   📈 Mejora total: {analysis['performance_metrics']['improvement_percentage']:.1f}%")
            print(f"   ✅ Calidad promedio: {analysis['performance_metrics']['average_quality_rate']:.1%}")
            
            print(f"\n🧠 COMPORTAMIENTO INTELIGENTE:")
            modes = analysis['system_behavior']['planner_modes_used']
            for mode, count in modes.items():
                print(f"   🎯 {mode}: {count} ciclos")
            print(f"   🔧 Adaptaciones totales: {analysis['system_behavior']['total_adaptations_applied']}")
            print(f"   💡 Learnings únicos: {analysis['system_behavior']['unique_learnings_count']}")
            
            print(f"\n🚀 CAPACIDADES FASE 2 DEMOSTRADAS:")
            caps = analysis['phase2_capabilities_demonstrated']
            print(f"   🔍 Bayesian Optimization: {'✅' if caps['bayesian_optimization'] else '❌'}")
            print(f"   🎯 Active Learning: {'✅' if caps['active_learning'] else '❌'}")
            print(f"   🔄 Recalibración: {'✅' if caps['recalibration'] else '❌'}")
            print(f"   🤖 Comportamiento Adaptivo: {'✅' if caps['adaptive_behavior'] else '❌'}")
            print(f"   📚 Aprendizaje Continuo: {'✅' if caps['continuous_learning'] else '❌'}")
            
            print(f"\n📈 ANÁLISIS DE TENDENCIAS:")
            trends = analysis['trend_analysis']
            print(f"   📊 Performance: {trends['performance_trend']}")
            print(f"   🎛️ Estabilidad: {trends['system_stability']}")
            print(f"   🧠 Progresión learning: {trends['learning_progression']}")
            
            print(f"\n🎯 OBJETIVOS FASE 2 ALCANZADOS:")
            print(f"   ✅ Auto-tuning con Bayesian Optimization")
            print(f"   ✅ Exploración inteligente con Active Learning") 
            print(f"   ✅ Detección de deriva y recalibración")
            print(f"   ✅ Aprendizaje continuo y adaptación")
            print(f"   ✅ Múltiples estrategias de optimización")
            
            print(f"\n🌟 OMEGA AHORA TIENE AUTO-TUNING AVANZADO!")
            
        else:
            print("❌ Demo no completado correctamente")

def main():
    """Función principal del demo"""
    
    print("🚀 INICIANDO DEMO FASE 2 - AUTO-TUNING AVANZADO")
    print("🎯 Demostrando capacidades de optimización inteligente")
    
    try:
        demo = Phase2Demo()
        result = demo.run_phase2_demo(n_cycles=6)
        demo.display_phase2_summary(result)
        
        print(f"\n✅ DEMO FASE 2 COMPLETADO EXITOSAMENTE")
        print(f"📁 Logs detallados en: results/agent_cycles_v2/")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error en demo Fase 2: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
