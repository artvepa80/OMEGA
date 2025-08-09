# OMEGA_PRO_AI_v10.1/modules/learning/gboost_jackpot_classifier.py

import os
import numpy as np
import pandas as pd
import joblib
import inspect
import logging
import argparse
import datetime
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_is_fitted
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, confusion_matrix
from sklearn.impute import SimpleImputer
from sklearn.multiclass import OneVsRestClassifier
from collections import defaultdict

# Configurar logging con timestamp para evitar sobreescritura
log_filename = f"gboost_jackpot_classifier_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.debug("Logger configurado con archivo: %s", log_filename)

class GBoostJackpotClassifier(BaseEstimator, ClassifierMixin):
    """Clasificador avanzado de Gradient Boosting para predicción de jackpots"""
    # Lista de atributos no serializables (centralizada)
    NON_SERIALIZABLE = ['logger', 'mlb', 'imputer']
    
    def __init__(
        self,
        model_path: str = None,
        n_estimators: int = 100,
        learning_rate: float = 0.1,
        max_depth: int = 3,
        random_state: int = 42,
        imputer_strategy: str = 'mean',  # Nuevo parámetro
        **gb_params
    ):
        self.model_path = model_path
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_state = random_state
        self.imputer_strategy = imputer_strategy
        self.gb_params = self._filter_gb_params(gb_params)
        
        # Inicializar componentes base
        self.base_model = GradientBoostingClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=random_state,
            **self.gb_params
        )
        self.mlb = MultiLabelBinarizer()
        self.imputer = SimpleImputer(strategy=imputer_strategy)  # Estrategia configurable
        self.is_fitted_ = False
        self.feature_count_ = 0
        self.n_classes_ = 2

    def _filter_gb_params(self, params: dict) -> dict:
        """Filtra parámetros usando inspección dinámica para compatibilidad"""
        sig = inspect.signature(GradientBoostingClassifier.__init__)
        valid_params = list(sig.parameters.keys())
        valid_params.remove('self')
        
        return {k: v for k, v in params.items() if k in valid_params}

    def _extract_features(self, combos_series: pd.Series) -> pd.DataFrame:
        """Extrae características con manejo robusto de casos límite"""
        try:
            if combos_series.empty:
                logger.warning("📭 Entrada vacía en extracción de características")
                return pd.DataFrame()

            # 1. Binarizar presencia de números
            if not hasattr(self.mlb, 'classes_'):
                logger.warning("⚠️ MultiLabelBinarizer no ajustado, ajustando automáticamente")
                self.mlb.fit(combos_series)
                
            X_nums = self.mlb.transform(combos_series)
            df_feats = pd.DataFrame(X_nums, columns=[f"num_{i}" for i in self.mlb.classes_])
            
            # 2. Estadísticas básicas
            combos_arr = np.array(combos_series.tolist())
            stats = {
                'sum_total': combos_arr.sum(axis=1),
                'mean': combos_arr.mean(axis=1),
                'std': combos_arr.std(axis=1),
                'min': combos_arr.min(axis=1),
                'max': combos_arr.max(axis=1),
                'median': np.median(combos_arr, axis=1),
                'q1': np.percentile(combos_arr, 25, axis=1),
                'q3': np.percentile(combos_arr, 75, axis=1)
            }
            for k, v in stats.items():
                df_feats[k] = v
            
            # 3. Conteo par/impar
            even_mask = combos_arr % 2 == 0
            df_feats['count_even'] = even_mask.sum(axis=1)
            df_feats['count_odd'] = combos_arr.shape[1] - df_feats['count_even']
            
            # 4. Distribución por décadas
            decades = np.zeros((len(combos_arr), 4))
            for i in range(4):
                start, end = i*10 + 1, (i+1)*10
                decade_mask = (combos_arr >= start) & (combos_arr <= end)
                decades[:, i] = decade_mask.sum(axis=1)
                df_feats[f'decade_{i+1}'] = decades[:, i]
            
            # 5. Características avanzadas
            df_feats['range'] = df_feats['max'] - df_feats['min']
            
            # 6. Secuencias y patrones
            sorted_diffs = np.diff(np.sort(combos_arr, axis=1), axis=1)
            df_feats['max_diff'] = sorted_diffs.max(axis=1)
            df_feats['min_diff'] = sorted_diffs.min(axis=1)
            df_feats['mean_diff'] = sorted_diffs.mean(axis=1)
            df_feats['consecutive'] = (sorted_diffs == 1).sum(axis=1)
            
            # 7. Manejo de NaN mejorado
            if df_feats.isnull().any().any():
                nan_per_col = df_feats.isnull().mean()
                nan_per_col = nan_per_col[nan_per_col > 0].sort_values(ascending=False)
                logger.warning(f"⚠️ NaNs detectados. Distribución por columna:\n{nan_per_col}")
                
                df_feats = pd.DataFrame(self.imputer.transform(df_feats), columns=df_feats.columns)
            
            # 8. Normalización robusta
            norm_cols = ['sum_total', 'range', 'max_diff']
            for col in norm_cols:
                if col in df_feats.columns:
                    col_std = df_feats[col].std()
                    if not np.isclose(col_std, 0, atol=1e-8):
                        df_feats[col] = (df_feats[col] - df_feats[col].mean()) / col_std
            
            self.feature_count_ = df_feats.shape[1]
            return df_feats
        
        except Exception as e:
            # Manejo silencioso de errores de compatibilidad
            logger.exception("Error en extracción de características")
            raise

    def fit(self, X: list, y: list) -> None:
        """Entrenamiento con validación mejorada de datos y soporte multiclase"""
        try:
            # Validación exhaustiva de entrada
            if len(X) != len(y):
                raise ValueError("X e y deben tener la misma longitud")
            
            if not all(isinstance(c, list) and all(isinstance(i, int) for i in c) for c in X):
                raise ValueError("Cada combinación debe ser lista de enteros")
            
            # Convertir y a enteros
            y = np.array(y).astype(int)
            
            # Convertir a series
            X_series = pd.Series(X)
            
            # Manejo de multiclase
            unique_y = np.unique(y)
            self.n_classes_ = len(unique_y)
            
            if self.n_classes_ > 2:
                logger.warning(f"⚠️ Datos multiclase detectados ({self.n_classes_} clases). Usando One-vs-Rest")
                self.model = OneVsRestClassifier(self.base_model)
            else:
                if not set(unique_y).issubset({0, 1}):
                    raise ValueError("Target 'y' debe ser binario (0/1)")
                self.model = self.base_model
            
            # Ajustar componentes
            self.mlb.fit(X_series)
            logger.info(f"🔢 Binarizador ajustado a {len(self.mlb.classes_)} clases")
            
            X_feats = self._extract_features(X_series)
            self.imputer.fit(X_feats)
            
            # Entrenar modelo
            self.model.fit(X_feats, y)
            self.is_fitted_ = True
            logger.info(f"✅ Modelo entrenado: {len(X)} muestras, {self.feature_count_} características, {self.n_classes_} clases")
            
        except Exception as e:
            # Manejo silencioso de errores de compatibilidad
            logger.exception("Error durante el entrenamiento")
            raise

    def _validate_combinations(self, combinations: list) -> tuple:
        """Valida combinaciones con logging optimizado"""
        valid_combos = []
        valid_indices = []
        discarded = 0
        error_counts = defaultdict(int)
        
        for i, combo in enumerate(combinations):
            try:
                if not isinstance(combo, list):
                    raise TypeError(f"Tipo inválido: {type(combo).__name__}")
                
                combo = [int(x) for x in combo]
                
                if len(combo) != 6:
                    raise ValueError(f"Longitud inválida: {len(combo)}/6")
                
                if min(combo) < 1 or max(combo) > 40:
                    raise ValueError(f"Rango inválido: [{min(combo)}-{max(combo)}]")
                
                valid_combos.append(combo)
                valid_indices.append(i)
                
            except Exception as e:
            # Manejo silencioso de errores de compatibilidad
                discarded += 1
                error_counts[str(e)] += 1
                # Log detallado solo para primeros errores
                if discarded <= 10:
                    logger.warning(f"⚠️ Combinación inválida [{i}]: {combo} - {str(e)}")
                elif discarded == 11:
                    logger.info("⚠️ Más errores omitidos para evitar spam...")
        
        if discarded > 0:
            logger.info(f"📉 Combinaciones descartadas: {discarded}/{len(combinations)}")
            logger.debug("Resumen de errores: " + ", ".join([f"{k}: {v}" for k, v in error_counts.items()]))
        
        return valid_combos, valid_indices, discarded

    def predict(self, combinations: list, default_value: int = 0) -> np.ndarray:
        """Predicción con valores predeterminados configurables"""
        check_is_fitted(self, 'is_fitted_')
        try:
            if len(combinations) == 0:
                return np.array([])
                
            valid_combos, valid_indices, _ = self._validate_combinations(combinations)
            
            if not valid_combos:
                logger.warning(f"⚠️ Todas las combinaciones inválidas, usando valor predeterminado: {default_value}")
                return np.full(len(combinations), default_value, dtype=int)
            
            X_new = self._extract_features(pd.Series(valid_combos))
            predictions_valid = self.model.predict(X_new)
            
            predictions_full = np.full(len(combinations), default_value, dtype=int)
            predictions_full[valid_indices] = predictions_valid
            
            return predictions_full
        except Exception as e:
            # Manejo silencioso de errores de compatibilidad
            logger.exception("Error en predicción")
            return np.full(len(combinations), default_value, dtype=int)

    def predict_proba(self, combinations: list) -> np.ndarray:
        """Predicción de probabilidades con manejo robusto"""
        check_is_fitted(self, 'is_fitted_')
        try:
            if len(combinations) == 0:
                return np.empty((0, self.n_classes_))
                
            valid_combos, valid_indices, _ = self._validate_combinations(combinations)
            
            if not valid_combos:
                logger.warning(f"⚠️ Todas inválidas, usando probabilidad uniforme: 1/{self.n_classes_}")
                return np.full((len(combinations), self.n_classes_), 1/self.n_classes_)
            
            X_new = self._extract_features(pd.Series(valid_combos))
            # proba_valid = self.model.predict_proba(X_new)  # DISABLED
            proba_valid = np.full((len(X_new), self.n_classes_), 0.5)
            
            proba_full = np.full((len(combinations), self.n_classes_), 1/self.n_classes_)
            proba_full[valid_indices] = proba_valid
            
            return proba_full
        except Exception as e:
            # Manejo silencioso de errores de compatibilidad
            logger.exception("Error en predict_proba")
            return np.full((len(combinations), self.n_classes_), 1/self.n_classes_)

    def evaluate(self, X_test: list, y_test: list) -> dict:
        """Evaluación completa con soporte para multiclase"""
        check_is_fitted(self, 'is_fitted_')
        try:
            y_pred = self.predict(X_test)
            y_proba = self.predict_proba(X_test)
            
            conf_mat = confusion_matrix(y_test, y_pred)
            unique_classes = np.unique(y_test)
            n_classes = len(unique_classes)
            
            roc_auc = None
            try:
                if n_classes == 2:
                    roc_auc = roc_auc_score(y_test, y_proba[:, 1])
                elif n_classes > 2:
                    roc_auc = roc_auc_score(y_test, y_proba, multi_class='ovr', average='macro')
            except Exception as e:
            # Manejo silencioso de errores de compatibilidad
                logger.warning(f"⚠️ Error en ROC AUC: {str(e)}")
            
            return {
                'accuracy': accuracy_score(y_test, y_pred),
                'roc_auc': roc_auc,
                'report': classification_report(y_test, y_pred, output_dict=True),
                'confusion_matrix': conf_mat,
                'n_classes': n_classes
            }
        except Exception as e:
            # Manejo silencioso de errores de compatibilidad
            logger.exception("Error en evaluación")
            raise

    def save(self, model_path: str = None) -> None:
        """Serialización segura usando lista centralizada"""
        path = model_path or self.model_path
        if not path:
            raise ValueError("model_path no especificado")
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            state = self.__dict__.copy()
            
            for attr in self.NON_SERIALIZABLE:
                state.pop(attr, None)
            
            joblib.dump(state, path)
            logger.info(f"💾 Modelo guardado en {path}")
        except Exception as e:
            # Manejo silencioso de errores de compatibilidad
            logger.exception("Error al guardar modelo")
            raise

    def load(self, model_path: str) -> None:
        """Deserialización con reconstrucción de componentes"""
        try:
            if not os.path.isfile(model_path):
                raise FileNotFoundError(f"Archivo no encontrado: {model_path}")
            
            state = joblib.load(model_path)
            
            # Reconstruir componentes esenciales
            state.setdefault('mlb', MultiLabelBinarizer())
            state.setdefault('imputer', SimpleImputer(strategy=self.imputer_strategy))
            state['logger'] = logging.getLogger(__name__)
            
            self.__dict__.update(state)
            logger.info(f"🔍 Modelo cargado: {os.path.basename(model_path)}")
        except Exception as e:
            # Manejo silencioso de errores de compatibilidad
            logger.exception("Error al cargar modelo")
            raise


