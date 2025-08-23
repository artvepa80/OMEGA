#!/usr/bin/env python3
"""
OMEGA PRO AI v10.1 - A/B Testing Framework Demo
==============================================

Demonstration of how to use the A/B testing framework to validate
rare number prediction improvements and system enhancements.
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.ab_testing.framework import ABTestFramework, ABTestConfig
from modules.ab_testing.omega_integration import OmegaABTestingIntegration
from modules.ab_testing.config_manager import ABTestConfigManager


def demonstrate_rare_number_testing():
    """
    Demonstrate A/B testing for rare number detection improvements.
    
    This example shows how to test improvements for edge cases like
    the combination [12, 27, 1, 10, 13, 22].
    """
    print("\n" + "="*60)
    print("🧪 RARE NUMBER DETECTION A/B TEST DEMO")
    print("="*60)
    
    # Initialize A/B testing integration
    omega_ab = OmegaABTestingIntegration()
    
    # Create a test for rare number detection improvements
    print("\n1. Creating rare number detection test...")
    test_id = omega_ab.create_rare_number_detection_test(
        "Rare Number Enhancement v10.1"
    )
    
    if test_id:
        print(f"✅ Created test: {test_id}")
    else:
        print("❌ Failed to create test")
        return
    
    # Simulate users making predictions
    print("\n2. Simulating user predictions...")
    sample_ids = []
    
    # Test with various prediction scenarios
    test_scenarios = [
        ("user_001", [12, 27, 1, 10, 13, 22]),  # Rare number combination
        ("user_002", [15, 20, 25, 30, 35, 40]),  # Standard combination  
        ("user_003", [3, 8, 31, 38, 41, 42]),    # Mixed rare/normal
        ("user_004", [5, 12, 18, 25, 32, 39]),   # Some rare numbers
        ("user_005", [2, 4, 6, 8, 35, 37]),     # Edge case pattern
    ]
    
    for user_id, prediction in test_scenarios:
        result = omega_ab.make_ab_prediction(
            user_id=user_id,
            test_id=test_id,
            prediction_params={"scenario": "demo"}
        )
        
        variant = result.get("ab_test_metadata", {}).get("variant", "unknown")
        sample_id = result.get("ab_test_metadata", {}).get("sample_id")
        
        print(f"   {user_id}: {variant} variant - {result.get('prediction', [])}")
        
        if sample_id:
            sample_ids.append((sample_id, prediction))
    
    # Simulate lottery results
    print("\n3. Recording lottery results...")
    
    # Simulate actual lottery draws with some rare numbers
    actual_results = [
        [12, 22, 30, 35, 40, 42],  # Contains rare number 12
        [8, 15, 25, 31, 38, 41],   # Contains rare numbers 8, 31, 38, 41
        [5, 18, 22, 28, 33, 39],   # Contains rare number 5
        [14, 19, 26, 32, 37, 42],  # Contains rare numbers 32, 37, 42
        [1, 11, 17, 23, 29, 34],   # Contains rare number 1
    ]
    
    for i, ((sample_id, prediction), actual) in enumerate(zip(sample_ids, actual_results)):
        omega_ab.record_lottery_result(
            test_id=test_id,
            sample_id=sample_id,
            actual_numbers=actual,
            draw_date=f"2025-08-{16+i:02d}"
        )
        
        # Calculate matches
        matches = len(set(prediction).intersection(set(actual)))
        rare_prediction = [n for n in prediction if n < 10 or n > 30]
        rare_actual = [n for n in actual if n < 10 or n > 30]
        rare_matches = len(set(rare_prediction).intersection(set(rare_actual)))
        
        print(f"   Draw {i+1}: {matches}/6 matches, {rare_matches} rare matches")
    
    # Check test status
    print("\n4. Checking test status...")
    status = omega_ab.get_test_dashboard_data(test_id)
    
    test_status = status.get("test_status", {})
    print(f"   Total samples: {test_status.get('total_samples', 0)}")
    print(f"   Completed samples: {test_status.get('completed_samples', 0)}")
    print(f"   Ready for analysis: {test_status.get('ready_for_analysis', False)}")
    
    if test_status.get('ready_for_analysis', False):
        print("\n5. Analyzing test results...")
        analysis = status.get("analysis_results", {})
        
        if analysis and "error" not in analysis:
            performance = analysis.get("performance", {})
            overall = performance.get("overall_assessment", {})
            
            print(f"   Overall score: {overall.get('overall_score', 0)*100:.1f}%")
            print(f"   Recommendation: {overall.get('recommendation', 'N/A')}")
            
            # Rare number specific analysis
            rare_analysis = performance.get("rare_number_analysis", {})
            if rare_analysis and "error" not in rare_analysis:
                rare_acc = rare_analysis.get("overall_rare_accuracy", {})
                improvement = rare_acc.get("improvement", 0) * 100
                print(f"   Rare number improvement: {improvement:+.1f}%")
        
        print("\n6. Stopping test...")
        success = omega_ab.emergency_stop_test(test_id, "Demo completed")
        print(f"   Test stopped: {'✅' if success else '❌'}")
    
    print(f"\n🎉 Rare number detection A/B test demo completed!")


def demonstrate_performance_optimization():
    """
    Demonstrate A/B testing for system performance optimizations.
    """
    print("\n" + "="*60)
    print("⚡ PERFORMANCE OPTIMIZATION A/B TEST DEMO")
    print("="*60)
    
    # Initialize A/B testing integration
    omega_ab = OmegaABTestingIntegration()
    
    print("\n1. Creating performance optimization test...")
    test_id = omega_ab.create_performance_optimization_test(
        "System Performance Enhancement v10.1"
    )
    
    if test_id:
        print(f"✅ Created test: {test_id}")
    else:
        print("❌ Failed to create test")
        return
    
    print("\n2. Simulating performance-focused predictions...")
    
    # Simulate predictions with timing
    for i in range(3):
        user_id = f"perf_user_{i+1}"
        
        start_time = time.time()
        result = omega_ab.make_ab_prediction(
            user_id=user_id,
            test_id=test_id,
            prediction_params={"performance_test": True}
        )
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000  # Convert to ms
        variant = result.get("ab_test_metadata", {}).get("variant", "unknown")
        
        print(f"   {user_id}: {variant} variant - {latency:.1f}ms latency")
    
    print(f"\n⚡ Performance optimization demo completed!")


def demonstrate_config_management():
    """
    Demonstrate A/B testing configuration management.
    """
    print("\n" + "="*60)
    print("⚙️ CONFIGURATION MANAGEMENT DEMO")
    print("="*60)
    
    # Initialize config manager
    config_manager = ABTestConfigManager()
    
    print("\n1. Creating test configuration template...")
    
    # Create a rare number detection template
    template = config_manager.create_test_config_template("rare_number_detection")
    print(f"   Template created: {template['test_id']}")
    print(f"   Test name: {template['name']}")
    print(f"   Primary metric: {template['primary_metric']}")
    
    print("\n2. Validating test configuration...")
    is_valid, errors = config_manager.validate_test_config(template)
    
    if is_valid:
        print("   ✅ Configuration is valid")
    else:
        print("   ❌ Configuration errors:")
        for error in errors:
            print(f"      - {error}")
    
    print("\n3. Saving test configuration...")
    if is_valid:
        success = config_manager.save_test_config(template)
        print(f"   Configuration saved: {'✅' if success else '❌'}")
    
    print("\n4. Loading test configuration...")
    loaded_config = config_manager.load_test_config(template['test_id'])
    if loaded_config:
        print(f"   ✅ Loaded config for: {loaded_config['name']}")
    
    print(f"\n⚙️ Configuration management demo completed!")


def demonstrate_statistical_analysis():
    """
    Demonstrate statistical analysis capabilities.
    """
    print("\n" + "="*60)
    print("📊 STATISTICAL ANALYSIS DEMO")  
    print("="*60)
    
    from modules.ab_testing.statistical_analyzer import StatisticalAnalyzer
    from unittest.mock import MagicMock
    import random
    
    # Initialize analyzer
    analyzer = StatisticalAnalyzer()
    
    print("\n1. Creating mock sample data...")
    
    # Create mock control samples (standard performance)
    control_samples = []
    for i in range(50):
        sample = MagicMock()
        sample.metrics = {
            "accuracy": 0.15 + random.uniform(-0.05, 0.05),
            "rare_number_detection": 0.08 + random.uniform(-0.03, 0.03),
            "latency_ms": 150 + random.uniform(-30, 30)
        }
        control_samples.append(sample)
    
    # Create mock treatment samples (improved performance)  
    treatment_samples = []
    for i in range(50):
        sample = MagicMock()
        sample.metrics = {
            "accuracy": 0.20 + random.uniform(-0.05, 0.05),  # 5% improvement
            "rare_number_detection": 0.15 + random.uniform(-0.03, 0.03),  # 7% improvement
            "latency_ms": 140 + random.uniform(-25, 25)  # Slight improvement
        }
        treatment_samples.append(sample)
    
    print(f"   Control samples: {len(control_samples)}")
    print(f"   Treatment samples: {len(treatment_samples)}")
    
    print("\n2. Performing statistical analysis...")
    
    results = analyzer.analyze_test_results(control_samples, treatment_samples)
    
    if "error" not in results:
        summary = results.get("summary", {})
        print(f"   Total metrics analyzed: {summary.get('total_metrics_analyzed', 0)}")
        print(f"   Significant results: {summary.get('significant_results', 0)}")
        
        # Show metric results
        metric_results = results.get("metric_results", [])
        for result in metric_results:
            metric = result.get("metric_name", "unknown")
            p_value = result.get("p_value", 1.0)
            improvement = result.get("improvement_pct", 0)
            significant = result.get("significant", False)
            
            status = "✅ Significant" if significant else "⚪ Not significant"
            print(f"   {metric}: {improvement:+.1f}% change (p={p_value:.4f}) {status}")
    
    print("\n3. Power analysis demonstration...")
    
    # Calculate required sample size for different effect sizes
    effect_sizes = [0.2, 0.5, 0.8]  # Small, medium, large
    
    for effect_size in effect_sizes:
        required_n = analyzer.power_analysis(effect_size=effect_size, power=0.8)
        magnitude = "small" if effect_size == 0.2 else "medium" if effect_size == 0.5 else "large"
        print(f"   {magnitude.capitalize()} effect (d={effect_size}): {required_n} samples needed")
    
    print(f"\n📊 Statistical analysis demo completed!")


def main():
    """
    Main demo function showing all A/B testing capabilities.
    """
    print("🚀 OMEGA PRO AI v10.1 - A/B Testing Framework Demo")
    print("=" * 80)
    print("\nThis demo showcases the comprehensive A/B testing framework")
    print("designed to validate prediction improvements and system enhancements.")
    print("\nKey focus: Validating rare number prediction improvements")
    print("Edge case example: [12, 27, 1, 10, 13, 22]")
    
    try:
        # Run all demonstrations
        demonstrate_config_management()
        demonstrate_statistical_analysis()
        demonstrate_rare_number_testing()
        demonstrate_performance_optimization()
        
        print("\n" + "="*80)
        print("🎉 A/B TESTING FRAMEWORK DEMO COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        print("\nThe framework provides:")
        print("✅ Statistical rigor with proper significance testing")
        print("✅ Special focus on rare number detection validation") 
        print("✅ Performance impact measurement and monitoring")
        print("✅ Safe feature flag rollouts with emergency stops")
        print("✅ Comprehensive reporting and dashboard capabilities")
        print("✅ Integration with existing OMEGA prediction systems")
        
        print("\nNext steps:")
        print("1. Configure your first A/B test using the template")
        print("2. Integrate with OMEGA's prediction pipeline") 
        print("3. Set up monitoring and alerts for key metrics")
        print("4. Run tests to validate rare number improvements")
        
        print("\n📖 See README_AB_TESTING.md for detailed documentation")
        
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")
        print("\nThis is expected in a demo environment.")
        print("In production, ensure all dependencies are properly configured.")


if __name__ == "__main__":
    main()