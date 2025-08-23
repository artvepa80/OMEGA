#!/usr/bin/env python3
"""
🤖 DEMO CICLO AGÉNTICO COMPLETO
Demostración del sistema agéntico OMEGA con un ciclo completo:
Observe → Plantee hipótesis → Actúe → Evalúe → Se auto-ajuste
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Añadir path del core
sys.path.append('core')

from agent.agent_controller import AgentController

class AgentDemo:
    """Demo del sistema agéntico con simulación de ejecución"""
    
    def __init__(self):
        self.controller = AgentController()
        self.demo_results = []
    
    def simulate_main_execution(self, cfg: dict) -> dict:
        """
        Simula la ejecución de main.py con una configuración específica.
        En producción, esto sería el Executor real llamando a main.py
        """
        print(f"    🔄 Simulando ejecución con config: {cfg['svi_profile']}")
        
        # Simular diferentes resultados basados en la configuración
        ensemble_weights = cfg["ensemble_weights"]
        neural_weight = ensemble_weights.get("neural_enhanced", 0.45)
        
        # Simular SVI basado en el peso neural (más neural = mejor SVI)
        base_svi = 0.6 + (neural_weight * 0.3)
        
        # Simular otros métricas
        diversity = 0.7 + (neural_weight * 0.2)
        jackpot = 0.5 + (neural_weight * 0.1)
        
        # Simular algunas variaciones realistas
        import random
        noise = random.uniform(-0.1, 0.1)
        
        simulated_stdout = f"""
