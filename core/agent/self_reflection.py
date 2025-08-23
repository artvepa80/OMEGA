#!/usr/bin/env python3
"""
🔍 SELF-REFLECTION ENGINE - Fase 3 del Sistema Agéntico
Sistema avanzado de auto-reflexión que analiza decisiones, patrones y resultados
Genera insights profundos para mejora continua del agente
"""

import json
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class DecisionAnalyzer:
    """Analiza patrones en decisiones del agente"""
    
    def __init__(self):
        self.decision_history = []
        self.pattern_cache = {}
        
    def analyze_decision_patterns(self, cycle_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza patrones en decisiones tomadas"""
        
        if not cycle_results:
            return {"error": "No hay decisiones para analizar"}
        
        # Extraer decisiones
        decisions = []
        for cycle in cycle_results:
            if "evaluation" in cycle and "chosen_config" in cycle["evaluation"]:
                config = cycle["evaluation"]["chosen_config"]
                reward = cycle["evaluation"].get("chosen_reward", 0)
                
                decisions.append({
                    "cycle": cycle.get("cycle_number", 0),
                    "config": config,
                    "reward": reward,
                    "timestamp": cycle.get("timestamp", "")
                })
        
        # Análisis de patrones
        patterns = {
            "ensemble_weights_evolution": self._analyze_weight_evolution(decisions),
            "svi_profile_preferences": self._analyze_svi_preferences(decisions),
            "reward_correlation": self._analyze_reward_correlations(decisions),
            "decision_consistency": self._analyze_decision_consistency(decisions),
            "temporal_patterns": self._analyze_temporal_patterns(decisions)
        }
        
        return {
            "total_decisions": len(decisions),
            "analysis_period": {
                "start": decisions[0]["timestamp"] if decisions else "",
                "end": decisions[-1]["timestamp"] if decisions else ""
            },
            "patterns": patterns,
            "insights": self._generate_pattern_insights(patterns),
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_weight_evolution(self, decisions: List[Dict]) -> Dict[str, Any]:
        """Analiza evolución de pesos del ensemble"""
        
        weight_evolution = defaultdict(list)
        
        for decision in decisions:
            weights = decision["config"].get("ensemble_weights", {})
            for model, weight in weights.items():
                weight_evolution[model].append({
                    "cycle": decision["cycle"],
                    "weight": weight,
                    "reward": decision.get("reward", 0.0)
                })
        
        # Calcular tendencias
        trends = {}
        for model, history in weight_evolution.items():
            if len(history) >= 3:
                weights = [h["weight"] for h in history]
                rewards = [h.get("reward", 0.0) for h in history]
            else:
                weights = [h["weight"] for h in history]
                rewards = [h.get("reward", 0.0) for h in history]
                
                # Correlación peso-reward
                correlation = np.corrcoef(weights, rewards)[0, 1] if len(weights) > 1 else 0
                
                # Tendencia del peso
                x = np.arange(len(weights))
                trend_slope = np.polyfit(x, weights, 1)[0] if len(weights) > 1 else 0
                
                trends[model] = {
                    "correlation_with_reward": float(correlation) if not np.isnan(correlation) else 0,
                    "weight_trend": "increasing" if trend_slope > 0.01 else "decreasing" if trend_slope < -0.01 else "stable",
                    "avg_weight": np.mean(weights),
                    "weight_volatility": np.std(weights)
                }
        
        return {
            "evolution_data": dict(weight_evolution),
            "trends": trends,
            "most_stable_model": min(trends.keys(), key=lambda k: trends[k]["weight_volatility"]) if trends else None,
            "highest_correlation": max(trends.keys(), key=lambda k: trends[k]["correlation_with_reward"]) if trends else None
        }
    
    def _analyze_svi_preferences(self, decisions: List[Dict]) -> Dict[str, Any]:
        """Analiza preferencias de perfil SVI"""
        
        profile_usage = Counter()
        profile_rewards = defaultdict(list)
        
        for decision in decisions:
            profile = decision["config"].get("svi_profile", "unknown")
            reward = decision.get("reward", 0.0)
            
            profile_usage[profile] += 1
            profile_rewards[profile].append(reward)
        
        # Análisis por perfil
        profile_analysis = {}
        for profile, rewards in profile_rewards.items():
            profile_analysis[profile] = {
                "usage_count": profile_usage[profile],
                "usage_percentage": profile_usage[profile] / len(decisions) * 100,
                "avg_reward": np.mean(rewards),
                "best_reward": max(rewards),
                "reward_consistency": 1 - (np.std(rewards) / np.mean(rewards)) if np.mean(rewards) > 0 else 0
            }
        
        # Perfil preferido
        preferred_profile = max(profile_analysis.keys(), 
                              key=lambda p: profile_analysis[p]["avg_reward"]) if profile_analysis else None
        
        return {
            "profile_analysis": profile_analysis,
            "preferred_profile": preferred_profile,
            "most_used_profile": profile_usage.most_common(1)[0][0] if profile_usage else None,
            "profile_diversity": len(profile_usage)
        }
    
    def _analyze_reward_correlations(self, decisions: List[Dict]) -> Dict[str, Any]:
        """Analiza correlaciones entre configuraciones y rewards"""
        
        if len(decisions) < 5:
            return {"insufficient_data": True}
        
        correlations = {}
        
        # Extraer features numéricas
        neural_weights = []
        rewards = []
        
        for decision in decisions:
            neural_w = decision["config"].get("ensemble_weights", {}).get("neural_enhanced", 0.45)
            neural_weights.append(neural_w)
            rewards.append(decision.get("reward", 0.0))
        
        # Calcular correlaciones
        if len(neural_weights) > 1:
            neural_corr = np.corrcoef(neural_weights, rewards)[0, 1]
            correlations["neural_enhanced_weight"] = float(neural_corr) if not np.isnan(neural_corr) else 0
        
        # Análisis de rangos óptimos
        df = pd.DataFrame({
            "neural_weight": neural_weights,
            "reward": rewards
        })
        
        # Binning para encontrar rangos óptimos
        df["neural_bin"] = pd.cut(df["neural_weight"], bins=5, labels=False)
        optimal_ranges = df.groupby("neural_bin")["reward"].mean().to_dict() if not df.empty else {}
        
        best_bin = max(optimal_ranges, key=optimal_ranges.get) if optimal_ranges else 0
        
        return {
            "correlations": correlations,
            "optimal_neural_range": {
                "bin": int(best_bin),
                "avg_reward": optimal_ranges.get(best_bin, 0),
                "recommendation": f"Neural weight entre {best_bin*0.15 + 0.2:.2f} y {(best_bin+1)*0.15 + 0.2:.2f}"
            },
            "feature_importance": {
                "neural_enhanced": abs(correlations.get("neural_enhanced_weight", 0))
            }
        }
    
    def _analyze_decision_consistency(self, decisions: List[Dict]) -> Dict[str, Any]:
        """Analiza consistencia en decisiones"""
        
        if len(decisions) < 3:
            return {"insufficient_data": True}
        
        # Analizar variabilidad en decisions consecutivas
        consecutive_changes = []
        
        for i in range(1, len(decisions)):
            prev_config = decisions[i-1]["config"]
            curr_config = decisions[i]["config"]
            
            # Calcular diferencia en neural weight
            prev_neural = prev_config.get("ensemble_weights", {}).get("neural_enhanced", 0.45)
            curr_neural = curr_config.get("ensemble_weights", {}).get("neural_enhanced", 0.45)
            
            weight_change = abs(curr_neural - prev_neural)
            consecutive_changes.append(weight_change)
            
            # Verificar cambio de perfil SVI
            profile_changed = prev_config.get("svi_profile") != curr_config.get("svi_profile")
        
        avg_weight_change = np.mean(consecutive_changes)
        consistency_score = 1 / (1 + avg_weight_change * 10)  # Score 0-1
        
        return {
            "avg_weight_change_per_cycle": avg_weight_change,
            "consistency_score": consistency_score,
            "consistency_level": "high" if consistency_score > 0.7 else "medium" if consistency_score > 0.4 else "low",
            "decision_volatility": np.std(consecutive_changes) if consecutive_changes else 0
        }
    
    def _analyze_temporal_patterns(self, decisions: List[Dict]) -> Dict[str, Any]:
        """Analiza patrones temporales en decisiones"""
        
        if len(decisions) < 5:
            return {"insufficient_data": True}
        
        # Analizar mejora temporal
        rewards = [d.get("reward", 0.0) for d in decisions]
        cycles = [d["cycle"] for d in decisions]
        
        # Tendencia de reward
        if len(rewards) > 2:
            x = np.arange(len(rewards))
            reward_trend = np.polyfit(x, rewards, 1)[0]
        else:
            reward_trend = 0
        
        # Ventanas deslizantes para detectar mejora
        window_size = min(3, len(rewards) // 2)
        if window_size >= 2:
            early_performance = np.mean(rewards[:window_size])
            late_performance = np.mean(rewards[-window_size:])
            improvement = (late_performance - early_performance) / early_performance * 100
        else:
            improvement = 0
        
        return {
            "reward_trend_slope": float(reward_trend),
            "trend_direction": "improving" if reward_trend > 0.01 else "degrading" if reward_trend < -0.01 else "stable",
            "performance_improvement_pct": improvement,
            "learning_detected": improvement > 10,
            "cycles_analyzed": len(cycles),
            "performance_volatility": np.std(rewards)
        }
    
    def _generate_pattern_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Genera insights basados en patrones detectados"""
        
        insights = []
        
        # Insights de evolución de pesos
        weight_patterns = patterns.get("ensemble_weights_evolution", {})
        if "trends" in weight_patterns:
            trends = weight_patterns["trends"]
            highest_corr_model = weight_patterns.get("highest_correlation")
            
            if highest_corr_model and highest_corr_model in trends:
                corr = trends[highest_corr_model]["correlation_with_reward"]
                if corr > 0.5:
                    insights.append(f"🔍 {highest_corr_model} muestra alta correlación ({corr:.2f}) con performance")
        
        # Insights de perfil SVI
        svi_patterns = patterns.get("svi_profile_preferences", {})
        preferred_profile = svi_patterns.get("preferred_profile")
        if preferred_profile:
            profile_data = svi_patterns["profile_analysis"][preferred_profile]
            insights.append(f"🎯 Perfil '{preferred_profile}' es más efectivo (avg reward: {profile_data['avg_reward']:.3f})")
        
        # Insights de consistencia
        consistency = patterns.get("decision_consistency", {})
        if "consistency_level" in consistency:
            level = consistency["consistency_level"]
            if level == "low":
                insights.append("⚠️ Decisiones inconsistentes - considerar más estabilidad")
            elif level == "high":
                insights.append("✅ Decisiones consistentes - estrategia estable")
        
        # Insights temporales
        temporal = patterns.get("temporal_patterns", {})
        if "learning_detected" in temporal and temporal["learning_detected"]:
            improvement = temporal["performance_improvement_pct"]
            insights.append(f"📈 Learning detectado: {improvement:.1f}% mejora en performance")
        
        return insights

class PerformanceAnalyzer:
    """Analiza performance histórica del agente"""
    
    def __init__(self):
        self.performance_metrics = []
        
    def analyze_performance_trends(self, cycle_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza tendencias de performance"""
        
        if not cycle_results:
            return {"error": "No hay datos de performance"}
        
        # Extraer métricas
        metrics_data = []
        for cycle in cycle_results:
            evaluation = cycle.get("evaluation", {})
            metrics = evaluation.get("metrics", {})
            
            if metrics:
                metrics_data.append({
                    "cycle": cycle.get("cycle_number", 0),
                    "best_reward": metrics.get("best_reward", 0),
                    "avg_reward": metrics.get("average_reward", 0),
                    "quality_rate": metrics.get("quality_rate", 0),
                    "execution_time": metrics.get("average_execution_time", 0),
                    "timestamp": cycle.get("timestamp", "")
                })
        
        if not metrics_data:
            return {"error": "No hay métricas válidas"}
        
        analysis = {
            "trend_analysis": self._analyze_trends(metrics_data),
            "performance_stability": self._analyze_stability(metrics_data),
            "efficiency_analysis": self._analyze_efficiency(metrics_data),
            "anomaly_detection": self._detect_anomalies(metrics_data),
            "comparative_analysis": self._comparative_analysis(metrics_data)
        }
        
        return {
            "total_cycles": len(metrics_data),
            "analysis_period": {
                "start": metrics_data[0]["timestamp"],
                "end": metrics_data[-1]["timestamp"]
            },
            "analysis": analysis,
            "summary": self._generate_performance_summary(analysis),
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_trends(self, metrics_data: List[Dict]) -> Dict[str, Any]:
        """Analiza tendencias en métricas clave"""
        
        rewards = [m["best_reward"] for m in metrics_data]
        quality_rates = [m["quality_rate"] for m in metrics_data]
        execution_times = [m["execution_time"] for m in metrics_data]
        
        def calculate_trend(values):
            if len(values) < 2:
                return {"slope": 0, "direction": "insufficient_data"}
            
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            
            return {
                "slope": float(slope),
                "direction": "improving" if slope > 0.01 else "degrading" if slope < -0.01 else "stable",
                "start_value": values[0],
                "end_value": values[-1],
                "change_percentage": (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0
            }
        
        return {
            "reward_trend": calculate_trend(rewards),
            "quality_trend": calculate_trend(quality_rates),
            "efficiency_trend": calculate_trend([-t for t in execution_times]),  # Negativo porque menor tiempo es mejor
            "overall_trend": self._calculate_overall_trend([rewards, quality_rates])
        }
    
    def _analyze_stability(self, metrics_data: List[Dict]) -> Dict[str, Any]:
        """Analiza estabilidad de performance"""
        
        rewards = [m["best_reward"] for m in metrics_data]
        quality_rates = [m["quality_rate"] for m in metrics_data]
        
        return {
            "reward_stability": {
                "std": float(np.std(rewards)),
                "coefficient_of_variation": float(np.std(rewards) / np.mean(rewards)) if np.mean(rewards) > 0 else 0,
                "stability_score": 1 / (1 + np.std(rewards))  # 0-1 score
            },
            "quality_stability": {
                "std": float(np.std(quality_rates)),
                "min_quality": min(quality_rates),
                "consistency": len([q for q in quality_rates if q > 0.7]) / len(quality_rates)
            },
            "overall_stability": "stable" if np.std(rewards) < 0.1 and min(quality_rates) > 0.6 else "variable"
        }
    
    def _analyze_efficiency(self, metrics_data: List[Dict]) -> Dict[str, Any]:
        """Analiza eficiencia del agente"""
        
        execution_times = [m["execution_time"] for m in metrics_data]
        rewards = [m["best_reward"] for m in metrics_data]
        
        # Eficiencia = reward / tiempo
        efficiency_scores = [r / max(t, 0.1) for r, t in zip(rewards, execution_times)]
        
        return {
            "avg_execution_time": float(np.mean(execution_times)),
            "avg_efficiency_score": float(np.mean(efficiency_scores)),
            "efficiency_trend": "improving" if len(efficiency_scores) > 1 and efficiency_scores[-1] > efficiency_scores[0] else "stable",
            "time_consistency": float(np.std(execution_times))
        }
    
    def _detect_anomalies(self, metrics_data: List[Dict]) -> Dict[str, Any]:
        """Detecta anomalías en performance"""
        
        rewards = [m["best_reward"] for m in metrics_data]
        
        if len(rewards) < 5:
            return {"insufficient_data": True}
        
        # Detección de outliers usando IQR
        q25, q75 = np.percentile(rewards, [25, 75])
        iqr = q75 - q25
        lower_bound = q25 - 1.5 * iqr
        upper_bound = q75 + 1.5 * iqr
        
        anomalies = []
        for i, reward in enumerate(rewards):
            if reward < lower_bound or reward > upper_bound:
                anomalies.append({
                    "cycle": metrics_data[i]["cycle"],
                    "reward": reward,
                    "type": "low_performance" if reward < lower_bound else "high_performance"
                })
        
        return {
            "total_anomalies": len(anomalies),
            "anomaly_rate": len(anomalies) / len(rewards),
            "anomalies": anomalies,
            "bounds": {"lower": lower_bound, "upper": upper_bound}
        }
    
    def _comparative_analysis(self, metrics_data: List[Dict]) -> Dict[str, Any]:
        """Análisis comparativo de períodos"""
        
        if len(metrics_data) < 6:
            return {"insufficient_data": True}
        
        mid_point = len(metrics_data) // 2
        early_period = metrics_data[:mid_point]
        late_period = metrics_data[mid_point:]
        
        early_avg_reward = np.mean([m["best_reward"] for m in early_period])
        late_avg_reward = np.mean([m["best_reward"] for m in late_period])
        
        improvement = (late_avg_reward - early_avg_reward) / early_avg_reward * 100
        
        return {
            "early_period_avg_reward": early_avg_reward,
            "late_period_avg_reward": late_avg_reward,
            "improvement_percentage": improvement,
            "learning_detected": improvement > 5,
            "periods_compared": f"{len(early_period)} vs {len(late_period)} cycles"
        }
    
    def _calculate_overall_trend(self, metric_lists: List[List[float]]) -> str:
        """Calcula tendencia general combinando múltiples métricas"""
        
        trends = []
        for metrics in metric_lists:
            if len(metrics) >= 2:
                slope = np.polyfit(range(len(metrics)), metrics, 1)[0]
                trends.append(slope)
        
        if not trends:
            return "insufficient_data"
        
        avg_slope = np.mean(trends)
        return "improving" if avg_slope > 0.01 else "degrading" if avg_slope < -0.01 else "stable"
    
    def _generate_performance_summary(self, analysis: Dict[str, Any]) -> List[str]:
        """Genera resumen de performance"""
        
        summary = []
        
        # Tendencias
        trend_analysis = analysis.get("trend_analysis", {})
        reward_trend = trend_analysis.get("reward_trend", {})
        if reward_trend.get("direction") == "improving":
            change = reward_trend.get("change_percentage", 0)
            summary.append(f"📈 Performance improving: {change:.1f}% increase in rewards")
        
        # Estabilidad
        stability = analysis.get("performance_stability", {})
        overall_stability = stability.get("overall_stability", "unknown")
        if overall_stability == "stable":
            summary.append("🎯 Performance is stable and consistent")
        else:
            summary.append("⚠️ Performance shows variability")
        
        # Anomalías
        anomalies = analysis.get("anomaly_detection", {})
        if not anomalies.get("insufficient_data") and anomalies.get("anomaly_rate", 0) > 0.2:
            summary.append(f"🚨 {anomalies['total_anomalies']} performance anomalies detected")
        
        # Learning
        comparative = analysis.get("comparative_analysis", {})
        if comparative.get("learning_detected"):
            improvement = comparative.get("improvement_percentage", 0)
            summary.append(f"🧠 Learning confirmed: {improvement:.1f}% improvement over time")
        
        return summary

class SelfReflectionEngine:
    """Motor principal de auto-reflexión"""
    
    def __init__(self):
        self.decision_analyzer = DecisionAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.reflection_history = []
        
        logger.info("🔍 SelfReflectionEngine inicializado")
    
    def reflect_on_cycles(self, cycle_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Realiza reflexión completa sobre ciclos ejecutados"""
        
        if not cycle_results:
            return {"error": "No hay ciclos para reflexionar"}
        
        logger.info(f"🔍 Iniciando reflexión sobre {len(cycle_results)} ciclos")
        
        # Análisis de decisiones
        decision_analysis = self.decision_analyzer.analyze_decision_patterns(cycle_results)
        
        # Análisis de performance
        performance_analysis = self.performance_analyzer.analyze_performance_trends(cycle_results)
        
        # Síntesis de reflexión
        reflection_synthesis = self._synthesize_insights(decision_analysis, performance_analysis)
        
        # Recomendaciones
        recommendations = self._generate_recommendations(decision_analysis, performance_analysis)
        
        # Compilar reflexión completa
        reflection_result = {
            "reflection_id": f"reflection_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "cycles_analyzed": len(cycle_results),
            "analysis_timestamp": datetime.now().isoformat(),
            "decision_analysis": decision_analysis,
            "performance_analysis": performance_analysis,
            "synthesis": reflection_synthesis,
            "recommendations": recommendations,
            "reflection_quality": self._assess_reflection_quality(decision_analysis, performance_analysis)
        }
        
        # Guardar en historial
        self.reflection_history.append(reflection_result)
        
        # Guardar a archivo
        self._save_reflection(reflection_result)
        
        logger.info(f"✅ Reflexión completada - Quality: {reflection_result['reflection_quality']}")
        
        return reflection_result
    
    def _synthesize_insights(self, decision_analysis: Dict, performance_analysis: Dict) -> Dict[str, Any]:
        """Sintetiza insights de ambos análisis"""
        
        # Combinar insights
        all_insights = []
        
        decision_insights = decision_analysis.get("insights", [])
        performance_summary = performance_analysis.get("summary", [])
        
        all_insights.extend(decision_insights)
        all_insights.extend(performance_summary)
        
        # Categorizar insights
        categorized_insights = {
            "optimization": [i for i in all_insights if any(word in i.lower() for word in ["correlación", "óptimo", "efectivo"])],
            "learning": [i for i in all_insights if any(word in i.lower() for word in ["learning", "mejora", "improvement"])],
            "stability": [i for i in all_insights if any(word in i.lower() for word in ["estable", "consistente", "variabilidad"])],
            "anomalies": [i for i in all_insights if any(word in i.lower() for word in ["anomalía", "inconsistente", "alerta"])]
        }
        
        # Meta-insights
        meta_insights = []
        
        if len(categorized_insights["learning"]) > 0:
            meta_insights.append("🧠 Agent muestra capacidad de aprendizaje activa")
        
        if len(categorized_insights["optimization"]) > 1:
            meta_insights.append("🔧 Múltiples oportunidades de optimización identificadas")
        
        if len(categorized_insights["anomalies"]) == 0:
            meta_insights.append("✅ Comportamiento del agent es predecible y estable")
        
        return {
            "total_insights": len(all_insights),
            "categorized_insights": categorized_insights,
            "meta_insights": meta_insights,
            "key_themes": list(categorized_insights.keys()),
            "synthesis_quality": "high" if len(all_insights) > 5 else "medium" if len(all_insights) > 2 else "low"
        }
    
    def _generate_recommendations(self, decision_analysis: Dict, performance_analysis: Dict) -> List[Dict[str, Any]]:
        """Genera recomendaciones basadas en análisis"""
        
        recommendations = []
        
        # Recomendaciones de decisión
        decision_patterns = decision_analysis.get("patterns", {})
        
        # Pesos del ensemble
        weight_evolution = decision_patterns.get("ensemble_weights_evolution", {})
        if "highest_correlation" in weight_evolution:
            highest_corr = weight_evolution["highest_correlation"]
            recommendations.append({
                "type": "optimization",
                "priority": "high",
                "action": f"Aumentar peso de {highest_corr}",
                "rationale": f"Modelo {highest_corr} muestra alta correlación con performance",
                "implementation": f"Ajustar peso a 0.5-0.6 en próximas configuraciones"
            })
        
        # Perfil SVI
        svi_preferences = decision_patterns.get("svi_profile_preferences", {})
        preferred_profile = svi_preferences.get("preferred_profile")
        if preferred_profile:
            recommendations.append({
                "type": "configuration",
                "priority": "medium",
                "action": f"Priorizar perfil '{preferred_profile}'",
                "rationale": f"Perfil muestra mejor performance promedio",
                "implementation": f"Usar '{preferred_profile}' como default en exploration"
            })
        
        # Recomendaciones de performance
        perf_analysis = performance_analysis.get("analysis", {})
        
        # Estabilidad
        stability = perf_analysis.get("performance_stability", {})
        overall_stability = stability.get("overall_stability")
        if overall_stability == "variable":
            recommendations.append({
                "type": "stability",
                "priority": "high",
                "action": "Reducir variabilidad en decisiones",
                "rationale": "Performance muestra alta variabilidad",
                "implementation": "Aumentar consistency_threshold en planner"
            })
        
        # Anomalías
        anomalies = perf_analysis.get("anomaly_detection", {})
        if not anomalies.get("insufficient_data") and anomalies.get("anomaly_rate", 0) > 0.2:
            recommendations.append({
                "type": "investigation",
                "priority": "medium",
                "action": "Investigar causas de anomalías",
                "rationale": f"{anomalies['total_anomalies']} anomalías detectadas",
                "implementation": "Añadir logging detallado en ciclos anómalos"
            })
        
        # Ordenar por prioridad
        priority_order = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 0), reverse=True)
        
        return recommendations
    
    def _assess_reflection_quality(self, decision_analysis: Dict, performance_analysis: Dict) -> str:
        """Evalúa calidad de la reflexión"""
        
        quality_score = 0
        max_score = 10
        
        # Cantidad de datos
        cycles_analyzed = decision_analysis.get("total_decisions", 0)
        if cycles_analyzed >= 10:
            quality_score += 3
        elif cycles_analyzed >= 5:
            quality_score += 2
        elif cycles_analyzed >= 2:
            quality_score += 1
        
        # Insights generados
        insights_count = len(decision_analysis.get("insights", []))
        if insights_count >= 5:
            quality_score += 2
        elif insights_count >= 3:
            quality_score += 1
        
        # Análisis de performance válido
        if not performance_analysis.get("error"):
            quality_score += 2
        
        # Detección de patterns
        patterns = decision_analysis.get("patterns", {})
        valid_patterns = sum(1 for p in patterns.values() if not isinstance(p, dict) or not p.get("insufficient_data"))
        if valid_patterns >= 4:
            quality_score += 2
        elif valid_patterns >= 2:
            quality_score += 1
        
        # Anomalías detectadas
        anomalies = performance_analysis.get("analysis", {}).get("anomaly_detection", {})
        if not anomalies.get("insufficient_data"):
            quality_score += 1
        
        # Mapear score a calidad
        quality_ratio = quality_score / max_score
        
        if quality_ratio >= 0.8:
            return "excellent"
        elif quality_ratio >= 0.6:
            return "good"
        elif quality_ratio >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def _save_reflection(self, reflection_result: Dict[str, Any]):
        """Guarda reflexión a archivo"""
        
        reflections_dir = Path("results/self_reflections")
        reflections_dir.mkdir(parents=True, exist_ok=True)
        
        reflection_id = reflection_result["reflection_id"]
        
        # Archivo individual
        reflection_file = reflections_dir / f"{reflection_id}.json"
        with open(reflection_file, 'w') as f:
            json.dump(reflection_result, f, indent=2, default=str)
        
        # Append al historial
        history_file = reflections_dir / "reflection_history.jsonl"
        with open(history_file, 'a') as f:
            f.write(json.dumps(reflection_result, default=str) + '\n')
        
        logger.info(f"💾 Reflexión guardada: {reflection_file}")

