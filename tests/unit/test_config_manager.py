#!/usr/bin/env python3
"""
🧪 Tests para ConfigManager
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.core.config_manager import ConfigManager, ModelConfig, SystemConfig

class TestConfigManager:
    """Tests para el gestor de configuración"""
    
    def test_default_initialization(self, test_data_dir):
        """Test de inicialización con valores por defecto"""
        config_path = test_data_dir / "test_config.json"
        
        config_manager = ConfigManager(str(config_path))
        
        # Verificar valores por defecto
        assert config_manager.system.app_name == "OMEGA PRO AI"
        assert config_manager.system.version == "10.1"
        assert config_manager.prediction.target_count == 8
        assert config_manager.prediction.combo_length == 6
        
        # Verificar que se creó archivo de configuración
        assert config_path.exists()
    
    def test_load_existing_config(self, test_data_dir):
        """Test de carga de configuración existente"""
        config_path = test_data_dir / "existing_config.json"
        
        # Crear archivo de configuración de prueba
        test_config = {
            "system": {
                "app_name": "OMEGA TEST",
                "version": "test-1.0",
                "environment": "testing",
                "debug": True,
                "log_level": "DEBUG"
            },
            "prediction": {
                "target_count": 5,
                "combo_length": 6,
                "number_range_min": 1,
                "number_range_max": 40
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        config_manager = ConfigManager(str(config_path))
        
        # Verificar que se cargaron los valores correctos
        assert config_manager.system.app_name == "OMEGA TEST"
        assert config_manager.system.version == "test-1.0"
        assert config_manager.system.debug is True
        assert config_manager.prediction.target_count == 5
    
    def test_model_configuration(self, test_data_dir):
        """Test de configuración de modelos"""
        config_path = test_data_dir / "config_with_models.json"
        models_path = test_data_dir / "models.json"
        
        # Crear configuración de modelos
        models_config = {
            "neural_test": {
                "enabled": True,
                "weight": 0.6,
                "params": {"epochs": 50},
                "lazy_loading": True
            },
            "lstm_test": {
                "enabled": False,
                "weight": 0.4,
                "params": {"layers": 2},
                "lazy_loading": False
            }
        }
        
        with open(models_path, 'w') as f:
            json.dump(models_config, f)
        
        config_manager = ConfigManager(str(config_path))
        
        # Verificar modelos cargados
        assert "neural_test" in config_manager.models
        assert "lstm_test" in config_manager.models
        assert config_manager.models["neural_test"].enabled is True
        assert config_manager.models["neural_test"].weight == 0.6
        assert config_manager.models["lstm_test"].enabled is False
    
    @patch.dict('os.environ', {
        'OMEGA_DEBUG': 'true',
        'OMEGA_LOG_LEVEL': 'ERROR',
        'OMEGA_TARGET_COUNT': '10'
    })
    def test_environment_variables(self, test_data_dir):
        """Test de carga de variables de entorno"""
        config_path = test_data_dir / "env_config.json"
        
        config_manager = ConfigManager(str(config_path))
        
        # Verificar que las variables de entorno se aplicaron
        assert config_manager.system.debug is True
        assert config_manager.system.log_level == "ERROR"
        assert config_manager.prediction.target_count == 10
    
    def test_get_enabled_models(self, test_data_dir):
        """Test de obtención de modelos habilitados"""
        config_path = test_data_dir / "enabled_models.json"
        
        config_manager = ConfigManager(str(config_path))
        
        # Agregar algunos modelos de prueba
        config_manager.models["model_1"] = ModelConfig("model_1", True, 0.5, {})
        config_manager.models["model_2"] = ModelConfig("model_2", False, 0.3, {})
        config_manager.models["model_3"] = ModelConfig("model_3", True, 0.2, {})
        
        enabled_models = config_manager.get_enabled_models()
        
        assert len(enabled_models) == 2
        assert "model_1" in enabled_models
        assert "model_3" in enabled_models
        assert "model_2" not in enabled_models
    
    def test_config_value_operations(self, test_data_dir):
        """Test de operaciones get/set de valores"""
        config_path = test_data_dir / "value_ops.json"
        config_manager = ConfigManager(str(config_path))
        
        # Test get_config_value
        debug_value = config_manager.get_config_value("system.debug", False)
        assert debug_value is False  # Valor por defecto
        
        # Test set_config_value
        config_manager.set_config_value("system.debug", True)
        assert config_manager.system.debug is True
        
        # Test valor personalizado
        config_manager.custom["test_key"] = "test_value"
        custom_value = config_manager.get_config_value("test_key")
        assert custom_value == "test_value"
    
    def test_model_weight_update(self, test_data_dir):
        """Test de actualización de pesos de modelos"""
        config_path = test_data_dir / "weight_update.json"
        config_manager = ConfigManager(str(config_path))
        
        # Agregar modelo de prueba
        config_manager.models["test_model"] = ModelConfig("test_model", True, 0.5, {})
        
        # Actualizar peso
        config_manager.update_model_weight("test_model", 0.8)
        
        assert config_manager.models["test_model"].weight == 0.8
    
    def test_model_toggle(self, test_data_dir):
        """Test de habilitación/deshabilitación de modelos"""
        config_path = test_data_dir / "model_toggle.json"
        config_manager = ConfigManager(str(config_path))
        
        # Agregar modelo de prueba
        config_manager.models["toggle_model"] = ModelConfig("toggle_model", True, 0.5, {})
        
        # Deshabilitar modelo
        config_manager.toggle_model("toggle_model", False)
        assert config_manager.models["toggle_model"].enabled is False
        
        # Habilitar modelo
        config_manager.toggle_model("toggle_model", True)
        assert config_manager.models["toggle_model"].enabled is True
    
    def test_config_summary(self, test_data_dir):
        """Test de resumen de configuración"""
        config_path = test_data_dir / "summary_test.json"
        config_manager = ConfigManager(str(config_path))
        
        # Agregar algunos modelos
        config_manager.models["enabled_model"] = ModelConfig("enabled_model", True, 0.5, {})
        config_manager.models["disabled_model"] = ModelConfig("disabled_model", False, 0.3, {})
        
        summary = config_manager.get_summary()
        
        assert "system" in summary
        assert "prediction" in summary
        assert "performance" in summary
        assert "models" in summary
        assert summary["models"]["total"] == 2
        assert summary["models"]["enabled"] == 1
        assert summary["models"]["disabled"] == 1
    
    def test_invalid_config_handling(self, test_data_dir):
        """Test de manejo de configuración inválida"""
        config_path = test_data_dir / "invalid_config.json"
        
        # Crear archivo con JSON inválido
        with open(config_path, 'w') as f:
            f.write("{ invalid json }")
        
        # Debería usar configuración por defecto sin fallar
        config_manager = ConfigManager(str(config_path))
        
        assert config_manager.system.app_name == "OMEGA PRO AI"
        assert config_manager.prediction.target_count == 8