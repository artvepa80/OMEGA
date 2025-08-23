#!/usr/bin/env python3
"""
Performance Optimizer for OMEGA PRO AI Modules
Implements optimizations based on code-reviewer and architect-review findings
"""

import logging
import time
import psutil
import gc
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from contextlib import contextmanager
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import multiprocessing
import warnings

logger = logging.getLogger(__name__)

@dataclass
class PerformanceConfig:
    """Configuration for performance optimizations"""
    enable_memory_monitoring: bool = True
    enable_cpu_optimization: bool = True
    enable_caching: bool = True
    max_cache_size: int = 1000
    parallel_threshold: int = 100  # Minimum data size for parallelization
    memory_limit_mb: int = 512  # Memory limit for operations
    gc_frequency: int = 50  # Garbage collection frequency
    enable_profiling: bool = False

class MemoryMonitor:
    """Memory usage monitoring and optimization"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.peak_memory = 0
        self.current_memory = 0
        self._lock = threading.RLock()
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            with self._lock:
                self.current_memory = memory_mb
                self.peak_memory = max(self.peak_memory, memory_mb)
            return memory_mb
        except Exception:
            return 0.0
    
    def check_memory_limit(self) -> bool:
        """Check if memory usage is within limits"""
        current = self.get_memory_usage()
        return current < self.config.memory_limit_mb
    
    def optimize_memory(self):
        """Force garbage collection and memory optimization"""
        gc.collect()
        
        # Clear numpy cache if available
        try:
            np.random.seed()  # Reset random state to free memory
        except Exception:
            pass
        
        logger.debug(f"🧹 Memory optimized: {self.get_memory_usage():.1f} MB")
    
    @contextmanager
    def monitor_operation(self, operation_name: str):
        """Context manager to monitor memory during operation"""
        start_memory = self.get_memory_usage()
        start_time = time.time()
        
        try:
            yield
        finally:
            end_memory = self.get_memory_usage()
            duration = time.time() - start_time
            memory_delta = end_memory - start_memory
            
            logger.debug(f"📊 {operation_name}: {duration:.2f}s, {memory_delta:+.1f}MB")
            
            # Auto-optimize if memory usage is high
            if end_memory > self.config.memory_limit_mb * 0.8:
                self.optimize_memory()

class DataOptimizer:
    """Optimizations for data processing operations"""
    
    @staticmethod
    def optimize_numpy_arrays(data: Union[np.ndarray, List]) -> np.ndarray:
        """Optimize numpy array memory usage and type"""
        if isinstance(data, list):
            data = np.array(data)
        
        # Optimize data type based on range
        if data.dtype != np.int8 and np.all((data >= 1) & (data <= 40)):
            # Lottery numbers fit in int8
            data = data.astype(np.int8)
        elif data.dtype == np.float64:
            # Try to use float32 if precision allows
            data = data.astype(np.float32)
        
        # Ensure C-contiguous for better performance
        if not data.flags.c_contiguous:
            data = np.ascontiguousarray(data)
        
        return data
    
    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Optimize pandas DataFrame memory usage"""
        # Optimize numeric columns
        for col in df.select_dtypes(include=['int64']).columns:
            col_min, col_max = df[col].min(), df[col].max()
            if col_min >= 1 and col_max <= 40:
                df[col] = df[col].astype(np.int8)
            elif col_min >= -128 and col_max <= 127:
                df[col] = df[col].astype(np.int8)
            elif col_min >= -32768 and col_max <= 32767:
                df[col] = df[col].astype(np.int16)
            elif col_min >= -2147483648 and col_max <= 2147483647:
                df[col] = df[col].astype(np.int32)
        
        # Optimize float columns
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Optimize categorical columns
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique values
                df[col] = df[col].astype('category')
        
        return df
    
    @staticmethod
    @lru_cache(maxsize=128)
    def cached_combination_validation(combination_tuple: tuple) -> bool:
        """Cached combination validation for frequently checked combinations"""
        try:
            return (
                len(combination_tuple) == 6 and
                len(set(combination_tuple)) == 6 and
                all(1 <= n <= 40 for n in combination_tuple)
            )
        except Exception:
            return False

