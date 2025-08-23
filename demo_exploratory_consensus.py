#!/usr/bin/env python3
"""
Demonstration of the new Exploratory Consensus Mode in OMEGA PRO AI v10.1

This script shows how to use the enhanced consensus engine to detect and 
prioritize rare number combinations like [12, 27, 1, 10, 13, 22].
"""

import sys
import pandas as pd
import numpy as np
import logging

# Add project root to path
sys.path.insert(0, '/Users/user/Documents/OMEGA_PRO_AI_v10.1')

# Disable heavy ML models for this demo
import core.consensus_engine as ce
ce.USE_LSTM = False
ce.USE_TRANSFORMER = False
ce.USE_GBOOST = False

from core.consensus_engine import (
    generar_combinaciones_consenso,
    generar_combinaciones_consenso_exploratory,
    PESO_MAP,
    EXPLORATORY_CONFIG
)

def load_demo_data():
    """Load demo lottery data with known patterns."""
    print("📊 Loading demo lottery data...")
    
    # Create realistic lottery data with some rare number patterns
    np.random.seed(42)
    data = []
    
    # Generate 100 historical draws
    for i in range(100):
        if i % 20 == 0:  # Every 20th draw has rare numbers
            # Create combinations with rare numbers (1, 2, 12, 27, 10, 13, 22, 38, 39, 40)
            rare_pool = [1, 2, 12, 27, 10, 13, 22, 38, 39, 40]
            common_pool = list(range(5, 36))
            
            rare_count = np.random.randint(2, 4)  # 2-3 rare numbers
            rare_selected = np.random.choice(rare_pool, size=rare_count, replace=False)
            common_selected = np.random.choice(common_pool, size=6-rare_count, replace=False)
            
            combo = sorted(list(rare_selected) + list(common_selected))
        else:
            # Normal combinations from middle range
            combo = sorted(np.random.choice(range(8, 35), size=6, replace=False))
        
        data.append(combo)
    
    # Add the specific target combination
    data.append([12, 27, 1, 10, 13, 22])
    
    df = pd.DataFrame(data, columns=[f'bolilla_{i}' for i in range(1, 7)])
    print(f"   ✅ Loaded {len(df)} historical draws")
    return df

def demo_standard_mode(df):
    """Demonstrate standard consensus mode."""
    print("\n🔹 STANDARD CONSENSUS MODE")
    print("-" * 50)
    
    combinations = generar_combinaciones_consenso(
        historial_df=df,
        cantidad=10,
        perfil_svi="default",
        exploration_mode=False
    )
    
    print(f"Generated {len(combinations)} combinations:")
    for i, combo in enumerate(combinations[:5]):
        score = combo.get('normalized', combo.get('score', 0))
        source = combo.get('source', 'unknown')
        print(f"   #{i+1}: {combo['combination']} (score: {score:.3f}, source: {source})")
    
    return combinations

def demo_exploratory_mode(df):
    """Demonstrate exploratory consensus mode."""
    print("\n🔍 EXPLORATORY CONSENSUS MODE")
    print("-" * 50)
    
    combinations = generar_combinaciones_consenso(
        historial_df=df,
        cantidad=10,
        perfil_svi="exploratory",
        exploration_mode=True,
        exploration_intensity=0.7
    )
    
    print(f"Generated {len(combinations)} combinations:")
    for i, combo in enumerate(combinations[:5]):
        score = combo.get('normalized', combo.get('score', 0))
        source = combo.get('source', 'unknown')
        metrics = combo.get('metrics', {})
        
        print(f"   #{i+1}: {combo['combination']} (score: {score:.3f}, source: {source})")
        
        if metrics.get('exploration_mode'):
            print(f"        🚀 Exploration boost: {metrics.get('exploration_boost', 0):.3f}")
            print(f"        🔬 Anomaly score: {metrics.get('anomaly_score', 0):.3f}")
            print(f"        🌈 Diversity bonus: {metrics.get('diversity_bonus', 0):.3f}")
            print(f"        💎 Rare numbers: {metrics.get('rare_count', 0)}")
    
    return combinations

def demo_convenience_function(df):
    """Demonstrate the convenience function."""
    print("\n🚀 CONVENIENCE FUNCTION (generar_combinaciones_consenso_exploratory)")
    print("-" * 70)
    
    combinations = generar_combinaciones_consenso_exploratory(
        historial_df=df,
        cantidad=5,
        exploration_intensity=0.8
    )
    
    print(f"Generated {len(combinations)} combinations with high exploration intensity:")
    for i, combo in enumerate(combinations):
        score = combo.get('normalized', combo.get('score', 0))
        metrics = combo.get('metrics', {})
        print(f"   #{i+1}: {combo['combination']} (score: {score:.3f})")
        if metrics.get('rare_count', 0) > 0:
            print(f"        💎 Contains {metrics.get('rare_count', 0)} rare numbers")
    
    return combinations

