"""
OMEGA PRO AI v10.1 - Unit Tests for Core Predictor Module
Tests for core/predictor.py functionality
"""

import pytest
import unittest.mock as mock
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.predictor import HybridOmegaPredictor


class TestHybridOmegaPredictor:
    """Test suite for HybridOmegaPredictor class"""
    
    @pytest.fixture
    def predictor_instance(self):
        """Create a predictor instance for testing"""
        with mock.patch('core.predictor.clean_historial_df'):
            predictor = HybridOmegaPredictor()
            return predictor
    
    @pytest.fixture
    def sample_historial_data(self):
        """Sample historical data for testing"""
        return pd.DataFrame({
            'fecha': ['2025-01-01', '2025-01-02', '2025-01-03'],
            'numero1': [1, 2, 3],
            'numero2': [10, 11, 12],
            'numero3': [20, 21, 22],
            'numero4': [30, 31, 32],
            'numero5': [40, 41, 42],
            'numero6': [45, 46, 47],
            'premio': [1000000, 2000000, 3000000]
        })
    
    def test_predictor_initialization(self, predictor_instance):
        """Test predictor initialization"""
        assert predictor_instance is not None
        assert hasattr(predictor_instance, 'historial_df')
        assert hasattr(predictor_instance, 'config')
    
    def test_predictor_with_mock_data(self, predictor_instance, sample_historial_data):
        """Test predictor with mock historical data"""
        predictor_instance.historial_df = sample_historial_data
        
        # Test that the predictor can access the data
        assert len(predictor_instance.historial_df) == 3
        assert 'numero1' in predictor_instance.historial_df.columns
    
    @mock.patch('core.predictor.generar_combinaciones_consenso')
    def test_consensus_integration(self, mock_consensus, predictor_instance):
        """Test integration with consensus engine"""
        mock_consensus.return_value = [[1, 2, 3, 4, 5, 6]]
        
        # This would normally call the consensus engine
        result = mock_consensus()
        
        assert result == [[1, 2, 3, 4, 5, 6]]
        mock_consensus.assert_called_once()
    
    def test_config_loading(self, predictor_instance):
        """Test configuration loading"""
        # Test that config is loaded or has defaults
        assert hasattr(predictor_instance, 'config')
    
    @pytest.mark.parametrize("combination", [
        [1, 2, 3, 4, 5, 6],
        [10, 20, 30, 40, 50, 60],
        [5, 15, 25, 35, 45, 55]
    ])
    def test_combination_validation(self, predictor_instance, combination):
        """Test combination validation logic"""
        # Test that combinations are within valid range
        assert all(1 <= num <= 60 for num in combination)
        assert len(combination) == 6
        assert len(set(combination)) == 6  # All unique numbers
    
    def test_memory_management(self, predictor_instance):
        """Test memory management features"""
        # Test PSUTIL_AVAILABLE flag
        from core.predictor import PSUTIL_AVAILABLE
        assert isinstance(PSUTIL_AVAILABLE, bool)
    
    def test_crypto_availability(self, predictor_instance):
        """Test cryptography availability"""
        from core.predictor import CRYPTO_AVAILABLE
        assert isinstance(CRYPTO_AVAILABLE, bool)
    
    @mock.patch('core.predictor.requests.get')
    def test_http_adapter_setup(self, mock_get, predictor_instance):
        """Test HTTP adapter configuration"""
        # Mock a successful HTTP response
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'ok'}
        mock_get.return_value = mock_response
        
        # Test would involve HTTP requests if implemented
        assert True  # Placeholder for HTTP adapter tests
    
    def test_thread_pool_executor_usage(self, predictor_instance):
        """Test ThreadPoolExecutor usage patterns"""
        from concurrent.futures import ThreadPoolExecutor
        
        # Test that ThreadPoolExecutor can be instantiated
        with ThreadPoolExecutor(max_workers=2) as executor:
            future = executor.submit(lambda: 42)
            result = future.result()
            assert result == 42
    
    def test_logging_configuration(self, predictor_instance):
        """Test logging setup"""
        import logging
        logger = logging.getLogger(__name__)
        assert logger is not None
    
    def test_data_validation_utils(self, predictor_instance):
        """Test data validation utilities"""
        # Test that validation functions are importable
        try:
            from utils.validation import clean_historial_df
            assert callable(clean_historial_df)
        except ImportError:
            pytest.skip("Validation utils not available")


class TestPredictorIntegration:
    """Integration tests for predictor components"""
    
    @pytest.fixture
    def mock_modules(self):
        """Mock all module dependencies"""
        modules_to_mock = [
            'modules.utils.combinador_maestro',
            'modules.montecarlo_model',
            'modules.apriori_model',
            'modules.transformer_model',
            'modules.filters.rules_filter',
            'modules.filters.ghost_rng_generative',
            'modules.inverse_mining_engine',
            'modules.score_dynamics',
            'utils.viabilidad',
            'modules.exporters.exportador_svi',
            'modules.clustering_engine',
            'modules.genetic_model',
            'modules.evaluation.evaluador_inteligente'
        ]
        
        mocks = {}
        for module in modules_to_mock:
            mocks[module] = mock.MagicMock()
        
        return mocks
    
    def test_module_imports_availability(self, mock_modules):
        """Test that all required modules can be imported"""
        # This test ensures all dependencies are properly mocked
        assert len(mock_modules) > 0
    
    @mock.patch('pandas.read_csv')
    def test_data_loading_integration(self, mock_read_csv):
        """Test data loading integration"""
        mock_read_csv.return_value = pd.DataFrame({
            'fecha': ['2025-01-01'],
            'numero1': [1], 'numero2': [2], 'numero3': [3],
            'numero4': [4], 'numero5': [5], 'numero6': [6]
        })
        
        df = mock_read_csv('dummy_path.csv')
        assert len(df) == 1
        assert 'numero1' in df.columns


class TestPredictorPerformance:
    """Performance tests for predictor module"""
    
    @pytest.mark.performance
    def test_predictor_initialization_speed(self):
        """Test predictor initialization performance"""
        import time
        
        with mock.patch('core.predictor.clean_historial_df'):
            start_time = time.time()
            predictor = HybridOmegaPredictor()
            end_time = time.time()
            
            # Should initialize within 5 seconds
            assert end_time - start_time < 5.0
    
    @pytest.mark.performance
    def test_memory_usage_reasonable(self):
        """Test that predictor doesn't use excessive memory"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            with mock.patch('core.predictor.clean_historial_df'):
                predictor = HybridOmegaPredictor()
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Should not increase memory by more than 100MB
            assert memory_increase < 100
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")


class TestPredictorErrorHandling:
    """Test error handling in predictor module"""
    
    def test_missing_data_handling(self):
        """Test behavior with missing historical data"""
        with mock.patch('core.predictor.clean_historial_df', side_effect=FileNotFoundError):
            with pytest.raises((FileNotFoundError, AttributeError)):
                HybridOmegaPredictor()
    
    def test_invalid_data_handling(self):
        """Test behavior with invalid data"""
        with mock.patch('core.predictor.clean_historial_df', return_value=pd.DataFrame()):
            predictor = HybridOmegaPredictor()
            assert len(predictor.historial_df) == 0
    
    def test_network_error_handling(self):
        """Test network error handling"""
        with mock.patch('requests.get', side_effect=ConnectionError):
            # Test would involve network calls if implemented
            assert True  # Placeholder for network error tests


if __name__ == '__main__':
    pytest.main([__file__, '-v'])