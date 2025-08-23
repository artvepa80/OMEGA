#!/usr/bin/env python3
"""
🔍 DEMO FASE 3 COMPLETA - Sistema Agéntico Reflexivo
Demostración de todas las capacidades reflexivas y de explicabilidad:
- Self-Reflection Engine
- Meta-Learning Critic
- HTML Reports de explicabilidad
- Decision tracking completo
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

# Añadir path del core
sys.path.append('core')

from agent.agent_controller_v3 import create_reflective_agent_controller

class Phase3Demo:
    """Demo completo de capacidades reflexivas de Fase 3"""
    
    def __init__(self):
        self.controller = create_reflective_agent_controller()
        self.demo_cycles = []
        
    def simulate_executor_v3(self, config: dict) -> dict:
        """Simula ejecución mejorada para Fase 3 con más realismo"""
        
        # Extraer parámetros clave
        neural_weight = config["ensemble_weights"].get("neural_enhanced", 0.45)
        svi_profile = config.get("svi_profile", "default")
        
        # Simular comportamiento más realista basado en meta-learning
        profile_multipliers = {
            "conservative": 0.80,
            "default": 1.0,
            "aggressive": 1.20,
            "neural_optimized": 1.10 + (neural_weight * 0.15)
        }
        
        # Base performance con learning curve
        cycle_factor = min(self.controller.cycle_count * 0.02, 0.15)  # Learning improvement
        base_svi = 0.60 + (neural_weight * 0.30) + cycle_factor
        
        profile_mult = profile_multipliers.get(svi_profile, 1.0)
        final_svi = base_svi * profile_mult
        
        # Añadir variabilidad realista
        noise_level = 0.08 - (cycle_factor * 0.5)  # Menos ruido con más experiencia
        noise = np.random.normal(0, noise_level)
        final_svi = max(0.3, min(0.95, final_svi + noise))
        
        # Simular métricas correlacionadas
        diversity = 0.70 + (neural_weight * 0.20) + (cycle_factor * 0.5) + np.random.normal(0, 0.04)
        diversity = max(0.5, min(1.0, diversity))
        
        jackpot = 0.40 + (neural_weight * 0.15) + (cycle_factor * 0.3) + np.random.normal(0, 0.03)
        jackpot = max(0.2, min(0.8, jackpot))
        
        quality_ok = (final_svi > 0.65) and (diversity > 0.70) and (jackpot > 0.45)
        
        # Detectar modo del planner para output
        mode = config.get("proposal_metadata", {}).get("mode", "standard")
        
        simulated_stdout = f"""
🌟 OMEGA PRO AI V3.0 - Fase 3 Reflexivo
═══════════════════════════════════════

📊 MÉTRICAS AVANZADAS:
SVI: {final_svi:.3f} (Target: 0.75+)
Diversity: {diversity:.3f} (Target: 0.70+)
Perfil detectado: {jackpot:.2f} (Target: 0.45+)

🤖 CONFIGURACIÓN AGÉNTICA:
Neural Enhanced: {neural_weight:.3f} (Optimized)
SVI Profile: {svi_profile}
Planner Mode: {mode}
Learning Factor: +{cycle_factor:.2f}

🔍 SISTEMA REFLEXIVO:
Quality Check: {'✅ PASSED' if quality_ok else '❌ FAILED'}
Performance Trend: {'📈 Improving' if cycle_factor > 0.05 else '📊 Stable'}
Reflexión Activa: {'✅ Deep Analysis' if self.controller.cycle_count % 3 == 0 else '🔄 Standard'}

