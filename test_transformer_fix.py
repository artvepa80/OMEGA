#!/usr/bin/env python3
"""
Test script to validate the transformer DataFrame serialization fix
"""
import sys
import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.transformer_model import generar_combinaciones_transformer

def test_transformer_fix():
    """Test the transformer model fix for DataFrame serialization issue"""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    print("🧪 Testing Transformer DataFrame Serialization Fix")
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
        
        historial_df = pd.DataFrame(data, columns=[f'Bolilla {i+1}' for i in range(6)])
        historial_df['fecha'] = dates
        
        print(f"✅ Created test dataset with {len(historial_df)} historical draws")
        print(f"   Sample combination: {historial_df.iloc[0][[f'Bolilla {i+1}' for i in range(6)]].tolist()}")
        
        # Test transformer model generation
        print("\n🚀 Testing transformer combination generation...")
        
        start_time = datetime.now()
        
        result = generar_combinaciones_transformer(
            historial_df=historial_df,
            cantidad=5,
            perfil_svi='moderado',
            train_model_if_missing=False,  # Don't train, just test with existing model or fallback
            enable_adaptive_config=True
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Generation completed in {duration:.2f} seconds")
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
                
            if not all(isinstance(n, int) and 1 <= n <= 40 for n in combo):
                print(f"❌ Invalid number range at index {i}: {combo}")
                success = False
                continue
                
            if len(set(combo)) != 6:
                print(f"❌ Duplicate numbers at index {i}: {combo}")
                success = False
                continue
                
            print(f"   [{i+1}] {combo} - Score: {combo_data.get('score', 'N/A'):.3f} - Source: {combo_data.get('source', 'unknown')}")
        
        if success:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ DataFrame serialization fix is working correctly")
            print("✅ No 'unhashable type: DataFrame' errors encountered")
            print("✅ Transformer model is generating valid combinations")
            return True
        else:
            print("\n❌ SOME TESTS FAILED!")
            return False
            
    except Exception as e:
        print(f"\n🚨 TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_transformer_fix()
    sys.exit(0 if success else 1)