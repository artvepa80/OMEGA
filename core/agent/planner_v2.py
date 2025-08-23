#!/usr/bin/env python3
"""
🧠 PLANNER V2 - Fase 2 del Sistema Agéntico
Planner avanzado que integra:
- Bayesian Optimization para hiperparámetros críticos
- Active Learning para exploración inteligente  
- Drift Detection para trigger de recalibración
"""

import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import copy
import random

from .bayesian_optimizer import create_bayesian_optimizer
from .active_learner import create_active_learner
from .drift_detector import create_drift_detector

logger = logging.getLogger(__name__)

class AdvancedPlanner:
    """Planner avanzado con capacidades de Fase 2"""
    
    def __init__(self, policy_cfg: dict):
        self.policy_cfg = policy_cfg
        
        # Componentes de Fase 2
        self.bayesian_optimizer = None
        self.active_learner = create_active_learner("uncertainty_sampling")
        self.drift_detector = create_drift_detector()
        
        # Estado del planner
        self.optimization_mode = "exploration"  # exploration, optimization, recalibration
        self.trials_since_last_optimization = 0
        self.trials_since_last_recalibration = 0
        
        # Configuraciones conocidas exitosas
        self.successful_configs = []
        self.baseline_config = self._get_baseline_config()
        
        logger.info("🧠 AdvancedPlanner V2 inicializado")
        logger.info(f"   🎯 Modo inicial: {self.optimization_mode}")
    
    def propose(self, state: dict, n: int = 3, executor_fn=None, evaluator_fn=None) -> List[Dict[str, Any]]:
        """Genera propuestas usando estrategias avanzadas de Fase 2"""
        
        # Actualizar detector de deriva con estado actual
        self._update_drift_detection(state)
        
        # Determinar modo de operación
        self._determine_operation_mode(state)
        
        # Generar propuestas según modo
        if self.optimization_mode == "bayesian_optimization":
            proposals = self._generate_bayesian_proposals(n, executor_fn, evaluator_fn)
        
        elif self.optimization_mode == "active_learning":
            proposals = self._generate_active_learning_proposals(n)
        
        elif self.optimization_mode == "recalibration":
            proposals = self._generate_recalibration_proposals(n)
        
        else:  # exploration (fallback)
            proposals = self._generate_exploration_proposals(n)
        
        # Añadir metadatos a propuestas
        for i, proposal in enumerate(proposals):
            proposal["proposal_metadata"] = {
                "mode": self.optimization_mode,
                "proposal_id": f"{self.optimization_mode}_{i}",
                "timestamp": datetime.now().isoformat(),
                "planner_version": "v2"
            }
        
        logger.info(f"🧠 Generadas {len(proposals)} propuestas en modo: {self.optimization_mode}")
        
        return proposals
    
    def _update_drift_detection(self, state: dict):
        """Actualiza detector de deriva con estado actual"""
        
        recent_rewards = state.get("recent_rewards", [])
        
        if recent_rewards:
            # Simular métricas para drift detection (en producción vendrían del estado)
            recent_reward = recent_rewards[-1] if recent_rewards else 0.7
            svi = 0.75  # Placeholder
            diversity = 0.8  # Placeholder
            quality_ok = recent_reward > 0.6
            
            # Simular combinaciones (en producción vendrían del estado)
            mock_combinations = [
                [random.randint(1, 40) for _ in range(6)] for _ in range(3)
            ]
            
            drift_result = self.drift_detector.add_episode(
                recent_reward, svi, diversity, quality_ok, mock_combinations
            )
            
            if drift_result.get("overall_drift"):
                logger.warning("🚨 Deriva detectada - Cambiando a modo recalibración")
                self.optimization_mode = "recalibration"
    
    def _determine_operation_mode(self, state: dict):
        """Determina modo de operación basado en estado y métricas"""
        
        recent_rewards = state.get("recent_rewards", [])
        n_episodes = state.get("n", 0)
        
        # Verificar si necesitamos recalibración
        should_recalibrate, recal_details = self.drift_detector.should_trigger_recalibration()
        
        if should_recalibrate:
            self.optimization_mode = "recalibration"
            self.trials_since_last_recalibration = 0
            logger.info("🔄 Modo: RECALIBRATION - Deriva detectada")
            return
        
        # Determinar entre Bayesian Optimization y Active Learning
        if n_episodes < 10:
            self.optimization_mode = "active_learning"
            logger.info("🎯 Modo: ACTIVE_LEARNING - Fase inicial")
        
        elif n_episodes < 50 and self.trials_since_last_optimization > 15:
            self.optimization_mode = "bayesian_optimization"
            self.trials_since_last_optimization = 0
            logger.info("🔍 Modo: BAYESIAN_OPTIMIZATION - Optimización dirigida")
        
        else:
            self.optimization_mode = "active_learning"
            logger.info("🎯 Modo: ACTIVE_LEARNING - Exploración continua")
        
        self.trials_since_last_optimization += 1
        self.trials_since_last_recalibration += 1
    
    def _generate_bayesian_proposals(self, n: int, executor_fn, evaluator_fn) -> List[Dict[str, Any]]:
        """Genera propuestas usando Bayesian Optimization"""
        
        # Inicializar optimizador si es necesario
        if self.bayesian_optimizer is None:
            self.bayesian_optimizer = create_bayesian_optimizer()
        
        proposals = []
        
        # Si tenemos ejecutor y evaluador, usar optimización real
        if executor_fn and evaluator_fn:
            logger.info("🔍 Ejecutando Bayesian Optimization real...")
            
            # Ejecutar pocas iteraciones para no bloquear
            optimization_result = self.bayesian_optimizer.optimize(
                executor_fn, evaluator_fn, 
                optimization_target="ensemble",
                n_trials=n,
                timeout=300  # 5 minutos max
            )
            
            # Usar mejor configuración encontrada
            best_config = optimization_result["best_config"]
            proposals.append(best_config)
            
            # Generar variaciones de la mejor
            for i in range(n - 1):
                variation = self._create_variation(best_config, variation_strength=0.1)
                proposals.append(variation)
        
        else:
            # Fallback: generar propuestas simuladas bayesianas
            logger.info("🔍 Generando propuestas bayesianas simuladas...")
            
            for i in range(n):
                proposal = self._generate_bayesian_inspired_config(i)
                proposals.append(proposal)
        
        return proposals
    
    def _generate_active_learning_proposals(self, n: int) -> List[Dict[str, Any]]:
        """Genera propuestas usando Active Learning"""
        
        # Generar candidatos base
        candidates = []
        for i in range(n * 2):  # Generar más candidatos para selección
            candidate = self._generate_random_variation()
            candidates.append(candidate)
        
        # Usar Active Learning para seleccionar mejores candidatos
        proposals = []
        for i in range(n):
            if candidates:
                selected = self.active_learner.select_next_configuration(candidates, i)
                proposals.append(selected)
                
                # Remover candidato seleccionado para evitar duplicados
                candidates = [c for c in candidates if c != selected]
        
        return proposals
    
    def _generate_recalibration_proposals(self, n: int) -> List[Dict[str, Any]]:
        """Genera propuestas para recalibración después de deriva"""
        
        proposals = []
        
        # 1. Configuración conservadora (baseline)
        conservative_config = self._get_baseline_config()
        conservative_config["svi_profile"] = "conservative"
        proposals.append(conservative_config)
        
        # 2. Configuración con neural weight reducido (más estable)
        stable_config = copy.deepcopy(conservative_config)
        stable_config["ensemble_weights"]["neural_enhanced"] = 0.35
        stable_config["ensemble_weights"]["transformer_deep"] = 0.25
        # Renormalizar
        total = sum(stable_config["ensemble_weights"].values())
        stable_config["ensemble_weights"] = {
            k: v/total for k, v in stable_config["ensemble_weights"].items()
        }
        proposals.append(stable_config)
        
        # 3. Generar configuraciones adicionales explorando rangos seguros
        for i in range(n - 2):
            safe_config = self._generate_safe_exploration_config()
            proposals.append(safe_config)
        
        return proposals
    
    def _generate_exploration_proposals(self, n: int) -> List[Dict[str, Any]]:
        """Genera propuestas de exploración básica (fallback)"""
        
        proposals = []
        for i in range(n):
            proposal = self._generate_random_variation()
            proposals.append(proposal)
        
        return proposals
    
    def _generate_bayesian_inspired_config(self, iteration: int) -> Dict[str, Any]:
        """Genera configuración inspirada en Bayesian Optimization"""
        
        # Simular suggestions de Bayesian optimizer
        base_config = self._get_baseline_config()
        
        # Variar neural_enhanced con bias hacia valores altos (bayesian learning)
        neural_weight = np.random.beta(3, 2) * 0.6 + 0.2  # Bias hacia 0.6-0.8
        
        base_config["ensemble_weights"]["neural_enhanced"] = neural_weight
        
        # Ajustar otros pesos
        remaining_weight = 1.0 - neural_weight
        other_models = [k for k in base_config["ensemble_weights"].keys() if k != "neural_enhanced"]
        
        # Distribuir peso restante
        weights = np.random.dirichlet([1] * len(other_models)) * remaining_weight
        for i, model in enumerate(other_models):
            base_config["ensemble_weights"][model] = weights[i]
        
        # SVI profile optimizado
        profiles = ["neural_optimized", "default", "aggressive"]
        base_config["svi_profile"] = np.random.choice(profiles, p=[0.5, 0.3, 0.2])
        
        return base_config
    
    def _generate_random_variation(self) -> Dict[str, Any]:
        """Genera variación aleatoria del baseline"""
        
        base_config = self._get_baseline_config()
        
        # Variar pesos aleatoriamente
        weights = base_config["ensemble_weights"]
        for model in weights.keys():
            # Variación ±20%
            current = weights[model]
            variation = np.random.uniform(-0.2, 0.2) * current
            weights[model] = max(0.01, current + variation)
        
        # Renormalizar
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}
        base_config["ensemble_weights"] = weights
        
        # SVI profile aleatorio
        profiles = ["conservative", "default", "aggressive", "neural_optimized"]
        base_config["svi_profile"] = np.random.choice(profiles)
        
        return base_config
    
    def _generate_safe_exploration_config(self) -> Dict[str, Any]:
        """Genera configuración de exploración segura post-deriva"""
        
        config = self._get_baseline_config()
        
        # Usar rangos conservadores
        neural_weight = np.random.uniform(0.3, 0.5)  # Rango más conservador
        config["ensemble_weights"]["neural_enhanced"] = neural_weight
        
        # Distribuir resto conservadoramente
        remaining = 1.0 - neural_weight
        config["ensemble_weights"]["transformer_deep"] = remaining * 0.4
        config["ensemble_weights"]["genetico"] = remaining * 0.35
        config["ensemble_weights"]["analizador_200"] = remaining * 0.25
        
        # Profile conservador
        config["svi_profile"] = np.random.choice(["conservative", "default"], p=[0.7, 0.3])
        
        return config
    
    def _create_variation(self, base_config: Dict[str, Any], variation_strength: float = 0.1) -> Dict[str, Any]:
        """Crea variación de una configuración base"""
        
        varied_config = copy.deepcopy(base_config)
        
        # Variar ensemble weights
        weights = varied_config["ensemble_weights"]
        for model in weights.keys():
            current = weights[model]
            max_variation = current * variation_strength
            variation = np.random.uniform(-max_variation, max_variation)
            weights[model] = max(0.01, current + variation)
        
        # Renormalizar
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}
        varied_config["ensemble_weights"] = weights
        
        return varied_config
    
    def _get_baseline_config(self) -> Dict[str, Any]:
        """Retorna configuración baseline"""
        
        return {
            "svi_profile": self.policy_cfg.get("baseline_profile", "default"),
            "ensemble_weights": {
                "neural_enhanced": 0.45,
                "transformer_deep": 0.15,
                "genetico": 0.15,
                "analizador_200": 0.12,
                "montecarlo": 0.05,
                "lstm_v2": 0.03,
                "clustering": 0.01
            },
            "filters": {"max_consecutivos": 3, "par_impar_balance": True},
            "seeds": [None]
        }
    
    def update_with_result(self, config: Dict[str, Any], reward: float, trial_number: int):
        """Actualiza planner con resultado de ejecución"""
        
        # Actualizar Active Learning
        self.active_learner.update_with_result(config, reward, trial_number)
        
        # Guardar configuraciones exitosas
        if reward > 0.7:  # Threshold para "exitoso"
            self.successful_configs.append({
                "config": config,
                "reward": reward,
                "trial": trial_number,
                "timestamp": datetime.now().isoformat()
            })
            
            # Mantener solo últimas 20 configs exitosas
            if len(self.successful_configs) > 20:
                self.successful_configs = self.successful_configs[-20:]
        
        # Log estadísticas cada 10 trials
        if trial_number % 10 == 0:
            self._log_planner_statistics(trial_number)
    
    def _log_planner_statistics(self, trial_number: int):
        """Log estadísticas del planner"""
        
        logger.info(f"🧠 Planner V2 Stats (Trial {trial_number}):")
        logger.info(f"   🎯 Modo actual: {self.optimization_mode}")
        logger.info(f"   🏆 Configs exitosas: {len(self.successful_configs)}")
        logger.info(f"   🔄 Trials desde recalibración: {self.trials_since_last_recalibration}")
        
        # Estadísticas de Active Learning
        al_insights = self.active_learner.get_learning_insights()
        if not al_insights.get("error"):
            logger.info(f"   🎯 AL exploration ratio: {al_insights['exploration_ratio']:.1%}")
            logger.info(f"   📈 AL best reward: {al_insights['best_reward']:.3f}")
    
    def get_planner_insights(self) -> Dict[str, Any]:
        """Obtiene insights completos del planner V2"""
        
        # Combinar insights de todos los componentes
        al_insights = self.active_learner.get_learning_insights()
        drift_status = self.drift_detector.performance_detector.get_drift_status()
        
        # Estadísticas propias
        successful_rewards = [c.get("reward", 0.0) for c in self.successful_configs]
        
        return {
            "planner_version": "v2",
            "current_mode": self.optimization_mode,
            "trials_since_recalibration": self.trials_since_last_recalibration,
            "successful_configs_count": len(self.successful_configs),
            "best_successful_reward": max(successful_rewards) if successful_rewards else 0,
            "active_learning": al_insights,
            "drift_detection": drift_status,
            "bayesian_optimizer_available": self.bayesian_optimizer is not None,
            "timestamp": datetime.now().isoformat()
        }