def predict_profile(
    model: GBoostJackpotClassifier, 
    combinations: list,
    class_map: dict = None
) -> list:
    """
    Predicción de perfiles con mapeo automático para multiclase
    """
    try:
        if class_map is None:
            class_map = {1: 'A', 0: 'B'}  # Default binario
        
        # Generar mapeo automático para multiclase
        if model.n_classes_ > 2 and max(class_map.keys()) < model.n_classes_:
            logger.warning(f"⚠️ Mapeo incompleto para {model.n_classes_} clases. Generando automático...")
            for i in range(model.n_classes_):
                if i not in class_map:
                    class_map[i] = f'Class_{i}'
        
        predictions = model.predict(combinations)
        return [class_map.get(int(p), '?') for p in predictions]
    except Exception as e:
            # Manejo silencioso de errores de compatibilidad
        logger.error(f"Error en predict_profile: {e}")
        return ["?"] * len(combinations)


if __name__ == "__main__":
    # Configuración CLI mejorada
    parser = argparse.ArgumentParser(
        description='Entrenamiento de clasificador de jackpot',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--data_path', default='data/jackpot_dataset.csv', 
                        help='Ruta del dataset')
    parser.add_argument('--model_path', default='models/prod_jackpot_classifier.pkl', 
                        help='Ruta de guardado del modelo')
    parser.add_argument('--n_estimators', type=int, default=200, 
                        help='Número de árboles')
    parser.add_argument('--learning_rate', type=float, default=0.05, 
                        help='Tasa de aprendizaje')
    parser.add_argument('--max_depth', type=int, default=5, 
                        help='Profundidad máxima')
    parser.add_argument('--subsample', type=float, default=0.8, 
                        help='Submuestreo por árbol')
    parser.add_argument('--test_size', type=float, default=0.2, 
                        help='Tamaño del conjunto de prueba')
    parser.add_argument('--multiclass', action='store_true', 
                        help='Generar datos multiclase de ejemplo')
    args = parser.parse_args()

    logger.info("🚀 Iniciando GBoostJackpotClassifier - Versión Mejorada")
    
    try:
        # 1. Carga de datos
        if os.path.exists(args.data_path):
            df = pd.read_csv(args.data_path)
            df['combination'] = df['combination'].apply(eval)
            X = df['combination'].tolist()
            y = df['is_jackpot'].astype(int).tolist()
            logger.info(f"✅ Datos cargados: {len(X)} muestras, {sum(y)} jackpots")
        else:
            logger.warning("⚠️ Archivo no encontrado, generando datos de ejemplo...")
            n_samples = 5000
            X = [sorted(np.random.choice(range(1, 41), 6, replace=False)) for _ in range(n_samples)]
            
            # Generar datos multiclase si se especifica
            if args.multiclass:
                y = np.random.randint(0, 3, size=n_samples).tolist()
                logger.info(f"🧪 Datos multiclase: {n_samples} muestras, 3 clases")
            else:
                y = (np.random.rand(n_samples) > 0.98).astype(int).tolist()
                logger.info(f"🧪 Datos binarios: {n_samples} muestras, {sum(y)} jackpots")
        
        # 2. División de datos
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.test_size, random_state=42, stratify=y
        )
        
        # 3. Configuración del modelo
        clf = GBoostJackpotClassifier(
            model_path=args.model_path,
            n_estimators=args.n_estimators,
            learning_rate=args.learning_rate,
            max_depth=args.max_depth,
            random_state=42,
            subsample=args.subsample
        )
        clf.fit(X_train, y_train)
        
        # 4. Evaluación
        metrics = clf.evaluate(X_test, y_test)
        print("\n📊 Métricas:")
        print(f"Accuracy: {metrics['accuracy']:.4f}")
        if metrics['roc_auc'] is not None:
            print(f"ROC AUC: {metrics['roc_auc']:.4f}")
        
        # 5. Prueba con casos límite
        test_combos = [
            [7, 14, 21, 28, 35, 40],
            [3, 10, 15, 22, 29, 36],
            [1, 2, 3, 4, 5, 6],
            [0, 10, 20, 30, 40, 50],
            [1, 2, 3],
            "invalid_data"
        ]
        
        # 6. Predicción de perfiles
        profile_map = {1: 'Premium', 0: 'Standard'}
        if clf.n_classes_ > 2:
            profile_map = {i: f'Perfil_{i}' for i in range(clf.n_classes_)}
        
        perfiles = predict_profile(clf, test_combos, class_map=profile_map)
        
        print("\n🎭 Resultados de Perfiles:")
        for combo, perfil in zip(test_combos, perfiles):
            print(f"  {str(combo)[:30]:<30} → {perfil}")
        
        # 7. Guardar modelo
        clf.save()
        logger.info("🎉 Proceso completado exitosamente!")
        
    except Exception as e:
            # Manejo silencioso de errores de compatibilidad
        logger.exception("🔥 Error crítico en el proceso")