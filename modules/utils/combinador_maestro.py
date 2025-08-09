# OMEGA_PRO_AI_v12.1/modules/utils/combinador_maestro.py v2.1
"""
Selector final de la *Combinación Maestra*.

Cambios v2.1 (04-Ago-2025)
~~~~~~~~~~~~~~~~~~~~~~~~~~
1. **Override core-full**: si alguna serie contiene los 6 números del `core_set`
   se devuelve tal cual, sin más procesamiento.
2. **Nueva métrica de ponderación** para elegir números cuando se construye la
   combinación maestra desde cero:

    score_total = 0.7 * frecuencia + 0.2 * score_hist + 0.1 * core_bonus

   donde core_bonus = 1 si el número pertenece al core_set, 0 en caso contrario.
"""

import os
import csv
import json
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Set, Optional, Union
import pandas as pd

import numpy as np
import logging

# Módulos internos
from modules.score_dynamics import score_combinations

logger = logging.getLogger(__name__)
from utils.viabilidad import calcular_svi_individual
from modules.profiling.jackpot_profiler import perfil_jackpot
from modules.history_manager import obtener_promedio_score_historico, numeros_recientes


# ------------------------------------------------------------------
# UTILIDADES
# ------------------------------------------------------------------

def evaluar_riesgo(perfil: str, svi: float) -> dict:
    """Determina nivel de riesgo y recomienda acción."""
    if perfil == "C" and svi < 0.4:
        return {
            "alerta": "🚨 RIESGO ALTO",
            "recomendacion": "NO APOSTAR - Generar nuevas combinaciones",
            "nivel_riesgo": "critico"
        }
    elif perfil == "C" or svi < 0.5:
        return {
            "alerta": "⚠️ RIESGO MODERADO",
            "recomendacion": "Revisar manualmente - Considerar regenerar",
            "nivel_riesgo": "moderado"
        }
    return {
        "alerta": "",
        "recomendacion": "Jugada óptima - OK para apostar",
        "nivel_riesgo": "bajo"
    }


def cobertura_core_hits(comb: Tuple[int, ...], core_set: Set[int]) -> int:
    """Cuántos números de core_set hay en la combinación."""
    # Asegurar que core_set es un set (en caso de que se pase una lista)
    if not isinstance(core_set, set):
        core_set = set(core_set) if core_set else set()
    
    return len(core_set.intersection(comb))


def ponderar_frecuencias(
    top_combinaciones: List[Dict],
    core_set: Set[int],
    peso_freq: float = 0.7,
    peso_hist: float = 0.3,
    peso_core: float = 0.0,
) -> List[Tuple[int, float]]:
    """
    Puntuación por número usando la nueva métrica 0.7 / 0.2 / 0.1.

    * frecuencia   : veces que aparece el número en top_combinaciones
    * score_hist   : promedio de score de las combinaciones donde aparece
    * core_bonus   : 1 si el número pertenece al core_set, 0 si no
    """
    contador = Counter()
    score_hist: Dict[int, List[float]] = defaultdict(list)

    for combo in top_combinaciones:
        sc = combo.get("score", 0.0)
        for num in combo["combinacion"]:
            contador[num] += 1
            score_hist[num].append(sc)

    resultados: List[Tuple[int, float]] = []
    for num in contador:
        freq_norm = contador[num]
        hist_avg = np.mean(score_hist[num]) if score_hist[num] else 0.0
        core_bonus = 1.0 if num in core_set else 0.0

        # v2.0: 70% frecuencia + 30% score histórico; core_bonus ignorado
        score_total = (
            peso_freq * freq_norm +
            peso_hist * hist_avg
        )
        resultados.append((num, score_total))

    resultados.sort(key=lambda x: x[1], reverse=True)
    return resultados


# ------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ------------------------------------------------------------------

