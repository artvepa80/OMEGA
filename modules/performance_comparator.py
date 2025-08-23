"""
OMEGA PRO AI v10.1 - Performance Comparison System
================================================

Comprehensive performance metrics comparison for A/B testing of:
- Prediction accuracy improvements
- Rare number detection capabilities  
- System latency and throughput
- Confidence scoring accuracy
- Historical performance analysis
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    accuracy: float
    rare_number_detection: float
    latency_ms: float
    confidence_score: float
    partial_matches: float
    exact_matches: float
    false_positives: float
    false_negatives: float
    f1_score: float
    precision: float
    recall: float


@dataclass 
class ComparisonResult:
    """Result of performance comparison."""
    metric_name: str
    control_value: float
    treatment_value: float
    improvement_pct: float
    improvement_absolute: float
    is_better: bool
    confidence: float
    historical_context: Dict[str, Any]


class PerformanceComparator:
    """
    Performance comparison engine for A/B testing.
    
    Analyzes and compares prediction performance metrics between
    control and treatment groups, with special focus on:
    - Rare number prediction accuracy (edge cases like [12, 27, 1, 10, 13, 22])
    - Overall prediction accuracy improvements
    - System performance (latency, throughput)
    - Confidence calibration accuracy
    """
    
    def __init__(self, historical_data_path: str = "data/historical_performance.json"):
        self.historical_data_path = historical_data_path
        self.logger = self._setup_logging()
        
        # Load historical performance baselines
        self.historical_baselines = self._load_historical_baselines()
        
        # Metric weights for overall scoring
        self.metric_weights = {
            "accuracy": 0.3,
            "rare_number_detection": 0.25,  # High weight for rare number cases
            "confidence_score": 0.15,
            "latency_ms": 0.1,
            "f1_score": 0.2
        }
        
        # Define what constitutes "rare" numbers for special analysis
        self.rare_number_ranges = [(1, 9), (31, 42)]  # Very low and very high numbers
        
        self.logger.info("Performance Comparator initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for performance comparison."""
        logger = logging.getLogger("omega_performance_comparator")
        logger.setLevel(logging.INFO)
        
        os.makedirs("logs/ab_testing", exist_ok=True)
        handler = logging.FileHandler("logs/ab_testing/performance_comparison.log")
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def compare_variants(self, control_samples: List[Any], 
                        treatment_samples: List[Any],
                        metrics_to_compare: List[str] = None) -> Dict[str, Any]:
        """
        Compare performance metrics between control and treatment variants.
        
        Args:
            control_samples: Control group samples
            treatment_samples: Treatment group samples  
            metrics_to_compare: Specific metrics to analyze
            
        Returns:
            Dict with comprehensive comparison results
        """
        try:
            if metrics_to_compare is None:
                metrics_to_compare = list(self.metric_weights.keys())
            
            # Extract and aggregate metrics
            control_metrics = self._aggregate_metrics(control_samples)
            treatment_metrics = self._aggregate_metrics(treatment_samples)
            
            # Perform detailed comparisons
            comparison_results = []
            
            for metric_name in metrics_to_compare:
                if metric_name in control_metrics and metric_name in treatment_metrics:
                    comparison = self._compare_metric(
                        metric_name, 
                        control_metrics[metric_name],
                        treatment_metrics[metric_name]
                    )
                    comparison_results.append(comparison)
            
            # Special analysis for rare number detection
            rare_number_analysis = self._analyze_rare_number_performance(
                control_samples, treatment_samples
            )
            
            # System performance analysis
            system_perf_analysis = self._analyze_system_performance(
                control_samples, treatment_samples
            )
            
            # Historical comparison
            historical_analysis = self._compare_with_historical_baselines(
                control_metrics, treatment_metrics
            )
            
            # Generate overall assessment
            overall_assessment = self._generate_overall_assessment(
                comparison_results, rare_number_analysis, system_perf_analysis
            )
            
            # Create comprehensive report
            results = {
                "comparison_timestamp": datetime.now().isoformat(),
                "sample_sizes": {
                    "control": len(control_samples),
                    "treatment": len(treatment_samples)
                },
                "metric_comparisons": [self._comparison_to_dict(c) for c in comparison_results],
                "rare_number_analysis": rare_number_analysis,
                "system_performance": system_perf_analysis,
                "historical_comparison": historical_analysis,
                "overall_assessment": overall_assessment,
                "detailed_metrics": {
                    "control": control_metrics,
                    "treatment": treatment_metrics
                }
            }
            
            # Save comparison results
            self._save_comparison_results(results)
            
            self.logger.info(f"Completed performance comparison for {len(comparison_results)} metrics")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in performance comparison: {str(e)}")
            return {"error": f"Performance comparison failed: {str(e)}"}
    
    def analyze_time_series_performance(self, samples: List[Any], 
                                      time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Analyze performance metrics over time to detect trends and degradation.
        
        Args:
            samples: Test samples with timestamps
            time_window_hours: Size of time window for analysis
            
        Returns:
            Dict with time series analysis
        """
        try:
            # Group samples by time windows
            time_groups = self._group_samples_by_time(samples, time_window_hours)
            
            # Calculate metrics for each time period
            time_series_data = []
            
            for timestamp, group_samples in time_groups.items():
                metrics = self._aggregate_metrics(group_samples)
                metrics["timestamp"] = timestamp
                metrics["sample_count"] = len(group_samples)
                time_series_data.append(metrics)
            
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(time_series_data)
            
            if df.empty:
                return {"error": "No time series data available"}
            
            # Analyze trends
            trends = {}
            for metric in ["accuracy", "rare_number_detection", "latency_ms"]:
                if metric in df.columns:
                    correlation = df['timestamp'].astype(int).corr(df[metric])
                    trends[metric] = {
                        "correlation": correlation,
                        "trend": "improving" if correlation > 0.1 else "degrading" if correlation < -0.1 else "stable",
                        "mean": float(df[metric].mean()),
                        "std": float(df[metric].std()),
                        "min": float(df[metric].min()),
                        "max": float(df[metric].max())
                    }
            
            # Detect performance anomalies
            anomalies = self._detect_performance_anomalies(df)
            
            return {
                "time_series_data": time_series_data,
                "trends": trends,
                "anomalies": anomalies,
                "analysis_period": {
                    "start": min(time_groups.keys()),
                    "end": max(time_groups.keys()),
                    "window_hours": time_window_hours
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in time series analysis: {str(e)}")
            return {"error": f"Time series analysis failed: {str(e)}"}
    
    def compare_edge_cases(self, control_samples: List[Any],
                          treatment_samples: List[Any]) -> Dict[str, Any]:
        """
        Special analysis for edge cases like rare number combinations.
        
        Focuses on combinations like [12, 27, 1, 10, 13, 22] that are
        particularly challenging to predict.
        """
        try:
            # Identify edge case samples
            control_edge_cases = self._identify_edge_cases(control_samples)
            treatment_edge_cases = self._identify_edge_cases(treatment_samples)
            
            if not control_edge_cases or not treatment_edge_cases:
                return {
                    "message": "Insufficient edge case samples for comparison",
                    "control_edge_cases": len(control_edge_cases),
                    "treatment_edge_cases": len(treatment_edge_cases)
                }
            
            # Compare performance on edge cases
            control_edge_metrics = self._aggregate_metrics(control_edge_cases)
            treatment_edge_metrics = self._aggregate_metrics(treatment_edge_cases)
            
            # Special metrics for edge cases
            edge_case_analysis = {
                "sample_counts": {
                    "control": len(control_edge_cases),
                    "treatment": len(treatment_edge_cases)
                },
                "accuracy_comparison": {
                    "control": control_edge_metrics.get("accuracy", 0),
                    "treatment": treatment_edge_metrics.get("accuracy", 0),
                    "improvement": treatment_edge_metrics.get("accuracy", 0) - control_edge_metrics.get("accuracy", 0)
                },
                "rare_number_detection": {
                    "control": control_edge_metrics.get("rare_number_detection", 0),
                    "treatment": treatment_edge_metrics.get("rare_number_detection", 0),
                    "improvement": treatment_edge_metrics.get("rare_number_detection", 0) - control_edge_metrics.get("rare_number_detection", 0)
                },
                "edge_case_patterns": self._analyze_edge_case_patterns(
                    control_edge_cases + treatment_edge_cases
                )
            }
            
            return edge_case_analysis
            
        except Exception as e:
            self.logger.error(f"Error in edge case analysis: {str(e)}")
            return {"error": f"Edge case analysis failed: {str(e)}"}
    
    def generate_performance_dashboard_data(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data for performance comparison dashboard visualization.
        
        Args:
            comparison_results: Results from compare_variants
            
        Returns:
            Dict with dashboard-ready data
        """
        try:
            dashboard_data = {
                "summary_cards": self._create_summary_cards(comparison_results),
                "metric_charts": self._create_metric_charts_data(comparison_results),
                "rare_number_charts": self._create_rare_number_charts_data(comparison_results),
                "performance_trends": self._create_performance_trends_data(comparison_results),
                "recommendations": self._generate_dashboard_recommendations(comparison_results)
            }
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard data: {str(e)}")
            return {"error": f"Dashboard data generation failed: {str(e)}"}
    
    def _aggregate_metrics(self, samples: List[Any]) -> Dict[str, float]:
        """Aggregate metrics from samples."""
        if not samples:
            return {}
        
        # Collect all metrics
        all_metrics = defaultdict(list)
        
        for sample in samples:
            sample_metrics = getattr(sample, 'metrics', {})
            for metric_name, value in sample_metrics.items():
                if isinstance(value, (int, float)) and not np.isnan(value):
                    all_metrics[metric_name].append(value)
        
        # Calculate aggregated values
        aggregated = {}
        for metric_name, values in all_metrics.items():
            if values:
                if metric_name in ["latency_ms"]:
                    # For latency, use median to reduce outlier impact
                    aggregated[metric_name] = float(np.median(values))
                else:
                    # For most metrics, use mean
                    aggregated[metric_name] = float(np.mean(values))
        
        # Calculate additional derived metrics
        if "partial_matches" in aggregated and "accuracy" not in aggregated:
            # Calculate accuracy from partial matches if not directly available
            aggregated["accuracy"] = aggregated["partial_matches"] / 6.0  # Assuming 6 numbers drawn
        
        # Calculate F1 score if we have precision and recall
        if "precision" in aggregated and "recall" in aggregated:
            p, r = aggregated["precision"], aggregated["recall"]
            if p + r > 0:
                aggregated["f1_score"] = 2 * (p * r) / (p + r)
        
        return aggregated
    
    def _compare_metric(self, metric_name: str, control_value: float, 
                       treatment_value: float) -> ComparisonResult:
        """Compare individual metric between variants."""
        # Calculate improvements
        if control_value == 0:
            improvement_pct = 0.0 if treatment_value == 0 else 100.0
        else:
            improvement_pct = ((treatment_value - control_value) / control_value) * 100
        
        improvement_absolute = treatment_value - control_value
        
        # Determine if treatment is better (depends on metric type)
        is_better = self._is_treatment_better(metric_name, control_value, treatment_value)
        
        # Calculate confidence based on magnitude of difference
        confidence = min(1.0, abs(improvement_pct) / 10.0)  # Simplified confidence
        
        # Get historical context
        historical_context = self._get_historical_context(metric_name, treatment_value)
        
        return ComparisonResult(
            metric_name=metric_name,
            control_value=control_value,
            treatment_value=treatment_value,
            improvement_pct=improvement_pct,
            improvement_absolute=improvement_absolute,
            is_better=is_better,
            confidence=confidence,
            historical_context=historical_context
        )
    
    def _is_treatment_better(self, metric_name: str, control_value: float, 
                           treatment_value: float) -> bool:
        """Determine if treatment is better for given metric."""
        # For most metrics, higher is better
        higher_is_better = ["accuracy", "rare_number_detection", "confidence_score", 
                           "f1_score", "precision", "recall", "partial_matches", "exact_matches"]
        
        # For some metrics, lower is better  
        lower_is_better = ["latency_ms", "false_positives", "false_negatives"]
        
        if metric_name in higher_is_better:
            return treatment_value > control_value
        elif metric_name in lower_is_better:
            return treatment_value < control_value
        else:
            # Default: assume higher is better
            return treatment_value > control_value
    
    def _analyze_rare_number_performance(self, control_samples: List[Any],
                                       treatment_samples: List[Any]) -> Dict[str, Any]:
        """Special analysis for rare number prediction performance."""
        try:
            # Filter samples with rare numbers in actual results
            control_rare = self._filter_rare_number_samples(control_samples)
            treatment_rare = self._filter_rare_number_samples(treatment_samples)
            
            if not control_rare or not treatment_rare:
                return {
                    "message": "Insufficient rare number samples",
                    "control_rare_samples": len(control_rare),
                    "treatment_rare_samples": len(treatment_rare)
                }
            
            # Calculate rare number specific metrics
            control_rare_accuracy = self._calculate_rare_number_accuracy(control_rare)
            treatment_rare_accuracy = self._calculate_rare_number_accuracy(treatment_rare)
            
            # Analyze specific rare number ranges
            range_analysis = {}
            for range_name, (low, high) in [("very_low", (1, 9)), ("very_high", (31, 42))]:
                control_range = self._filter_number_range_samples(control_samples, low, high)
                treatment_range = self._filter_number_range_samples(treatment_samples, low, high)
                
                if control_range and treatment_range:
                    range_analysis[range_name] = {
                        "control_accuracy": self._calculate_range_accuracy(control_range, low, high),
                        "treatment_accuracy": self._calculate_range_accuracy(treatment_range, low, high),
                        "sample_counts": {
                            "control": len(control_range),
                            "treatment": len(treatment_range)
                        }
                    }
            
            return {
                "overall_rare_accuracy": {
                    "control": control_rare_accuracy,
                    "treatment": treatment_rare_accuracy,
                    "improvement": treatment_rare_accuracy - control_rare_accuracy
                },
                "range_analysis": range_analysis,
                "rare_sample_counts": {
                    "control": len(control_rare),
                    "treatment": len(treatment_rare)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in rare number analysis: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_system_performance(self, control_samples: List[Any],
                                  treatment_samples: List[Any]) -> Dict[str, Any]:
        """Analyze system performance metrics like latency and throughput."""
        try:
            # Extract timing information
            control_latencies = []
            treatment_latencies = []
            
            for sample in control_samples:
                latency = getattr(sample, 'metrics', {}).get('latency_ms')
                if latency is not None:
                    control_latencies.append(latency)
            
            for sample in treatment_samples:
                latency = getattr(sample, 'metrics', {}).get('latency_ms')
                if latency is not None:
                    treatment_latencies.append(latency)
            
            if not control_latencies or not treatment_latencies:
                return {"message": "Insufficient latency data"}
            
            # Calculate latency statistics
            latency_analysis = {
                "control": {
                    "mean": float(np.mean(control_latencies)),
                    "median": float(np.median(control_latencies)),
                    "p95": float(np.percentile(control_latencies, 95)),
                    "p99": float(np.percentile(control_latencies, 99)),
                    "std": float(np.std(control_latencies))
                },
                "treatment": {
                    "mean": float(np.mean(treatment_latencies)),
                    "median": float(np.median(treatment_latencies)),
                    "p95": float(np.percentile(treatment_latencies, 95)),
                    "p99": float(np.percentile(treatment_latencies, 99)),
                    "std": float(np.std(treatment_latencies))
                }
            }
            
            # Calculate improvement
            latency_analysis["improvement"] = {
                "mean_pct": ((latency_analysis["control"]["mean"] - latency_analysis["treatment"]["mean"]) / 
                            latency_analysis["control"]["mean"] * 100),
                "median_pct": ((latency_analysis["control"]["median"] - latency_analysis["treatment"]["median"]) / 
                              latency_analysis["control"]["median"] * 100)
            }
            
            return latency_analysis
            
        except Exception as e:
            self.logger.error(f"Error in system performance analysis: {str(e)}")
            return {"error": str(e)}
    
    def _filter_rare_number_samples(self, samples: List[Any]) -> List[Any]:
        """Filter samples that contain rare numbers in actual results."""
        rare_samples = []
        
        for sample in samples:
            actual_result = getattr(sample, 'actual_result', None)
            if actual_result and self._contains_rare_numbers(actual_result):
                rare_samples.append(sample)
        
        return rare_samples
    
    def _contains_rare_numbers(self, numbers: List[int]) -> bool:
        """Check if number list contains rare numbers."""
        for number in numbers:
            for low, high in self.rare_number_ranges:
                if low <= number <= high:
                    return True
        return False
    
    def _calculate_rare_number_accuracy(self, samples: List[Any]) -> float:
        """Calculate accuracy specifically for rare number predictions."""
        if not samples:
            return 0.0
        
        total_rare_predicted = 0
        total_rare_actual = 0
        
        for sample in samples:
            prediction = getattr(sample, 'prediction', [])
            actual = getattr(sample, 'actual_result', [])
            
            if not prediction or not actual:
                continue
            
            # Count rare numbers in prediction and actual
            rare_predicted = self._count_rare_numbers(prediction)
            rare_actual = self._count_rare_numbers(actual)
            
            # Count correct rare predictions
            rare_correct = len(set(self._get_rare_numbers(prediction)).intersection(
                set(self._get_rare_numbers(actual))
            ))
            
            total_rare_predicted += rare_correct
            total_rare_actual += rare_actual
        
        return total_rare_predicted / max(total_rare_actual, 1)
    
    def _count_rare_numbers(self, numbers: List[int]) -> int:
        """Count rare numbers in a list."""
        count = 0
        for number in numbers:
            for low, high in self.rare_number_ranges:
                if low <= number <= high:
                    count += 1
                    break
        return count
    
    def _get_rare_numbers(self, numbers: List[int]) -> List[int]:
        """Get list of rare numbers from a number list."""
        rare_numbers = []
        for number in numbers:
            for low, high in self.rare_number_ranges:
                if low <= number <= high:
                    rare_numbers.append(number)
                    break
        return rare_numbers
    
    def _filter_number_range_samples(self, samples: List[Any], low: int, high: int) -> List[Any]:
        """Filter samples containing numbers in specific range."""
        filtered = []
        for sample in samples:
            actual = getattr(sample, 'actual_result', [])
            if any(low <= num <= high for num in actual):
                filtered.append(sample)
        return filtered
    
    def _calculate_range_accuracy(self, samples: List[Any], low: int, high: int) -> float:
        """Calculate accuracy for specific number range."""
        if not samples:
            return 0.0
        
        correct_predictions = 0
        total_in_range = 0
        
        for sample in samples:
            prediction = getattr(sample, 'prediction', [])
            actual = getattr(sample, 'actual_result', [])
            
            if not prediction or not actual:
                continue
            
            # Numbers in range for actual and predicted
            actual_in_range = [n for n in actual if low <= n <= high]
            predicted_in_range = [n for n in prediction if low <= n <= high]
            
            # Count correct predictions in range
            correct_in_range = len(set(actual_in_range).intersection(set(predicted_in_range)))
            
            correct_predictions += correct_in_range
            total_in_range += len(actual_in_range)
        
        return correct_predictions / max(total_in_range, 1)
    
    def _identify_edge_cases(self, samples: List[Any]) -> List[Any]:
        """Identify edge case samples for special analysis."""
        edge_cases = []
        
        for sample in samples:
            actual = getattr(sample, 'actual_result', [])
            if not actual:
                continue
            
            # Define edge case criteria
            is_edge_case = (
                self._contains_rare_numbers(actual) or  # Contains rare numbers
                len(set(actual)) != len(actual) or  # Contains duplicates
                max(actual) - min(actual) > 35 or  # Very wide spread
                self._has_unusual_pattern(actual)  # Other unusual patterns
            )
            
            if is_edge_case:
                edge_cases.append(sample)
        
        return edge_cases
    
    def _has_unusual_pattern(self, numbers: List[int]) -> bool:
        """Check for unusual patterns in number combinations."""
        if len(numbers) < 3:
            return False
        
        # Check for arithmetic sequence
        sorted_numbers = sorted(numbers)
        diffs = [sorted_numbers[i+1] - sorted_numbers[i] for i in range(len(sorted_numbers)-1)]
        if len(set(diffs)) == 1 and diffs[0] > 1:  # Consistent gap > 1
            return True
        
        # Check for all even or all odd
        if all(n % 2 == 0 for n in numbers) or all(n % 2 == 1 for n in numbers):
            return True
        
        return False
    
    def _analyze_edge_case_patterns(self, edge_case_samples: List[Any]) -> Dict[str, Any]:
        """Analyze patterns in edge case samples."""
        if not edge_case_samples:
            return {}
        
        patterns = {
            "rare_numbers": 0,
            "wide_spread": 0,
            "arithmetic_sequence": 0,
            "all_even": 0,
            "all_odd": 0
        }
        
        for sample in edge_case_samples:
            actual = getattr(sample, 'actual_result', [])
            if not actual:
                continue
            
            if self._contains_rare_numbers(actual):
                patterns["rare_numbers"] += 1
            
            if max(actual) - min(actual) > 35:
                patterns["wide_spread"] += 1
            
            if self._is_arithmetic_sequence(actual):
                patterns["arithmetic_sequence"] += 1
            
            if all(n % 2 == 0 for n in actual):
                patterns["all_even"] += 1
            elif all(n % 2 == 1 for n in actual):
                patterns["all_odd"] += 1
        
        return patterns
    
    def _is_arithmetic_sequence(self, numbers: List[int]) -> bool:
        """Check if numbers form arithmetic sequence."""
        if len(numbers) < 3:
            return False
        
        sorted_numbers = sorted(numbers)
        diff = sorted_numbers[1] - sorted_numbers[0]
        
        for i in range(2, len(sorted_numbers)):
            if sorted_numbers[i] - sorted_numbers[i-1] != diff:
                return False
        
        return diff > 1
    
    def _compare_with_historical_baselines(self, control_metrics: Dict[str, float],
                                         treatment_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Compare current results with historical baselines."""
        try:
            if not self.historical_baselines:
                return {"message": "No historical baselines available"}
            
            historical_comparison = {}
            
            for metric_name in control_metrics:
                if metric_name in self.historical_baselines:
                    baseline_value = self.historical_baselines[metric_name]["mean"]
                    baseline_std = self.historical_baselines[metric_name]["std"]
                    
                    # Compare control and treatment to baseline
                    control_vs_baseline = (control_metrics[metric_name] - baseline_value) / baseline_std if baseline_std > 0 else 0
                    treatment_vs_baseline = (treatment_metrics[metric_name] - baseline_value) / baseline_std if baseline_std > 0 else 0
                    
                    historical_comparison[metric_name] = {
                        "baseline_value": baseline_value,
                        "control_z_score": control_vs_baseline,
                        "treatment_z_score": treatment_vs_baseline,
                        "control_vs_baseline_pct": ((control_metrics[metric_name] - baseline_value) / baseline_value * 100) if baseline_value != 0 else 0,
                        "treatment_vs_baseline_pct": ((treatment_metrics[metric_name] - baseline_value) / baseline_value * 100) if baseline_value != 0 else 0
                    }
            
            return historical_comparison
            
        except Exception as e:
            self.logger.error(f"Error in historical comparison: {str(e)}")
            return {"error": str(e)}
    
    def _generate_overall_assessment(self, comparison_results: List[ComparisonResult],
                                   rare_number_analysis: Dict[str, Any],
                                   system_perf_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall assessment of A/B test performance."""
        try:
            # Count improvements
            improved_metrics = [r for r in comparison_results if r.is_better]
            degraded_metrics = [r for r in comparison_results if not r.is_better and abs(r.improvement_pct) > 1]
            
            # Calculate weighted score
            weighted_score = 0
            total_weight = 0
            
            for result in comparison_results:
                if result.metric_name in self.metric_weights:
                    weight = self.metric_weights[result.metric_name]
                    score = result.improvement_pct / 100 if result.is_better else -abs(result.improvement_pct) / 100
                    weighted_score += score * weight
                    total_weight += weight
            
            if total_weight > 0:
                weighted_score /= total_weight
            
            # Generate recommendation
            if weighted_score > 0.05:  # 5% overall improvement
                recommendation = "DEPLOY_TREATMENT"
                reason = f"Treatment shows {weighted_score*100:.1f}% overall improvement"
            elif weighted_score < -0.02:  # 2% overall degradation
                recommendation = "KEEP_CONTROL"
                reason = f"Treatment shows {abs(weighted_score)*100:.1f}% overall degradation"
            else:
                recommendation = "CONTINUE_TEST"
                reason = "Results are inconclusive, continue testing"
            
            # Special consideration for rare number performance
            rare_improvement = rare_number_analysis.get("overall_rare_accuracy", {}).get("improvement", 0)
            if rare_improvement > 0.1:  # 10% improvement in rare number detection
                recommendation = "DEPLOY_TREATMENT"
                reason += f" (Strong rare number detection improvement: +{rare_improvement*100:.1f}%)"
            
            return {
                "overall_score": weighted_score,
                "improved_metrics": len(improved_metrics),
                "degraded_metrics": len(degraded_metrics),
                "total_metrics": len(comparison_results),
                "recommendation": recommendation,
                "reason": reason,
                "key_improvements": [
                    {
                        "metric": r.metric_name,
                        "improvement_pct": r.improvement_pct
                    }
                    for r in improved_metrics[:3]  # Top 3 improvements
                ],
                "key_concerns": [
                    {
                        "metric": r.metric_name,
                        "degradation_pct": r.improvement_pct
                    }
                    for r in degraded_metrics[:3]  # Top 3 concerns
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error generating overall assessment: {str(e)}")
            return {"error": str(e)}
    
    def _load_historical_baselines(self) -> Dict[str, Dict[str, float]]:
        """Load historical performance baselines."""
        try:
            if os.path.exists(self.historical_data_path):
                with open(self.historical_data_path, 'r') as f:
                    return json.load(f)
            else:
                # Create default baselines
                defaults = {
                    "accuracy": {"mean": 0.15, "std": 0.05},
                    "rare_number_detection": {"mean": 0.08, "std": 0.03},
                    "latency_ms": {"mean": 150.0, "std": 50.0},
                    "confidence_score": {"mean": 0.7, "std": 0.1}
                }
                return defaults
        except Exception as e:
            self.logger.error(f"Error loading historical baselines: {str(e)}")
            return {}
    
    def _get_historical_context(self, metric_name: str, value: float) -> Dict[str, Any]:
        """Get historical context for a metric value."""
        if metric_name not in self.historical_baselines:
            return {}
        
        baseline = self.historical_baselines[metric_name]
        z_score = (value - baseline["mean"]) / baseline["std"] if baseline["std"] > 0 else 0
        
        # Interpret z-score
        if abs(z_score) < 1:
            interpretation = "within normal range"
        elif abs(z_score) < 2:
            interpretation = "somewhat unusual" if z_score > 0 else "somewhat below average"
        else:
            interpretation = "exceptionally high" if z_score > 0 else "exceptionally low"
        
        return {
            "baseline_mean": baseline["mean"],
            "z_score": z_score,
            "interpretation": interpretation,
            "percentile": float(stats.norm.cdf(z_score) * 100)
        }
    
    def _group_samples_by_time(self, samples: List[Any], 
                              window_hours: int) -> Dict[int, List[Any]]:
        """Group samples by time windows."""
        time_groups = defaultdict(list)
        
        for sample in samples:
            timestamp = getattr(sample, 'timestamp', None)
            if timestamp:
                # Convert to hour bucket
                hour_bucket = int(timestamp.timestamp() // (window_hours * 3600))
                time_groups[hour_bucket].append(sample)
        
        return dict(time_groups)
    
    def _detect_performance_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect performance anomalies in time series data."""
        anomalies = []
        
        for metric in ["accuracy", "rare_number_detection", "latency_ms"]:
            if metric not in df.columns:
                continue
            
            values = df[metric]
            mean_val = values.mean()
            std_val = values.std()
            
            # Simple outlier detection
            for i, value in enumerate(values):
                z_score = abs((value - mean_val) / std_val) if std_val > 0 else 0
                if z_score > 3:  # 3 standard deviations
                    anomalies.append({
                        "metric": metric,
                        "timestamp": df.iloc[i]["timestamp"],
                        "value": value,
                        "z_score": z_score,
                        "type": "outlier"
                    })
        
        return anomalies
    
    def _create_summary_cards(self, comparison_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create summary cards for dashboard."""
        cards = []
        
        # Overall performance card
        overall = comparison_results.get("overall_assessment", {})
        cards.append({
            "title": "Overall Performance",
            "value": f"{overall.get('overall_score', 0)*100:.1f}%",
            "subtitle": overall.get("recommendation", ""),
            "trend": "up" if overall.get('overall_score', 0) > 0 else "down"
        })
        
        # Rare number detection card
        rare_analysis = comparison_results.get("rare_number_analysis", {})
        rare_improvement = rare_analysis.get("overall_rare_accuracy", {}).get("improvement", 0)
        cards.append({
            "title": "Rare Number Detection",
            "value": f"{rare_improvement*100:+.1f}%",
            "subtitle": "Edge Case Performance",
            "trend": "up" if rare_improvement > 0 else "down"
        })
        
        return cards
    
    def _create_metric_charts_data(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create chart data for metrics comparison."""
        # This would generate data for various chart types
        return {
            "comparison_chart": "data for metric comparison chart",
            "improvement_chart": "data for improvement percentage chart"
        }
    
    def _create_rare_number_charts_data(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create chart data for rare number analysis."""
        return {
            "rare_accuracy_chart": "data for rare number accuracy chart",
            "range_analysis_chart": "data for number range analysis"
        }
    
    def _create_performance_trends_data(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create performance trend chart data."""
        return {
            "time_series_chart": "data for performance over time",
            "anomaly_markers": "data for anomaly detection visualization"
        }
    
    def _generate_dashboard_recommendations(self, comparison_results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations for dashboard."""
        recommendations = []
        
        overall = comparison_results.get("overall_assessment", {})
        if overall.get("recommendation") == "DEPLOY_TREATMENT":
            recommendations.append("Deploy treatment variant - shows significant improvement")
        elif overall.get("recommendation") == "KEEP_CONTROL":
            recommendations.append("Keep control variant - treatment shows degradation")
        else:
            recommendations.append("Continue testing - results inconclusive")
        
        return recommendations
    
    def _comparison_to_dict(self, comparison: ComparisonResult) -> Dict[str, Any]:
        """Convert ComparisonResult to dictionary."""
        return {
            "metric_name": comparison.metric_name,
            "control_value": comparison.control_value,
            "treatment_value": comparison.treatment_value,
            "improvement_pct": comparison.improvement_pct,
            "improvement_absolute": comparison.improvement_absolute,
            "is_better": comparison.is_better,
            "confidence": comparison.confidence,
            "historical_context": comparison.historical_context
        }
    
    def _save_comparison_results(self, results: Dict[str, Any]):
        """Save comparison results to disk."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results/ab_testing/performance_comparison_{timestamp}.json"
            
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error saving comparison results: {str(e)}")