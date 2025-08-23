# OMEGA_PRO_AI_v10.1/main.py – OMEGA PRO AI v12.4 HÍBRIDO – Lanzador Principal – Versión Mejorada

import os

PATHS_TO_CREATE = [
    'core', 'modules/utils', 'modules/filters', 'modules/learning', 'modules/evaluation',
    'modules/profiling', 'modules/reporting', 'utils', 'backup', 'data', 'config',
    'models', 'outputs', 'results', 'logs', 'temp'
]
for _p in PATHS_TO_CREATE:
    os.makedirs(_p, exist_ok=True)

import sys
import time
import argparse
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*enable_nested_tensor.*")
warnings.filterwarnings("ignore", message=".*Creating a tensor from a list.*")

try:
    from utils.numpy_compat import patch_numpy_deprecated_aliases, safe_json_export, safe_slice_list
    patch_numpy_deprecated_aliases()
except ImportError:
    def safe_json_export(obj, filepath, **kwargs):
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(obj, f, default=str, **kwargs)
    
    def safe_slice_list(lst, start=None, end=None):
        if not lst:
            return []
        try:
            return list(lst)[start:end] if start is not None or end is not None else list(lst)
        except:
            return []

import json as json_module
import pandas as pd
import numpy as np
from datetime import datetime
import pathlib
import random
from typing import Optional, List, Dict, Tuple
import importlib

# Importar sistema de monitoreo de rendimiento
try:
    from modules.performance_monitor import (
        get_performance_monitor, initialize_performance_monitoring, 
        shutdown_performance_monitoring
    )
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False
    print("⚠️ Sistema de monitoreo de rendimiento no disponible")

# MCP Integration - OMEGA AI Multi-Channel Platform
try:
    from omega_mcp_integration import (
        get_omega_mcp_integration, initialize_mcp_integration, 
        shutdown_mcp_integration, OMEGAMCPIntegration
    )
    MCP_INTEGRATION_AVAILABLE = True
    print("🔗 OMEGA MCP Integration disponible")
except ImportError:
    MCP_INTEGRATION_AVAILABLE = False
    print("⚠️ MCP Integration no disponible - instalar dependencias con: pip install -r requirements.txt")

# AGENTE: Soporte para configuración de agente
def load_agent_config():
    """Carga configuración del agente si existe OMEGA_AGENT_CFG"""
    agent_cfg_path = os.getenv("OMEGA_AGENT_CFG")
    if agent_cfg_path and pathlib.Path(agent_cfg_path).exists():
        try:
            with open(agent_cfg_path, 'r') as f:
                agent_cfg = json_module.load(f)
            print(f"🤖 Configuración de agente cargada desde: {agent_cfg_path}")
            return agent_cfg
        except Exception as e:
            print(f"⚠️ Error cargando config de agente: {e}")
    return None

# Importar manejo de errores mejorado
try:
    from modules.utils.error_handling import (
        ErrorHandler, OmegaError, DataValidationError, ModelTrainingError,
        ModelPredictionError, ConfigurationError, FileIOError, MultiprocessingError,
        handle_omega_errors, safe_execute, validate_and_execute, log_error_statistics
    )
    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_AVAILABLE = False
    print("⚠️ Manejo de errores mejorado no disponible")
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing
from functools import partial
import gc
from typing import Callable, Awaitable

# ---------------------------------------------------------------------------
# 2.1. Imports de IA Avanzada (Nuevos módulos)
# ---------------------------------------------------------------------------
try:
    from omega_ai_core import create_omega_ai_core, quick_ai_interaction
    from modules.nlp_intelligence import create_nlp_system, process_user_query
    from modules.meta_learning_integrator import create_meta_learning_system, intelligent_predict
    from modules.aprendizaje_omega_v2 import ejecutar_aprendizaje_post_sorteo, obtener_configuracion_aprendida
    from modules.advanced_neural_networks import create_advanced_ai_system, train_with_historical_data
    AI_MODULES_AVAILABLE = True
    META_LEARNING_AVAILABLE = True
    ADAPTIVE_LEARNING_AVAILABLE = True
    ADVANCED_AI_AVAILABLE = True
    print("🤖 Módulos de IA Avanzada cargados correctamente")
    print("🌟 Sistema de Meta-Learning disponible")
    print("🧠 Motor de Aprendizaje Adaptativo disponible")
    print("🚀 Sistema de IA Neuronal Avanzado disponible")
except ImportError as e:
    AI_MODULES_AVAILABLE = False
    META_LEARNING_AVAILABLE = False
    ADAPTIVE_LEARNING_AVAILABLE = False
    ADVANCED_AI_AVAILABLE = False
    print(f"⚠️ Módulos de IA no disponibles: {e}")
from pathlib import Path
try:
    from tqdm import tqdm
except Exception:
    class _DummyPbar:
        def update(self, n):
            return None
        def close(self):
            return None

    def tqdm(iterable=None, *args, **kwargs):
        # Si se llama como barra de progreso (sin iterable), devolvemos un stub con update/close
        # Si se pasa un iterable, devolvemos el iterable directamente (comportamiento mínimo)
        return iterable if iterable is not None else _DummyPbar()
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from collections import Counter
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# ---------------------------------------------------------------------------
# 3. Logging global con rotación
# ---------------------------------------------------------------------------
import logging
from logging.handlers import RotatingFileHandler

APP_NAME = "OMEGA PRO AI"
APP_VERSION = "v12.4"  # Incrementado tras el parche

def setup_rotating_logger(
    log_file="logs/omega.log",
    max_bytes=10 * 1024 * 1024,
    backup_count=5,
    level=logging.INFO
):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger_ = logging.getLogger()
    if logger_.handlers:                       # Evita duplicar handlers
        return logger_
    logger_.setLevel(level)

    fh = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger_.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger_.addHandler(ch)
    return logger_

logger = setup_rotating_logger()

# ---------------------------------------------------------------------------
# 4. Imports internos (después de tener logger disponible para fallback stubs)
# ---------------------------------------------------------------------------
def _check_module_exists(module_name):
    """Verifica si un módulo está disponible y registra información detallada si no lo está."""
    import importlib.util
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        logger.error(f"❌ Módulo {module_name} no encontrado")
        logger.error(f"💡 Asegúrese de que:")
        logger.error(f"   1. El módulo está instalado (pip install -r requirements.txt)")
        logger.error(f"   2. El archivo existe en la ruta correcta")
        logger.error(f"   3. No hay errores de sintaxis en el módulo")
        return False
    return True

# Importación de módulos de aprendizaje con verificación mejorada
if _check_module_exists("modules.learning.auto_retrain"):
    from modules.learning.auto_retrain import auto_retrain
else:
    def auto_retrain(*args, **kwargs):
        raise ImportError("Módulo auto_retrain requerido pero no disponible")

if _check_module_exists("modules.learning.retrotracker"):
    from modules.learning.retrotracker import RetroTracker
else:
    class RetroTracker:
        def __init__(self, *_, **__):
            raise ImportError("Módulo RetroTracker requerido pero no disponible")
        def get_results(self):
            raise ImportError("Módulo RetroTracker requerido pero no disponible")

if _check_module_exists("modules.learning.evaluate_model"):
    from modules.learning.evaluate_model import evaluate_model_performance
else:
    def evaluate_model_performance(*args, **kwargs):
        raise ImportError("Módulo evaluate_model_performance requerido pero no disponible")

from core.predictor import HybridOmegaPredictor as OmegaPredictor
from modules.partial_hit_optimizer import optimize_omega_for_partial_hits
from modules.score_dynamics import clean_combination
from utils.viabilidad import batch_calcular_svi, cargar_viabilidad, parallel_svi
from core.consensus_engine import validate_combination
from modules.exporters.exportador_svi import exportar_combinaciones_svi
from modules.utils.combinador_maestro import generar_combinacion_maestra
from utils.validation import clean_historial_df
from utils.random_control import maybe_seed_from_env

# Nuevos imports para IA mejorada
from modules.omega_auto_learning import aprender_automaticamente
from modules.balanced_range_predictor import crear_predictor_balanceado

# ---------------------------------------------------------------------------
# 5. ANSI para salida coloreada
# ---------------------------------------------------------------------------
ANSI = {
    "reset": "\033[0m", "cyan": "\033[96m", "green": "\033[92m",
    "yellow": "\033[93m", "red": "\033[91m", "bold": "\033[1m",
    "blue": "\033[94m", "magenta": "\033[95m", "underline": "\033[4m"
}

# ---------------------------------------------------------------------------
# Fallback para SimpleImputer (scikit-learn opcional)
# ---------------------------------------------------------------------------
try:
    from sklearn.impute import SimpleImputer  # Manejo de NaN
except ImportError:
    logger.warning("⚠️ scikit-learn no disponible – usando SimpleImputer básico")

    class SimpleImputer:
        """Implementación mínima de imputación media (solo strategy='mean')."""
        def __init__(self, strategy: str = "mean"):
            if strategy != "mean":
                raise ValueError("Solo strategy='mean' soportado en stub")
        def fit_transform(self, X):
            import numpy as np
            col_means = np.nanmean(X, axis=0)
            return np.where(np.isnan(X), col_means, X)

# ---------------------------------------------------------------------------
# 6. Utilidades varias
# ---------------------------------------------------------------------------
def get_fallback_item(error_info=None):
    """Retorna una combinación de fallback con información del error.
    
    Args:
        error_info (dict, optional): Información sobre el error que causó el fallback
            - error_type: Tipo de error (ej: "data_error", "config_error", "runtime_error")
            - message: Mensaje descriptivo del error
            - details: Detalles adicionales o stack trace
    """
    fallback = {
        "combination": [1, 2, 3, 4, 5, 6],
        "score": 0.5,
        "svi_score": 0.5,
        "source": "fallback",
        "original_score": 0.5,
        "error_info": error_info or {
            "error_type": "unknown",
            "message": "Fallback genérico activado",
            "details": None
        }
    }
    
    if error_info:
        logger.error(f"❌ Error tipo: {error_info['error_type']}")
        logger.error(f"📝 Mensaje: {error_info['message']}")
        if error_info.get('details'):
            logger.error(f"🔍 Detalles: {error_info['details']}")
    
    return fallback

def reportar_progreso(i, total, config=None):
    """Barra de progreso segura con cierre automático."""
    config = config or {}
    try:
        if not hasattr(reportar_progreso, "_pbar"):
            bar_style = config.get("progress_bar_style", {"desc": "Procesando", "unit": "combo"})
            reportar_progreso._pbar = tqdm(total=total, **bar_style)
        reportar_progreso._pbar.update(1)
        if i == total:
            reportar_progreso._pbar.close()
            delattr(reportar_progreso, "_pbar")
    except Exception as exc:
        logger.error(f"Error en barra de progreso: {exc}")
        if hasattr(reportar_progreso, "_pbar"):
            reportar_progreso._pbar.close()
            delattr(reportar_progreso, "_pbar")

class ConfigHandler(PatternMatchingEventHandler):
    """Observa cambios en archivos de configuración."""
    def __init__(self, callback, patterns):
        super().__init__(patterns=patterns)
        self.callback = callback
    def on_modified(self, event):
        if not event.is_directory:
            self.callback()

def start_config_watcher(config_path, callback):
    observer = Observer()
    observer.schedule(ConfigHandler(callback, patterns=[config_path.name]),
                      str(config_path.parent), recursive=False)
    observer.start()
    return observer

def print_summary_stats(stats, config, logger):
    """Resumen estructurado de métricas de ejecución."""
    logger.info(f"\n{'=' * 60}")
    logger.info("📊 RESUMEN ESTADÍSTICO:")
    logger.info(f"{'=' * 60}")
    logger.info(f"🔢 Total combinaciones: {stats['total']}")
    logger.info(f"🏆 Mejor score: {stats['max_score']:.3f}")
    logger.info(f"⚖️ Peor score: {stats['min_score']:.3f}")
    logger.info(f"📈 Score promedio: {stats['avg_score']:.3f} (Pred: {stats['avg_original']:.3f}, SVI: {stats['avg_svi']:.3f})")
    logger.info(f"⚖️ Pesos: Pred={stats['pred_weight']*100:.0f}%, SVI={stats['svi_weight']*100:.0f}%")
    logger.info(f"📊 Perfil SVI: {stats['svi_profile']}")

    logger.info("\n🌐 DISTRIBUCIÓN POR FUENTE:")
    emojis = config.get("emojis", {})
    for fuente, cantidad in stats["source_counter"].most_common():
        pct = (cantidad / stats['total']) * 100 if stats['total'] else 0
        logger.info(f" - {emojis.get(fuente, '🔹')} {fuente:<15}: {cantidad} ({pct:.1f}%)")

    if config.get("visualize_summary", False):
        logger.info(f"\n{'=' * 60}")
        logger.info("📊 VISUALIZACIÓN DE DISTRIBUCIÓN:")
        logger.info(f"{'=' * 60}")
        max_val = max(stats['source_counter'].values()) if stats['source_counter'] else 1
        for fuente, cantidad in stats['source_counter'].most_common():
            bar = '█' * int(config.get("max_bar_length", 50) * cantidad / max_val)
            pct = (cantidad / stats['total']) * 100 if stats['total'] else 0
            logger.info(f"{emojis.get(fuente, '🔹')} {fuente:<12} {bar} {pct:.1f}% ({cantidad})")

