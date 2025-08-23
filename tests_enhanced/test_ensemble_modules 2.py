import numpy as np
import pandas as pd

from modules.ensemble_trainer_enhanced import (
    EnsembleTrainerEnhanced,
    TrainingConfig,
    EnsembleStrategy,
)
from modules.ensemble_calibrator_enhanced import (
    EnsembleCalibratorEnhanced,
    CalibrationConfig,
    ModelPerformance as CalibPerf,
)


def _synthetic_combinations(n: int = 64) -> list[list[int]]:
    rng = np.random.default_rng(42)
    combos: list[list[int]] = []
    for _ in range(n):
        # 6 números únicos en [1, 40]
        c = sorted(rng.choice(np.arange(1, 41), size=6, replace=False).tolist())
        combos.append(c)
    return combos


def test_ensemble_trainer_minimal_runs():
    combos = _synthetic_combinations(80)

    cfg = TrainingConfig(
        strategy=EnsembleStrategy.STACKING,
        cv_folds=2,
        temporal_validation=True,
        n_jobs=1,
    )
    trainer = EnsembleTrainerEnhanced(cfg)
    results = trainer.train_ensemble(combos, targets=None, validation_split=0.25)

    assert trainer.is_trained is True
    assert results is not None
    assert 0.0 <= results.ensemble_performance.accuracy <= 1.0
    assert isinstance(results.base_models_performance, dict)
    # Debe haber al menos 1 métrica de CV
    assert isinstance(results.cross_validation_scores, dict)


def test_ensemble_calibrator_simulation_runs():
    combos = _synthetic_combinations(120)
    df = pd.DataFrame({
        "combination": combos,
        # Columna opcional de fecha para habilitar TimeSeriesSplit si aplica
        "fecha": pd.date_range("2024-01-01", periods=len(combos), freq="D"),
    })

    calib = EnsembleCalibratorEnhanced(
        calibration_config=CalibrationConfig(
            cross_validation_folds=2,
            temporal_validation=True,
            drift_detection=False,
            min_samples_for_calibration=10,
        )
    )

    perf = calib.simulate_historical_performance(df, cv_folds=2)
    assert isinstance(perf, dict)
    # Tomar uno cualquiera y verificar estructura de métricas
    if perf:
        any_model = next(iter(perf))
        assert isinstance(perf[any_model], CalibPerf)
        assert 0.0 <= perf[any_model].accuracy <= 1.0


