#!/usr/bin/env python3
"""
🎯 MULTI-OBJECTIVE OPTIMIZER - Fase 4 del Sistema Agéntico
Optimizador multi-objetivo con frentes de Pareto para balancear múltiples criterios
Optimiza simultáneamente performance, diversidad, estabilidad y eficiencia
"""

import json
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from scipy.optimize import differential_evolution
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

@dataclass
class Objective:
    """Definición de un objetivo de optimización"""
    name: str
    description: str
    weight: float
    minimize: bool  # True para minimizar, False para maximizar
    target_value: Optional[float] = None
    tolerance: float = 0.01

@dataclass
class Solution:
    """Solución candidata en el espacio multi-objetivo"""
    config: Dict[str, Any]
    objectives: Dict[str, float]
    overall_score: float
    pareto_rank: int = 0
    crowding_distance: float = 0.0
    dominated_count: int = 0
    dominates: List[int] = None
    
    def __post_init__(self):
        if self.dominates is None:
            self.dominates = []

class ParetoFrontAnalyzer:
    """Analizador de frentes de Pareto"""
    
    def __init__(self):
        self.fronts = []
        
    def calculate_pareto_fronts(self, solutions: List[Solution]) -> List[List[Solution]]:
        """Calcula frentes de Pareto usando NSGA-II"""
        
        # Reset dominance relationships
        for solution in solutions:
            solution.dominated_count = 0
            solution.dominates = []
        
        # Calculate dominance relationships
        for i, sol_i in enumerate(solutions):
            for j, sol_j in enumerate(solutions):
                if i != j:
                    if self._dominates(sol_i, sol_j):
                        sol_i.dominates.append(j)
                    elif self._dominates(sol_j, sol_i):
                        sol_i.dominated_count += 1
        
        # Build fronts
        fronts = []
        current_front = []
        
        # First front: non-dominated solutions
        for i, solution in enumerate(solutions):
            if solution.dominated_count == 0:
                solution.pareto_rank = 0
                current_front.append(solution)
        
        fronts.append(current_front)
        
        # Subsequent fronts
        front_index = 0
        while fronts[front_index]:
            next_front = []
            
            for solution in fronts[front_index]:
                for j in solution.dominates:
                    dominated_solution = solutions[j]
                    dominated_solution.dominated_count -= 1
                    
                    if dominated_solution.dominated_count == 0:
                        dominated_solution.pareto_rank = front_index + 1
                        next_front.append(dominated_solution)
            
            if next_front:
                fronts.append(next_front)
            
            front_index += 1
        
        # Calculate crowding distance for each front
        for front in fronts:
            self._calculate_crowding_distance(front)
        
        self.fronts = fronts
        return fronts
    
    def _dominates(self, sol_a: Solution, sol_b: Solution) -> bool:
        """Verifica si la solución A domina a la solución B"""
        
        better_in_any = False
        worse_in_any = False
        
        for obj_name, value_a in sol_a.objectives.items():
            value_b = sol_b.objectives[obj_name]
            
            # Asumir que mayores valores son mejores (se puede configurar por objetivo)
            if value_a > value_b:
                better_in_any = True
            elif value_a < value_b:
                worse_in_any = True
        
        return better_in_any and not worse_in_any
    
    def _calculate_crowding_distance(self, front: List[Solution]):
        """Calcula distancia de crowding para preservar diversidad"""
        
        if len(front) <= 2:
            for solution in front:
                solution.crowding_distance = float('inf')
            return
        
        # Initialize distances
        for solution in front:
            solution.crowding_distance = 0.0
        
        # Calculate distance for each objective
        for obj_name in front[0].objectives.keys():
            # Sort by objective value
            front.sort(key=lambda s: s.objectives[obj_name])
            
            # Boundary solutions get infinite distance
            front[0].crowding_distance = float('inf')
            front[-1].crowding_distance = float('inf')
            
            # Calculate range
            obj_range = front[-1].objectives[obj_name] - front[0].objectives[obj_name]
            
            if obj_range == 0:
                continue
            
            # Calculate distances for intermediate solutions
            for i in range(1, len(front) - 1):
                distance = (front[i + 1].objectives[obj_name] - front[i - 1].objectives[obj_name]) / obj_range
                front[i].crowding_distance += distance

