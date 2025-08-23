#!/usr/bin/env python3
"""
⚡ Performance Benchmarks para OMEGA Pro AI
"""

import pytest
import asyncio
import time
import psutil
import os
from typing import Dict, Any
from unittest.mock import Mock, patch
import statistics

from src.core.orchestrator import OmegaOrchestrator
from src.utils.parallel_processor import ParallelProcessor
from src.services.cache_service import CacheService

@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Benchmarks de performance del sistema"""
    
    @pytest.fixture
    def performance_targets(self) -> Dict[str, float]:
        """Targets de performance esperados"""
        return {
            'prediction_time_max': 3.0,  # segundos
            'memory_usage_max': 200.0,   # MB
            'cache_hit_rate_min': 0.8,   # 80%
            'concurrent_users_min': 10,  # usuarios simultáneos
            'throughput_min': 5.0        # predicciones por segundo
        }
    
    @pytest.mark.asyncio
    async def test_single_prediction_performance(self, performance_targets):
        """Benchmark de predicción individual"""
        with patch('src.core.config_manager.ConfigManager'):
            orchestrator = OmegaOrchestrator()
            
            try:
                # Warmup
                await orchestrator.run_prediction_cycle(top_n=1)
                
                # Benchmark
                times = []
                for _ in range(5):
                    start_time = time.time()
                    result = await orchestrator.run_prediction_cycle(top_n=8)
                    execution_time = time.time() - start_time
                    times.append(execution_time)
                    
                    assert len(result['predictions']) == 8
                
                avg_time = statistics.mean(times)
                p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
                
                print(f"📊 Prediction Performance:")
                print(f"   Average: {avg_time:.2f}s")
                print(f"   P95: {p95_time:.2f}s")
                print(f"   Target: <{performance_targets['prediction_time_max']}s")
                
                assert avg_time < performance_targets['prediction_time_max']
                assert p95_time < performance_targets['prediction_time_max'] * 1.5
                
            finally:
                await orchestrator.shutdown_gracefully()
    
    @pytest.mark.asyncio
    async def test_memory_usage_benchmark(self, performance_targets):
        """Benchmark de uso de memoria"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch('src.core.config_manager.ConfigManager'):
            orchestrator = OmegaOrchestrator()
            
            try:
                # Ejecutar múltiples ciclos para verificar memory leaks
                memory_measurements = []
                
                for i in range(10):
                    await orchestrator.run_prediction_cycle(top_n=5)
                    
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - initial_memory
                    memory_measurements.append(memory_increase)
                    
                    # Log cada 3 iteraciones
                    if (i + 1) % 3 == 0:
                        print(f"   Iteration {i+1}: +{memory_increase:.1f}MB")
                
                max_memory_increase = max(memory_measurements)
                final_memory_increase = memory_measurements[-1]
                
                print(f"📊 Memory Usage:")
                print(f"   Max increase: {max_memory_increase:.1f}MB")
                print(f"   Final increase: {final_memory_increase:.1f}MB")
                print(f"   Target: <{performance_targets['memory_usage_max']}MB")
                
                assert max_memory_increase < performance_targets['memory_usage_max']
                
                # Verificar que no haya memory leaks significativos
                # (final no debe ser más del 20% mayor que el máximo)
                assert final_memory_increase <= max_memory_increase * 1.2
                
            finally:
                await orchestrator.shutdown_gracefully()
    
    @pytest.mark.asyncio
    async def test_cache_performance_benchmark(self, performance_targets):
        """Benchmark de performance del cache"""
        cache_service = CacheService(enable_redis=False)
        
        try:
            # Test cache warming
            test_data = []
            for i in range(100):
                combination = [1 + (i % 40), 2 + (i % 39), 3 + (i % 38), 
                              4 + (i % 37), 5 + (i % 36), 6 + (i % 35)]
                test_data.append((f"svi_{i}", combination, 0.5 + (i % 50) / 100))
            
            # Warm up cache
            for key, combination, score in test_data:
                await cache_service.cache_svi_score(combination, score)
            
            # Benchmark cache hits
            hit_count = 0
            total_requests = 0
            cache_times = []
            
            for key, combination, expected_score in test_data:
                start_time = time.time()
                cached_score = await cache_service.get_cached_svi_score(combination)
                cache_time = (time.time() - start_time) * 1000  # ms
                
                cache_times.append(cache_time)
                total_requests += 1
                
                if cached_score is not None:
                    hit_count += 1
                    assert cached_score == expected_score
            
            hit_rate = hit_count / total_requests
            avg_cache_time = statistics.mean(cache_times)
            p95_cache_time = statistics.quantiles(cache_times, n=20)[18]
            
            print(f"📊 Cache Performance:")
            print(f"   Hit rate: {hit_rate:.1%}")
            print(f"   Average time: {avg_cache_time:.2f}ms")
            print(f"   P95 time: {p95_cache_time:.2f}ms")
            print(f"   Target hit rate: >{performance_targets['cache_hit_rate_min']:.0%}")
            
            assert hit_rate >= performance_targets['cache_hit_rate_min']
            assert avg_cache_time < 1.0  # Less than 1ms average
            assert p95_cache_time < 5.0   # Less than 5ms P95
            
        finally:
            await cache_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_users_benchmark(self, performance_targets):
        """Benchmark de usuarios concurrentes"""
        with patch('src.core.config_manager.ConfigManager'):
            orchestrator = OmegaOrchestrator()
            
            try:
                async def simulate_user(user_id: int):
                    """Simula un usuario haciendo predicciones"""
                    try:
                        start_time = time.time()
                        result = await orchestrator.run_prediction_cycle(top_n=3)
                        execution_time = time.time() - start_time
                        
                        return {
                            'user_id': user_id,
                            'success': True,
                            'time': execution_time,
                            'predictions': len(result['predictions'])
                        }
                    except Exception as e:
                        return {
                            'user_id': user_id,
                            'success': False,
                            'error': str(e),
                            'time': 0
                        }
                
                # Test incremental de concurrencia
                for concurrent_users in [5, 10, 15, 20]:
                    print(f"\n🔄 Testing {concurrent_users} concurrent users...")
                    
                    start_time = time.time()
                    
                    # Crear tareas concurrentes
                    tasks = [simulate_user(i) for i in range(concurrent_users)]
                    results = await asyncio.gather(*tasks)
                    
                    total_time = time.time() - start_time
                    
                    # Analizar resultados
                    successful = [r for r in results if r['success']]
                    failed = [r for r in results if not r['success']]
                    
                    success_rate = len(successful) / len(results)
                    avg_response_time = statistics.mean([r['time'] for r in successful]) if successful else 0
                    throughput = len(successful) / total_time
                    
                    print(f"   Success rate: {success_rate:.1%}")
                    print(f"   Avg response time: {avg_response_time:.2f}s")
                    print(f"   Throughput: {throughput:.1f} req/s")
                    print(f"   Failed requests: {len(failed)}")
                    
                    # Assertions para targets mínimos
                    if concurrent_users <= performance_targets['concurrent_users_min']:
                        assert success_rate >= 0.9  # 90% success rate
                        assert avg_response_time <= performance_targets['prediction_time_max'] * 2
                    
                    if len(successful) > 0:
                        assert throughput >= performance_targets['throughput_min'] * 0.5  # 50% of target
                
            finally:
                await orchestrator.shutdown_gracefully()
    
    @pytest.mark.asyncio
    async def test_parallel_processing_benchmark(self):
        """Benchmark del sistema de procesamiento paralelo"""
        processor = ParallelProcessor(max_threads=8, batch_size=25)
        
        try:
            def cpu_intensive_task(n: int) -> int:
                """Tarea CPU-intensiva simulada"""
                result = 0
                for i in range(n * 1000):
                    result += i ** 0.5
                return int(result)
            
            # Test different workloads
            workloads = [100, 500, 1000, 2000]
            
            for workload_size in workloads:
                print(f"\n⚡ Testing parallel processing: {workload_size} tasks")
                
                # Sequential baseline
                start_time = time.time()
                sequential_results = [cpu_intensive_task(10) for _ in range(workload_size)]
                sequential_time = time.time() - start_time
                
                # Parallel execution
                start_time = time.time()
                parallel_results = await processor.parallel_map(
                    lambda _: cpu_intensive_task(10),
                    list(range(workload_size)),
                    chunk_size=50,
                    use_processes=False  # Use threads for this test
                )
                parallel_time = time.time() - start_time
                
                # Analysis
                speedup = sequential_time / parallel_time if parallel_time > 0 else 0
                efficiency = speedup / processor.max_threads
                
                print(f"   Sequential time: {sequential_time:.2f}s")
                print(f"   Parallel time: {parallel_time:.2f}s")
                print(f"   Speedup: {speedup:.2f}x")
                print(f"   Efficiency: {efficiency:.1%}")
                
                assert len(parallel_results) == workload_size
                assert speedup >= 1.5  # At least 1.5x speedup
                assert efficiency >= 0.3  # At least 30% efficiency
                
        finally:
            await processor.shutdown()
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_stress_test(self, performance_targets):
        """Stress test del sistema completo"""
        with patch('src.core.config_manager.ConfigManager'):
            orchestrator = OmegaOrchestrator()
            
            try:
                print("\n🔥 Starting stress test...")
                
                # Warmup
                await orchestrator.run_prediction_cycle(top_n=1)
                
                # Metrics collection
                total_requests = 0
                successful_requests = 0
                total_time = 0
                errors = []
                
                # Stress test: 100 requests over 2 minutes
                test_duration = 120  # seconds
                target_requests = 100
                
                start_time = time.time()
                
                while time.time() - start_time < test_duration and total_requests < target_requests:
                    try:
                        request_start = time.time()
                        
                        result = await orchestrator.run_prediction_cycle(
                            top_n=5,
                            enable_learning=False
                        )
                        
                        request_time = time.time() - request_start
                        total_time += request_time
                        total_requests += 1
                        successful_requests += 1
                        
                        # Validate result
                        assert len(result['predictions']) == 5
                        
                        # Small delay to avoid overwhelming
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        total_requests += 1
                        errors.append(str(e))
                        await asyncio.sleep(0.5)  # Longer delay on error
                
                elapsed_time = time.time() - start_time
                
                # Analysis
                success_rate = successful_requests / total_requests if total_requests > 0 else 0
                avg_response_time = total_time / successful_requests if successful_requests > 0 else 0
                throughput = successful_requests / elapsed_time
                
                print(f"📊 Stress Test Results:")
                print(f"   Duration: {elapsed_time:.1f}s")
                print(f"   Total requests: {total_requests}")
                print(f"   Successful: {successful_requests}")
                print(f"   Success rate: {success_rate:.1%}")
                print(f"   Average response time: {avg_response_time:.2f}s")
                print(f"   Throughput: {throughput:.2f} req/s")
                print(f"   Errors: {len(errors)}")
                
                # Stress test assertions (more lenient)
                assert success_rate >= 0.8  # 80% under stress
                assert avg_response_time <= performance_targets['prediction_time_max'] * 3
                assert throughput >= 0.5  # At least 0.5 req/s under stress
                
            finally:
                await orchestrator.shutdown_gracefully()

@pytest.fixture(scope="session")
def benchmark_report():
    """Fixture para generar reporte de benchmarks"""
    results = []
    
    yield results
    
    # Generate benchmark report
    if results:
        print("\n" + "="*60)
        print("📊 BENCHMARK REPORT SUMMARY")
        print("="*60)
        
        for result in results:
            print(f"{result['test']}: {result['status']}")
            for metric, value in result.get('metrics', {}).items():
                print(f"  {metric}: {value}")
        
        print("="*60)