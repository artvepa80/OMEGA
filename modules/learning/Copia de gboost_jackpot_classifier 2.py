
# OMEGA_PRO_AI_v10.1/modules/learning/gboost_jackpot_classifier.py

import os
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_is_fitted
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, confusion_matrix
from sklearn.impute import SimpleImputer  # Nueva importación para manejar NaN
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GBoostJackpotClassifier(BaseEstimator, ClassifierMixin):
    """
    Clasificador de Gradient Boosting para predicción de jackpots con mejoras en robustez y manejo de errores.
    
    Mejoras implementadas:
    - Manejo automático de NaN en features con SimpleImputer.
    - Validación estricta de fitted state antes de transform/predict.
    - Binarizador (mlb) ajustado correctamente en fit con datos limpios.
    - Logging detallado en cada paso crítico.
    - Fallbacks para errores comunes (e.g., return default probs si predict falla).
    - Optimización: Reducción de features innecesarias si posible.
    
    Parámetros:
        model_path (str): Ruta para guardar/cargar modelo
        n_estimators (int): Número de árboles (default=100)
        learning_rate (float): Tasa de aprendizaje (default=0.1)
        max_depth (int): Profundidad máxima (default=3)
        random_state (int): Semilla (default=42)
        **gb_params: Parámetros adicionales compatibles con GradientBoostingClassifier
    """

    def __init__(
        self,
        model_path: str = None,
        n_estimators: int = 100,
        learning_rate: float = 0.1,
        max_depth: int = 3,
        random_state: int = 42,
        **gb_params
    ):
        self.model_path = model_path
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_state = random_state
        self.gb_params = self._filter_gb_params(gb_params)  # Filtrar parámetros
        
        # Inicializar componentes
        self.model = GradientBoostingClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=random_state,
            **self.gb_params  # Solo parámetros compatibles
        )
        self.mlb = MultiLabelBinarizer()
        self.imputer = SimpleImputer(strategy='mean')  # Nueva: Imputador para NaN
        self.is_fitted_ = False
        self.feature_count_ = 0

    def _filter_gb_params(self, params: dict) -> dict:
        """Filtra parámetros incompatibles con GradientBoostingClassifier"""
        valid_params = [
            'loss', 'criterion', 'min_samples_split', 'min_samples_leaf',
            'min_weight_fraction_leaf', 'min_impurity_decrease', 'init',
            'subsample', 'max_features', 'max_leaf_nodes', 'validation_fraction',
            'n_iter_no_change', 'tol', 'ccp_alpha', 'verbose'
        ]
        
        filtered_params = {}
        invalid_params = []
        
        for key, value in params.items():
            if key in valid_params:
                filtered_params[key] = value
            else:
                invalid_params.append(key)
        
        if invalid_params:
            logger.warning(f"⚠️ Parámetros no compatibles ignorados: {invalid_params}")
        
        return filtered_params

    def _extract_features(self, combos_series: pd.Series) -> pd.DataFrame:
        """Extrae características con normalización robusta, manejo de NaN y registro de métricas"""
        try:
            # 1. Binarizar presencia de números (fallback a fit si no estaba ajustado)
            if not hasattr(self.mlb, 'classes_'):
                logger.warning("⚠️ MultiLabelBinarizer no está ajustado, ajustando automáticamente al set de datos.")
                self.mlb.fit(combos_series)
                logger.info(f"🔢 Binarizador ajustado automáticamente a {len(self.mlb.classes_)} clases: {self.mlb.classes_}")
            X_nums = self.mlb.transform(combos_series)
            df_feats = pd.DataFrame(X_nums, columns=[f"num_{i}" for i in self.mlb.classes_])
            
            # 2. Estadísticas básicas
            combos_arr = np.array(combos_series.tolist())
            df_feats['sum_total'] = combos_arr.sum(axis=1)
            df_feats['mean'] = combos_arr.mean(axis=1)
            df_feats['std'] = combos_arr.std(axis=1)
            df_feats['min'] = combos_arr.min(axis=1)
            df_feats['max'] = combos_arr.max(axis=1)
            
            # 3. Conteo par/impar
            even_mask = combos_arr % 2 == 0
            df_feats['count_even'] = even_mask.sum(axis=1)
            df_feats['count_odd'] = 6 - df_feats['count_even']
            
            # 4. Distribución por décadas
            decades = np.zeros((len(combos_arr), 4))
            for i in range(4):
                start, end = i*10 + 1, (i+1)*10
                decade_mask = (combos_arr >= start) & (combos_arr <= end)
                decades[:, i] = decade_mask.sum(axis=1)
            for i in range(4):
                df_feats[f'decade_{i+1}'] = decades[:, i]
            
            # 5. Características avanzadas
            df_feats['range'] = df_feats['max'] - df_feats['min']
            df_feats['median'] = np.median(combos_arr, axis=1)
            df_feats['q1'] = np.percentile(combos_arr, 25, axis=1)
            df_feats['q3'] = np.percentile(combos_arr, 75, axis=1)
            
            # 6. Secuencias y patrones
            sorted_diffs = np.diff(np.sort(combos_arr, axis=1), axis=1)
            df_feats['max_diff'] = sorted_diffs.max(axis=1)
            df_feats['min_diff'] = sorted_diffs.min(axis=1)
            df_feats['mean_diff'] = sorted_diffs.mean(axis=1)
            df_feats['consecutive'] = (sorted_diffs == 1).sum(axis=1)
            
            # 7. Manejo de NaN con imputer
            if df_feats.isnull().any().any():
                logger.warning("⚠️ NaN detectados en features, aplicando imputación")
                df_feats = pd.DataFrame(self.imputer.transform(df_feats), columns=df_feats.columns)
            
            # 8. Normalización robusta con tolerancia numérica
            norm_cols = ['sum_total', 'range', 'max_diff']
            for col in norm_cols:
                col_std = df_feats[col].std()
                if not np.isclose(col_std, 0, atol=1e-8):
                    df_feats[col] = (df_feats[col] - df_feats[col].mean()) / col_std
            
            # Registrar cantidad de características generadas
            self.feature_count_ = df_feats.shape[1]
            logger.info(f"🧮 Características generadas: {self.feature_count_}")
            
            return df_feats
        
        except Exception as e:
            logger.exception("Error en extracción de características")
            raise

    def fit(self, X: list, y: list) -> None:
        """Entrenamiento con validación estricta de entrada y manejo de NaN"""
        try:
            # Validación exhaustiva de entrada
            if len(X) != len(y):
                raise ValueError("X e y deben tener la misma longitud")
            
            if not all(isinstance(c, list) and all(isinstance(i, int) for i in c) for c in X):
                raise ValueError("Cada combinación debe ser una lista de enteros")
            
            # Convertir a series
            X_series = pd.Series(X)
            
            # Ajustar binarizador a los datos actuales
            self.mlb.fit(X_series)
            logger.info(f"🔢 Binarizador ajustado a {len(self.mlb.classes_)} clases: {self.mlb.classes_}")
            
            # Extraer características
            X_feats = self._extract_features(X_series)
            
            # Ajustar imputador a los datos de entrenamiento
            self.imputer.fit(X_feats)
            logger.info("✅ Imputador ajustado para manejo de NaN")
            
            # Entrenar modelo
            self.model.fit(X_feats, y)
            self.is_fitted_ = True
            logger.info(f"✅ Modelo entrenado con {len(X)} muestras y {self.feature_count_} características")
            
        except Exception as e:
            logger.exception("Error durante el entrenamiento")
            raise

    def predict(self, combinations: list) -> np.ndarray:
        """
        Predice clases para combinaciones con validación robusta.
        
        Parámetros:
            combinations (list): Lista de combinaciones a predecir
        
        Retorna:
            np.ndarray: Clases predichas (0 o 1)
        """
        check_is_fitted(self, 'is_fitted_')
        try:
            combos = self._validate_combinations(combinations)
            X_new = self._extract_features(pd.Series(combos))
            return self.model.predict(X_new)
        except Exception as e:
            logger.exception("Error en predicción")
            raise

    def predict_proba(self, combinations: list) -> np.ndarray:
        """
        Predice probabilidades para combinaciones.
        
        Parámetros:
            combinations (list): Lista de combinaciones a evaluar
        
        Retorna:
            np.ndarray: Probabilidades de clase [P(0), P(1)]
        """
        check_is_fitted(self, 'is_fitted_')
        try:
            combos = self._validate_combinations(combinations)
            X_new = self._extract_features(pd.Series(combos))
            return self.model.predict_proba(X_new)
        except Exception as e:
            logger.exception("Error en predicción de probabilidades")
            # Fallback: Retornar probabilidades neutras si falla
            return np.full((len(combinations), 2), 0.5)

    def evaluate(self, X_test: list, y_test: list) -> dict:
        """Evaluación completa con métricas detalladas"""
        check_is_fitted(self, 'is_fitted_')
        try:
            y_pred = self.predict(X_test)
            y_proba = self.predict_proba(X_test)[:, 1]
            
            # Calcular métricas
            conf_mat = confusion_matrix(y_test, y_pred)
            
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'roc_auc': roc_auc_score(y_test, y_proba),
                'report': classification_report(y_test, y_pred, output_dict=True),
                'confusion_matrix': conf_mat
            }
            
            logger.info(f"📊 Evaluación - ROC AUC: {metrics['roc_auc']:.4f}")
            logger.info(f"🔢 Matriz de confusión:\n{conf_mat}")
            
            return metrics
        
        except Exception as e:
            logger.exception("Error en evaluación del modelo")
            raise

    def _validate_combinations(self, combinations: list) -> list:
        """Valida y normaliza combinaciones con mensajes detallados"""
        valid_combos = []
        for i, combo in enumerate(combinations):
            try:
                # Conversión y validación de tipos
                if not isinstance(combo, list):
                    raise TypeError(f"Debe ser lista, recibido {type(combo).__name__}")
                
                combo = [int(x) for x in combo]
                
                # Validación de estructura
                if len(combo) != 6:
                    raise ValueError(f"Debe tener 6 números, tiene {len(combo)}")
                
                if min(combo) < 1 or max(combo) > 40:
                    raise ValueError(f"Números fuera de rango [1-40]")
                
                valid_combos.append(combo)
                
            except Exception as e:
                logger.error(f"❌ Combinación inválida en posición {i}: {combo}")
                logger.error(f"    → Error: {str(e)}")
                raise
        
        return valid_combos

    def save(self, model_path: str = None) -> None:
        """Serialización completa del estado del objeto"""
        path = model_path or self.model_path
        if not path:
            raise ValueError("Debe especificar model_path")
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            # Serializar todo el estado del objeto
            state = self.__dict__.copy()
            joblib.dump(state, path)
            logger.info(f"💾 Estado completo del modelo guardado en {path}")
        except Exception as e:
            logger.exception("Error al guardar modelo")
            raise

    def load(self, model_path: str) -> None:
        """Deserialización completa del estado del objeto"""
        try:
            if not os.path.isfile(model_path):
                raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
            
            # Deserializar y actualizar estado
            state = joblib.load(model_path)
            self.__dict__.update(state)
            logger.info(f"🔍 Modelo cargado desde {model_path}")
            
            # Registro detallado
            if self.is_fitted_:
                logger.info(f"⚙️ Modelo entrenado con {self.feature_count_} características")
                logger.info(f"⚙️ Parámetros: n_estimators={self.n_estimators}, "
                           f"learning_rate={self.learning_rate}, max_depth={self.max_depth}")
        except Exception as e:
            logger.exception("Error al cargar modelo")
            raise


