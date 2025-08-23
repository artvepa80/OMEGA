#!/usr/bin/env python3
"""
⚡ OMEGA Parallel Processor - Sistema de Procesamiento Paralelo Optimizado
Procesamiento concurrente inteligente con balanceado de carga y gestión de recursos
"""

import asyncio
import concurrent.futures
import multiprocessing as mp
import threading
import time
import psutil
from typing import List, Dict, Any, Callable, Optional, Union, Awaitable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from contextlib import asynccontextmanager
import functools

from src.utils.logger_factory import LoggerFactory, performance_monitor
from src.monitoring.metrics_collector import MetricsCollector

@dataclass
class TaskResult:
    """Resultado de tarea procesada"""
    task_id: str
    result: Any
    execution_time: float
    worker_id: str
    success: bool
    error: Optional[str] = None

@dataclass
class WorkerStats:
    """Estadísticas de worker"""
    worker_id: str
    tasks_completed: int
    total_execution_time: float
    average_task_time: float
    error_count: int
    cpu_usage: float
    memory_usage: float

class AdaptiveThreadPool:
    """Pool de threads adaptativo que se ajusta según carga"""
    
    def __init__(self, 
                 min_threads: int = 2,
                 max_threads: int = None,
                 queue_size: int = 1000):
        
        self.min_threads = min_threads
        self.max_threads = max_threads or min(32, (mp.cpu_count() or 1) + 4)
        self.queue_size = queue_size
        
        self.logger = LoggerFactory.get_logger("AdaptiveThreadPool")
        self.metrics = MetricsCollector()
        
        # Pool actual
        self._executor: Optional[ThreadPoolExecutor] = None
        self._current_threads = min_threads
        self._adjustment_lock = threading.Lock()
        
        # Métricas para adaptación
        self._task_queue_size = 0
        self._recent_execution_times = []
        self._last_adjustment = time.time()
        self._adjustment_interval = 30  # segundos
        
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Inicializa el pool de threads"""
        if self._executor:
            self._executor.shutdown(wait=False)
        
        self._executor = ThreadPoolExecutor(
            max_workers=self._current_threads,
            thread_name_prefix="omega_worker"
        )
        
        self.logger.info(f"⚡ Thread pool initialized: {self._current_threads} threads")
    
    async def submit_task(self, func: Callable, *args, **kwargs) -> TaskResult:
        """Envía tarea al pool con adaptación automática"""
        task_id = f"task_{time.time()}_{id(func)}"
        start_time = time.time()
        
        try:
            # Adaptar pool si es necesario
            await self._maybe_adapt_pool()
            
            # Enviar tarea
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self._executor, func, *args, **kwargs)
            
            execution_time = time.time() - start_time
            self._recent_execution_times.append(execution_time)
            
            # Mantener solo las últimas 100 mediciones
            if len(self._recent_execution_times) > 100:
                self._recent_execution_times = self._recent_execution_times[-100:]
            
            return TaskResult(
                task_id=task_id,
                result=result,
                execution_time=execution_time,
                worker_id=f"thread_{threading.current_thread().ident}",
                success=True
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Task execution failed: {e}")
            
            return TaskResult(
                task_id=task_id,
                result=None,
                execution_time=execution_time,
                worker_id="unknown",
                success=False,
                error=str(e)
            )
    
    async def _maybe_adapt_pool(self):
        """Adapta el tamaño del pool según métricas"""
        current_time = time.time()
        
        # Solo ajustar cada intervalo definido
        if current_time - self._last_adjustment < self._adjustment_interval:
            return
        
        with self._adjustment_lock:
            if current_time - self._last_adjustment < self._adjustment_interval:
                return  # Double-check locking
            
            # Calcular métricas
            avg_execution_time = (
                sum(self._recent_execution_times) / len(self._recent_execution_times)
                if self._recent_execution_times else 0
            )
            
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent
            
            # Decidir ajuste
            should_scale_up = (
                avg_execution_time > 0.5 and  # Tareas lentas
                cpu_usage < 80 and  # CPU disponible
                memory_usage < 85 and  # Memoria disponible
                self._current_threads < self.max_threads
            )
            
            should_scale_down = (
                avg_execution_time < 0.1 and  # Tareas rápidas
                cpu_usage < 50 and  # CPU subutilizada
                self._current_threads > self.min_threads
            )
            
            if should_scale_up:
                new_threads = min(self.max_threads, self._current_threads + 2)
                if new_threads != self._current_threads:
                    self._current_threads = new_threads
                    self._initialize_pool()
                    self.logger.info(f"🔝 Scaled up to {new_threads} threads")
                    self.metrics.set_gauge("thread_pool_size", new_threads)
            
            elif should_scale_down:
                new_threads = max(self.min_threads, self._current_threads - 1)
                if new_threads != self._current_threads:
                    self._current_threads = new_threads
                    self._initialize_pool()
                    self.logger.info(f"🔽 Scaled down to {new_threads} threads")
                    self.metrics.set_gauge("thread_pool_size", new_threads)
            
            self._last_adjustment = current_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del pool"""
        avg_time = (
            sum(self._recent_execution_times) / len(self._recent_execution_times)
            if self._recent_execution_times else 0
        )
        
        return {
            "current_threads": self._current_threads,
            "min_threads": self.min_threads,
            "max_threads": self.max_threads,
            "average_execution_time": avg_time,
            "recent_tasks": len(self._recent_execution_times),
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent
        }
    
    def shutdown(self, wait: bool = True):
        """Cierra el pool de threads"""
        if self._executor:
            self._executor.shutdown(wait=wait)
            self.logger.info("🔄 Thread pool shut down")

