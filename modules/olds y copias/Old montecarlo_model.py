# Modelo Monte Carlo – OMEGA PRO AI
import random
import numpy as np

def generate_montecarlo_predictions(data, n_simulations=50, n_predictions=5, seed=42):
    """
    Simulación tipo Monte Carlo para generar combinaciones válidas.
    """
    random.seed(seed)
    predictions = set()

    while len(predictions) < n_predictions:
        combo = sorted(random.sample(range(1, 41), 6))
        combo_tuple = tuple(combo)

        if combo_tuple not in predictions:
            predictions.add(combo_tuple)

    print(f"✅ [MONTECARLO] Combinaciones generadas: {list(predictions)}")
    return [list(c) for c in predictions]
