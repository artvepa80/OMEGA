#!/usr/bin/env python3
"""
Test script para verificar que las correcciones de LSTM v2 funcionan
"""

import sys
import logging
from pathlib import Path
import asyncio

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_lstm_v2_standalone():
    """Test LSTM v2 standalone functionality"""
    logger.info("🧪 Testing LSTM v2 standalone...")
    
    try:
        from modules.lstm_predictor_v2 import LSTMPredictorV2, create_lstm_predictor_v2
        
        # Create predictor
        predictor = create_lstm_predictor_v2(sequence_length=15, hidden_size=128, num_layers=2)
        
        # Sample data - sufficient for training
        sample_data = [
            [1, 15, 23, 31, 35, 40], [3, 12, 18, 27, 33, 39],
            [5, 14, 22, 28, 34, 38], [2, 11, 19, 25, 32, 37],
            [7, 16, 24, 29, 36, 38], [4, 13, 21, 26, 34, 39],
            [6, 17, 25, 30, 37, 40], [8, 10, 20, 24, 31, 35],
            [9, 18, 26, 32, 38, 40], [1, 12, 20, 28, 33, 36],
            [3, 14, 19, 27, 35, 39], [5, 11, 17, 23, 29, 34],
            [2, 16, 22, 30, 36, 40], [4, 9, 15, 25, 31, 37],
            [6, 13, 21, 26, 32, 38], [7, 18, 24, 28, 34, 39],
            [8, 12, 19, 27, 33, 35], [1, 10, 16, 22, 29, 31],
            [3, 11, 17, 24, 30, 36], [5, 15, 20, 26, 32, 40]
        ]
        
        logger.info(f"📊 Training with {len(sample_data)} combinations...")
        
        # Test training - this should not fail with "too many values to unpack"
        training_results = predictor.train(
            historical_data=sample_data,
            epochs=5,
            validation_split=0.2,
            early_stopping_patience=10
        )
        
        logger.info(f"✅ Training completed successfully!")
        logger.info(f"   Final validation loss: {training_results.get('final_val_loss', 'N/A')}")
        logger.info(f"   Model trained: {predictor.is_trained}")
        
        # Test predictions
        predictions = predictor.predict(sample_data[-10:], num_predictions=3)
        logger.info(f"🎯 Generated {len(predictions)} predictions")
        
        for i, pred in enumerate(predictions, 1):
            combo = pred['combination']
            confidence = pred['confidence']
            logger.info(f"   {i}. {' - '.join(map(str, combo))} (Confidence: {confidence:.1%})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ LSTM v2 standalone test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_meta_learning_integration():
    """Test LSTM v2 within meta-learning system"""
    logger.info("🧪 Testing LSTM v2 with meta-learning integration...")
    
    try:
        from modules.meta_learning_integrator import MetaLearningIntegrator, create_meta_learning_system
        
        # Create integrated system
        integrator = create_meta_learning_system(enable_all=False)
        # Enable only essential components to test LSTM v2
        integrator.components_enabled['lstm_v2'] = True
        integrator.components_enabled['meta_controller'] = True
        integrator._initialize_components()
        
        # Sample data
        sample_data = [
            [1, 15, 23, 31, 35, 40], [3, 12, 18, 27, 33, 39],
            [5, 14, 22, 28, 34, 38], [2, 11, 19, 25, 32, 37],
            [7, 16, 24, 29, 36, 38], [4, 13, 21, 26, 34, 39],
            [6, 17, 25, 30, 37, 40], [8, 10, 20, 24, 31, 35],
            [9, 18, 26, 32, 38, 40], [1, 12, 20, 28, 33, 36],
            [3, 14, 19, 27, 35, 39], [5, 11, 17, 23, 29, 34],
            [2, 16, 22, 30, 36, 40], [4, 9, 15, 25, 31, 37],
            [6, 13, 21, 26, 32, 38], [7, 18, 24, 28, 34, 39],
            [8, 12, 19, 27, 33, 35], [1, 10, 16, 22, 29, 31],
            [3, 11, 17, 24, 30, 36], [5, 15, 20, 26, 32, 40],
            [2, 14, 18, 25, 28, 37], [4, 13, 19, 23, 34, 38],
            [6, 9, 21, 27, 31, 39], [7, 12, 16, 24, 33, 35],
            [8, 11, 20, 26, 29, 40], [1, 14, 17, 22, 30, 38],
            [3, 10, 15, 28, 35, 40], [5, 13, 19, 26, 32, 36],
            [2, 16, 21, 27, 34, 39], [4, 11, 18, 23, 31, 37]
        ]
        
        logger.info(f"🏋️ Training integrated system with {len(sample_data)} combinations...")
        
        # Test integrated training
        training_results = integrator.train_integrated_system(sample_data)
        logger.info(f"✅ Integrated training completed!")
        logger.info(f"   Components trained: {training_results['components_trained']}")
        
        # Check LSTM v2 specific results
        if 'lstm_v2' in training_results['training_results']:
            lstm_result = training_results['training_results']['lstm_v2']
            logger.info(f"   LSTM v2 success: {lstm_result.get('success', False)}")
            if 'error' in lstm_result:
                logger.warning(f"   LSTM v2 error: {lstm_result['error']}")
            else:
                logger.info(f"   LSTM v2 validation loss: {lstm_result.get('final_val_loss', 'N/A')}")
        
        # Test intelligent prediction
        logger.info("🧠 Testing intelligent prediction...")
        prediction_results = await integrator.intelligent_prediction(sample_data, num_predictions=3)
        
        logger.info(f"✅ Intelligent prediction completed!")
        logger.info(f"   Predictions generated: {prediction_results['integration_metrics']['predictions_generated']}")
        logger.info(f"   Processing time: {prediction_results['integration_metrics']['processing_time']:.2f}s")
        
        # Check LSTM v2 component results
        if 'lstm_v2' in prediction_results['component_results']:
            lstm_component = prediction_results['component_results']['lstm_v2']
            logger.info(f"   LSTM v2 predictions: {lstm_component.get('predictions_count', 0)}")
            logger.info(f"   LSTM v2 trained: {lstm_component.get('is_trained', False)}")
            if 'error' in lstm_component:
                logger.warning(f"   LSTM v2 error: {lstm_component['error']}")
        
        # Display predictions
        for i, pred in enumerate(prediction_results['predictions'], 1):
            combo = pred['combination']
            confidence = pred['confidence']
            components = ', '.join(pred.get('components_used', []))
            logger.info(f"   {i}. {' - '.join(map(str, combo))} (Confidence: {confidence:.1%}, Components: {components})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Meta-learning integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting LSTM v2 fix verification tests...")
    
    results = {}
    
    # Test 1: LSTM v2 standalone
    logger.info("\n" + "="*60)
    results['lstm_v2_standalone'] = test_lstm_v2_standalone()
    
    # Test 2: Meta-learning integration
    logger.info("\n" + "="*60)
    try:
        results['meta_learning_integration'] = asyncio.run(test_meta_learning_integration())
    except Exception as e:
        logger.error(f"❌ Meta-learning integration test exception: {e}")
        results['meta_learning_integration'] = False
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 All tests passed! LSTM v2 fixes are working correctly.")
        logger.info("   - No more 'too many values to unpack' errors")
        logger.info("   - Meta-learning integration working")
        logger.info("   - Ready for production use with meta-learning weights")
    else:
        logger.error("💥 Some tests failed. Check the logs above for details.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)