# clustering_engine.py – Motor de clustering histórico para OMEGA PRO AI

import pandas as pd
import random
from kmodes.kmodes import KModes

def apply_clustering(history, n_clusters=5, random_state=42):
    """
    Aplica clustering K-Modes sobre el historial de combinaciones.

    Args:
        history (pd.DataFrame): Combinaciones históricas (cada fila una jugada).
        n_clusters (int): Número de clústeres a generar.
        random_state (int): Semilla para resultados reproducibles.

    Returns:
        labels (list): Clúster asignado a cada combinación del historial.
        centroids (list): Combinación representativa (centroide) de cada clúster.
    """
    X = history.astype(str)

    km = KModes(
        n_clusters=n_clusters,
        init='Huang',
        n_init=5,
        verbose=0,
        random_state=random_state
    )
    
    labels = km.fit_predict(X)
    centroids = km.cluster_centroids_

    return labels, centroids

def generate_clustering_predictions(data, n_clusters=5):
    """
    Interfaz para OMEGA PRO AI.
    Usa los centroides generados por K-Modes como predicciones válidas.
    """
    labels, centroids = apply_clustering(data, n_clusters=n_clusters)
    predictions = []

    for centroide in centroids:
        # Convertir a enteros válidos y filtrar duplicados
        combo = [int(x) for x in centroide if x.isdigit()]
        combo = sorted(set([x for x in combo if 1 <= x <= 40]))

        # Completar con números aleatorios si hay menos de 6
        if len(combo) < 6:
            faltantes = list(set(range(1, 41)) - set(combo))
            combo += random.sample(faltantes, 6 - len(combo))

        if len(combo) == 6:
            predictions.append(combo)
        else:
            print(f"⚠️ [CLUSTER] Centroide descartado por formato inválido: {combo}")

    print(f"✅ [CLUSTER] Combinaciones generadas: {predictions}")
    return predictions