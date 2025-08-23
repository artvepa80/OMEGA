#!/usr/bin/env python3
"""
ML Model Validation Suite for OMEGA PRO AI
Tests all ML models to identify and fix issues
"""

import sys
import os
import logging
import traceback
import numpy as np
import pandas as pd
import torch
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gboost_classifier():
    """Test GBoost Jackpot Classifier"""
    logger.info("Testing GBoost Classifier...")
    try:
        from modules.learning.gboost_jackpot_classifier import GBoostJackpotClassifier
        
        # Create test data
        X_train = [[1, 5, 10, 15, 20, 25], [2, 6, 11, 16, 21, 26], [3, 7, 12, 17, 22, 27]]
        y_train = [0, 1, 0]
        
        X_test = [[4, 8, 13, 18, 23, 28], [5, 9, 14, 19, 24, 29]]
        
        # Initialize and train
        clf = GBoostJackpotClassifier(n_estimators=10, random_state=42)
        clf.fit(X_train, y_train)
        
        # Test predictions
        predictions = clf.predict(X_test)
        probas = clf.predict_proba(X_test)
        
        # Test evaluation
        metrics = clf.evaluate(X_test, [0, 1])
        
        logger.info(f"✅ GBoost Classifier: Predictions={predictions}, Accuracy={metrics['accuracy']:.4f}")
        return True
        
    except Exception as e:
        logger.error(f"❌ GBoost Classifier failed: {e}")
        logger.error(traceback.format_exc())
        return False

def test_lstm_model():
    """Test LSTM Model"""
    logger.info("Testing LSTM Model...")
    try:
        from modules.lstm_model import generar_combinaciones_lstm, LSTMConfig
        
        # Create test data
        np.random.seed(42)
        data = np.random.randint(1, 41, (50, 6))
        historial_set = {tuple(row) for row in data[:30]}
        
        # Test with default config
        config = {"n_steps": 3, "epochs": 2, "batch_size": 8}
        results = generar_combinaciones_lstm(
            data=data,
            historial_set=historial_set,
            cantidad=5,
            config=config
        )
        
        assert len(results) == 5, f"Expected 5 combinations, got {len(results)}"
        assert all('combination' in r and len(r['combination']) == 6 for r in results), "Invalid combinations"
        
        logger.info(f"✅ LSTM Model: Generated {len(results)} valid combinations")
        return True
        
    except Exception as e:
        logger.error(f"❌ LSTM Model failed: {e}")
        logger.error(traceback.format_exc())
        return False

def test_transformer_model():
    """Test Transformer Model"""
    logger.info("Testing Transformer Model...")
    try:
        from modules.transformer_model import generar_combinaciones_transformer
        
        # Create test DataFrame
        np.random.seed(42)
        data = np.random.randint(1, 41, (20, 6))
        historial_df = pd.DataFrame(data, columns=[f'Bolilla {i+1}' for i in range(6)])
        historial_df['fecha'] = pd.date_range('2020-01-01', periods=20, freq='D')
        
        # Test transformer generation
        results = generar_combinaciones_transformer(
            historial_df=historial_df,
            cantidad=5,
            train_model_if_missing=False  # Don't train to avoid complexity
        )
        
        assert len(results) >= 1, f"Expected at least 1 combination, got {len(results)}"
        assert all('combination' in r and len(r['combination']) == 6 for r in results), "Invalid combinations"
        
        logger.info(f"✅ Transformer Model: Generated {len(results)} valid combinations")
        return True
        
    except Exception as e:
        logger.error(f"❌ Transformer Model failed: {e}")
        logger.error(traceback.format_exc())
        return False

def test_arima_cycles():
    """Test ARIMA Cycles Model"""
    logger.info("Testing ARIMA Cycles...")
    try:
        from modules.arima_cycles import arima_cycles, analyze_cycles, predict_cycles
        
        # Test with sample data
        test_data = [1.0, 1.2, 0.8, 1.5, 0.9, 1.1, 1.3, 0.7, 1.4, 1.0]
        
        # Test basic arima_cycles function
        score = arima_cycles(test_data)
        assert isinstance(score, float) and 0.1 <= score <= 2.5, f"Invalid ARIMA score: {score}"
        
        # Test analyze_cycles
        analysis = analyze_cycles(test_data)
        assert isinstance(analysis, float), f"Invalid analysis result: {analysis}"
        
        # Test predict_cycles
        predictions = predict_cycles(test_data, periods=6)
        assert len(predictions) == 6, f"Expected 6 predictions, got {len(predictions)}"
        assert all(isinstance(p, float) and 0 <= p <= 1 for p in predictions), "Invalid predictions"
        
        logger.info(f"✅ ARIMA Cycles: Score={score:.4f}, Predictions={len(predictions)}")
        return True
        
    except Exception as e:
        logger.error(f"❌ ARIMA Cycles failed: {e}")
        logger.error(traceback.format_exc())
        return False

