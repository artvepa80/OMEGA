#!/usr/bin/env python3
"""
💾 OMEGA Cache Service - Sistema de Caché Inteligente con Redis
Caching optimizado para predicciones, SVI y datos temporales
"""

import asyncio
import json
import pickle
import hashlib
import time
import zlib
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
from dataclasses import asdict, is_dataclass
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis
    import redis.exceptions
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.utils.logger_factory import LoggerFactory, performance_monitor
from src.monitoring.metrics_collector import MetricsCollector

class CacheKey:
    """Generador de claves de cache estructuradas"""
    
    @staticmethod
    def prediction(model_name: str, data_hash: str, count: int) -> str:
        """Clave para predicciones"""
        return f"omega:pred:{model_name}:{data_hash}:{count}"
    
    @staticmethod
    def svi_score(combination: List[int]) -> str:
        """Clave para scores SVI"""
        combo_str = "_".join(map(str, sorted(combination)))
        return f"omega:svi:{combo_str}"
    
    @staticmethod
    def svi_batch(combinations_hash: str) -> str:
        """Clave para batch SVI"""
        return f"omega:svi_batch:{combinations_hash}"
    
    @staticmethod
    def historical_data(data_source: str, version: str) -> str:
        """Clave para datos históricos"""
        return f"omega:hist:{data_source}:{version}"
    
    @staticmethod
    def model_state(model_name: str, version: str) -> str:
        """Clave para estado de modelo"""
        return f"omega:model:{model_name}:{version}"
    
    @staticmethod
    def session_data(session_id: str, data_type: str) -> str:
        """Clave para datos de sesión"""
        return f"omega:session:{session_id}:{data_type}"
    
    @staticmethod
    def user_preferences(user_id: str) -> str:
        """Clave para preferencias de usuario"""
        return f"omega:user:{user_id}:prefs"

class CacheSerializer:
    """Serializador optimizado para diferentes tipos de datos"""
    
    @staticmethod
    def serialize(data: Any) -> bytes:
        """Serializa datos con compresión"""
        try:
            # Convertir dataclass a dict si es necesario
            if is_dataclass(data):
                data = asdict(data)
            
            # Serializar con pickle (más eficiente que JSON para objetos complejos)
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Comprimir si es beneficioso
            if len(serialized) > 1024:  # Comprimir solo si es > 1KB
                compressed = zlib.compress(serialized, level=6)
                if len(compressed) < len(serialized) * 0.9:  # Solo si ahorra >10%
                    return b'compressed:' + compressed
            
            return b'raw:' + serialized
            
        except Exception as e:
            # Fallback a JSON para casos especiales
            try:
                json_data = json.dumps(data, default=str).encode('utf-8')
                return b'json:' + json_data
            except:
                raise ValueError(f"Cannot serialize data: {e}")
    
    @staticmethod
    def deserialize(data: bytes) -> Any:
        """Deserializa datos"""
        if data.startswith(b'compressed:'):
            compressed_data = data[11:]  # Remove 'compressed:' prefix
            serialized = zlib.decompress(compressed_data)
            return pickle.loads(serialized)
        
        elif data.startswith(b'raw:'):
            serialized = data[4:]  # Remove 'raw:' prefix
            return pickle.loads(serialized)
        
        elif data.startswith(b'json:'):
            json_data = data[5:]  # Remove 'json:' prefix
            return json.loads(json_data.decode('utf-8'))
        
        else:
            # Legacy fallback
            try:
                return pickle.loads(data)
            except:
                return json.loads(data.decode('utf-8'))

