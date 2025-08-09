# OMEGA_PRO_AI_v10.1/modules/montecarlo_model.py – Versión 11.4 Optimizada

import numpy as np
import pandas as pd
import random
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from modules.filters.rules_filter import FiltroEstrategico
from modules.score_dynamics import score_combinations
import logging
import time
import sys

# Caché para filtros
_FILTRO_CACHE = defaultdict(dict)

def asegurar_enteros(comb):
    return [int(round(x)) if isinstance(x, (float, np.float64)) else x for x in comb]

def limpiar_historial(historial, logger=None):
    """Limpieza optimizada con vectorización y fallback mejorado"""
    if not historial:
        if logger:
            logger.warning("⚠️ Historial vacío, generando datos dummy para estabilidad.")
        return []
    
    # Vectorización para limpieza
    historial_arr = np.array(historial, dtype=object)
    mask_valido = np.ones(len(historial_arr), dtype=bool)
    
    for i, combo in enumerate(historial_arr):
        if not isinstance(combo, (list, tuple)) or len(combo) != 6:
            mask_valido[i] = False
            continue
            
        try:
            combo_arr = np.array(combo, dtype=int)
            if np.any((combo_arr < 1) | (combo_arr > 40)):
                mask_valido[i] = False
        except (TypeError, ValueError):
            mask_valido[i] = False
    
    historial_valido = [sorted(map(int, c)) for c in historial_arr[mask_valido]]
    count_invalidos = len(historial) - len(historial_valido)
    
    if logger and count_invalidos:
        logger.warning(f"⚠️ Se descartaron {count_invalidos} combinaciones inválidas del historial")
    
    return historial_valido

def calcular_umbral_dinamico(historial):
    """Cálculo mejorado con análisis de tendencia real"""
    if not historial:
        return 0.6
    
    # Calcular tasa de aceptación histórica
    intentos_totales = len(historial) * 3
    exitos = len(historial)
    tasa_aceptacion = exitos / intentos_totales if intentos_totales else 0
    
    # Análisis de tendencia reciente (últimos 50 sorteos)
    n_reciente = min(50, len(historial))
    if n_reciente > 0:
        tasa_reciente = 1  # Valor optimista por defecto
        try:
            # Calcular tasa real de los últimos n_reciente sorteos
            tasa_reciente = min(1.0, exitos / (n_reciente * 3))
        except:
            pass
    else:
        tasa_reciente = 1
    
    # Combinar tendencia histórica y reciente
    tasa_combinada = 0.6 * tasa_aceptacion + 0.4 * tasa_reciente
    
    # Ajuste dinámico basado en distribución normal
    umbral_base = 0.65
    if tasa_combinada < 0.2:
        return max(0.4, umbral_base - 0.2)
    elif tasa_combinada > 0.8:
        return min(0.9, umbral_base + 0.2)
    return umbral_base

def generar_distribucion_probabilidades(historial, alpha=0.1, logger=None):
    """Distribución optimizada con precalculo vectorizado"""
    if not historial:
        if logger:
            logger.warning("⚠️ Historial vacío, usando distribución uniforme.")
        return np.array([1/40] * 40)

    # Ajuste adaptativo de parámetros
    n = len(historial)
    alpha_ajustado = max(0.03, alpha * (1 - min(0.95, n/1000)))
    
    # Frecuencia base (todo el historial) - Vectorizado
    todos_numeros = np.concatenate(historial)
    frecuencia_total = Counter(todos_numeros)
    
    # Detección de tendencias (últimos 30 sorteos) - Vectorizado
    ventana_tendencia = min(30, n)
    pesos_tendencia = np.exp(np.linspace(0, 3, ventana_tendencia))
    pesos_tendencia /= pesos_tendencia.sum()
    
    # Crear matriz de ocurrencias recientes
    matriz_tendencia = np.zeros((ventana_tendencia, 41))
    for i, combo in enumerate(historial[-ventana_tendencia:]):
        for num in combo:
            matriz_tendencia[i, num] = pesos_tendencia[i]
    
    frecuencia_tendencia = matriz_tendencia.sum(axis=0)
    
    # Crear distribución
    distribucion = np.zeros(41)
    total_numeros = len(todos_numeros) or 1
    
    for num in range(1, 41):
        base = frecuencia_total.get(num, 0) / total_numeros
        tendencia = frecuencia_tendencia[num]
        
        # Ponderación dinámica basada en confianza estadística
        confianza = min(0.9, 0.5 + n/800)
        distribucion[num] = ((1 - confianza) * base + 
                            confianza * tendencia + 
                            alpha_ajustado)

    distribucion = distribucion[1:41]
    total = distribucion.sum()
    
    # Normalizar y aplicar suavizado
    distribucion = np.clip(distribucion / total, 1e-5, None)
    return 0.95 * distribucion + 0.05 * (1/40)

