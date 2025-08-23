# clustering_engine.py – Motor de clustering histórico para OMEGA PRO AI

import pandas as pd
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
    # Convertir a cadenas para usar K-Modes (requiere datos categóricos)
    X = history.astype(str)

    # Modelo de clustering
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
