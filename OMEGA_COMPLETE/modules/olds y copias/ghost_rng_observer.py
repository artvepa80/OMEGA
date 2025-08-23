# ghost_rng_observer.py – OMEGA PRO AI v10.7

import random
import numpy as np
from functools import lru_cache
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple, Dict, Any
from numpy.fft import fft
import pandas as pd


@lru_cache(maxsize=128)
def simulate_ghost_rng(seed: int, total_draws: int = 100) -> List[Tuple[int, ...]]:
    random.seed(seed)
    draws = []
    for _ in range(total_draws):
        draw = tuple(sorted(random.sample(range(1, 41), 6)))
        draws.append(draw)
    return draws


def calculate_similarity(observed: List[List[int]], simulated: List[Tuple[int, ...]]) -> float:
    observed_set = set(tuple(sorted(o)) for o in observed)
    simulated_set = set(simulated)
    matches = observed_set.intersection(simulated_set)
    return len(matches) / len(simulated_set)


def build_frequency_map(draws: List[Tuple[int, ...]]) -> Dict[int, int]:
    freq_map = {i: 0 for i in range(1, 41)}
    for draw in draws:
        for num in draw:
            freq_map[num] += 1
    return freq_map


def fft_entropy_spectrum(draws: List[Tuple[int, ...]]) -> float:
    freq_map = build_frequency_map(draws)
    freq_vector = np.array(list(freq_map.values()))
    freq_vector = freq_vector / np.sum(freq_vector)
    entropy = -np.sum(freq_vector * np.log2(freq_vector + 1e-12))
    return entropy


def process_seed(seed: int, historial_real: List[List[int]]) -> Dict[str, Any]:
    try:
        simulated = simulate_ghost_rng(seed)
        similarity_score = calculate_similarity(historial_real, simulated)
        fft_score, _ = detect_fft_artifacts(simulated)
        entropy_score = fft_entropy_spectrum(simulated)

        composite_score = (
            0.4 * similarity_score +
            0.3 * (1.0 / (1.0 + abs(fft_score))) +
            0.3 * (1.0 / (1.0 + abs(entropy_score)))
        )

        return {
            "seed": seed,
            "similarity_score": similarity_score,
            "fft_score": fft_score,
            "entropy_score": entropy_score,
            "composite_score": composite_score,
        }

    except Exception as e:
        return {"seed": seed, "error": str(e)}


def detect_rng_artifacts(historial_real: List[List[int]], threshold=0.01, num_seeds=1000) -> List[Dict[str, Any]]:
    seeds_to_test = [random.getrandbits(64) for _ in range(num_seeds)]
    results = []

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_seed, seed, historial_real) for seed in seeds_to_test]
        for f in futures:
            try:
                res = f.result()
                if "error" not in res and res["composite_score"] > threshold:
                    results.append(res)
                elif "error" in res:
                    print(f"⚠️ Seed {res['seed']} falló: {res['error']}")
            except Exception as e:
                print(f"⚠️ Error en la ejecución paralela: {e}")
    return sorted(results, key=lambda x: x["composite_score"], reverse=True)


# 🧠 Detección básica de artefactos FFT
def detect_fft_artifacts(draws: List[Tuple[int, ...]]) -> Tuple[float, Any]:
    """
    Aplica FFT a la frecuencia de aparición de números para detectar patrones periódicos.
    Retorna una métrica basada en el pico de la transformada y la transformada completa.
    """
    flat_numbers = [num for draw in draws for num in draw]
    freq = np.bincount(flat_numbers, minlength=41)[1:]  # índices 1-40

    fft_values = np.abs(fft(freq))
    max_peak = np.max(fft_values[1:])  # ignorar el componente de frecuencia cero

    return max_peak, fft_values


# ✅ Función get_seeds dinámica – integrada con detect_rng_artifacts
def get_seeds(historial_csv_path: str = "data/historial_kabala_github.csv", 
              threshold: float = 0.006, 
              num_seeds: int = 500,
              max_seeds: int = 5,
              max_draws_per_seed: int = 40) -> List[Dict[str, Any]]:
    """
    Genera y devuelve una lista de combinaciones sospechosas a partir del historial real,
    usando el detector de artefactos de RNG. 
    
    Parámetros:
    historial_csv_path: Ruta al archivo CSV con datos históricos
    threshold: Umbral de puntuación compuesta para filtrar semillas sospechosas
    num_seeds: Número de semillas aleatorias a probar
    max_seeds: Máximo de semillas sospechosas a considerar
    max_draws_per_seed: Máximo de combinaciones por semilla a incluir
    
    Retorna lista de diccionarios con estructura:
        [{"seed": str, "draw": List[int]}, ...]
    """
    try:
        # Leer datos históricos desde CSV
        df = pd.read_csv(historial_csv_path)
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        
        if not numeric_cols:
            raise ValueError("No se encontraron columnas numéricas en el CSV")
            
        historial = df[numeric_cols].dropna().astype(int).values.tolist()
        
        # Detectar semillas sospechosas
        seed_infos = detect_rng_artifacts(historial, threshold, num_seeds)
        
        # Procesar las semillas más sospechosas (mayor composite_score)
        seed_infos_sorted = sorted(seed_infos, key=lambda x: x['composite_score'], reverse=True)
        top_seeds = seed_infos_sorted[:max_seeds]
        
        # Generar resultados con combinaciones de las semillas sospechosas
        results = []
        for seed_info in top_seeds:
            seed = seed_info['seed']
            draws = simulate_ghost_rng(seed)
            
            for i, draw_tuple in enumerate(draws):
                if i >= max_draws_per_seed:
                    break
                results.append({
                    "seed": f"ghost_{seed}",
                    "draw": list(draw_tuple)
                })
        
        return results
        
    except Exception as e:
        print(f"❌ [ghost_rng_observer] Error en get_seeds: {str(e)}")
        return []