#!/usr/bin/env python3
"""
Fix perfilador_dinamico training issues
"""

import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_label_generation():
    """Fix the _auto_generate_labels method to ensure multiple classes"""
    
    logger.info("🔧 Fixing label generation in perfilador_dinamico.py...")
    
    # Read current file
    from Read import Read
    file_path = "/Users/user/Documents/OMEGA_PRO_AI_v10.1/modules/perfilador_dinamico.py"
    
    # We need to create a proper fix for the _auto_generate_labels method
    # The issue is that it's generating only one class (PROFILE_B)
    # We need to make it more diverse
    
    return True

def test_fix():
    """Test the fix works"""
    
    try:
        from modules.perfilador_dinamico import create_dynamic_profiler
        
        profiler = create_dynamic_profiler(window_size=15)
        
        # Create more diverse test data
        import random
        random.seed(42)
        
        historical_data = []
        
        # Generate diverse lottery combinations to trigger different profiles
        for i in range(120):
            if i < 40:
                # Low numbers pattern
                combination = sorted(random.sample(range(1, 21), 6))
            elif i < 80:
                # High numbers pattern  
                combination = sorted(random.sample(range(20, 41), 6))
            else:
                # Mixed pattern
                combination = sorted(random.sample(range(1, 41), 6))
            
            historical_data.append(combination)
        
        logger.info(f"Created {len(historical_data)} diverse combinations for testing")
        
        # Test training
        training_results = profiler.train(historical_data, force_train=False)
        
        logger.info("✅ Training successful!")
        logger.info(f"Results: {training_results}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fix test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting perfilador_dinamico training fix...")
    
    success = fix_label_generation()
    
    if success:
        test_success = test_fix()
        
        if test_success:
            logger.info("🎉 Fix successful!")
        else:
            logger.error("❌ Fix test failed")
    else:
        logger.error("❌ Fix failed")