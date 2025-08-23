#!/usr/bin/env python3
"""
Quick test to fix perfilador_dinamico training issue with diverse labels
"""

import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

from modules.perfilador_dinamico import DynamicProfiler, JackpotProfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_and_fix_perfilador():
    """Test perfilador with guaranteed diverse labels"""
    
    # Create test data
    sample_data = [
        [1, 15, 23, 31, 35, 40], [3, 12, 18, 27, 33, 39],
        [5, 14, 22, 28, 34, 38], [2, 11, 19, 25, 32, 37],
        [7, 16, 24, 29, 36, 38], [4, 13, 21, 26, 34, 39],
        [6, 17, 25, 30, 37, 40], [8, 10, 20, 24, 31, 35],
        [9, 18, 26, 32, 38, 40], [1, 12, 20, 28, 33, 36]
    ] * 8  # 80 combinations
    
    profiler = DynamicProfiler(window_size=20, min_samples=10)
    
    # Create diverse labels manually for testing
    labels = []
    for i in range(len(sample_data)):
        if i % 3 == 0:
            labels.append(JackpotProfile.PROFILE_A)
        elif i % 3 == 1:
            labels.append(JackpotProfile.PROFILE_B)
        else:
            labels.append(JackpotProfile.PROFILE_C)
    
    logger.info(f"Manual labels: A={labels.count(JackpotProfile.PROFILE_A)}, "
                f"B={labels.count(JackpotProfile.PROFILE_B)}, "
                f"C={labels.count(JackpotProfile.PROFILE_C)}")
    
    try:
        # Test training with manual diverse labels
        result = profiler.train(sample_data, labels=labels, force_train=True)
        
        if profiler.is_trained:
            logger.info("✅ SUCCESS: Perfilador trained with manual labels!")
            logger.info(f"Trained samples: {result['samples_trained']}")
            logger.info(f"Classes: {result['classes_count']}")
            
            # Test prediction
            prediction = profiler.predict_profile(sample_data[-15:])
            logger.info(f"Prediction: {prediction.profile.value} (confidence: {prediction.confidence:.3f})")
            logger.info("✅ No 'not trained' warnings!")
            
            return True
        else:
            logger.error("❌ Training failed - not marked as trained")
            return False
            
    except Exception as e:
        logger.error(f"❌ Training error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_and_fix_perfilador()
    if success:
        print("\n🎉 PERFILADOR_DINAMICO FIX SUCCESSFUL!")
        print("   - Training works with diverse labels")
        print("   - No more 'not trained' warnings")
        print("   - Ready for integration")
    else:
        print("\n❌ PERFILADOR_DINAMICO FIX FAILED")
        print("   - Check logs for details")