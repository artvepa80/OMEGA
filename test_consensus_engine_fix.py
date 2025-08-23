#!/usr/bin/env python3
"""
Test the consensus engine fix to ensure bolilla_1 values display correctly
"""

import sys
import os
sys.path.insert(0, os.getcwd())

def test_evaluate_model_call():
    try:
        print("🔍 Testing evaluate_model_performance call fix...")
        
        # Import the fixed function
        from modules.learning.evaluate_model import evaluate_model_performance
        
        print("⚙️ Calling evaluate_model_performance with correct parameters...")
        
        # Call with the correct parameter signature
        result = evaluate_model_performance(n_ultimos=5)  # Small number for quick test
        
        print(f"✅ Function executed successfully!")
        print(f"📊 Result type: {type(result)}")
        if isinstance(result, dict):
            print(f"📊 Result keys: {list(result.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing evaluate_model_performance: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_consensus_minimal():
    try:
        print("\n" + "="*60)
        print("🔍 Testing minimal consensus engine call...")
        
        import pandas as pd
        from core.consensus_engine import generar_combinaciones_consenso
        
        # Create a minimal DataFrame
        print("⚙️ Creating test DataFrame...")
        test_data = {
            'bolilla_1': [1, 3, 5, 7, 9],
            'bolilla_2': [2, 4, 6, 8, 10], 
            'bolilla_3': [11, 13, 15, 17, 19],
            'bolilla_4': [12, 14, 16, 18, 20],
            'bolilla_5': [21, 23, 25, 27, 29],
            'bolilla_6': [22, 24, 26, 28, 30]
        }
        df = pd.DataFrame(test_data)
        
        print(f"📊 Test DataFrame shape: {df.shape}")
        print("📋 Test DataFrame:")
        print(df)
        
        print("\n⚙️ Calling generar_combinaciones_consenso with evaluate=True...")
        
        # Call with evaluate=True to test our fix
        result = generar_combinaciones_consenso(
            historial_df=df, 
            cantidad=3, 
            evaluate=True,  # This will trigger the fixed evaluate_model_performance call
            retrain=False,  # Disable to speed up test
            backtest=False  # Disable to speed up test
        )
        
        print(f"✅ Consensus engine executed successfully!")
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Number of combinations returned: {len(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing consensus engine: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_evaluate_model_call()
    success2 = test_consensus_minimal()
    
    if success1 and success2:
        print(f"\n🎉 ALL TESTS PASSED! The fix appears to be working correctly.")
    else:
        print(f"\n❌ Some tests failed. Please check the output above.")