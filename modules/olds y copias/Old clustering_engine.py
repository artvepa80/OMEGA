# clustering_engine.py – Generador de combinaciones por clustering con filtros para OMEGA PRO AI

import pandas as pd
import random
import numpy as np
from modules.clustering_model import apply_clustering
from modules.filters.rules_filter import aplicar_filtros

def generar_combinaciones_clustering(data_path="data/historial_kabala_github.csv", cantidad=30, logger=print):
    # Cargar historial numérico
    df = pd.read_csv(data_path)
    df_numeric = df.select_dtypes(include='number').dropna()

    # Aplicar clustering
    labels, centroids = apply_clustering(df_numeric)

    # Construir historial como set de tuplas
    historial = set(tuple(sorted(row.dropna().astype(int))) for _, row in df_numeric.iterrows())
    combinaciones = []
    universo = list(range(1, 41))

    for centroide in centroids:
        # ✅ Conversión segura: float, filtrado, redondeo, eliminación de duplicados
        combo = []
        for x in centroide:
            try:
                val = float(x)
                rounded = int(round(val))
                if 1 <= rounded <= 40:
                    combo.append(rounded)
            except (ValueError, TypeError):
                continue  # Ignora si no puede convertirse

        combo = sorted(set(combo))  # Eliminar duplicados

        while len(combo) < 6:
            faltantes = list(set(universo) - set(combo))
            if not faltantes:
                break
            combo.append(random.choice(faltantes))

        combo = sorted(combo)

        if len(combo) == 6 and tuple(combo) not in historial:
            if aplicar_filtros(combo, historial):
                combinaciones.append(combo)
                logger(f"[CLUSTER] Combinación aceptada: {combo}")

        if len(combinaciones) >= cantidad:
            break

    logger(f"✅ [CLUSTER] Total combinaciones generadas: {len(combinaciones)}")
    return combinaciones