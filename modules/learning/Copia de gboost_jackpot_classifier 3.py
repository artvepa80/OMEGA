# OMEGA_PRO_AI_v10.1/modules/learning/gboost_jackpot_classifier.py

import os
import numpy as np
import pandas as pd
import joblib
import inspect
import logging
import argparse
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_is_fitted
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, confusion_matrix
from sklearn.impute import SimpleImputer

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GBoostJackpotClassifier(BaseEstimator, ClassifierMixin):
    """
    Clasificador de Gradient Boosting mejorado para predicción de jackpots con:
    - Manejo robusto de NaN
    - Validación estricta de datos
    - Serialización segura
    - Parámetros dinámicos
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
        self.gb_params = self._filter_gb_params(gb_params)
        
        # Inicializar componentes
        self.model = GradientBoostingClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=random_state,
            **self.gb_params
        )
        self.mlb = MultiLabelBinarizer()
        self.imputer = SimpleImputer(strategy='mean')
        self.is_fitted_ = False
        self.feature_count_ = 0

    def _filter_gb_params(self, params: dict) -> dict:
        """Filtra parámetros usando inspección dinámica para compatibilidad"""
        sig = inspect.signature(GradientBoostingClassifier.__init__)
        valid_params = list(sig.parameters.keys())
        valid_params.remove('self')  # Excluir parámetro self
        
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
        """Extrae características con manejo robusto de casos límite"""
        try:
            # Manejo de entrada vacía
            if combos_series.empty:
                logger.warning("📭 Entrada vacía en extracción de características")
                return pd.DataFrame()

            # 1. Binarizar presencia de números
            if not hasattr(self.mlb, 'classes_'):
                logger.warning("⚠️ MultiLabelBinarizer no ajustado, ajustando automáticamente")
                self.mlb.fit(combos_series)
                logger.info(f"🔢 Binarizador ajustado a {len(self.mlb.classes_)} clases")
                
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
            
            # 7. Manejo de NaN con detección mejorada
            if df_feats.isnull().any().any():
                nan_count = df_feats.isnull().sum().sum()
                sample_nan = df_feats[df_feats.isnull().any(axis=1)].iloc[0].to_dict()
                logger.warning(f"⚠️ {nan_count} NaNs detectados. Ejemplo: {sample_nan}")
                df_feats = pd.DataFrame(self.imputer.transform(df_feats), columns=df_feats.columns)
            
            # 8. Normalización robusta
            norm_cols = ['sum_total', 'range', 'max_diff']
            for col in norm_cols:
                col_std = df_feats[col].std()
                if not np.isclose(col_std, 0, atol=1e-8):
                    df_feats[col] = (df_feats[col] - df_feats[col].mean()) / col_std
            
            # Registrar cantidad de características
            self.feature_count_ = df_feats.shape[1]
            logger.info(f"🧮 Características generadas: {self.feature_count_}")
            
            return df_feats
        
        except Exception as e:
            logger.exception("Error en extracción de características")
            raise

    def fit(self, X: list, y: list) -> None:
        """Entrenamiento con validación mejorada de datos"""
        try:
            # Validación exhaustiva de entrada
            if len(X) != len(y):
                raise ValueError("X e y deben tener la misma longitud")
            
            if not all(isinstance(c, list) and all(isinstance(i, int) for i in c) for c in X):
                raise ValueError("Cada combinación debe ser lista de enteros")
            
            # Validar que y sea binario
            unique_y = np.unique(y)
            if not set(unique_y).issubset({0, 1}):
                invalid = [val for val in unique_y if val not in (0, 1)]
                raise ValueError(f"Target 'y' debe ser binario (0/1). Valores inválidos: {invalid}")
            
            # Convertir a series
            X_series = pd.Series(X)
            
            # Ajustar componentes
            self.mlb.fit(X_series)
            logger.info(f"🔢 Binarizador ajustado a {len(self.mlb.classes_)} clases")
            
            X_feats = self._extract_features(X_series)
            self.imputer.fit(X_feats)
            logger.info("✅ Imputador ajustado")
            
            # Entrenar modelo
            self.model.fit(X_feats, y)
            self.is_fitted_ = True
            logger.info(f"✅ Modelo entrenado: {len(X)} muestras, {self.feature_count_} características")
            
        except Exception as e:
            logger.exception("Error durante el entrenamiento")
            raise

    def predict(self, combinations: list) -> np.ndarray:
        """Predicción con manejo de entrada vacía"""
        check_is_fitted(self, 'is_fitted_')
        try:
            # Manejo explícito de entrada vacía
            if len(combinations) == 0:
                logger.warning("📭 Entrada vacía en predict(), retornando array vacío")
                return np.array([])
                
            combos = self._validate_combinations(combinations)
            X_new = self._extract_features(pd.Series(combos))
            return self.model.predict(X_new)
        except Exception as e:
            logger.exception("Error en predicción")
            raise

    def predict_proba(self, combinations: list) -> np.ndarray:
        """Predicción de probabilidades con manejo de entrada vacía"""
        check_is_fitted(self, 'is_fitted_')
        try:
            # Manejo explícito de entrada vacía
            if len(combinations) == 0:
                logger.warning("📭 Entrada vacía en predict_proba(), retornando array vacío")
                return np.empty((0, 2))
                
            combos = self._validate_combinations(combinations)
            X_new = self._extract_features(pd.Series(combos))
            return self.model.predict_proba(X_new)
        except Exception as e:
            logger.exception("Error en predicción de probabilidades")
            # Fallback mejorado
            return np.full((len(combinations), 2), 0.5)

    def evaluate(self, X_test: list, y_test: list) -> dict:
        """Evaluación con chequeo multiclase"""
        check_is_fitted(self, 'is_fitted_')
        try:
            y_pred = self.predict(X_test)
            y_proba = self.predict_proba(X_test)[:, 1]
            
            # Calcular métricas
            conf_mat = confusion_matrix(y_test, y_pred)
            unique_classes = np.unique(y_test)
            
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'roc_auc': roc_auc_score(y_test, y_proba) if len(unique_classes) == 2 else None,
                'report': classification_report(y_test, y_pred, output_dict=True),
                'confusion_matrix': conf_mat,
                'n_classes': len(unique_classes)
            }
            
            logger.info(f"📊 Evaluación - Accuracy: {metrics['accuracy']:.4f}")
            if metrics['roc_auc'] is not None:
                logger.info(f"📈 ROC AUC: {metrics['roc_auc']:.4f}")
            logger.info(f"🔢 Matriz de confusión:\n{conf_mat}")
            
            return metrics
        
        except Exception as e:
            logger.exception("Error en evaluación del modelo")
            raise

    def _validate_combinations(self, combinations: list) -> list:
        """Valida combinaciones con reporte detallado de errores"""
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
        """Serialización segura excluyendo objetos no serializables"""
        path = model_path or self.model_path
        if not path:
            raise ValueError("Debe especificar model_path")
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            state = self.__dict__.copy()
            
            # Excluir objetos no serializables
            if 'logger' in state:
                del state['logger']
                
            joblib.dump(state, path)
            logger.info(f"💾 Modelo guardado en {path}")
        except Exception as e:
            logger.exception("Error al guardar modelo")
            raise

    def load(self, model_path: str) -> None:
        """Deserialización con reconstrucción de objetos esenciales"""
        try:
            if not os.path.isfile(model_path):
                raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
            
            state = joblib.load(model_path)
            
            # Reconstruir objetos excluidos
            state['logger'] = logging.getLogger(__name__)
            self.__dict__.update(state)
            
            logger.info(f"🔍 Modelo cargado desde {model_path}")
            if self.is_fitted_:
                logger.info(f"⚙️ Modelo entrenado con {self.feature_count_} características")
                logger.info(f"⚙️ Parámetros: n_estimators={self.n_estimators}, "
                           f"learning_rate={self.learning_rate}, max_depth={self.max_depth}")
        except Exception as e:
            logger.exception("Error al cargar modelo")
            raise


def predict_profile(
    model: GBoostJackpotClassifier, 
    combinations: list,
    class_map: dict = {1: 'A', 0: 'B'}  # Mapeo personalizable
) -> list:
    """
    Devuelve perfiles simbólicos para cada combinación
    con mapeo personalizable de clases
    
    Parámetros:
        model: Modelo entrenado
        combinations: Combinaciones a predecir
        class_map: Diccionario de mapeo de clases
        
    Retorna:
        Lista de perfiles para cada combinación
    """
    try:
        predictions = model.predict(combinations)
        profiles = [class_map.get(int(p), '?') for p in predictions]
        return profiles
    except Exception as e:
        logger.error(f"Error al predecir perfil: {e}")
        return ["?"] * len(combinations)


if __name__ == "__main__":
    # Configuración mediante CLI
    parser = argparse.ArgumentParser(description='Entrenamiento y evaluación de GBoostJackpotClassifier')
    parser.add_argument('--data_path', default='data/jackpot_dataset.csv', help='Ruta del dataset')
    parser.add_argument('--model_path', default='models/prod_jackpot_classifier.pkl', help='Ruta para guardar modelo')
    parser.add_argument('--n_estimators', type=int, default=200, help='Número de estimadores')
    parser.add_argument('--learning_rate', type=float, default=0.05, help='Tasa de aprendizaje')
    parser.add_argument('--max_depth', type=int, default=5, help='Profundidad máxima')
    args = parser.parse_args()

    logger.info("🚀 Ejecutando GBoostJackpotClassifier - Versión Mejorada")
    
    try:
        # 1. Cargar datos usando ruta configurable
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
            y = (np.random.rand(n_samples) > 0.98).astype(int).tolist()
            logger.info(f"🧪 Datos de ejemplo: {n_samples} muestras, {sum(y)} jackpots")
        
        # 2. Dividir datos
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        logger.info(f"📊 Conjuntos: Train={len(X_train)}, Test={len(X_test)}")
        
        # 3. Entrenar modelo con parámetros configurables
        clf = GBoostJackpotClassifier(
            model_path=args.model_path,
            n_estimators=args.n_estimators,
            learning_rate=args.learning_rate,
            max_depth=args.max_depth,
            random_state=42,
            subsample=0.8
        )
        clf.fit(X_train, y_train)
        
        # 4. Evaluar modelo
        metrics = clf.evaluate(X_test, y_test)
        print("\n📊 Métricas de Rendimiento:")
        print(f"Accuracy: {metrics['accuracy']:.4f}")
        if metrics['roc_auc'] is not None:
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
        
        # 6. Ejemplo de predicción de perfiles con mapeo personalizado
        print("\n🎭 Predicciones de Perfiles:")
        profile_map = {1: 'Premium', 0: 'Standard'}  # Mapeo personalizado
        perfiles = predict_profile(clf, test_combos, class_map=profile_map)
        for combo, perfil in zip(test_combos, perfiles):
            print(f"  {combo}: Perfil {perfil}")
        
        # 7. Guardar modelo
        clf.save()
        logger.info("🎉 Proceso completado exitosamente!")
        
    except Exception as e:
        logger.exception("🔥 Error crítico en el proceso")