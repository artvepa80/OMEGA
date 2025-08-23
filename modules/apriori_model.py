# ✅ OMEGA_PRO_AI_v10.1/modules/apriori_model.py - Versión Mejorada

from itertools import combinations
from collections import Counter, defaultdict
import random
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Set, Union, Any, Optional
from modules.filters.rules_filter import FiltroEstrategico
from modules.score_dynamics import score_combinations
from joblib import Parallel, delayed
import logging
import time
from functools import wraps
import os
import sys
import multiprocessing # ← seguimos necesitándolo

# Configuración de logger para evitar duplicados
logger_module = logging.getLogger(__name__)
logger_module.propagate = False

# Asegurar que el logger tenga al menos un handler
if not logger_module.handlers:
    logging.basicConfig(level=logging.INFO)

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None
    logger_module.warning("⚠️ Biblioteca xgboost no encontrada. Usando implementación personalizada.")

try:
    from modules.filters.ghost_rng_generative import evaluar_ghost_generativo
except ImportError:
    def evaluar_ghost_generativo(combo: List[int]) -> float:
        """Función de respaldo si ghost_rng_generative no está disponible"""
        return 0.5  # Puntaje neutro

# Función auxiliar para conteo de candidatos (para paralelización)
def _count_candidate(candidate: List[int], transactions: List[List[int]]) -> Tuple[Tuple[int, ...], int]:
    count = sum(1 for t in transactions if set(candidate).issubset(set(t)))
    return tuple(candidate), count

