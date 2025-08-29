# OMEGA_PRO_AI_v10.1/utils/viabilidad.py – Versión Mejorada v12.4

import json
import os
import time
import ast
import logging
import threading
from typing import List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from utils.logging.unified_logger import log_debug, log_info, log_warning, log_error

# Soporte para Cython si disponible (para batches grandes)
try:
    from utils.cython_svi import fast_calculate_svi
except ImportError:
    fast_calculate_svi = None

# Configuración de depuración
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
_CONFIG_CACHE = None
_CONFIG_LAST_MODIFIED = 0
_CACHE_LOCK = threading.Lock()

def calcular_svi(combinacion: str, perfil_rng: str, validacion_ghost: bool, score_historico: float, config: dict = None) -> float:
    """Calcula el Score de Viabilidad de Inversión (SVI) mejorado y normalizado a 0-1."""
    try:
        score_historico = max(0.0, min(5.0, float(score_historico)))
    except (TypeError, ValueError):
        score_historico = 0.5
    
    perfil_rng = str(perfil_rng).lower() if perfil_rng else "b"  # Default a medio
    validacion_ghost = bool(validacion_ghost)
    config = config or {}  # Config opcional para pesos

    # Validar y parsear combinación
    try:
        nums = ast.literal_eval(combinacion)
        if not (isinstance(nums, list) and len(nums) == 6 and all(isinstance(n, int) and 1 <= n <= 40 for n in nums)):
            log_warning(f"Combinación inválida: {combinacion} (debe ser 6 únicos entre 1-40)")
            return 0.5
        nums = sorted(set(nums))  # Asegurar únicos y ordenados
        if len(nums) != 6:
            log_warning(f"Duplicados en {combinacion}, fallback")
            return 0.5
    except (ValueError, SyntaxError):
        log_warning(f"Combinación no válida: {combinacion}")
        return 0.5

    if DEBUG_MODE:
        log_debug(f"Iniciando SVI para: {combinacion} | Params: RNG={perfil_rng}, Ghost={validacion_ghost}, Hist={score_historico}")

    # Mapear perfiles a rangos preferidos (compatibilidad con "A"/"B"/"C" y legacy)
    perfil_map = {
        "a": "conservador", "conservador": "conservador",  # Bajo: 1-20
        "b": "moderado", "moderado": "moderado",          # Medio: 11-20
        "c": "agresivo", "agresivo": "agresivo"           # Alto: 21-40
    }
    perfil_normalized = perfil_map.get(perfil_rng, "moderado")

    # Cálculos sofisticados (pesos configurables via config)
    min_sum = 21  # 1+2+3+4+5+6
    max_sum = 225  # 35+36+37+38+39+40
    sum_nums = sum(nums)
    sum_norm = (sum_nums - min_sum) / (max_sum - min_sum) if sum_nums >= min_sum else 0.0  # Normalizado 0-1

    even_count = sum(1 for n in nums if n % 2 == 0)
    parity_balance = 1.0 - abs(even_count - 3) / 3.0  # Ideal 3/3

    consec = sum(1 for i in range(5) if nums[i+1] - nums[i] == 1)
    consec_penalty = 1.0 - (consec / 5.0)

    # Peso por rango según perfil (ajustado mid a 11-20 para menos overlap)
    low = sum(1 for n in nums if 1 <= n <= 20)
    mid = sum(1 for n in nums if 11 <= n <= 20)
    high = sum(1 for n in nums if 21 <= n <= 40)
    range_weight = 0.5
    if perfil_normalized == "conservador":
        range_weight = low / 6.0
    elif perfil_normalized == "moderado":
        range_weight = mid / 6.0
    elif perfil_normalized == "agresivo":
        range_weight = high / 6.0

    ghost_bonus = 0.1 if validacion_ghost else 0.0
    hist_bonus = score_historico / 5.0  # Normalizado

    # Pesos (customizables)
    weights = config.get("svi_weights", {"sum": 0.25, "parity": 0.2, "consec": 0.2, "range": 0.2, "ghost": 0.1, "hist": 0.1})
    svi = (
        sum_norm * weights["sum"] +
        parity_balance * weights["parity"] +
        consec_penalty * weights["consec"] +
        range_weight * weights["range"] +
        ghost_bonus * weights["ghost"] +
        hist_bonus * weights["hist"]
    )

    svi = min(max(svi, 0.0), 1.0)  # Clamp 0-1
    if DEBUG_MODE:
        log_info(f"SVI: {combinacion} | SumNorm={sum_norm:.2f}, Parity={parity_balance:.2f}, Consec={consec_penalty:.2f}, Range={range_weight:.2f}, Ghost={ghost_bonus:.2f}, Hist={hist_bonus:.2f} → {svi:.2f}")
    return svi

def batch_calcular_svi(combinations: List[str], perfil_rng: str, validacion_ghost: bool, score_historico: float, config: dict = None) -> List[Tuple[str, float]]:
    """Batch con logging optimizado."""
    config = config or {}
    results = []
    failed = 0
    for comb in combinations:
        try:
            svi = calcular_svi(comb, perfil_rng, validacion_ghost, score_historico, config)
            results.append((comb, svi))
        except Exception as e:
            log_error(f"Error SVI {comb}: {str(e)}")
            results.append((comb, 0.5))
            failed += 1
    
    if failed:
        log_warning(f"{failed}/{len(combinations)} fallidas")
    
    if len(results) > 100:
        max_svi = max(r[1] for r in results)
        min_svi = min(r[1] for r in results)
        avg_svi = sum(r[1] for r in results) / len(results)
        log_info(f"Batch {len(results)}: Max={max_svi:.2f}, Min={min_svi:.2f}, Avg={avg_svi:.2f}")
    else:
        log_info(f"Batch {len(results)}: {results}")
    return results

def parallel_svi(
    combinations: List[str],
    perfil_rng: str,
    validacion_ghost: bool,
    score_historico: float,
    progress_callback: callable = None,
    config: dict = None,
    logger: logging.Logger = None,
    max_workers: int = None,
    executor=None  # Para custom executor en main.py
) -> List[Tuple[str, float]]:
    """Paralelo con fallback a Cython si disponible y batch grande."""
    if not combinations:
        log_warning("Combinaciones vacías")
        return []
    
    total = len(combinations)
    if total > 500 and fast_calculate_svi:
        log_info("Usando Cython para SVI rápido")
        return fast_calculate_svi(combinations, perfil_rng, validacion_ghost, score_historico)
    
    max_workers = max_workers or max(1, cpu_count() - 1)
    batch_size = max(1, total // max_workers)
    batches = [combinations[i:i + batch_size] for i in range(0, total, batch_size)]
    
    results = []
    executor_class = executor or ProcessPoolExecutor
    with executor_class(max_workers=max_workers) as exec:
        futures = [exec.submit(batch_calcular_svi, batch, perfil_rng, validacion_ghost, score_historico, config) for batch in batches]
        
        completed = 0
        for future in as_completed(futures):
            try:
                batch_results = future.result()
                results.extend(batch_results)
                completed += len(batch_results)
                if progress_callback:
                    progress_callback(completed, total)
            except Exception as e:
                log_error(f"Batch error: {str(e)}")
                fallback = [(comb, 0.5) for comb in batches[0]]  # Asumir tamaño batch
                results.extend(fallback)
                completed += len(fallback)
                if progress_callback:
                    progress_callback(completed, total)
    
    return results

def cargar_viabilidad(path: str = "data/viabilidad_config.json", watch_changes: bool = False, cache_timeout: int = 3600) -> dict:
    """Carga config con caché (sin cambios mayores, pero añade svi_weights default)."""
    global _CONFIG_CACHE, _CONFIG_LAST_MODIFIED
    with _CACHE_LOCK:
        abs_path = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path))
        
        current_time = time.time()
        if _CONFIG_CACHE is not None and current_time - _CONFIG_LAST_MODIFIED < cache_timeout:
            return _CONFIG_CACHE
        
        if watch_changes and os.path.exists(abs_path):
            mod_time = os.path.getmtime(abs_path)
            if mod_time <= _CONFIG_LAST_MODIFIED:
                return _CONFIG_CACHE
        
        try:
            with open(abs_path, "r") as f:
                config = json.load(f)
                # Añadir defaults para nuevos pesos
                if "svi_weights" not in config:
                    config["svi_weights"] = {"sum": 0.25, "parity": 0.2, "consec": 0.2, "range": 0.2, "ghost": 0.1, "hist": 0.1}
                _CONFIG_CACHE = config
                _CONFIG_LAST_MODIFIED = os.path.getmtime(abs_path)
                log_info(f"Config cargada: {len(config)} params")
                return config
        except Exception as e:
            log_error(f"Error carga config: {str(e)}")
            return {"svi_weights": {"sum": 0.25, "parity": 0.2, "consec": 0.2, "range": 0.2, "ghost": 0.1, "hist": 0.1}}

def invalidate_config_cache() -> None:
    global _CONFIG_CACHE, _CONFIG_LAST_MODIFIED
    with _CACHE_LOCK:
        _CONFIG_CACHE = None
        _CONFIG_LAST_MODIFIED = 0
    log_info("Caché invalidado")

def calcular_svi_individual(combinacion, perfil_rng: str = "B", validacion_ghost: bool = False,
                            score_historico: float = 3.0, config: Optional[dict] = None) -> float:
    """Wrapper retrocompatible."""
    try:
        combinacion_str = json.dumps(combinacion) if not isinstance(combinacion, str) else combinacion
        return calcular_svi(combinacion_str, perfil_rng, validacion_ghost, score_historico, config)
    except Exception as e:
        log_warning(f"Fallback individual: {e}")
        return 0.5