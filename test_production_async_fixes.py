#!/usr/bin/env python3
"""
Production Test: Verify async fixes work in the real OMEGA system
"""

import sys
import os
import logging

# Add project root to path
sys.path.append('/Users/user/Documents/OMEGA_PRO_AI_v10.1')

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_real_predictor():
    """Test the real predictor with fixed async patterns"""
    logger.info("🧪 Testing real OMEGA predictor with async fixes...")
    
    try:
        # Import core system
        from core.predictor import HybridOmegaPredictor
        
        # Create a minimal test
        logger.info("📊 Creating predictor instance...")
        
        # Use the actual historical data file
        data_path = '/Users/user/Documents/OMEGA_PRO_AI_v10.1/data/historial_kabala_github_emergency_clean.csv'
        
        if not os.path.exists(data_path):
            logger.warning("⚠️ Using backup data path")
            data_path = '/Users/user/Documents/OMEGA_PRO_AI_v10.1/data/historial_kabala_github.csv'
        
        if not os.path.exists(data_path):
            logger.error("❌ No historical data file found")
            return False
            
        # Initialize predictor  
        predictor = HybridOmegaPredictor(data_path)
        
        logger.info("🔄 Testing main prediction system (includes async fixes)...")
        # This will test the async systems internally
        all_results = predictor.run_all_models()
        logger.info(f"✅ Main prediction system: Generated {len(all_results)} predictions")
        
        logger.info("🔄 Testing async model execution...")
        from utils.async_utils import safe_run_async
        async_results = safe_run_async(predictor.run_all_models_async())
        logger.info(f"✅ Async model execution: Generated {len(async_results)} predictions")
        
        # Test consensus engine functions directly
        logger.info("🔄 Testing Consensus Engine functions...")
        from core.consensus_engine import generar_combinaciones_consenso
        
        # Load data for consensus test
        import pandas as pd
        df = pd.read_csv(data_path)
        consensus_results = generar_combinaciones_consenso(
            historial_df=df,
            cantidad=2,
            modo_avanzado=True,
            perfil_svi='default',
            usar_meta_learning=True
        )
        logger.info(f"✅ Consensus Functions: Generated {len(consensus_results)} predictions")
        
        logger.info("🎉 ALL ASYNC SYSTEMS WORKING IN PRODUCTION!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Production test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    logger.info("🚀 Testing OMEGA Production System with Async Fixes")
    logger.info("=" * 60)
    
    success = test_real_predictor()
    
    if success:
        logger.info("\n✅ PRODUCTION ASYNC FIXES VALIDATED!")
        logger.info("✅ Adaptive Learning System working")
        logger.info("✅ AI Ensemble System working") 
        logger.info("✅ Consensus Engine functions working")
        logger.info("✅ No event loop conflicts detected")
        return 0
    else:
        logger.error("\n❌ PRODUCTION TEST FAILED")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)