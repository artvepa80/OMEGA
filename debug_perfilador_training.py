#!/usr/bin/env python3
"""
Debug script to test perfilador_dinamico training
"""

import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_perfilador_training():
    """Test the perfilador_dinamico training process"""
    
    try:
        print("🔍 DEBUG: Testing perfilador_dinamico training...")
        
        # Import the profiler
        from modules.perfilador_dinamico import create_dynamic_profiler, DynamicProfiler
        
        print("✅ Successfully imported perfilador_dinamico")
        
        # Create profiler instance
        profiler = create_dynamic_profiler(window_size=20)  # Smaller window for testing
        print(f"✅ Created profiler, window_size: {profiler.window_size}, min_samples: {profiler.min_samples}")
        
        # Create test data (simulate historical lottery data)
        historical_data = []
        
        # Generate 100 realistic lottery combinations
        import random
        random.seed(42)  # For reproducible results
        
        for i in range(100):
            # Generate 6 unique numbers between 1 and 40
            combination = sorted(random.sample(range(1, 41), 6))
            historical_data.append(combination)
        
        print(f"✅ Created {len(historical_data)} historical lottery combinations")
        print(f"   First few: {historical_data[:3]}")
        print(f"   Data requirements check:")
        print(f"   - Min required samples: {profiler.min_samples * 3} (min_samples * 3)")
        print(f"   - Actual samples: {len(historical_data)}")
        print(f"   - Window size: {profiler.window_size}")
        print(f"   - Samples after windowing: {len(historical_data) - profiler.window_size}")
        
        # Check if profiler is initially trained
        print(f"✅ Initial profiler state - is_trained: {profiler.is_trained}")
        
        # Try to train the profiler
        print("🏋️ Starting profiler training...")
        
        try:
            training_results = profiler.train(historical_data, force_train=False)
            
            print("✅ TRAINING COMPLETED SUCCESSFULLY!")
            print(f"   Training results: {training_results}")
            print(f"   Profiler is_trained: {profiler.is_trained}")
            
            if profiler.is_trained:
                print("🎯 Testing prediction...")
                
                # Test prediction with recent data
                recent_data = historical_data[-10:]  # Use last 10 combinations
                prediction = profiler.predict_profile(recent_data)
                
                print(f"✅ Prediction successful!")
                print(f"   Profile: {prediction.profile.value}")
                print(f"   Confidence: {prediction.confidence:.3f}")
                print(f"   Probability distribution: {prediction.probability_distribution}")
                
                # No more "not trained" warnings!
                return True
            else:
                print("❌ Training completed but profiler.is_trained is still False")
                return False
                
        except Exception as training_error:
            print(f"❌ TRAINING FAILED: {training_error}")
            print(f"   Error type: {type(training_error).__name__}")
            
            # Print more detailed debug info
            import traceback
            traceback.print_exc()
            
            # Try to understand what went wrong
            print(f"\n🔍 DEBUGGING INFO:")
            print(f"   - Historical data length: {len(historical_data)}")
            print(f"   - Window size: {profiler.window_size}")
            print(f"   - Min samples: {profiler.min_samples}")
            print(f"   - Required total samples: {profiler.min_samples * 3}")
            
            return False
            
    except ImportError as e:
        print(f"❌ IMPORT ERROR: {e}")
        print("   Make sure perfilador_dinamico.py exists and is properly structured")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_real_data():
    """Test with actual historical lottery data if available"""
    
    try:
        print("\n🔍 DEBUG: Testing with real historical data...")
        
        # Try to load real historical data
        import pandas as pd
        
        # Look for the CSV file
        data_path = "data/historial_kabala_github.csv"
        
        if os.path.exists(data_path):
            print(f"✅ Found historical data file: {data_path}")
            
            try:
                df = pd.read_csv(data_path)
                print(f"   DataFrame shape: {df.shape}")
                print(f"   Columns: {df.columns.tolist()}")
                
                # Extract combinations (assuming the CSV has number columns)
                historical_data = []
                
                # Look for number columns (Bolilla columns in this case)
                number_cols = [col for col in df.columns if 'Bolilla' in col]
                
                if len(number_cols) >= 6:
                    print(f"   Found number columns: {number_cols[:6]}")
                    
                    for _, row in df.iterrows():
                        try:
                            combination = [int(row[col]) for col in number_cols[:6]]
                            if all(1 <= n <= 40 for n in combination) and len(set(combination)) == 6:
                                historical_data.append(sorted(combination))
                        except (ValueError, TypeError):
                            continue
                else:
                    # Also try looking for columns starting with 'n'
                    number_cols = [col for col in df.columns if col.lower().startswith('n') and col[-1].isdigit()]
                    
                    if len(number_cols) >= 6:
                        print(f"   Found number columns: {number_cols[:6]}")
                        
                        for _, row in df.iterrows():
                            try:
                                combination = [int(row[col]) for col in number_cols[:6]]
                                if all(1 <= n <= 40 for n in combination) and len(set(combination)) == 6:
                                    historical_data.append(sorted(combination))
                            except (ValueError, TypeError):
                                continue
                
                print(f"✅ Extracted {len(historical_data)} valid combinations from CSV")
                
                if len(historical_data) >= 60:  # Enough for training
                    return test_with_data(historical_data[:500])  # Use first 500 for testing
                else:
                    print(f"❌ Not enough valid data: {len(historical_data)} (need at least 60)")
                    return False
                    
            except Exception as csv_error:
                print(f"❌ Error reading CSV: {csv_error}")
                return False
        else:
            print(f"❌ Historical data file not found: {data_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error in real data test: {e}")
        return False

def test_with_data(historical_data):
    """Test training with provided historical data"""
    
    try:
        from modules.perfilador_dinamico import create_dynamic_profiler
        
        profiler = create_dynamic_profiler(window_size=20)
        
        print(f"🔍 Testing with {len(historical_data)} real historical combinations")
        print(f"   First few: {historical_data[:3]}")
        print(f"   Required samples: {profiler.min_samples * 3}")
        
        # Train the profiler
        training_results = profiler.train(historical_data, force_train=False)
        
        print(f"✅ REAL DATA TRAINING SUCCESSFUL!")
        print(f"   Results: {training_results}")
        print(f"   Profiler is_trained: {profiler.is_trained}")
        
        # Test prediction
        if profiler.is_trained:
            recent_data = historical_data[-15:]
            prediction = profiler.predict_profile(recent_data)
            
            print(f"✅ Real data prediction successful!")
            print(f"   Profile: {prediction.profile.value}")
            print(f"   Confidence: {prediction.confidence:.3f}")
            
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Real data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 PERFILADOR DINAMICO TRAINING DEBUG")
    print("="*60)
    
    # Test 1: Basic training with synthetic data
    success1 = test_perfilador_training()
    
    # Test 2: Training with real historical data (if available)
    success2 = test_with_real_data()
    
    print("\n📊 SUMMARY:")
    print(f"   Synthetic data test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"   Real data test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 or success2:
        print("\n🎉 PERFILADOR TRAINING IS WORKING!")
        print("   The issue might be in the integration or data flow.")
    else:
        print("\n❌ PERFILADOR TRAINING HAS ISSUES")
        print("   Need to fix the training method implementation.")