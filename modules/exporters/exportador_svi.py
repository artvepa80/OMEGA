# modules/exporters/exportador_svi.py – Exportador de combinaciones SVI (OMEGA PRO AI v10.10)

import os
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
from utils.logging.unified_logger import log_info, log_error
from core.consensus_engine import validate_combination

# Configuración del logger
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def exportar_combinaciones_svi(combinaciones: List[Dict[str, Any]], output_path: str = "results/svi_export.csv", umbral: float = 0.5) -> None:
    """
    Exporta las combinaciones con SVI a un CSV.
    Registra combinaciones con SVI por debajo del umbral y maneja errores.

    Args:
        combinaciones (List[Dict[str, Any]]): Lista de diccionarios con 'combination', 'score', 'svi_score', 'source'.
        output_path (str): Ruta del archivo CSV de salida (default: 'results/svi_export.csv').
        umbral (float): Umbral para registrar combinaciones con SVI bajo (default: 0.5).
    """
    try:
        log_info(f"📤 Starting export to {output_path} with umbral={umbral}")

        # Validar entrada
        if not combinaciones:
            log_error("🚨 No combinations provided, exporting fallback")
            combinaciones = [{
                "combination": [1, 2, 3, 4, 5, 6],
                "score": 0.5,
                "svi_score": 0.5,
                "source": "fallback"
            }]

        # Validar estructura de combinaciones
        valid_combinaciones = []
        for comb in combinaciones:
            if not isinstance(comb, dict):
                log_info(f"⚠️ Skipping invalid combination: {comb} (not a dict)")
                continue
            if not validate_combination(comb.get("combination", [])):
                log_info(f"⚠️ Skipping invalid combination: {comb.get('combination', [])}")
                continue
            if "score" not in comb or not isinstance(comb["score"], (int, float)):
                comb["score"] = 1.0
                log_info(f"⚠️ Missing or invalid score for {comb['combination']}, defaulting to 1.0")
            if "svi_score" not in comb or not isinstance(comb["svi_score"], (int, float)):
                comb["svi_score"] = 0.5
                log_info(f"⚠️ Missing or invalid svi_score for {comb['combination']}, defaulting to 0.5")
            if "source" not in comb:
                comb["source"] = "unknown"
                log_info(f"⚠️ Missing source for {comb['combination']}, defaulting to 'unknown'")
            valid_combinaciones.append(comb)

        if not valid_combinaciones:
            log_error("🚨 No valid combinations after validation, using fallback")
            valid_combinaciones = [{
                "combination": [1, 2, 3, 4, 5, 6],
                "score": 0.5,
                "svi_score": 0.5,
                "source": "fallback"
            }]

        # Crear directorio de salida
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Preparar datos para CSV
        data = [
            {
                "combination": str(comb["combination"]),
                "score": comb["score"],
                "svi_score": comb["svi_score"],
                "source": comb["source"],
                "timestamp": datetime.now().isoformat()
            }
            for comb in valid_combinaciones
        ]

        # Registrar combinaciones con SVI bajo
        for comb in valid_combinaciones:
            if comb["svi_score"] < umbral:
                log_info(f"⚠️ Low SVI: {comb['combination']} | Source: {comb['source']} | SVI: {comb['svi_score']:.4f}")

        # Exportar a CSV
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        log_info(f"✅ Successfully exported {len(valid_combinaciones)} combinations to {output_path}")

    except Exception as e:
        log_error(f"🚨 Export error: {str(e)}")
        # Exportar fallback en caso de error
        fallback_data = [{
            "combination": str([1, 2, 3, 4, 5, 6]),
            "score": 0.5,
            "svi_score": 0.5,
            "source": "fallback",
            "timestamp": datetime.now().isoformat()
        }]
        try:
            pd.DataFrame(fallback_data).to_csv(output_path, index=False)
            log_info(f"✅ Exported fallback combination to {output_path}")
        except Exception as e2:
            log_error(f"🚨 Failed to export fallback: {str(e2)}")
        raise
