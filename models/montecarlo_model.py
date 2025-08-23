# Modelo Monte Carlo – OMEGA PRO AI
import random
import numpy as np

def generate_montecarlo_predictions(data, num_simulations=200, valid_fn=None):
    """
    Genera predicciones usando simulación Monte Carlo.
    
    Args:
        data (DataFrame): Historial de combinaciones anteriores.
        num_simulations (int): Número de combinaciones a generar.
        valid_fn (callable): Función de validación (opcional) que recibe una combinación
                             y retorna True si es válida según filtros de OMEGA.
                             
    Returns:
        List[dict]: Lista de combinaciones simuladas con metadatos.
    """
    combinations = set()
    all_numbers = list(range(1, 41))
    
    while len(combinations) < num_simulations:
        combo = tuple(sorted(random.sample(all_numbers, 6)))
        if combo in combinations:
            continue
        if valid_fn and not valid_fn(combo):
            continue
        combinations.add(combo)
    
    return [{"combination": list(c), "model": "montecarlo"} for c in combinations]
