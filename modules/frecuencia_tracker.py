# OMEGA_PRO_AI_v10.1/modules/reporting/frecuencia_tracker.py
# =======================

"""
Módulo utilitario para calcular la frecuencia de aparición de cada número en
un lote de combinaciones y extraer el *core set* de números dominantes.

Se diseñó para integrarse con OMEGA PRO AI:
    1. `top_numbers(...)` devuelve un conjunto con los *n* números más repetidos
       en el pool generado (por defecto 6).
    2. `frequency_dataframe(...)` produce un DataFrame ordenado por frecuencia.
    3. `save_frequency_csv(...)` guarda un CSV listo para análisis externo.

Uso típico (desde predictor o retrotracker):
    >>> from modules.reporting.frecuencia_tracker import top_numbers
    >>> core_set = top_numbers(series_generadas, top=6)
"""

from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Dict, Set

import pandas as pd

# ---------------------------------------------------------------------------
# Logging setup (re‑uses global config if present)
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _ch = logging.StreamHandler()
    _ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(_ch)

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _flatten(combinations: Iterable[Iterable[int]]) -> List[int]:
    """Generador que aplana una lista de combinaciones en una secuencia de ints."""
    for combo in combinations:
        for n in combo:
            yield int(n)


def compute_frequency(combinations: Iterable[Iterable[int]]) -> Dict[int, int]:
    """Cuenta ocurrencias de cada número en *combinations*.

    Args:
        combinations: Iterable de combinaciones (cada combinación es Iterable[int]).

    Returns:
        dict {numero: frecuencia}
    """
    return Counter(_flatten(combinations))


def top_numbers(combinations: Iterable[Iterable[int]], top: int = 6) -> Set[int]:
    """Devuelve los *top* números más frecuentes como un set."""
    freq = compute_frequency(combinations)
    core = {num for num, _ in freq.most_common(top)}
    logger.info("🔍 Core set (top %d): %s", top, sorted(core))
    return core


def frequency_dataframe(combinations: Iterable[Iterable[int]]) -> pd.DataFrame:
    """DataFrame ordenado de frecuencias (desc).

    Columnas: *number*, *count*.
    """
    freq = compute_frequency(combinations)
    df = pd.DataFrame(freq.items(), columns=["number", "count"])
    df = df.sort_values("count", ascending=False).reset_index(drop=True)
    return df


def save_frequency_csv(
    combinations: Iterable[Iterable[int]],
    path: str | Path = "reports/frecuencias.csv",
) -> None:
    """Guarda la tabla de frecuencias en *path* (crea dir si no existe)."""
    df = frequency_dataframe(combinations)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("💾 Frequency table saved to %s", path)


# ---------------------------------------------------------------------------
# CLI (opcional)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse, json

    ap = argparse.ArgumentParser(description="Generate frequency table from JSON list of combinations")
    ap.add_argument("--input", required=True, help="Ruta a un JSON que contenga una lista de combinaciones (lista de listas)")
    ap.add_argument("--output", default="reports/frecuencias.csv", help="Ruta donde guardar el CSV de frecuencias")
    ap.add_argument("--top", type=int, default=6, help="Cuántos números devolver en el core set")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as fh:
        combos = json.load(fh)

    core = top_numbers(combos, top=args.top)
    print("Core set:", sorted(core))
    save_frequency_csv(combos, args.output)
