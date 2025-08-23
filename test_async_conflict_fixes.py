#!/usr/bin/env python3
"""
Test Script: Async Event Loop Conflict Resolution
Tests the fixed async execution patterns in OMEGA AI system
"""

import sys
import os
import logging
import asyncio
import threading
import time
from typing import Dict, Any, List

# Add project root to path
sys.path.append('/Users/user/Documents/OMEGA_PRO_AI_v10.1')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/Users/user/Documents/OMEGA_PRO_AI_v10.1/async_conflict_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_async_utils():
    """Test the new async utilities"""
    logger.info("🧪 Testing async utilities...")
    
    try:
        from utils.async_utils import (
            safe_run_async, 
            is_async_context, 
            AsyncContext,
            async_manager
        )
        
        # Test 1: Basic safe_run_async
        async def simple_async_task():
            await asyncio.sleep(0.1)
            return "async_task_result"
        
        result = safe_run_async(simple_async_task())
        assert result == "async_task_result", f"Expected 'async_task_result', got {result}"
        logger.info("✅ Test 1 passed: Basic safe_run_async")
        
        # Test 2: Nested event loop handling
        async def nested_async_call():
            # This should work even from within an event loop
            return safe_run_async(simple_async_task())
        
        # Test from within an event loop
        async def test_from_event_loop():
            return await nested_async_call()
        
        # This will test the thread pool execution path
        nested_result = safe_run_async(test_from_event_loop())
        logger.info(f"✅ Test 2 passed: Nested event loop handling - {nested_result}")
        
        # Test 3: AsyncContext
        with AsyncContext() as ctx:
            context_result = ctx.run(simple_async_task())
            assert context_result == "async_task_result"
        logger.info("✅ Test 3 passed: AsyncContext")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Async utils test failed: {e}")
        return False