class InMemoryCache:
    """Cache en memoria como fallback cuando Redis no está disponible"""
    
    def __init__(self, max_size: int = 10000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.logger = LoggerFactory.get_logger("InMemoryCache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtiene valor del cache"""
        if key in self._cache:
            entry = self._cache[key]
            
            # Verificar TTL
            if entry['expires_at'] > time.time():
                return entry['value']
            else:
                del self._cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Establece valor en cache"""
        # Limpiar cache si está lleno
        if len(self._cache) >= self.max_size:
            await self._cleanup_expired()
            
            if len(self._cache) >= self.max_size:
                # Remover 20% de entradas más antiguas
                sorted_keys = sorted(
                    self._cache.keys(), 
                    key=lambda k: self._cache[k]['created_at']
                )
                keys_to_remove = sorted_keys[:self.max_size // 5]
                for k in keys_to_remove:
                    del self._cache[k]
        
        ttl = ttl or self.default_ttl
        self._cache[key] = {
            'value': value,
            'created_at': time.time(),
            'expires_at': time.time() + ttl
        }
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Elimina clave del cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Verifica si existe una clave"""
        return await self.get(key) is not None
    
    async def _cleanup_expired(self):
        """Limpia entradas expiradas"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry['expires_at'] <= current_time
        ]
        
        for key in expired_keys:
            del self._cache[key]

class CacheService:
    """
    Servicio de caché inteligente con Redis y fallback en memoria
    """
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 enable_redis: bool = True,
                 default_ttl: int = 3600):
        
        self.redis_url = redis_url
        self.enable_redis = enable_redis and REDIS_AVAILABLE
        self.default_ttl = default_ttl
        
        self.logger = LoggerFactory.get_logger("CacheService")
        self.metrics = MetricsCollector()
        
        # Inicializar Redis
        self.redis_client: Optional[redis.Redis] = None
        self.redis_available = False
        
        # Fallback cache
        self.memory_cache = InMemoryCache(default_ttl=default_ttl)
        
        # Configuración
        self.cache_config = {
            'compression_threshold': 1024,  # Bytes
            'batch_size': 100,
            'max_key_length': 250,
            'enable_stats': True
        }
        
        # Inicializar conexión
        asyncio.create_task(self._initialize_redis())
    
    async def _initialize_redis(self):
        """Inicializa conexión a Redis"""
        if not self.enable_redis:
            self.logger.info("💾 Redis disabled, using memory cache only")
            return
        
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False,  # Mantener bytes para serialización
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            self.redis_available = True
            
            self.logger.info(f"✅ Redis connected: {self.redis_url}")
            self.metrics.set_gauge("cache_redis_available", 1)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Redis connection failed: {e}")
            self.logger.info("💾 Using memory cache as fallback")
            self.redis_available = False
            self.metrics.set_gauge("cache_redis_available", 0)
    
    @performance_monitor()
    async def get(self, key: str) -> Optional[Any]:
        """Obtiene valor del cache"""
        try:
            # Intentar Redis primero
            if self.redis_available:
                data = await self.redis_client.get(key)
                if data is not None:
                    self.metrics.increment("cache_hits", labels={"backend": "redis"})
                    return CacheSerializer.deserialize(data)
                else:
                    self.metrics.increment("cache_misses", labels={"backend": "redis"})
            
            # Fallback a memoria
            result = await self.memory_cache.get(key)
            if result is not None:
                self.metrics.increment("cache_hits", labels={"backend": "memory"})
                return result
            else:
                self.metrics.increment("cache_misses", labels={"backend": "memory"})
            
            return None
            
        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {e}")
            self.metrics.record_error("cache_get_error", str(e))
            return None
    
    @performance_monitor()
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Establece valor en cache"""
        ttl = ttl or self.default_ttl
        
        try:
            # Validar clave
            if len(key) > self.cache_config['max_key_length']:
                key = self._hash_key(key)
            
            serialized_data = CacheSerializer.serialize(value)
            
            # Intentar Redis primero
            if self.redis_available:
                try:
                    await self.redis_client.setex(key, ttl, serialized_data)
                    self.metrics.increment("cache_sets", labels={"backend": "redis"})
                    return True
                except Exception as e:
                    self.logger.warning(f"Redis set failed: {e}")
                    self.redis_available = False
            
            # Fallback a memoria
            success = await self.memory_cache.set(key, value, ttl)
            if success:
                self.metrics.increment("cache_sets", labels={"backend": "memory"})
            
            return success
            
        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {e}")
            self.metrics.record_error("cache_set_error", str(e))
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Obtiene múltiples valores del cache"""
        results = {}
        
        if self.redis_available and keys:
            try:
                # Hash keys si son muy largos
                processed_keys = [
                    self._hash_key(key) if len(key) > self.cache_config['max_key_length'] else key
                    for key in keys
                ]
                
                # Obtener en batch de Redis
                values = await self.redis_client.mget(processed_keys)
                
                for i, (original_key, value) in enumerate(zip(keys, values)):
                    if value is not None:
                        try:
                            results[original_key] = CacheSerializer.deserialize(value)
                            self.metrics.increment("cache_hits", labels={"backend": "redis"})
                        except Exception as e:
                            self.logger.warning(f"Deserialization error for {original_key}: {e}")
                    else:
                        self.metrics.increment("cache_misses", labels={"backend": "redis"})
                
            except Exception as e:
                self.logger.warning(f"Redis mget failed: {e}")
                self.redis_available = False
        
        # Fallback para keys no encontradas
        missing_keys = [key for key in keys if key not in results]
        for key in missing_keys:
            value = await self.memory_cache.get(key)
            if value is not None:
                results[key] = value
                self.metrics.increment("cache_hits", labels={"backend": "memory"})
            else:
                self.metrics.increment("cache_misses", labels={"backend": "memory"})
        
        return results
    
    async def set_many(self, items: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Establece múltiples valores en cache"""
        ttl = ttl or self.default_ttl
        
        try:
            if self.redis_available and items:
                # Preparar datos para Redis
                redis_data = {}
                for key, value in items.items():
                    processed_key = self._hash_key(key) if len(key) > self.cache_config['max_key_length'] else key
                    redis_data[processed_key] = CacheSerializer.serialize(value)
                
                # Usar pipeline para eficiencia
                async with self.redis_client.pipeline() as pipe:
                    pipe.mset(redis_data)
                    for key in redis_data.keys():
                        pipe.expire(key, ttl)
                    await pipe.execute()
                
                self.metrics.increment("cache_sets", value=len(items), labels={"backend": "redis"})
                return True
        
        except Exception as e:
            self.logger.warning(f"Redis mset failed: {e}")
            self.redis_available = False
        
        # Fallback a memoria
        success_count = 0
        for key, value in items.items():
            if await self.memory_cache.set(key, value, ttl):
                success_count += 1
        
        self.metrics.increment("cache_sets", value=success_count, labels={"backend": "memory"})
        return success_count == len(items)
    
    async def delete(self, key: str) -> bool:
        """Elimina clave del cache"""
        success = False
        
        if self.redis_available:
            try:
                processed_key = self._hash_key(key) if len(key) > self.cache_config['max_key_length'] else key
                deleted = await self.redis_client.delete(processed_key)
                success = deleted > 0
                if success:
                    self.metrics.increment("cache_deletes", labels={"backend": "redis"})
            except Exception as e:
                self.logger.warning(f"Redis delete failed: {e}")
        
        # También eliminar de memoria
        memory_success = await self.memory_cache.delete(key)
        if memory_success:
            self.metrics.increment("cache_deletes", labels={"backend": "memory"})
        
        return success or memory_success
    
    async def exists(self, key: str) -> bool:
        """Verifica si existe una clave"""
        if self.redis_available:
            try:
                processed_key = self._hash_key(key) if len(key) > self.cache_config['max_key_length'] else key
                return await self.redis_client.exists(processed_key) > 0
            except Exception as e:
                self.logger.warning(f"Redis exists failed: {e}")
        
        return await self.memory_cache.exists(key)
    
    def _hash_key(self, key: str) -> str:
        """Crea hash de clave larga"""
        return f"omega:hash:{hashlib.sha256(key.encode()).hexdigest()[:16]}"
    
    # Métodos especializados para casos de uso específicos
    
    async def cache_prediction(self, 
                             model_name: str, 
                             data_hash: str, 
                             count: int,
                             predictions: List[Dict],
                             ttl: int = 1800) -> bool:
        """Cache específico para predicciones (30 min TTL)"""
        key = CacheKey.prediction(model_name, data_hash, count)
        return await self.set(key, predictions, ttl)
    
    async def get_cached_prediction(self, 
                                  model_name: str, 
                                  data_hash: str, 
                                  count: int) -> Optional[List[Dict]]:
        """Obtiene predicción cacheada"""
        key = CacheKey.prediction(model_name, data_hash, count)
        return await self.get(key)
    
    async def cache_svi_score(self, 
                            combination: List[int], 
                            svi_score: float,
                            ttl: int = 7200) -> bool:
        """Cache para scores SVI individuales (2 horas TTL)"""
        key = CacheKey.svi_score(combination)
        return await self.set(key, svi_score, ttl)
    
    async def get_cached_svi_score(self, combination: List[int]) -> Optional[float]:
        """Obtiene score SVI cacheado"""
        key = CacheKey.svi_score(combination)
        return await self.get(key)
    
    async def cache_svi_batch(self, 
                            combinations: List[List[int]], 
                            scores: List[float],
                            ttl: int = 7200) -> bool:
        """Cache para batch de SVI scores"""
        # Crear hash de todas las combinaciones
        combo_str = json.dumps(combinations, sort_keys=True)
        combinations_hash = hashlib.sha256(combo_str.encode()).hexdigest()[:16]
        
        key = CacheKey.svi_batch(combinations_hash)
        
        # Guardar mapping de combinaciones a scores
        batch_data = {
            'combinations': combinations,
            'scores': scores,
            'cached_at': time.time()
        }
        
        # También cachear scores individuales
        for combo, score in zip(combinations, scores):
            await self.cache_svi_score(combo, score, ttl)
        
        return await self.set(key, batch_data, ttl)
    
    async def get_cached_svi_batch(self, combinations: List[List[int]]) -> Optional[List[float]]:
        """Obtiene batch de scores SVI si están todos cacheados"""
        scores = []
        
        # Intentar obtener scores individuales primero
        for combo in combinations:
            score = await self.get_cached_svi_score(combo)
            if score is None:
                return None  # Si falta alguno, no usar cache parcial
            scores.append(score)
        
        return scores
    
    @asynccontextmanager
    async def cache_context(self, prefix: str, ttl: int = 3600):
        """Context manager para cache con prefijo"""
        cache_data = {}
        
        class PrefixedCache:
            def __init__(self, service, prefix):
                self.service = service
                self.prefix = prefix
            
            async def get(self, key: str):
                full_key = f"{self.prefix}:{key}"
                return await self.service.get(full_key)
            
            async def set(self, key: str, value: Any, ttl: Optional[int] = None):
                full_key = f"{self.prefix}:{key}"
                return await self.service.set(full_key, value, ttl)
        
        try:
            yield PrefixedCache(self, prefix)
        finally:
            # Cleanup si es necesario
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache"""
        return {
            'redis_available': self.redis_available,
            'memory_cache_size': len(self.memory_cache._cache),
            'default_ttl': self.default_ttl,
            'metrics': {
                'hits': self.metrics.get_counter('cache_hits'),
                'misses': self.metrics.get_counter('cache_misses'),
                'sets': self.metrics.get_counter('cache_sets'),
                'deletes': self.metrics.get_counter('cache_deletes'),
                'errors': self.metrics.get_counter('cache_get_error') + self.metrics.get_counter('cache_set_error')
            }
        }
    
    async def clear_pattern(self, pattern: str):
        """Limpia claves que coinciden con patrón (solo Redis)"""
        if not self.redis_available:
            self.logger.warning("Pattern clear only supported with Redis")
            return 0
        
        try:
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await self.redis_client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    deleted_count += deleted
                
                if cursor == 0:
                    break
            
            self.logger.info(f"🧹 Cleared {deleted_count} keys matching pattern: {pattern}")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error clearing pattern {pattern}: {e}")
            return 0
    
    async def cleanup(self):
        """Limpieza de recursos"""
        self.logger.info("🔄 Cleaning up cache service")
        
        if self.redis_client:
            await self.redis_client.close()
        
        self.logger.info("✅ Cache service cleanup complete")