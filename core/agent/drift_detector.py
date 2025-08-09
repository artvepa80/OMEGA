#!/usr/bin/env python3
"""
📊 DRIFT DETECTOR - Fase 2 del Sistema Agéntico
Detecta deriva de rendimiento y patrones para trigger recalibración automática
Usa estadísticas de Kolmogorov-Smirnov y ADWIN para detección online
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class PerformanceDriftDetector:
    """Detector de deriva de rendimiento usando estadísticas online"""
    
    def __init__(self, 
                 window_size: int = 50,
                 min_samples: int = 20,
                 drift_threshold: float = 0.05,
                 sensitivity: float = 0.8):
        
        self.window_size = window_size
        self.min_samples = min_samples
        self.drift_threshold = drift_threshold
        self.sensitivity = sensitivity
        
        # Buffers para diferentes métricas
        self.reward_history = deque(maxlen=window_size)
        self.svi_history = deque(maxlen=window_size)
        self.diversity_history = deque(maxlen=window_size)
        self.quality_history = deque(maxlen=window_size)
        
        # Estado de deriva
        self.drift_detected = False
        self.last_drift_time = None
        self.drift_count = 0
        
        # Baseline estadísticas
        self.baseline_stats = {}
        self.baseline_established = False
        
        logger.info(f"📊 DriftDetector inicializado: window={window_size}, threshold={drift_threshold}")
    
    def add_measurement(self, 
                       reward: float, 
                       svi: float, 
                       diversity: float, 
                       quality_ok: bool):
        """Añade nueva medición y verifica deriva"""
        
        # Añadir a buffers
        self.reward_history.append(reward)
        self.svi_history.append(svi)
        self.diversity_history.append(diversity)
        self.quality_history.append(1.0 if quality_ok else 0.0)
        
        # Establecer baseline si tenemos suficientes samples
        if not self.baseline_established and len(self.reward_history) >= self.min_samples:
            self._establish_baseline()
        
        # Detectar deriva si baseline está establecido
        if self.baseline_established and len(self.reward_history) >= self.min_samples:
            drift_result = self._detect_drift()
            
            if drift_result["drift_detected"]:
                self.drift_detected = True
                self.last_drift_time = datetime.now()
                self.drift_count += 1
                
                logger.warning(f"🚨 DERIVA DETECTADA:")
                logger.warning(f"   📊 Métrica afectada: {drift_result['affected_metrics']}")
                logger.warning(f"   📈 Severidad: {drift_result['severity']:.3f}")
                logger.warning(f"   🔢 P-values: {drift_result['p_values']}")
                
                return drift_result
        
        return {"drift_detected": False}
    
    def _establish_baseline(self):
        """Establece estadísticas baseline"""
        
        self.baseline_stats = {
            "reward": {
                "mean": np.mean(self.reward_history),
                "std": np.std(self.reward_history),
                "median": np.median(self.reward_history),
                "q25": np.percentile(self.reward_history, 25),
                "q75": np.percentile(self.reward_history, 75)
            },
            "svi": {
                "mean": np.mean(self.svi_history),
                "std": np.std(self.svi_history),
                "median": np.median(self.svi_history)
            },
            "diversity": {
                "mean": np.mean(self.diversity_history),
                "std": np.std(self.diversity_history)
            },
            "quality_rate": np.mean(self.quality_history)
        }
        
        self.baseline_established = True
        logger.info("✅ Baseline estadísticas establecidas")
        logger.info(f"   📊 Reward baseline: μ={self.baseline_stats['reward']['mean']:.3f}, σ={self.baseline_stats['reward']['std']:.3f}")
        logger.info(f"   📈 SVI baseline: μ={self.baseline_stats['svi']['mean']:.3f}")
        logger.info(f"   🎯 Quality rate baseline: {self.baseline_stats['quality_rate']:.1%}")
    
    def _detect_drift(self) -> Dict[str, Any]:
        """Detecta deriva usando multiple tests estadísticos"""
        
        # Dividir ventana en dos mitades para comparación
        mid_point = len(self.reward_history) // 2
        
        # Recent vs Historical
        recent_rewards = list(self.reward_history)[mid_point:]
        historical_rewards = list(self.reward_history)[:mid_point]
        
        recent_svi = list(self.svi_history)[mid_point:]
        historical_svi = list(self.svi_history)[:mid_point]
        
        # Tests estadísticos
        drift_tests = {}
        
        # 1. Kolmogorov-Smirnov test para reward
        if len(recent_rewards) >= 5 and len(historical_rewards) >= 5:
            ks_stat, ks_pvalue = stats.ks_2samp(historical_rewards, recent_rewards)
            drift_tests["reward_ks"] = {
                "statistic": ks_stat,
                "p_value": ks_pvalue,
                "drift": ks_pvalue < self.drift_threshold
            }
        
        # 2. T-test para cambio en media
        if len(recent_rewards) >= 5 and len(historical_rewards) >= 5:
            t_stat, t_pvalue = stats.ttest_ind(historical_rewards, recent_rewards)
            drift_tests["reward_ttest"] = {
                "statistic": t_stat,
                "p_value": t_pvalue,
                "drift": t_pvalue < self.drift_threshold
            }
        
        # 3. Test similar para SVI
        if len(recent_svi) >= 5 and len(historical_svi) >= 5:
            ks_stat_svi, ks_pvalue_svi = stats.ks_2samp(historical_svi, recent_svi)
            drift_tests["svi_ks"] = {
                "statistic": ks_stat_svi,
                "p_value": ks_pvalue_svi,
                "drift": ks_pvalue_svi < self.drift_threshold
            }
        
        # 4. Test de degradación de calidad
        recent_quality = np.mean(list(self.quality_history)[mid_point:])
        baseline_quality = self.baseline_stats["quality_rate"]
        
        quality_degradation = (baseline_quality - recent_quality) / baseline_quality
        quality_drift = quality_degradation > 0.2  # 20% degradación
        
        drift_tests["quality_degradation"] = {
            "baseline_rate": baseline_quality,
            "recent_rate": recent_quality,
            "degradation_pct": quality_degradation * 100,
            "drift": quality_drift
        }
        
        # Determinar deriva general
        drift_signals = [test["drift"] for test in drift_tests.values()]
        drift_count = sum(drift_signals)
        total_tests = len(drift_signals)
        
        # Deriva detectada si más del X% de tests fallan
        drift_detected = (drift_count / total_tests) >= self.sensitivity
        
        # Calcular severidad
        severity = drift_count / total_tests if total_tests > 0 else 0
        
        # Identificar métricas afectadas
        affected_metrics = [
            metric.split("_")[0] 
            for metric, test in drift_tests.items() 
            if test["drift"]
        ]
        
        return {
            "drift_detected": drift_detected,
            "severity": severity,
            "affected_metrics": list(set(affected_metrics)),
            "p_values": {k: v.get("p_value", v.get("degradation_pct", 0)) for k, v in drift_tests.items()},
            "test_results": drift_tests,
            "drift_count": drift_count,
            "total_tests": total_tests,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_drift_status(self) -> Dict[str, Any]:
        """Obtiene estado actual de deriva"""
        
        return {
            "drift_detected": self.drift_detected,
            "last_drift_time": self.last_drift_time.isoformat() if self.last_drift_time else None,
            "drift_count": self.drift_count,
            "baseline_established": self.baseline_established,
            "samples_collected": len(self.reward_history),
            "window_size": self.window_size,
            "drift_threshold": self.drift_threshold,
            "sensitivity": self.sensitivity
        }
    
    def reset_drift_status(self):
        """Reset estado de deriva después de recalibración"""
        self.drift_detected = False
        logger.info("🔄 Estado de deriva reset - Sistema recalibrado")
    
    def get_recommendations(self) -> List[str]:
        """Obtiene recomendaciones basadas en deriva detectada"""
        
        if not self.drift_detected:
            return ["✅ No se detectó deriva - Sistema estable"]
        
        recommendations = []
        
        # Recomendaciones generales
        recommendations.append("🔄 Recalibrar pesos del ensemble")
        recommendations.append("📊 Re-entrenar modelos con datos recientes")
        recommendations.append("🎯 Ajustar thresholds SVI")
        
        # Recomendaciones específicas si tenemos test results
        if hasattr(self, '_last_drift_result'):
            affected = self._last_drift_result.get("affected_metrics", [])
            
            if "reward" in affected:
                recommendations.append("💰 Revisar función de reward")
            
            if "svi" in affected:
                recommendations.append("📈 Recalibrar SVI thresholds")
            
            if "quality" in affected:
                recommendations.append("🔧 Revisar filtros de calidad")
        
        return recommendations

class PatternDriftDetector:
    """Detector de deriva de patrones en combinaciones generadas"""
    
    def __init__(self, pattern_window: int = 100):
        self.pattern_window = pattern_window
        self.combination_history = deque(maxlen=pattern_window)
        self.pattern_stats = {}
        
        logger.info(f"🎨 PatternDriftDetector inicializado: window={pattern_window}")
    
    def add_combinations(self, combinations: List[List[int]]):
        """Añade nuevas combinaciones para análisis de patrones"""
        
        for combo in combinations:
            if len(combo) == 6:  # Validar formato
                self.combination_history.append(tuple(sorted(combo)))
        
        # Analizar patrones si tenemos suficientes datos
        if len(self.combination_history) >= 50:
            self._analyze_patterns()
    
    def _analyze_patterns(self):
        """Analiza patrones en las combinaciones"""
        
        combos = list(self.combination_history)
        
        # 1. Distribución de sumas
        sums = [sum(combo) for combo in combos]
        
        # 2. Distribución por décadas
        decade_dist = {i: 0 for i in range(4)}  # 0-9, 10-19, 20-29, 30-39
        for combo in combos:
            for num in combo:
                decade = num // 10
                if decade < 4:
                    decade_dist[decade] += 1
        
        # 3. Patrones pares/impares
        par_ratios = [sum(1 for n in combo if n % 2 == 0) / 6 for combo in combos]
        
        # 4. Números más frecuentes
        all_numbers = [num for combo in combos for num in combo]
        number_freq = pd.Series(all_numbers).value_counts()
        
        self.pattern_stats = {
            "sum_distribution": {
                "mean": np.mean(sums),
                "std": np.std(sums),
                "min": min(sums),
                "max": max(sums)
            },
            "decade_distribution": decade_dist,
            "par_ratio": {
                "mean": np.mean(par_ratios),
                "std": np.std(par_ratios)
            },
            "top_numbers": number_freq.head(10).to_dict(),
            "analyzed_combinations": len(combos),
            "timestamp": datetime.now().isoformat()
        }
    
    def detect_pattern_anomalies(self) -> Dict[str, Any]:
        """Detecta anomalías en patrones"""
        
        if not self.pattern_stats:
            return {"anomalies_detected": False, "reason": "Insufficient data"}
        
        anomalies = []
        
        # Verificar distribución de sumas (debe estar en rango razonable)
        sum_mean = self.pattern_stats["sum_distribution"]["mean"]
        if sum_mean < 100 or sum_mean > 200:
            anomalies.append(f"Suma promedio anómala: {sum_mean:.1f}")
        
        # Verificar distribución por décadas (no debe estar muy sesgada)
        decade_dist = self.pattern_stats["decade_distribution"]
        total_numbers = sum(decade_dist.values())
        decade_ratios = {k: v/total_numbers for k, v in decade_dist.items()}
        
        # Cada década debería tener aproximadamente 25% ± 15%
        for decade, ratio in decade_ratios.items():
            if ratio < 0.10 or ratio > 0.40:
                anomalies.append(f"Década {decade*10}-{decade*10+9} tiene {ratio:.1%} (anómalo)")
        
        # Verificar ratio par/impar (debería estar cerca de 50%)
        par_ratio = self.pattern_stats["par_ratio"]["mean"]
        if par_ratio < 0.3 or par_ratio > 0.7:
            anomalies.append(f"Ratio par/impar anómalo: {par_ratio:.1%}")
        
        return {
            "anomalies_detected": len(anomalies) > 0,
            "anomalies": anomalies,
            "pattern_stats": self.pattern_stats,
            "timestamp": datetime.now().isoformat()
        }

class CompositeDriftDetector:
    """Detector compuesto que combina deriva de rendimiento y patrones"""
    
    def __init__(self):
        self.performance_detector = PerformanceDriftDetector()
        self.pattern_detector = PatternDriftDetector()
        self.integration_history = []
        
        logger.info("🔄 CompositeDriftDetector inicializado")
    
    def add_episode(self, 
                   reward: float,
                   svi: float, 
                   diversity: float,
                   quality_ok: bool,
                   combinations: List[List[int]]):
        """Añade episodio completo para análisis de deriva"""
        
        # Análisis de rendimiento
        perf_result = self.performance_detector.add_measurement(
            reward, svi, diversity, quality_ok
        )
        
        # Análisis de patrones
        self.pattern_detector.add_combinations(combinations)
        pattern_result = self.pattern_detector.detect_pattern_anomalies()
        
        # Integrar resultados
        integrated_result = {
            "timestamp": datetime.now().isoformat(),
            "performance_drift": perf_result,
            "pattern_anomalies": pattern_result,
            "overall_drift": perf_result.get("drift_detected", False) or pattern_result.get("anomalies_detected", False)
        }
        
        self.integration_history.append(integrated_result)
        
        # Log si hay deriva significativa
        if integrated_result["overall_drift"]:
            logger.warning("🚨 DERIVA INTEGRAL DETECTADA")
            if perf_result.get("drift_detected"):
                logger.warning(f"   📊 Performance: {perf_result.get('affected_metrics', [])}")
            if pattern_result.get("anomalies_detected"):
                logger.warning(f"   🎨 Patterns: {len(pattern_result.get('anomalies', []))} anomalías")
        
        return integrated_result
    
    def should_trigger_recalibration(self) -> Tuple[bool, Dict[str, Any]]:
        """Determina si se debe trigger recalibración automática"""
        
        if not self.integration_history:
            return False, {"reason": "No hay historial suficiente"}
        
        # Verificar últimos N episodios
        recent_episodes = self.integration_history[-5:]
        drift_count = sum(1 for ep in recent_episodes if ep["overall_drift"])
        
        # Trigger si más del 60% de episodios recientes tienen deriva
        should_recalibrate = (drift_count / len(recent_episodes)) >= 0.6
        
        recommendations = []
        if should_recalibrate:
            recommendations.extend(self.performance_detector.get_recommendations())
            recommendations.append("🔄 Ejecutar recalibración automática")
            recommendations.append("📊 Actualizar baseline estadísticas")
        
        return should_recalibrate, {
            "drift_episodes": drift_count,
            "total_episodes": len(recent_episodes),
            "drift_ratio": drift_count / len(recent_episodes),
            "recommendations": recommendations,
            "performance_status": self.performance_detector.get_drift_status(),
            "timestamp": datetime.now().isoformat()
        }

# Función de conveniencia para integración
def create_drift_detector() -> CompositeDriftDetector:
    """Crea detector de deriva configurado para OMEGA"""
    return CompositeDriftDetector()

if __name__ == '__main__':
    # Test básico
    print("📊 Testing Drift Detector...")
    
    detector = create_drift_detector()
    
    # Simular episodios normales
    print("   📈 Simulando episodios normales...")
    for i in range(25):
        detector.add_episode(
            reward=0.7 + np.random.normal(0, 0.05),
            svi=0.75 + np.random.normal(0, 0.03),
            diversity=0.8 + np.random.normal(0, 0.02),
            quality_ok=True,
            combinations=[[np.random.randint(1, 41) for _ in range(6)] for _ in range(3)]
        )
    
    # Simular deriva
    print("   🚨 Simulando deriva...")
    for i in range(10):
        detector.add_episode(
            reward=0.5 + np.random.normal(0, 0.02),  # Performance degradation
            svi=0.6 + np.random.normal(0, 0.02),
            diversity=0.6 + np.random.normal(0, 0.02),
            quality_ok=i > 5,  # Quality issues
            combinations=[[np.random.randint(1, 20) for _ in range(6)] for _ in range(3)]  # Pattern bias
        )
    
    # Verificar recalibración
    should_recal, details = detector.should_trigger_recalibration()
    
    print(f"✅ Test completado:")
    print(f"   🔄 Recalibración requerida: {'✅' if should_recal else '❌'}")
    print(f"   📊 Episodios con deriva: {details['drift_episodes']}/{details['total_episodes']}")
    print(f"   💡 Recomendaciones: {len(details.get('recommendations', []))}")
    
    if should_recal:
        print("   📋 Recomendaciones principales:")
        for rec in details['recommendations'][:3]:
            print(f"      • {rec}")
