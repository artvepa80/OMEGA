#!/usr/bin/env python3
"""
Tests para omega_config_enhanced.py
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
import numpy as np

# Importar módulos a testear
try:
    from omega_config_enhanced import (
        OmegaConfig, OmegaLogger, OmegaConfigError, OmegaValidationError,
        LoggingConfig, PerformanceConfig, SecurityConfig, ModelConfig,
        validate_combinations, sanitize_file_path, load_config_from_env,
        get_config, set_config, get_logger
    )
except ImportError as e:
    pytest.skip(f"No se puede importar omega_config_enhanced: {e}", allow_module_level=True)


class TestOmegaConfig:
    """Tests para OmegaConfig"""
    
    def test_config_creation_default(self):
        """Test creación de configuración por defecto"""
        config = OmegaConfig()
        
        assert config.project_name == "OMEGA PRO AI"
        assert config.version == "v10.1-enhanced"
        assert config.environment in ["dev", "test", "production"]
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.performance, PerformanceConfig)
        assert isinstance(config.security, SecurityConfig)
    
    def test_config_validation(self):
        """Test validación de configuración"""
        # Configuración válida
        config = OmegaConfig()
        # No debe lanzar excepción
        
        # Configuración inválida - max_workers
        with pytest.raises(OmegaConfigError):
            OmegaConfig(performance=PerformanceConfig(max_workers=0))
        
        # Configuración inválida - logging level
        with pytest.raises(OmegaConfigError):
            OmegaConfig(logging=LoggingConfig(level="INVALID"))
        
        # Configuración inválida - environment
        with pytest.raises(OmegaConfigError):
            OmegaConfig(environment="invalid_env")
    
    def test_config_to_dict(self):
        """Test conversión a diccionario"""
        config = OmegaConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "project_name" in config_dict
        assert "version" in config_dict
        assert "logging" in config_dict
        assert "performance" in config_dict
        
        # Verificar que paths se convirtieron a strings
        assert isinstance(config_dict["data_dir"], str)
    
    def test_config_from_dict(self):
        """Test creación desde diccionario"""
        data = {
            "project_name": "Test Project",
            "version": "test-v1.0",
            "environment": "test",
            "logging": {"level": "DEBUG"},
            "performance": {"max_workers": 2}
        }
        
        config = OmegaConfig.from_dict(data)
        
        assert config.project_name == "Test Project"
        assert config.version == "test-v1.0"
        assert config.environment == "test"
        assert config.logging.level == "DEBUG"
        assert config.performance.max_workers == 2
    
    def test_config_save_load_json(self):
        """Test guardar y cargar en JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            # Crear y guardar configuración
            original_config = OmegaConfig(project_name="Test Save/Load")
            original_config.save_to_file(config_path)
            
            # Cargar configuración
            loaded_config = OmegaConfig.from_file(config_path)
            
            assert loaded_config.project_name == "Test Save/Load"
            assert loaded_config.version == original_config.version
            
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_config_save_load_yaml(self):
        """Test guardar y cargar en YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            # Crear y guardar configuración
            original_config = OmegaConfig(project_name="Test YAML")
            original_config.save_to_file(config_path)
            
            # Cargar configuración
            loaded_config = OmegaConfig.from_file(config_path)
            
            assert loaded_config.project_name == "Test YAML"
            
        finally:
            Path(config_path).unlink(missing_ok=True)


class TestOmegaLogger:
    """Tests para OmegaLogger"""
    
    def test_logger_creation(self):
        """Test creación de logger"""
        config = LoggingConfig(level="INFO")
        logger_wrapper = OmegaLogger(config, "TEST")
        logger = logger_wrapper.get_logger()
        
        assert logger.name == "TEST"
        assert logger.level == 20  # INFO level
    
    def test_logger_file_output(self):
        """Test logger con salida a archivo"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_path = f.name
        
        try:
            config = LoggingConfig(level="DEBUG", file_path=log_path)
            logger_wrapper = OmegaLogger(config, "FILE_TEST")
            logger = logger_wrapper.get_logger()
            
            logger.info("Test message")
            
            # Verificar que el archivo se creó
            assert Path(log_path).exists()
            
        finally:
            Path(log_path).unlink(missing_ok=True)


