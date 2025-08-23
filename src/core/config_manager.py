#!/usr/bin/env python3
"""
⚙️ OMEGA Config Manager - Gestor Centralizado de Configuración
Maneja todas las configuraciones del sistema de manera centralizada
"""

import json
import os
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

@dataclass
class ModelConfig:
    """Configuración de modelo individual"""
    name: str
    enabled: bool
    weight: float
    params: Dict[str, Any]
    lazy_loading: bool = True

@dataclass
class SystemConfig:
    """Configuración del sistema"""
    app_name: str = "OMEGA PRO AI"
    version: str = "10.1"
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"

@dataclass
class PredictionConfig:
    """Configuración de predicciones"""
    target_count: int = 8
    combo_length: int = 6
    number_range_min: int = 1
    number_range_max: int = 40
    svi_weight: float = 0.3
    confidence_weight: float = 0.7
    diversity_threshold: float = 0.6

@dataclass
class PerformanceConfig:
    """Configuración de rendimiento"""
    enable_parallel_processing: bool = True
    max_workers: int = 4
    batch_size: int = 100
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour
    lazy_loading: bool = True

class ConfigChangeHandler(FileSystemEventHandler):
    """Maneja cambios en archivos de configuración"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger("ConfigChangeHandler")
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            self.logger.info(f"📝 Detectado cambio en configuración: {event.src_path}")
            self.config_manager.reload_config()

class ConfigManager:
    """
    Gestor centralizado de configuración con recarga automática
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/omega_config.json"
        self.config_dir = Path(self.config_path).parent
        self.logger = logging.getLogger("ConfigManager")
        
        # Configuraciones por defecto
        self.system = SystemConfig()
        self.prediction = PredictionConfig()
        self.performance = PerformanceConfig()
        self.models: Dict[str, ModelConfig] = {}
        self.custom: Dict[str, Any] = {}
        
        # Observer para cambios en archivos
        self.observer = Observer()
        self.config_handler = ConfigChangeHandler(self)
        
        # Inicializar
        self.ensure_config_directory()
        self.load_config()
        self.start_watching()
    
    def ensure_config_directory(self):
        """Crea directorio de configuración si no existe"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"📁 Directorio de configuración: {self.config_dir}")
    
    def load_config(self):
        """Carga configuración desde archivos"""
        try:
            # Cargar configuración principal
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                self._apply_config_data(config_data)
                self.logger.info(f"✅ Configuración cargada desde: {self.config_path}")
            else:
                self.logger.info("📝 Archivo de configuración no existe, creando configuración por defecto")
                self.save_default_config()
            
            # Cargar configuraciones específicas
            self.load_model_configs()
            self.load_environment_variables()
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando configuración: {e}")
            self.logger.info("🔄 Usando configuración por defecto")
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Aplica datos de configuración a los objetos internos"""
        # Sistema
        if 'system' in config_data:
            system_data = config_data['system']
            self.system = SystemConfig(**system_data)
        
        # Predicciones
        if 'prediction' in config_data:
            pred_data = config_data['prediction']
            self.prediction = PredictionConfig(**pred_data)
        
        # Rendimiento
        if 'performance' in config_data:
            perf_data = config_data['performance']
            self.performance = PerformanceConfig(**perf_data)
        
        # Configuración personalizada
        if 'custom' in config_data:
            self.custom = config_data['custom']
    
    def load_model_configs(self):
        """Carga configuraciones específicas de modelos"""
        model_config_path = self.config_dir / "models.json"
        
        if model_config_path.exists():
            try:
                with open(model_config_path, 'r', encoding='utf-8') as f:
                    models_data = json.load(f)
                
                for model_name, model_data in models_data.items():
                    self.models[model_name] = ModelConfig(
                        name=model_name,
                        **model_data
                    )
                
                self.logger.info(f"🤖 Configuraciones de {len(self.models)} modelos cargadas")
                
            except Exception as e:
                self.logger.error(f"❌ Error cargando configuración de modelos: {e}")
        else:
            # Crear configuración por defecto de modelos
            self.create_default_model_config()
    
    def load_environment_variables(self):
        """Carga variables de entorno relevantes"""
        env_mappings = {
            'OMEGA_DEBUG': ('system.debug', bool),
            'OMEGA_LOG_LEVEL': ('system.log_level', str),
            'OMEGA_TARGET_COUNT': ('prediction.target_count', int),
            'OMEGA_MAX_WORKERS': ('performance.max_workers', int),
            'OMEGA_CACHE_ENABLED': ('performance.cache_enabled', bool)
        }
        
        for env_var, (config_path, type_func) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    typed_value = type_func(value) if type_func != bool else value.lower() == 'true'
                    self.set_config_value(config_path, typed_value)
                    self.logger.info(f"🌍 Variable de entorno aplicada: {env_var}={typed_value}")
                except ValueError as e:
                    self.logger.warning(f"⚠️ Error procesando {env_var}: {e}")
    
    def set_config_value(self, path: str, value: Any):
        """Establece valor de configuración usando notación de punto"""
        parts = path.split('.')
        if len(parts) == 2:
            section, key = parts
            if hasattr(self, section):
                section_obj = getattr(self, section)
                if hasattr(section_obj, key):
                    setattr(section_obj, key, value)
    
    def get_config_value(self, path: str, default: Any = None) -> Any:
        """Obtiene valor de configuración usando notación de punto"""
        parts = path.split('.')
        if len(parts) == 2:
            section, key = parts
            if hasattr(self, section):
                section_obj = getattr(self, section)
                return getattr(section_obj, key, default)
        elif len(parts) == 1:
            return self.custom.get(parts[0], default)
        
        return default
    
    def create_default_model_config(self):
        """Crea configuración por defecto de modelos"""
        default_models = {
            "neural_enhanced": {
                "enabled": True,
                "weight": 0.45,
                "params": {"epochs": 60, "learning_rate": 0.002},
                "lazy_loading": True
            },
            "transformer_deep": {
                "enabled": True,
                "weight": 0.15,
                "params": {"attention_heads": 8, "layers": 6},
                "lazy_loading": True
            },
            "lstm_v2": {
                "enabled": True,
                "weight": 0.12,
                "params": {"hidden_size": 256, "num_layers": 3},
                "lazy_loading": True
            },
            "genetic": {
                "enabled": True,
                "weight": 0.15,
                "params": {"population_size": 100, "generations": 50},
                "lazy_loading": True
            },
            "clustering": {
                "enabled": True,
                "weight": 0.08,
                "params": {"n_clusters": 8, "method": "kmeans"},
                "lazy_loading": True
            },
            "montecarlo": {
                "enabled": True,
                "weight": 0.05,
                "params": {"simulations": 10000, "method": "adaptive"},
                "lazy_loading": True
            }
        }
        
        for name, config in default_models.items():
            self.models[name] = ModelConfig(name=name, **config)
        
        # Guardar configuración
        self.save_model_config()
    
    def save_default_config(self):
        """Guarda configuración por defecto"""
        config_data = {
            "system": asdict(self.system),
            "prediction": asdict(self.prediction),
            "performance": asdict(self.performance),
            "custom": self.custom
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 Configuración por defecto guardada en: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando configuración: {e}")
    
    def save_model_config(self):
        """Guarda configuración de modelos"""
        model_config_path = self.config_dir / "models.json"
        
        models_data = {}
        for name, config in self.models.items():
            models_data[name] = {
                "enabled": config.enabled,
                "weight": config.weight,
                "params": config.params,
                "lazy_loading": config.lazy_loading
            }
        
        try:
            with open(model_config_path, 'w', encoding='utf-8') as f:
                json.dump(models_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"🤖 Configuración de modelos guardada en: {model_config_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando configuración de modelos: {e}")
    
    def reload_config(self):
        """Recarga configuración desde archivos"""
        self.logger.info("🔄 Recargando configuración...")
        self.load_config()
    
    def start_watching(self):
        """Inicia observación de cambios en archivos de configuración"""
        try:
            self.observer.schedule(self.config_handler, str(self.config_dir), recursive=True)
            self.observer.start()
            self.logger.info(f"👁️ Observando cambios en: {self.config_dir}")
        except Exception as e:
            self.logger.warning(f"⚠️ No se pudo iniciar observador de archivos: {e}")
    
    def stop_watching(self):
        """Detiene observación de cambios"""
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            self.logger.info("🛑 Observador de configuración detenido")
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Obtiene configuración de un modelo específico"""
        return self.models.get(model_name)
    
    def get_enabled_models(self) -> Dict[str, ModelConfig]:
        """Obtiene todos los modelos habilitados"""
        return {name: config for name, config in self.models.items() if config.enabled}
    
    def update_model_weight(self, model_name: str, new_weight: float):
        """Actualiza peso de un modelo"""
        if model_name in self.models:
            self.models[model_name].weight = new_weight
            self.save_model_config()
            self.logger.info(f"⚖️ Peso actualizado para {model_name}: {new_weight}")
    
    def toggle_model(self, model_name: str, enabled: bool):
        """Habilita/deshabilita un modelo"""
        if model_name in self.models:
            self.models[model_name].enabled = enabled
            self.save_model_config()
            status = "habilitado" if enabled else "deshabilitado"
            self.logger.info(f"🔧 Modelo {model_name} {status}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de configuración actual"""
        return {
            "system": asdict(self.system),
            "prediction": asdict(self.prediction),
            "performance": asdict(self.performance),
            "models": {
                "total": len(self.models),
                "enabled": len([m for m in self.models.values() if m.enabled]),
                "disabled": len([m for m in self.models.values() if not m.enabled])
            },
            "config_path": str(self.config_path),
            "watching": self.observer.is_alive()
        }
    
    def __del__(self):
        """Cleanup al destruir objeto"""
        self.stop_watching()