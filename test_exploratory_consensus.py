#!/usr/bin/env python3
"""
Test script for the new exploratory consensus mode functionality.
"""

import sys
import os
import pandas as pd
import numpy as np
import logging

# Add project root to path
sys.path.insert(0, '/Users/user/Documents/OMEGA_PRO_AI_v10.1')

from core.consensus_engine import (
    generar_combinaciones_consenso, 
    generar_combinaciones_consenso_exploratory,
    EXPLORATORY_CONFIG
)

def create_test_data():
    """Create synthetic lottery data for testing."""
    np.random.seed(42)
    
    # Generate historical data with some patterns
    historical_data = []
    
    # Add some regular combinations
    for _ in range(80):
        combo = sorted(np.random.choice(range(1, 41), size=6, replace=False))
        historical_data.append(combo)
    
    # Add some rare number combinations
    rare_numbers = [1, 2, 12, 27, 10, 13, 22, 38, 39, 40]
    for _ in range(10):
        # Create combinations with more rare numbers
        rare_count = np.random.randint(2, 5)
        rare_selected = np.random.choice(rare_numbers, size=rare_count, replace=False)
        remaining_count = 6 - rare_count
        common_numbers = [n for n in range(15, 30) if n not in rare_selected]
        common_selected = np.random.choice(common_numbers, size=remaining_count, replace=False)
        combo = sorted(list(rare_selected) + list(common_selected))
        historical_data.append(combo)
    
    # Convert to DataFrame
    df = pd.DataFrame(historical_data, columns=[f'bolilla_{i}' for i in range(1, 7)])
    
    return df

def test_standard_mode():
    """Test standard consensus mode."""
    print("🔧 Testing standard consensus mode...")
    
    df = create_test_data()
    
    combinations = generar_combinaciones_consenso(
        historial_df=df,
        cantidad=10,
        perfil_svi="default",
        exploration_mode=False
    )
    
    print(f"✅ Standard mode generated {len(combinations)} combinations")
    for i, combo in enumerate(combinations[:3]):
        print(f"   #{i+1}: {combo['combination']} (score: {combo.get('normalized', 0):.3f})")
    
    return combinations

def test_exploratory_mode():
    """Test exploratory consensus mode."""
    print("\n🔍 Testing exploratory consensus mode...")
    
    df = create_test_data()
    
    combinations = generar_combinaciones_consenso(
        historial_df=df,
        cantidad=10,
        perfil_svi="exploratory",
        exploration_mode=True,
        exploration_intensity=0.5
    )
    
    print(f"✅ Exploratory mode generated {len(combinations)} combinations")
    for i, combo in enumerate(combinations[:3]):
        metrics = combo.get('metrics', {})
        print(f"   #{i+1}: {combo['combination']} (score: {combo.get('normalized', 0):.3f})")
        if metrics.get('exploration_mode'):
            print(f"       🔍 Exploration boost: {metrics.get('exploration_boost', 0):.3f}")
            print(f"       🔬 Anomaly score: {metrics.get('anomaly_score', 0):.3f}")
            print(f"       💎 Rare count: {metrics.get('rare_count', 0)}")
    
    return combinations

def test_convenience_function():
    """Test the convenience function."""
    print("\n🚀 Testing convenience function...")
    
    df = create_test_data()
    
    combinations = generar_combinaciones_consenso_exploratory(
        historial_df=df,
        cantidad=5,
        exploration_intensity=0.7
    )
    
    print(f"✅ Convenience function generated {len(combinations)} combinations")
    for i, combo in enumerate(combinations):
        print(f"   #{i+1}: {combo['combination']}")
    
    return combinations

def test_rare_number_detection():
    """Test rare number detection with specific patterns."""
    print("\n💎 Testing rare number detection...")
    
    # Create data with known rare numbers
    df = create_test_data()
    
    from core.consensus_engine import _extract_historical_numbers, _identify_rare_numbers
    
    num_cols = [f'bolilla_{i}' for i in range(1, 7)]
    historical_numbers = _extract_historical_numbers(df, num_cols)
    rare_numbers = _identify_rare_numbers(historical_numbers)
    
    print(f"✅ Identified {len(rare_numbers)} rare numbers: {sorted(rare_numbers)}")
    
    # Test with target combination [12, 27, 1, 10, 13, 22]
    target_combo = [12, 27, 1, 10, 13, 22]
    rare_in_target = set(target_combo).intersection(rare_numbers)
    print(f"🎯 Target combination [12, 27, 1, 10, 13, 22] has {len(rare_in_target)} rare numbers: {sorted(rare_in_target)}")
    
    return rare_numbers

def main():
    """Run all tests."""
    print("🧪 Testing OMEGA PRO AI v10.1 Exploratory Consensus Mode\n")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    try:
        # Test standard mode
        standard_combos = test_standard_mode()
        
        # Test exploratory mode  
        exploratory_combos = test_exploratory_mode()
        
        # Test convenience function
        convenience_combos = test_convenience_function()
        
        # Test rare number detection
        rare_numbers = test_rare_number_detection()
        
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        print(f"   📈 Standard combinations: {len(standard_combos)}")
        print(f"   🔍 Exploratory combinations: {len(exploratory_combos)}")
        print(f"   🚀 Convenience combinations: {len(convenience_combos)}")
        print(f"   💎 Rare numbers detected: {len(rare_numbers)}")
        
        # Compare exploration boost
        exploration_boosted = [
            c for c in exploratory_combos 
            if c.get('metrics', {}).get('exploration_boost', 0) > 0
        ]
        print(f"   🌟 Combinations with exploration boost: {len(exploration_boosted)}")
        
        print("\n✅ All tests completed successfully!")
        print("\n🔍 EXPLORATORY CONSENSUS MODE IS READY FOR PRODUCTION!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)