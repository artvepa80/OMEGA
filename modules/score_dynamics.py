# OMEGA_PRO_AI_v10.1/modules/score_dynamics.py

import pandas as pd
import numpy as np
from collections import Counter
from typing import List, Dict, Any, Optional, Union, Sequence, Set
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
        'core_hits': 1.0  # NEW: Weight for core bonus
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
    historial_columns = [f'Bolilla {i}' for i in range(1, 7)]

    # Aceptar DataFrame, ndarray (shape n×6) o lista; validar dimensiones e filtrar listas incompletas
    if isinstance(historial, pd.DataFrame):
        df_hist = historial.copy()
    elif isinstance(historial, np.ndarray):
        if historial.ndim == 2 and historial.shape[1] == 6:
            df_hist = pd.DataFrame(historial, columns=historial_columns)
        else:
            logger.error(f"🚨 Historial ndarray inválido con forma {historial.shape}, debe ser (n,6)")
            raise ValueError(f"Historial ndarray inválido: forma esperada (n,6), obtenida {historial.shape}")
    elif isinstance(historial, list):
        complete_rows = [row for row in historial if isinstance(row, (list, tuple)) and len(row) == 6]
        removed = len(historial) - len(complete_rows)
        if removed > 0:
            logger.warning(f"⚠️ Se eliminaron {removed} filas incompletas del historial")
        df_hist = pd.DataFrame(complete_rows, columns=historial_columns) if complete_rows else pd.DataFrame(columns=historial_columns)
    else:
        logger.warning(f"🚨 Tipo de historial no soportado ({type(historial)}), creando DataFrame vacío")
        df_hist = pd.DataFrame(columns=historial_columns)

    # A partir de aquí, `historial` siempre es un DataFrame normalizado
    historial = df_hist

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

    # NEW: Calcular serie temporal para ARIMA (sumas de bolillas)
    if not historial.empty:
        historial_sums = historial.sum(axis=1).tolist()
        try:
            arima_score = arima_cycles(historial_sums)  # NEW: Obtener ARIMA_score
            logger.info(f"🔮 ARIMA_score calculado: {arima_score:.3f}")
        except Exception as e:
            arima_score = 1.0  # Default neutral si error
            logger.warning(f"⚠️ Error en ARIMA_cycles: {e}, usando 1.0 como default")
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
                
                # Fix numpy boolean operations - usar boolean masking para evitar errores de indexing
                if hist_data.size > 0:
                    # Crear máscara booleana para filas válidas (sin NaN)
                    valid_mask = ~np.isnan(hist_data).any(axis=1)
                    hist_data = hist_data[valid_mask] if valid_mask.any() else np.array([]).reshape(0, hist_data.shape[1])
                else:
                    hist_data = np.array([])
                    
                historical_scores = [calc_score(row) for row in hist_data] if len(hist_data) > 0 else []
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

    # Parallelizable path using safe_parallel_map, passing only pure data
    def _wrapper(item):
        i, cd = item
        return score_single(cd, i)

    if sequential:
        results = []
        for idx, cd in enumerate(combinations):
            try:
                results.append(score_single(cd, idx))
            except Exception as e:
                logger.warning(f"⚠️ Error procesando combinación {idx}: {e}")
                results.append((None, 1))
    else:
        items = list(enumerate(combinations))
        results = safe_parallel_map(_wrapper, items, n_jobs=-1, backend="loky")
    
    scored = [res[0] for res in results if res[0] is not None]
    rejected_count = sum(res[1] for res in results)

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

    # Guardar métricas en CSV
    log_dir = f"logs/{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
    os.makedirs(log_dir, exist_ok=True)
    pd.DataFrame([item['metrics'] for item in scored]).to_csv(f"{log_dir}/score_metrics.csv", index=False)

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