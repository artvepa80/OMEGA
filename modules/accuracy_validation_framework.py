# OMEGA_PRO_AI_v10.1/modules/accuracy_validation_framework.py
"""
Accuracy Validation Framework for OMEGA PRO AI
Validates and benchmarks ML optimizations against 50% baseline accuracy
Tests the enhanced models targeting 65-70% accuracy improvement
"""

import logging
import numpy as np
import pandas as pd
import json
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import datetime
from collections import defaultdict, Counter
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import StratifiedKFold
from scipy.stats import ttest_ind
import matplotlib.pyplot as plt
import seaborn as sns

# Set reproducibility seeds
np.random.seed(42)
torch.manual_seed(42) if 'torch' in globals() else None

# Local imports
from modules.advanced_feature_engineering import AdvancedFeatureEngineer
from modules.lstm_model_enhanced import generar_combinaciones_lstm_enhanced
from modules.advanced_ensemble_system import generar_combinaciones_ensemble_advanced
from modules.model_optimization_suite import (
    generar_combinaciones_transformer_optimized,
    generar_combinaciones_gboost_optimized
)

logger = logging.getLogger(__name__)

class AccuracyValidationFramework:
    """
    Comprehensive validation framework to test ML improvements
    
    Validation Methods:
    1. Historical Backtesting - Test on recent draws
    2. Cross-Validation - Multiple time periods
    3. Pattern Recognition Validation - Test specific patterns (consecutive pairs, hot numbers)
    4. Benchmark Comparison - Compare against baseline 50% accuracy
    """
    
    def __init__(self, baseline_accuracy: float = 0.50):
        self.baseline_accuracy = baseline_accuracy
        self.validation_results = defaultdict(list)
        self.pattern_analysis_results = {}
        # Set reproducibility
        np.random.seed(42)
        
    def calculate_lottery_accuracy(self, predictions: List[Dict[str, Any]], 
                                 actual_result: List[int]) -> Dict[str, float]:
        """
        Calculate lottery-specific accuracy metrics
        
        Args:
            predictions: List of prediction dictionaries
            actual_result: Actual lottery result [6 numbers]
            
        Returns:
            Dictionary with accuracy metrics
        """
        actual_set = set(actual_result)
        
        # Metrics for all predictions
        best_match = 0
        total_matches = []
        exact_matches = 0
        
        for pred in predictions:
            combination = pred.get('combination', [])
            pred_set = set(combination)
            
            # Number of matching numbers
            matches = len(actual_set.intersection(pred_set))
            total_matches.append(matches)
            
            # Track best match
            best_match = max(best_match, matches)
            
            # Exact match
            if matches == 6:
                exact_matches += 1
        
        # Calculate metrics
        avg_matches = np.mean(total_matches) if total_matches else 0
        match_rate = avg_matches / 6  # Normalize to 0-1
        
        # Partial hit analysis (2+ numbers is considered a "win" in many lotteries)
        partial_hits = sum(1 for m in total_matches if m >= 2)
        partial_hit_rate = partial_hits / len(predictions) if predictions else 0
        
        # Success rate based on best prediction
        success_rate = best_match / 6
        
        return {
            'exact_accuracy': float(exact_matches > 0),  # Binary: did we get exact match?
            'best_match_accuracy': success_rate,  # Best single prediction accuracy
            'average_match_rate': match_rate,  # Average matching rate across all predictions
            'partial_hit_rate': partial_hit_rate,  # Rate of 2+ number matches
            'best_matches': int(best_match),
            'total_predictions': len(predictions),
            'average_matches': avg_matches
        }
    
    def validate_consecutive_pairs_prediction(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate the consecutive pairs pattern (74.5% of draws contain them)
        This was a key finding from data scientist analysis
        """
        results = {
            'predictions_with_consecutive': 0,
            'total_predictions': len(predictions),
            'consecutive_pair_rate': 0,
            'identified_pairs': []
        }
        
        for pred in predictions:
            combination = sorted(pred.get('combination', []))
            
            # Check for consecutive pairs
            consecutive_pairs = []
            for i in range(len(combination) - 1):
                if combination[i+1] - combination[i] == 1:
                    consecutive_pairs.append((combination[i], combination[i+1]))
            
            if consecutive_pairs:
                results['predictions_with_consecutive'] += 1
                results['identified_pairs'].extend(consecutive_pairs)
        
        if results['total_predictions'] > 0:
            results['consecutive_pair_rate'] = results['predictions_with_consecutive'] / results['total_predictions']
        
        # Target: 74.5% should contain consecutive pairs
        results['target_rate'] = 0.745
        results['meets_target'] = results['consecutive_pair_rate'] >= 0.60  # Allow some tolerance
        
        return results
    
    def validate_hot_number_detection(self, predictions: List[Dict[str, Any]], 
                                    hot_numbers: List[int] = [39, 28, 29]) -> Dict[str, Any]:
        """
        Validate hot number momentum detection (number 39 showing 2.0x frequency)
        """
        results = {
            'predictions_with_hot_numbers': 0,
            'total_predictions': len(predictions),
            'hot_number_inclusion_rate': 0,
            'hot_number_counts': Counter()
        }
        
        for pred in predictions:
            combination = pred.get('combination', [])
            
            # Check for hot numbers
            found_hot = []
            for hot_num in hot_numbers:
                if hot_num in combination:
                    found_hot.append(hot_num)
                    results['hot_number_counts'][hot_num] += 1
            
            if found_hot:
                results['predictions_with_hot_numbers'] += 1
        
        if results['total_predictions'] > 0:
            results['hot_number_inclusion_rate'] = results['predictions_with_hot_numbers'] / results['total_predictions']
        
        # Number 39 should appear frequently (2.0x expected rate)
        expected_rate_39 = 6/40  # Expected rate for any number
        actual_rate_39 = results['hot_number_counts'][39] / results['total_predictions'] if results['total_predictions'] > 0 else 0
        results['number_39_momentum'] = actual_rate_39 / expected_rate_39 if expected_rate_39 > 0 else 0
        results['meets_momentum_target'] = results['number_39_momentum'] >= 1.5  # Target: 2.0x, allow 1.5x tolerance
        
        return results
    
    def validate_position_preferences(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate position-specific preferences (1-20 prefer positions 1-3, 21-40 prefer 4-6)
        """
        results = {
            'early_numbers_in_early_positions': 0,
            'late_numbers_in_late_positions': 0,
            'total_early_placements': 0,
            'total_late_placements': 0,
            'position_preference_accuracy': 0
        }
        
        for pred in predictions:
            combination = pred.get('combination', [])
            if len(combination) == 6:
                # Check early numbers (1-20) in early positions (1-3)
                early_positions = combination[:3]
                late_positions = combination[3:]
                
                early_in_early = sum(1 for num in early_positions if 1 <= num <= 20)
                late_in_late = sum(1 for num in late_positions if 21 <= num <= 40)
                
                results['early_numbers_in_early_positions'] += early_in_early
                results['late_numbers_in_late_positions'] += late_in_late
                results['total_early_placements'] += 3  # 3 early positions
                results['total_late_placements'] += 3   # 3 late positions
        
        # Calculate accuracy rates
        if results['total_early_placements'] > 0:
            early_accuracy = results['early_numbers_in_early_positions'] / results['total_early_placements']
        else:
            early_accuracy = 0
            
        if results['total_late_placements'] > 0:
            late_accuracy = results['late_numbers_in_late_positions'] / results['total_late_placements']
        else:
            late_accuracy = 0
        
        results['early_position_accuracy'] = early_accuracy
        results['late_position_accuracy'] = late_accuracy
        results['overall_position_accuracy'] = (early_accuracy + late_accuracy) / 2
        
        # Target: Better than random (50%)
        results['meets_position_target'] = results['overall_position_accuracy'] > 0.55
        
        return results
    
    def backtest_model(self, model_generator: callable, historial_df: pd.DataFrame,
                      test_periods: int = 10, predictions_per_test: int = 10) -> Dict[str, Any]:
        """
        Perform backtesting on a specific model
        
        Args:
            model_generator: Function to generate predictions
            historial_df: Historical data
            test_periods: Number of test periods
            predictions_per_test: Predictions per test
            
        Returns:
            Backtesting results
        """
        logger.info(f"🔄 Backtesting model with {test_periods} periods...")
        
        results = {
            'test_accuracies': [],
            'consecutive_pair_results': [],
            'hot_number_results': [],
            'position_preference_results': [],
            'pattern_analysis': {}
        }
        
        # Ensure we have enough data for backtesting
        if len(historial_df) < test_periods + 20:
            logger.warning("Insufficient data for comprehensive backtesting")
            test_periods = max(1, len(historial_df) // 4)
        
        for i in range(test_periods):
            try:
                # Split data: use everything except the last (test_periods - i) draws for training
                train_end_idx = len(historial_df) - (test_periods - i)
                test_idx = train_end_idx
                
                if test_idx >= len(historial_df):
                    continue
                
                train_data = historial_df.iloc[:train_end_idx]
                actual_result_row = historial_df.iloc[test_idx]
                
                # Get actual result
                numeric_cols = [col for col in historial_df.columns 
                               if 'bolilla' in col.lower() or col.startswith('Bolilla')]
                actual_result = [int(actual_result_row[col]) for col in numeric_cols[:6]]
                
                # Generate predictions
                predictions = model_generator(train_data, predictions_per_test)
                
                # Calculate accuracy metrics
                accuracy_metrics = self.calculate_lottery_accuracy(predictions, actual_result)
                results['test_accuracies'].append(accuracy_metrics)
                
                # Pattern validation
                consecutive_results = self.validate_consecutive_pairs_prediction(predictions)
                hot_number_results = self.validate_hot_number_detection(predictions)
                position_results = self.validate_position_preferences(predictions)
                
                results['consecutive_pair_results'].append(consecutive_results)
                results['hot_number_results'].append(hot_number_results)
                results['position_preference_results'].append(position_results)
                
                logger.info(f"Test {i+1}: Best match {accuracy_metrics['best_matches']}/6, "
                          f"Avg rate: {accuracy_metrics['average_match_rate']:.3f}")
                
            except Exception as e:
                logger.error(f"Error in backtest period {i}: {e}")
                continue
        
        # Aggregate results
        if results['test_accuracies']:
            avg_accuracy = np.mean([r['average_match_rate'] for r in results['test_accuracies']])
            best_match_avg = np.mean([r['best_match_accuracy'] for r in results['test_accuracies']])
            partial_hit_avg = np.mean([r['partial_hit_rate'] for r in results['test_accuracies']])
            
            results['summary'] = {
                'average_accuracy': avg_accuracy,
                'best_match_accuracy': best_match_avg,
                'partial_hit_rate': partial_hit_avg,
                'improvement_vs_baseline': (avg_accuracy - self.baseline_accuracy) / self.baseline_accuracy,
                'test_periods': len(results['test_accuracies'])
            }
        else:
            results['summary'] = {'error': 'No successful test periods'}
        
        return results
    
    def comprehensive_model_validation(self, historial_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run comprehensive validation on all enhanced models
        """
        logger.info("🚀 Starting comprehensive model validation...")
        
        validation_results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'baseline_accuracy': self.baseline_accuracy,
            'target_accuracy': 0.65,  # 65-70% target
            'models': {}
        }
        
        # Define models to test
        models_to_test = {
            'enhanced_lstm': lambda df, n: generar_combinaciones_lstm_enhanced(df, n),
            'advanced_ensemble': lambda df, n: generar_combinaciones_ensemble_advanced(df, n),
            'optimized_transformer': lambda df, n: generar_combinaciones_transformer_optimized(df, n),
            'optimized_gboost': lambda df, n: generar_combinaciones_gboost_optimized(df, n)
        }
        
        # Test each model
        for model_name, model_func in models_to_test.items():
            try:
                logger.info(f"🧪 Testing {model_name}...")
                
                # Run backtest
                backtest_results = self.backtest_model(
                    model_func, 
                    historial_df, 
                    test_periods=min(10, len(historial_df) // 10),
                    predictions_per_test=15
                )
                
                validation_results['models'][model_name] = backtest_results
                
                if 'summary' in backtest_results:
                    summary = backtest_results['summary']
                    logger.info(f"✅ {model_name} - Avg Accuracy: {summary['average_accuracy']:.3f}, "
                              f"Improvement: {summary['improvement_vs_baseline']:.2%}")
                
            except Exception as e:
                logger.error(f"❌ Error testing {model_name}: {e}")
                validation_results['models'][model_name] = {'error': str(e)}
        
        # Generate overall assessment
        validation_results['assessment'] = self._generate_overall_assessment(validation_results)
        
        # Save results
        self._save_validation_results(validation_results)
        
        return validation_results
    
    def _generate_overall_assessment(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall assessment of the validation results"""
        assessment = {
            'models_tested': len(validation_results['models']),
            'successful_models': 0,
            'target_achieved': False,
            'best_model': None,
            'best_accuracy': 0,
            'recommendations': []
        }
        
        # Analyze model performance
        for model_name, results in validation_results['models'].items():
            if 'summary' in results and 'error' not in results:
                assessment['successful_models'] += 1
                
                avg_accuracy = results['summary']['average_accuracy']
                if avg_accuracy > assessment['best_accuracy']:
                    assessment['best_accuracy'] = avg_accuracy
                    assessment['best_model'] = model_name
        
        # Check if target accuracy achieved
        target_accuracy = validation_results['target_accuracy']
        assessment['target_achieved'] = assessment['best_accuracy'] >= target_accuracy
        
        # Generate recommendations
        if assessment['target_achieved']:
            assessment['recommendations'].append(
                f"✅ TARGET ACHIEVED! Best model '{assessment['best_model']}' reached "
                f"{assessment['best_accuracy']:.1%} accuracy (target: {target_accuracy:.1%})"
            )
        else:
            improvement = assessment['best_accuracy'] - self.baseline_accuracy
            improvement_pct = improvement / self.baseline_accuracy * 100
            
            assessment['recommendations'].extend([
                f"📊 Best improvement: {improvement_pct:.1f}% above baseline ({assessment['best_accuracy']:.1%})",
                f"🎯 Still {(target_accuracy - assessment['best_accuracy']):.1%} away from target",
                "🔧 Consider further model tuning or ensemble optimization"
            ])
        
        return assessment
    
    def _save_validation_results(self, results: Dict[str, Any]):
        """Save validation results to file"""
        try:
            output_dir = Path("results/validation")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"accuracy_validation_{timestamp}.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"💾 Validation results saved to {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error saving validation results: {e}")
    
    def generate_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate human-readable validation report"""
        
        report = [
            "=" * 80,
            "OMEGA PRO AI - ACCURACY VALIDATION REPORT",
            "=" * 80,
            f"Validation Date: {validation_results.get('timestamp', 'Unknown')}",
            f"Baseline Accuracy: {self.baseline_accuracy:.1%}",
            f"Target Accuracy: {validation_results.get('target_accuracy', 0.65):.1%}",
            "",
            "MODEL PERFORMANCE SUMMARY:",
            "-" * 40
        ]
        
        # Model results
        for model_name, results in validation_results.get('models', {}).items():
            if 'error' in results:
                report.append(f"❌ {model_name}: FAILED - {results['error']}")
            elif 'summary' in results:
                summary = results['summary']
                avg_acc = summary['average_accuracy']
                improvement = summary['improvement_vs_baseline']
                
                status = "✅" if avg_acc >= validation_results.get('target_accuracy', 0.65) else "📊"
                report.append(f"{status} {model_name}:")
                report.append(f"   Average Accuracy: {avg_acc:.1%}")
                report.append(f"   Improvement: {improvement:+.1%}")
                report.append(f"   Partial Hit Rate: {summary.get('partial_hit_rate', 0):.1%}")
                report.append("")
        
        # Overall assessment
        assessment = validation_results.get('assessment', {})
        report.extend([
            "OVERALL ASSESSMENT:",
            "-" * 20,
            f"Best Model: {assessment.get('best_model', 'None')}",
            f"Best Accuracy: {assessment.get('best_accuracy', 0):.1%}",
            f"Target Achieved: {'Yes' if assessment.get('target_achieved', False) else 'No'}",
            "",
            "RECOMMENDATIONS:",
            "-" * 15
        ])
        
        for rec in assessment.get('recommendations', []):
            report.append(f"• {rec}")
        
        report.extend([
            "",
            "=" * 80,
            "END REPORT"
        ])
        
        return "\n".join(report)

def run_accuracy_validation(historial_df: pd.DataFrame, 
                          baseline_accuracy: float = 0.50) -> Dict[str, Any]:
    """
    Main function to run accuracy validation
    
    Args:
        historial_df: Historical lottery data
        baseline_accuracy: Baseline accuracy to compare against
        
    Returns:
        Comprehensive validation results
    """
    validator = AccuracyValidationFramework(baseline_accuracy)
    results = validator.comprehensive_model_validation(historial_df)
    
    # Generate and print report
    report = validator.generate_validation_report(results)
    print(report)
    
    return results