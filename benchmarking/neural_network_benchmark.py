#!/usr/bin/env python3
"""
OMEGA AI Neural Network Performance Benchmarking Suite
=======================================================

Comprehensive benchmarking framework for all neural network models in the Omega AI system.
Focuses on performance metrics, memory profiling, execution timing, and accuracy analysis.

Performance Engineer: Claude AI
Version: 1.0.0
"""

import os
import gc
import sys
import time
import json
import logging
import tracemalloc
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from collections import defaultdict

import numpy as np
import pandas as pd
import psutil
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import cross_val_score

# GPU monitoring
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

# Neural network models
try:
    from modules.lstm_model import LSTMCombiner, LSTMConfig, generar_combinaciones_lstm
    from modules.transformer_model import generar_combinaciones_transformer
    from modules.ensemble_calibrator import EnsembleCalibrator
    from modules.learning.gboost_jackpot_classifier import GBoostJackpotClassifier
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import some models: {e}")
    MODELS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BenchmarkMetrics:
    """Container for benchmark results"""
    model_name: str
    execution_time: float
    memory_usage_mb: float
    peak_memory_mb: float
    cpu_usage_percent: float
    gpu_usage_percent: float = 0.0
    gpu_memory_mb: float = 0.0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    predictions_per_second: float = 0.0
    memory_efficiency: float = 0.0
    throughput_mbps: float = 0.0
    errors: List[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class SystemProfiler:
    """Advanced system resource profiler"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.monitoring_active = False
        self.metrics = defaultdict(list)
        self.monitor_thread = None
    
    def start_monitoring(self, interval: float = 0.1):
        """Start continuous resource monitoring"""
        self.monitoring_active = True
        self.metrics.clear()
        
        def monitor():
            while self.monitoring_active:
                try:
                    # CPU and Memory
                    cpu_percent = self.process.cpu_percent()
                    memory_info = self.process.memory_info()
                    
                    self.metrics['cpu_percent'].append(cpu_percent)
                    self.metrics['memory_mb'].append(memory_info.rss / 1024 / 1024)
                    self.metrics['timestamp'].append(time.time())
                    
                    # GPU monitoring if available
                    if GPU_AVAILABLE:
                        try:
                            gpus = GPUtil.getGPUs()
                            if gpus:
                                gpu = gpus[0]
                                self.metrics['gpu_usage'].append(gpu.load * 100)
                                self.metrics['gpu_memory_mb'].append(gpu.memoryUsed)
                            else:
                                self.metrics['gpu_usage'].append(0)
                                self.metrics['gpu_memory_mb'].append(0)
                        except:
                            self.metrics['gpu_usage'].append(0)
                            self.metrics['gpu_memory_mb'].append(0)
                    
                    time.sleep(interval)
                except Exception as e:
                    logger.warning(f"Monitoring error: {e}")
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> Dict[str, float]:
        """Stop monitoring and return aggregated metrics"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        
        if not self.metrics['cpu_percent']:
            return {
                'avg_cpu_percent': 0.0,
                'peak_memory_mb': 0.0,
                'avg_gpu_usage': 0.0,
                'peak_gpu_memory_mb': 0.0
            }
        
        return {
            'avg_cpu_percent': np.mean(self.metrics['cpu_percent']),
            'peak_memory_mb': max(self.metrics['memory_mb']) if self.metrics['memory_mb'] else 0,
            'avg_gpu_usage': np.mean(self.metrics['gpu_usage']) if self.metrics['gpu_usage'] else 0,
            'peak_gpu_memory_mb': max(self.metrics['gpu_memory_mb']) if self.metrics['gpu_memory_mb'] else 0
        }

class MemoryProfiler:
    """Advanced memory profiling for neural networks"""
    
    @contextmanager
    def profile_memory(self):
        """Context manager for memory profiling"""
        tracemalloc.start()
        gc.collect()  # Clean start
        
        try:
            yield
        finally:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            self.current_memory = current / 1024 / 1024  # MB
            self.peak_memory = peak / 1024 / 1024  # MB
    
    def get_memory_stats(self) -> Dict[str, float]:
        """Get current memory statistics"""
        return {
            'current_mb': getattr(self, 'current_memory', 0),
            'peak_mb': getattr(self, 'peak_memory', 0)
        }

class NeuralNetworkBenchmark:
    """Main benchmarking class for neural network models"""
    
    def __init__(self, output_dir: str = "benchmarking/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.profiler = SystemProfiler()
        self.memory_profiler = MemoryProfiler()
        self.benchmark_results = []
        
        # Test data configurations
        self.test_configs = {
            'small': {'samples': 100, 'features': 6, 'sequence_length': 10},
            'medium': {'samples': 1000, 'features': 6, 'sequence_length': 20},
            'large': {'samples': 5000, 'features': 6, 'sequence_length': 50}
        }
        
        logger.info(f"Neural Network Benchmark initialized - Output: {self.output_dir}")
    
    def generate_test_data(self, config_name: str = 'medium') -> Tuple[pd.DataFrame, np.ndarray]:
        """Generate synthetic lottery data for testing"""
        config = self.test_configs[config_name]
        
        # Generate lottery data (numbers 1-40)
        np.random.seed(42)
        data = np.random.randint(1, 41, size=(config['samples'], config['features']))
        
        # Ensure no duplicates in rows (valid lottery combinations)
        for i in range(len(data)):
            while len(set(data[i])) != config['features']:
                data[i] = np.random.randint(1, 41, size=config['features'])
        
        # Create DataFrame with proper column names
        columns = [f'Bolilla {j+1}' for j in range(config['features'])]
        df = pd.DataFrame(data, columns=columns)
        
        # Add date column for transformer
        dates = pd.date_range('2020-01-01', periods=config['samples'], freq='D')
        df['fecha'] = dates
        
        logger.info(f"Generated {config_name} test data: {df.shape}")
        return df, data
    
    def benchmark_lstm_model(self, test_data: Tuple[pd.DataFrame, np.ndarray], 
                           config_name: str = 'medium') -> BenchmarkMetrics:
        """Benchmark LSTM model performance"""
        logger.info("Benchmarking LSTM Model...")
        
        df, data = test_data
        errors = []
        
        try:
            # Configure LSTM
            lstm_config = LSTMConfig(
                n_steps=10,
                n_units=64,
                epochs=20,  # Reduced for benchmarking
                batch_size=32,
                validation_split=0.2,
                seed=42
            )
            
            # Memory profiling
            with self.memory_profiler.profile_memory():
                self.profiler.start_monitoring()
                start_time = time.time()
                
                # Create and train LSTM
                combiner = LSTMCombiner(lstm_config)
                
                # Convert to historical set for interface
                historial_set = {tuple(sorted(row)) for row in data}
                
                # Generate combinations
                combinations = generar_combinaciones_lstm(
                    data=data,
                    historial_set=historial_set,
                    cantidad=50,
                    config=asdict(lstm_config)
                )
                
                execution_time = time.time() - start_time
                system_metrics = self.profiler.stop_monitoring()
                memory_stats = self.memory_profiler.get_memory_stats()
            
            # Performance calculations
            predictions_per_second = len(combinations) / execution_time
            memory_efficiency = len(combinations) / memory_stats['peak_mb'] if memory_stats['peak_mb'] > 0 else 0
            
            return BenchmarkMetrics(
                model_name="LSTM",
                execution_time=execution_time,
                memory_usage_mb=memory_stats['current_mb'],
                peak_memory_mb=memory_stats['peak_mb'],
                cpu_usage_percent=system_metrics['avg_cpu_percent'],
                gpu_usage_percent=system_metrics['avg_gpu_usage'],
                gpu_memory_mb=system_metrics['peak_gpu_memory_mb'],
                predictions_per_second=predictions_per_second,
                memory_efficiency=memory_efficiency,
                accuracy=self._calculate_mock_accuracy(combinations),
                errors=errors
            )
            
        except Exception as e:
            errors.append(str(e))
            logger.error(f"LSTM benchmark failed: {e}")
            return BenchmarkMetrics(
                model_name="LSTM",
                execution_time=0,
                memory_usage_mb=0,
                peak_memory_mb=0,
                cpu_usage_percent=0,
                errors=errors
            )
    
    def benchmark_transformer_model(self, test_data: Tuple[pd.DataFrame, np.ndarray],
                                  config_name: str = 'medium') -> BenchmarkMetrics:
        """Benchmark Transformer model performance"""
        logger.info("Benchmarking Transformer Model...")
        
        df, data = test_data
        errors = []
        
        try:
            with self.memory_profiler.profile_memory():
                self.profiler.start_monitoring()
                start_time = time.time()
                
                # Generate combinations using transformer
                combinations = generar_combinaciones_transformer(
                    historial_df=df,
                    cantidad=50,
                    train_model_if_missing=True
                )
                
                execution_time = time.time() - start_time
                system_metrics = self.profiler.stop_monitoring()
                memory_stats = self.memory_profiler.get_memory_stats()
            
            predictions_per_second = len(combinations) / execution_time
            memory_efficiency = len(combinations) / memory_stats['peak_mb'] if memory_stats['peak_mb'] > 0 else 0
            
            return BenchmarkMetrics(
                model_name="Transformer",
                execution_time=execution_time,
                memory_usage_mb=memory_stats['current_mb'],
                peak_memory_mb=memory_stats['peak_mb'],
                cpu_usage_percent=system_metrics['avg_cpu_percent'],
                gpu_usage_percent=system_metrics['avg_gpu_usage'],
                gpu_memory_mb=system_metrics['peak_gpu_memory_mb'],
                predictions_per_second=predictions_per_second,
                memory_efficiency=memory_efficiency,
                accuracy=self._calculate_mock_accuracy(combinations),
                errors=errors
            )
            
        except Exception as e:
            errors.append(str(e))
            logger.error(f"Transformer benchmark failed: {e}")
            return BenchmarkMetrics(
                model_name="Transformer",
                execution_time=0,
                memory_usage_mb=0,
                peak_memory_mb=0,
                cpu_usage_percent=0,
                errors=errors
            )
    
    def benchmark_ensemble_calibrator(self, test_data: Tuple[pd.DataFrame, np.ndarray],
                                    config_name: str = 'medium') -> BenchmarkMetrics:
        """Benchmark Ensemble Calibrator performance"""
        logger.info("Benchmarking Ensemble Calibrator...")
        
        df, data = test_data
        errors = []
        
        try:
            with self.memory_profiler.profile_memory():
                self.profiler.start_monitoring()
                start_time = time.time()
                
                # Initialize and run calibrator
                calibrator = EnsembleCalibrator()
                performance_metrics = calibrator.simulate_historical_performance(df, test_size=20)
                
                execution_time = time.time() - start_time
                system_metrics = self.profiler.stop_monitoring()
                memory_stats = self.memory_profiler.get_memory_stats()
            
            # Mock calculations for calibrator
            operations_per_second = len(performance_metrics) / execution_time if execution_time > 0 else 0
            memory_efficiency = len(performance_metrics) / memory_stats['peak_mb'] if memory_stats['peak_mb'] > 0 else 0
            
            return BenchmarkMetrics(
                model_name="Ensemble_Calibrator",
                execution_time=execution_time,
                memory_usage_mb=memory_stats['current_mb'],
                peak_memory_mb=memory_stats['peak_mb'],
                cpu_usage_percent=system_metrics['avg_cpu_percent'],
                gpu_usage_percent=system_metrics['avg_gpu_usage'],
                gpu_memory_mb=system_metrics['peak_gpu_memory_mb'],
                predictions_per_second=operations_per_second,
                memory_efficiency=memory_efficiency,
                accuracy=np.mean(list(performance_metrics.values())) if performance_metrics else 0.5,
                errors=errors
            )
            
        except Exception as e:
            errors.append(str(e))
            logger.error(f"Ensemble Calibrator benchmark failed: {e}")
            return BenchmarkMetrics(
                model_name="Ensemble_Calibrator",
                execution_time=0,
                memory_usage_mb=0,
                peak_memory_mb=0,
                cpu_usage_percent=0,
                errors=errors
            )
    
    def benchmark_gboost_classifier(self, test_data: Tuple[pd.DataFrame, np.ndarray],
                                  config_name: str = 'medium') -> BenchmarkMetrics:
        """Benchmark GBoost Classifier performance"""
        logger.info("Benchmarking GBoost Classifier...")
        
        df, data = test_data
        errors = []
        
        try:
            with self.memory_profiler.profile_memory():
                self.profiler.start_monitoring()
                start_time = time.time()
                
                # Initialize GBoost classifier
                classifier = GBoostJackpotClassifier()
                
                # Generate dummy targets (jackpot vs non-jackpot)
                targets = np.random.binomial(1, 0.1, len(data))  # 10% jackpots
                
                # Fit model
                classifier.fit(data, targets)
                
                # Make predictions
                predictions = classifier.predict(data[:100])  # Predict on subset
                
                execution_time = time.time() - start_time
                system_metrics = self.profiler.stop_monitoring()
                memory_stats = self.memory_profiler.get_memory_stats()
            
            predictions_per_second = len(predictions) / execution_time if execution_time > 0 else 0
            memory_efficiency = len(predictions) / memory_stats['peak_mb'] if memory_stats['peak_mb'] > 0 else 0
            
            # Calculate accuracy
            test_targets = targets[:len(predictions)]
            accuracy = accuracy_score(test_targets, predictions) if len(test_targets) == len(predictions) else 0.5
            
            return BenchmarkMetrics(
                model_name="GBoost_Classifier",
                execution_time=execution_time,
                memory_usage_mb=memory_stats['current_mb'],
                peak_memory_mb=memory_stats['peak_mb'],
                cpu_usage_percent=system_metrics['avg_cpu_percent'],
                gpu_usage_percent=system_metrics['avg_gpu_usage'],
                gpu_memory_mb=system_metrics['peak_gpu_memory_mb'],
                predictions_per_second=predictions_per_second,
                memory_efficiency=memory_efficiency,
                accuracy=accuracy,
                errors=errors
            )
            
        except Exception as e:
            errors.append(str(e))
            logger.error(f"GBoost Classifier benchmark failed: {e}")
            return BenchmarkMetrics(
                model_name="GBoost_Classifier",
                execution_time=0,
                memory_usage_mb=0,
                peak_memory_mb=0,
                cpu_usage_percent=0,
                errors=errors
            )
    
    def _calculate_mock_accuracy(self, combinations: List[Dict]) -> float:
        """Calculate mock accuracy for lottery combinations"""
        try:
            if not combinations:
                return 0.0
            
            # Mock accuracy based on score distribution
            scores = [combo.get('score', 0) for combo in combinations]
            return np.mean(scores) if scores else 0.5
        except:
            return 0.5
    
    def run_comprehensive_benchmark(self, test_configs: List[str] = None) -> List[BenchmarkMetrics]:
        """Run comprehensive benchmark across all models and configurations"""
        if test_configs is None:
            test_configs = ['small', 'medium', 'large']
        
        logger.info("Starting comprehensive neural network benchmark...")
        all_results = []
        
        # Model benchmark functions
        benchmark_functions = [
            self.benchmark_lstm_model,
            self.benchmark_transformer_model,
            self.benchmark_ensemble_calibrator,
            self.benchmark_gboost_classifier
        ]
        
        for config_name in test_configs:
            logger.info(f"\n=== Benchmarking with {config_name} dataset ===")
            test_data = self.generate_test_data(config_name)
            
            for benchmark_func in benchmark_functions:
                try:
                    # Force garbage collection between tests
                    gc.collect()
                    
                    result = benchmark_func(test_data, config_name)
                    result.model_name += f"_{config_name}"
                    all_results.append(result)
                    
                    logger.info(f"✅ {result.model_name}: "
                              f"{result.execution_time:.3f}s, "
                              f"{result.peak_memory_mb:.1f}MB peak, "
                              f"{result.predictions_per_second:.1f} pred/s")
                    
                except Exception as e:
                    logger.error(f"❌ Benchmark failed for {benchmark_func.__name__}: {e}")
        
        self.benchmark_results.extend(all_results)
        return all_results
    
    def generate_performance_report(self, results: List[BenchmarkMetrics] = None) -> Dict[str, Any]:
        """Generate comprehensive performance analysis report"""
        if results is None:
            results = self.benchmark_results
        
        if not results:
            logger.warning("No benchmark results available for report generation")
            return {}
        
        logger.info("Generating performance analysis report...")
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([asdict(result) for result in results])
        
        # Performance analysis
        report = {
            'summary': {
                'total_models_tested': len(df),
                'successful_tests': len(df[df['execution_time'] > 0]),
                'failed_tests': len(df[df['execution_time'] == 0]),
                'average_execution_time': df['execution_time'].mean(),
                'average_memory_usage_mb': df['peak_memory_mb'].mean(),
                'average_accuracy': df['accuracy'].mean()
            },
            'model_rankings': {
                'fastest_execution': df.loc[df['execution_time'].idxmin()]['model_name'] if not df.empty else 'N/A',
                'lowest_memory_usage': df.loc[df['peak_memory_mb'].idxmin()]['model_name'] if not df.empty else 'N/A',
                'highest_accuracy': df.loc[df['accuracy'].idxmax()]['model_name'] if not df.empty else 'N/A',
                'best_memory_efficiency': df.loc[df['memory_efficiency'].idxmax()]['model_name'] if not df.empty else 'N/A',
                'highest_throughput': df.loc[df['predictions_per_second'].idxmax()]['model_name'] if not df.empty else 'N/A'
            },
            'detailed_metrics': df.to_dict('records'),
            'optimization_recommendations': self._generate_optimization_recommendations(df),
            'scalability_analysis': self._analyze_scalability(df),
            'resource_utilization': self._analyze_resource_utilization(df)
        }
        
        return report
    
    def _generate_optimization_recommendations(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Generate specific optimization recommendations"""
        recommendations = []
        
        if df.empty:
            return recommendations
        
        # Memory optimization recommendations
        high_memory_models = df[df['peak_memory_mb'] > df['peak_memory_mb'].quantile(0.75)]
        for _, model in high_memory_models.iterrows():
            recommendations.append({
                'model': model['model_name'],
                'type': 'memory_optimization',
                'issue': f"High memory usage: {model['peak_memory_mb']:.1f}MB",
                'recommendation': "Consider reducing batch size, implementing gradient checkpointing, or using model pruning techniques"
            })
        
        # Performance optimization recommendations
        slow_models = df[df['execution_time'] > df['execution_time'].quantile(0.75)]
        for _, model in slow_models.iterrows():
            recommendations.append({
                'model': model['model_name'],
                'type': 'performance_optimization',
                'issue': f"Slow execution: {model['execution_time']:.3f}s",
                'recommendation': "Consider model quantization, mixed precision training, or architectural simplification"
            })
        
        # Accuracy improvement recommendations
        low_accuracy_models = df[df['accuracy'] < df['accuracy'].quantile(0.25)]
        for _, model in low_accuracy_models.iterrows():
            recommendations.append({
                'model': model['model_name'],
                'type': 'accuracy_improvement',
                'issue': f"Low accuracy: {model['accuracy']:.3f}",
                'recommendation': "Consider hyperparameter tuning, ensemble methods, or data augmentation techniques"
            })
        
        return recommendations
    
    def _analyze_scalability(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze model scalability across different data sizes"""
        scalability = {}
        
        if df.empty:
            return scalability
        
        # Group by model type (removing size suffix)
        df['base_model'] = df['model_name'].str.replace('_(small|medium|large)$', '', regex=True)
        
        for model_name in df['base_model'].unique():
            model_data = df[df['base_model'] == model_name].sort_values('model_name')
            
            if len(model_data) > 1:
                # Calculate scaling factors
                time_scaling = model_data['execution_time'].iloc[-1] / model_data['execution_time'].iloc[0]
                memory_scaling = model_data['peak_memory_mb'].iloc[-1] / model_data['peak_memory_mb'].iloc[0]
                
                scalability[model_name] = {
                    'time_scaling_factor': time_scaling,
                    'memory_scaling_factor': memory_scaling,
                    'scalability_rating': 'Good' if time_scaling < 10 and memory_scaling < 5 else 
                                        'Fair' if time_scaling < 50 and memory_scaling < 10 else 'Poor'
                }
        
        return scalability
    
    def _analyze_resource_utilization(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze resource utilization patterns"""
        if df.empty:
            return {}
        
        return {
            'cpu_utilization': {
                'average': df['cpu_usage_percent'].mean(),
                'max': df['cpu_usage_percent'].max(),
                'models_high_cpu': df[df['cpu_usage_percent'] > 80]['model_name'].tolist()
            },
            'memory_utilization': {
                'average_mb': df['peak_memory_mb'].mean(),
                'max_mb': df['peak_memory_mb'].max(),
                'total_mb': df['peak_memory_mb'].sum()
            },
            'gpu_utilization': {
                'average': df['gpu_usage_percent'].mean(),
                'max': df['gpu_usage_percent'].max(),
                'models_using_gpu': df[df['gpu_usage_percent'] > 0]['model_name'].tolist()
            } if 'gpu_usage_percent' in df.columns else {}
        }
    
    def save_results(self, results: List[BenchmarkMetrics] = None, 
                    report: Dict[str, Any] = None) -> str:
        """Save benchmark results and report to files"""
        if results is None:
            results = self.benchmark_results
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw results
        results_file = self.output_dir / f"neural_benchmark_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump([asdict(result) for result in results], f, indent=2, default=str)
        
        # Generate and save report if not provided
        if report is None:
            report = self.generate_performance_report(results)
        
        report_file = self.output_dir / f"neural_benchmark_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Generate visualization
        self.create_visualizations(results, timestamp)
        
        logger.info(f"Benchmark results saved to {results_file}")
        logger.info(f"Performance report saved to {report_file}")
        
        return str(report_file)
    
    def create_visualizations(self, results: List[BenchmarkMetrics], timestamp: str):
        """Create performance visualization charts"""
        try:
            df = pd.DataFrame([asdict(result) for result in results])
            
            if df.empty:
                return
            
            # Set up the plotting style
            plt.style.use('seaborn-v0_8')
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Neural Network Performance Benchmark Results', fontsize=16)
            
            # Execution Time Comparison
            if 'execution_time' in df.columns:
                df_plot = df[df['execution_time'] > 0]  # Filter out failed tests
                if not df_plot.empty:
                    axes[0, 0].bar(range(len(df_plot)), df_plot['execution_time'])
                    axes[0, 0].set_title('Execution Time by Model')
                    axes[0, 0].set_ylabel('Time (seconds)')
                    axes[0, 0].set_xticks(range(len(df_plot)))
                    axes[0, 0].set_xticklabels(df_plot['model_name'], rotation=45)
            
            # Memory Usage Comparison
            if 'peak_memory_mb' in df.columns:
                df_plot = df[df['peak_memory_mb'] > 0]
                if not df_plot.empty:
                    axes[0, 1].bar(range(len(df_plot)), df_plot['peak_memory_mb'])
                    axes[0, 1].set_title('Peak Memory Usage by Model')
                    axes[0, 1].set_ylabel('Memory (MB)')
                    axes[0, 1].set_xticks(range(len(df_plot)))
                    axes[0, 1].set_xticklabels(df_plot['model_name'], rotation=45)
            
            # Throughput Comparison
            if 'predictions_per_second' in df.columns:
                df_plot = df[df['predictions_per_second'] > 0]
                if not df_plot.empty:
                    axes[1, 0].bar(range(len(df_plot)), df_plot['predictions_per_second'])
                    axes[1, 0].set_title('Throughput by Model')
                    axes[1, 0].set_ylabel('Predictions/Second')
                    axes[1, 0].set_xticks(range(len(df_plot)))
                    axes[1, 0].set_xticklabels(df_plot['model_name'], rotation=45)
            
            # Accuracy Comparison
            if 'accuracy' in df.columns:
                df_plot = df[df['accuracy'] > 0]
                if not df_plot.empty:
                    axes[1, 1].bar(range(len(df_plot)), df_plot['accuracy'])
                    axes[1, 1].set_title('Accuracy by Model')
                    axes[1, 1].set_ylabel('Accuracy Score')
                    axes[1, 1].set_xticks(range(len(df_plot)))
                    axes[1, 1].set_xticklabels(df_plot['model_name'], rotation=45)
            
            plt.tight_layout()
            chart_file = self.output_dir / f"neural_benchmark_charts_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Visualization saved to {chart_file}")
            
        except Exception as e:
            logger.error(f"Failed to create visualizations: {e}")

class RegressionTestFramework:
    """Framework for performance regression testing"""
    
    def __init__(self, benchmark_suite: NeuralNetworkBenchmark):
        self.benchmark_suite = benchmark_suite
        self.baseline_results = None
        self.regression_threshold = 0.20  # 20% performance degradation threshold
    
    def set_baseline(self, results: List[BenchmarkMetrics] = None):
        """Set baseline performance metrics"""
        if results is None:
            results = self.benchmark_suite.run_comprehensive_benchmark(['medium'])
        
        self.baseline_results = {result.model_name: result for result in results}
        logger.info(f"Baseline set for {len(self.baseline_results)} models")
    
    def run_regression_test(self) -> Dict[str, Any]:
        """Run regression test against baseline"""
        if self.baseline_results is None:
            raise ValueError("No baseline set. Call set_baseline() first.")
        
        current_results = self.benchmark_suite.run_comprehensive_benchmark(['medium'])
        current_dict = {result.model_name: result for result in current_results}
        
        regression_report = {
            'regressions': [],
            'improvements': [],
            'new_models': [],
            'removed_models': []
        }
        
        # Check for regressions and improvements
        for model_name in self.baseline_results:
            if model_name in current_dict:
                baseline = self.baseline_results[model_name]
                current = current_dict[model_name]
                
                # Check execution time regression
                time_change = (current.execution_time - baseline.execution_time) / baseline.execution_time
                if time_change > self.regression_threshold:
                    regression_report['regressions'].append({
                        'model': model_name,
                        'metric': 'execution_time',
                        'baseline': baseline.execution_time,
                        'current': current.execution_time,
                        'change_percent': time_change * 100
                    })
                elif time_change < -0.10:  # 10% improvement threshold
                    regression_report['improvements'].append({
                        'model': model_name,
                        'metric': 'execution_time',
                        'baseline': baseline.execution_time,
                        'current': current.execution_time,
                        'change_percent': time_change * 100
                    })
                
                # Check memory regression
                memory_change = (current.peak_memory_mb - baseline.peak_memory_mb) / baseline.peak_memory_mb
                if memory_change > self.regression_threshold:
                    regression_report['regressions'].append({
                        'model': model_name,
                        'metric': 'memory_usage',
                        'baseline': baseline.peak_memory_mb,
                        'current': current.peak_memory_mb,
                        'change_percent': memory_change * 100
                    })
            else:
                regression_report['removed_models'].append(model_name)
        
        # Check for new models
        for model_name in current_dict:
            if model_name not in self.baseline_results:
                regression_report['new_models'].append(model_name)
        
        return regression_report

def main():
    """Main function to run the neural network benchmark suite"""
    print("🚀 OMEGA AI Neural Network Performance Benchmark Suite")
    print("=" * 60)
    
    # Initialize benchmark suite
    benchmark = NeuralNetworkBenchmark()
    
    try:
        # Run comprehensive benchmark
        results = benchmark.run_comprehensive_benchmark()
        
        # Generate performance report
        report = benchmark.generate_performance_report(results)
        
        # Save results
        report_file = benchmark.save_results(results, report)
        
        # Print summary
        print(f"\n📊 Benchmark Summary:")
        print(f"✅ Models tested: {report['summary']['total_models_tested']}")
        print(f"✅ Successful tests: {report['summary']['successful_tests']}")
        print(f"❌ Failed tests: {report['summary']['failed_tests']}")
        print(f"⚡ Average execution time: {report['summary']['average_execution_time']:.3f}s")
        print(f"💾 Average memory usage: {report['summary']['average_memory_usage_mb']:.1f}MB")
        print(f"🎯 Average accuracy: {report['summary']['average_accuracy']:.3f}")
        
        print(f"\n🏆 Top Performers:")
        rankings = report['model_rankings']
        print(f"⚡ Fastest: {rankings['fastest_execution']}")
        print(f"💾 Lowest Memory: {rankings['lowest_memory_usage']}")
        print(f"🎯 Highest Accuracy: {rankings['highest_accuracy']}")
        print(f"🔥 Best Efficiency: {rankings['best_memory_efficiency']}")
        print(f"🚀 Highest Throughput: {rankings['highest_throughput']}")
        
        print(f"\n💡 Optimization Recommendations:")
        for rec in report['optimization_recommendations'][:5]:  # Show top 5
            print(f"   • {rec['model']}: {rec['recommendation']}")
        
        print(f"\n📁 Full report saved to: {report_file}")
        
        # Regression testing demo
        print(f"\n🔄 Running regression test demo...")
        regression_framework = RegressionTestFramework(benchmark)
        regression_framework.set_baseline(results)
        
        # Simulate running again (would normally be run at different time)
        regression_report = regression_framework.run_regression_test()
        print(f"   • Regressions found: {len(regression_report['regressions'])}")
        print(f"   • Improvements found: {len(regression_report['improvements'])}")
        
        print("\n✅ Neural Network Benchmark Suite completed successfully!")
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        print(f"❌ Benchmark failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())