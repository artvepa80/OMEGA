#!/usr/bin/env python3
"""Debug the limpiar_historial function specifically"""

import sys
sys.path.append('.')

import numpy as np
import logging
from modules.montecarlo_model import limpiar_historial
from modules.data_manager import OmegaDataManager

# Configure logging with detailed output
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("DebugLimpiarHistorial")

def debug_limpiar_historial():
    """Debug the limpiar_historial function step by step"""
    
    print("=" * 60)
    print("DEBUG: LIMPIAR_HISTORIAL FUNCTION")
    print("=" * 60)
    
    # Load actual data
    dm = OmegaDataManager()
    data = dm.load_historical_data()
    
    # Extract lottery columns
    lottery_cols = [col for col in data.columns if 'bolilla_' in col][:6]
    lottery_data = data[lottery_cols].values.tolist()
    
    print(f"Input data: {len(lottery_data)} rows")
    print(f"Sample row: {lottery_data[0]}")
    print(f"Sample row types: {[type(x) for x in lottery_data[0]]}")
    print()
    
    # Manual step-by-step processing to debug
    print("Step-by-step debugging:")
    
    # Step 1: Convert to numpy array
    historial_arr = np.array(lottery_data[:5], dtype=object)  # Test with first 5 rows
    print(f"1. Array shape: {historial_arr.shape}")
    print(f"1. Array dtype: {historial_arr.dtype}")
    
    # Step 2: Create mask
    mask_valido = np.ones(len(historial_arr), dtype=bool)
    print(f"2. Initial mask: {mask_valido}")
    
    # Step 3: Process each combination manually
    for i, combo in enumerate(historial_arr):
        print(f"\n3.{i+1}. Processing combo {i}: {combo}")
        print(f"     Type: {type(combo)}")
        print(f"     Is list/tuple: {isinstance(combo, (list, tuple))}")
        print(f"     Length: {len(combo)}")
        
        if not isinstance(combo, (list, tuple)) or len(combo) != 6:
            print(f"     ❌ INVALID: Wrong type or length")
            mask_valido[i] = False
            continue
            
        try:
            # Try the fixed conversion logic
            combo_clean = []
            for j, val in enumerate(combo):
                print(f"       Val {j}: {val} (type: {type(val)})")
                if isinstance(val, (int, float, np.number)):
                    int_val = int(round(float(val)))
                    combo_clean.append(int_val)
                    print(f"         -> Converted to: {int_val}")
                elif isinstance(val, str) and val.replace('.', '').replace('-', '').isdigit():
                    int_val = int(round(float(val)))
                    combo_clean.append(int_val)
                    print(f"         -> Converted from string to: {int_val}")
                else:
                    print(f"         ❌ Invalid data type: {type(val)}")
                    raise ValueError(f"Invalid data type: {type(val)}")
            
            print(f"     Cleaned combo: {combo_clean}")
            
            # Validate range and uniqueness
            combo_arr = np.array(combo_clean, dtype=int)
            has_duplicates = len(set(combo_clean)) != 6
            out_of_range = np.any((combo_arr < 1) | (combo_arr > 40))
            
            print(f"     Duplicates: {has_duplicates}")
            print(f"     Out of range: {out_of_range}")
            
            if has_duplicates:
                print(f"     ❌ INVALID: Has duplicates")
                mask_valido[i] = False
            elif out_of_range:
                print(f"     ❌ INVALID: Out of range [1-40]")
                mask_valido[i] = False
            else:
                print(f"     ✅ VALID")
                
        except Exception as e:
            print(f"     ❌ EXCEPTION: {e}")
            mask_valido[i] = False
    
    print(f"\nFinal mask: {mask_valido}")
    print(f"Valid count: {mask_valido.sum()}")
    
    # Now test with the actual function
    print("\n" + "=" * 60)
    print("TESTING WITH ACTUAL FUNCTION")
    print("=" * 60)
    
    resultado = limpiar_historial(lottery_data[:5], logger=logger)
    print(f"Function result: {len(resultado)} valid combinations")
    
    for i, combo in enumerate(resultado):
        print(f"  Valid {i+1}: {combo}")

if __name__ == "__main__":
    debug_limpiar_historial()