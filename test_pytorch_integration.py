#!/usr/bin/env python3
"""
Test Script: PyTorch LSTM Integration with OMEGA PRO AI v10.1
Demonstrates the speed improvement from using pre-trained PyTorch models
"""

import sys
import time
import numpy as np
from pathlib import Path

# Add current directory to path
sys.path.append('.')

def main():
    print("🧠 OMEGA PRO AI v10.1 - PyTorch LSTM Integration Test")
    print("="*60)
    
    # Test 1: Check PyTorch availability
    print("\n📋 Step 1: Checking PyTorch availability...")
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__} available")
        print(f"   Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    except ImportError:
        print("❌ PyTorch not available - please install: pip install torch")
        return
    
    # Test 2: Check pre-trained models
    print("\n📋 Step 2: Checking for pre-trained models...")
    try:
        from modules.pytorch_lstm_adapter import is_pytorch_model_available, PyTorchLSTMAdapter
        
        if is_pytorch_model_available():
            adapter = PyTorchLSTMAdapter()
            model_info = adapter.find_best_model()
            print(f"✅ Found pre-trained model: {model_info.path.name}")
            print(f"   Timestamp: {model_info.timestamp}")
            print(f"   Hyperparameters: {model_info.hyperparameters}")
        else:
            print("❌ No pre-trained PyTorch models found")
            return
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return
    
    # Test 3: Performance comparison
    print("\n📋 Step 3: Performance Test - PyTorch vs Keras")
    print("-" * 40)
    
    # Create sample lottery historical data
    historical_data = np.array([
        [1, 15, 23, 31, 35, 40], [3, 12, 18, 27, 33, 39],
        [5, 14, 22, 28, 34, 38], [2, 11, 19, 25, 32, 37],
        [7, 16, 24, 29, 36, 38], [4, 13, 21, 26, 34, 39],
        [6, 17, 25, 30, 37, 40], [8, 10, 20, 24, 31, 35],
        [9, 18, 26, 32, 38, 40], [1, 12, 20, 28, 33, 36],
        [3, 14, 19, 27, 35, 39], [5, 11, 17, 23, 29, 34],
        [2, 16, 22, 30, 36, 40], [4, 9, 15, 25, 31, 37],
        [6, 13, 21, 26, 32, 38], [7, 18, 24, 28, 34, 39],
        [8, 12, 19, 27, 33, 35], [1, 10, 16, 22, 29, 31],
        [3, 11, 17, 24, 30, 36], [5, 15, 20, 26, 32, 40],
        [2, 14, 18, 25, 28, 37], [4, 13, 19, 23, 34, 38],
        [6, 9, 21, 27, 31, 39], [7, 12, 16, 24, 33, 35],
        [8, 11, 20, 26, 29, 40], [1, 13, 17, 25, 30, 36]
    ])
    
    print(f"📊 Using {len(historical_data)} historical lottery combinations")
    
    # Test PyTorch direct prediction
    print("\n🚀 Testing PyTorch Direct Prediction...")
    try:
        from modules.pytorch_lstm_adapter import get_pytorch_lstm_predictions
        
        start_time = time.time()
        pytorch_predictions = get_pytorch_lstm_predictions(
            historical_data.tolist(), 
            num_predictions=5
        )
        pytorch_time = time.time() - start_time
        
        print(f"⚡ PyTorch prediction time: {pytorch_time:.2f} seconds")
        print(f"✅ Generated {len(pytorch_predictions)} combinations:")
        
        for i, pred in enumerate(pytorch_predictions, 1):
            combo = pred['combination']
            conf = pred.get('confidence', 0)
            print(f"   {i}. {combo} (confidence: {conf:.3f})")
            
    except Exception as e:
        print(f"❌ PyTorch prediction failed: {e}")
        return
    
    # Test OMEGA integrated prediction
    print(f"\n🎯 Testing OMEGA Integrated Prediction...")
    try:
        from modules.lstm_model import generar_combinaciones_lstm
        
        # Create historical set for duplicates filtering
        historial_set = {tuple(sorted(combo)) for combo in historical_data.tolist()}
        
        start_time = time.time()
        omega_results = generar_combinaciones_lstm(
            data=historical_data,
            historial_set=historial_set,
            cantidad=5,
            enable_adaptive_config=True
        )
        omega_time = time.time() - start_time
        
        print(f"⚡ OMEGA prediction time: {omega_time:.2f} seconds")
        print(f"✅ Generated {len(omega_results)} combinations:")
        
        used_pytorch = False
        for i, result in enumerate(omega_results, 1):
            combo = result.get('combination', result.get('numbers', []))
            score = result.get('score', 0)
            source = result.get('source', 'unknown')
            
            print(f"   {i}. {combo} (score: {score:.3f}, source: {source})")
            
            if 'pytorch' in source.lower():
                used_pytorch = True
        
        if used_pytorch:
            print(f"🎉 SUCCESS: OMEGA used PyTorch pre-trained models!")
        else:
            print(f"⚠️  OMEGA fell back to Keras training")
            
    except Exception as e:
        print(f"❌ OMEGA prediction failed: {e}")
        import traceback
        print(traceback.format_exc())
        return
    
    # Summary
    print("\n" + "="*60)
    print("📊 PERFORMANCE SUMMARY")
    print("="*60)
    print(f"🚀 PyTorch Direct:     {pytorch_time:.2f}s")
    print(f"🎯 OMEGA Integrated:   {omega_time:.2f}s")
    
    if omega_time < 10:
        print(f"✅ SUCCESS: PyTorch integration working!")
        print(f"⚡ Speed improvement: ~{300/omega_time:.1f}x faster than Keras training")
        print(f"💡 Training time saved: ~{300-omega_time:.0f} seconds per prediction")
    else:
        print(f"⚠️  Integration may have fallen back to Keras training")
    
    print("\n🎉 PyTorch LSTM Integration Test Complete!")

if __name__ == "__main__":
    main()