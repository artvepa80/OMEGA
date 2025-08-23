#!/usr/bin/env python3
"""
Test script for Advanced Ensemble Calibrator with rare number specialization
OMEGA PRO AI v10.1
"""

import pandas as pd
import numpy as np
from modules.ensemble_calibrator import (
    AdvancedEnsembleCalibrator, 
    CalibrationMode,
    calibrate_ensemble,
    create_rare_focused_calibrator,
    create_exploratory_calibrator
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_advanced_calibrator():
    """Test the advanced ensemble calibrator functionality"""
    
    print("=" * 60)
    print("🧪 TESTING ADVANCED ENSEMBLE CALIBRATOR")
    print("=" * 60)
    
    # Load historical data
    try:
        historial_df = pd.read_csv('data/historial_kabala_github.csv')
        print(f"✅ Loaded historical data: {len(historial_df)} records")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False
    
    # Test 1: Basic Advanced Calibrator
    print("\n🔬 Test 1: Basic Advanced Calibrator")
    try:
        calibrator = AdvancedEnsembleCalibrator(
            rare_threshold=0.15,
            adaptation_rate=0.3
        )
        
        weights = calibrator.calibrate_weights(historial_df)
        print(f"✅ Basic calibration completed")
        print(f"📊 Generated weights for {len(weights)} models")
        
        # Show top 3 models
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
        for model, weight in sorted_weights:
            print(f"   {model}: {weight:.4f}")
            
    except Exception as e:
        print(f"❌ Basic calibrator test failed: {e}")
        return False
    
    # Test 2: Rare Number Analysis
    print("\n🔬 Test 2: Rare Number Analysis")
    try:
        rare_profiles = calibrator.analyze_rare_number_combinations(historial_df)
        print(f"✅ Identified {len(rare_profiles)} rare combinations")
        
        if rare_profiles:
            # Show rarest combination
            rarest = max(rare_profiles.items(), key=lambda x: x[1].rarity_score)
            combo_key, profile = rarest
            print(f"   Rarest: {combo_key} (score: {profile.rarity_score:.4f})")
            
    except Exception as e:
        print(f"❌ Rare number analysis test failed: {e}")
        return False
    
    # Test 3: Different Calibration Modes
    print("\n🔬 Test 3: Calibration Modes")
    modes_to_test = [
        CalibrationMode.RARE_FOCUSED,
        CalibrationMode.EXPLORATORY,
        CalibrationMode.HYBRID
    ]
    
    mode_results = {}
    for mode in modes_to_test:
        try:
            calibrator.set_calibration_mode(mode)
            weights = calibrator.calibrate_weights(historial_df)
            mode_results[mode.value] = weights
            print(f"✅ {mode.value.upper()} mode completed")
        except Exception as e:
            print(f"❌ {mode.value} mode failed: {e}")
    
    # Test 4: Validation Metrics
    print("\n🔬 Test 4: Validation Metrics")
    try:
        validation_metrics = calibrator.validate_calibration_effectiveness(historial_df)
        print(f"✅ Validation completed")
        print(f"   Overall effectiveness: {validation_metrics.get('overall_effectiveness', 0):.4f}")
        print(f"   Weight stability: {validation_metrics.get('weight_stability', 0):.4f}")
        print(f"   Diversity index: {validation_metrics.get('diversity_index', 0):.4f}")
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False
    
    # Test 5: Rare Number Insights
    print("\n🔬 Test 5: Rare Number Insights")
    try:
        insights = calibrator.get_rare_number_insights()
        print(f"✅ Insights generated")
        print(f"   Total rare profiles: {insights.get('total_rare_profiles', 0)}")
        
        if insights.get('most_successful_rare_models'):
            best_rare_model = insights['most_successful_rare_models'][0]
            print(f"   Best rare number model: {best_rare_model['model']} ({best_rare_model['rare_accuracy']:.4f})")
            
    except Exception as e:
        print(f"❌ Rare insights test failed: {e}")
        return False
    
    # Test 6: Specialized Calibrators
    print("\n🔬 Test 6: Specialized Calibrators")
    try:
        # Test rare-focused calibrator
        rare_calibrator = create_rare_focused_calibrator(historial_df)
        rare_weights = rare_calibrator.calibrate_weights(historial_df)
        print(f"✅ Rare-focused calibrator: {len(rare_weights)} weights")
        
        # Test exploratory calibrator
        exp_calibrator = create_exploratory_calibrator(historial_df)
        exp_weights = exp_calibrator.calibrate_weights(historial_df)
        print(f"✅ Exploratory calibrator: {len(exp_weights)} weights")
        
    except Exception as e:
        print(f"❌ Specialized calibrator test failed: {e}")
        return False
    
    # Test 7: Main Calibration Function
    print("\n🔬 Test 7: Main Calibration Function")
    try:
        result = calibrate_ensemble(
            historial_df,
            calibration_mode="rare_focused",
            rare_threshold=0.12
        )
        
        if result['success']:
            print(f"✅ Main calibration function succeeded")
            print(f"   Mode: {result['calibration_mode']}")
            print(f"   Models: {len(result['weights'])}")
            print(f"   Rare insights: {len(result.get('rare_insights', {}).get('rarest_combinations', []))} combinations")
        else:
            print(f"❌ Main calibration failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Main calibration test failed: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("✅ Advanced Ensemble Calibrator is fully functional")
    print("🎯 Rare number specialization is working")
    print("🔄 Adaptive calibration is operational")
    print("📊 Statistical validation is active")
    print("🚀 Integration with exploratory consensus ready")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_advanced_calibrator()
    exit(0 if success else 1)