# ghost_rng_observer.py – Versión refinada para detección inteligente

import random
import numpy as np
from datetime import datetime
from hashlib import sha256

def simulate_ghost_rng(seed: int, total_draws=1000):
    rng = random.Random(seed)
    draws = []
    for _ in range(total_draws):
        combo = sorted(rng.sample(range(1, 41), 6))
        draws.append(combo)
    return draws

def count_partial_matches(combo1, combo2):
    return len(set(combo1) & set(combo2))  # Coincidencias parciales

def calculate_similarity_score(real_draws, simulated_draws, min_matches=3):
    """
    Evalúa coincidencias parciales entre combinaciones.
    """
    total = 0
    for real in real_draws:
        for sim in simulated_draws:
            if count_partial_matches(real, sim) >= min_matches:
                total += 1
                break  # Contamos solo una vez por combinación real
    return total / len(real_draws)

def generate_dynamic_seeds(base_time=None, num_seeds=500):
    if base_time is None:
        base_time = datetime.now()
    seeds = []
    for i in range(num_seeds):
        base_str = f"{base_time.isoformat()}_{i}"
        hash_digest = sha256(base_str.encode()).hexdigest()
        seed = int(hash_digest[:16], 16)
        seeds.append(seed)
    return seeds

def detect_rng_artifacts(real_history, threshold=0.005, num_seeds=500, min_matches=3):
    seeds = generate_dynamic_seeds(num_seeds=num_seeds)
    results = []

    for seed in seeds:
        simulated = simulate_ghost_rng(seed, total_draws=len(real_history))
        score = calculate_similarity_score(real_history, simulated, min_matches=min_matches)
        if score > threshold:
            results.append({
                "seed": seed,
                "similarity_score": score
            })

    return sorted(results, key=lambda x: x["similarity_score"], reverse=True)

# Uso aislado
if __name__ == "__main__":
    historial_real = [
        [5, 12, 18, 24, 30, 39],
        [2, 8, 11, 16, 25, 37],
        [1, 6, 14, 22, 33, 40],
        [3, 9, 15, 21, 28, 35],
    ]
    artefactos = detect_rng_artifacts(historial_real)
    for r in artefactos:
        print(f"🔍 Seed sospechosa: {r['seed']} – Similaridad: {r['similarity_score']:.4f}")