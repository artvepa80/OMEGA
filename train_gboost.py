import pandas as pd
import numpy as np
import os
import argparse
import logging
import pickle
import subprocess
import sys
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, RocCurveDisplay
from imblearn.over_sampling import SMOTE
from modules.learning.gboost_jackpot_classifier import GBoostJackpotClassifier

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("training.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_data(data_path: str, labels_path: str = None) -> pd.DataFrame:
    logger.info(f"📂 Cargando datos históricos desde {data_path}...")
    df = pd.read_csv(data_path)
    logger.info(f"✅ Datos crudos cargados: {df.shape[0]} filas, {df.shape[1]} columnas")

    rename_map = {}
    for i in range(1, 7):
        for pattern in [f"Bolilla {i}", f"Numero {i}", f"n{i}", f"number{i}", f"ball{i}"]:
            if pattern in df.columns:
                rename_map[pattern] = f"n{i}"
                break
    if rename_map:
        df = df.rename(columns=rename_map)
        logger.info(f"🔄 Columnas renombradas: {rename_map}")

    if labels_path:
        labels_df = pd.read_csv(labels_path)
        if 'label' not in labels_df.columns and 'ganado' in labels_df.columns:
            labels_df = labels_df.rename(columns={'ganado': 'label'})
        df = df.merge(labels_df[['fecha', 'label']], on='fecha', how='left')

    # Validación de estructura
    required_columns = {'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'fecha'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        logger.error(f"🚨 Columnas obligatorias faltantes: {missing}")
        raise ValueError("Estructura de datos inválida")
    
    df['_data_version'] = os.path.basename(data_path)  # Trackeo de versión
    return df

def main():
    parser = argparse.ArgumentParser(description='Entrenar modelo Gradient Boosting para predecir jackpots.')
    parser.add_argument('--data_path', type=str, required=True)
    parser.add_argument('--labels_path', type=str, default=None)
    parser.add_argument('--model_path', type=str, default='models/gboost_model.pkl')
    parser.add_argument('--report_dir', type=str, default='reports/')
    parser.add_argument('--test_size', type=float, default=0.2)
    parser.add_argument('--random_state', type=int, default=42)
    parser.add_argument('--min_auc', type=float, default=0.7, help='Umbral mínimo de AUC para guardar modelo')
    parser.add_argument('--save_low_auc', action='store_true', help='Guardar modelo incluso con AUC bajo')
    args = parser.parse_args()

    # Asegurar directorios
    os.makedirs(os.path.dirname(args.model_path), exist_ok=True)
    os.makedirs(args.report_dir, exist_ok=True)
    low_auc_dir = os.path.join(os.path.dirname(args.model_path), 'low_auc_models')
    os.makedirs(low_auc_dir, exist_ok=True)

    logger.info("🚀 Iniciando entrenamiento con parámetros:")
    logger.info(vars(args))

    df = load_data(args.data_path, args.labels_path)
    df = df.dropna(subset=['label'])
    df['label'] = df['label'].astype(int)

    logger.info("📊 Distribución de clases original:")
    logger.info(df['label'].value_counts(normalize=True))

    # Validación de features
    features = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6'] 
    if not set(features).issubset(df.columns):
        missing = set(features) - set(df.columns)
        logger.error(f"🚨 Features numéricas faltantes: {missing}")
        raise ValueError("Features requeridas no disponibles")
    
    X = df[features].values.tolist()
    y = df['label'].tolist()

    # Convertir a array para compatibilidad con SMOTE
    try:
        smote = SMOTE(random_state=args.random_state)
        X_resampled, y_resampled = smote.fit_resample(X, y)
    except TypeError:
        logger.warning("⚠️ SMOTE no aceptó listas. Convirtiendo a arrays...")
        X = np.array(X)
        smote = SMOTE(random_state=args.random_state)
        X_resampled, y_resampled = smote.fit_resample(X, y)
    
    logger.info(f"↔️ Nuevo tamaño del dataset: {len(X_resampled)} muestras")
    logger.info(f"📊 Distribución después de SMOTE: {pd.Series(y_resampled).value_counts()}")

    # Validación cruzada estratificada
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=args.random_state)
    fold_results = []
    
    for fold, (train_idx, test_idx) in enumerate(skf.split(X_resampled, y_resampled)):
        logger.info(f"=== FOLD {fold+1}/5 ===")
        X_train = [X_resampled[i] for i in train_idx]
        X_test = [X_resampled[i] for i in test_idx]
        y_train = [y_resampled[i] for i in train_idx]
        y_test = [y_resampled[i] for i in test_idx]

        # CORRECCIÓN: Remover early_stopping_rounds
        clf = GBoostJackpotClassifier(
            model_path=args.model_path,
            eval_metric='auc'
        )
        clf.fit(X_train, y_train)
        
        # Evaluación
        y_pred = clf.predict(X_test)
        y_proba = clf.predict_proba(X_test)[:, 1]
        roc_auc = roc_auc_score(y_test, y_proba)
        report = classification_report(y_test, y_pred, output_dict=True)
        cm = confusion_matrix(y_test, y_pred)
        
        fold_results.append({
            'fold': fold+1,
            'roc_auc': roc_auc,
            'accuracy': report['accuracy'],
            'precision_0': report['0']['precision'],
            'recall_0': report['0']['recall'],
            'f1_0': report['0']['f1-score'],
            'precision_1': report['1']['precision'],
            'recall_1': report['1']['recall'],
            'f1_1': report['1']['f1-score'],
        })
        
        logger.info(f"📊 Fold {fold+1} - AUC: {roc_auc:.4f}, Accuracy: {report['accuracy']:.4f}")

    # Consolidar resultados
    fold_results_df = pd.DataFrame(fold_results)
    mean_auc = fold_results_df['roc_auc'].mean()
    logger.info(f"📊 AUC promedio: {mean_auc:.4f}")
    
    # Guardar resultados por fold
    fold_results_df.to_csv(os.path.join(args.report_dir, "fold_metrics.csv"), index=False)
    logger.info(f"💾 Métricas por fold guardadas en {args.report_dir}/fold_metrics.csv")

    # Obtener commit de Git con robustez
    try:
        git_commit = subprocess.getoutput('git rev-parse HEAD')
    except Exception as e:
        logger.warning(f"⚠️ No se pudo obtener commit de Git: {str(e)}")
        git_commit = "N/A"

    # Entrenar modelo final
    logger.info("🏁 Entrenando modelo final con todos los datos...")
    
    # CORRECCIÓN: Remover early_stopping_rounds
    final_clf = GBoostJackpotClassifier(
        model_path=args.model_path,
        eval_metric='auc'
    )
    final_clf.fit(X_resampled, y_resampled)
    
    # Evaluación final
    _, X_eval, _, y_eval = train_test_split(
        X_resampled, 
        y_resampled, 
        test_size=0.2, 
        stratify=y_resampled,
        random_state=args.random_state
    )
    y_proba = final_clf.predict_proba(X_eval)[:, 1]
    final_auc = roc_auc_score(y_eval, y_proba)
    
    # Preparar metadatos
    final_clf.metadata = {
        'trained_date': datetime.now().isoformat(),
        'git_commit': git_commit,
        'cv_auc': mean_auc,
        'final_auc': final_auc,
        'data_version': df['_data_version'].iloc[0],
        'model_status': 'ACCEPTED' if mean_auc >= args.min_auc else 'LOW_AUC'
    }

    # Guardar modelo según calidad
    if mean_auc >= args.min_auc:
        save_path = args.model_path
        logger.info(f"💾 Modelo guardado en {save_path} (AUC={mean_auc:.4f})")
    elif args.save_low_auc:
        model_name = f"gboost_model_auc_{mean_auc:.4f}.pkl"
        save_path = os.path.join(low_auc_dir, model_name)
        logger.warning(f"⚠️ Guardando modelo con AUC bajo en {save_path}")
    else:
        logger.warning(f"❌ Modelo descartado. AUC promedio {mean_auc:.4f} < {args.min_auc}")
        save_path = None
    
    if save_path:
        final_clf.model_path = save_path
        final_clf.save()
        
        # Reporte final
        report_path = os.path.join(args.report_dir, "final_report.txt")
        with open(report_path, "w") as f:
            f.write(f"Modelo entrenado: {datetime.now()}\n")
            f.write(f"Git Commit: {git_commit}\n")
            f.write(f"Data Version: {final_clf.metadata['data_version']}\n")
            f.write(f"AUC Promedio (CV): {mean_auc:.4f}\n")
            f.write(f"AUC Final (Holdout): {final_auc:.4f}\n\n")
            f.write("Resultados por Fold:\n")
            f.write(fold_results_df.to_string(index=False))
            
        # Curva ROC
        roc_path = os.path.join(args.report_dir, 'roc_curve.png')
        RocCurveDisplay.from_predictions(
            y_eval, 
            y_proba, 
            name=f'Modelo (AUC={final_auc:.4f})'
        )
        plt.savefig(roc_path)
        logger.info(f"📈 Curva ROC guardada en {roc_path}")
        
        # Importancia de características (Ordenado)
        importances = final_clf.model.feature_importances_
        feature_names = final_clf._extract_features(pd.Series(X_resampled[:100])).columns
        
        sorted_idx = np.argsort(importances)
        sorted_importances = importances[sorted_idx]
        sorted_features = feature_names[sorted_idx]
        
        imp_path = os.path.join(args.report_dir, 'feature_importance.png')
        plt.figure(figsize=(12, 6))
        plt.barh(sorted_features, sorted_importances)
        plt.xlabel("Importancia")
        plt.title("Importancia de características (Ordenado)")
        plt.tight_layout()
        plt.savefig(imp_path)
        logger.info(f"📊 Importancia de características guardada en {imp_path}")
    else:
        logger.warning("❌ Modelo no guardado. Use --save_low_auc para guardar modelos con AUC bajo")

if __name__ == "__main__":
    main()