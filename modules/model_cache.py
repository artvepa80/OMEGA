#!/usr/bin/env python3
"""
💾 OMEGA Model Cache Manager
Sistema de caché para modelos entrenados
"""

import os
import pickle
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ModelCacheManager:
    """Gestor de caché para modelos entrenados"""
    
    def __init__(self, cache_dir="models/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.load_metadata()
    
    def load_metadata(self):
        """Carga metadatos del caché"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
    
    def save_metadata(self):
        """Guarda metadatos del caché"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_cache_key(self, model_name, data_hash, params):
        """Genera clave única para el caché"""
        key_data = f"{model_name}_{data_hash}_{hash(str(sorted(params.items())))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def is_cached(self, cache_key):
        """Verifica si un modelo está en caché y es válido"""
        if cache_key not in self.metadata:
            return False
        
        cache_info = self.metadata[cache_key]
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        # Verificar que el archivo existe
        if not cache_file.exists():
            del self.metadata[cache_key]
            self.save_metadata()
            return False
        
        # Verificar que no ha expirado (24 horas)
        cached_time = datetime.fromisoformat(cache_info['timestamp'])
        if datetime.now() - cached_time > timedelta(hours=24):
            cache_file.unlink()
            del self.metadata[cache_key]
            self.save_metadata()
            return False
        
        return True
    
    def save_model(self, cache_key, model, model_info):
        """Guarda modelo en caché"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            with open(cache_file, 'wb') as f:
                pickle.dump(model, f)
            
            self.metadata[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'model_info': model_info,
                'file_size': cache_file.stat().st_size
            }
            
            self.save_metadata()
            logger.info(f"💾 Modelo guardado en caché: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando modelo en caché: {e}")
            return False
    
    def load_model(self, cache_key):
        """Carga modelo desde caché"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            with open(cache_file, 'rb') as f:
                model = pickle.load(f)
            
            logger.info(f"✅ Modelo cargado desde caché: {cache_key}")
            return model
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo desde caché: {e}")
            return None
    
    def clear_old_cache(self, hours=48):
        """Limpia caché antiguo"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        removed_count = 0
        
        for cache_key, info in list(self.metadata.items()):
            cached_time = datetime.fromisoformat(info['timestamp'])
            if cached_time < cutoff_time:
                cache_file = self.cache_dir / f"{cache_key}.pkl"
                if cache_file.exists():
                    cache_file.unlink()
                del self.metadata[cache_key]
                removed_count += 1
        
        if removed_count > 0:
            self.save_metadata()
            logger.info(f"🧹 Eliminados {removed_count} modelos antiguos del caché")
        
        return removed_count
    
    def get_cache_stats(self):
        """Obtiene estadísticas del caché"""
        total_files = len(self.metadata)
        total_size = sum(info.get('file_size', 0) for info in self.metadata.values())
        
        return {
            'total_models': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir)
        }
