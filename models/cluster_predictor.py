# cluster_predictor.py – Generador de combinaciones desde centroides para OMEGA PRO AI

import random

def generate_combinations_from_centroids(centroids, total_combinations=10):
    """
    Genera combinaciones basadas en los centroides de clúster.

    Args:
        centroids (list): Lista de centroides (cada uno es una lista de strings).
        total_combinations (int): Número total de combinaciones a generar.

    Returns:
        results (list): Lista de combinaciones dictadas por centroides.
    """
    results = []
    all_numbers = list(range(1, 41))

    while len(results) < total_combinations:
        # Elegir un centroide aleatorio
        centroid = random.choice(centroids)
        centroid_nums = sorted([int(n) for n in centroid])

        # Pequeña variación aleatoria (1 o 2 números)
        variation = random.sample(all_numbers, 2)
        combo = sorted(list(set(centroid_nums + variation))[:6])  # Asegura solo 6 números

        if combo not in results:
            results.append(combo)

    return [{"combination": c, "model": "clustering"} for c in results]
