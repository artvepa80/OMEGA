# clustering_engine.py – Versión avanzada con núcleo + exploración histórica

import pandas as pd
import numpy as np
import random
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from modules.filters.rules_filter import FiltroEstrategico

# Instancia global del filtro
filtro = FiltroEstrategico()

def generar_combinaciones_clustering(historial_df, cantidad=30, logger=print):
    df = historial_df.copy()
    df_numeric = df.select_dtypes(include='number').dropna()
    columnas_bolillas = [col for col in df_numeric.columns if "Bolilla" in col or col in ["1", "2", "3", "4", "5", "6"]]
    
    if not columnas_bolillas or len(columnas_bolillas) < 6:
        logger("⚠️ No se encontraron columnas válidas. Usando backup completo")
        return generar_backup(cantidad, df_numeric, logger)

    filtro.cargar_historial(df_numeric[columnas_bolillas].values.tolist())

    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(df_numeric[columnas_bolillas])
    
    try:
        mejor_k = seleccionar_mejor_k(data_scaled)
    except:
        mejor_k = 5
        logger("⚠️ Falló selección óptima de K. Usando K=5")
    
    kmeans = KMeans(n_clusters=mejor_k, n_init=10, random_state=42)
    etiquetas = kmeans.fit_predict(data_scaled)
    centroids = scaler.inverse_transform(kmeans.cluster_centers_)

    historial = set(tuple(sorted(row.astype(int))) for _, row in df_numeric[columnas_bolillas].iterrows())
    universo = list(range(1, 41))

    cluster_scores = evaluar_score_clusters(df_numeric, etiquetas, columnas_bolillas)
    cluster_order = sorted(cluster_scores.items(), key=lambda x: x[1], reverse=True)

    combinaciones = []

    for cluster_id, _ in cluster_order:
        centroide = centroids[cluster_id]
        combo = generar_desde_centroide(centroide, universo)
        if es_combinacion_valida(combo, historial):
            cluster_score = cluster_scores.get(cluster_id, 0)
            combinaciones.append({
                "combination": combo,
                "source": "clustering",
                "cluster_score": cluster_score
            })
            logger(f"[CLUSTER-HIST] Dominante {cluster_id} → {combo}")
        if len(combinaciones) >= cantidad:
            break

    if len(combinaciones) < cantidad:
        logger("🔁 Refuerzo desde muestras de clústeres dominantes...")
        for cluster_id, _ in cluster_order:
            indices = np.where(etiquetas == cluster_id)[0]
            random.shuffle(indices)
            for idx in indices:
                combo_base = df_numeric.iloc[idx][columnas_bolillas].values.astype(int).tolist()
                combo = mutar_combinacion(combo_base, universo)
                if es_combinacion_valida(combo, historial):
                    cluster_score = cluster_scores.get(cluster_id, 0)
                    combinaciones.append({
                        "combination": combo,
                        "source": "clustering",
                        "cluster_score": cluster_score
                    })
                    logger(f"[CLUSTER-MUT] {cluster_id} → {combo}")
                if len(combinaciones) >= cantidad:
                    break
            if len(combinaciones) >= cantidad:
                break

    return completar_con_backup(combinaciones, cantidad, historial, universo, logger)

# --- FUNCIONES AUXILIARES ---

def generar_desde_centroide(centroide, universo):
    valores_validos = [int(round(x)) for x in centroide if 1 <= int(round(x)) <= 40]
    combo = sorted(set(valores_validos))
    while len(combo) < 6:
        faltantes = list(set(universo) - set(combo))
        if not faltantes: break
        combo.append(random.choice(faltantes))
    return sorted(combo[:6])

def mutar_combinacion(combo_base, universo):
    combo = combo_base[:4]
    cambios = random.sample(range(4), 2)
    for idx in cambios:
        disponibles = list(set(universo) - set(combo))
        if disponibles:
            combo[idx] = random.choice(disponibles)
    while len(combo) < 6:
        nuevos = list(set(universo) - set(combo))
        if nuevos:
            combo.append(random.choice(nuevos))
    return sorted(combo)

def es_combinacion_valida(combo, historial):
    return (
        len(combo) == 6 and
        tuple(combo) not in historial and
        filtro.aplicar_filtros(combo)
    )

def evaluar_score_clusters(df, etiquetas, columnas):
    scores = {}
    for cluster_id in np.unique(etiquetas):
        indices = np.where(etiquetas == cluster_id)[0]
        count_3_plus = 0
        for idx in indices:
            row = df.iloc[idx][columnas].dropna().astype(int).tolist()
            aciertos = len(set(row) & set(df.iloc[idx][columnas].dropna().astype(int)))
            if aciertos >= 3:
                count_3_plus += 1
        scores[cluster_id] = count_3_plus
    return scores

def seleccionar_mejor_k(data_scaled, rango=range(3, 9)):
    mejor_score = -1
    mejor_k = 5
    for k in rango:
        modelo = KMeans(n_clusters=k, n_init=5, random_state=42)
        etiquetas = modelo.fit_predict(data_scaled)
        score = silhouette_score(data_scaled, etiquetas)
        if score > mejor_score:
            mejor_score = score
            mejor_k = k
    return mejor_k

def generar_backup(cantidad, df_numeric, logger):
    columnas_bolillas = [col for col in df_numeric.columns if "Bolilla" in col or col in ["1", "2", "3", "4", "5", "6"]]
    historial = set(tuple(sorted(row.astype(int))) for _, row in df_numeric[columnas_bolillas].iterrows())
    universo = list(range(1, 41))
    combinaciones = []
    while len(combinaciones) < cantidad:
        combo = sorted(random.sample(universo, 6))
        if es_combinacion_valida(combo, historial):
            combinaciones.append(combo)
            logger(f"[CLUSTER-BACKUP] {combo}")
    return combinaciones

def completar_con_backup(combinaciones, cantidad, historial, universo, logger):
    intentos = 0
    while len(combinaciones) < cantidad and intentos < cantidad * 3:
        combo = sorted(random.sample(universo, 6))
        if es_combinacion_valida(combo, historial):
            combinaciones.append(combo)
            logger(f"[CLUSTER-RESERVA] {combo}")
        intentos += 1
    logger(f"✅ [CLUSTER] Total combinaciones generadas: {len(combinaciones)}")
    return combinaciones[:cantidad]