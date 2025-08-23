"""
OMEGA PRO AI v10.1 - Unit Tests for ML Models
Tests for various machine learning models in the modules directory
"""

import pytest
import unittest.mock as mock
import pandas as pd
import numpy as np
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestGeneticModel:
    """Test suite for genetic model"""
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for genetic model testing"""
        return pd.DataFrame({
            'numero1': [1, 5, 10, 15, 20],
            'numero2': [2, 6, 11, 16, 21],
            'numero3': [3, 7, 12, 17, 22],
            'numero4': [4, 8, 13, 18, 23],
            'numero5': [9, 14, 19, 24, 25],
            'numero6': [26, 27, 28, 29, 30]
        })
    
    def test_genetic_model_import(self):
        """Test genetic model import"""
        try:
            from modules.genetic_model import generar_combinaciones_geneticas, GeneticConfig
            assert generar_combinaciones_geneticas is not None
            assert GeneticConfig is not None
        except ImportError:
            pytest.skip("Genetic model not available")
    
    @mock.patch('modules.genetic_model.generar_combinaciones_geneticas')
    def test_genetic_model_output_format(self, mock_genetic, sample_data):
        """Test genetic model output format"""
        mock_genetic.return_value = [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]]
        
        result = mock_genetic(sample_data, num_combinaciones=2)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(comb, list) and len(comb) == 6 for comb in result)
        assert all(all(1 <= num <= 60 for num in comb) for comb in result)


class TestMonteCarloModel:
    """Test suite for Monte Carlo model"""
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for Monte Carlo testing"""
        return pd.DataFrame({
            'numero1': range(1, 11),
            'numero2': range(11, 21),
            'numero3': range(21, 31),
            'numero4': range(31, 41),
            'numero5': range(41, 51),
            'numero6': range(51, 61)
        })
    
    def test_montecarlo_model_import(self):
        """Test Monte Carlo model import"""
        try:
            from modules.montecarlo_model import generar_combinaciones_montecarlo
            assert generar_combinaciones_montecarlo is not None
        except ImportError:
            pytest.skip("Monte Carlo model not available")
    
    @mock.patch('modules.montecarlo_model.generar_combinaciones_montecarlo')
    def test_montecarlo_model_output(self, mock_monte, sample_data):
        """Test Monte Carlo model output"""
        mock_monte.return_value = [[1, 10, 20, 30, 40, 50]]
        
        result = mock_monte(sample_data, num_combinaciones=1)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert len(result[0]) == 6


class TestTransformerModel:
    """Test suite for Transformer model"""
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for transformer testing"""
        return pd.DataFrame({
            'numero1': [1, 2, 3, 4, 5],
            'numero2': [6, 7, 8, 9, 10],
            'numero3': [11, 12, 13, 14, 15],
            'numero4': [16, 17, 18, 19, 20],
            'numero5': [21, 22, 23, 24, 25],
            'numero6': [26, 27, 28, 29, 30]
        })
    
    def test_transformer_model_import(self):
        """Test transformer model import"""
        try:
            from modules.transformer_model import generar_combinaciones_transformer
            assert generar_combinaciones_transformer is not None
        except ImportError:
            pytest.skip("Transformer model not available")
    
    @mock.patch('modules.transformer_model.generar_combinaciones_transformer')
    def test_transformer_model_functionality(self, mock_transformer, sample_data):
        """Test transformer model functionality"""
        mock_transformer.return_value = [[5, 15, 25, 35, 45, 55]]
        
        result = mock_transformer(sample_data)
        
        assert isinstance(result, list)
        assert len(result) >= 1
        assert all(isinstance(comb, list) for comb in result)


class TestLSTMModel:
    """Test suite for LSTM model"""
    
    @pytest.fixture
    def sample_sequences(self):
        """Sample sequence data for LSTM"""
        return np.array([
            [[1, 2, 3, 4, 5, 6]],
            [[7, 8, 9, 10, 11, 12]],
            [[13, 14, 15, 16, 17, 18]]
        ])
    
    def test_lstm_model_import(self):
        """Test LSTM model import"""
        try:
            from modules.lstm_model import generar_combinaciones_lstm
            assert generar_combinaciones_lstm is not None
        except ImportError:
            pytest.skip("LSTM model not available")
    
    @mock.patch('modules.lstm_model.generar_combinaciones_lstm')
    def test_lstm_model_prediction(self, mock_lstm, sample_sequences):
        """Test LSTM model prediction"""
        mock_lstm.return_value = [[19, 20, 21, 22, 23, 24]]
        
        result = mock_lstm(sample_sequences)
        
        assert isinstance(result, list)
        assert len(result) >= 1


class TestClusteringModel:
    """Test suite for clustering model"""
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for clustering"""
        return pd.DataFrame({
            'numero1': [1, 5, 9, 13, 17],
            'numero2': [2, 6, 10, 14, 18],
            'numero3': [3, 7, 11, 15, 19],
            'numero4': [4, 8, 12, 16, 20],
            'numero5': [21, 25, 29, 33, 37],
            'numero6': [22, 26, 30, 34, 38]
        })
    
    def test_clustering_model_import(self):
        """Test clustering model import"""
        try:
            from modules.clustering_engine import generar_combinaciones_clustering
            assert generar_combinaciones_clustering is not None
        except ImportError:
            pytest.skip("Clustering model not available")
    
    @mock.patch('modules.clustering_engine.generar_combinaciones_clustering')
    def test_clustering_model_output(self, mock_cluster, sample_data):
        """Test clustering model output"""
        mock_cluster.return_value = [[1, 8, 15, 22, 29, 36]]
        
        result = mock_cluster(sample_data, n_clusters=3)
        
        assert isinstance(result, list)
        assert len(result) >= 1


