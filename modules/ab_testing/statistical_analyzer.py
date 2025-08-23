"""
OMEGA PRO AI v10.1 - Statistical Analysis for A/B Tests
======================================================

Comprehensive statistical analysis of A/B test results including:
- Hypothesis testing (t-tests, chi-square, Mann-Whitney U)
- Effect size calculation (Cohen's d)
- Confidence intervals
- Power analysis
- Multiple comparisons correction
- Bayesian analysis
"""

import math
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import norm, chi2, mannwhitneyu, ttest_ind, beta


class TestType(Enum):
    """Types of statistical tests available."""
    T_TEST = "t_test"
    CHI_SQUARE = "chi_square"
    MANN_WHITNEY = "mann_whitney"
    PROPORTIONS = "proportions"
    BAYESIAN = "bayesian"


@dataclass
class StatisticalResult:
    """Result of a statistical test."""
    test_type: str
    metric_name: str
    control_mean: float
    treatment_mean: float
    effect_size: float
    p_value: float
    confidence_interval: Tuple[float, float]
    significant: bool
    power: float
    sample_size_control: int
    sample_size_treatment: int
    interpretation: str


@dataclass
class BayesianResult:
    """Result of Bayesian analysis."""
    metric_name: str
    probability_treatment_better: float
    credible_interval: Tuple[float, float]
    expected_loss_control: float
    expected_loss_treatment: float
    interpretation: str


