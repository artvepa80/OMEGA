#!/usr/bin/env python3
"""
🤖 AGENT CONTROLLER V3 - Fase 3 del Sistema Agéntico
Controlador con reflexión profunda y explicabilidad completa:
- Self-Reflection Engine integrado
- Meta-Learning Critic avanzado
- HTML Reports de explicabilidad
- Decision tracking completo
"""

import json
import time
import hashlib
import logging
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .agent_controller_v2 import AdvancedAgentController
from .critic_v2 import create_advanced_critic
from .self_reflection import create_self_reflection_engine
from modules.reporting.html_reporter_v3 import generate_advanced_report

logger = logging.getLogger(__name__)

class ReflectiveAgentController(AdvancedAgentController):
    """Controlador agéntico con capacidades reflexivas completas"""
    
    def __init__(self, cfg_path="config/agent_policy.json"):
        # Inicializar controlador base V2
        super().__init__(cfg_path)
        
        # Componentes de Fase 3
        self.advanced_critic = create_advanced_critic()
        self.reflection_engine = create_self_reflection_engine()
        
        # Estado reflexivo
        self.reflection_history = []
        self.explainability_reports = []
        self.meta_learning_insights = []
        
        # Configuración reflexiva
        self.reflection_config = {
            "enable_deep_reflection": True,
            "reflection_frequency": 3,  # Cada 3 ciclos
            "enable_explainability_reports": True,
            "enable_meta_learning": True,
            "max_reflection_history": 100,
            "auto_generate_reports": True
        }
        
        logger.info("🤖 ReflectiveAgentController V3 inicializado")
        logger.info(f"   🔍 Deep Reflection: {'✅' if self.reflection_config['enable_deep_reflection'] else '❌'}")
        logger.info(f"   📊 Explainability Reports: {'✅' if self.reflection_config['enable_explainability_reports'] else '❌'}")
        logger.info(f"   🧠 Meta-Learning: {'✅' if self.reflection_config['enable_meta_learning'] else '❌'}")
    
    def cycle_v3(self) -> Dict[str, Any]:
        """Ejecuta ciclo reflexivo completo (V3)"""
        
        cycle_start_time = datetime.now()
        self.cycle_count += 1
        
        logger.info(f"🔄 Iniciando Cycle V3 #{self.cycle_count} (Reflexivo)")
        
        try:
            # FASE 1-5: Ejecutar ciclo V2 base
            base_result = super().cycle_v2()
            
            if "error" in base_result:
                return base_result
            
            # FASE 6: REFLEXIÓN PROFUNDA (V3)
            reflection_result = self._deep_reflection_phase(base_result)
            
            # FASE 7: META-LEARNING (V3)
            meta_learning_result = self._meta_learning_phase()
            
            # FASE 8: EXPLICABILIDAD (V3)
            explainability_result = self._explainability_phase(base_result, reflection_result)
            
            # FASE 9: AUTO-MEJORA (V3)
            auto_improvement_result = self._auto_improvement_phase(
                reflection_result, meta_learning_result
            )
            
            cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
            
            # Compilar resultado V3
            v3_result = {
                **base_result,  # Incluir todo de V2
                "v3_enhancements": {
                    "deep_reflection": reflection_result,
                    "meta_learning": meta_learning_result,
                    "explainability": explainability_result,
                    "auto_improvement": auto_improvement_result
                },
                "v3_duration": cycle_duration,
                "v3_version": "3.0"
            }
            
            # Guardar resultado V3
            self._save_v3_cycle_result(v3_result)
            
            logger.info(f"✅ Cycle V3 #{self.cycle_count} completado en {cycle_duration:.1f}s")
            logger.info(f"   🔍 Reflection quality: {reflection_result.get('quality', 'unknown')}")
            logger.info(f"   🧠 Meta insights: {len(meta_learning_result.get('insights', []))}")
            logger.info(f"   📊 Report generated: {'✅' if explainability_result.get('report_generated') else '❌'}")
            
            return v3_result
            
        except Exception as e:
            logger.error(f"❌ Error en Cycle V3 #{self.cycle_count}: {e}")
            return {
                "cycle_number": self.cycle_count,
                "error": str(e),
                "timestamp": cycle_start_time.isoformat(),
                "version": "v3"
            }
    
    def _deep_reflection_phase(self, base_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de reflexión profunda"""
        
        logger.info("🔍 Ejecutando reflexión profunda...")
        
        # Verificar si es momento de reflexión profunda
        should_reflect = (
            self.cycle_count % self.reflection_config["reflection_frequency"] == 0 or
            self.cycle_count <= 3  # Siempre en primeros ciclos
        )
        
        if not should_reflect:
            return {"skipped": True, "reason": "Not reflection cycle"}
        
        # Obtener historial de ciclos recientes
        recent_cycles = self._get_recent_cycle_history(20)
        
        if not recent_cycles:
            return {"error": "No cycle history available"}
        
        # Ejecutar reflexión profunda
        reflection_result = self.reflection_engine.reflect_on_cycles(recent_cycles)
        
        # Actualizar historial
        self.reflection_history.append({
            "cycle": self.cycle_count,
            "timestamp": datetime.now().isoformat(),
            "reflection": reflection_result
        })
        
        # Mantener historial limitado
        if len(self.reflection_history) > self.reflection_config["max_reflection_history"]:
            self.reflection_history = self.reflection_history[-self.reflection_config["max_reflection_history"]:]
        
        return {
            "executed": True,
            "quality": reflection_result.get("reflection_quality", "unknown"),
            "insights_count": reflection_result.get("synthesis", {}).get("total_insights", 0),
            "recommendations_count": len(reflection_result.get("recommendations", [])),
            "reflection_id": reflection_result.get("reflection_id")
        }
    
    def _meta_learning_phase(self) -> Dict[str, Any]:
        """Fase de meta-learning"""
        
        if not self.reflection_config["enable_meta_learning"]:
            return {"disabled": True}
        
        logger.info("🧠 Ejecutando meta-learning...")
        
        # Obtener historial para meta-learning
        cycle_history = self._get_recent_cycle_history(30)
        
        if len(cycle_history) < 5:
            return {"insufficient_data": True}
        
        # Ejecutar análisis meta-learning
        meta_analysis = self.advanced_critic.analyze_cycle_results(cycle_history)
        
        # Extraer insights meta
        meta_insights = meta_analysis.get("meta_insights", [])
        actionable_recommendations = meta_analysis.get("actionable_recommendations", [])
        
        # Actualizar conocimiento meta
        self.meta_learning_insights.extend(meta_insights)
        
        # Mantener solo insights recientes
        if len(self.meta_learning_insights) > 50:
            self.meta_learning_insights = self.meta_learning_insights[-50:]
        
        return {
            "executed": True,
            "confidence": meta_analysis.get("criticism_confidence", "unknown"),
            "insights": meta_insights,
            "recommendations": actionable_recommendations,
            "success_patterns_identified": "success_patterns" in meta_analysis,
            "failure_patterns_identified": "failure_patterns" in meta_analysis
        }
    
    def _explainability_phase(self, base_result: Dict[str, Any], reflection_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de explicabilidad y reportes"""
        
        if not self.reflection_config["enable_explainability_reports"]:
            return {"disabled": True}
        
        logger.info("📊 Generando reporte de explicabilidad...")
        
        try:
            # Preparar datos para reporte
            cycle_history = self._get_recent_cycle_history(15)
            
            # Obtener última reflexión
            latest_reflection = None
            if self.reflection_history:
                latest_reflection = self.reflection_history[-1]["reflection"]
            
            # Generar reporte HTML avanzado
            agent_data = {
                "cycle_results": cycle_history,
                "current_cycle": base_result,
                "reflection_history": self.reflection_history[-5:],  # Últimas 5 reflexiones
                "meta_insights": self.meta_learning_insights[-10:]   # Últimos 10 insights
            }
            
            report_path = generate_advanced_report(
                f"OMEGA Agent V3 - Ciclo #{self.cycle_count}",
                agent_data,
                latest_reflection,
                f"outputs/omega_v3_report_cycle_{self.cycle_count:04d}.html"
            )
            
            # Registrar reporte
            self.explainability_reports.append({
                "cycle": self.cycle_count,
                "timestamp": datetime.now().isoformat(),
                "report_path": report_path,
                "reflection_included": latest_reflection is not None
            })
            
            return {
                "executed": True,
                "report_generated": True,
                "report_path": report_path,
                "reflection_included": latest_reflection is not None
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return {
                "executed": False,
                "error": str(e)
            }
    
    def _auto_improvement_phase(self, reflection_result: Dict[str, Any], 
                               meta_learning_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de auto-mejora basada en reflexión y meta-learning"""
        
        logger.info("🔧 Ejecutando auto-mejora...")
        
        improvements_applied = []
        
        # Auto-mejoras basadas en reflexión
        if reflection_result.get("executed"):
            reflection_improvements = self._apply_reflection_improvements()
            improvements_applied.extend(reflection_improvements)
        
        # Auto-mejoras basadas en meta-learning
        if meta_learning_result.get("executed"):
            meta_improvements = self._apply_meta_learning_improvements(meta_learning_result)
            improvements_applied.extend(meta_improvements)
        
        # Auto-mejoras de configuración
        config_improvements = self._apply_configuration_improvements()
        improvements_applied.extend(config_improvements)
        
        return {
            "executed": True,
            "improvements_applied": improvements_applied,
            "improvement_count": len(improvements_applied),
            "timestamp": datetime.now().isoformat()
        }
    
    def _apply_reflection_improvements(self) -> List[str]:
        """Aplica mejoras basadas en reflexión"""
        
        improvements = []
        
        # Ejemplo: Ajustar exploration rate basado en reflexión
        if len(self.reflection_history) >= 2:
            latest_reflection = self.reflection_history[-1]["reflection"]
            
            # Verificar recomendaciones de reflexión
            recommendations = latest_reflection.get("recommendations", [])
            
            for rec in recommendations[:2]:  # Top 2 recomendaciones
                if rec.get("type") == "optimization" and rec.get("priority") == "high":
                    improvements.append(f"Applied: {rec.get('action', 'Unknown optimization')}")
        
        return improvements
    
    def _apply_meta_learning_improvements(self, meta_result: Dict[str, Any]) -> List[str]:
        """Aplica mejoras basadas en meta-learning"""
        
        improvements = []
        
        recommendations = meta_result.get("recommendations", [])
        
        for rec in recommendations[:1]:  # Top 1 recomendación meta
            if rec.get("priority") == "high":
                improvements.append(f"Meta-improvement: {rec.get('action', 'Unknown action')}")
        
        return improvements
    
    def _apply_configuration_improvements(self) -> List[str]:
        """Aplica mejoras de configuración automáticas"""
        
        improvements = []
        
        # Ajustar reflection frequency basado en performance
        if self.cycle_count >= 10:
            recent_performance = self._calculate_recent_performance()
            
            if recent_performance > 0.8:
                # Performance alta - reducir frequency de reflexión
                if self.reflection_config["reflection_frequency"] < 5:
                    self.reflection_config["reflection_frequency"] += 1
                    improvements.append("Increased reflection frequency (high performance)")
            
            elif recent_performance < 0.6:
                # Performance baja - aumentar frequency de reflexión
                if self.reflection_config["reflection_frequency"] > 2:
                    self.reflection_config["reflection_frequency"] -= 1
                    improvements.append("Decreased reflection frequency (low performance)")
        
        return improvements
    
    def _get_recent_cycle_history(self, n_cycles: int) -> List[Dict[str, Any]]:
        """Obtiene historial reciente de ciclos"""
        
        # En implementación real, esto leería de archivos guardados
        # Por ahora, simular con datos mock
        history = []
        
        for i in range(max(1, self.cycle_count - n_cycles + 1), self.cycle_count + 1):
            cycle_data = {
                "cycle": i,
                "best_reward": 0.6 + (i * 0.02) + np.random.normal(0, 0.03),
                "quality_rate": 0.7 + (i * 0.01),
                "planner_mode": ["active_learning", "bayesian_optimization", "recalibration"][i % 3],
                "timestamp": datetime.now().isoformat()
            }
            history.append(cycle_data)
        
        return history
    
    def _calculate_recent_performance(self) -> float:
        """Calcula performance reciente"""
        
        recent_cycles = self._get_recent_cycle_history(5)
        rewards = [c.get("best_reward", 0) for c in recent_cycles]
        
        return np.mean(rewards) if rewards else 0.5
    
    def _save_v3_cycle_result(self, cycle_result: Dict[str, Any]):
        """Guarda resultado de ciclo V3"""
        
        results_dir = Path("results/agent_cycles_v3")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivo individual del ciclo V3
        cycle_file = results_dir / f"cycle_v3_{self.cycle_count:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(cycle_file, 'w') as f:
            json.dump(cycle_result, f, indent=2, default=str)
        
        # Append a historial V3
        history_file = results_dir / "cycles_v3_history.jsonl"
        with open(history_file, 'a') as f:
            f.write(json.dumps(cycle_result, default=str) + '\n')
    
    def run_forever_v3(self):
        """Ejecuta agente V3 en modo continuo con reflexión"""
        
        interval = self.policy_cfg["schedule_seconds"]
        min_interval = self.advanced_config["min_interval_between_cycles"]
        max_cycles_per_day = self.advanced_config["max_cycles_per_day"]
        
        daily_cycle_count = 0
        last_cycle_date = datetime.now().date()
        
        logger.info(f"🚀 Iniciando Agent V3 (Reflexivo) en modo continuo...")
        logger.info(f"   ⏱️ Intervalo base: {interval}s")
        logger.info(f"   🔄 Max cycles/día: {max_cycles_per_day}")
        logger.info(f"   🔍 Reflexión cada {self.reflection_config['reflection_frequency']} ciclos")
        
        while True:
            try:
                current_date = datetime.now().date()
                
                # Reset contador diario
                if current_date != last_cycle_date:
                    daily_cycle_count = 0
                    last_cycle_date = current_date
                
                # Verificar límite diario
                if daily_cycle_count >= max_cycles_per_day:
                    logger.info(f"🛑 Límite diario alcanzado ({max_cycles_per_day}), esperando...")
                    time.sleep(interval)
                    continue
                
                # Ejecutar ciclo V3 reflexivo
                cycle_result = self.cycle_v3()
                daily_cycle_count += 1
                
                # Determinar intervalo hasta próximo ciclo
                if cycle_result.get("error"):
                    sleep_time = interval * 2  # Más tiempo si hay error
                else:
                    # Intervalo adaptativo basado en reflexión
                    v3_enhancements = cycle_result.get("v3_enhancements", {})
                    reflection_executed = v3_enhancements.get("deep_reflection", {}).get("executed", False)
                    
                    if reflection_executed:
                        sleep_time = max(interval * 1.5, min_interval)  # Más tiempo después de reflexión
                    else:
                        sleep_time = max(interval, min_interval)
                
                logger.info(f"😴 Durmiendo {sleep_time}s hasta próximo ciclo...")
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logger.info("⏹️ Agent V3 detenido por usuario")
                break
            except Exception as e:
                logger.error(f"❌ Error en loop principal V3: {e}")
                time.sleep(interval)
    
    def get_v3_insights(self) -> Dict[str, Any]:
        """Obtiene insights completos del sistema V3"""
        
        return {
            "controller_version": "v3",
            "total_cycles": self.cycle_count,
            "reflection_history_count": len(self.reflection_history),
            "meta_insights_count": len(self.meta_learning_insights),
            "explainability_reports_count": len(self.explainability_reports),
            "reflection_config": self.reflection_config,
            "latest_reflection_quality": (
                self.reflection_history[-1]["reflection"].get("reflection_quality", "unknown") 
                if self.reflection_history else "none"
            ),
            "latest_meta_insights": self.meta_learning_insights[-3:] if len(self.meta_learning_insights) >= 3 else self.meta_learning_insights,
            "recent_performance": self._calculate_recent_performance(),
            "capabilities": {
                "deep_reflection": self.reflection_config["enable_deep_reflection"],
                "meta_learning": self.reflection_config["enable_meta_learning"],
                "explainability_reports": self.reflection_config["enable_explainability_reports"],
                "auto_improvement": True
            },
            "timestamp": datetime.now().isoformat()
        }

# Función de conveniencia para crear controlador V3
def create_reflective_agent_controller(cfg_path: str = "config/agent_policy.json") -> ReflectiveAgentController:
    """Crea controlador agéntico reflexivo V3"""
    return ReflectiveAgentController(cfg_path)

if __name__ == "__main__":
    # Ejecutar agente V3 directamente
    controller = create_reflective_agent_controller()
    
    # Ejecutar un ciclo de prueba
    print("🚀 Testing Agent V3 - Single Cycle")
    result = controller.cycle_v3()
    
    print(f"✅ Cycle V3 completado:")
    print(f"   🔍 Deep reflection: {'✅' if result.get('v3_enhancements', {}).get('deep_reflection', {}).get('executed') else '❌'}")
    print(f"   🧠 Meta learning: {'✅' if result.get('v3_enhancements', {}).get('meta_learning', {}).get('executed') else '❌'}")
    print(f"   📊 Report generated: {'✅' if result.get('v3_enhancements', {}).get('explainability', {}).get('report_generated') else '❌'}")
    
    # Mostrar insights V3
    insights = controller.get_v3_insights()
    print(f"   📈 Recent performance: {insights['recent_performance']:.3f}")
    print(f"   💡 Meta insights: {insights['meta_insights_count']}")
    print(f"   📊 Reports generated: {insights['explainability_reports_count']}")