class AsyncBatchProcessor:
    """Procesador de lotes asíncrono optimizado"""
    
    def __init__(self, 
                 batch_size: int = 50,
                 max_concurrent_batches: int = 4,
                 timeout_seconds: int = 60):
        
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.timeout_seconds = timeout_seconds
        
        self.logger = LoggerFactory.get_logger("AsyncBatchProcessor")
        self.metrics = MetricsCollector()
        
        # Semáforo para limitar concurrencia
        self._semaphore = asyncio.Semaphore(max_concurrent_batches)
    
    async def process_batch(self, 
                          items: List[Any],
                          processor_func: Callable[[List[Any]], Awaitable[List[Any]]],
                          progress_callback: Optional[Callable] = None) -> List[Any]:
        """Procesa lista de items en lotes paralelos"""
        
        if not items:
            return []
        
        self.logger.info(f"⚡ Processing {len(items)} items in batches of {self.batch_size}")
        start_time = time.time()
        
        # Dividir en lotes
        batches = [items[i:i + self.batch_size] for i in range(0, len(items), self.batch_size)]
        
        # Procesar lotes de forma concurrente
        tasks = []
        for i, batch in enumerate(batches):
            task = self._process_single_batch(
                batch, processor_func, f"batch_{i}", progress_callback
            )
            tasks.append(task)
        
        # Ejecutar con timeout
        try:
            batch_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            self.logger.error(f"⏰ Batch processing timed out after {self.timeout_seconds}s")
            raise
        
        # Combinar resultados
        results = []
        error_count = 0
        
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                self.logger.error(f"Batch failed: {batch_result}")
                error_count += 1
            else:
                results.extend(batch_result)
        
        processing_time = time.time() - start_time
        
        self.metrics.record_histogram("batch_processing_time", processing_time)
        self.metrics.increment("batch_processing_completed")
        self.metrics.increment("batch_processing_errors", value=error_count)
        
        self.logger.info(
            f"✅ Batch processing complete: {len(results)} results, "
            f"{error_count} errors, {processing_time:.2f}s"
        )
        
        return results
    
    async def _process_single_batch(self,
                                  batch: List[Any],
                                  processor_func: Callable,
                                  batch_id: str,
                                  progress_callback: Optional[Callable]) -> List[Any]:
        """Procesa un lote individual"""
        
        async with self._semaphore:  # Limitar concurrencia
            try:
                self.logger.debug(f"🔄 Processing {batch_id}: {len(batch)} items")
                
                result = await processor_func(batch)
                
                if progress_callback:
                    await progress_callback(batch_id, len(batch), True)
                
                return result
                
            except Exception as e:
                self.logger.error(f"❌ Error processing {batch_id}: {e}")
                
                if progress_callback:
                    await progress_callback(batch_id, len(batch), False)
                
                raise

