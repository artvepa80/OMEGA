# OMEGA_PRO_AI_v10.1/modules/heuristic_optimizer.py - Optimizador de Heurísticas
"""
Optimizador de heurísticas del Jackpot Profiler usando datos reales de lotería
- Analiza patrones en sorteos históricos
- Calibra weights y parámetros de scoring
- Optimiza umbrales de evaluación
- Genera modelos predictivos mejorados
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from pathlib import Path
import json
from collections import Counter, defaultdict
from scipy.optimize import minimize
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score

# Imports internos
from modules.profiling.jackpot_profiler import JackpotProfiler
from utils.validation import validate_combination

logger = logging.getLogger(__name__)

class HeuristicOptimizer:
    """Optimizador de heurísticas para el Jackpot Profiler"""
    
    def __init__(self, data_path: str = "data/historial_kabala_github_fixed.csv"):
        self.data_path = Path(data_path)
        self.historical_data = None
        self.analysis_results = {}
        self.optimized_params = {}
        
        # Parámetros por defecto del Jackpot Profiler
        self.default_params = {
            'balance_weight': 0.3,
            'sum_weight': 0.25,
            'diversity_weight': 0.25,
            'pattern_weight': 0.2,
            'base_prob': 0.4,
            'noise_factor': 0.05,
            'ideal_sum_range': (120, 150),
            'ideal_gap': 6.5,
            'consecutive_penalty': 0.1,
            'multiple_penalty': 0.05
        }
        
        logger.info("🎯 Optimizador de heurísticas inicializado")

    def load_historical_data(self) -> pd.DataFrame:
        """Carga y procesa datos históricos"""
        logger.info("📊 Cargando datos históricos para análisis...")
        
        df = pd.read_csv(self.data_path)
        
        # Extraer combinaciones
        ball_columns = [f'Bolilla {i}' for i in range(1, 7)]
        
        # Buscar columnas alternativas si no existen
        if not all(col in df.columns for col in ball_columns):
            alt_columns = [col for col in df.columns if 'bolilla' in col.lower()]
            if len(alt_columns) >= 6:
                ball_columns = alt_columns[:6]
        
        combinations = []
        dates = []
        additional_features = []
        
        for idx, row in df.iterrows():
            try:
                combo = [int(row[col]) for col in ball_columns]
                if validate_combination(combo):
                    combinations.append(combo)
                    
                    # Fecha
                    if 'fecha' in row:
                        try:
                            date = pd.to_datetime(row['fecha'])
                        except:
                            date = datetime.now()
                    else:
                        date = datetime.now()
                    dates.append(date)
                    
                    # Features adicionales si están disponibles
                    features = {}
                    if 'suma_total' in row:
                        features['suma_total'] = row['suma_total']
                    if 'num_pares' in row:
                        features['num_pares'] = row['num_pares']
                    if 'num_impares' in row:
                        features['num_impares'] = row['num_impares']
                    
                    additional_features.append(features)
                    
            except (ValueError, KeyError):
                continue
        
        # Crear DataFrame procesado
        self.historical_data = pd.DataFrame({
            'fecha': dates,
            'combination': combinations,
            'additional_features': additional_features
        })
        
        logger.info(f"✅ {len(self.historical_data)} combinaciones históricas cargadas")
        return self.historical_data

    def analyze_historical_patterns(self) -> Dict[str, Any]:
        """Analiza patrones en los datos históricos"""
        logger.info("🔍 Analizando patrones históricos...")
        
        if self.historical_data is None:
            self.load_historical_data()
        
        combinations = self.historical_data['combination'].tolist()
        
        # Análisis de distribución de números
        all_numbers = [num for combo in combinations for num in combo]
        number_freq = Counter(all_numbers)
        
        # Análisis de sumas
        sums = [sum(combo) for combo in combinations]
        sum_stats = {
            'mean': np.mean(sums),
            'std': np.std(sums),
            'min': np.min(sums),
            'max': np.max(sums),
            'quartiles': np.percentile(sums, [25, 50, 75]).tolist()
        }
        
        # Análisis de gaps (diferencias entre números consecutivos)
        all_gaps = []
        for combo in combinations:
            sorted_combo = sorted(combo)
            gaps = [sorted_combo[i+1] - sorted_combo[i] for i in range(len(sorted_combo)-1)]
            all_gaps.extend(gaps)
        
        gap_stats = {
            'mean': np.mean(all_gaps),
            'std': np.std(all_gaps),
            'most_common': Counter(all_gaps).most_common(10)
        }
        
        # Análisis de paridad (pares/impares)
        parity_distribution = []
        for combo in combinations:
            pares = sum(1 for num in combo if num % 2 == 0)
            parity_distribution.append(pares)
        
        parity_stats = {
            'mean_pares': np.mean(parity_distribution),
            'distribution': Counter(parity_distribution)
        }
        
        # Análisis de rangos
        range_distributions = []
        for combo in combinations:
            ranges = self._categorize_by_range(combo)
            range_distributions.append(ranges)
        
        range_stats = {
            'mean_distribution': np.mean(range_distributions, axis=0).tolist(),
            'std_distribution': np.std(range_distributions, axis=0).tolist()
        }
        
        # Análisis de consecutivos
        consecutive_counts = []
        for combo in combinations:
            count = self._count_consecutive(sorted(combo))
            consecutive_counts.append(count)
        
        consecutive_stats = {
            'mean': np.mean(consecutive_counts),
            'distribution': Counter(consecutive_counts)
        }
        
        self.analysis_results = {
            'total_combinations': len(combinations),
            'number_frequency': dict(number_freq),
            'sum_statistics': sum_stats,
            'gap_statistics': gap_stats,
            'parity_statistics': parity_stats,
            'range_statistics': range_stats,
            'consecutive_statistics': consecutive_stats,
            'analysis_date': datetime.now().isoformat()
        }
        
        logger.info("✅ Análisis de patrones completado")
        return self.analysis_results

    def optimize_heuristic_parameters(self) -> Dict[str, Any]:
        """Optimiza parámetros de las heurísticas usando datos reales"""
        logger.info("⚙️ Optimizando parámetros de heurísticas...")
        
        if not self.analysis_results:
            self.analyze_historical_patterns()
        
        # Optimización basada en análisis estadístico
        optimized = self.default_params.copy()
        
        # 1. Optimizar rango ideal de suma
        sum_stats = self.analysis_results['sum_statistics']
        mean_sum = sum_stats['mean']
        std_sum = sum_stats['std']
        
        # Usar rango de ±1 desviación estándar alrededor de la media
        optimized['ideal_sum_range'] = (
            int(mean_sum - std_sum),
            int(mean_sum + std_sum)
        )
        
        # 2. Optimizar gap ideal
        gap_stats = self.analysis_results['gap_statistics']
        optimized['ideal_gap'] = gap_stats['mean']
        
        # 3. Ajustar pesos basado en variabilidad observada
        # Mayor peso a características con menor variabilidad (más predictivas)
        
        # Variabilidad de suma (normalizada)
        sum_cv = sum_stats['std'] / sum_stats['mean']
        
        # Variabilidad de gaps
        gap_cv = gap_stats['std'] / gap_stats['mean']
        
        # Variabilidad de distribución de rangos
        range_stats = self.analysis_results['range_statistics']
        range_cv = np.mean(range_stats['std_distribution']) / np.mean(range_stats['mean_distribution'])
        
        # Ajustar pesos inversamente proporcional a la variabilidad
        total_inv_cv = (1/sum_cv) + (1/gap_cv) + (1/range_cv)
        
        optimized['sum_weight'] = (1/sum_cv) / total_inv_cv * 0.8  # 80% del peso total
        optimized['diversity_weight'] = (1/gap_cv) / total_inv_cv * 0.8
        optimized['balance_weight'] = (1/range_cv) / total_inv_cv * 0.8
        optimized['pattern_weight'] = 0.2  # Peso fijo para patrones
        
        # 4. Ajustar probabilidad base
        # Basado en la distribución de frecuencias
        freq_std = np.std(list(self.analysis_results['number_frequency'].values()))
        freq_mean = np.mean(list(self.analysis_results['number_frequency'].values()))
        
        # Mayor uniformidad → mayor probabilidad base
        uniformity = 1 - (freq_std / freq_mean)
        optimized['base_prob'] = 0.3 + (uniformity * 0.4)  # Entre 0.3 y 0.7
        
        # 5. Ajustar penalizaciones basado en frecuencia observada
        consec_stats = self.analysis_results['consecutive_statistics']
        consec_freq = consec_stats['distribution'].get(3, 0) / consec_stats['distribution'].get(0, 1)
        
        # Mayor frecuencia de consecutivos → menor penalización
        optimized['consecutive_penalty'] = max(0.05, 0.15 - consec_freq * 0.1)
        
        self.optimized_params = optimized
        
        logger.info("✅ Parámetros optimizados")
        return optimized

    def create_enhanced_profiler(self) -> 'EnhancedJackpotProfiler':
        """Crea un Jackpot Profiler mejorado con parámetros optimizados"""
        if not self.optimized_params:
            self.optimize_heuristic_parameters()
        
        return EnhancedJackpotProfiler(
            optimized_params=self.optimized_params,
            historical_analysis=self.analysis_results
        )

    def validate_optimization(self, test_combinations: List[List[int]]) -> Dict[str, Any]:
        """Valida la optimización comparando resultados antes/después"""
        logger.info("🧪 Validando optimización...")
        
        # Profiler original
        original_profiler = JackpotProfiler()
        
        # Profiler optimizado
        enhanced_profiler = self.create_enhanced_profiler()
        
        # Evaluar ambos en combinaciones de test
        original_results = []
        enhanced_results = []
        
        for combo in test_combinations:
            try:
                # Resultado original
                orig_result = original_profiler.profile([combo])
                if orig_result:
                    original_results.append(orig_result[0]['jackpot_prob'])
                else:
                    original_results.append(0.0)
                
                # Resultado mejorado
                enh_result = enhanced_profiler.profile([combo])
                if enh_result:
                    enhanced_results.append(enh_result[0]['jackpot_prob'])
                else:
                    enhanced_results.append(0.0)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error evaluando {combo}: {e}")
                original_results.append(0.0)
                enhanced_results.append(0.0)
        
        # Análisis comparativo
        validation_results = {
            'original_stats': {
                'mean': np.mean(original_results),
                'std': np.std(original_results),
                'range': np.max(original_results) - np.min(original_results),
                'unique_values': len(set(original_results))
            },
            'enhanced_stats': {
                'mean': np.mean(enhanced_results),
                'std': np.std(enhanced_results),
                'range': np.max(enhanced_results) - np.min(enhanced_results),
                'unique_values': len(set(enhanced_results))
            },
            'improvement_metrics': {
                'variance_improvement': np.std(enhanced_results) / np.std(original_results) if np.std(original_results) > 0 else 1,
                'range_improvement': (np.max(enhanced_results) - np.min(enhanced_results)) / (np.max(original_results) - np.min(original_results)) if (np.max(original_results) - np.min(original_results)) > 0 else 1,
                'diversity_improvement': len(set(enhanced_results)) / len(set(original_results)) if len(set(original_results)) > 0 else 1
            }
        }
        
        logger.info("✅ Validación completada")
        return validation_results

    def _count_consecutive(self, numbers: List[int]) -> int:
        """Cuenta números consecutivos"""
        if len(numbers) <= 1:
            return 0
        
        consecutive = 0
        current_streak = 1
        
        for i in range(1, len(numbers)):
            if numbers[i] == numbers[i-1] + 1:
                current_streak += 1
            else:
                if current_streak >= 2:
                    consecutive += current_streak
                current_streak = 1
        
        if current_streak >= 2:
            consecutive += current_streak
        
        return consecutive

    def _categorize_by_range(self, numbers: List[int]) -> List[int]:
        """Categoriza números por rangos"""
        ranges = [0, 0, 0]
        for num in numbers:
            if 1 <= num <= 13:
                ranges[0] += 1
            elif 14 <= num <= 27:
                ranges[1] += 1
            elif 28 <= num <= 40:
                ranges[2] += 1
        return ranges

    def save_optimization_results(self):
        """Guarda resultados de optimización"""
        output_dir = Path("results/heuristic_optimization")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar análisis
        analysis_file = output_dir / f"historical_analysis_{timestamp}.json"
        with open(analysis_file, 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
        
        # Guardar parámetros optimizados
        params_file = output_dir / f"optimized_params_{timestamp}.json"
        with open(params_file, 'w') as f:
            json.dump(self.optimized_params, f, indent=2, default=str)
        
        logger.info(f"💾 Resultados guardados en {output_dir}")


class EnhancedJackpotProfiler(JackpotProfiler):
    """Jackpot Profiler mejorado con parámetros optimizados"""
    
    def __init__(self, optimized_params: Dict[str, Any], historical_analysis: Dict[str, Any]):
        super().__init__()
        self.optimized_params = optimized_params
        self.historical_analysis = historical_analysis
        self.is_enhanced = True
        
        logger.info("🚀 Jackpot Profiler mejorado inicializado")

    def _profile_with_heuristics(self, combinaciones: List[List[int]]) -> List[Dict[str, Any]]:
        """Versión mejorada con parámetros optimizados"""
        results = []
        
        for comb in combinaciones:
            arr = np.array(comb)
            
            # Usar parámetros optimizados
            balance_score = self._calculate_balance_score_enhanced(arr)
            sum_score = self._calculate_sum_score_enhanced(arr)
            diversity_score = self._calculate_diversity_score_enhanced(arr)
            pattern_score = self._calculate_pattern_score_enhanced(arr)
            
            # Combinar con pesos optimizados
            prob_adjustment = (
                balance_score * self.optimized_params['balance_weight'] +
                sum_score * self.optimized_params['sum_weight'] +
                diversity_score * self.optimized_params['diversity_weight'] +
                pattern_score * self.optimized_params['pattern_weight']
            ) * 0.6  # Aumentar rango de ajuste
            
            final_prob = self.optimized_params['base_prob'] + prob_adjustment
            
            # Ruido adaptativo basado en datos históricos
            np.random.seed(hash(tuple(sorted(comb))) % 2**32)
            noise = np.random.uniform(
                -self.optimized_params['noise_factor'], 
                self.optimized_params['noise_factor']
            )
            final_prob += noise
            
            # Clamp mejorado
            final_prob = max(0.05, min(0.95, final_prob))
            
            results.append({
                "combination": comb,
                "jackpot_prob": round(final_prob, 4)
            })
        
        return results

    def _calculate_sum_score_enhanced(self, arr: np.ndarray) -> float:
        """Score de suma mejorado con rango optimizado"""
        suma = np.sum(arr)
        ideal_range = self.optimized_params['ideal_sum_range']
        
        if ideal_range[0] <= suma <= ideal_range[1]:
            center = (ideal_range[0] + ideal_range[1]) / 2
            distance_from_center = abs(suma - center)
            max_distance = (ideal_range[1] - ideal_range[0]) / 2
            return 1.0 - (distance_from_center / max_distance)
        else:
            if suma < ideal_range[0]:
                distance = ideal_range[0] - suma
            else:
                distance = suma - ideal_range[1]
            
            return max(-0.5, -distance / 40.0)

    def _calculate_diversity_score_enhanced(self, arr: np.ndarray) -> float:
        """Score de diversidad mejorado con gap optimizado"""
        sorted_arr = np.sort(arr)
        gaps = np.diff(sorted_arr)
        
        ideal_gap = self.optimized_params['ideal_gap']
        gap_scores = []
        
        for gap in gaps:
            if 1 <= gap <= 15:  # Rango expandido
                gap_score = 1.0 - abs(gap - ideal_gap) / ideal_gap
            else:
                gap_score = -0.4
            gap_scores.append(gap_score)
        
        return np.mean(gap_scores)

    def _calculate_pattern_score_enhanced(self, arr: np.ndarray) -> float:
        """Score de patrones mejorado con penalizaciones ajustadas"""
        sorted_arr = np.sort(arr)
        
        # Penalización por consecutivos ajustada
        consecutive_penalty = 0
        current_run = 1
        
        for i in range(1, len(sorted_arr)):
            if sorted_arr[i] - sorted_arr[i-1] == 1:
                current_run += 1
            else:
                if current_run >= 3:
                    consecutive_penalty -= current_run * self.optimized_params['consecutive_penalty']
                current_run = 1
        
        if current_run >= 3:
            consecutive_penalty -= current_run * self.optimized_params['consecutive_penalty']
        
        # Penalización por múltiplos ajustada
        multiples_5 = np.sum(arr % 5 == 0)
        multiples_10 = np.sum(arr % 10 == 0)
        
        multiple_penalty = -multiples_5 * self.optimized_params['multiple_penalty'] - multiples_10 * (self.optimized_params['multiple_penalty'] * 2)
        
        return consecutive_penalty + multiple_penalty

    def _calculate_balance_score_enhanced(self, arr: np.ndarray) -> float:
        """Score de balance mejorado con distribución optimizada"""
        # Usar distribución real observada en datos históricos
        if 'range_statistics' in self.historical_analysis:
            ideal_distribution = np.array(self.historical_analysis['range_statistics']['mean_distribution'])
        else:
            ideal_distribution = np.array([1.5, 1.5, 1.5])  # Fallback
        
        # Calcular distribución actual
        current_distribution = np.array(self._categorize_by_range(arr))
        
        # Calcular desviación de la distribución ideal
        deviation = np.sum(np.abs(current_distribution - ideal_distribution))
        
        # Score inverso
        return max(-0.5, 1.0 - deviation / 6.0)

    def _categorize_by_range(self, arr) -> List[int]:
        """Categoriza números por rangos"""
        ranges = [0, 0, 0]
        for num in arr:
            if 1 <= num <= 13:
                ranges[0] += 1
            elif 14 <= num <= 27:
                ranges[1] += 1
            elif 28 <= num <= 40:
                ranges[2] += 1
        return ranges


# Función principal
def optimize_jackpot_heuristics(data_path: str = "data/historial_kabala_github_fixed.csv") -> Dict[str, Any]:
    """Ejecuta optimización completa de heurísticas"""
    
    optimizer = HeuristicOptimizer(data_path)
    
    # Análisis histórico
    analysis = optimizer.analyze_historical_patterns()
    
    # Optimización de parámetros
    optimized_params = optimizer.optimize_heuristic_parameters()
    
    # Guardar resultados
    optimizer.save_optimization_results()
    
    return {
        'historical_analysis': analysis,
        'optimized_parameters': optimized_params,
        'enhancement_ready': True
    }


if __name__ == "__main__":
    # Ejecutar optimización
    results = optimize_jackpot_heuristics()
    
    print("\n" + "="*60)
    print("🎯 OPTIMIZACIÓN DE HEURÍSTICAS COMPLETADA")
    print("="*60)
    
    analysis = results['historical_analysis']
    params = results['optimized_parameters']
    
    print(f"📊 Combinaciones analizadas: {analysis['total_combinations']}")
    print(f"📈 Suma promedio histórica: {analysis['sum_statistics']['mean']:.1f}")
    print(f"🎯 Gap promedio histórico: {analysis['gap_statistics']['mean']:.1f}")
    
    print(f"\n⚙️ PARÁMETROS OPTIMIZADOS:")
    print(f"  • Rango suma ideal: {params['ideal_sum_range']}")
    print(f"  • Gap ideal: {params['ideal_gap']:.2f}")
    print(f"  • Probabilidad base: {params['base_prob']:.2f}")
    print(f"  • Pesos: Sum={params['sum_weight']:.2f}, Div={params['diversity_weight']:.2f}, Bal={params['balance_weight']:.2f}")
    
    print("="*60)
