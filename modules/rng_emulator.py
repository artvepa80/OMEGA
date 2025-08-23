# OMEGA_PRO_AI_v10.1/modules/rng_emulator.py – Emulador de RNG Mejorado con Estadísticas Avanzadas – Versión Corregida

import random
import numpy as np
import pandas as pd
import logging
from collections import Counter
from modules.filters.rules_filter import FiltroEstrategico
from modules.score_dynamics import score_combinations

# Instancia del filtro estratégico
filtro = FiltroEstrategico()

# Constante para convertir explícitamente a entero
CANTIDAD_NUMEROS = int(6)

def generar_distribucion_rng(historical_combinations, alpha=0.05):
    if not historical_combinations:
        return np.array([1/40] * 40)
    
    flat_numbers = [num for combo in historical_combinations for num in combo]
    frequency = Counter(flat_numbers)
    total_numbers = len(flat_numbers)
    
    distribucion = np.zeros(41)  # índice 1-40
    for num in range(1, 41):
        freq = frequency.get(num, 0)
        probabilidad = (freq / total_numbers) + alpha
        distribucion[num] = probabilidad
    
    distribucion = distribucion[1:41]
    total = distribucion.sum()
    return distribucion / total if total > 0 else np.array([1/40] * 40)

def emular_rng_combinaciones(historial: list, cantidad=200, seed=None, 
                             logger=None, positional=False, config=None):
    # FIX: Cambiado param 'historical_combinations' a 'historial' para coincidir con llamadas en consensus_engine.py
    default_config = {
        'peso_score': 0.7,
        'peso_frecuencia': 0.3,
        'min_score': 0.7
    }
    config = {**default_config, **(config or {})}
    
    def safe_log(message):
        if logger and hasattr(logger, 'info'):
            logger.info(message)
        elif logger:
            print(f"[RNG] {message}")  # Fallback para objetos no compatibles
    
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Convertir explícitamente a entero nativo
    cantidad = int(cantidad)
    
    historial_set = set(tuple(sorted(c)) for c in historial)
    numeros = list(range(1, 41))
    combinaciones = []
    
    distribucion = generar_distribucion_rng(historial)
    safe_log(f"🎰 [RNG] Distribución probabilística generada (semilla: {seed})")
    
    intentos = 0
    generadas = 0
    max_intentos = cantidad * 20
    
    safe_log(f"🎰 [RNG] Iniciando generación de {cantidad} combinaciones")
    
    while generadas < cantidad and intentos < max_intentos:
        intentos += 1
        try:
            # Convertir explícitamente los números a enteros nativos
            combo_arr = np.random.choice(numeros, size=CANTIDAD_NUMEROS, replace=False, p=distribucion)
            combo = [int(x) for x in combo_arr]  # Conversión explícita a int
            combo.sort()
        except ValueError:
            # Usar la constante convertida explícitamente a int
            combo = sorted(random.sample(numeros, CANTIDAD_NUMEROS))
        
        combo_tuple = tuple(combo)
        if combo_tuple in historial_set:
            continue
        if not filtro.aplicar_filtros(combo):
            continue
        if any(combo_tuple == tuple(c["combination"]) for c in combinaciones):
            continue
        
        combinaciones.append({
            "combination": combo,
            "score": 0.85,
            "source": "rng_emulado",
            "frecuencia_pesada": sum(distribucion[n-1] for n in combo) / CANTIDAD_NUMEROS
        })
        generadas += 1
        if generadas % 10 == 0:
            safe_log(f"🎰 [RNG] Generadas {generadas}/{cantidad} combinaciones")
    
    if generadas < cantidad:
        faltantes = cantidad - generadas
        safe_log(f"🔁 [RNG] Generando respaldo para {faltantes} combinaciones")
        for _ in range(faltantes * 5):
            if generadas >= cantidad:
                break
            # Usar la constante convertida explícitamente a int
            combo = sorted(random.sample(numeros, CANTIDAD_NUMEROS))
            combo_tuple = tuple(combo)
            if (combo_tuple not in historial_set and 
                filtro.aplicar_filtros(combo) and
                not any(combo_tuple == tuple(c["combination"]) for c in combinaciones)):
                combinaciones.append({
                    "combination": combo,
                    "score": 0.75,
                    "source": "rng_emulado_backup",
                    "frecuencia_pesada": sum(distribucion[n-1] for n in combo) / CANTIDAD_NUMEROS
                })
                generadas += 1
    
    if historial and combinaciones:
        try:
            df_historial = pd.DataFrame(historial, columns=[f"Bolilla {i+1}" for i in range(6)])
            combinaciones_scored = score_combinations(
                [{"combination": c["combination"], "source": c["source"]} for c in combinaciones],
                df_historial
            )
            for i, scored in enumerate(combinaciones_scored):
                if i < len(combinaciones):
                    score_estructural = scored["score"]
                    freq_pesada = combinaciones[i]["frecuencia_pesada"]
                    score_final = (
                        config['peso_score'] * score_estructural +
                        config['peso_frecuencia'] * freq_pesada
                    )
                    combinaciones[i]["score"] = max(config['min_score'], score_final)
        except Exception as e:
            safe_log(f"⚠️ [RNG] Error en scoring: {str(e)}")
    
    eficiencia = (generadas / intentos) * 100 if intentos > 0 else 0
    safe_log(f"📊 [RNG] Eficiencia: {generadas}/{intentos} intentos ({eficiencia:.1f}%)")
    safe_log(f"✅ [RNG] Generadas {len(combinaciones)} combinaciones válidas")
    
    return combinaciones