def test_lottery_transformer():
    """Test LotteryTransformer class directly"""
    logger.info("Testing LotteryTransformer class...")
    try:
        from modules.lottery_transformer import LotteryTransformer
        
        # Create model
        model = LotteryTransformer(num_numbers=40, d_model=64, nhead=2, num_layers=2)
        model.eval()
        
        # Create test inputs
        batch_size, seq_len, num_count = 2, 5, 6
        numbers = torch.randint(1, 41, (batch_size, seq_len, num_count))
        temporal = torch.randn(batch_size, seq_len, 3)
        positions = torch.arange(seq_len).unsqueeze(0).expand(batch_size, -1)
        
        # Test forward pass
        with torch.no_grad():
            num_logits, sum_pred = model(numbers, temporal, positions)
        
        # Validate outputs
        expected_num_shape = (batch_size, num_count, 40)
        expected_sum_shape = (batch_size, 1)
        
        assert num_logits.shape == expected_num_shape, f"Expected {expected_num_shape}, got {num_logits.shape}"
        assert sum_pred.shape == expected_sum_shape, f"Expected {expected_sum_shape}, got {sum_pred.shape}"
        
        logger.info(f"✅ LotteryTransformer: Output shapes correct")
        return True
        
    except Exception as e:
        logger.error(f"❌ LotteryTransformer failed: {e}")
        logger.error(traceback.format_exc())
        return False

def test_score_dynamics():
    """Test Score Dynamics module"""
    logger.info("Testing Score Dynamics...")
    try:
        from modules.score_dynamics import score_combinations
        
        # Create test combinations
        combinations = [
            {"combination": [1, 5, 10, 15, 20, 25], "source": "test", "score": 0.5},
            {"combination": [2, 6, 11, 16, 21, 26], "source": "test", "score": 0.6}
        ]
        
        # Create test historial
        historial = np.random.randint(1, 41, (20, 6))
        
        # Test scoring
        scored_combinations = score_combinations(combinations, historial)
        
        assert len(scored_combinations) == len(combinations), "Mismatch in combination count"
        assert all('score' in c for c in scored_combinations), "Missing scores"
        
        logger.info(f"✅ Score Dynamics: Scored {len(scored_combinations)} combinations")
        return True
        
    except Exception as e:
        logger.error(f"❌ Score Dynamics failed: {e}")
        logger.error(traceback.format_exc())
        return False

def run_model_optimization():
    """Run model optimization and hyperparameter tuning"""
    logger.info("Running model optimization...")
    try:
        # Test different hyperparameter configurations
        configs_to_test = [
            {"n_estimators": 50, "learning_rate": 0.1, "max_depth": 3},
            {"n_estimators": 100, "learning_rate": 0.05, "max_depth": 5},
            {"n_estimators": 200, "learning_rate": 0.01, "max_depth": 7}
        ]
        
        best_config = None
        best_score = 0
        
        for config in configs_to_test:
            try:
                from modules.learning.gboost_jackpot_classifier import GBoostJackpotClassifier
                
                # Create test data
                X_train = [[i, i+5, i+10, i+15, i+20, i+25] for i in range(1, 21)]
                y_train = [i % 2 for i in range(20)]
                X_test = [[i, i+5, i+10, i+15, i+20, i+25] for i in range(21, 26)]
                y_test = [i % 2 for i in range(5)]
                
                clf = GBoostJackpotClassifier(**config, random_state=42)
                clf.fit(X_train, y_train)
                metrics = clf.evaluate(X_test, y_test)
                
                if metrics['accuracy'] > best_score:
                    best_score = metrics['accuracy']
                    best_config = config
                    
                logger.info(f"Config {config}: Accuracy = {metrics['accuracy']:.4f}")
                
            except Exception as e:
                logger.warning(f"Config {config} failed: {e}")
                continue
        
        logger.info(f"✅ Best config: {best_config} with accuracy {best_score:.4f}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Model optimization failed: {e}")
        return False

def main():
    """Run all model validation tests"""
    logger.info("🚀 Starting ML Model Validation Suite...")
    
    test_results = {
        "GBoost Classifier": test_gboost_classifier(),
        "LSTM Model": test_lstm_model(),
        "Transformer Model": test_transformer_model(),
        "ARIMA Cycles": test_arima_cycles(),
        "LotteryTransformer": test_lottery_transformer(),
        "Score Dynamics": test_score_dynamics(),
        "Model Optimization": run_model_optimization()
    }
    
    # Summary
    passed = sum(test_results.values())
    total = len(test_results)
    
    logger.info(f"\n📊 VALIDATION SUMMARY:")
    logger.info(f"   Passed: {passed}/{total}")
    logger.info(f"   Failed: {total - passed}/{total}")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    if passed == total:
        logger.info("🎉 All models are working correctly!")
        return 0
    else:
        logger.warning(f"⚠️  {total - passed} model(s) need attention")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)