# Función de conveniencia para migración desde Planner V1
def create_advanced_planner(policy_cfg: dict) -> AdvancedPlanner:
    """Crea Planner V2 con capacidades avanzadas"""
    return AdvancedPlanner(policy_cfg)

if __name__ == '__main__':
    # Test básico
    print("🧠 Testing Advanced Planner V2...")
    
    policy_cfg = {"baseline_profile": "default"}
    planner = create_advanced_planner(policy_cfg)
    
    # Simular varios cycles
    for trial in range(15):
        state = {"recent_rewards": [0.7 + np.random.normal(0, 0.05) for _ in range(5)], "n": trial}
        
        proposals = planner.propose(state, n=3)
        
        # Simular ejecución del mejor proposal
        best_proposal = proposals[0]
        simulated_reward = 0.6 + np.random.random() * 0.3
        
        planner.update_with_result(best_proposal, simulated_reward, trial)
        
        if trial % 5 == 0:
            print(f"   Trial {trial}: Mode = {planner.optimization_mode}, Reward = {simulated_reward:.3f}")
    
    # Obtener insights finales
    insights = planner.get_planner_insights()
    
    print(f"✅ Test completado:")
    print(f"   🎯 Modo final: {insights['current_mode']}")
    print(f"   🏆 Configs exitosas: {insights['successful_configs_count']}")
    print(f"   📈 Mejor reward: {insights['best_successful_reward']:.3f}")
    print(f"   🔍 Bayesian disponible: {insights['bayesian_optimizer_available']}")