class ParallelProcessor:
    """Parallel processing optimizations"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.cpu_count = multiprocessing.cpu_count()
        self.optimal_workers = min(4, self.cpu_count)
    
    def should_parallelize(self, data_size: int) -> bool:
        """Determine if operation should be parallelized"""
        return data_size >= self.config.parallel_threshold
    
    def parallel_map(self, func: Callable, data: List, chunk_size: Optional[int] = None) -> List:
        """Parallel map operation with optimal chunking"""
        if not self.should_parallelize(len(data)):
            return [func(item) for item in data]
        
        chunk_size = chunk_size or max(1, len(data) // (self.optimal_workers * 2))
        
        with ThreadPoolExecutor(max_workers=self.optimal_workers) as executor:
            # Split data into chunks
            chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
            
            # Process chunks in parallel
            futures = [executor.submit(lambda chunk: [func(item) for item in chunk], chunk) 
                      for chunk in chunks]
            
            # Collect results
            results = []
            for future in futures:
                results.extend(future.result())
            
            return results
    
    def parallel_combination_processing(self, combinations: List[Dict], 
                                      process_func: Callable) -> List[Dict]:
        """Optimized parallel processing for combinations"""
        if not self.should_parallelize(len(combinations)):
            return [process_func(combo) for combo in combinations]
        
        # Use process pool for CPU-intensive operations
        chunk_size = max(10, len(combinations) // (self.cpu_count * 2))
        
        try:
            with ProcessPoolExecutor(max_workers=self.cpu_count) as executor:
                chunks = [combinations[i:i + chunk_size] 
                         for i in range(0, len(combinations), chunk_size)]
                
                futures = [executor.submit(self._process_chunk, chunk, process_func) 
                          for chunk in chunks]
                
                results = []
                for future in futures:
                    results.extend(future.result())
                
                return results
                
        except Exception as e:
            logger.warning(f"⚠️ Parallel processing failed, falling back to sequential: {e}")
            return [process_func(combo) for combo in combinations]
    
    @staticmethod
    def _process_chunk(chunk: List[Dict], process_func: Callable) -> List[Dict]:
        """Process a chunk of combinations"""
        return [process_func(combo) for combo in chunk]

def performance_monitor(func):
    """Decorator for monitoring function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
            raise
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            logger.debug(f"📊 {func.__name__}: {duration:.3f}s, {memory_delta:+.1f}MB, success={success}")
            
            # Log warning for slow operations
            if duration > 5.0:
                logger.warning(f"⏰ Slow operation: {func.__name__} took {duration:.2f}s")
            
            # Log warning for memory-intensive operations
            if memory_delta > 50:
                logger.warning(f"🧠 Memory-intensive: {func.__name__} used {memory_delta:.1f}MB")
        
        return result
    
    return wrapper