class TestValidationFunctions:
    """Tests para funciones de validación"""
    
    def test_validate_combinations_valid(self):
        """Test validación de combinaciones válidas"""
        valid_combinations = [
            [1, 2, 3, 4, 5, 6],
            [10, 15, 20, 25, 30, 35],
            [5, 12, 18, 23, 31, 40]
        ]
        
        result = validate_combinations(valid_combinations)
        
        assert len(result) == 3
        assert all(len(combo) == 6 for combo in result)
        assert all(all(1 <= x <= 40 for x in combo) for combo in result)
        # Verificar que están ordenadas
        assert all(combo == sorted(combo) for combo in result)
    
    def test_validate_combinations_invalid(self):
        """Test validación con combinaciones inválidas"""
        invalid_combinations = [
            [1, 2, 3, 4, 5],  # Muy pocos números
            [1, 2, 3, 4, 5, 6, 7],  # Demasiados números
            [0, 1, 2, 3, 4, 5],  # Número fuera de rango (0)
            [1, 2, 3, 4, 5, 41],  # Número fuera de rango (41)
            [1, 1, 2, 3, 4, 5],  # Duplicados
        ]
        
        # Debería lanzar excepción porque no hay combinaciones válidas
        with pytest.raises(OmegaValidationError):
            validate_combinations(invalid_combinations)
    
    def test_validate_combinations_mixed(self):
        """Test validación con combinaciones mixtas"""
        mixed_combinations = [
            [1, 2, 3, 4, 5, 6],     # Válida
            [1, 2, 3, 4, 5],        # Inválida (pocos números)
            [10, 15, 20, 25, 30, 35], # Válida
            [1, 1, 2, 3, 4, 5],     # Inválida (duplicados)
        ]
        
        result = validate_combinations(mixed_combinations)
        
        assert len(result) == 2  # Solo las 2 válidas
    
    def test_validate_combinations_empty(self):
        """Test validación con lista vacía"""
        with pytest.raises(OmegaValidationError):
            validate_combinations([])
    
    def test_sanitize_file_path_valid(self):
        """Test sanitización de path válido"""
        valid_path = "data/test.csv"
        result = sanitize_file_path(valid_path)
        
        assert isinstance(result, Path)
        assert result.suffix == ".csv"
    
    def test_sanitize_file_path_invalid_extension(self):
        """Test sanitización con extensión inválida"""
        invalid_path = "data/test.exe"
        
        with pytest.raises(OmegaValidationError):
            sanitize_file_path(invalid_path)
    
    def test_sanitize_file_path_custom_extensions(self):
        """Test sanitización con extensiones personalizadas"""
        path = "data/test.txt"
        allowed = [".txt", ".csv"]
        
        result = sanitize_file_path(path, allowed)
        assert result.suffix == ".txt"


class TestGlobalConfig:
    """Tests para configuración global"""
    
    def test_get_set_config(self):
        """Test obtener y establecer configuración global"""
        # Configuración inicial
        initial_config = get_config()
        assert isinstance(initial_config, OmegaConfig)
        
        # Establecer nueva configuración
        new_config = OmegaConfig(project_name="Test Global")
        set_config(new_config)
        
        # Verificar que se estableció
        current_config = get_config()
        assert current_config.project_name == "Test Global"
    
    def test_get_logger_global(self):
        """Test obtener logger global"""
        logger = get_logger("GLOBAL_TEST")
        
        assert logger.name == "GLOBAL_TEST"
        
        # Test que funciona logging
        logger.info("Test global logger")


class TestModelConfig:
    """Tests para ModelConfig"""
    
    def test_model_config_creation(self):
        """Test creación de configuración de modelo"""
        model_config = ModelConfig(
            name="test_model",
            enabled=True,
            timeout_seconds=120,
            params={"param1": "value1"}
        )
        
        assert model_config.name == "test_model"
        assert model_config.enabled is True
        assert model_config.timeout_seconds == 120
        assert model_config.params["param1"] == "value1"


class TestConfigFeatures:
    """Tests para features de dependencias opcionales"""
    
    def test_features_detection(self):
        """Test detección de features disponibles"""
        config = OmegaConfig()
        
        assert isinstance(config.features, dict)
        assert "neural_networks" in config.features
        assert "ensemble_learning" in config.features
        
        # Verificar que son booleanos
        for feature, available in config.features.items():
            assert isinstance(available, bool)


# Fixtures para tests
@pytest.fixture
def sample_config():
    """Fixture con configuración de prueba"""
    return OmegaConfig(
        project_name="Test Project",
        environment="test",
        logging=LoggingConfig(level="DEBUG"),
        performance=PerformanceConfig(max_workers=2)
    )


@pytest.fixture
def sample_combinations():
    """Fixture con combinaciones de prueba"""
    return [
        [1, 2, 3, 4, 5, 6],
        [10, 15, 20, 25, 30, 35],
        [5, 12, 18, 23, 31, 40],
        [7, 14, 21, 28, 35, 39]
    ]


# Tests con fixtures
def test_config_with_fixture(sample_config):
    """Test usando fixture de configuración"""
    assert sample_config.project_name == "Test Project"
    assert sample_config.environment == "test"
    assert sample_config.logging.level == "DEBUG"


def test_validation_with_fixture(sample_combinations):
    """Test validación usando fixture de combinaciones"""
    result = validate_combinations(sample_combinations)
    
    assert len(result) == 4
    assert all(len(combo) == 6 for combo in result)


if __name__ == "__main__":
    # Ejecutar tests directamente
    pytest.main([__file__, "-v"])