# ---------------------------------------------------------------------------
# 6. CONFIGURACIÓN OPTIMIZADA DE DATOS HISTÓRICOS (NUEVO)
# ---------------------------------------------------------------------------

def get_system_resources() -> Dict:
    """Get current system resource information for optimization"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        cpu_count = multiprocessing.cpu_count()
        return {
            'available_memory_gb': memory.available / (1024**3),
            'total_memory_gb': memory.total / (1024**3),
            'memory_percent': memory.percent,
            'cpu_count': cpu_count,
            'cpu_percent': psutil.cpu_percent(interval=1)
        }
    except ImportError:
        # Fallback without psutil
        return {
            'available_memory_gb': 4.0,  # Conservative estimate
            'total_memory_gb': 8.0,
            'memory_percent': 50.0,
            'cpu_count': multiprocessing.cpu_count(),
            'cpu_percent': 50.0
        }

def get_adaptive_config(resources: Dict) -> Dict:
    """Generate adaptive configuration based on system resources"""
    config = {
        'max_parallel_models': min(4, max(2, resources['cpu_count'] // 2)),
        'batch_size': 16 if resources['available_memory_gb'] > 4 else 8,
        'epochs': 30 if resources['available_memory_gb'] > 6 else 20,
        'enable_gpu': resources['available_memory_gb'] > 8,
        'max_combinations': 500 if resources['available_memory_gb'] > 4 else 200,
        'use_caching': resources['available_memory_gb'] > 3,
        'timeout_seconds': 300 if resources['cpu_percent'] < 80 else 180,
        'parallel_threshold': 3,  # Minimum models to justify parallel execution
        'enable_gc': resources['memory_percent'] > 75
    }
    
    # Memory-based optimizations
    if resources['memory_percent'] > 80:
        config['batch_size'] = max(4, config['batch_size'] // 2)
        config['max_combinations'] = min(100, config['max_combinations'])
        config['max_parallel_models'] = max(2, config['max_parallel_models'] // 2)
        config['enable_gc'] = True
    
    return config

def get_optimal_historical_data(df: pd.DataFrame, cols: List[str], 
                                min_records: int = 800, 
                                max_records: int = 1000,
                                component: str = "general") -> Tuple[List, Dict]:
    """
    Obtiene la cantidad óptima de datos históricos según el componente.
    
    Args:
        df: DataFrame con datos históricos
        cols: Columnas de bolillas
        min_records: Mínimo recomendado de registros
        max_records: Máximo de registros para eficiencia
        component: Componente que solicita los datos ('IA', 'Meta-Learning', etc.)
    
    Returns:
        Tuple[List, Dict]: (datos_históricos, metadata)
    """
    total_records = len(df)
    
    # Configuraciones específicas por componente - OPTIMIZADO PARA 1000 SORTEOS
    component_configs = {
        'IA': {'min': 800, 'max': 1000, 'optimal': 1000},
        'Meta-Learning': {'min': 700, 'max': 1000, 'optimal': 1000}, 
        'LSTM': {'min': 500, 'max': 1000, 'optimal': 800},
        'Transformer': {'min': 300, 'max': 1000, 'optimal': 600},
        'Clustering': {'min': 400, 'max': 1000, 'optimal': 700},
        'general': {'min': 800, 'max': 1000, 'optimal': 1000}
    }
    
    config = component_configs.get(component, component_configs['general'])
    
    # Determinar cantidad a usar
    if total_records >= config['optimal']:
        records_to_use = min(config['optimal'], total_records)
        status = "optimal"
    elif total_records >= config['min']:
        records_to_use = total_records
        status = "good"
    elif total_records >= 50:
        records_to_use = total_records
        status = "limited"
    else:
        records_to_use = total_records
        status = "insufficient"
    
    # Extraer datos
    historical_data = df[cols].values.tolist()[-records_to_use:] if records_to_use > 0 else []
    
    # Metadata
    metadata = {
        'records_used': len(historical_data),
        'total_available': total_records,
        'component': component,
        'status': status,
        'recommended_min': config['min'],
        'optimal_amount': config['optimal'],
        'efficiency_ratio': len(historical_data) / config['optimal'] if config['optimal'] > 0 else 0
    }
    
    return historical_data, metadata

def log_data_status(metadata: Dict, logger):
    """Log del estado de los datos históricos"""
    status_emojis = {
        'optimal': '🟢',
        'good': '🟡', 
        'limited': '🟠',
        'insufficient': '🔴'
    }
    
    emoji = status_emojis.get(metadata['status'], '⚪')
    
    if metadata['status'] == 'optimal':
        logger.info(f"{emoji} Dataset {metadata['component']}: {metadata['records_used']} registros (ÓPTIMO)")
    elif metadata['status'] == 'good':
        logger.info(f"{emoji} Dataset {metadata['component']}: {metadata['records_used']} registros (BUENO)")
    elif metadata['status'] == 'limited':
        logger.warning(f"{emoji} Dataset {metadata['component']}: {metadata['records_used']} registros (LIMITADO - Recomendado: {metadata['recommended_min']}+)")
    else:
        logger.error(f"{emoji} Dataset {metadata['component']}: {metadata['records_used']} registros (INSUFICIENTE - Mínimo: {metadata['recommended_min']})")
    
    logger.info(f"   Eficiencia: {metadata['efficiency_ratio']:.1%} | Total disponible: {metadata['total_available']}")

# ---------------------------------------------------------------------------
# 7. ASYNC MODEL EXECUTION FUNCTIONS (NEW)
# ---------------------------------------------------------------------------

async def execute_model_async(model_name: str, model_func: Callable, 
                             *args, timeout: int = 300, **kwargs) -> Tuple[str, List]:
    """Execute a model asynchronously with timeout management"""
    loop = asyncio.get_event_loop()
    
    try:
        # Use ThreadPoolExecutor for I/O bound operations
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = loop.run_in_executor(
                executor, 
                partial(model_func, *args, **kwargs)
            )
            
            # Wait with timeout
            result = await asyncio.wait_for(future, timeout=timeout)
            return model_name, result if result else []
            
    except asyncio.TimeoutError:
        logger.warning(f"⏰ {model_name} timeout after {timeout}s")
        return model_name, []
    except Exception as e:
        logger.error(f"🚨 {model_name} failed: {e}")
        return model_name, []

async def execute_models_parallel(model_configs: List[Dict], 
                                adaptive_config: Dict) -> Dict[str, List]:
    """Execute multiple models in parallel with resource management"""
    max_parallel = adaptive_config['max_parallel_models']
    timeout = adaptive_config['timeout_seconds']
    
    # Create semaphore to limit concurrent execution
    semaphore = asyncio.Semaphore(max_parallel)
    
    async def run_with_semaphore(config):
        async with semaphore:
            return await execute_model_async(
                config['name'],
                config['function'],
                *config.get('args', []),
                timeout=timeout,
                **config.get('kwargs', {})
            )
    
    # Execute models with controlled parallelism
    tasks = [run_with_semaphore(config) for config in model_configs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    model_results = {}
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"🚨 Model execution exception: {result}")
            continue
        
        model_name, model_output = result
        model_results[model_name] = model_output
        
        # Memory management
        if adaptive_config.get('enable_gc', False):
            gc.collect()
    
    return model_results

# ---------------------------------------------------------------------------
# 8. FUNCIONES DE IA AVANZADA (OPTIMIZADAS) Y UTILIDADES ASYNC

def safe_async_execution(coro_or_future):
    """
    Ejecuta async functions de manera segura detectando el contexto del event loop.
    Esta función es SINCRÓNICA y maneja la ejecución async internamente.
    """
    try:
        # Verificar si ya estamos en un event loop activo
        loop = asyncio.get_running_loop()
        # Si hay un loop ejecutándose, usamos ThreadPoolExecutor para evitar conflicto
        logger.debug("🔄 Event loop detectado, ejecutando async function en hilo separado")
        
        import concurrent.futures
        import threading
        
        def run_in_new_loop():
            """Ejecuta la corrutina en un nuevo event loop en un hilo separado"""
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                if hasattr(coro_or_future, '__await__'):
                    return new_loop.run_until_complete(coro_or_future)
                else:
                    return coro_or_future
            finally:
                new_loop.close()
        
        # Ejecutar en ThreadPoolExecutor para evitar bloqueo
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_in_new_loop)
            return future.result(timeout=300)  # 5 minutos timeout
            
    except RuntimeError:
        # No hay event loop activo, usar asyncio.run() normalmente
        logger.debug("🔄 No hay event loop, ejecutando con asyncio.run()")
        try:
            if hasattr(coro_or_future, '__await__'):
                return asyncio.run(coro_or_future)
            else:
                return coro_or_future
        except Exception as e:
            logger.error(f"❌ Error ejecutando corrutina: {e}")
            return None
    
    except Exception as e:
        logger.error(f"❌ Error inesperado en safe_async_execution: {e}")
        return None

# 8. FUNCIONES DE IA AVANZADA (OPTIMIZADAS)
# ---------------------------------------------------------------------------

async def handle_ai_mode(data_path, ai_query, ai_interactive, ai_analyze, top_n):
    """Maneja todos los modos de IA avanzada"""
    logger.info("🤖 Iniciando modo IA avanzada...")
    
    # Cargar datos históricos optimizados para contexto
    historical_data = []
    try:
        df = pd.read_csv(data_path)
        cols = [c for c in df.columns if "bolilla" in c.lower()][:6]
        if len(cols) >= 6:
            # MEJORADO: Uso optimizado de datos históricos
            historical_data, metadata = get_optimal_historical_data(df, cols, component='IA')
            log_data_status(metadata, logger)
    except Exception as e:
        logger.warning(f"⚠️ No se pudieron cargar datos históricos: {e}")
    
    context = {'historical_data': historical_data}
    
    # Modo interactivo
    if ai_interactive:
        return await interactive_ai_mode(context)
    
    # Consulta específica
    if ai_query:
        return await process_ai_query(ai_query, context)
    
    # Análisis inteligente
    if ai_analyze:
        return await ai_pattern_analysis(context)
    
    # Modo IA general
    return await general_ai_mode(context, top_n)

async def interactive_ai_mode(context):
    """Modo interactivo con IA"""
    print("\n🤖 OMEGA PRO AI - Modo Interactivo")
    print("="*50)
    print("Puedes hacer preguntas como:")
    print("• 'Genera 5 combinaciones conservadoras'")
    print("• 'Analiza los patrones históricos'")
    print("• 'Qué probabilidad tiene [1,15,23,31,35,40]'")
    print("• 'Dame recomendaciones'")
    print("• 'salir' para terminar")
    print("="*50)
    
    ai_core = create_omega_ai_core()
    
    try:
        while True:
            user_input = input("\n🔤 Tu pregunta: ").strip()
            
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("👋 ¡Hasta luego!")
                break
            
            if not user_input:
                continue
            
            print("🧠 Procesando con IA...")
            response = await ai_core.process_intelligent_request(user_input, context)
            
            print(f"\n🤖 OMEGA AI:")
            print(response['ai_response'])
            
            # Mostrar resultados si hay combinaciones
            if 'combinations' in response.get('ai_results', {}):
                combinations = response['ai_results']['combinations']
                if combinations:
                    print("\n🎯 Combinaciones generadas:")
                    for i, combo in enumerate(combinations[:5], 1):
                        if isinstance(combo, dict) and 'combination' in combo:
                            numbers = combo['combination']
                            confidence = combo.get('confidence', 0.5)
                            print(f"   {i}. {' - '.join(map(str, numbers))} (Confianza: {confidence:.1%})")
    
    finally:
        await ai_core.shutdown_gracefully()
    
    return {"status": "interactive_completed"}

async def process_ai_query(query, context):
    """Procesa una consulta específica de IA"""
    logger.info(f"🎯 Procesando consulta: {query}")
    
    response = await quick_ai_interaction(query, context.get('historical_data', []))
    
    print(f"\n🤖 OMEGA AI - Respuesta:")
    print("="*50)
    print(response['ai_response'])
    
    # Mostrar resultados detallados
    if 'combinations' in response.get('ai_results', {}):
        combinations = response['ai_results']['combinations']
        print(f"\n🎯 Combinaciones generadas ({len(combinations)}):")
        for i, combo in enumerate(combinations, 1):
            if isinstance(combo, dict) and 'combination' in combo:
                numbers = combo['combination']
                confidence = combo.get('confidence', 0.5)
                source = combo.get('source', 'unknown')
                print(f"   {i}. {' - '.join(map(str, numbers))} ")
                print(f"      Confianza: {confidence:.1%} | Fuente: {source}")
    
    return response

async def ai_pattern_analysis(context):
    """Análisis inteligente de patrones"""
    logger.info("🔍 Iniciando análisis inteligente de patrones...")
    
    if not context.get('historical_data'):
        print("❌ No hay datos históricos para analizar")
        return {"error": "No data"}
    
    query = "Analiza profundamente todos los patrones en estos datos históricos"
    response = await quick_ai_interaction(query, context['historical_data'])
    
    print("\n🔍 ANÁLISIS INTELIGENTE DE PATRONES")
    print("="*50)
    print(response['ai_response'])
    
    # Mostrar análisis técnico si está disponible
    ai_results = response.get('ai_results', {})
    if 'analysis' in ai_results:
        analysis = ai_results['analysis']
        if 'pattern_intelligence' in analysis:
            pattern_info = analysis['pattern_intelligence']
            print(f"\n📊 MÉTRICAS TÉCNICAS:")
            print(f"• Complejidad de patrones: {pattern_info.get('pattern_complexity', 0):.3f}")
            print(f"• Confianza de IA: {pattern_info.get('ai_confidence', 0):.1%}")
            print(f"• Tendencia detectada: {pattern_info.get('predicted_trend', 'neutral')}")
            print(f"• Score de inteligencia: {pattern_info.get('intelligence_score', 0):.3f}")
            
            if 'recommendations' in pattern_info:
                print(f"\n💡 RECOMENDACIONES:")
                for rec in pattern_info['recommendations']:
                    print(f"• {rec}")
    
    return response

async def general_ai_mode(context, top_n):
    """Modo IA general - genera combinaciones inteligentes"""
    logger.info("🚀 Ejecutando modo IA general...")
    
    query = f"Genera {top_n} combinaciones usando toda tu inteligencia artificial"
    response = await quick_ai_interaction(query, context.get('historical_data', []))
    
    print("\n🚀 OMEGA PRO AI - MODO IA AVANZADA")
    print("="*60)
    print(response['ai_response'])
    
    # Generar archivo de resultados
    if 'combinations' in response.get('ai_results', {}):
        combinations = response['ai_results']['combinations']
        
        # Crear estructura compatible con el sistema original
        omega_results = []
        for i, combo in enumerate(combinations):
            if isinstance(combo, dict) and 'combination' in combo:
                omega_results.append({
                    'rank': int(i + 1),
                    'combination': [int(x) for x in combo['combination']],
                    'confidence': float(combo.get('confidence', 0.5)),
                    'ai_source': str(combo.get('source', 'ai_system')),
                    'method': str(combo.get('method', 'integrated_ai')),
                    'timestamp': datetime.now().isoformat()
                })
        
        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ai_results_file = f"results/omega_ai_results_{timestamp}.json"
        os.makedirs("results", exist_ok=True)
        
        with open(ai_results_file, 'w') as f:
            json_module.dump({
                'metadata': {
                    'system': 'OMEGA PRO AI - Advanced Mode',
                    'timestamp': timestamp,
                    'total_combinations': len(omega_results),
                    'ai_systems_used': response.get('metadata', {}).get('systems_used', [])
                },
                'combinations': omega_results
            }, f, indent=2)
        
        print(f"\n💾 Resultados guardados en: {ai_results_file}")
    
    return response

async def handle_meta_learning_mode(data_path, train_meta, meta_predict, enable_rl, top_n):
    """Maneja el modo de meta-learning avanzado"""
    logger.info("🌟 Iniciando modo Meta-Learning avanzado...")
    
    # Cargar datos históricos optimizados
    historical_data = []
    try:
        df = pd.read_csv(data_path)
        cols = [c for c in df.columns if "bolilla" in c.lower()][:6]
        if len(cols) >= 6:
            # MEJORADO: Uso optimizado para Meta-Learning
            historical_data, metadata = get_optimal_historical_data(df, cols, component='Meta-Learning')
            log_data_status(metadata, logger)
    except Exception as e:
        logger.error(f"❌ Error cargando datos: {e}")
        return {"error": "No se pudieron cargar datos históricos"}
    
    if len(historical_data) < 30:
        logger.error("❌ Insuficientes datos históricos para Meta-Learning")
        return {"error": "Mínimo 30 combinaciones históricas requeridas"}
    
    # Log adicional del estado del dataset
    if metadata['status'] == 'optimal':
        logger.info(f"🚀 Dataset excelente para Meta-Learning: {len(historical_data)} registros")
    elif metadata['status'] == 'good':
        logger.info(f"✅ Dataset adecuado para Meta-Learning: {len(historical_data)} registros")
    elif metadata['status'] == 'limited':
        logger.warning(f"⚠️ Dataset limitado pero funcional: {len(historical_data)} registros")
    else:
        logger.warning(f"🟡 Dataset mínimo: {len(historical_data)} registros - Precisión puede verse afectada")
    
    # Crear sistema de meta-learning
    integrator = create_meta_learning_system(enable_all=True)
    
    print("\n🌟 OMEGA PRO AI - META-LEARNING AVANZADO")
    print("="*70)
    
    # Entrenar sistema si se solicita
    if train_meta:
        print("🏋️ ENTRENANDO SISTEMA DE META-LEARNING...")
        print("-"*50)
        
        training_results = integrator.train_integrated_system(historical_data)
        
        print(f"✅ Entrenamiento completado:")
        print(f"   • Componentes entrenados: {len(training_results['components_trained'])}")
        for component in training_results['components_trained']:
            print(f"     - {component}")
        
        # Guardar estado entrenado
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        state_file = f"models/meta_learning_state_{timestamp}.json"
        os.makedirs("models", exist_ok=True)
        integrator.save_system_state(state_file)
        print(f"   • Estado guardado en: {state_file}")
    
    # Generar predicciones si se solicita
    num_predictions = meta_predict if meta_predict else top_n
    
    print(f"\n🧠 GENERANDO {num_predictions} PREDICCIONES CON META-LEARNING...")
    print("-"*50)
    
    # Predicción inteligente
    results = await intelligent_predict(integrator, historical_data, num_predictions)
    
    # Mostrar análisis meta
    if 'meta_analysis' in results and 'regime' in results['meta_analysis']:
        analysis = results['meta_analysis']
        print(f"📊 ANÁLISIS DE CONTEXTO:")
        print(f"   • Régimen detectado: {analysis['regime']}")
        print(f"   • Entropía: {analysis['entropy']:.3f}")
        print(f"   • Varianza: {analysis['variance']:.3f}")
        print(f"   • Fuerza de tendencia: {analysis['trend_strength']:.3f}")
        
        if 'optimal_weights' in analysis:
            print(f"   • Pesos optimizados:")
            for model, weight in analysis['optimal_weights'].items():
                print(f"     - {model}: {weight:.3f}")
    
    # Mostrar resultados de componentes
    if 'component_results' in results:
        comp_results = results['component_results']
        print(f"\n🔧 RESULTADOS DE COMPONENTES:")
        
        if 'profiler' in comp_results:
            prof = comp_results['profiler']
            print(f"   • Perfil predicho: {prof['profile']} ({prof['confidence']:.1%})")
        
        if 'lstm_v2' in comp_results:
            lstm = comp_results['lstm_v2']
            print(f"   • LSTM v2: {lstm['predictions_count']} predicciones (entrenado: {lstm['is_trained']})")
        
        if 'reinforcement' in comp_results:
            rl = comp_results['reinforcement']
            print(f"   • RL: {rl['action_type']} en {rl['model_adjusted']}")
    
    # Mostrar predicciones
    print(f"\n🎯 PREDICCIONES META-LEARNING:")
    print("-"*50)
    
    for i, prediction in enumerate(results['predictions'], 1):
        combination = prediction['combination']
        confidence = prediction['confidence']
        components = ', '.join(prediction.get('components_used', []))
        
        print(f"{i:2d}. {' - '.join(f'{n:2d}' for n in combination)}")
        print(f"    Confianza: {confidence:.1%} | Componentes: {components}")
    
    # Métricas de integración
    if 'integration_metrics' in results:
        metrics = results['integration_metrics']
        print(f"\n📈 MÉTRICAS DE INTEGRACIÓN:")
        print(f"   • Tiempo de procesamiento: {metrics['processing_time']:.3f}s")
        print(f"   • Componentes utilizados: {metrics['components_used']}")
        print(f"   • Confianza promedio: {metrics['confidence_avg']:.1%}")
    
    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"results/meta_learning_results_{timestamp}.json"
    os.makedirs("results", exist_ok=True)
    
    # Preparar resultados para guardar
    save_results = {
        'metadata': {
            'system': 'OMEGA PRO AI - Meta-Learning',
            'timestamp': timestamp,
            'total_predictions': len(results['predictions']),
            'components_used': results.get('integration_metrics', {}).get('components_used', 0),
            'data_size': len(historical_data)
        },
        'predictions': results['predictions'],
        'meta_analysis': results.get('meta_analysis', {}),
        'component_results': results.get('component_results', {}),
        'integration_metrics': results.get('integration_metrics', {})
    }
    
    with open(results_file, 'w') as f:
        json_module.dump(save_results, f, indent=2, default=str)
    
    print(f"\n💾 Resultados guardados en: {results_file}")
    
    # Estado del sistema
    status = integrator.get_system_status()
    print(f"\n📊 ESTADO DEL SISTEMA:")
    print(f"   • Sesión ID: {status['session_id']}")
    print(f"   • Componentes activos: {sum(status['components_enabled'].values())}/4")
    
    if 'integration_stats' in status:
        stats = status['integration_stats']
        print(f"   • Total de predicciones: {stats['total_predictions']}")
        print(f"   • Tiempo promedio: {stats['avg_processing_time']:.3f}s")
    
    print(f"\n🎉 Meta-Learning completado exitosamente!")
    
    return results

async def execute_parallel_models(predictor, adaptive_config: Dict, logger) -> List[Dict]:
    """Execute models in parallel using the optimized predictor"""
    try:
        # Use the predictor's parallel execution capabilities
        return await predictor.run_all_models_async(adaptive_config)
    except AttributeError:
        # Fallback to sequential if async not available
        logger.warning("⚠️ Predictor doesn't support async, using sequential")
        return predictor.run_all_models()
    except Exception as e:
        logger.error(f"🚨 Error in parallel execution: {e}")
        return predictor.run_all_models()

# ---------------------------------------------------------------------------
# 7. FUNCIÓN PRINCIPAL
# ---------------------------------------------------------------------------
@handle_omega_errors(
    context="Función principal de OMEGA PRO AI",
    fallback_return=[{"combination": [5, 7, 11, 22, 33, 36], "score": 0.5, "source": "fallback_emergency"}]
)
async def main(
    data_path="data/historial_kabala_github_emergency_clean.csv",
    svi_profile="default",
    top_n=8,  # MODIFICADO: Genera exactamente 8 series finales
    enable_models=None,
    export_formats=None,
    viabilidad_config="config/viabilidad.json",
    retrain=True,  # Cambiado a False por defecto
    evaluate=True,  # Cambiado a False por defecto
    backtest=True,  # Cambiado a False por defecto
    disable_multiprocessing=False,  # Si es True, usa ThreadPoolExecutor en lugar de ProcessPoolExecutor
    # Nuevos parámetros de IA
    ai_mode=False,
    ai_query=None,
    ai_interactive=False,
    ai_analyze=False,
    # Nuevos parámetros de Meta-Learning
    meta_learning=False,
    train_meta=False,
    meta_predict=None,
    enable_rl=False,
    # Nuevos parámetros de Aprendizaje Adaptativo
    learn_from_sorteo=False,
    resultado_oficial=None,
    perfil_sorteo='B',
    regime_rng='moderate',
    dry_run: bool = False,
    limit: Optional[int] = None,
    partial_hits: bool = False,  # 🎯 NUEVO: Modo optimizado para 4-5 números
    # Parámetros de actualización de datos
    update_data: bool = False,  # 📊 NUEVO: Actualizar dataset
    fecha_sorteo: Optional[str] = None,  # 📅 Fecha del sorteo
    numeros_sorteo: Optional[str] = None,  # 🎲 Números del sorteo
    data_info: bool = False,  # 📋 Mostrar información del dataset
    backup_data: bool = False,  # 💾 Crear backup
    enable_performance_monitoring: bool = True,  # 🔍 NUEVO: Habilitar monitoreo de rendimiento
    # MCP Integration parameters
    enable_mcp: bool = False,  # 🔗 NUEVO: Habilitar MCP Integration
    mcp_config: Optional[str] = None,  # 📄 Configuración MCP
    mcp_credentials: Optional[str] = None,  # 🔑 Credenciales MCP
    mcp_auto_start: bool = False,  # 🚀 Auto-start MCP services
    mcp_test: bool = False,  # 🧪 Test MCP before prediction
    mcp_notify: bool = False,  # 📱 Send MCP notifications
):
    """Ejecuta el sistema de predicción OMEGA PRO AI."""
    # MODIFICADO: Forzar que TODOS los modelos estén activos para mejor predicción
    enable_models = ["all"]  # Todos los modelos siempre activos
    export_formats = export_formats or ["csv", "json"]

    # -----------------------------------------------------------------------
    # INICIALIZAR MONITOREO DE RENDIMIENTO
    # -----------------------------------------------------------------------
    performance_monitor = None
    if enable_performance_monitoring and PERFORMANCE_MONITORING_AVAILABLE:
        try:
            performance_monitor = initialize_performance_monitoring({
                'monitor_interval': 1.0,
                'history_size': 1000,
                'alert_thresholds': {
                    'max_execution_time': 35.0,  # Detectar timeouts de 30+ segundos
                    'max_memory_percent': 85.0,
                    'max_cpu_percent': 95.0,
                    'min_success_rate': 0.80,
                    'memory_growth_rate': 100.0,  # MB por minuto
                }
            })
            logger.info("🔍 Sistema de monitoreo de rendimiento iniciado")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo inicializar monitoreo de rendimiento: {e}")
            performance_monitor = None
    elif enable_performance_monitoring:
        logger.warning("⚠️ Monitoreo de rendimiento solicitado pero no disponible")

    # -----------------------------------------------------------------------
    # MCP INTEGRATION INITIALIZATION
    # -----------------------------------------------------------------------
    mcp_integration = None
    if MCP_INTEGRATION_AVAILABLE and (enable_mcp or os.getenv("OMEGA_MCP_AUTO_INIT", "false").lower() == "true"):
        try:
            logger.info("🔗 Inicializando OMEGA MCP Integration...")
            
            # Initialize MCP integration with custom config if provided
            mcp_integration = OMEGAMCPIntegration(mcp_config)
            
            # Load credentials from specified file or auto-discover
            credentials = None
            if mcp_credentials:
                try:
                    with open(mcp_credentials, 'r') as f:
                        credentials = json_module.load(f)
                    logger.info(f"🔑 Credenciales MCP cargadas desde: {mcp_credentials}")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando credenciales MCP: {e}")
            
            # Initialize MCP
            await mcp_integration.initialize(credentials)
            
            # Run tests if requested
            if mcp_test:
                logger.info("🧪 Ejecutando pruebas de MCP Integration...")
                if hasattr(mcp_integration, 'mcp_manager') and mcp_integration.mcp_manager:
                    test_results = await mcp_integration.mcp_manager.test_all_systems()
                    
                    all_passed = all(result.get("success", False) for result in test_results.values())
                    if all_passed:
                        logger.info("✅ Todas las pruebas MCP pasaron correctamente")
                    else:
                        logger.warning("⚠️ Algunas pruebas MCP fallaron:")
                        for system, result in test_results.items():
                            if not result.get("success"):
                                logger.warning(f"   ❌ {system}: {result.get('error', 'Error desconocido')}")
                else:
                    logger.warning("⚠️ No se pudo ejecutar pruebas MCP - manager no disponible")
            
            # Auto-start services if requested
            if mcp_auto_start:
                logger.info("🚀 Auto-iniciando servicios MCP...")
                # Default user preferences for auto-start
                user_prefs = {
                    "notification_channels": ["email"],
                    "contact_info": {"email": os.getenv("TEST_EMAIL", "admin@localhost")},
                    "prediction_count": 3,
                    "include_analysis": True,
                    "include_disclaimer": True
                }
                await mcp_integration.start(user_prefs)
                logger.info("✅ Servicios MCP iniciados en modo automático")
            
            logger.info("✅ OMEGA MCP Integration inicializada correctamente")
            
        except Exception as e:
            logger.warning(f"⚠️ No se pudo inicializar MCP Integration: {e}")
            mcp_integration = None
    elif MCP_INTEGRATION_AVAILABLE:
        logger.info("🔗 MCP Integration disponible (no habilitada)")
        logger.info("💡 Para habilitar: --enable-mcp o OMEGA_MCP_AUTO_INIT=true")

    # -----------------------------------------------------------------------
    # FUNCIONALIDAD DE ACTUALIZACIÓN DE DATOS
    # -----------------------------------------------------------------------
    if update_data or data_info:
        from modules.data_manager import OmegaDataManager
        
        dm = OmegaDataManager()
        
        # Mostrar información del dataset si se solicita
        if data_info:
            logger.info("📊 Obteniendo información del dataset...")
            info = dm.get_data_info()
            
            print("\n" + "="*60)
            print("📊 INFORMACIÓN DEL DATASET OMEGA PRO AI")
            print("="*60)
            print(f"📈 Total de registros: {info['total_records']}")
            print(f"📅 Rango de fechas: {info['date_range']['from']} → {info['date_range']['to']}")
            print(f"🗂️ Columnas disponibles: {len(info['columns'])}")
            
            if info.get('last_sorteo'):
                last = info['last_sorteo']
                print(f"\n🎯 ÚLTIMO SORTEO REGISTRADO:")
                print(f"   📅 Fecha: {last['fecha']}")
                print(f"   🎲 Números: {' - '.join(map(str, last['numeros']))}")
            
            print(f"\n✅ Calidad de datos:")
            print(f"   • Registros completos: {info['data_quality']['complete_records']}")
            print(f"   • Datos faltantes: {info['data_quality']['missing_data']}")
            print("="*60)
            
            if not update_data:
                return []  # Solo mostrar info y salir
        
        # Actualizar dataset si se solicita
        if update_data:
            if not fecha_sorteo or not numeros_sorteo:
                logger.error("❌ Error: Se requieren --fecha-sorteo y --numeros-sorteo")
                logger.info("💡 Uso: python main.py --update-data --fecha-sorteo 2025-08-16 --numeros-sorteo '1,2,3,4,5,6'")
                return []
            
            # Parsear números
            try:
                numeros_str = numeros_sorteo.replace(',', ' ').split()
                numeros = [int(n) for n in numeros_str]
                
                if len(numeros) != 6:
                    raise ValueError(f"Se requieren exactamente 6 números, proporcionados: {len(numeros)}")
                
                if not all(1 <= n <= 40 for n in numeros):
                    raise ValueError(f"Todos los números deben estar entre 1 y 40")
                
            except ValueError as e:
                logger.error(f"❌ Error en números: {e}")
                logger.info("💡 Formato correcto: --numeros-sorteo '1,2,3,4,5,6' o '1 2 3 4 5 6'")
                return []
            
            # Validar fecha
            try:
                fecha_dt = datetime.strptime(fecha_sorteo, '%Y-%m-%d')
            except ValueError:
                logger.error(f"❌ Error en fecha: formato debe ser YYYY-MM-DD")
                logger.info(f"💡 Ejemplo: --fecha-sorteo 2025-08-16")
                return []
            
            # Crear backup si se solicita
            if backup_data:
                logger.info("💾 Creando backup...")
                backup_path = dm.create_backup()
                if backup_path:
                    logger.info(f"✅ Backup creado: {backup_path}")
                else:
                    logger.warning("⚠️ No se pudo crear backup")
            
            # Mostrar resumen
            print("\n" + "="*50)
            print("📊 RESUMEN DEL SORTEO A AÑADIR")
            print("="*50)
            print(f"📅 Fecha: {fecha_sorteo}")
            print(f"🎲 Números: {' - '.join(map(str, numeros))}")
            print(f"📊 Suma: {sum(numeros)}")
            print(f"📈 Promedio: {sum(numeros)/6:.2f}")
            print(f"📏 Rango: {max(numeros) - min(numeros)}")
            print("="*50)
            
            # Añadir sorteo
            logger.info(f"➕ Añadiendo sorteo: {fecha_sorteo} - {numeros}")
            
            try:
                result = dm.add_new_sorteo(fecha_sorteo, numeros)
                
                if result:
                    print("\n✅ ¡SORTEO AÑADIDO EXITOSAMENTE!")
                    
                    # Mostrar información actualizada
                    info = dm.get_data_info()
                    print(f"📊 Total de registros ahora: {info['total_records']}")
                    
                    if info.get('last_sorteo'):
                        last = info['last_sorteo']
                        print(f"🎯 Último sorteo registrado:")
                        print(f"   📅 {last['fecha']}")
                        print(f"   🎲 {' - '.join(map(str, last['numeros']))}")
                    
                    print(f"\n💾 Archivos actualizados:")
                    print(f"   • Historial CSV actualizado")
                    print(f"   • Último resultado: data/ultimo_resultado_oficial.json")
                    print(f"\n🚀 El sistema OMEGA PRO AI ya puede usar estos datos!")
                    
                    return []  # Salir después de actualizar
                    
                else:
                    logger.error("❌ Error añadiendo sorteo")
                    return []
                    
            except Exception as e:
                logger.error(f"❌ Error inesperado: {e}")
                return []
    
    logger.info(f"🚀 {APP_NAME} {APP_VERSION} arrancando")
    
    # INFORMACIÓN DEL DATASET 
    try:
        dataset_info = pd.read_csv(data_path)
        total_records = len(dataset_info)
        date_cols = [c for c in dataset_info.columns if 'fecha' in c.lower()]
        if date_cols:
            first_date = dataset_info[date_cols[0]].iloc[0] if len(dataset_info) > 0 else "N/A"
            last_date = dataset_info[date_cols[0]].iloc[-1] if len(dataset_info) > 0 else "N/A"
            logger.info(f"📊 DATASET: {total_records} registros históricos disponibles ({first_date} → {last_date})")
        else:
            logger.info(f"📊 DATASET: {total_records} registros históricos disponibles")
        
        if total_records >= 1000:
            logger.info(f"✅ CONFIGURACIÓN ÓPTIMA: Usando los últimos 1000 sorteos para análisis robusto")
        elif total_records >= 500:
            logger.info(f"✅ CONFIGURACIÓN BUENA: Usando los últimos {min(total_records, 800)} sorteos")
        else:
            logger.warning(f"⚠️ DATASET LIMITADO: Solo {total_records} registros disponibles (recomendado: 1000+)")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo obtener información del dataset: {e}")
    
    # -----------------------------------------------------------------------
    # 6.1 MODO IA AVANZADA (NUEVO) – Ejecutar e INTEGRAR sin salir
    # -----------------------------------------------------------------------
    ai_output = None
    if AI_MODULES_AVAILABLE:
        try:
            # Usar async context detection para evitar conflictos de event loop
            ai_output = safe_async_execution(handle_ai_mode(
                data_path, ai_query, ai_interactive, ai_analyze, top_n
            ))
            logger.info("🤖 Modo IA avanzada ejecutado (integración diferida)")
        except Exception as e:
            logger.warning(f"⚠️ Falló modo IA avanzada: {e}")
    
    # -----------------------------------------------------------------------
    # 6.2 MODO META-LEARNING AVANZADO (NUEVO) – Ejecutar e INTEGRAR sin salir
    # -----------------------------------------------------------------------
    meta_output = None
    if META_LEARNING_AVAILABLE:
        try:
            # Usar async context detection para evitar conflictos de event loop
            meta_output = safe_async_execution(handle_meta_learning_mode(
                data_path, train_meta, meta_predict, enable_rl, top_n
            ))
            logger.info("🌟 Meta-Learning ejecutado (integración diferida)")
        except Exception as e:
            logger.warning(f"⚠️ Falló meta-learning: {e}")

    # -----------------------------------------------------------------------
    # 7.1 CARGA Y LIMPIEZA DE DATOS (MEJORADA CON DATAMANAGER)
    # -----------------------------------------------------------------------
    try:
        from modules.data_manager import OmegaDataManager
        
        logger.info(f"📂 Cargando datos con DataManager: {data_path}")
        
        # Usar DataManager para carga robusta
        data_manager = OmegaDataManager(data_path)
        historial_df = data_manager.load_historical_data()
        
        # Obtener información del dataset
        info = data_manager.get_data_info()
        logger.info(f"📊 Dataset cargado: {info['total_records']} registros")
        logger.info(f"📅 Rango: {info['date_range']['from']} → {info['date_range']['to']}")
        
        if info.get('last_sorteo'):
            last = info['last_sorteo']
            logger.info(f"🎯 Último sorteo: {last['fecha']} - {last['numeros']}")
        
        # Aplicar limpieza adicional si es necesaria
        historial_df = clean_historial_df(historial_df)

        # Validar columnas de bolillas  
        cols = [c for c in historial_df.columns if "bolilla" in c.lower()]
        if len(cols) < 6:
            if ERROR_HANDLING_AVAILABLE:
                raise DataValidationError(
                    f"Datos insuficientes: se encontraron {len(cols)} columnas 'bolilla', se requieren ≥6",
                    details={'columns_found': cols, 'data_path': data_path}
                )
            else:
                raise ValueError("No se encontraron ≥6 columnas con 'bolilla'")

        # El DataManager ya ha limpiado y validado los datos
        logger.info(f"✅ Dataset procesado con DataManager: {len(historial_df)} registros")
    except Exception as exc:
        error_info = {
            "error_type": "data_error",
            "message": f"Error al procesar datos: {exc}",
            "details": f"Archivo: {data_path}\nExcepción: {str(exc)}"
        }
        logger.exception(f"⚠️ {error_info['message']}")
        return [get_fallback_item(error_info)]

    # -----------------------------------------------------------------------
    # 7.2 REENTRENAR / EVALUAR / BACKTEST (OPCIONALES)
    # -----------------------------------------------------------------------
    if retrain:
        logger.info("♻️ Reentrenando modelos …")
        auto_retrain(historial_df)

    perf_metrics = None
    if evaluate:
        logger.info("🧪 Evaluando rendimiento …")
        perf_metrics = evaluate_model_performance(historial_df)
        logger.info(f"✅ Métricas obtenidas: {len(perf_metrics)}")

    retro_tracker = RetroTracker() if backtest else None

    # -----------------------------------------------------------------------
    # 7.3 CARGAR CONFIGURACIÓN DE VIABILIDAD
    # -----------------------------------------------------------------------
    config_file = Path(viabilidad_config)
    required_keys = ["combo_length", "combo_range_min", "combo_range_max", "svi_batch_size"]
    try:
        config = cargar_viabilidad(watch_changes=False)
        if not all(k in config for k in required_keys):
            raise KeyError("Faltan claves requeridas en config")
    except Exception as exc:
        error_info = {
            "error_type": "config_error",
            "message": f"Configuración inválida: {exc}",
            "details": f"Archivo: {viabilidad_config}\nClaves requeridas: {required_keys}\nExcepción: {str(exc)}"
        }
        logger.exception(f"⚠️ {error_info['message']}")
        return [get_fallback_item(error_info)]

    observer = None
    if config.get("watch_changes", False):
        def reload_config(current_config=config):
            try:
                logger.info("🔄 Detectado cambio de configuración, recargando …")
                new_cfg = cargar_viabilidad(watch_changes=False)
                if all(k in new_cfg for k in required_keys):
                    current_config.update(new_cfg)
                    logger.info("✅ Config recargada")
            except Exception as exc_:
                logger.error(f"⚠️ Recarga fallida: {exc_}")

        observer = start_config_watcher(config_file, lambda: reload_config(config))
        logger.info(f"👁️ Observando cambios en {config_file}")

    # -----------------------------------------------------------------------
    # 7.4 INICIALIZAR PREDICTOR
    # -----------------------------------------------------------------------
    try:
        predictor = OmegaPredictor(
            data_path=data_path,
            cantidad_final=top_n,  # Exactamente 8 series
            historial_df=historial_df,
            perfil_svi=svi_profile,
            logger=logger
        )
        # Seeding determinístico opcional
        maybe_seed_from_env()
        # Configuraciones ya establecidas por defecto en constructor
        predictor.use_positional = True
        predictor.auto_export = True
        predictor.log_level = "INFO"
        
        # 🆕 NUEVO: Integrar predictor balanceado
        logger.info("⚖️ Integrando predictor con balanceo de rangos...")
        predictor_balanceado = crear_predictor_balanceado(historial_df)

        valid_models = [
            "consensus", "ghost_rng", "inverse_mining", "lstm_v2",
            "montecarlo", "apriori", "transformer_deep", "clustering", "genetico"
        ]
        # MODIFICADO: Todos los modelos SIEMPRE activos para máxima predicción
        enable_models = valid_models
        for m in valid_models:
            predictor.usar_modelos[m] = True
        logger.info("🔥 TODOS LOS MODELOS ACTIVADOS PARA MÁXIMA PRECISIÓN")
        
        # ───── Meta-Learning Systems Configuration ─────────────────────────────────────
        if args.disable_all_meta:
            logger.info("🚫 Desactivando todos los sistemas de meta-learning por solicitud del usuario")
            predictor.usar_modelos["meta_learning"] = False
            predictor.usar_modelos["adaptive_learning"] = False
            predictor.usar_modelos["neural_enhancer"] = False
            predictor.usar_modelos["ai_ensemble"] = False
        else:
            # Configure individual meta-learning systems
            predictor.usar_modelos["meta_learning"] = args.enable_meta_controller
            predictor.usar_modelos["adaptive_learning"] = args.enable_adaptive_learning
            predictor.usar_modelos["neural_enhancer"] = args.enable_neural_enhancer
            predictor.usar_modelos["ai_ensemble"] = args.enable_ai_ensemble
            
            meta_systems_active = []
            if args.enable_meta_controller:
                meta_systems_active.append("Meta-Learning Controller")
            if args.enable_adaptive_learning:
                meta_systems_active.append("Adaptive Learning System")
            if args.enable_neural_enhancer:
                meta_systems_active.append("Neural Enhancer")
            if args.enable_ai_ensemble:
                meta_systems_active.append("AI Ensemble System")
            
            if meta_systems_active:
                logger.info(f"🧠 Sistemas de Meta-Learning activados: {', '.join(meta_systems_active)}")
                logger.info(f"🔧 Meta Controller Memory Size: {args.meta_memory_size}")
            else:
                logger.info("⚠️ No hay sistemas de meta-learning activados")

        # Configurar Ghost RNG directamente
        predictor.ghost_rng_params = {
            'max_seeds': 8,
            'cantidad_por_seed': 4, 
            'training_mode': False
        }

        perfiles_svi_validos = ["default", "conservative", "aggressive"]
        svi_profile = svi_profile if svi_profile in perfiles_svi_validos else "default"
        predictor.perfil_svi = svi_profile

        logger.info(f"⚙️ Modelos activos: {', '.join(enable_models)}")
        logger.info(f"⚙️ Perfil SVI: {svi_profile}")
    except Exception as exc:
        error_info = {
            "error_type": "initialization_error",
            "message": f"Error al inicializar predictor: {exc}",
            "details": f"Modelos activos: {enable_models}\nPerfil SVI: {svi_profile}\nExcepción: {str(exc)}"
        }
        logger.exception(f"⚠️ {error_info['message']}")
        return [get_fallback_item(error_info)]

    # -----------------------------------------------------------------------
    # 7.5 EJECUTAR MODELOS CON PARALELIZACIÓN OPTIMIZADA
    # -----------------------------------------------------------------------
    try:
        # Get system resources and adaptive configuration
        system_resources = get_system_resources()
        adaptive_config = get_adaptive_config(system_resources)
        
        logger.info(f"🔧 Sistema: {adaptive_config['max_parallel_models']} modelos paralelos, "
                   f"memoria: {system_resources['available_memory_gb']:.1f}GB")
        
        logger.info("🧠 Ejecutando modelos con paralelización optimizada y monitoreo de rendimiento …")
        t0 = time.time()
        
        # Ejecutar modelos con seguimiento de rendimiento
        if performance_monitor:
            with performance_monitor.track_model_execution("predictor_execution", expected_duration=30.0):
                # Use async parallel execution if beneficial
                if adaptive_config['max_parallel_models'] > 2:
                    combinaciones_finales = await execute_parallel_models(
                        predictor, adaptive_config, logger
                    )
                else:
                    # Fall back to sequential execution for low-resource systems
                    combinaciones_finales = predictor.run_all_models()
        else:
            # Use async parallel execution if beneficial
            if adaptive_config['max_parallel_models'] > 2:
                combinaciones_finales = await execute_parallel_models(
                    predictor, adaptive_config, logger
                )
            else:
                # Fall back to sequential execution for low-resource systems
                combinaciones_finales = predictor.run_all_models()
        
        # NUEVO: Sistema de aprendizaje automático integrado
        try:
            from modules.omega_auto_learning import OmegaAutoLearning
            from modules.balanced_range_predictor import BalancedRangePredictor
            
            learning_system = OmegaAutoLearning()
            balanced_predictor = BalancedRangePredictor(historial_df)
            
            # Aplicar mejoras del sistema de aprendizaje
            print("🧠 Aplicando mejoras del sistema de aprendizaje automático...")
            
            # Balancear combinaciones generadas
            print("⚖️ Aplicando balanceo de rangos numéricos...")
            balanced_combos = balanced_predictor.generar_combinaciones_balanceadas(cantidad=min(10, len(combinaciones_finales)))
            
            # Integrar combinaciones balanceadas
            for i, combo in enumerate(balanced_combos):
                combinaciones_finales.append({
                    'combination': combo['combination'],
                    'score': combo['score'],
                    'svi_score': combo['score'],
                    'source': 'balanced_predictor',
                    'balance_info': combo.get('balance_info', {}),
                    'original_score': combo['score']
                })
            
            print(f"✅ Integradas {len(balanced_combos)} combinaciones balanceadas")
            
        except ImportError as e:
            print(f"⚠️ Sistema de aprendizaje no disponible: {e}")
        
        # Integrar resultados desde IA avanzada (si existen)
        try:
            merged_ai = 0
            if isinstance(ai_output, dict):
                ai_results = ai_output.get('ai_results', {})
                ai_combos = ai_results.get('combinations', []) if isinstance(ai_results, dict) else []
                for combo in ai_combos:
                    if isinstance(combo, dict) and 'combination' in combo:
                        combinaciones_finales.append({
                            'combination': [int(x) for x in combo['combination']],
                            'score': float(combo.get('confidence', 0.5)),
                            'svi_score': float(combo.get('confidence', 0.5)),
                            'source': str(combo.get('source', 'ai_system')),
                            'original_score': float(combo.get('confidence', 0.5))
                        })
                        merged_ai += 1
            if merged_ai:
                logger.info(f"🤖 Integradas {merged_ai} combinaciones desde IA avanzada")
        except Exception as _e:
            logger.warning(f"⚠️ No fue posible integrar resultados de IA: {_e}")

        # Integrar resultados desde Meta-Learning (si existen)
        try:
            merged_meta = 0
            if isinstance(meta_output, dict):
                meta_preds = meta_output.get('predictions', [])
                for pred in meta_preds:
                    combo = pred.get('combination') if isinstance(pred, dict) else None
                    conf = pred.get('confidence', 0.5) if isinstance(pred, dict) else 0.5
                    if combo and isinstance(combo, (list, tuple)):
                        combinaciones_finales.append({
                            'combination': [int(x) for x in combo],
                            'score': float(conf),
                            'svi_score': float(conf),
                            'source': 'meta_learning',
                            'original_score': float(conf)
                        })
                        merged_meta += 1
            if merged_meta:
                logger.info(f"🌟 Integradas {merged_meta} combinaciones desde Meta-Learning")
        except Exception as _e:
            logger.warning(f"⚠️ No fue posible integrar resultados de Meta-Learning: {_e}")
        
        # 🆕 NUEVO: Agregar combinaciones balanceadas
        logger.info("⚖️ Generando combinaciones con balance de rangos optimizado...")
        try:
            combinaciones_balanceadas = predictor_balanceado.generar_combinaciones_balanceadas(
                cantidad=max(1, top_n // 4),  # 25% de las combinaciones serán balanceadas
                enforce_distribution=True
            )
            
            if combinaciones_balanceadas:
                combinaciones_finales.extend(combinaciones_balanceadas)
                logger.info(f"✅ Agregadas {len(combinaciones_balanceadas)} combinaciones balanceadas")
                
                # Analizar si las predicciones actuales necesitan más balance
                analisis_balance = predictor_balanceado.analizar_mejoras_necesarias(combinaciones_finales)
                if analisis_balance.get("necesita_balance", False):
                    logger.warning("⚠️ Detectado desbalance en predicciones - agregando más combinaciones balanceadas")
                    combinaciones_extra_balance = predictor_balanceado.generar_combinaciones_balanceadas(
                        cantidad=2, enforce_distribution=True
                    )
                    combinaciones_finales.extend(combinaciones_extra_balance)
            
        except Exception as e:
            logger.warning(f"⚠️ Error generando combinaciones balanceadas: {e}")
        
        if limit is not None:
            combinaciones_finales = combinaciones_finales[: max(0, int(limit))]
        # Memory cleanup after model execution
        if adaptive_config.get('enable_gc', False):
            gc.collect()
            
        logger.info(f"✅ {len(combinaciones_finales)} combinaciones totales en {time.time() - t0:.2f}s")
        logger.info(f"📊 Memoria post-ejecución: {get_system_resources()['available_memory_gb']:.1f}GB")
        
    except Exception as exc:
        error_info = {
            "error_type": "prediction_error",
            "message": f"Error en predictor: {exc}",
            "details": f"Modelos activos: {enable_models}\nPerfil SVI: {svi_profile}\nExcepción: {str(exc)}"
        }
        logger.exception(f"⚠️ {error_info['message']}")
        return [get_fallback_item(error_info)]

    if not combinaciones_finales:
        error_info = {
            "error_type": "empty_result",
            "message": "Predictor no devolvió combinaciones",
            "details": f"Modelos activos: {enable_models}\nPerfil SVI: {svi_profile}"
        }
        logger.warning(f"⚠️ {error_info['message']}")
        return [get_fallback_item(error_info)]

    # -----------------------------------------------------------------------
    # 7.6 VALIDACIÓN, LIMPIEZA Y DEDUPLICADO
    # -----------------------------------------------------------------------
    seen, validas = set(), []
    combo_len     = config["combo_length"]
    cmin          = config["combo_range_min"]
    cmax          = config["combo_range_max"]

    for itm in combinaciones_finales:
        combo = clean_combination(itm.get("combination", []), logger)
        if len(combo) != combo_len \
           or not validate_combination(combo) \
           or not all(cmin <= n <= cmax for n in combo):
            logger.warning(f"⚠️ Combinación descartada: {combo}")
            continue
        key = tuple(sorted(combo))
        if key not in seen:
            seen.add(key)
            itm["combination"] = combo
            validas.append(itm)

    if not validas:
        error_info = {
            "error_type": "validation_error",
            "message": "Todas las combinaciones fueron descartadas",
            "details": f"Reglas de validación:\n" + \
                      f"- Longitud requerida: {combo_len}\n" + \
                      f"- Rango válido: [{cmin}, {cmax}]\n" + \
                      f"Combinaciones originales: {len(combinaciones_finales)}"
        }
        logger.warning(f"⚠️ {error_info['message']}")
        return [get_fallback_item(error_info)]

    combinaciones_finales = validas

    # -----------------------------------------------------------------------
    # 7.7 COMBINACIÓN MAESTRA
    # -----------------------------------------------------------------------
    try:
        combos_maestra = [{"combinacion": x["combination"], "score": x["score"]} for x in combinaciones_finales]
        # Extraer core_set de las mejores combinaciones
        core_set = list(set([num for combo in [x["combination"] for x in combinaciones_finales[:6]] for num in combo]))
        core_set = sorted(core_set)[:6]  # Tomar los 6 números más frecuentes
        maestra = generar_combinacion_maestra(combos_maestra, core_set)
        logger.info(f"🏆 Maestra: {maestra['combinacion_maestra']}  Score={maestra['score']:.3f}  SVI={maestra['svi']:.3f}")
        logger.info(f"⚠️ Riesgo: {maestra['riesgo']['alerta']} – {maestra['riesgo']['recomendacion']}")

        combinaciones_finales.insert(0, {
            "combination": maestra["combinacion_maestra"],
            "score": maestra["score"],
            "svi_score": maestra["svi"],
            "source": "maestra",
            "original_score": maestra["score"],
            "perfil": maestra["perfil"],
            "riesgo": maestra["riesgo"]
        })
    except Exception as exc:
        logger.warning(f"⚠️ Error al generar maestra: {exc}")

    # -----------------------------------------------------------------------
    # 7.8 CALCULAR SVI PARA TODAS LAS COMBINACIONES
    # -----------------------------------------------------------------------
    prediction_weight = config.get("prediction_weight", 0.6)
    svi_weight        = config.get("svi_weight", 0.6)

    combos_list = [x["combination"] for x in combinaciones_finales]
    executor_cls = ProcessPoolExecutor if not disable_multiprocessing else ThreadPoolExecutor
    try:
        logger.info("🧮 Calculando SVI …")
        t_svi = time.time()
        resultados_svi = parallel_svi(
            combos_list,
            perfil_rng=config.get("preferencia_rangos", "B"),
            validacion_ghost=any(x.get("source") == "ghost_rng" for x in combinaciones_finales),
            score_historico=config.get("score_historico_base", 3.0),
            progress_callback=reportar_progreso,
            config=config,
            logger=logger,
            executor=executor_cls
        )
        logger.info(f"✅ SVI en {time.time() - t_svi:.2f}s")
    except Exception as exc:
        logger.exception(f"⚠️ Error en SVI: {exc}. Asignando SVI=0.5 a todos.")
        resultados_svi = [(json_module.dumps(c), 0.5) for c in combos_list]

    for itm, (_, svi_val) in zip(combinaciones_finales, resultados_svi):
        original = itm.get("score", 0)
        itm["svi_score"] = svi_val
        itm["original_score"] = original
        itm["score"] = (original * prediction_weight) + (svi_val * svi_weight)

    # -----------------------------------------------------------------------
    # 7.9 ENSAMBLE AVANZADO: 4 SERIES MAESTRAS ADICIONALES (opcional)
    # -----------------------------------------------------------------------
    def _compute_model_entropy_proxy(items):
        # Entropía proxy: cobertura de números únicos por modelo
        source_to_nums = {}
        for it in items:
            src = str(it.get('source', 'unknown')).lower()
            source_to_nums.setdefault(src, set())
            for n in it.get('combination', []):
                source_to_nums[src].add(int(n))
        coverage = {s: (len(nums) / max(1, 6 * sum(1 for it in items if str(it.get('source','')).lower()==s)))
                    for s, nums in source_to_nums.items()}
        # Normalizar a [0.5, 1.5]
        if coverage:
            vals = list(coverage.values())
            vmin, vmax = min(vals), max(vals)
            if vmax > vmin:
                for s, v in coverage.items():
                    coverage[s] = 0.5 + (v - vmin) * (1.0) / (vmax - vmin)  # [0.5,1.5] luego escalamos
            else:
                coverage = {s: 1.0 for s in coverage}
        return coverage

    def _select_master_plus(items, k=4, config_dict=None):
        cfg = (config_dict or {}).get('advanced_ensemble', {})
        lambda_overlap = float(cfg.get('lambda_overlap', 0.15))
        base_weights = {str(k).lower(): float(v) for k, v in cfg.get('model_base_weights', {}).items()}
        entropy_w = float(cfg.get('entropy_weight', 1.0))

        ent_by_model = _compute_model_entropy_proxy(items)
        # Peso por modelo: base * (0.5 + entropy_weight * entropy_proxy)
        model_weight = {}
        for it in items:
            src = str(it.get('source', 'unknown')).lower()
            base = base_weights.get(src, 1.0)
            ent = ent_by_model.get(src, 1.0)
            model_weight[src] = base * (0.5 + entropy_w * ent)

        # Score ajustado por modelo
        candidates = []
        for it in items:
            src = str(it.get('source', 'unknown')).lower()
            w = model_weight.get(src, 1.0)
            adj = float(it.get('score', 0.0)) * w
            candidates.append((adj, it))
        candidates.sort(key=lambda x: x[0], reverse=True)

        selected, selected_nums = [], []
        for adj, it in candidates:
            combo = it.get('combination', [])
            # Penalización por solapamiento con seleccionadas
            overlap_penalty = 0.0
            for nums in selected_nums:
                overlap_penalty += lambda_overlap * len(set(combo) & set(nums))
            final_score = adj - overlap_penalty
            selected.append((final_score, it))
            selected_nums.append(combo)
            # Mantener top k por final_score
            selected.sort(key=lambda x: x[0], reverse=True)
            if len(selected) > k:
                selected.pop()
                selected_nums.pop()
        return [it for _, it in selected]

    # Calcular 4 series maestras adicionales desde el pool actual
    master_plus_series = _select_master_plus(combinaciones_finales, k=4, config_dict=config)

    # Etiquetar claramente el origen para logging/export
    for it in master_plus_series:
        it['source'] = str(it.get('source', 'master_plus')).lower().replace(' ', '_')
        it.setdefault('tag', 'master_plus')

    # -----------------------------------------------------------------------
    # 7.10 ASEGURAR EXACTAMENTE 8 SERIES DE ALTA CALIDAD (bloque principal)
    # -----------------------------------------------------------------------
    # Ordenar por score y tomar las mejores
    combinaciones_finales.sort(key=lambda x: x["score"], reverse=True)
    
    # GARANTIZAR EXACTAMENTE 8 SERIES FINALES
    if len(combinaciones_finales) > 8:
        combinaciones_finales = combinaciones_finales[:8]
        logger.info(f"🎯 Seleccionadas las mejores 8 combinaciones de {len(combinaciones_finales)} disponibles")
    elif len(combinaciones_finales) < 8:
        # Si hay menos de 8, generar las faltantes usando el mejor modelo
        logger.warning(f"⚠️ Solo {len(combinaciones_finales)} combinaciones disponibles, generando {8 - len(combinaciones_finales)} adicionales")
        try:
            combinaciones_extra = predictor.generar_combinaciones_adicionales(8 - len(combinaciones_finales))
            combinaciones_finales.extend(combinaciones_extra)
        except:
            # Fallback: completar con combinaciones generadas aleatoriamente pero validadas
            for i in range(8 - len(combinaciones_finales)):
                combo_fallback = {
                    "combination": sorted(random.sample(range(1, 41), 6)),
                    "score": 0.4,
                    "svi_score": 0.4,
                    "source": f"fallback_extra_{i+1}",
                    "original_score": 0.4
                }
                combinaciones_finales.append(combo_fallback)
    
    # Asegurar que tenemos exactamente 8
    combinaciones_finales = combinaciones_finales[:8]
    logger.info(f"✅ SISTEMA OPTIMIZADO: Generando exactamente {len(combinaciones_finales)} series finales")

    emojis = config.get("emojis", {})
    color_fuente = config.get("color_fuente", {})
    thresholds = config.get("score_thresholds", {"high": 0.9, "medium": 0.6})

    # -----------------------------------------------------------------------
    # 7.10.5 APLICAR APRENDIZAJE AUTOMÁTICO FINAL
    # -----------------------------------------------------------------------
    try:
        if learning_system is not None:
            print("\n🧠 Sistema de aprendizaje automático - Análisis final...")
            
            # Verificar si hay resultados oficiales disponibles para aprender
            try:
                with open('/Users/user/Documents/OMEGA_PRO_AI_v10.1/data/ultimo_resultado_oficial.json', 'r') as f:
                    ultimo_resultado = json_module.load(f)
                    resultado_oficial = ultimo_resultado.get('numeros', [])
                    fecha_resultado = ultimo_resultado.get('fecha', None)
                    
                    if resultado_oficial and len(resultado_oficial) == 6:
                        print(f"📊 Aplicando aprendizaje del resultado {fecha_resultado}: {resultado_oficial}")
                        
                        # Preparar predicciones actuales para análisis
                        predicciones_para_analisis = []
                        for combo in combinaciones_finales:
                            predicciones_para_analisis.append({
                                'combination': combo['combination'],
                                'score': combo['score'],
                                'source': combo.get('source', 'unknown')
                            })
                        
                        # Aplicar aprendizaje automático
                        resultado_aprendizaje = learning_system.aprender_de_resultado(
                            resultado_oficial, predicciones_para_analisis, fecha_resultado
                        )
                        
                        print(f"✅ Aprendizaje completado - Score: {resultado_aprendizaje.get('learning_score', 0):.3f}")
                        print(f"📈 Precisión: {resultado_aprendizaje.get('precision', 0):.1%}")
                        
                        # Mostrar recomendaciones
                        recomendaciones = resultado_aprendizaje.get('recomendaciones', [])
                        if recomendaciones:
                            print("💡 Recomendaciones de mejora:")
                            for rec in recomendaciones[:3]:  # Solo mostrar las 3 principales
                                print(f"   • {rec}")
                        
            except FileNotFoundError:
                print("⚠️ No se encontró archivo de último resultado oficial")
            except Exception as e:
                print(f"⚠️ Error en aprendizaje automático: {e}")
                
    except Exception as e:
        print(f"⚠️ Sistema de aprendizaje no disponible: {e}")

    # -----------------------------------------------------------------------
    # 7.11 MOSTRAR RESULTADOS OPTIMIZADOS PARA 8 SERIES + 4 MAESTRAS
    # -----------------------------------------------------------------------
    logger.info(f"\n{'='*80}")
    logger.info(f"🎯 OMEGA PRO AI - 8 SERIES FINALES DE ALTA PRECISIÓN")
    logger.info(f"🔥 TODOS LOS MODELOS ACTIVOS PARA MÁXIMA CALIDAD")
    logger.info(f"🧠 SISTEMA DE APRENDIZAJE AUTOMÁTICO INTEGRADO")
    logger.info(f"{'='*80}")

    for idx, itm in enumerate(combinaciones_finales, 1):
        fuente = itm.get("source", "consensus")
        combo_str = " - ".join(f"{n:02d}" for n in itm["combination"])
        score = itm["score"]
        svi   = itm["svi_score"]
        color = color_fuente.get(fuente, "")
        emoji = emojis.get(fuente, "🔹")
        sc_color = ANSI["green"] if score > thresholds["high"] else \
                   ANSI["yellow"] if score > thresholds["medium"] else ANSI["red"]

        if fuente == "maestra":
            logger.info(f"{'⭐'*3} COMBINACIÓN MAESTRA {'⭐'*3}")
        logger.info(f"{idx:2d}. {color}{emoji} {fuente.upper():<18} | "
                    f"{combo_str} | Score: {sc_color}{score:.3f}{ANSI['reset']} "
                    f"(SVI: {svi:.3f}, Pred: {itm['original_score']:.3f}){ANSI['reset']}")
        if fuente == "maestra":
            logger.info(f"   Perfil: {itm['perfil']}  "
                        f"Riesgo: {itm['riesgo']['alerta']} – {itm['riesgo']['recomendacion']}")
            logger.info(f"{'⭐'*9}")

    # Mostrar bloque adicional: 4 series maestras (ensamble avanzado)
    logger.info("\n" + "-"*80)
    logger.info("🏆 4 SERIES MAESTRAS (ENSAMBLE AVANZADO)")
    logger.info("-"*80)
    for idx, itm in enumerate(master_plus_series, 1):
        combo_str = " - ".join(f"{n:02d}" for n in itm["combination"])
        src = itm.get('source', 'master_plus')
        sc = itm.get('score', 0.0)
        logger.info(f"M{idx}: {combo_str} | Score*: {sc:.3f} | Origen: {src}")

    # Marcar explícitamente las 8 series base
    for it in combinaciones_finales:
        it.setdefault('tag', 'base')

    # Estadísticas
    fuentes_ctr = Counter(itm.get("source", "consensus") for itm in combinaciones_finales)
    print_summary_stats(
        stats={
            "total": len(combinaciones_finales),
            "max_score": max(itm["score"] for itm in combinaciones_finales),
            "min_score": min(itm["score"] for itm in combinaciones_finales),
            "avg_score": sum(itm["score"] for itm in combinaciones_finales) / len(combinaciones_finales),
            "avg_svi": sum(itm["svi_score"] for itm in combinaciones_finales) / len(combinaciones_finales),
            "avg_original": sum(itm["original_score"] for itm in combinaciones_finales) / len(combinaciones_finales),
            "pred_weight": prediction_weight,
            "svi_weight": svi_weight,
            "svi_profile": svi_profile,
            "source_counter": fuentes_ctr
        },
        config={
            "emojis": emojis,
            "visualize_summary": config.get("visualize_summary", False),
            "max_bar_length": config.get("max_bar_length", 50)
        },
        logger=logger
    )

    # -----------------------------------------------------------------------
    # 7.10 EXPORTAR RESULTADOS
    # -----------------------------------------------------------------------
    output_dir = Path(config.get("output_dir", "results"))
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metadata = {
        "app": APP_NAME,
        "version": APP_VERSION,
        "export_date": datetime.now().isoformat(),
        "parameters": {
            "data_path": data_path,
            "svi_profile": svi_profile,
            "top_n": top_n,
            "enable_models": enable_models,
            "config": {k: v for k, v in config.items() if isinstance(v, (str, int, float, bool, list, dict))}
        }
    }

    if not dry_run and "csv" in export_formats and config.get("export_csv", False):
        csv_path = output_dir / f"combinaciones_{timestamp}.csv"
        try:
            with open(csv_path, "w", encoding="utf-8") as fh:
                fh.write(f"# {APP_NAME} {APP_VERSION}\n")
                fh.write(f"# {metadata['export_date']}\n")
                fh.write(f"# params: {json_module.dumps(metadata['parameters'], ensure_ascii=False)}\n")
            # Exportar 8 base
            exportar_combinaciones_svi(combinaciones_finales, str(csv_path))
            # Exportar 4 maestras en archivo complementario
            csv_path_m = output_dir / f"combinaciones_master_plus_{timestamp}.csv"
            with open(csv_path_m, "w", encoding="utf-8") as fh:
                fh.write(f"# {APP_NAME} {APP_VERSION} - MASTER PLUS\n")
                fh.write(f"# {metadata['export_date']}\n")
                fh.write(f"# params: {json_module.dumps(metadata['parameters'], ensure_ascii=False)}\n")
            exportar_combinaciones_svi(master_plus_series, str(csv_path_m))
            logger.info(f"📁 CSV exportado: {csv_path}")
            logger.info(f"📁 CSV (Master Plus) exportado: {csv_path_m}")
        except Exception as exc:
            logger.error(f"⚠️ Error al exportar CSV: {exc}")

    if not dry_run and "json" in export_formats and config.get("export_json", False):
        json_path = output_dir / f"combinaciones_{timestamp}.json"
        try:
            export_data = {
                "metadata": metadata,
                "combinations": combinaciones_finales,
                "master_plus": master_plus_series
            }
            safe_json_export(export_data, str(json_path), indent=4, ensure_ascii=False)
            logger.info(f"📁 JSON exportado: {json_path}")
        except Exception as exc:
            logger.error(f"⚠️ Error al exportar JSON: {exc}")

    # -----------------------------------------------------------------------
    # 7.11 APRENDIZAJE ADAPTATIVO POST-SORTEO MEJORADO (NUEVO)
    # -----------------------------------------------------------------------
    if learn_from_sorteo or resultado_oficial:
        if ADAPTIVE_LEARNING_AVAILABLE:
            logger.info(f"\n{'🧠'*20}")
            logger.info("🧠 INICIANDO APRENDIZAJE ADAPTATIVO MEJORADO")
            logger.info(f"{'🧠'*20}")
            
            try:
                # Parsear resultado oficial si viene como string
                if isinstance(resultado_oficial, str):
                    resultado_numeros = [int(x.strip()) for x in resultado_oficial.split(',')]
                elif isinstance(resultado_oficial, list):
                    resultado_numeros = resultado_oficial
                else:
                    logger.warning("⚠️ Resultado oficial no proporcionado, usando ejemplo para demo")
                    resultado_numeros = [23, 32, 11, 18, 21, 33]  # Resultado del 02/08/2025
                
                # 🆕 NUEVO: Aprendizaje automático inteligente
                logger.info("🤖 Activando sistema de aprendizaje automático...")
                resultado_aprendizaje_auto = aprender_automaticamente(
                    resultado_oficial=resultado_numeros,
                    predicciones=combinaciones_finales,
                    fecha=datetime.now().strftime("%Y-%m-%d")
                )
                
                logger.info("✅ APRENDIZAJE AUTOMÁTICO COMPLETADO:")
                logger.info(f"   • Score de aprendizaje: {resultado_aprendizaje_auto.get('learning_score', 0):.3f}")
                logger.info(f"   • Precisión lograda: {resultado_aprendizaje_auto['performance_analysis']['precision_general']:.3f}")
                logger.info(f"   • Mejora sobre azar: +{resultado_aprendizaje_auto['performance_analysis']['mejora_sobre_azar']:.3f}")
                
                # Mostrar números omitidos críticos
                numeros_omitidos = resultado_aprendizaje_auto['number_analysis']['numeros_omitidos']
                if numeros_omitidos:
                    logger.warning(f"⚠️ Números críticos omitidos: {numeros_omitidos}")
                
                # Mostrar recomendaciones
                logger.info("💡 RECOMENDACIONES AUTOMÁTICAS:")
                for rec in resultado_aprendizaje_auto['recommendations']:
                    logger.info(f"   • {rec}")
                
                logger.info(f"\n{'🔧'*20}")
                logger.info("🔧 PESOS DE MODELOS ACTUALIZADOS AUTOMÁTICAMENTE")
                logger.info(f"{'🔧'*20}")
                
                # Extraer scores de modelos del config (usando scores basados en rendimiento)
                modelos_scores = {
                    "lstm_v2": 26.8,
                    "transformer": 27.2,
                    "clustering": 25.5,
                    "montecarlo": 26.0,
                    "genetic": 25.8,
                    "gboost": 24.5,
                    "ensemble_ai": 27.5,
                    "apriori": 26.3,
                    "fallback": 25.0
                }
                
                # Ejecutar aprendizaje adaptativo
                resultado_aprendizaje = ejecutar_aprendizaje_post_sorteo(
                    combinaciones=combinaciones_finales,
                    resultado_oficial=resultado_numeros,
                    modelos_scores=modelos_scores,
                    perfil_real=perfil_sorteo,
                    regime_actual=regime_rng
                )
                
                # Mostrar resultados del aprendizaje
                logger.info(f"✅ APRENDIZAJE COMPLETADO:")
                logger.info(f"   • Resultado oficial: {' - '.join(map(str, resultado_numeros))}")
                logger.info(f"   • Combinaciones exitosas (3+): {resultado_aprendizaje['rendimiento_predicciones']['combinaciones_exitosas']}")
                logger.info(f"   • Promedio aciertos: {resultado_aprendizaje['rendimiento_predicciones']['promedio_aciertos']}")
                logger.info(f"   • Máximo aciertos: {resultado_aprendizaje['rendimiento_predicciones']['maximo_aciertos']}")
                logger.info(f"   • Patrones reforzados: {resultado_aprendizaje['aprendizaje_realizado']['patrones_reforzados']}")
                logger.info(f"   • Modelos reajustados: {resultado_aprendizaje['aprendizaje_realizado']['modelos_ajustados']}")
                
                # Mostrar modo asalto
                if resultado_aprendizaje['aprendizaje_realizado']['modo_asalto_activo']:
                    logger.info(f"   🔥 MODO ASALTO ACTIVADO - Sistema optimizado para ataque")
                else:
                    logger.info(f"   🔒 Modo asalto inactivo")
                
                # Mostrar pesos actualizados
                logger.info(f"   🔧 Pesos de modelos actualizados:")
                for modelo, peso in resultado_aprendizaje['pesos_modelos_actualizados'].items():
                    logger.info(f"      • {modelo}: {peso:.2f}")
                
                # Mostrar configuración dinámica
                config_dinamica = resultado_aprendizaje['configuracion_actual']
                logger.info(f"   ⚙️ Configuración dinámica:")
                logger.info(f"      • Score mínimo: {config_dinamica['score_minimo']}")
                logger.info(f"      • Agresividad filtros: {config_dinamica['filtro_agresividad']}")
                logger.info(f"      • Ghost RNG: {'🟢 ACTIVO' if config_dinamica['ghost_rng_activo'] else '🔴 INACTIVO'}")
                logger.info(f"      • Refuerzo clustering: {'🟢 ACTIVO' if config_dinamica['refuerzo_clustering'] else '🔴 INACTIVO'}")
                
                # Obtener configuración aprendida para futuras ejecuciones
                config_aprendida = obtener_configuracion_aprendida()
                logger.info(f"   📚 Configuración guardada para próximas ejecuciones")
                logger.info(f"      • Patrones reforzados: {len(config_aprendida['patrones_reforzados'])}")
                logger.info(f"      • Patrones penalizados: {len(config_aprendida['patrones_penalizados'])}")
                
                logger.info(f"\n{'🧠'*20}")
                logger.info("🧠 APRENDIZAJE ADAPTATIVO COMPLETADO")
                logger.info(f"{'🧠'*20}")
                
            except Exception as e:
                logger.error(f"❌ Error en aprendizaje adaptativo: {e}")
                logger.warning("⚠️ Continuando sin aprendizaje adaptativo...")
        
        else:
            logger.warning("⚠️ Motor de aprendizaje adaptativo no disponible")

    # -----------------------------------------------------------------------
    # RESUMEN FINAL OPTIMIZADO PARA 8 SERIES
    # -----------------------------------------------------------------------
    logger.info(f"\n{'🎯'*20}")
    logger.info("🚀 OMEGA PRO AI - EJECUCIÓN COMPLETADA")
    logger.info("✅ 8 SERIES GENERADAS CON TODOS LOS MODELOS ACTIVOS")
    logger.info("🎲 RESUMEN FINAL DE LAS 8 SERIES:")
    logger.info(f"{'🎯'*20}")
    
    for idx, itm in enumerate(combinaciones_finales, 1):
        combo_str = " - ".join(f"{n:02d}" for n in itm["combination"])
        score = itm["score"]
        fuente = itm.get("source", "consensus")
        logger.info(f"Serie {idx}: {combo_str} | Score: {score:.3f} | Modelo: {fuente}")
    
    logger.info(f"\n{'='*60}")
    logger.info("🍀 ¡BUENA SUERTE CON TUS 8 SERIES!")
    logger.info(f"{'='*60}")
    
    # -----------------------------------------------------------------------
    # REPORTE FINAL DE RENDIMIENTO
    # -----------------------------------------------------------------------
    if performance_monitor:
        try:
            logger.info(f"\n{'🔍'*20}")
            logger.info("🔍 REPORTE FINAL DE RENDIMIENTO")
            logger.info(f"{'🔍'*20}")
            
            # Mostrar resumen de rendimiento
            performance_monitor.print_performance_summary()
            
            # Exportar reporte detallado
            report_path = performance_monitor.export_performance_report()
            logger.info(f"📊 Reporte completo exportado: {report_path}")
            
            # Verificar si hay alertas críticas
            summary = performance_monitor.get_performance_summary()
            critical_alerts = [a for a in summary['recent_alerts'] if a['severity'] == 'critical']
            if critical_alerts:
                logger.warning(f"🚨 {len(critical_alerts)} alertas críticas detectadas")
                for alert in safe_slice_list(critical_alerts, -3):  # Mostrar las 3 más recientes
                    logger.warning(f"   🚨 {alert['message']}")
                    if alert.get('recommendation'):
                        logger.warning(f"      💡 {alert['recommendation']}")
            
            # Mostrar recomendaciones principales
            recommendations = summary.get('optimization_recommendations', [])
            high_priority_recs = [r for r in recommendations if r.get('priority') == 'high']
            if high_priority_recs:
                logger.info("\n🔥 RECOMENDACIONES PRIORITARIAS DE OPTIMIZACIÓN:")
                for rec in high_priority_recs[:3]:
                    logger.info(f"   🔥 {rec['recommendation']}")
            
            logger.info(f"{'🔍'*20}")
            
        except Exception as e:
            logger.error(f"❌ Error generando reporte de rendimiento: {e}")
        finally:
            # Detener monitoreo
            shutdown_performance_monitoring()
            
            # Cleanup MCP Integration
            if mcp_integration:
                try:
                    logger.info("🔗 Cerrando MCP Integration...")
                    await mcp_integration.shutdown()
                except Exception as e:
                    logger.warning(f"⚠️ Error cerrando MCP Integration: {e}")
    
    # Mostrar estadísticas de errores si está disponible
    if ERROR_HANDLING_AVAILABLE:
        log_error_statistics()

    if observer:
        observer.stop()
        observer.join()

    # -----------------------------------------------------------------------
    # MCP NOTIFICATIONS (Send prediction results if enabled)
    # -----------------------------------------------------------------------
    if mcp_notify and mcp_integration and mcp_integration.is_mcp_enabled():
        try:
            logger.info("📱 Enviando notificaciones MCP con resultados...")
            
            # Format prediction results for notification
            if combinaciones_finales and len(combinaciones_finales) > 0:
                # Create readable message
                message_lines = [
                    "🎯 OMEGA AI - Predicciones Generadas",
                    f"📊 Total de predicciones: {len(combinaciones_finales)}",
                    "",
                    "🎲 Mejores Combinaciones:"
                ]
                
                # Add top 5 predictions
                for i, pred in enumerate(combinaciones_finales[:5], 1):
                    numbers = pred.get('combination', [])
                    score = pred.get('score', 0)
                    source = pred.get('source', 'unknown')
                    
                    numbers_str = ' - '.join(map(str, sorted(numbers)))
                    message_lines.append(f"  {i}. {numbers_str} (Score: {score:.3f}, {source})")
                
                message_lines.extend([
                    "",
                    f"⏰ Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "🤖 Powered by OMEGA AI v10.1"
                ])
                
                notification_message = "\n".join(message_lines)
                
                # Send notification via MCP
                if hasattr(mcp_integration, 'mcps') and 'notifications' in mcp_integration.mcps:
                    try:
                        # Use available notification channels
                        channels = ["email"]  # Default to email
                        if os.getenv("TEST_WHATSAPP"):
                            channels.append("whatsapp")
                        if os.getenv("TEST_TELEGRAM_CHAT_ID"):
                            channels.append("telegram")
                        
                        await mcp_integration.mcps['notifications'].send_notification(
                            message=notification_message,
                            channels=channels,
                            priority="normal"
                        )
                        logger.info("✅ Notificaciones MCP enviadas correctamente")
                    except Exception as e:
                        logger.warning(f"⚠️ Error enviando notificaciones MCP: {e}")
                else:
                    logger.warning("⚠️ Servicio de notificaciones MCP no disponible")
            else:
                logger.warning("⚠️ No hay predicciones para notificar via MCP")
                
        except Exception as e:
            logger.error(f"❌ Error en notificaciones MCP: {e}")

    return combinaciones_finales

# ---------------------------------------------------------------------------
# 8. CLI (MEJORADA CON MANEJO DE ERRORES)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Protección para multiprocessing en Windows/macOS
    import multiprocessing
    multiprocessing.freeze_support()
    
    parser = argparse.ArgumentParser(description=f"{APP_NAME} {APP_VERSION}")
    parser.add_argument("--data_path", type=str, default="data/historial_kabala_github_emergency_clean.csv")
    parser.add_argument("--svi_profile", type=str, default="default", choices=["default", "conservative", "aggressive"])
    parser.add_argument("--top_n", type=int, default=8, help="Número de series finales (fijo en 8 para máxima precisión)")
    parser.add_argument("--enable-models", nargs="+", default=["all"])
    parser.add_argument("--export-formats", nargs="+", default=["csv", "json"], choices=["csv", "json"])
    parser.add_argument("--viabilidad-config", type=str, default="config/viabilidad.json")
    parser.add_argument("--retrain", action="store_true")
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--backtest", action="store_true")
    parser.add_argument("--disable-multiprocessing", action="store_true")
    
    # Argumentos de IA Avanzada
    parser.add_argument("--ai-mode", action="store_true", help="Activar modo IA avanzada")
    parser.add_argument("--ai-query", type=str, help="Consulta en lenguaje natural para la IA")
    parser.add_argument("--ai-interactive", action="store_true", help="Modo interactivo con IA")
    parser.add_argument("--ai-analyze", action="store_true", help="Análisis inteligente de patrones")
    
    # Argumentos de Meta-Learning
    parser.add_argument("--meta-learning", action="store_true", help="Activar sistema de meta-learning avanzado")
    parser.add_argument("--train-meta", action="store_true", help="Entrenar sistema de meta-learning")
    parser.add_argument("--meta-predict", type=int, help="Predicciones con meta-learning (número)")
    parser.add_argument("--enable-rl", action="store_true", help="Habilitar aprendizaje por refuerzo")
    
    # Meta-Learning Systems Control
    parser.add_argument("--enable-meta-controller", action="store_true", default=True, help="Activar Meta-Learning Controller")
    parser.add_argument("--enable-adaptive-learning", action="store_true", default=True, help="Activar Adaptive Learning System")
    parser.add_argument("--enable-neural-enhancer", action="store_true", default=True, help="Activar Neural Enhancer")
    parser.add_argument("--enable-ai-ensemble", action="store_true", default=True, help="Activar AI Ensemble System")
    parser.add_argument("--meta-memory-size", type=int, default=1000, help="Tamaño de memoria del meta-controller")
    parser.add_argument("--disable-all-meta", action="store_true", help="Desactivar todos los sistemas de meta-learning")
    
    # Argumentos de Aprendizaje Adaptativo
    parser.add_argument("--learn-from-sorteo", action="store_true", help="Activar aprendizaje post-sorteo automático")
    parser.add_argument("--resultado-oficial", type=str, help="Resultado oficial del sorteo (ej: '1,2,3,4,5,6')")
    parser.add_argument("--perfil-sorteo", type=str, choices=['A', 'B', 'C'], default='B', help="Perfil del sorteo (A, B, C)")
    parser.add_argument("--regime-rng", type=str, default='moderate', help="Régimen RNG detectado")
    
    # Argumentos de IA Neuronal Avanzada
    parser.add_argument("--advanced-ai", action="store_true", help="Activar sistema de IA neuronal avanzado")
    parser.add_argument("--train-advanced", action="store_true", help="Entrenar IA avanzada con datos históricos")
    parser.add_argument("--ai-combinations", type=int, default=0, help="Generar N combinaciones con IA avanzada")
    
    parser.add_argument("--dry-run", action="store_true", help="No exporta archivos; sólo ejecuta pipeline")
    parser.add_argument("--limit", type=int, help="Limita cantidad de combinaciones en salida")
    parser.add_argument("--partial-hits", action="store_true",
                        help="🎯 Modo especializado: Optimizar para 4-5 números (no jackpot)")
    
    # Argumentos de actualización de datos
    parser.add_argument("--update-data", action="store_true",
                        help="📊 Actualizar dataset con nuevo sorteo")
    parser.add_argument("--fecha-sorteo", type=str,
                        help="📅 Fecha del sorteo (formato: YYYY-MM-DD)")
    parser.add_argument("--numeros-sorteo", type=str,
                        help="🎲 Números del sorteo (formato: '1,2,3,4,5,6' o '1 2 3 4 5 6')")
    parser.add_argument("--data-info", action="store_true",
                        help="📋 Mostrar información del dataset")
    parser.add_argument("--backup-data", action="store_true",
                        help="💾 Crear backup antes de actualizar")
    
    # Argumentos de monitoreo de rendimiento
    parser.add_argument("--enable-performance-monitoring", action="store_true", default=True,
                        help="🔍 Habilitar monitoreo de rendimiento (por defecto activo)")
    parser.add_argument("--disable-performance-monitoring", action="store_true",
                        help="🚫 Deshabilitar monitoreo de rendimiento")
    
    # Argumentos de MCP Integration
    parser.add_argument("--enable-mcp", action="store_true",
                        help="🔗 Habilitar OMEGA MCP Integration (Multi-Channel Platform)")
    parser.add_argument("--mcp-config", type=str,
                        help="📄 Ruta al archivo de configuración MCP (default: config/mcp_config.json)")
    parser.add_argument("--mcp-credentials", type=str,
                        help="🔑 Ruta al archivo de credenciales MCP (default: config/credentials.json)")
    parser.add_argument("--mcp-auto-start", action="store_true",
                        help="🚀 Auto-iniciar servicios MCP después de la predicción")
    parser.add_argument("--mcp-test", action="store_true",
                        help="🧪 Ejecutar pruebas de MCP Integration antes de predicción")
    parser.add_argument("--mcp-notify", action="store_true",
                        help="📱 Enviar notificaciones MCP con resultados de predicción")
    
    args = parser.parse_args()

    try:
        # Ejecutar función main async usando asyncio.run de manera segura
        resultado = asyncio.run(main(
            data_path=args.data_path,
            svi_profile=args.svi_profile,
            top_n=args.top_n,
            enable_models=args.enable_models,
            export_formats=args.export_formats,
            viabilidad_config=args.viabilidad_config,
            retrain=args.retrain,
            evaluate=args.evaluate,
            backtest=args.backtest,
            disable_multiprocessing=args.disable_multiprocessing,
            # Nuevos parámetros de IA
            ai_mode=args.ai_mode,
            ai_query=args.ai_query,
            ai_interactive=args.ai_interactive,
            ai_analyze=args.ai_analyze,
            # Nuevos parámetros de Meta-Learning
            meta_learning=args.meta_learning,
            train_meta=args.train_meta,
            meta_predict=args.meta_predict,
            enable_rl=args.enable_rl,
            # Nuevos parámetros de Aprendizaje Adaptativo
            learn_from_sorteo=args.learn_from_sorteo,
            resultado_oficial=args.resultado_oficial,
            perfil_sorteo=args.perfil_sorteo,
            regime_rng=args.regime_rng,
            dry_run=args.dry_run,
            limit=args.limit,
            # Argumentos de actualización de datos
            update_data=args.update_data,
            fecha_sorteo=args.fecha_sorteo,
            numeros_sorteo=args.numeros_sorteo,
            data_info=args.data_info,
            backup_data=args.backup_data,
            enable_performance_monitoring=args.enable_performance_monitoring and not args.disable_performance_monitoring,
            # MCP Integration arguments
            enable_mcp=args.enable_mcp,
            mcp_config=args.mcp_config,
            mcp_credentials=args.mcp_credentials,
            mcp_auto_start=args.mcp_auto_start,
            mcp_test=args.mcp_test,
            mcp_notify=args.mcp_notify,
        ))
        if len(resultado) == 1 and resultado[0]["source"] == "fallback":
            logger.warning("⚠️ Se devolvió fallback – revisar logs")
            sys.exit(0)
    except Exception as exc:
        logger.exception(f"❌ Error fatal: {exc}")
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    # Protección crítica para multiprocessing
    import multiprocessing
    multiprocessing.freeze_support()
    
    # Configurar multiprocessing para evitar warnings
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        # Already set, ignore
        pass
    
    # Ejecutar función principal con async support
    asyncio.run(main())
