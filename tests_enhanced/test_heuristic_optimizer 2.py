#!/usr/bin/env python3
"""
Tests para heuristic_optimizer_enhanced.py
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Importar módulos a testear
try:
    from modules.heuristic_optimizer_enhanced import (
        HeuristicOptimizerEnhanced, OptimizationResult, FeatureEngineering,
        TemporalValidator, EnhancedFeatureExtractor, BayesianOptimizer,
        CachedPredictor, optimize_heuristics
    )
except ImportError as e:
    pytest.skip(f"No se puede importar heuristic_optimizer_enhanced: {e}", allow_module_level=True)


class TestFeatureEngineering:
    """Tests para FeatureEngineering dataclass"""
    
    def test_feature_engineering_default(self):
        """Test configuración por defecto"""
        config = FeatureEngineering()
        
        assert config.include_temporal is True
        assert config.include_interactions is True
        assert config.include_lags is True
        assert len(config.lag_periods) > 0
        assert len(config.rolling_windows) > 0


class TestTemporalValidator:
    """Tests para TemporalValidator"""
    
    def test_temporal_validator_creation(self):
        """Test creación de validador temporal"""
        validator = TemporalValidator(date_column='fecha', test_size=0.2)
        
        assert validator.date_column == 'fecha'
        assert validator.test_size == 0.2
    
    def test_temporal_split_without_dates(self):
        """Test split sin columna de fecha"""
        validator = TemporalValidator(date_column='fecha_inexistente')
        
        # DataFrame sin columna de fecha
        df = pd.DataFrame({
            'combination': [[1, 2, 3, 4, 5, 6]] * 100,
            'other_col': range(100)
        })
        
        splits = validator.split(df, n_splits=3)
        
        assert len(splits) == 3
        for train_idx, test_idx in splits:
            assert len(train_idx) > 0
            assert len(test_idx) > 0
            assert len(set(train_idx) & set(test_idx)) == 0  # No overlap
    
    def test_temporal_split_with_dates(self):
        """Test split con columna de fecha"""
        validator = TemporalValidator(date_column='fecha')
        
        # DataFrame con fechas
        df = pd.DataFrame({
            'combination': [[1, 2, 3, 4, 5, 6]] * 100,
            'fecha': pd.date_range('2020-01-01', periods=100)
        })
        
        splits = validator.split(df, n_splits=3)
        
        assert len(splits) == 3
        for train_idx, test_idx in splits:
            # Verificar orden temporal: train siempre antes que test
            if len(train_idx) > 0 and len(test_idx) > 0:
                assert max(train_idx) < min(test_idx)


class TestEnhancedFeatureExtractor:
    """Tests para EnhancedFeatureExtractor"""
    
    def test_feature_extractor_creation(self):
        """Test creación del extractor"""
        config = FeatureEngineering()
        extractor = EnhancedFeatureExtractor(config)
        
        assert extractor.config == config
        assert isinstance(extractor.scalers, dict)
    
    def test_extract_basic_features(self):
        """Test extracción de features básicas"""
        extractor = EnhancedFeatureExtractor()
        
        combinations = [
            [1, 2, 3, 4, 5, 6],
            [10, 15, 20, 25, 30, 35],
            [5, 12, 18, 23, 31, 40]
        ]
        
        features = extractor.extract_basic_features(combinations)
        
        assert features.shape[0] == 3  # 3 combinaciones
        assert features.shape[1] > 10  # Varias features
        
        # Verificar que las features son numéricas
        assert np.all(np.isfinite(features))
    
    def test_fit_transform(self):
        """Test fit_transform completo"""
        extractor = EnhancedFeatureExtractor()
        
        # DataFrame de prueba
        df = pd.DataFrame({
            'combination': [
                [1, 2, 3, 4, 5, 6],
                [10, 15, 20, 25, 30, 35],
                [5, 12, 18, 23, 31, 40]
            ]
        })
        
        features = extractor.fit_transform(df)
        
        assert features.shape[0] == 3
        assert features.shape[1] > 0
        
        # Verificar que features están normalizadas (aproximadamente)
        assert abs(np.mean(features)) < 1.0  # Media cerca de 0
    
    def test_extract_temporal_features_disabled(self):
        """Test features temporales deshabilitadas"""
        config = FeatureEngineering(include_temporal=False)
        extractor = EnhancedFeatureExtractor(config)
        
        df = pd.DataFrame({
            'combination': [[1, 2, 3, 4, 5, 6]] * 5
        })
        
        temporal_features = extractor.extract_temporal_features(df)
        
        # Debe retornar array vacío
        assert temporal_features.size == 0


class TestBayesianOptimizer:
    """Tests para BayesianOptimizer"""
    
    def test_bayesian_optimizer_creation(self):
        """Test creación del optimizador"""
        optimizer = BayesianOptimizer(n_trials=10, timeout=60)
        
        assert optimizer.n_trials == 10
        assert optimizer.timeout == 60
    
    def test_optimize_fallback(self):
        """Test optimización con fallback (sin Optuna)"""
        optimizer = BayesianOptimizer(n_trials=5)
        
        def objective(params):
            # Función objetivo simple
            return params.get('x', 0) ** 2
        
        param_space = {
            'x': {'type': 'float', 'low': -5.0, 'high': 5.0}
        }
        
        # Mock para forzar fallback
        with patch('modules.heuristic_optimizer_enhanced.HAVE_OPTUNA', False):
            best_params = optimizer.optimize(objective, param_space)
        
        assert isinstance(best_params, dict)
        assert 'x' in best_params
        assert -5.0 <= best_params['x'] <= 5.0


class TestOptimizationResult:
    """Tests para OptimizationResult dataclass"""
    
    def test_optimization_result_creation(self):
        """Test creación de resultado"""
        result = OptimizationResult(
            best_params={'param1': 0.5},
            best_score=0.85,
            cv_scores=[0.8, 0.85, 0.9]
        )
        
        assert result.best_params == {'param1': 0.5}
        assert result.best_score == 0.85
        assert len(result.cv_scores) == 3


class TestHeuristicOptimizerEnhanced:
    """Tests para HeuristicOptimizerEnhanced"""
    
    @pytest.fixture
    def sample_data(self):
        """Fixture con datos de prueba"""
        return pd.DataFrame({
            'combination': [
                [1, 2, 3, 4, 5, 6],
                [10, 15, 20, 25, 30, 35],
                [5, 12, 18, 23, 31, 40],
                [7, 14, 21, 28, 35, 39],
                [2, 8, 16, 24, 32, 38]
            ],
            'fecha': pd.date_range('2020-01-01', periods=5)
        })
    
    @pytest.fixture
    def optimizer(self):
        """Fixture con optimizador"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Crear archivo CSV temporal
            df = pd.DataFrame({
                'combination': [[1, 2, 3, 4, 5, 6]] * 10
            })
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            optimizer = HeuristicOptimizerEnhanced(data_path=temp_path)
            yield optimizer
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_optimizer_creation(self, optimizer):
        """Test creación del optimizador"""
        assert isinstance(optimizer, HeuristicOptimizerEnhanced)
        assert hasattr(optimizer, 'feature_extractor')
        assert hasattr(optimizer, 'temporal_validator')
        assert hasattr(optimizer, 'bayesian_optimizer')
    
    def test_load_historical_data_csv(self, sample_data):
        """Test carga de datos CSV"""
        optimizer = HeuristicOptimizerEnhanced()
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_data.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            loaded_data = optimizer.load_historical_data(temp_path)
            
            assert len(loaded_data) == 5
            assert 'combination' in loaded_data.columns
            assert 'fecha' in loaded_data.columns
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_process_combination_column(self, optimizer):
        """Test procesamiento de columna de combinaciones"""
        # DataFrame con combinaciones en string
        df = pd.DataFrame({
            'combination': [
                '[1, 2, 3, 4, 5, 6]',
                '10, 15, 20, 25, 30, 35',
                '5 12 18 23 31 40'
            ]
        })
        
        processed_df = optimizer._process_combination_column(df)
        
        assert len(processed_df) <= 3  # Algunas pueden ser inválidas
        for combo in processed_df['combination']:
            assert isinstance(combo, list)
            assert len(combo) == 6
    
    def test_analyze_historical_patterns(self, optimizer, sample_data):
        """Test análisis de patrones históricos"""
        analysis = optimizer.analyze_historical_patterns(sample_data)
        
        assert isinstance(analysis, dict)
        assert 'timestamp' in analysis
        assert 'total_records' in analysis
        assert 'number_frequencies' in analysis
        assert 'sum_statistics' in analysis
        
        # Verificar estadísticas de suma
        sum_stats = analysis['sum_statistics']
        assert 'mean' in sum_stats
        assert 'std' in sum_stats
        assert 'min' in sum_stats
        assert 'max' in sum_stats
    
    def test_generate_predictions_fallback(self, optimizer):
        """Test generación de predicciones con fallback"""
        # Mock para simular falta de modelos entrenados
        optimizer.models = {}
        optimizer.optimized_params = {}
        
        predictions = optimizer.generate_predictions(n_predictions=3)
        
        assert len(predictions) == 3
        for pred in predictions:
            assert len(pred) == 6
            assert all(1 <= x <= 40 for x in pred)
            assert len(set(pred)) == 6  # Sin duplicados
    
    def test_create_synthetic_targets(self, optimizer):
        """Test creación de targets sintéticos"""
        combinations = [
            [1, 2, 3, 4, 5, 6],
            [10, 15, 20, 25, 30, 35],
            [5, 12, 18, 23, 31, 40]
        ]
        
        targets = optimizer._generate_synthetic_targets(combinations)
        
        assert len(targets) == 3
        assert all(t in [0, 1] for t in targets)  # Targets binarios
    
    def test_export_results(self, optimizer):
        """Test exportación de resultados"""
        # Añadir algunos datos de prueba
        optimizer.analysis_results = {'test': 'data'}
        optimizer.optimized_params = {'param1': 0.5}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            exported = optimizer.export_results(temp_dir)
            
            assert isinstance(exported, dict)
            
            # Verificar que se crearon archivos
            for file_type, file_path in exported.items():
                assert Path(file_path).exists()


