# OMEGA_PRO_AI_v10.1/modules/filters/rules_filter.py

import logging
import os
import pandas as pd
import numpy as np
import json
import gzip
import shutil
import time
from collections import defaultdict, deque
from collections import Counter as CollectionsCounter  # Fix name conflict
from typing import List, Set, Tuple, Dict, Union, Optional
from joblib import Parallel, delayed
import jwt
from fastapi import FastAPI, HTTPException
import sqlite3
import matplotlib.pyplot as plt
from functools import lru_cache
import psutil
from tenacity import retry, stop_after_attempt, wait_exponential
import redis
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from datetime import datetime
from utils.logger import log_error, log_info, log_warning
from modules.filters.ghost_rng_observer import is_suspicious_seed_pattern

# --------------------------------------------------------------------------- 
# N U E V A R E G L A -> CoberturaCore 
# --------------------------------------------------------------------------- 
from typing import Set, Tuple, List # ya debe estar, pero lo incluimos por seguridad 
def _core_hits(comb: Tuple[int, ...], core_set: Set[int]) -> int: 
    """Cuenta cuántos números del core_set aparecen en la combinación.""" 
    return len(core_set.intersection(comb)) 
class CoberturaCore: 
    """ 
    Valida que la combinación incluya un mínimo de números del `core_set`. 
    Parámetros 
    ---------- 
    core_set : set[int] 
        Conjunto de los números 'calientes' calculado por frecuencia_tracker. 
    min_hits : int, default = 4 
        Mínimo de coincidencias requeridas; si no se alcanza, la serie se descarta o se penaliza (según tu flujo). 
    penalizar : bool, default = False 
        Si True aplica un factor de penalización; si False descarta por completo. 
    """ 
    def __init__(self, core_set: Set[int], min_hits: int = 4, penalizar: bool = False, factor_penalizacion: float = 0.85): 
        self.core_set = core_set 
        self.min_hits = min_hits 
        self.penalizar = penalizar 
        self.factor_penalizacion = factor_penalizacion 
    # ------------- interfaz tipo “filtro callable” ----------------- 
    def __call__(self, comb: Tuple[int, ...], score_actual: float = 0.0) -> Tuple[bool, float]: 
        """ 
        Devuelve (aceptar, nuevo_score). 
        Si se descarta => (False, score_actual) 
        Si se penaliza => (True, score_penalizado) 
        Si pasa => (True, score_actual) 
        """ 
        hits = _core_hits(comb, self.core_set) 
        if hits < self.min_hits: 
            if self.penalizar: 
                return True, score_actual * self.factor_penalizacion 
            return False, score_actual  # descartada 
        return True, score_actual  # combinación válida

# Configuración de logging
LOG_DIR = f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("filtros_logger")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(os.path.join(LOG_DIR, "filtros.log"))
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(file_handler)

# Configuración de Prometheus
prom_aprobaciones = Counter('kabala_aprobaciones_total', 'Total de combinaciones aprobadas', ['perfil_svi', 'contexto'])
prom_rechazos = Counter('kabala_rechazos_total', 'Total de combinaciones rechazadas', ['perfil_svi', 'contexto'])
prom_tasa_aprobacion = Gauge('kabala_tasa_aprobacion', 'Tasa de aprobación actual', ['perfil_svi', 'contexto'])
prom_tiempo_procesamiento = Histogram('kabala_tiempo_procesamiento_seconds', 'Tiempo de procesamiento por combinación', ['perfil_svi', 'contexto'])
prom_alertas = Counter('kabala_alertas_total', 'Total de alertas disparadas', ['nombre', 'perfil_svi', 'contexto'])

