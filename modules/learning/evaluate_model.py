# modules/learning/evaluate_model.py – Módulo de Evaluación de Modelos OMEGA PRO AI v10.1

import os
import pandas as pd
import joblib
import logging
from datetime import datetime
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer  # ADDED: For NaN handling
from modules.profiling.jackpot_profiler import perfil_jackpot
import matplotlib.pyplot as plt
import seaborn as sns  # ADDED: For confusion matrix visualization

# --- Configuración ---
DATA_PATH = "data/processed/DataFrame_completo_de_sorteos.csv"
MODEL_PATH = "models/gboost_model.pkl"
SCALER_PATH = "models/gboost_scaler.pkl"
EVAL_LOG = "metrics/evaluation_log.csv"
CONFUSION_IMG = "metrics/confusion_matrix.png"

# --- Logging ---
logger = logging.getLogger("EvaluateModel")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# --- Funciones ---

def cargar_datos() -> pd.DataFrame:
    """
    Carga y valida los datos históricos.
    """
    if not os.path.exists(DATA_PATH):
        logger.error(f"❌ No se encuentra el archivo de datos: {DATA_PATH}")
        return pd.DataFrame()
    df = pd.read_csv(DATA_PATH)
    # Use n1-n6 columns for this processed dataset, not bolilla columns
    bolilla_cols = [col for col in df.columns if col.lower().startswith("bolilla")]
    if bolilla_cols:
        df = df[bolilla_cols]  # Use bolilla columns if available
    else:
        df = df[['n1', 'n2', 'n3', 'n4', 'n5', 'n6']]  # Use n1-n6 columns
    if df.shape[1] != 6:
        logger.error("❌ Número de columnas Bolilla inválido.")
        return pd.DataFrame()
    imputer = SimpleImputer(strategy='mean')
    df = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
    df = df.dropna()
    # Check if any values are outside the valid range [1,40]
    values_too_low = (df < 1).any().any()
    values_too_high = (df > 40).any().any()
    
    if values_too_low or values_too_high:
        logger.warning("⚠️ Algunos valores fuera de [1,40], corrigiendo...")
        df = df.clip(1, 40)
    return df

def evaluar_modelo(n_ultimos: int = 50, model_path: str = MODEL_PATH, scaler_path: str = SCALER_PATH, visualize: bool = False):
    """
    Evalúa el modelo con los últimos n_ultimos sorteos.
    
    Parámetros:
        n_ultimos (int): Número de sorteos a evaluar.
        model_path (str): Ruta al modelo.
        scaler_path (str): Ruta al scaler.
        visualize (bool): Generar gráfico de confusion matrix.
    
    Retorna:
        dict: Métricas de evaluación.
    """
    logger.info(f"🔍 Evaluando modelo con los últimos {n_ultimos} sorteos...")

    # Cargar datos
    df = cargar_datos()
    if df.empty:
        logger.error("🚫 El DataFrame está vacío. No se puede evaluar.")
        return {}

    # Seleccionar últimos sorteos
    df_eval = df.tail(n_ultimos).astype(int)
    etiquetas_reales = df_eval.apply(lambda row: perfil_jackpot(row.tolist()), axis=1)

    # Cargar modelo y escalador
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        logger.error("🚫 Modelo o scaler no encontrado.")
        return {}

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    X_eval = scaler.transform(df_eval)
    y_pred = model.predict(X_eval)

    acc = accuracy_score(etiquetas_reales, y_pred)
    f1 = f1_score(etiquetas_reales, y_pred, average="macro")
    report = classification_report(etiquetas_reales, y_pred, output_dict=True)
    cm = confusion_matrix(etiquetas_reales, y_pred)

    logger.info(f"✅ Accuracy: {acc:.4f} | F1 macro: {f1:.4f}")
    logger.info("📊 Reporte de clasificación:\n" + classification_report(etiquetas_reales, y_pred))

    # Guardar log de evaluación
    log = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "accuracy": round(acc, 4),
        "f1_macro": round(f1, 4),
        "n_eval": n_ultimos,
        "modelo": os.path.basename(model_path)
    }])
    if os.path.exists(EVAL_LOG):
        log.to_csv(EVAL_LOG, mode="a", index=False, header=False)
    else:
        log.to_csv(EVAL_LOG, index=False)
    logger.info(f"✅ Evaluación registrada en: {EVAL_LOG}")

    # Visualización opcional
    if visualize:
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
        plt.title("Confusion Matrix")
        plt.xlabel("Predicted")
        plt.ylabel("Actual")
        plt.savefig(CONFUSION_IMG)
        logger.info(f"✅ Confusion matrix guardada en: {CONFUSION_IMG}")

    return {
        "accuracy": acc,
        "f1_macro": f1,
        "report": report,
        "confusion_matrix": cm
    }

# Alias para compatibilidad con imports en inglés
evaluate_model_performance = evaluar_modelo

# --- Ejecución directa ---
if __name__ == "__main__":
    evaluar_modelo(n_ultimos=200, visualize=True)