class TestCachedPredictor:
    """Tests para CachedPredictor"""
    
    def test_cached_predictor_creation(self):
        """Test creación de predictor con cache"""
        predictor = CachedPredictor(cache_size=10)
        
        assert predictor.cache_size == 10
    
    def test_cache_functionality(self):
        """Test funcionalidad del cache"""
        class TestPredictor(CachedPredictor):
            def _predict_impl(self, features_hash):
                # Simulación costosa
                return hash(features_hash) % 100
        
        predictor = TestPredictor(cache_size=5)
        
        # Primera predicción
        features = np.array([[1, 2, 3, 4, 5, 6]])
        result1 = predictor.predict(features)
        
        # Segunda predicción (debería usar cache)
        result2 = predictor.predict(features)
        
        assert np.array_equal(result1, result2)
        
        # Verificar que el cache funciona
        cache_info = predictor._predict.cache_info()
        assert cache_info.hits > 0


class TestIntegration:
    """Tests de integración"""
    
    def test_optimize_heuristics_function(self):
        """Test función de conveniencia"""
        # Crear datos temporales
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'combination': [[1, 2, 3, 4, 5, 6]] * 20
            })
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            result = optimize_heuristics(
                data_path=temp_path,
                target='hit_rate',
                n_trials=5  # Pocos trials para test rápido
            )
            
            assert isinstance(result, OptimizationResult)
            assert isinstance(result.best_params, dict)
            assert isinstance(result.best_score, (int, float))
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_full_workflow(self):
        """Test workflow completo"""
        # Crear datos de prueba
        combinations = [
            [1, 2, 3, 4, 5, 6],
            [10, 15, 20, 25, 30, 35],
            [5, 12, 18, 23, 31, 40],
            [7, 14, 21, 28, 35, 39],
            [2, 8, 16, 24, 32, 38]
        ] * 4  # 20 combinaciones total
        
        df = pd.DataFrame({
            'combination': combinations,
            'fecha': pd.date_range('2020-01-01', periods=len(combinations))
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            optimizer = HeuristicOptimizerEnhanced(data_path=temp_path)
            
            # 1. Cargar datos
            data = optimizer.load_historical_data()
            assert len(data) > 0
            
            # 2. Analizar patrones
            analysis = optimizer.analyze_historical_patterns(data)
            assert 'total_records' in analysis
            
            # 3. Optimizar parámetros (versión rápida)
            result = optimizer.optimize_heuristic_parameters(n_trials=3)
            assert isinstance(result, OptimizationResult)
            
            # 4. Generar predicciones
            predictions = optimizer.generate_predictions(n_predictions=2)
            assert len(predictions) == 2
            
            # 5. Exportar resultados
            with tempfile.TemporaryDirectory() as temp_dir:
                exported = optimizer.export_results(temp_dir)
                assert len(exported) > 0
            
        finally:
            Path(temp_path).unlink(missing_ok=True)


# Tests con mocks para dependencias opcionales
class TestOptionalDependencies:
    """Tests para dependencias opcionales"""
    
    @patch('modules.heuristic_optimizer_enhanced.HAVE_OPTUNA', False)
    def test_without_optuna(self):
        """Test funcionamiento sin Optuna"""
        optimizer = BayesianOptimizer(n_trials=3)
        
        def objective(params):
            return params.get('x', 0) ** 2
        
        param_space = {
            'x': {'type': 'float', 'low': -1.0, 'high': 1.0}
        }
        
        result = optimizer.optimize(objective, param_space)
        
        assert isinstance(result, dict)
        assert 'x' in result
    
    @patch('modules.heuristic_optimizer_enhanced.HAVE_XGB', False)
    def test_without_xgboost(self):
        """Test funcionamiento sin XGBoost"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'combination': [[1, 2, 3, 4, 5, 6]] * 10
            })
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            optimizer = HeuristicOptimizerEnhanced(data_path=temp_path)
            model = optimizer.create_predictive_model(model_type='auto')
            
            # Debería usar RandomForest como fallback
            assert hasattr(model, 'fit')
            assert hasattr(model, 'predict')
            
        finally:
            Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    # Ejecutar tests directamente
    pytest.main([__file__, "-v"])