class MultiObjectiveOptimizer:
    """Optimizador multi-objetivo principal"""
    
    def __init__(self):
        self.objectives = {}
        self.pareto_analyzer = ParetoFrontAnalyzer()
        self.solution_history = []
        self.optimization_history = []
        
        # Configuración del optimizador
        self.config = {
            "population_size": 50,
            "max_generations": 30,
            "mutation_rate": 0.1,
            "crossover_rate": 0.9,
            "elite_ratio": 0.2,
            "diversity_threshold": 0.1,
            "convergence_threshold": 0.001,
            "max_stagnation_generations": 10
        }
        
        logger.info("🎯 MultiObjectiveOptimizer inicializado")
    
    def add_objective(self, objective: Objective):
        """Añade un objetivo de optimización"""
        
        self.objectives[objective.name] = objective
        logger.info(f"🎯 Objetivo añadido: {objective.name} (peso: {objective.weight})")
    
    def setup_default_objectives(self):
        """Configura objetivos por defecto para el agente"""
        
        objectives = [
            Objective(
                name="performance",
                description="Maximizar reward promedio",
                weight=0.35,
                minimize=False,
                target_value=0.85
            ),
            Objective(
                name="stability",
                description="Minimizar variabilidad de performance",
                weight=0.25,
                minimize=True,
                target_value=0.05
            ),
            Objective(
                name="efficiency",
                description="Minimizar tiempo de ejecución",
                weight=0.20,
                minimize=True,
                target_value=60.0  # segundos
            ),
            Objective(
                name="diversity",
                description="Maximizar diversidad de estrategias",
                weight=0.15,
                minimize=False,
                target_value=0.8
            ),
            Objective(
                name="robustness",
                description="Maximizar resistencia a fallos",
                weight=0.05,
                minimize=False,
                target_value=0.95
            )
        ]
        
        for obj in objectives:
            self.add_objective(obj)
    
    def evaluate_solution(self, config: Dict[str, Any], 
                         execution_results: List[Dict[str, Any]]) -> Solution:
        """Evalúa una configuración según todos los objetivos"""
        
        if not execution_results:
            # Configuración sin resultados - valores por defecto bajos
            objectives = {name: 0.1 for name in self.objectives.keys()}
        else:
            objectives = {}
            
            # Evaluar cada objetivo
            for obj_name, objective in self.objectives.items():
                objectives[obj_name] = self._evaluate_objective(objective, execution_results)
        
        # Calcular score general ponderado
        overall_score = sum(
            objectives[name] * obj.weight 
            for name, obj in self.objectives.items()
        )
        
        return Solution(
            config=config,
            objectives=objectives,
            overall_score=overall_score
        )
    
    def _evaluate_objective(self, objective: Objective, 
                          execution_results: List[Dict[str, Any]]) -> float:
        """Evalúa un objetivo específico"""
        
        if objective.name == "performance":
            # Performance basada en rewards
            rewards = [r.get("best_reward", 0) for r in execution_results]
            return np.mean(rewards) if rewards else 0.0
        
        elif objective.name == "stability":
            # Estabilidad basada en variabilidad de rewards
            rewards = [r.get("best_reward", 0) for r in execution_results]
            return np.std(rewards) if len(rewards) > 1 else 0.0
        
        elif objective.name == "efficiency":
            # Eficiencia basada en tiempo de ejecución
            durations = [r.get("duration", 60) for r in execution_results]
            return np.mean(durations) if durations else 60.0
        
        elif objective.name == "diversity":
            # Diversidad basada en variedad de estrategias usadas
            modes = [r.get("planner_mode", "unknown") for r in execution_results]
            unique_modes = len(set(modes))
            max_possible_modes = 4  # active_learning, bayesian, recalibration, exploration
            return unique_modes / max_possible_modes
        
        elif objective.name == "robustness":
            # Robustez basada en tasa de éxito
            successful = len([r for r in execution_results if r.get("quality_rate", 0) > 0.7])
            return successful / len(execution_results) if execution_results else 0.0
        
        else:
            logger.warning(f"⚠️ Objetivo desconocido: {objective.name}")
            return 0.5
    
    def optimize_configurations(self, 
                              candidate_configs: List[Dict[str, Any]],
                              execution_results_map: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Optimiza configuraciones usando algoritmo multi-objetivo"""
        
        logger.info(f"🎯 Iniciando optimización multi-objetivo con {len(candidate_configs)} configuraciones")
        
        # Evaluar todas las configuraciones candidatas
        solutions = []
        for i, config in enumerate(candidate_configs):
            config_id = f"config_{i}"
            results = execution_results_map.get(config_id, [])
            solution = self.evaluate_solution(config, results)
            solutions.append(solution)
        
        # Calcular frentes de Pareto
        pareto_fronts = self.pareto_analyzer.calculate_pareto_fronts(solutions)
        
        # Analizar resultados
        optimization_result = self._analyze_optimization_results(pareto_fronts, solutions)
        
        # Guardar en historial
        self.optimization_history.append({
            "timestamp": datetime.now().isoformat(),
            "total_solutions": len(solutions),
            "pareto_fronts_count": len(pareto_fronts),
            "best_solution": optimization_result["best_solution"],
            "diversity_metrics": optimization_result["diversity_metrics"]
        })
        
        logger.info(f"✅ Optimización completada:")
        logger.info(f"   🏆 Frentes de Pareto: {len(pareto_fronts)}")
        logger.info(f"   🎯 Mejor score: {optimization_result['best_solution']['overall_score']:.3f}")
        
        return optimization_result
    
    def _analyze_optimization_results(self, pareto_fronts: List[List[Solution]], 
                                    all_solutions: List[Solution]) -> Dict[str, Any]:
        """Analiza resultados de la optimización"""
        
        if not pareto_fronts or not pareto_fronts[0]:
            return {"error": "No hay soluciones válidas"}
        
        # Mejor solución del primer frente
        first_front = pareto_fronts[0]
        best_solution = max(first_front, key=lambda s: s.overall_score)
        
        # Métricas de diversidad
        diversity_metrics = self._calculate_diversity_metrics(pareto_fronts)
        
        # Análisis de objetivos
        objective_analysis = self._analyze_objectives(all_solutions)
        
        # Recomendaciones
        recommendations = self._generate_optimization_recommendations(
            best_solution, pareto_fronts, objective_analysis
        )
        
        return {
            "best_solution": {
                "config": best_solution.config,
                "objectives": best_solution.objectives,
                "overall_score": best_solution.overall_score,
                "pareto_rank": best_solution.pareto_rank
            },
            "pareto_summary": {
                "total_fronts": len(pareto_fronts),
                "first_front_size": len(first_front),
                "dominated_solutions": len(all_solutions) - len(first_front)
            },
            "diversity_metrics": diversity_metrics,
            "objective_analysis": objective_analysis,
            "recommendations": recommendations,
            "pareto_fronts": [
                [{"config": s.config, "objectives": s.objectives, "score": s.overall_score} 
                 for s in front]
                for front in pareto_fronts[:3]  # Solo primeros 3 frentes
            ]
        }
    
    def _calculate_diversity_metrics(self, pareto_fronts: List[List[Solution]]) -> Dict[str, Any]:
        """Calcula métricas de diversidad de las soluciones"""
        
        if not pareto_fronts or not pareto_fronts[0]:
            return {"diversity_score": 0.0}
        
        first_front = pareto_fronts[0]
        
        # Diversidad en el espacio de objetivos
        objective_values = []
        for solution in first_front:
            values = list(solution.objectives.values())
            objective_values.append(values)
        
        if len(objective_values) < 2:
            return {"diversity_score": 0.0}
        
        objective_values = np.array(objective_values)
        
        # Calcular diversidad usando distancias promedio
        distances = []
        for i in range(len(objective_values)):
            for j in range(i + 1, len(objective_values)):
                distance = np.linalg.norm(objective_values[i] - objective_values[j])
                distances.append(distance)
        
        diversity_score = np.mean(distances) if distances else 0.0
        
        spread = np.max(objective_values, axis=0) - np.min(objective_values, axis=0) if len(objective_values) > 0 else np.array([])
        
        return {
            "diversity_score": diversity_score,
            "spread": spread.tolist() if len(spread) > 0 else [],
            "solutions_in_first_front": len(first_front)
        }
    
    def _analyze_objectives(self, solutions: List[Solution]) -> Dict[str, Any]:
        """Analiza performance de objetivos individuales"""
        
        analysis = {}
        
        for obj_name in self.objectives.keys():
            values = [s.objectives[obj_name] for s in solutions]
            
            analysis[obj_name] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "target": self.objectives[obj_name].target_value,
                "weight": self.objectives[obj_name].weight
            }
            
            # Calcular qué porcentaje alcanza el target
            if self.objectives[obj_name].target_value is not None:
                target = self.objectives[obj_name].target_value
                if self.objectives[obj_name].minimize:
                    achieving_target = len([v for v in values if v <= target])
                else:
                    achieving_target = len([v for v in values if v >= target])
                
                analysis[obj_name]["target_achievement_rate"] = achieving_target / len(values)
        
        return analysis
    
    def _generate_optimization_recommendations(self, 
                                            best_solution: Solution,
                                            pareto_fronts: List[List[Solution]],
                                            objective_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera recomendaciones basadas en la optimización"""
        
        recommendations = []
        
        # Analizar objetivos que no alcanzan target
        for obj_name, analysis in objective_analysis.items():
            target_rate = analysis.get("target_achievement_rate", 0)
            
            if target_rate < 0.5:  # Menos del 50% alcanza target
                recommendations.append({
                    "type": "objective_improvement",
                    "priority": "high",
                    "objective": obj_name,
                    "current_achievement": target_rate,
                    "recommendation": f"Mejorar {obj_name}: solo {target_rate:.1%} alcanza target",
                    "suggested_action": self._get_objective_improvement_action(obj_name)
                })
        
        # Analizar diversidad del frente de Pareto
        if len(pareto_fronts) > 0 and len(pareto_fronts[0]) < 3:
            recommendations.append({
                "type": "diversity_improvement",
                "priority": "medium",
                "recommendation": "Aumentar diversidad de soluciones",
                "suggested_action": "Expandir espacio de búsqueda o usar más variaciones de configuración"
            })
        
        # Recomendación de configuración óptima
        recommendations.append({
            "type": "optimal_configuration",
            "priority": "high",
            "recommendation": f"Usar configuración con score {best_solution.overall_score:.3f}",
            "config_summary": self._summarize_config(best_solution.config),
            "expected_improvements": self._calculate_expected_improvements(best_solution)
        })
        
        return recommendations
    
    def _get_objective_improvement_action(self, obj_name: str) -> str:
        """Obtiene acción sugerida para mejorar un objetivo"""
        
        actions = {
            "performance": "Aumentar pesos de modelos de alto rendimiento (neural_enhanced)",
            "stability": "Reducir exploration rate y usar configuraciones más consistentes",
            "efficiency": "Optimizar timeouts y reducir número de experimentos por ciclo",
            "diversity": "Usar múltiples estrategias de planificación en rotación",
            "robustness": "Implementar más validaciones y mecanismos de fallback"
        }
        
        return actions.get(obj_name, "Revisar configuración y ajustar parámetros")
    
    def _summarize_config(self, config: Dict[str, Any]) -> str:
        """Crea resumen legible de una configuración"""
        
        summary_parts = []
        
        if "ensemble_weights" in config:
            neural_weight = config["ensemble_weights"].get("neural_enhanced", 0)
            summary_parts.append(f"Neural: {neural_weight:.2f}")
        
        if "svi_profile" in config:
            summary_parts.append(f"SVI: {config['svi_profile']}")
        
        if "proposal_metadata" in config:
            mode = config["proposal_metadata"].get("mode", "unknown")
            summary_parts.append(f"Mode: {mode}")
        
        return " | ".join(summary_parts) if summary_parts else "Standard config"
    
    def _calculate_expected_improvements(self, solution: Solution) -> Dict[str, str]:
        """Calcula mejoras esperadas de una solución"""
        
        improvements = {}
        
        for obj_name, value in solution.objectives.items():
            objective = self.objectives[obj_name]
            
            if objective.target_value is not None:
                if objective.minimize:
                    if value <= objective.target_value:
                        improvements[obj_name] = f"✅ Target alcanzado ({value:.3f})"
                    else:
                        gap = value - objective.target_value
                        improvements[obj_name] = f"📈 Mejorar {gap:.3f} para alcanzar target"
                else:
                    if value >= objective.target_value:
                        improvements[obj_name] = f"✅ Target alcanzado ({value:.3f})"
                    else:
                        gap = objective.target_value - value
                        improvements[obj_name] = f"📈 Mejorar {gap:.3f} para alcanzar target"
            else:
                improvements[obj_name] = f"Current: {value:.3f}"
        
        return improvements
    
    def get_optimization_insights(self) -> Dict[str, Any]:
        """Obtiene insights del proceso de optimización"""
        
        if not self.optimization_history:
            return {"error": "No hay historial de optimización"}
        
        latest = self.optimization_history[-1]
        
        # Tendencias históricas
        if len(self.optimization_history) > 1:
            scores = [opt["best_solution"]["overall_score"] for opt in self.optimization_history]
            trend = "improving" if scores[-1] > scores[0] else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "total_optimizations": len(self.optimization_history),
            "latest_optimization": latest,
            "objectives_configured": len(self.objectives),
            "optimization_trend": trend,
            "best_score_overall": max(
                opt["best_solution"]["overall_score"] 
                for opt in self.optimization_history
            ) if self.optimization_history else 0,
            "average_pareto_fronts": np.mean([
                opt["pareto_fronts_count"] 
                for opt in self.optimization_history
            ]) if self.optimization_history else 0
        }

