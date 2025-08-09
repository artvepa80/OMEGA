import pandas as pd
import numpy as np
import joblib
import logging
from pathlib import Path
import json
import time
import os
import sys
import requests
import schedule
import subprocess
from datetime import datetime, timedelta
from typing import List, Tuple, Any, Dict, Optional
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import SGDClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
import skops.io as sio
import onnx
import onnxruntime as ort
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import mlflow
import mlflow.sklearn
import telegram
import smtplib
from email.mime.text import MIMEText

# ===================== CONFIGURACIÓN AVANZADA =====================
class Config:
    # Rutas de datos
    DATA_PATH = Path("/mnt/data/DataFrame_completo_de_sorteos.csv")
    HISTORICAL_DATA_DIR = Path("/mnt/data/historical")
    BASE_OUTPUT_DIR = Path("/mnt/data/models")
    
    # Columnas requeridas
    REQUIRED_COLUMNS = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'label']
    
    # Nombres de características
    FEATURE_NAMES = [
        'sum', 'mean', 'std', 'min', 'max', 'range',
        'decade_1', 'decade_2', 'decade_3', 'decade_4',
        'entropy_decades', 'fft_1', 'fft_2', 'fft_3',
        'max_diff', 'mean_diff', 'entropy_diffs'
    ]
    
    # Configuración de modelos
    MODELS = {
        "RandomForest": {
            "class": RandomForestClassifier,
            "params": {
                "n_estimators": 200,
                "max_depth": 12,
                "class_weight": 'balanced_subsample',
                "random_state": 42,
                "n_jobs": -1
            }
        },
        "XGBoost": {
            "class": XGBClassifier,
            "params": {
                "n_estimators": 200,
                "max_depth": 6,
                "learning_rate": 0.1,
                "use_label_encoder": False,
                "eval_metric": 'logloss',
                "random_state": 42,
                "n_jobs": -1
            }
        },
        "LightGBM": {
            "class": LGBMClassifier,
            "params": {
                "n_estimators": 200,
                "max_depth": 6,
                "learning_rate": 0.1,
                "class_weight": 'balanced',
                "random_state": 42,
                "n_jobs": -1
            }
        },
        "HistGradientBoosting": {
            "class": HistGradientBoostingClassifier,
            "params": {
                "max_iter": 200,
                "max_depth": 6,
                "learning_rate": 0.1,
                "random_state": 42
            }
        },
        "SGDClassifier": {
            "class": SGDClassifier,
            "params": {
                "loss": 'log_loss',
                "penalty": 'l2',
                "max_iter": 1000,
                "random_state": 42,
                "n_jobs": -1
            }
        }
    }
    
    # Configuración incremental
    INCREMENTAL_TRAINING = True
    MAX_INCREMENTAL_SAMPLES = 10000
    
    # MLflow
    MLFLOW_TRACKING_URI = "http://mlflow-tracking-server:5000"
    MLFLOW_EXPERIMENT_NAME = "JackpotProfiler"
    
    # Validación cruzada
    CV_FOLDS = 5
    CV_STRATIFIED = True
    
    # Métricas de negocio
    TOP_N = 10  # Para precisión en top-N
    TICKET_PRICE = 1.0  # Precio por boleto
    JACKPOT_PRIZE = 1000000.0  # Premio por ganar el jackpot
    MATCH_5_PRIZE = 10000.0  # Premio por acertar 5 números
    
    # Notificaciones
    SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."  # Webhook para Slack
    TELEGRAM_TOKEN = "your_telegram_bot_token"
    TELEGRAM_CHAT_ID = "your_chat_id"
    EMAIL_CONFIG = {
        "sender": "your_email@example.com",
        "password": "your_email_password",
        "receiver": "receiver@example.com",
        "smtp_server": "smtp.example.com",
        "smtp_port": 587
    }
    
    # Exportación de modelos
    EXPORT_ONNX = True
    EXPORT_SKOPS = True
    
    # Configuración de horario para automatización
    TRAINING_SCHEDULE = "daily"  # daily, weekly, monthly
    
    @classmethod
    def setup_logging(cls, run_timestamp: str):
        """Configura logging avanzado con directorio de salida"""
        cls.OUTPUT_DIR = cls.BASE_OUTPUT_DIR / run_timestamp
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(cls.OUTPUT_DIR / "jackpot_profiler.log"),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

