# OMEGA_PRO_v10.1/core/predictor.py – HybridOmegaPredictor OMEGA PRO AI v10.1 – Versión Corregida

import os
import re
import math
import random
import logging
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple

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

from utils.logging import get_logger
from utils.errors import DataLoadError, ModelLoadError, ValidationError, OmegaError

# Logger unificado
logger = get_logger("OmegaPredictor")

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
        self.filtro.cargar_historial(self.data.values.tolist() if not self.data.empty else [])
        
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
            "evaluador": True
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
        
        # Crear filtro de cobertura
        cobertura_filter = CoberturaCore(core_set, min_hits=4, penalizar=False) if core_set else None
        
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
            
            # Umbral según perfil
            thresholds = {'moderado': 0.7, 'conservador': 0.8, 'agresivo': 0.4}
            threshold = thresholds.get(self._map_svi_profile(self.perfil_svi), 0.7)
            
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
        """Ejecuta modelo de consenso"""
        try:
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
            return results
            
        except Exception as e:
            self.logger.error(f"🚨 Error en consenso: {e}")
            return []
    
    def _run_lstm(self, max_comb: int) -> List[Dict[str, Any]]:
        """Ejecuta modelo LSTM con configuración optimizada"""
        try:
            data_array = self.data.values
            
            if data_array.shape[0] < self.lstm_config['min_history']:
                return []
            if data_array.shape[0] < self.lstm_config['n_steps'] + 1:
                return []
            
            historial = data_array.tolist()
            historial_set = {tuple(sorted(map(int, d))) for d in historial}
            
            raw = generar_combinaciones_lstm(
                data=data_array,
                cantidad=max_comb,
                historial_set=historial_set,
                logger=self.logger,
                config=self.lstm_config
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
            raw = generar_combinaciones_montecarlo(
                historial=self.data.values.tolist(),
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
            historial = self.data.values.tolist()
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
            historial_set = {tuple(sorted(map(int, x))) for x in self.data.values.tolist()}
            raw = generar_combinaciones_geneticas(
                data=self.data,
                historial_set=historial_set,
                cantidad=max_comb,
                config=GeneticConfig(),
                logger=self.logger
            )
            
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
    
    def run_all_models(self) -> List[Dict[str, Any]]:
        """Ejecuta todos los modelos y genera predicciones finales"""
        self.logger.info("🚀 Iniciando pipeline de predicción")
        
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
            ("genetico", self._run_genetico, max_comb // 8)
        ]
        
        combinaciones = []
        
        # Ejecutar modelos principales
        for name, fn, cnt in models:
            if self.usar_modelos.get(name, True):
                self.logger.info(f"⚙️ Ejecutando modelo: {name}")
                try:
                    model_results = fn(cnt)
                    if isinstance(model_results, list):
                        combinaciones.extend(model_results)
                    del model_results  # Liberar memoria
                except Exception as e:
                    self.logger.error(f"🚨 {name} falló: {e}")
        
        # Ghost RNG
        if self.usar_modelos.get("ghost_rng", True):
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
        
        # Minado inverso
        if self.usar_modelos.get("inverse_mining", True):
            try:
                ultima = self.data.values.tolist()[-1].copy() if not self.data.empty else [1,2,3,4,5,6]
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
            
            # Combinar scores: 60% SVI + 40% dinámico
            for c in scored:
                dyn_score = c.get("score", 0.0)
                svi_score = c.get("svi_score", 0.5)
                
                c.setdefault("metrics", {})["dynamic_score"] = dyn_score
                c["score"] = 0.6 * svi_score + 0.4 * (dyn_score / 5.0)
                c["normalized"] = 0.0
            
            combinaciones = scored
            self.logger.info("✅ Dynamic scoring aplicado")
            
        except Exception as e:
            self.logger.error(f"🚨 Error en dynamic scoring: {e}")
            # Fallback simple
            for c in combinaciones:
                dyn_score = random.uniform(0.5, 1.0)
                svi_score = c.get("svi_score", 0.5)
                c["score"] = 0.6 * svi_score + 0.4 * dyn_score
                c.setdefault("metrics", {})["dynamic_score"] = dyn_score
        
        # Clasificación GBoost
        if self.usar_modelos.get("gboost", True):
            try:
                try:
            from modules.utils.safe_model_loader import safe_load_xgboost_model
            clf = GBoostJackpotClassifier()
        except ImportError:
            logger.warning("⚠️ GBoost no disponible, usando dummy classifier")
            clf = None
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
        
        # Calcular core_set
        series_generadas = combinaciones
        core_set = top_numbers([s["combination"] for s in series_generadas], top=6)
        self.ctx["core_set"] = sorted(core_set)
        self.logger.info(f"🔍 Core_set calculado: {self.ctx['core_set']}")
        
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
        return final