def autenticar_usuario(token: str, secret_key: str = os.path.join(LOG_DIR, "jwt_secret.key")) -> bool:
    """Autentica usuario usando JWT con expiración."""
    if not os.path.exists(secret_key):
        log_warning("Clave JWT no encontrada")
        return False
    try:
        with open(secret_key, 'rb') as f:
            key = f.read()
        jwt.decode(token, key, algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError:
        log_error("Token JWT expirado")
        return False
    except Exception as e:
        log_error(f"Error en autenticación JWT: {str(e)}")
        return False

class FiltroEstrategico:
    """Clase para aplicar filtros estratégicos a combinaciones de Kábala con optimización y análisis avanzado."""
    
    PRUEBAS_CONFIG = {
        'suma_total': {
            'fn': lambda self, comb: self.config['suma_min'] <= sum(comb) <= self.config['suma_max'],
            'msg': "Suma total fuera de rango",
            'relajable': False
        },
        'saltos': {
            'fn': lambda self, comb: self.config['saltos_min'] <= self.calcular_saltos(comb) <= self.config['saltos_max'],
            'msg': "Suma de saltos fuera de rango",
            'relajable': True
        },
        'paridad': {
            'fn': lambda self, comb: self.config['pares_min'] <= sum(1 for n in comb if n % 2 == 0) <= self.config['pares_max'],
            'msg': "Desequilibrio par/impar",
            'relajable': False
        },
        'historial': {
            'fn': lambda self, comb: tuple(sorted(comb)) not in self.get_cached_historial(),
            'msg': "Combinación histórica repetida",
            'relajable': False
        },
        'decadas': {
            'fn': lambda self, comb: (
                len(CollectionsCounter(min((int(n) - 1) // 10, 3) for n in comb)) >= self.config['decadas_min'] and 
                all(v <= self.config['max_por_decada'] for v in CollectionsCounter(min((int(n) - 1) // 10, 3) for n in comb).values())
            ),
            'msg': "Distribución por décadas inadecuada",
            'relajable': False
        },
        'repetidos': {
            'fn': lambda self, comb: not self.ultimo_sorteo or len(set(comb) & self.ultimo_sorteo) <= self.config['repetidos_ultimo'],
            'msg': "Demasiados repetidos del último sorteo",
            'relajable': True
        },
        'patrones': {
            'fn': lambda self, comb: all(tuple(sorted(comb)) != tuple(sorted(patron)) for patron in self.config['patrones_prohibidos']),
            'msg': "Coincide con patrón prohibido",
            'relajable': False
        },
        'posiciones': {
            'fn': lambda self, comb: self.posiciones_atipicas_ok(comb),
            'msg': "Número en posición atípica",
            'relajable': False
        },
        'visual': {
            'fn': lambda self, comb: not any(n in self.config['zonas_frias'] for n in comb),
            'msg': "Problema físico/visual",
            'relajable': False
        },
        'rng_sospechoso': {
            'fn': lambda self, comb: not self.penalizar_si_rng_sospechoso(comb, self.semillas_sospechosas),
            'msg': "Asociada a seed sospechosa",
            'relajable': False
        }
    }

    ALERTAS_CONFIG = {
        'baja_aprobacion': {
            'metric': lambda self: self.tasa_aprobacion(),
            'umbral': 0.15,
            'accion': lambda self: log_warning("ALERTA CRÍTICA: Tasa de aprobación < 15%"),
            'cooldown': 3600
        },
        'alta_rechazo_rng': {
            'metric': lambda self: self.estadisticas_fallos.get("Asociada a seed sospechosa", 0) / max(1, self.contador_combinaciones),
            'umbral': 0.3,
            'accion': lambda self: self.recalibrar_deteccion_rng(),
            'cooldown': 86400
        },
        'rendimiento_batch': {
            'metric': lambda self: (time.time() - self.ultimo_batch_start) if hasattr(self, 'ultimo_batch_start') else 0,
            'umbral': 60,
            'accion': lambda self: log_error("ALERTA RENDIMIENTO: Procesamiento de lote excede 1 minuto"),
            'cooldown': 300
        }
    }

    def __init__(self, config: Optional[Dict] = None, token_autenticacion: Optional[str] = None, 
                 modo_rendimiento: bool = False, seed_refresh_interval: int = 3600):
        # Caché de resultados para evitar reprocesar combinaciones
        self.cache_resultados = {}
        """Inicializa el filtro estratégico con configuración y autenticación."""
        if token_autenticacion and not autenticar_usuario(token_autenticacion):
            raise ValueError("Token de autenticación inválido")

        self.config = {
            'suma_min': 100,  # Relaxed from 105
            'suma_max': 150,  # Relaxed from 145
            'saltos_min': 20,
            'saltos_max': 40,
            'pares_min': 2,
            'pares_max': 4,
            'decadas_min': 2,  # Relaxed from 3
            'max_por_decada': 4,  # Relaxed from 3
            'repetidos_ultimo': 3,  # Relaxed from 2
            'patrones_prohibidos': [
                tuple(sorted([1, 2, 3, 4, 5, 6])),
                tuple(sorted([35, 36, 37, 38, 39, 40]))
            ],
            'umbral_asalto': 0.4,  # Relaxed from 0.65
            'umbral_custom': 0.7,  # Relaxed from 0.85
            'umbral_minimo': 0.5,  # Relaxed from 0.65
            'relajaciones': {
                'saltos_min': 15,
                'saltos_max': 45,
                'repetidos_ultimo': 4
            },
            'pesos_filtros': {
                'suma_total': 0.15,
                'saltos': 0.15,
                'paridad': 0.10,
                'historial': 0.20,
                'decadas': 0.10,
                'repetidos': 0.10,
                'patrones': 0.10,
                'posiciones': 0.05,
                'visual': 0.05,
                'rng_sospechoso': 0.10
            },
            'zonas_frias': {15, 16, 17, 18, 19}
        }

        if config:
            self.validar_config(config)
            self.config.update(config)

        self.historial_set = set()
        self.ultimo_sorteo = None
        self.frecuencia_posicional = defaultdict(lambda: defaultdict(int))
        self.estadisticas_fallos = defaultdict(int)
        self.contador_combinaciones = 0
        self.contador_aprobados = 0
        self.historial_scores = deque(maxlen=1000)
        self.ultimos_rechazos = deque(maxlen=100)
        self.alertas_activas = set()
        self.ultimas_alertas = {}
        self.semillas_sospechosas = set()
        self.modo_rendimiento = modo_rendimiento
        self.seed_refresh_interval = seed_refresh_interval
        self.last_seed_refresh = 0  # FIX: Added initialization
        self.redis_client = self.init_redis()
        self.conn = self.init_db(token_autenticacion)
        self.cargar_semillas_sospechosas()
        self.actualizar_pesos_pruebas()

    def set_threshold(self, threshold: float):
        """Establece un umbral personalizado para la aprobación de combinaciones.
        
        Args:
            threshold (float): Nuevo valor de umbral entre 0.0 y 1.0
        """
        if not 0.0 <= threshold <= 1.0:
            log_error(f"Intento de establecer umbral inválido: {threshold}")
            raise ValueError("El umbral debe estar entre 0.0 y 1.0")
        
        log_info(f"Actualizando umbral mínimo: {self.config['umbral_minimo']} -> {threshold}")
        self.config['umbral_minimo'] = threshold
        prom_tasa_aprobacion.labels(
            perfil_svi="custom", 
            contexto="manual"
        ).set(threshold)

    def init_redis(self):
        """Inicializa cliente Redis."""
        try:
            client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            client.ping()
            log_info("Conexión Redis establecida")
            return client
        except Exception as e:
            log_warning(f"No se pudo conectar a Redis: {str(e)}. Usando memoria local.")
            return None

    def validar_config(self, config: Dict):
        """Valida la configuración proporcionada."""
        if not isinstance(config, dict):
            raise ValueError("La configuración debe ser un diccionario")
        if 'suma_min' in config and (not isinstance(config['suma_min'], (int, float)) or config['suma_min'] < 0):
            raise ValueError("suma_min debe ser un número no negativo")
        if 'suma_max' in config and (not isinstance(config['suma_max'], (int, float)) or config['suma_max'] < config.get('suma_min', self.config['suma_min'])):
            raise ValueError("suma_max debe ser mayor o igual que suma_min")
        if 'patrones_prohibidos' in config:
            for pattern in config['patrones_prohibidos']:
                if not (isinstance(pattern, tuple) and len(pattern) == 6 and all(isinstance(n, int) and 1 <= n <= 40 for n in pattern)):
                    raise ValueError("patrones_prohibidos deben ser tuplas de 6 enteros entre 1 y 40")
        if 'pesos_filtros' in config:
            if abs(sum(config['pesos_filtros'].values()) - 1.0) > 0.01:
                raise ValueError("La suma de pesos_filtros debe ser aproximadamente 1.0")
        log_info("Configuración validada correctamente")

    def init_db(self, token_auth=None):
        """Inicializa base de datos SQLite con índices optimizados."""
        if token_auth and not autenticar_usuario(token_auth):
            raise ValueError("Token inválido para acceso a base de datos")
        
        db_path = ":memory:" if self.modo_rendimiento else os.path.join(LOG_DIR, "filtros.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS estadisticas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            total_combinaciones INTEGER,
            combinaciones_validas INTEGER,
            tasa_retencion REAL,
            promedio_scores REAL,
            perfil_svi TEXT,
            contexto TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS descartes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            combination TEXT,
            motivo TEXT,
            timestamp TEXT,
            perfil_svi TEXT,
            contexto TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            valor REAL,
            timestamp TEXT,
            perfil_svi TEXT,
            contexto TEXT
        )''')
        
        if not self.modo_rendimiento:
            c.execute('CREATE INDEX IF NOT EXISTS idx_estadisticas ON estadisticas (timestamp, perfil_svi, contexto)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_descartes ON descartes (timestamp, perfil_svi, contexto)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_alertas ON alertas (timestamp, nombre)')
        
        conn.commit()
        return conn

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def cargar_semillas_sospechosas(self):
        """Carga semillas sospechosas desde un archivo."""
        try:
            self.semillas_sospechosas = set()
            seeds_file = os.path.join(LOG_DIR, "suspicious_seeds.json")
            if os.path.exists(seeds_file):
                with open(seeds_file, 'r') as f:
                    seeds_data = json.load(f)
                for seed in seeds_data:
                    if isinstance(seed, list) and len(seed) == 6 and all(isinstance(n, int) and 1 <= n <= 40 for n in seed):
                        self.semillas_sospechosas.add(tuple(sorted(seed)))
            log_info(f"Cargadas {len(self.semillas_sospechosas)} semillas sospechosas")
        except Exception as e:
            log_error(f"Error cargando semillas sospechosas: {str(e)}")
            self.semillas_sospechosas = set()

    def actualizar_pesos_pruebas(self):
        """Actualiza pesos de pruebas desde configuración según perfil_svi."""
        for key in self.PRUEBAS_CONFIG:
            if key in self.config['pesos_filtros']:
                self.PRUEBAS_CONFIG[key]['peso'] = self.config['pesos_filtros'][key]

    def cargar_historial(self, data: Union[str, List[List[int]]]):
        """Carga datos históricos y los cachea en Redis."""
        try:
            if isinstance(data, str):
                df = pd.read_csv(data)
                df_numeric = df.select_dtypes(include='number').dropna()
                # Convertir a enteros después de redondear
                df_numeric = df_numeric.round().astype(int)
                historial = [tuple(sorted(row.values.astype(int))) for _, row in df_numeric.iterrows()]
            else:
                # Convertir cada combinación a enteros
                historial = [tuple(sorted(int(round(x)) for x in comb)) for comb in data]

            self.historial_set = set(historial)
            if not historial:
                log_warning("Historial vacío, no se aplicará filtro de historial")
            else:
                log_info(f"Cargado historial con {len(historial)} combinaciones")

            if self.redis_client:
                try:
                    pipe = self.redis_client.pipeline()
                    self.redis_client.delete('kabala:historial')
                    for comb in historial:
                        pipe.sadd('kabala:historial', json.dumps(comb))
                    pipe.execute()
                    log_info("Historial cacheado en Redis")
                except Exception as e:
                    log_warning(f"Error cacheando historial en Redis: {str(e)}")

            if historial:
                self.ultimo_sorteo = set(historial[-1])

            self.frecuencia_posicional = defaultdict(lambda: defaultdict(int))
            for comb in historial:
                for pos, num in enumerate(comb):
                    self.frecuencia_posicional[pos][num] += 1
            
            for pos in range(6):
                self.calcular_percentiles.cache_clear()
                _ = self.calcular_percentiles(pos)
                
        except Exception as e:
            log_error(f"Error cargando historial: {str(e)}")
            raise

    def get_cached_historial(self):
        """Obtiene historial desde Redis o memoria."""
        if self.redis_client:
            try:
                cached = self.redis_client.smembers('kabala:historial')
                historial = {tuple(json.loads(c)) for c in cached}
                if not historial:
                    log_warning("Redis devolvió historial vacío, usando memoria local")
                    return self.historial_set
                return historial
            except Exception as e:
                log_warning(f"Error accediendo Redis, usando memoria local: {str(e)}")
        if not self.historial_set:
            log_warning("Historial local vacío, no se aplicará filtro de historial")
        return self.historial_set

    def calcular_saltos(self, comb):
        """Calcula la suma de diferencias entre números consecutivos."""
        sorted_comb = sorted(comb)
        return sum(abs(sorted_comb[i] - sorted_comb[i-1]) for i in range(1, len(sorted_comb)))

    @lru_cache(maxsize=6)
    def calcular_percentiles(self, posicion: int):
        """Calcula percentiles para posición con caché."""
        frecuencias = list(self.frecuencia_posicional[posicion].values())
        total = sum(frecuencias)
        
        if total < 100 or len(frecuencias) < 10:
            return {'q1': 0, 'mediana': 0}
        
        return {
            'q1': np.percentile(frecuencias, 25),
            'mediana': np.percentile(frecuencias, 50)
        }

    def posiciones_atipicas_ok(self, comb):
        """Verifica si números están en posiciones atípicas."""
        sorted_comb = sorted(comb)
        for pos, num in enumerate(sorted_comb):
            percentiles = self.calcular_percentiles(pos)
            freq_actual = self.frecuencia_posicional[pos].get(num, 0)
            if freq_actual < percentiles['q1']:
                return False
        return True

    def penalizar_si_rng_sospechoso(self, comb: List[int], semillas_sospechosas: set) -> bool:
        """Verifica si combinación coincide con patrones de semillas sospechosas."""
        if time.time() - self.last_seed_refresh > self.seed_refresh_interval:
            self.cargar_semillas_sospechosas()
            self.last_seed_refresh = time.time()
        
        comb_tuple = tuple(sorted(comb))
        # Fast-path: observer cached heuristic
        try:
            if is_suspicious_seed_pattern(comb_tuple):
                return True
        except Exception:
            log_warning("ghost_rng_observer fallo; continuando con chequeos locales")
        for sospechosa in semillas_sospechosas:
            if len(set(comb_tuple) & set(sospechosa)) >= 4:
                return True
        return False

    def aplicar_filtros(self, comb, return_score=False, return_reasons=False, contexto="normal", perfil_svi="moderado"):
        """Aplica filtros a una combinación individual."""
        import sys
        print(f"DEBUG: applying filter to {comb}", file=sys.stderr)
        start_time = time.time()
        
        # Convertir combinación a enteros (corrección principal)
        try:
            comb = [int(round(x)) for x in comb]
        except Exception as e:
            log_error(f"Error convirtiendo combinación a enteros: {comb}, error: {str(e)}")
            if return_score and return_reasons:
                return False, 0.0, ["Error interno: conversión a entero fallida"]
            elif return_score:
                return False, 0.0
            elif return_reasons:
                return False, ["Error interno: conversión a entero fallida"]
            else:
                return False
                
        self.contador_combinaciones += 1
        razones = []
        score = 0.0
        relajado = contexto == "asalto"

        # Adjust thresholds based on perfil_svi
        umbral_normal = {'moderado': 0.85, 'conservador': 0.9, 'agresivo': 0.75}.get(perfil_svi, 0.85)
        umbral_asalto = {'moderado': 0.4, 'conservador': 0.5, 'agresivo': 0.3}.get(perfil_svi, 0.4)
        umbral_minimo = self.config['umbral_minimo']  # Usa el umbral actualizado

        try:
            self.verificar_alertas(perfil_svi, contexto)
            
            for key, prueba in self.PRUEBAS_CONFIG.items():
                peso = prueba.get('peso', 0)
                if peso <= 0:
                    continue
                
                try:
                    if prueba['fn'](self, comb):
                        score += peso
                    else:
                        razones.append(prueba['msg'])
                        self.estadisticas_fallos[prueba['msg']] += 1
                        if relajado and prueba.get('relajable', False):
                            score += peso * 0.5
                except Exception as e:
                    log_error(f"Error en prueba '{key}': {str(e)}")
            
            self.historial_scores.append(score)
            
            if contexto == "normal":
                aprobado = score >= umbral_normal
            elif contexto == "asalto":
                aprobado = score >= umbral_asalto
            else:
                aprobado = score >= self.config['umbral_custom']
            
            aprobado = aprobado and score >= umbral_minimo

            if not aprobado:
                self.ultimos_rechazos.append((comb, razones, score))
                prom_rechazos.labels(perfil_svi=perfil_svi, contexto=contexto).inc()
                log_info(f"Combinación rechazada: {comb}, Score: {score:.3f}, Razones: {razones}")
            else:
                self.contador_aprobados += 1
                prom_aprobaciones.labels(perfil_svi=perfil_svi, contexto=contexto).inc()
                log_info(f"Combinación aprobada: {comb}, Score: {score:.3f}")

            prom_tasa_aprobacion.labels(perfil_svi=perfil_svi, contexto=contexto).set(self.tasa_aprobacion())

            if self.conn:
                try:
                    c = self.conn.cursor()
                    c.execute('''INSERT INTO descartes 
                                (combination, motivo, timestamp, perfil_svi, contexto) 
                                VALUES (?, ?, ?, ?, ?)''',
                            (str(comb), '; '.join(razones), str(pd.Timestamp.now()), perfil_svi, contexto))
                    self.conn.commit()
                except Exception as e:
                    log_warning(f"Error insertando en base de datos: {str(e)}")
            
            if contexto == "normal" and self.contador_combinaciones > 100 and self.tasa_aprobacion() < self.config['umbral_asalto']:
                log_info("Activando modo asalto por baja tasa de aprobación")
                return self.aplicar_filtros(comb, return_score, return_reasons, "asalto", perfil_svi)

            if self.contador_combinaciones % 100 == 0:
                self.actualizar_umbrales_automatico()

            prom_tiempo_procesamiento.labels(perfil_svi=perfil_svi, contexto=contexto).observe(time.time() - start_time)
            
            if return_score and return_reasons:
                return aprobado, score, razones
            elif return_score:
                return aprobado, score
            elif return_reasons:
                return aprobado, razones
            else:
                return aprobado
            
        except Exception as e:
            log_error(f"Error crítico en aplicar_filtros: {str(e)}", exc_info=True)
            if return_score and return_reasons:
                return False, 0.0, ["Error interno"]
            elif return_score:
                return False, 0.0
            elif return_reasons:
                return False, ["Error interno"]
            else:
                return False

    def aplicar_filtros_batch(self, combinaciones: List[List[int]], return_score=False, return_reasons=False, contexto="normal", 
                             perfil_svi="moderado", progress_callback=None):
        """Procesa lotes de combinaciones con paralelismo y retroalimentación."""
        def chunk_generator(data, size):
            for i in range(0, len(data), size):
                yield data[i:i+size]
        
        def procesar_combinacion(comb):
            try:
                # Convertir a enteros y normalizar antes de procesar
                comb_int = tuple(sorted(int(round(x)) for x in comb))
                # Usar caché para evitar reprocesar
                if comb_int in self.cache_resultados:
                    return comb_int, self.cache_resultados[comb_int]
                
                comb_list = list(comb_int)
                res = self.aplicar_filtros(comb_list, return_score, return_reasons, contexto, perfil_svi)
                
                # Cachear resultado
                self.cache_resultados[comb_int] = res
                return comb_int, res
            except Exception as e:
                log_error(f"Error procesando combinación {comb}: {str(e)}")
                return None
        
        batch_size = min(max(1000, len(combinaciones) // 10), 10000)
        log_info(f"Procesando {len(combinaciones)} combinaciones en lotes de {batch_size}")
        
        resultados = []
        self.ultimo_batch_start = time.time()
        total_processed = 0

        for chunk in chunk_generator(combinaciones, batch_size):
            processed = Parallel(n_jobs=min(os.cpu_count(), max(1, len(chunk) // 1000)))(
                delayed(procesar_combinacion)(comb) for comb in chunk
            )
            
            for res in processed:
                if res is None:
                    continue
                comb_int, result = res
                if return_score:
                    if result is None:
                        continue
                    score, razones = result
                    if score >= self.config['umbral_minimo']:
                        resultados.append({"combination": comb_int, "score": score, "razones": razones})
                else:
                    if result:
                        resultados.append(comb_int)
            
            total_processed += len(chunk)
            if progress_callback:
                progress_callback(total_processed, len(combinaciones))
        
        log_info(f"Procesamiento completado. Combinaciones válidas: {len(resultados)}")
        return resultados

    def verificar_alertas(self, perfil_svi="moderado", contexto="normal"):
        """Verifica y registra alertas con persistencia."""
        now = time.time()
        for nombre, cfg in self.ALERTAS_CONFIG.items():
            valor_actual = cfg['metric'](self)
            if valor_actual > cfg['umbral']:
                ultimo_disparo = self.ultimas_alertas.get(nombre, 0)
                if now - ultimo_disparo > cfg['cooldown']:
                    cfg['accion'](self)
                    self.ultimas_alertas[nombre] = now
                    prom_alertas.labels(nombre=nombre, perfil_svi=perfil_svi, contexto=contexto).inc()
                    if self.conn:
                        try:
                            c = self.conn.cursor()
                            c.execute('''INSERT INTO alertas (nombre, valor, timestamp, perfil_svi, contexto)
                                        VALUES (?, ?, ?, ?, ?)''',
                                     (nombre, valor_actual, str(pd.Timestamp.now()), perfil_svi, contexto))
                            self.conn.commit()
                        except Exception as e:
                            log_warning(f"Error insertando alerta en base de datos: {str(e)}")

    def recalibrar_deteccion_rng(self):
        """Recalibra detección de semillas sospechosas."""
        log_info("Recalibrando detección de semillas sospechosas...")
        self.cargar_semillas_sospechosas()
        self.config['pesos_filtros']['rng_sospechoso'] = min(0.15, self.config['pesos_filtros']['rng_sospechoso'] + 0.02)
        self.actualizar_pesos_pruebas()

    def tasa_aprobacion(self): 
        return self.contador_aprobados / self.contador_combinaciones if self.contador_combinaciones else 0.0
    
    def promedio_scores(self): 
        return sum(self.historial_scores) / len(self.historial_scores) if self.historial_scores else 0.0

    def reporte_estadisticas(self, perfil_svi="moderado", contexto="normal"): 
        """Genera reporte de estadísticas y lo guarda en base de datos."""
        total_fallos = sum(self.estadisticas_fallos.values()) or 1
        stats = {filtro: round((count / total_fallos) * 100, 2) for filtro, count in self.estadisticas_fallos.items()}
        
        if self.conn:
            try:
                c = self.conn.cursor()
                c.execute('''INSERT INTO estadisticas (
                    timestamp, total_combinaciones, combinaciones_validas, tasa_retencion, 
                    promedio_scores, perfil_svi, contexto
                ) VALUES (?, ?, ?, ?, ?, ?, ?)''', (
                    str(pd.Timestamp.now()), self.contador_combinaciones, self.contador_aprobados,
                    self.tasa_aprobacion(), self.promedio_scores(), perfil_svi, contexto
                ))
                self.conn.commit()
            except Exception as e:
                log_warning(f"Error insertando estadísticas en base de datos: {str(e)}")
        
        return stats

    def actualizar_umbrales_automatico(self):
        """Ajusta umbrales dinámicamente."""
        if len(self.historial_scores) < 100: 
            return
            
        scores_aprobados = [s for s in self.historial_scores if s >= self.config['umbral_minimo']]
        if scores_aprobados:
            q25 = np.percentile(scores_aprobados, 25)
            q10 = np.percentile(scores_aprobados, 10)
            self.config['umbral_custom'] = max(0.70, round(q25, 3))
            self.config['umbral_asalto'] = max(0.55, round(q10, 3))
            log_info(f"Umbrales actualizados: custom={self.config['umbral_custom']}, asalto={self.config['umbral_asalto']}")

    def generar_graficos(self, perfil_svi="moderado"):
        """Genera gráficos de análisis con verificación de recursos."""
        os.makedirs(LOG_DIR, exist_ok=True)
        
        def check_memory():
            mem = psutil.virtual_memory()
            if mem.percent > 90:
                log_warning("Memoria alta (>90%), posponiendo gráficos")
                return False
            return True

        def plot_score_distribution():
            if not check_memory():
                return
            plt.figure(figsize=(10, 6))
            plt.hist(self.historial_scores, bins=20, color='#1f77b4', edgecolor='black', alpha=0.7)
            plt.axvline(x=self.config['umbral_minimo'], color='r', linestyle='--', label=f'Umbral Mínimo')
            plt.xlabel('Puntaje')
            plt.ylabel('Frecuencia')
            plt.title(f'Distribución de Puntajes ({perfil_svi.upper()})')
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(os.path.join(LOG_DIR, "score_distribution.png"), dpi=300)
            plt.close()
            log_info("Gráfico de distribución de puntajes guardado")

        def plot_rejection_reasons():
            if not check_memory():
                return
            total_fallos = sum(self.estadisticas_fallos.values()) or 1
            motivos = [m for m in self.estadisticas_fallos.keys() if self.estadisticas_fallos[m] > 0]
            valores = [self.estadisticas_fallos[m] / total_fallos * 100 for m in motivos]
            
            plt.figure(figsize=(12, 7))
            plt.barh(motivos, valores, color='#ff7f0e')
            plt.xlabel('Porcentaje (%)')
            plt.ylabel('Motivo de Rechazo')
            plt.title(f'Rechazos por Filtro ({perfil_svi.upper()})')
            plt.grid(axis='x', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(os.path.join(LOG_DIR, "rejection_reasons.png"), dpi=300)
            plt.close()
            log_info("Gráfico de razones de rechazo guardado")

        def plot_retention_per_profile():
            if not check_memory() or not self.conn:
                return
            c = self.conn.cursor()
            perfiles = ['moderado', 'conservador', 'agresivo']
            datos = {p: [] for p in perfiles}
            
            for perfil in perfiles:
                c.execute('SELECT tasa_retencion FROM estadisticas WHERE perfil_svi = ?', (perfil,))
                tasas = [row[0] * 100 for row in c.fetchall() if row[0] is not None]
                datos[perfil] = tasas
            
            plt.figure(figsize=(10, 6))
            plt.boxplot([datos[p] for p in perfiles], labels=[p.capitalize() for p in perfiles])
            plt.ylabel('Tasa de Retención (%)')
            plt.title('Distribución de Tasas de Retención por Perfil SVI')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(os.path.join(LOG_DIR, "retencion_por_perfil.png"), dpi=300)
            plt.close()
            log_info("Gráfico de tasas de retención por perfil guardado")

        for func in [plot_score_distribution, plot_rejection_reasons, plot_retention_per_profile]:
            func()

    def comprimir_logs(self):
        """Comprime logs cuando exceden tamaño límite."""
        log_file = os.path.join(LOG_DIR, "filtros.log")
        if os.path.exists(log_file) and os.path.getsize(log_file) > 5 * 1024 * 1024:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            compressed_path = f"{log_file}.{timestamp}.gz"
            with open(log_file, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(log_file)
            log_info(f"Log comprimido: {compressed_path}")

    def close(self):
        """Cierra recursos y conexiones."""
        if self.conn:
            try:
                self.conn.close()
                log_info("Conexión SQLite cerrada")
            except Exception as e:
                log_warning(f"Error cerrando SQLite: {str(e)}")
        if self.redis_client:
            try:
                self.redis_client.close()
                log_info("Conexión Redis cerrada")
            except Exception as e:
                log_warning(f"Error cerrando Redis: {str(e)}")

def crear_app_conversacional(token_autenticacion: Optional[str] = None):
    """Crea aplicación FastAPI para servicio web."""
    app = FastAPI(
        title="API de Filtrado Estratégico (Rules)",
        version="5.2",
        description="API para filtrado estratégico de combinaciones de Kábala con análisis avanzado."
    )
    
    # Montar endpoint de Prometheus
    app.mount("/metrics", make_asgi_app())

    @app.post("/filtrar_combinaciones", summary="Filtra combinaciones de Kábala")
    async def filtrar_combinaciones(data: dict):
        """Filtra combinaciones según parámetros especificados."""
        try:
            if token_autenticacion and not autenticar_usuario(data.get("token", "")):
                raise HTTPException(status_code=401, detail="Token inválido o expirado")
            
            combinaciones = data.get("combinations", [])
            historial = data.get("historial", "data/historial_kabala_github.csv")
            contexto = data.get("contexto", "normal")
            perfil_svi = data.get("perfil_svi", "moderado")
            config = data.get("config", None)
            modo_rendimiento = data.get("modo_rendimiento", False)
            
            def progress_callback(processed, total):
                log_info(f"Progreso: {processed}/{total} combinaciones procesadas")
            
            filtro = FiltroEstrategico(config, token_autenticacion, modo_rendimiento)
            filtro.cargar_historial(historial)
            
            # Actualizar umbral si se proporciona
            if "umbral_minimo" in data:
                filtro.set_threshold(data["umbral_minimo"])
                
            filtered = filtro.aplicar_filtros_batch(
                combinaciones, return_score=True, contexto=contexto, 
                perfil_svi=perfil_svi, progress_callback=progress_callback
            )
            stats = filtro.reporte_estadisticas(perfil_svi, contexto)
            filtro.generar_graficos(perfil_svi)
            filtro.comprimir_logs()
            
            return {
                "status": "success",
                "filtered_count": len(filtered),
                "filtered_combinations": filtered,
                "statistics": stats,
                "tasa_aprobacion": filtro.tasa_aprobacion(),
                "umbral_actual": filtro.config['umbral_minimo']
            }
        except Exception as e:
            log_error(f"Error en API: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/generar_token", summary="Genera token de autenticación")
    async def generar_token(master_token: Optional[str] = None):
        """Genera un token JWT con expiración."""
        secret_key_path = os.path.join(LOG_DIR, "jwt_secret.key")
        if not os.path.exists(secret_key_path):
            secret_key = os.urandom(32)
            with open(secret_key_path, 'wb') as f:
                f.write(secret_key)
        with open(secret_key_path, 'rb') as f:
            secret_key = f.read()
        
        if master_token:
            try:
                jwt.decode(master_token, secret_key, algorithms=["HS256"])
            except:
                raise HTTPException(status_code=401, detail="Master token inválido")
        
        payload = {
            "user": "kabala_user",
            "exp": time.time() + 3600  # 1 hour expiration
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return {"token": token}
    
    return app

if __name__ == "__main__":
    print("✅ rules_filter.py cargado correctamente y sin errores de sintaxis.")
    auth_key_path = os.path.join(LOG_DIR, "jwt_secret.key")
    os.makedirs(LOG_DIR, exist_ok=True)
    
    if not os.path.exists(auth_key_path):
        key = os.urandom(32)
        with open(auth_key_path, 'wb') as f:
            f.write(key)
        log_info(f"Clave JWT generada en {auth_key_path}")
    
    with open(auth_key_path, 'rb') as f:
        key = f.read()
    token = jwt.encode({"user": "kabala_user", "exp": time.time() + 3600}, key, algorithm="HS256")
    log_info(f"Token de ejemplo: {token}")