class ParallelModelProcessor:
    """Procesador paralelo específico para modelos de IA"""
    
    def __init__(self, thread_pool: AdaptiveThreadPool):
        self.thread_pool = thread_pool
        self.logger = LoggerFactory.get_logger("ParallelModelProcessor")
        self.metrics = MetricsCollector()
    
    async def run_models_parallel(self,
                                models: Dict[str, Any],
                                input_data: Any,
                                target_count: int) -> Dict[str, List[Dict]]:
        """Ejecuta múltiples modelos en paralelo"""
        
        self.logger.info(f"⚡ Running {len(models)} models in parallel")
        start_time = time.time()
        
        # Crear tareas para cada modelo
        tasks = []
        for model_name, model in models.items():
            task = self._run_single_model(model_name, model, input_data, target_count)
            tasks.append(task)
        
        # Ejecutar en paralelo
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(f"❌ Error in parallel model execution: {e}")
            raise
        
        # Procesar resultados
        model_results = {}
        success_count = 0
        
        for model_name, result in zip(models.keys(), results):
            if isinstance(result, Exception):
                self.logger.error(f"❌ Model {model_name} failed: {result}")
                self.metrics.record_error(f"model_execution_error_{model_name}", str(result))
            else:
                model_results[model_name] = result
                success_count += 1
                self.metrics.increment(f"model_executions_success", labels={"model": model_name})
        
        execution_time = time.time() - start_time
        
        self.metrics.record_histogram("parallel_model_execution_time", execution_time)
        self.metrics.set_gauge("parallel_models_success_rate", success_count / len(models))
        
        self.logger.info(
            f"✅ Parallel model execution complete: "
            f"{success_count}/{len(models)} successful, {execution_time:.2f}s"
        )
        
        return model_results
    
    async def _run_single_model(self,
                              model_name: str,
                              model: Any,
                              input_data: Any,
                              target_count: int) -> List[Dict]:
        """Ejecuta un modelo individual"""
        
        def sync_model_execution():
            """Función síncrona para ejecutar modelo"""
            try:
                if hasattr(model, 'predict') and asyncio.iscoroutinefunction(model.predict):
                    # Modelo asíncrono - ejecutar en loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(model.predict(input_data, target_count))
                    finally:
                        loop.close()
                else:
                    # Modelo síncrono
                    return model.predict(input_data, target_count)
                    
            except Exception as e:
                self.logger.error(f"Model {model_name} execution error: {e}")
                raise
        
        # Ejecutar en thread pool
        task_result = await self.thread_pool.submit_task(sync_model_execution)
        
        if not task_result.success:
            raise Exception(task_result.error)
        
        return task_result.result

