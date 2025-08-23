#!/usr/bin/env python3
"""
🏭 OMEGA Model Registry - Registro y Lazy Loading de Modelos
Sistema optimizado para carga bajo demanda de modelos de IA
"""

import asyncio
import threading
import time
from typing import Dict, Any, Optional, Callable, Type
from abc import ABC, abstractmethod
from pathlib import Path
import pickle
import gzip
from datetime import datetime
import weakref

from src.utils.logger_factory import LoggerFactory, performance_monitor
from src.monitoring.metrics_collector import MetricsCollector
from src.core.config_manager import ConfigManager

class ModelInterface(ABC):
    """Interfaz base para todos los modelos"""
    
    @abstractmethod
    async def predict(self, data: Any, count: int = 8) -> list:
        """Genera predicciones"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Retorna versión del modelo"""
        pass
    
    @abstractmethod
    def get_training_date(self) -> str:
        """Retorna fecha de entrenamiento"""
        pass
    
    @abstractmethod
    def get_memory_usage(self) -> float:
        """Retorna uso de memoria en MB"""
        pass
    
    def cleanup(self):
        """Limpieza de recursos (opcional)"""
        pass

class LazyModelProxy:
    """Proxy para lazy loading de modelos"""
    
    def __init__(self, model_name: str, model_class: Type, registry: 'ModelRegistry'):
        self.model_name = model_name
        self.model_class = model_class
        self.registry = registry
        self._model_instance: Optional[ModelInterface] = None
        self._load_lock = threading.Lock()
        self._last_access = time.time()
        self.logger = LoggerFactory.get_logger(f"LazyModel_{model_name}")
    
    def _ensure_loaded(self) -> ModelInterface:
        """Asegura que el modelo esté cargado"""
        if self._model_instance is None:
            with self._load_lock:
                if self._model_instance is None:
                    self.logger.info(f"🔄 Lazy loading model: {self.model_name}")
                    start_time = time.time()
                    
                    try:
                        # Cargar configuración específica
                        config = self.registry.config_manager.get_model_config(self.model_name)
                        
                        # Instanciar modelo
                        self._model_instance = self.model_class(config)
                        
                        # Métricas
                        load_time = time.time() - start_time
                        self.registry.metrics.record_histogram(
                            "model_load_time_seconds", 
                            load_time,
                            labels={"model": self.model_name}
                        )
                        
                        self.logger.info(f"✅ Model {self.model_name} loaded in {load_time:.2f}s")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Failed to load model {self.model_name}: {e}")
                        raise
        
        self._last_access = time.time()
        return self._model_instance
    
    async def predict(self, data: Any, count: int = 8) -> list:
        """Proxy para predict con lazy loading"""
        model = self._ensure_loaded()
        return await model.predict(data, count)
    
    def get_version(self) -> str:
        """Proxy para get_version"""
        if self._model_instance:
            return self._model_instance.get_version()
        return "not_loaded"
    
    def get_training_date(self) -> str:
        """Proxy para get_training_date"""
        if self._model_instance:
            return self._model_instance.get_training_date()
        return "unknown"
    
    def get_memory_usage(self) -> float:
        """Proxy para get_memory_usage"""
        if self._model_instance:
            return self._model_instance.get_memory_usage()
        return 0.0
    
    def is_loaded(self) -> bool:
        """Verifica si el modelo está cargado"""
        return self._model_instance is not None
    
    def unload(self):
        """Descarga el modelo de memoria"""
        if self._model_instance:
            self.logger.info(f"💾 Unloading model: {self.model_name}")
            
            # Cleanup del modelo
            if hasattr(self._model_instance, 'cleanup'):
                self._model_instance.cleanup()
            
            self._model_instance = None
            
            self.registry.metrics.increment(
                "models_unloaded", 
                labels={"model": self.model_name}
            )
    
    def get_last_access_time(self) -> float:
        """Retorna tiempo del último acceso"""
        return self._last_access