# ===================== FUNCIONES DE NOTIFICACIÓN =====================
def notify(message: str, is_error: bool = False):
    """Envía notificaciones por múltiples canales"""
    title = "❌ Error en Jackpot Profiler" if is_error else "✅ Jackpot Profiler Completado"
    
    # Slack
    if Config.SLACK_WEBHOOK_URL:
        try:
            payload = {
                "text": f"*{title}*\n{message}",
                "username": "Jackpot Profiler",
                "icon_emoji": ":slot_machine:"
            }
            requests.post(Config.SLACK_WEBHOOK_URL, json=payload)
        except Exception as e:
            print(f"Error enviando a Slack: {str(e)}")
    
    # Telegram
    if Config.TELEGRAM_TOKEN and Config.TELEGRAM_CHAT_ID:
        try:
            bot = telegram.Bot(token=Config.TELEGRAM_TOKEN)
            bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=f"{title}\n{message}")
        except Exception as e:
            print(f"Error enviando a Telegram: {str(e)}")
    
    # Email
    if Config.EMAIL_CONFIG["sender"]:
        try:
            msg = MIMEText(message)
            msg['Subject'] = title
            msg['From'] = Config.EMAIL_CONFIG["sender"]
            msg['To'] = Config.EMAIL_CONFIG["receiver"]
            
            with smtplib.SMTP(
                Config.EMAIL_CONFIG["smtp_server"],
                Config.EMAIL_CONFIG["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    Config.EMAIL_CONFIG["sender"],
                    Config.EMAIL_CONFIG["password"]
                )
                server.send_message(msg)
        except Exception as e:
            print(f"Error enviando email: {str(e)}")

# ===================== FUNCIONES DE EVALUACIÓN AVANZADA =====================
def evaluate_business_metrics(model, X_test, y_test, top_n: int = 10) -> dict:
    """
    Evalúa métricas de negocio:
    - Precisión en top-N: % de veces que la combinación real está en las top-N predicciones
    - Ganancia simulada: ROI si jugamos las combinaciones recomendadas
    """
    results = {}
    
    # Precisión en top-N
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X_test)[:, 1]
        top_n_idx = np.argsort(y_proba)[-top_n:]
        top_n_accuracy = np.mean(y_test[top_n_idx])
        results["top_n_accuracy"] = top_n_accuracy
    else:
        results["top_n_accuracy"] = None
    
    # Simulación de ganancia
    if hasattr(model, "predict_proba"):
        # Obtener las top-N predicciones más probables
        all_probas = model.predict_proba(X_test)[:, 1]
        top_idx = np.argsort(all_probas)[-top_n:]
        
        # Calcular costos y ganancias
        total_cost = top_n * Config.TICKET_PRICE
        total_prize = 0
        
        # Contar aciertos
        jackpot_hits = np.sum(y_test[top_idx] == 1)
        # Suponemos que todas las ganancias son jackpot para simplificar
        total_prize = jackpot_hits * Config.JACKPOT_PRIZE
        
        # Calcular ROI
        net_profit = total_prize - total_cost
        roi = net_profit / total_cost if total_cost > 0 else 0
        
        results["simulated_profit"] = {
            "total_cost": total_cost,
            "total_prize": total_prize,
            "net_profit": net_profit,
            "roi": roi,
            "jackpot_hits": jackpot_hits
        }
    else:
        results["simulated_profit"] = None
    
    return results

def cross_validate(model, X, y, n_folds: int = 5, stratified: bool = True) -> dict:
    """Realiza validación cruzada estratificada con métricas completas"""
    cv_metrics = {
        "f1": [],
        "precision": [],
        "recall": [],
        "top_n_accuracy": [],
        "roi": []
    }
    
    if stratified:
        cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    else:
        cv = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    
    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Clonar y entrenar modelo
        fold_model = model.__class__(**model.get_params())
        fold_model.fit(X_train, y_train)
        
        # Métricas estándar
        y_pred = fold_model.predict(X_test)
        cv_metrics["f1"].append(f1_score(y_test, y_pred))
        cv_metrics["precision"].append(precision_score(y_test, y_pred))
        cv_metrics["recall"].append(recall_score(y_test, y_pred))
        
        # Métricas de negocio
        business_metrics = evaluate_business_metrics(fold_model, X_test, y_test, Config.TOP_N)
        if business_metrics["top_n_accuracy"] is not None:
            cv_metrics["top_n_accuracy"].append(business_metrics["top_n_accuracy"])
        if business_metrics["simulated_profit"] is not None:
            cv_metrics["roi"].append(business_metrics["simulated_profit"]["roi"])
    
    # Calcular promedios
    avg_metrics = {k: np.mean(v) if v else None for k, v in cv_metrics.items()}
    return avg_metrics

