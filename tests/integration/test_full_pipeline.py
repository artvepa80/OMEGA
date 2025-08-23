#!/usr/bin/env python3
"""
🧪 Tests de Integración Completos para OMEGA Pipeline
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import pandas as pd
import numpy as np

from src.core.orchestrator import OmegaOrchestrator
from src.core.pipeline import PredictionPipeline
from src.services.data_service import DataService
from src.ai.ensemble_manager import EnsembleManager
from src.services.cache_service import CacheService

@pytest.mark.integration
class TestFullPipeline:
    """Tests de integración del pipeline completo"""
    
    @pytest.fixture
    async def orchestrator(self):
        """Fixture de orchestrator configurado para testing"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            # Configuración mock
            mock_config.return_value.get_enabled_models.return_value = {
                'neural_enhanced': Mock(weight=0.6),
                'lstm_v2': Mock(weight=0.4)
            }
            
            orchestrator = OmegaOrchestrator()
            yield orchestrator
            await orchestrator.shutdown_gracefully()
    
    @pytest.mark.asyncio
    async def test_complete_prediction_flow(self, orchestrator):
        """Test del flujo completo de predicción"""
        # Ejecutar ciclo de predicción
        results = await orchestrator.run_prediction_cycle(
            top_n=3,
            enable_learning=False
        )
        
        # Validar resultados
        assert 'predictions' in results
        assert 'session_id' in results
        assert 'metrics' in results
        assert len(results['predictions']) <= 3
        
        # Validar cada predicción
        for pred in results['predictions']:
            assert hasattr(pred, 'combination')
            assert len(pred.combination) == 6
            assert all(1 <= n <= 40 for n in pred.combination)
            assert 0 <= pred.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_data_service_integration(self):
        """Test de integración del servicio de datos"""
        with patch('src.core.config_manager.ConfigManager'):
            data_service = DataService(Mock())
            
            # Mock de datos históricos
            with patch.object(data_service, '_load_historical_data') as mock_load:
                mock_df = pd.DataFrame({
                    'fecha': ['2025-01-01', '2025-01-02'],
                    'Bolilla 1': [1, 7],
                    'Bolilla 2': [15, 14],
                    'Bolilla 3': [23, 21],
                    'Bolilla 4': [31, 28],
                    'Bolilla 5': [35, 35],
                    'Bolilla 6': [40, 42]
                })
                mock_load.return_value = mock_df
                
                # Test carga de datos
                data = await data_service.load_and_prepare_data()
                
                assert len(data) == 2
                assert all('combination' in record for record in data)
                assert all('fecha' in record for record in data)
    
    @pytest.mark.asyncio
    async def test_cache_integration(self):
        """Test de integración del sistema de caché"""
        cache_service = CacheService(enable_redis=False)  # Solo memory para test
        
        # Test cache básico
        await cache_service.set("test_key", {"value": 123}, ttl=60)
        result = await cache_service.get("test_key")
        
        assert result == {"value": 123}
        
        # Test SVI cache
        combination = [1, 15, 23, 31, 35, 40]
        await cache_service.cache_svi_score(combination, 0.75)
        
        cached_score = await cache_service.get_cached_svi_score(combination)
        assert cached_score == 0.75
        
        await cache_service.cleanup()

@pytest.mark.performance
class TestPerformanceIntegration:
    """Tests de performance e integración"""
    
    @pytest.mark.asyncio
    async def test_prediction_performance(self):
        """Test de performance de predicciones"""
        import time
        
        with patch('src.core.config_manager.ConfigManager'):
            orchestrator = OmegaOrchestrator()
            
            try:
                start_time = time.time()
                
                results = await orchestrator.run_prediction_cycle(
                    top_n=5,
                    enable_learning=False
                )
                
                execution_time = time.time() - start_time
                
                # Debe completarse en menos de 5 segundos
                assert execution_time < 5.0
                assert len(results['predictions']) == 5
                
            finally:
                await orchestrator.shutdown_gracefully()
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test de uso de memoria"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch('src.core.config_manager.ConfigManager'):
            orchestrator = OmegaOrchestrator()
            
            try:
                # Ejecutar múltiples ciclos
                for _ in range(3):
                    await orchestrator.run_prediction_cycle(top_n=2)
                
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = final_memory - initial_memory
                
                # No debe aumentar más de 100MB
                assert memory_increase < 100
                
            finally:
                await orchestrator.shutdown_gracefully()

