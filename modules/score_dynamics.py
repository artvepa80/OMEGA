# OMEGA_PRO_AI_v10.1/modules/score_dynamics.py

import pandas as pd
import numpy as np
from collections import Counter
from typing import List, Dict, Any, Optional, Union, Sequence, Set
from scipy import stats
import math

# Advanced statistical analysis utilities
def calculate_shannon_entropy(sequence: List[int]) -> float:
    """Calculate Shannon entropy for a sequence of numbers.
    
    Measures the randomness or diversity of a number combination.
    Higher entropy suggests more unpredictable/diverse combinations.
    """
    if not sequence:
        return 0.0
    
    unique_nums = set(sequence)
    total_nums = len(sequence)
    probabilities = [sequence.count(num) / total_nums for num in unique_nums]
    entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
    return entropy

def calculate_z_scores(sequence: List[int]) -> List[float]:
    """Calculate Z-scores for a sequence of numbers.
    
    Identifies how many standard deviations each number is from the mean.
    Useful for detecting statistical outliers in number combinations.
    """
    if len(sequence) < 2:
        return [0.0] * len(sequence)
    
    mean = np.mean(sequence)
    std = np.std(sequence)
    return [(x - mean) / std if std != 0 else 0.0 for x in sequence]

def calculate_autocorrelation(sequence: List[int], lag: int = 1) -> float:
    """Calculate autocorrelation for a sequence.
    
    Measures similarity between a sequence and a lagged version of itself.
    Helps detect periodic or patterned behavior in number selections.
    """
    if len(sequence) <= lag:
        return 0.0
    
    def autocorr(x, l):
        return np.corrcoef(x[:-l], x[l:])[0,1]
    
    return autocorr(sequence, lag)

def chi_square_goodness_of_fit(sequence: List[int], expected_distribution: Optional[Dict[int, float]] = None) -> float:
    """Perform Chi-square goodness of fit test.
    
    Determines how well an observed distribution matches an expected distribution.
    Lower p-values suggest significant deviation from expected.
    """
    if not sequence:
        return 1.0  # Default for empty sequence
    
    # Default to uniform distribution if no expected distribution provided
    if expected_distribution is None:
        expected_prob = 1/40  # Assuming numbers from 1 to 40
        expected_distribution = {num: expected_prob for num in range(1, 41)}
    
    observed = Counter(sequence)
    obs_freq = [observed.get(num, 0) for num in range(1, 41)]
    exp_freq = [expected_distribution.get(num, 0) * len(sequence) for num in range(1, 41)]
    
    try:
        chi2_stat, p_value = stats.chisquare(obs_freq, exp_freq)
        return p_value
    except Exception:
        return 1.0  # Default if computation fails

def calculate_pattern_complexity(sequence: List[int]) -> float:
    """Calculate a complexity score based on unique subsequences.
    
    Higher values indicate more intricate/unusual number patterns.
    """
    if len(sequence) < 3:
        return 0.0
    
    # Generate all 3-number subsequences
    subsequences = [tuple(sequence[i:i+3]) for i in range(len(sequence)-2)]
    unique_subseqs = len(set(subsequences))
    complexity = unique_subseqs / len(subsequences)
    return complexity
from modules.filters.rules_filter import FiltroEstrategico
from utils.validation import validate_combination
import os
from scipy.spatial.distance import hamming
import logging
from joblib import Parallel, delayed
from modules.utils.parallel import safe_parallel_map
from modules.arima_cycles import arima_cycles  # NEW: Import ARIMA module

# Configuración avanzada de ponderaciones
SCORE_CONFIG = {
    'weights': {
        'sum_total': 0.9,
        'even_count': 0.7,
        'consecutive_diff': 1.0,
        'repeats_last_draw': 0.9,
        'decade_distribution': 1.0,
        'decade_overload': 0.6,
        'prime_numbers': 0.5,
        'diversity': 0.4
    },
    'bonuses': {
        'low_numbers': 0.25,
        'high_numbers': 0.25,
        'cluster_performance': 0.5,
        'cluster_frequency': 0.3,
        'core_hits': 1.0,  # NEW: Weight for core bonus
        'rare_numbers': 0.40,
        'diversity_boost': 0.30,
        # Advanced statistical bonuses
        'complexity_boost': 0.20,  # Bonus for complex patterns
        'entropy_boost': 0.15,     # Bonus for high entropy combinations
        'outlier_bonus': 0.25      # Bonus for statistically rare combinations
    },
    'source_weights': {
        'apriori': 1.2,
        'clustering': 1.3,
        'ghost_rng': 1.35,
        'lstm_v2': 1.25,
        'montecarlo': 1.1,
        'genetico': 1.15,
        'transformer_deep': 1.2,
        'default': 1.0,
        'fallback': 0.8
    },
    'perfil_thresholds': {
        'moderado': 0.7,
        'conservador': 0.8,
        'agresivo': 0.4
    }
}

