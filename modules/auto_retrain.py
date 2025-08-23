# modules/learning/auto_retrain.py

import os
import sys
import argparse
import pandas as pd
try:
    import joblib
except ImportError:
    joblib = None
import logging
from datetime import datetime
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, f1_score
import matplotlib.pyplot as plt
from modules.profiling.jackpot_profiler import perfil_jackpot

# --- Configuración ---
DATA_PATH = "data/processed/DataFrame_completo_de_sorteos.csv"
BASE_MODEL_PATH = "models/gboost_model.pkl"
VERSIONED_DIR = "models/versioned"
SCALER_PATH = "models/gboost_scaler.pkl"
STATS_PATH = "models/gboost_model.stats"
METRICS_LOG = "metrics/training_log.csv"
FEATURE_IMPORTANCE_IMG = "metrics/feature_importance.png"

# --- Logging ---
logger = logging.getLogger("AutoRetrain")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# --- Utilidades ---

def cargar_data_actual() -> pd.DataFrame:
    if not os.path.exists(DATA_PATH):
        logger.error(f"❌ Archivo de datos no encontrado: {DATA_PATH}")
        return pd.DataFrame()
    df = pd.read_csv(DATA_PATH).dropna()
    return df

def calcular_etiquetas(df: pd.DataFrame) -> pd.Series:
    return df.apply(lambda row: perfil_jackpot(row.tolist()), axis=1)

def obtener_num_sorteos_modelo() -> int:
    if not os.path.exists(STATS_PATH):
        return 0
    try:
        with open(STATS_PATH, 'r') as f:
            return int(f.read().strip())
    except Exception as e:
        logger.warning(f"⚠️ Error leyendo stats: {e}")
        return 0

def guardar_num_sorteos_actual(n: int):
    with open(STATS_PATH, 'w') as f:
        f.write(str(n))

def guardar_metricas(metrics: dict):
    df = pd.DataFrame([metrics])
    if os.path.exists(METRICS_LOG):
        df.to_csv(METRICS_LOG, mode='a', index=False, header=False)
    else:
        df.to_csv(METRICS_LOG, index=False)

def guardar_importancias(model, feature_names):
    importancias = model.feature_importances_
    indices = importancias.argsort()[::-1]
    top_features = [feature_names[i] for i in indices[:10]]
    top_scores = importancias[indices[:10]]

    plt.figure()
    plt.bar(top_features, top_scores)
    plt.title("Top 10 Importancia de Características")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(FEATURE_IMPORTANCE_IMG)
    plt.close()
    logger.info(f"📊 Feature importance guardado en: {FEATURE_IMPORTANCE_IMG}")

def get_model(tipo: str):
    if tipo == "rf":
        return RandomForestClassifier(n_estimators=200, max_depth=5, random_state=42)
    elif tipo == "gboost":
        return GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42)
    else:
        raise ValueError(f"Modelo '{tipo}' no soportado.")

def optimizar_modelo(X, y, base_model):
    param_grid = {
        "n_estimators": [100, 200],
        "max_depth": [3, 5],
        "learning_rate": [0.01, 0.05, 0.1]
    }
    search = GridSearchCV(base_model, param_grid, cv=3, n_jobs=-1)
    search.fit(X, y)
    logger.info(f"🔍 Mejor modelo encontrado: {search.best_params_}")
    return search.best_estimator_

def reentrenar_modelo(df: pd.DataFrame, etiquetas: pd.Series, model_type="gboost", optimize=False):
    logger.info(f"⚙️ Entrenando modelo ({model_type}) {'con optimización' if optimize else ''}...")

    X = df.astype(int).values
    y = etiquetas
    feature_names = df.columns.tolist()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.25, random_state=42, stratify=y
    )

    base_model = get_model(model_type)
    model = optimizar_modelo(X_train, y_train, base_model) if optimize else base_model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="macro")
    report = classification_report(y_test, y_pred)

    logger.info(f"✅ Accuracy: {acc:.4f} | F1 macro: {f1:.4f}")
    logger.info("📊 Reporte:\n" + report)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = f"{VERSIONED_DIR}/model_{model_type}_{timestamp}.pkl"
    joblib.dump(model, BASE_MODEL_PATH)
    joblib.dump(model, model_path)
    joblib.dump(scaler, SCALER_PATH)

    guardar_num_sorteos_actual(len(df))
    guardar_metricas({
        "timestamp": timestamp,
        "modelo": model_type,
        "accuracy": round(acc, 4),
        "f1_macro": round(f1, 4),
        "n_sorteos": len(df),
        "model_path": model_path
    })

    guardar_importancias(model, feature_names)
    logger.info(f"💾 Modelo guardado en: {model_path}")
    logger.info(f"💾 Modelo base actualizado: {BASE_MODEL_PATH}")

def auto_retrain(force=False, model_type="gboost", optimize=False):
    logger.info("🔍 Verificando necesidad de reentrenamiento...")

    df = cargar_data_actual()
    if df.empty:
        logger.error("🚫 No se puede continuar: DataFrame vacío.")
        return

    df_bolas = df[[col for col in df.columns if col.lower().startswith("bolilla")]]  # Case-insensitive bolilla column selection
    if df_bolas.empty:
        logger.error("🚫 Columnas de bolillas no encontradas.")
        return

    etiquetas = calcular_etiquetas(df_bolas)
    num_actual = len(df_bolas)
    num_modelo = obtener_num_sorteos_modelo()

    if force or num_actual > num_modelo:
        logger.info(f"📈 Reentrenando con {num_actual} sorteos...")
        reentrenar_modelo(df_bolas, etiquetas, model_type, optimize)
    else:
        logger.info("🔁 No hay nuevos sorteos. Reentrenamiento no necesario.")

# --- CLI ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto retrain de modelo Jackpot")
    parser.add_argument("--force", action="store_true", help="Forzar reentrenamiento incluso sin nuevos sorteos")
    parser.add_argument("--model", choices=["gboost", "rf"], default="gboost", help="Tipo de modelo a usar")
    parser.add_argument("--optimize", action="store_true", help="Activar búsqueda de hiperparámetros")

    args = parser.parse_args()

    try:
        auto_retrain(force=args.force, model_type=args.model, optimize=args.optimize)
    except Exception as e:
        logger.exception(f"🔥 Error crítico durante auto_retrain: {e}")