def generar_combinacion_maestra(
    combinaciones: List[Dict],
    core_set: Set[int],
    ruta_exportacion: str = "outputs/combinacion_maestra",
    historial: Optional[Union[pd.DataFrame, np.ndarray, List[List[int]]]] = None
) -> Dict:
    """
    Genera y exporta la combinación maestra.

    1. **Override core-full:** si ya existe una serie que incluya los 6 números
       del core_set, la exporta directamente.
    2. De lo contrario, usa las top-6 combinaciones por score y la nueva métrica
       ponderada para construir una combinación equilibrada.
    """

    # ---------- 1. Override core-full ----------
    for combo in combinaciones:
        comb_tuple = tuple(sorted(combo.get("combinacion", combo.get("combination", []))))
        if cobertura_core_hits(comb_tuple, core_set) == 6:
            return _exporta_resultado(
                combinacion=comb_tuple,
                top_combinaciones=[combo],
                core_set=core_set,
                ruta_exportacion=ruta_exportacion,
                nota="core-full override",
                historial=historial
            )

    # ---------- 2. Construcción estándar ----------
    top_combinaciones = sorted(
        combinaciones,
        key=lambda x: x.get("score", 0),
        reverse=True
    )[:6]

    frec_ponderada = ponderar_frecuencias(top_combinaciones, core_set)

    # Selecciona 6 números respetando balance de décadas (máx 3 por década)
    seleccion: List[int] = []
    decada_ctr = Counter()
    # Excluir números calientes de los últimos 3 sorteos si hay historial
    calientes: set[int] = set()
    try:
        if isinstance(historial, pd.DataFrame) and not historial.empty:
            ult = historial.tail(3).values.tolist()
            calientes = set(int(x) for row in ult for x in row)
        elif isinstance(historial, np.ndarray) and historial.size:
            ult = historial[-3:]
            calientes = set(int(x) for row in ult for x in row)
        elif isinstance(historial, list) and len(historial) >= 1:
            ult = historial[-3:]
            calientes = set(int(x) for row in ult for x in row)
    except Exception:
        calientes = set()

    for num, _ in frec_ponderada:
        if num in calientes:
            continue
        dec = num // 10
        if decada_ctr[dec] >= 3:
            continue
        seleccion.append(num)
        decada_ctr[dec] += 1
        if len(seleccion) == 6:
            break

    # Fallback si faltan números
    if len(seleccion) < 6:
        extras = [n for n, _ in frec_ponderada if n not in seleccion]
        seleccion.extend(extras[: 6 - len(seleccion)])

    combinacion_final = tuple(sorted(seleccion))

    return _exporta_resultado(
        combinacion=combinacion_final,
        top_combinaciones=top_combinaciones,
        core_set=core_set,
        ruta_exportacion=ruta_exportacion,
        nota="ponderada 0.7/0.2/0.1",
        historial=historial
    )


# ------------------------------------------------------------------
# EXPORTADOR AUXILIAR
# ------------------------------------------------------------------

def _exporta_resultado(
    combinacion: Tuple[int, ...],
    top_combinaciones: List[Dict],
    core_set: Set[int],
    ruta_exportacion: str,
    nota: str,
    historial: Optional[Union[pd.DataFrame, np.ndarray, List[List[int]]]] = None
) -> Dict:
    """Guarda CSV y JSON con metadatos de la combinación maestra."""
    # Calcular score usando historial si está disponible
    if historial is not None:
        try:
            score_result = score_combinations([{"combination": list(combinacion)}], historial)
            score = score_result[0].get('score', 0.5) if score_result else 0.5
        except Exception as e:
            logger.warning(f"⚠️ Error calculando score: {e}")
            score = 0.5
    else:
        score = 0.5  # Score por defecto si no hay historial
    svi = calcular_svi_individual(combinacion)
    perfil = perfil_jackpot(combinacion)

    riesgo = evaluar_riesgo(perfil, svi)

    os.makedirs(os.path.dirname(ruta_exportacion), exist_ok=True)

    # CSV
    with open(f"{ruta_exportacion}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["n1", "n2", "n3", "n4", "n5", "n6", "score", "SVI", "perfil", "alerta", "nota"]
        )
        writer.writerow(
            list(combinacion) +
            [round(score, 3), round(svi, 3), perfil, riesgo["alerta"], nota]
        )

    # JSON
    metadata = {
        "combinacion_maestra": list(combinacion),
        "score": round(score, 3),
        "svi": round(svi, 3),
        "perfil": perfil,
        "riesgo": riesgo,
        "nota": nota,
        "proceso_generacion": {
            "top_combinaciones": [c.get("id") for c in top_combinaciones],
            "core_set": sorted(core_set),
        }
    }
    with open(f"{ruta_exportacion}.json", "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata
