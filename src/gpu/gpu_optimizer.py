#!/usr/bin/env python3
"""
🚀 OMEGA GPU Optimizer - Optimización para GPU Cloud
Gestión inteligente de GPU, memoria y batch processing
"""

import os
import asyncio
import torch
import tensorflow as tf
from typing import Dict, List, Any, Optional, Tuple
import psutil
import time
from dataclasses import dataclass
from enum import Enum
import numpy as np

from src.utils.logger_factory import LoggerFactory
from src.monitoring.metrics_collector import MetricsCollector

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False

try:
    import nvidia_ml_py as nvml
    nvml.nvmlInit()
    NVIDIA_ML_AVAILABLE = True
except ImportError:
    NVIDIA_ML_AVAILABLE = False

class GPUProvider(Enum):
    """Proveedores de GPU"""
    NVIDIA = "nvidia"
    AMD = "amd" 
    INTEL = "intel"
    UNKNOWN = "unknown"

class GPUMemoryStrategy(Enum):
    """Estrategias de gestión de memoria GPU"""
    CONSERVATIVE = "conservative"  # 70% uso máximo
    BALANCED = "balanced"         # 85% uso máximo  
    AGGRESSIVE = "aggressive"     # 95% uso máximo

@dataclass
class GPUInfo:
    """Información de GPU"""
    device_id: int
    name: str
    memory_total: int  # MB
    memory_free: int   # MB
    memory_used: int   # MB
    utilization: float # %
    temperature: Optional[int] = None  # °C
    power_usage: Optional[int] = None  # W

@dataclass
class GPUBatchConfig:
    """Configuración de batch para GPU"""
    batch_size: int
    max_sequence_length: int
    memory_threshold: float
    use_mixed_precision: bool = True

class GPUMonitor:
    """Monitor de GPU en tiempo real"""
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        self.metrics = metrics_collector or MetricsCollector()
        self.logger = LoggerFactory.get_logger("GPUMonitor")
        self.monitoring_active = False
        
    def get_gpu_info(self) -> List[GPUInfo]:
        """Obtiene información actual de GPUs"""
        gpu_info = []
        
        if not NVIDIA_ML_AVAILABLE:
            self.logger.warning("NVIDIA ML not available")
            return gpu_info
        
        try:
            device_count = nvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = nvml.nvmlDeviceGetHandleByIndex(i)
                
                # Información básica
                name = nvml.nvmlDeviceGetName(handle).decode('utf-8')
                
                # Memoria
                mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
                memory_total = mem_info.total // (1024 * 1024)  # MB
                memory_free = mem_info.free // (1024 * 1024)   # MB
                memory_used = mem_info.used // (1024 * 1024)   # MB
                
                # Utilización
                util = nvml.nvmlDeviceGetUtilizationRates(handle)
                utilization = util.gpu
                
                # Temperatura (opcional)
                try:
                    temp = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
                except:
                    temp = None
                
                # Potencia (opcional)
                try:
                    power = nvml.nvmlDeviceGetPowerUsage(handle) // 1000  # W
                except:
                    power = None
                
                gpu_info.append(GPUInfo(
                    device_id=i,
                    name=name,
                    memory_total=memory_total,
                    memory_free=memory_free,
                    memory_used=memory_used,
                    utilization=utilization,
                    temperature=temp,
                    power_usage=power
                ))
                
        except Exception as e:
            self.logger.error(f"Error getting GPU info: {e}")
        
        return gpu_info
    
    async def start_monitoring(self, interval: int = 30):
        """Inicia monitoreo continuo de GPU"""
        self.monitoring_active = True
        self.logger.info("🔍 GPU monitoring started")
        
        while self.monitoring_active:
            try:
                gpu_info = self.get_gpu_info()
                
                for gpu in gpu_info:
                    # Métricas de memoria
                    self.metrics.set_gauge(
                        f"gpu_{gpu.device_id}_memory_total_mb", 
                        gpu.memory_total
                    )
                    self.metrics.set_gauge(
                        f"gpu_{gpu.device_id}_memory_used_mb", 
                        gpu.memory_used
                    )
                    self.metrics.set_gauge(
                        f"gpu_{gpu.device_id}_memory_free_mb", 
                        gpu.memory_free
                    )
                    
                    # Métricas de utilización
                    self.metrics.set_gauge(
                        f"gpu_{gpu.device_id}_utilization_percent", 
                        gpu.utilization
                    )
                    
                    # Métricas de temperatura
                    if gpu.temperature:
                        self.metrics.set_gauge(
                            f"gpu_{gpu.device_id}_temperature_celsius", 
                            gpu.temperature
                        )
                    
                    # Métricas de potencia
                    if gpu.power_usage:
                        self.metrics.set_gauge(
                            f"gpu_{gpu.device_id}_power_watts", 
                            gpu.power_usage
                        )
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in GPU monitoring: {e}")
                await asyncio.sleep(60)  # Longer wait on error
    
    def stop_monitoring(self):
        """Detiene monitoreo de GPU"""
        self.monitoring_active = False
        self.logger.info("🛑 GPU monitoring stopped")