primes_set = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37}

# NEW: Core bonus calculation function
def bonus_core_hits(comb: Sequence[int], core_set: Set[int]) -> float:
    """Calcula el bonus según coincidencias con `core_set`.
    • +0.05 por cada número común.
    • Límite superior +0.30 (=> 6 hits).
    """
    # Asegurar que core_set es un set (en caso de que se pase una lista)
    if not isinstance(core_set, set):
        core_set = set(core_set) if core_set else set()
    
    hits = len(set(comb).intersection(core_set))
    return min(0.05 * hits, 0.30)

# NEW: Rare number bonus calculation
def bonus_rare_numbers(comb: Sequence[int], historial_data: Union[pd.DataFrame, np.ndarray, List]) -> float:
    """Calcula bonus por números históricamente raros.
    • Identifica números en bottom 30% de frecuencia histórica
    • +0.08 por cada número raro en la combinación
    • Límite superior +0.32 (=> 4+ números raros)
    """
    try:
        # Extract historical numbers
        if isinstance(historial_data, pd.DataFrame):
            if not historial_data.empty:
                lottery_cols = [col for col in historial_data.columns if 'bolilla' in col.lower()][:6]
                if len(lottery_cols) >= 6:
                    hist_nums = historial_data[lottery_cols].values.flatten()
                else:
                    numeric_cols = historial_data.select_dtypes(include='number').columns
                    hist_nums = historial_data[numeric_cols[:6]].values.flatten()
            else:
                return 0.0
        elif isinstance(historial_data, np.ndarray):
            hist_nums = historial_data.flatten()
        elif isinstance(historial_data, list):
            hist_nums = [n for row in historial_data for n in row if isinstance(row, (list, tuple))]
        else:
            return 0.0
            
        if len(hist_nums) < 50:  # Need sufficient historical data
            return 0.0
            
        # Calculate frequency
        from collections import Counter
        freq_count = Counter(hist_nums)
        total_nums = len(set(hist_nums))
        
        if total_nums < 20:  # Need diverse historical data
            return 0.0
            
        # Find rare numbers (bottom 30% by frequency)
        sorted_by_freq = sorted(freq_count.items(), key=lambda x: x[1])
        rare_threshold = int(len(sorted_by_freq) * 0.30)
        rare_numbers = {num for num, _ in sorted_by_freq[:rare_threshold] if 1 <= num <= 40}
        
        # Calculate bonus
        rare_count = len(set(comb).intersection(rare_numbers))
        return min(0.08 * rare_count, 0.32)
        
    except Exception:
        return 0.0

def clean_combination(combo, logger):
    """Convierte np.int64 a int en combinaciones y valida duplicates/rango."""
    try:
        cleaned = [int(n) if isinstance(n, np.integer) else n for n in combo]
        if len(set(cleaned)) != len(cleaned) or not all(1 <= n <= 40 for n in cleaned):
            logger.warning(f"⚠️ Invalid after clean: duplicates or out of range {cleaned}")
            return None
        return cleaned
    except Exception as e:
        logger.info(f"⚠️ Failed to clean combination {combo}: {str(e)}")
        return None

def calculate_diversity(combo: List[int], other_combos: List[List[int]]) -> float:
    """Calculate diversity score based on Jaccard similarity (1 - avg similarity)."""
    if not other_combos:
        return 1.0
    set_combo = set(combo)
    jaccards = [len(set_combo & set(other)) / len(set_combo | set(other)) for other in other_combos]
    similarity = np.mean(jaccards) if jaccards else 0.0
    return 1.0 - similarity

