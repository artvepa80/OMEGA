# OMEGA_PRO_AI_v12.1/modules/calibrador_consenso.py
"""
Calibrador de pesos para el consenso de modelos OMEGA PRO AI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
• Recolecta estadísticas de cuántos números del `core_set` acierta cada modelo
  dentro del TOP-k de combinaciones.
• Ajusta los pesos aplicados en `consensus_engine` según reglas simples:
    - +0.05 si el modelo ≥ 4 core-hits en el TOP-k
    - −0.05 si el modelo ≤ 1 core-hit en el TOP-k
• Normaliza los pesos para que sumen 1.
• Guarda / carga los pesos en JSON (fácil de editar a mano si hace falta).

Uso programático (típico en predictor.py):
------------------------------------------
    from modules.calibrador_consenso import recalibrar_pesos

    # al final del ciclo, cuando ya conoces las combinaciones y el core_set
    nuevas_metricas = recalibrar_pesos(
        combinaciones=series_filtradas,
        core_set=core_set,
        k_top=10,
        ruta_pesos="config/pesos_modelos.json"
    )
"""

from __future__ import annotations
import json
import os
import logging
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set

logger = logging.getLogger("CalibradorConsenso")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(ch)


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _core_hits(comb: Tuple[int, ...], core_set: Set[int]) -> int:
    """Cuenta cuántos números del core_set están presentes en la combinación."""
    return len(core_set.intersection(comb))


def _normalizar(pesos: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(v, 0.0) for v in pesos.values())
    if total == 0:
        raise ValueError("La suma de pesos llegó a 0; revisa las reglas de ajuste.")
    return {m: round(v / total, 4) for m, v in pesos.items()}


def _cargar_pesos(ruta: str) -> Dict[str, float]:
    if not os.path.exists(ruta):
        logger.warning("⚠️  Archivo de pesos %s no existe; se crearán pesos iguales.", ruta)
        return {}
    with open(ruta, "r") as f:
        return json.load(f)


def _guardar_pesos(pesos: Dict[str, float], ruta: str) -> None:
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w") as f:
        json.dump(pesos, f, indent=2)
    logger.info("✅ Pesos actualizados guardados en %s -> %s", ruta, pesos)


# -------------------------------------------------------------------------
# API pública
# -------------------------------------------------------------------------

def recalibrar_pesos(
    combinaciones: List[Dict],
    core_set: Set[int],
    k_top: int = 10,
    ruta_pesos: str = "config/pesos_modelos.json",
    incremento: float = 0.05,
    decremento: float = 0.05,
    min_peso: float = 0.05,
) -> Dict[str, float]:
    """
    Ajusta y devuelve los pesos de cada modelo.

    Parameters
    ----------
    combinaciones : list[dict]
        Lista de dicts que DEBEN contener claves:
        • 'source'       -> str    (nombre o id del modelo)
        • 'combination'  -> tuple[int] | list[int]
        • 'score'        -> float  (para ordenar TOP-k)
    core_set : set[int]
        Conjunto de números calientes.
    k_top : int
        Número de combinaciones que se consideran para métricas.
    ruta_pesos : str
        Archivo JSON donde se almacenan los pesos.
    """

    if not combinaciones:
        logger.warning("No se proporcionaron combinaciones; no se recalibran pesos.")
        return {}

    # 1️⃣  Ordenamos por score y tomamos TOP-k
    top_k = sorted(combinaciones, key=lambda x: x.get("score", 0), reverse=True)[:k_top]

    # 2️⃣  Contamos core-hits por modelo
    core_hits_por_modelo: Dict[str, int] = defaultdict(int)
    for c in top_k:
        modelo = c["source"]  # Use 'source' key which is used throughout codebase
        comb = tuple(c["combination"])
        core_hits_por_modelo[modelo] += _core_hits(comb, core_set)

    logger.info("🔍 Core-hits en TOP-%d: %s", k_top, dict(core_hits_por_modelo))

    # 3️⃣  Cargamos pesos actuales
    pesos = _cargar_pesos(ruta_pesos)
    if not pesos:
        # Inicializa con 1 / n modelos si no había archivo
        modelos = {c["source"] for c in combinaciones}
        pesos = {m: round(1.0 / len(modelos), 4) for m in modelos}

    # 4️⃣  Aplicamos reglas de ajuste
    for modelo, hits in core_hits_por_modelo.items():
        if hits >= 4:
            pesos[modelo] = pesos.get(modelo, 0.0) + incremento
            logger.info("⬆️  %s gana +%.2f (hits=%d)", modelo, incremento, hits)
        elif hits <= 1:
            pesos[modelo] = max(min_peso, pesos.get(modelo, 0.0) - decremento)
            logger.info("⬇️  %s pierde %.2f (hits=%d)", modelo, decremento, hits)

    # 5️⃣  Normalizamos
    pesos = _normalizar(pesos)

    # 6️⃣  Guardamos
    _guardar_pesos(pesos, ruta_pesos)

    return pesos


# -------------------------------------------------------------------------
# CLI rápido para debug
# -------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import random

    parser = argparse.ArgumentParser(description="Recalibrador rápido de pesos")
    parser.add_argument("--dummy", action="store_true", help="Ejecuta demo con datos ficticios")
    parser.add_argument("--pesos", default="config/pesos_modelos.json", help="Ruta archivo pesos")
    args = parser.parse_args()

    if args.dummy:
        core = {11, 18, 21, 23, 32, 33}
        modelos = ["MonteCarlo", "Apriori", "Clustering", "Genetico"]
        dummy = []
        for i in range(30):
            modelo = random.choice(modelos)
            comb = tuple(sorted(random.sample(range(1, 41), 6)))
            score = random.random()
            dummy.append({"source": modelo, "combination": comb, "score": score})
        recalibrar_pesos(dummy, core_set=core, ruta_pesos=args.pesos)
    else:
        parser.print_help()
