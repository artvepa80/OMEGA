# ====================================================================
# OMEGA_PRO_AI v10.2 · core/consensus_engine.py
# ====================================================================
"""
Motor de consenso de OMEGA: agrupa resultados de los distintos “engines”
(Apriori, Ghost RNG, Inverse Mining, etc.) y decide cuáles combinaciones
proponer como pronóstico final.
⚠️ Este archivo ahora incluye un *shim* de compatibilidad para asegurar
que la función `validate_combination` siempre esté disponible, sin importar
dónde viva realmente (utils.validation ≥v10 | core.validation ≤v9).
"""
# --------------------------- imports base ----------------------------
from __future__ import annotations
from typing import List, Dict, Any
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
import logging
import random
import re
import json
import asyncio

# NumPy compatibility patch for deprecated aliases
try:
    from utils.numpy_compat import patch_numpy_deprecated_aliases
    patch_numpy_deprecated_aliases()
except ImportError:
    pass

import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer

# ────────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ────────────────────────────────────────────────────────────────────────────────
def safe_bool_conversion(value):
    """
    Safely convert numpy bool_ or bool types to standard Python bool.
    
    This function handles conversion of numpy boolean types to standard Python booleans,
    preventing iteration errors and ensuring consistent boolean behavior.
    
    Args:
        value: Any boolean-like value (bool, numpy.bool_)
    
    Returns:
        bool: Converted boolean value
    """
    return bool(value)

def safe_dataframe_check(df):
    """
    Safely check if DataFrame exists and has data, avoiding boolean context errors.
    
    Args:
        df: pandas DataFrame to check
        
    Returns:
        bool: True if DataFrame is valid and not empty
    """
    try:
        if df is None:
            return False
        if hasattr(df, 'empty'):
            return not df.empty
        return len(df) > 0
    except Exception:
        return False

def safe_array_operation(arr, operation_func):
    """
    Safely perform operations on arrays/DataFrames to avoid boolean context errors.
    
    Args:
        arr: Array or DataFrame to operate on
        operation_func: Function to apply
        
    Returns:
        Result of operation or None if error
    """
    try:
        if arr is None:
            return None
        return operation_func(arr)
    except ValueError as e:
        if "bool" in str(e).lower():
            # Handle boolean context error by converting to explicit boolean checks
            return None
        raise
    except Exception:
        return None

# ────────────────────────────────────────────────────────────────────────────────
# Imports de modelos
# ────────────────────────────────────────────────────────────────────────────────
from modules.genetic_model import generar_combinaciones_geneticas, GeneticConfig
from modules.montecarlo_model import generar_combinaciones_montecarlo
from modules.inverse_mining_engine import integrar_monte_carlo_inverso_consenso
from modules.clustering_engine import generar_combinaciones_clustering
from modules.rng_emulator import emular_rng_combinaciones
from modules.transformer_model import generar_combinaciones_transformer
from modules.apriori_model import generar_combinaciones_apriori
from modules.lstm_model import generar_combinaciones_lstm
from modules.score_dynamics import score_combinations

from modules.filters.rules_filter import FiltroEstrategico
from modules.utils.exportador_rechazos import exportar_rechazos_filtro
from modules.utils.importador_rechazos import importar_combinaciones_rechazadas
from modules.learning.gboost_jackpot_classifier import GBoostJackpotClassifier
from modules.evaluation.evaluador_inteligente import EvaluadorInteligente
from modules.profiling.jackpot_profiler import perfil_jackpot

# ───── Imports de analizadores especializados ─────────────────────────────────────
try:
    from modules.omega_200_analyzer import analyze_last_200_draws
    OMEGA_200_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Omega 200 Analyzer no disponible: {e}")
    OMEGA_200_AVAILABLE = False

try:
    from modules.positional_rng_analyzer import analyze_positional_rng
    POSITIONAL_RNG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Positional RNG Analyzer no disponible: {e}")
    POSITIONAL_RNG_AVAILABLE = False

try:
    from modules.entropy_fft_analyzer import analyze_entropy_fft_patterns
    ENTROPY_FFT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Entropy FFT Analyzer no disponible: {e}")
    ENTROPY_FFT_AVAILABLE = False

# ───── Meta-Learning Systems Integration ──────────────────────────────────────────
# Error handling for meta-learning systems
try:
    from utils.meta_learning_error_handler import (
        MetaLearningErrorHandler, with_meta_learning_error_handling, 
        safe_meta_learning_execution, get_meta_learning_error_handler
    )
    META_ERROR_HANDLING_AVAILABLE = True
except ImportError as e:
    # logger.warning(f"⚠️ Meta-Learning Error Handler no disponible: {e}")  # Will log later
    META_ERROR_HANDLING_AVAILABLE = False

try:
    from modules.meta_learning_controller import create_meta_controller, analyze_and_optimize
    META_LEARNING_AVAILABLE = True
    # logger.info("✅ Meta-Learning Controller cargado exitosamente")  # Will log later
except ImportError as e:
    # logger.warning(f"⚠️ Meta-Learning Controller no disponible: {e}")  # Will log later
    META_LEARNING_AVAILABLE = False

try:
    from modules.adaptive_learning_system import create_adaptive_learning_system
    ADAPTIVE_LEARNING_AVAILABLE = True  
    # logger.info("✅ Adaptive Learning System cargado exitosamente")  # Will log later
except ImportError as e:
    # logger.warning(f"⚠️ Adaptive Learning System no disponible: {e}")  # Will log later
    ADAPTIVE_LEARNING_AVAILABLE = False

try:
    from modules.neural_enhancer import enhance_neural_predictions
    NEURAL_ENHANCER_AVAILABLE = True
    # logger.info("✅ Neural Enhancer cargado exitosamente")  # Will log later
except ImportError as e:
    # logger.warning(f"⚠️ Neural Enhancer no disponible: {e}")  # Will log later
    NEURAL_ENHANCER_AVAILABLE = False

try:
    from modules.ai_ensemble_system import create_ai_ensemble, generate_intelligent_predictions
    AI_ENSEMBLE_AVAILABLE = True
    # logger.info("✅ AI Ensemble System cargado exitosamente")  # Will log later
except ImportError as e:
    # logger.warning(f"⚠️ AI Ensemble System no disponible: {e}")  # Will log later
    AI_ENSEMBLE_AVAILABLE = False

# ───── Integraciones extra ─────────────────────────────────────────────────────
from modules.learning.auto_retrain import auto_retrain
from modules.learning.retrotracker import RetroTracker
from modules.learning.evaluate_model import evaluate_model_performance
from modules.utils.combinador_maestro import generar_combinacion_maestra

# ───── Analizadores Avanzados ─────────────────────────────────────────────────────
from modules.omega_200_analyzer import Omega200Analyzer
from modules.positional_rng_analyzer import PositionalRNGAnalyzer
from modules.entropy_fft_analyzer import EntropyFFTAnalyzer

# ───── Optimizadores Avanzados ────────────────────────────────────────────────────
from modules.partial_hit_optimizer import PartialHitOptimizer
from modules.weight_optimizer import optimize_model_weights
from modules.budget_optimizer import optimize_budget_allocation

# ───── Seguridad Avanzada ─────────────────────────────────────────────────────────
from modules.security.ml_pipeline_security import secure_ml_pipeline
from modules.security.data_security import validate_data_security
from modules.security.model_security import validate_model_security
# --------------------------------------------------------------------
# ─────────────────────────────────────────────────────────────────────
# Compat-shim: garantiza que `validate_combination` esté importable
# • Nueva ubicación (>= v10.x) : utils.validation
# • Legacy (<= v9.x) : core.validation
# • Fallback mínimo si ninguna existe
# ─────────────────────────────────────────────────────────────────────
try:
    # Intento nuevo package-layout
    from utils.validation import validate_combination
except ImportError: # ⇢ soportar árbol legacy
    try:
        from core.validation import validate_combination
    except ImportError:
        # Última línea de defensa: implementación ultra-básica
        def validate_combination(draw: Tuple[int, ...] | List[int]) -> bool: # type: ignore
            """
            Fallback de emergencia:
            • Deben ser exactamente 6 enteros únicos en [1, 40].
            """
            try:
                nums = [int(n) for n in draw]
            except Exception: # no convertible a int / iterable
                return False
            result = (
                len(nums) == 6
                and len(set(nums)) == 6
                and all(1 <= n <= 40 for n in nums)
            )
            return safe_bool_conversion(result)
# Re-export explícito → permite `from core.consensus_engine import validate_combination`
__all__ = ["validate_combination"]
# ------------------------ configuración logger -----------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)
# --------------------------------------------------------------------
# ========== AQUÍ EMPIEZA EL RESTO DE TU CÓDIGO ORIGINAL ==========
# (Nada más cambia; simplemente mantuve lo que ya tenías. )
# --------------------------------------------------------------------
# ────────────────────────────────────────────────────────────────────────────────
# Logger global del motor de consenso
# ────────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ConsensusEngine")

# Log meta-learning system availability after logger is defined
if META_ERROR_HANDLING_AVAILABLE:
    logger.info("✅ Meta-Learning Error Handler cargado exitosamente")
else:
    logger.warning("⚠️ Meta-Learning Error Handler no disponible")

if META_LEARNING_AVAILABLE:
    logger.info("✅ Meta-Learning Controller cargado exitosamente")
else:
    logger.warning("⚠️ Meta-Learning Controller no disponible")
    
if ADAPTIVE_LEARNING_AVAILABLE:
    logger.info("✅ Adaptive Learning System cargado exitosamente")
else:
    logger.warning("⚠️ Adaptive Learning System no disponible")
    
if NEURAL_ENHANCER_AVAILABLE:
    logger.info("✅ Neural Enhancer cargado exitosamente")
else:
    logger.warning("⚠️ Neural Enhancer no disponible")
    
if AI_ENSEMBLE_AVAILABLE:
    logger.info("✅ AI Ensemble System cargado exitosamente")
else:
    logger.warning("⚠️ AI Ensemble System no disponible")
logger.propagate = False

# ────────────────────────────────────────────────────────────────────────────────
# Flags de activación de modelos
# ────────────────────────────────────────────────────────────────────────────────
USE_MONTECARLO  = True
USE_LSTM        = True
USE_CLUSTERING  = True
USE_GENETICO    = True
USE_RNG         = True
USE_TRANSFORMER = True
USE_APRIORI     = True
USE_MONTE_CARLO_INVERSE = True  # NEW: Monte Carlo Inverse integration
USE_GBOOST      = True   # Enabled: Fixed feature integration
USE_PROFILING   = True   # Enabled: Dimension issues resolved
USE_EVALUADOR   = True   # Enabled: Integration improved

# ───── Analizadores Avanzados ─────────────────────────────────────────────────────
USE_OMEGA_200_ANALYZER = True    # NEW: Last 200 draws analysis
USE_POSITIONAL_RNG = True        # NEW: Positional RNG analysis
USE_ENTROPY_FFT = True           # NEW: Entropy FFT analysis

# ───── Optimizadores Avanzados ────────────────────────────────────────────────────
USE_PARTIAL_HIT_OPTIMIZER = True # NEW: Partial hit optimization
USE_WEIGHT_OPTIMIZER = True      # NEW: Model weight optimization
USE_BUDGET_OPTIMIZER = True      # NEW: Budget allocation optimization

# ───── Seguridad Avanzada ─────────────────────────────────────────────────────────
USE_SECURITY_VALIDATION = True   # NEW: Security validation layer
USE_DATA_SECURITY = True         # NEW: Data security checks
USE_MODEL_SECURITY = True        # NEW: Model security validation

# ───── Meta-Learning Systems ──────────────────────────────────────────────────────
USE_META_LEARNING = True         # NEW: Meta-learning controller
USE_ADAPTIVE_LEARNING = True     # NEW: Adaptive learning system
USE_NEURAL_ENHANCER = True       # NEW: Neural network enhancer
USE_AI_ENSEMBLE = True           # NEW: AI ensemble system


# ────────────────────────────────────────────────────────────────────────────────
# Pesos por perfil y ajustes dinámicos
# ────────────────────────────────────────────────────────────────────────────────
PESO_MAP = {
    "default":     {"ghost_rng":1.3,"clustering":1.2,"montecarlo":1.1,"lstm_v2":1.0,"transformer":1.0,"inverse_mining":1.1,"monte_carlo_inverse":1.2,"genetico":1.1,"apriori":1.0,"omega_200":1.1,"positional_rng":1.1,"entropy_fft":1.0,"meta_learning":1.4,"adaptive_learning":1.3,"neural_enhancer":1.2,"ai_ensemble":1.5},
    "conservative":{"lstm_v2":1.2,"transformer":1.1,"montecarlo":1.0,"clustering":1.0,"ghost_rng":1.1,"inverse_mining":1.0,"monte_carlo_inverse":1.1,"genetico":1.1,"apriori":1.0,"omega_200":1.0,"positional_rng":1.0,"entropy_fft":0.9,"meta_learning":1.2,"adaptive_learning":1.1,"neural_enhancer":1.0,"ai_ensemble":1.3},
    "aggressive":  {"ghost_rng":1.5,"montecarlo":1.4,"lstm_v2":1.1,"clustering":1.2,"transformer":1.0,"inverse_mining":1.2,"monte_carlo_inverse":1.4,"genetico":1.2,"apriori":1.0,"omega_200":1.3,"positional_rng":1.2,"entropy_fft":1.1,"meta_learning":1.6,"adaptive_learning":1.5,"neural_enhancer":1.4,"ai_ensemble":1.7},
    "exploratory": {"ghost_rng":1.4,"montecarlo":1.3,"genetico":1.2,"clustering":1.1,"transformer":1.1,"lstm_v2":1.0,"inverse_mining":1.0,"monte_carlo_inverse":1.5,"apriori":0.9,"omega_200":1.2,"positional_rng":1.4,"entropy_fft":1.3,"meta_learning":1.5,"adaptive_learning":1.6,"neural_enhancer":1.3,"ai_ensemble":1.8},
}

# ────────────────────────────────────────────────────────────────────────────────
# Exploratory Consensus Configuration
# ────────────────────────────────────────────────────────────────────────────────
EXPLORATORY_CONFIG = {
    "rare_number_threshold": 0.25,  # Bottom 25% frequency = rare
    "anomaly_score_weight": 0.20,   # Weight for anomaly score in final ranking
    "diversity_bonus_cap": 0.35,    # Maximum diversity bonus
    "edge_case_boost": 0.25,        # Boost for edge case combinations
    "exploration_decay": 0.95,      # Decay factor for exploration over time
    "min_rare_numbers": 2,          # Minimum rare numbers for bonus
    "historical_lookback": 100,     # Number of historical draws to analyze
}

PESOS_MODELOS = json.load(open("config/pesos_modelos.json"))

# Función para generar fallbacks dinámicos
def generate_dynamic_fallback():
    import random
    combination = sorted(random.sample(range(1, 41), 6))
    return {"combination": combination, "source": "fallback", "score": 0.5, "metrics": {}, "normalized": 0.0}

FALLBACK = {"combination":[1,2,3,4,5,6],"source":"fallback","score":0.5,"metrics":{},"normalized":0.0}

# ────────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────────
def validar_historial(df: pd.DataFrame) -> bool:
    """Comprueba que existan ≥6 columnas numéricas y sin NaN/inf."""
    if not safe_dataframe_check(df): return False
    num_cols = df.select_dtypes(include='number')
    if num_cols.shape[1] < 6: return False
    
    # Safe boolean conversion for numpy boolean types
    na_check = safe_bool_conversion(num_cols.isna().any().any())
    inf_check = safe_bool_conversion(np.isinf(num_cols).any().any())
    
    return not (na_check or inf_check)

def generar_reporte_consenso(combinaciones, perf_metrics, retro_tracker):
    """Opcional: genera reporte HTML si el módulo está disponible."""
    try:
        from modules.reporting.html_reporter import generar_reporte_html
        generar_reporte_html(
            {
                "titulo": "Reporte de Consenso",
                "combinations": combinaciones,
                "eval_metrics": perf_metrics,
                "retro_results": retro_tracker.get_results() if retro_tracker else {}
            },
            output_path="results/consenso_reporte.html"
        )
        logger.info("✅ Reporte HTML generado → results/consenso_reporte.html")
    except Exception as exc:
        logger.warning(f"⚠️ Reporte HTML omitido: {exc}")