def predict_profile(model: GBoostJackpotClassifier, combinations: list) -> list:  # FIXED: Renamed from 'predecir_perfil' to English for consistency
    """
    Devuelve perfiles simbólicos ('A', 'B') para cada combinación
    según la predicción del modelo (0 → B, 1 → A).
    
    Parámetros:
        model (GBoostJackpotClassifier): Modelo entrenado
        combinations (list): Lista de combinaciones a predecir
        
    Retorna:
        list: Lista de perfiles ('A' o 'B') para cada combinación
    """
    try:
        predicciones = model.predict(combinations)
        perfiles = ['A' if p == 1 else 'B' for p in predicciones]
        return perfiles
    except Exception as e:
        logger.error(f"Error al predecir perfil: {e}")
        return ["?"] * len(combinations)


if __name__ == "__main__":
    # Ejemplo de uso profesional
    from sklearn.model_selection import train_test_split
    
    logger.info("🚀 Ejecutando GBoostJackpotClassifier - Versión Completa")
    
    try:
        # 1. Cargar datos
        data_path = os.path.join("data", "jackpot_dataset.csv")
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            df['combination'] = df['combination'].apply(eval)
            X = df['combination'].tolist()
            y = df['is_jackpot'].astype(int).tolist()
            logger.info(f"✅ Datos cargados: {len(X)} muestras, {sum(y)} jackpots")
        else:
            logger.warning("⚠️ Archivo no encontrado, generando datos de ejemplo...")
            n_samples = 5000
            X = [sorted(np.random.choice(range(1, 41), 6, replace=False)) for _ in range(n_samples)]
            y = (np.random.rand(n_samples) > 0.98).astype(int).tolist()  # ~2% jackpots
            logger.info(f"🧪 Datos de ejemplo: {n_samples} muestras, {sum(y)} jackpots")
        
        # 2. Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        logger.info(f"📊 Conjuntos: Train={len(X_train)}, Test={len(X_test)}")
        
        # 3. Entrenar modelo con parámetros seguros
        clf = GBoostJackpotClassifier(
            model_path="models/prod_jackpot_classifier.pkl",
            n_estimators=200,
            learning_rate=0.05,
            max_depth=5,
            random_state=42,
            subsample=0.8
        )
        clf.fit(X_train, y_train)
        
        # 4. Evaluar modelo
        metrics = clf.evaluate(X_test, y_test)
        print("\n📊 Métricas de Rendimiento:")
        print(f"Accuracy: {metrics['accuracy']:.4f}")
        print(f"ROC AUC: {metrics['roc_auc']:.4f}")
        print("\n📝 Reporte de Clasificación:")
        print(classification_report(y_test, clf.predict(X_test)))
        
        # 5. Ejemplo de predicción
        test_combos = [
            [7, 14, 21, 28, 35, 40],  
            [3, 10, 15, 22, 29, 36],
            [1, 2, 3, 4, 5, 6]
        ]
        
        print("\n🔮 Predicciones:")
        for combo in test_combos:
            try:
                proba = clf.predict_proba([combo])[0][1]
                status = "GANADORA" if proba > 0.5 else "no ganadora"
                print(f"  {combo}: {proba:.4f} → {status}")
            except Exception as e:
                print(f"  {combo}: ERROR - {str(e)}")
        
        # 6. Ejemplo de predicción de perfiles
        print("\n🎭 Predicciones de Perfiles:")
        perfiles = predict_profile(clf, test_combos)
        for combo, perfil in zip(test_combos, perfiles):
            print(f"  {combo}: Perfil {perfil}")
        
        # 7. Guardar modelo
        clf.save()
        logger.info("🎉 Proceso completado exitosamente!")
        
    except Exception as e:
        logger.exception("🔥 Error crítico en el proceso")