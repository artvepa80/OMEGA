#!/usr/bin/env python3
"""
Quick ML Model Test - Identify immediate issues
"""

import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce verbosity

def test_imports():
    """Test if all ML modules can be imported"""
    print("🔍 Testing ML module imports...")
    
    try:
        from modules.learning.gboost_jackpot_classifier import GBoostJackpotClassifier
        print("✅ GBoost Classifier import successful")
    except Exception as e:
        print(f"❌ GBoost Classifier import failed: {e}")
    
    try:
        from modules.lstm_model import generar_combinaciones_lstm
        print("✅ LSTM Model import successful")
    except Exception as e:
        print(f"❌ LSTM Model import failed: {e}")
    
    try:
        from modules.transformer_model import generar_combinaciones_transformer
        print("✅ Transformer Model import successful")
    except Exception as e:
        print(f"❌ Transformer Model import failed: {e}")
    
    try:
        from modules.arima_cycles import arima_cycles
        print("✅ ARIMA Cycles import successful")
    except Exception as e:
        print(f"❌ ARIMA Cycles import failed: {e}")
    
    try:
        from modules.score_dynamics import score_combinations
        print("✅ Score Dynamics import successful")
    except Exception as e:
        print(f"❌ Score Dynamics import failed: {e}")

def test_basic_functionality():
    """Test basic functionality of each model"""
    print("\n🧪 Testing basic functionality...")
    
    # Test ARIMA (simplest)
    try:
        from modules.arima_cycles import arima_cycles
        result = arima_cycles([1, 2, 3, 4, 5])
        print(f"✅ ARIMA Cycles: {result}")
    except Exception as e:
        print(f"❌ ARIMA Cycles failed: {e}")
    
    # Test GBoost with minimal data
    try:
        from modules.learning.gboost_jackpot_classifier import GBoostJackpotClassifier
        clf = GBoostJackpotClassifier(n_estimators=5)
        clf.fit([[1,2,3,4,5,6], [7,8,9,10,11,12]], [0, 1])
        pred = clf.predict([[13,14,15,16,17,18]])
        print(f"✅ GBoost Classifier prediction: {pred}")
    except Exception as e:
        print(f"❌ GBoost Classifier failed: {e}")

def check_dependencies():
    """Check if all required dependencies are available"""
    print("\n📦 Checking dependencies...")
    
    modules_to_check = [
        'numpy', 'pandas', 'torch', 'tensorflow', 'sklearn', 
        'joblib', 'logging', 'pathlib'
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - MISSING")

def main():
    print("🚀 Quick ML Model Validation")
    print("=" * 40)
    
    check_dependencies()
    test_imports() 
    test_basic_functionality()
    
    print("\n✅ Quick validation complete!")

if __name__ == "__main__":
    main()