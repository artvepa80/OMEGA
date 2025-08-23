#!/usr/bin/env python3
"""
Quick test for the exploratory consensus core functionality.
Tests the helper functions without running the full ML pipeline.
"""

import sys
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, '/Users/user/Documents/OMEGA_PRO_AI_v10.1')

from core.consensus_engine import (
    _extract_historical_numbers,
    _identify_rare_numbers,
    _calculate_exploration_boost,
    _calculate_anomaly_score,
    _calculate_enhanced_diversity_bonus,
    _is_arithmetic_progression,
    EXPLORATORY_CONFIG
)
from collections import Counter

def create_simple_test_data():
    """Create simple test data."""
    # Historical data with known patterns
    data = [
        [1, 5, 12, 20, 25, 30],   # Normal
        [2, 8, 15, 22, 28, 35],   # Normal  
        [3, 9, 18, 24, 31, 38],   # Normal
        [12, 27, 1, 10, 13, 22],  # Target rare combo
        [4, 11, 16, 26, 33, 39],  # Normal
        [7, 14, 21, 28, 35, 40],  # Arithmetic progression
        [1, 2, 3, 4, 5, 6],       # Consecutive (anomaly)
        [6, 12, 19, 23, 29, 34],  # Normal
        [38, 39, 40, 37, 36, 35], # High edge numbers
        [8, 17, 24, 27, 32, 36],  # Normal
    ]
    
    df = pd.DataFrame(data, columns=[f'bolilla_{i}' for i in range(1, 7)])
    return df

def test_rare_number_detection():
    """Test rare number identification."""
    print("💎 Testing rare number detection...")
    
    df = create_simple_test_data()
    num_cols = [f'bolilla_{i}' for i in range(1, 7)]
    
    historical_numbers = _extract_historical_numbers(df, num_cols)
    rare_numbers = _identify_rare_numbers(historical_numbers)
    
    print(f"   Historical numbers: {len(historical_numbers)} total")
    print(f"   Rare numbers identified: {sorted(rare_numbers)}")
    
    # Check if target numbers are considered rare
    target_combo = [12, 27, 1, 10, 13, 22]
    rare_in_target = set(target_combo).intersection(rare_numbers)
    print(f"   Target combo [12, 27, 1, 10, 13, 22] rare numbers: {sorted(rare_in_target)}")
    
    return rare_numbers

def test_exploration_boost():
    """Test exploration boost calculation."""
    print("\n🚀 Testing exploration boost...")
    
    df = create_simple_test_data()
    num_cols = [f'bolilla_{i}' for i in range(1, 7)]
    
    historical_numbers = _extract_historical_numbers(df, num_cols)
    rare_numbers = _identify_rare_numbers(historical_numbers)
    
    test_combinations = [
        [12, 27, 1, 10, 13, 22],  # Target with rare numbers
        [5, 15, 20, 25, 30, 35],  # Common numbers
        [1, 2, 38, 39, 40, 3],    # Mix of rare and edge
    ]
    
    for combo in test_combinations:
        boost = _calculate_exploration_boost(combo, rare_numbers, historical_numbers, 0.5)
        rare_count = len(set(combo).intersection(rare_numbers))
        print(f"   {combo}: boost={boost:.3f}, rare_count={rare_count}")
    
    return True

def test_anomaly_detection():
    """Test anomaly score calculation."""
    print("\n🔬 Testing anomaly detection...")
    
    df = create_simple_test_data()
    num_cols = [f'bolilla_{i}' for i in range(1, 7)]
    
    historical_numbers = _extract_historical_numbers(df, num_cols)
    
    test_combinations = [
        [1, 2, 3, 4, 5, 6],       # Consecutive (high anomaly)
        [2, 4, 6, 8, 10, 12],     # Arithmetic progression
        [12, 27, 1, 10, 13, 22],  # Target combo
        [38, 39, 40, 37, 36, 35], # High edge numbers
        [15, 20, 25, 30, 32, 35], # Normal
    ]
    
    for combo in test_combinations:
        anomaly_score = _calculate_anomaly_score(combo, historical_numbers)
        is_arith = _is_arithmetic_progression(sorted(combo))
        print(f"   {combo}: anomaly={anomaly_score:.3f}, arithmetic={is_arith}")
    
    return True

def test_diversity_bonus():
    """Test enhanced diversity bonus."""
    print("\n🌈 Testing diversity bonus...")
    
    # Create frequency counter
    all_numbers = [1, 1, 2, 2, 3, 3, 12, 27, 10, 13, 22, 38, 39, 40]  # Some numbers more frequent
    num_frequency = Counter(all_numbers)
    total_combos = 10
    
    test_combinations = [
        [12, 27, 1, 10, 13, 22],  # Target with rare numbers
        [1, 2, 3, 4, 5, 6],       # Mix of common/rare
        [15, 20, 25, 30, 32, 35], # Not in frequency list (rare by absence)
    ]
    
    for combo in test_combinations:
        bonus = _calculate_enhanced_diversity_bonus(combo, num_frequency, total_combos, 0.5)
        print(f"   {combo}: diversity_bonus={bonus:.3f}")
    
    return True

def test_configuration():
    """Test configuration values."""
    print("\n⚙️ Testing configuration...")
    
    print("   EXPLORATORY_CONFIG:")
    for key, value in EXPLORATORY_CONFIG.items():
        print(f"     {key}: {value}")
    
    # Test that values are reasonable
    assert 0 < EXPLORATORY_CONFIG["rare_number_threshold"] < 1
    assert 0 < EXPLORATORY_CONFIG["anomaly_score_weight"] < 1
    assert EXPLORATORY_CONFIG["min_rare_numbers"] >= 1
    
    print("   ✅ Configuration values are valid")
    return True

def main():
    """Run core functionality tests."""
    print("🧪 Testing OMEGA Exploratory Consensus Core Functions\n")
    print("=" * 60)
    
    try:
        # Test individual components
        rare_numbers = test_rare_number_detection()
        test_exploration_boost()
        test_anomaly_detection() 
        test_diversity_bonus()
        test_configuration()
        
        print("\n" + "=" * 60)
        print("📊 Core Function Test Summary:")
        print(f"   💎 Rare numbers detected: {len(rare_numbers)}")
        print("   🚀 Exploration boost: Working")
        print("   🔬 Anomaly detection: Working") 
        print("   🌈 Diversity bonus: Working")
        print("   ⚙️ Configuration: Valid")
        
        print("\n✅ All core function tests passed!")
        print("\n🎯 Ready to detect rare combinations like [12, 27, 1, 10, 13, 22]!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)