def log_time(func):
    """Decorador para medir el tiempo de ejecución de una función."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        logger = kwargs.get('logger', logger_module)
        logger.info(f"⏱️ {func.__name__} tomó {time.time() - start:.2f} segundos")
        return result
    return wrapper

class FPNode:
    """Nodo para el FP-Tree."""
    def __init__(self, item: int, count: int, parent: 'FPNode' = None):
        self.item = item
        self.count = count
        self.parent = parent
        self.children = {}
        self.node_link = None

class FPTree:
    """Árbol FP para minería de patrones frecuentes."""
    def __init__(self):
        self.root = FPNode(None, 0, None)
        self.header_table = {}

class DecisionTree:
    """Árbol de decisión simple para Random Forest."""
    def __init__(self, max_depth: int = 5):
        self.max_depth = max_depth
        self.feature = None
        self.threshold = None
        self.left = None
        self.right = None
        self.value = None

    def fit(self, X: np.ndarray, y: np.ndarray, depth: int = 0) -> None:
        if depth >= self.max_depth or len(np.unique(y)) == 1 or len(y) < 2:
            self.value = np.mean(y)
            return
        
        n_features = X.shape[1]
        best_gain = -float('inf')
        best_feature = None
        best_threshold = None
        
        for feature in range(n_features):
            thresholds = np.unique(X[:, feature])
            for threshold in thresholds:
                left_mask = X[:, feature] <= threshold
                right_mask = ~left_mask
                if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:
                    continue
                y_left = y[left_mask]
                y_right = y[right_mask]
                gain = np.var(y) - (len(y_left) / len(y) * np.var(y_left) + len(y_right) / len(y) * np.var(y_right))
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature
                    best_threshold = threshold
        
        if best_gain == -float('inf'):
            self.value = np.mean(y)
            return
        
        self.feature = best_feature
        self.threshold = best_threshold
        self.left = DecisionTree(max_depth=self.max_depth)
        self.right = DecisionTree(max_depth=self.max_depth)
        
        mask = X[:, best_feature] <= best_threshold
        self.left.fit(X[mask], y[mask], depth + 1)
        self.right.fit(X[~mask], y[~mask], depth + 1)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.value is not None:
            return np.full(X.shape[0], self.value)
        
        predictions = np.zeros(X.shape[0])
        mask = X[:, self.feature] <= self.threshold
        predictions[mask] = self.left.predict(X[mask])
        predictions[~mask] = self.right.predict(X[~mask])
        return predictions

class RandomForest:
    """Random Forest simple para clasificación."""
    def __init__(self, n_trees: int = 10, max_depth: int = 5, max_features: float = 0.5):
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.max_features = max_features
        self.trees = []
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        n_samples, n_features = X.shape
        max_features = int(self.max_features * n_features)
        self.trees = []
        
        for _ in range(self.n_trees):
            indices = np.random.choice(n_samples, n_samples, replace=True)
            features = np.random.choice(n_features, max_features, replace=False)
            X_subset = X[indices][:, features]
            y_subset = y[indices]
            tree = DecisionTree(max_depth=self.max_depth)
            tree.fit(X_subset, y_subset)
            self.trees.append((tree, features))
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        predictions = np.zeros(X.shape[0])
        for tree, features in self.trees:
            predictions += tree.predict(X[:, features])
        return predictions / self.n_trees

class XGBoostTree:
    """Árbol simple para XGBoost (usado solo si xgboost no está disponible)."""
    def __init__(self, max_depth: int = 5, lambda_reg: float = 1.0):
        self.max_depth = max_depth
        self.lambda_reg = lambda_reg
        self.feature = None
        self.threshold = None
        self.left = None
        self.right = None
        self.value = None

    def fit(self, X: np.ndarray, y: np.ndarray, grad: np.ndarray, hess: np.ndarray, depth: int = 0) -> None:
        if depth >= self.max_depth or len(np.unique(y)) == 1 or len(y) < 2:
            self.value = -np.sum(grad) / (np.sum(hess) + self.lambda_reg)
            return
        
        n_features = X.shape[1]
        best_gain = -float('inf')
        best_feature = None
        best_threshold = None
        
        for feature in range(n_features):
            thresholds = np.unique(X[:, feature])
            for threshold in thresholds:
                left_mask = X[:, feature] <= threshold
                right_mask = ~left_mask
                if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:
                    continue
                grad_left, grad_right = grad[left_mask], grad[right_mask]
                hess_left, hess_right = hess[left_mask], hess[right_mask]
                gain = (
                    0.5 * (
                        (np.sum(grad_left)**2 / (np.sum(hess_left) + self.lambda_reg)) +
                        (np.sum(grad_right)**2 / (np.sum(hess_right) + self.lambda_reg)) -
                        (np.sum(grad)**2 / (np.sum(hess) + self.lambda_reg))
                    ) - self.lambda_reg
                )
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature
                    best_threshold = threshold
        
        if best_gain == -float('inf'):
            self.value = -np.sum(grad) / (np.sum(hess) + self.lambda_reg)
            return
        
        self.feature = best_feature
        self.threshold = best_threshold
        self.left = XGBoostTree(max_depth=self.max_depth, lambda_reg=self.lambda_reg)
        self.right = XGBoostTree(max_depth=self.max_depth, lambda_reg=self.lambda_reg)
        
        mask = X[:, best_feature] <= best_threshold
        self.left.fit(X[mask], y[mask], grad[mask], hess[mask], depth + 1)
        self.right.fit(X[~mask], y[~mask], grad[~mask], hess[~mask], depth + 1)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.value is not None:
            return np.full(X.shape[0], self.value)
        
        predictions = np.zeros(X.shape[0])
        mask = X[:, self.feature] <= self.threshold
        predictions[mask] = self.left.predict(X[mask])
        predictions[~mask] = self.right.predict(X[~mask])
        return predictions

class CustomXGBoostClassifier:
    """XGBoost simple para clasificación (usado solo si xgboost no está disponible)."""
    def __init__(self, n_estimators: int = 10, max_depth: int = 5, learning_rate: float = 0.1, lambda_reg: float = 1.0):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.lambda_reg = lambda_reg
        self.trees = []
    
    def sigmoid(self, x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-x))
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        n_samples = X.shape[0]
        predictions = np.zeros(n_samples)
        self.trees = []
        
        for _ in range(self.n_estimators):
            probs = self.sigmoid(predictions)
            grad = probs - y
            hess = probs * (1 - probs)
            tree = XGBoostTree(max_depth=self.max_depth, lambda_reg=self.lambda_reg)
            tree.fit(X, y, grad, hess)
            self.trees.append(tree)
            predictions += self.learning_rate * tree.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        predictions = np.zeros(X.shape[0])
        for tree in self.trees:
            predictions += self.learning_rate * tree.predict(X)
        return self.sigmoid(predictions)

def _preparar_datos(data: Union[List[List[int]], pd.DataFrame], logger: logging.Logger) -> List[List[int]]:
    logger.debug(f"Preparando datos: tipo={type(data)}, tamaño={data.shape if isinstance(data, pd.DataFrame) else len(data)}")
    
    if isinstance(data, pd.DataFrame):
        # Buscar columnas con diferentes patrones
        columnas_numericas = [col for col in data.columns if any(pattern in col for pattern in ["Bolilla", "Numero", "n1", "n2", "n3", "n4", "n5", "n6", "B1", "B2", "B3", "B4", "B5", "B6"])]
        
        # Si no encuentra, usar las primeras 6 columnas numéricas
        if len(columnas_numericas) < 6:
            numeric_cols = [col for col in data.columns if data[col].dtype in ['int64', 'float64', 'int32', 'float32']]
            if len(numeric_cols) >= 6:
                columnas_numericas = numeric_cols[:6]
                logger.warning(f"⚠️ Usando primeras 6 columnas numéricas: {columnas_numericas}")
            else:
                logger.error(f"❌ Menos de 6 columnas numéricas en el DataFrame: {columnas_numericas}")
                # Retornar datos dummy en lugar de lista vacía
                logger.warning("🔄 Generando datos dummy para continuar el procesamiento")
                import numpy as np
                return [[i+1, i+2, i+3, i+4, i+5, i+6] for i in range(0, 60, 6)][:60]
        try:
            data_clean = data[columnas_numericas].dropna().apply(lambda x: x.map(lambda v: int(round(v)) if pd.notnull(v) else v))
            data_clean = data_clean.values.tolist()
        except Exception as e:
            logger.error(f"❌ Error al procesar DataFrame: {str(e)}")
            return []
    else:
        data_clean = [sorted([int(x) for x in draw if isinstance(x, (int, float))]) for draw in data if len(draw) >= 6]
    
    valid_draws = [d for d in data_clean if len(d) == 6 and all(1 <= x <= 40 for x in d)]
    if not valid_draws:
        logger.error("❌ No se encontraron sorteos válidos después de la limpieza")
    else:
        logger.info(f"✅ Preparados {len(valid_draws)} sorteos válidos")
    return valid_draws

def _calcular_frecuencias_posicionales(data: List[List[int]]) -> Dict[int, Dict[int, int]]:
    pos_freq = defaultdict(lambda: defaultdict(int))
    for draw in data:
        for pos, num in enumerate(draw):
            pos_freq[num][pos] += 1
    return pos_freq

def combinar_itemsets(
    apriori_itemsets: Dict[Tuple[int, ...], float],
    eclat_itemsets: Dict[Tuple[int, ...], float],
    fp_growth_itemsets: Dict[Tuple[int, ...], float],
    seq_patterns: Dict[Tuple[int, ...], float],
    mode: str,
    logger: logging.Logger
) -> Dict[Tuple[int, ...], float]:
    combined = {}
    try:
        if mode == 'union':
            for itemsets in [apriori_itemsets, eclat_itemsets, fp_growth_itemsets, seq_patterns]:
                combined.update(itemsets)
        elif mode == 'intersection':
            keys = set(apriori_itemsets.keys()) & set(eclat_itemsets.keys()) & set(fp_growth_itemsets.keys()) & set(seq_patterns.keys())
            for k in keys:
                combined[k] = max(apriori_itemsets.get(k, 0), eclat_itemsets.get(k, 0), fp_growth_itemsets.get(k, 0), seq_patterns.get(k, 0))
        elif mode == 'weighted':
            weights = {'apriori': 0.3, 'eclat': 0.3, 'fp_growth': 0.3, 'prefixspan': 0.1}
            for k in set(apriori_itemsets) | set(eclat_itemsets) | set(fp_growth_itemsets) | set(seq_patterns):
                combined[k] = sum(weights[algo] * itemsets.get(k, 0) for algo, itemsets in [
                    ('apriori', apriori_itemsets), ('eclat', eclat_itemsets), ('fp_growth', fp_growth_itemsets), ('prefixspan', seq_patterns)
                ])
        logger.info(f"✅ Combinados {len(combined)} itemsets en modo '{mode}'")
    except Exception as e:
        logger.error(f"❌ Error al combinar itemsets: {str(e)}")
    return combined

def _puntuar_combinacion(
    combo: List[int],
    frequency: Counter,
    co_occur: Dict[int, Counter],
    frequent_itemsets: Dict[Tuple[int, ...], float],
    pos_freq: Dict[int, Dict[int, int]],
    total_draws: int,
    config: Dict,
    clean_data: List[List[int]],
    cluster_centroids: List[Tuple[np.ndarray, int]],
    classifier: Any
) -> Dict[str, Any]:
    logger = config.get('logger', logger_module)
    metrics = {}
    
    try:
        freq_score = sum(frequency.get(num, 0) for num in combo) / (6 * total_draws)
        metrics['freq_score'] = freq_score
        
        co_occur_score = sum(
            co_occur.get(min(pair), Counter()).get(max(pair), 0) / max(1, sum(co_occur.get(min(pair), Counter()).values()))
            for pair in combinations(combo, 2)
        ) / max(1, len(list(combinations(combo, 2))))
        metrics['co_occur_score'] = co_occur_score
        
        itemset_score = sum(support for itemset, support in frequent_itemsets.items() if set(itemset).issubset(combo))
        metrics['itemset_score'] = itemset_score
        
        min_distance = float('inf')
        if cluster_centroids and config.get('use_clustering'):
            combo_array = np.array(sorted(combo), dtype=float)
            for centroid, _ in cluster_centroids:
                distance = np.sqrt(((combo_array - centroid)**2).sum())
                min_distance = min(min_distance, distance)
            clustering_score = 1.0 / (1.0 + min_distance) if min_distance != float('inf') else 0.0
            metrics['clustering_score'] = clustering_score
        else:
            clustering_score = 0.0
        
        pos_score = sum(pos_freq.get(num, {}).get(i, 0) / total_draws for i, num in enumerate(combo)) / 6 if pos_freq else 0.0
        metrics['pos_score'] = pos_score
        
        ghost_score = evaluar_ghost_generativo(combo) if config.get('use_ghost_rng') else 0.5
        metrics['ghost_score'] = ghost_score
        
        # Cálculo de classifier_score mejorado
        classifier_score = 0.5
        if config.get('use_classifier') and classifier is not None:
            try:
                features = extraer_caracteristicas(
                    [combo], frequency, co_occur, frequent_itemsets, 
                    cluster_centroids, pos_freq, total_draws
                )
                probs = classifier.predict_proba(features)
                
                # Manejar diferentes formatos de salida
                if probs.ndim == 2 and probs.shape[1] >= 2:
                    # Formato estándar: [prob_clase_0, prob_clase_1]
                    classifier_score = probs[0, 1]
                else:
                    # Formato personalizado: probabilidad directa
                    classifier_score = probs.flat[0]
            except Exception as e:
                logger.warning(f"⚠️ Error al predecir con el clasificador: {str(e)}")
                classifier_score = 0.5
        else:
            classifier_score = 0.5
        
        metrics['classifier_score'] = classifier_score
        
        score = (
            0.25 * freq_score +
            0.25 * co_occur_score +
            0.20 * itemset_score +
            0.10 * clustering_score +
            0.10 * pos_score +
            0.05 * ghost_score +
            0.05 * classifier_score
        )
        
        if config.get('penalizar_desequilibrio'):
            pares = sum(1 for num in combo if num % 2 == 0)
            if pares < 2 or pares > 4:
                score -= config.get('penalizacion_desequilibrio', 0.03)
        if config.get('validar_saltos'):
            saltos = [combo[i+1] - combo[i] for i in range(len(combo)-1)]
            if max(saltos) > 15:
                score -= config.get('penalizacion_saltos', 0.03)
        
        return {"score": max(0.0, min(1.0, score)), "metrics": metrics}
    
    except Exception as e:
        logger.warning(f"⚠️ Error al puntuar combinación {combo}: {str(e)}")
        return {"score": 0.5, "metrics": metrics}

def calcular_co_ocurrencia(data: List[List[int]], ventana: int = 10, logger: logging.Logger = None) -> Dict[int, Counter]:
    logger = logger or logger_module
    
    if not data or not all(isinstance(d, list) for d in data):
        logger.error("❌ Datos inválidos en calcular_co_ocurrencia")
        return defaultdict(Counter)
    
    co_occur = defaultdict(Counter)
    ventana_sets = [set(draw) for draw in data]
    
    for i in range(len(ventana_sets) - ventana + 1):
        ventana_actual = set.union(*ventana_sets[i:i+ventana])
        for pair in combinations(sorted(ventana_actual), 2):
            co_occur[pair[0]][pair[1]] += 1
            
    return co_occur

@log_time
def calcular_apriori(data: List[List[int]], min_support: float = 0.01, max_length: int = 3, logger: logging.Logger = None, rng_seed: int = None) -> Dict[Tuple[int, ...], float]:
    """
    Algoritmo Apriori con paralelización opcional.
    Si el dataset tiene ≥1000 transacciones se paraleliza el conteo de
    candidatos con **joblib** y backend ``threading`` (evita problemas de
    *pickling* al serializar funciones locales).
    """
    logger = logger or logger_module
    if rng_seed is not None:
        random.seed(rng_seed)
        np.random.seed(rng_seed)
    
    if not data:
        logger.error("❌ Datos vacíos en calcular_apriori")
        return {}
    
    total_transactions = len(data)
    min_support_count = max(1, int(min_support * total_transactions))
    
    frequency = Counter(num for draw in data for num in draw)
    frequent_items = {item: count for item, count in frequency.items() if count >= min_support_count}
    
    frequent_itemsets = {tuple([item]): count / total_transactions for item, count in frequent_items.items()}
    current_itemsets = [[item] for item in frequent_items]
    k = 2
    
    while current_itemsets and k <= max_length:
        new_itemsets = []
        for i, itemset1 in enumerate(current_itemsets):
            for itemset2 in current_itemsets[i+1:]:
                if itemset1[:-1] == itemset2[:-1]:
                    candidate = sorted(itemset1 + [itemset2[-1]])
                    if len(candidate) == k:
                        new_itemsets.append(candidate)
        
        if total_transactions < 1000:
            candidate_counts = {tuple(c): sum(1 for t in data if set(c).issubset(set(t))) for c in new_itemsets}
        else:
            # Usar backend threading para evitar problemas de serialización
            n_jobs = min(4, os.cpu_count() or 1)
            candidate_counts = dict(Parallel(n_jobs=n_jobs, backend="threading")(
                delayed(_count_candidate)(c, data) for c in new_itemsets
            ))
        
        for candidate in new_itemsets:
            count = candidate_counts.get(tuple(candidate), 0)
            if count >= min_support_count:
                frequent_itemsets[tuple(candidate)] = count / total_transactions
        
        current_itemsets = [list(itemset) for itemset, count in candidate_counts.items() if count >= min_support_count]
        k += 1
    
    logger.info(f"✅ [Apriori] Itemsets: {len(frequent_itemsets)} | Soporte: {min_support}")
    return frequent_itemsets

@log_time
def calcular_eclat(data: List[List[int]], min_support: float = 0.01, max_length: int = 3, logger: logging.Logger = None, rng_seed: int = None) -> Dict[Tuple[int, ...], float]:
    logger = logger or logger_module
    if rng_seed is not None:
        random.seed(rng_seed)
        np.random.seed(rng_seed)
    
    if not data:
        logger.error("❌ Datos vacíos en calcular_eclat")
        return {}

    try:
        tid_sets = defaultdict(set)
        for tid, draw in enumerate(data):
            for num in draw:
                tid_sets[num].add(tid)
        
        total_transactions = len(data)
        min_support_count = max(1, int(min_support * total_transactions))
        items_frecuentes = {item: tids for item, tids in tid_sets.items() if len(tids) >= min_support_count}
        
        queue = [([item], tid_set) for item, tid_set in items_frecuentes.items()]
        frequent_itemsets = {}
        
        while queue:
            itemset, tidset = queue.pop(0)
            frequent_itemsets[tuple(sorted(itemset))] = len(tidset) / total_transactions
            
            if len(itemset) >= max_length:
                continue
                
            ultimo_indice = list(items_frecuentes.keys()).index(itemset[-1])
            for next_item in list(items_frecuentes.keys())[ultimo_indice+1:]:
                new_tidset = tidset & items_frecuentes[next_item]
                if len(new_tidset) < min_support_count:
                    continue
                new_itemset = itemset + [next_item]
                queue.append((new_itemset, new_tidset))
        
        logger.info(f"✅ [ECLAT] Itemsets: {len(frequent_itemsets)} | Soporte: {min_support}")
        return frequent_itemsets
    
    except Exception as e:
        logger.error(f"❌ Error en calcular_eclat: {str(e)}")
        return {}

@log_time
def calcular_fp_growth(data: List[List[int]], min_support: float = 0.01, max_length: int = 3, logger: logging.Logger = None, rng_seed: int = None) -> Dict[Tuple[int, ...], float]:
    logger = logger or logger_module
    if rng_seed is not None:
        random.seed(rng_seed)
        np.random.seed(rng_seed)
    
    if not data:
        logger.error("❌ Datos vacíos en calcular_fp_growth")
        return {}

    try:
        total_transactions = len(data)
        min_support_count = max(1, int(min_support * total_transactions))
        frequency = Counter(num for draw in data for num in draw)
        frequent_items = {item: count for item, count in frequency.items() if count >= min_support_count}
        
        tree = FPTree()
        for item, count in frequent_items.items():
            tree.header_table[item] = [count, None]
        
        for transaction in data:
            transaction = [item for item in transaction if item in frequent_items]
            transaction.sort(key=lambda x: (-frequent_items[x], x))
            current_node = tree.root
            for item in transaction:
                if item in current_node.children:
                    current_node.children[item].count += 1
                else:
                    new_node = FPNode(item, 1, current_node)
                    current_node.children[item] = new_node
                    if tree.header_table[item][1] is None:
                        tree.header_table[item][1] = new_node
                    else:
                        current_link = tree.header_table[item][1]
                        while current_link.node_link:
                            current_link = current_link.node_link
                        current_link.node_link = new_node
                current_node = current_node.children[item]
        
        def mine_patterns(base_item: int, prefix: List[int], conditional_tree: FPTree, frequent_itemsets: Dict, max_depth: int = 5):
            if base_item not in conditional_tree.header_table:
                return
            
            if len(prefix) + 1 > max_length or len(prefix) >= max_depth:
                return
            
            try:
                count = conditional_tree.header_table[base_item][0]
                if count >= min_support_count:
                    itemset = tuple(sorted(prefix + [base_item]))
                    frequent_itemsets[itemset] = count / total_transactions
                
                items = sorted(
                    [(i, c) for i, (c, _) in conditional_tree.header_table.items() if i != base_item],
                    key=lambda x: (-x[1], x[0])
                )
                for next_item, _ in items:
                    if next_item not in conditional_tree.header_table:
                        continue
                    
                    conditional_patterns = []
                    current_node = conditional_tree.header_table[next_item][1]
                    while current_node:
                        path = []
                        path_count = current_node.count
                        parent = current_node.parent
                        while parent.item is not None:
                            path.append(parent.item)
                            parent = parent.parent
                        if path:
                            conditional_patterns.append((path, path_count))
                        current_node = current_node.node_link
                    
                    new_tree = FPTree()
                    new_frequency = Counter()
                    for path, count in conditional_patterns:
                        new_frequency.update({item: count for item in path})
                    new_frequent_items = {item: count for item, count in new_frequency.items() if count >= min_support_count}
                    for item in new_frequent_items:
                        new_tree.header_table[item] = [new_frequency[item], None]
                    
                    for path, count in conditional_patterns:
                        path = [item for item in path if item in new_frequent_items]
                        path.sort(key=lambda x: (-new_frequent_items[x], x))
                        current_node = new_tree.root
                        for item in path:
                            if item in current_node.children:
                                current_node.children[item].count += count
                            else:
                                new_node = FPNode(item, count, current_node)
                                current_node.children[item] = new_node
                                if new_tree.header_table[item][1] is None:
                                    new_tree.header_table[item][1] = new_node
                                else:
                                    current_link = new_tree.header_table[item][1]
                                    while current_link.node_link:
                                        current_link = current_link.node_link
                                    current_link.node_link = new_node
                            current_node = current_node.children[item]
                    
                    if new_tree.header_table:
                        mine_patterns(next_item, prefix + [base_item], new_tree, frequent_itemsets, max_depth)
            
            except KeyError as ke:
                logger.error(f"❌ Error en mine_patterns (KeyError): {str(ke)}")
            except Exception as e:
                logger.error(f"❌ Error inesperado en mine_patterns: {str(e)}")
        
        frequent_itemsets = {}
        for item in sorted(tree.header_table.keys(), key=lambda x: (-tree.header_table[x][0], x)):
            mine_patterns(item, [], tree, frequent_itemsets)
        
        logger.info(f"✅ [FP-Growth] Itemsets: {len(frequent_itemsets)} | Soporte: {min_support}")
        return frequent_itemsets
    
    except Exception as e:
        logger.error(f"❌ Error en calcular_fp_growth: {str(e)}")
        return {}

@log_time
def calcular_prefixspan(data: List[List[int]], min_support: float = 0.01, max_length: int = 3, logger: logging.Logger = None, rng_seed: int = None) -> Dict[Tuple[int, ...], float]:
    logger = logger or logger_module
    if rng_seed is not None:
        random.seed(rng_seed)
        np.random.seed(rng_seed)
    
    if not data:
        logger.error("❌ Datos vacíos en calcular_prefixspan")
        return {}

    total_sequences = len(data)
    min_support_count = max(1, int(min_support * total_sequences))

    def project_database(prefix: List[int], sequences: List[List[int]]) -> List[Tuple[List[int], int]]:
        projected_db = []
        for seq_idx, sequence in enumerate(sequences):
            found = False
            for i in range(len(sequence) - len(prefix) + 1):
                if sequence[i:i+len(prefix)] == prefix:
                    suffix = sequence[i+len(prefix):]
                    if suffix:
                        projected_db.append((suffix, 1))
                    found = True
                    break
            if not found and not prefix:
                projected_db.append((sequence, 1))
        return projected_db

    def prefixspan_recursive(prefix: List[int], projected_db: List[Tuple[List[int], int]], frequent_patterns: Dict, max_depth: int = 5):
        if len(prefix) >= max_length or len(prefix) >= max_depth:
            return
        
        item_counts = Counter()
        for suffix, count in projected_db:
            for item in suffix:
                item_counts[item] += count
        
        frequent_items = {item: count for item, count in item_counts.items() if count >= min_support_count}
        
        for item in sorted(frequent_items.keys()):
            new_prefix = prefix + [item]
            new_pattern = tuple(new_prefix)
            frequent_patterns[new_pattern] = frequent_items[item] / total_sequences
            
            new_projected_db = project_database(new_prefix, data)
            if new_projected_db:
                prefixspan_recursive(new_prefix, new_projected_db, frequent_patterns, max_depth)
    
    frequent_patterns = {}
    prefixspan_recursive([], [(seq, 1) for seq in data], frequent_patterns)
    
    logger.info(f"✅ [PrefixSpan] Patrones secuenciales: {len(frequent_patterns)} | Soporte: {min_support}")
    return frequent_patterns

@log_time
def calcular_kmeans(data: List[List[int]], k: int, max_iter: int = 100, logger: logging.Logger = None, rng_seed: int = None) -> List[Tuple[np.ndarray, int]]:
    logger = logger or logger_module
    if rng_seed is not None:
        np.random.seed(rng_seed)
    
    if not data:
        logger.error("❌ Datos vacíos en calcular_kmeans")
        return []

    X = np.array([sorted(draw) for draw in data], dtype=float)
    n_samples = X.shape[0]
    k = min(k, n_samples)
    
    indices = np.random.choice(n_samples, k, replace=False)
    centroids = X[indices]
    
    for _ in range(max_iter):
        distances = np.sqrt(((X - centroids[:, np.newaxis])**2).sum(axis=2))
        labels = np.argmin(distances, axis=0)
        new_centroids = np.array([X[labels == i].mean(axis=0) if np.sum(labels == i) > 0 else centroids[i] for i in range(k)])
        
        if np.all(centroids == new_centroids):
            break
        centroids = new_centroids
    
    cluster_sizes = Counter(labels)
    result = [(centroid, cluster_sizes[i]) for i, centroid in enumerate(centroids)]
    
    logger.info(f"✅ [K-Means] {k} clústeres generados")
    return result

def extraer_caracteristicas(
    combos: List[List[int]],
    frequency: Counter,
    co_occur: Dict[int, Counter],
    frequent_itemsets: Dict[Tuple[int, ...], float],
    cluster_centroids: List[Tuple[np.ndarray, int]],
    pos_freq: Dict[int, Dict[int, int]],
    total_draws: int
) -> np.ndarray:
    features = []
    for combo in combos:
        sorted_combo = sorted(combo)
        suma = sum(combo)
        num_pares = sum(1 for num in combo if num % 2 == 0)
        saltos = sum(sorted_combo[i] - sorted_combo[i-1] for i in range(1, len(combo))) / (len(combo) - 1) if len(combo) > 1 else 0
        freq_score = sum(frequency.get(num, 0) for num in combo) / (6 * total_draws)
        co_occur_score = sum(
            co_occur.get(min(pair), Counter()).get(max(pair), 0) / 
            max(1, sum(co_occur.get(min(pair), Counter()).values()))
            for pair in combinations(sorted_combo, 2)
        ) / max(1, len(list(combinations(sorted_combo, 2))))
        itemset_score = sum(support for itemset, support in frequent_itemsets.items() if set(itemset).issubset(combo))
        min_distance = float('inf')
        if cluster_centroids:
            combo_array = np.array(sorted_combo, dtype=float)
            for centroid, _ in cluster_centroids:
                distance = np.sqrt(((combo_array - centroid)**2).sum())
                min_distance = min(min_distance, distance)
        # Eliminado std_dev ya que no se usa
        pos_freq_score = sum(pos_freq.get(num, {}).get(i, 0) / total_draws for i, num in enumerate(combo)) / 6 if pos_freq else 0
        features.append([suma, num_pares, saltos, freq_score, co_occur_score, itemset_score, min_distance, pos_freq_score])
    return np.array(features)

def calcular_random_forest(
    data: List[List[int]],
    frequency: Counter,
    co_occur: Dict[int, Counter],
    frequent_itemsets: Dict[Tuple[int, ...], float],
    cluster_centroids: List[Tuple[np.ndarray, int]],
    pos_freq: Dict[int, Dict[int, int]],
    total_draws: int,
    n_trees: int = 10,
    logger: logging.Logger = None,
    rng_seed: int = None
) -> RandomForest:
    logger = logger or logger_module
    if rng_seed is not None:
        np.random.seed(rng_seed)
    
    if not data:
        logger.error("❌ Datos vacíos en calcular_random_forest")
        return RandomForest(n_trees=0)
    
    X = extraer_caracteristicas(data, frequency, co_occur, frequent_itemsets, cluster_centroids, pos_freq, total_draws)
    y = np.ones(len(data))  # Etiquetas positivas para datos históricos
    
    # Ajustar dinámicamente el número de árboles
    n_trees = max(10, n_trees) if len(data) > 0 else 0
    
    classifier = RandomForest(n_trees=n_trees, max_depth=5, max_features=0.5)
    classifier.fit(X, y)
    
    logger.info(f"✅ Random Forest entrenado con {n_trees} árboles")
    return classifier

def calcular_xgboost(
    data: List[List[int]],
    frequency: Counter,
    co_occur: Dict[int, Counter],
    frequent_itemsets: Dict[Tuple[int, ...], float],
    cluster_centroids: List[Tuple[np.ndarray, int]],
    pos_freq: Dict[int, Dict[int, int]],
    total_draws: int,
    n_estimators: int = 50,
    learning_rate: float = 0.05,
    logger: logging.Logger = None,
    rng_seed: int = None
) -> Optional[Union[XGBClassifier, CustomXGBoostClassifier]]:
    logger = logger or logger_module
    if rng_seed is not None:
        np.random.seed(rng_seed)
    
    if not data:
        logger.error("❌ Datos vacíos en calcular_xgboost")
        return None
    
    try:
        # Extraer características para datos positivos (historial)
        X = extraer_caracteristicas(data, frequency, co_occur, frequent_itemsets, cluster_centroids, pos_freq, total_draws)
        y = np.ones(len(data))  # Etiquetas positivas para datos históricos
        
        # Ajustar n_estimators basado en el tamaño del dataset
        if len(data) < 200:
            n_estimators = min(50, n_estimators)
            logger.info(f"🔧 Ajustando n_estimators a {n_estimators} para dataset pequeño")
        
        # Generar datos negativos sintéticos si solo hay una clase
        if np.unique(y).size < 2:
            n_neg = max(50, len(X))  # Mismo tamaño que positivos o 50 como mínimo
            logger.info(f"🩹 Generando {n_neg} ejemplos negativos sintéticos")
            
            # Crear combinaciones aleatorias como ejemplos negativos
            rnd_combos = []
            for _ in range(n_neg):
                combo = sorted(random.sample(range(1, 41), 6))
                rnd_combos.append(combo)
            
            # Extraer características para los ejemplos negativos
            X_neg = extraer_caracteristicas(
                rnd_combos, frequency, co_occur, frequent_itemsets,
                cluster_centroids, pos_freq, total_draws
            )
            
            # Combinar datos positivos y negativos
            X = np.vstack([X, X_neg])
            y = np.concatenate([y, np.zeros(n_neg)])
            logger.info(f"🩹 Añadidos {n_neg} ejemplos negativos sintéticos")
        
        # Entrenar el clasificador
        if XGBClassifier is not None:
            classifier = XGBClassifier(
                n_estimators=n_estimators,
                learning_rate=learning_rate,
                max_depth=5,
                random_state=rng_seed,
                objective="binary:logistic",
                eval_metric="logloss",
                n_jobs=1
            )
            classifier.fit(X, y)
        else:
            classifier = CustomXGBoostClassifier(
                n_estimators=n_estimators,
                max_depth=5,
                learning_rate=learning_rate
            )
            classifier.fit(X, y)
        
        logger.info(f"✅ XGBoost entrenado con {np.unique(y).size} clases")
        return classifier
    
    except Exception as e:
        logger.error(f"❌ Error en calcular_xgboost: {str(e)}")
        return None

def generar_combinaciones_apriori(
    data: Union[List[List[int]], pd.DataFrame],
    historial_set: Set[Tuple[int, ...]],
    num_predictions: int = 100,
    cantidad: int = None,
    logger: logging.Logger = None,
    config: Dict = None,
    rng_seed: int = None,
    **kwargs
) -> List[Dict]:
    # Configuración del logger
    logger = logger or logger_module
    logger.propagate = False
    
    # Verificar funciones helper
    helper_functions = {
        '_preparar_datos': globals().get('_preparar_datos'),
        '_calcular_frecuencias_posicionales': globals().get('_calcular_frecuencias_posicionales'),
        'combinar_itemsets': globals().get('combinar_itemsets')
    }
    for func_name, func in helper_functions.items():
        if func is None:
            logger.error(f"❌ Función helper {func_name} no definida")
            return []
    logger.info("✅ Todas las funciones helper están definidas")
    
    if cantidad is not None:
        if not isinstance(cantidad, int) or cantidad <= 0 or cantidad > 1000:
            logger.error(f"❌ Valor inválido para 'cantidad': {cantidad}. Debe ser un entero positivo <= 1000.")
            return []
        logger.info(f"⚠️ Usando 'cantidad' como alias de 'num_predictions': {cantidad}")
        num_predictions = cantidad
    
    logger.debug(f"Datos de entrada: tipo={data.__class__.__name__}, tamaño={data.shape if isinstance(data, pd.DataFrame) else len(data)}")
    if isinstance(data, pd.DataFrame):
        if data.empty and len(data.columns) != 0 or data.shape[1] < 6:
            logger.error("Datos incorrectos: DataFrame vacío o con columnas insuficientes")
            return []
    elif not data or not all(isinstance(d, list) and len(d) >= 6 for d in data):
        logger.error("Datos incorrectos: Lista de datos vacía o con sorteos incorrectos")
        return []
    
    clean_data = _preparar_datos(data, logger)
    if not clean_data:
        logger.error("❌ No se pudieron preparar los datos")
        return []
    
    total_draws = len(clean_data)
    
    # Configuración con claves normalizadas
    default_config = {
        'penalizar_desequilibrio': True,
        'penalizacion_desequilibrio': 0.03,
        'validar_saltos': True,
        'penalizacion_saltos': 0.03,
        'positional_analysis': True,
        'bonus_posicional': 0.07,
        'ventana_co_ocurrencia': 11,
        'frequent_itemset_method': 'combined',
        'combination_mode': 'union',
        'min_support_frequent': 0.01,
        'max_itemset_length': 2,
        'diversificacion_temporal': True,
        'penalizacion_temporal': 0.04,
        'use_ghost_rng': True,
        'penalizacion_ghost_rng': 0.07,
        'bonus_ghost_rng': 0.03,
        'use_clustering': True,
        'num_clusters': 4,
        'clustering_threshold': 8.0,
        'bonus_clustering': 0.04,
        'use_classifier': True,
        'classifier_type': 'xgboost',
        'n_estimators': 100,
        'learning_rate': 0.05,
        'classifier_threshold': 0.6,
        'bonus_classifier': 0.04,
        'penalizacion_classifier': 0.02,
        'verbose': True,
        'fallback_to_rf': True
    }
    config = {**default_config, **(config or {}), **kwargs}
    config['logger'] = logger
    
    if rng_seed is not None:
        random.seed(rng_seed)
        np.random.seed(rng_seed)
        os.environ['PYTHONHASHSEED'] = str(rng_seed)
    
    logger.info(f"🚗 Iniciando generación de combinaciones con {total_draws} sorteos, método={config['frequent_itemset_method']}")
    
    flat_numbers = [num for draw in clean_data for num in draw]
    frequency = Counter(flat_numbers)
    co_occur = calcular_co_ocurrencia(clean_data, config['ventana_co_ocurrencia'], logger)
    pos_freq = _calcular_frecuencias_posicionales(clean_data) if config['positional_analysis'] else {}
    
    frequent_itemsets = {}
    seq_patterns = {}
    cluster_centroids = []
    classifier = None
    
    try:
        if config['frequent_itemset_method'] == 'combined':
            logger.info("🚗 Usando combinación de Apriori, ECLAT, FP-Growth y PrefixSpan")
            apriori_itemsets = calcular_apriori(
                clean_data, 
                min_support=config['min_support_frequent'],
                max_length=config['max_itemset_length'],
                logger=logger,
                rng_seed=rng_seed
            )
            eclat_itemsets = calcular_eclat(
                clean_data, 
                min_support=config['min_support_frequent'],
                max_length=config['max_itemset_length'],
                logger=logger,
                rng_seed=rng_seed
            )
            fp_growth_itemsets = calcular_fp_growth(
                clean_data, 
                min_support=config['min_support_frequent'],
                max_length=config['max_itemset_length'],
                logger=logger,
                rng_seed=rng_seed
            )
            seq_patterns = calcular_prefixspan(
                clean_data,
                min_support=config['min_support_frequent'],
                max_length=config['max_itemset_length'],
                logger=logger,
                rng_seed=rng_seed
            )
            frequent_itemsets = combinar_itemsets(
                apriori_itemsets, 
                eclat_itemsets, 
                fp_growth_itemsets, 
                seq_patterns,
                config['combination_mode'], 
                logger
            )
        elif config['frequent_itemset_method'] == 'apriori':
            logger.info("🚗 Usando Apriori para itemsets frecuentes")
            frequent_itemsets = calcular_apriori(
                clean_data, 
                min_support=config['min_support_frequent'],
                max_length=config['max_itemset_length'],
                logger=logger,
                rng_seed=rng_seed
            )
        elif config['frequent_itemset_method'] == 'eclat':
            logger.info("🚗 Usando ECLAT para itemsets frecuentes")
            frequent_itemsets = calcular_eclat(
                clean_data, 
                min_support=config['min_support_frequent'],
                max_length=config['max_itemset_length'],
                logger=logger,
                rng_seed=rng_seed
            )
        elif config['frequent_itemset_method'] == 'fp_growth':
            logger.info("🚗 Usando FP-Growth para itemsets frecuentes")
            frequent_itemsets = calcular_fp_growth(
                clean_data, 
                min_support=config['min_support_frequent'],
                max_length=config['max_itemset_length'],
                logger=logger,
                rng_seed=rng_seed
            )
        elif config['frequent_itemset_method'] == 'prefixspan':
            logger.info("🚗 Usando PrefixSpan para patrones secuenciales")
            frequent_itemsets = calcular_prefixspan(
                clean_data,
                min_support=config['min_support_frequent'],
                max_length=config['max_itemset_length'],
                logger=logger,
                rng_seed=rng_seed
            )
        
        if not frequent_itemsets:
            logger.warning("⚠️ No se generaron itemsets frecuentes, usando respaldo")
        
        if config['use_clustering']:
            logger.info(f"🚗 Aplicando K-Means con {config['num_clusters']} clústeres")
            cluster_centroids = calcular_kmeans(
                clean_data,
                k=config['num_clusters'],
                logger=logger,
                rng_seed=rng_seed
            )
        
        if config['use_classifier']:
            if config['classifier_type'] == 'xgboost':
                logger.info(f"🚗 Entrenando XGBoost con {config['n_estimators']} árboles")
                classifier = calcular_xgboost(
                    clean_data,
                    frequency,
                    co_occur,
                    frequent_itemsets,
                    cluster_centroids,
                    pos_freq,
                    total_draws,
                    n_estimators=config['n_estimators'],
                    learning_rate=config['learning_rate'],
                    logger=logger,
                    rng_seed=rng_seed
                )
                # Si XGBoost falló y tenemos fallback a RF, entrenamos un RandomForest
                if classifier is None and config.get('fallback_to_rf', True):
                    # Ajustar número de árboles para el fallback
                    n_trees = max(10, config['n_estimators'])
                    logger.warning(f"⚠️ Fallando a Random Forest con {n_trees} árboles")
                    classifier = calcular_random_forest(
                        clean_data,
                        frequency,
                        co_occur,
                        frequent_itemsets,
                        cluster_centroids,
                        pos_freq,
                        total_draws,
                        n_trees=n_trees,
                        logger=logger,
                        rng_seed=rng_seed
                    )
            else:
                logger.info(f"🚗 Entrenando Random Forest con {config['n_estimators']} árboles")
                classifier = calcular_random_forest(
                    clean_data,
                    frequency,
                    co_occur,
                    frequent_itemsets,
                    cluster_centroids,
                    pos_freq,
                    total_draws,
                    n_trees=config['n_estimators'],
                    logger=logger,
                    rng_seed=rng_seed
                )
    
    except ValueError as ve:
        logger.error(f"❌ Error de valor en generación de itemsets o clasificador: {str(ve)}")
        return []
    except MemoryError as me:
        logger.error(f"❌ Error de memoria en generación de itemsets o clasificador: {str(me)}")
        return []
    except Exception as e:
        logger.error(f"❌ Error inesperado en generación de itemsets o clasificador: {str(e)}")
        return []
    
    config['use_frequent_itemsets'] = config['frequent_itemset_method'] in ['apriori', 'eclat', 'fp_growth', 'prefixspan', 'combined']
    
    filtro = FiltroEstrategico()
    try:
        filtro.cargar_historial([list(t) for t in historial_set])
    except Exception as e:
        logger.error(f"❌ Error en filtro: {str(e)}")
        return []
    
    results = []
    numeros_disponibles = list(range(1, 41))
    intentos = 0
    max_intentos = num_predictions * 20
    
    while len(results) < num_predictions and intentos < max_intentos:
        intentos += 1
        
        try:
            if config['use_frequent_itemsets'] and frequent_itemsets:
                itemset = random.choice(list(frequent_itemsets.keys()))
                nucleo = list(itemset)
                relacionados = set()
                for num in nucleo:
                    if num in co_occur:
                        relacionados.update(
                            n for n, cnt in co_occur[num].most_common(3) 
                            if n in numeros_disponibles
                        )
                
                if random.random() < 0.2:
                    if nucleo and relacionados:
                        idx = random.randint(0, len(nucleo) - 1)
                        nucleo[idx] = random.choice(list(relacionados))
                
                candidatos = set(nucleo)
                if random.random() < 0.1 and len(frequent_itemsets) > 1:
                    other_itemset = random.choice(list(frequent_itemsets.keys()))
                    candidatos.update(list(other_itemset)[:3])
                
                faltantes = 6 - len(candidatos)
                if faltantes > 0:
                    candidatos.update(random.sample(numeros_disponibles, faltantes))
            else:
                nucleo = random.choices(
                    population=list(frequency.keys()),
                    weights=list(frequency.values()),
                    k=3
                )
                relacionados = set()
                for num in nucleo:
                    if num in co_occur:
                        relacionados.update(
                            n for n, cnt in co_occur[num].most_common(3) 
                            if n in numeros_disponibles
                        )
                candidatos = set(nucleo) | relacionados
                faltantes = 6 - len(candidatos)
                if faltantes > 0:
                    candidatos.update(random.sample(numeros_disponibles, faltantes))
            
            combo = sorted(list(candidatos))
            if len(combo) != 6:
                continue
            combo_tuple = tuple(combo)
            
            if combo_tuple in historial_set:
                if config['verbose']:
                    logger.info(f"[Apriori] Descartada (historial): {combo}")
                continue
                
            if not filtro.aplicar_filtros(combo):
                if config['verbose']:
                    razones_filtro = getattr(filtro, 'obtener_razones_rechazo', lambda x: ["Filtros no especificados"])(combo)
                    logger.info(f"[Apriori] Descartada por filtros: {combo} - Razones: {razones_filtro}")
                continue
                
            if any(combo_tuple == tuple(r["combination"]) for r in results):
                if config['verbose']:
                    logger.info(f"[Apriori] Descartada (duplicado en lote): {combo}")
                continue
                
            score_result = _puntuar_combinacion(
                combo,
                frequency,
                co_occur,
                frequent_itemsets,
                pos_freq,
                total_draws,
                config,
                clean_data,
                cluster_centroids,
                classifier
            )
            
            results.append({
                "combination": combo,
                "score": score_result["score"],
                "source": config['frequent_itemset_method'],
                "metrics": score_result["metrics"]
            })
            if config['verbose']:
                logger.info(f"[Apriori] Combinación generada: {combo} - Score: {score_result['score']:.4f}")
        
        except Exception as e:
            logger.warning(f"⚠️ Error al generar combinación: {str(e)}")
            continue
    
    if len(results) < num_predictions:
        logger.info(f"🔁 [Apriori] Generando respaldo para {num_predictions - len(results)} combinaciones")
        faltantes = num_predictions - len(results)
        for _ in range(faltantes * 5):
            if len(results) >= num_predictions:
                break
            try:
                combo = sorted(random.sample(numeros_disponibles, 6))
                combo_tuple = tuple(combo)
                if (combo_tuple not in historial_set and 
                    filtro.aplicar_filtros(combo) and
                    not any(combo_tuple == tuple(r["combination"]) for r in results)):
                    score_result = _puntuar_combinacion(
                        combo,
                        frequency,
                        co_occur,
                        frequent_itemsets,
                        pos_freq,
                        total_draws,
                        config,
                        clean_data,
                        cluster_centroids,
                        classifier
                    )
                    results.append({
                        "combination": combo,
                        "score": score_result["score"],
                        "source": "apriori_backup",
                        "metrics": score_result["metrics"]
                    })
                    if config['verbose']:
                        logger.info(f"[Apriori] Respaldo generado: {combo} - Score: {score_result['score']:.4f}")
            except Exception as e:
                logger.warning(f"⚠️ Error al generar combinación de respaldo: {str(e)}")
                continue
    
    if results and total_draws > 100:
        try:
            df_historial = pd.DataFrame(clean_data, columns=[f"Num_{i+1}" for i in range(6)])
            resultados_mejorados = score_combinations(
                combinations=results,
                historial=df_historial,
                logger=logger
            )
            for i, res in enumerate(resultados_mejorados):
                results[i]["score"] = res["score"]
                results[i]["metrics"] = res.get("metrics", results[i]["metrics"])
        except Exception as e:
            logger.warning(f"⚠️ Error en scoring avanzado: {str(e)}")
    
    logger.info(f"✅ Generadas {len(results)}/{num_predictions} combinaciones válidas")
    return results[:num_predictions]

# Smoke test para ejecución directa
if __name__ == "__main__":
    import pandas as pd
    import os
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("apriori_smoke_test")
    
    logger.info("🔥 Iniciando prueba de humo para apriori_model")
    
    try:
        # Verificar si existe el archivo CSV
        csv_path = "data/loteria.csv"
        if os.path.exists(csv_path):
            datos = pd.read_csv(csv_path)
            logger.info(f"✅ Datos cargados desde {csv_path}")
        else:
            # Generar datos de prueba si no existe el archivo
            logger.warning("⚠️ Archivo de datos no encontrado, generando datos de prueba")
            datos = [random.sample(range(1, 41), 6) for _ in range(100)]
        
        # Preparar historial
        if isinstance(datos, pd.DataFrame):
            historial = set(tuple(sorted(row)) for row in datos.values.tolist())
        else:
            historial = set(tuple(sorted(draw)) for draw in datos)
        
        # Generar combinaciones
        combinaciones = generar_combinaciones_apriori(
            data=datos,
            historial_set=historial,
            num_predictions=5,
            logger=logger,
            rng_seed=42
        )
        
        if combinaciones:
            logger.info("✅ Prueba de humo exitosa. Combinaciones generadas:")
            for i, combo in enumerate(combinaciones):
                logger.info(f"{i+1}. {combo['combination']} - Score: {combo['score']:.4f}")
        else:
            logger.error("❌ Prueba de humo fallida: no se generaron combinaciones")
    except Exception as e:
        logger.exception(f"❌ Prueba de humo fallida: {str(e)}")
        sys.exit(1)