# Función de conveniencia
def create_self_reflection_engine() -> SelfReflectionEngine:
    """Crea motor de auto-reflexión"""
    return SelfReflectionEngine()

if __name__ == '__main__':
    # Test básico
    print("🔍 Testing Self-Reflection Engine...")
    
    engine = create_self_reflection_engine()
    
    # Mock cycle results
    mock_cycles = []
    for i in range(8):
        cycle = {
            "cycle_number": i + 1,
            "timestamp": datetime.now().isoformat(),
            "evaluation": {
                "chosen_config": {
                    "ensemble_weights": {
                        "neural_enhanced": 0.4 + (i * 0.05),
                        "transformer_deep": 0.3 - (i * 0.02),
                        "genetico": 0.3
                    },
                    "svi_profile": ["default", "neural_optimized", "aggressive"][i % 3]
                },
                "chosen_reward": 0.6 + (i * 0.03) + np.random.normal(0, 0.02),
                "metrics": {
                    "best_reward": 0.6 + (i * 0.03) + np.random.normal(0, 0.02),
                    "average_reward": 0.55 + (i * 0.025),
                    "quality_rate": 0.7 + (i * 0.02),
                    "average_execution_time": 45 + np.random.normal(0, 5)
                }
            }
        }
        mock_cycles.append(cycle)
    
    # Ejecutar reflexión
    reflection = engine.reflect_on_cycles(mock_cycles)
    
    print(f"✅ Test completado:")
    print(f"   🔍 Reflexión quality: {reflection['reflection_quality']}")
    print(f"   💡 Insights: {reflection['synthesis']['total_insights']}")
    print(f"   📋 Recomendaciones: {len(reflection['recommendations'])}")
    print(f"   🎯 Key themes: {reflection['synthesis']['key_themes']}")
    
    if reflection['recommendations']:
        print(f"   📌 Top recomendación: {reflection['recommendations'][0]['action']}")
