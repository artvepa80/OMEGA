# montecarlo_model.py – Versión mejorada con distribución probabilística inteligente y score dinámico

import numpy as np
import pandas as pd
import random
from collections import Counter
from modules.filters.rules_filter import aplicar_filtros
from modules.score_dynamics import score_combinations

def generar_distribucion_probabilidades(historial, alpha=0.1):
    """
    Crea una distribución de probabilidad basada en:
    - Frecuencia histórica general
    - Tendencia reciente (últimos 20 sorteos)
    - Suavizado para evitar probabilidades cero
    """
    historial = list(historial)  # 👈 protección total

    if not historial:
        return np.array([1/40] * 40)

    todos_numeros = [num for combo in historial for num in combo]
    frecuencia_total = Counter(todos_numeros)
    frecuencia_reciente = Counter([num for combo in historial[-20:] for num in combo])

    distribucion = np.zeros(41)  # índice 1–40
    for num in range(1, 41):
        base = frecuencia_total.get(num, 0) / len(todos_numeros)
        reciente = frecuencia_reciente.get(num, 0) / (20 * 6)
        distribucion[num] = (0.7 * base) + (0.3 * reciente) + alpha

    distribucion = distribucion[1:41]
    return distribucion / distribucion.sum()

def generar_combinacion_inteligente(distribucion, historial_set, max_intentos=100):
    """Genera una combinación única y válida con filtros aplicados"""
    numeros = list(range(1, 41))
    for _ in range(max_intentos):
        combo = np.random.choice(numeros, size=6, replace=False, p=distribucion)
        combo = sorted(combo)
        if tuple(combo) not in historial_set and aplicar_filtros(combo, historial_set):
            return [int(n) for n in combo]
    return None  # Si falla, devolver None para manejo posterior

def generar_combinaciones_montecarlo(historial, cantidad=60, logger=print):
    """
    Genera combinaciones con lógica Monte Carlo avanzada:
    - Basado en frecuencias reales y recientes
    - Aplicación de filtros y score adaptativo
    - Manejo de duplicados y respaldo automático
    """
    historial_set = set(tuple(sorted(c)) for c in historial) if historial else set()
    distribucion = generar_distribucion_probabilidades(historial)

    combinaciones = []
    intentos = 0
    intentos_max = cantidad * 5

    while len(combinaciones) < cantidad and intentos < intentos_max:
        combo = generar_combinacion_inteligente(distribucion, historial_set)
        if combo:
            combo_tup = tuple(combo)
            if combo_tup not in [c['combination'] for c in combinaciones]:
                combinaciones.append({
                    "combination": combo,
                    "score": 0.8,
                    "source": "montecarlo"
                })
                logger(f"[MONTECARLO] Combinación válida generada: {combo}")
        else:
            intentos += 1

    # Puntuar combinaciones si hay historial
    if historial and combinaciones:
        df_historial = pd.DataFrame(historial, columns=[f"Bolilla {i+1}" for i in range(6)])
        combinaciones_scored = score_combinations(combinaciones, df_historial)
        for i, scored in enumerate(combinaciones_scored):
            combinaciones[i]['score'] = max(0.5, scored['score'])

    # Respaldo si faltan combinaciones
    faltantes = cantidad - len(combinaciones)
    if faltantes > 0:
        logger(f"🔁 [MONTECARLO] Generando respaldo para {faltantes} combinaciones")
        for _ in range(faltantes):
            combo = sorted(random.sample(range(1, 41), 6))
            if tuple(combo) not in historial_set and aplicar_filtros(combo, historial_set):
                combinaciones.append({
                    "combination": combo,
                    "score": 0.7,
                    "source": "montecarlo"
                })

    logger(f"✅ [MONTECARLO] Total combinaciones generadas: {len(combinaciones)}")
    return combinaciones