class ModelCache:
    """Cache inteligente para modelos pre-entrenados"""
    
    def __init__(self, cache_dir: str = "models/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = LoggerFactory.get_logger("ModelCache")
        self._cache_index: Dict[str, Dict[str, Any]] = {}
        self._load_cache_index()
    
    def _get_cache_path(self, model_name: str, version: str) -> Path:
        """Obtiene path del cache para un modelo"""
        return self.cache_dir / f"{model_name}_{version}.pkl.gz"
    
    def _load_cache_index(self):
        """Carga índice de cache"""
        index_path = self.cache_dir / "cache_index.json"
        if index_path.exists():
            import json
            try:
                with open(index_path, 'r') as f:
                    self._cache_index = json.load(f)
                self.logger.info(f"📂 Cache index loaded: {len(self._cache_index)} entries")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load cache index: {e}")
    
    def _save_cache_index(self):
        """Guarda índice de cache"""
        index_path = self.cache_dir / "cache_index.json"
        import json
        try:
            with open(index_path, 'w') as f:
                json.dump(self._cache_index, f, indent=2)
        except Exception as e:
            self.logger.error(f"❌ Could not save cache index: {e}")
    
    @performance_monitor()
    def save_model(self, model_name: str, version: str, model_data: Any):
        """Guarda modelo en cache"""
        cache_path = self._get_cache_path(model_name, version)
        
        try:
            with gzip.open(cache_path, 'wb') as f:
                pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Actualizar índice
            self._cache_index[f"{model_name}_{version}"] = {
                "model_name": model_name,
                "version": version,
                "cached_at": datetime.now().isoformat(),
                "file_size": cache_path.stat().st_size
            }
            
            self._save_cache_index()
            self.logger.info(f"💾 Model cached: {model_name} v{version}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to cache model {model_name}: {e}")
    
    @performance_monitor()
    def load_model(self, model_name: str, version: str) -> Optional[Any]:
        """Carga modelo desde cache"""
        cache_path = self._get_cache_path(model_name, version)
        
        if not cache_path.exists():
            return None
        
        try:
            with gzip.open(cache_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.logger.info(f"📂 Model loaded from cache: {model_name} v{version}")
            return model_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load cached model {model_name}: {e}")
            return None
    
    def is_cached(self, model_name: str, version: str) -> bool:
        """Verifica si un modelo está en cache"""
        cache_key = f"{model_name}_{version}"
        return cache_key in self._cache_index
    
    def cleanup_old_cache(self, max_age_days: int = 30):
        """Limpia cache antiguo"""
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        
        removed_count = 0
        for key, info in list(self._cache_index.items()):
            cached_time = datetime.fromisoformat(info["cached_at"]).timestamp()
            
            if cached_time < cutoff_time:
                cache_path = self._get_cache_path(info["model_name"], info["version"])
                if cache_path.exists():
                    cache_path.unlink()
                
                del self._cache_index[key]
                removed_count += 1
        
        if removed_count > 0:
            self._save_cache_index()
            self.logger.info(f"🧹 Removed {removed_count} old cache entries")

class ModelRegistry:
    """
    Registro centralizado de modelos con lazy loading
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.metrics = MetricsCollector()
        self.logger = LoggerFactory.get_logger("ModelRegistry")
        
        # Registro de modelos
        self._model_classes: Dict[str, Type] = {}
        self._model_proxies: Dict[str, LazyModelProxy] = {}
        self._model_factories: Dict[str, Callable] = {}
        
        # Cache de modelos
        self.cache = ModelCache()
        
        # Configuración
        self.max_loaded_models = 3  # Máximo modelos en memoria simultáneamente
        self.auto_unload_timeout = 300  # 5 minutos sin uso
        
        # Thread para cleanup automático
        self._cleanup_thread = None
        self._cleanup_enabled = True
        self._start_cleanup_thread()
    
    def register_model_class(self, name: str, model_class: Type[ModelInterface]):
        """Registra una clase de modelo"""
        self._model_classes[name] = model_class
        self.logger.info(f"📝 Model class registered: {name}")
    
    def register_model_factory(self, name: str, factory_func: Callable):
        """Registra una factory function para modelo"""
        self._model_factories[name] = factory_func
        self.logger.info(f"🏭 Model factory registered: {name}")
    
    def get_model(self, name: str) -> LazyModelProxy:
        """Obtiene modelo (lazy loaded)"""
        if name not in self._model_proxies:
            if name not in self._model_classes and name not in self._model_factories:
                raise ValueError(f"Model {name} not registered")
            
            # Crear proxy lazy
            if name in self._model_classes:
                self._model_proxies[name] = LazyModelProxy(
                    name, self._model_classes[name], self
                )
            else:
                # Para factories, crear proxy especial
                self._model_proxies[name] = self._create_factory_proxy(name)
        
        return self._model_proxies[name]
    
    def _create_factory_proxy(self, name: str) -> LazyModelProxy:
        """Crea proxy para factory functions"""
        class FactoryModelAdapter(ModelInterface):
            def __init__(self, factory_func, config):
                self._model = factory_func(config)
            
            async def predict(self, data: Any, count: int = 8) -> list:
                if hasattr(self._model, 'predict'):
                    return await self._model.predict(data, count)
                elif callable(self._model):
                    return self._model(data, count)
                else:
                    raise NotImplementedError("Model doesn't support prediction")
            
            def get_version(self) -> str:
                return getattr(self._model, 'version', 'factory_1.0')
            
            def get_training_date(self) -> str:
                return getattr(self._model, 'training_date', '2025-01-01')
            
            def get_memory_usage(self) -> float:
                return getattr(self._model, 'memory_usage', 0.0)
        
        return LazyModelProxy(name, FactoryModelAdapter, self)
    
    def get_enabled_models(self) -> Dict[str, LazyModelProxy]:
        """Obtiene todos los modelos habilitados"""
        enabled_configs = self.config_manager.get_enabled_models()
        enabled_models = {}
        
        for model_name in enabled_configs.keys():
            if (model_name in self._model_classes or 
                model_name in self._model_factories):
                enabled_models[model_name] = self.get_model(model_name)
        
        return enabled_models
    
    def get_loaded_models(self) -> Dict[str, LazyModelProxy]:
        """Obtiene modelos actualmente cargados en memoria"""
        loaded = {}
        for name, proxy in self._model_proxies.items():
            if proxy.is_loaded():
                loaded[name] = proxy
        return loaded
    
    def get_model_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene estado de todos los modelos"""
        status = {}
        
        for name, proxy in self._model_proxies.items():
            status[name] = {
                "loaded": proxy.is_loaded(),
                "last_access": proxy.get_last_access_time(),
                "memory_usage_mb": proxy.get_memory_usage(),
                "version": proxy.get_version() if proxy.is_loaded() else "unknown",
                "config": self.config_manager.get_model_config(name)
            }
        
        return status
    
    def unload_model(self, name: str):
        """Descarga modelo específico"""
        if name in self._model_proxies:
            self._model_proxies[name].unload()
            self.logger.info(f"💾 Model {name} unloaded manually")
    
    def unload_all_models(self):
        """Descarga todos los modelos"""
        count = 0
        for proxy in self._model_proxies.values():
            if proxy.is_loaded():
                proxy.unload()
                count += 1
        
        self.logger.info(f"💾 {count} models unloaded")
    
    def _start_cleanup_thread(self):
        """Inicia thread para cleanup automático"""
        def cleanup_worker():
            while self._cleanup_enabled:
                try:
                    self._auto_cleanup()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    self.logger.error(f"Error in cleanup worker: {e}")
                    time.sleep(60)
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        self.logger.info("🧹 Cleanup thread started")
    
    def _auto_cleanup(self):
        """Cleanup automático de modelos no utilizados"""
        current_time = time.time()
        loaded_models = self.get_loaded_models()
        
        # Si hay demasiados modelos cargados, descargar los menos usados
        if len(loaded_models) > self.max_loaded_models:
            # Ordenar por último acceso
            sorted_models = sorted(
                loaded_models.items(),
                key=lambda x: x[1].get_last_access_time()
            )
            
            # Descargar los más antiguos
            models_to_unload = len(loaded_models) - self.max_loaded_models
            for i in range(models_to_unload):
                name, proxy = sorted_models[i]
                proxy.unload()
                self.logger.info(f"🧹 Auto-unloaded model {name} (LRU cleanup)")
        
        # Descargar modelos no utilizados recientemente
        for name, proxy in loaded_models.items():
            time_since_access = current_time - proxy.get_last_access_time()
            if time_since_access > self.auto_unload_timeout:
                proxy.unload()
                self.logger.info(f"🧹 Auto-unloaded model {name} (timeout)")
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Obtiene uso de memoria de todos los modelos"""
        usage = {}
        total = 0.0
        
        for name, proxy in self._model_proxies.items():
            if proxy.is_loaded():
                memory = proxy.get_memory_usage()
                usage[name] = memory
                total += memory
        
        usage['total'] = total
        return usage
    
    def optimize_memory(self):
        """Optimiza uso de memoria"""
        self.logger.info("🔧 Starting memory optimization")
        
        # Cleanup cache antiguo
        self.cache.cleanup_old_cache()
        
        # Descargar modelos no utilizados
        current_time = time.time()
        unloaded = []
        
        for name, proxy in self._model_proxies.items():
            if proxy.is_loaded():
                time_since_access = current_time - proxy.get_last_access_time()
                if time_since_access > 60:  # 1 minuto para optimización agresiva
                    proxy.unload()
                    unloaded.append(name)
        
        self.logger.info(f"🔧 Memory optimization complete: {len(unloaded)} models unloaded")
    
    def shutdown(self):
        """Cierre ordenado del registry"""
        self.logger.info("🔄 Shutting down model registry")
        
        # Detener cleanup thread
        self._cleanup_enabled = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        
        # Descargar todos los modelos
        self.unload_all_models()
        
        # Cleanup cache
        self.cache.cleanup_old_cache()
        
        self.logger.info("✅ Model registry shutdown complete")

# Decorador para auto-registro de modelos
def register_model(name: str, registry: ModelRegistry):
    """Decorador para registrar modelos automáticamente"""
    def decorator(model_class):
        registry.register_model_class(name, model_class)
        return model_class
    return decorator