@pytest.mark.external
class TestExternalIntegration:
    """Tests que requieren servicios externos"""
    
    @pytest.mark.redis
    @pytest.mark.asyncio
    async def test_redis_integration(self):
        """Test de integración con Redis (requiere Redis running)"""
        try:
            cache_service = CacheService(enable_redis=True)
            
            # Test conexión
            await cache_service._initialize_redis()
            
            if cache_service.redis_available:
                # Test operaciones Redis
                await cache_service.set("redis_test", {"data": "test"})
                result = await cache_service.get("redis_test")
                
                assert result == {"data": "test"}
                
                # Test batch operations
                batch_data = {
                    "key1": "value1",
                    "key2": {"nested": "value2"}
                }
                
                await cache_service.set_many(batch_data)
                batch_results = await cache_service.get_many(list(batch_data.keys()))
                
                assert batch_results == batch_data
                
            await cache_service.cleanup()
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")

class TestErrorHandling:
    """Tests de manejo de errores"""
    
    @pytest.mark.asyncio
    async def test_model_failure_handling(self):
        """Test manejo de fallos en modelos"""
        with patch('src.core.config_manager.ConfigManager'):
            orchestrator = OmegaOrchestrator()
            
            try:
                # Mock un modelo que falla
                with patch.object(orchestrator.ensemble_manager, 'get_model') as mock_get_model:
                    failing_model = Mock()
                    failing_model.predict = AsyncMock(side_effect=Exception("Model error"))
                    mock_get_model.return_value = failing_model
                    
                    # El sistema debe continuar funcionando
                    results = await orchestrator.run_prediction_cycle(top_n=2)
                    
                    # Debe retornar algo, aunque sea con modelos limitados
                    assert 'predictions' in results
                    
            finally:
                await orchestrator.shutdown_gracefully()
    
    @pytest.mark.asyncio
    async def test_data_corruption_handling(self):
        """Test manejo de datos corruptos"""
        with patch('src.core.config_manager.ConfigManager'):
            data_service = DataService(Mock())
            
            # Mock datos corruptos
            with patch.object(data_service, '_load_historical_data') as mock_load:
                # DataFrame con datos inválidos
                mock_df = pd.DataFrame({
                    'fecha': ['invalid_date', '2025-01-02'],
                    'Bolilla 1': [0, 7],  # 0 es inválido
                    'Bolilla 2': [50, 14],  # 50 es inválido
                    'Bolilla 3': [23, 21],
                    'Bolilla 4': [31, 28],
                    'Bolilla 5': [35, 35],
                    'Bolilla 6': [40, 42]
                })
                mock_load.return_value = mock_df
                
                # Debe manejar datos corruptos sin fallar
                data = await data_service.load_and_prepare_data()
                
                # Debe filtrar datos inválidos
                assert len(data) <= 1  # Solo el registro válido

class TestConcurrency:
    """Tests de concurrencia"""
    
    @pytest.mark.asyncio
    async def test_concurrent_predictions(self):
        """Test de predicciones concurrentes"""
        with patch('src.core.config_manager.ConfigManager'):
            orchestrator = OmegaOrchestrator()
            
            try:
                # Ejecutar múltiples predicciones concurrentemente
                tasks = []
                for i in range(3):
                    task = orchestrator.run_prediction_cycle(
                        top_n=2,
                        enable_learning=False
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Todas deben completarse exitosamente
                assert len(results) == 3
                assert all(not isinstance(r, Exception) for r in results)
                
                # Cada resultado debe ser válido
                for result in results:
                    assert 'predictions' in result
                    assert len(result['predictions']) == 2
                    
            finally:
                await orchestrator.shutdown_gracefully()
    
    @pytest.mark.asyncio
    async def test_cache_concurrency(self):
        """Test de concurrencia en cache"""
        cache_service = CacheService(enable_redis=False)
        
        async def cache_operation(key_suffix: int):
            key = f"concurrent_test_{key_suffix}"
            value = {"data": key_suffix}
            
            await cache_service.set(key, value)
            result = await cache_service.get(key)
            
            return result == value
        
        # Ejecutar operaciones concurrentes
        tasks = [cache_operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Todas deben ser exitosas
        assert all(results)
        
        await cache_service.cleanup()

# Fixtures globales para tests de integración
@pytest.fixture(scope="session")
def event_loop():
    """Event loop para tests async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup automático para ambiente de testing"""
    monkeypatch.setenv("OMEGA_ENV", "testing")
    monkeypatch.setenv("OMEGA_LOG_LEVEL", "ERROR")  # Reducir logs en tests