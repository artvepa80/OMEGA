# tests/test_predictor.py – Tests unitarios para HybridOmegaPredictor

import pytest
import os
from core.predictor import HybridOmegaPredictor

@pytest.fixture
def sample_data(tmp_path):
    """Crea un archivo CSV simulado con sorteos históricos."""
    file_path = tmp_path / "historial_kabala_github.csv"
    with open(file_path, "w") as f:
        f.write("Bolilla 1,Bolilla 2,Bolilla 3,Bolilla 4,Bolilla 5,Bolilla 6\n")
        for i in range(1, 51):
            f.write(f"{i},{(i%40)+1},{(i+1)%40+1},{(i+2)%40+1},{(i+3)%40+1},{(i+4)%40+1}\n")
    return str(file_path)

def test_predictor_initialization(sample_data):
    predictor = HybridOmegaPredictor(data_path=sample_data, cantidad_final=5)
    assert predictor.data is not None
    assert len(predictor.data) >= 10

def test_predictor_run_all_models(sample_data):
    predictor = HybridOmegaPredictor(data_path=sample_data, cantidad_final=5)
    predictor.set_ghost_rng_usage(True)
    predictor.set_ghost_rng_params(max_seeds=2, cantidad_por_seed=2, training_mode=False)
    predictor.set_positional_analysis(True)
    predictor.set_auto_export(False)
    predictor.set_logging_level("INFO")
    
    combinaciones = predictor.run_all_models()
    
    assert isinstance(combinaciones, list)
    assert len(combinaciones) > 0
    assert all("combination" in c and isinstance(c["combination"], list) for c in combinaciones)