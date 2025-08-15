# clustering_engine.py - Versión optimizada para OMEGA_PRO_AI_v10.1
import pandas as pd
import numpy as np
import random
import logging
import os
import ast
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from modules.filters.rules_filter import FiltroEstrategico

# Configuración de logging
module_logger = logging.getLogger('clustering_engine')
if not module_logger.handlers:
    module_logger.setLevel(logging.INFO)
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.FileHandler('logs/clustering_engine.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    module_logger.addHandler(file_handler)
    module_logger.addHandler(console_handler)

# Instancia global del filtro
filtro = FiltroEstrategico()

def cargar_datos_jackpots(jackpot_path="data/jackpots_omega.csv", logger=None):
    """Carga y procesa los datos de jackpots históricos"""
    logger = logger or module_logger
    try:
        if not os.path.exists(jackpot_path):
            logger.warning(f"⚠️ Jackpot file {jackpot_path} not found, returning empty set")
            return set()
        jackpots_df = pd.read_csv(jackpot_path)
        jackpots_df['numeros'] = jackpots_df['numeros'].apply(ast.literal_eval)
        jackpot_combinations = set(tuple(sorted(comb)) for comb in jackpots_df['numeros'])
        logger.info(f"✅ Cargados {len(jackpot_combinations)} jackpots históricos")
        return jackpot_combinations
    except Exception as e:
        logger.error(f"❌ Error cargando datos de jackpots: {str(e)}")
        return set()

def generar_combinaciones_clustering(historial_df, cantidad=30, logger=None, jackpot_path="data/jackpots_omega.csv"):
    """Genera combinaciones usando clustering"""
    logger = logger or module_logger
    try:
        df = historial_df.copy()
        df_numeric = df.select_dtypes(include='number').dropna()
        # Improved column detection - check for multiple patterns
        columnas_bolillas = []
        for col in df_numeric.columns:
            col_str = str(col).lower()
            if ("bolilla" in col_str or 
                col_str in ["1", "2", "3", "4", "5", "6"] or
                col_str.startswith("bolilla_") or
                any(f"bolilla{i}" == col_str or f"bolilla {i}" == col_str for i in range(1, 7))):
                columnas_bolillas.append(col)
        
        # Debug: log what columns were found
        logger.info(f"🔍 Columnas disponibles: {list(df_numeric.columns)}")
        logger.info(f"🎯 Columnas bolillas detectadas: {columnas_bolillas}")
        
        if not columnas_bolillas or len(columnas_bolillas) < 6:
            # If we don't have enough bolilla columns, try using the first 6 numeric columns
            if len(df_numeric.columns) >= 6:
                columnas_bolillas = df_numeric.columns[:6].tolist()
                logger.warning(f"⚠️ Usando primeras 6 columnas numéricas: {columnas_bolillas}")
            else:
                logger.warning("⚠️ No se encontraron columnas válidas. Usando backup")
                return generar_backup(cantidad, df_numeric, logger)

        filtro.cargar_historial(df_numeric[columnas_bolillas].values.tolist())
        jackpot_combinations = cargar_datos_jackpots(jackpot_path, logger)

        df_numeric['combo_tuple'] = df_numeric[columnas_bolillas].apply(
            lambda row: tuple(sorted(row.astype(int))), axis=1
        )
        df_numeric['JACKPOT'] = df_numeric['combo_tuple'].apply(
            lambda x: 1 if x in jackpot_combinations else 0
        )
        df_numeric = df_numeric.drop(columns=['combo_tuple'])

        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(df_numeric[columnas_bolillas])
        
        try:
            mejor_k = seleccionar_mejor_k(data_scaled)
            logger.info(f"✅ Seleccionado K óptimo: {mejor_k}")
        except Exception as e:
            mejor_k = 5
            logger.warning(f"⚠️ Falló selección óptima de K: {str(e)}. Usando K=5")
        
        kmeans = KMeans(n_clusters=mejor_k, n_init=10, random_state=42)
        etiquetas = kmeans.fit_predict(data_scaled)
        centroids = scaler.inverse_transform(kmeans.cluster_centers_)

        historial = set(tuple(sorted(row.astype(int))) for _, row in df_numeric[columnas_bolillas].iterrows())
        universo = list(range(1, 41))

        cluster_scores = evaluar_score_clusters(df_numeric, etiquetas, columnas_bolillas)
        jackpot_scores = analizar_coocurrencia(df_numeric, etiquetas, columnas_bolillas, logger)
        pos_entropy = calcular_entropia_posicional(df_numeric, columnas_bolillas, etiquetas)

        for cluster_id in cluster_scores:
            jackpot_data = jackpot_scores.get(cluster_id, {'composite_score': 0})
            cluster_score = cluster_scores[cluster_id]
            if jackpot_data['composite_score'] > 0:
                cluster_scores[cluster_id] = (cluster_score * 0.4) + (jackpot_data['composite_score'] * 0.6)
            else:
                cluster_scores[cluster_id] = cluster_score * 0.9

        cluster_order = sorted(cluster_scores.items(), key=lambda x: x[1], reverse=True)
        combinaciones = []

        for cluster_id, score_val in cluster_order:
            centroide = centroids[cluster_id]
            entropias = pos_entropy.get(cluster_id, [0.5] * 6)
            combo = generar_desde_centroide(centroide, universo, entropias)
            if es_combinacion_valida(combo, historial):
                combinaciones.append({
                    "combination": sorted([int(round(x)) for x in combo]),
                    "source": "clustering",
                    "score": score_val / 100
                })
                logger.info(f"[CLUSTER-HIST] Cluster {cluster_id} → {combo} | Score: {score_val:.2f}")
            if len(combinaciones) >= cantidad:
                break

        if len(combinaciones) < cantidad:
            logger.info(f"🔁 Refuerzo desde muestras de clústeres dominantes ({len(combinaciones)}/{cantidad})...")
            for cluster_id, score_val in cluster_order:
                indices = np.where(etiquetas == cluster_id)[0]
                random.shuffle(indices)
                for idx in indices[:min(5, len(indices))]:
                    combo_base = df_numeric.iloc[idx][columnas_bolillas].values.astype(int).tolist()
                    combo = mutar_combinacion(combo_base, universo)
                    if es_combinacion_valida(combo, historial):
                        combinaciones.append({
                            "combination": sorted([int(round(x)) for x in combo]),
                            "source": "clustering",
                            "score": score_val / 120
                        })
                        logger.info(f"[CLUSTER-MUT] Muestra {idx} → {combo} | Score: {score_val/120:.4f}")
                    if len(combinaciones) >= cantidad:
                        break
                if len(combinaciones) >= cantidad:
                    break

        if len(combinaciones) < cantidad:
            logger.info(f"🔄 Completando con backup ({len(combinaciones)}/{cantidad})...")
            combinaciones = completar_con_backup(combinaciones, cantidad, historial, universo, logger)

        logger.info(f"✅ [CLUSTER] Total combinaciones generadas: {len(combinaciones)}")
        return combinaciones[:cantidad]

    except Exception as e:
        logger.error(f"🚨 Error en generar_combinaciones_clustering: {str(e)}")
        return [{"combination": [1, 2, 3, 4, 5, 6], "source": "clustering", "score": 0.3}]

def analizar_coocurrencia(df, etiquetas, columnas, logger):
    """Analiza patrones de co-ocurrencia en clusters con jackpots históricos"""
    logger = logger or module_logger
    if 'JACKPOT' not in df.columns:
        logger.error("❌ No se encontró columna JACKPOT para análisis de co-ocurrencia")
        return {}
    
    cluster_jackpot_scores = {}
    for cluster_id in np.unique(etiquetas):
        indices = np.where(etiquetas == cluster_id)[0]
        cluster_data = df.iloc[indices]
        total_rows = len(cluster_data)
        
        if total_rows == 0:
            cluster_jackpot_scores[cluster_id] = {'composite_score': 0}
            continue
        
        jackpot_count = cluster_data['JACKPOT'].sum()
        jackpot_rate = jackpot_count / total_rows if total_rows > 0 else 0
        diversity_score = 0
        pair_strength = 0
        winning_combos = cluster_data[cluster_data['JACKPOT'] == 1][columnas]
        co_occurrence_score = 0
        
        if len(winning_combos) > 0:
            pair_counts = {}
            for _, row in winning_combos.iterrows():
                nums = sorted(row.astype(int))
                for i in range(len(nums)):
                    for j in range(i+1, len(nums)):
                        pair = (nums[i], nums[j])
                        pair_counts[pair] = pair_counts.get(pair, 0) + 1
            
            if pair_counts:
                max_count = max(pair_counts.values())
                pair_strength = max_count / len(winning_combos)
                strong_pairs = sum(1 for count in pair_counts.values() if count > 1)
                diversity_score = strong_pairs / len(pair_counts) if pair_counts else 0
                co_occurrence_score = pair_strength * (1 + diversity_score)
        
        composite = (jackpot_rate * 0.7) + (co_occurrence_score * 0.3)
        cluster_jackpot_scores[cluster_id] = {
            'jackpot_rate': jackpot_rate,
            'pair_strength': pair_strength,
            'diversity_score': diversity_score,
            'co_occurrence_score': co_occurrence_score,
            'composite_score': composite
        }
        logger.info(f"📊 Cluster {cluster_id}: Jackpot Rate: {jackpot_rate:.3f}, Pair Strength: {pair_strength:.3f}, Diversity: {diversity_score:.3f}, Score: {composite:.3f}")
    
    return cluster_jackpot_scores

def calcular_entropia_posicional(df, columnas, etiquetas):
    """Calcula la entropía posicional para cada posición en los clusters"""
    pos_entropy = {}
    all_numbers = list(range(1, 41))
    
    for cluster_id in np.unique(etiquetas):
        cluster_data = df[etiquetas == cluster_id][columnas]
        position_entropy = []
        
        if len(cluster_data) == 0:
            pos_entropy[cluster_id] = [1.0] * 6
            continue
        
        for pos in range(6):
            counts = cluster_data.iloc[:, pos].value_counts().reindex(all_numbers, fill_value=0)
            frecuencias = counts / counts.sum()
            entropy_val = -np.sum(frecuencias * np.log2(frecuencias + 1e-10))
            max_entropy = np.log2(len(all_numbers))
            normalized_entropy = entropy_val / max_entropy
            position_entropy.append(normalized_entropy)
        
        pos_entropy[cluster_id] = position_entropy
    
    return pos_entropy

def generar_desde_centroide(centroide, universo, entropias=None):
    """Genera combinación considerando entropía posicional"""
    if entropias is None:
        entropias = [0.5] * 6
    combo = []
    for i, value in enumerate(centroide):
        target = int(round(value))
        if entropias[i] < 0.3:
            candidates = []
            for diff in range(0, 6):
                candidates.extend([target + diff, target - diff])
            valid_candidates = [c for c in candidates if 1 <= c <= 40 and c not in combo]
            if valid_candidates:
                chosen = min(valid_candidates, key=lambda x: abs(x - value))
                combo.append(chosen)
            else:
                available = [x for x in universo if x not in combo]
                combo.append(random.choice(available))
        else:
            available = [x for x in universo if x not in combo]
            weights = [1 / (abs(x - value) + 0.1) for x in available]
            total_weight = sum(weights)
            if total_weight > 0:
                normalized_weights = [w / total_weight for w in weights]
                chosen = random.choices(available, weights=normalized_weights, k=1)[0]
                combo.append(chosen)
            else:
                combo.append(random.choice(available))
    return sorted(combo)

def generar_simple(centroide, universo):
    """Genera combinación simple desde centroide"""
    valores_validos = [int(round(x)) for x in centroide if 1 <= int(round(x)) <= 40]
    combo = sorted(set(valores_validos))
    while len(combo) < 6:
        faltantes = list(set(universo) - set(combo))
        if not faltantes:
            break
        combo.append(random.choice(faltantes))
    return sorted(combo)

def mutar_combinacion(combo_base, universo):
    """Muta una combinación base"""
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
    """Valida una combinación"""
    return (
        len(combo) == 6 and
        len(set(combo)) == 6 and
        all(1 <= num <= 40 for num in combo) and
        tuple(combo) not in historial and
        filtro.aplicar_filtros(combo)
    )

def evaluar_score_clusters(df, etiquetas, columnas):
    """Evalúa scores de clusters"""
    scores = {}
    for cluster_id in np.unique(etiquetas):
        indices = np.where(etiquetas == cluster_id)[0]
        count = len(indices)
        count_3_plus = 0
        if count == 0:
            scores[cluster_id] = 0
            continue
        for idx in indices:
            row = df.iloc[idx][columnas].dropna().astype(int).tolist()
            if len(set(row)) >= 3:
                count_3_plus += 1
        scores[cluster_id] = (count_3_plus / count) * count if count > 0 else 0
    return scores

def seleccionar_mejor_k(data_scaled, rango=range(3, 9)):
    """Selecciona el mejor número de clusters"""
    mejor_score = -1
    mejor_k = 5
    for k in rango:
        modelo = KMeans(n_clusters=k, n_init=10, random_state=42)
        etiquetas = modelo.fit_predict(data_scaled)
        if len(np.unique(etiquetas)) < 2:
            continue
        try:
            score = silhouette_score(data_scaled, etiquetas)
            if score > mejor_score:
                mejor_score = score
                mejor_k = k
        except:
            continue
    return mejor_k

def generar_backup(cantidad, df_numeric, logger):
    """Genera combinaciones de respaldo"""
    # Improved column detection for backup
    columnas_bolillas = []
    for col in df_numeric.columns:
        col_str = str(col).lower()
        if ("bolilla" in col_str or 
            col_str in ["1", "2", "3", "4", "5", "6"] or
            col_str.startswith("bolilla_") or
            any(f"bolilla{i}" == col_str or f"bolilla {i}" == col_str for i in range(1, 7))):
            columnas_bolillas.append(col)
    historial = set(tuple(sorted(row.astype(int))) for _, row in df_numeric[columnas_bolillas].iterrows())
    universo = list(range(1, 41))
    combinaciones = []
    intentos = 0
    max_intentos = cantidad * 5
    while len(combinaciones) < cantidad and intentos < max_intentos:
        combo = sorted(random.sample(universo, 6))
        if es_combinacion_valida(combo, historial):
            combinaciones.append({
                "combination": sorted([int(round(x)) for x in combo]),
                "source": "clustering",
                "score": 0.3
            })
            logger.info(f"[CLUSTER-BACKUP] {combo}")
        intentos += 1
    return combinaciones

def completar_con_backup(combinaciones, cantidad, historial, universo, logger):
    """Completa combinaciones con respaldo"""
    faltantes = cantidad - len(combinaciones)
    intentos = 0
    max_intentos = faltantes * 5
    while len(combinaciones) < cantidad and intentos < max_intentos:
        combo = sorted(random.sample(universo, 6))
        if es_combinacion_valida(combo, historial):
            combinaciones.append({
                "combination": sorted([int(round(x)) for x in combo]),
                "source": "clustering",
                "score": 0.4
            })
            logger.info(f"[CLUSTER-RESERVA] {combo}")
        intentos += 1
    return combinaciones

if __name__ == "__main__":
    data = pd.DataFrame({
        'Bolilla1': np.random.randint(1, 41, 100),
        'Bolilla2': np.random.randint(1, 41, 100),
        'Bolilla3': np.random.randint(1, 41, 100),
        'Bolilla4': np.random.randint(1, 41, 100),
        'Bolilla5': np.random.randint(1, 41, 100),
        'Bolilla6': np.random.randint(1, 41, 100)
    })
    combos = generar_combinaciones_clustering(data, cantidad=5)
    print("\nCombinaciones generadas:")
    for c in combos:
        print(f"- {c['combination']} (Score: {c['score']:.2f})")