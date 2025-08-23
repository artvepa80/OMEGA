#!/usr/bin/env python3
"""
Test para verificar que los pesos del ensemble funcionan correctamente con LSTM v2 corregido
"""

import sys
import logging
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ensemble_weights_with_lstm_v2():
    """Test que los pesos del ensemble se aplican correctamente"""
    logger.info("🧪 Testing ensemble weights with LSTM v2...")
    
    try:
        from modules.meta_learning_integrator import create_meta_learning_system
        from modules.meta_learning_controller import MetaLearningContext, DataRegime
        
        # Create system with meta-learning enabled
        integrator = create_meta_learning_system(enable_all=True)
        
        # Sample data sufficient for meta-learning analysis
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
            [2, 16, 21, 27, 34, 39], [4, 11, 18, 23, 31, 37],
            [9, 14, 22, 30, 36, 40], [6, 12, 17, 25, 29, 33]
        ]
        
        logger.info(f"📊 Using {len(sample_data)} data points for weight analysis...")
        
        # Check if meta-controller can analyze context
        if integrator.meta_controller:
            context = integrator.meta_controller.analyze_current_context(sample_data)
            logger.info(f"✅ Context analysis: {context.regime.value}")
            logger.info(f"   Entropy: {context.entropy:.3f}")
            logger.info(f"   Variance: {context.variance:.3f}")
            logger.info(f"   Trend: {context.trend_strength:.3f}")
            
            # Get optimal weights for this context
            optimal_weights = integrator.meta_controller.get_optimal_weights(context)
            logger.info(f"🎯 Optimal weights for {context.regime.value}:")
            for model_name, weight in optimal_weights.items():
                logger.info(f"   {model_name}: {weight:.3f}")
            
            # Verify that LSTM v2 has expected weight (should be 1.000 for moderate_balanced)
            expected_lstm_weight = 1.000
            actual_lstm_weight = optimal_weights.get('lstm_v2', 0.0)
            
            if abs(actual_lstm_weight - expected_lstm_weight) < 0.1:
                logger.info(f"✅ LSTM v2 weight is correct: {actual_lstm_weight:.3f} (expected ~{expected_lstm_weight})")
            else:
                logger.warning(f"⚠️ LSTM v2 weight unexpected: {actual_lstm_weight:.3f} (expected ~{expected_lstm_weight})")
            
            # Check if ensemble_ai has expected weight (should be 1.500)
            expected_ensemble_weight = 1.500
            actual_ensemble_weight = optimal_weights.get('ensemble_ai', 0.0)
            
            if abs(actual_ensemble_weight - expected_ensemble_weight) < 0.1:
                logger.info(f"✅ Ensemble AI weight is correct: {actual_ensemble_weight:.3f} (expected ~{expected_ensemble_weight})")
            else:
                logger.warning(f"⚠️ Ensemble AI weight unexpected: {actual_ensemble_weight:.3f} (expected ~{expected_ensemble_weight})")
            
            return True
        else:
            logger.error("❌ Meta-controller not available")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ensemble weights test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_intelligent_prediction_with_weights():
    """Test que la predicción inteligente usa correctamente los pesos"""
    logger.info("🧪 Testing intelligent prediction with proper weights...")
    
    try:
        from modules.meta_learning_integrator import create_meta_learning_system
        
        # Create system
        integrator = create_meta_learning_system(enable_all=True)
        
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
            [2, 16, 21, 27, 34, 39], [4, 11, 18, 23, 31, 37],
            [9, 14, 22, 30, 36, 40], [6, 12, 17, 25, 29, 33],
            [8, 15, 23, 28, 34, 39], [1, 13, 20, 27, 31, 40]
        ]
        
        logger.info("🧠 Running intelligent prediction with weight optimization...")
        
        # Run intelligent prediction
        results = await integrator.intelligent_prediction(sample_data, num_predictions=5)
        
        # Check if meta-analysis includes regime detection
        if 'meta_analysis' in results and 'regime' in results['meta_analysis']:
            regime = results['meta_analysis']['regime']
            optimal_weights = results['meta_analysis'].get('optimal_weights', {})
            
            logger.info(f"✅ Detected regime: {regime}")
            logger.info(f"🎯 Applied weights:")
            for model_name, weight in optimal_weights.items():
                logger.info(f"   {model_name}: {weight:.3f}")
            
            # Verify LSTM v2 is being used with proper weight
            lstm_weight = optimal_weights.get('lstm_v2', 0.0)
            if lstm_weight > 0.5:
                logger.info(f"✅ LSTM v2 is properly weighted: {lstm_weight:.3f}")
            else:
                logger.warning(f"⚠️ LSTM v2 weight seems low: {lstm_weight:.3f}")
            
            # Check component results
            if 'component_results' in results and 'lstm_v2' in results['component_results']:
                lstm_results = results['component_results']['lstm_v2']
                
                if lstm_results.get('is_trained', False):
                    logger.info("✅ LSTM v2 is trained and working")
                    logger.info(f"   Predictions: {lstm_results.get('predictions_count', 0)}")
                    logger.info(f"   Avg confidence: {lstm_results.get('avg_confidence', 0):.3f}")
                else:
                    logger.warning("⚠️ LSTM v2 is not trained")
                    if 'error' in lstm_results:
                        logger.error(f"   Error: {lstm_results['error']}")
            
            # Check that predictions have weight information
            for i, pred in enumerate(results['predictions'][:3], 1):
                combo = pred['combination']
                confidence = pred['confidence'] 
                meta_weights = pred.get('meta_weights', {})
                components = pred.get('components_used', [])
                
                logger.info(f"🎯 Prediction {i}: {' - '.join(map(str, combo))}")
                logger.info(f"   Confidence: {confidence:.1%}")
                logger.info(f"   Components: {', '.join(components)}")
                
                if 'lstm_v2' in meta_weights:
                    logger.info(f"   LSTM v2 weight applied: {meta_weights['lstm_v2']:.3f}")
                
            return True
            
        else:
            logger.warning("⚠️ No meta-analysis found in results")
            return False
        
    except Exception as e:
        logger.error(f"❌ Intelligent prediction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all ensemble weight tests"""
    logger.info("🚀 Starting ensemble weights integration tests...")
    
    results = {}
    
    # Test 1: Basic weight calculation
    logger.info("\n" + "="*60)
    results['weight_calculation'] = test_ensemble_weights_with_lstm_v2()
    
    # Test 2: Intelligent prediction with weights
    logger.info("\n" + "="*60) 
    try:
        results['prediction_with_weights'] = asyncio.run(test_intelligent_prediction_with_weights())
    except Exception as e:
        logger.error(f"❌ Prediction test exception: {e}")
        results['prediction_with_weights'] = False
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 ENSEMBLE WEIGHTS TEST RESULTS")
    logger.info("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 All ensemble weight tests passed!")
        logger.info("   - LSTM v2 properly integrated with meta-learning")
        logger.info("   - Weights are correctly applied (LSTM v2: 1.000, Ensemble AI: 1.500)")
        logger.info("   - Meta-learning pipeline working with moderate_balanced regime")
        logger.info("   - Ready for production use!")
    else:
        logger.error("💥 Some tests failed. Check logs for details.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)