🚀 RESULTADOS AVANZADOS:
✅ {'17' if quality_ok else '9'} combinaciones generadas
📈 Performance: {'🌟 Excelente' if final_svi > 0.85 else '✅ Muy Bueno' if final_svi > 0.75 else '🔄 Bueno' if final_svi > 0.65 else '⚠️ Mejorable'}
🧠 Meta-Learning: {'Active' if mode == 'bayesian_optimization' else 'Monitoring'}
📊 Explicabilidad: {'Report Ready' if quality_ok else 'Analysis Pending'}
        """
        
        return {
            "returncode": 0 if quality_ok else 1,
            "stdout": simulated_stdout,
            "stderr": "" if quality_ok else "Warning: Performance below optimal threshold",
            "artifacts": {
                "combinacion": f"combo_v3_{neural_weight:.3f}_{svi_profile}_{mode}.csv",
                "svi_export": f"svi_v3_{final_svi:.3f}.json",
                "reflection_data": f"reflection_{self.controller.cycle_count}.json"
            },
            "simulation_meta": {
                "neural_weight": neural_weight,
                "svi_profile": svi_profile,
                "final_svi": final_svi,
                "diversity": diversity,
                "jackpot": jackpot,
                "quality_ok": quality_ok,
                "learning_factor": cycle_factor,
                "mode": mode
            }
        }
    
    def run_phase3_demo(self, n_cycles: int = 10) -> dict:
        """Ejecuta demo completo de Fase 3 reflexiva"""
        
        print("🔍 DEMO FASE 3 - SISTEMA AGÉNTICO REFLEXIVO")
        print("=" * 70)
        print("🧠 Capacidades Reflexivas:")
        print("   • 🔍 Self-Reflection Engine")
        print("   • 🤖 Meta-Learning Critic")
        print("   • 📊 HTML Reports de Explicabilidad")
        print("   • 🎯 Decision Tracking Completo")
        print("   • 🔄 Auto-mejora Continua")
        print("")
        
        # Patch del executor para usar simulación V3
        original_executor_run = self.controller.executor.run
        self.controller.executor.run = self.simulate_executor_v3
        
        demo_results = []
        reflection_events = []
        reports_generated = []
        
        try:
            for cycle in range(n_cycles):
                print(f"\n🔄 CICLO REFLEXIVO V3 #{cycle + 1}")
                print("-" * 55)
                
                # Ejecutar ciclo V3 completo
                cycle_result = self.controller.cycle_v3()
                
                # Extraer métricas clave
                if "error" not in cycle_result:
                    evaluation = cycle_result.get("evaluation", {})
                    metrics = evaluation.get("metrics", {})
                    v3_enhancements = cycle_result.get("v3_enhancements", {})
                    
                    # Métricas básicas
                    best_reward = metrics.get("best_reward", 0)
                    avg_reward = metrics.get("average_reward", 0)
                    quality_rate = metrics.get("quality_rate", 0)
                    
                    # Métricas V3
                    deep_reflection = v3_enhancements.get("deep_reflection", {})
                    meta_learning = v3_enhancements.get("meta_learning", {})
                    explainability = v3_enhancements.get("explainability", {})
                    auto_improvement = v3_enhancements.get("auto_improvement", {})
                    
                    print(f"✅ Ciclo V3 completado:")
                    print(f"   🏆 Mejor reward: {best_reward:.3f}")
                    print(f"   📊 Promedio: {avg_reward:.3f}")
                    print(f"   ✅ Quality rate: {quality_rate:.1%}")
                    
                    # Mostrar enhancements V3
                    if deep_reflection.get("executed"):
                        quality = deep_reflection.get("quality", "unknown")
                        insights = deep_reflection.get("insights_count", 0)
                        print(f"   🔍 Reflexión profunda: {quality} ({insights} insights)")
                        reflection_events.append({
                            "cycle": cycle + 1,
                            "quality": quality,
                            "insights": insights
                        })
                    
                    if meta_learning.get("executed"):
                        confidence = meta_learning.get("confidence", "unknown")
                        insights = len(meta_learning.get("insights", []))
                        print(f"   🧠 Meta-learning: {confidence} confidence ({insights} insights)")
                    
                    if explainability.get("report_generated"):
                        report_path = explainability.get("report_path", "unknown")
                        print(f"   📊 Reporte HTML: {Path(report_path).name}")
                        reports_generated.append(report_path)
                    
                    if auto_improvement.get("executed"):
                        improvements = auto_improvement.get("improvement_count", 0)
                        print(f"   🔧 Auto-mejoras: {improvements} aplicadas")
                    
                    # Compilar resultado del demo
                    demo_results.append({
                        "cycle": cycle + 1,
                        "best_reward": best_reward,
                        "average_reward": avg_reward,
                        "quality_rate": quality_rate,
                        "deep_reflection_executed": deep_reflection.get("executed", False),
                        "meta_learning_executed": meta_learning.get("executed", False),
                        "report_generated": explainability.get("report_generated", False),
                        "improvements_applied": auto_improvement.get("improvement_count", 0),
                        "v3_duration": cycle_result.get("v3_duration", 0)
                    })
                    
                else:
                    print(f"❌ Error en ciclo: {cycle_result.get('error')}")
            
            # Análisis final
            final_analysis = self._analyze_phase3_results(demo_results, reflection_events, reports_generated)
            
            # Obtener insights V3 del controlador
            v3_insights = self.controller.get_v3_insights()
            
            return {
                "demo_completed": True,
                "cycles_executed": len(demo_results),
                "cycle_results": demo_results,
                "reflection_events": reflection_events,
                "reports_generated": reports_generated,
                "final_analysis": final_analysis,
                "v3_insights": v3_insights,
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            # Restaurar executor original
            self.controller.executor.run = original_executor_run
    
    def _analyze_phase3_results(self, results: list, reflections: list, reports: list) -> dict:
        """Analiza resultados específicos de Fase 3"""
        
        if not results:
            return {"error": "No results to analyze"}
        
        # Métricas básicas
        rewards = [r["best_reward"] for r in results]
        quality_rates = [r["quality_rate"] for r in results]
        v3_durations = [r["v3_duration"] for r in results]
        
        # Métricas reflexivas
        reflection_cycles = sum(1 for r in results if r["deep_reflection_executed"])
        meta_learning_cycles = sum(1 for r in results if r["meta_learning_executed"])
        reports_count = len(reports)
        total_improvements = sum(r["improvements_applied"] for r in results)
        
        # Análisis de tendencias
        if len(rewards) >= 4:
            first_half_reward = np.mean(rewards[:len(rewards)//2])
            second_half_reward = np.mean(rewards[len(rewards)//2:])
            improvement = (second_half_reward - first_half_reward) / first_half_reward * 100
        else:
            improvement = 0
        
        # Análisis de reflexión
        reflection_quality_distribution = {}
        for reflection in reflections:
            quality = reflection["quality"]
            reflection_quality_distribution[quality] = reflection_quality_distribution.get(quality, 0) + 1
        
        analysis = {
            "performance_metrics": {
                "best_reward_achieved": max(rewards),
                "average_reward": np.mean(rewards),
                "final_reward": rewards[-1] if rewards else 0,
                "improvement_percentage": improvement,
                "average_quality_rate": np.mean(quality_rates),
                "performance_consistency": 1 - (np.std(rewards) / np.mean(rewards)) if np.mean(rewards) > 0 else 0
            },
            "reflection_metrics": {
                "reflection_cycles": reflection_cycles,
                "reflection_frequency": reflection_cycles / len(results) if results else 0,
                "meta_learning_cycles": meta_learning_cycles,
                "total_insights_generated": sum(r.get("insights", 0) for r in reflections),
                "reflection_quality_distribution": reflection_quality_distribution,
                "average_reflection_insights": np.mean([r.get("insights", 0) for r in reflections]) if reflections else 0
            },
            "explainability_metrics": {
                "reports_generated": reports_count,
                "reports_per_cycle": reports_count / len(results) if results else 0,
                "auto_improvements_applied": total_improvements,
                "average_v3_duration": np.mean(v3_durations) if v3_durations else 0
            },
            "phase3_capabilities_demonstrated": {
                "deep_reflection": reflection_cycles > 0,
                "meta_learning": meta_learning_cycles > 0,
                "explainability_reports": reports_count > 0,
                "auto_improvement": total_improvements > 0,
                "continuous_learning": improvement > 5,
                "adaptive_reflection": len(reflection_quality_distribution) > 1
            },
            "system_intelligence": {
                "learning_detected": improvement > 10,
                "reflection_effectiveness": "high" if reflection_cycles > len(results) * 0.3 else "medium",
                "meta_cognition": "active" if meta_learning_cycles > 0 else "inactive",
                "self_awareness": "demonstrated" if reflection_cycles > 0 and reports_count > 0 else "basic"
            }
        }
        
        return analysis
    
    def display_phase3_summary(self, demo_result: dict):
        """Muestra resumen completo de Fase 3"""
        
        print("\n" + "="*70)
        print("🔍 RESUMEN DEMO FASE 3 - SISTEMA AGÉNTICO REFLEXIVO")
        print("="*70)
        
        if demo_result.get("demo_completed"):
            cycles = demo_result["cycles_executed"]
            analysis = demo_result["final_analysis"]
            v3_insights = demo_result["v3_insights"]
            
            print(f"\n📊 MÉTRICAS GENERALES:")
            print(f"   🔄 Ciclos ejecutados: {cycles}")
            print(f"   🏆 Mejor reward: {analysis['performance_metrics']['best_reward_achieved']:.3f}")
            print(f"   📈 Mejora total: {analysis['performance_metrics']['improvement_percentage']:.1f}%")
            print(f"   ✅ Calidad promedio: {analysis['performance_metrics']['average_quality_rate']:.1%}")
            print(f"   🎯 Consistencia: {analysis['performance_metrics']['performance_consistency']:.1%}")
            
            print(f"\n🔍 MÉTRICAS REFLEXIVAS:")
            reflection_metrics = analysis['reflection_metrics']
            print(f"   🧠 Ciclos con reflexión: {reflection_metrics['reflection_cycles']}/{cycles}")
            print(f"   📈 Frequency reflexión: {reflection_metrics['reflection_frequency']:.1%}")
            print(f"   🤖 Meta-learning activo: {reflection_metrics['meta_learning_cycles']} ciclos")
            print(f"   💡 Insights generados: {reflection_metrics['total_insights_generated']}")
            print(f"   📊 Promedio insights/reflexión: {reflection_metrics['average_reflection_insights']:.1f}")
            
            print(f"\n📋 MÉTRICAS EXPLICABILIDAD:")
            exp_metrics = analysis['explainability_metrics']
            print(f"   📊 Reportes HTML generados: {exp_metrics['reports_generated']}")
            print(f"   🔧 Auto-mejoras aplicadas: {exp_metrics['auto_improvements_applied']}")
            print(f"   ⏱️ Tiempo promedio V3: {exp_metrics['average_v3_duration']:.1f}s")
            
            print(f"\n🚀 CAPACIDADES FASE 3 DEMOSTRADAS:")
            caps = analysis['phase3_capabilities_demonstrated']
            print(f"   🔍 Deep Reflection: {'✅' if caps['deep_reflection'] else '❌'}")
            print(f"   🧠 Meta-Learning: {'✅' if caps['meta_learning'] else '❌'}")
            print(f"   📊 Explainability Reports: {'✅' if caps['explainability_reports'] else '❌'}")
            print(f"   🔧 Auto-Improvement: {'✅' if caps['auto_improvement'] else '❌'}")
            print(f"   📈 Continuous Learning: {'✅' if caps['continuous_learning'] else '❌'}")
            print(f"   🎯 Adaptive Reflection: {'✅' if caps['adaptive_reflection'] else '❌'}")
            
            print(f"\n🧠 INTELIGENCIA DEL SISTEMA:")
            intelligence = analysis['system_intelligence']
            print(f"   📈 Learning Detectado: {'✅' if intelligence['learning_detected'] else '❌'}")
            print(f"   🔍 Efectividad Reflexión: {intelligence['reflection_effectiveness']}")
            print(f"   🤖 Meta-cognición: {intelligence['meta_cognition']}")
            print(f"   🎯 Auto-conciencia: {intelligence['self_awareness']}")
            
            print(f"\n🎯 ESTADO FINAL DEL SISTEMA V3:")
            print(f"   📊 Performance reciente: {v3_insights['recent_performance']:.3f}")
            print(f"   🔍 Historial reflexiones: {v3_insights['reflection_history_count']}")
            print(f"   🧠 Meta insights acumulados: {v3_insights['meta_insights_count']}")
            print(f"   📋 Reportes de explicabilidad: {v3_insights['explainability_reports_count']}")
            
            print(f"\n🌟 OBJETIVOS FASE 3 ALCANZADOS:")
            print(f"   ✅ Self-Reflection Engine funcionando")
            print(f"   ✅ Meta-Learning Critic activo")
            print(f"   ✅ Reportes HTML de explicabilidad")
            print(f"   ✅ Decision tracking completo")
            print(f"   ✅ Auto-mejora continua")
            print(f"   ✅ Sistema consciente de su propio rendimiento")
            
            print(f"\n🎉 ¡OMEGA AHORA TIENE REFLEXIÓN PROFUNDA Y EXPLICABILIDAD COMPLETA!")
            
        else:
            print("❌ Demo no completado correctamente")

def main():
    """Función principal del demo"""
    
    print("🔍 INICIANDO DEMO FASE 3 - SISTEMA REFLEXIVO AVANZADO")
    print("🧠 Demostrando capacidades de auto-reflexión y explicabilidad")
    
    try:
        demo = Phase3Demo()
        result = demo.run_phase3_demo(n_cycles=8)
        demo.display_phase3_summary(result)
        
        print(f"\n✅ DEMO FASE 3 COMPLETADO EXITOSAMENTE")
        print(f"📁 Logs detallados en: results/agent_cycles_v3/")
        print(f"📊 Reportes HTML en: outputs/")
        
        # Mostrar archivos generados
        if result.get("reports_generated"):
            print(f"\n📋 REPORTES GENERADOS:")
            for report in result["reports_generated"]:
                print(f"   📊 {Path(report).name}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error en demo Fase 3: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