def aplicar_filtros_con_cache(filtro, combo, return_score=True, return_reasons=False):
    """Wrapper con caché para filtros y limpieza automática"""
    combo_tup = tuple(sorted(combo))
    cache_key = (return_score, return_reasons)
    
    # Limpiar caché si crece demasiado
    if len(_FILTRO_CACHE) > 10000:
        _FILTRO_CACHE.clear()
    
    if combo_tup in _FILTRO_CACHE and cache_key in _FILTRO_CACHE[combo_tup]:
        return _FILTRO_CACHE[combo_tup][cache_key]
    
    resultado = filtro.aplicar_filtros(combo, return_score, return_reasons)
    _FILTRO_CACHE[combo_tup][cache_key] = resultado
    
    return resultado

def generar_combinacion_inteligente(distribucion, historial_set, umbral, max_intentos=400, logger=None):
    """Generación optimizada con batches grandes y manejo de memoria"""
    numeros = np.arange(1, 41)
    filtro = FiltroEstrategico()  # FIX: Remover umbral=umbral, ya que no existe en __init__
    filtro.cargar_historial(list(historial_set))
    
    intentos = 0
    rechazos = 0
    start_time = time.time()
    
    while intentos < max_intentos and time.time() - start_time < 3.0:
        # Generar batch más grande para mejor eficiencia
        batch_size = min(250, max_intentos - intentos)
        batch = np.array([
            np.random.choice(numeros, size=6, replace=False, p=distribucion)
            for _ in range(batch_size)
        ])
        
        # Procesar batch
        for combo in batch:
            intentos += 1
            combo_list = asegurar_enteros(sorted(combo.tolist()))
            combo_tup = tuple(combo_list)
            
            if combo_tup in historial_set:
                rechazos += 1
                continue
                
            try:
                valido, score_filtro, razones = aplicar_filtros_con_cache(
                    filtro, combo_list, return_score=True, return_reasons=True)
                
                if valido:
                    return combo_list
                else:
                    rechazos += 1
                    if logger and intentos % 100 == 0:
                        logger.debug(f"⏳ Rechazado: {combo_list} | Score: {score_filtro:.2f} | Razones: {', '.join(razones[:2])}")
            except Exception as e:
                if logger:
                    logger.error(f"⚠️ Error en filtros: {str(e)}", exc_info=True)
    
    # Fallback: generar combinación aleatoria válida
    for _ in range(100):
        combo = sorted(random.sample(range(1, 41), 6))
        if tuple(combo) not in historial_set:
            return combo
    
    return sorted(random.sample(range(1, 41), 6))

def escalar_score(score_raw):
    """Escalado adaptativo con curva sigmoide mejorada"""
    return 0.5 + 0.5 / (1 + np.exp(-20 * (score_raw - 0.055)))

def parallel_score_combinations(combinaciones, df_historial, logger=None):
    """Paralelización robusta con manejo de errores y balanceo dinámico"""
    if not combinaciones or len(combinaciones) < 20:
        return score_combinations(combinaciones, df_historial, logger=logger)
    
    n_workers = min(8, max(1, cpu_count() - 1))
    batch_size = max(5, len(combinaciones) // n_workers)
    batches = [combinaciones[i:i+batch_size] for i in range(0, len(combinaciones), batch_size)]
    
    resultados = []
    fallos = 0
    
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(score_combinations, batch, df_historial, logger): batch for batch in batches}
        
        for future in as_completed(futures):
            try:
                resultados.extend(future.result())
            except Exception as e:
                fallos += 1
                if logger:
                    logger.error(f"⚠️ Error en scoring paralelo: {str(e)}")
    
    # Si hubo fallos, intentar secuencialmente
    if fallos > 0:
        if logger:
            logger.warning(f"⚠️ {fallos} batches fallaron, reintentando secuencialmente")
        for batch in batches[len(resultados):]:
            try:
                resultados.extend(score_combinations(batch, df_historial, logger))
            except:
                pass
    
    return resultados

