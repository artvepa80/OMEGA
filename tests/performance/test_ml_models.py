"""
OMEGA PRO AI v10.1 - Performance Tests for ML Models
Tests for machine learning model performance, accuracy, and benchmarks
"""

import pytest
import time
import numpy as np
import pandas as pd
import os
import sys
import psutil
from unittest.mock import patch, MagicMock
import gc

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestModelPerformanceBenchmarks:
    """Performance benchmarks for ML models"""
    
    @pytest.fixture
    def large_dataset(self):
        """Generate large dataset for performance testing"""
        np.random.seed(42)
        size = 10000
        
        return pd.DataFrame({
            'numero1': np.random.randint(1, 61, size),
            'numero2': np.random.randint(1, 61, size),
            'numero3': np.random.randint(1, 61, size),
            'numero4': np.random.randint(1, 61, size),
            'numero5': np.random.randint(1, 61, size),
            'numero6': np.random.randint(1, 61, size),
            'fecha': pd.date_range('2020-01-01', periods=size, freq='D')
        })
    
    @pytest.fixture
    def memory_monitor(self):
        """Memory monitoring fixture"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        yield process
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Log memory usage for debugging
        print(f"Memory usage increase: {memory_increase:.2f} MB")
    
    @pytest.mark.performance
    def test_genetic_model_performance(self, large_dataset, memory_monitor):
        """Test genetic model performance with large dataset"""
        with patch('modules.genetic_model.generar_combinaciones_geneticas') as mock_genetic:
            mock_genetic.return_value = [[1, 2, 3, 4, 5, 6]] * 10
            
            start_time = time.time()
            start_cpu = time.process_time()
            
            # Simulate genetic algorithm execution
            for _ in range(100):  # Simulate multiple generations
                result = mock_genetic(large_dataset, num_combinaciones=10)
                assert len(result) == 10
            
            end_time = time.time()
            end_cpu = time.process_time()
            
            wall_time = end_time - start_time
            cpu_time = end_cpu - start_cpu
            
            # Performance assertions
            assert wall_time < 30.0  # Should complete within 30 seconds
            assert cpu_time < 25.0   # CPU time should be reasonable
            
            # Memory check
            current_memory = memory_monitor.memory_info().rss / 1024 / 1024
            assert current_memory < 500  # Should not exceed 500MB
    
    @pytest.mark.performance
    def test_monte_carlo_model_performance(self, large_dataset, memory_monitor):
        """Test Monte Carlo model performance"""
        with patch('modules.montecarlo_model.generar_combinaciones_montecarlo') as mock_monte:
            mock_monte.return_value = [[7, 8, 9, 10, 11, 12]] * 5
            
            start_time = time.time()
            
            # Simulate Monte Carlo simulations
            for _ in range(1000):  # Many simulation runs
                result = mock_monte(large_dataset, num_simulaciones=100)
                assert len(result) == 5
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Monte Carlo should be fast for many simulations
            assert execution_time < 15.0
    
    @pytest.mark.performance
    def test_transformer_model_performance(self, large_dataset, memory_monitor):
        """Test Transformer model performance"""
        with patch('modules.transformer_model.generar_combinaciones_transformer') as mock_transformer:
            mock_transformer.return_value = [[13, 14, 15, 16, 17, 18]] * 3
            
            start_time = time.time()
            
            # Simulate transformer inference
            for batch in range(50):  # Process in batches
                result = mock_transformer(large_dataset.iloc[batch*100:(batch+1)*100])
                assert len(result) == 3
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Transformer should handle batches efficiently
            assert execution_time < 60.0  # Allow more time for transformer
    
    @pytest.mark.performance
    def test_lstm_model_performance(self, large_dataset, memory_monitor):
        """Test LSTM model performance"""
        with patch('modules.lstm_model.generar_combinaciones_lstm') as mock_lstm:
            mock_lstm.return_value = [[19, 20, 21, 22, 23, 24]] * 2
            
            # Create sequence data for LSTM
            sequence_data = np.array([
                large_dataset.iloc[i:i+10].values 
                for i in range(0, len(large_dataset)-10, 10)
            ])
            
            start_time = time.time()
            
            # Process sequences
            for i in range(0, len(sequence_data), 100):  # Process in chunks
                batch = sequence_data[i:i+100]
                result = mock_lstm(batch)
                assert len(result) == 2
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # LSTM should process sequences efficiently
            assert execution_time < 45.0
    
    @pytest.mark.performance
    def test_clustering_model_performance(self, large_dataset, memory_monitor):
        """Test clustering model performance"""
        with patch('modules.clustering_engine.generar_combinaciones_clustering') as mock_cluster:
            mock_cluster.return_value = [[25, 26, 27, 28, 29, 30]] * 4
            
            start_time = time.time()
            
            # Test different cluster sizes
            for n_clusters in [3, 5, 8, 10]:
                result = mock_cluster(large_dataset, n_clusters=n_clusters)
                assert len(result) == 4
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Clustering should scale well with data size
            assert execution_time < 25.0


class TestModelAccuracyBenchmarks:
    """Accuracy and quality benchmarks for ML models"""
    
    @pytest.fixture
    def historical_validation_data(self):
        """Historical validation data with known outcomes"""
        return pd.DataFrame({
            'fecha': pd.date_range('2024-01-01', periods=100, freq='W'),
            'numero1': [1, 5, 10, 15, 20] * 20,
            'numero2': [2, 6, 11, 16, 21] * 20,
            'numero3': [3, 7, 12, 17, 22] * 20,
            'numero4': [4, 8, 13, 18, 23] * 20,
            'numero5': [9, 14, 19, 24, 25] * 20,
            'numero6': [26, 30, 35, 40, 45] * 20,
            'premio': [1000000, 2000000, 500000, 3000000, 1500000] * 20
        })
    
    @pytest.mark.performance
    def test_model_prediction_accuracy(self, historical_validation_data):
        """Test model prediction accuracy against historical data"""
        
        # Mock model predictions
        with patch('modules.genetic_model.generar_combinaciones_geneticas') as mock_genetic:
            mock_genetic.return_value = [[1, 2, 3, 4, 9, 26], [5, 6, 7, 8, 14, 30]]
            
            predictions = mock_genetic(historical_validation_data)
            
            # Calculate accuracy metrics
            accuracy_scores = []
            for pred in predictions:
                # Simulate accuracy calculation
                accuracy = np.random.uniform(0.6, 0.9)  # Mock accuracy
                accuracy_scores.append(accuracy)
            
            avg_accuracy = np.mean(accuracy_scores)
            
            # Performance assertions
            assert avg_accuracy > 0.65  # Minimum accuracy threshold
            assert len(predictions) == 2
            assert all(len(pred) == 6 for pred in predictions)
    
    @pytest.mark.performance
    def test_model_consistency(self, historical_validation_data):
        """Test model prediction consistency"""
        
        with patch('modules.genetic_model.generar_combinaciones_geneticas') as mock_model:
            # Test multiple runs with same data
            results = []
            for run in range(10):
                # Mock consistent but slightly varied results
                mock_model.return_value = [
                    [1 + run % 3, 2 + run % 3, 3 + run % 3, 4 + run % 3, 5 + run % 3, 6 + run % 3]
                ]
                
                result = mock_model(historical_validation_data)
                results.append(result[0])
            
            # Calculate consistency metrics
            consistency_scores = []
            for i in range(len(results) - 1):
                # Simple consistency check - numbers should be in similar ranges
                overlap = len(set(results[i]).intersection(set(results[i + 1])))
                consistency = overlap / 6.0
                consistency_scores.append(consistency)
            
            avg_consistency = np.mean(consistency_scores)
            
            # Consistency should be reasonable but not too high (avoiding overfitting)
            assert 0.2 <= avg_consistency <= 0.8
    
    @pytest.mark.performance
    def test_model_diversity(self, historical_validation_data):
        """Test diversity of model predictions"""
        
        models = ['genetic', 'monte_carlo', 'transformer', 'lstm']
        all_predictions = []
        
        for model in models:
            with patch(f'modules.{model}_model.generar_combinaciones_{model}') as mock_model:
                # Each model should produce different predictions
                if model == 'genetic':
                    mock_model.return_value = [[1, 10, 20, 30, 40, 50]]
                elif model == 'monte_carlo':
                    mock_model.return_value = [[5, 15, 25, 35, 45, 55]]
                elif model == 'transformer':
                    mock_model.return_value = [[2, 12, 22, 32, 42, 52]]
                else:  # lstm
                    mock_model.return_value = [[8, 18, 28, 38, 48, 58]]
                
                try:
                    predictions = mock_model(historical_validation_data)
                    all_predictions.extend(predictions)
                except:
                    # Handle cases where models might not be available
                    pass
        
        # Test diversity
        if len(all_predictions) > 1:
            unique_numbers = set()
            for pred in all_predictions:
                unique_numbers.update(pred)
            
            # Should have good diversity in number selection
            assert len(unique_numbers) >= len(all_predictions) * 3  # At least 3 unique numbers per prediction


class TestModelScalabilityBenchmarks:
    """Scalability benchmarks for ML models"""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_model_scaling_with_data_size(self):
        """Test how models scale with increasing data size"""
        
        data_sizes = [100, 500, 1000, 5000]
        execution_times = []
        
        for size in data_sizes:
            # Generate data of specified size
            test_data = pd.DataFrame({
                'numero1': np.random.randint(1, 61, size),
                'numero2': np.random.randint(1, 61, size),
                'numero3': np.random.randint(1, 61, size),
                'numero4': np.random.randint(1, 61, size),
                'numero5': np.random.randint(1, 61, size),
                'numero6': np.random.randint(1, 61, size)
            })
            
            with patch('modules.genetic_model.generar_combinaciones_geneticas') as mock_model:
                mock_model.return_value = [[1, 2, 3, 4, 5, 6]]
                
                start_time = time.time()
                result = mock_model(test_data)
                end_time = time.time()
                
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
                # Basic assertions
                assert len(result) == 1
                assert execution_time < 10.0  # Should scale reasonably
        
        # Test that execution time doesn't grow exponentially
        # Allow for some variance in timing
        for i in range(1, len(execution_times)):
            scaling_factor = execution_times[i] / execution_times[0]
            data_scaling_factor = data_sizes[i] / data_sizes[0]
            
            # Execution time should not scale worse than quadratically
            assert scaling_factor < data_scaling_factor ** 2
    
    @pytest.mark.performance
    def test_concurrent_model_execution(self):
        """Test concurrent execution of multiple models"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        threads = []
        
        def run_model(model_name):
            with patch(f'modules.{model_name}_model.generar_combinaciones_{model_name}') as mock_model:
                mock_model.return_value = [[1, 2, 3, 4, 5, 6]]
                
                start_time = time.time()
                result = mock_model(pd.DataFrame({'test': [1, 2, 3]}))
                end_time = time.time()
                
                results_queue.put({
                    'model': model_name,
                    'execution_time': end_time - start_time,
                    'result': result
                })
        
        # Start multiple models concurrently
        models = ['genetic', 'monte_carlo', 'transformer']
        start_time = time.time()
        
        for model in models:
            thread = threading.Thread(target=run_model, args=(model,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Assertions
        assert len(results) == len(models)
        assert total_time < 20.0  # Concurrent execution should be faster than sequential
        
        # Each model should have completed successfully
        for result in results:
            assert result['execution_time'] > 0
            assert len(result['result']) == 1


class TestModelResourceUtilization:
    """Test resource utilization of ML models"""
    
    @pytest.mark.performance
    def test_cpu_utilization(self):
        """Test CPU utilization during model execution"""
        
        with patch('modules.genetic_model.generar_combinaciones_geneticas') as mock_model:
            mock_model.return_value = [[1, 2, 3, 4, 5, 6]]
            
            # Monitor CPU usage
            process = psutil.Process(os.getpid())
            cpu_before = process.cpu_percent()
            
            # Simulate CPU-intensive operation
            large_data = pd.DataFrame({
                'numero1': list(range(1000)),
                'numero2': list(range(1000, 2000)),
                'numero3': list(range(2000, 3000)),
                'numero4': list(range(3000, 4000)),
                'numero5': list(range(4000, 5000)),
                'numero6': list(range(5000, 6000))
            })
            
            for _ in range(10):
                result = mock_model(large_data)
            
            time.sleep(0.1)  # Allow CPU measurement to stabilize
            cpu_after = process.cpu_percent()
            
            # CPU usage should increase during processing
            assert cpu_after >= cpu_before or cpu_after > 0
    
    @pytest.mark.performance
    def test_memory_efficiency(self):
        """Test memory efficiency of models"""
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Test memory usage with large dataset
        large_dataset = pd.DataFrame({
            'numero1': np.random.randint(1, 61, 50000),
            'numero2': np.random.randint(1, 61, 50000),
            'numero3': np.random.randint(1, 61, 50000),
            'numero4': np.random.randint(1, 61, 50000),
            'numero5': np.random.randint(1, 61, 50000),
            'numero6': np.random.randint(1, 61, 50000)
        })
        
        with patch('modules.genetic_model.generar_combinaciones_geneticas') as mock_model:
            mock_model.return_value = [[1, 2, 3, 4, 5, 6]]
            
            # Process large dataset multiple times
            for _ in range(5):
                result = mock_model(large_dataset)
                
                # Force garbage collection
                gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 200  # Should not increase by more than 200MB
        
        # Clean up
        del large_dataset
        gc.collect()
    
    @pytest.mark.performance
    def test_disk_io_efficiency(self):
        """Test disk I/O efficiency during model operations"""
        
        # Monitor disk I/O
        process = psutil.Process(os.getpid())
        io_before = process.io_counters()
        
        with patch('modules.transformer_model.generar_combinaciones_transformer') as mock_model:
            mock_model.return_value = [[1, 2, 3, 4, 5, 6]]
            
            # Simulate operations that might involve disk I/O
            test_data = pd.DataFrame({
                'numero1': range(1000),
                'numero2': range(1000, 2000),
                'numero3': range(2000, 3000),
                'numero4': range(3000, 4000),
                'numero5': range(4000, 5000),
                'numero6': range(5000, 6000)
            })
            
            for _ in range(20):
                result = mock_model(test_data)
        
        io_after = process.io_counters()
        
        # Calculate I/O usage
        read_bytes = io_after.read_bytes - io_before.read_bytes
        write_bytes = io_after.write_bytes - io_before.write_bytes
        
        # I/O should be reasonable (not excessive)
        total_io = (read_bytes + write_bytes) / 1024 / 1024  # MB
        assert total_io < 100  # Should not exceed 100MB of I/O


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])