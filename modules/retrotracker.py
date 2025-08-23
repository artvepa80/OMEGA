# modules/learning/retrotracker.py – Módulo de Retroanálisis OMEGA PRO AI v10.1

import json
from datetime import datetime
import logging
import pandas as pd
import numpy as np
from typing import Any, List, Dict, Union, Optional
from joblib import Memory
import matplotlib.pyplot as plt
from numba import njit
from modules.learning.gboost_jackpot_classifier import GBoostJackpotClassifier  # Import the class directly

# Setup cache
memory = Memory(".retrotracker_cache", verbose=0)

# Logger
logger = logging.getLogger("RetroTracker")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

class RetroTracker:
    def __init__(self, log_path="logs/retro_predictions.json"):
        self.log_path = log_path
        self.predictions = []
        try:
            with open(self.log_path, "r") as f:
                self.predictions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("✅ RetroTracker inicializado")

    def log_predictions(self, combinations: List[Dict[str, Any]]):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "predictions": combinations
        }
        self.predictions.append(entry)
        with open(self.log_path, "w") as f:
            json.dump(self.predictions, f, indent=2)
        logger.info(f"✅ {len(combinations)} predicciones registradas en {self.log_path}")

    def get_results(self, historical_draws: pd.DataFrame = None):
        """
        Compara predicciones con sorteos históricos y retorna resultados.
        """
        results = []
        for entry in self.predictions:
            matches = 0
            if historical_draws is not None:
                hist_set = {tuple(sorted(row)) for row in historical_draws.values.tolist()}
                matches = sum(1 for pred in entry["predictions"] if tuple(sorted(pred["combination"])) in hist_set)
            results.append({
                "timestamp": entry["timestamp"],
                "total_predictions": len(entry["predictions"]),
                "matches": matches,
                "accuracy": matches / len(entry["predictions"]) if entry["predictions"] else 0
            })
        return results

@njit
def calcular_aciertos_vectorizados(combinacion: np.ndarray, resultados: np.ndarray) -> np.ndarray:
    """
    Vectoriza el cálculo de aciertos entre una combinación y todos los resultados históricos.
    """
    return np.sum(np.isin(resultados, combinacion), axis=1)

def generar_metrica_distribucion(aciertos: np.ndarray) -> str:
    hist, _ = np.histogram(aciertos, bins=np.arange(0, 8))
    return ",".join(str(h) for h in hist)

def graficar_histograma(aciertos: np.ndarray, combinacion_id: int):
    plt.figure()
    plt.hist(aciertos, bins=np.arange(0, 8) - 0.5, rwidth=0.8)
    plt.title(f"Distribución de Aciertos - Combinación #{combinacion_id}")
    plt.xlabel("Aciertos")
    plt.ylabel("Frecuencia")
    plt.grid(True)
    plt.show()

@memory.cache
def evaluar_combinaciones_batch(
    combinaciones: List[Dict],
    resultados_np: np.ndarray,
    modelo_gboost: Optional[GBoostJackpotClassifier] = None,
    safe_mode: bool = True
) -> List[Dict]:
    pred_list = [sorted(c.get('combinacion', [])) for c in combinaciones]  # FIXED: Added fallback for missing 'combinacion'
    scores = [c.get("score", 0) for c in combinaciones]
    pred_np_list = [np.array(c, dtype=np.int32) for c in pred_list if len(c) == 6]  # FIXED: Filter invalid lengths

    # Batch de perfiles
    perfiles = ["?"] * len(pred_list)
    if modelo_gboost is not None:
        try:
            perfiles = modelo_gboost.predict(pred_list).tolist()  # FIXED: Use model's predict method
        except Exception as e:
            if safe_mode:
                logger.error(f"Error al predecir perfil (modo seguro): {e}")
            else:
                raise

    reportes = []
    for idx, (pred_np, score, perfil) in enumerate(zip(pred_np_list, scores, perfiles)):
        if len(pred_np) != 6:
            continue  # Skip invalid
        aciertos = calcular_aciertos_vectorizados(pred_np, resultados_np)

        reporte = {
            "indice": idx,
            "combinacion": pred_np.tolist(),
            "aciertos_max": int(np.max(aciertos)),
            "aciertos_prom": round(float(np.mean(aciertos)), 2),
            "aciertos_std": round(float(np.std(aciertos)), 2),
            "frecuencia_4+": int(np.sum(aciertos >= 4)),
            "aciertos_>=3_pct": round(100 * np.sum(aciertos >= 3) / len(aciertos), 2) if len(aciertos) > 0 else 0,
            "aciertos_histograma": generar_metrica_distribucion(aciertos),
            "score": score,
            "perfil_gboost": perfil,
            "aciertos_raw": aciertos.tolist()  # útil para análisis posterior
        }
        reportes.append(reporte)
    return reportes

def retrotracker(
    historial: pd.DataFrame,
    combinaciones: List[Dict[str, Union[List[int], float]]],
    modelo_gboost=None,
    ventana: int = 500,
    graficar: bool = False,
    safe_mode: bool = True
) -> pd.DataFrame:
    """
    Simula aciertos de combinaciones sobre sorteos pasados para evaluar el rendimiento de OMEGA.

    Parámetros:
        historial: DataFrame con sorteos históricos.
        combinaciones: Lista de combinaciones a evaluar.
        modelo_gboost: Modelo GBoost para predicción de perfil (opcional).
        ventana: Cuántos sorteos del pasado considerar.
        graficar: Mostrar histogramas de aciertos.
        safe_mode: No lanzar errores críticos.

    Retorna:
        DataFrame con estadísticas por combinación.
    """
    logger.info(f"🔍 Ejecutando retrotracker sobre los últimos {ventana} sorteos...")

    if historial.empty:
        logger.warning("⚠️ Historial vacío.")
        return pd.DataFrame()

    if not combinaciones:
        logger.warning("⚠️ Lista de combinaciones vacía.")
        return pd.DataFrame()

    if modelo_gboost is None:
        logger.warning("⚠️ Modelo GBoost no proporcionado, inicializando y cargando...")
        modelo_gboost = GBoostJackpotClassifier()
        try:
            modelo_gboost.load("models/prod_jackpot_classifier.pkl")  # FIXED: Use load method
        except FileNotFoundError:
            logger.error("🚨 Modelo no encontrado, usando predicciones default '?'")
            modelo_gboost = None

    historial = historial.tail(ventana).reset_index(drop=True)
    resultados = historial[[col for col in historial.columns if "Bolilla" in col]]
    resultados_np = resultados.to_numpy(dtype=np.int32)

    logger.info(f"✅ Evaluando {len(combinaciones)} combinaciones...")

    reportes = evaluar_combinaciones_batch(
        combinaciones=combinaciones,
        resultados_np=resultados_np,
        modelo_gboost=modelo_gboost,
        safe_mode=safe_mode
    )

    if graficar:
        for r in reportes:
            aciertos = np.array(r["aciertos_raw"])
            graficar_histograma(aciertos, r["indice"])

    logger.info("✅ Retrotracker finalizado.")
    df_resultado = pd.DataFrame(reportes).drop(columns=["aciertos_raw"])
    return df_resultado