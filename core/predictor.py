# OMEGA_PRO_v10.1/core/predictor.py – HybridOmegaPredictor OMEGA PRO AI v10.1 – Versión Corregida

import os
import re
import math
import random
import logging
import json
import asyncio
import gc
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple, Callable
from functools import partial

# NumPy compatibility patch for deprecated aliases
try:
    from utils.numpy_compat import patch_numpy_deprecated_aliases
    patch_numpy_deprecated_aliases()
except ImportError:
    pass

import pandas as pd
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Importar función de limpieza de datos
from utils.validation import clean_historial_df

# Intentar carga de psutil para ajuste dinámico de memoria
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Importar sistema de monitoreo de rendimiento
try:
    from modules.performance_monitor import get_performance_monitor
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False

# Intentar carga de cryptography para autenticación
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# Importar motores de generación de combinaciones
from modules.utils.combinador_maestro import generar_combinacion_maestra
from core.consensus_engine import generar_combinaciones_consenso
from modules.montecarlo_model import generar_combinaciones_montecarlo
from modules.apriori_model import generar_combinaciones_apriori
from modules.transformer_model import generar_combinaciones_transformer
from modules.filters.rules_filter import FiltroEstrategico, CoberturaCore
from modules.filters.ghost_rng_generative import get_seeds
from modules.inverse_mining_engine import ejecutar_minado_inverso
from modules.score_dynamics import score_combinations, clean_combination
from utils.viabilidad import calcular_svi
from modules.exporters.exportador_svi import exportar_combinaciones_svi
from modules.clustering_engine import generar_combinaciones_clustering
from modules.genetic_model import generar_combinaciones_geneticas, GeneticConfig
from modules.evaluation.evaluador_inteligente import EvaluadorInteligente
from modules.profiling.jackpot_profiler import JackpotProfiler
from modules.lstm_model import generar_combinaciones_lstm
from modules.learning.gboost_jackpot_classifier import GBoostJackpotClassifier
from modules.reporting.frecuencia_tracker import top_numbers
from modules.calibrador_consenso import recalibrar_pesos

# ───── Imports de analizadores especializados ─────────────────────────────────────
from modules.omega_200_analyzer import analyze_last_200_draws
from modules.positional_rng_analyzer import analyze_positional_rng
from modules.entropy_fft_analyzer import analyze_entropy_fft_patterns

from utils.logging import get_logger
from utils.errors import DataLoadError, ModelLoadError, ValidationError, OmegaError
from modules.advanced_logging_metrics import get_metrics_collector, track_rare_number_detection

# ───── Meta-Learning Systems Integration ──────────────────────────────────────────
try:
    from modules.meta_learning_controller import create_meta_controller, analyze_and_optimize
    META_LEARNING_AVAILABLE = True
    print("✅ Meta-Learning Controller disponible en predictor")
except ImportError:
    META_LEARNING_AVAILABLE = False
    print("⚠️ Meta-Learning Controller no disponible en predictor")

try:
    from modules.adaptive_learning_system import create_adaptive_learning_system
    ADAPTIVE_LEARNING_AVAILABLE = True
    print("✅ Adaptive Learning System disponible en predictor")
except ImportError:
    ADAPTIVE_LEARNING_AVAILABLE = False
    print("⚠️ Adaptive Learning System no disponible en predictor")

try:
    from modules.neural_enhancer import enhance_neural_predictions
    NEURAL_ENHANCER_AVAILABLE = True
    print("✅ Neural Enhancer disponible en predictor")
except ImportError:
    NEURAL_ENHANCER_AVAILABLE = False
    print("⚠️ Neural Enhancer no disponible en predictor")

try:
    from modules.ai_ensemble_system import create_ai_ensemble, generate_intelligent_predictions
    AI_ENSEMBLE_AVAILABLE = True
    print("✅ AI Ensemble System disponible en predictor")
except ImportError:
    AI_ENSEMBLE_AVAILABLE = False
    print("⚠️ AI Ensemble System no disponible en predictor")

# Logger unificado
logger = get_logger("OmegaPredictor")

# Initialize metrics collector for advanced logging
metrics_collector = get_metrics_collector()

# === Creación automática de directorios para evitar crashes ===
paths_to_create = [
    'core/', 'modules/utils/', 'modules/filters/', 'modules/learning/', 'modules/evaluation/', 
    'modules/profiling/', 'modules/reporting/', 'utils/', 'backup/', 'data/', 'config/', 
    'models/', 'outputs/', 'results/', 'logs/', 'temp/'
]

for path in paths_to_create:
    os.makedirs(path, exist_ok=True)
logger.info("✅ Directorios clave creados o verificados.")