def analyze_rare_detection(standard_combos, exploratory_combos):
    """Analyze how well the system detects rare combinations."""
    print("\n📈 RARE NUMBER DETECTION ANALYSIS")
    print("-" * 50)
    
    target_combo = [12, 27, 1, 10, 13, 22]
    
    # Check if target combination appears in results
    def contains_target_numbers(combo_list, target):
        for combo in combo_list:
            intersection = set(combo['combination']).intersection(set(target))
            if len(intersection) >= 4:  # At least 4 numbers match
                return combo, len(intersection)
        return None, 0
    
    std_match, std_count = contains_target_numbers(standard_combos, target_combo)
    exp_match, exp_count = contains_target_numbers(exploratory_combos, target_combo)
    
    print(f"Target rare combination: {target_combo}")
    print(f"Standard mode best match: {std_count} numbers")
    if std_match:
        print(f"   Combo: {std_match['combination']}")
    
    print(f"Exploratory mode best match: {exp_count} numbers")
    if exp_match:
        print(f"   Combo: {exp_match['combination']}")
        metrics = exp_match.get('metrics', {})
        if metrics.get('exploration_mode'):
            print(f"   🚀 Exploration boost: {metrics.get('exploration_boost', 0):.3f}")
    
    # Count combinations with rare numbers
    def count_rare_combos(combo_list):
        rare_numbers = {1, 2, 12, 27, 10, 13, 22, 38, 39, 40}
        count = 0
        for combo in combo_list[:10]:  # Top 10
            rare_in_combo = set(combo['combination']).intersection(rare_numbers)
            if len(rare_in_combo) >= 2:
                count += 1
        return count
    
    std_rare_count = count_rare_combos(standard_combos)
    exp_rare_count = count_rare_combos(exploratory_combos)
    
    print(f"\nTop 10 combinations with 2+ rare numbers:")
    print(f"   Standard mode: {std_rare_count}/10")
    print(f"   Exploratory mode: {exp_rare_count}/10")
    
    improvement = ((exp_rare_count - std_rare_count) / max(std_rare_count, 1)) * 100
    if improvement > 0:
        print(f"   📈 Improvement: +{improvement:.1f}%")
    else:
        print(f"   📉 Change: {improvement:.1f}%")

def show_configuration():
    """Show the exploratory configuration."""
    print("\n⚙️ EXPLORATORY CONFIGURATION")
    print("-" * 40)
    
    print("PESO_MAP profiles available:")
    for profile, weights in PESO_MAP.items():
        print(f"   {profile}: {weights}")
    
    print(f"\nEXPLORATORY_CONFIG:")
    for key, value in EXPLORATORY_CONFIG.items():
        print(f"   {key}: {value}")

def main():
    """Main demonstration."""
    print("🎯 OMEGA PRO AI v10.1 - Exploratory Consensus Mode Demo")
    print("=" * 60)
    
    # Configure minimal logging
    logging.basicConfig(level=logging.WARNING)
    
    # Load demo data
    df = load_demo_data()
    
    # Show configuration
    show_configuration()
    
    # Demonstrate standard mode
    standard_combos = demo_standard_mode(df)
    
    # Demonstrate exploratory mode
    exploratory_combos = demo_exploratory_mode(df)
    
    # Demonstrate convenience function
    convenience_combos = demo_convenience_function(df)
    
    # Analyze rare number detection
    analyze_rare_detection(standard_combos, exploratory_combos)
    
    print("\n" + "=" * 60)
    print("🎉 DEMO COMPLETED SUCCESSFULLY!")
    print("\n✨ Key Features Demonstrated:")
    print("   🔍 Exploration mode toggle")
    print("   🚀 Dynamic exploration boost for rare combinations")
    print("   🔬 Anomaly score calculation for edge cases")
    print("   🌈 Enhanced diversity bonus system")
    print("   💎 Rare number detection and prioritization")
    print("   ⚙️ Flexible configuration system")
    print("   🔄 Full backward compatibility")
    
    print("\n🎯 Ready to detect rare combinations like [12, 27, 1, 10, 13, 22]!")
    print("   Use exploration_mode=True for rare number hunting")
    print("   Use exploration_intensity=0.1-1.0 to control aggressiveness")
    print("   Use generar_combinaciones_consenso_exploratory() for convenience")

if __name__ == "__main__":
    main()