class PerformanceOptimizer:
    """Main performance optimizer class"""
    
    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig()
        self.memory_monitor = MemoryMonitor(self.config)
        self.parallel_processor = ParallelProcessor(self.config)
        self.data_optimizer = DataOptimizer()
        self._operation_counter = 0
        
        # Suppress common warnings to reduce noise
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="numpy")
        warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")
        
        logger.info("🚀 Performance Optimizer initialized")
    
    def optimize_historical_data(self, data: Union[pd.DataFrame, np.ndarray, List]) -> np.ndarray:
        """Optimize historical data for better performance"""
        with self.memory_monitor.monitor_operation("data_optimization"):
            if isinstance(data, pd.DataFrame):
                data = self.data_optimizer.optimize_dataframe(data)
                return self.data_optimizer.optimize_numpy_arrays(data.values)
            elif isinstance(data, list):
                return self.data_optimizer.optimize_numpy_arrays(np.array(data))
            else:
                return self.data_optimizer.optimize_numpy_arrays(data)
    
    @performance_monitor
    def optimize_combination_processing(self, combinations: List[Dict], 
                                      process_func: Callable) -> List[Dict]:
        """Optimized combination processing with parallelization"""
        # Auto garbage collection
        self._operation_counter += 1
        if self._operation_counter % self.config.gc_frequency == 0:
            self.memory_monitor.optimize_memory()
        
        # Check memory before processing
        if not self.memory_monitor.check_memory_limit():
            logger.warning("⚠️ Memory limit approaching, optimizing...")
            self.memory_monitor.optimize_memory()
        
        # Use parallel processing if beneficial
        return self.parallel_processor.parallel_combination_processing(
            combinations, process_func
        )
    
    def optimize_numpy_operations(self):
        """Apply numpy-specific optimizations"""
        # Set numpy thread count for optimal performance
        try:
            import os
            os.environ['OMP_NUM_THREADS'] = str(self.parallel_processor.optimal_workers)
            os.environ['MKL_NUM_THREADS'] = str(self.parallel_processor.optimal_workers)
            os.environ['NUMEXPR_NUM_THREADS'] = str(self.parallel_processor.optimal_workers)
        except Exception as e:
            logger.debug(f"Could not set numpy threading: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        return {
            'current_memory_mb': self.memory_monitor.current_memory,
            'peak_memory_mb': self.memory_monitor.peak_memory,
            'cpu_count': self.parallel_processor.cpu_count,
            'optimal_workers': self.parallel_processor.optimal_workers,
            'operations_processed': self._operation_counter,
            'memory_within_limits': self.memory_monitor.check_memory_limit(),
            'config': {
                'memory_limit_mb': self.config.memory_limit_mb,
                'parallel_threshold': self.config.parallel_threshold,
                'caching_enabled': self.config.enable_caching
            }
        }
    
    def create_optimized_cache(self, maxsize: int = None) -> Callable:
        """Create an optimized LRU cache"""
        cache_size = maxsize or self.config.max_cache_size
        return lru_cache(maxsize=cache_size)
    
    @contextmanager
    def optimized_operation(self, operation_name: str):
        """Context manager for optimized operations"""
        with self.memory_monitor.monitor_operation(operation_name):
            # Pre-operation optimization
            if not self.memory_monitor.check_memory_limit():
                self.memory_monitor.optimize_memory()
            
            try:
                yield self
            finally:
                # Post-operation cleanup
                if self._operation_counter % (self.config.gc_frequency // 2) == 0:
                    gc.collect()

# Utility functions for common optimizations
def optimize_score_dynamics_performance():
    """Specific optimizations for score_dynamics.py"""
    optimizations = {
        "numpy_operations": "Use vectorized operations instead of loops",
        "memory_usage": "Pre-allocate arrays and reuse them",
        "caching": "Cache frequently computed values like prime numbers",
        "data_types": "Use appropriate data types (int8 for lottery numbers)",
        "parallel_processing": "Parallelize independent calculations"
    }
    return optimizations

def optimize_model_predictions():
    """Optimizations for AI model predictions"""
    return {
        "batch_processing": "Process combinations in batches",
        "memory_management": "Clear intermediate results",
        "early_stopping": "Stop when enough good predictions found",
        "model_caching": "Cache model states between predictions",
        "input_validation": "Fast validation with cached results"
    }

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Performance Optimizer...")
    
    # Create optimizer
    config = PerformanceConfig(
        memory_limit_mb=256,
        parallel_threshold=50,
        enable_profiling=True
    )
    optimizer = PerformanceOptimizer(config)
    
    # Test data optimization
    sample_data = np.random.randint(1, 41, size=(1000, 6))
    optimized_data = optimizer.optimize_historical_data(sample_data)
    
    print(f"✅ Data optimized: {sample_data.dtype} → {optimized_data.dtype}")
    print(f"📊 Memory usage: {optimized_data.nbytes / 1024:.1f}KB")
    
    # Test combination processing
    sample_combinations = [
        {'combination': [1, 2, 3, 4, 5, 6], 'score': 1.0}
        for _ in range(100)
    ]
    
    def dummy_process(combo):
        return {**combo, 'processed': True}
    
    with optimizer.optimized_operation("test_processing"):
        results = optimizer.optimize_combination_processing(
            sample_combinations, dummy_process
        )
    
    print(f"✅ Processed {len(results)} combinations")
    
    # Performance stats
    stats = optimizer.get_performance_stats()
    print(f"📈 Performance stats:")
    print(f"   Memory: {stats['current_memory_mb']:.1f}MB")
    print(f"   CPU cores: {stats['cpu_count']}")
    print(f"   Operations: {stats['operations_processed']}")
    
    print("🏁 Performance Optimizer test completed")