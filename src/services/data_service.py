#!/usr/bin/env python3
"""
📊 OMEGA Data Service - Servicio Optimizado de Datos
Gestión de datos históricos con caché inteligente y procesamiento optimizado
"""

import asyncio
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

from src.services.cache_service import CacheService, CacheKey
from src.core.config_manager import ConfigManager
from src.utils.logger_factory import LoggerFactory, performance_monitor
from src.monitoring.metrics_collector import MetricsCollector

class DataService:
    """
    Servicio optimizado de datos con caché inteligente
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.cache_service = CacheService()
        self.logger = LoggerFactory.get_logger("DataService")
        self.metrics = MetricsCollector()
        
        # Configuración
        self.data_config = {
            'historical_data_path': 'data/historial_kabala_github_emergency_clean.csv',
            'optimal_records_count': 1000,
            'cache_ttl_historical': 7200,  # 2 horas
            'cache_ttl_svi': 3600,  # 1 hora
            'batch_size': 100,
            'svi_profiles': {
                'default': {'frequency_weight': 0.4, 'recency_weight': 0.3, 'pattern_weight': 0.3},
                'conservative': {'frequency_weight': 0.6, 'recency_weight': 0.3, 'pattern_weight': 0.1},
                'aggressive': {'frequency_weight': 0.2, 'recency_weight': 0.2, 'pattern_weight': 0.6},
                'neural_optimized': {'frequency_weight': 0.35, 'recency_weight': 0.35, 'pattern_weight': 0.3}
            }
        }
        
        # Cache de datos en memoria para acceso rápido
        self._historical_data_cache: Optional[pd.DataFrame] = None
        self._historical_data_version: Optional[str] = None
        self._frequency_cache: Optional[Dict] = None
        
        self.logger.info("📊 DataService inicializado")
    
    @performance_monitor()
    async def load_and_prepare_data(self) -> List[Dict]:
        """Carga y prepara datos históricos con caché"""
        try:
            # Verificar cache primero
            data_version = await self._get_data_version()
            cache_key = CacheKey.historical_data("main", data_version)
            
            cached_data = await self.cache_service.get(cache_key)
            if cached_data is not None:
                self.logger.debug("📂 Datos históricos obtenidos del caché")
                self.metrics.increment("data_cache_hits")
                return cached_data
            
            # Cargar desde archivo
            self.logger.info("📂 Cargando datos históricos desde archivo")
            historical_df = await self._load_historical_data()
            
            if historical_df is None or historical_df.empty:
                raise ValueError("No se pudieron cargar datos históricos")
            
            # Procesar y optimizar datos
            processed_data = await self._process_historical_data(historical_df)
            
            # Cachear datos procesados
            await self.cache_service.set(
                cache_key, 
                processed_data, 
                ttl=self.data_config['cache_ttl_historical']
            )
            
            self.metrics.increment("data_cache_misses")
            self.metrics.set_gauge("historical_data_records", len(processed_data))
            
            self.logger.info(f"✅ Datos históricos procesados: {len(processed_data)} registros")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando datos históricos: {e}")
            self.metrics.record_error("data_load_error", str(e))
            raise
    
    async def _get_data_version(self) -> str:
        """Genera versión de datos basada en timestamp del archivo"""
        try:
            data_path = Path(self.data_config['historical_data_path'])
            if data_path.exists():
                mtime = data_path.stat().st_mtime
                return f"v{int(mtime)}"
            else:
                return f"v{int(time.time())}"
        except:
            return f"v{int(time.time())}"
    
    async def _load_historical_data(self) -> Optional[pd.DataFrame]:
        """Carga datos históricos desde archivo"""
        data_path = self.data_config['historical_data_path']
        
        try:
            # Intentar múltiples paths
            possible_paths = [
                data_path,
                "data/historial_kabala_github.csv",
                "data/historial_kabala_github_fixed.csv"
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    df = pd.read_csv(path)
                    self.logger.info(f"📂 Datos cargados desde: {path}")
                    return df
            
            self.logger.error("❌ No se encontró ningún archivo de datos históricos")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error leyendo archivo CSV: {e}")
            return None
    
    async def _process_historical_data(self, df: pd.DataFrame) -> List[Dict]:
        """Procesa y optimiza datos históricos"""
        try:
            # Validar columnas requeridas
            required_columns = ['fecha', 'Bolilla 1', 'Bolilla 2', 'Bolilla 3', 
                              'Bolilla 4', 'Bolilla 5', 'Bolilla 6']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                # Intentar mapeo alternativo de columnas
                column_mapping = {
                    'bolilla_1': 'Bolilla 1',
                    'bolilla_2': 'Bolilla 2',
                    'bolilla_3': 'Bolilla 3',
                    'bolilla_4': 'Bolilla 4',
                    'bolilla_5': 'Bolilla 5',
                    'bolilla_6': 'Bolilla 6'
                }
                
                df = df.rename(columns=column_mapping)
                
                # Verificar nuevamente
                still_missing = [col for col in required_columns if col not in df.columns]
                if still_missing:
                    raise ValueError(f"Columnas faltantes: {still_missing}")
            
            # Limpiar y validar datos
            df = df.dropna(subset=required_columns)
            
            # Validar rangos de números
            for col in required_columns[1:]:  # Skip 'fecha'
                df = df[(df[col] >= 1) & (df[col] <= 40)]
            
            # Convertir fecha
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
            df = df.dropna(subset=['fecha'])
            
            # Ordenar por fecha (más reciente primero)
            df = df.sort_values('fecha', ascending=False)
            
            # Tomar solo los registros más recientes para optimizar performance
            optimal_count = self.data_config['optimal_records_count']
            if len(df) > optimal_count:
                df = df.head(optimal_count)
                self.logger.info(f"📊 Optimizado a {optimal_count} registros más recientes")
            
            # Convertir a lista de diccionarios para facilitar manipulación
            records = []
            for _, row in df.iterrows():
                record = {
                    'fecha': row['fecha'].isoformat(),
                    'combination': [
                        int(row['Bolilla 1']),
                        int(row['Bolilla 2']),
                        int(row['Bolilla 3']),
                        int(row['Bolilla 4']),
                        int(row['Bolilla 5']),
                        int(row['Bolilla 6'])
                    ]
                }
                records.append(record)
            
            # Actualizar cache interno
            self._historical_data_cache = df
            
            return records
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando datos históricos: {e}")
            raise
    
    @performance_monitor()
    async def calculate_svi_batch(self, combinations: List[List[int]], 
                                profile: str = "default") -> List[float]:
        """Calcula scores SVI en lote con caché optimizado"""
        try:
            # Verificar caché para combinaciones individuales
            cached_scores = await self.cache_service.get_cached_svi_batch(combinations)
            if cached_scores is not None:
                self.logger.debug(f"📊 SVI batch obtenido del caché: {len(combinations)} combinaciones")
                self.metrics.increment("svi_cache_hits")
                return cached_scores
            
            # Calcular scores individualmente
            self.logger.debug(f"📊 Calculando SVI batch: {len(combinations)} combinaciones")
            
            # Obtener datos de frecuencia si no están cacheados
            frequency_data = await self._get_frequency_data()
            
            # Calcular scores en paralelo (simulado con batch processing)
            scores = []
            profile_config = self.data_config['svi_profiles'].get(profile, 
                                                                self.data_config['svi_profiles']['default'])
            
            for combination in combinations:
                svi_score = await self._calculate_single_svi(combination, frequency_data, profile_config)
                scores.append(svi_score)
            
            # Cachear resultados
            await self.cache_service.cache_svi_batch(
                combinations, 
                scores, 
                ttl=self.data_config['cache_ttl_svi']
            )
            
            self.metrics.increment("svi_cache_misses")
            self.metrics.increment("svi_calculations", value=len(combinations))
            
            return scores
            
        except Exception as e:
            self.logger.error(f"❌ Error calculando SVI batch: {e}")
            self.metrics.record_error("svi_calculation_error", str(e))
            
            # Fallback: retornar scores por defecto
            return [0.5] * len(combinations)
    
    async def _get_frequency_data(self) -> Dict[str, Any]:
        """Obtiene datos de frecuencia de números"""
        if self._frequency_cache is not None:
            return self._frequency_cache
        
        # Verificar caché
        cache_key = "omega:frequency_data"
        cached_freq = await self.cache_service.get(cache_key)
        
        if cached_freq is not None:
            self._frequency_cache = cached_freq
            return cached_freq
        
        # Calcular frecuencias
        if self._historical_data_cache is None:
            await self.load_and_prepare_data()
        
        frequency_data = await self._calculate_frequency_data()
        
        # Cachear
        await self.cache_service.set(cache_key, frequency_data, ttl=3600)
        self._frequency_cache = frequency_data
        
        return frequency_data
    
    async def _calculate_frequency_data(self) -> Dict[str, Any]:
        """Calcula estadísticas de frecuencia de números"""
        try:
            if self._historical_data_cache is None:
                historical_data = await self.load_and_prepare_data()
                # Reconstruir DataFrame para cálculos
                combinations = [record['combination'] for record in historical_data]
            else:
                df = self._historical_data_cache
                combinations = []
                for _, row in df.iterrows():
                    combo = [row['Bolilla 1'], row['Bolilla 2'], row['Bolilla 3'], 
                            row['Bolilla 4'], row['Bolilla 5'], row['Bolilla 6']]
                    combinations.append(combo)
            
            # Calcular frecuencias individuales
            number_freq = {}
            pair_freq = {}
            total_combinations = len(combinations)
            
            for combo in combinations:
                # Frecuencias individuales
                for num in combo:
                    number_freq[num] = number_freq.get(num, 0) + 1
                
                # Frecuencias de pares
                for i in range(len(combo)):
                    for j in range(i + 1, len(combo)):
                        pair = tuple(sorted([combo[i], combo[j]]))
                        pair_freq[pair] = pair_freq.get(pair, 0) + 1
            
            # Normalizar frecuencias
            number_freq = {num: freq / total_combinations for num, freq in number_freq.items()}
            pair_freq = {pair: freq / total_combinations for pair, freq in pair_freq.items()}
            
            # Calcular estadísticas adicionales
            recent_combinations = combinations[:min(100, len(combinations))]  # Últimas 100
            recent_numbers = {}
            
            for combo in recent_combinations:
                for num in combo:
                    recent_numbers[num] = recent_numbers.get(num, 0) + 1
            
            return {
                'number_frequencies': number_freq,
                'pair_frequencies': pair_freq,
                'recent_numbers': recent_numbers,
                'total_combinations': total_combinations,
                'calculated_at': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error calculando frecuencias: {e}")
            return {
                'number_frequencies': {i: 1/40 for i in range(1, 41)},
                'pair_frequencies': {},
                'recent_numbers': {},
                'total_combinations': 0,
                'calculated_at': time.time()
            }
    
    async def _calculate_single_svi(self, combination: List[int], 
                                   frequency_data: Dict, 
                                   profile_config: Dict) -> float:
        """Calcula SVI score individual"""
        try:
            weights = profile_config
            number_freq = frequency_data.get('number_frequencies', {})
            pair_freq = frequency_data.get('pair_frequencies', {})
            recent_numbers = frequency_data.get('recent_numbers', {})
            
            # 1. Frequency Score (qué tan frecuentes son los números)
            freq_score = 0.0
            for num in combination:
                freq_score += number_freq.get(num, 1/40)
            freq_score /= len(combination)
            
            # 2. Recency Score (qué tan recientes son los números)
            recency_score = 0.0
            total_recent = sum(recent_numbers.values())
            if total_recent > 0:
                for num in combination:
                    recency_score += recent_numbers.get(num, 0) / total_recent
            else:
                recency_score = 0.5
            
            # 3. Pattern Score (patrones de pares)
            pattern_score = 0.0
            pair_count = 0
            
            for i in range(len(combination)):
                for j in range(i + 1, len(combination)):
                    pair = tuple(sorted([combination[i], combination[j]]))
                    pattern_score += pair_freq.get(pair, 0)
                    pair_count += 1
            
            if pair_count > 0:
                pattern_score /= pair_count
            
            # Combinar scores según perfil
            final_score = (
                freq_score * weights['frequency_weight'] +
                recency_score * weights['recency_weight'] +
                pattern_score * weights['pattern_weight']
            )
            
            # Normalizar a rango 0-1
            final_score = max(0.0, min(1.0, final_score))
            
            return final_score
            
        except Exception as e:
            self.logger.error(f"❌ Error calculando SVI individual: {e}")
            return 0.5  # Score neutral por defecto
    
    async def load_recent_predictions(self) -> List[Dict]:
        """Carga predicciones recientes para aprendizaje"""
        try:
            # Implementar carga desde base de datos o archivos
            # Por ahora, retorna lista vacía
            return []
        except Exception as e:
            self.logger.error(f"❌ Error cargando predicciones recientes: {e}")
            return []
    
    def get_health_status(self) -> str:
        """Obtiene estado de salud del servicio de datos"""
        try:
            data_path = Path(self.data_config['historical_data_path'])
            if not data_path.exists():
                return "unhealthy"
            
            # Verificar que los datos no sean muy antiguos
            mtime = datetime.fromtimestamp(data_path.stat().st_mtime)
            if datetime.now() - mtime > timedelta(days=30):
                return "degraded"
            
            return "healthy"
            
        except Exception as e:
            self.logger.error(f"Error checking health: {e}")
            return "unknown"
    
    @performance_monitor()
    async def get_data_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de los datos"""
        try:
            frequency_data = await self._get_frequency_data()
            
            stats = {
                'total_historical_records': frequency_data.get('total_combinations', 0),
                'data_version': await self._get_data_version(),
                'most_frequent_numbers': [],
                'least_frequent_numbers': [],
                'cache_stats': self.cache_service.get_stats(),
                'last_updated': frequency_data.get('calculated_at', 0)
            }
            
            # Números más y menos frecuentes
            number_freq = frequency_data.get('number_frequencies', {})
            if number_freq:
                sorted_numbers = sorted(number_freq.items(), key=lambda x: x[1], reverse=True)
                stats['most_frequent_numbers'] = sorted_numbers[:10]
                stats['least_frequent_numbers'] = sorted_numbers[-10:]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    async def refresh_data(self) -> bool:
        """Refresca datos y limpia caché"""
        try:
            self.logger.info("🔄 Refrescando datos...")
            
            # Limpiar caché interno
            self._historical_data_cache = None
            self._historical_data_version = None
            self._frequency_cache = None
            
            # Limpiar caché de servicio
            await self.cache_service.clear_pattern("omega:hist:*")
            await self.cache_service.clear_pattern("omega:svi*")
            await self.cache_service.delete("omega:frequency_data")
            
            # Recargar datos
            await self.load_and_prepare_data()
            
            self.logger.info("✅ Datos refrescados exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error refrescando datos: {e}")
            return False
    
    async def cleanup(self):
        """Limpieza de recursos"""
        self.logger.info("🔄 Cleaning up DataService")
        
        # Cleanup del cache service
        await self.cache_service.cleanup()
        
        # Limpiar caché interno
        self._historical_data_cache = None
        self._frequency_cache = None
        
        self.logger.info("✅ DataService cleanup complete")