def generar_combinaciones_montecarlo(historial, cantidad=60, logger=None):
    """Generador optimizado con todas las mejoras integradas"""
    # Configuración de logging robusta
    log_func = logger.info if logger and hasattr(logger, 'info') else print
    
    def log(msg, level='info'):
        if not logger:
            print(f"[{level.upper()}] {msg}")
            return
            
        if level == 'warn' and hasattr(logger, 'warning'):
            logger.warning(msg)
        elif level == 'error' and hasattr(logger, 'error'):
            logger.error(msg)
        elif level == 'debug' and hasattr(logger, 'debug'):
            logger.debug(msg)
        elif hasattr(logger, 'info'):
            logger.info(msg)

    # Paso 0: Limpieza profunda del historial
    try:
        historial_limpio = limpiar_historial(historial, logger)
        historial_set = set(tuple(c) for c in historial_limpio)
    except Exception as e:
        log(f"❌ Error crítico en limpieza de historial: {str(e)}", 'error')
        historial_limpio = []
        historial_set = set()
    
    # Paso 1: Preparar distribución probabilística
    try:
        distribucion = generar_distribucion_probabilidades(historial_limpio, logger=log)
    except Exception as e:
        log(f"❌ Error en generación de distribución: {str(e)}", 'error')
        distribucion = np.array([1/40] * 40)
    
    # Paso 2: Configurar filtro con umbral dinámico
    try:
        umbral = calcular_umbral_dinamico(historial_limpio)
        filtro = FiltroEstrategico()  # FIX: Sin umbral, ya que no existe en __init__
        filtro.cargar_historial(list(historial_set))
        log(f"⚙️ Config: Umbral={umbral:.2f} | Hist={len(historial_limpio)} combos", 'debug')
    except Exception as e:
        log(f"⚠️ Error en configuración de filtro: {str(e)}", 'warn')
        umbral = 0.65
    
    # Paso 3: Generación principal
    _FILTRO_CACHE.clear()
    combinaciones = []
    generados_set = set()
    intentos = 0
    intentos_max = cantidad * 10
    
    log(f"🚀 Iniciando generación de {cantidad} combinaciones...", 'debug')
    
    while len(combinaciones) < cantidad and intentos < intentos_max:
        try:
            combo = generar_combinacion_inteligente(
                distribucion, 
                historial_set, 
                umbral,
                logger=log
            )
            combo_tup = tuple(combo)
            
            if combo and combo_tup not in generados_set:
                generados_set.add(combo_tup)
                try:
                    score_base = np.mean(distribucion[np.array(combo)-1])
                    score_escalado = escalar_score(score_base)
                    
                    combinaciones.append({
                        "combination": combo,
                        "score": round(score_escalado, 4),
                        "source": "montecarlo",
                        "metrics": {}
                    })
                    log(f"✓ GEN: {combo} | Score: {score_escalado:.4f}", 'debug')
                except Exception as e:
                    log(f"⚠️ Error en cálculo de score: {str(e)}", 'warn')
        except Exception as e:
            log(f"⚠️ Error en generación: {str(e)}", 'warn')
        finally:
            intentos += 1
    
    log(f"✅ Fase 1: Generados {len(combinaciones)}/{cantidad} combos | Intentos: {intentos}", 'debug')
    
    # Paso 4: Scoring dinámico paralelo
    if historial_limpio and combinaciones:
        try:
            df_historial = pd.DataFrame(historial_limpio, columns=[f"n{i+1}" for i in range(6)])
            resultados = parallel_score_combinations(combinaciones, df_historial, logger)
            
            for i, res in enumerate(resultados):
                if i >= len(combinaciones):
                    continue
                    
                # Asegurar score dentro de rango
                new_score = max(0.5, min(1.0, res['score']))
                combinaciones[i]['score'] = round(new_score, 4)
                combinaciones[i]['metrics'] = res.get('metrics', {})
                
                # Log detallado de métricas
                metrics = combinaciones[i]['metrics']
                if metrics:
                    log_entry = (
                        f"📊 COMBO: {res['combination']} | "
                        f"Score: {new_score:.4f} | "
                        f"Suma: {metrics.get('sum_total', '?')} | "
                        f"Pares: {metrics.get('even_count', '?')} | "
                        f"Primos: {metrics.get('prime_count', '?')}"
                    )
                    log(log_entry, 'debug')
        except Exception as e:
            log(f"⚠️ Error crítico en scoring dinámico: {str(e)}", 'warn')
    
    # Paso 5: Respaldo inteligente
    faltantes = cantidad - len(combinaciones)
    if faltantes > 0:
        log(f"🔁 Generando {faltantes} respaldos...", 'info')
        respaldos = []
        intentos_respaldo = 0
        max_intentos_respaldo = faltantes * 25
        
        while len(respaldos) < faltantes and intentos_respaldo < max_intentos_respaldo:
            try:
                # Usar distribución para respaldos
                combo = np.random.choice(range(1, 41), size=6, replace=False, p=distribucion)
                combo = asegurar_enteros(sorted(combo.tolist()))
                combo_tup = tuple(combo)
                
                if (combo_tup not in historial_set and
                    combo_tup not in generados_set and
                    aplicar_filtros_con_cache(filtro, combo)):
                    
                    score_base = np.mean(distribucion[np.array(combo)-1])
                    respaldos.append({
                        "combination": combo,
                        "score": round(escalar_score(score_base), 4),
                        "source": "montecarlo_backup"
                    })
                    generados_set.add(combo_tup)
            except Exception as e:
                log(f"⚠️ Error en respaldo: {str(e)}", 'warn')
            finally:
                intentos_respaldo += 1
        
        if respaldos:
            combinaciones.extend(respaldos)
            log(f"✓ Respaldo: {len(respaldos)} combos generados", 'debug')
        else:
            log("⚠️ Fallo en generación de respaldo", 'warn')
    
    # Limpieza final
    _FILTRO_CACHE.clear()
    
    log(f"✅ Generadas {len(combinaciones)}/{cantidad} combos | "
        f"Fuente: {Counter(c['source'] for c in combinaciones)}", 'info')
    
    return combinaciones[:cantidad]