def test_adaptive_learning_system():
    """Test the Adaptive Learning System with fixed async patterns"""
    logger.info("🧪 Testing Adaptive Learning System...")
    
    try:
        from modules.adaptive_learning_system import AdaptiveLearningSystem
        
        # Create sample data
        sample_data = [
            [1, 15, 23, 28, 35, 40],
            [2, 12, 19, 31, 36, 39],
            [7, 14, 18, 25, 32, 38],
            [3, 11, 22, 29, 34, 37],
            [5, 16, 21, 27, 33, 41]
        ]
        
        # Test async execution
        adaptive_system = AdaptiveLearningSystem()
        
        # This should work without event loop conflicts
        from utils.async_utils import safe_run_async
        
        predictions = safe_run_async(
            adaptive_system.generate_adaptive_predictions(sample_data, 5)
        )
        
        assert 'predictions' in predictions, "Missing predictions key"
        assert len(predictions['predictions']) > 0, "No predictions generated"
        
        logger.info(f"✅ Adaptive Learning System test passed - Generated {len(predictions['predictions'])} predictions")
        
        # Test from within an async context
        async def test_adaptive_from_async():
            result = safe_run_async(
                adaptive_system.generate_adaptive_predictions(sample_data, 3)
            )
            return result
        
        async_result = safe_run_async(test_adaptive_from_async())
        logger.info("✅ Adaptive Learning System works from async context")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Adaptive Learning System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_ensemble_system():
    """Test the AI Ensemble System with fixed async patterns"""
    logger.info("🧪 Testing AI Ensemble System...")
    
    try:
        from modules.ai_ensemble_system import AIEnsembleSystem, generate_intelligent_predictions
        
        # Create sample data
        sample_data = [
            [1, 15, 23, 28, 35, 40],
            [2, 12, 19, 31, 36, 39],
            [7, 14, 18, 25, 32, 38],
            [3, 11, 22, 29, 34, 37],
            [5, 16, 21, 27, 33, 41]
        ]
        
        # Test ensemble system
        ensemble_system = AIEnsembleSystem()
        ensemble_system.train_ensemble(sample_data)
        
        # This should work without event loop conflicts
        from utils.async_utils import safe_run_async
        
        predictions = safe_run_async(
            generate_intelligent_predictions(ensemble_system, sample_data, 5)
        )
        
        assert isinstance(predictions, list), "Predictions should be a list"
        logger.info(f"✅ AI Ensemble System test passed - Generated {len(predictions)} predictions")
        
        # Test from within an async context
        async def test_ensemble_from_async():
            result = safe_run_async(
                generate_intelligent_predictions(ensemble_system, sample_data, 3)
            )
            return result
        
        async_result = safe_run_async(test_ensemble_from_async())
        logger.info("✅ AI Ensemble System works from async context")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AI Ensemble System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_predictor_integration():
    """Test the main predictor with both systems integrated"""
    logger.info("🧪 Testing Predictor integration...")
    
    try:
        # Import and test the main predictor
        from core.predictor import HybridOmegaPredictor
        
        # Create sample data file content
        import pandas as pd
        
        sample_df = pd.DataFrame({
            'Numero_1': [1, 2, 7, 3, 5],
            'Numero_2': [15, 12, 14, 11, 16],
            'Numero_3': [23, 19, 18, 22, 21],
            'Numero_4': [28, 31, 25, 29, 27],
            'Numero_5': [35, 36, 32, 34, 33],
            'Numero_6': [40, 39, 38, 37, 41]
        })
        
        # Create predictor instance
        predictor = HybridOmegaPredictor('/tmp/test_data.csv', debug=True)
        predictor.data = sample_df  # Mock data
        
        # Test adaptive learning mode
        adaptive_results = predictor.predict_adaptive_learning(max_comb=3)
        logger.info(f"✅ Predictor adaptive learning: {len(adaptive_results)} results")
        
        # Test AI ensemble mode
        ensemble_results = predictor.predict_ai_ensemble(max_comb=3)
        logger.info(f"✅ Predictor AI ensemble: {len(ensemble_results)} results")
        
        logger.info("✅ Predictor integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Predictor integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_concurrent_execution():
    """Test concurrent execution of multiple async operations"""
    logger.info("🧪 Testing concurrent async execution...")
    
    try:
        from utils.async_utils import safe_run_async
        from modules.adaptive_learning_system import AdaptiveLearningSystem
        from modules.ai_ensemble_system import AIEnsembleSystem, generate_intelligent_predictions
        
        # Sample data
        sample_data = [
            [1, 15, 23, 28, 35, 40],
            [2, 12, 19, 31, 36, 39],
            [7, 14, 18, 25, 32, 38]
        ]
        
        # Create systems
        adaptive_system = AdaptiveLearningSystem()
        ensemble_system = AIEnsembleSystem()
        ensemble_system.train_ensemble(sample_data)
        
        # Test concurrent execution
        async def concurrent_test():
            # Run both systems concurrently
            adaptive_task = adaptive_system.generate_adaptive_predictions(sample_data, 3)
            ensemble_task = generate_intelligent_predictions(ensemble_system, sample_data, 3)
            
            # Use asyncio.gather for concurrent execution
            from utils.async_utils import safe_gather
            adaptive_result, ensemble_result = await safe_gather(
                adaptive_task,
                ensemble_task,
                return_exceptions=True
            )
            
            return adaptive_result, ensemble_result
        
        adaptive_result, ensemble_result = safe_run_async(concurrent_test())
        
        # Validate results
        if isinstance(adaptive_result, Exception):
            logger.error(f"Adaptive concurrent test failed: {adaptive_result}")
            return False
            
        if isinstance(ensemble_result, Exception):
            logger.error(f"Ensemble concurrent test failed: {ensemble_result}")
            return False
        
        logger.info("✅ Concurrent execution test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Concurrent execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_threading_safety():
    """Test thread safety of async execution"""
    logger.info("🧪 Testing thread safety...")
    
    try:
        from utils.async_utils import safe_run_async
        from modules.adaptive_learning_system import AdaptiveLearningSystem
        
        adaptive_system = AdaptiveLearningSystem()
        sample_data = [
            [1, 15, 23, 28, 35, 40],
            [2, 12, 19, 31, 36, 39]
        ]
        
        results = []
        errors = []
        
        def thread_worker(thread_id):
            """Worker function for thread testing"""
            try:
                result = safe_run_async(
                    adaptive_system.generate_adaptive_predictions(sample_data, 2)
                )
                results.append(f"Thread-{thread_id}: {len(result.get('predictions', []))}")
            except Exception as e:
                errors.append(f"Thread-{thread_id}: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=thread_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        if errors:
            logger.error(f"❌ Thread safety test failed: {errors}")
            return False
        
        logger.info(f"✅ Thread safety test passed: {results}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Thread safety test failed: {e}")
        return False

def main():
    """Run all async conflict resolution tests"""
    logger.info("🚀 Starting Async Event Loop Conflict Resolution Tests")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Async Utilities", test_async_utils),
        ("Adaptive Learning System", test_adaptive_learning_system),
        ("AI Ensemble System", test_ai_ensemble_system),
        ("Predictor Integration", test_predictor_integration),
        ("Concurrent Execution", test_concurrent_execution),
        ("Thread Safety", test_threading_safety)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} test...")
        try:
            result = test_func()
            test_results[test_name] = result
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            test_results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🏁 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name:25}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL ASYNC CONFLICT TESTS PASSED!")
        logger.info("✅ Adaptive Learning and AI Ensemble systems should now work without event loop conflicts")
        return 0
    else:
        logger.error(f"⚠️ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)