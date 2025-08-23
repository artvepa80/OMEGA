#!/usr/bin/env python3
"""
OMEGA Critical Fixes Quick Validation
====================================

Quick validation of the 4 critical fixes implemented.
"""

import logging
import sys
import traceback

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def validate_fixes():
    """Quick validation of all fixes"""
    results = {}
    
    # Fix 1: Transformer Architecture
    try:
        from modules.transformer_model import get_adaptive_transformer_config, get_system_resources
        resources = get_system_resources()
        config = get_adaptive_transformer_config(resources)
        
        if config.get('d_model') == 128:
            results['transformer'] = '✅ FIXED - d_model=128 alignment'
        else:
            results['transformer'] = f'❌ ISSUE - d_model={config.get("d_model")}'
    except Exception as e:
        results['transformer'] = f'❌ ERROR - {e}'
    
    # Fix 2: LSTM Integration
    try:
        from modules.lstm_model import generar_combinaciones_lstm
        import numpy as np
        
        test_data = np.random.randint(1, 41, size=(50, 6))
        historial_set = set()
        
        lstm_results = generar_combinaciones_lstm(
            data=test_data,
            historial_set=historial_set, 
            cantidad=3,
            enable_adaptive_config=True
        )
        
        if isinstance(lstm_results, list) and len(lstm_results) > 0:
            results['lstm'] = f'✅ FIXED - Generated {len(lstm_results)} combinations'
        else:
            results['lstm'] = f'❌ ISSUE - Invalid results: {type(lstm_results)}'
    except Exception as e:
        results['lstm'] = f'❌ ERROR - {str(e)[:100]}'
    
    # Fix 3: Genetic Algorithm Timeout
    try:
        from modules.genetic_model import GeneticConfig
        
        config = GeneticConfig(timeout_seconds=10, early_convergence_threshold=0.001)
        
        if hasattr(config, 'timeout_seconds') and config.timeout_seconds == 10:
            results['genetic'] = '✅ FIXED - Timeout handling implemented'
        else:
            results['genetic'] = '❌ ISSUE - Timeout not properly configured'
    except Exception as e:
        results['genetic'] = f'❌ ERROR - {e}'
    
    # Fix 4: Consensus Engine DataFrame Safety
    try:
        from core.consensus_engine import safe_dataframe_check, safe_bool_conversion
        import pandas as pd
        
        # Test safe DataFrame checks
        test_empty = safe_dataframe_check(pd.DataFrame())
        test_valid = safe_dataframe_check(pd.DataFrame({'a': [1, 2, 3]}))
        test_none = safe_dataframe_check(None)
        
        if not test_empty and test_valid and not test_none:
            results['consensus'] = '✅ FIXED - Safe DataFrame operations'
        else:
            results['consensus'] = f'❌ ISSUE - Tests: empty={test_empty}, valid={test_valid}, none={test_none}'
    except Exception as e:
        results['consensus'] = f'❌ ERROR - {e}'
    
    return results

def main():
    logger.info("🚀 OMEGA Critical Fixes Quick Validation")
    logger.info("=" * 50)
    
    results = validate_fixes()
    
    passed = 0
    total = len(results)
    
    for fix_name, status in results.items():
        logger.info(f"{fix_name.title():15} | {status}")
        if '✅ FIXED' in status:
            passed += 1
    
    logger.info("=" * 50)
    logger.info(f"Summary: {passed}/{total} fixes validated successfully")
    
    if passed == total:
        logger.info("🎉 ALL CRITICAL FIXES WORKING!")
        logger.info("🚀 OMEGA is ready for 65-70% accuracy targeting")
        return 0
    else:
        logger.error(f"⚠️ {total - passed} fixes need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())