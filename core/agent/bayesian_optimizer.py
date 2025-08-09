#!/usr/bin/env python3
"""
🔍 BAYESIAN OPTIMIZER - Fase 2 del Sistema Agéntico
Optimización Bayesiana de hiperparámetros usando Optuna
Auto-tuning inteligente de configuraciones OMEGA
"""

import json
import logging
try:
    import optuna
    _OPTUNA_AVAILABLE = True
except Exception:
    optuna = None
    _OPTUNA_AVAILABLE = False
import numpy as np
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", message=".*experimental.*")

logger = logging.getLogger(__name__)

class OmegaBayesianOptimizer:
    """Optimizador Bayesiano para configuraciones OMEGA"""
    
    def __init__(self, 
                 study_name: str = "omega_optimization",
                 storage_url: str = "sqlite:///results/omega_optimization.db",
                 n_trials: int = 50,
                 timeout: int = 3600):
        
        self.study_name = study_name
        self.storage_url = storage_url
        self.n_trials = n_trials
        self.timeout = timeout
        
        # Configurar Optuna si disponible
        self.study = None
        if _OPTUNA_AVAILABLE:
            optuna.logging.set_verbosity(optuna.logging.WARNING)
            self.study = optuna.create_study(
                study_name=study_name,
                storage=storage_url,
                load_if_exists=True,
                direction="maximize",
                sampler=optuna.samplers.TPESampler(seed=42)
            )
        
        # Espacios de búsqueda para diferentes componentes
        self.search_spaces = {
            "ensemble_weights": {
                "neural_enhanced": (0.20, 0.80),
                "transformer_deep": (0.05, 0.30),
                "genetico": (0.05, 0.30),
                "analizador_200": (0.05, 0.25),
                "montecarlo": (0.01, 0.15),
                "lstm_v2": (0.01, 0.15),
                "clustering": (0.01, 0.10)
            },
            "neural_params": {
                "learning_rate": (0.0001, 0.01),
                "epochs": (20, 100),
                "batch_size": [16, 32, 64, 128],
                "dropout": (0.1, 0.5)
            },
            "svi_thresholds": {
                "conservative": (0.75, 0.95),
                "default": (0.60, 0.80),
                "aggressive": (0.30, 0.60)
            },
            "filter_params": {
                "max_consecutivos": [2, 3, 4, 5],
                "par_impar_tolerance": (0.1, 0.4),
                "suma_range_factor": (0.8, 1.2)
            }
        }
        
        self.best_trials_history = []
        logger.info(f"🔍 BayesianOptimizer inicializado: {study_name}")
    
    def suggest_configuration(self, trial, 
                            optimization_target: str = "ensemble") -> Dict[str, Any]:
        """Sugiere una configuración basada en el trial actual"""
        
        config = {}
        
        if optimization_target == "ensemble":
            # Optimizar pesos del ensemble
            weights = {}
            total_weight = 0
            
            # Sugerir pesos individuales
            for model, (min_w, max_w) in self.search_spaces["ensemble_weights"].items():
                weight = trial.suggest_float(f"weight_{model}", min_w, max_w)
                weights[model] = weight
                total_weight += weight
            
            # Normalizar pesos para que sumen 1
            weights = {k: v/total_weight for k, v in weights.items()}
            config["ensemble_weights"] = weights
            
            # Sugerir perfil SVI
            svi_profiles = ["conservative", "default", "aggressive", "neural_optimized"]
            config["svi_profile"] = trial.suggest_categorical("svi_profile", svi_profiles)
        
        elif optimization_target == "neural":
            # Optimizar parámetros neurales
            neural_params = {}
            for param, space in self.search_spaces["neural_params"].items():
                if isinstance(space, tuple):
                    if param == "learning_rate":
                        neural_params[param] = trial.suggest_float(param, space[0], space[1], log=True)
                    else:
                        neural_params[param] = trial.suggest_float(param, space[0], space[1])
                elif isinstance(space, list):
                    neural_params[param] = trial.suggest_categorical(param, space)
            
            config["neural_params"] = neural_params
            config["ensemble_weights"] = self._get_baseline_weights()
            config["svi_profile"] = "neural_optimized"
        
        elif optimization_target == "filters":
            # Optimizar filtros
            filter_params = {}
            for param, space in self.search_spaces["filter_params"].items():
                if isinstance(space, tuple):
                    filter_params[param] = trial.suggest_float(param, space[0], space[1])
                elif isinstance(space, list):
                    filter_params[param] = trial.suggest_categorical(param, space)
            
            config["filter_params"] = filter_params
            config["ensemble_weights"] = self._get_baseline_weights()
            config["svi_profile"] = "default"
        
        # Añadir metadatos
        config["optimization_target"] = optimization_target
        config["trial_number"] = trial.number
        config["timestamp"] = datetime.now().isoformat()
        
        return config
    
    def _get_baseline_weights(self) -> Dict[str, float]:
        """Retorna pesos baseline del ensemble"""
        return {
            "neural_enhanced": 0.45,
            "transformer_deep": 0.15,
            "genetico": 0.15,
            "analizador_200": 0.12,
            "montecarlo": 0.05,
            "lstm_v2": 0.03,
            "clustering": 0.01
        }
    
    def objective_function(self, trial, 
                          executor_fn: Callable, 
                          evaluator_fn: Callable,
                          optimization_target: str = "ensemble") -> float:
        """Función objetivo para optimización Bayesiana"""
        
        try:
            # Generar configuración sugerida
            config = self.suggest_configuration(trial, optimization_target)
            
            # Ejecutar configuración
            logger.info(f"🔬 Trial {trial.number}: Testing {optimization_target} optimization")
            run_result = executor_fn(config)
            
            # Evaluar resultado
            eval_result = evaluator_fn(run_result, "default")
            
            reward = eval_result["reward"]
            quality_ok = eval_result["quality_ok"]
            
            # Penalizar si la calidad no es aceptable
            if not quality_ok:
                reward *= 0.5  # Penalización del 50%
            
            # Log progreso
            logger.info(f"   ✅ Trial {trial.number}: Reward = {reward:.4f}, Quality = {'✅' if quality_ok else '❌'}")
            
            # Guardar metadatos del trial
            trial.set_user_attr("config", json.dumps(config))
            trial.set_user_attr("quality_ok", quality_ok)
            trial.set_user_attr("optimization_target", optimization_target)
            
            return reward
            
        except Exception as e:
            logger.error(f"❌ Error in trial {trial.number}: {e}")
            # Retornar reward muy bajo para trials fallidos
            return 0.1
    
    def optimize(self, 
                executor_fn: Callable, 
                evaluator_fn: Callable,
                optimization_target: str = "ensemble",
                n_trials: Optional[int] = None,
                timeout: Optional[int] = None) -> Dict[str, Any]:
        """Ejecuta optimización Bayesiana"""
        
        n_trials = n_trials or self.n_trials
        timeout = timeout or self.timeout
        
        logger.info(f"🚀 Iniciando optimización: {optimization_target}")
        logger.info(f"   🎯 Target: {optimization_target}")
        logger.info(f"   🔢 Trials: {n_trials}")
        logger.info(f"   ⏱️ Timeout: {timeout}s")
        
        # Fallback si no hay Optuna: random search ligero
        start_time = datetime.now()
        if not _OPTUNA_AVAILABLE:
            logger.warning("Optuna no disponible. Usando Random Search fallback.")
            best_reward = -1.0
            best_config = None
            for i in range(min(20, n_trials)):
                # Construir 'trial' mínimo
                class DummyTrial:
                    def __init__(self, num): self.number = num
                    def suggest_float(self, name, low, high, log=False):
                        import random
                        if log:
                            import math
                            return math.exp(random.uniform(math.log(low), math.log(high)))
                        return random.uniform(low, high)
                    def suggest_categorical(self, name, choices):
                        import random
                        return random.choice(choices)
                    def set_user_attr(self, *args, **kwargs):
                        pass
                dt = DummyTrial(i)
                reward = self.objective_function(dt, executor_fn, evaluator_fn, optimization_target)
                if reward > best_reward:
                    best_reward = reward
                    best_config = json.loads(json.dumps(self.suggest_configuration(dt, optimization_target)))
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            optimization_result = {
                "best_trial_number": 0,
                "best_reward": best_reward,
                "best_config": best_config or {},
                "optimization_target": optimization_target,
                "completed_trials": min(20, n_trials),
                "failed_trials": 0,
                "total_duration_seconds": duration,
                "trials_per_second": (min(20, n_trials) / duration) if duration > 0 else 0,
                "study_name": self.study_name,
                "timestamp": end_time.isoformat()
            }
            self._save_optimization_result(optimization_result)
            return optimization_result
        
        # Con Optuna
        def objective(trial):
            return self.objective_function(trial, executor_fn, evaluator_fn, optimization_target)
        try:
            self.study.optimize(objective, n_trials=n_trials, timeout=timeout, show_progress_bar=True)
        except KeyboardInterrupt:
            logger.info("⏹️ Optimización interrumpida por usuario")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Analizar resultados
        best_trial = self.study.best_trial
        best_config = json.loads(best_trial.user_attrs["config"])
        
        # Estadísticas
        completed_trials = len([t for t in self.study.trials if t.state == optuna.trial.TrialState.COMPLETE])
        failed_trials = len([t for t in self.study.trials if t.state == optuna.trial.TrialState.FAIL])
        
        optimization_result = {
            "best_trial_number": best_trial.number,
            "best_reward": best_trial.value,
            "best_config": best_config,
            "optimization_target": optimization_target,
            "completed_trials": completed_trials,
            "failed_trials": failed_trials,
            "total_duration_seconds": duration,
            "trials_per_second": completed_trials / duration if duration > 0 else 0,
            "study_name": self.study_name,
            "timestamp": end_time.isoformat()
        }
        
        # Guardar resultado
        self._save_optimization_result(optimization_result)
        
        logger.info(f"✅ Optimización completada:")
        logger.info(f"   🏆 Mejor reward: {best_trial.value:.4f}")
        logger.info(f"   🎯 Trial ganador: #{best_trial.number}")
        logger.info(f"   ✅ Trials exitosos: {completed_trials}")
        logger.info(f"   ❌ Trials fallidos: {failed_trials}")
        logger.info(f"   ⏱️ Duración: {duration:.1f}s")
        
        return optimization_result
    
    def _save_optimization_result(self, result: Dict[str, Any]):
        """Guarda resultado de optimización"""
        
        results_dir = Path("results/bayesian_optimization")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar resultado individual
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"optimization_{result['optimization_target']}_{timestamp}.json"
        
        result_path = results_dir / filename
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Actualizar historial
        history_path = results_dir / "optimization_history.jsonl"
        with open(history_path, 'a') as f:
            f.write(json.dumps(result) + '\n')
        
        logger.info(f"💾 Resultado guardado en: {result_path}")
    
    def get_optimization_insights(self) -> Dict[str, Any]:
        """Obtiene insights de la optimización"""
        
        if len(self.study.trials) == 0:
            return {"error": "No hay trials disponibles"}
        
        # Análisis de importancia de parámetros
        importance = {}
        if _OPTUNA_AVAILABLE and self.study is not None:
            try:
                importance = optuna.importance.get_param_importances(self.study)
            except Exception:
                importance = {}
        
        # Top trials
        completed_trials = [t for t in self.study.trials if t.state == optuna.trial.TrialState.COMPLETE]
        top_trials = sorted(completed_trials, key=lambda t: t.value, reverse=True)[:5]
        
        # Estadísticas de convergencia
        values = [t.value for t in completed_trials]
        
        insights = {
            "parameter_importance": importance,
            "top_5_trials": [
                {
                    "number": t.number,
                    "value": t.value,
                    "params": t.params
                } for t in top_trials
            ],
            "convergence_stats": {
                "best_value": max(values) if values else 0,
                "mean_value": np.mean(values) if values else 0,
                "std_value": np.std(values) if values else 0,
                "improvement_trend": self._calculate_improvement_trend(values)
            },
            "total_trials": len(self.study.trials),
            "completed_trials": len(completed_trials),
            "study_name": self.study_name
        }
        
        return insights
    
    def _calculate_improvement_trend(self, values: List[float]) -> str:
        """Calcula tendencia de mejora"""
        if len(values) < 10:
            return "insufficient_data"
        
        # Comparar primeros 10 vs últimos 10
        first_10 = np.mean(values[:10])
        last_10 = np.mean(values[-10:])
        
        improvement = (last_10 - first_10) / first_10 * 100
        
        if improvement > 5:
            return "improving"
        elif improvement < -5:
            return "degrading"
        else:
            return "stable"
    
    def suggest_next_optimization_target(self) -> str:
        """Sugiere próximo target de optimización basado en resultados"""
        
        insights = self.get_optimization_insights()
        
        if insights.get("error"):
            return "ensemble"  # Default
        
        # Lógica simple: rotar entre targets
        completed = insights["completed_trials"]
        
        if completed < 20:
            return "ensemble"
        elif completed < 40:
            return "neural"
        else:
            return "filters"