# ===================== FUNCIONES DE EXPORTACIÓN =====================
def export_model(model, model_name: str, output_dir: Path):
    """Exporta el modelo a múltiples formatos"""
    # Joblib (estándar)
    joblib.dump(model, output_dir / f"{model_name}.joblib")
    
    # SKOPS
    if Config.EXPORT_SKOPS:
        try:
            sio.dump(model, output_dir / f"{model_name}.skops")
        except Exception as e:
            logging.error(f"Error exportando a SKOPS: {str(e)}")
    
    # ONNX
    if Config.EXPORT_ONNX:
        try:
            # Convertir a ONNX
            initial_type = [('float_input', FloatTensorType([None, len(Config.FEATURE_NAMES)]))]
            onnx_model = convert_sklearn(model, initial_types=initial_type)
            
            # Guardar modelo
            onnx_path = output_dir / f"{model_name}.onnx"
            with open(onnx_path, "wb") as f:
                f.write(onnx_model.SerializeToString())
            
            # Verificar que se puede cargar
            ort.InferenceSession(onnx_path)
        except Exception as e:
            logging.error(f"Error exportando a ONNX: {str(e)}")

# ===================== FUNCIONES PRINCIPALES =====================
def load_data(file_path: Path, incremental: bool = False) -> pd.DataFrame:
    """Carga datos con soporte incremental y verificación mejorada"""
    try:
        if incremental:
            dfs = []
            historical_files = sorted(Config.HISTORICAL_DATA_DIR.glob("*.csv"))
            if not historical_files:
                logging.warning("No hay datos históricos. Cargando datos completos.")
                return pd.read_csv(file_path)
                
            # Cargar solo los archivos más recientes
            for path in historical_files[-Config.MAX_INCREMENTAL_SAMPLES:]:
                dfs.append(pd.read_csv(path))
            df = pd.concat(dfs, ignore_index=True)
        else:
            df = pd.read_csv(file_path)
        
        # Validación de datos
        missing_cols = [col for col in Config.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Columnas faltantes: {missing_cols}")
            
        if df[Config.REQUIRED_COLUMNS[:-1]].isnull().any().any():
            raise ValueError("Valores nulos detectados en los números")
            
        # Crear columna de combinación
        df['combinacion'] = df[Config.REQUIRED_COLUMNS[:-1]].values.tolist()
        return df
    
    except Exception as e:
        logging.exception("Error en carga de datos")
        raise

def calculate_entropy(values: np.ndarray) -> float:
    """Calcula entropía con estabilidad numérica mejorada"""
    unique, counts = np.unique(values, return_counts=True)
    probabilities = counts / counts.sum()
    return -np.sum(probabilities * np.log2(probabilities + 1e-10))

def extraer_features(combinaciones: List[List[int]]) -> np.ndarray:
    """Extrae características optimizadas para loterías"""
    features = []
    for combo in combinaciones:
        arr = np.array(combo)
        sorted_arr = np.sort(arr)
        
        # Estadísticas básicas
        stats = [
            np.sum(arr),
            np.mean(arr),
            np.std(arr),
            np.min(arr),
            np.max(arr),
            np.ptp(arr)
        ]
        
        # Análisis por décadas con entropía
        decade_bins = (arr - 1) // 10
        decades = [np.sum(decade_bins == i) for i in range(4)]
        entropy_decades = calculate_entropy(decade_bins)
        
        # Análisis espectral sobre valores ordenados
        normalized = sorted_arr - np.mean(sorted_arr)
        fft = np.abs(np.fft.rfft(normalized)[:3])
        
        # Análisis de diferencias con entropía
        diffs = np.diff(sorted_arr)
        diff_features = [
            np.max(diffs),
            np.mean(diffs),
            calculate_entropy(diffs)
        ]
        
        features.append(stats + decades + [entropy_decades] + fft.tolist() + diff_features)
    
    return np.array(features)

def train_and_evaluate(X: np.ndarray, y: np.ndarray, incremental_model: Any = None) -> Dict[str, Any]:
    """Entrena y evalúa múltiples modelos con validación cruzada y MLflow"""
    # Dividir en train y test (estratificado)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        stratify=y, 
        test_size=0.2, 
        random_state=42
    )
    
    results = {}
    best_score = -1
    best_model = None
    best_model_name = ""
    
    # Configurar MLflow
    mlflow.set_tracking_uri(Config.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(Config.MLFLOW_EXPERIMENT_NAME)
    
    with mlflow.start_run():
        mlflow.log_param("data_samples", len(X))
        mlflow.log_param("test_size", 0.2)
        mlflow.log_param("cv_folds", Config.CV_FOLDS)
        
        for model_name, model_config in Config.MODELS.items():
            with mlflow.start_run(nested=True, run_name=model_name):
                logging.info(f"Entrenando {model_name}...")
                
                # Crear instancia del modelo
                model = model_config["class"](**model_config["params"])
                
                # Pipeline con escalado
                pipeline = Pipeline([
                    ("scaler", StandardScaler()),
                    ("clf", model)
                ])
                
                # Entrenamiento incremental si está disponible
                if incremental_model and model_name == incremental_model["name"]:
                    logging.info(f"Realizando entrenamiento incremental para {model_name}")
                    pipeline.named_steps['scaler'] = incremental_model["scaler"]
                    pipeline.named_steps['clf'] = incremental_model["classifier"]
                    
                    # Entrenamiento parcial
                    if hasattr(pipeline.named_steps['clf'], 'partial_fit'):
                        pipeline.named_steps['clf'].partial_fit(
                            X_train, y_train, 
                            classes=np.unique(y)
                        )
                    else:
                        logging.warning("Modelo no soporta incremental learning. Entrenando desde cero.")
                        pipeline.fit(X_train, y_train)
                else:
                    pipeline.fit(X_train, y_train)
                
                # Validación cruzada para evaluación robusta
                cv_metrics = cross_validate(
                    pipeline, 
                    X_train, 
                    y_train,
                    n_folds=Config.CV_FOLDS,
                    stratified=Config.CV_STRATIFIED
                )
                
                # Evaluación en test
                y_pred = pipeline.predict(X_test)
                test_f1 = f1_score(y_test, y_pred)
                test_precision = precision_score(y_test, y_pred)
                test_recall = recall_score(y_test, y_pred)
                
                # Métricas de negocio
                business_metrics = evaluate_business_metrics(pipeline, X_test, y_test, Config.TOP_N)
                
                # Registro en MLflow
                mlflow.log_params(model_config["params"])
                mlflow.log_metric("test_f1", test_f1)
                mlflow.log_metric("test_precision", test_precision)
                mlflow.log_metric("test_recall", test_recall)
                
                if cv_metrics["f1"] is not None:
                    mlflow.log_metric("cv_f1", cv_metrics["f1"])
                if cv_metrics["top_n_accuracy"] is not None:
                    mlflow.log_metric("cv_top_n_accuracy", cv_metrics["top_n_accuracy"])
                if cv_metrics["roi"] is not None:
                    mlflow.log_metric("cv_roi", cv_metrics["roi"])
                
                mlflow.sklearn.log_model(pipeline, model_name)
                
                # Guardar resultados
                results[model_name] = {
                    "model": pipeline,
                    "cv_metrics": cv_metrics,
                    "test_metrics": {
                        "f1": test_f1,
                        "precision": test_precision,
                        "recall": test_recall
                    },
                    "business_metrics": business_metrics
                }
                
                # Exportar modelo
                export_model(pipeline, model_name, Config.OUTPUT_DIR)
                
                # Actualizar mejor modelo (basado en F1 de test)
                if test_f1 > best_score:
                    best_score = test_f1
                    best_model = pipeline
                    best_model_name = model_name
                
                logging.info(f"{model_name} - Test F1: {test_f1:.4f}, CV F1: {cv_metrics['f1']:.4f}")
        
        # Registrar mejor modelo
        mlflow.log_param("best_model", best_model_name)
        mlflow.log_metric("best_f1", best_score)
        mlflow.sklearn.log_model(best_model, "best_model")
        export_model(best_model, "best_model", Config.OUTPUT_DIR)
        
        # Guardar estado para entrenamiento incremental
        incremental_data = {
            "name": best_model_name,
            "scaler": best_model.named_steps['scaler'],
            "classifier": best_model.named_steps['clf']
        }
        joblib.dump(incremental_data, Config.OUTPUT_DIR / "incremental_state.pkl")
    
    return {
        "all_results": results,
        "best_model": best_model,
        "best_model_name": best_model_name
    }

# ===================== AUTOMATIZACIÓN =====================
def run_training():
    """Función principal para ejecutar el entrenamiento"""
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = Config.setup_logging(run_timestamp)
    start_time = time.time()
    success = False
    
    try:
        logger.info("=== INICIO JACKPOT PROFILER ===")
        logger.info(f"Versión: {run_timestamp}")
        
        # Carga de datos
        incremental_state = None
        if Config.INCREMENTAL_TRAINING:
            # Buscar el último modelo entrenado
            model_dirs = sorted(Config.BASE_OUTPUT_DIR.glob("*"), reverse=True)
            if model_dirs:
                last_model_dir = model_dirs[0]
                incremental_state_path = last_model_dir / "incremental_state.pkl"
                if incremental_state_path.exists():
                    incremental_state = joblib.load(incremental_state_path)
                    logger.info(f"Entrenamiento incremental con estado de {incremental_state['name']}")
        
        df = load_data(Config.DATA_PATH, incremental=Config.INCREMENTAL_TRAINING)
        logger.info(f"Datos cargados: {len(df)} registros")
        
        # Extracción de características
        X = extraer_features(df['combinacion'])
        y = df['label'].astype(int)
        logger.info(f"Matriz de características: {X.shape}")
        
        # Entrenamiento y evaluación
        results = train_and_evaluate(X, y, incremental_state)
        
        # Reporte final
        best = results['all_results'][results['best_model_name']]
        best_f1 = best["test_metrics"]["f1"]
        best_roi = best["business_metrics"].get("simulated_profit", {}).get("roi", 0)
        
        logger.info(f"Mejor modelo: {results['best_model_name']} | F1: {best_f1:.4f} | ROI: {best_roi:.2%}")
        logger.info(f"Proceso completado en {time.time()-start_time:.2f} segundos")
        
        # Mensaje de éxito
        success = True
        message = (
            f"✅ Entrenamiento completado exitosamente!\n"
            f"- Mejor modelo: {results['best_model_name']}\n"
            f"- Test F1: {best_f1:.4f}\n"
            f"- ROI simulado: {best_roi:.2%}\n"
            f"- Duración: {time.time()-start_time:.2f} segundos"
        )
        return message, True
        
    except Exception as e:
        logger.exception("Error crítico en el flujo principal")
        error_message = f"❌ Error en entrenamiento:\n{str(e)}\n\nVer logs para más detalles"
        return error_message, False

def schedule_training():
    """Programa la ejecución automática según la configuración"""
    if Config.TRAINING_SCHEDULE == "daily":
        schedule.every().day.at("02:00").do(execute_training)
    elif Config.TRAINING_SCHEDULE == "weekly":
        schedule.every().monday.at("03:00").do(execute_training)
    elif Config.TRAINING_SCHEDULE == "monthly":
        # Ejecutar el primer día de cada mes
        def first_of_month():
            return datetime.now().day == 1
            
        schedule.every().day.at("04:00").do(execute_training).tag("monthly").when(first_of_month)
    
    logging.info(f"Programado entrenamiento {Config.TRAINING_SCHEDULE}")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def execute_training():
    """Ejecuta el entrenamiento y maneja notificaciones"""
    message, success = run_training()
    notify(message, is_error=not success)
    
    # Para ejecuciones programadas, mantener el proceso activo
    if Config.TRAINING_SCHEDULE:
        logging.info("Esperando próxima ejecución programada...")

# ===================== PUNTO DE ENTRADA =====================
if __name__ == "__main__":
    # Modo de ejecución
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        # Ejecución programada (para usar con cron/systemd)
        logging.basicConfig(level=logging.INFO)
        schedule_training()
    else:
        # Ejecución única
        message, success = run_training()
        notify(message, is_error=not success)
        
        # Salir con código apropiado para CI/CD
        sys.exit(0 if success else 1)