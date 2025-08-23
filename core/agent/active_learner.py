#!/usr/bin/env python3
"""
🎯 ACTIVE LEARNER - Fase 2 del Sistema Agéntico
Sistema de aprendizaje activo que identifica configuraciones prometedoras
y dirige la optimización hacia áreas de mayor potencial de mejora
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class UncertaintyEstimator:
    """Estima incertidumbre en predicciones para guiar exploración"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.historical_configs = []
        self.historical_rewards = []
        self.feature_names = []
        
    def add_observation(self, config: Dict[str, Any], reward: float):
        """Añade observación de config-reward para entrenamiento"""
        
        # Extraer features de la configuración
        features = self._extract_features(config)
        
        self.historical_configs.append(features)
        self.historical_rewards.append(reward)
        
        if len(self.historical_configs) > 100:
            # Mantener solo últimas 100 observaciones
            self.historical_configs = self.historical_configs[-100:]
            self.historical_rewards = self.historical_rewards[-100:]
    
    def _extract_features(self, config: Dict[str, Any]) -> List[float]:
        """Extrae features numéricas de una configuración"""
        
        features = []
        feature_names = []
        
        # Features de ensemble weights
        if "ensemble_weights" in config:
            weights = config["ensemble_weights"]
            for model_name in sorted(weights.keys()):
                features.append(weights[model_name])
                feature_names.append(f"weight_{model_name}")
        
        # Features de neural params
        if "neural_params" in config:
            neural = config["neural_params"]
            for param_name in sorted(neural.keys()):
                if isinstance(neural[param_name], (int, float)):
                    features.append(float(neural[param_name]))
                    feature_names.append(f"neural_{param_name}")
        
        # Features de filter params
        if "filter_params" in config:
            filters = config["filter_params"]
            for param_name in sorted(filters.keys()):
                if isinstance(filters[param_name], (int, float)):
                    features.append(float(filters[param_name]))
                    feature_names.append(f"filter_{param_name}")
        
        # Feature de SVI profile (encoded)
        if "svi_profile" in config:
            profile_encoding = {
                "conservative": 0.8,
                "default": 0.6,
                "aggressive": 0.3,
                "neural_optimized": 0.45
            }
            features.append(profile_encoding.get(config["svi_profile"], 0.5))
            feature_names.append("svi_profile_encoded")
        
        # Guardar nombres de features la primera vez
        if not self.feature_names:
            self.feature_names = feature_names
        
        return features
    
    def estimate_uncertainty(self, config: Dict[str, Any]) -> float:
        """Estima incertidumbre de una configuración no vista"""
        
        if len(self.historical_configs) < 5:
            return 1.0  # Máxima incertidumbre si hay pocos datos
        
        # Extraer features de la config
        config_features = self._extract_features(config)
        
        # Convertir a arrays numpy
        X_historical = np.array(self.historical_configs)
        x_new = np.array(config_features).reshape(1, -1)
        
        try:
            # Escalar features
            X_scaled = self.scaler.fit_transform(X_historical)
            x_new_scaled = self.scaler.transform(x_new)
            
            # Calcular distancia a vecinos más cercanos
            distances = np.linalg.norm(X_scaled - x_new_scaled, axis=1)
            min_distance = np.min(distances)
            
            # Convertir distancia a incertidumbre [0, 1]
            # Mayor distancia = mayor incertidumbre
            uncertainty = min(min_distance / 2.0, 1.0)
            
            return float(uncertainty)
            
        except Exception as e:
            logger.warning(f"Error estimando incertidumbre: {e}")
            return 0.5  # Incertidumbre media como fallback