# Función de conveniencia para integración con el agente
def create_bayesian_optimizer(study_name: str = None) -> OmegaBayesianOptimizer:
    """Crea optimizador Bayesiano configurado para OMEGA"""
    
    if study_name is None:
        study_name = f"omega_opt_{datetime.now().strftime('%Y%m%d')}"
    
    return OmegaBayesianOptimizer(
        study_name=study_name,
        n_trials=30,  # Reducido para demos
        timeout=1800  # 30 minutos
    )

if __name__ == '__main__':
    # Test básico
    print("🔍 Testing Bayesian Optimizer...")
    
    optimizer = create_bayesian_optimizer("test_study")
    
    # Mock functions para testing
    def mock_executor(config):
        import random
        return {
            "returncode": 0,
            "stdout": f"SVI: {random.uniform(0.6, 0.9):.3f} Generadas",
            "stderr": ""
        }
    
    def mock_evaluator(run_result, baseline):
        import re
        svi = float(re.search(r"SVI: ([0-9.]+)", run_result["stdout"]).group(1))
        return {
            "reward": svi * 0.8,
            "quality_ok": svi > 0.65,
            "signals": {"svi": svi}
        }
    
    # Test con pocos trials
    result = optimizer.optimize(mock_executor, mock_evaluator, "ensemble", n_trials=5, timeout=60)
    
    print(f"✅ Test completado:")
    print(f"   🏆 Mejor reward: {result['best_reward']:.4f}")
    print(f"   ✅ Trials: {result['completed_trials']}")
    
    # Test insights
    insights = optimizer.get_optimization_insights()
    print(f"   📊 Parameter importance: {list(insights['parameter_importance'].keys())[:3]}")
    print(f"   📈 Trend: {insights['convergence_stats']['improvement_trend']}")
