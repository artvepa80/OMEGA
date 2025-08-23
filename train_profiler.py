# train_profiler.py

import pandas as pd
import joblib
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Any
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

logger = logging.getLogger(__name__)

class JackpotProfiler:
    """
    Perfilador avanzado de combinaciones de lotería.
    Carga opcionalmente un modelo entrenado y un MultiLabelBinarizer
    para generar probabilidades de jackpot.
    """

    def __init__(
        self,
        model_path: str = "models/jackpot_profiler.pkl",
        mlb_path: str = "models/jackpot_profiler_mlb.pkl",
        log_file: str = None,
        **config
    ):
        self.model_path = Path(model_path)
        self.mlb_path = Path(mlb_path)
        self.config = config
        self._file_handler = None

        self._setup_logging(log_file)

        # Solo cargar modelo si nos pasan ruta no vacía
        if model_path:
            self._load_model()
            self._validate_model()
        else:
            logger.info("⚠️ Saltando carga de modelo (ruta vacía).")

        # Solo cargar mlb si ruta no vacía
        if mlb_path:
            self._load_mlb()
        else:
            logger.info("⚠️ Saltando carga del MultiLabelBinarizer (ruta vacía).")

        logger.info(f"✅ JackpotProfiler listo.")

    def _setup_logging(self, log_file: str):
        for h in logger.handlers[:]:
            logger.removeHandler(h)
        fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(fmt)
            fh.setLevel(logging.DEBUG)
            logger.addHandler(fh)
            self._file_handler = fh

    def _load_model(self):
        if not self.model_path.exists():
            logger.critical(f"❌ Modelo no encontrado: {self.model_path}")
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        try:
            self.model = joblib.load(self.model_path)
            logger.info(f"🔍 Modelo cargado desde {self.model_path}")
        except Exception as e:
            logger.exception("Error cargando modelo")
            raise RuntimeError(f"Error loading model: {e}") from e

    def _validate_model(self):
        if not hasattr(self.model, 'classes_'):
            raise AttributeError("Modelo no tiene clases definidas")
        logger.info(f"🏷️ Clases: {self.model.classes_}")
        self.expected_features = getattr(self.model, 'n_features_in_', 17)
        logger.info(f"📐 Espera {self.expected_features} features")

    def _load_mlb(self):
        if not self.mlb_path.exists():
            logger.critical(f"❌ MLB no encontrado: {self.mlb_path}")
            raise FileNotFoundError(f"MLB file not found: {self.mlb_path}")
        try:
            self.mlb = joblib.load(self.mlb_path)
            logger.info(f"🔍 MLB cargado desde {self.mlb_path}")
        except Exception as e:
            logger.exception("Error cargando MLB")
            raise RuntimeError(f"Error loading MLB: {e}") from e

    def _calculate_entropy(self, values: np.ndarray) -> float:
        uniq, cnts = np.unique(values, return_counts=True)
        p = cnts / cnts.sum()
        return -np.sum(p * np.log2(p + 1e-10))

    def _extract_features(self, comb: List[int]) -> np.ndarray:
        arr = np.array(comb)
        sorted_arr = np.sort(arr)
        stats = [arr.sum(), arr.mean(), arr.std(), arr.min(), arr.max(), np.ptp(arr)]
        bins = (arr - self.config.get('min_value', 1)) // 10
        decades = [np.sum(bins == i) for i in range(4)]
        ent_dec = self._calculate_entropy(bins)
        norm = sorted_arr - sorted_arr.mean()
        fft = np.abs(np.fft.rfft(norm))[:3]
        diffs = np.diff(sorted_arr)
        diff_feats = [diffs.max(), diffs.mean(), self._calculate_entropy(diffs)]
        feat = np.concatenate([stats, decades, [ent_dec], fft, diff_feats])
        if hasattr(self, 'expected_features') and feat.shape[0] != self.expected_features:
            logger.warning(f"Dim features {feat.shape[0]} vs esperado {self.expected_features}")
        return feat

    def profile(self, combinations: List[List[int]]) -> List[Dict[str, Any]]:
        feats = [self._extract_features(c) for c in combinations]
        X_feat = np.vstack(feats)
        X_num = self.mlb.transform(combinations)
        X_full = np.hstack([X_num, X_feat])
        probas = self.model.predict_proba(X_full)
        pos_idx = list(self.model.classes_).index(1)
        results = []
        for comb, p in zip(combinations, probas):
            results.append({
                "combination": comb,
                "jackpot_prob": round(float(p[pos_idx]), 4)
            })
        return results

    def close(self):
        if self._file_handler:
            logger.removeHandler(self._file_handler)
            self._file_handler.close()

    def __enter__(self): return self
    def __exit__(self, *args): self.close()

# ── Script de entrenamiento ────────────────────────────────────────────────

if __name__ == "__main__":
    # 1) Monkey-patch para saltar carga inicial de sklearn/skipped
    import modules.profiling.jackpot_profiler as jp
    jp.JackpotProfiler._load_model = lambda self: None
    jp.JackpotProfiler._validate_model = lambda self: None

    # 2) Leer dataset completo
    df = pd.read_csv("data/processed/DataFrame_completo_de_sorteos.csv")
    combos = df[["n1","n2","n3","n4","n5","n6"]].apply(lambda r: tuple(r.astype(int)), axis=1)
    y = df["label"].astype(int)

    # 3) Preparar binarizador
    profiler = JackpotProfiler(model_path="", mlb_path="")  # rutas dummy → salta carga
    profiler.mlb = MultiLabelBinarizer()
    profiler.mlb.fit(combos)

    # 4) Extraer features + números one-hot
    X_feats = np.array([profiler._extract_features(list(c)) for c in combos])
    X_nums  = profiler.mlb.transform(combos)
    X_full  = np.hstack([X_nums, X_feats])

    # 5) Entrenar RandomForest
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_full, y)

    # 6) Guardar pickles
    Path("models").mkdir(exist_ok=True)
    joblib.dump(clf, "models/jackpot_profiler.pkl")
    joblib.dump(profiler.mlb, "models/jackpot_profiler_mlb.pkl")

    print("✅ JackpotProfiler trained and pickles saved.")