class ExplorationStrategy:
    """Estrategias de exploración para Active Learning"""
    
    def __init__(self, strategy: str = "uncertainty_sampling"):
        self.strategy = strategy
        self.uncertainty_estimator = UncertaintyEstimator()
        
    def score_candidates(self, candidates: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """Scores candidatos según estrategia de exploración"""
        
        scored_candidates = []
        
        for candidate in candidates:
            if self.strategy == "uncertainty_sampling":
                score = self.uncertainty_estimator.estimate_uncertainty(candidate)
            
            elif self.strategy == "diversity_sampling":
                score = self._calculate_diversity_score(candidate, candidates)
            
            elif self.strategy == "expected_improvement":
                score = self._calculate_expected_improvement(candidate)
            
            else:  # random baseline
                score = np.random.random()
            
            scored_candidates.append((candidate, score))
        
        # Ordenar por score descendente (mayor score = más prometedor)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        return scored_candidates
    
    def _calculate_diversity_score(self, candidate: Dict[str, Any], all_candidates: List[Dict[str, Any]]) -> float:
        """Calcula score de diversidad vs otros candidatos"""
        
        try:
            candidate_features = self.uncertainty_estimator._extract_features(candidate)
            
            total_distance = 0
            count = 0
            
            for other in all_candidates:
                if other != candidate:
                    other_features = self.uncertainty_estimator._extract_features(other)
                    if len(candidate_features) == len(other_features):
                        distance = np.linalg.norm(
                            np.array(candidate_features) - np.array(other_features)
                        )
                        total_distance += distance
                        count += 1
            
            return total_distance / max(count, 1)
            
        except Exception:
            return 0.5
    
    def _calculate_expected_improvement(self, candidate: Dict[str, Any]) -> float:
        """Calcula expected improvement usando historical data"""
        
        if len(self.uncertainty_estimator.historical_rewards) < 3:
            return 0.5
        
        # Simple heuristic: uncertainty * potential_reward
        uncertainty = self.uncertainty_estimator.estimate_uncertainty(candidate)
        max_reward_seen = max(self.uncertainty_estimator.historical_rewards)
        
        # Expected improvement = uncertainty * (max_reward + buffer)
        expected_improvement = uncertainty * (max_reward_seen + 0.1)
        
        return min(expected_improvement, 1.0)
    
    def update_with_result(self, config: Dict[str, Any], reward: float):
        """Actualiza estrategia con nuevo resultado"""
        self.uncertainty_estimator.add_observation(config, reward)

class ActiveLearningCoordinator:
    """Coordinador principal del sistema de Active Learning"""
    
    def __init__(self, 
                 strategy: str = "uncertainty_sampling",
                 exploration_rate: float = 0.3,
                 min_exploration_trials: int = 5):
        
        self.strategy = strategy
        self.exploration_rate = exploration_rate
        self.min_exploration_trials = min_exploration_trials
        
        self.exploration_strategy = ExplorationStrategy(strategy)
        self.trial_history = []
        self.exploration_count = 0
        self.exploitation_count = 0
        
        logger.info(f"🎯 ActiveLearningCoordinator inicializado: {strategy}")
    
    def should_explore(self, trial_number: int) -> bool:
        """Decide si explorar o explotar en este trial"""
        
        # Forzar exploración en primeros trials
        if trial_number < self.min_exploration_trials:
            return True
        
        # Exploration rate con decay
        current_exploration_rate = self.exploration_rate * (0.95 ** (trial_number // 10))
        
        # Decisión estocástica
        return np.random.random() < current_exploration_rate
    
    def select_next_configuration(self, 
                                candidates: List[Dict[str, Any]], 
                                trial_number: int) -> Dict[str, Any]:
        """Selecciona próxima configuración usando Active Learning"""
        
        if self.should_explore(trial_number):
            # EXPLORAR: Usar estrategia de exploración
            logger.info(f"🔍 Trial {trial_number}: EXPLORATION")
            
            scored_candidates = self.exploration_strategy.score_candidates(candidates)
            selected_config = scored_candidates[0][0]  # Mejor score de exploración
            
            self.exploration_count += 1
            selection_type = "exploration"
            
        else:
            # EXPLOTAR: Usar mejor configuración conocida o bayesian optimization
            logger.info(f"💰 Trial {trial_number}: EXPLOITATION")
            
            # Si tenemos historia, usar la mejor configuración vista
            if self.trial_history:
                best_trial = max(self.trial_history, key=lambda t: t["reward"])
                selected_config = best_trial["config"]
                
                # Añadir pequeña variación para no quedarse stuck
                selected_config = self._add_small_variation(selected_config)
            else:
                # Fallback a candidato aleatorio
                selected_config = np.random.choice(candidates)
            
            self.exploitation_count += 1
            selection_type = "exploitation"
        
        # Log selección
        self._log_selection(trial_number, selected_config, selection_type)
        
        return selected_config
    
    def _add_small_variation(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Añade pequeña variación a una configuración base"""
        
        import copy
        varied_config = copy.deepcopy(base_config)
        
        # Variar ensemble weights ligeramente
        if "ensemble_weights" in varied_config:
            weights = varied_config["ensemble_weights"]
            
            # Seleccionar peso aleatorio para variar
            weight_keys = list(weights.keys())
            key_to_vary = np.random.choice(weight_keys)
            
            # Variación pequeña ±5%
            current_weight = weights[key_to_vary]
            variation = np.random.uniform(-0.05, 0.05)
            new_weight = np.clip(current_weight + variation, 0.01, 0.8)
            
            weights[key_to_vary] = new_weight
            
            # Renormalizar
            total_weight = sum(weights.values())
            weights = {k: v/total_weight for k, v in weights.items()}
            varied_config["ensemble_weights"] = weights
        
        return varied_config
    
    def _log_selection(self, trial_number: int, config: Dict[str, Any], selection_type: str):
        """Log detalles de la selección"""
        
        config_summary = {}
        if "ensemble_weights" in config:
            neural_weight = config["ensemble_weights"].get("neural_enhanced", 0)
            config_summary["neural_weight"] = neural_weight
        
        if "svi_profile" in config:
            config_summary["svi_profile"] = config["svi_profile"]
        
        logger.info(f"   📋 Config seleccionada: {config_summary}")
        logger.info(f"   📊 Tipo: {selection_type}")
    
    def update_with_result(self, 
                          config: Dict[str, Any], 
                          reward: float, 
                          trial_number: int):
        """Actualiza sistema con resultado de trial"""
        
        # Añadir a historia
        trial_record = {
            "trial_number": trial_number,
            "config": config,
            "reward": reward,
            "timestamp": datetime.now().isoformat()
        }
        
        self.trial_history.append(trial_record)
        
        # Actualizar estrategia de exploración
        self.exploration_strategy.update_with_result(config, reward)
        
        # Log estadísticas
        if len(self.trial_history) % 10 == 0:
            self._log_statistics()
    
    def _log_statistics(self):
        """Log estadísticas del Active Learning"""
        
        if not self.trial_history:
            return
        
        recent_rewards = [t["reward"] for t in self.trial_history[-10:]]
        
        logger.info(f"📊 Active Learning Stats:")
        logger.info(f"   🔍 Exploration trials: {self.exploration_count}")
        logger.info(f"   💰 Exploitation trials: {self.exploitation_count}")
        logger.info(f"   📈 Recent avg reward: {np.mean(recent_rewards):.3f}")
        logger.info(f"   🏆 Best reward seen: {max(t['reward'] for t in self.trial_history):.3f}")
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Obtiene insights del proceso de Active Learning"""
        
        if not self.trial_history:
            return {"error": "No hay historial de trials"}
        
        rewards = [t["reward"] for t in self.trial_history]
        
        # Análisis de convergencia
        if len(rewards) >= 10:
            first_half = rewards[:len(rewards)//2]
            second_half = rewards[len(rewards)//2:]
            
            improvement = np.mean(second_half) - np.mean(first_half)
            improvement_pct = (improvement / np.mean(first_half)) * 100
        else:
            improvement_pct = 0
        
        # Exploration vs Exploitation balance
        total_trials = self.exploration_count + self.exploitation_count
        exploration_ratio = self.exploration_count / max(total_trials, 1)
        
        return {
            "total_trials": len(self.trial_history),
            "exploration_count": self.exploration_count,
            "exploitation_count": self.exploitation_count,
            "exploration_ratio": exploration_ratio,
            "best_reward": max(rewards),
            "average_reward": np.mean(rewards),
            "reward_std": np.std(rewards),
            "improvement_percentage": improvement_pct,
            "learning_trend": "improving" if improvement_pct > 5 else "stable",
            "strategy": self.strategy,
            "current_exploration_rate": self.exploration_rate * (0.95 ** (len(self.trial_history) // 10))
        }

# Función de conveniencia para integración
def create_active_learner(strategy: str = "uncertainty_sampling") -> ActiveLearningCoordinator:
    """Crea Active Learner configurado para OMEGA"""
    
    return ActiveLearningCoordinator(
        strategy=strategy,
        exploration_rate=0.4,  # 40% exploration inicial
        min_exploration_trials=8
    )

if __name__ == '__main__':
    # Test básico
    print("🎯 Testing Active Learner...")
    
    learner = create_active_learner("uncertainty_sampling")
    
    # Mock configurations
    mock_configs = [
        {
            "ensemble_weights": {"neural_enhanced": 0.4, "transformer_deep": 0.3, "genetico": 0.3},
            "svi_profile": "default"
        },
        {
            "ensemble_weights": {"neural_enhanced": 0.6, "transformer_deep": 0.2, "genetico": 0.2},
            "svi_profile": "neural_optimized"
        },
        {
            "ensemble_weights": {"neural_enhanced": 0.3, "transformer_deep": 0.4, "genetico": 0.3},
            "svi_profile": "aggressive"
        }
    ]
    
    # Simular trials
    print("   🔬 Simulando trials...")
    for trial in range(20):
        # Seleccionar configuración
        selected_config = learner.select_next_configuration(mock_configs, trial)
        
        # Simular reward (mejor para neural_enhanced alto)
        neural_weight = selected_config["ensemble_weights"].get("neural_enhanced", 0.4)
        base_reward = 0.6 + (neural_weight * 0.3)
        noise = np.random.normal(0, 0.05)
        reward = max(0.1, base_reward + noise)
        
        # Actualizar learner
        learner.update_with_result(selected_config, reward, trial)
    
    # Obtener insights
    insights = learner.get_learning_insights()
    
    print(f"✅ Test completado:")
    print(f"   🔍 Exploration ratio: {insights['exploration_ratio']:.1%}")
    print(f"   🏆 Best reward: {insights['best_reward']:.3f}")
    print(f"   📈 Learning trend: {insights['learning_trend']}")
    print(f"   📊 Improvement: {insights['improvement_percentage']:.1f}%")
