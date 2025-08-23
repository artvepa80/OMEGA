import numpy as np
import csv
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import gzip
import shutil
import hashlib
import sqlite3
import requests
from collections import Counter
from typing import List, Dict, Any, Tuple, Union, Optional
from joblib import Parallel, delayed
from functools import lru_cache
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException  # Para la app conversacional opcional
from modules.profiling.jackpot_profiler import perfil_jackpot

# ------------------------------
# 1. Autenticación para filtros.db
# ------------------------------
def autenticar_usuario(token: str, key_path: str = "logs/auth_key.key") -> bool:
    """Autentica el token de usuario usando clave Fernet"""
    if not os.path.exists(key_path):
        print("⚠️ Clave de autenticación no encontrada")
        return False
    
    try:
        with open(key_path, 'rb') as f:
            key = f.read()
        fernet = Fernet(key)
        fernet.decrypt(token.encode())
        return True
    except Exception as e:
        print(f"⚠️ Error en autenticación: {str(e)}")
        return False

# ------------------------------
# 2. Función principal mejorada
# ------------------------------
def apply_strategic_filters(
    combinations: List[Dict[str, Any]],
    data,
    previous_results: List[List[int]],
    regimen: str = 'A',
    perfil_svi: str = 'moderado',
    modo_ataque: bool = False,
    return_score: bool = False,
    token_autenticacion: Optional[str] = None
) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]]:
    """
    Filtro dinámico adaptativo con configuración robusta y optimización avanzada.
    Prioriza números bajos (1-5) en régimen C según la Ley de Compensación Extrema.
    """
    # 1. Validación de datos de entrada
    if not isinstance(data, pd.DataFrame) or data.empty:
        raise ValueError("El parámetro 'data' debe ser un DataFrame no vacío")
    if not all(data.select_dtypes(include='number').columns):
        raise ValueError("El DataFrame 'data' debe contener columnas numéricas")
    for result in previous_results:
        if not (isinstance(result, list) and len(result) == 6 and all(1 <= x <= 40 for x in result)):
            raise ValueError("previous_results debe contener listas de 6 números en [1, 40]")
    for item in combinations:
        if not (isinstance(item, dict) and "combination" in item and isinstance(item["combination"], list) and len(item["combination"]) == 6):
            raise ValueError("Cada elemento en 'combinations' debe ser un diccionario con una clave 'combination' que contiene una lista de 6 números")
    
    # 1.5. Validación avanzada: Detectar duplicados
    def validar_combinaciones_unicas(combs):
        seen = set()
        for item in combs:
            comb_tuple = tuple(sorted(item["combination"]))
            if comb_tuple in seen:
                raise ValueError(f"Combinación duplicada detectada: {comb_tuple}")
            seen.add(comb_tuple)
    
    def validar_resultados_anteriores(results):
        seen = set()
        for result in results:
            result_tuple = tuple(sorted(result))
            if result_tuple in seen:
                raise ValueError(f"Resultado anterior duplicado: {result_tuple}")
            seen.add(result_tuple)
    
    validar_combinaciones_unicas(combinations)
    validar_resultados_anteriores(previous_results)

    # 2. Manejo de datasets vacíos
    if not combinations:
        print("⚠️ No se proporcionaron combinaciones para procesar")
        empty_stats = {}
        empty_discards = Counter({
            "repetidas": 0, "invalidas": 0, "frecuencia_excesiva": 0,
            "frecuencia_insuficiente": 0, "mal_formateadas": 0, "razones": []
        })
        return ([], dict(empty_discards), empty_stats) if return_score else []

    # 3. Validación de parámetros de entrada
    valid_perfiles = ['moderado', 'alto', 'extremo']
    valid_regimenes = ['A', 'C']
    if perfil_svi not in valid_perfiles:
        raise ValueError(f"Perfil SVI inválido: {perfil_svi}. Debe ser uno de {valid_perfiles}")
    if regimen not in valid_regimenes:
        raise ValueError(f"Régimen inválido: {regimen}. Debe ser uno de {valid_regimenes}")

    # 4. Configuración por defecto y carga de JSON
    default_config = {
        "umbrales_suma": {
            "moderado": {"A": [85, 170], "C": [50, 130]},
            "alto": {"A": [80, 175], "C": [45, 135]},
            "extremo": {"A": [75, 180], "C": [40, 140]}
        },
        "umbrales_low_nums": {
            "moderado": {"A": 0, "C": 3},
            "alto": {"A": 0, "C": 2},
            "extremo": {"A": 0, "C": 1}
        },
        "umbral_freq": {
            "moderado": {"A": 95, "C": 90},
            "alto": {"A": 90, "C": 85},
            "extremo": {"A": 85, "C": 80}
        },
        "umbral_freq_min": {
            "moderado": {"A": 5, "C": 5},
            "alto": {"A": 3, "C": 3},
            "extremo": {"A": 2, "C": 2}
        },
        "max_number": 40,
        "umbrales_saltos": {"A": [10, 50], "C": [10, 50]},
        "umbrales_pares": {"A": [0, 6], "C": [0, 6]},
        "umbral_puntaje": {
            "moderado": 0.85,
            "alto": 0.75,
            "extremo": 0.65
        },
        "omega_endpoint": "https://api.omegapro.ai/v10.2/predictions"
    }
    
    config_path = "config/filtros_config.json"
    os.makedirs("config", exist_ok=True)
    
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"⚙️ Archivo de configuración creado en {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    required_keys = ["umbrales_suma", "umbrales_low_nums", "umbral_freq", "umbral_freq_min", 
                    "max_number", "umbrales_saltos", "umbrales_pares", "umbral_puntaje"]
    missing_keys = [k for k in required_keys if k not in config]
    if missing_keys:
        raise ValueError(f"Faltan claves en filtros_config.json: {missing_keys}")
    
    # Validación de configuración lógica
    for profile in valid_perfiles:
        for reg in valid_regimenes:
            if profile not in config["umbrales_suma"] or reg not in config["umbrales_suma"][profile]:
                raise ValueError(f"Configuración incompleta para perfil {profile}/{reg}")
            
            suma_min, suma_max = config["umbrales_suma"][profile][reg]
            if suma_min > suma_max:
                raise ValueError(f"umbral_suma inválido para {profile}/{reg}: min > max")
            
        # Validar umbral_puntaje
        umbral_val = config["umbral_puntaje"].get(profile, 0)
        if umbral_val <= 0 or umbral_val >= 1:
            raise ValueError(f"umbral_puntaje para {profile} debe estar entre 0 y 1")
    
    for reg in valid_regimenes:
        saltos_min, saltos_max = config["umbrales_saltos"][reg]
        pares_min, pares_max = config["umbrales_pares"][reg]
        
        if saltos_min > saltos_max:
            raise ValueError(f"umbral_saltos inválido para {reg}: min > max")
        if pares_min > pares_max:
            raise ValueError(f"umbral_pares inválido para {reg}: min > max")
    
    umbrales_suma = config["umbrales_suma"]
    umbrales_low_nums = config["umbrales_low_nums"]
    umbral_freq_config = config["umbral_freq"]
    umbral_freq_min = config["umbral_freq_min"]
    max_number = config["max_number"]
    umbrales_saltos = config["umbrales_saltos"]
    umbrales_pares = config["umbrales_pares"]
    umbral_puntaje = config["umbral_puntaje"].get(perfil_svi, 0.85)

    # Ajuste dinámico de umbral_puntaje
    if os.path.exists("logs/estadisticas_filtros.json"):
        try:
            with open("logs/estadisticas_filtros.json", 'r') as f:
                stats_list = json.load(f)
            if isinstance(stats_list, list) and stats_list:
                historical_scores = [s["promedio_puntajes"] for s in stats_list if "promedio_puntajes" in s]
                if historical_scores:
                    umbral_puntaje = max(umbral_puntaje, np.percentile(historical_scores, 75))
                    print(f"⚙️ Umbral de puntaje ajustado dinámicamente a: {umbral_puntaje:.3f}")
        except (json.JSONDecodeError, FileNotFoundError):
            print("⚠️ Error al leer estadisticas_filtros.json para ajuste de umbral")

    # 5. Precomputación eficiente con optimización de memoria
    last_draw = data.values[-1].astype(np.int32)
    
    @lru_cache(maxsize=10000)
    def hash_combination(comb_tuple):
        return hashlib.sha256(str(sorted(comb_tuple)).encode()).hexdigest()
    
    @lru_cache(maxsize=10000)
    def get_freq_tuple(comb_tuple):
        if len(comb_tuple) != 6:
            raise ValueError("comb_tuple debe contener exactamente 6 números")
        comb = np.array(comb_tuple, dtype=np.int32)
        return tuple(freq[comb - 1])
    
    historical_set = {hash_combination(tuple(row.astype(np.int32))) for row in data.values}
    previous_recent = {hash_combination(tuple(np.array(r, dtype=np.int32))) for r in previous_results[-30:]}

    # 6. Vectorización optimizada
    flat = data.select_dtypes(include='number').values.flatten().astype(np.int32)
    freq = np.bincount(flat, minlength=max_number + 1)[1:]

    # 7. Calcular umbral de frecuencia dinámico
    freq_non_zero = freq[freq > 0]
    if len(freq_non_zero) > 0:
        percentil = umbral_freq_config[perfil_svi][regimen]
        umbral_freq = np.percentile(freq_non_zero, percentil)
    else:
        umbral_freq = 9999

    # 8. Funciones núcleo optimizadas
    def suma_total(comb): return np.sum(comb)
    def suma_saltos(comb): return np.sum(np.abs(np.diff(comb)))
    def cantidad_pares(comb): return np.sum(comb % 2 == 0)
    def repetidos_ult_sorteo(comb): return np.sum(np.isin(comb, last_draw))
    def low_num_score(comb): return np.sum(comb <= 5)

    # 9. Función de validación optimizada
    def es_valida(comb):
        s = suma_total(comb)
        saltos = suma_saltos(comb)
        pares = cantidad_pares(comb)
        rep_last = repetidos_ult_sorteo(comb)
        low_nums = low_num_score(comb)
        
        suma_min, suma_max = umbrales_suma[perfil_svi][regimen]
        saltos_min, saltos_max = umbrales_saltos[regimen]
        pares_min, pares_max = umbrales_pares[regimen]
        low_nums_min = umbrales_low_nums[perfil_svi][regimen]
        
        if modo_ataque:
            return (
                suma_min <= s <= suma_max and
                saltos_min <= saltos <= saltos_max and
                pares_min <= pares <= pares_max and
                rep_last <= 5 and
                low_nums >= low_nums_min
            )
        return (
            suma_min <= s <= suma_max and
            saltos_min <= saltos <= saltos_max and
            pares_min <= pares <= pares_max and
            rep_last <= 4 and
            low_nums >= low_nums_min
        )

    # 10. Cálculo de puntaje con umbral dinámico
    def calcular_puntaje(comb):
        s = suma_total(comb)
        saltos = suma_saltos(comb)
        pares = cantidad_pares(comb)
        rep_last = repetidos_ult_sorteo(comb)
        low_nums = low_num_score(comb)
        
        suma_min, suma_max = umbrales_suma[perfil_svi][regimen]
        saltos_min, saltos_max = umbrales_saltos[regimen]
        pares_min, pares_max = umbrales_pares[regimen]
        
        s_norm = (s - suma_min) / max(1, suma_max - suma_min)
        saltos_norm = (saltos - saltos_min) / max(1, saltos_max - saltos_min)
        pares_norm = (pares - pares_min) / max(1, pares_max - pares_min)
        rep_max = 5 if modo_ataque else 4
        rep_norm = rep_last / rep_max if rep_max > 0 else 0
        low_nums_norm = low_nums / 6
        
        coefs_suma = {'moderado': 0.3, 'alto': 0.25, 'extremo': 0.2}
        coefs_low = {
            'moderado': 0.2 if regimen == 'C' else 0.1,
            'alto': 0.25 if regimen == 'C' else 0.15,
            'extremo': 0.3 if regimen == 'C' else 0.2
        }
        return (
            coefs_suma[perfil_svi] * (1 - abs(s_norm - 0.5)) +
            0.2 * (1 - abs(saltos_norm - 0.5)) +
            0.2 * (1 - abs(pares_norm - 0.5)) +
            0.1 * (1 - rep_norm) +
            coefs_low[perfil_svi] * low_nums_norm
        )

    # 11. Funciones de filtrado optimizadas con caché
    def es_repetida_exacta(comb):
        tcomb = hash_combination(tuple(comb))
        return tcomb in previous_recent or tcomb in historical_set

    def frecuencia_individual_excesiva(comb, umbral=umbral_freq):
        return np.any(np.array(get_freq_tuple(tuple(comb))) > umbral)

    def frecuencia_individual_insuficiente(comb, umbral=umbral_freq_min[perfil_svi][regimen]):
        return np.any(np.array(get_freq_tuple(tuple(comb))) < umbral)

    def procesar_combinacion(item):
        try:
            comb = np.array(item.get("combination", []), dtype=np.int32)
            if comb.size != 6:
                return None, "mal_formateadas"
            if es_repetida_exacta(comb):
                return None, "repetidas"
            if frecuencia_individual_excesiva(comb):
                return None, "frecuencia_excesiva"
            if frecuencia_individual_insuficiente(comb):
                return None, "frecuencia_insuficiente"
            
            razones = []
            suma_min, suma_max = umbrales_suma[perfil_svi][regimen]
            saltos_min, saltos_max = umbrales_saltos[regimen]
            pares_min, pares_max = umbrales_pares[regimen]
            low_nums_min = umbrales_low_nums[perfil_svi][regimen]
            
            s = suma_total(comb)
            saltos = suma_saltos(comb)
            pares = cantidad_pares(comb)
            rep_last = repetidos_ult_sorteo(comb)
            low_nums = low_num_score(comb)
            
            valid = True
            if not np.all((comb >= 1) & (comb <= max_number)):
                razones.append(f"Números fuera de rango [1, {max_number}]")
                valid = False
            if not (suma_min <= s <= suma_max):
                razones.append(f"Suma {s} fuera de [{suma_min}, {suma_max}]")
                valid = False
            if not (saltos_min <= saltos <= saltos_max):
                razones.append(f"Saltos {saltos} fuera de [{saltos_min}, {saltos_max}]")
                valid = False
            if not (pares_min <= pares <= pares_max):
                razones.append(f"Pares {pares} fuera de [{pares_min}, {pares_max}]")
                valid = False
            rep_max = 5 if modo_ataque else 4
            if rep_last > rep_max:
                razones.append(f"Repetidos {rep_last} excede {rep_max}")
                valid = False
            if low_nums < low_nums_min:
                razones.append(f"Números bajos {low_nums} < {low_nums_min}")
                valid = False
            
            if valid:
                score = calcular_puntaje(comb)
                if score < umbral_puntaje:
                    razones.append(f"Puntaje {score:.3f} < umbral {umbral_puntaje}")
                    return None, ("invalidas", razones)
                return {"combination": comb.tolist(), "score": score}, None
            else:
                return None, ("invalidas", razones)
        except Exception as e:
            print(f"⚠️ Error procesando combinación: {str(e)}")
            return None, "mal_formateadas"

    def procesar_combinacion_safe(item):
        try:
            return procesar_combinacion(item)
        except Exception as e:
            print(f"⚠️ Error crítico en combinación: {str(e)}")
            return None, "mal_formateadas"

    # 12. Contador de descartes
    descartadas = Counter({
        "repetidas": 0,
        "invalidas": 0,
        "frecuencia_excesiva": 0,
        "frecuencia_insuficiente": 0,
        "mal_formateadas": 0,
        "razones": []
    })

    # 13. Batch size dinámico
    batch_size = min(max(1000, len(combinations) // 10), 10000)
    print(f"⚙️ Tamaño de lote optimizado: {batch_size} combinaciones por lote")

    # 14. Optimización de memoria para lotes grandes (streaming)
    def procesar_combinaciones_stream(combs, batch_sz):
        for i in range(0, len(combs), batch_sz):
            batch = combs[i:i+batch_sz]
            yield Parallel(n_jobs=min(os.cpu_count(), max(1, len(batch) // 1000)))(
                delayed(procesar_combinacion_safe)(item) for item in batch
            )
    
    # 15. Procesamiento en lotes optimizado
    final = []
    total_batches = (len(combinations) + batch_size - 1) // batch_size
    
    for results in procesar_combinaciones_stream(combinations, batch_size):
        print(f"🔁 Procesando lote {len(final)//batch_size + 1}/{total_batches}")
        for r in results:
            if r[0] is not None:
                final.append(r[0])
            elif r[1] is not None:
                if isinstance(r[1], tuple):
                    descartadas[r[1][0]] += 1
                    if r[1][1]:
                        descartadas["razones"].append(r[1][1])
                else:
                    descartadas[r[1]] += 1

    # 16. Estadísticas avanzadas
    stats = {}
    
    # Función para inicializar la base de datos con autenticación
    def init_db(token_auth=None):
        if token_auth and not autenticar_usuario(token_auth):
            raise ValueError("Token de autenticación inválido para acceso a base de datos")
        
        conn = sqlite3.connect("logs/filtros.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS estadisticas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            total_combinaciones INTEGER,
            combinaciones_validas INTEGER,
            tasa_retencion REAL,
            promedio_puntajes REAL,
            max_puntaje REAL,
            min_puntaje REAL,
            desviacion_puntajes REAL,
            promedio_bajos REAL,
            distribucion_bajos TEXT,
            perfil_svi TEXT,
            regimen TEXT,
            umbral_puntaje REAL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS descartes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            combination TEXT,
            motivo TEXT,
            timestamp TEXT,
            perfil_svi TEXT,
            regimen TEXT
        )''')
        # Crear índices para optimizar consultas
        c.execute('CREATE INDEX IF NOT EXISTS idx_estadisticas_timestamp ON estadisticas (timestamp)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_estadisticas_perfil_regimen ON estadisticas (perfil_svi, regimen)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_descartes_timestamp ON descartes (timestamp)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_descartes_perfil_regimen ON descartes (perfil_svi, regimen)')
        conn.commit()
        return conn

    # Abrir conexión única a la base de datos con autenticación
    try:
        conn = init_db(token_autenticacion)
    except Exception as e:
        print(f"⚠️ Error de autenticación para base de datos: {str(e)}")
        conn = None
    
    try:
        if final:
            scores = [item["score"] for item in final]
            low_nums_counts = [low_num_score(np.array(item["combination"], dtype=np.int32)) for item in final]
            stats = {
                "total_combinaciones": len(combinations),
                "combinaciones_validas": len(final),
                "tasa_retencion": len(final) / len(combinations),
                "promedio_puntajes": float(np.mean(scores)),
                "max_puntaje": float(np.max(scores)),
                "min_puntaje": float(np.min(scores)),
                "desviacion_puntajes": float(np.std(scores)),
                "promedio_bajos": float(np.mean(low_nums_counts)),
                "distribucion_bajos": dict(Counter(low_nums_counts)),
                "umbral_puntaje": umbral_puntaje,
                "perfil_svi": perfil_svi,
                "regimen": regimen
            }

            # 17. Generación de gráficos en paralelo
            def generar_grafico(func, *args, **kwargs):
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    print(f"⚠️ Error al generar gráfico: {str(e)}")

            def plot_puntajes(scores, umbral_puntaje, perfil_svi):
                plt.figure(figsize=(10, 6))
                plt.hist(scores, bins=20, color='#1f77b4', edgecolor='black', alpha=0.7)
                plt.axvline(x=umbral_puntaje, color='r', linestyle='--', label=f'Umbral: {umbral_puntaje}')
                plt.xlabel('Puntaje', fontsize=12)
                plt.ylabel('Frecuencia', fontsize=12)
                plt.title(f'Distribución de Puntajes ({perfil_svi.upper()})', fontsize=14)
                plt.legend()
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                plt.tight_layout()
                plt.savefig("logs/puntajes_distribucion.png", dpi=300)
                plt.close()
                print(f"📊 Histograma de puntajes guardado en logs/puntajes_distribucion.png")

            def plot_bajos_distribucion(distribucion_bajos, perfil_svi):
                if distribucion_bajos:
                    plt.figure(figsize=(10, 6))
                    bajos = list(distribucion_bajos.keys())
                    counts = list(distribucion_bajos.values())
                    plt.bar(bajos, counts, color='#2ca02c')
                    plt.xlabel('Cantidad de Números Bajos (1-5)', fontsize=12)
                    plt.ylabel('Frecuencia', fontsize=12)
                    plt.title(f'Distribución de Números Bajos ({perfil_svi.upper()})', fontsize=14)
                    plt.grid(axis='y', linestyle='--', alpha=0.7)
                    for i, v in enumerate(counts):
                        plt.text(i, v + 0.5, str(v), ha='center', va='bottom', fontweight='bold')
                    plt.tight_layout()
                    plt.savefig("logs/bajos_distribucion.png", dpi=300)
                    plt.close()
                    print(f"📊 Histograma de números bajos guardado en logs/bajos_distribucion.png")

            def plot_numeros_distribucion(final, max_number, perfil_svi):
                all_numbers = np.concatenate([item["combination"] for item in final]).astype(np.int32)
                number_counts = np.bincount(all_numbers, minlength=max_number + 1)[1:]
                plt.figure(figsize=(14, 7))
                plt.bar(range(1, max_number + 1), number_counts, color='#1f77b4')
                plt.xlabel('Número', fontsize=12)
                plt.ylabel('Frecuencia', fontsize=12)
                plt.title(f'Distribución de Números en Combinaciones Válidas ({perfil_svi.upper()})', fontsize=14)
                plt.xticks(range(1, max_number + 1))
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                plt.tight_layout()
                plt.savefig("logs/numeros_distribucion.png", dpi=300)
                plt.close()
                print(f"📊 Gráfico de distribución de números guardado en logs/numeros_distribucion.png")

            def plot_puntajes_vs_bajos(final, scores, perfil_svi):
                low_nums = [low_num_score(np.array(item["combination"], dtype=np.int32)) for item in final]
                plt.figure(figsize=(10, 6))
                plt.scatter(low_nums, scores, color='#1f77b4', alpha=0.5)
                plt.xlabel('Cantidad de Números Bajos (1-5)', fontsize=12)
                plt.ylabel('Puntaje', fontsize=12)
                plt.title(f'Puntajes vs. Números Bajos ({perfil_svi.upper()})', fontsize=14)
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                plt.savefig("logs/puntajes_vs_bajos.png", dpi=300)
                plt.close()
                print(f"📊 Gráfico de puntajes vs. bajos guardado en logs/puntajes_vs_bajos.png")

            # Cargar estadísticas históricas para gráficos de tendencia
            stats_list = []
            if os.path.exists("logs/estadisticas_filtros.json"):
                try:
                    with open("logs/estadisticas_filtros.json", 'r') as f:
                        stats_list = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    print("⚠️ Error al leer estadisticas_filtros.json para gráficos")

            def plot_bajos_trend(stats_list, perfil_svi):
                if isinstance(stats_list, list) and stats_list:
                    plt.figure(figsize=(10, 6))
                    for i, s in enumerate(stats_list[-5:], 1):
                        if "distribucion_bajos" in s:
                            bajos = sorted(s["distribucion_bajos"].keys())
                            counts = [s["distribucion_bajos"].get(k, 0) for k in bajos]
                            plt.plot(bajos, counts, marker='o', label=f'Ejecución {len(stats_list)-i+1}')
                    plt.xlabel('Números Bajos (1-5)', fontsize=12)
                    plt.ylabel('Frecuencia', fontsize=12)
                    plt.title(f'Evolución de Distribución de Números Bajos ({perfil_svi.upper()})', fontsize=14)
                    plt.legend()
                    plt.grid(True, linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    plt.savefig("logs/bajos_trend.png", dpi=300)
                    plt.close()
                    print(f"📊 Gráfico de tendencia de números bajos guardado en logs/bajos_trend.png")

            def plot_tasa_retencion_trend(stats_list, perfil_svi):
                if isinstance(stats_list, list) and stats_list:
                    tasas = [s["tasa_retencion"] * 100 for s in stats_list]
                    plt.figure(figsize=(10, 6))
                    plt.plot(range(1, len(tasas) + 1), tasas, marker='o', color='#1f77b4')
                    plt.xlabel('Ejecución', fontsize=12)
                    plt.ylabel('Tasa de Retención (%)', fontsize=12)
                    plt.title(f'Evolución de la Tasa de Retención ({perfil_svi.upper()})', fontsize=14)
                    plt.grid(True, linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    plt.savefig("logs/tasa_retencion_trend.png", dpi=300)
                    plt.close()
                    print(f"📊 Gráfico de tendencia de tasa de retención guardado en logs/tasa_retencion_trend.png")

            def plot_puntajes_por_perfil(conn, perfiles_validos):
                if conn is None:
                    return
                plt.figure(figsize=(10, 6))
                for perfil in perfiles_validos:
                    c = conn.cursor()
                    c.execute('SELECT promedio_puntajes FROM estadisticas WHERE perfil_svi = ?', (perfil,))
                    scores = [row[0] for row in c.fetchall() if row[0] is not None]
                    if scores:
                        plt.hist(scores, bins=20, alpha=0.5, label=perfil.capitalize())
                plt.xlabel('Puntaje Promedio', fontsize=12)
                plt.ylabel('Frecuencia', fontsize=12)
                plt.title('Distribución de Puntajes por Perfil SVI', fontsize=14)
                plt.legend()
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                plt.savefig("logs/puntajes_por_perfil.png", dpi=300)
                plt.close()
                print(f"📊 Gráfico de puntajes por perfil guardado en logs/puntajes_por_perfil.png")
                
            def plot_retencion_por_perfil(conn, perfiles_validos):
                if conn is None:
                    return
                plt.figure(figsize=(10, 6))
                for perfil in perfiles_validos:
                    c = conn.cursor()
                    c.execute('SELECT tasa_retencion FROM estadisticas WHERE perfil_svi = ?', (perfil,))
                    tasas = [row[0] * 100 for row in c.fetchall() if row[0] is not None]
                    if tasas:
                        plt.hist(tasas, bins=20, alpha=0.5, label=perfil.capitalize())
                plt.xlabel('Tasa de Retención (%)', fontsize=12)
                plt.ylabel('Frecuencia', fontsize=12)
                plt.title('Distribución de Tasas de Retención por Perfil SVI', fontsize=14)
                plt.legend()
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                plt.savefig("logs/retencion_por_perfil.png", dpi=300)
                plt.close()
                print(f"📊 Gráfico de tasas de retención por perfil guardado en logs/retencion_por_perfil.png")

            # Ejecutar generación de gráficos en paralelo
            Parallel(n_jobs=min(os.cpu_count(), 4))(
                delayed(generar_grafico)(func, *args) for func, args in [
                    (plot_puntajes, (scores, umbral_puntaje, perfil_svi)),
                    (plot_bajos_distribucion, (stats["distribucion_bajos"], perfil_svi)),
                    (plot_numeros_distribucion, (final, max_number, perfil_svi)),
                    (plot_puntajes_vs_bajos, (final, scores, perfil_svi)),
                    (plot_bajos_trend, (stats_list, perfil_svi)),
                    (plot_tasa_retencion_trend, (stats_list, perfil_svi)),
                    (plot_puntajes_por_perfil, (conn, valid_perfiles)),
                    (plot_retencion_por_perfil, (conn, valid_perfiles))
                ]
            )

            # 18. Registro de estadísticas en SQLite
            if conn:
                c = conn.cursor()
                c.execute('''INSERT INTO estadisticas (
                    timestamp, total_combinaciones, combinaciones_validas, tasa_retencion,
                    promedio_puntajes, max_puntaje, min_puntaje, desviacion_puntajes,
                    promedio_bajos, distribucion_bajos, perfil_svi, regimen, umbral_puntaje
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                    str(pd.Timestamp.now()), stats["total_combinaciones"], stats["combinaciones_validas"],
                    stats["tasa_retencion"], stats["promedio_puntajes"], stats["max_puntaje"],
                    stats["min_puntaje"], stats["desviacion_puntajes"], stats["promedio_bajos"],
                    json.dumps(stats["distribucion_bajos"]), perfil_svi, regimen, umbral_puntaje
                ))
                conn.commit()

        # 19. Registro de descartes en SQLite
        if conn:
            for i, razones in enumerate(descartadas["razones"]):
                c = conn.cursor()
                c.execute('INSERT INTO descartes (combination, motivo, timestamp, perfil_svi, regimen) VALUES (?, ?, ?, ?, ?)',
                          (f"Comb_{i+1}", '; '.join(razones), str(pd.Timestamp.now()), perfil_svi, regimen))
                conn.commit()
            
    finally:
        if conn:
            conn.close()

    # 20. Registro de descartes en CSV
    with open("logs/combinaciones_fallidas.csv", 'a', newline='') as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(['Combination', 'Motivo', 'Timestamp', 'Perfil_SVI', 'Regimen'])
        for i, razones in enumerate(descartadas["razones"]):
            writer.writerow([f"Comb_{i+1}", '; '.join(razones), pd.Timestamp.now(), perfil_svi, regimen])

    # 21. Gráfico de descartes
    plt.figure(figsize=(12, 7))
    motivos = [k for k in descartadas.keys() if k != "razones"]
    valores = [descartadas[k] for k in motivos]
    plt.bar(motivos, valores, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
    plt.xlabel('Motivo de Descarte', fontsize=12)
    plt.ylabel('Cantidad', fontsize=12)
    plt.title(f'Combinaciones Descartadas ({perfil_svi.upper()}, {regimen})', fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    for i, v in enumerate(valores):
        plt.text(i, v + 0.5, str(v), ha='center', va='bottom', fontweight='bold')
    plt.tight_layout()
    plt.savefig("logs/descartes_analysis.png", dpi=300)
    plt.close()

    # 22. Reporte final mejorado
    reporte = {
        "timestamp": str(pd.Timestamp.now()),
        "total_combinaciones": len(combinations),
        "combinaciones_validas": len(final),
        "tasa_retencion": stats.get('tasa_retencion', 0) * 100,
        "descartes": {k: v for k, v in descartadas.items() if k != "razones"},
        "razones_detalladas": descartadas["razones"][:5],
        "stats": stats,
        "config": config,
        "hash_set_size": len(historical_set),
        "metadata": {
            "version": "4.0.0",
            "model": "GhostRNG Pro",
            "checksum_config": hashlib.md5(json.dumps(config).encode()).hexdigest()
        }
    }
    os.makedirs("logs", exist_ok=True)
    with open("logs/reporte_filtros.json", 'w') as f:
        json.dump(reporte, f, indent=2, default=str)
    print(f"📝 Reporte guardado en logs/reporte_filtros.json")

    # 23. Cifrado de logs sensibles
    def cifrar_archivo(file_path, key):
        try:
            if file_path.endswith('.enc'):
                print(f"⚠️ {file_path} ya está cifrado, omitiendo")
                return
            if not os.access(file_path, os.W_OK):
                print(f"⚠️ No hay permisos para modificar {file_path}")
                return
            fernet = Fernet(key)
            with open(file_path, 'rb') as f:
                data = f.read()
            cifrado = fernet.encrypt(data)
            with open(f"{file_path}.enc", 'wb') as f:
                f.write(cifrado)
            os.remove(file_path)
            print(f"🔒 Archivo cifrado: {file_path}.enc")
        except Exception as e:
            print(f"⚠️ Error al cifrar {file_path}: {str(e)}")

    key = Fernet.generate_key()
    with open("logs/encryption_key.key", 'wb') as f:
        f.write(key)
    for archivo in ["logs/reporte_filtros.json", "logs/combinaciones_fallidas.csv"]:
        if os.path.exists(archivo):
            cifrar_archivo(archivo, key)

    # 24. Rotación y compresión de logs
    def comprimir_archivo(file_path):
        try:
            if file_path.endswith('.gz'):
                print(f"⚠️ {file_path} ya está comprimido, omitiendo")
                return
            if not os.access(file_path, os.W_OK):
                print(f"⚠️ No hay permisos para modificar {file_path}")
                return
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            archivo_rotado = f"{file_path}.{timestamp}"
            os.rename(file_path, archivo_rotado)
            compressed_path = f"{archivo_rotado}.gz"
            with open(archivo_rotado, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(archivo_rotado)
            print(f"📦 Archivo comprimido: {compressed_path}")
            return compressed_path
        except Exception as e:
            print(f"⚠️ Error al comprimir {file_path}: {str(e)}")
            return None

    def comprimir_grafico(file_path):
        try:
            if file_path.endswith('.gz'):
                print(f"⚠️ {file_path} ya está comprimido, omitiendo")
                return
            if not os.access(file_path, os.W_OK):
                print(f"⚠️ No hay permisos para modificar {file_path}")
                return
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            archivo_rotado = f"{file_path}.{timestamp}"
            os.rename(file_path, archivo_rotado)
            compressed_path = f"{archivo_rotado}.gz"
            with open(archivo_rotado, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(archivo_rotado)
            print(f"📦 Gráfico comprimido: {compressed_path}")
        except Exception as e:
            print(f"⚠️ Error al comprimir {file_path}: {str(e)}")

    archivos_log = [
        "logs/estadisticas_filtros.json"
    ]
    graficos = [
        "logs/descartes_analysis.png", "logs/puntajes_distribucion.png",
        "logs/bajos_distribucion.png", "logs/numeros_distribucion.png",
        "logs/puntajes_vs_bajos.png", "logs/bajos_trend.png",
        "logs/tasa_retencion_trend.png", "logs/puntajes_por_perfil.png",
        "logs/retencion_por_perfil.png"
    ]
    
    for archivo in archivos_log:
        if os.path.exists(archivo) and os.path.getsize(archivo) > 5 * 1024 * 1024:  # 5 MB
            comprimir_archivo(archivo)
    for grafico in graficos:
        if os.path.exists(grafico) and os.path.getsize(grafico) > 2 * 1024 * 1024:  # 2 MB
            comprimir_grafico(grafico)

    # 25. Integración con OMEGA PRO AI v10.2
    def enviar_a_omega_pro(final_combs, stats_data, endpoint=None):
        if not endpoint:
            endpoint = config.get("omega_endpoint", "https://api.omegapro.ai/v10.2/predictions")
        
        payload = {
            "combinations": final_combs,
            "statistics": stats_data,
            "metadata": {
                "timestamp": str(pd.Timestamp.now()),
                "model": "GhostRNG Pro",
                "version": "4.0.0"
            }
        }
        try:
            response = requests.post(endpoint, json=payload, timeout=10)
            response.raise_for_status()
            print(f"✅ Enviado a OMEGA PRO AI: {response.json()}")
            return response.json()
        except requests.RequestException as e:
            print(f"⚠️ Error al enviar a OMEGA PRO AI: {str(e)}")
            return None

    if final and config.get("omega_endpoint"):
        enviar_a_omega_pro(final, stats)

    # 26. Reporte de salida
    print(f"\n✅ PROCESAMIENTO COMPLETADO")
    print(f"   - Combinaciones totales: {len(combinations)}")
    print(f"   - Combinaciones válidas: {len(final)}")
    print(f"   - Tasa de retención: {stats.get('tasa_retencion', 0)*100:.2f}%")
    print(f"   - Umbral de puntaje aplicado: {umbral_puntaje}")
    
    print(f"\n📊 RESUMEN DE DESCARTES:")
    for k, v in descartadas.items():
        if k != "razones":
            print(f"   - {k.capitalize()}: {v}")
    
    if stats:
        print("\n📈 ESTADÍSTICAS AVANZADAS:")
        print(f"   - Puntaje promedio: {stats['promedio_puntajes']:.3f}")
        print(f"   - Puntaje máximo: {stats['max_puntaje']:.3f}")
        print(f"   - Puntaje mínimo: {stats['min_puntaje']:.3f}")
        print(f"   - Desviación estándar: {stats['desviacion_puntajes']:.3f}")
        print(f"   - Promedio números bajos: {stats['promedio_bajos']:.2f}")
    
    if descartadas["razones"]:
        print("\n🔍 RAZONES DETALLADAS (primeras 5):")
        for i, razones in enumerate(descartadas["razones"][:5]):
            print(f"   {i+1}. {', '.join(razones)}")
        if len(descartadas["razones"]) > 5:
            print(f"   ... y {len(descartadas['razones']) - 5} combinaciones más con problemas de validez")
    
    print(f"\n📦 SALIDAS GUARDADAS:")
    print(f"   - logs/descartes_analysis.png")
    print(f"   - logs/puntajes_distribucion.png")
    print(f"   - logs/bajos_distribucion.png")
    print(f"   - logs/numeros_distribucion.png")
    print(f"   - logs/puntajes_vs_bajos.png")
    print(f"   - logs/bajos_trend.png")
    print(f"   - logs/tasa_retencion_trend.png")
    print(f"   - logs/puntajes_por_perfil.png")
    print(f"   - logs/retencion_por_perfil.png")
    print(f"   - logs/filtros.db (SQLite)")
    print(f"   - logs/combinaciones_fallidas.csv.enc*")
    print(f"   - logs/estadisticas_filtros.json*")
    print(f"   - logs/reporte_filtros.json.enc*")
    print(f"   - logs/encryption_key.key")
    print(f"   - logs/auth_key.key")
    print(f"  (*archivos comprimidos si superan umbral, .enc indica cifrado)")

    if return_score:
        return final, dict(descartadas), stats
    return final

# ------------------------------
# 3. Función para interfaz API
# ------------------------------
def crear_app_conversacional():
    app = FastAPI(title="API de Filtrado Estratégico", version="4.0.0")

    @app.post("/filtrar_combinaciones")
    async def filtrar_combinaciones(data: dict):
        try:
            combinaciones = data.get("combinations", [])
            historial_csv = data.get("historial_csv", "data/historial_kabala_github.csv")
            regimen = data.get("regimen", "C")
            perfil_svi = data.get("perfil_svi", "extremo")
            token = data.get("token", None)
            
            df = pd.read_csv(historial_csv)
            historial = [list(row) for row in df.values]
            
            filtered, descartadas, stats = apply_strategic_filters(
                combinaciones, 
                df, 
                historial, 
                regimen=regimen, 
                perfil_svi=perfil_svi, 
                return_score=True,
                token_autenticacion=token
            )
            
            return {
                "status": "success",
                "filtered_combinations": filtered,
                "discarded_count": dict(descartadas),
                "statistics": stats
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/generar_token")
    async def generar_token():
        key = Fernet.generate_key()
        fernet = Fernet(key)
        token = fernet.encrypt(b"usuario_autorizado").decode()
        return {"token": token, "key": key.decode()}

    return app

# ------------------------------
# 4. Score dinámico total (versión segura)
# ------------------------------
def score_dinamico_total(combination, contexto=None, modo="normal"):
    """
    Devuelve un dict con:
        - combinacion : lista[int]         (la jugada tal cual)
        - score       : int                (puntuación cruda, >=0)
        - svi         : float              (score normalizado 0-1)
        - detalles    : dict[str, Any]     (break-down opcional)

    Nunca devuelve un entero suelto; así evitamos el error
    "'int' object is not subscriptable".
    """
    # ---------------- Validación básica ----------------
    try:
        comb = [int(x) for x in combination]      # cast a int por si llegan np.int64
    except Exception:
        return {"combinacion": [], "score": 0, "svi": 0.0,
                "detalles": {"motivo": "valores no enteros"}}

    if not (len(comb) == 6 and all(1 <= x <= 40 for x in comb)):
        return {"combinacion": [], "score": 0, "svi": 0.0,
                "detalles": {"motivo": "fuera de rango o longitud ≠ 6"}}

    # ---------------- Cálculo de score -----------------
    score = 0
    detalles = {}

    # 1. Perfil Jackpot
    perfil = perfil_jackpot(comb)          # A / B / C
    perfil_pts = {"A": 3, "B": 2, "C": 1}.get(perfil, 0)
    score += perfil_pts
    detalles["perfil"] = (perfil, perfil_pts)

    # 2. Saltos
    saltos = [b - a for a, b in zip(sorted(comb), sorted(comb)[1:])]
    if all(1 <= s <= 10 for s in saltos):
        saltos_pts = 2
    elif all(1 <= s <= 15 for s in saltos):
        saltos_pts = 1
    else:
        saltos_pts = 0
    score += saltos_pts
    detalles["saltos"] = (saltos, saltos_pts)

    # 3. Variedad de decenas
    decenas = {n // 10 for n in comb}
    decenas_pts = len(decenas)             # máx 4
    score += decenas_pts
    detalles["decenas"] = (decenas, decenas_pts)

    # 4. Penalizaciones contexto
    pen = 0
    if contexto:
        # Repetidos con último sorteo
        if "ultimo_resultado" in contexto:
            repetidos = set(comb) & set(contexto["ultimo_resultado"])
            if len(repetidos) > 1:
                pen -= 2
                detalles["repetidos"] = -2

        # Semillas sospechosas
        if "semillas_sospechosas" in contexto and contexto.get("comb_id") in contexto["semillas_sospechosas"]:
            pen -= 3
            detalles["ghost_rng"] = -3
    score += pen

    # 5. Ajuste por modo
    ajuste = 0
    if modo == "asalto":
        if perfil == "C":
            ajuste -= 1
        if any(x <= 5 for x in comb):
            ajuste += 1
    score += ajuste
    detalles["modo_ajuste"] = ajuste

    # ---------------- Normalización SVI ----------------
    # Máximo teórico: perfil(3)+saltos(2)+decenas(4)+ajuste(1) = 10
    max_posible = 10
    svi = round(max(score, 0) / max_posible, 3)

    return {
        "combinacion": comb,
        "score": max(score, 0),
        "svi": svi,
        "detalles": detalles
    }


# ------------------------------
# 5. Ejecución inicial
# ------------------------------
if __name__ == "__main__":
    # Generar clave de autenticación si no existe
    auth_key_path = "logs/auth_key.key"
    os.makedirs("logs", exist_ok=True)
    
    if not os.path.exists(auth_key_path):
        key = Fernet.generate_key()
        with open(auth_key_path, 'wb') as f:
            f.write(key)
        print(f"🔑 Clave de autenticación generada en {auth_key_path}")
    
    # Generar token de ejemplo
    with open(auth_key_path, 'rb') as f:
        key = f.read()
    fernet = Fernet(key)
    token = fernet.encrypt(b"usuario_autorizado").decode()
    print(f"🔐 Token de ejemplo: {token}")
    
    # Iniciar app conversacional (opcional)
    # app = crear_app_conversacional()
    # Para ejecutar: uvicorn nombre_archivo:app --host 0.0.0.0 --port 8000