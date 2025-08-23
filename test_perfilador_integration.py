#!/usr/bin/env python3
"""
Test perfilador_dinamico integration in the main system
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_perfilador_in_meta_learning_system():
    """Test that perfilador trains correctly in the meta-learning integration"""
    
    try:
        logger.info("🔍 Testing perfilador integration in meta-learning system...")
        
        # Import the meta-learning integrator
        from modules.meta_learning_integrator import create_meta_learning_system
        
        logger.info("✅ Successfully imported meta-learning system")
        
        # Create the integrated system
        integrator = create_meta_learning_system(enable_all=True)
        
        logger.info("✅ Meta-learning system created")
        logger.info(f"   Components enabled: {integrator.components_enabled}")
        
        # Check if profiler is available
        if integrator.profiler:
            logger.info(f"✅ Profiler available - is_trained: {integrator.profiler.is_trained}")
        else:
            logger.error("❌ Profiler not available")
            return False
        
        # Create historical data (load real data if available)
        historical_data = load_historical_data()
        
        logger.info(f"✅ Loaded {len(historical_data)} historical combinations")
        
        # Train the integrated system
        logger.info("🏋️ Training integrated system...")
        training_results = integrator.train_integrated_system(historical_data)
        
        logger.info("✅ Training completed!")
        logger.info(f"   Components trained: {training_results['components_trained']}")
        
        # Check if profiler is now trained
        if integrator.profiler:
            logger.info(f"✅ Profiler status after training - is_trained: {integrator.profiler.is_trained}")
            
            if integrator.profiler.is_trained:
                logger.info("🎉 PERFILADOR IS NOW TRAINED!")
                
                # Test prediction to ensure no "not trained" warning
                logger.info("🧪 Testing prediction to verify no 'not trained' warnings...")
                
                # Use recent data for prediction
                recent_data = historical_data[-20:]  # Last 20 combinations
                
                # Capture logging to check for warnings
                import io
                log_capture_string = io.StringIO()
                ch = logging.StreamHandler(log_capture_string)
                ch.setLevel(logging.WARNING)
                
                # Get the perfilador logger
                profiler_logger = logging.getLogger('modules.perfilador_dinamico')
                profiler_logger.addHandler(ch)
                
                try:
                    prediction = integrator.profiler.predict_profile(recent_data)
                    
                    # Check captured logs for "not trained" warning
                    log_contents = log_capture_string.getvalue()
                    
                    if "Modelo no entrenado" in log_contents:
                        logger.error("❌ STILL SHOWING 'NOT TRAINED' WARNING")
                        logger.error(f"   Warning: {log_contents.strip()}")
                        return False
                    else:
                        logger.info("✅ NO 'NOT TRAINED' WARNINGS!")
                        logger.info(f"   Prediction successful: {prediction.profile.value} ({prediction.confidence:.3f})")
                        return True
                        
                finally:
                    profiler_logger.removeHandler(ch)
                
            else:
                logger.error("❌ Profiler still not trained after training process")
                return False
        else:
            logger.error("❌ Profiler not available after training")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_historical_data():
    """Load historical data for testing"""
    
    try:
        # Try to load from CSV first
        import pandas as pd
        
        csv_path = "data/historial_kabala_github.csv"
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            
            # Extract combinations from Bolilla columns
            number_cols = [col for col in df.columns if 'Bolilla' in col]
            
            if len(number_cols) >= 6:
                historical_data = []
                
                for _, row in df.iterrows():
                    try:
                        combination = [int(row[col]) for col in number_cols[:6]]
                        if all(1 <= n <= 40 for n in combination) and len(set(combination)) == 6:
                            historical_data.append(sorted(combination))
                    except (ValueError, TypeError):
                        continue
                
                logger.info(f"✅ Loaded {len(historical_data)} combinations from CSV")
                return historical_data[:200]  # Use first 200 for testing
        
        # Fallback to synthetic data
        logger.info("⚠️ CSV not found, generating synthetic data")
        
        import random
        random.seed(42)
        
        historical_data = []
        for i in range(100):
            combination = sorted(random.sample(range(1, 41), 6))
            historical_data.append(combination)
        
        return historical_data
        
    except Exception as e:
        logger.error(f"❌ Error loading historical data: {e}")
        
        # Generate minimal synthetic data
        import random
        return [sorted(random.sample(range(1, 41), 6)) for _ in range(100)]

if __name__ == "__main__":
    logger.info("🚀 TESTING PERFILADOR INTEGRATION")
    logger.info("="*50)
    
    success = test_perfilador_in_meta_learning_system()
    
    logger.info("\n📊 FINAL RESULT:")
    if success:
        logger.info("🎉 SUCCESS: Perfilador trains correctly and no longer shows 'not trained' warnings!")
        logger.info("✅ The perfilador_dinamico training issue has been FIXED!")
    else:
        logger.info("❌ FAILURE: Perfilador training issue persists")
        
    sys.exit(0 if success else 1)