def score_combinations(
    combinations: List[Dict[str, Any]],
    historial: Union[pd.DataFrame, np.ndarray, List[List[int]]],
    cluster_data: Optional[Dict] = None,
    config: Dict = SCORE_CONFIG,
    perfil_svi: str = 'moderado',
    logger: Optional[logging.Logger] = None,
    core_set: Optional[Set[int]] = None,  # Optional core set parameter
    sequential: bool = False  # NEW: Force sequential processing
) -> List[Dict[str, Any]]:
    """
    Calcula puntuaciones avanzadas para combinaciones considerando:
    - Validación estadística básica
    - Distribución por décadas
    - Repetición con el último sorteo
    - Bonificaciones por extremos, clusters y CORE
    - Diversidad entre combinaciones
    - Ponderación según modelo generador
    - NEW: Multiplicación por ARIMA_score para sensores temporales
    """
    if logger is None:
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO)

    logger.info("🚀 Starting score_combinations")
    
    # NEW: Log core set usage
    if core_set:
        logger.info(f"🎯 Using CORE SET: {sorted(core_set)}")
    else:
        logger.info("ℹ️ No core set provided - skipping core bonus")

    # Columnas esperadas para el historial: cada fila con 6 columnas (una por bolilla)
    # Soportar ambos formatos: 'Bolilla X' y 'bolilla_x'
    historial_columns_standard = [f'Bolilla {i}' for i in range(1, 7)]
    historial_columns_underscore = [f'bolilla_{i}' for i in range(1, 7)]

    # Aceptar DataFrame, ndarray (shape n×6) o lista; validar dimensiones e filtrar listas incompletas
    if isinstance(historial, pd.DataFrame):
        df_hist = historial.copy()
        
        # 🔧 FIX: Detectar y normalizar formato de columnas
        if all(col in df_hist.columns for col in historial_columns_underscore):
            # Formato 'bolilla_x' - renombrar a formato estándar
            column_mapping = {f'bolilla_{i}': f'Bolilla {i}' for i in range(1, 7)}
            df_hist = df_hist.rename(columns=column_mapping)
            logger.debug("🔄 Columnas renombradas de 'bolilla_x' a 'Bolilla X'")
        elif not all(col in df_hist.columns for col in historial_columns_standard):
            # Intentar mapeo flexible
            possible_columns = [col for col in df_hist.columns if any(str(i) in col for i in range(1, 7))]
            if len(possible_columns) >= 6:
                # Usar las primeras 6 columnas numéricas encontradas
                df_hist = df_hist[possible_columns[:6]]
                df_hist.columns = historial_columns_standard
                logger.debug(f"🔄 Mapeado columnas flexibles: {possible_columns[:6]} → {historial_columns_standard}")
        
    elif isinstance(historial, np.ndarray):
        if historial.ndim == 2 and historial.shape[1] == 6:
            df_hist = pd.DataFrame(historial, columns=historial_columns_standard)
        else:
            logger.error(f"🚨 Historial ndarray inválido con forma {historial.shape}, debe ser (n,6)")
            raise ValueError(f"Historial ndarray inválido: forma esperada (n,6), obtenida {historial.shape}")
    elif isinstance(historial, list):
        complete_rows = [row for row in historial if isinstance(row, (list, tuple)) and len(row) == 6]
        removed = len(historial) - len(complete_rows)
        if removed > 0:
            logger.warning(f"⚠️ Se eliminaron {removed} filas incompletas del historial")
        df_hist = pd.DataFrame(complete_rows, columns=historial_columns_standard) if complete_rows else pd.DataFrame(columns=historial_columns_standard)
    else:
        logger.warning(f"🚨 Tipo de historial no soportado ({type(historial)}), creando DataFrame vacío")
        df_hist = pd.DataFrame(columns=historial_columns_standard)

    # A partir de aquí, `historial` siempre es un DataFrame normalizado con formato 'Bolilla X'
    historial = df_hist
    historial_columns = historial_columns_standard

    # Notificar si historial es muy pequeño tras filtrado
    rows = historial.shape[0]
    if rows == 0:
        logger.warning("⚠️ Historial vacío después del filtrado; el scoring puede no ser confiable")
    elif rows < 10:
        logger.warning(f"⚠️ Historial reducido a {rows} filas; considera más datos para un scoring fiable")

    # Validación de contenido y extracción de último sorteo
    ultimos = []
    if not historial.empty and all(col in historial.columns for col in historial_columns):
        # Coerce numeric and sanitize to avoid numpy type issues
        historial = historial[historial_columns].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
        valid_range = all(historial[col].between(1, 40).all() for col in historial_columns)
        if valid_range:
            ultimos = historial.iloc[-1][historial_columns].tolist()
            if not validate_combination(ultimos):
                logger.warning(f"⚠️ Último sorteo inválido: {ultimos}, usando default fallback")
                ultimos = []
        else:
            logger.info("🚨 Valores fuera de rango [1,40] en historial; se ignora último sorteo")
    else:
        logger.info("🚨 Historial inválido o vacío; no se extrae último sorteo")

    # NEW: Calcular serie temporal para ARIMA (sumas de bolillas) with statistical logging
    if not historial.empty:
        historial_sums = historial.sum(axis=1).tolist()
        try:
            arima_score = arima_cycles(historial_sums)  # NEW: Obtener ARIMA_score
            logger.info(f"🔮 ARIMA_score calculado: {arima_score:.3f}")
            
            # Log ARIMA analysis with advanced metrics
            try:
                ADVANCED_LOGGING_AVAILABLE
            except NameError:
                ADVANCED_LOGGING_AVAILABLE = False
            
            if ADVANCED_LOGGING_AVAILABLE and metrics_collector:
                # Analyze temporal patterns in sums
                sum_mean = np.mean(historial_sums)
                sum_std = np.std(historial_sums)
                
                # Simple trend analysis
                if len(historial_sums) >= 10:
                    recent_avg = np.mean(historial_sums[-10:])
                    overall_avg = np.mean(historial_sums)
                    trend_ratio = recent_avg / overall_avg if overall_avg > 0 else 1.0
                else:
                    trend_ratio = 1.0
                
                # ARIMA significance assessment
                arima_deviation = abs(arima_score - 1.0)  # Deviation from neutral
                is_significant = arima_deviation > 0.1
                
                metrics_collector.log_statistical_analysis(
                    analysis_type="temporal_analysis",
                    test_name="arima_cycles_analysis",
                    test_statistic=arima_score,
                    p_value=1.0 - arima_deviation,  # Inverse relationship
                    significance_level=0.1,  # More sensitive for temporal data
                    effect_size=arima_deviation,
                    confidence_interval=(arima_score - 0.1, arima_score + 0.1),
                    sample_size=len(historial_sums),
                    series_mean=sum_mean,
                    series_std=sum_std,
                    trend_ratio=trend_ratio,
                    temporal_pattern="arima_cycles",
                    score_interpretation="boost" if arima_score > 1.0 else "neutral" if arima_score == 1.0 else "penalty"
                )
                
        except Exception as e:
            arima_score = 1.0  # Default neutral si error
            logger.warning(f"⚠️ Error en ARIMA_cycles: {e}, usando 1.0 como default")
            
            # Log ARIMA failure
            try:
                ADVANCED_LOGGING_AVAILABLE
            except NameError:
                ADVANCED_LOGGING_AVAILABLE = False
            
            if ADVANCED_LOGGING_AVAILABLE and metrics_collector:
                metrics_collector.log_statistical_analysis(
                    analysis_type="temporal_analysis",
                    test_name="arima_cycles_analysis_failed",
                    test_statistic=1.0,
                    p_value=1.0,
                    significance_level=0.1,
                    effect_size=0.0,
                    confidence_interval=(1.0, 1.0),
                    sample_size=len(historial_sums),
                    error_message=str(e),
                    test_failed=True
                )
    else:
        arima_score = 1.0
        logger.info("ℹ️ Historial vacío; ARIMA_score default a 1.0")

    # Inicializar filtro estratégico
    filtro = FiltroEstrategico()
    try:
        filtro.cargar_historial(historial.values.tolist() if not historial.empty else [])
    except Exception as e:
        logger.info(f"❌ Error loading historial into FiltroEstrategico: {e}")
        filtro = None

    # Calcular umbral dinámico basado en historial
    threshold = config['perfil_thresholds'].get(perfil_svi, 0.7)
    if filtro and rows > 0:
        try:
            def calc_score(row):
                try:
                    result = filtro.aplicar_filtros(row, return_score=True, perfil_svi=perfil_svi)
                    # Handle different return formats
                    if isinstance(result, tuple) and len(result) >= 2:
                        return result[1]  # Return score (second element)
                    elif isinstance(result, (int, float)):
                        return result
                    else:
                        return 0.5  # Default score
                except Exception as e:
                    logger.warning(f"Error en calc_score: {e}")
                    return 0.5
            
            # Use sequential processing to avoid multiprocessing issues
            # Ensure we have valid numeric data for historical scores
            try:
                if hasattr(historial, 'tail'):
                    hist_data = historial.tail(100).values
                else:
                    hist_data = historial.values[-100:] if hasattr(historial, 'values') else historial[-100:]
                
                # Robust handling of boolean masking and array validation
                if hist_data.size > 0:
                    # Ensure valid numeric data and create proper boolean mask
                    try:
                        # Convert to numeric, handling potential mixed types
                        hist_data_numeric = np.array(hist_data, dtype=float)
                        
                        # Create boolean mask with explicit conversion
                        valid_mask = np.logical_not(np.isnan(hist_data_numeric).any(axis=1))
                        
                        # Ensure valid_mask is a numpy array of booleans
                        if isinstance(valid_mask, np.ndarray) and valid_mask.ndim == 1:
                            hist_data = hist_data[valid_mask] if valid_mask.any() else np.array([]).reshape(0, hist_data.shape[1])
                        else:
                            hist_data = np.array([]).reshape(0, hist_data.shape[1])
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to process historical data: {e}")
                        hist_data = np.array([]).reshape(0, hist_data.shape[1])
                else:
                    hist_data = np.array([])
                
                # Safe iteration using numpy/list comprehension
                historical_scores = []
                if hist_data.size > 0 and len(hist_data) > 0:
                    historical_scores = [calc_score(row) for row in hist_data]
                    
                # Log iteration details for debugging
                logger.debug(f"🔍 Historical data processing: {len(historical_scores)} valid historical scores")
            except (TypeError, IndexError, ValueError):
                historical_scores = []
            if historical_scores:
                percentile_val = np.percentile(historical_scores, 25)
                threshold = max(threshold * 0.8, min(threshold, max(0, percentile_val)))
                logger.info(f"🔄 Adjusted threshold to {threshold:.3f} based on historical scores")
        except Exception as e:
            logger.info(f"⚠️ Could not adjust threshold dynamically: {e}")

    scored = []
    metrics_log = []
    valid_combinations = [clean_combination(cd['combination'], logger) for cd in combinations 
                         if isinstance(cd, dict) and 'combination' in cd and validate_combination(cd['combination'])]

    rejected_count = 0
    
    # Convert DataFrame to serializable format for parallel processing
    historial_values = historial.values.tolist() if not historial.empty else []
    historial_columns = historial.columns.tolist() if not historial.empty else []
    
    # Create a function that doesn't capture non-serializable objects
    def create_score_function(hist_values, hist_cols, ultimos_list, arima_score_val, 
                             threshold_val, config_dict, primes_set_list, 
                             valid_combinations_list, core_set_list):
        def score_single_parallel(item_data):
            cd, idx = item_data
            
            if not isinstance(cd, dict) or 'combination' not in cd:
                return None, 1
            combo = clean_combination(cd['combination'], None)  # Pass None for logger to avoid issues
            if combo is None or not validate_combination(combo):
                return None, 1

            source = cd.get('source', 'default')
            svi_score = cd.get('svi_score', cd.get('svi', 0.5))

            score_base = 0.5
            
            # Create minimal FiltroEstrategico for this process
            try:
                from modules.filters.rules_filter import FiltroEstrategico
                local_filtro = FiltroEstrategico()
                local_filtro.cargar_historial(hist_values)
                score_base, razones = local_filtro.aplicar_filtros(combo, return_score=True)
                if score_base < threshold_val:
                    return None, 1
            except Exception:
                razones = []

            sorted_combo = sorted(combo)
            score = 0.0
            bonus = 0.0
            weights = config_dict['weights']
            bonuses = config_dict['bonuses']

            # 1. Suma total
            total = sum(sorted_combo)
            if 100 <= total <= 150:
                score += weights['sum_total']

            # 2. Número de pares
            pares = sum(1 for n in sorted_combo if n % 2 == 0)
            if 1 <= pares <= 5:
                score += weights['even_count']

            # 3. Saltos totales
            diff_sum = sum(sorted_combo[i] - sorted_combo[i-1] for i in range(1, len(sorted_combo)))
            if 22 <= diff_sum <= 37:
                score += weights['consecutive_diff']

            # 4. Repetidos con último sorteo
            repetidos = len(set(sorted_combo) & set(ultimos_list))
            if repetidos <= 2:
                score += weights['repeats_last_draw']

            # 5. Decades
            combo_array = np.array(sorted_combo, dtype=int)
            decades = np.minimum((combo_array - 1) // 10, 3)
            decade_counts = {}
            for d in decades:
                decade_counts[d] = decade_counts.get(d, 0) + 1
            if len(decade_counts) >= 3:
                score += weights['decade_distribution']
            if max(decade_counts.values()) <= 3:
                score += weights['decade_overload']

            # 6. Primos
            prime_count = sum(1 for n in sorted_combo if n in primes_set_list)
            if 1 <= prime_count <= 3:
                score += weights['prime_numbers'] * min(prime_count / 3, 1.0)

            # 7. Diversidad
            diversity_score = calculate_diversity(sorted_combo, valid_combinations_list)
            score += weights['diversity'] * diversity_score

            # Bonificaciones
            if sum(1 for n in sorted_combo if 1 <= n <= 5) >= 2:
                bonus += bonuses['low_numbers']
            if sum(1 for n in sorted_combo if 36 <= n <= 40) >= 2:
                bonus += bonuses['high_numbers']

            # Core bonus
            core_bonus = 0.0
            if core_set_list:
                core_bonus = bonus_core_hits(sorted_combo, set(core_set_list)) * bonuses['core_hits']
                bonus += core_bonus

            # Rare number bonus
            rare_bonus = 0.0
            if hist_values:
                # Create temporary DataFrame for rare number calculation
                import pandas as pd
                temp_df = pd.DataFrame(hist_values, columns=hist_cols)
                rare_bonus = bonus_rare_numbers(sorted_combo, temp_df) * bonuses['rare_numbers']
                bonus += rare_bonus

            source_weight = config_dict['source_weights'].get(source, config_dict['source_weights']['default'])
            final_score = (score * source_weight) + bonus + (svi_score * 0.3)

            # Multiply by ARIMA score
            final_score *= arima_score_val

            metrics = {
                'combination': sorted_combo,
                'score': final_score,
                'svi_score': svi_score,
                'source': source,
                'sum_total': total,
                'even_count': pares,
                'diff_sum': diff_sum,
                'repeats': repetidos,
                'decades': dict(decade_counts),
                'primes': prime_count,
                'diversity': diversity_score,
                'filter_reasons': razones,
                'core_bonus': core_bonus,
                'rare_bonus': rare_bonus,
                'arima_score': arima_score_val
            }

            return {
                'combination': sorted_combo,
                'score': round(final_score, 3),
                'svi_score': svi_score,
                'source': source,
                'metrics': metrics,
                'normalized': 0.0
            }, 0
        
        return score_single_parallel
    
    def score_single(cd, idx):
        if not isinstance(cd, dict) or 'combination' not in cd:
            logger.info(f"⚠️ Skipping invalid entry at index {idx}: {cd}")
            return None, 1
        combo = clean_combination(cd['combination'], logger)
        if combo is None or not validate_combination(combo):
            logger.info(f"⚠️ Skipping invalid combination at index {idx}: {combo}")
            return None, 1

        source = cd.get('source', 'default')
        svi_score = cd.get('svi_score', cd.get('svi', 0.5))

        score_base = 0.5
        razones = []
        if filtro:
            try:
                score_base, razones = filtro.aplicar_filtros(combo, return_score=True, perfil_svi=perfil_svi)
                if score_base < threshold:
                    logger.info(f"🧹 Rejected combination: {combo}, Score: {score_base:.4f}, Reasons: {razones}")
                    return None, 1
            except Exception as e:
                logger.info(f"⚠️ Error applying FiltroEstrategico: {e}, using default score_base=0.5")

        sorted_combo = sorted(combo)
        score = 0.0
        bonus = 0.0
        weights = config['weights']
        bonuses = config['bonuses']

        # 🎯 1. Suma total
        total = sum(sorted_combo)
        if 100 <= total <= 150:
            score += weights['sum_total']

        # 🎯 2. Número de pares
        pares = sum(1 for n in sorted_combo if n % 2 == 0)
        if 1 <= pares <= 5:
            score += weights['even_count']

        # 🎯 3. Saltos totales
        diff_sum = sum(sorted_combo[i] - sorted_combo[i-1] for i in range(1, len(sorted_combo)))
        if 22 <= diff_sum <= 37:
            score += weights['consecutive_diff']

        # 🎯 4. Repetidos con último sorteo
        repetidos = len(set(sorted_combo) & set(ultimos))
        if repetidos <= 2:
            score += weights['repeats_last_draw']

        # 🎯 5. Decades
        # Fix: Use explicit integer conversion to avoid NumPy boolean subtract warning
        combo_array = np.array(sorted_combo, dtype=int)
        decades = np.minimum((combo_array - 1) // 10, 3)
        decade_counts = Counter(decades)
        if len(decade_counts) >= 3:
            score += weights['decade_distribution']
        if max(decade_counts.values()) <= 3:
            score += weights['decade_overload']

        # 🎯 6. Primos
        prime_count = sum(1 for n in sorted_combo if n in primes_set)
        if 1 <= prime_count <= 3:
            score += weights['prime_numbers'] * min(prime_count / 3, 1.0)

        # 🎯 7. Diversidad
        diversity_score = calculate_diversity(sorted_combo, valid_combinations)
        score += weights['diversity'] * diversity_score

        # ⚡ Bonificaciones
        if sum(1 for n in sorted_combo if 1 <= n <= 5) >= 2:
            bonus += bonuses['low_numbers']
        if sum(1 for n in sorted_combo if 36 <= n <= 40) >= 2:
            bonus += bonuses['high_numbers']
        if cluster_data is not None:
            cs = cd.get('cluster_score', 0)
            bonus += min(cs * bonuses['cluster_performance'], 0.5)
            freq = cluster_data.get('frequency', {})
            bonus += freq.get(tuple(sorted_combo), 0) * bonuses['cluster_frequency']
        else:
            logger.debug("⚠️ cluster_data is None, skipping cluster bonuses")
            
        # NEW: Core bonus calculation
        core_bonus = 0.0
        if core_set:
            core_bonus = bonus_core_hits(sorted_combo, core_set) * bonuses['core_hits']
            bonus += core_bonus
            
        # NEW: Rare number bonus calculation with statistical significance logging
        rare_bonus = 0.0
        if historial is not None:
            rare_bonus = bonus_rare_numbers(sorted_combo, historial) * bonuses['rare_numbers']
            bonus += rare_bonus
            if rare_bonus > 0:
                logger.info(f"🔥 Rare number bonus: {rare_bonus:.3f} for combo {sorted_combo}")
                
                # Log rare number statistical significance
                try:
                    ADVANCED_LOGGING_AVAILABLE
                except NameError:
                    ADVANCED_LOGGING_AVAILABLE = False
                
                if ADVANCED_LOGGING_AVAILABLE and metrics_collector:
                    # Calculate statistical significance of rare number detection
                    rare_count = int(rare_bonus / bonuses['rare_numbers'] / 0.08)  # Reverse calculation
                    significance_level = min(0.05, rare_bonus / 0.32)  # Scale with bonus magnitude
                    
                    # Effect size based on bonus magnitude
                    effect_size = rare_bonus / 0.32  # Normalize to max possible bonus
                    
                    metrics_collector.log_statistical_analysis(
                        analysis_type="rare_number_analysis",
                        test_name="rare_number_bonus_significance",
                        test_statistic=rare_bonus,
                        p_value=significance_level,
                        significance_level=0.05,
                        effect_size=effect_size,
                        confidence_interval=(rare_bonus * 0.8, rare_bonus * 1.2),
                        sample_size=len(sorted_combo),
                        rare_numbers_detected=rare_count,
                        combination=sorted_combo,
                        bonus_applied=rare_bonus,
                        detection_method="frequency_analysis"
                    )
                
        # NEW: Additional diversity boost for combinations with multiple rare numbers
        if rare_bonus > 0.16:  # At least 2 rare numbers
            diversity_extra = min(diversity_score * bonuses['diversity_boost'], 0.20)
            bonus += diversity_extra

        source_weight = config['source_weights'].get(source, config['source_weights']['default'])
        final_score = (score * source_weight) + bonus + (svi_score * 0.3)

        # NEW: Multiplicar por ARIMA_score para boost temporal
        final_score *= arima_score

        metrics = {
            'combination': sorted_combo,
            'score': final_score,
            'svi_score': svi_score,
            'source': source,
            'sum_total': total,
            'even_count': pares,
            'diff_sum': diff_sum,
            'repeats': repetidos,
            'decades': dict(decade_counts),
            'primes': prime_count,
            'diversity': diversity_score,
            'filter_reasons': razones,
            'core_bonus': core_bonus,  # NEW: Track core bonus in metrics
            'rare_bonus': rare_bonus,  # NEW: Track rare number bonus
            'arima_score': arima_score  # NEW: Track ARIMA in metrics
        }

        return {
            'combination': sorted_combo,
            'score': round(final_score, 3),
            'svi_score': svi_score,
            'source': source,
            'metrics': metrics,
            'normalized': 0.0
        }, 0

    # Use serializable function for parallel processing to avoid DataFrame hashing issues
    if sequential:
        results = []
        for idx, cd in enumerate(combinations):
            try:
                results.append(score_single(cd, idx))
            except Exception as e:
                logger.warning(f"⚠️ Error procesando combinación {idx}: {e}")
                results.append((None, 1))
    else:
        # Create serializable function with all necessary data
        parallel_score_func = create_score_function(
            historial_values, 
            historial_columns, 
            ultimos, 
            arima_score, 
            threshold, 
            config, 
            list(primes_set), 
            valid_combinations,
            list(core_set) if core_set else []
        )
        
        # Prepare data for parallel processing - each item contains (cd, idx)
        items = [(cd, idx) for idx, cd in enumerate(combinations)]
        
        try:
            results = safe_parallel_map(parallel_score_func, items, n_jobs=-1, backend="loky")
        except Exception as e:
            logger.warning(f"⚠️ Parallel processing failed: {e}, falling back to sequential")
            # Fallback to sequential processing
            results = []
            for idx, cd in enumerate(combinations):
                try:
                    results.append(score_single(cd, idx))
                except Exception as fallback_e:
                    logger.warning(f"⚠️ Error procesando combinación {idx}: {fallback_e}")
                    results.append((None, 1))
    
    # Handle results safely
    scored = []
    rejected_count = 0
    for res in results:
        if res is not None:
            if isinstance(res, tuple) and len(res) == 2:
                result_data, reject_flag = res
                if result_data is not None:
                    scored.append(result_data)
                rejected_count += reject_flag
            elif isinstance(res, dict):
                # Direct result without tuple wrapping
                scored.append(res)

    # Normalización y fallback
    if scored:
        max_score = max(item['score'] for item in scored)
        if max_score > 0:
            for item in scored:
                item['normalized'] = round(item['score'] / max_score, 3)
    else:
        logger.info("🚨 No valid combinations scored, returning fallback")
        fb = ultimos if ultimos and validate_combination(ultimos) else [1, 2, 3, 4, 5, 6]
        fb_total = sum(fb)
        fb_even = sum(1 for n in fb if n % 2 == 0)
        fb_diff = sum(fb[i] - fb[i-1] for i in range(1, len(fb)))
        # Fix: Ensure integer conversion to avoid NumPy boolean subtract warning
        fb_decades = dict(Counter(min((int(n) - 1) // 10, 3) for n in fb))
        fb_primes = sum(1 for n in fb if n in primes_set)
        return [{
            'combination': fb,
            'score': 0.5,
            'svi_score': 0.5,
            'source': 'fallback',
            'metrics': {
                'sum_total': fb_total,
                'even_count': fb_even,
                'diff_sum': fb_diff,
                'repeats': 0,
                'decades': fb_decades,
                'primes': fb_primes,
                'diversity': 1.0,
                'filter_reasons': [],
                'core_bonus': 0.0,
                'arima_score': 1.0  # NEW: Default in fallback
            },
            'normalized': 1.0
        }]

    # Guardar métricas en CSV with enhanced statistical logging
    log_dir = f"logs/{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
    os.makedirs(log_dir, exist_ok=True)
    
    # Save metrics with enhanced statistical data
    metrics_df = pd.DataFrame([item['metrics'] for item in scored])
    metrics_df.to_csv(f"{log_dir}/score_metrics.csv", index=False)
    
    # Log aggregate scoring statistics
    if ADVANCED_LOGGING_AVAILABLE and metrics_collector and scored:
        all_scores = [item['score'] for item in scored]
        all_core_bonuses = [item['metrics'].get('core_bonus', 0.0) for item in scored]
        all_rare_bonuses = [item['metrics'].get('rare_bonus', 0.0) for item in scored]
        
        # Statistical analysis of scoring distribution
        score_mean = np.mean(all_scores)
        score_std = np.std(all_scores)
        score_entropy = calculate_shannon_entropy([int(s * 100) for s in all_scores])  # Scale for entropy
        
        # Log aggregate scoring statistics
        metrics_collector.log_statistical_analysis(
            analysis_type="scoring_distribution",
            test_name="combination_scoring_analysis",
            test_statistic=score_mean,
            p_value=1.0 - (score_std / score_mean) if score_mean > 0 else 1.0,
            significance_level=0.05,
            effect_size=score_std / score_mean if score_mean > 0 else 0.0,
            confidence_interval=(score_mean - score_std, score_mean + score_std),
            sample_size=len(scored),
            score_distribution_entropy=score_entropy,
            mean_core_bonus=np.mean(all_core_bonuses),
            mean_rare_bonus=np.mean(all_rare_bonuses),
            scoring_perfil=perfil_svi,
            arima_multiplier=arima_score
        )

    summary = {
        'timestamp': pd.Timestamp.now(),
        'total_combinations': len(combinations),
        'scored_combinations': len(scored),
        'rejected_combinations': rejected_count,
        'average_score': np.mean([item['score'] for item in scored]) if scored else 0.0,
        'average_svi_score': np.mean([item['svi_score'] for item in scored]) if scored else 0.0,
        'max_score': max([item['score'] for item in scored]) if scored else 0.0,
        'min_score': min([item['score'] for item in scored]) if scored else 0.0,
        'sources': Counter(item['source'] for item in scored),
        'perfil_svi': perfil_svi,
        'threshold': threshold,
        'arima_score': arima_score  # NEW: Track ARIMA in summary
    }
    pd.DataFrame([summary]).to_csv(f"{log_dir}/score_summary.csv", index=False)
    logger.info(f"📊 Scoring metrics and summary saved to {log_dir}")
    logger.info(f"✅ Scored {len(scored)} combinations, rejected {rejected_count}")

    return scored