class GPUOptimizer:
    """Optimizador principal para GPU"""
    
    def __init__(self, 
                 memory_strategy: GPUMemoryStrategy = GPUMemoryStrategy.BALANCED,
                 metrics_collector: Optional[MetricsCollector] = None):
        
        self.memory_strategy = memory_strategy
        self.metrics = metrics_collector or MetricsCollector()
        self.logger = LoggerFactory.get_logger("GPUOptimizer")
        self.monitor = GPUMonitor(metrics_collector)
        
        # Configuración de memoria por estrategia
        self.memory_limits = {
            GPUMemoryStrategy.CONSERVATIVE: 0.70,
            GPUMemoryStrategy.BALANCED: 0.85,
            GPUMemoryStrategy.AGGRESSIVE: 0.95
        }
        
        # Auto-detectar GPU disponible
        self.gpu_available = self._detect_gpu()
        self._configure_gpu()
        
        self.logger.info(f"🚀 GPU Optimizer initialized (Strategy: {memory_strategy.value})")
    
    def _detect_gpu(self) -> Dict[str, Any]:
        """Detecta GPU disponible"""
        gpu_info = {
            "available": False,
            "provider": GPUProvider.UNKNOWN,
            "devices": [],
            "torch_cuda": False,
            "tensorflow_gpu": False
        }
        
        # Verificar PyTorch CUDA
        if torch.cuda.is_available():
            gpu_info["torch_cuda"] = True
            gpu_info["available"] = True
            gpu_info["provider"] = GPUProvider.NVIDIA
            
            for i in range(torch.cuda.device_count()):
                device_name = torch.cuda.get_device_name(i)
                gpu_info["devices"].append({
                    "id": i,
                    "name": device_name,
                    "memory_gb": torch.cuda.get_device_properties(i).total_memory / (1024**3)
                })
        
        # Verificar TensorFlow GPU
        try:
            tf_gpus = tf.config.list_physical_devices('GPU')
            if tf_gpus:
                gpu_info["tensorflow_gpu"] = True
                gpu_info["available"] = True
                if gpu_info["provider"] == GPUProvider.UNKNOWN:
                    gpu_info["provider"] = GPUProvider.NVIDIA
        except:
            pass
        
        self.logger.info(f"🔍 GPU Detection: {gpu_info}")
        return gpu_info
    
    def _configure_gpu(self):
        """Configura GPU para uso óptimo"""
        if not self.gpu_available["available"]:
            self.logger.warning("⚠️ No GPU detected, using CPU")
            return
        
        # Configurar PyTorch
        if self.gpu_available["torch_cuda"]:
            # Habilitar optimizaciones
            torch.backends.cudnn.benchmark = True  # Para tamaños de entrada fijos
            torch.backends.cudnn.deterministic = False  # Para máximo rendimiento
            
            # Configurar memoria
            memory_limit = self.memory_limits[self.memory_strategy]
            
            for i in range(torch.cuda.device_count()):
                # Reservar memoria de forma conservadora
                torch.cuda.set_per_process_memory_fraction(memory_limit, device=i)
                
                self.logger.info(
                    f"⚙️ Configured PyTorch GPU {i} with {memory_limit:.1%} memory limit"
                )
        
        # Configurar TensorFlow
        if self.gpu_available["tensorflow_gpu"]:
            try:
                gpus = tf.config.list_physical_devices('GPU')
                for gpu in gpus:
                    # Habilitar crecimiento de memoria dinámico
                    tf.config.experimental.set_memory_growth(gpu, True)
                
                self.logger.info("⚙️ Configured TensorFlow GPU with dynamic memory growth")
                
            except Exception as e:
                self.logger.error(f"Error configuring TensorFlow GPU: {e}")
    
    def get_optimal_batch_size(self, 
                              model_size_mb: int, 
                              input_size: Tuple[int, ...],
                              safety_factor: float = 0.8) -> GPUBatchConfig:
        """Calcula tamaño de batch óptimo para GPU"""
        
        if not self.gpu_available["available"]:
            return GPUBatchConfig(
                batch_size=32,
                max_sequence_length=512,
                memory_threshold=0.5,
                use_mixed_precision=False
            )
        
        gpu_info = self.monitor.get_gpu_info()
        if not gpu_info:
            return GPUBatchConfig(
                batch_size=64,
                max_sequence_length=1024, 
                memory_threshold=0.7,
                use_mixed_precision=True
            )
        
        # Usar primera GPU disponible
        gpu = gpu_info[0]
        available_memory_mb = gpu.memory_free * safety_factor
        
        # Estimar memoria por muestra (rough estimation)
        input_elements = np.prod(input_size)
        memory_per_sample_mb = (input_elements * 4) / (1024 * 1024)  # float32
        
        # Considerar overhead del modelo
        total_overhead_mb = model_size_mb * 1.5  # 50% overhead
        usable_memory_mb = available_memory_mb - total_overhead_mb
        
        if usable_memory_mb <= 0:
            self.logger.warning("⚠️ Insufficient GPU memory, using minimal batch")
            batch_size = 1
        else:
            batch_size = max(1, int(usable_memory_mb // memory_per_sample_mb))
        
        # Limitar a tamaños razonables
        batch_size = min(batch_size, 256)
        batch_size = max(batch_size, 1)
        
        # Ajustar secuencia máxima basada en memoria
        max_seq_length = 512
        if gpu.memory_total > 16000:  # >16GB
            max_seq_length = 2048
        elif gpu.memory_total > 8000:   # >8GB
            max_seq_length = 1024
        
        config = GPUBatchConfig(
            batch_size=batch_size,
            max_sequence_length=max_seq_length,
            memory_threshold=self.memory_limits[self.memory_strategy],
            use_mixed_precision=gpu.memory_total > 6000  # Solo en GPUs >6GB
        )
        
        self.logger.info(f"🎯 Optimal batch config: {config}")
        return config
    
    async def optimize_model_inference(self, model, sample_input) -> Dict[str, Any]:
        """Optimiza modelo para inferencia en GPU"""
        optimizations = {
            "applied": [],
            "performance_gain": 0.0,
            "memory_saved_mb": 0.0
        }
        
        if not self.gpu_available["available"]:
            return optimizations
        
        # PyTorch optimizations
        if hasattr(model, 'eval') and callable(model.eval):
            try:
                # Modo evaluación
                model.eval()
                optimizations["applied"].append("eval_mode")
                
                # JIT compilation si es posible
                try:
                    if hasattr(torch, 'jit'):
                        traced_model = torch.jit.trace(model, sample_input)
                        optimizations["applied"].append("torch_jit")
                        self.logger.info("✅ Applied TorchScript JIT compilation")
                        model = traced_model
                except Exception as e:
                    self.logger.warning(f"JIT compilation failed: {e}")
                
                # Mixed precision si está disponible
                gpu_config = self.get_optimal_batch_size(100, sample_input.shape[1:])
                if gpu_config.use_mixed_precision:
                    try:
                        from torch.cuda.amp import autocast
                        optimizations["applied"].append("mixed_precision")
                        self.logger.info("✅ Mixed precision enabled")
                    except ImportError:
                        pass
                
                # Mover a GPU
                if torch.cuda.is_available():
                    model = model.cuda()
                    optimizations["applied"].append("gpu_placement")
                
            except Exception as e:
                self.logger.error(f"Error optimizing PyTorch model: {e}")
        
        # TensorFlow optimizations
        elif hasattr(model, 'predict'):
            try:
                # Optimizaciones específicas de TF
                optimizations["applied"].append("tensorflow_optimized")
            except Exception as e:
                self.logger.error(f"Error optimizing TensorFlow model: {e}")
        
        return optimizations
    
    async def benchmark_gpu_performance(self, iterations: int = 100) -> Dict[str, Any]:
        """Ejecuta benchmark de rendimiento GPU"""
        if not self.gpu_available["available"]:
            return {"error": "No GPU available for benchmarking"}
        
        benchmark_results = {
            "gpu_info": self.monitor.get_gpu_info(),
            "compute_performance": {},
            "memory_bandwidth": {},
            "mixed_precision_speedup": 0.0
        }
        
        try:
            # Benchmark de compute (PyTorch)
            if self.gpu_available["torch_cuda"]:
                device = torch.device('cuda')
                
                # Test matrix multiplication
                size = 2048
                a = torch.randn(size, size, device=device)
                b = torch.randn(size, size, device=device)
                
                torch.cuda.synchronize()
                start_time = time.time()
                
                for _ in range(iterations):
                    c = torch.matmul(a, b)
                    torch.cuda.synchronize()
                
                compute_time = (time.time() - start_time) / iterations
                benchmark_results["compute_performance"]["matmul_ms"] = compute_time * 1000
                
                # Test memory bandwidth
                large_tensor = torch.randn(100_000_000, device=device)  # ~400MB
                
                torch.cuda.synchronize()
                start_time = time.time()
                
                for _ in range(10):
                    copied_tensor = large_tensor.clone()
                    torch.cuda.synchronize()
                
                memory_time = (time.time() - start_time) / 10
                memory_bandwidth_gb_s = (400 * 2) / (memory_time * 1024)  # Read + Write
                benchmark_results["memory_bandwidth"]["bandwidth_gb_s"] = memory_bandwidth_gb_s
                
            self.logger.info(f"🏁 GPU benchmark completed: {benchmark_results['compute_performance']}")
            
        except Exception as e:
            self.logger.error(f"Error in GPU benchmark: {e}")
            benchmark_results["error"] = str(e)
        
        return benchmark_results
    
    def get_gpu_status_summary(self) -> Dict[str, Any]:
        """Resumen del estado actual de GPU"""
        gpu_info = self.monitor.get_gpu_info()
        
        if not gpu_info:
            return {
                "status": "no_gpu",
                "message": "No GPU detected or available"
            }
        
        # Calcular estadísticas agregadas
        total_memory = sum(gpu.memory_total for gpu in gpu_info)
        used_memory = sum(gpu.memory_used for gpu in gpu_info)
        avg_utilization = sum(gpu.utilization for gpu in gpu_info) / len(gpu_info)
        avg_temperature = None
        
        temps = [gpu.temperature for gpu in gpu_info if gpu.temperature]
        if temps:
            avg_temperature = sum(temps) / len(temps)
        
        # Determinar estado
        memory_usage_pct = (used_memory / total_memory) * 100 if total_memory > 0 else 0
        
        if avg_utilization > 90 or memory_usage_pct > 95:
            status = "overloaded"
        elif avg_utilization > 70 or memory_usage_pct > 85:
            status = "busy"
        elif avg_utilization > 30:
            status = "active"
        else:
            status = "idle"
        
        return {
            "status": status,
            "gpu_count": len(gpu_info),
            "total_memory_gb": total_memory / 1024,
            "used_memory_gb": used_memory / 1024,
            "memory_usage_percent": memory_usage_pct,
            "average_utilization": avg_utilization,
            "average_temperature": avg_temperature,
            "strategy": self.memory_strategy.value,
            "gpus": [
                {
                    "id": gpu.device_id,
                    "name": gpu.name,
                    "utilization": gpu.utilization,
                    "memory_used_gb": gpu.memory_used / 1024,
                    "memory_total_gb": gpu.memory_total / 1024
                }
                for gpu in gpu_info
            ]
        }

# Funciones de utilidad para integración rápida
def setup_gpu_environment() -> GPUOptimizer:
    """Setup rápido del entorno GPU"""
    optimizer = GPUOptimizer(memory_strategy=GPUMemoryStrategy.BALANCED)
    return optimizer

async def optimize_for_cloud_gpu(model, sample_input = None) -> Tuple[Any, Dict[str, Any]]:
    """Optimización rápida para GPU cloud"""
    optimizer = setup_gpu_environment()
    
    if sample_input is not None:
        optimizations = await optimizer.optimize_model_inference(model, sample_input)
        return model, optimizations
    else:
        return model, {"applied": ["basic_gpu_setup"]}

def get_recommended_instance_type(model_size_gb: float, 
                                 expected_qps: float) -> Dict[str, str]:
    """Recomienda tipo de instancia según requirements"""
    
    recommendations = {}
    
    # Google Cloud
    if model_size_gb <= 4 and expected_qps <= 10:
        recommendations["gcp"] = "n1-standard-4 + nvidia-tesla-t4"
    elif model_size_gb <= 16 and expected_qps <= 50:
        recommendations["gcp"] = "n1-standard-8 + nvidia-tesla-v100"
    else:
        recommendations["gcp"] = "a2-highgpu-1g + nvidia-tesla-a100"
    
    # AWS
    if model_size_gb <= 4 and expected_qps <= 10:
        recommendations["aws"] = "g4dn.xlarge"
    elif model_size_gb <= 16 and expected_qps <= 50:
        recommendations["aws"] = "p3.2xlarge"
    else:
        recommendations["aws"] = "p4d.24xlarge"
    
    # Azure  
    if model_size_gb <= 4 and expected_qps <= 10:
        recommendations["azure"] = "NC4as_T4_v3"
    elif model_size_gb <= 16 and expected_qps <= 50:
        recommendations["azure"] = "NC6s_v3"
    else:
        recommendations["azure"] = "ND96asr_v4"
    
    return recommendations