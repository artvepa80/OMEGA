#!/usr/bin/env python3
"""
Complete test to validate that the fixes resolve the validation issue
where all 3648 combinations were being marked as invalid.
"""

import sys
import os
sys.path.append('.')

import pandas as pd
import numpy as np
import logging
from modules.montecarlo_model import limpiar_historial, generar_combinaciones_montecarlo
from modules.data_manager import OmegaDataManager
from core.predictor import HybridOmegaPredictor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("CompleteValidationTest")

def test_montecarlo_validation():
    """Test the montecarlo validation fix specifically"""
    print("=" * 60)
    print("TEST 1: MONTECARLO VALIDATION FIX")
    print("=" * 60)
    
    # Load actual data
    dm = OmegaDataManager()
    data = dm.load_historical_data()
    
    print(f"Loaded data shape: {data.shape}")
    
    # Extract only lottery columns like the fix does
    lottery_cols = [col for col in data.columns if 'bolilla_' in col][:6]
    if len(lottery_cols) >= 6:
        lottery_data = data[lottery_cols].values.tolist()
    else:
        numeric_cols = data.select_dtypes(include='number').columns
        lottery_data = data[numeric_cols[:6]].values.tolist()
    
    print(f"Lottery columns used: {lottery_cols}")
    print(f"Lottery data shape: {len(lottery_data)} rows, {len(lottery_data[0]) if lottery_data else 0} cols")
    
    # Test the validation
    print("\nTesting limpiar_historial function...")
    resultado = limpiar_historial(lottery_data, logger=logger)
    
    print(f"✅ Result: {len(resultado)}/{len(lottery_data)} combinations are valid")
    
    if len(resultado) > 0:
        print("✅ SUCCESS: Validation is now working correctly!")
        print(f"Sample valid combinations (first 3):")
        for i in range(min(3, len(resultado))):
            print(f"  {i+1}: {resultado[i]}")
        return True
    else:
        print("❌ FAILED: Still no valid combinations found")
        return False

def test_montecarlo_generation():
    """Test the montecarlo combination generation"""
    print("\n" + "=" * 60)
    print("TEST 2: MONTECARLO COMBINATION GENERATION")
    print("=" * 60)
    
    # Load actual data
    dm = OmegaDataManager()
    data = dm.load_historical_data()
    
    # Extract lottery columns
    lottery_cols = [col for col in data.columns if 'bolilla_' in col][:6]
    if len(lottery_cols) >= 6:
        lottery_data = data[lottery_cols].values.tolist()
    else:
        numeric_cols = data.select_dtypes(include='number').columns
        lottery_data = data[numeric_cols[:6]].values.tolist()
    
    # Test combination generation
    print(f"Generating 5 combinations from {len(lottery_data)} historical records...")
    
    try:
        combinations = generar_combinaciones_montecarlo(
            historial=lottery_data,
            cantidad=5,
            logger=logger
        )
        
        print(f"✅ Generated {len(combinations)} combinations")
        for i, combo in enumerate(combinations):
            print(f"  {i+1}: {combo.get('combination', 'N/A')} (score: {combo.get('score', 'N/A')})")
        
        return len(combinations) > 0
        
    except Exception as e:
        print(f"❌ Error generating combinations: {e}")
        return False

def test_full_predictor():
    """Test the full predictor with fixes"""
    print("\n" + "=" * 60)
    print("TEST 3: FULL PREDICTOR TEST")
    print("=" * 60)
    
    try:
        # Create predictor instance
        predictor = HybridOmegaPredictor(cantidad_final=5)
        
        print(f"Predictor initialized with {predictor.data.shape[0]} records")
        print(f"Predictor columns: {list(predictor.data.columns)}")
        
        # Test montecarlo model specifically
        print("\nTesting montecarlo model...")
        montecarlo_results = predictor._run_montecarlo(5)
        
        print(f"✅ Montecarlo generated {len(montecarlo_results)} combinations")
        
        if montecarlo_results:
            for i, combo in enumerate(montecarlo_results):
                print(f"  {i+1}: {combo.get('combination', 'N/A')} (score: {combo.get('score', 'N/A')})")
            return True
        else:
            print("❌ No combinations generated")
            return False
            
    except Exception as e:
        print(f"❌ Error in full predictor test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_extraction():
    """Test that lottery columns are correctly extracted"""
    print("\n" + "=" * 60)
    print("TEST 4: DATA EXTRACTION VERIFICATION")
    print("=" * 60)
    
    dm = OmegaDataManager()
    data = dm.load_historical_data()
    
    print(f"Full data shape: {data.shape}")
    print(f"Full data columns: {list(data.columns)}")
    
    # Test extraction logic
    lottery_cols = [col for col in data.columns if 'bolilla_' in col][:6]
    print(f"Lottery columns: {lottery_cols}")
    
    if len(lottery_cols) >= 6:
        lottery_data = data[lottery_cols]
        print(f"Lottery data shape: {lottery_data.shape}")
        print(f"Lottery data types: {lottery_data.dtypes.tolist()}")
        
        # Show sample data
        print("\nSample lottery data:")
        for i in range(min(3, len(lottery_data))):
            row = lottery_data.iloc[i].tolist()
            print(f"  Row {i}: {row} (types: {[type(x) for x in row]})")
        
        # Verify all values are in valid range
        all_values = lottery_data.values.flatten()
        valid_values = np.all((all_values >= 1) & (all_values <= 40))
        print(f"\nAll values in range [1-40]: {valid_values}")
        print(f"Min value: {all_values.min()}, Max value: {all_values.max()}")
        
        return valid_values
    else:
        print("❌ Not enough lottery columns found")
        return False

def main():
    """Run all tests"""
    print("🚀 RUNNING COMPLETE VALIDATION TESTS")
    print("These tests verify the fixes for the validation issue where all 3648 combinations were invalid.")
    print()
    
    test_results = []
    
    # Run tests
    test_results.append(("Montecarlo Validation", test_montecarlo_validation()))
    test_results.append(("Montecarlo Generation", test_montecarlo_generation()))  
    test_results.append(("Full Predictor", test_full_predictor()))
    test_results.append(("Data Extraction", test_data_extraction()))
    
    # Summary
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25}: {status}")
        if result:
            passed += 1
    
    print(f"\nSummary: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ The validation fixes should resolve the issue where all 3648 combinations were marked invalid.")
        print("✅ The system should now properly validate lottery combinations and use the historical data.")
    else:
        print(f"\n⚠️ {len(test_results) - passed} test(s) failed.")
        print("❌ Further investigation may be needed.")

if __name__ == "__main__":
    main()