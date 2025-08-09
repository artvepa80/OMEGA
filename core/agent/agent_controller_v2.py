#!/usr/bin/env python3
"""
🤖 AGENT CONTROLLER V2 - Fase 2 del Sistema Agéntico
Controlador avanzado con capacidades completas de auto-tuning:
- Bayesian Optimization integrada
- Active Learning para exploración inteligente
- Drift Detection con recalibración automática
- Auto-retraining basado en performance
"""

import json
import time
import hashlib
import logging
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .planner_v2 import create_advanced_planner
from .executor import Executor
from .evaluator import Evaluator
from .memory import Memory
from .policies.bandit import UCB1Policy, ThompsonSamplingPolicy
from .critic import Critic

logger = logging.getLogger(__name__)

class AdvancedAgentController:
    """Controlador de agente avanzado con capacidades de Fase 2"""
    
    def __init__(self, cfg_path="config/agent_policy.json"):
        # Cargar configuración
        self.policy_cfg = json.loads(Path(cfg_path).read_text())
        
        # Componentes principales (V2)
        self.planner = create_advanced_planner(self.policy_cfg)
        self.executor = Executor()
        self.evaluator = Evaluator(self.policy_cfg)
        self.memory = Memory(Path("results/agent_memory_v2.parquet"))
        # Política de bandit configurable: 'ucb1' (default) o 'thompson'
        policy_name = str(self.policy_cfg.get("bandit_policy", "ucb1")).lower()
        if policy_name in ("thompson", "thompson_sampling"):
            self.policy = ThompsonSamplingPolicy()
        else:
            self.policy = UCB1Policy()
        self.critic = Critic()
        
        # Estado del controlador V2
        self.cycle_count = 0
        self.last_recalibration_time = None
        self.performance_window = []
        self.auto_retraining_enabled = True
        
        # Configuración avanzada
        self.advanced_config = {
            "max_cycles_per_day": 10,
            "min_interval_between_cycles": 300,  # 5 minutos
            "performance_degradation_threshold": 0.15,  # 15%
            "auto_recalibration_threshold": 0.20,  # 20%
            "max_consecutive_poor_performance": 3,
            "enable_bayesian_optimization": True,
            "enable_active_learning": True,
            "enable_drift_detection": True
        }
        
        logger.info("🤖 AdvancedAgentController V2 inicializado")
        logger.info(f"   🔧 Bayesian Optimization: {'✅' if self.advanced_config['enable_bayesian_optimization'] else '❌'}")
        logger.info(f"   🎯 Active Learning: {'✅' if self.advanced_config['enable_active_learning'] else '❌'}")
        logger.info(f"   📊 Drift Detection: {'✅' if self.advanced_config['enable_drift_detection'] else '❌'}")
    
    def _sig(self, cfg: dict) -> str:
        """Genera signature de configuración"""
        return hashlib.md5(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:10]
    
    def cycle_v2(self) -> Dict[str, Any]:
        """Ejecuta ciclo avanzado con capacidades de Fase 2"""
        
        cycle_start_time = datetime.now()
        self.cycle_count += 1
        
        logger.info(f"🔄 Iniciando Cycle V2 #{self.cycle_count}")
        
        try:
            # FASE 1: OBSERVE - Análisis de estado avanzado
            state = self._advanced_state_analysis()
            
            # FASE 2: PLAN - Generación de propuestas inteligentes
            candidates = self._advanced_planning(state)
            
            # FASE 3: ACT - Ejecución con monitoreo
            results = self._advanced_execution(candidates)
            
            # FASE 4: EVALUATE - Evaluación multi-criterio
            evaluation_result = self._advanced_evaluation(results)
            
            # FASE 5: LEARN - Aprendizaje y adaptación
            learning_result = self._advanced_learning(state, results, evaluation_result)
            
            # FASE 6: ADAPT - Auto-ajuste inteligente
            adaptation_result = self._intelligent_adaptation(evaluation_result, learning_result)
            
            cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
            
            # Compilar resultado del ciclo
            cycle_result = {
                "cycle_number": self.cycle_count,
                "timestamp": cycle_start_time.isoformat(),
                "duration_seconds": cycle_duration,
                "state_analysis": state,
                "candidates_generated": len(candidates),
                "execution_results": results,
                "evaluation": evaluation_result,
                "learning": learning_result,
                "adaptation": adaptation_result,
                "version": "v2"
            }
            
            # Guardar resultado del ciclo
            self._save_cycle_result(cycle_result)
            
            logger.info(f"✅ Cycle V2 #{self.cycle_count} completado en {cycle_duration:.1f}s")
            
            return cycle_result
            
        except Exception as e:
            logger.error(f"❌ Error en Cycle V2 #{self.cycle_count}: {e}")
            return {
                "cycle_number": self.cycle_count,
                "error": str(e),
                "timestamp": cycle_start_time.isoformat(),
                "version": "v2"
            }
    
    def _advanced_state_analysis(self) -> Dict[str, Any]:
        """Análisis avanzado de estado del sistema"""
        
        # Estado básico de memoria
        basic_state = self.memory.summarize(last_k=50)
        
        # Análisis de tendencias
        recent_rewards = basic_state.get("recent_rewards", [])
        performance_trend = self._analyze_performance_trend(recent_rewards)
        
        # Estado del planner
        planner_insights = self.planner.get_planner_insights()
        
        # Detección de necesidad de recalibración
        needs_recalibration = self._needs_recalibration(recent_rewards)
        
        advanced_state = {
            "basic_memory": basic_state,
            "performance_trend": performance_trend,
            "planner_insights": planner_insights,
            "needs_recalibration": needs_recalibration,
            "cycle_count": self.cycle_count,
            "last_recalibration": self.last_recalibration_time.isoformat() if self.last_recalibration_time else None,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"📊 Estado analizado:")
        logger.info(f"   📈 Trend: {performance_trend['trend_type']}")
        logger.info(f"   🎯 Planner mode: {planner_insights.get('current_mode', 'unknown')}")
        logger.info(f"   🔄 Needs recalibration: {'✅' if needs_recalibration else '❌'}")
        
        return advanced_state
    
    def _analyze_performance_trend(self, recent_rewards: List[float]) -> Dict[str, Any]:
        """Analiza tendencia de performance"""
        
        if len(recent_rewards) < 5:
            return {"trend_type": "insufficient_data", "confidence": 0.0}
        
        # Análisis de tendencia simple
        first_half = recent_rewards[:len(recent_rewards)//2]
        second_half = recent_rewards[len(recent_rewards)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        change_pct = (second_avg - first_avg) / first_avg * 100
        
        if change_pct > 10:
            trend_type = "improving"
        elif change_pct < -10:
            trend_type = "degrading"
        else:
            trend_type = "stable"
        
        return {
            "trend_type": trend_type,
            "change_percentage": change_pct,
            "first_half_avg": first_avg,
            "second_half_avg": second_avg,
            "confidence": min(len(recent_rewards) / 20, 1.0)
        }
    
    def _needs_recalibration(self, recent_rewards: List[float]) -> bool:
        """Determina si necesita recalibración"""
        
        if len(recent_rewards) < 10:
            return False
        
        # Verificar degradación significativa
        recent_avg = sum(recent_rewards[-5:]) / 5
        overall_avg = sum(recent_rewards) / len(recent_rewards)
        
        degradation = (overall_avg - recent_avg) / overall_avg
        
        # Verificar tiempo desde última recalibración
        time_since_recalibration = float('inf')
        if self.last_recalibration_time:
            time_since_recalibration = (datetime.now() - self.last_recalibration_time).days
        
        # Recalibrar si hay degradación significativa o ha pasado mucho tiempo
        return (degradation > self.advanced_config['auto_recalibration_threshold'] or 
                time_since_recalibration > 7)  # 7 días max
    
    def _advanced_planning(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Planificación avanzada con estrategias inteligentes"""
        
        n_candidates = self.policy_cfg["max_experiments_per_cycle"]
        
        # Usar planner V2 con capacidades avanzadas
        candidates = self.planner.propose(
            state["basic_memory"], 
            n=n_candidates,
            executor_fn=self.executor.run if self.advanced_config['enable_bayesian_optimization'] else None,
            evaluator_fn=self.evaluator.score if self.advanced_config['enable_bayesian_optimization'] else None
        )
        
        logger.info(f"🧠 Planner V2 generó {len(candidates)} candidatos")
        
        return candidates
    
    def _advanced_execution(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ejecución avanzada con monitoreo"""
        
        results = []
        
        for i, cfg in enumerate(candidates):
            logger.info(f"⚡ Ejecutando candidato {i+1}/{len(candidates)}")
            
            execution_start = datetime.now()
            
            # Ejecutar configuración
            run_out = self.executor.run(cfg)
            
            # Evaluar resultado
            eval_out = self.evaluator.score(run_out, baseline_profile=self.policy_cfg["baseline_profile"])
            
            execution_duration = (datetime.now() - execution_start).total_seconds()
            
            # Compilar resultado
            sig = self._sig(cfg)
            result = {
                "signature": sig,
                "config": cfg,
                "execution_output": run_out,
                "evaluation": eval_out,
                "execution_duration": execution_duration,
                "candidate_index": i
            }
            
            results.append(result)
            
            # Log en memoria
            self.memory.log(sig, cfg, run_out, eval_out)
            
            # Actualizar planner con resultado
            reward_value = eval_out.get("reward", 0.0) if isinstance(eval_out, dict) else 0.0
            self.planner.update_with_result(cfg, reward_value, self.cycle_count)
            
            logger.info(f"   ✅ Reward: {reward_value:.3f}, Duration: {execution_duration:.1f}s")
        
        return results
    
    def _advanced_evaluation(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluación multi-criterio avanzada"""
        
        if not results:
            return {"error": "No results to evaluate"}
        
        # Extracción de métricas
        rewards = []
        for r in results:
            eval_data = r.get("evaluation", {})
            if isinstance(eval_data, dict) and "reward" in eval_data:
                rewards.append(eval_data["reward"])
            else:
                rewards.append(0.0)
        quality_scores = []
        for r in results:
            eval_data = r.get("evaluation", {})
            if isinstance(eval_data, dict) and "quality_ok" in eval_data:
                quality_scores.append(1.0 if eval_data["quality_ok"] else 0.0)
            else:
                quality_scores.append(0.0)
        
        execution_times = [r.get("execution_duration", 0.0) for r in results]
        
        # Selección del mejor candidato usando UCB1
        arms = {}
        for r in results:
            eval_data = r.get("evaluation", {})
            if isinstance(eval_data, dict) and "reward" in eval_data:
                arms[r["signature"]] = eval_data["reward"]
            else:
                arms[r["signature"]] = 0.0
        chosen_sig = self.policy.select(arms)
        chosen_result = next(r for r in results if r["signature"] == chosen_sig)
        
        # Métricas avanzadas
        evaluation_result = {
            "chosen_signature": chosen_sig,
            "chosen_config": chosen_result["config"],
            "chosen_reward": (chosen_result.get("evaluation") or {}).get("reward", 0.0),
            "metrics": {
                "average_reward": sum(rewards) / len(rewards),
                "best_reward": max(rewards),
                "worst_reward": min(rewards),
                "reward_std": float(np.std(rewards)) if len(rewards) > 1 else 0.0,
                "quality_rate": sum(quality_scores) / len(quality_scores),
                "average_execution_time": sum(execution_times) / len(execution_times)
            },
            "performance_indicators": {
                "all_quality_ok": all(q == 1.0 for q in quality_scores),
                "significant_improvement": max(rewards) > 0.8,
                "consistent_performance": float(np.std(rewards)) < 0.1 if len(rewards) > 1 else True
            }
        }
        
        logger.info(f"⚖️ Evaluación completada:")
        logger.info(f"   🏆 Mejor reward: {evaluation_result['metrics']['best_reward']:.3f}")
        logger.info(f"   📊 Promedio: {evaluation_result['metrics']['average_reward']:.3f}")
        logger.info(f"   ✅ Quality rate: {evaluation_result['metrics']['quality_rate']:.1%}")
        
        return evaluation_result
    
    def _advanced_learning(self, state: Dict[str, Any], results: List[Dict[str, Any]], 
                          evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Aprendizaje avanzado con múltiples fuentes"""
        
        learning_insights = []
        
        # 1. Learning del planner
        planner_insights = self.planner.get_planner_insights()
        learning_insights.append({
            "source": "planner_v2",
            "insights": planner_insights
        })
        
        # 2. Learning de patrones de configuración
        config_patterns = self._analyze_config_patterns(results)
        learning_insights.append({
            "source": "config_patterns",
            "insights": config_patterns
        })
        
        # 3. Learning de performance
        performance_learning = self._analyze_performance_patterns(evaluation)
        learning_insights.append({
            "source": "performance_analysis",
            "insights": performance_learning
        })
        
        # Compilar resultado de learning
        learning_result = {
            "cycle_number": self.cycle_count,
            "learning_insights": learning_insights,
            "key_learnings": self._extract_key_learnings(learning_insights),
            "timestamp": datetime.now().isoformat()
        }
        
        return learning_result
    
    def _analyze_config_patterns(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza patrones en configuraciones exitosas"""
        
        successful_configs = []
        for r in results:
            eval_data = r.get("evaluation", {}) or {}
            reward_val = eval_data.get("reward", 0.0)
            if reward_val > 0.7:
                successful_configs.append(r)
        
        if not successful_configs:
            return {"pattern": "no_successful_configs"}
        
        # Analizar pesos de ensemble exitosos
        neural_weights = [c["config"]["ensemble_weights"]["neural_enhanced"] for c in successful_configs]
        svi_profiles = [c["config"]["svi_profile"] for c in successful_configs]
        
        return {
            "successful_count": len(successful_configs),
            "neural_weight_range": {
                "min": min(neural_weights),
                "max": max(neural_weights),
                "avg": sum(neural_weights) / len(neural_weights)
            },
            "popular_svi_profiles": list(set(svi_profiles)),
            "pattern": "neural_weight_correlation" if len(set(neural_weights)) > 1 else "stable_weights"
        }
    
    def _analyze_performance_patterns(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza patrones de performance"""
        
        metrics = evaluation.get("metrics", {})
        indicators = evaluation.get("performance_indicators", {})
        
        # Actualizar ventana de performance
        self.performance_window.append(metrics.get("best_reward", 0.5))
        if len(self.performance_window) > 20:
            self.performance_window = self.performance_window[-20:]
        
        # Análisis de tendencia en ventana
        if len(self.performance_window) >= 5:
            recent_performance = sum(self.performance_window[-5:]) / 5
            overall_performance = sum(self.performance_window) / len(self.performance_window)
            performance_trend = "improving" if recent_performance > overall_performance else "stable"
        else:
            performance_trend = "insufficient_data"
        
        return {
            "current_performance": metrics.get("best_reward", 0.5),
            "performance_trend": performance_trend,
            "consistency": "high" if indicators.get("consistent_performance", False) else "low",
            "quality_stability": "stable" if metrics.get("quality_rate", 0) > 0.8 else "unstable"
        }
    
    def _extract_key_learnings(self, learning_insights: List[Dict[str, Any]]) -> List[str]:
        """Extrae aprendizajes clave del ciclo"""
        
        key_learnings = []
        
        for insight in learning_insights:
            source = insight["source"]
            data = insight["insights"]
            
            if source == "planner_v2":
                mode = data.get("current_mode", "unknown")
                key_learnings.append(f"Planner operando en modo: {mode}")
                
                if data.get("successful_configs_count", 0) > 5:
                    key_learnings.append("Acumulando configuraciones exitosas")
            
            elif source == "config_patterns":
                if data.get("pattern") == "neural_weight_correlation":
                    avg_neural = data["neural_weight_range"]["avg"]
                    key_learnings.append(f"Neural weight óptimo cerca de {avg_neural:.2f}")
            
            elif source == "performance_analysis":
                trend = data.get("performance_trend", "unknown")
                if trend == "improving":
                    key_learnings.append("Performance en tendencia ascendente")
                elif trend == "stable":
                    key_learnings.append("Performance estable")
        
        return key_learnings
    
    def _intelligent_adaptation(self, evaluation: Dict[str, Any], learning: Dict[str, Any]) -> Dict[str, Any]:
        """Adaptación inteligente basada en learning"""
        
        adaptations_applied = []
        
        # 1. Aplicar mejor configuración
        chosen_config = evaluation.get("chosen_config")
        if chosen_config:
            self.executor.apply(chosen_config, guardrails=self.policy_cfg["guardrails"])
            adaptations_applied.append("applied_best_configuration")
        
        # 2. Reflexión del crítico
        results_for_critic = [
            (evaluation["chosen_signature"], {}, {}, evaluation["metrics"])
        ]
        self.critic.reflect(
            evaluation, results_for_critic, evaluation["chosen_signature"],
            out_path=Path("results/agent_decisions_v2.jsonl")
        )
        adaptations_applied.append("critic_reflection_logged")
        
        # 3. Auto-retraining si es necesario
        if self._should_trigger_retraining(evaluation, learning):
            retraining_result = self._trigger_auto_retraining()
            adaptations_applied.append(f"auto_retraining_{retraining_result}")
        
        # 4. Recalibración si es necesario
        if evaluation["metrics"]["quality_rate"] < 0.5:
            self.last_recalibration_time = datetime.now()
            adaptations_applied.append("recalibration_triggered")
        
        return {
            "adaptations_applied": adaptations_applied,
            "timestamp": datetime.now().isoformat()
        }
    
    def _should_trigger_retraining(self, evaluation: Dict[str, Any], learning: Dict[str, Any]) -> bool:
        """Determina si trigger auto-retraining"""
        
        if not self.auto_retraining_enabled:
            return False
        
        # Trigger si performance es consistentemente baja
        metrics = evaluation.get("metrics", {})
        return (metrics.get("best_reward", 0) < 0.6 and 
                metrics.get("quality_rate", 0) < 0.7)
    
    def _trigger_auto_retraining(self) -> str:
        """Trigger auto-retraining de modelos"""
        
        logger.info("🔄 Triggering auto-retraining...")
        
        # En implementación real, esto triggearía reentrenamiento de modelos
        # Por ahora, solo log
        retraining_config = {
            "triggered_at": datetime.now().isoformat(),
            "trigger_reason": "performance_degradation",
            "models_to_retrain": ["neural_enhanced", "transformer_deep"]
        }
        
        # Guardar configuración de retraining
        retraining_path = Path("results/auto_retraining_log.jsonl")
        with open(retraining_path, "a") as f:
            f.write(json.dumps(retraining_config) + "\n")
        
        return "scheduled"
    
    def _save_cycle_result(self, cycle_result: Dict[str, Any]):
        """Guarda resultado completo del ciclo"""
        
        results_dir = Path("results/agent_cycles_v2")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivo individual del ciclo
        cycle_file = results_dir / f"cycle_{self.cycle_count:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(cycle_file, 'w') as f:
            json.dump(cycle_result, f, indent=2, default=str)
        
        # Append a historial completo
        history_file = results_dir / "cycles_history.jsonl"
        with open(history_file, 'a') as f:
            f.write(json.dumps(cycle_result, default=str) + '\n')
    
    def run_forever_v2(self):
        """Ejecuta agente V2 en modo continuo"""
        
        interval = self.policy_cfg["schedule_seconds"]
        min_interval = self.advanced_config["min_interval_between_cycles"]
        max_cycles_per_day = self.advanced_config["max_cycles_per_day"]
        
        daily_cycle_count = 0
        last_cycle_date = datetime.now().date()
        
        logger.info(f"🚀 Iniciando Agent V2 en modo continuo...")
        logger.info(f"   ⏱️ Intervalo base: {interval}s")
        logger.info(f"   🔄 Max cycles/día: {max_cycles_per_day}")
        
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
                
                # Ejecutar ciclo V2
                cycle_result = self.cycle_v2()
                daily_cycle_count += 1
                
                # Determinar intervalo hasta próximo ciclo
                if cycle_result.get("error"):
                    sleep_time = interval * 2  # Más tiempo si hay error
                else:
                    sleep_time = max(interval, min_interval)
                
                logger.info(f"😴 Durmiendo {sleep_time}s hasta próximo ciclo...")
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logger.info("⏹️ Agent V2 detenido por usuario")
                break
            except Exception as e:
                logger.error(f"❌ Error en loop principal V2: {e}")
                time.sleep(interval)

# Función de conveniencia para crear controlador V2
def create_advanced_agent_controller(cfg_path: str = "config/agent_policy.json") -> AdvancedAgentController:
    """Crea controlador de agente avanzado V2"""
    return AdvancedAgentController(cfg_path)

if __name__ == "__main__":
    # Ejecutar agente V2 directamente
    controller = create_advanced_agent_controller()
    controller.run_forever_v2()