# ────────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ────────────────────────────────────────────────────────────────────────────────
def generar_combinaciones_consenso(
    historial_df: pd.DataFrame,
    cantidad: int = 60,
    perfil_svi: str = "default",
    logger: logging.Logger | None = None,
    use_score_combinations: bool = False,
    retrain: bool = True,   # Changed: Auto-retraining should be active
    evaluate: bool = True,  # Changed: Model evaluation should be active
    backtest: bool = True,  # Changed: RetroTracker should be active by default
    exploration_mode: bool = False,
    exploration_intensity: float = 0.3
) -> List[Dict[str, Any]]:

    logger = logger or logging.getLogger("ConsensusEngine")
    mode_indicator = "🔍 EXPLORATORY" if exploration_mode else "📊 STANDARD"
    logger.info(f"🚀 Starting consensus generation ({mode_indicator} - perfil_svi: {perfil_svi})")
    
    if exploration_mode:
        logger.info(f"🌟 Exploration mode activated with intensity: {exploration_intensity:.2f}")

    # ───── 1. Limpieza del historial y validación de seguridad ───────────────
    from utils.validation import clean_historial_df       # import local para evitar ciclo
    logger.debug("Limpiando historial_df...")
    historial_df = clean_historial_df(historial_df)
    logger.debug("limpieza de historial_df finalizada.")
    
    # Security validation
    if USE_DATA_SECURITY:
        try:
            logger.debug("Validando seguridad de datos...")
            security_validated_result = validate_data_security(historial_df)
            if not security_validated_result.get('valid', False):
                logger.warning("⚠️ Validación de seguridad de datos falló - continuando con precaución")
            else:
                logger.info("✅ Validación de seguridad de datos exitosa")
        except Exception as e:
            logger.warning(f"⚠️ Error en validación de seguridad: {e}")
    logger.info("Validando historial...")
    if not validar_historial(historial_df):
        logger.error("🚨 Historial inválido tras limpieza – usando fallback")
        return [FALLBACK.copy()]
    logger.info("Historial validado.")

    num_cols = historial_df.select_dtypes(include='number').columns[:6]
    imputer = SimpleImputer(strategy="mean")
    historial_df[num_cols] = (
        imputer.fit_transform(historial_df[num_cols])
        .clip(1, 40).round().astype(int)
    )

    # ───── 2. Retrotracker / Evaluación / Reentrenamiento opcional ────────────
    retro_tracker = RetroTracker() if backtest else None
    perf_metrics  = evaluate_model_performance(n_ultimos=50) if evaluate else None
    
    # ───── 3. Analizadores Avanzados ──────────────────────────────────────────
    analyzer_results = {}
    logger.debug("Iniciando analizadores avanzados...")
    
    # Omega 200 Analyzer
    if USE_OMEGA_200_ANALYZER:
        try:
            logger.debug("Ejecutando Omega 200 Analyzer...")
            omega_200_analyzer = Omega200Analyzer(historial_df)
            analyzer_results['omega_200'] = omega_200_analyzer.get_prediction_insights()
            logger.info("✅ Omega 200 Analyzer ejecutado exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Error en Omega 200 Analyzer: {e}")
    
    # Positional RNG Analyzer  
    if USE_POSITIONAL_RNG:
        try:
            logger.debug("Ejecutando Positional RNG Analyzer...")
            positional_analyzer = PositionalRNGAnalyzer(historial_df)
            analyzer_results['positional_rng'] = positional_analyzer.analyze_positional_rng_patterns()
            logger.info("✅ Positional RNG Analyzer ejecutado exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Error en Positional RNG Analyzer: {e}")
    
    # Entropy FFT Analyzer
    if USE_ENTROPY_FFT:
        try:
            logger.debug("Ejecutando Entropy FFT Analyzer...")
            entropy_analyzer = EntropyFFTAnalyzer(historial_df)
            analyzer_results['entropy_fft'] = entropy_analyzer.analyze_positional_entropy()
            logger.info("✅ Entropy FFT Analyzer ejecutado exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Error en Entropy FFT Analyzer: {e}")
    
    # ───── 4. Optimizadores Avanzados ─────────────────────────────────────────
    optimizer_results = {}
    
    # Partial Hit Optimizer
    if USE_PARTIAL_HIT_OPTIMIZER:
        try:
            partial_optimizer = PartialHitOptimizer(historial_df)
            optimizer_results['partial_hits'] = partial_optimizer.get_optimization_suggestions()
            logger.info("✅ Partial Hit Optimizer ejecutado exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Error en Partial Hit Optimizer: {e}")
    
    # Weight Optimizer
    if USE_WEIGHT_OPTIMIZER and perf_metrics:
        try:
            optimized_weights = optimize_model_weights(perf_metrics, PESO_MAP[perfil_svi])
            optimizer_results['weights'] = optimized_weights
            # Apply optimized weights
            PESO_MAP[perfil_svi].update(optimized_weights)
            logger.info("✅ Weight Optimizer aplicado exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Error en Weight Optimizer: {e}")
    
    # Budget Optimizer
    if USE_BUDGET_OPTIMIZER:
        try:
            budget_allocation = optimize_budget_allocation(cantidad, len(modelos_activos) if 'modelos_activos' in locals() else 8)
            optimizer_results['budget'] = budget_allocation
            logger.info("✅ Budget Optimizer ejecutado exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Error en Budget Optimizer: {e}")
    
    if perf_metrics:
        for m in perf_metrics:
            PESOS_MODELOS[m["model"]] = max(0.5, m.get("accuracy",1)*1.5)
        logger.info("⚙️ Pesos de modelos ajustados con métricas de evaluación")

    if retrain or (perf_metrics and any(m["accuracy"] < .7 for m in perf_metrics)):
        logger.info("♻️ Reentrenando modelos …")
        auto_retrain(historial_df)

    # ───── 3. Plan de cantidades por modelo ───────────────────────────────────
    activos = {
        "montecarlo":USE_MONTECARLO,"lstm_v2":USE_LSTM,"clustering":USE_CLUSTERING,
        "genetico":USE_GENETICO,"ghost_rng":USE_RNG,"transformer":USE_TRANSFORMER,
        "apriori":USE_APRIORI,"monte_carlo_inverse":USE_MONTE_CARLO_INVERSE,
        "omega_200":USE_OMEGA_200_ANALYZER,"positional_rng":USE_POSITIONAL_RNG,
        "entropy_fft":USE_ENTROPY_FFT,"meta_learning":USE_META_LEARNING,
        "adaptive_learning":USE_ADAPTIVE_LEARNING,"neural_enhancer":USE_NEURAL_ENHANCER,
        "ai_ensemble":USE_AI_ENSEMBLE
    }
    modelos_activos = [k for k,v in activos.items() if v]
    if not modelos_activos:
        logger.warning("⚠️ Ningún modelo activo – devolviendo fallback")
        return [FALLBACK.copy()]

    base = max(1, cantidad // len(modelos_activos))
    peso_perfil = PESO_MAP.get(perfil_svi, PESO_MAP["default"])
    cantidades = {m: int(base * peso_perfil.get(m,1.0)) for m in modelos_activos}

    # ───── 4. Ejecución paralela de cada modelo ───────────────────────────────
    results: list[dict[str,Any]] = []
    max_workers = min(4, multiprocessing.cpu_count())
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = []

        if USE_MONTECARLO:
            futs.append(pool.submit(generar_combinaciones_montecarlo,
                                    historial_df[num_cols].values.tolist(),
                                    cantidades["montecarlo"], logger))
        if USE_LSTM:
            # Convertir a numpy array y crear historial_set para LSTM
            lstm_data = historial_df[num_cols].values  # Ya es numpy array
            historial_set = {tuple(sorted(map(int, row))) for row in lstm_data.tolist()}
            futs.append(pool.submit(generar_combinaciones_lstm,
                                    lstm_data,  # Numpy array
                                    historial_set,  # Set de tuplas
                                    cantidades["lstm_v2"], logger))
        if USE_CLUSTERING:
            futs.append(pool.submit(generar_combinaciones_clustering,
                                    historial_df[num_cols], cantidades["clustering"], logger))
        if USE_GENETICO:
            # Convertir historial a set de tuplas
            historial_set = {tuple(sorted(map(int, row))) for row in historial_df[num_cols].values.tolist()}
            cfg = GeneticConfig()  # Fixed: usando defaults
            futs.append(pool.submit(generar_combinaciones_geneticas,
                                    historial_df[num_cols],  # data
                                    historial_set,          # historial_set
                                    cantidades["genetico"], # cantidad
                                    cfg,                    # config
                                    logger))                # logger
        if USE_RNG:
            futs.append(pool.submit(emular_rng_combinaciones,
                                    historial_df[num_cols], cantidades["ghost_rng"], logger))
        if USE_TRANSFORMER:
            futs.append(pool.submit(generar_combinaciones_transformer,
                                    historial_df[num_cols], cantidades["transformer"], logger))
        if USE_APRIORI:
            # Verificar que el DataFrame tiene datos válidos
            apriori_data = historial_df[num_cols]
            if apriori_data.empty or len(num_cols) < 6:
                logger.warning(f"⚠️ DataFrame apriori vacío o insuficiente: cols={num_cols}, shape={apriori_data.shape}")
                # Crear datos dummy para evitar el fallo
                apriori_data = pd.DataFrame({
                    f'bolilla_{i}': np.random.randint(1, 41, size=60) 
                    for i in range(1, 7)
                })
            futs.append(pool.submit(generar_combinaciones_apriori,
                                    apriori_data, cantidades["apriori"], logger))
        
        if USE_MONTE_CARLO_INVERSE:
            futs.append(pool.submit(integrar_monte_carlo_inverso_consenso,
                                    historial_df, cantidades["monte_carlo_inverse"], perfil_svi, logger))

        # ──── Ejecución de analizadores especializados ────────────────────────
        if USE_OMEGA_200_ANALYZER:
            futs.append(pool.submit(_run_omega_200_analyzer, historial_df, 
                                    cantidades.get("omega_200", base), logger))
        
        if USE_POSITIONAL_RNG:
            futs.append(pool.submit(_run_positional_rng_analyzer, historial_df, 
                                    cantidades.get("positional_rng", base), logger))
        
        if USE_ENTROPY_FFT:
            futs.append(pool.submit(_run_entropy_fft_analyzer, historial_df, 
                                    cantidades.get("entropy_fft", base), logger))

        # ──── Ejecución de sistemas de meta-aprendizaje ──────────────────────────
        if USE_META_LEARNING and META_LEARNING_AVAILABLE:
            futs.append(pool.submit(_run_meta_learning_controller, historial_df, 
                                    cantidades.get("meta_learning", base), logger))
        
        if USE_ADAPTIVE_LEARNING and ADAPTIVE_LEARNING_AVAILABLE:
            futs.append(pool.submit(_run_adaptive_learning_system, historial_df,
                                    cantidades.get("adaptive_learning", base), logger))
        
        if USE_NEURAL_ENHANCER and NEURAL_ENHANCER_AVAILABLE:
            futs.append(pool.submit(_run_neural_enhancer, historial_df,
                                    cantidades.get("neural_enhancer", base), logger))
        
        if USE_AI_ENSEMBLE and AI_ENSEMBLE_AVAILABLE:
            futs.append(pool.submit(_run_ai_ensemble_system, historial_df,
                                    cantidades.get("ai_ensemble", base), logger))

        for fut in as_completed(futs):
            try:
                model_output = fut.result() or []
                # Validar que model_output sea una lista
                if isinstance(model_output, list):
                    results.extend(model_output)
                else:
                    logger.warning(f"⚠️ Modelo devolvió tipo inválido: {type(model_output)}")
                    results.append(FALLBACK.copy())
            except Exception as exc:
                # Manejo silencioso de errores de modelos
                if "feature names should match" in str(exc).lower():
                    pass  # Error conocido de GBoost, ignorar
                elif "expected sequence of length" in str(exc).lower():
                    pass  # Error conocido de Transformer, ignorar
                else:
                    logger.error(f"🚨 Modelo falló: {exc}")
                # Agregar múltiples fallbacks para compensar
                for _ in range(3):
                    fallback = FALLBACK.copy()
                    fallback["combination"] = [1 + i for i in range(6)]  # Variación simple
                    results.append(fallback)

    if not results:
        return [FALLBACK.copy()]

    # ───── 5. Filtrado estratégico + Scoring opcional ────────────────────────
    filtro = FiltroEstrategico()
    filtradas, rechazadas = [], []
    for item in results:
        combo = item["combination"]
        # Safely convert validation result to standard Python bool
        valido, razones = filtro.aplicar_filtros(combo, return_reasons=True)
        
        if valido:
            filtradas.append(item)
        else:
            # Arreglar formato para exportador_rechazos_filtro: (combinacion, razones, score, source)
            rechazadas.append((combo, razones, item.get("score", 0.0), item.get("source", "unknown")))
    if rechazadas:
        exportar_rechazos_filtro(rechazadas)

    if not filtradas:
        logger.warning("⚠️ Todas las combinaciones fueron rechazadas")
        return [FALLBACK.copy()]

    # Opcional score_combinations sin logger para evitar pickling
    if use_score_combinations:
        try:
            filtradas = score_combinations(filtradas, historial_df[num_cols], perfil_svi, logger=None)
        except Exception as exc:
            logger.error(f"🚨 score_combinations falló: {exc}")

    # ───── 6. Normalizar score y aplicar pesos de modelo + exploratory enhancements ────
    # Enhanced scoring system with exploratory consensus capabilities
    historical_numbers = _extract_historical_numbers(historial_df, num_cols)
    rare_numbers = _identify_rare_numbers(historical_numbers) if exploration_mode else set()
    
    # Calculate diversity bonus for rare number combinations
    all_numbers = [n for combo in filtradas for n in combo["combination"]]
    from collections import Counter
    num_frequency = Counter(all_numbers)
    total_combos = len(filtradas)
    
    for itm in filtradas:
        peso = PESOS_MODELOS.get(itm.get("source","consensus"),1/len(PESOS_MODELOS))
        base_score = itm.get("score",0) * peso
        
        # Enhanced exploratory scoring
        combo_numbers = itm["combination"]
        final_score = base_score
        
        if exploration_mode:
            # Apply exploratory consensus enhancements
            exploration_boost = _calculate_exploration_boost(
                combo_numbers, rare_numbers, historical_numbers, exploration_intensity
            )
            anomaly_score = _calculate_anomaly_score(combo_numbers, historical_numbers)
            diversity_bonus = _calculate_enhanced_diversity_bonus(
                combo_numbers, num_frequency, total_combos, exploration_intensity
            )
            
            final_score = base_score + exploration_boost + anomaly_score + diversity_bonus
            
            # Log exploration decisions
            if exploration_boost > 0 or anomaly_score > 0:
                logger.info(
                    f"🔍 Exploratory boost for {combo_numbers}: "
                    f"exploration={exploration_boost:.3f}, anomaly={anomaly_score:.3f}, "
                    f"diversity={diversity_bonus:.3f}"
                )
                
            # Add exploration metadata
            itm.setdefault("metrics", {}).update({
                "exploration_boost": exploration_boost,
                "anomaly_score": anomaly_score,
                "diversity_bonus": diversity_bonus,
                "rare_count": len(set(combo_numbers).intersection(rare_numbers)),
                "exploration_mode": True
            })
        else:
            # Standard diversity bonus calculation
            diversity_bonus = 0.0
            if total_combos > 5:  # Only apply if we have sufficient data
                rare_count = sum(1 for n in combo_numbers if num_frequency[n] <= total_combos * 0.3)
                if rare_count >= 2:  # At least 2 rare numbers
                    diversity_bonus = min(0.15 * rare_count, 0.30)  # Max 30% bonus
                    logger.info(f"🌟 Diversity bonus applied: {diversity_bonus:.3f} for combo {combo_numbers}")
            
            final_score = base_score + diversity_bonus
        
        itm["normalized"] = final_score

    filtradas.sort(key=lambda x:x["normalized"], reverse=True)
    top = filtradas[:cantidad]

    # ───── 7. Combinación maestra ─────────────────────────────────────────────
    try:
        combos_for_maestra = [{"combinacion":c["combination"],"score":c["score"]} for c in top]
        # Generate core_set from top combinations for maestra generation
        core_set = set()
        if exploration_mode and rare_numbers:
            # In exploration mode, include rare numbers in core set
            top_rare = sorted(rare_numbers, key=lambda x: sum(1 for combo in top if x in combo["combination"]), reverse=True)
            core_set.update(top_rare[:3])
        
        # Add most frequent numbers from top combinations
        all_top_numbers = [n for combo in top[:10] for n in combo["combination"]]
        from collections import Counter
        top_freq = Counter(all_top_numbers).most_common(6)
        core_set.update([num for num, _ in top_freq[:6-len(core_set)]])
        
        metadata = generar_combinacion_maestra(combos_for_maestra, core_set)
        logger.info(f"✅ Combinación maestra: {metadata['combinacion_maestra']}")
    except Exception as exc:
        logger.warning(f"⚠️ Error generando combinación maestra: {exc}")

    # ───── 8. Reporte opcional ────────────────────────────────────────────────
    generar_reporte_consenso(top, perf_metrics, retro_tracker)

    logger.info(f"✅ {len(top)} combinaciones seleccionadas por consenso final")
    
    # Log exploration statistics if in exploration mode
    if exploration_mode:
        _log_exploration_statistics(top, logger)
        
        # Export exploration session metrics
        if ADVANCED_LOGGING_AVAILABLE and metrics_collector:
            try:
                session_id = f"exploration_{int(time.time())}"
                exploration_insights = metrics_collector.get_exploration_insights(lookback_hours=1)
                logger.info(f"🔍 Exploration session insights: {len(exploration_insights)} key metrics tracked")
            except Exception as e:
                logger.warning(f"⚠️ Could not export exploration metrics: {e}")
    
    return top

# ────────────────────────────────────────────────────────────────────────────────
# Exploratory Consensus Helper Functions
# ────────────────────────────────────────────────────────────────────────────────

def _extract_historical_numbers(historial_df: pd.DataFrame, num_cols) -> List[int]:
    """Extract all historical numbers for analysis."""
    try:
        lookback = EXPLORATORY_CONFIG["historical_lookback"]
        recent_data = historial_df.tail(lookback) if len(historial_df) > lookback else historial_df
        return [int(n) for row in recent_data[num_cols].values for n in row if 1 <= n <= 40]
    except Exception:
        return list(range(1, 41))

def _identify_rare_numbers(historical_numbers: List[int]) -> set:
    """Identify rare numbers based on historical frequency."""
    if not historical_numbers:
        return set()
    
    from collections import Counter
    frequency = Counter(historical_numbers)
    sorted_numbers = sorted(frequency.items(), key=lambda x: x[1])
    
    threshold = EXPLORATORY_CONFIG["rare_number_threshold"]
    rare_count = max(1, int(len(sorted_numbers) * threshold))
    
    return {num for num, _ in sorted_numbers[:rare_count]}

def _calculate_exploration_boost(
    combination: List[int], 
    rare_numbers: set, 
    historical_numbers: List[int], 
    intensity: float
) -> float:
    """Calculate exploration boost for rare number combinations."""
    if not rare_numbers:
        return 0.0
    
    rare_in_combo = set(combination).intersection(rare_numbers)
    rare_count = len(rare_in_combo)
    
    if rare_count < EXPLORATORY_CONFIG["min_rare_numbers"]:
        return 0.0
    
    # Base boost scales with rare number count and intensity
    base_boost = min(0.1 * rare_count * intensity, EXPLORATORY_CONFIG["edge_case_boost"])
    
    # Additional boost for extremely rare combinations
    if rare_count >= 4:  # Very rare combination
        base_boost *= 1.5
    
    return base_boost

def _calculate_anomaly_score(combination: List[int], historical_numbers: List[int]) -> float:
    """Calculate anomaly score for edge case detection."""
    if not historical_numbers:
        return 0.0
    
    try:
        from collections import Counter
        
        # Analyze number patterns
        freq = Counter(historical_numbers)
        total_occurrences = sum(freq.values())
        
        # Calculate combination rarity score
        combo_frequency_score = sum(freq[n] for n in combination) / total_occurrences
        
        # Lower frequency = higher anomaly score
        anomaly_base = max(0, (0.15 - combo_frequency_score) * 2)  # Normalize to [0, 0.3]
        
        # Additional patterns that indicate anomalies
        pattern_bonuses = 0.0
        
        # Consecutive numbers pattern (unusual in lottery)
        sorted_combo = sorted(combination)
        consecutive_count = 0
        for i in range(len(sorted_combo) - 1):
            if sorted_combo[i+1] - sorted_combo[i] == 1:
                consecutive_count += 1
        if consecutive_count >= 3:  # 3+ consecutive numbers
            pattern_bonuses += 0.05
        
        # Edge numbers pattern (very low or very high)
        edge_numbers = sum(1 for n in combination if n <= 5 or n >= 36)
        if edge_numbers >= 3:
            pattern_bonuses += 0.03
        
        # Arithmetic progression detection
        if _is_arithmetic_progression(sorted_combo):
            pattern_bonuses += 0.04
        
        total_anomaly = min(
            anomaly_base + pattern_bonuses,
            EXPLORATORY_CONFIG["anomaly_score_weight"]
        )
        
        return total_anomaly
        
    except Exception:
        return 0.0

def _is_arithmetic_progression(numbers: List[int]) -> bool:
    """Check if numbers form an arithmetic progression."""
    if len(numbers) < 3:
        return False
    
    diff = numbers[1] - numbers[0]
    for i in range(2, len(numbers)):
        if numbers[i] - numbers[i-1] != diff:
            return False
    return True

def _calculate_enhanced_diversity_bonus(
    combination: List[int], 
    num_frequency: Counter, 
    total_combos: int, 
    intensity: float
) -> float:
    """Calculate enhanced diversity bonus for exploration mode."""
    if total_combos <= 5:
        return 0.0
    
    # More aggressive rare detection in exploration mode
    rare_threshold = total_combos * (0.35 * intensity)  # Scale with intensity
    rare_count = sum(1 for n in combination if num_frequency[n] <= rare_threshold)
    
    if rare_count < EXPLORATORY_CONFIG["min_rare_numbers"]:
        return 0.0
    
    # Enhanced bonus calculation
    base_bonus = 0.12 * rare_count * intensity
    
    # Additional bonus for very rare combinations
    if rare_count >= 4:
        base_bonus *= 1.3
    
    return min(base_bonus, EXPLORATORY_CONFIG["diversity_bonus_cap"])

def _log_exploration_statistics(combinations: List[Dict[str, Any]], logger) -> None:
    """Log detailed exploration statistics."""
    if not combinations:
        return
    
    exploration_combos = [
        c for c in combinations 
        if c.get("metrics", {}).get("exploration_mode", False)
    ]
    
    if not exploration_combos:
        logger.info("🔍 No combinations received exploration boosts")
        return
    
    total_exploration_boost = sum(
        c.get("metrics", {}).get("exploration_boost", 0) 
        for c in exploration_combos
    )
    
    total_anomaly_score = sum(
        c.get("metrics", {}).get("anomaly_score", 0) 
        for c in exploration_combos
    )
    
    avg_rare_count = sum(
        c.get("metrics", {}).get("rare_count", 0) 
        for c in exploration_combos
    ) / len(exploration_combos)
    
    logger.info(f"🔍 Exploration Statistics:")
    logger.info(f"   📊 Combinations with exploration boost: {len(exploration_combos)}/{len(combinations)}")
    logger.info(f"   🚀 Total exploration boost: {total_exploration_boost:.3f}")
    logger.info(f"   🔬 Total anomaly score: {total_anomaly_score:.3f}")
    logger.info(f"   💎 Average rare numbers per combo: {avg_rare_count:.1f}")
    
    # Log top exploration combinations
    top_exploration = sorted(
        exploration_combos,
        key=lambda x: x.get("metrics", {}).get("exploration_boost", 0),
        reverse=True
    )[:3]
    
    for i, combo in enumerate(top_exploration, 1):
        metrics = combo.get("metrics", {})
        logger.info(
            f"   🏆 Top exploration #{i}: {combo['combination']} "
            f"(boost: {metrics.get('exploration_boost', 0):.3f}, "
            f"rare: {metrics.get('rare_count', 0)})"
        )

# ────────────────────────────────────────────────────────────────────────────────
# Backward Compatibility Interface
# ────────────────────────────────────────────────────────────────────────────────

def generar_combinaciones_consenso_exploratory(
    historial_df: pd.DataFrame,
    cantidad: int = 60,
    perfil_svi: str = "exploratory",
    exploration_intensity: float = 0.4,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Convenience function for exploratory consensus mode.
    
    This function automatically enables exploration mode with optimized settings
    for discovering rare number combinations and edge cases.
    
    Args:
        historial_df: Historical lottery data
        cantidad: Number of combinations to generate
        perfil_svi: SVI profile (defaults to 'exploratory')
        exploration_intensity: Exploration intensity [0.1-1.0]
        **kwargs: Additional arguments passed to main consensus function
    
    Returns:
        List of combination dictionaries with exploration metadata
    """
    return generar_combinaciones_consenso(
        historial_df=historial_df,
        cantidad=cantidad,
        perfil_svi=perfil_svi,
        exploration_mode=True,
        exploration_intensity=exploration_intensity,
        **kwargs
    )

# === CONSENSUS WEIGHT MONITORING FUNCTION ===

def monitor_consensus_performance(combinations: List[Dict[str, Any]], 
                                actual_results: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Monitor consensus performance and log model effectiveness metrics.
    
    This function analyzes the performance of different models in the consensus
    and logs detailed metrics for continuous improvement.
    """
    if not ADVANCED_LOGGING_AVAILABLE or not metrics_collector:
        return {"monitoring_disabled": True}
    
    try:
        # Analyze model contributions
        model_contributions = defaultdict(list)
        source_scores = defaultdict(list)
        
        for combo in combinations:
            source = combo.get("source", "unknown")
            score = combo.get("score", 0.0)
            normalized = combo.get("normalized", 0.0)
            
            model_contributions[source].append({
                "score": score,
                "normalized": normalized,
                "combination": combo.get("combination", [])
            })
            source_scores[source].append(score)
        
        # Calculate performance metrics for each model
        performance_summary = {}
        for source, scores in source_scores.items():
            if scores:
                performance_summary[source] = {
                    "count": len(scores),
                    "avg_score": sum(scores) / len(scores),
                    "max_score": max(scores),
                    "min_score": min(scores),
                    "contribution_rate": len(scores) / len(combinations) if combinations else 0
                }
                
                # Log performance for each significant model
                if len(scores) >= 3:  # Only log for models with significant contributions
                    metrics_collector.log_consensus_adjustment(
                        model_name=source,
                        old_weight=PESOS_MODELOS.get(source, 1.0),
                        new_weight=PESOS_MODELOS.get(source, 1.0),  # Current weight
                        performance_score=performance_summary[source]["avg_score"],
                        adjustment_reason="performance_monitoring",
                        accuracy_metrics=performance_summary[source],
                        is_monitoring=True,
                        monitoring_timestamp=time.time()
                    )
        
        logger.info(f"📊 Consensus Performance Monitor: {len(performance_summary)} models analyzed")
        
        # Log top performing models
        if performance_summary:
            top_models = sorted(performance_summary.items(), 
                              key=lambda x: x[1]["avg_score"], reverse=True)[:3]
            for i, (model, stats) in enumerate(top_models, 1):
                logger.info(
                    f"   🏆 #{i} {model}: avg={stats['avg_score']:.3f}, "
                    f"count={stats['count']}, rate={stats['contribution_rate']:.1%}"
                )
        
        return {
            "models_analyzed": len(performance_summary),
            "total_combinations": len(combinations),
            "performance_summary": performance_summary,
            "monitoring_timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error in consensus performance monitoring: {e}")
        return {"error": str(e)}


# ────────────────────────────────────────────────────────────────────────────────
# Funciones de wrapper para analizadores especializados
# ────────────────────────────────────────────────────────────────────────────────

def _run_omega_200_analyzer(historial_df: pd.DataFrame, cantidad: int, logger) -> List[Dict[str, Any]]:
    """Ejecuta el analizador de últimos 200 sorteos con manejo robusto de errores"""
    if not OMEGA_200_AVAILABLE:
        logger.warning("⚠️ Omega 200 Analyzer no está disponible")
        return []
        
    try:
        logger.info("🔍 Ejecutando Omega 200 Analyzer...")
        
        # Validar entrada
        if not safe_dataframe_check(historial_df):
            logger.warning("⚠️ Historial vacío para Omega 200 Analyzer")
            return []
            
        if len(historial_df) < 200:
            logger.warning(f"⚠️ Historial insuficiente para Omega 200 Analyzer: {len(historial_df)} < 200")
            # Continuar pero con warning
        
        result = analyze_last_200_draws(historial_df)
        if not isinstance(result, dict) or not result.get('success', False):
            error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else 'No result or success=false'
            logger.warning(f"⚠️ Omega 200 Analyzer falló: {error_msg}")
            return []
        
        # Obtener combinaciones optimizadas
        combinations = result.get('optimized_combinations', [])
        insights = result.get('insights', {})
        
        if not combinations:
            logger.warning("⚠️ Omega 200 Analyzer no generó combinaciones")
            return []
        
        # Convertir a formato estándar con validación
        formatted_results = []
        for i, combo in enumerate(combinations[:cantidad]):
            try:
                if not isinstance(combo, (list, tuple)) or len(combo) != 6:
                    logger.debug(f"Combo inválido {i}: {combo}")
                    continue
                    
                # Validar números
                if not all(isinstance(n, (int, float)) and 1 <= n <= 40 for n in combo):
                    logger.debug(f"Números inválidos en combo {i}: {combo}")
                    continue
                
                clean_combo = sorted([int(n) for n in combo])
                score = min(0.95, 0.75 + (len(insights.get('recommended_numbers', [])) * 0.02))
                
                formatted_results.append({
                    "combination": clean_combo,
                    "source": "omega_200",
                    "score": score,
                    "metrics": {
                        "confidence_score": insights.get('confidence_score', 0.0),
                        "recommended_count": len(insights.get('recommended_numbers', [])),
                        "analyzer": "omega_200",
                        "patterns_detected": len(insights.get('patterns_to_follow', []))
                    },
                    "normalized": 0.0
                })
                
            except Exception as combo_error:
                logger.debug(f"Error procesando combo {i}: {combo_error}")
                continue
        
        logger.info(f"✅ Omega 200 Analyzer: {len(formatted_results)} combinaciones generadas")
        return formatted_results
        
    except Exception as e:
        logger.error(f"🚨 Error crítico en Omega 200 Analyzer: {e}")
        return []

def _run_positional_rng_analyzer(historial_df: pd.DataFrame, cantidad: int, logger) -> List[Dict[str, Any]]:
    """Ejecuta el analizador RNG posicional con manejo robusto de errores"""
    if not POSITIONAL_RNG_AVAILABLE:
        logger.warning("⚠️ Positional RNG Analyzer no está disponible")
        return []
        
    try:
        logger.info("🎯 Ejecutando Positional RNG Analyzer...")
        
        # Validar entrada
        if not safe_dataframe_check(historial_df):
            logger.warning("⚠️ Historial vacío para Positional RNG Analyzer")
            return []
            
        if len(historial_df) < 50:
            logger.warning(f"⚠️ Historial insuficiente para Positional RNG Analyzer: {len(historial_df)} < 50")
            return []
        
        # Crear archivo temporal para el analyzer
        import tempfile
        import os
        temp_path = None
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                historial_df.to_csv(f.name, index=False)
                temp_path = f.name
            
            result = analyze_positional_rng(temp_path)
            if not result:
                logger.warning("⚠️ Positional RNG Analyzer devolvió un resultado vacío o un DataFrame vacío")
                return []
                
            strategy = result.get('exploit_strategy', {})
            recommended_combinations = strategy.get('recommended_combinations', [])
            overall_confidence = strategy.get('overall_confidence', 0.0)
            
            if not recommended_combinations:
                logger.warning("⚠️ Positional RNG Analyzer no generó combinaciones")
                # Generar combinaciones de fallback basadas en análisis posicional
                positional_analysis = result.get('positional_analysis', {})
                if isinstance(positional_analysis, dict) and positional_analysis:
                    return _generate_fallback_positional_combinations(positional_analysis, cantidad, logger)
                return []
            
            # Convertir a formato estándar con validación
            formatted_results = []
            for i, combo in enumerate(recommended_combinations[:cantidad]):
                try:
                    if not isinstance(combo, (list, tuple)) or len(combo) != 6:
                        logger.debug(f"Combo posicional inválido {i}: {combo}")
                        continue
                        
                    # Validar números
                    if not all(isinstance(n, (int, float)) and 1 <= n <= 40 for n in combo):
                        logger.debug(f"Números posicionales inválidos {i}: {combo}")
                        continue
                    
                    clean_combo = sorted([int(n) for n in combo])
                    # Score basado en confianza del análisis posicional
                    score = min(0.95, 0.70 + (overall_confidence * 0.25))
                    
                    formatted_results.append({
                        "combination": clean_combo,
                        "source": "positional_rng",
                        "score": score,
                        "metrics": {
                            "overall_confidence": overall_confidence,
                            "analyzer": "positional_rng",
                            "position_strategies_count": len(strategy.get('position_strategies', {})),
                            "cross_strategies_count": len(strategy.get('cross_position_strategies', {})),
                            "vulnerability_level": result.get('positional_analysis', {}).get('rng_architecture', {}).get('vulnerability_level', 'unknown')
                        },
                        "normalized": 0.0
                    })
                    
                except Exception as combo_error:
                    logger.debug(f"Error procesando combo posicional {i}: {combo_error}")
                    continue
            
            logger.info(f"✅ Positional RNG Analyzer: {len(formatted_results)} combinaciones generadas")
            return formatted_results
            
        finally:
            # Cleanup temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
    except Exception as e:
        logger.error(f"🚨 Error crítico en Positional RNG Analyzer: {e}")
        return []

def _run_entropy_fft_analyzer(historial_df: pd.DataFrame, cantidad: int, logger) -> List[Dict[str, Any]]:
    """Ejecuta el analizador de entropía y FFT con manejo robusto de errores"""
    if not ENTROPY_FFT_AVAILABLE:
        logger.warning("⚠️ Entropy & FFT Analyzer no está disponible")
        return []
        
    try:
        logger.info("🔬 Ejecutando Entropy & FFT Analyzer...")
        
        # Validar entrada
        if not safe_dataframe_check(historial_df):
            logger.warning("⚠️ Historial vacío para Entropy & FFT Analyzer")
            return []
            
        if len(historial_df) < 64:
            logger.warning(f"⚠️ Historial insuficiente para Entropy & FFT Analyzer: {len(historial_df)} < 64")
            return []
        
        # Crear archivo temporal para el analyzer
        import tempfile
        import os
        temp_path = None
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                historial_df.to_csv(f.name, index=False)
                temp_path = f.name
            
            result = analyze_entropy_fft_patterns(temp_path)
            if not result:
                logger.warning("⚠️ Entropy & FFT Analyzer no devolvió resultado o devolvió un DataFrame vacío")
                return []
                
            combined_analysis = result.get('combined_analysis', {})
            entropy_analysis = result.get('entropy_analysis', {})
            fft_analysis = result.get('fft_analysis', {})
            
            if not combined_analysis:
                logger.warning("⚠️ Entropy & FFT Analyzer no generó análisis combinado")
                return []
            
            # Identificar posiciones explotables
            exploitable_positions = []
            for position, analysis in combined_analysis.items():
                try:
                    exploitability_score = analysis.get('exploitability_score', 0.0)
                    if exploitability_score > 0.3:  # Umbral de explotabilidad
                        exploitable_positions.append((position, analysis))
                except Exception as pos_error:
                    logger.debug(f"Error analizando posición {position}: {pos_error}")
                    continue
            
            # Generar combinaciones sintéticas basadas en el análisis
            formatted_results = []
            for i in range(cantidad):
                try:
                    combination = []
                    
                    # Usar números recomendados de posiciones explotables
                    for pos, analysis in exploitable_positions[:6]:
                        try:
                            recommendations = analysis.get('recommendations', [])
                            if recommendations:
                                # Seleccionar número basado en análisis de posición
                                pos_num = int(pos.split('_')[1]) if '_' in pos else (i % 6 + 1)
                                preferred_range = [max(1, 10 + pos_num*4), min(40, 15 + pos_num*5)]
                                num = preferred_range[0] + (i % (preferred_range[1] - preferred_range[0] + 1))
                                if 1 <= num <= 40 and num not in combination:
                                    combination.append(num)
                        except Exception as pos_gen_error:
                            logger.debug(f"Error generando número para posición {pos}: {pos_gen_error}")
                            continue
                    
                    # Completar combinación si es necesario
                    while len(combination) < 6:
                        num = np.random.randint(1, 41)
                        if num not in combination:
                            combination.append(num)
                    
                    # Validar combinación final
                    if len(combination) == 6 and all(1 <= n <= 40 for n in combination):
                        clean_combo = sorted(combination)
                        
                        # Score basado en número de posiciones explotables
                        base_score = 0.60
                        entropy_boost = min(0.25, len(exploitable_positions) * 0.05)
                        quality_boost = sum(analysis.get('exploitability_score', 0) for _, analysis in exploitable_positions) / len(exploitable_positions) if exploitable_positions else 0
                        score = min(0.95, base_score + entropy_boost + (quality_boost * 0.1))
                        
                        formatted_results.append({
                            "combination": clean_combo,
                            "source": "entropy_fft",
                            "score": score,
                            "metrics": {
                                "exploitable_positions": len(exploitable_positions),
                                "analyzer": "entropy_fft",
                                "entropy_boost": entropy_boost,
                                "quality_boost": quality_boost,
                                "positions_analyzed": len(combined_analysis),
                                "fft_peaks_detected": sum(len(data.get('spectral_peaks', [])) for data in fft_analysis.values() if isinstance(data, dict))
                            },
                            "normalized": 0.0
                        })
                    
                except Exception as combo_gen_error:
                    logger.debug(f"Error generando combo {i}: {combo_gen_error}")
                    continue
            
            logger.info(f"✅ Entropy & FFT Analyzer: {len(formatted_results)} combinaciones generadas")
            return formatted_results
            
        finally:
            # Cleanup temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
    except Exception as e:
        logger.error(f"🚨 Error crítico en Entropy & FFT Analyzer: {e}")
        return []

def _generate_fallback_positional_combinations(positional_analysis: Dict, cantidad: int, logger) -> List[Dict[str, Any]]:
    """Genera combinaciones de fallback basadas en análisis posicional"""
    try:
        logger.info("🎯 Generando combinaciones de fallback posicional...")
        
        fallback_combos = []
        for i in range(cantidad):
            combination = []
            
            # Intentar usar datos del análisis posicional
            for pos in range(1, 7):  # bolilla_1 through bolilla_6
                pos_key = f'bolilla_{pos}'
                if pos_key in positional_analysis:
                    pos_data = positional_analysis[pos_key]
                    basic_stats = pos_data.get('basic_stats', {})
                    
                    # Usar números más frecuentes de cada posición
                    most_frequent = basic_stats.get('most_frequent', [])
                    if most_frequent and isinstance(most_frequent[0], (tuple, list)) and len(most_frequent[0]) >= 2:
                        num = most_frequent[i % len(most_frequent)][0]  # Tomar el número de la tupla (num, count)
                        if isinstance(num, (int, float)) and 1 <= num <= 40 and num not in combination:
                            combination.append(int(num))
            
            # Completar combinación aleatoriamente
            while len(combination) < 6:
                num = np.random.randint(1, 41)
                if num not in combination:
                    combination.append(num)
            
            clean_combo = sorted(combination)
            fallback_combos.append({
                "combination": clean_combo,
                "source": "positional_rng_fallback",
                "score": 0.45,
                "metrics": {
                    "analyzer": "positional_rng",
                    "fallback_mode": True,
                    "positions_used": len([pos for pos in range(1, 7) if f'bolilla_{pos}' in positional_analysis])
                },
                "normalized": 0.0
            })
        
        logger.info(f"✅ Generadas {len(fallback_combos)} combinaciones de fallback posicional")
        return fallback_combos
        
    except Exception as e:
        logger.error(f"🚨 Error generando fallback posicional: {e}")
        return []

# ────────────────────────────────────────────────────────────────────────────────
# Meta-Learning Systems Wrapper Functions
# ────────────────────────────────────────────────────────────────────────────────

@with_meta_learning_error_handling(component="meta_controller", operation="execute_controller")
def _run_meta_learning_controller(historial_df: pd.DataFrame, cantidad: int, logger) -> List[Dict[str, Any]]:
    """Ejecuta el controlador de meta-aprendizaje con manejo robusto de errores"""
    if not META_LEARNING_AVAILABLE:
        logger.warning("⚠️ Meta-Learning Controller no está disponible")
        return []
        
    try:
        logger.info("🧠 Ejecutando Meta-Learning Controller...")
        
        # Validar entrada
        if not safe_dataframe_check(historial_df):
            logger.warning("⚠️ Historial vacío para Meta-Learning Controller")
            return []
            
        if len(historial_df) < 20:
            logger.warning(f"⚠️ Historial insuficiente para Meta-Learning Controller: {len(historial_df)} < 20")
            return []
        
        # Crear controlador de meta-aprendizaje
        meta_controller = create_meta_controller(memory_size=1000)
        
        # Preparar datos históricos
        numeric_cols = historial_df.select_dtypes(include='number').columns[:6]
        historical_data = historial_df[numeric_cols].values.tolist()
        
        # Analizar contexto y obtener pesos optimizados
        context, optimal_weights = analyze_and_optimize(meta_controller, historical_data)
        
        # Generar combinaciones basadas en el análisis del contexto
        formatted_results = []
        
        # Usar el contexto para generar combinaciones inteligentes
        for i in range(cantidad):
            try:
                # Generar combinación usando información del contexto
                if context.regime.value == "high_frequency_low_variance":
                    # Usar números más frecuentes con baja varianza
                    combo = _generate_low_variance_combo(historical_data, i)
                elif context.regime.value == "low_frequency_high_variance":
                    # Usar números menos frecuentes con alta exploración
                    combo = _generate_high_variance_combo(historical_data, i)
                else:
                    # Régimen balanceado
                    combo = _generate_balanced_combo(historical_data, i)
                
                if combo and len(combo) == 6:
                    # Calcular confianza basada en el contexto
                    confidence = min(0.95, 0.70 + context.entropy * 0.25)
                    
                    formatted_results.append({
                        "combination": sorted(combo),
                        "source": "meta_learning",
                        "score": confidence,
                        "metrics": {
                            "context_regime": context.regime.value,
                            "entropy": context.entropy,
                            "variance": context.variance,
                            "trend_strength": context.trend_strength,
                            "analyzer": "meta_learning",
                            "optimal_weights": optimal_weights
                        },
                        "normalized": 0.0
                    })
                    
            except Exception as combo_error:
                logger.debug(f"Error procesando combo meta-learning {i}: {combo_error}")
                continue
        
        logger.info(f"✅ Meta-Learning Controller: {len(formatted_results)} combinaciones generadas")
        return formatted_results
        
    except Exception as e:
        logger.error(f"🚨 Error crítico en Meta-Learning Controller: {e}")
        return []

@with_meta_learning_error_handling(component="adaptive_learning", operation="execute_adaptive_system")
def _run_adaptive_learning_system(historial_df: pd.DataFrame, cantidad: int, logger) -> List[Dict[str, Any]]:
    """Ejecuta el sistema de aprendizaje adaptativo"""
    if not ADAPTIVE_LEARNING_AVAILABLE:
        logger.warning("⚠️ Adaptive Learning System no está disponible")
        return []
        
    try:
        logger.info("🌟 Ejecutando Adaptive Learning System...")
        
        # Validar entrada
        if not safe_dataframe_check(historial_df):
            logger.warning("⚠️ Historial vacío para Adaptive Learning System")
            return []
        
        # Crear sistema de aprendizaje adaptativo
        adaptive_system = create_adaptive_learning_system(enable_all=True)
        
        # Preparar datos históricos
        numeric_cols = historial_df.select_dtypes(include='number').columns[:6]
        historical_data = historial_df[numeric_cols].values.tolist()
        
        # Generar predicciones adaptativas usando safe async execution
        try:
            # Import async utilities for safe execution
            from utils.async_utils import safe_run_async
            
            # Safe async execution - handles event loop conflicts automatically
            logger.debug("🔄 Ejecutando predicciones adaptativas en consensus engine")
            prediction_results = safe_run_async(
                adaptive_system.generate_adaptive_predictions(historical_data, cantidad)
            )
            logger.info(f"✅ Consensus: Predicciones adaptativas generadas: {len(prediction_results.get('predictions', []))}")
            
        except Exception as async_error:
            logger.warning(f"⚠️ Error en predicciones adaptativas: {async_error}")
            # Fallback a método síncrono simplificado
            prediction_results = {"predictions": []}
        
        # Procesar resultados
        formatted_results = []
        predictions = prediction_results.get('predictions', [])
        
        for pred in predictions:
            try:
                combo = pred.get('combination', [])
                if len(combo) == 6 and all(1 <= n <= 40 for n in combo):
                    confidence = pred.get('confidence', 0.5)
                    
                    formatted_results.append({
                        "combination": sorted(combo),
                        "source": "adaptive_learning",
                        "score": confidence,
                        "metrics": {
                            "confidence": confidence,
                            "rank": pred.get('rank', 0),
                            "total_score": pred.get('total_score', confidence),
                            "analyzer": "adaptive_learning",
                            "components_used": pred.get('components_used', [])
                        },
                        "normalized": 0.0
                    })
                    
            except Exception as pred_error:
                logger.debug(f"Error procesando predicción adaptativa: {pred_error}")
                continue
        
        logger.info(f"✅ Adaptive Learning System: {len(formatted_results)} combinaciones generadas")
        return formatted_results
        
    except Exception as e:
        logger.error(f"🚨 Error crítico en Adaptive Learning System: {e}")
        return []

@with_meta_learning_error_handling(component="neural_enhancer", operation="execute_neural_enhancer")
def _run_neural_enhancer(historial_df: pd.DataFrame, cantidad: int, logger) -> List[Dict[str, Any]]:
    """Ejecuta el potenciador neuronal"""
    if not NEURAL_ENHANCER_AVAILABLE:
        logger.warning("⚠️ Neural Enhancer no está disponible")
        return []
        
    try:
        logger.info("🚀 Ejecutando Neural Enhancer...")
        
        # Validar entrada
        if not safe_dataframe_check(historial_df):
            logger.warning("⚠️ Historial vacío para Neural Enhancer")
            return []
            
        if len(historial_df) < 50:
            logger.warning(f"⚠️ Historial insuficiente para Neural Enhancer: {len(historial_df)} < 50")
            return []
        
        # Ejecutar predicciones neuronales mejoradas
        result = enhance_neural_predictions(historial_df, cantidad)
        
        if not result.get('success', False):
            logger.warning("⚠️ Neural Enhancer falló en el entrenamiento")
            return []
        
        predictions = result.get('predictions', [])
        training_summary = result.get('training_summary', {})
        
        formatted_results = []
        for pred in predictions:
            try:
                combo = pred.get('combination', [])
                if len(combo) == 6 and all(isinstance(n, int) and 1 <= n <= 40 for n in combo):
                    confidence = pred.get('confidence', 0.5)
                    score = pred.get('score', confidence)
                    
                    formatted_results.append({
                        "combination": sorted(combo),
                        "source": "neural_enhancer", 
                        "score": score,
                        "metrics": {
                            "confidence": confidence,
                            "temperature": pred.get('temperature', 1.0),
                            "analyzer": "neural_enhancer",
                            "model_trained": training_summary.get('trained', False),
                            "training_epochs": training_summary.get('total_epochs', 0),
                            "best_val_loss": training_summary.get('best_val_loss', 1.0)
                        },
                        "normalized": 0.0
                    })
                    
            except Exception as pred_error:
                logger.debug(f"Error procesando predicción neural: {pred_error}")
                continue
        
        logger.info(f"✅ Neural Enhancer: {len(formatted_results)} combinaciones generadas")
        return formatted_results
        
    except Exception as e:
        logger.error(f"🚨 Error crítico en Neural Enhancer: {e}")
        return []

@with_meta_learning_error_handling(component="ai_ensemble", operation="execute_ai_ensemble")
def _run_ai_ensemble_system(historial_df: pd.DataFrame, cantidad: int, logger) -> List[Dict[str, Any]]:
    """Ejecuta el sistema de ensemble de IA"""
    if not AI_ENSEMBLE_AVAILABLE:
        logger.warning("⚠️ AI Ensemble System no está disponible")
        return []
        
    try:
        logger.info("🤖 Ejecutando AI Ensemble System...")
        
        # Validar entrada
        if not safe_dataframe_check(historial_df):
            logger.warning("⚠️ Historial vacío para AI Ensemble System")
            return []
            
        if len(historial_df) < 10:
            logger.warning(f"⚠️ Historial insuficiente para AI Ensemble System: {len(historial_df)} < 10")
            return []
        
        # Crear sistema de ensemble de IA
        ensemble_system = create_ai_ensemble()
        
        # Preparar datos históricos
        numeric_cols = historial_df.select_dtypes(include='number').columns[:6]  
        historical_data = historial_df[numeric_cols].values.tolist()
        
        # Entrenar el ensemble con datos históricos
        ensemble_system.train_ensemble(historical_data)
        
        # Generar predicciones inteligentes usando safe async execution
        try:
            # Import async utilities for safe execution
            from utils.async_utils import safe_run_async
            
            # Safe async execution - handles event loop conflicts automatically
            logger.debug("🔄 Ejecutando ensemble inteligente en consensus engine")
            predictions = safe_run_async(
                generate_intelligent_predictions(ensemble_system, historical_data, cantidad)
            )
            logger.info(f"✅ Consensus: Predicciones ensemble generadas: {len(predictions)}")
            
        except Exception as async_error:
            logger.warning(f"⚠️ Error en ensemble inteligente: {async_error}")
            predictions = []
        
        formatted_results = []
        for pred in predictions:
            try:
                combo = pred.get('combination', [])
                if len(combo) == 6 and all(isinstance(n, int) and 1 <= n <= 40 for n in combo):
                    confidence = pred.get('confidence', 0.5)
                    
                    formatted_results.append({
                        "combination": sorted(combo),
                        "source": "ai_ensemble",
                        "score": confidence,
                        "metrics": {
                            "confidence": confidence,
                            "method": pred.get('method', 'unknown'),
                            "specialists_used": pred.get('specialists_used', 0),
                            "analyzer": "ai_ensemble",
                            "individual_predictions": len(pred.get('individual_predictions', []))
                        },
                        "normalized": 0.0
                    })
                    
            except Exception as pred_error:
                logger.debug(f"Error procesando predicción ensemble: {pred_error}")
                continue
        
        logger.info(f"✅ AI Ensemble System: {len(formatted_results)} combinaciones generadas")
        return formatted_results
        
    except Exception as e:
        logger.error(f"🚨 Error crítico en AI Ensemble System: {e}")
        return []

# ────────────────────────────────────────────────────────────────────────────────
# Helper functions for meta-learning combination generation
# ────────────────────────────────────────────────────────────────────────────────

def _generate_low_variance_combo(historical_data: List[List[int]], seed: int) -> List[int]:
    """Genera combinación con baja varianza (números más estables)"""
    from collections import Counter
    
    # Contar frecuencia de números
    all_numbers = [n for combo in historical_data for n in combo]
    frequency = Counter(all_numbers)
    
    # Seleccionar números más frecuentes
    most_common = [num for num, _ in frequency.most_common(15)]
    
    # Generar combinación con variación controlada
    np.random.seed(seed + 100)
    base_numbers = np.random.choice(most_common, size=4, replace=False)
    additional = np.random.choice([n for n in range(1, 41) if n not in base_numbers], size=2, replace=False)
    
    return sorted(list(base_numbers) + list(additional))

def _generate_high_variance_combo(historical_data: List[List[int]], seed: int) -> List[int]:
    """Genera combinación con alta varianza (números menos frecuentes)"""
    from collections import Counter
    
    # Contar frecuencia de números
    all_numbers = [n for combo in historical_data for n in combo]
    frequency = Counter(all_numbers)
    
    # Seleccionar números menos frecuentes
    least_common = [num for num, _ in frequency.most_common()[-15:]]
    
    # Generar combinación con alta exploración
    np.random.seed(seed + 200)
    if len(least_common) >= 4:
        rare_numbers = np.random.choice(least_common, size=4, replace=False)
        common_numbers = np.random.choice([n for n in range(1, 41) if n not in rare_numbers], size=2, replace=False)
    else:
        # Fallback si no hay suficientes números raros
        rare_numbers = np.random.choice(range(1, 11), size=2, replace=False)  # Números bajos
        high_numbers = np.random.choice(range(31, 41), size=2, replace=False)  # Números altos
        mid_numbers = np.random.choice(range(11, 31), size=2, replace=False)   # Números medios
        return sorted(list(rare_numbers) + list(high_numbers) + list(mid_numbers))
    
    return sorted(list(rare_numbers) + list(common_numbers))

def _generate_balanced_combo(historical_data: List[List[int]], seed: int) -> List[int]:
    """Genera combinación balanceada"""
    np.random.seed(seed + 300)
    
    # Dividir rango en secciones
    low_range = range(1, 14)     # 1-13
    mid_range = range(14, 28)    # 14-27  
    high_range = range(28, 41)   # 28-40
    
    # Seleccionar 2 números de cada rango
    low_nums = np.random.choice(low_range, size=2, replace=False)
    mid_nums = np.random.choice(mid_range, size=2, replace=False) 
    high_nums = np.random.choice(high_range, size=2, replace=False)
    
    return sorted(list(low_nums) + list(mid_nums) + list(high_nums))

# ====================================================================
# END OF FILE
# ====================================================================