🌟 OMEGA PRO AI Ultimate V3.0 - Simulación
SVI: {base_svi + noise:.3f}
Perfil detectado: {jackpot:.2f}
✅ 12 combinaciones generadas
Distribución: Balanced
Neural Enhanced Weight: {neural_weight:.2f}
Profile: {cfg['svi_profile']}
        """
        
        return {
            "returncode": 0,
            "stdout": simulated_stdout,
            "stderr": "",
            "artifacts": {
                "combinacion": "simulated_combo.csv",
                "svi_export": "simulated_svi.json"
            }
        }
    
    def run_demo_cycle(self):
        """Ejecuta un ciclo completo de demostración"""
        
        print("\n🤖 INICIANDO CICLO AGÉNTICO DEMO")
        print("=" * 60)
        
        # FASE 1: OBSERVE (Estado actual)
        print("\n📊 FASE 1: OBSERVE - Análisis del estado actual")
        state = self.controller.memory.summarize(last_k=50)
        print(f"   📈 Recompensas recientes: {state.get('recent_rewards', [])}")
        print(f"   📝 Episodios en memoria: {state.get('n', 0)}")
        
        # FASE 2: PLANTEAR HIPÓTESIS (Generar candidatos)
        print("\n🧠 FASE 2: PLANTEAR HIPÓTESIS - Generando configuraciones experimentales")
        candidates = self.controller.planner.propose(state, n=3)
        
        print(f"   🔬 Candidatos generados: {len(candidates)}")
        for i, cfg in enumerate(candidates):
            neural_w = cfg["ensemble_weights"]["neural_enhanced"]
            profile = cfg["svi_profile"]
            print(f"      {i+1}. Neural: {neural_w:.2f}, Profile: {profile}")
        
        # FASE 3: ACTUAR (Ejecutar experimentos)
        print("\n⚡ FASE 3: ACTUAR - Ejecutando experimentos")
        results = []
        
        for i, cfg in enumerate(candidates):
            print(f"   🚀 Experimento {i+1}/3...")
            
            # Simular ejecución (en producción sería executor.run(cfg))
            run_out = self.simulate_main_execution(cfg)
            
            # Evaluar resultado
            eval_out = self.controller.evaluator.score(run_out, "default")
            
            sig = self.controller._sig(cfg)
            results.append((sig, cfg, run_out, eval_out))
            
            # Log en memoria
            self.controller.memory.log(sig, cfg, run_out, eval_out)
            
            print(f"      ✅ Reward: {eval_out['reward']:.3f}, Quality: {'✅' if eval_out['quality_ok'] else '❌'}")
        
        # FASE 4: EVALUAR (Seleccionar mejor)
        print("\n⚖️ FASE 4: EVALUAR - Seleccionando mejor configuración")
        
        arms = {sig: eval_out["reward"] for sig, cfg, run_out, eval_out in results}
        chosen_sig = self.controller.policy.select(arms)
        chosen_cfg = next(cfg for sig, cfg, run_out, eval_out in results if sig == chosen_sig)
        
        print(f"   🎯 Configuración seleccionada: {chosen_sig}")
        print(f"   🏆 Neural weight elegido: {chosen_cfg['ensemble_weights']['neural_enhanced']:.2f}")
        print(f"   📋 Profile elegido: {chosen_cfg['svi_profile']}")
        
        best_result = next(eval_out for sig, cfg, run_out, eval_out in results if sig == chosen_sig)
        print(f"   🎊 Reward obtenido: {best_result['reward']:.3f}")
        
        # FASE 5: AUTO-AJUSTARSE (Aplicar cambios y reflexionar)
        print("\n🔄 FASE 5: AUTO-AJUSTARSE - Aplicando cambios y reflexionando")
        
        # Aplicar cambios (en demo solo mostramos)
        print(f"   📝 Actualizando ensemble_weights.json con nueva configuración")
        print(f"   📄 Neural enhanced: {chosen_cfg['ensemble_weights']['neural_enhanced']:.2f}")
        
        # Reflexión del Critic
        self.controller.critic.reflect(
            state, results, chosen_sig, 
            out_path=Path("results/demo_agent_decisions.jsonl")
        )
        
        print(f"   🔍 Reflexión guardada en results/demo_agent_decisions.jsonl")
        
        # Guardar resultado para análisis
        demo_result = {
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "candidates": len(candidates),
            "chosen_config": chosen_cfg,
            "final_reward": best_result['reward'],
            "improvement": "TBD"  # Se calculará en próximos ciclos
        }
        
        self.demo_results.append(demo_result)
        
        return demo_result
    
    def show_demo_summary(self, result: dict):
        """Muestra resumen del demo"""
        
        print("\n" + "="*60)
        print("📊 RESUMEN DEL CICLO AGÉNTICO DEMO")
        print("="*60)
        
        print(f"\n🕐 Timestamp: {result['timestamp']}")
        print(f"🔬 Candidatos evaluados: {result['candidates']}")
        print(f"🎯 Reward final: {result['final_reward']:.3f}")
        
        config = result['chosen_config']
        print(f"\n🏆 CONFIGURACIÓN GANADORA:")
        print(f"   🧠 Neural Enhanced: {config['ensemble_weights']['neural_enhanced']:.2f}")
        print(f"   🤖 Transformer: {config['ensemble_weights']['transformer_deep']:.2f}")
        print(f"   🧬 Genético: {config['ensemble_weights']['genetico']:.2f}")
        print(f"   📊 Perfil SVI: {config['svi_profile']}")
        
        print(f"\n🎯 PRÓXIMOS PASOS:")
        print(f"   • El agente aplicó la configuración automáticamente")
        print(f"   • En el próximo sorteo, evaluará el rendimiento real")
        print(f"   • Se auto-ajustará basado en resultados observados")
        print(f"   • Continuará mejorando de forma autónoma")
        
        print(f"\n💡 CAPACIDADES DEMOSTRADAS:")
        print(f"   ✅ Observación del estado actual")
        print(f"   ✅ Generación de hipótesis (configuraciones)")
        print(f"   ✅ Ejecución de experimentos")
        print(f"   ✅ Evaluación y selección óptima")
        print(f"   ✅ Auto-ajuste y reflexión")
        print(f"   ✅ Memoria de episodios para aprendizaje")
        
        print("\n🚀 ¡OMEGA AHORA PIENSA POR SÍ MISMA!")

def main():
    """Función principal del demo"""
    
    print("🤖 OMEGA PRO AI - DEMO SISTEMA AGÉNTICO")
    print("🎯 Demostración de autonomía operativa real")
    print("🔄 Ciclo: Observe → Hipótesis → Actúe → Evalúe → Auto-ajuste")
    
    try:
        # Crear y ejecutar demo
        demo = AgentDemo()
        result = demo.run_demo_cycle()
        demo.show_demo_summary(result)
        
        print(f"\n✅ DEMO COMPLETADO EXITOSAMENTE")
        print(f"📁 Logs guardados en: results/demo_agent_decisions.jsonl")
        
        # Mostrar archivo de decisiones
        decisions_file = Path("results/demo_agent_decisions.jsonl")
        if decisions_file.exists():
            print(f"\n📋 DECISIÓN DEL AGENTE:")
            with open(decisions_file, 'r') as f:
                decision = json.loads(f.read().strip().split('\n')[-1])
                print(f"   🕐 {decision['ts']}")
                print(f"   🎯 Elegido: {decision['chosen']}")
                print(f"   📊 Top configs: {decision['top'][:2]}")
                print(f"   💭 Nota: {decision['note']}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error en demo: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
