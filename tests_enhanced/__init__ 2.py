"""
Tests Enhanced para OMEGA PRO AI v10.1

Tests unitarios para los módulos enhanced del proyecto OMEGA.
Incluye tests para:
- omega_config_enhanced
- heuristic_optimizer_enhanced  
- ensemble_calibrator_enhanced
- ensemble_trainer_enhanced
- Y otros módulos enhanced

Uso:
    pytest tests_enhanced/
    python -m pytest tests_enhanced/ -v
    python -m pytest tests_enhanced/test_omega_config.py::TestOmegaConfig::test_config_creation_default -v
"""

__version__ = "1.0.0"
__author__ = "OMEGA Enhanced Team"

# Configuración por defecto de pytest
pytest_plugins = []

# Configuraciones comunes para tests
TEST_DATA_DIR = "tests_enhanced/data"
TEST_TEMP_DIR = "tests_enhanced/temp"

# Fixtures globales disponibles para todos los tests
import pytest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path


@pytest.fixture(scope="session")
def test_combinations():
    """Fixture global con combinaciones de prueba"""
    return [
        [1, 2, 3, 4, 5, 6],
        [10, 15, 20, 25, 30, 35],
        [5, 12, 18, 23, 31, 40],
        [7, 14, 21, 28, 35, 39],
        [2, 8, 16, 24, 32, 38],
        [13, 17, 22, 29, 33, 37],
        [4, 9, 14, 19, 26, 34],
        [6, 11, 18, 25, 31, 36]
    ]


@pytest.fixture(scope="session")
def test_dataframe(test_combinations):
    """Fixture global con DataFrame de prueba"""
    return pd.DataFrame({
        'combination': test_combinations,
        'fecha': pd.date_range('2020-01-01', periods=len(test_combinations)),
        'resultado': np.random.choice([0, 1], size=len(test_combinations))
    })


@pytest.fixture
def temp_csv_file(test_dataframe):
    """Fixture que crea archivo CSV temporal"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        test_dataframe.to_csv(f.name, index=False)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_directory():
    """Fixture que crea directorio temporal"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


# Configuración de logging para tests
import logging
logging.getLogger("omega").setLevel(logging.WARNING)  # Reducir verbosidad en tests
