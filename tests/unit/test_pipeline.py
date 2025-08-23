#!/usr/bin/env python3
"""
🧪 Tests para PredictionPipeline
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from src.core.pipeline import PredictionPipeline, PredictionResult

@pytest.mark.asyncio
class TestPredictionPipeline:
    """Tests para el pipeline de predicción"""
    
    async def test_pipeline_initialization(self, mock_data_service, mock_ensemble_manager):
        """Test de inicialización del pipeline"""
        prediction_service = Mock()
        learning_engine = Mock()
        metrics = Mock()
        
        pipeline = PredictionPipeline(
            data_service=mock_data_service,
            prediction_service=prediction_service,
            ensemble_manager=mock_ensemble_manager,
            learning_engine=learning_engine,
            metrics=metrics
        )
        
        assert pipeline.data_service == mock_data_service
        assert pipeline.ensemble_manager == mock_ensemble_manager
        assert pipeline.prediction_service == prediction_service
    
    async def test_generate_predictions_success(self, mock_data_service, mock_ensemble_manager):
        """Test de generación exitosa de predicciones"""
        # Setup mocks
        prediction_service = Mock()
        learning_engine = Mock()
        metrics = Mock()
        
        mock_ensemble_manager.get_active_models.return_value = ["neural_enhanced", "lstm_v2"]
        mock_ensemble_manager.get_model_weights.return_value = {"neural_enhanced": 0.6, "lstm_v2": 0.4}
        
        # Mock para modelos
        mock_model = AsyncMock()
        mock_model.predict.return_value = [
            {'combination': [1, 15, 23, 31, 35, 40], 'confidence': 0.8},
            {'combination': [3, 12, 19, 26, 33, 38], 'confidence': 0.7}
        ]
        mock_model.get_version.return_value = "1.0"
        mock_model.get_training_date.return_value = "2025-01-01"
        
        mock_ensemble_manager.get_model.return_value = mock_model
        mock_data_service.calculate_svi_batch.return_value = [0.75, 0.68]
        
        pipeline = PredictionPipeline(
            data_service=mock_data_service,
            prediction_service=prediction_service,
            ensemble_manager=mock_ensemble_manager,
            learning_engine=learning_engine,
            metrics=metrics
        )
        
        # Ejecutar test
        historical_data = [{'fecha': '2025-01-01', 'bolilla_1': 1}]
        results = await pipeline.generate_predictions(historical_data, 2)
        
        # Verificaciones
        assert len(results) <= 2  # Target count
        assert all(isinstance(r, PredictionResult) for r in results)
        
        # Verificar que se llamaron los métodos correctos
        mock_ensemble_manager.get_active_models.assert_called_once()
        mock_data_service.calculate_svi_batch.assert_called_once()
    
    async def test_model_prediction_failure_handling(self, mock_data_service, mock_ensemble_manager):
        """Test de manejo de fallos en modelos"""
        prediction_service = Mock()
        learning_engine = Mock()
        metrics = Mock()
        
        mock_ensemble_manager.get_active_models.return_value = ["failing_model", "working_model"]
        
        # Mock para modelo que falla
        failing_model = AsyncMock()
        failing_model.predict.side_effect = Exception("Model error")
        
        # Mock para modelo que funciona
        working_model = AsyncMock()
        working_model.predict.return_value = [
            {'combination': [1, 15, 23, 31, 35, 40], 'confidence': 0.8}
        ]
        working_model.get_version.return_value = "1.0"
        working_model.get_training_date.return_value = "2025-01-01"
        
        def mock_get_model(name):
            return failing_model if name == "failing_model" else working_model
        
        mock_ensemble_manager.get_model.side_effect = mock_get_model
        mock_data_service.calculate_svi_batch.return_value = [0.75]
        
        pipeline = PredictionPipeline(
            data_service=mock_data_service,
            prediction_service=prediction_service,
            ensemble_manager=mock_ensemble_manager,
            learning_engine=learning_engine,
            metrics=metrics
        )
        
        # El pipeline debería continuar aunque un modelo falle
        historical_data = [{'fecha': '2025-01-01'}]
        results = await pipeline.generate_predictions(historical_data, 1)
        
        # Debe tener resultados del modelo que funciona
        assert len(results) > 0
    
    async def test_ensemble_logic(self, mock_data_service, mock_ensemble_manager):
        """Test de lógica de ensemble"""
        prediction_service = Mock()
        learning_engine = Mock()
        metrics = Mock()
        
        mock_ensemble_manager.get_model_weights.return_value = {
            "model_a": 0.6,
            "model_b": 0.4
        }
        
        pipeline = PredictionPipeline(
            data_service=mock_data_service,
            prediction_service=prediction_service,
            ensemble_manager=mock_ensemble_manager,
            learning_engine=learning_engine,
            metrics=metrics
        )
        
        # Crear predicciones con la misma combinación de diferentes modelos
        predictions = [
            PredictionResult(
                combination=[1, 2, 3, 4, 5, 6],
                confidence=0.8,
                source_model="model_a",
                svi_score=0.0,
                metadata={}
            ),
            PredictionResult(
                combination=[1, 2, 3, 4, 5, 6],  # Misma combinación
                confidence=0.6,
                source_model="model_b",
                svi_score=0.0,
                metadata={}
            ),
            PredictionResult(
                combination=[7, 8, 9, 10, 11, 12],  # Diferente combinación
                confidence=0.7,
                source_model="model_a",
                svi_score=0.0,
                metadata={}
            )
        ]
        
        ensemble_results = await pipeline._apply_ensemble_logic(predictions)
        
        # Debe combinar las predicciones duplicadas
        assert len(ensemble_results) == 2  # 2 combinaciones únicas
        
        # La combinación [1,2,3,4,5,6] debe tener confianza weighted
        combo_123456 = next(r for r in ensemble_results if r.combination == [1, 2, 3, 4, 5, 6])
        # Weighted average: (0.8 * 0.6 + 0.6 * 0.4) / (0.6 + 0.4) = 0.72
        assert abs(combo_123456.confidence - 0.72) < 0.01
    
    async def test_svi_calculation(self, mock_data_service, mock_ensemble_manager):
        """Test de cálculo de SVI"""
        prediction_service = Mock()
        learning_engine = Mock()
        metrics = Mock()
        
        mock_data_service.calculate_svi_batch.return_value = [0.8, 0.6, 0.7]
        
        pipeline = PredictionPipeline(
            data_service=mock_data_service,
            prediction_service=prediction_service,
            ensemble_manager=mock_ensemble_manager,
            learning_engine=learning_engine,
            metrics=metrics
        )
        
        predictions = [
            PredictionResult([1, 2, 3, 4, 5, 6], 0.9, "model_a", 0.0, {}),
            PredictionResult([7, 8, 9, 10, 11, 12], 0.7, "model_b", 0.0, {}),
            PredictionResult([13, 14, 15, 16, 17, 18], 0.6, "model_c", 0.0, {})
        ]
        
        results = await pipeline._calculate_svi_scores(predictions)
        
        # Verificar que se asignaron los scores SVI
        assert results[0].svi_score == 0.8
        assert results[1].svi_score == 0.6
        assert results[2].svi_score == 0.7
        
        # Verificar que se calculó el score final
        for result in results:
            expected_final = (result.confidence * 0.7) + (result.svi_score * 0.3)
            assert abs(result.final_score - expected_final) < 0.01
    
    async def test_svi_calculation_fallback(self, mock_data_service, mock_ensemble_manager):
        """Test de fallback cuando falla el cálculo SVI"""
        prediction_service = Mock()
        learning_engine = Mock()
        metrics = Mock()
        
        # Mock que falla
        mock_data_service.calculate_svi_batch.side_effect = Exception("SVI calculation failed")
        
        pipeline = PredictionPipeline(
            data_service=mock_data_service,
            prediction_service=prediction_service,
            ensemble_manager=mock_ensemble_manager,
            learning_engine=learning_engine,
            metrics=metrics
        )
        
        predictions = [
            PredictionResult([1, 2, 3, 4, 5, 6], 0.8, "model_a", 0.0, {})
        ]
        
        # No debe fallar, debe usar fallback
        results = await pipeline._calculate_svi_scores(predictions)
        
        # Debe usar la confianza como SVI fallback
        assert results[0].svi_score == 0.8
        assert results[0].final_score == 0.8
    
    async def test_best_predictions_selection(self, mock_data_service, mock_ensemble_manager):
        """Test de selección de mejores predicciones"""
        prediction_service = Mock()
        learning_engine = Mock()
        metrics = Mock()
        
        pipeline = PredictionPipeline(
            data_service=mock_data_service,
            prediction_service=prediction_service,
            ensemble_manager=mock_ensemble_manager,
            learning_engine=learning_engine,
            metrics=metrics
        )
        
        predictions = [
            PredictionResult([1, 2, 3, 4, 5, 6], 0.9, "model_a", 0.8, {}),
            PredictionResult([7, 8, 9, 10, 11, 12], 0.8, "model_b", 0.7, {}),
            PredictionResult([13, 14, 15, 16, 17, 18], 0.7, "model_c", 0.6, {}),
            PredictionResult([19, 20, 21, 22, 23, 24], 0.6, "model_d", 0.5, {}),
            PredictionResult([25, 26, 27, 28, 29, 30], 0.5, "model_e", 0.4, {})
        ]
        
        # Calcular final scores
        for pred in predictions:
            pred.final_score = (pred.confidence * 0.7) + (pred.svi_score * 0.3)
        
        results = await pipeline._select_best_predictions(predictions, 3)
        
        assert len(results) == 3
        # Deben estar ordenadas por final_score descendente
        assert results[0].final_score >= results[1].final_score >= results[2].final_score
    
    async def test_prediction_validation(self, mock_data_service, mock_ensemble_manager):
        """Test de validación de predicciones"""
        prediction_service = Mock()
        learning_engine = Mock()
        metrics = Mock()
        
        pipeline = PredictionPipeline(
            data_service=mock_data_service,
            prediction_service=prediction_service,
            ensemble_manager=mock_ensemble_manager,
            learning_engine=learning_engine,
            metrics=metrics
        )
        
        predictions = [
            PredictionResult([1, 2, 3, 4, 5, 6], 0.8, "model_a", 0.7, {}),  # Válida
            PredictionResult([1, 2, 3, 4, 5], 0.7, "model_b", 0.6, {}),     # Inválida: 5 números
            PredictionResult([1, 2, 3, 4, 5, 41], 0.9, "model_c", 0.8, {}), # Inválida: fuera de rango
            PredictionResult([7, 8, 9, 10, 11, 12], 0.6, "model_d", 0.5, {}) # Válida
        ]
        
        valid_predictions = await pipeline.validate_predictions(predictions)
        
        assert len(valid_predictions) == 2
        assert valid_predictions[0].combination == [1, 2, 3, 4, 5, 6]
        assert valid_predictions[1].combination == [7, 8, 9, 10, 11, 12]