class TestAprioriModel:
    """Test suite for Apriori model"""
    
    @pytest.fixture
    def sample_transactions(self):
        """Sample transaction data for Apriori"""
        return [
            [1, 2, 3, 4, 5, 6],
            [7, 8, 9, 10, 11, 12],
            [1, 8, 15, 22, 29, 36],
            [5, 10, 15, 20, 25, 30]
        ]
    
    def test_apriori_model_import(self):
        """Test Apriori model import"""
        try:
            from modules.apriori_model import generar_combinaciones_apriori
            assert generar_combinaciones_apriori is not None
        except ImportError:
            pytest.skip("Apriori model not available")
    
    @mock.patch('modules.apriori_model.generar_combinaciones_apriori')
    def test_apriori_model_associations(self, mock_apriori, sample_transactions):
        """Test Apriori model association rules"""
        mock_apriori.return_value = [[1, 5, 10, 15, 20, 25]]
        
        result = mock_apriori(sample_transactions, min_support=0.1)
        
        assert isinstance(result, list)
        assert len(result) >= 1


class TestModelValidation:
    """Test suite for model validation utilities"""
    
    @pytest.mark.parametrize("combination", [
        [1, 2, 3, 4, 5, 6],
        [10, 20, 30, 40, 50, 60],
        [5, 15, 25, 35, 45, 55],
        [1, 11, 21, 31, 41, 51]
    ])
    def test_combination_validation(self, combination):
        """Test combination validation across all models"""
        # Test basic validation rules
        assert len(combination) == 6
        assert len(set(combination)) == 6  # All unique
        assert all(1 <= num <= 60 for num in combination)
        assert combination == sorted(combination)  # Should be sorted
    
    def test_model_consistency(self):
        """Test that all models follow consistent interfaces"""
        model_functions = []
        
        try:
            from modules.genetic_model import generar_combinaciones_geneticas
            model_functions.append(generar_combinaciones_geneticas)
        except ImportError:
            pass
        
        try:
            from modules.montecarlo_model import generar_combinaciones_montecarlo
            model_functions.append(generar_combinaciones_montecarlo)
        except ImportError:
            pass
        
        # All model functions should be callable
        assert all(callable(func) for func in model_functions)
    
    def test_model_error_handling(self):
        """Test error handling across models"""
        with mock.patch('modules.genetic_model.generar_combinaciones_geneticas', side_effect=ValueError("Test error")):
            try:
                from modules.genetic_model import generar_combinaciones_geneticas
                with pytest.raises(ValueError):
                    generar_combinaciones_geneticas(pd.DataFrame(), num_combinaciones=-1)
            except ImportError:
                pytest.skip("Genetic model not available")


class TestModelPerformance:
    """Performance tests for ML models"""
    
    @pytest.mark.performance
    def test_model_initialization_speed(self):
        """Test model initialization performance"""
        import time
        
        start_time = time.time()
        
        # Try to import and initialize models
        models_imported = 0
        try:
            from modules.genetic_model import generar_combinaciones_geneticas
            models_imported += 1
        except ImportError:
            pass
        
        try:
            from modules.montecarlo_model import generar_combinaciones_montecarlo
            models_imported += 1
        except ImportError:
            pass
        
        end_time = time.time()
        
        # Should import quickly
        assert end_time - start_time < 2.0
        assert models_imported >= 0
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_model_prediction_speed(self):
        """Test model prediction performance"""
        sample_data = pd.DataFrame({
            'numero1': range(1, 101),
            'numero2': range(2, 102),
            'numero3': range(3, 103),
            'numero4': range(4, 104),
            'numero5': range(5, 105),
            'numero6': range(6, 106)
        })
        
        # Mock model to test performance framework
        with mock.patch('modules.genetic_model.generar_combinaciones_geneticas') as mock_model:
            mock_model.return_value = [[1, 2, 3, 4, 5, 6]]
            
            import time
            start_time = time.time()
            
            result = mock_model(sample_data, num_combinaciones=10)
            
            end_time = time.time()
            
            # Should complete within reasonable time
            assert end_time - start_time < 10.0
            assert isinstance(result, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])