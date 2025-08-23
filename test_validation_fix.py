#!/usr/bin/env python3
"""Test script to validate the fix for combination validation logic"""

import sys
import os
sys.path.append('.')

import pandas as pd
import numpy as np
import logging
from modules.montecarlo_model import limpiar_historial
from utils.validation import clean_historial_df

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ValidationTest")

def test_validation_fix():
    """Test the validation fix with various data types"""
    
    # Test data with mixed types (simulating the actual problem)
    test_data = [
        # Float values (this was causing the issue)
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        [7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
        [13.0, 14.0, 15.0, 16.0, 17.0, 18.0],
        # Integer values (should work fine)
        [19, 20, 21, 22, 23, 24],
        [25, 26, 27, 28, 29, 30],
        # Mixed int/float values
        [31, 32.0, 33, 34.0, 35, 36.0],
        # Edge cases
        [1, 2, 3, 4, 5, 40],  # Min/max values
        [37, 38, 39, 40, 1, 2],  # Mixed order
        # Invalid cases (should be rejected)
        [0, 1, 2, 3, 4, 5],  # Out of range (0)
        [36, 37, 38, 39, 40, 41],  # Out of range (41)
        [1, 2, 3, 4, 5],  # Wrong length
        [1, 2, 3, 4, 5, 5],  # Duplicates
    ]
    
    print("=" * 60)
    print("TESTING VALIDATION FIX")
    print("=" * 60)
    print(f"Total test combinations: {len(test_data)}")
    print(f"Expected valid: 8 (first 8)")
    print(f"Expected invalid: 4 (last 4)")
    print()
    
    # Test the fixed limpiar_historial function
    resultado = limpiar_historial(test_data, logger=logger)
    
    print(f"✅ Result: {len(resultado)} valid combinations found")
    print()
    
    for i, combo in enumerate(resultado):
        print(f"Valid combo {i+1}: {combo}")
    
    print()
    
    # Expected result: should be 8 valid combinations
    if len(resultado) == 8:
        print("🎉 SUCCESS: Validation fix is working correctly!")
        return True
    else:
        print(f"❌ FAILED: Expected 8 valid combinations, got {len(resultado)}")
        return False

def test_with_actual_data():
    """Test with actual data from the system"""
    try:
        print("=" * 60)
        print("TESTING WITH ACTUAL DATA")
        print("=" * 60)
        
        # Try to load actual historical data
        from modules.data_manager import OmegaDataManager
        dm = OmegaDataManager()
        data = dm.load_historical_data()
        
        print(f"Loaded data shape: {data.shape}")
        print(f"Data types: {data.dtypes.tolist()}")
        print()
        
        # Show sample of raw data
        print("Sample raw data (first 3 rows):")
        for i in range(min(3, len(data))):
            print(f"Row {i}: {data.iloc[i].tolist()}")
        print()
        
        # Test the validation
        historial_list = data.values.tolist()
        resultado = limpiar_historial(historial_list, logger=logger)
        
        print(f"✅ Result: {len(resultado)}/{len(historial_list)} combinations are valid")
        
        # Show sample of valid data
        if resultado:
            print("\nSample valid combinations (first 3):")
            for i in range(min(3, len(resultado))):
                print(f"Valid combo {i+1}: {resultado[i]}")
        
        return len(resultado) > 0
        
    except Exception as e:
        print(f"❌ Error testing with actual data: {e}")
        return False

if __name__ == "__main__":
    success1 = test_validation_fix()
    success2 = test_with_actual_data()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Basic validation test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Actual data test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! The validation fix should resolve the issue.")
    else:
        print("\n❌ Some tests failed. Further investigation needed.")