class HybridOmegaPredictor:
    """
    Predictor híbrido para números de lotería que combina múltiples modelos y técnicas.
    Versión corregida con todas las mejoras implementadas.
    """
    
    VALID_POSITIONS = {'B1', 'B2', 'B3', 'B4', 'B5', 'B6'}
    MIN_VALUE = 1
    MAX_VALUE = 40
    VALID_SVI_PROFILES = {'default', 'conservative', 'aggressive'}
    
    def __init__(self, data_path: Optional[str] = None, cantidad_final: int = 30, 
                 historial_df: Optional[pd.DataFrame] = None, perfil_svi: str = 'default',
                 logger: Optional[logging.Logger] = None, seed: int = 42):
        
        if cantidad_final <= 0:
            cantidad_final = 30
        
        self.data_path = data_path
        self.cantidad_final = cantidad_final
        self.logger = get_logger("OmegaPredictor")
        
        # Implementar caché de combinaciones para evitar cálculos redundantes
        self._combination_cache = {}
        self._cache_max_size = 1000  # Límite de tamaño de caché
        
        # Cargar y limpiar datos usando DataManager
        try:
            if historial_df is not None:
                self.data = historial_df
            else:
                from modules.data_manager import OmegaDataManager
                dm = OmegaDataManager(data_path) if data_path else OmegaDataManager()
                self.data = dm.load_historical_data()
        except Exception as e:
            self.logger.error(f"Error cargando datos: {e}")
            # Generar datos dummy como fallback
            self.data = pd.DataFrame(
                np.random.randint(1, 41, size=(100, 6)), 
                columns=[f'bolilla_{i}' for i in range(1, 7)]
            )
        
        # Limpiar datos
        self.data = clean_historial_df(self.data)
        
        if self.data.empty:
            self.logger.warning("⚠️ Historial vacío, generando dummy data")
            self.data = pd.DataFrame(
                np.random.randint(1, 41, size=(100, 6)), 
                columns=[f'bolilla_{i}' for i in range(1, 7)]
            )
        
        # Filtro estratégico
        self.filtro = FiltroEstrategico()
        # FIX: Extract only lottery number columns for filtro
        if not self.data.empty:
            lottery_cols = [col for col in self.data.columns if 'bolilla_' in col][:6]
            if len(lottery_cols) >= 6:
                filtro_data = self.data[lottery_cols].values.tolist()
            else:
                # Fallback: try to get first 6 numeric columns
                numeric_cols = self.data.select_dtypes(include='number').columns
                filtro_data = self.data[numeric_cols[:6]].values.tolist()
            self.filtro.cargar_historial(filtro_data)
        else:
            self.filtro.cargar_historial([])
        
        # Configuración inicial
        self.use_positional = True
        self.perfil_svi = perfil_svi if perfil_svi in self.VALID_SVI_PROFILES else 'default'
        self.auto_export = True
        self._internal_token = None
        self.log_level = 'INFO'
        self._cached_rng_seeds = None
        self.ctx = {}
        
        # Configuración de modelos
        self.ghost_rng_params = {
            'max_seeds': 8,
            'cantidad_por_seed': 4,
            'training_mode': False
        }
        
        self.inverse_mining_params = {
            'boost_strategy': 'high_values',
            'penalize': [1, 2, 3],
            'focus_positions': ['B3', 'B5'],
            'count': 12
        }
        
        # Config LSTM optimizada (epochs reducidos)
        self.lstm_config = {
            'n_steps': 5,
            'seed': seed,
            'epochs': 20,  # Optimizado: reducido de 100 a 20
            'batch_size': 16,
            'min_history': 100
        }
        
        # Flags para modelos - TODOS ACTIVOS para máxima precisión
        self.usar_modelos = {
            "consensus": True,
            "ghost_rng": True,
            "inverse_mining": True,
            "svi": True,
            "lstm_v2": True,
            "montecarlo": True,
            "apriori": True,
            "transformer_deep": True,
            "clustering": True,
            "genetico": True,
            "gboost": True,
            "profiling": True,
            "evaluador": True,
            # ───── Analizadores especializados ─────────────────────────
            "omega_200_analyzer": True,
            "positional_rng_analyzer": True,
            "entropy_fft_analyzer": True,
            # ───── Meta-Learning Systems ────────────────────────────────
            "meta_learning": META_LEARNING_AVAILABLE,
            "adaptive_learning": ADAPTIVE_LEARNING_AVAILABLE,
            "neural_enhancer": NEURAL_ENHANCER_AVAILABLE,
            "ai_ensemble": AI_ENSEMBLE_AVAILABLE
        }
        
        # Inicializar JackpotProfiler
        try:
            self.jackpot_profiler = JackpotProfiler(
                model_path="models/jackpot_profiler.pkl",
                mlb_path="models/jackpot_profiler_mlb.pkl"
            )
        except Exception as e:
            self.logger.warning(f"⚠️ Error inicializando JackpotProfiler: {e}")
            self.jackpot_profiler = None
        
        self.logger.info(f"✅ Predictor inicializado con {self.data.shape[0]} sorteos históricos")
    
    def _map_svi_profile(self, profile: str) -> str:
        """Mapea perfil SVI interno a nombre de función"""
        mapping = {
            'default': 'moderado',
            'conservative': 'conservador', 
            'aggressive': 'agresivo'
        }
        return mapping.get(profile, 'moderado')
    
    def aplicar_ghost_rng(self, resultados_rng: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aplica Ghost RNG con validación mejorada"""
        combinaciones = []
        
        if not resultados_rng or not self.usar_modelos["ghost_rng"]:
            self.logger.info("⚠️ Ghost RNG omitido")
            return combinaciones
        
        # Validar y limpiar seeds
        valid_seeds = []
        for r in resultados_rng:
            if isinstance(r, dict) and 'seed' in r and 'draw' in r:
                r.setdefault('composite_score', 1.0)
                valid_seeds.append(r)
        
        if not valid_seeds:
            self.logger.warning("⚠️ No hay seeds RNG válidas")
            return combinaciones
        
        # Tomar los mejores seeds
        top_seeds = sorted(valid_seeds, key=lambda x: x['composite_score'], reverse=True)
        top_seeds = top_seeds[:self.ghost_rng_params['max_seeds']]
        
        for seed_data in top_seeds:
            clean_combo = clean_combination(seed_data['draw'], self.logger)
            if clean_combo and len(clean_combo) == 6:
                score = seed_data['composite_score'] * 1.10
                combinaciones.append({
                    "combination": clean_combo,
                    "source": "ghost_rng",
                    "score": score,
                    "ghost_ok": True,
                    "seed": seed_data['seed'],
                    "metrics": {"composite_score": seed_data['composite_score']},
                    "normalized": 0.0
                })
        
        self.logger.info(f"✅ Ghost RNG: {len(combinaciones)} combos")
        return combinaciones
    
    def aplicar_minado_inverso(self, ultima_combinacion: List[int]) -> List[Dict[str, Any]]:
        """Aplica minado inverso con validación"""
        if not self.usar_modelos["inverse_mining"]:
            return []
        
        clean_last = clean_combination(ultima_combinacion, self.logger)
        if not clean_last or len(clean_last) != 6:
            self.logger.warning("⚠️ Ultima combinación inválida, skipping minado inverso")
            return []
        
        # Configurar boost
        boost = (
            [n for n in clean_last if n > 20]
            if self.inverse_mining_params['boost_strategy'] == 'high_values'
            else [clean_last[-1]]
        )
        
        try:
            raw_results = ejecutar_minado_inverso(
                seed=clean_last,
                boost=boost,
                penalize=self.inverse_mining_params['penalize'],
                focus_positions=self.inverse_mining_params['focus_positions'],
                count=self.inverse_mining_params['count'],
                historial_df=self.data,
                mostrar=False
            )
        except Exception as e:
            self.logger.error(f"🚨 Error en minado inverso: {e}")
            return []
        
        # Procesar resultados
        result = []
        for item in raw_results:
            combo = clean_combination(item.get("combination", []), self.logger)
            if combo and len(combo) == 6:
                score = item.get("score", 1.0) * (
                    1.15 if self.inverse_mining_params['boost_strategy'] == 'high_values' else 1.10
                )
                result.append({
                    "combination": combo,
                    "source": "inverse_mining", 
                    "score": score,
                    "ghost_ok": False,
                    "metrics": {"minado_score": item.get("score", 0)},
                    "normalized": 0.0
                })
        
        self.logger.info(f"✅ Minado inverso: {len(result)} combos")
        return result
    
    def filtrar_combinaciones(self, combinaciones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtra combinaciones usando core_set y filtros estratégicos"""
        if not combinaciones:
            return []
        
        final = []
        
        # Calcular core_set de números más frecuentes
        clean_combinations = []
        for item in combinaciones:
            combo = clean_combination(item.get("combination", []), self.logger)
            if combo and len(combo) == 6:
                clean_combinations.append(combo)
        
        if clean_combinations:
            core_set = top_numbers(clean_combinations, top=6)
            self.logger.info(f"🔍 Core_set calculado: {core_set}")
        else:
            core_set = []
            self.logger.warning("⚠️ No hay combinaciones válidas para calcular core_set")
        
        # Crear filtro de cobertura with enhanced rare number support
        # Reduce minimum hits requirement to allow more diverse combinations
        min_hits_required = max(2, min(3, len(core_set) // 2)) if core_set else 2
        cobertura_filter = CoberturaCore(core_set, min_hits=min_hits_required, penalizar=True, factor_penalizacion=0.90) if core_set else None
        
        for item in combinaciones:
            combo = clean_combination(item.get("combination", []), self.logger)
            if not combo or len(combo) != 6:
                continue
            
            try:
                # Aplicar filtro de cobertura
                if cobertura_filter:
                    cobertura_ok, cobertura_score = cobertura_filter.apply(combo)
                else:
                    cobertura_ok, cobertura_score = True, 1.0
                
                if cobertura_ok:
                    # Aplicar filtros estratégicos
                    score, _ = self.filtro.aplicar_filtros(
                        combo, 
                        return_score=True,
                        perfil_svi=self._map_svi_profile(self.perfil_svi)
                    )
                else:
                    score = 0.0
                    
            except Exception as e:
                self.logger.debug(f"Error en filtro para {combo}: {e}")
                continue
            
            # Umbral según perfil (reduced for rare number acceptance)
            thresholds = {'moderado': 0.55, 'conservador': 0.65, 'agresivo': 0.30}
            threshold = thresholds.get(self._map_svi_profile(self.perfil_svi), 0.55)
            
            if score >= threshold:
                item["combination"] = combo
                item["score"] *= score
                item.setdefault("metrics", {})["filtro_score"] = score
                item["metrics"]["cobertura_score"] = cobertura_score
                item["normalized"] = 0.0
                final.append(item)
        
        return final
    
    def calcular_svi_para_combinaciones(self, combinaciones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calcula SVI para cada combinación"""
        if not self.usar_modelos["svi"] or not combinaciones:
            return combinaciones
        
        results = []
        for combo in combinaciones:
            c = combo.get("combination", [])
            clean_combo = clean_combination(c, self.logger)
            
            if not clean_combo or len(clean_combo) != 6:
                continue
                
            try:
                combo_str = str(clean_combo)
                svi = calcular_svi(
                    combinacion=combo_str,
                    perfil_rng=self._map_svi_profile(self.perfil_svi),
                    validacion_ghost=combo.get("ghost_ok", False),
                    score_historico=combo.get("score", 1.0)
                )
                
                combo["combination"] = clean_combo
                combo["svi_score"] = svi
                combo["score"] *= svi
                combo.setdefault("metrics", {})["svi_score"] = svi
                combo["normalized"] = 0.0
                results.append(combo)
                
            except Exception as e:
                self.logger.debug(f"Error calculando SVI: {e}")
                continue
        
        return results
    
    def _run_consensus(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta modelo de consenso con caché integrado"""
        try:
            # Verificar caché de combinaciones
            cache_key = f'consensus_{hash(str(self.data.values.tobytes()))}_{max_comb}'
            if cache_key in self._combination_cache:
                return self._combination_cache[cache_key]
            
            df = self.data.select_dtypes(include='number')
            if df.shape[1] < 6:
                raise RuntimeError("Historial sin al menos 6 columnas numéricas para consenso")
            
            raw = generar_combinaciones_consenso(
                historial_df=df,
                cantidad=max_comb,
                perfil_svi=self._map_svi_profile(self.perfil_svi),
                logger=self.logger,
                use_score_combinations=False
            )
            
            results = []
            for item in raw:
                combo = clean_combination(item["combination"], self.logger)
                if combo and len(combo) == 6:
                    results.append({
                        "combination": combo,
                        "source": item.get("source", "consensus"),
                        "score": item.get("score", 1.0),
                        "metrics": item.get("metrics", {}),
                        "normalized": 0.0
                    })
            
            # Actualizar caché
            self._combination_cache[cache_key] = results
            
            # Limpiar caché si supera el límite
            if len(self._combination_cache) > self._cache_max_size:
                # Eliminar las entradas más antiguas
                oldest_keys = sorted(
                    self._combination_cache.keys(), 
                    key=lambda k: self._combination_cache[k][0]['score'] if self._combination_cache[k] else 0
                )[:len(self._combination_cache) - self._cache_max_size]
                for key in oldest_keys:
                    del self._combination_cache[key]
            
            return results
            
        except Exception as e:
            self.logger.error(f"🚨 Error en consenso: {e}")
            return []
    
    def _run_lstm(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta modelo LSTM con configuración optimizada"""
        try:
            # FIX: Extract only lottery number columns (bolilla_1 through bolilla_6)
            lottery_cols = [col for col in self.data.columns if 'bolilla_' in col][:6]
            if len(lottery_cols) >= 6:
                data_array = self.data[lottery_cols].values
            else:
                # Fallback: try to get first 6 numeric columns
                numeric_cols = self.data.select_dtypes(include='number').columns
                data_array = self.data[numeric_cols[:6]].values
            
            if data_array.shape[0] < self.lstm_config['min_history']:
                return []
            if data_array.shape[0] < self.lstm_config['n_steps'] + 1:
                return []
            
            historial = data_array.tolist()
            historial_set = {tuple(sorted(map(int, d))) for d in historial}
            
            raw = generar_combinaciones_lstm(
                data=data_array,
                historial_set=historial_set,
                cantidad=max_comb,
                logger=self.logger,
                config=self.lstm_config,
                enable_adaptive_config=True  # Enable 65-70% accuracy targeting
            )
            
            results = []
            for item in raw:
                clean_combo = clean_combination(item.get("combination", []), self.logger)
                if clean_combo and len(clean_combo) == 6:
                    results.append({
                        "combination": clean_combo,
                        "source": "lstm_v2",
                        "score": item.get("score", 1.0),
                        "metrics": item.get("metrics", {}),
                        "normalized": 0.0
                    })
            return results
            
        except Exception as e:
            self.logger.error(f"🚨 Error en LSTM: {e}")
            # Fallback
            fallback = sorted(random.sample(range(1, 41), 6))
            return [{
                "combination": fallback,
                "source": "lstm_fallback",
                "score": 0.5,
                "metrics": {"fallback_reason": str(e)},
                "normalized": 0.0
            }]
    
    def _run_montecarlo(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta modelo Monte Carlo"""
        try:
            # FIX: Extract only lottery number columns (bolilla_1 through bolilla_6)
            lottery_cols = [col for col in self.data.columns if 'bolilla_' in col][:6]
            if len(lottery_cols) >= 6:
                historial_data = self.data[lottery_cols].values.tolist()
            else:
                # Fallback: try to get first 6 numeric columns
                numeric_cols = self.data.select_dtypes(include='number').columns
                historial_data = self.data[numeric_cols[:6]].values.tolist()
            
            raw = generar_combinaciones_montecarlo(
                historial=historial_data,
                cantidad=max_comb,
                logger=self.logger
            )
            
            results = []
            for item in raw:
                clean_combo = clean_combination(item.get("combination", []), self.logger)
                if clean_combo and len(clean_combo) == 6:
                    results.append({
                        "combination": clean_combo,
                        "source": "montecarlo",
                        "score": item.get("score", 1.0),
                        "metrics": item.get("metrics", {}),
                        "normalized": 0.0
                    })
            return results
            
        except Exception as e:
            self.logger.error(f"🚨 Error en Montecarlo: {e}")
            return []
    
    def _run_apriori(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta modelo Apriori"""
        try:
            # FIX: Extract only lottery number columns (bolilla_1 through bolilla_6)
            lottery_cols = [col for col in self.data.columns if 'bolilla_' in col][:6]
            if len(lottery_cols) >= 6:
                historial = self.data[lottery_cols].values.tolist()
            else:
                # Fallback: try to get first 6 numeric columns
                numeric_cols = self.data.select_dtypes(include='number').columns
                historial = self.data[numeric_cols[:6]].values.tolist()
                
            raw = generar_combinaciones_apriori(
                data=historial,
                historial_set={tuple(sorted(c)) for c in historial},
                num_predictions=max_comb,
                logger=self.logger
            )
            
            results = []
            for item in raw:
                clean_combo = clean_combination(item.get("combination", []), self.logger)
                if clean_combo and len(clean_combo) == 6:
                    results.append({
                        "combination": clean_combo,
                        "source": "apriori",
                        "score": item.get("score", 1.0),
                        "metrics": item.get("metrics", {}),
                        "normalized": 0.0
                    })
            return results
            
        except Exception as e:
            self.logger.error(f"🚨 Error en Apriori: {e}")
            return []
    
    def _run_transformer(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta modelo Transformer"""
        try:
            if self.data.empty:
                raise ValueError("Data empty for transformer")
                
            raw = generar_combinaciones_transformer(
                historial_df=self.data,
                cantidad=max_comb,
                perfil_svi=self._map_svi_profile(self.perfil_svi),
                logger=self.logger
            )
            
            results = []
            for item in raw:
                clean_combo = clean_combination(item.get("combination", []), self.logger)
                if clean_combo and len(clean_combo) == 6:
                    results.append({
                        "combination": clean_combo,
                        "source": "transformer_deep",
                        "score": item.get("score", 1.0),
                        "metrics": item.get("metrics", {}),
                        "normalized": 0.0
                    })
            return results
            
        except Exception as e:
            self.logger.error(f"🚨 Error en Transformer: {e}")
            # Fallback manual
            results = []
            for _ in range(min(max_comb, 5)):
                clean_combo = sorted(random.sample(range(1, 41), 6))
                results.append({
                    "combination": clean_combo,
                    "source": "transformer_fallback",
                    "score": random.uniform(0.5, 0.8),
                    "metrics": {},
                    "normalized": 0.0
                })
            return results
    
    def _run_clustering(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta modelo de clustering"""
        try:
            raw = generar_combinaciones_clustering(
                historial_df=self.data,
                cantidad=max_comb,
                logger=self.logger
            )
            
            results = []
            for item in raw:
                clean_combo = clean_combination(item.get("combination", []), self.logger)
                if clean_combo and len(clean_combo) == 6:
                    results.append({
                        "combination": clean_combo,
                        "source": "clustering",
                        "score": item.get("score", 1.0),
                        "metrics": item.get("metrics", {}),
                        "normalized": 0.0
                    })
            return results
            
        except Exception as e:
            self.logger.error(f"🚨 Error en Clustering: {e}")
            return []
    
    def _run_genetico(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta algoritmo genético"""
        try:
            # FIX: Extract only lottery number columns (bolilla_1 through bolilla_6)
            lottery_cols = [col for col in self.data.columns if 'bolilla_' in col][:6]
            if len(lottery_cols) >= 6:
                lottery_data = self.data[lottery_cols]
                historial_list = lottery_data.values.tolist()
            else:
                # Fallback: try to get first 6 numeric columns
                numeric_cols = self.data.select_dtypes(include='number').columns
                lottery_data = self.data[numeric_cols[:6]]
                historial_list = lottery_data.values.tolist()
                
            historial_set = {tuple(sorted(map(int, x))) for x in historial_list}
            # Use optimized config for 65-70% accuracy with timeout protection
            genetic_config = GeneticConfig(
                pop_size=15,  # Further reduced for faster execution
                generations=5,  # Further reduced for faster execution
                timeout_seconds=10,  # More strict timeout
                early_convergence_threshold=0.005  # Less strict convergence
            )
            
            # Use thread-safe timeout approach instead of signals
            def run_genetic_safe():
                """Run genetic algorithm safely without signal handling"""
                try:
                    return generar_combinaciones_geneticas(
                        data=lottery_data,
                        historial_set=historial_set,
                        cantidad=max_comb,
                        config=genetic_config,
                        logger=self.logger
                    )
                except Exception as e:
                    self.logger.error(f"Genetic algorithm internal error: {e}")
                    return []
            
            try:
                # Run genetic algorithm (timeout handled internally by genetic_config.timeout_seconds)
                raw = run_genetic_safe()
            except Exception as e:
                self.logger.warning(f"⏰ Genetic algorithm failed: {e}, using fallback")
                raw = []
            
            results = []
            for item in raw:
                clean_combo = clean_combination(item.get("combination", []), self.logger)
                if clean_combo and len(clean_combo) == 6:
                    score = item.get("score", item.get("fitness", 0) / 100)
                    results.append({
                        "combination": clean_combo,
                        "source": "genetico",
                        "score": score,
                        "metrics": item.get("metrics", {"fitness": item.get("fitness", 0)}),
                        "normalized": 0.0
                    })
            return results
            
        except Exception as e:
            self.logger.error(f"🚨 Error en Genético: {e}")
            return []
    
    def _run_omega_200_analyzer(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta analizador de últimos 200 sorteos"""
        if not self.usar_modelos.get("omega_200_analyzer", True):
            return []
            
        try:
            result = analyze_last_200_draws(self.data)
            if not result.get('success', False):
                self.logger.warning("⚠️ Omega 200 Analyzer falló")
                return []
                
            combinations = result.get('optimized_combinations', [])
            insights = result.get('insights', {})
            
            formatted_results = []
            for combo in combinations[:max_comb]:
                if isinstance(combo, list) and len(combo) == 6:
                    clean_combo = clean_combination(combo, self.logger)
                    if clean_combo:
                        score = 0.75 + (len(insights.get('recommended_numbers', [])) * 0.02)
                        formatted_results.append({
                            "combination": clean_combo,
                            "source": "omega_200_analyzer",
                            "score": score,
                            "metrics": {
                                "confidence_score": insights.get('confidence_score', 0.0),
                                "recommended_count": len(insights.get('recommended_numbers', [])),
                                "analyzer": "omega_200"
                            },
                            "normalized": 0.0
                        })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"🚨 Error en Omega 200 Analyzer: {e}")
            return []
    
    def _run_positional_rng_analyzer(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta analizador RNG posicional"""
        if not self.usar_modelos.get("positional_rng_analyzer", True):
            return []
            
        try:
            # Crear archivo temporal CSV para el analyzer
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                self.data.to_csv(f.name, index=False)
                temp_path = f.name
            
            try:
                result = analyze_positional_rng(temp_path)
                if not result:
                    self.logger.warning("⚠️ Positional RNG Analyzer falló")
                    return []
                    
                strategy = result.get('exploit_strategy', {})
                recommended_combinations = strategy.get('recommended_combinations', [])
                overall_confidence = strategy.get('overall_confidence', 0.0)
                
                formatted_results = []
                for combo in recommended_combinations[:max_comb]:
                    if isinstance(combo, list) and len(combo) == 6:
                        clean_combo = clean_combination(combo, self.logger)
                        if clean_combo:
                            score = 0.70 + (overall_confidence * 0.30)
                            formatted_results.append({
                                "combination": clean_combo,
                                "source": "positional_rng_analyzer",
                                "score": score,
                                "metrics": {
                                    "overall_confidence": overall_confidence,
                                    "analyzer": "positional_rng",
                                    "position_strategies_count": len(strategy.get('position_strategies', {}))
                                },
                                "normalized": 0.0
                            })
                
                return formatted_results
                
            finally:
                # Cleanup temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"🚨 Error en Positional RNG Analyzer: {e}")
            return []
    
    def _run_entropy_fft_analyzer(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta analizador de entropía y FFT"""
        if not self.usar_modelos.get("entropy_fft_analyzer", True):
            return []
            
        try:
            # Crear archivo temporal CSV para el analyzer
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                self.data.to_csv(f.name, index=False)
                temp_path = f.name
            
            try:
                result = analyze_entropy_fft_patterns(temp_path)
                if not result:
                    self.logger.warning("⚠️ Entropy & FFT Analyzer falló")
                    return []
                    
                combined_analysis = result.get('combined_analysis', {})
                
                # Generar combinaciones basadas en el análisis
                formatted_results = []
                exploitable_positions = []
                
                # Identificar posiciones explotables
                for position, analysis in combined_analysis.items():
                    exploitability_score = analysis.get('exploitability_score', 0.0)
                    if exploitability_score > 0.3:
                        exploitable_positions.append((position, analysis))
                
                # Generar combinaciones sintéticas
                for i in range(max_comb):
                    combination = []
                    
                    # Usar números recomendados de posiciones explotables
                    for pos, analysis in exploitable_positions[:6]:
                        recommendations = analysis.get('recommendations', [])
                        if recommendations:
                            pos_num = int(pos.split('_')[1]) if '_' in pos else (i % 6 + 1)
                            preferred_range = [10 + pos_num*5, 15 + pos_num*5]
                            num = preferred_range[0] + (i % (preferred_range[1] - preferred_range[0] + 1))
                            if 1 <= num <= 40 and num not in combination:
                                combination.append(num)
                    
                    # Completar combinación
                    while len(combination) < 6:
                        num = np.random.randint(1, 41)
                        if num not in combination:
                            combination.append(num)
                    
                    clean_combo = clean_combination(sorted(combination), self.logger)
                    if clean_combo:
                        base_score = 0.60
                        entropy_boost = min(0.25, len(exploitable_positions) * 0.05)
                        score = base_score + entropy_boost
                        
                        formatted_results.append({
                            "combination": clean_combo,
                            "source": "entropy_fft_analyzer",
                            "score": score,
                            "metrics": {
                                "exploitable_positions": len(exploitable_positions),
                                "analyzer": "entropy_fft",
                                "entropy_boost": entropy_boost
                            },
                            "normalized": 0.0
                        })
                
                return formatted_results
                
            finally:
                # Cleanup temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"🚨 Error en Entropy & FFT Analyzer: {e}")
            return []
    
    def _run_meta_learning_controller(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta el controlador de meta-aprendizaje"""
        if not self.usar_modelos.get("meta_learning", False) or not META_LEARNING_AVAILABLE:
            return []
            
        try:
            self.logger.info("🧠 Ejecutando Meta-Learning Controller...")
            
            # Validar entrada
            if self.data.empty:
                self.logger.warning("⚠️ Historial vacío para Meta-Learning Controller")
                return []
                
            if len(self.data) < 20:
                self.logger.warning(f"⚠️ Historial insuficiente para Meta-Learning Controller: {len(self.data)} < 20")
                return []
            
            # Crear controlador de meta-aprendizaje
            meta_controller = create_meta_controller(memory_size=1000)
            
            # Preparar datos históricos
            numeric_cols = self.data.select_dtypes(include='number').columns[:6]
            historical_data = self.data[numeric_cols].values.tolist()
            
            # Analizar contexto y obtener pesos optimizados
            context, optimal_weights = analyze_and_optimize(meta_controller, historical_data)
            
            # Generar combinaciones basadas en el análisis del contexto
            formatted_results = []
            
            for i in range(max_comb):
                try:
                    # Generar combinación usando información del contexto
                    if hasattr(context, 'regime') and hasattr(context.regime, 'value'):
                        if context.regime.value == "high_frequency_low_variance":
                            combo = self._generate_low_variance_combo(historical_data, i)
                        elif context.regime.value == "low_frequency_high_variance":
                            combo = self._generate_high_variance_combo(historical_data, i)
                        else:
                            combo = self._generate_balanced_combo(historical_data, i)
                    else:
                        combo = self._generate_balanced_combo(historical_data, i)
                    
                    if combo and len(combo) == 6:
                        # Calcular confianza basada en el contexto
                        confidence = min(0.95, 0.70 + (getattr(context, 'entropy', 0.5) * 0.25))
                        
                        formatted_results.append({
                            "combination": sorted(combo),
                            "source": "meta_learning",
                            "score": confidence,
                            "metrics": {
                                "context_regime": getattr(context.regime, 'value', 'balanced') if hasattr(context, 'regime') else 'balanced',
                                "entropy": getattr(context, 'entropy', 0.5),
                                "variance": getattr(context, 'variance', 0.5),
                                "trend_strength": getattr(context, 'trend_strength', 0.5),
                                "analyzer": "meta_learning",
                                "optimal_weights": optimal_weights
                            },
                            "normalized": 0.0
                        })
                        
                except Exception as combo_error:
                    self.logger.debug(f"Error procesando combo meta-learning {i}: {combo_error}")
                    continue
            
            self.logger.info(f"✅ Meta-Learning Controller: {len(formatted_results)} combinaciones generadas")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"🚨 Error crítico en Meta-Learning Controller: {e}")
            return []

    def _run_adaptive_learning_system(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta el sistema de aprendizaje adaptativo"""
        if not self.usar_modelos.get("adaptive_learning", False) or not ADAPTIVE_LEARNING_AVAILABLE:
            return []
            
        try:
            self.logger.info("🌟 Ejecutando Adaptive Learning System...")
            
            # Validar entrada
            if self.data.empty:
                self.logger.warning("⚠️ Historial vacío para Adaptive Learning System")
                return []
            
            # Crear sistema de aprendizaje adaptativo
            adaptive_system = create_adaptive_learning_system(enable_all=True)
            
            # Preparar datos históricos
            numeric_cols = self.data.select_dtypes(include='number').columns[:6]
            historical_data = self.data[numeric_cols].values.tolist()
            
            # Generar predicciones adaptativas usando safe async execution
            prediction_results = {"predictions": []}
            try:
                # Import async utilities for safe execution
                from utils.async_utils import safe_run_async
                
                # Safe async execution - handles event loop conflicts automatically
                self.logger.debug("🔄 Ejecutando predicciones adaptativas de forma segura")
                prediction_results = safe_run_async(
                    adaptive_system.generate_adaptive_predictions(historical_data, max_comb)
                )
                self.logger.info(f"✅ Predicciones adaptativas generadas: {len(prediction_results.get('predictions', []))}")
                
            except Exception as async_error:
                self.logger.warning(f"⚠️ Error en predicciones adaptativas: {async_error}")
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
                    self.logger.debug(f"Error procesando predicción adaptativa: {pred_error}")
                    continue
            
            self.logger.info(f"✅ Adaptive Learning System: {len(formatted_results)} combinaciones generadas")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"🚨 Error crítico en Adaptive Learning System: {e}")
            return []

    def _run_neural_enhancer(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta el potenciador neuronal"""
        if not self.usar_modelos.get("neural_enhancer", False) or not NEURAL_ENHANCER_AVAILABLE:
            return []
            
        try:
            self.logger.info("🚀 Ejecutando Neural Enhancer...")
            
            # Validar entrada
            if self.data.empty:
                self.logger.warning("⚠️ Historial vacío para Neural Enhancer")
                return []
                
            if len(self.data) < 50:
                self.logger.warning(f"⚠️ Historial insuficiente para Neural Enhancer: {len(self.data)} < 50")
                return []
            
            # Ejecutar predicciones neuronales mejoradas
            result = enhance_neural_predictions(self.data, max_comb)
            
            if not result.get('success', False):
                self.logger.warning("⚠️ Neural Enhancer falló en el entrenamiento")
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
                    self.logger.debug(f"Error procesando predicción neural: {pred_error}")
                    continue
            
            self.logger.info(f"✅ Neural Enhancer: {len(formatted_results)} combinaciones generadas")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"🚨 Error crítico en Neural Enhancer: {e}")
            return []

    def _run_ai_ensemble_system(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta el sistema de ensemble de IA"""
        if not self.usar_modelos.get("ai_ensemble", False) or not AI_ENSEMBLE_AVAILABLE:
            return []
            
        try:
            self.logger.info("🤖 Ejecutando AI Ensemble System...")
            
            # Validar entrada
            if self.data.empty:
                self.logger.warning("⚠️ Historial vacío para AI Ensemble System")
                return []
                
            if len(self.data) < 10:
                self.logger.warning(f"⚠️ Historial insuficiente para AI Ensemble System: {len(self.data)} < 10")
                return []
            
            # Crear sistema de ensemble de IA
            ensemble_system = create_ai_ensemble()
            
            # Preparar datos históricos
            numeric_cols = self.data.select_dtypes(include='number').columns[:6]  
            historical_data = self.data[numeric_cols].values.tolist()
            
            # Entrenar el ensemble con datos históricos
            ensemble_system.train_ensemble(historical_data)
            
            # Generar predicciones inteligentes usando safe async execution
            predictions = []
            try:
                # Import async utilities for safe execution
                from utils.async_utils import safe_run_async
                
                # Safe async execution - handles event loop conflicts automatically
                self.logger.debug("🔄 Ejecutando ensemble inteligente de forma segura")
                predictions = safe_run_async(
                    generate_intelligent_predictions(ensemble_system, historical_data, max_comb)
                )
                self.logger.info(f"✅ Predicciones ensemble generadas: {len(predictions)}")
                
            except Exception as async_error:
                self.logger.warning(f"⚠️ Error en ensemble inteligente: {async_error}")
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
                    self.logger.debug(f"Error procesando predicción ensemble: {pred_error}")
                    continue
            
            self.logger.info(f"✅ AI Ensemble System: {len(formatted_results)} combinaciones generadas")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"🚨 Error crítico en AI Ensemble System: {e}")
            return []
    
    # Helper methods for meta-learning combination generation
    def _generate_low_variance_combo(self, historical_data: List[List[int]], seed: int) -> List[int]:
        """Genera combinación con baja varianza (números más estables)"""
        from collections import Counter
        import numpy as np
        
        # Contar frecuencia de números
        all_numbers = [n for combo in historical_data for n in combo]
        frequency = Counter(all_numbers)
        
        # Seleccionar números más frecuentes
        most_common = [num for num, _ in frequency.most_common(15)]
        
        # Generar combinación con variación controlada
        np.random.seed(seed + 100)
        if len(most_common) >= 4:
            base_numbers = np.random.choice(most_common, size=4, replace=False)
            additional = np.random.choice([n for n in range(1, 41) if n not in base_numbers], size=2, replace=False)
            return sorted(list(base_numbers) + list(additional))
        else:
            # Fallback
            return sorted(random.sample(range(1, 41), 6))

    def _generate_high_variance_combo(self, historical_data: List[List[int]], seed: int) -> List[int]:
        """Genera combinación con alta varianza (números menos frecuentes)"""
        from collections import Counter
        import numpy as np
        
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
            return sorted(list(rare_numbers) + list(common_numbers))
        else:
            # Fallback si no hay suficientes números raros
            return sorted(random.sample(range(1, 41), 6))

    def _generate_balanced_combo(self, historical_data: List[List[int]], seed: int) -> List[int]:
        """Genera combinación balanceada"""
        import numpy as np
        
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
    
    def run_all_models(self) -> List[Dict[str, Any]]:
        """Ejecuta todos los modelos y genera predicciones finales con monitoreo de rendimiento"""
        self.logger.info("🚀 Iniciando pipeline de predicción con monitoreo")
        
        # Initialize adaptive configuration from system resources
        system_resources = self._get_system_resources()
        adaptive_config = self._get_adaptive_config(system_resources)
        
        # Obtener monitor de rendimiento si está disponible
        performance_monitor = None
        if PERFORMANCE_MONITORING_AVAILABLE:
            try:
                performance_monitor = get_performance_monitor()
            except Exception as e:
                self.logger.warning(f"⚠️ No se pudo obtener monitor de rendimiento: {e}")
        
        core_set = []  # Inicializar core_set para evitar NameError
        
        # Ajustar max_comb según memoria disponible
        max_comb = 500
        if PSUTIL_AVAILABLE:
            try:
                mem = psutil.virtual_memory().available / 1024**2
                max_comb = min(500, int(mem / 10))
                self.logger.debug(f"🔧 max_comb ajustado: {max_comb}")
            except:
                pass
        
        # Definir modelos a ejecutar
        models = [
            ("consensus", self._run_consensus, max_comb // 8),
            ("lstm_v2", self._run_lstm, max_comb // 8), 
            ("montecarlo", self._run_montecarlo, max_comb // 8),
            ("apriori", self._run_apriori, max_comb // 8),
            ("transformer_deep", self._run_transformer, max_comb // 8),
            ("clustering", self._run_clustering, max_comb // 8),
            ("genetico", self._run_genetico, max_comb // 8),
            # ───── Analizadores especializados ─────────────────────────
            ("omega_200_analyzer", self._run_omega_200_analyzer, max_comb // 10),
            ("positional_rng_analyzer", self._run_positional_rng_analyzer, max_comb // 10),
            ("entropy_fft_analyzer", self._run_entropy_fft_analyzer, max_comb // 10),
            # ───── Meta-Learning Systems ────────────────────────────────
            ("meta_learning", self._run_meta_learning_controller, max_comb // 8),
            ("adaptive_learning", self._run_adaptive_learning_system, max_comb // 8),
            ("neural_enhancer", self._run_neural_enhancer, max_comb // 8),
            ("ai_ensemble", self._run_ai_ensemble_system, max_comb // 8)
        ]
        
        combinaciones = []
        
        # Ejecutar modelos principales con monitoreo
        for name, fn, cnt in models:
            if self.usar_modelos.get(name, True):
                self.logger.info(f"⚙️ Ejecutando modelo: {name}")
                
                # Usar monitoreo de rendimiento si está disponible
                if performance_monitor:
                    try:
                        with performance_monitor.track_model_execution(name, expected_duration=15.0):
                            model_results = fn(cnt)
                            if isinstance(model_results, list):
                                combinaciones.extend(model_results)
                            del model_results  # Liberar memoria
                    except TimeoutError:
                        self.logger.error(f"⏰ TIMEOUT: {name} excedió tiempo límite")
                        if performance_monitor:
                            performance_monitor.record_fallback_usage(name, "timeout")
                        # Usar fallback simple para este modelo
                        fallback_combo = {
                            "combination": sorted(random.sample(range(1, 41), 6)),
                            "source": f"{name}_fallback_timeout",
                            "score": 0.3,
                            "svi_score": 0.3,
                            "metrics": {"timeout": True},
                            "normalized": 0.0
                        }
                        combinaciones.append(fallback_combo)
                    except Exception as e:
                        self.logger.error(f"🚨 {name} falló: {e}")
                        if performance_monitor:
                            performance_monitor.record_fallback_usage(name, f"error: {str(e)[:50]}")
                else:
                    # Ejecución sin monitoreo (método original)
                    try:
                        model_results = fn(cnt)
                        if isinstance(model_results, list):
                            combinaciones.extend(model_results)
                        del model_results  # Liberar memoria
                    except Exception as e:
                        self.logger.error(f"🚨 {name} falló: {e}")
        
        # Ghost RNG con monitoreo
        if self.usar_modelos.get("ghost_rng", True):
            if performance_monitor:
                try:
                    with performance_monitor.track_model_execution("ghost_rng", expected_duration=10.0):
                        if self._cached_rng_seeds is None:
                            self._cached_rng_seeds = get_seeds(
                                historial_csv_path=self.data_path,
                                sorteos_reales_path=None,
                                perfil_svi=self._map_svi_profile(self.perfil_svi),
                                max_seeds=self.ghost_rng_params['max_seeds'],
                                training_mode=self.ghost_rng_params['training_mode']
                            )
                        
                        # Validar seeds
                        if not self._cached_rng_seeds or not isinstance(self._cached_rng_seeds, list):
                            self.logger.warning("⚠️ Seeds RNG inválidas, generando alternativas")
                            self._cached_rng_seeds = [{
                                'seed': random.randint(1000, 9999),
                                'draw': random.sample(range(1, 41), 6),
                                'composite_score': random.uniform(0.7, 0.95)
                            } for _ in range(self.ghost_rng_params['max_seeds'])]
                        
                        combinaciones.extend(self.aplicar_ghost_rng(self._cached_rng_seeds))
                        
                except TimeoutError:
                    self.logger.error("⏰ TIMEOUT: Ghost RNG excedió tiempo límite")
                    performance_monitor.record_fallback_usage("ghost_rng", "timeout")
                except Exception as e:
                    self.logger.error(f"🚨 Error generando Ghost RNG: {e}")
                    performance_monitor.record_fallback_usage("ghost_rng", f"error: {str(e)[:50]}")
            else:
                try:
                    if self._cached_rng_seeds is None:
                        self._cached_rng_seeds = get_seeds(
                            historial_csv_path=self.data_path,
                            sorteos_reales_path=None,
                            perfil_svi=self._map_svi_profile(self.perfil_svi),
                            max_seeds=self.ghost_rng_params['max_seeds'],
                            training_mode=self.ghost_rng_params['training_mode']
                        )
                    
                    # Validar seeds
                    if not self._cached_rng_seeds or not isinstance(self._cached_rng_seeds, list):
                        self.logger.warning("⚠️ Seeds RNG inválidas, generando alternativas")
                        self._cached_rng_seeds = [{
                            'seed': random.randint(1000, 9999),
                            'draw': random.sample(range(1, 41), 6),
                            'composite_score': random.uniform(0.7, 0.95)
                        } for _ in range(self.ghost_rng_params['max_seeds'])]
                    
                    combinaciones.extend(self.aplicar_ghost_rng(self._cached_rng_seeds))
                    
                except Exception as e:
                    self.logger.error(f"🚨 Error generando Ghost RNG: {e}")
        
        # Minado inverso con monitoreo
        if self.usar_modelos.get("inverse_mining", True):
            if performance_monitor:
                try:
                    with performance_monitor.track_model_execution("inverse_mining", expected_duration=5.0):
                        # FIX: Extract only lottery columns for ultima combination
                        if not self.data.empty:
                            lottery_cols = [col for col in self.data.columns if 'bolilla_' in col][:6]
                            if len(lottery_cols) >= 6:
                                ultima = self.data[lottery_cols].values.tolist()[-1].copy()
                            else:
                                numeric_cols = self.data.select_dtypes(include='number').columns
                                ultima = self.data[numeric_cols[:6]].values.tolist()[-1].copy()
                        else:
                            ultima = [1,2,3,4,5,6]
                        combinaciones.extend(self.aplicar_minado_inverso(ultima))
                except TimeoutError:
                    self.logger.error("⏰ TIMEOUT: Minado inverso excedió tiempo límite")
                    performance_monitor.record_fallback_usage("inverse_mining", "timeout")
                except Exception as e:
                    self.logger.error(f"🚨 Error generando minado inverso: {e}")
                    performance_monitor.record_fallback_usage("inverse_mining", f"error: {str(e)[:50]}")
            else:
                try:
                    # FIX: Extract only lottery columns for ultima combination
                    if not self.data.empty:
                        lottery_cols = [col for col in self.data.columns if 'bolilla_' in col][:6]
                        if len(lottery_cols) >= 6:
                            ultima = self.data[lottery_cols].values.tolist()[-1].copy()
                        else:
                            numeric_cols = self.data.select_dtypes(include='number').columns
                            ultima = self.data[numeric_cols[:6]].values.tolist()[-1].copy()
                    else:
                        ultima = [1,2,3,4,5,6]
                    combinaciones.extend(self.aplicar_minado_inverso(ultima))
                except Exception as e:
                    self.logger.error(f"🚨 Error generando minado inverso: {e}")
        
        # Verificar que tenemos combinaciones
        if not combinaciones:
            self.logger.warning("⚠️ No se generaron combinaciones; retornando fallback")
            return [{
                "combination": sorted(random.sample(range(1, 41), 6)),
                "source": "fallback",
                "score": 0.5,
                "svi_score": 0.5,
                "metrics": {},
                "normalized": 0.0
            }]
        
        # Calcular SVI
        combinaciones = self.calcular_svi_para_combinaciones(combinaciones)
        
        # Dynamic scoring
        try:
            scored = score_combinations(
                combinations=combinaciones,
                historial=self.data,
                cluster_data=None,
                perfil_svi=self._map_svi_profile(self.perfil_svi),
                logger=self.logger
            )
            
            # Enhanced scoring combination: Rare number adaptive weighting
            for c in scored:
                dyn_score = c.get("score", 0.0)
                svi_score = c.get("svi_score", 0.5)
                
                # Check for rare number bonus in metrics
                rare_bonus = c.get("metrics", {}).get("rare_bonus", 0.0)
                
                # Adaptive weighting: boost dynamic score for rare number combinations
                if rare_bonus > 0.15:  # Significant rare number presence
                    # 45% SVI + 55% dynamic for rare number combinations
                    weight_svi = 0.45
                    weight_dyn = 0.55
                    c.setdefault("metrics", {})["scoring_mode"] = "rare_boosted"
                    
                    # Log rare number scoring boost application
                    combination = c.get('combination', [])
                    metrics_collector.log_rare_number_detection(
                        numbers=[n for n in combination if n in rare_numbers] if 'rare_numbers' in locals() else [],
                        frequency_scores={n: frequency_scores.get(n, 0.0) for n in combination if n in frequency_scores} if 'frequency_scores' in locals() else {},
                        boost_applied=rare_bonus,
                        combination=combination,
                        source_model="dynamic_scoring",
                        detection_method="rare_bonus_scoring",
                        scoring_mode="rare_boosted",
                        weight_svi=weight_svi,
                        weight_dynamic=weight_dyn,
                        original_score=dyn_score,
                        svi_score=svi_score
                    )
                    
                    self.logger.info(f"🚀 Rare-boosted scoring for {combination} (bonus: {rare_bonus:.3f})")
                else:
                    # 60% SVI + 40% dynamic for standard combinations  
                    weight_svi = 0.60
                    weight_dyn = 0.40
                    c.setdefault("metrics", {})["scoring_mode"] = "standard"
                
                c.setdefault("metrics", {})["dynamic_score"] = dyn_score
                c["score"] = weight_svi * svi_score + weight_dyn * (dyn_score / 5.0)
                c["normalized"] = 0.0
            
            combinaciones = scored
            self.logger.info("✅ Dynamic scoring aplicado")
            
        except Exception as e:
            self.logger.error(f"🚨 Error en dynamic scoring: {e}")
            # Fallback simple with adaptive weighting
            for c in combinaciones:
                dyn_score = random.uniform(0.5, 1.0)
                svi_score = c.get("svi_score", 0.5)
                
                # Check for rare numbers even in fallback mode
                combination = c.get("combination", [])
                rare_detected = any(num in [1, 2, 3, 12, 13, 38, 39, 40] for num in combination)  # Common rare numbers
                
                if rare_detected:
                    # Boost rare combinations in fallback too
                    c["score"] = 0.45 * svi_score + 0.55 * dyn_score
                    c.setdefault("metrics", {})["scoring_mode"] = "fallback_rare_boosted"
                    
                    # Log fallback rare number detection
                    detected_rare_nums = [num for num in combination if num in [1, 2, 3, 12, 13, 38, 39, 40]]
                    boost_applied = 0.15 * len(detected_rare_nums)  # Estimate boost
                    
                    metrics_collector.log_rare_number_detection(
                        numbers=detected_rare_nums,
                        frequency_scores={num: 0.1 for num in detected_rare_nums},  # Fallback scores
                        boost_applied=boost_applied,
                        combination=combination,
                        source_model="fallback_scoring",
                        detection_method="fallback_rare_detection",
                        scoring_mode="fallback_rare_boosted",
                        fallback_mode=True,
                        svi_score=svi_score,
                        dynamic_score=dyn_score
                    )
                else:
                    c["score"] = 0.6 * svi_score + 0.4 * dyn_score
                    c.setdefault("metrics", {})["scoring_mode"] = "fallback_standard"
                    
                c.setdefault("metrics", {})["dynamic_score"] = dyn_score
        
        # Clasificación GBoost
        if self.usar_modelos.get("gboost", True):
            try:
                clf = GBoostJackpotClassifier()
                if not clf.is_fitted_:
                    # Auto-fit con datos dummy si no está entrenado
                    X_dummy = [sorted(random.sample(range(1, 41), 6)) for _ in range(100)]
                    y_dummy = [random.randint(0, 1) for _ in range(100)]
                    clf.fit(X_dummy, y_dummy)
                    self.logger.info("⚙️ GBoost auto-fitted con dummy data")
                
                combos_list = [c["combination"] for c in combinaciones]
                gb_scores = clf.predict(combos_list)
                
                for idx, c in enumerate(combinaciones):
                    gb_score = float(gb_scores[idx])
                    c.setdefault("metrics", {})["gboost_score"] = gb_score
                    c["score"] *= gb_score
                
                self.logger.info(f"✅ GBoost aplicado a {len(combinaciones)} combos")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Clasificación GBoost omitida: {e}")
        
        # Perfilado de Jackpot
        if self.usar_modelos.get("profiling", True) and self.jackpot_profiler:
            try:
                perfil_metrics = self.jackpot_profiler.profile([c["combination"] for c in combinaciones])
                
                for combo_dict, perf_metrics in zip(combinaciones, perfil_metrics):
                    combo_dict.setdefault("metrics", {}).update(perf_metrics)
                    jackpot_prob = perf_metrics.get("jackpot_prob", 1.0)
                    combo_dict["score"] *= jackpot_prob
                
                self.logger.info(f"✅ Perfilado aplicado a {len(combinaciones)} combos")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Perfilado omitido: {e}")
        
        # Evaluador Inteligente
        if self.usar_modelos.get("evaluador", True):
            try:
                evaluator = EvaluadorInteligente()
                for combo in combinaciones:
                    try:
                        result = evaluator.evaluate(combo["combination"])
                        combo.setdefault("metrics", {})["evaluador"] = result
                    except Exception as e:
                        combo.setdefault("metrics", {})["evaluador_error"] = str(e)
                
                self.logger.info(f"✅ Evaluador aplicado a {len(combinaciones)} combos")
                
            except Exception as e:
                self.logger.warning(f"⚠️ EvaluadorInteligente omitido: {e}")
        
        # Calcular core_set with enhanced rare number integration
        series_generadas = combinaciones
        
        # Calculate traditional core set
        traditional_core = top_numbers([s["combination"] for s in series_generadas], top=4)
        
        # Add rare number boost - include historically underrepresented numbers
        historial_nums = []
        if not self.data.empty:
            lottery_cols = [col for col in self.data.columns if 'bolilla_' in col][:6]
            if len(lottery_cols) >= 6:
                historial_nums = self.data[lottery_cols].values.flatten()
            else:
                numeric_cols = self.data.select_dtypes(include='number').columns
                historial_nums = self.data[numeric_cols[:6]].values.flatten()
        
        # Enhanced rare number detection and integration with comprehensive logging
        enhanced_core = traditional_core.copy()
        if len(historial_nums) > 0:
            from collections import Counter
            freq_count = Counter([int(x) for x in historial_nums if 1 <= x <= 40])
            sorted_by_freq = sorted(freq_count.items(), key=lambda x: x[1])
            
            # Identify bottom 30% as rare (increased from 25% for better coverage)
            rare_threshold = max(1, int(len(sorted_by_freq) * 0.30))
            rare_numbers = {num for num, _ in sorted_by_freq[:rare_threshold]}
            
            # Create frequency scores for detailed logging
            total_occurrences = sum(freq_count.values())
            frequency_scores = {num: count / total_occurrences for num, count in freq_count.items() if num in rare_numbers}
            
            # Boost rare numbers that appear in current predictions
            predicted_nums = set()
            for s in series_generadas:
                predicted_nums.update(s["combination"])
            
            rare_boost = rare_numbers.intersection(predicted_nums)
            if len(rare_boost) > 0:
                # Add up to 2 most promising rare numbers to core set
                rare_boost_sorted = sorted(rare_boost, key=lambda x: sum(1 for s in series_generadas if x in s["combination"]), reverse=True)
                enhanced_core.update(rare_boost_sorted[:2])
                
                # Calculate boost applied
                boost_applied = len(rare_boost_sorted[:2]) * 0.15  # Estimate boost value
                
                # Log rare number detection event with comprehensive metrics
                metrics_collector.log_rare_number_detection(
                    numbers=list(rare_boost_sorted[:2]),
                    frequency_scores=frequency_scores,
                    boost_applied=boost_applied,
                    combination=sorted(enhanced_core),
                    source_model="core_predictor",
                    detection_method="frequency_analysis_enhanced",
                    total_historical_numbers=len(historial_nums),
                    rare_threshold_percent=30,
                    predicted_combinations_count=len(series_generadas),
                    traditional_core_size=len(traditional_core),
                    enhanced_core_size=len(enhanced_core)
                )
                
                self.logger.info(f"🔥 Rare number boost applied: {sorted(rare_boost_sorted[:2])}")
                self.logger.info(f"📊 Enhanced core set: {sorted(enhanced_core)} (size: {len(enhanced_core)})")
                self.logger.info(f"📈 Rare number frequency analysis: {len(rare_numbers)} rare numbers identified from {len(sorted_by_freq)} total numbers")
            
            # Ensure core set stays manageable (4-8 numbers optimal)
            if len(enhanced_core) > 8:
                # Keep traditional core + top rare boosts
                enhanced_core = set(list(traditional_core)[:4] + list(rare_boost_sorted[:2]))
            
            core_set = enhanced_core
        else:
            core_set = traditional_core
            
        # Ensure core set has at least 4 numbers, maximum 8
        if len(core_set) < 4:
            # Fill with most frequent from predictions
            pred_freq = Counter([n for s in series_generadas for n in s["combination"]])
            additional = {num for num, _ in pred_freq.most_common(6-len(core_set))}
            core_set = core_set.union(additional)
        elif len(core_set) > 8:
            # Keep only top 8 by combined frequency + rarity score
            core_set = set(sorted(core_set)[:8])
        
        self.ctx["core_set"] = sorted(core_set)
        self.logger.info(f"🔍 Enhanced core_set (w/rare boost): {self.ctx['core_set']}")
        
        # Aplicar filtros
        combinaciones = self.filtrar_combinaciones(combinaciones)
        if not combinaciones:
            self.logger.warning("⚠️ Todos los combos filtrados; usando fallback")
            return [{
                "combination": sorted(random.sample(range(1, 41), 6)),
                "source": "fallback",
                "score": 0.5,
                "svi_score": 0.5,
                "metrics": {},
                "normalized": 0.0
            }]
        
        # Ordenar y deduplicar
        combinaciones.sort(key=lambda x: x["score"], reverse=True)
        unique = {}
        for c in combinaciones:
            tup = tuple(sorted(c["combination"]))
            if tup not in unique:
                unique[tup] = c
        
        final = list(unique.values())[:self.cantidad_final]
        
        # Normalizar scores
        max_score = max(c["score"] for c in final) if final else 1.0
        for c in final:
            c["normalized"] = c["score"] / max_score
        
        # Generar combinación maestra
        try:
            combos_for_maestra = [{"combinacion": c["combination"], "score": c["score"]} for c in final]
            metadata_maestra = generar_combinacion_maestra(combos_for_maestra, core_set)
            
            final.append({
                "combination": metadata_maestra["combinacion_maestra"],
                "source": "maestra",
                "score": metadata_maestra["score"],
                "metrics": {"maestra_score": metadata_maestra["score"]},
                "normalized": metadata_maestra["score"] / max_score if max_score > 0 else 1.0
            })
            
            self.logger.info(f"✅ Combinación maestra generada: {metadata_maestra['combinacion_maestra']}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error generando combinación maestra: {e}")
        
        # Recalibrar pesos de modelos
        try:
            recalibrar_pesos(
                combinaciones=combinaciones,
                core_set=core_set,
                k_top=10,
                ruta_pesos="config/pesos_modelos.json"
            )
            self.logger.info("✅ Pesos de modelos recalibrados exitosamente")
        except Exception as e:
            self.logger.error(f"🚨 Error en recalibración de pesos: {e}")
        
        # Auto exportación
        if self.auto_export:
            try:
                os.makedirs("results", exist_ok=True)
                exportar_combinaciones_svi(
                    final, 
                    f"results/svi_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
            except Exception as e:
                self.logger.debug(f"Error en auto-exportación: {e}")
        
        # Cerrar profiler si existe
        if self.jackpot_profiler:
            try:
                self.jackpot_profiler.close()
            except:
                pass
        
        self.logger.info(f"🏁 Pipeline completado: {len(final)} combos finales")
        
        # Aplicar detección y corrección de sesgos sistemáticos
        try:
            from modules.bias_detector import detect_prediction_biases, correct_prediction_biases
            from modules.diversity_enhancer import enhance_prediction_diversity, validate_prediction_diversity
            
            # 1. Detectar sesgos sistemáticos
            bias_analysis = detect_prediction_biases(final)
            
            if bias_analysis.get('needs_correction', False):
                self.logger.warning(f"🔍 Detectados {len(bias_analysis['biases_detected'])} sesgos sistemáticos")
                
                # Aplicar corrección de sesgos
                final = correct_prediction_biases(final, bias_analysis)
                self.logger.info("🔧 Sesgos sistemáticos corregidos")
            
            # 2. Validar y mejorar diversidad
            diversity_validation = validate_prediction_diversity(final)
            coverage_before = diversity_validation['coverage_score']
            
            if not diversity_validation['is_diverse']:
                self.logger.warning(f"⚠️ Diversidad insuficiente: {coverage_before:.1f}% cobertura")
                self.logger.warning(f"⚠️ Números omitidos: {diversity_validation['missing_numbers']}")
                
                # Aplicar mejora de diversidad
                final = enhance_prediction_diversity(final)
                
                # Validar mejora
                diversity_validation_after = validate_prediction_diversity(final)
                coverage_after = diversity_validation_after['coverage_score']
                
                self.logger.info(f"🎯 Diversidad mejorada: {coverage_before:.1f}% → {coverage_after:.1f}%")
                if diversity_validation_after['missing_numbers']:
                    self.logger.info(f"📊 Números aún omitidos: {diversity_validation_after['missing_numbers']}")
                else:
                    self.logger.info("✅ Cobertura completa del espacio numérico lograda")
            else:
                self.logger.info(f"✅ Diversidad adecuada: {coverage_before:.1f}% cobertura")
                
        except Exception as e:
            self.logger.error(f"🚨 Error en sistema anti-sesgo: {e}")
        
        # Final memory cleanup
        if adaptive_config.get('enable_gc', False):
            gc.collect()
            
        return final
    
    def _get_system_resources(self) -> Dict:
        """Get current system resource information"""
        try:
            if PSUTIL_AVAILABLE:
                memory = psutil.virtual_memory()
                return {
                    'available_memory_gb': memory.available / (1024**3),
                    'total_memory_gb': memory.total / (1024**3),
                    'memory_percent': memory.percent,
                    'cpu_count': os.cpu_count() or 4,
                    'cpu_percent': psutil.cpu_percent(interval=0.1)
                }
        except Exception:
            pass
        
        # Fallback
        return {
            'available_memory_gb': 4.0,
            'total_memory_gb': 8.0, 
            'memory_percent': 50.0,
            'cpu_count': os.cpu_count() or 4,
            'cpu_percent': 50.0
        }
    
    def _get_adaptive_config(self, resources: Dict) -> Dict:
        """Generate adaptive configuration based on system resources"""
        config = {
            'max_parallel_models': min(6, max(2, resources['cpu_count'] // 2)),
            'max_combinations': 500 if resources['available_memory_gb'] > 4 else 200,
            'batch_size': 32 if resources['available_memory_gb'] > 6 else 16,
            'use_caching': resources['available_memory_gb'] > 3,
            'timeout_seconds': 180 if resources['cpu_percent'] < 80 else 120,
            'enable_gc': resources['memory_percent'] > 75,
            'parallel_threshold': 3  # Minimum models to justify parallel execution
        }
        
        # Conservative adjustments for high memory usage
        if resources['memory_percent'] > 80:
            config['max_combinations'] = min(100, config['max_combinations'])
            config['max_parallel_models'] = max(2, config['max_parallel_models'] // 2)
            config['enable_gc'] = True
            
        return config
    
    async def run_all_models_async(self, adaptive_config: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Async version of run_all_models with parallel execution"""
        if adaptive_config is None:
            system_resources = self._get_system_resources()
            adaptive_config = self._get_adaptive_config(system_resources)
        
        self.logger.info("🚀 Iniciando pipeline asíncrono de predicción")
        
        # Prepare model configurations for parallel execution
        max_comb_per_model = adaptive_config.get('max_combinations', 200) // 8
        
        model_configs = [
            {
                'name': 'consensus',
                'function': self._run_consensus,
                'args': [max_comb_per_model],
                'enabled': self.usar_modelos.get('consensus', True)
            },
            {
                'name': 'lstm_v2', 
                'function': self._run_lstm,
                'args': [max_comb_per_model],
                'enabled': self.usar_modelos.get('lstm_v2', True)
            },
            {
                'name': 'montecarlo',
                'function': self._run_montecarlo,
                'args': [max_comb_per_model],
                'enabled': self.usar_modelos.get('montecarlo', True)
            },
            {
                'name': 'transformer_deep',
                'function': self._run_transformer,
                'args': [max_comb_per_model],
                'enabled': self.usar_modelos.get('transformer_deep', True)
            },
            {
                'name': 'clustering',
                'function': self._run_clustering,
                'args': [max_comb_per_model],
                'enabled': self.usar_modelos.get('clustering', True)
            },
            {
                'name': 'genetico',
                'function': self._run_genetico,
                'args': [max_comb_per_model],
                'enabled': self.usar_modelos.get('genetico', True)
            },
            # ───── Analizadores especializados ─────────────────────────
            {
                'name': 'omega_200_analyzer',
                'function': self._run_omega_200_analyzer,
                'args': [max_comb_per_model],
                'enabled': self.usar_modelos.get('omega_200_analyzer', True)
            },
            {
                'name': 'positional_rng_analyzer',
                'function': self._run_positional_rng_analyzer,
                'args': [max_comb_per_model],
                'enabled': self.usar_modelos.get('positional_rng_analyzer', True)
            },
            {
                'name': 'entropy_fft_analyzer',
                'function': self._run_entropy_fft_analyzer,
                'args': [max_comb_per_model],
                'enabled': self.usar_modelos.get('entropy_fft_analyzer', True)
            }
        ]
        
        # Filter enabled models
        enabled_models = [config for config in model_configs if config['enabled']]
        
        # Execute models in parallel if we have enough models and resources
        if (len(enabled_models) >= adaptive_config.get('parallel_threshold', 3) and 
            adaptive_config.get('max_parallel_models', 2) > 2):
            
            model_results = await self._execute_models_parallel(
                enabled_models, adaptive_config
            )
        else:
            # Sequential execution for small model sets or low resources
            model_results = self._execute_models_sequential(enabled_models)
        
        # Combine all results
        combinaciones = []
        for model_name, results in model_results.items():
            if results:
                combinaciones.extend(results)
                self.logger.info(f"⚙️ {model_name}: {len(results)} combinaciones")
        
        # Continue with Ghost RNG and Inverse Mining (these are typically fast)
        if self.usar_modelos.get("ghost_rng", True):
            try:
                if self._cached_rng_seeds is None:
                    self._cached_rng_seeds = get_seeds(
                        historial_csv_path=self.data_path,
                        sorteos_reales_path=None,
                        perfil_svi=self._map_svi_profile(self.perfil_svi),
                        max_seeds=8,
                        training_mode=False
                    )
                
                if self._cached_rng_seeds:
                    combinaciones.extend(self.aplicar_ghost_rng(self._cached_rng_seeds))
                    
            except Exception as e:
                self.logger.error(f"🚨 Error generando Ghost RNG: {e}")
        
        if self.usar_modelos.get("inverse_mining", True):
            try:
                # FIX: Extract only lottery columns for ultima combination
                if not self.data.empty:
                    lottery_cols = [col for col in self.data.columns if 'bolilla_' in col][:6]
                    if len(lottery_cols) >= 6:
                        ultima = self.data[lottery_cols].values.tolist()[-1].copy()
                    else:
                        numeric_cols = self.data.select_dtypes(include='number').columns
                        ultima = self.data[numeric_cols[:6]].values.tolist()[-1].copy()
                else:
                    ultima = [1,2,3,4,5,6]
                combinaciones.extend(self.aplicar_minado_inverso(ultima))
            except Exception as e:
                self.logger.error(f"🚨 Error generando minado inverso: {e}")
        
        # Continue with rest of pipeline (SVI, scoring, filtering, etc.)
        return self._finalize_combinations(combinaciones, adaptive_config)
    
    async def _execute_models_parallel(self, model_configs: List[Dict], 
                                     adaptive_config: Dict) -> Dict[str, List]:
        """Execute models in parallel with resource management"""
        max_parallel = adaptive_config.get('max_parallel_models', 2)
        timeout = adaptive_config.get('timeout_seconds', 180)
        
        # Create semaphore to limit concurrent execution
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def run_model_with_semaphore(config):
            async with semaphore:
                return await self._execute_model_async(
                    config['name'],
                    config['function'],
                    config['args'],
                    timeout
                )
        
        # Execute models with controlled parallelism
        tasks = [run_model_with_semaphore(config) for config in model_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        model_results = {}
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"🚨 Model execution exception: {result}")
                continue
            
            model_name, model_output = result
            model_results[model_name] = model_output if model_output else []
            
            # Memory management
            if adaptive_config.get('enable_gc', False):
                gc.collect()
        
        return model_results
    
    def _execute_models_sequential(self, model_configs: List[Dict]) -> Dict[str, List]:
        """Sequential model execution fallback"""
        model_results = {}
        
        for config in model_configs:
            model_name = config['name']
            try:
                self.logger.info(f"⚙️ Ejecutando modelo: {model_name}")
                results = config['function'](*config['args'])
                model_results[model_name] = results if results else []
            except Exception as e:
                self.logger.error(f"🚨 {model_name} falló: {e}")
                model_results[model_name] = []
                
        return model_results
    
    async def _execute_model_async(self, model_name: str, model_func: Callable,
                                  args: List, timeout: int) -> Tuple[str, List]:
        """Execute a single model asynchronously with timeout"""
        loop = asyncio.get_event_loop()
        
        try:
            # Use ThreadPoolExecutor for CPU-bound operations
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = loop.run_in_executor(
                    executor,
                    partial(model_func, *args)
                )
                
                # Wait with timeout
                result = await asyncio.wait_for(future, timeout=timeout)
                return model_name, result if result else []
                
        except asyncio.TimeoutError:
            self.logger.warning(f"⏰ {model_name} timeout after {timeout}s")
            return model_name, []
        except Exception as e:
            self.logger.error(f"🚨 {model_name} failed: {e}")
            return model_name, []
    
    def _finalize_combinations(self, combinaciones: List[Dict], 
                              adaptive_config: Dict) -> List[Dict[str, Any]]:
        """Finalize combination processing (SVI, scoring, filtering)"""
        # Check if we have any combinations
        if not combinaciones:
            self.logger.warning("⚠️ No se generaron combinaciones; retornando fallback")
            return [{
                "combination": sorted(random.sample(range(1, 41), 6)),
                "source": "fallback",
                "score": 0.5,
                "svi_score": 0.5,
                "metrics": {},
                "normalized": 0.0
            }]
        
        # Continue with existing pipeline logic
        # SVI calculation
        combinaciones = self.calcular_svi_para_combinaciones(combinaciones)
        
        # Dynamic scoring with memory management
        try:
            scored = score_combinations(
                combinations=combinaciones,
                historial=self.data,
                cluster_data=None,
                perfil_svi=self._map_svi_profile(self.perfil_svi),
                logger=self.logger
            )
            
            # Enhanced scoring combination: Rare number adaptive weighting (async version)
            for c in scored:
                dyn_score = c.get("score", 0.0)
                svi_score = c.get("svi_score", 0.5)
                
                # Check for rare number bonus in metrics
                rare_bonus = c.get("metrics", {}).get("rare_bonus", 0.0)
                
                # Adaptive weighting: boost dynamic score for rare number combinations
                if rare_bonus > 0.15:  # Significant rare number presence
                    # 45% SVI + 55% dynamic for rare number combinations
                    weight_svi = 0.45
                    weight_dyn = 0.55
                    c.setdefault("metrics", {})["scoring_mode"] = "rare_boosted"
                else:
                    # 60% SVI + 40% dynamic for standard combinations  
                    weight_svi = 0.60
                    weight_dyn = 0.40
                    c.setdefault("metrics", {})["scoring_mode"] = "standard"
                
                c.setdefault("metrics", {})["dynamic_score"] = dyn_score
                c["score"] = weight_svi * svi_score + weight_dyn * (dyn_score / 5.0)
                c["normalized"] = 0.0
            
            combinaciones = scored
            self.logger.info("✅ Dynamic scoring aplicado")
            
        except Exception as e:
            self.logger.error(f"🚨 Error en dynamic scoring: {e}")
            # Continue with basic scoring
        
        # Apply filters
        combinaciones = self.filtrar_combinaciones(combinaciones)
        
        if not combinaciones:
            self.logger.warning("⚠️ Todos los combos filtrados; usando fallback")
            return [{
                "combination": sorted(random.sample(range(1, 41), 6)),
                "source": "fallback",
                "score": 0.5,
                "svi_score": 0.5,
                "metrics": {},
                "normalized": 0.0
            }]
        
        # Final processing
        combinaciones.sort(key=lambda x: x["score"], reverse=True)
        unique = {}
        for c in combinaciones:
            tup = tuple(sorted(c["combination"]))
            if tup not in unique:
                unique[tup] = c
        
        final = list(unique.values())[:self.cantidad_final]
        
        # Normalize scores
        max_score = max(c["score"] for c in final) if final else 1.0
        for c in final:
            c["normalized"] = c["score"] / max_score
        
        return final
    
    def generar_combinaciones_adicionales(self, cantidad_faltante: int) -> List[Dict[str, Any]]:
        """Generate additional combinations when needed"""
        combinaciones_extra = []
        
        try:
            # Use the best performing model to generate extras
            if self.usar_modelos.get('lstm_v2', True):
                extras = self._run_lstm(cantidad_faltante)
            elif self.usar_modelos.get('consensus', True):
                extras = self._run_consensus(cantidad_faltante)
            else:
                # Fallback to random generation
                for i in range(cantidad_faltante):
                    combo = sorted(random.sample(range(1, 41), 6))
                    combinaciones_extra.append({
                        "combination": combo,
                        "score": 0.4,
                        "svi_score": 0.4, 
                        "source": "fallback_additional",
                        "original_score": 0.4
                    })
                return combinaciones_extra
            
            # Process the generated extras
            for extra in extras[:cantidad_faltante]:
                if 'combination' in extra:
                    combinaciones_extra.append({
                        "combination": extra['combination'],
                        "score": extra.get('score', 0.4),
                        "svi_score": extra.get('score', 0.4),
                        "source": f"additional_{extra.get('source', 'model')}",
                        "original_score": extra.get('score', 0.4)
                    })
                    
        except Exception as e:
            self.logger.error(f"Error generating additional combinations: {e}")
            # Final fallback
            for i in range(cantidad_faltante):
                combo = sorted(random.sample(range(1, 41), 6))
                combinaciones_extra.append({
                    "combination": combo,
                    "score": 0.4,
                    "svi_score": 0.4,
                    "source": "fallback_error",
                    "original_score": 0.4
                })
                
        return combinaciones_extra[:cantidad_faltante]