class ParallelProcessor:
    """
    Procesador paralelo principal que combina todas las funcionalidades
    """
    
    def __init__(self, 
                 max_threads: int = None,
                 batch_size: int = 50,
                 enable_adaptive_scaling: bool = True):
        
        self.max_threads = max_threads
        self.batch_size = batch_size
        self.enable_adaptive_scaling = enable_adaptive_scaling
        
        self.logger = LoggerFactory.get_logger("ParallelProcessor")
        self.metrics = MetricsCollector()
        
        # Componentes
        self.thread_pool = AdaptiveThreadPool(
            max_threads=max_threads
        ) if enable_adaptive_scaling else None
        
        self.batch_processor = AsyncBatchProcessor(batch_size=batch_size)
        self.model_processor = ParallelModelProcessor(self.thread_pool)
        
        # Process pool para tareas CPU-intensivas
        self._process_pool: Optional[ProcessPoolExecutor] = None
        
        self.logger.info("⚡ ParallelProcessor initialized")
    
    @asynccontextmanager
    async def process_pool_context(self, max_workers: int = None):
        """Context manager para process pool"""
        max_workers = max_workers or mp.cpu_count()
        
        try:
            self._process_pool = ProcessPoolExecutor(max_workers=max_workers)
            self.logger.info(f"🏭 Process pool created: {max_workers} processes")
            yield self._process_pool
        finally:
            if self._process_pool:
                self._process_pool.shutdown(wait=True)
                self._process_pool = None
                self.logger.info("🔄 Process pool shut down")
    
    async def process_cpu_intensive_task(self,
                                       func: Callable,
                                       data_chunks: List[Any],
                                       max_processes: int = None) -> List[Any]:
        """Procesa tarea CPU-intensiva usando multiprocessing"""
        
        async with self.process_pool_context(max_processes) as pool:
            loop = asyncio.get_event_loop()
            
            # Crear tareas para cada chunk
            tasks = []
            for chunk in data_chunks:
                task = loop.run_in_executor(pool, func, chunk)
                tasks.append(task)
            
            # Ejecutar en paralelo
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filtrar errores
            successful_results = []
            error_count = 0
            
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Process task failed: {result}")
                    error_count += 1
                else:
                    successful_results.append(result)
            
            self.metrics.increment("cpu_intensive_tasks_completed")
            self.metrics.increment("cpu_intensive_task_errors", value=error_count)
            
            return successful_results
    
    async def parallel_map(self,
                         func: Callable,
                         items: List[Any],
                         chunk_size: int = None,
                         use_processes: bool = False) -> List[Any]:
        """Map paralelo con opción de threads o processes"""
        
        chunk_size = chunk_size or self.batch_size
        chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        
        if use_processes:
            # Usar multiprocessing para tareas CPU-intensivas
            def process_chunk(chunk):
                return [func(item) for item in chunk]
            
            chunk_results = await self.process_cpu_intensive_task(process_chunk, chunks)
            
            # Aplanar resultados
            results = []
            for chunk_result in chunk_results:
                results.extend(chunk_result)
            
            return results
        
        else:
            # Usar threads para I/O bound tasks
            async def process_chunk_async(chunk):
                chunk_results = []
                for item in chunk:
                    if self.thread_pool:
                        task_result = await self.thread_pool.submit_task(func, item)
                        if task_result.success:
                            chunk_results.append(task_result.result)
                        else:
                            self.logger.error(f"Task failed: {task_result.error}")
                    else:
                        chunk_results.append(func(item))
                return chunk_results
            
            return await self.batch_processor.process_batch(
                chunks, process_chunk_async
            )
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de procesamiento paralelo"""
        stats = {
            'cpu_count': mp.cpu_count(),
            'cpu_usage_percent': psutil.cpu_percent(interval=0.1),
            'memory': {
                'total_gb': psutil.virtual_memory().total / (1024**3),
                'available_gb': psutil.virtual_memory().available / (1024**3),
                'usage_percent': psutil.virtual_memory().percent
            },
            'batch_processor': {
                'batch_size': self.batch_processor.batch_size,
                'max_concurrent_batches': self.batch_processor.max_concurrent_batches
            }
        }
        
        if self.thread_pool:
            stats['thread_pool'] = self.thread_pool.get_stats()
        
        return stats
    
    @performance_monitor()
    async def optimize_performance(self):
        """Optimiza configuración basada en métricas del sistema"""
        self.logger.info("🔧 Optimizing parallel processing performance")
        
        system_stats = self.get_system_stats()
        cpu_usage = system_stats['cpu_usage_percent']
        memory_usage = system_stats['memory']['usage_percent']
        
        optimizations = []
        
        # Ajustar batch size según memoria
        if memory_usage > 85:
            new_batch_size = max(10, self.batch_size // 2)
            self.batch_processor.batch_size = new_batch_size
            optimizations.append(f"Reduced batch size to {new_batch_size}")
        
        elif memory_usage < 50:
            new_batch_size = min(200, self.batch_size * 2)
            self.batch_processor.batch_size = new_batch_size
            optimizations.append(f"Increased batch size to {new_batch_size}")
        
        # Log optimizaciones
        if optimizations:
            self.logger.info(f"⚡ Applied optimizations: {', '.join(optimizations)}")
        else:
            self.logger.info("⚡ No optimizations needed")
        
        return optimizations
    
    async def shutdown(self):
        """Cierra todos los recursos"""
        self.logger.info("🔄 Shutting down ParallelProcessor")
        
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        
        if self._process_pool:
            self._process_pool.shutdown(wait=True)
        
        self.logger.info("✅ ParallelProcessor shutdown complete")

# Decoradores utilitarios
def parallelize(processor: ParallelProcessor, chunk_size: int = None, use_processes: bool = False):
    """Decorador para paralelizar funciones automáticamente"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(items: List[Any], *args, **kwargs):
            if len(items) <= 1:
                return [func(item, *args, **kwargs) for item in items]
            
            # Crear función parcial con argumentos adicionales
            partial_func = functools.partial(func, *args, **kwargs)
            
            return await processor.parallel_map(
                partial_func, items, chunk_size, use_processes
            )
        
        return wrapper
    return decorator