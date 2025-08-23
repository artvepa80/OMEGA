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
    
    # Función interna para generar combinación desde centroide
    def generar_desde_centroide(centroide):
        combo = []
        valores_validos = []
        
        # Paso 1: Recoger y redondear valores válidos
        for x in centroide:
            try:
                val = float(x)
                if not np.isnan(val):
                    rounded = int(round(val))
                    if 1 <= rounded <= 40:
                        valores_validos.append(rounded)
            except (ValueError, TypeError):
                continue
        
        # Paso 2: Usar valores únicos y completar si es necesario
        combo = sorted(set(valores_validos))
        
        # Paso 3: Completar con números aleatorios si faltan
        while len(combo) < 6:
            faltantes = list(set(universo) - set(combo))
            if not faltantes:
                break
            combo.append(random.choice(faltantes))
        
        return sorted(combo[:6])  # Asegurar solo 6 números

    # Generar combinaciones desde centroides
    for centroide in centroids:
        combo = generar_desde_centroide(centroide)
        
        # Validar combinación
        if len(combo) == 6 and tuple(combo) not in historial:
            if aplicar_filtros(combo, historial):
                combinaciones.append(combo)
                logger(f"[CLUSTER] Combinación aceptada: {combo}")
    
    # Mecanismo de respaldo si no se generaron suficientes
    if len(combinaciones) < cantidad:
        faltantes = cantidad - len(combinaciones)
        logger(f"[CLUSTER] Generando {faltantes} combinaciones de respaldo...")
        
        # Generar combinaciones aleatorias válidas
        for _ in range(faltantes * 3):  # Intentar más de lo necesario
            if len(combinaciones) >= cantidad:
                break
                
            combo = sorted(random.sample(universo, 6))
            if tuple(combo) not in historial and aplicar_filtros(combo, historial):
                combinaciones.append(combo)
                logger(f"[CLUSTER-RESERVA] Combinación aceptada: {combo}")

    logger(f"✅ [CLUSTER] Total combinaciones generadas: {len(combinaciones)}")
    return combinaciones[:cantidad]  # Devolver máximo la cantidad solicitada