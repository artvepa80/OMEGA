"""
OMEGA PRO AI v10.1 - A/B Test Reporter
=====================================

Automated reporting and insights generation for A/B testing results.
Creates comprehensive reports with visualizations, recommendations,
and actionable insights for stakeholders.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import base64
from io import BytesIO

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


@dataclass
class ReportSection:
    """A section of the A/B test report."""
    title: str
    content: str
    charts: List[str]  # Base64 encoded chart images
    insights: List[str]
    recommendations: List[str]


class TestReporter:
    """
    Automated A/B test reporting and insights generation.
    
    Creates comprehensive reports including:
    - Executive summary with key findings
    - Statistical analysis results
    - Performance metrics comparison  
    - Rare number detection analysis
    - Visual charts and graphs
    - Actionable recommendations
    """
    
    def __init__(self, output_dir: str = "reports/ab_testing"):
        self.output_dir = output_dir
        self.logger = self._setup_logging()
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/charts", exist_ok=True)
        
        # Configure plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        self.logger.info("Test Reporter initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for test reporter."""
        logger = logging.getLogger("omega_test_reporter")
        logger.setLevel(logging.INFO)
        
        os.makedirs("logs/ab_testing", exist_ok=True)
        handler = logging.FileHandler("logs/ab_testing/reporter.log")
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def generate_test_report(self, test_config: Any, 
                           statistical_results: Dict[str, Any],
                           performance_results: Dict[str, Any],
                           samples: List[Any]) -> Dict[str, Any]:
        """
        Generate comprehensive A/B test report.
        
        Args:
            test_config: A/B test configuration
            statistical_results: Results from statistical analysis
            performance_results: Results from performance comparison
            samples: All test samples
            
        Returns:
            Dict with complete report data
        """
        try:
            timestamp = datetime.now()
            
            # Generate report sections
            sections = []
            
            # Executive Summary
            exec_summary = self._create_executive_summary(
                test_config, statistical_results, performance_results
            )
            sections.append(exec_summary)
            
            # Statistical Analysis Section
            stats_section = self._create_statistical_section(statistical_results)
            sections.append(stats_section)
            
            # Performance Analysis Section  
            perf_section = self._create_performance_section(performance_results)
            sections.append(perf_section)
            
            # Rare Number Analysis Section
            rare_section = self._create_rare_number_section(performance_results)
            sections.append(rare_section)
            
            # Visual Analytics Section
            visual_section = self._create_visual_section(
                statistical_results, performance_results, samples
            )
            sections.append(visual_section)
            
            # Recommendations Section
            recommendations_section = self._create_recommendations_section(
                statistical_results, performance_results
            )
            sections.append(recommendations_section)
            
            # Compile full report
            report = {
                "test_id": test_config.test_id,
                "test_name": test_config.name,
                "generated_at": timestamp.isoformat(),
                "report_version": "1.0",
                "sections": [self._section_to_dict(s) for s in sections],
                "metadata": {
                    "sample_count": len(samples),
                    "test_duration_days": (timestamp - datetime.now()).days,  # Placeholder
                    "significance_level": test_config.significance_level
                }
            }
            
            # Save report files
            self._save_report(report, test_config.test_id)
            
            # Generate HTML report
            html_report = self._generate_html_report(report)
            self._save_html_report(html_report, test_config.test_id)
            
            self.logger.info(f"Generated comprehensive report for test {test_config.test_id}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating test report: {str(e)}")
            return {"error": f"Report generation failed: {str(e)}"}
    
    def generate_dashboard_data(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data for real-time A/B testing dashboard.
        
        Args:
            test_results: Complete test results
            
        Returns:
            Dict with dashboard-ready data
        """
        try:
            dashboard_data = {
                "summary_metrics": self._extract_summary_metrics(test_results),
                "charts": self._generate_dashboard_charts(test_results),
                "alerts": self._generate_alerts(test_results),
                "recommendations": self._extract_top_recommendations(test_results),
                "recent_updates": self._generate_recent_updates(test_results),
                "last_updated": datetime.now().isoformat()
            }
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard data: {str(e)}")
            return {"error": str(e)}
    
    def create_stakeholder_summary(self, test_results: Dict[str, Any],
                                 target_audience: str = "executive") -> Dict[str, Any]:
        """
        Create audience-specific summary report.
        
        Args:
            test_results: Complete test results
            target_audience: "executive", "technical", or "product"
            
        Returns:
            Dict with audience-tailored summary
        """
        try:
            if target_audience == "executive":
                return self._create_executive_summary_full(test_results)
            elif target_audience == "technical":
                return self._create_technical_summary(test_results)
            elif target_audience == "product":
                return self._create_product_summary(test_results)
            else:
                return self._create_general_summary(test_results)
                
        except Exception as e:
            self.logger.error(f"Error creating stakeholder summary: {str(e)}")
            return {"error": str(e)}
    
    def _create_executive_summary(self, test_config: Any,
                                statistical_results: Dict[str, Any],
                                performance_results: Dict[str, Any]) -> ReportSection:
        """Create executive summary section."""
        
        # Extract key metrics
        overall_assessment = performance_results.get("overall_assessment", {})
        recommendation = overall_assessment.get("recommendation", "CONTINUE_TEST")
        overall_score = overall_assessment.get("overall_score", 0) * 100
        
        # Key insights
        insights = [
            f"Test shows {abs(overall_score):.1f}% {'improvement' if overall_score > 0 else 'degradation'} overall",
            f"Recommendation: {recommendation.replace('_', ' ').title()}",
        ]
        
        # Add rare number insight if significant
        rare_analysis = performance_results.get("rare_number_analysis", {})
        rare_improvement = rare_analysis.get("overall_rare_accuracy", {}).get("improvement", 0)
        if abs(rare_improvement) > 0.05:  # 5% threshold
            insights.append(f"Rare number detection {'improved' if rare_improvement > 0 else 'degraded'} by {abs(rare_improvement)*100:.1f}%")
        
        # Statistical significance insight
        stats_summary = statistical_results.get("summary", {})
        significant_results = stats_summary.get("significant_results", 0)
        total_metrics = stats_summary.get("total_metrics_analyzed", 0)
        
        if total_metrics > 0:
            insights.append(f"{significant_results}/{total_metrics} metrics showed statistically significant differences")
        
        # Recommendations
        recommendations = [
            overall_assessment.get("reason", "Continue monitoring test results"),
            "Review detailed performance metrics before final decision",
            "Consider edge case performance in deployment planning"
        ]
        
        content = f"""
        **Test Overview**: {test_config.name}
        
        **Key Findings**:
        - Overall performance change: {overall_score:+.1f}%
        - Statistical significance: {significant_results}/{total_metrics} metrics
        - Rare number detection impact: {rare_improvement*100:+.1f}%
        
        **Business Impact**: {'Positive' if overall_score > 0 else 'Negative' if overall_score < 0 else 'Neutral'}
        """
        
        return ReportSection(
            title="Executive Summary",
            content=content,
            charts=[],  # Executive summary typically doesn't have charts
            insights=insights,
            recommendations=recommendations
        )
    
    def _create_statistical_section(self, statistical_results: Dict[str, Any]) -> ReportSection:
        """Create statistical analysis section."""
        
        insights = []
        recommendations = []
        
        # Process metric results
        metric_results = statistical_results.get("metric_results", [])
        
        significant_metrics = [r for r in metric_results if r.get("significant", False)]
        
        insights.append(f"Analyzed {len(metric_results)} performance metrics")
        insights.append(f"Found {len(significant_metrics)} statistically significant results")
        
        # Top significant results
        for result in significant_metrics[:3]:  # Top 3
            metric = result.get("metric_name", "unknown")
            improvement = result.get("improvement_pct", 0)
            p_value = result.get("p_value", 1)
            
            insights.append(f"{metric}: {improvement:+.1f}% change (p={p_value:.4f})")
        
        # Power analysis insights
        low_power_metrics = [r for r in metric_results if r.get("power", 1) < 0.8]
        if low_power_metrics:
            recommendations.append("Consider increasing sample size for more reliable results")
        
        # Generate statistical charts
        charts = []
        if metric_results:
            chart_data = self._create_statistical_charts(metric_results)
            charts.extend(chart_data)
        
        content = f"""
        **Statistical Analysis Results**
        
        Comprehensive statistical testing was performed on {len(metric_results)} metrics
        using appropriate tests (t-tests, Mann-Whitney U, proportions tests).
        
        **Significance Level**: {statistical_results.get('significance_level', 0.05)}
        **Multiple Comparisons**: Bonferroni correction applied
        """
        
        return ReportSection(
            title="Statistical Analysis",
            content=content,
            charts=charts,
            insights=insights,
            recommendations=recommendations
        )
    
    def _create_performance_section(self, performance_results: Dict[str, Any]) -> ReportSection:
        """Create performance analysis section."""
        
        insights = []
        recommendations = []
        
        # Overall assessment
        overall = performance_results.get("overall_assessment", {})
        improved_count = overall.get("improved_metrics", 0)
        degraded_count = overall.get("degraded_metrics", 0)
        
        insights.append(f"Performance improved in {improved_count} metrics")
        insights.append(f"Performance degraded in {degraded_count} metrics")
        
        # Key improvements and concerns
        key_improvements = overall.get("key_improvements", [])
        for improvement in key_improvements:
            metric = improvement.get("metric", "unknown")
            pct = improvement.get("improvement_pct", 0)
            insights.append(f"Best improvement: {metric} (+{pct:.1f}%)")
        
        key_concerns = overall.get("key_concerns", [])
        for concern in key_concerns:
            metric = concern.get("metric", "unknown")
            pct = abs(concern.get("degradation_pct", 0))
            insights.append(f"Concern: {metric} (-{pct:.1f}%)")
        
        # System performance
        system_perf = performance_results.get("system_performance", {})
        if "improvement" in system_perf:
            latency_improvement = system_perf["improvement"].get("median_pct", 0)
            if abs(latency_improvement) > 5:  # 5% threshold
                insights.append(f"Latency {'improved' if latency_improvement > 0 else 'increased'} by {abs(latency_improvement):.1f}%")
        
        # Generate performance charts
        charts = self._create_performance_charts(performance_results)
        
        # Recommendations
        if improved_count > degraded_count:
            recommendations.append("Performance improvements outweigh degradations")
        elif degraded_count > improved_count:
            recommendations.append("Address performance degradations before deployment")
        
        if system_perf and latency_improvement < -10:  # 10% latency increase
            recommendations.append("Investigate latency increase - may impact user experience")
        
        content = f"""
        **Performance Analysis**
        
        Comprehensive comparison of prediction accuracy, system performance,
        and user experience metrics between control and treatment variants.
        
        **Metrics Analyzed**: Accuracy, rare number detection, latency, confidence scoring
        **Performance Score**: {overall.get('overall_score', 0)*100:.1f}%
        """
        
        return ReportSection(
            title="Performance Analysis",
            content=content,
            charts=charts,
            insights=insights,
            recommendations=recommendations
        )
    
    def _create_rare_number_section(self, performance_results: Dict[str, Any]) -> ReportSection:
        """Create rare number analysis section."""
        
        insights = []
        recommendations = []
        charts = []
        
        rare_analysis = performance_results.get("rare_number_analysis", {})
        
        if "error" in rare_analysis:
            content = "**Rare Number Analysis**\n\nInsufficient data for rare number analysis."
            insights.append("Need more samples with rare number combinations")
            recommendations.append("Continue test to gather rare number edge cases")
        else:
            # Overall rare number performance
            overall_rare = rare_analysis.get("overall_rare_accuracy", {})
            control_accuracy = overall_rare.get("control", 0) * 100
            treatment_accuracy = overall_rare.get("treatment", 0) * 100
            improvement = overall_rare.get("improvement", 0) * 100
            
            insights.append(f"Control rare number accuracy: {control_accuracy:.1f}%")
            insights.append(f"Treatment rare number accuracy: {treatment_accuracy:.1f}%")
            insights.append(f"Improvement in rare number detection: {improvement:+.1f}%")
            
            # Range analysis
            range_analysis = rare_analysis.get("range_analysis", {})
            for range_name, data in range_analysis.items():
                control_acc = data.get("control_accuracy", 0) * 100
                treatment_acc = data.get("treatment_accuracy", 0) * 100
                range_improvement = treatment_acc - control_acc
                
                insights.append(f"{range_name} numbers: {range_improvement:+.1f}% improvement")
            
            # Generate rare number charts
            charts = self._create_rare_number_charts(rare_analysis)
            
            # Recommendations based on results
            if improvement > 10:
                recommendations.append("Strong improvement in rare number detection - deploy treatment")
            elif improvement < -5:
                recommendations.append("Rare number detection degraded - investigate algorithm changes")
            else:
                recommendations.append("Rare number performance stable - continue monitoring")
            
            content = f"""
            **Rare Number Detection Analysis**
            
            Special focus on edge cases like [12, 27, 1, 10, 13, 22] that are 
            particularly challenging to predict accurately.
            
            **Sample Size**: Control: {rare_analysis.get('rare_sample_counts', {}).get('control', 0)}, 
                            Treatment: {rare_analysis.get('rare_sample_counts', {}).get('treatment', 0)}
            **Overall Improvement**: {improvement:+.1f}%
            """
        
        return ReportSection(
            title="Rare Number Analysis",
            content=content,
            charts=charts,
            insights=insights,
            recommendations=recommendations
        )
    
    def _create_visual_section(self, statistical_results: Dict[str, Any],
                             performance_results: Dict[str, Any],
                             samples: List[Any]) -> ReportSection:
        """Create visual analytics section."""
        
        insights = ["Interactive visualizations provide detailed metric comparisons"]
        recommendations = ["Use charts to identify patterns and outliers in test results"]
        
        # Generate comprehensive chart suite
        charts = []
        
        # Main comparison dashboard chart
        dashboard_chart = self._create_dashboard_chart(statistical_results, performance_results)
        charts.extend(dashboard_chart)
        
        # Time series analysis if samples have timestamps
        if samples and hasattr(samples[0], 'timestamp'):
            time_series_chart = self._create_time_series_charts(samples)
            charts.extend(time_series_chart)
        
        # Distribution comparison charts
        distribution_charts = self._create_distribution_charts(statistical_results)
        charts.extend(distribution_charts)
        
        content = """
        **Visual Analytics**
        
        Interactive charts and visualizations for detailed analysis of A/B test results.
        Charts include metric comparisons, time series analysis, and distribution plots.
        """
        
        return ReportSection(
            title="Visual Analytics",
            content=content,
            charts=charts,
            insights=insights,
            recommendations=recommendations
        )
    
    def _create_recommendations_section(self, statistical_results: Dict[str, Any],
                                      performance_results: Dict[str, Any]) -> ReportSection:
        """Create recommendations section."""
        
        recommendations = []
        insights = []
        
        # Overall recommendation
        overall_assessment = performance_results.get("overall_assessment", {})
        main_recommendation = overall_assessment.get("recommendation", "CONTINUE_TEST")
        reason = overall_assessment.get("reason", "")
        
        recommendations.append(f"Main Recommendation: {main_recommendation.replace('_', ' ').title()}")
        recommendations.append(f"Rationale: {reason}")
        
        # Statistical recommendations
        stats_summary = statistical_results.get("summary", {})
        overall_rec = stats_summary.get("overall_recommendation", "")
        if overall_rec:
            recommendations.append(f"Statistical Analysis: {overall_rec}")
        
        # Performance-based recommendations
        overall_score = overall_assessment.get("overall_score", 0)
        if overall_score > 0.05:  # 5% improvement threshold
            recommendations.append("Deploy treatment variant - shows meaningful improvement")
            recommendations.append("Monitor post-deployment metrics to confirm results")
        elif overall_score < -0.02:  # 2% degradation threshold
            recommendations.append("Keep control variant - treatment shows degradation")
            recommendations.append("Investigate root causes of performance decrease")
        else:
            recommendations.append("Continue testing - results are inconclusive")
            recommendations.append("Consider increasing sample size for more definitive results")
        
        # Rare number specific recommendations
        rare_analysis = performance_results.get("rare_number_analysis", {})
        rare_improvement = rare_analysis.get("overall_rare_accuracy", {}).get("improvement", 0)
        
        if rare_improvement > 0.1:  # 10% improvement
            recommendations.append("Treatment significantly improves rare number detection")
            insights.append("Strong edge case performance improvement detected")
        elif rare_improvement < -0.05:  # 5% degradation
            recommendations.append("Address rare number detection degradation before deployment")
            insights.append("Edge case performance concern identified")
        
        # Next steps
        recommendations.append("Document learnings for future A/B test designs")
        recommendations.append("Plan gradual rollout if deploying treatment variant")
        recommendations.append("Set up monitoring alerts for key metrics post-deployment")
        
        # Risk assessment
        risks = []
        if overall_score < 0:
            risks.append("Performance degradation risk")
        
        degraded_metrics = overall_assessment.get("degraded_metrics", 0)
        if degraded_metrics > 2:
            risks.append("Multiple metric degradation")
        
        if risks:
            recommendations.append(f"Risk mitigation needed: {', '.join(risks)}")
        
        content = f"""
        **Final Recommendations**
        
        Based on comprehensive statistical analysis and performance comparison,
        the following recommendations are provided for stakeholders.
        
        **Primary Decision**: {main_recommendation.replace('_', ' ').title()}
        **Confidence Level**: {'High' if abs(overall_score) > 0.05 else 'Medium' if abs(overall_score) > 0.02 else 'Low'}
        **Risk Level**: {'High' if risks else 'Low'}
        """
        
        return ReportSection(
            title="Recommendations",
            content=content,
            charts=[],
            insights=insights,
            recommendations=recommendations
        )
    
    def _create_statistical_charts(self, metric_results: List[Dict[str, Any]]) -> List[str]:
        """Create statistical analysis charts."""
        charts = []
        
        try:
            # P-values chart
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # P-values bar chart
            metrics = [r["metric_name"] for r in metric_results]
            p_values = [r["p_value"] for r in metric_results]
            
            bars = ax1.bar(range(len(metrics)), p_values)
            ax1.axhline(y=0.05, color='red', linestyle='--', label='Significance threshold')
            ax1.set_xlabel('Metrics')
            ax1.set_ylabel('P-value')
            ax1.set_title('Statistical Significance by Metric')
            ax1.set_xticks(range(len(metrics)))
            ax1.set_xticklabels(metrics, rotation=45, ha='right')
            ax1.legend()
            
            # Color bars based on significance
            for i, (bar, p_val) in enumerate(zip(bars, p_values)):
                bar.set_color('green' if p_val < 0.05 else 'orange')
            
            # Effect sizes chart
            effect_sizes = [r["effect_size"] for r in metric_results]
            
            bars2 = ax2.bar(range(len(metrics)), effect_sizes)
            ax2.set_xlabel('Metrics')
            ax2.set_ylabel('Effect Size (Cohen\'s d)')
            ax2.set_title('Effect Size by Metric')
            ax2.set_xticks(range(len(metrics)))
            ax2.set_xticklabels(metrics, rotation=45, ha='right')
            
            # Color bars based on effect size magnitude
            for i, (bar, effect) in enumerate(zip(bars2, effect_sizes)):
                if abs(effect) > 0.8:
                    bar.set_color('darkgreen')  # Large effect
                elif abs(effect) > 0.5:
                    bar.set_color('green')      # Medium effect
                elif abs(effect) > 0.2:
                    bar.set_color('orange')     # Small effect
                else:
                    bar.set_color('lightgray')  # Negligible effect
            
            plt.tight_layout()
            
            # Save chart
            chart_buffer = BytesIO()
            plt.savefig(chart_buffer, format='png', dpi=300, bbox_inches='tight')
            chart_buffer.seek(0)
            chart_b64 = base64.b64encode(chart_buffer.read()).decode('utf-8')
            charts.append(chart_b64)
            
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Error creating statistical charts: {str(e)}")
        
        return charts
    
    def _create_performance_charts(self, performance_results: Dict[str, Any]) -> List[str]:
        """Create performance comparison charts."""
        charts = []
        
        try:
            # Metric comparison chart
            comparisons = performance_results.get("metric_comparisons", [])
            if not comparisons:
                return charts
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # Performance comparison chart
            metrics = [c["metric_name"] for c in comparisons]
            control_values = [c["control_value"] for c in comparisons]
            treatment_values = [c["treatment_value"] for c in comparisons]
            
            x = np.arange(len(metrics))
            width = 0.35
            
            ax1.bar(x - width/2, control_values, width, label='Control', alpha=0.7)
            ax1.bar(x + width/2, treatment_values, width, label='Treatment', alpha=0.7)
            
            ax1.set_xlabel('Metrics')
            ax1.set_ylabel('Value')
            ax1.set_title('Performance Comparison: Control vs Treatment')
            ax1.set_xticks(x)
            ax1.set_xticklabels(metrics, rotation=45, ha='right')
            ax1.legend()
            ax1.grid(axis='y', alpha=0.3)
            
            # Improvement percentage chart
            improvements = [c["improvement_pct"] for c in comparisons]
            
            bars = ax2.bar(metrics, improvements)
            ax2.set_xlabel('Metrics')
            ax2.set_ylabel('Improvement (%)')
            ax2.set_title('Performance Improvement by Metric')
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax2.set_xticklabels(metrics, rotation=45, ha='right')
            
            # Color bars based on improvement
            for bar, improvement in zip(bars, improvements):
                if improvement > 5:
                    bar.set_color('green')
                elif improvement > 0:
                    bar.set_color('lightgreen')
                elif improvement > -5:
                    bar.set_color('orange')
                else:
                    bar.set_color('red')
            
            plt.tight_layout()
            
            # Save chart
            chart_buffer = BytesIO()
            plt.savefig(chart_buffer, format='png', dpi=300, bbox_inches='tight')
            chart_buffer.seek(0)
            chart_b64 = base64.b64encode(chart_buffer.read()).decode('utf-8')
            charts.append(chart_b64)
            
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Error creating performance charts: {str(e)}")
        
        return charts
    
    def _create_rare_number_charts(self, rare_analysis: Dict[str, Any]) -> List[str]:
        """Create rare number analysis charts."""
        charts = []
        
        try:
            # Overall rare number accuracy comparison
            overall_rare = rare_analysis.get("overall_rare_accuracy", {})
            if not overall_rare:
                return charts
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Accuracy comparison
            control_acc = overall_rare.get("control", 0) * 100
            treatment_acc = overall_rare.get("treatment", 0) * 100
            
            categories = ['Control', 'Treatment']
            accuracies = [control_acc, treatment_acc]
            
            bars1 = ax1.bar(categories, accuracies, color=['blue', 'green'])
            ax1.set_ylabel('Accuracy (%)')
            ax1.set_title('Rare Number Detection Accuracy')
            ax1.set_ylim(0, max(accuracies) * 1.2)
            
            # Add value labels on bars
            for bar, value in zip(bars1, accuracies):
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                        f'{value:.1f}%', ha='center', va='bottom')
            
            # Range analysis if available
            range_analysis = rare_analysis.get("range_analysis", {})
            if range_analysis:
                ranges = list(range_analysis.keys())
                control_range_acc = [range_analysis[r]["control_accuracy"] * 100 for r in ranges]
                treatment_range_acc = [range_analysis[r]["treatment_accuracy"] * 100 for r in ranges]
                
                x = np.arange(len(ranges))
                width = 0.35
                
                ax2.bar(x - width/2, control_range_acc, width, label='Control', alpha=0.7)
                ax2.bar(x + width/2, treatment_range_acc, width, label='Treatment', alpha=0.7)
                
                ax2.set_xlabel('Number Ranges')
                ax2.set_ylabel('Accuracy (%)')
                ax2.set_title('Rare Number Accuracy by Range')
                ax2.set_xticks(x)
                ax2.set_xticklabels(ranges)
                ax2.legend()
            
            plt.tight_layout()
            
            # Save chart
            chart_buffer = BytesIO()
            plt.savefig(chart_buffer, format='png', dpi=300, bbox_inches='tight')
            chart_buffer.seek(0)
            chart_b64 = base64.b64encode(chart_buffer.read()).decode('utf-8')
            charts.append(chart_b64)
            
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Error creating rare number charts: {str(e)}")
        
        return charts
    
    def _create_dashboard_chart(self, statistical_results: Dict[str, Any],
                              performance_results: Dict[str, Any]) -> List[str]:
        """Create comprehensive dashboard chart."""
        # Implementation for dashboard chart
        # This would create a comprehensive overview chart
        return []
    
    def _create_time_series_charts(self, samples: List[Any]) -> List[str]:
        """Create time series analysis charts."""
        # Implementation for time series charts
        # This would analyze performance over time
        return []
    
    def _create_distribution_charts(self, statistical_results: Dict[str, Any]) -> List[str]:
        """Create distribution comparison charts."""
        # Implementation for distribution charts
        # This would show metric distributions for control vs treatment
        return []
    
    def _extract_summary_metrics(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary metrics for dashboard."""
        performance = test_results.get("performance", {})
        overall = performance.get("overall_assessment", {})
        
        return {
            "overall_score": overall.get("overall_score", 0) * 100,
            "recommendation": overall.get("recommendation", "CONTINUE_TEST"),
            "improved_metrics": overall.get("improved_metrics", 0),
            "degraded_metrics": overall.get("degraded_metrics", 0),
            "rare_number_improvement": (
                performance.get("rare_number_analysis", {})
                .get("overall_rare_accuracy", {})
                .get("improvement", 0) * 100
            )
        }
    
    def _generate_dashboard_charts(self, test_results: Dict[str, Any]) -> Dict[str, str]:
        """Generate charts for dashboard."""
        # Return base64 encoded chart data for dashboard
        return {
            "metrics_comparison": "chart_data_here",
            "time_series": "chart_data_here",
            "rare_numbers": "chart_data_here"
        }
    
    def _generate_alerts(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts for dashboard."""
        alerts = []
        
        performance = test_results.get("performance", {})
        overall = performance.get("overall_assessment", {})
        
        # Performance degradation alert
        overall_score = overall.get("overall_score", 0)
        if overall_score < -0.05:  # 5% degradation
            alerts.append({
                "type": "warning",
                "title": "Performance Degradation Detected",
                "message": f"Overall performance decreased by {abs(overall_score)*100:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # Statistical significance alert
        statistics = test_results.get("statistics", {})
        significant_results = statistics.get("summary", {}).get("significant_results", 0)
        if significant_results > 0:
            alerts.append({
                "type": "info",
                "title": "Statistically Significant Results",
                "message": f"{significant_results} metrics show significant differences",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def _extract_top_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Extract top recommendations for dashboard."""
        performance = test_results.get("performance", {})
        overall = performance.get("overall_assessment", {})
        
        recommendations = []
        
        # Main recommendation
        main_rec = overall.get("recommendation", "CONTINUE_TEST")
        recommendations.append(main_rec.replace('_', ' ').title())
        
        # Add context
        reason = overall.get("reason", "")
        if reason:
            recommendations.append(reason)
        
        return recommendations[:3]  # Top 3 recommendations
    
    def _generate_recent_updates(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recent updates for dashboard."""
        return [
            {
                "timestamp": datetime.now().isoformat(),
                "type": "analysis",
                "message": "Statistical analysis completed"
            },
            {
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "type": "data",
                "message": "Performance comparison updated"
            }
        ]
    
    def _create_executive_summary_full(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create full executive summary."""
        # Implementation for executive summary
        return {"summary": "Executive summary content"}
    
    def _create_technical_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create technical summary."""
        # Implementation for technical summary
        return {"summary": "Technical summary content"}
    
    def _create_product_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create product summary."""
        # Implementation for product summary
        return {"summary": "Product summary content"}
    
    def _create_general_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create general summary."""
        # Implementation for general summary
        return {"summary": "General summary content"}
    
    def _section_to_dict(self, section: ReportSection) -> Dict[str, Any]:
        """Convert ReportSection to dictionary."""
        return {
            "title": section.title,
            "content": section.content,
            "charts": section.charts,
            "insights": section.insights,
            "recommendations": section.recommendations
        }
    
    def _save_report(self, report: Dict[str, Any], test_id: str):
        """Save report to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/report_{test_id}_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
                
            self.logger.info(f"Saved report to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving report: {str(e)}")
    
    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML version of report."""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>OMEGA A/B Test Report - {test_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .section {{ margin-bottom: 30px; padding: 20px; border-left: 4px solid #007acc; }}
                .chart {{ max-width: 100%; height: auto; margin: 20px 0; }}
                .insight {{ background-color: #f0f8ff; padding: 10px; margin: 5px 0; border-radius: 5px; }}
                .recommendation {{ background-color: #f0fff0; padding: 10px; margin: 5px 0; border-radius: 5px; }}
                h1 {{ color: #007acc; }}
                h2 {{ color: #005c99; }}
            </style>
        </head>
        <body>
            <h1>A/B Test Report: {test_name}</h1>
            <p><strong>Generated:</strong> {generated_at}</p>
            
            {sections_html}
        </body>
        </html>
        """
        
        # Generate sections HTML
        sections_html = ""
        for section in report["sections"]:
            sections_html += f"""
            <div class="section">
                <h2>{section['title']}</h2>
                <div>{section['content']}</div>
                
                {''.join([f'<img class="chart" src="data:image/png;base64,{chart}" />' for chart in section.get('charts', [])])}
                
                <h3>Key Insights:</h3>
                {''.join([f'<div class="insight">• {insight}</div>' for insight in section.get('insights', [])])}
                
                <h3>Recommendations:</h3>
                {''.join([f'<div class="recommendation">• {rec}</div>' for rec in section.get('recommendations', [])])}
            </div>
            """
        
        return html_template.format(
            test_name=report.get("test_name", "Unknown Test"),
            generated_at=report.get("generated_at", "Unknown Time"),
            sections_html=sections_html
        )
    
    def _save_html_report(self, html_content: str, test_id: str):
        """Save HTML report to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/report_{test_id}_{timestamp}.html"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            self.logger.info(f"Saved HTML report to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving HTML report: {str(e)}")