class StatisticalAnalyzer:
    """
    Statistical analysis engine for A/B test results.
    
    Provides comprehensive statistical testing with proper corrections
    for multiple comparisons and detailed interpretation of results.
    """
    
    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level
        self.logger = self._setup_logging()
        
        # Minimum sample sizes for reliable tests
        self.min_sample_sizes = {
            TestType.T_TEST: 30,
            TestType.CHI_SQUARE: 5,
            TestType.MANN_WHITNEY: 10,
            TestType.PROPORTIONS: 30,
            TestType.BAYESIAN: 10
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for statistical analysis."""
        logger = logging.getLogger("omega_statistical_analyzer")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler("logs/ab_testing/statistical_analysis.log")
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def analyze_test_results(self, control_samples: List[Any], 
                           treatment_samples: List[Any],
                           significance_level: float = None) -> Dict[str, Any]:
        """
        Perform comprehensive statistical analysis of A/B test results.
        
        Args:
            control_samples: List of control group samples
            treatment_samples: List of treatment group samples
            significance_level: Override default significance level
            
        Returns:
            Dict with complete statistical analysis
        """
        if significance_level is None:
            significance_level = self.significance_level
        
        try:
            # Extract metrics from samples
            control_metrics = self._extract_metrics(control_samples)
            treatment_metrics = self._extract_metrics(treatment_samples)
            
            # Validate sample sizes
            if not self._validate_sample_sizes(control_metrics, treatment_metrics):
                return {"error": "Insufficient sample size for reliable analysis"}
            
            # Perform analysis for each metric
            results = {}
            
            # Get common metrics
            common_metrics = set(control_metrics.keys()).intersection(
                set(treatment_metrics.keys())
            )
            
            if not common_metrics:
                return {"error": "No common metrics found between control and treatment"}
            
            # Analyze each metric
            metric_results = []
            bayesian_results = []
            
            for metric_name in common_metrics:
                control_values = control_metrics[metric_name]
                treatment_values = treatment_metrics[metric_name]
                
                # Skip if insufficient data
                if len(control_values) < 10 or len(treatment_values) < 10:
                    continue
                
                # Determine appropriate test
                test_type = self._select_test_type(control_values, treatment_values)
                
                # Perform statistical test
                stat_result = self._perform_statistical_test(
                    control_values, treatment_values, metric_name, 
                    test_type, significance_level
                )
                
                if stat_result:
                    metric_results.append(stat_result)
                
                # Perform Bayesian analysis
                bayes_result = self._perform_bayesian_analysis(
                    control_values, treatment_values, metric_name
                )
                
                if bayes_result:
                    bayesian_results.append(bayes_result)
            
            # Multiple comparisons correction
            corrected_results = self._correct_multiple_comparisons(
                metric_results, method="bonferroni"
            )
            
            # Overall test summary
            summary = self._generate_test_summary(
                corrected_results, bayesian_results, control_samples, treatment_samples
            )
            
            results = {
                "summary": summary,
                "metric_results": [self._result_to_dict(r) for r in corrected_results],
                "bayesian_results": [self._bayes_to_dict(r) for r in bayesian_results],
                "sample_sizes": {
                    "control": len(control_samples),
                    "treatment": len(treatment_samples)
                },
                "significance_level": significance_level,
                "analysis_timestamp": pd.Timestamp.now().isoformat()
            }
            
            self.logger.info(f"Completed statistical analysis for {len(metric_results)} metrics")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in statistical analysis: {str(e)}")
            return {"error": f"Statistical analysis failed: {str(e)}"}
    
    def power_analysis(self, effect_size: float, alpha: float = 0.05, 
                      power: float = 0.8) -> int:
        """
        Calculate required sample size for given effect size and power.
        
        Args:
            effect_size: Expected Cohen's d
            alpha: Type I error rate (significance level)
            power: Desired statistical power
            
        Returns:
            int: Required sample size per group
        """
        try:
            # Z-scores for alpha and power
            z_alpha = norm.ppf(1 - alpha / 2)
            z_beta = norm.ppf(power)
            
            # Sample size calculation
            n = ((z_alpha + z_beta) ** 2 * 2) / (effect_size ** 2)
            
            return math.ceil(n)
            
        except Exception as e:
            self.logger.error(f"Error in power analysis: {str(e)}")
            return 100  # Safe default
    
    def sequential_analysis(self, control_samples: List[Any],
                          treatment_samples: List[Any],
                          metric_name: str) -> Dict[str, Any]:
        """
        Perform sequential analysis to detect early stopping opportunities.
        
        Args:
            control_samples: Control group samples
            treatment_samples: Treatment group samples
            metric_name: Metric to analyze
            
        Returns:
            Dict with sequential analysis results
        """
        try:
            control_metrics = [
                getattr(sample, 'metrics', {}).get(metric_name, 0)
                for sample in control_samples
            ]
            treatment_metrics = [
                getattr(sample, 'metrics', {}).get(metric_name, 0)
                for sample in treatment_samples
            ]
            
            # Remove None/invalid values
            control_values = [v for v in control_metrics if v is not None]
            treatment_values = [v for v in treatment_metrics if v is not None]
            
            if len(control_values) < 20 or len(treatment_values) < 20:
                return {"recommendation": "continue", "reason": "Insufficient sample size"}
            
            # Calculate running statistics
            running_p_values = []
            running_effect_sizes = []
            
            min_size = min(len(control_values), len(treatment_values))
            
            for i in range(20, min_size, 10):  # Check every 10 samples after minimum
                c_subset = control_values[:i]
                t_subset = treatment_values[:i]
                
                # Perform t-test
                t_stat, p_val = ttest_ind(c_subset, t_subset)
                running_p_values.append(p_val)
                
                # Calculate effect size
                effect_size = self._calculate_cohens_d(c_subset, t_subset)
                running_effect_sizes.append(effect_size)
            
            # Sequential testing with alpha spending
            current_p = running_p_values[-1] if running_p_values else 1.0
            current_effect = abs(running_effect_sizes[-1]) if running_effect_sizes else 0.0
            
            # Stopping criteria
            if current_p < 0.01 and current_effect > 0.5:
                recommendation = "stop_significant"
                reason = f"Strong significant result detected (p={current_p:.4f}, d={current_effect:.3f})"
            elif current_p < 0.05 and len(control_values) > 100:
                recommendation = "stop_significant"
                reason = f"Significant result with adequate sample size (p={current_p:.4f})"
            elif current_p > 0.5 and len(control_values) > 200:
                recommendation = "stop_futility"
                reason = f"Futility analysis suggests no effect (p={current_p:.4f})"
            else:
                recommendation = "continue"
                reason = "Insufficient evidence for early stopping"
            
            return {
                "recommendation": recommendation,
                "reason": reason,
                "current_p_value": current_p,
                "current_effect_size": current_effect,
                "running_p_values": running_p_values,
                "running_effect_sizes": running_effect_sizes
            }
            
        except Exception as e:
            self.logger.error(f"Error in sequential analysis: {str(e)}")
            return {"recommendation": "continue", "reason": "Analysis error"}
    
    def _extract_metrics(self, samples: List[Any]) -> Dict[str, List[float]]:
        """Extract metrics from sample objects."""
        metrics = {}
        
        for sample in samples:
            sample_metrics = getattr(sample, 'metrics', {})
            
            for metric_name, value in sample_metrics.items():
                if isinstance(value, (int, float)) and not math.isnan(value):
                    if metric_name not in metrics:
                        metrics[metric_name] = []
                    metrics[metric_name].append(float(value))
        
        return metrics
    
    def _validate_sample_sizes(self, control_metrics: Dict[str, List], 
                             treatment_metrics: Dict[str, List]) -> bool:
        """Validate that sample sizes are sufficient for analysis."""
        for metric_name in control_metrics:
            if metric_name in treatment_metrics:
                c_size = len(control_metrics[metric_name])
                t_size = len(treatment_metrics[metric_name])
                
                if c_size >= 10 and t_size >= 10:
                    return True
        
        return False
    
    def _select_test_type(self, control_values: List[float], 
                         treatment_values: List[float]) -> TestType:
        """Select appropriate statistical test based on data characteristics."""
        # Check for normality (simplified)
        control_normal = self._is_approximately_normal(control_values)
        treatment_normal = self._is_approximately_normal(treatment_values)
        
        # Check if data is binary/proportional
        control_binary = all(v in [0, 1] for v in control_values)
        treatment_binary = all(v in [0, 1] for v in treatment_values)
        
        if control_binary and treatment_binary:
            return TestType.PROPORTIONS
        elif control_normal and treatment_normal:
            return TestType.T_TEST
        else:
            return TestType.MANN_WHITNEY
    
    def _is_approximately_normal(self, values: List[float]) -> bool:
        """Check if values are approximately normally distributed."""
        if len(values) < 8:
            return True  # Assume normal for small samples
        
        try:
            # Shapiro-Wilk test for normality
            _, p_value = stats.shapiro(values)
            return p_value > 0.05
        except:
            return True  # Default to normal if test fails
    
    def _perform_statistical_test(self, control_values: List[float],
                                treatment_values: List[float],
                                metric_name: str,
                                test_type: TestType,
                                significance_level: float) -> Optional[StatisticalResult]:
        """Perform the appropriate statistical test."""
        try:
            control_array = np.array(control_values)
            treatment_array = np.array(treatment_values)
            
            control_mean = np.mean(control_array)
            treatment_mean = np.mean(treatment_array)
            
            # Perform test based on type
            if test_type == TestType.T_TEST:
                t_stat, p_value = ttest_ind(control_array, treatment_array)
                effect_size = self._calculate_cohens_d(control_values, treatment_values)
                
            elif test_type == TestType.MANN_WHITNEY:
                u_stat, p_value = mannwhitneyu(
                    control_array, treatment_array, alternative='two-sided'
                )
                effect_size = self._calculate_rank_effect_size(
                    control_values, treatment_values
                )
                
            elif test_type == TestType.PROPORTIONS:
                p_value, effect_size = self._proportions_test(
                    control_values, treatment_values
                )
                
            else:
                return None
            
            # Calculate confidence interval
            ci = self._calculate_confidence_interval(
                control_values, treatment_values, significance_level
            )
            
            # Calculate power
            power = self._calculate_power(
                control_values, treatment_values, effect_size, significance_level
            )
            
            # Determine significance
            significant = p_value < significance_level
            
            # Generate interpretation
            interpretation = self._interpret_result(
                metric_name, control_mean, treatment_mean, 
                effect_size, p_value, significant
            )
            
            return StatisticalResult(
                test_type=test_type.value,
                metric_name=metric_name,
                control_mean=control_mean,
                treatment_mean=treatment_mean,
                effect_size=effect_size,
                p_value=p_value,
                confidence_interval=ci,
                significant=significant,
                power=power,
                sample_size_control=len(control_values),
                sample_size_treatment=len(treatment_values),
                interpretation=interpretation
            )
            
        except Exception as e:
            self.logger.error(f"Error in statistical test for {metric_name}: {str(e)}")
            return None
    
    def _calculate_cohens_d(self, control: List[float], treatment: List[float]) -> float:
        """Calculate Cohen's d effect size."""
        control_array = np.array(control)
        treatment_array = np.array(treatment)
        
        pooled_std = np.sqrt(
            ((len(control) - 1) * np.var(control_array, ddof=1) +
             (len(treatment) - 1) * np.var(treatment_array, ddof=1)) /
            (len(control) + len(treatment) - 2)
        )
        
        if pooled_std == 0:
            return 0.0
        
        return (np.mean(treatment_array) - np.mean(control_array)) / pooled_std
    
    def _calculate_rank_effect_size(self, control: List[float], 
                                  treatment: List[float]) -> float:
        """Calculate effect size for Mann-Whitney U test."""
        n1, n2 = len(control), len(treatment)
        u_stat, _ = mannwhitneyu(control, treatment, alternative='two-sided')
        
        # Convert to effect size (r = Z / sqrt(N))
        z_score = (u_stat - (n1 * n2) / 2) / np.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12)
        return abs(z_score) / np.sqrt(n1 + n2)
    
    def _proportions_test(self, control: List[float], 
                         treatment: List[float]) -> Tuple[float, float]:
        """Perform proportions test and calculate effect size."""
        c_successes = sum(control)
        t_successes = sum(treatment)
        c_n = len(control)
        t_n = len(treatment)
        
        # Proportions
        p1 = c_successes / c_n
        p2 = t_successes / t_n
        
        # Pooled proportion
        p_pool = (c_successes + t_successes) / (c_n + t_n)
        
        # Standard error
        se = np.sqrt(p_pool * (1 - p_pool) * (1/c_n + 1/t_n))
        
        if se == 0:
            return 1.0, 0.0
        
        # Z-statistic
        z = (p2 - p1) / se
        
        # P-value (two-tailed)
        p_value = 2 * (1 - norm.cdf(abs(z)))
        
        # Effect size (Cohen's h)
        effect_size = 2 * (np.arcsin(np.sqrt(p2)) - np.arcsin(np.sqrt(p1)))
        
        return p_value, effect_size
    
    def _calculate_confidence_interval(self, control: List[float],
                                     treatment: List[float],
                                     significance_level: float) -> Tuple[float, float]:
        """Calculate confidence interval for the difference in means."""
        try:
            control_array = np.array(control)
            treatment_array = np.array(treatment)
            
            diff_mean = np.mean(treatment_array) - np.mean(control_array)
            
            # Standard error of difference
            se = np.sqrt(
                np.var(control_array, ddof=1) / len(control) +
                np.var(treatment_array, ddof=1) / len(treatment)
            )
            
            # Degrees of freedom (Welch's)
            df = (
                (np.var(control_array, ddof=1) / len(control) +
                 np.var(treatment_array, ddof=1) / len(treatment)) ** 2
            ) / (
                (np.var(control_array, ddof=1) / len(control)) ** 2 / (len(control) - 1) +
                (np.var(treatment_array, ddof=1) / len(treatment)) ** 2 / (len(treatment) - 1)
            )
            
            # Critical t-value
            t_crit = stats.t.ppf(1 - significance_level / 2, df)
            
            # Confidence interval
            margin = t_crit * se
            
            return (diff_mean - margin, diff_mean + margin)
            
        except:
            return (0.0, 0.0)
    
    def _calculate_power(self, control: List[float], treatment: List[float],
                        effect_size: float, significance_level: float) -> float:
        """Calculate statistical power of the test."""
        try:
            n1, n2 = len(control), len(treatment)
            
            # Critical value
            z_alpha = norm.ppf(1 - significance_level / 2)
            
            # Non-centrality parameter
            ncp = abs(effect_size) * np.sqrt((n1 * n2) / (n1 + n2))
            
            # Power calculation
            power = 1 - norm.cdf(z_alpha - ncp) + norm.cdf(-z_alpha - ncp)
            
            return max(0.0, min(1.0, power))
            
        except:
            return 0.5  # Default power estimate
    
    def _perform_bayesian_analysis(self, control: List[float],
                                 treatment: List[float],
                                 metric_name: str) -> Optional[BayesianResult]:
        """Perform Bayesian analysis of the results."""
        try:
            control_array = np.array(control)
            treatment_array = np.array(treatment)
            
            # Use Beta-Binomial model for binary metrics, normal for continuous
            if all(v in [0, 1] for v in control + treatment):
                result = self._bayesian_proportions(control, treatment, metric_name)
            else:
                result = self._bayesian_continuous(control_array, treatment_array, metric_name)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in Bayesian analysis for {metric_name}: {str(e)}")
            return None
    
    def _bayesian_proportions(self, control: List[float], treatment: List[float],
                            metric_name: str) -> BayesianResult:
        """Bayesian analysis for proportions using Beta-Binomial model."""
        # Prior parameters (non-informative Beta(1,1))
        alpha_prior, beta_prior = 1, 1
        
        # Control group posterior
        c_successes = sum(control)
        c_trials = len(control)
        alpha_c = alpha_prior + c_successes
        beta_c = beta_prior + c_trials - c_successes
        
        # Treatment group posterior
        t_successes = sum(treatment)
        t_trials = len(treatment)
        alpha_t = alpha_prior + t_successes
        beta_t = beta_prior + t_trials - t_successes
        
        # Monte Carlo sampling for probability calculation
        n_samples = 10000
        c_samples = beta.rvs(alpha_c, beta_c, size=n_samples)
        t_samples = beta.rvs(alpha_t, beta_t, size=n_samples)
        
        # Probability that treatment is better
        prob_t_better = np.mean(t_samples > c_samples)
        
        # Credible interval for difference
        diff_samples = t_samples - c_samples
        ci_lower = np.percentile(diff_samples, 2.5)
        ci_upper = np.percentile(diff_samples, 97.5)
        
        # Expected loss calculations
        expected_loss_c = np.mean(np.maximum(0, t_samples - c_samples))
        expected_loss_t = np.mean(np.maximum(0, c_samples - t_samples))
        
        # Interpretation
        if prob_t_better > 0.95:
            interpretation = f"Very strong evidence that treatment is better ({prob_t_better:.1%} probability)"
        elif prob_t_better > 0.9:
            interpretation = f"Strong evidence that treatment is better ({prob_t_better:.1%} probability)"
        elif prob_t_better > 0.8:
            interpretation = f"Moderate evidence that treatment is better ({prob_t_better:.1%} probability)"
        elif prob_t_better < 0.05:
            interpretation = f"Very strong evidence that control is better ({1-prob_t_better:.1%} probability)"
        elif prob_t_better < 0.1:
            interpretation = f"Strong evidence that control is better ({1-prob_t_better:.1%} probability)"
        elif prob_t_better < 0.2:
            interpretation = f"Moderate evidence that control is better ({1-prob_t_better:.1%} probability)"
        else:
            interpretation = f"Inconclusive results ({prob_t_better:.1%} probability treatment is better)"
        
        return BayesianResult(
            metric_name=metric_name,
            probability_treatment_better=prob_t_better,
            credible_interval=(ci_lower, ci_upper),
            expected_loss_control=expected_loss_c,
            expected_loss_treatment=expected_loss_t,
            interpretation=interpretation
        )
    
    def _bayesian_continuous(self, control: np.ndarray, treatment: np.ndarray,
                           metric_name: str) -> BayesianResult:
        """Bayesian analysis for continuous metrics using normal model."""
        # Simple approach using t-distribution approximation
        c_mean, c_std = np.mean(control), np.std(control, ddof=1)
        t_mean, t_std = np.mean(treatment), np.std(treatment, ddof=1)
        
        n_c, n_t = len(control), len(treatment)
        
        # Posterior parameters for difference in means
        pooled_var = ((n_c - 1) * c_std**2 + (n_t - 1) * t_std**2) / (n_c + n_t - 2)
        se_diff = np.sqrt(pooled_var * (1/n_c + 1/n_t))
        
        diff_mean = t_mean - c_mean
        
        # Use normal approximation for large samples
        if n_c + n_t > 60:
            # Probability that treatment is better
            prob_t_better = 1 - norm.cdf(0, diff_mean, se_diff)
        else:
            # Use t-distribution for small samples
            df = n_c + n_t - 2
            prob_t_better = 1 - stats.t.cdf(0, df, diff_mean, se_diff)
        
        # 95% credible interval
        ci_lower = diff_mean - 1.96 * se_diff
        ci_upper = diff_mean + 1.96 * se_diff
        
        # Expected loss calculations (simplified)
        expected_loss_c = max(0, diff_mean) * prob_t_better
        expected_loss_t = max(0, -diff_mean) * (1 - prob_t_better)
        
        # Interpretation
        if prob_t_better > 0.975:
            interpretation = f"Very strong evidence that treatment is better ({prob_t_better:.1%} probability)"
        elif prob_t_better > 0.95:
            interpretation = f"Strong evidence that treatment is better ({prob_t_better:.1%} probability)"
        elif prob_t_better > 0.8:
            interpretation = f"Moderate evidence that treatment is better ({prob_t_better:.1%} probability)"
        elif prob_t_better < 0.025:
            interpretation = f"Very strong evidence that control is better ({1-prob_t_better:.1%} probability)"
        elif prob_t_better < 0.05:
            interpretation = f"Strong evidence that control is better ({1-prob_t_better:.1%} probability)"
        elif prob_t_better < 0.2:
            interpretation = f"Moderate evidence that control is better ({1-prob_t_better:.1%} probability)"
        else:
            interpretation = f"Inconclusive results ({prob_t_better:.1%} probability treatment is better)"
        
        return BayesianResult(
            metric_name=metric_name,
            probability_treatment_better=prob_t_better,
            credible_interval=(ci_lower, ci_upper),
            expected_loss_control=expected_loss_c,
            expected_loss_treatment=expected_loss_t,
            interpretation=interpretation
        )
    
    def _correct_multiple_comparisons(self, results: List[StatisticalResult],
                                    method: str = "bonferroni") -> List[StatisticalResult]:
        """Apply multiple comparisons correction."""
        if not results or len(results) <= 1:
            return results
        
        p_values = [r.p_value for r in results]
        
        if method == "bonferroni":
            corrected_alpha = self.significance_level / len(results)
            
            for result in results:
                result.significant = result.p_value < corrected_alpha
        
        # Could add other methods like Benjamini-Hochberg here
        
        return results
    
    def _interpret_result(self, metric_name: str, control_mean: float,
                         treatment_mean: float, effect_size: float,
                         p_value: float, significant: bool) -> str:
        """Generate human-readable interpretation of result."""
        direction = "increased" if treatment_mean > control_mean else "decreased"
        change_pct = abs((treatment_mean - control_mean) / control_mean * 100) if control_mean != 0 else 0
        
        # Effect size interpretation
        if abs(effect_size) < 0.2:
            magnitude = "negligible"
        elif abs(effect_size) < 0.5:
            magnitude = "small"
        elif abs(effect_size) < 0.8:
            magnitude = "medium"
        else:
            magnitude = "large"
        
        if significant:
            interpretation = (
                f"Statistically significant result: {metric_name} {direction} by "
                f"{change_pct:.1f}% in treatment group (p={p_value:.4f}). "
                f"Effect size is {magnitude} (d={effect_size:.3f})."
            )
        else:
            interpretation = (
                f"No statistically significant difference in {metric_name} "
                f"(p={p_value:.4f}). Observed {change_pct:.1f}% {direction[:-1]}se "
                f"may be due to random variation. Effect size is {magnitude} (d={effect_size:.3f})."
            )
        
        return interpretation
    
    def _generate_test_summary(self, statistical_results: List[StatisticalResult],
                             bayesian_results: List[BayesianResult],
                             control_samples: List[Any],
                             treatment_samples: List[Any]) -> Dict[str, Any]:
        """Generate overall test summary."""
        significant_results = [r for r in statistical_results if r.significant]
        
        summary = {
            "total_metrics_analyzed": len(statistical_results),
            "significant_results": len(significant_results),
            "sample_sizes": {
                "control": len(control_samples),
                "treatment": len(treatment_samples)
            },
            "overall_recommendation": self._get_overall_recommendation(
                statistical_results, bayesian_results
            )
        }
        
        return summary
    
    def _get_overall_recommendation(self, statistical_results: List[StatisticalResult],
                                  bayesian_results: List[BayesianResult]) -> str:
        """Generate overall recommendation based on all results."""
        significant_count = sum(1 for r in statistical_results if r.significant)
        total_count = len(statistical_results)
        
        if significant_count == 0:
            return "No significant differences detected. Consider continuing test or investigating implementation."
        elif significant_count == total_count and total_count > 1:
            return "All metrics show significant improvement. Strong evidence for treatment effectiveness."
        elif significant_count > total_count * 0.5:
            return "Majority of metrics show significant improvement. Treatment appears effective."
        else:
            return "Mixed results detected. Some metrics improved significantly while others did not."
    
    def _result_to_dict(self, result: StatisticalResult) -> Dict[str, Any]:
        """Convert StatisticalResult to dictionary."""
        return {
            "test_type": result.test_type,
            "metric_name": result.metric_name,
            "control_mean": result.control_mean,
            "treatment_mean": result.treatment_mean,
            "effect_size": result.effect_size,
            "p_value": result.p_value,
            "confidence_interval": result.confidence_interval,
            "significant": result.significant,
            "power": result.power,
            "sample_size_control": result.sample_size_control,
            "sample_size_treatment": result.sample_size_treatment,
            "interpretation": result.interpretation
        }
    
    def _bayes_to_dict(self, result: BayesianResult) -> Dict[str, Any]:
        """Convert BayesianResult to dictionary."""
        return {
            "metric_name": result.metric_name,
            "probability_treatment_better": result.probability_treatment_better,
            "credible_interval": result.credible_interval,
            "expected_loss_control": result.expected_loss_control,
            "expected_loss_treatment": result.expected_loss_treatment,
            "interpretation": result.interpretation
        }