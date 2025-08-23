#!/usr/bin/env python3
"""
Test script to validate the transformer_deep model through the main predictor
"""
import sys
import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.predictor import HybridOmegaPredictor

def test_predictor_transformer():
    """Test the transformer_deep model through the main predictor"""
    
    print("🧪 Testing Transformer through OmegaPredictor")
    print("=" * 60)
    
    try:
        # Create test historical data
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        np.random.seed(42)  # For reproducible results
        data = []
        
        for i in range(50):
            # Generate realistic lottery combinations (6 unique numbers 1-40)
            combo = sorted(np.random.choice(range(1, 41), 6, replace=False))
            data.append(combo)
        
        historial_df = pd.DataFrame(data, columns=[f'bolilla_{i+1}' for i in range(6)])
        historial_df['fecha'] = dates
        
        print(f"✅ Created test dataset with {len(historial_df)} historical draws")
        
        # Initialize predictor
        predictor = HybridOmegaPredictor()
        
        # Test transformer_deep model specifically
        print("\n🚀 Testing transformer_deep model through predictor...")
        
        start_time = datetime.now()
        
        # Call the predictor's transformer method directly
        try:
            result = predictor._run_transformer(max_comb=3)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"✅ Transformer prediction completed in {duration:.2f} seconds")
            print(f"   Generated {len(result)} combinations")
            
            # Validate results
            success = True
            for i, combo_data in enumerate(result):
                if not isinstance(combo_data, dict):
                    print(f"❌ Invalid result format at index {i}: {type(combo_data)}")
                    success = False
                    continue
                    
                if 'combination' not in combo_data:
                    print(f"❌ Missing 'combination' key at index {i}")
                    success = False
                    continue
                    
                combo = combo_data['combination']
                if not isinstance(combo, list) or len(combo) != 6:
                    print(f"❌ Invalid combination format at index {i}: {combo}")
                    success = False
                    continue
                    
                if not all(isinstance(n, (int, np.integer)) and 1 <= n <= 40 for n in combo):
                    print(f"❌ Invalid number range at index {i}: {combo}")
                    success = False
                    continue
                    
                if len(set(combo)) != 6:
                    print(f"❌ Duplicate numbers at index {i}: {combo}")
                    success = False
                    continue
                
                source = combo_data.get('source', 'unknown')
                score = combo_data.get('score', 0)
                print(f"   [{i+1}] {combo} - Score: {score:.3f} - Source: {source}")
            
            if success:
                print("\n🎉 TRANSFORMER INTEGRATION TEST PASSED!")
                print("✅ transformer_deep model working through predictor")
                print("✅ No DataFrame serialization errors")
                return True
            else:
                print("\n❌ SOME VALIDATION TESTS FAILED!")
                return False
        
        except Exception as transformer_error:
            print(f"\n🚨 Transformer method failed: {transformer_error}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"\n🚨 TEST SETUP FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_predictor_transformer()
    sys.exit(0 if success else 1)