# Función de conveniencia
def create_multi_objective_optimizer() -> MultiObjectiveOptimizer:
    """Crea optimizador multi-objetivo configurado"""
    
    optimizer = MultiObjectiveOptimizer()
    optimizer.setup_default_objectives()
    
    return optimizer

if __name__ == '__main__':
    # Test básico del optimizador
    print("🎯 Testing Multi-Objective Optimizer...")
    
    optimizer = create_multi_objective_optimizer()
    
    # Mock configurations y resultados
    mock_configs = [
        {"ensemble_weights": {"neural_enhanced": 0.5}, "svi_profile": "default"},
        {"ensemble_weights": {"neural_enhanced": 0.7}, "svi_profile": "neural_optimized"},
        {"ensemble_weights": {"neural_enhanced": 0.3}, "svi_profile": "conservative"}
    ]
    
    mock_results_map = {
        "config_0": [{"best_reward": 0.75, "duration": 45, "quality_rate": 0.8, "planner_mode": "active_learning"}],
        "config_1": [{"best_reward": 0.82, "duration": 60, "quality_rate": 0.9, "planner_mode": "bayesian_optimization"}],
        "config_2": [{"best_reward": 0.68, "duration": 30, "quality_rate": 0.75, "planner_mode": "conservative"}]
    }
    
    # Ejecutar optimización
    result = optimizer.optimize_configurations(mock_configs, mock_results_map)
    
    print(f"✅ Test completado:")
    print(f"   🏆 Mejor score: {result['best_solution']['overall_score']:.3f}")
    print(f"   📊 Frentes de Pareto: {result['pareto_summary']['total_fronts']}")
    print(f"   🎯 Diversidad: {result['diversity_metrics']['diversity_score']:.3f}")
    print(f"   💡 Recomendaciones: {len(result['recommendations'])}")
    
    # Mostrar insights
    insights = optimizer.get_optimization_insights()
    print(f"   📈 Objetivos configurados: {insights['objectives_configured']}")
    print(f"   🔍 Mejor score general: {insights['best_score_overall']:.3f}")
