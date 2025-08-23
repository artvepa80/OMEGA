# montecarlo_model.py – actualizado y compatible con logging

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

    return [list(c) for c in predictions]

# ✅ Interfaz compatible con el predictor + logging
def generar_combinaciones_montecarlo(historial, cantidad=60, logger=print):
    resultados = generate_montecarlo_predictions(historial, n_simulations=100, n_predictions=cantidad)

    combinaciones = []
    for combinacion in resultados:
        logger(f"[MONTECARLO] Combinación generada: {combinacion}")
        combinaciones.append({
            "combination": combinacion,
            "score": 0.8,
            "source": "montecarlo"
        })

    logger(f"✅ [MONTECARLO] Total combinaciones generadas: {len(combinaciones)}")
    return combinaciones